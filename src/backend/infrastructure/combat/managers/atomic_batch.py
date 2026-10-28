"""Stage fallible Redis commands before publishing an RBC state transition.

Redis scripts isolate execution, but do not roll back command errors. All
fallible mutations therefore target private copies. Publication uses only
pre-authorized RENAME/DEL on known keys, after staging has fully succeeded.
This adapter targets the project's standalone Redis 7 server (COPY and ACL
checks); it does not provide cross-slot Redis Cluster transactions.
"""

STAGED_BATCH_SCRIPT = r"""
local request = cjson.decode(ARGV[1])
local meta = KEYS[1]
local function reject(reason) return redis.error_reply('Combat ' .. reason) end
if request.mode == 'create' then
    if redis.call('EXISTS', meta) == 1 then
        local fingerprint = redis.call('HGET', meta, 'creation_fingerprint')
        if fingerprint ~= request.fingerprint then return reject('creation conflict or incomplete session') end
        if redis.call('HGET', meta, 'creation_complete') ~= '1' then return reject('incomplete session') end
        for _, key in ipairs(request.required_json) do
            if not redis.call('JSON.GET', key, '$') then return reject('incomplete session') end
        end
        return 0
    end
    for _, key in ipairs(KEYS) do
        if redis.call('EXISTS', key) == 1 then return reject('incomplete session') end
    end
else
    if redis.call('GET', request.lock_key) ~= request.owner then return reject('owner lost') end
    if redis.call('HGET', meta, 'last_exchange_id') == request.exchange_id then
        if redis.call('HGET', meta, 'last_exchange_digest') ~= request.digest then
            return reject('exchange identity conflict')
        end
        return 0
    end
    if redis.call('HGET', meta, 'active') ~= '1' then return reject('inactive session') end
    if tonumber(redis.call('HGET', meta, 'revision') or '0') ~= request.revision then
        return reject('revision conflict')
    end
    for field, value in pairs(request.expected_meta) do
        if redis.call('HGET', meta, field) ~= value then return reject('meta snapshot changed') end
    end
    for key, value in pairs(request.expected_actors) do
        if redis.call('JSON.GET', key, '$') ~= value then return reject('actor snapshot changed') end
    end
    for i, value in ipairs(request.actions) do
        if redis.call('LINDEX', request.queue_key, i - 1) ~= value then return reject('queue prefix changed') end
    end
end

local stages = {}
for i, key in ipairs(KEYS) do
    stages[i] = key .. ':stage:' .. request.nonce
    if redis.call('EXISTS', stages[i]) == 1 then return reject('stage collision') end
    -- ACL failures must be detected BEFORE publishing the first live key.
    if not redis.acl_check_cmd('RENAME', stages[i], key) or
       not redis.acl_check_cmd('DEL', key, stages[i]) then return reject('publication permission denied') end
end
local function cleanup()
    for _, key in ipairs(stages) do redis.pcall('DEL', key) end
end
local function command(...)
    local result = redis.pcall(...)
    if type(result) == 'table' and result.err then error(result.err) end
    return result
end
local ok, failure = pcall(function()
    for i, key in ipairs(KEYS) do
        if request.mode ~= 'create' then command('COPY', key, stages[i], 'REPLACE') end
        command('EXPIRE', stages[i], 60)
    end
    for _, operation in ipairs(request.operations) do
        local key = stages[operation.index]
        if operation.kind == 'logs' then
            for turn, additions in pairs(operation.entries) do
                local previous = command('HGET', key, turn)
                local values = previous and cjson.decode(previous) or {}
                for _, value in ipairs(cjson.decode(additions)) do table.insert(values, value) end
                command('HSET', key, turn, cjson.encode(values))
            end
        elseif operation.kind == 'prune' then
            local raw = command('JSON.GET', key, '$')
            if not raw then error('missing targets') end
            local dead = {}
            for _, actor in ipairs(operation.dead) do dead[tostring(actor)] = true end
            for actor, targets in pairs(cjson.decode(raw)[1]) do
                local path = '$[' .. cjson.encode(actor) .. ']'
                command('JSON.SET', key, path, '[]')
                if not dead[actor] then
                    for _, target in ipairs(targets) do
                        if not dead[tostring(target)] then command('JSON.ARRAPPEND', key, path, cjson.encode(target)) end
                    end
                end
            end
        else
            local args = {operation.command, key}
            for _, value in ipairs(operation.args) do table.insert(args, value) end
            local result = command(unpack(args))
            -- JSON.SET/MERGE may report a missing path without a Redis error.
            if operation.required and (not result or
               (type(result) == 'table' and not result.ok and (#result == 0 or result[1] == false))) then
                error('missing JSON destination')
            end
        end
    end
    for _, key in ipairs(stages) do command('EXPIRE', key, request.ttl) end
end)
if not ok then cleanup(); return reject('staging failed: ' .. tostring(failure)) end

-- No JSON parsing, allocation-heavy commands, TTL writes or fallible mutation
-- remains after this point. Sources exist, destinations and ACLs were checked.
for i, key in ipairs(KEYS) do
    if redis.call('EXISTS', stages[i]) == 1 then
        redis.call('RENAME', stages[i], key)
    else
        redis.call('DEL', key)
    end
end
return 1
"""
