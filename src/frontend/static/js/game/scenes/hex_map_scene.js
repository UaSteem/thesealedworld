class HexMapScene extends Phaser.Scene {
    constructor() {
        super({ key: 'HexMapScene' });
        this.tiles = {};
        this.backgroundLayer = null;
        this.playerToken = null;
        this.currentCoord = { x: 0, y: 0 };
        this.width = 10;
        this.height = 10;
        // The images are 512x512 but the drawn hex has a bounding box of 368x425.
        this.hexVisibleWidth = 368;
        this.hexVisibleHeight = 425;
        this.tileScale = 0.78;
        this.initialZoom = 1.42;
        this.minZoom = 0.16;
        this.maxZoom = 2.0;
        this.backgroundTileScale = 1;
        this.hexGap = 8;
        this.colSpacing = this.hexVisibleWidth * this.tileScale + this.hexGap;
        this.rowSpacing = this.hexVisibleHeight * this.tileScale * 0.75 + this.hexGap;
        this.startX = 50;
        this.startY = 84;
        this.isLocked = false;
        this.showAllMap = false;
        this.clearedCombatTileIndex = 402;
    }

    init(data) {
        const parent = document.getElementById("phaser-hex-map");
        if (parent) {
            this.theme = parent.getAttribute("data-rift-theme") || "";
            this.showAllMap = parent.getAttribute("data-show-all-map") === "true";
        } else {
            this.theme = "";
        }

        if (data && data.rift) {
            this.riftState = data.rift;
            this.instanceId = data.instanceId;
        } else {
            if (parent) {
                this.riftState = JSON.parse(parent.getAttribute("data-rift-state"));
                this.instanceId = parent.getAttribute("data-instance-id");
            }
        }
        if (this.riftState) {
            if (this.riftState.theme) {
                this.theme = this.riftState.theme;
            }
            this.currentCoord = { x: this.riftState.current_x, y: this.riftState.current_y };
            if (this.riftState.combat_prompt) {
                this.isLocked = true;
            }
        }
    }

    preload() {
        const version = Date.now();
        for (const node of this.riftState.nodes) {
            if (node.content_slot === 'void') continue;
            const key = this.getTileTextureKey(node);
            const url = this.getTileAssetUrl(node);
            if (url && !this.textures.exists(key)) {
                this.load.image(key, `${url}?v=${version}`);
            }
        }
        // Load default avatar for player standee
        this.load.image('player_avatar', '/static/images/avatars/silhouette_m.webp');
        this.load.image('void_interworld_bg', `/static/images/rift/void_interworld_bg_v3.webp?v=${version}`);
        this.load.image(this.getFogPlanTextureKey(), `${this.getFogPlanTileAssetUrl()}?v=${version}`);

        // Load portals spritesheet
        this.load.spritesheet('portal_sprites', `/static/images/rift/portals_spritesheet.png?v=${version}`, {
            frameWidth: 128,
            frameHeight: 128
        });

        // Load crystals spritesheet
        this.load.spritesheet('crystal_sprites', `/static/images/rift/crystals_spritesheet.png?v=${version}`, {
            frameWidth: 128,
            frameHeight: 128
        });
    }

    create() {
        // Register animations for the 7 tiers of portals
        for (let t = 1; t <= 7; t++) {
            const startFrame = (t - 1) * 8;
            this.anims.create({
                key: `portal_tier_${t}`,
                frames: this.anims.generateFrameNumbers('portal_sprites', { start: startFrame, end: startFrame + 7 }),
                frameRate: 6,
                repeat: -1
            });
        }

        // Register animations for the 7 tiers of crystals
        for (let t = 1; t <= 7; t++) {
            const startFrame = (t - 1) * 8;
            this.anims.create({
                key: `crystal_tier_${t}`,
                frames: this.anims.generateFrameNumbers('crystal_sprites', { start: startFrame, end: startFrame + 7 }),
                frameRate: 6,
                repeat: -1
            });
        }

        this.createBackgroundLayer();
        this.drawMap();
        this.createPlayerToken();

        // 1. Center camera on player token initially
        const startPixels = this.getHexPixels(this.currentCoord.x, this.currentCoord.y);
        this.cameras.main.setZoom(this.initialZoom);
        this.cameras.main.centerOn(startPixels.x, startPixels.y);

        // 2. Drag to Pan map logic
        this.isDragging = false;
        this.hasDragged = false;
        this.dragStart = { x: 0, y: 0 };

        this.input.on('pointerdown', (pointer) => {
            this.isDragging = true;
            this.dragStart = { x: pointer.x, y: pointer.y };
        });

        this.input.on('pointermove', (pointer) => {
            if (!this.isDragging || !pointer.isDown) return;
            const dx = pointer.x - this.dragStart.x;
            const dy = pointer.y - this.dragStart.y;
            // If moved more than 5px, treat as drag and scroll camera
            if (Math.abs(dx) > 5 || Math.abs(dy) > 5) {
                this.cameras.main.scrollX -= (pointer.x - pointer.prevPosition.x) / this.cameras.main.zoom;
                this.cameras.main.scrollY -= (pointer.y - pointer.prevPosition.y) / this.cameras.main.zoom;
                this.hasDragged = true;
            }
        });

        this.input.on('pointerup', () => {
            this.isDragging = false;
            // Reset drag flag shortly after to allow pointerup handlers to check it
            this.time.delayedCall(10, () => {
                this.hasDragged = false;
            });
        });

        // 3. Mouse Wheel to Zoom logic
        this.input.on('wheel', (pointer, gameObjects, deltaX, deltaY, deltaZ) => {
            const zoomFactor = 0.05;
            let newZoom = this.cameras.main.zoom - deltaY * zoomFactor * 0.01;
            newZoom = Phaser.Math.Clamp(newZoom, this.minZoom, this.maxZoom);
            this.cameras.main.setZoom(newZoom);
        });

        // Expose update state function to window so the page can call it on HTMX response
        window.updatePhaserRiftState = (newState) => {
            this.updateRiftState(newState);
        };
        window.setPhaserShowAllMap = (value) => {
            this.setShowAllMap(value);
        };
        window.fitPhaserHexMap = () => {
            this.fitMapToViewport();
        };
    }

    setLocked(value) {
        this.isLocked = value;
        this.drawMap();
    }

    setShowAllMap(value) {
        this.showAllMap = Boolean(value);
        this.drawMap();
    }

    getMapBounds() {
        const coords = this.riftState && this.riftState.nodes ? this.riftState.nodes : [];
        if (coords.length === 0) {
            return { centerX: 0, centerY: 0, width: 1, height: 1 };
        }

        let minX = Number.POSITIVE_INFINITY;
        let minY = Number.POSITIVE_INFINITY;
        let maxX = Number.NEGATIVE_INFINITY;
        let maxY = Number.NEGATIVE_INFINITY;
        const halfWidth = (this.hexVisibleWidth * this.tileScale) / 2;
        const halfHeight = (this.hexVisibleHeight * this.tileScale) / 2;

        coords.forEach((node) => {
            const pixels = this.getHexPixels(node.x, node.y);
            minX = Math.min(minX, pixels.x - halfWidth);
            minY = Math.min(minY, pixels.y - halfHeight);
            maxX = Math.max(maxX, pixels.x + halfWidth);
            maxY = Math.max(maxY, pixels.y + halfHeight);
        });

        return {
            centerX: (minX + maxX) / 2,
            centerY: (minY + maxY) / 2,
            width: Math.max(1, maxX - minX),
            height: Math.max(1, maxY - minY)
        };
    }

    fitMapToViewport() {
        const bounds = this.getMapBounds();
        const padding = 56;
        const zoomX = this.cameras.main.width / (bounds.width + padding * 2);
        const zoomY = this.cameras.main.height / (bounds.height + padding * 2);
        const zoom = Phaser.Math.Clamp(Math.min(zoomX, zoomY), this.minZoom, this.maxZoom);

        this.cameras.main.setZoom(zoom);
        this.cameras.main.centerOn(bounds.centerX, bounds.centerY);
    }

    update() {
        const currentNode = (this.riftState && this.riftState.nodes) ? this.riftState.nodes.find(n => n.x === this.riftState.current_x && n.y === this.riftState.current_y) : null;
        const isClearedFinish = currentNode && this.riftState.current_x === this.riftState.finish_x && this.riftState.current_y === this.riftState.finish_y && currentNode.tile_index === this.clearedCombatTileIndex && this.riftState.floor < 3;

        if (this.playerToken && (this.isLocked || isClearedFinish)) {
            const cam = this.cameras.main;

            // Map player standee scene coordinates to viewport screen space using worldView bounds
            const px = (this.playerToken.x - cam.worldView.x) * cam.zoom;
            const py = (this.playerToken.y - cam.worldView.y) * cam.zoom;

            const bubble = document.getElementById("hex-floating-actions");
            if (bubble) {
                bubble.style.display = "flex";
                bubble.style.left = `${px}px`;
                bubble.style.top = `${py - 120 * cam.zoom}px`; // Moved up since scale is larger
                bubble.style.transform = `translate(-50%, -100%) scale(${cam.zoom})`;
            }
        } else {
            const bubble = document.getElementById("hex-floating-actions");
            if (bubble) {
                bubble.style.display = "none";
            }
        }
    }

    createBackgroundLayer() {
        this.backgroundLayer = this.add.tileSprite(-2400, -1800, 7200, 5200, 'void_interworld_bg');
        this.backgroundLayer.setOrigin(0, 0);
        this.backgroundLayer.setScrollFactor(0.12);
        this.backgroundLayer.setDepth(-1000);
        this.backgroundLayer.setAlpha(0.72);
        this.backgroundLayer.setTileScale(this.backgroundTileScale, this.backgroundTileScale);
    }

    // Convert grid (x, y) to screen pixels (cx, cy)
    getHexPixels(x, y) {
        let cx = this.startX + x * this.colSpacing;
        if (y % 2 !== 0) {
            cx += this.colSpacing / 2;
        }
        let cy = this.startY + y * this.rowSpacing;
        return { x: cx, y: cy };
    }

    getMappedTileIndex(index) {
        if (this.theme === 'glass_eden') {
            const mapping = {
                1: 50,   // Entrance -> Star Well (Tile 50)
                2: 2,    // Cavern -> Tile 2 (Sparse crystal weeds)
                3: 64,   // Rift Heart -> Resonant Crystal (Tile 64)
                4: 11,   // Cavern -> Tile 11 (Small crystal mound)
                5: 57,   // Crystal Druza -> Tile 57 (Standing Stone)
                6: 29,   // Wall -> Tile 29 (Crystal spires)
                7: 28,   // Cracked plate -> Tile 28 (Cracked crystal platform)
                8: 1,    // Cavern Floor -> Tile 1 (Pure quartz sand)
                9: 47,   // Runes -> Tile 47 (Shaman Focus)
                10: 48,  // Camp -> Tile 48 (Scavenger Camp)
                11: 32,  // Wall -> Tile 32 (Basalt wall)
                12: 33,  // Fence -> Tile 33 (Spiky crystal fence)
                13: 15,  // Cavern Floor -> Tile 15 (Straight path)
                14: 16,  // Cavern Floor -> Tile 16 (Winding trail)
                15: 52,  // Chest -> Tile 52 (Void Chest)
                16: 34,  // Wall -> Tile 34 (Crystallized vines)
                17: 47,  // Runes -> Tile 47 (Shaman Focus)
                18: 18,  // Path -> Tile 18 (Crossroad)
                19: 19,  // Path -> Tile 19 (Trail end)
                20: 20,  // Path -> Tile 20 (Clearing path)
                21: 21,  // Path -> Tile 21 (Precautionary trail)
                22: 22,  // Path -> Tile 22 (Stepping stones)
                23: 23,  // Path -> Tile 23 (Wooden bridge)
                24: 24,  // Path -> Tile 24 (Silica arch)
                25: 16,  // Void -> Tile 16 (Pure Void)
            };
            return mapping[index] || index;
        }
        return index;
    }

    getTileTextureKey(node) {
        return `rift_tile_${node.asset_path || node.tile_index}`;
    }

    getFogPlanTextureKey() {
        return `rift_tile_fog_plan_${this.theme || 'default'}`;
    }

    getFogPlanTileAssetUrl() {
        const folder = this.theme ? `${this.theme}/tiles` : 'hexes';
        return `/static/images/rift/${folder}/tile_503.png`;
    }

    getTileAssetUrl(node) {
        if (node.asset_path) {
            if (node.asset_path.startsWith('http://') || node.asset_path.startsWith('https://') || node.asset_path.startsWith('/')) {
                return node.asset_path;
            }
            const folder = this.theme ? `${this.theme}` : 'hexes';
            return `/static/images/rift/${folder}/${node.asset_path}`;
        }
        const tileIndex = this.getMappedTileIndex(node.tile_index);
        const paddedI = tileIndex.toString().padStart(2, '0');
        const folder = this.theme ? `${this.theme}/tiles` : 'hexes';
        return `/static/images/rift/${folder}/tile_${paddedI}.png`;
    }

    drawMap() {
        const visitedCoords = new Set(this.riftState.visited.map(c => `${c[0]}:${c[1]}`));
        const revealedCoords = new Set(this.riftState.revealed.map(c => `${c[0]}:${c[1]}`));

        this.riftState.nodes.forEach(node => {
            const key = `${node.x}:${node.y}`;
            if (node.content_slot === 'void') {
                this.tiles[key]?.setVisible(false);
                return;
            }
            const pixels = this.getHexPixels(node.x, node.y);
            const textureKey = this.getTileTextureKey(node);
            const isDiscovered = this.showAllMap || visitedCoords.has(key) || revealedCoords.has(key);
            const displayTextureKey = node.is_walkable && !isDiscovered ? this.getFogPlanTextureKey() : textureKey;

            if (!this.textures.exists(textureKey) || !this.textures.exists(displayTextureKey)) {
                return;
            }

            let sprite;
            if (this.tiles[key]) {
                sprite = this.tiles[key];
                const keepsDrift = node.content_slot === 'void_decor' && sprite.getData('voidDecorDriftKey') === key;
                if (!keepsDrift) {
                    sprite.setPosition(pixels.x, pixels.y);
                }
            } else {
                sprite = this.add.sprite(pixels.x, pixels.y, textureKey);
                sprite.setScale(this.tileScale);
                sprite.setOrigin(0.5, 0.5);
                this.tiles[key] = sprite;
            }

            // Store node data on sprite
            sprite.setData('nodeData', node);

            // Dev harness fog: show the whole generated labyrinth as a gray plan,
            // while only visited/revealed nodes get full readable lighting.
            const isVisible = this.showAllMap || isDiscovered || node.is_walkable || node.content_slot === 'void_decor';

            sprite.setTexture(displayTextureKey);

            if (!isVisible) {
                sprite.setVisible(false);
            } else if (!node.is_walkable) {
                sprite.setVisible(true);
                sprite.setAlpha(0.82);
                sprite.setTint(0xc4ccdd);
            } else {
                sprite.setVisible(true);
                if (visitedCoords.has(key)) {
                    sprite.setAlpha(1.0);
                    sprite.setTint(0xffffff);
                } else if (revealedCoords.has(key)) {
                    sprite.setAlpha(0.6);
                    sprite.setTint(0x9999bb);  // Blue-gray tint for fog of war
                } else {
                    sprite.setAlpha(0.36);
                    sprite.setTint(0x777a88);
                }
            }

            this.updateVoidDecorDrift(sprite, node, pixels, isVisible);

            // Update interactivity
            this.updateTileInteractivity(sprite);

            // Render Portal overlay on starting hex
            const portalKey = `portal_${node.x}:${node.y}`;
            if (node.x === this.riftState.start_x && node.y === this.riftState.start_y) {
                if (isVisible) {
                    let portalSprite = this.tiles[portalKey];
                    if (!portalSprite) {
                        portalSprite = this.add.sprite(pixels.x, pixels.y, 'portal_sprites');
                        portalSprite.setScale(1.15); // Scale 128px frame
                        portalSprite.setOrigin(0.5, 0.5);
                        portalSprite.setDepth(10);
                        portalSprite.setBlendMode(Phaser.BlendModes.ADD);
                        this.tiles[portalKey] = portalSprite;
                    }
                    const tier = this.riftState.tier || 7;
                    portalSprite.play(`portal_tier_${tier}`, true);
                    portalSprite.setVisible(true);
                } else {
                    if (this.tiles[portalKey]) this.tiles[portalKey].setVisible(false);
                }
            } else {
                if (this.tiles[portalKey]) {
                    this.tiles[portalKey].setVisible(false);
                }
            }

            // Render Crystal overlay only when backend marks a rift-heart node.
            const crystalKey = `crystal_${node.x}:${node.y}`;
            if (node.overlay_key === "rift_crystal") {
                if (isDiscovered) {
                    let crystalSprite = this.tiles[crystalKey];
                    if (!crystalSprite) {
                        crystalSprite = this.add.sprite(pixels.x, pixels.y, 'crystal_sprites');
                        crystalSprite.setScale(1.15);
                        crystalSprite.setOrigin(0.5, 0.5);
                        crystalSprite.setDepth(10);
                        crystalSprite.setBlendMode(Phaser.BlendModes.ADD);
                        this.tiles[crystalKey] = crystalSprite;
                    }
                    const tier = this.riftState.tier || 7;
                    crystalSprite.play(`crystal_tier_${tier}`, true);
                    crystalSprite.setVisible(true);
                } else {
                    if (this.tiles[crystalKey]) this.tiles[crystalKey].setVisible(false);
                }
            } else {
                if (this.tiles[crystalKey]) {
                    this.tiles[crystalKey].setVisible(false);
                }
            }
        });
    }

    updateVoidDecorDrift(sprite, node, pixels, isVisible) {
        if (node.content_slot !== 'void_decor' || !isVisible) {
            this.stopVoidDecorDrift(sprite, pixels);
            return;
        }

        const driftKey = `${node.x}:${node.y}`;
        if (sprite.getData('voidDecorDriftKey') === driftKey) {
            return;
        }

        this.stopVoidDecorDrift(sprite, pixels);

        const phase = ((node.x * 37 + node.y * 53) % 100) / 100;
        const xAmplitude = 8 + ((node.x + node.y) % 8);
        const yAmplitude = 8 + ((node.x * 2 + node.y) % 8);
        const duration = 6800 + ((node.x * 211 + node.y * 127) % 3200);
        const offsetX = Math.sin(phase * Math.PI * 2) * xAmplitude;
        const offsetY = Math.cos(phase * Math.PI * 2) * yAmplitude;

        sprite.setData('voidDecorDriftKey', driftKey);
        sprite.setPosition(pixels.x - offsetX, pixels.y - offsetY);
        this.tweens.add({
            targets: sprite,
            x: pixels.x + offsetX,
            y: pixels.y + offsetY,
            duration,
            delay: Math.round(phase * duration),
            yoyo: true,
            repeat: -1,
            ease: 'Sine.easeInOut'
        });
    }

    stopVoidDecorDrift(sprite, pixels) {
        if (!sprite.getData('voidDecorDriftKey')) {
            return;
        }

        this.tweens.killTweensOf(sprite);
        sprite.setData('voidDecorDriftKey', null);
        sprite.setPosition(pixels.x, pixels.y);
    }

    updateTileInteractivity(sprite) {
        const node = sprite.getData('nodeData');
        const key = `${node.x}:${node.y}`;

        const visitedCoords = new Set(this.riftState.visited.map(c => `${c[0]}:${c[1]}`));
        const revealedCoords = new Set(this.riftState.revealed.map(c => `${c[0]}:${c[1]}`));
        const isRevealed = revealedCoords.has(key);

        // Check if adjacent to current node
        const isAdjacent = this.isAdjacent(this.currentCoord.x, this.currentCoord.y, node.x, node.y);
        const isClickable = !this.isLocked && isRevealed && isAdjacent && node.is_walkable;

        if (isClickable) {
            sprite.setInteractive({ useHandCursor: true });
            sprite.removeAllListeners('pointerdown');
            sprite.removeAllListeners('pointerover');
            sprite.removeAllListeners('pointerout');

            sprite.on('pointerdown', () => {
                this.handleTileClick(node.x, node.y);
            });

            sprite.on('pointerover', () => {
                sprite.setTint(0xffd700); // Gold highlight
            });

            sprite.on('pointerout', () => {
                sprite.setScale(this.tileScale);
                if (visitedCoords.has(key)) {
                    sprite.setTint(0xffffff);
                } else {
                    sprite.setTint(0x9999bb);
                }
            });

            sprite.setScale(this.tileScale);
        } else {
            sprite.disableInteractive();
            sprite.removeAllListeners('pointerdown');
            sprite.setScale(this.tileScale);
        }
    }

    isAdjacent(x1, y1, x2, y2) {
        const offsets = y1 % 2 === 0
            ? [(-1, -1), (0, -1), (-1, 0), (1, 0), (-1, 1), (0, 1)]
            : [(0, -1), (1, -1), (-1, 0), (1, 0), (0, 1), (1, 1)];

        if (y1 % 2 === 0) {
            return (
                (x2 === x1 - 1 && y2 === y1 - 1) ||
                (x2 === x1 && y2 === y1 - 1) ||
                (x2 === x1 - 1 && y2 === y1) ||
                (x2 === x1 + 1 && y2 === y1) ||
                (x2 === x1 - 1 && y2 === y1 + 1) ||
                (x2 === x1 && y2 === y1 + 1)
            );
        } else {
            return (
                (x2 === x1 && y2 === y1 - 1) ||
                (x2 === x1 + 1 && y2 === y1 - 1) ||
                (x2 === x1 - 1 && y2 === y1) ||
                (x2 === x1 + 1 && y2 === y1) ||
                (x2 === x1 && y2 === y1 + 1) ||
                (x2 === x1 + 1 && y2 === y1 + 1)
            );
        }
    }

    createPlayerToken() {
        const pixels = this.getHexPixels(this.currentCoord.x, this.currentCoord.y);

        // We build a player standee token container
        this.playerToken = this.add.container(pixels.x, pixels.y);
        this.playerToken.setDepth(100);

        // 1. Standee base shadow
        const shadow = this.add.graphics();
        shadow.fillStyle(0x000000, 0.4);
        shadow.fillEllipse(0, 15, 55, 25);
        this.playerToken.add(shadow);

        // 2. Standee circular base (tabletop standee plate)
        const base = this.add.graphics();
        base.fillStyle(0xd97706, 0.9); // Golden amber base
        base.lineStyle(2, 0xffffff, 1);
        base.fillEllipse(0, 10, 50, 20);
        base.strokeEllipse(0, 10, 50, 20);
        this.playerToken.add(base);

        // 3. Card portrait border
        const cardBorder = this.add.graphics();
        cardBorder.fillStyle(0x1e1b4b, 0.95);
        cardBorder.lineStyle(2, 0xf59e0b, 1);
        cardBorder.fillRoundedRect(-22.5, -40, 45, 50, 5);
        cardBorder.strokeRoundedRect(-22.5, -40, 45, 50, 5);
        this.playerToken.add(cardBorder);

        // 4. Portrait avatar
        const avatar = this.add.sprite(0, -15, 'player_avatar');
        avatar.setDisplaySize(40, 45);
        // Mask avatar into rounded corners (simplified for preview: just display size matched)
        this.playerToken.add(avatar);

        // Breathing idle animation using Phaser Tween
        this.tweens.add({
            targets: this.playerToken,
            y: pixels.y - 4,
            duration: 1200,
            yoyo: true,
            repeat: -1,
            ease: 'Sine.easeInOut'
        });
    }

    handleTileClick(x, y) {
        if (this.isLocked || this.hasDragged) return; // Prevent movement when locked or dragging/panning the map

        // Trigger global move function defined in the parent HTML page
        if (window.onPhaserHexMove) {
            window.onPhaserHexMove(x, y);
        }
    }

    ensureMapTexturesLoaded(onReady) {
        const version = Date.now();
        let missingCount = 0;

        if (!this.textures.exists(this.getFogPlanTextureKey())) {
            this.load.image(this.getFogPlanTextureKey(), `${this.getFogPlanTileAssetUrl()}?v=${version}`);
            missingCount += 1;
        }

        for (const node of this.riftState.nodes || []) {
            if (node.content_slot === 'void') continue;
            const key = this.getTileTextureKey(node);
            const url = this.getTileAssetUrl(node);
            if (url && !this.textures.exists(key)) {
                this.load.image(key, `${url}?v=${version}`);
                missingCount += 1;
            }
        }

        if (missingCount === 0) {
            onReady();
            return;
        }

        this.load.once(Phaser.Loader.Events.COMPLETE, onReady);
        this.load.start();
    }

    updateRiftState(newState) {
        const floorChanged = this.riftState && this.riftState.floor !== newState.floor;
        this.riftState = newState;
        this.currentCoord = { x: newState.current_x, y: newState.current_y };

        // Stop current breathing idle tween to prevent offset confusion
        this.tweens.killTweensOf(this.playerToken);

        if (floorChanged) {
            // Destroy all map and overlay tiles
            for (let key in this.tiles) {
                this.tiles[key].destroy();
            }
            this.tiles = {};

            // Teleport player token immediately
            const targetPixels = this.getHexPixels(this.currentCoord.x, this.currentCoord.y);
            this.playerToken.setPosition(targetPixels.x, targetPixels.y);

            this.ensureMapTexturesLoaded(() => {
                this.drawMap();
            });

            // Center camera immediately
            this.cameras.main.centerOn(targetPixels.x, targetPixels.y);

            // Restart breathing idle animation
            this.tweens.add({
                targets: this.playerToken,
                y: targetPixels.y - 4,
                duration: 1200,
                yoyo: true,
                repeat: -1,
                ease: 'Sine.easeInOut'
            });

            // Update Info Card
            if (window.updateHexInfoCard) {
                window.updateHexInfoCard(newState);
            }
            return;
        }

        // Get new target pixels
        const targetPixels = this.getHexPixels(this.currentCoord.x, this.currentCoord.y);

        // Smoothly pan camera to center on the new position
        this.cameras.main.pan(targetPixels.x, targetPixels.y, 400, 'Cubic.easeOut');

        // Smooth tween slide to new hex
        this.tweens.add({
            targets: this.playerToken,
            x: targetPixels.x,
            y: targetPixels.y,
            duration: 400,
            ease: 'Cubic.easeOut',
            onComplete: () => {
                this.ensureMapTexturesLoaded(() => {
                    // Redraw map tiles (fog of war reveals, textures refresh)
                    this.drawMap();

                    // Restart breathing idle animation at new location
                    this.tweens.add({
                        targets: this.playerToken,
                        y: targetPixels.y - 4,
                        duration: 1200,
                        yoyo: true,
                        repeat: -1,
                        ease: 'Sine.easeInOut'
                    });

                    // Update info card on page
                    if (window.updateHexInfoCard) {
                        window.updateHexInfoCard(newState);
                    }
                });
            }
        });
    }
}
