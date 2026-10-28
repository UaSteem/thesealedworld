/* Texture leases belong to scenes/components, never to gameplay state. */
export function validateCatalog(value) {
    if (value?.schema_version !== 1 || !Array.isArray(value.assets)) throw new Error('Invalid asset catalog');
    const keys = new Set();
    for (const entry of value.assets) {
        if (!entry.key || keys.has(entry.key) || !entry.group || !/^\/static\/images\/game-client\/[a-zA-Z0-9_.\/-]+\.png$/.test(entry.url)
            || entry.url.includes('..') || !Number.isInteger(entry.width) || entry.width < 1
            || !Number.isInteger(entry.height) || entry.height < 1 || !Number.isInteger(entry.bytes) || entry.bytes < 1
            || !/^[a-f0-9]{64}$/.test(entry.sha256)) throw new Error('Invalid asset entry');
        keys.add(entry.key);
        for (const rect of Object.values(entry.frames || {})) {
            if (!Array.isArray(rect) || rect.length !== 4 || !rect.every(Number.isInteger)
                || rect[0] < 0 || rect[1] < 0 || rect[2] < 1 || rect[3] < 1
                || rect[0] + rect[2] > entry.width || rect[1] + rect[3] > entry.height) throw new Error('Invalid asset frame');
        }
    }
    return value;
}

async function browserImage(entry) {
    const response = await fetch(entry.url);
    if (!response.ok) throw new Error(`Asset ${entry.key}: HTTP ${response.status}`);
    const url = URL.createObjectURL(await response.blob());
    try {
        const image = new Image();
        image.src = url;
        await image.decode();
        return image;
    } finally { URL.revokeObjectURL(url); }
}

export function createAssetManager({textures, catalog, catalogURL, loadImage = browserImage}) {
    const records = new Map();
    let manifest = catalog ? Promise.resolve(validateCatalog(catalog)) : null, disposed = false;
    let downloads = 0, transferredBytes = 0, decodeMilliseconds = 0;
    function getCatalog() {
        if (!manifest) manifest = fetch(catalogURL).then(response => {
            if (!response.ok) throw new Error(`Asset catalog: HTTP ${response.status}`);
            return response.json();
        }).then(validateCatalog).catch(error => {manifest = null; throw error;});
        return manifest;
    }
    function cleanup(record) {
        if (record.refs || !record.settled) return;
        if (record.ready && textures.exists(record.entry.key)) textures.remove(record.entry.key);
        record.image?.close?.(); record.image = null;
        if (records.get(record.entry.key) === record) records.delete(record.entry.key);
    }
    function retain(entry) {
        let record = records.get(entry.key);
        if (!record) {
            if (textures.exists(entry.key)) throw new Error(`Texture key already owned: ${entry.key}`);
            record = {entry, refs: 0, ready: false, settled: false, image: null};
            records.set(entry.key, record);
            record.promise = (async () => {
                const start = performance.now();
                const image = await loadImage(entry);
                record.image = image;
                if (disposed) throw new Error('Asset manager disposed');
                if ((image.naturalWidth || image.width) !== entry.width || (image.naturalHeight || image.height) !== entry.height) {
                    throw new Error(`Asset dimensions mismatch: ${entry.key}`);
                }
                const texture = textures.addImage(entry.key, image);
                record.ready = Boolean(texture);
                if (!texture) throw new Error(`Cannot create texture: ${entry.key}`);
                for (const [name, rect] of Object.entries(entry.frames || {})) if (!texture.has(name)) texture.add(name, 0, ...rect);
                downloads++; transferredBytes += entry.bytes;
                decodeMilliseconds += performance.now() - start;
            })().catch(error => {
                if (record.ready && textures.exists(entry.key)) textures.remove(entry.key);
                record.ready = false; record.image?.close?.(); record.image = null;
                throw error;
            }).finally(() => {record.settled = true; cleanup(record);});
            // Every pending record is observed even if a later retain fails.
            record.promise.catch(() => {});
        }
        record.refs++;
        return record;
    }
    function release(recordsToRelease) {
        for (const record of recordsToRelease) {
            record.refs = Math.max(0, record.refs - 1);
            cleanup(record);
        }
    }
    return {
        async acquire(group) {
            if (disposed) throw new Error('Asset manager disposed');
            const value = await getCatalog();
            if (disposed) throw new Error('Asset manager disposed');
            const entries = value.assets.filter(entry => entry.group === group);
            if (!entries.length) throw new Error(`Unknown asset group: ${group}`);
            for (const entry of entries) if (!records.has(entry.key) && textures.exists(entry.key)) throw new Error(`Texture key already owned: ${entry.key}`);
            const held = [];
            try {
                for (const entry of entries) held.push(retain(entry));
                const results = await Promise.allSettled(held.map(record => record.promise));
                const failed = results.find(result => result.status === 'rejected');
                if (failed) throw failed.reason;
                if (disposed) throw new Error('Asset manager disposed');
                let released = false;
                return {release() {if (!released) {released = true; release(held);}}};
            } catch (error) {release(held); throw error;}
        },
        inspect() {
            return {residentBytes: [...records.values()].filter(record => record.ready).reduce((sum, record) => sum + record.entry.width * record.entry.height * 4, 0),
                textures: records.size, downloads, transferredBytes, decodeMilliseconds};
        },
        dispose() {disposed = true; for (const record of records.values()) {record.refs = 0; cleanup(record);}},
    };
}
