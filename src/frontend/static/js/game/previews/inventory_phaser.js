/* Isolated presentation study: no game API, storage, equipment or identify actions. */
(() => {
    'use strict';

    const host = document.getElementById('inventory-phaser-host');
    const status = document.getElementById('inventory-phaser-status');
    const source = document.getElementById('inventory-phaser-data');
    if (!host || !status || !source) return;
    const report = message => { status.textContent = message; };
    let data;
    try {
        data = JSON.parse(source.textContent);
        if (!Array.isArray(data.items) || !data.items.length) throw new Error('Нет предметов.');
        const ids = new Set();
        data.items.forEach(item => {
            if (!item.item_id || ids.has(item.item_id) || !item.name || !item.image_url) {
                throw new Error('Некорректный ID, название или адрес изображения.');
            }
            ids.add(item.item_id);
            if (!Array.isArray(item.details) || !Array.isArray(item.affixes)) {
                throw new Error('Не переданы параметры предмета.');
            }
        });
        if (data.columns !== 8 || data.rows !== 5) throw new Error('Ожидается рюкзак 8 × 5.');
        if (!window.Phaser) throw new Error('Локальный Phaser не загрузился.');
    } catch (error) {
        report(`Phaser preview: ${error.message}`);
        return;
    }

    const P = window.Phaser;
    const width = Math.max(340, Math.min(920, Math.floor(host.clientWidth || 920)));
    const height = 640;
    const colors = {
        bg: 0x0c1213, panel: 0x151d19, cell: 0x18201d, line: 0x34423a,
        gold: 0xc6ad7e, text: '#e4d4b8', dim: '#a7b2a3', green: '#c0d4ac',
    };
    const keyFor = item => `inventory-preview:${item.item_id}`;
    const clampCell = item => ({
        w: Math.max(1, Math.min(8, Math.floor(Number(item.grid_w) || 1))),
        h: Math.max(1, Math.min(5, Math.floor(Number(item.grid_h) || 1))),
    });

    class InventoryPreview extends P.Scene {
        constructor() {
            super('inventory-preview');
            this.failed = new Set();
            this.placements = [];
            this.cards = new Map();
            this.current = null;
            this.pinned = false;
        }

        preload() {
            report(`Phaser ${P.VERSION}: загрузка изображений 0 / ${data.items.length}…`);
            this.load.setCORS('anonymous');
            this.load.on('loaderror', file => {
                this.failed.add(file.key);
                this.updateStatus('Ошибка загрузки изображения');
            });
            data.items.forEach(item => this.load.image(keyFor(item), item.texture_url || item.image_url));
        }

        text(x, y, content, size = 14, color = colors.text, wrap = 0, world = false) {
            return this.add.text(x, y, String(content ?? ''), {
                fontFamily: world ? 'Georgia, serif' : 'Arial, sans-serif',
                fontSize: `${size}px`, color, lineSpacing: 3,
                ...(wrap ? { wordWrap: { width: wrap, useAdvancedWrap: true } } : {}),
            });
        }

        create() {
            this.game.canvas.setAttribute('aria-label', 'Интерактивный Phaser-инвентарь: шесть мечей, рюкзак и пояс. Стрелки выбирают меч, Escape закрывает карточку.');
            this.game.canvas.setAttribute('tabindex', '0');
            this.cameras.main.setBackgroundColor(colors.bg);
            this.overlay = width < 860;
            this.cell = Math.min(48, Math.floor((width - 32 - 7 * 5) / 8));
            this.gap = 5;
            this.bagW = this.cell * 8 + this.gap * 7;
            this.bagX = this.overlay ? Math.floor((width - this.bagW) / 2) : 24;
            this.bagY = 120;
            this.bagH = this.cell * 5 + this.gap * 4;

            const chrome = this.add.graphics();
            chrome.lineStyle(1, colors.line).lineBetween(24, 74, width - 24, 74);
            this.text(24, 24, 'Инвентарь', 27, colors.text, 0, true);
            this.text(width - 24, 35, 'PHASER · ПРИМЕР', 12, colors.dim).setOrigin(1, 0);
            this.text(this.bagX, 94, 'Рюкзак', 16);
            this.occupancy = this.text(this.bagX + this.bagW, 97, '', 12, colors.dim).setOrigin(1, 0);
            for (let row = 0; row < 5; row += 1) {
                for (let col = 0; col < 8; col += 1) {
                    chrome.fillStyle(colors.cell).fillRect(this.bagX + col * (this.cell + this.gap), this.bagY + row * (this.cell + this.gap), this.cell, this.cell);
                    chrome.lineStyle(1, colors.line).strokeRect(this.bagX + col * (this.cell + this.gap), this.bagY + row * (this.cell + this.gap), this.cell, this.cell);
                }
            }
            this.placeItems();
            this.occupancy.setText(`${this.usedCells} / 40 ячеек`);
            this.selectionBorder = this.add.graphics();
            this.text(this.bagX, this.bagY + this.bagH + 15, this.overlay ? 'Коснитесь меча, чтобы открыть карточку.' : 'Наведите на меч. Нажмите, чтобы закрепить.', 13, colors.dim, this.bagW);
            const beltY = this.bagY + this.bagH + 88;
            this.text(this.bagX, beltY - 29, 'Пояс', 16);
            this.text(this.bagX + this.bagW, beltY - 26, 'Быстрый доступ', 12, colors.dim).setOrigin(1, 0);
            for (let col = 0; col < 8; col += 1) {
                const x = this.bagX + col * (this.cell + this.gap);
                chrome.fillStyle(colors.cell).fillRect(x, beltY, this.cell, this.cell);
                chrome.lineStyle(1, 0x536158, 0.7).strokeRect(x, beltY, this.cell, this.cell);
                chrome.lineStyle(1, 0x647262, 0.3).strokeCircle(x + this.cell / 2, beltY + this.cell / 2, 5);
                this.text(x + 5, beltY + 4, col + 1, 11, colors.dim);
            }
            this.text(24, height - 38, 'Локальный пример. Игровые действия отключены.', 12, colors.dim, width - 48);

            this.input.on('pointermove', pointer => {
                if (this.pinned || this.overlay) return;
                const entry = this.itemAt(pointer);
                if (entry) this.showCard(entry.item, false);
                else if (!this.inCard(pointer)) this.hideCard();
            });
            this.input.on('pointerdown', pointer => {
                this.game.canvas.focus({ preventScroll: true });
                if (this.current && this.closeBounds.contains(pointer.x, pointer.y)) {
                    this.hideCard();
                    return;
                }
                // On narrow canvases the card covers the bag: its pixels own the input.
                if (this.overlay && this.inCard(pointer)) return;
                const entry = this.itemAt(pointer);
                if (entry) this.showCard(entry.item, true);
                else if (!this.inCard(pointer)) this.hideCard();
            });
            this.input.on('gameout', () => { if (!this.pinned) this.hideCard(); });
            this.input.keyboard.on('keydown', event => {
                if (document.activeElement !== this.game.canvas) return;
                if (event.key === 'Escape') this.hideCard();
                if (event.key === 'ArrowRight' || event.key === 'ArrowLeft') {
                    event.preventDefault();
                    const index = this.placements.findIndex(entry => entry.item === this.current);
                    const step = event.key === 'ArrowRight' ? 1 : -1;
                    const next = index < 0 ? (step > 0 ? 0 : this.placements.length - 1)
                        : (index + step + this.placements.length) % this.placements.length;
                    if (this.placements[next]) this.showCard(this.placements[next].item, true);
                }
            });
            const initial = data.items.find(item => item.item_id === data.selected_id);
            if (initial) this.showCard(initial, true);
            else this.updateStatus();
        }

        placeItems() {
            const occupied = Array.from({ length: 5 }, () => Array(8).fill(false));
            this.usedCells = 0;
            data.items.forEach(item => {
                const size = clampCell(item);
                let spot = null;
                for (let row = 0; row <= 5 - size.h && !spot; row += 1) {
                    for (let col = 0; col <= 8 - size.w; col += 1) {
                        const fits = Array.from({ length: size.h }, (_, dy) =>
                            occupied[row + dy].slice(col, col + size.w).every(value => !value)).every(Boolean);
                        if (fits) { spot = { row, col }; break; }
                    }
                }
                if (!spot) throw new Error(`Предмет не помещается в preview: ${item.name}`);
                for (let dy = 0; dy < size.h; dy += 1) {
                    for (let dx = 0; dx < size.w; dx += 1) occupied[spot.row + dy][spot.col + dx] = true;
                }
                this.usedCells += size.w * size.h;
                const x = this.bagX + spot.col * (this.cell + this.gap);
                const y = this.bagY + spot.row * (this.cell + this.gap);
                const w = size.w * this.cell + (size.w - 1) * this.gap;
                const h = size.h * this.cell + (size.h - 1) * this.gap;
                const tile = this.add.rectangle(x, y, w, h, 0x27352c, 0.85).setOrigin(0).setStrokeStyle(1, 0x65735e);
                tile.setInteractive({ useHandCursor: true });
                this.placements.push({ item, rect: new P.Geom.Rectangle(x, y, w, h) });
                this.art(item, x + w / 2, y + (h - 19) / 2 + 5, w - 8, h - 27);
                this.text(x + w / 2, y + h - 17, `T${item.tier}`, 11, colors.green).setOrigin(0.5, 0);
            });
        }

        art(item, x, y, w, h) {
            if (!this.textures.exists(keyFor(item)) || this.failed.has(keyFor(item))) {
                return this.text(x, y, 'Нет\nизображения', 11, '#d5ab91', w).setOrigin(0.5);
            }
            const image = this.add.image(x, y, keyFor(item));
            image.setScale(Math.min(w / image.width, h / image.height));
            return image;
        }

        itemAt(pointer) { return this.placements.find(entry => entry.rect.contains(pointer.x, pointer.y)); }
        inCard(pointer) { return Boolean(this.current && this.cardBounds.contains(pointer.x, pointer.y)); }

        buildCard(item) {
            const cardW = this.overlay ? Math.min(406, width - 24) : width - this.bagX - this.bagW - 48;
            const x = this.overlay ? (width - cardW) / 2 : this.bagX + this.bagW + 24;
            const y = 86;
            const card = this.add.container(x, y).setDepth(10);
            const background = this.add.graphics();
            card.add(background);
            const addText = (tx, ty, value, size, color, wrap, world) => {
                const object = this.text(tx, ty, value, size, color, wrap, world);
                card.add(object);
                return object;
            };
            const inner = cardW - 36;
            let cursor = 17;
            const title = addText(18, cursor, item.name, 23, colors.text, inner - 24, true);
            addText(cardW - 26, 12, '×', 25, colors.dim).setOrigin(0.5, 0);
            cursor += title.height + 8;
            addText(18, cursor, `T${item.tier}  ·  ${item.rarity_label}`, 13, colors.green, inner);
            cursor += 29;
            const mainTop = cursor;
            const artW = cardW < 340 ? 64 : 76;
            const statX = 18 + artW + 14;
            const statW = cardW - 18 - statX;
            const row = (line, rowX, rowW, color = colors.dim) => {
                const value = addText(rowX + rowW, cursor + 1, line.value, 14, color === colors.green ? color : colors.text).setOrigin(1, 0);
                const label = addText(rowX, cursor, line.label, 13, color, Math.max(75, rowW - value.width - 13));
                cursor += Math.max(label.height, value.height) + 8;
            };
            item.details.forEach(line => row(line, statX, statW));
            const mainH = Math.max(144, cursor - mainTop);
            const image = this.art(item, 18 + artW / 2, mainTop + mainH / 2, artW, 144);
            card.add(image);
            cursor = mainTop + mainH + 13;
            const dividers = [cursor - 4];
            if (item.affixes.length) {
                addText(18, cursor + 5, 'СВОЙСТВА', 11, colors.dim);
                cursor += 28;
                item.affixes.forEach(line => row(line, 18, inner, colors.green));
                dividers.push(cursor + 2);
                cursor += 15;
            } else cursor += 10;
            const description = addText(18, cursor, item.description, 15, '#c7c4b1', inner, true);
            cursor += description.height + 12;
            if (!item.is_identified) {
                const unknown = addText(18, cursor, '◇ Происхождение пока не определено.', 12, colors.dim, inner);
                cursor += unknown.height + 12;
            }
            dividers.push(cursor);
            cursor += 12;
            const buttonW = (inner - 10) / 2;
            ['Надеть', 'Определить'].forEach((label, index) => {
                const bx = 18 + index * (buttonW + 10);
                addText(bx + buttonW / 2, cursor + 8, label, 13, '#929580').setOrigin(0.5, 0);
            });
            cursor += 45;
            addText(18, cursor, '× / Esc — закрыть · действия отключены', 11, colors.dim, inner);
            cursor += 29;
            // Background is drawn first in the display list; controls stay visible above it.
            background.fillStyle(colors.panel, 1).fillRect(0, 0, cardW, cursor);
            background.lineStyle(1, colors.gold, 0.7).strokeRect(0, 0, cardW, cursor);
            dividers.forEach(dy => background.lineStyle(1, colors.gold, 0.2).lineBetween(18, dy, cardW - 18, dy));
            // Draw disabled action surfaces after the panel without depending on renderer internals.
            const actionY = cursor - 74;
            for (let index = 0; index < 2; index += 1) {
                const bx = 18 + index * (buttonW + 10);
                background.fillStyle(0x202820).fillRect(bx, actionY, buttonW, 32);
                background.lineStyle(1, 0x5c604a).strokeRect(bx, actionY, buttonW, 32);
            }
            return { container: card, bounds: new P.Geom.Rectangle(x, y, cardW, cursor), close: new P.Geom.Rectangle(x + cardW - 45, y + 5, 38, 38) };
        }

        showCard(item, pinned) {
            if (this.current === item && this.pinned === pinned) return;
            if (this.current) this.cards.get(this.current.item_id).container.setVisible(false);
            if (!this.cards.has(item.item_id)) this.cards.set(item.item_id, this.buildCard(item));
            const card = this.cards.get(item.item_id);
            card.container.setVisible(true);
            this.cardBounds = card.bounds;
            this.closeBounds = card.close;
            this.current = item;
            this.pinned = pinned;
            const placement = this.placements.find(entry => entry.item === item);
            this.selectionBorder.clear().lineStyle(2, colors.gold).strokeRectShape(placement.rect);
            this.updateStatus();
        }

        hideCard() {
            if (!this.current) return;
            this.cards.get(this.current.item_id).container.setVisible(false);
            this.current = null;
            this.pinned = false;
            this.selectionBorder.clear();
            this.updateStatus();
        }

        updateStatus(prefix = '') {
            const loaded = data.items.filter(item => this.textures.exists(keyFor(item)) && !this.failed.has(keyFor(item))).length;
            const selected = this.current ? `${this.pinned ? 'Выбран' : 'Просмотр'}: ${this.current.name} (T${this.current.tier}).` : 'Предмет не выбран.';
            const error = this.failed.size ? ` Ошибка загрузки ${this.failed.size} изображений: проверьте URL и CORS; заменяющие рисунки не используются.` : '';
            const renderer = this.game.renderer ? (this.game.renderer.type === P.WEBGL ? 'WebGL' : 'Canvas') : 'загрузка';
            report(`${prefix ? `${prefix}. ` : ''}Phaser ${P.VERSION} · ${renderer} · изображения ${loaded}/${data.items.length} · ${width}×${height}. ${selected}${error}`);
        }
    }

    try {
        new P.Game({
            type: P.AUTO, parent: host, width, height, backgroundColor: colors.bg,
            scale: { mode: P.Scale.FIT, autoCenter: P.Scale.CENTER_BOTH, width, height },
            input: { keyboard: { capture: [] } },
            render: { antialias: true, pixelArt: false },
            scene: InventoryPreview,
            callbacks: { postBoot: game => { game.canvas.style.display = 'block'; } },
        });
    } catch (error) {
        report(`Phaser preview: ошибка запуска: ${error.message}`);
    }
})();
