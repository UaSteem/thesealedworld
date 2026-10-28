/* Independent combat report model. No chat messages, channels or persistence. */
(function (global) {
    'use strict';
    const labels = { hit: 'попадание', miss: 'промах', dodged: 'уклонение', dodge: 'уклонение',
        parried: 'парирование', parry: 'парирование', blocked: 'блок', block: 'блок',
        death: 'смерть', heal: 'лечение', damage: 'урон', effect: 'эффект',
        attack: 'атака', exchange: 'размен', log: 'событие', tactical_transition: 'смена состояния',
        crit: 'критический удар', counter: 'контратака', offhand: 'вторая рука',
        normal: 'обычное', advantage: 'выгодное', far: 'дальняя', mid: 'средняя', close: 'ближняя',
        two_handed: 'двуручное оружие', shield: 'щит', dual_wield: 'два оружия', ranged: 'дальний бой' };
    Object.assign(labels, { skill_two_handed: 'двуручное оружие', skill_shield: 'щит', skill_shield_mastery: 'щит', skill_dual_wield: 'два оружия', skill_ranged: 'дальний бой', skill_ranged_combat: 'дальний бой',
        feint_dislodge: 'противник выбил финтом', feint_protect: 'финт защитил состояние', feint_entry: 'вход через финт',
        initiative_entry: 'преимущество инициативы', initiative_loss: 'потеря по инициативе', feint_assisted_entry: 'инициатива с помощью финта',
        initiative: 'инициатива', feint_position: 'смена дистанции через финт', initiative_position: 'смена дистанции по инициативе',
        apply: 'наложен', applied: 'наложен', remove: 'снят', removed: 'снят', expired: 'истёк' });
    function describe(line) {
        const data = line.data || {};
        const targets = line.target_results || data.target_results || [];
        if (targets.length) {
            // Each recipient owns its actual outcome and numbers. Never repeat
            // the aggregate as though every AoE target received that damage.
            return targets.map(target => describe({ ...line, ...target, data: { ...data, target_results: [] }, target_results: [], numbers: target.numbers || {}, resources: target.resources || [], effects: target.effects || [], result: target.result || {}, tactical_transitions: target.tactical_transitions || [], badges: target.badges || [], flags: target.flags || {}, outcome: target.outcome || null })).join(' ; ');
        }
        // Historical narrative is never parsed or displayed as a factual report.
        const source = line.source || data.source || {};
        const target = line.target || data.target || {};
        const action = line.action || data.action || {};
        const result = line.result || {};
        const ownerName = id => String(id) === String(source.id) ? source.name : String(id) === String(target.id) ? target.name : id || 'участник';
        const heading = (source.name || 'Источник неизвестен') + (target.name ? ' → ' + target.name : '') + ': ' + (action.label || labels[line.kind] || 'событие');
        const parts = [heading];
        if (line.outcome) parts.push(labels[line.outcome] || line.outcome);
        const numbers = line.numbers || data.numbers || {};
        const numberLabels = { damage: 'урон', healing: 'лечение', absorbed: 'поглощено', reflected: 'возвращено' };
        Object.entries(numbers).forEach(([key, value]) => { if (value != null && value !== 0) parts.push((numberLabels[key] || key) + ' ' + value); });
        const resources = line.resources?.length ? line.resources : result.resources || [];
        resources.forEach(r => parts.push(ownerName(r.actor_id) + ': ' + r.resource + ' ' + r.after + '/' + r.max + (r.delta == null ? '' : ' (' + (r.delta > 0 ? '+' : '') + r.delta + ')')));
        const effects = line.effects?.length ? line.effects : result.effects || [];
        effects.forEach(e => parts.push(ownerName(e.actor_id || e.owner) + ': ' + (e.tooltip || e.effect_id || 'эффект') + ' ' + (labels[e.action] || e.action || '') + (e.duration == null ? '' : ' (' + e.duration + ' разменов)')));
        (result.tokens || []).forEach(t => parts.push(ownerName(t.actor_id || t.owner) + ': ' + t.token + ' ' + t.amount));
        (line.badges || []).forEach(b => { if (['crit', 'counter', 'offhand', 'death'].includes(b.kind)) parts.push(labels[b.kind] || b.kind); });
        ['crit', 'counter', 'offhand', 'death'].forEach(key => { if (line.flags?.[key] && !(line.badges || []).some(b => b.kind === key)) parts.push(labels[key]); });
        (line.tactical_transitions || result.tactical_transitions || []).forEach(t => parts.push(ownerName(t.actor_id) + ': ' + (labels[t.style] || t.style) + ' ' + (labels[t.before] || t.before) + ' → ' + (labels[t.after] || t.after) + ' (' + (labels[t.reason] || t.reason) + ')' + (t.source_feint_id ? ' / финт: ' + (t.source_feint_label || (action.id === t.source_feint_id ? action.label || t.source_feint_id : t.source_feint_id)) : '') + (t.source_action_id && t.source_action_id !== t.source_feint_id ? ' / действие: ' + t.source_action_id : '')));
        return parts.join(' · ');
    }
    function create() {
        return {
            battle: { id: '', charId: '', active: false, visible: false, page: 1, pages: 1, turns: [], loading: false, error: '', unread: false, fingerprint: '' },
            _battleGeneration: 0,
            _battleController: null,
            _battleRoot: null,
            _battleText: describe,
            _battleInit() {
                const sync = () => this._battleSync(document.getElementById('game-session-root'));
                sync();
                this._battleObserver = new MutationObserver(sync);
                this._battleObserver.observe(document.getElementById('main-content') || document.body, { childList: true, subtree: true });
                this._battleTimer = setInterval(() => { if (this.battle.active) this._battleRefresh(); }, 3000);
                this._battleReconnect = () => { if (this.battle.visible) this._battleRefresh(); };
                window.addEventListener('online', this._battleReconnect);
                document.body.addEventListener('htmx:wsOpen', this._battleReconnect);
                this.$watch('chatTab', value => { if (value === 'battle') this.battle.unread = false; });
            },
            _battleSync(root) {
                if (!root || root === this._battleRoot) return;
                this._battleRoot = root;
                const charId = root.dataset.characterId || '';
                const id = root.dataset.battleId || '';
                const active = root.dataset.battleActive === 'true';
                if (this.battle.charId && charId !== this.battle.charId) {
                    this._battleGeneration++;
                    this._battleController?.abort();
                    this.battle = create().battle;
                    if (this.chatTab === 'battle') this.chatTab = 'global';
                }
                this.battle.charId = charId;
                if (id && id !== 'NO_DATA' && id !== this.battle.id) {
                    this._battleGeneration++;
                    this._battleController?.abort();
                    Object.assign(this.battle, { id, active, visible: true, page: 1, pages: 1, turns: [], fingerprint: '', unread: true, error: '' });
                }
                const wasActive = this.battle.active;
                this.battle.active = active && Boolean(this.battle.id);
                if (this.battle.visible && (active || wasActive || id === this.battle.id)) this._battleRefresh();
            },
            async _battleRefresh(page = this.battle.page) {
                if (!this.battle.visible) return;
                const generation = ++this._battleGeneration;
                this._battleController?.abort();
                const controller = new AbortController();
                this._battleController = controller;
                const id = this.battle.id;
                const charId = this.battle.charId;
                this.battle.loading = true;
                try {
                    const response = await fetch('/game/combat/report?' + new URLSearchParams({ char_id: charId, page }), { credentials: 'same-origin', cache: 'no-store', signal: controller.signal });
                    if (!response.ok) throw new Error('HTTP ' + response.status);
                    const report = await response.json();
                    if (generation !== this._battleGeneration || charId !== this.battle.charId || id !== this.battle.id || report.session_id !== id) return;
                    const log = this.$refs.battleScroll;
                    const samePage = this.battle.page === report.page;
                    const top = log?.scrollTop || 0;
                    const atBottom = !log || log.scrollHeight - log.clientHeight - top < 32;
                    const turns = report.turns?.length ? report.turns : [{ title: 'События', entries: report.entries || [] }];
                    const fingerprint = JSON.stringify(turns);
                    if (fingerprint !== this.battle.fingerprint && this.chatTab !== 'battle') this.battle.unread = true;
                    Object.assign(this.battle, { turns, page: report.page, pages: Math.max(1, Math.ceil((report.total_turns || report.total || 0) / report.page_size)), fingerprint, error: '' });
                    this.$nextTick(() => { if (log) log.scrollTop = samePage ? (atBottom ? log.scrollHeight : top) : 0; });
                } catch (error) {
                    if (generation === this._battleGeneration && error.name !== 'AbortError') this.battle.error = 'Журнал недоступен. Повторить загрузку.';
                } finally {
                    if (generation === this._battleGeneration) this.battle.loading = false;
                }
            },
            destroy() {
                this._battleGeneration++;
                this._battleController?.abort();
                this._battleObserver?.disconnect();
                clearInterval(this._battleTimer);
                window.removeEventListener('online', this._battleReconnect);
                document.body.removeEventListener('htmx:wsOpen', this._battleReconnect);
            }
        };
    }
    global.GameBattleFeed = { create, describe };
})(typeof window === 'undefined' ? globalThis : window);
