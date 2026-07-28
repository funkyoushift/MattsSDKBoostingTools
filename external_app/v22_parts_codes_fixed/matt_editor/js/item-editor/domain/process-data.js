        // Build typeIdMap, partsMap, partsByTypeId from flattened format (metadata + parts_by_id only)
        // Class mod typeId -> display name (Siren -> Vex for consistency with legacy)
        var CLASS_MOD_NAMES = { 254: 'Vex', 255: 'Amon', 256: 'Rafa', 257: 'Rafa', 258: 'Harlowe', 259: 'Harlowe' };
        function buildFromPartsById(data) {
            const partsById = data.parts_by_id || {};
            let total = 0;
            for (const [fullId, part] of Object.entries(partsById)) {
                if (!part || typeof part !== 'object' || !part.id) continue;
                const partId = String(part.id);
                if (!partId.includes(':')) continue;
                const idx = partId.indexOf(':');
                const typeId = parseInt(partId.substring(0, idx), 10);
                if (isNaN(typeId)) continue;

                var partType = 'Part';
                var category = 'Weapon';
                var manufacturer = null;
                var weaponType = null;
                var loc = part.locations && part.locations[0];
                if (loc && typeof loc === 'string') {
                    var partTypesMatch = loc.match(/\.part_types\.(.+?)\.parts/);
                    if (partTypesMatch) partType = partTypesMatch[1];
                    if (loc.indexOf('weapons.manufacturers.') === 0) {
                        category = 'Weapon';
                        var mMatch = loc.match(/weapons\.manufacturers\.([^.]+)/);
                        if (mMatch) manufacturer = mMatch[1];
                        var wMatch = loc.match(/weapon_types\.(.+?)\.part_types/);
                        if (wMatch) weaponType = wMatch[1];
                    } else if (loc.indexOf('characters.') === 0) {
                        category = 'Class Mod';
                        var charMatch = loc.match(/characters\.([^.]+)\./);
                        if (charMatch) {
                            var rawName = charMatch[1];
                            manufacturer = (rawName && rawName.toLowerCase() === 'siren') ? 'Vex' : rawName;
                        }
                        if (CLASS_MOD_NAMES[typeId]) manufacturer = CLASS_MOD_NAMES[typeId];
                        // Class mod paths: characters.X.class_mods.Body.parts or .Rarity.Legendary Rarity.parts - set partType for guidelines
                        var classModSection = loc.match(/class_mods\.(.+?)\.parts/);
                        if (classModSection) partType = classModSection[1];
                    } else if (loc.indexOf('gadgets.') === 0) {
                        category = 'Gadget';
                        var gadgetSub = loc.match(/gadgets\.([^.]+)\./);
                        if (gadgetSub) {
                            var sub = gadgetSub[1].toLowerCase();
                            if (sub.indexOf('ordonance') !== -1 || sub.indexOf('ordnance') !== -1) {
                                category = loc.indexOf('grenades') !== -1 ? 'Grenades' : 'Ordnance';
                            } else if (sub.indexOf('repkit') !== -1) category = 'Repkit';
                            else if (sub.indexOf('shield') !== -1) category = 'Shield';
                            else if (sub.indexOf('enhancement') !== -1) {
                                category = 'Enhancements';
                                var enhManu = loc.match(/gadgets\.enhancements\.([^.]+)\./);
                                if (enhManu && enhManu[1] && enhManu[1] !== 'Universal') manufacturer = enhManu[1];
                            }
                        }
                    }
                }

                if (!typeIdMap.has(typeId)) {
                    var displayName = 'Type ' + typeId;
                    var useCategory = category;
                    var useManufacturer = manufacturer;
                    if (CLASS_MOD_NAMES[typeId]) {
                        useManufacturer = CLASS_MOD_NAMES[typeId];
                        displayName = useManufacturer + ' Class Mod';
                        useCategory = 'Class Mod';
                    } else if (category === 'Class Mod' && manufacturer) {
                        displayName = manufacturer + ' Class Mod';
                        useCategory = 'Class Mod';
                    } else if (category === 'Grenades' || category === 'Ordnance') {
                        displayName = category === 'Grenades' ? 'Grenades' : 'Ordnance';
                        useCategory = category;
                    } else if (category === 'Repkit' || category === 'Shield' || category === 'Enhancements') {
                        displayName = (manufacturer && category === 'Enhancements') ? (manufacturer + ' Enhancement') : category;
                        useCategory = category;
                        if (manufacturer && category === 'Enhancements') useManufacturer = manufacturer;
                    } else if (weaponType) {
                        displayName = weaponType;
                    } else if (manufacturer && category === 'Weapon') {
                        displayName = manufacturer + ' Weapon';
                    }
                    typeIdMap.set(typeId, {
                        id: typeId,
                        name: displayName,
                        category: useCategory,
                        manufacturer: useManufacturer || null,
                        context: useCategory === 'Class Mod' ? (useManufacturer || null) : null
                    });
                } else {
                    var existing = typeIdMap.get(typeId);
                    if (CLASS_MOD_NAMES[typeId]) {
                        existing.name = CLASS_MOD_NAMES[typeId] + ' Class Mod';
                        existing.category = 'Class Mod';
                        existing.manufacturer = CLASS_MOD_NAMES[typeId];
                        existing.context = CLASS_MOD_NAMES[typeId];
                    } else if (category === 'Class Mod' && manufacturer && (existing.name === 'Type ' + typeId || !existing.manufacturer)) {
                        existing.name = manufacturer + ' Class Mod';
                        existing.category = 'Class Mod';
                        existing.manufacturer = manufacturer;
                        existing.context = manufacturer;
                    } else if ((category === 'Grenades' || category === 'Ordnance' || category === 'Repkit' || category === 'Shield' || category === 'Enhancements') && existing.category === 'Gadget') {
                        existing.name = category === 'Grenades' ? 'Grenades' : (category === 'Ordnance' ? 'Ordnance' : category);
                        existing.category = category;
                    } else if (weaponType && existing.name === 'Type ' + typeId) {
                        existing.name = weaponType;
                        if (manufacturer) existing.manufacturer = manufacturer;
                    } else if (category === 'Enhancements' && manufacturer && (existing.name === 'Enhancements' || existing.name === 'Type ' + typeId)) {
                        existing.name = manufacturer + ' Enhancement';
                        existing.manufacturer = manufacturer;
                    }
                }
                if (!partsByTypeId.has(typeId)) {
                    partsByTypeId.set(typeId, []);
                }

                var partInfo = extractPartInfo(part, typeId, partType, category, weaponType, manufacturer, weaponType);
                if (!partInfo) continue;
                partInfo.path = loc || '';

                partsMap.set(partInfo.fullId, partInfo);
                partsMap.set(partInfo.id, partInfo);
                if (partInfo.spawnCode) partsMap.set(partInfo.spawnCode, partInfo);
                if (partInfo.string && partInfo.string !== partInfo.spawnCode) partsMap.set(partInfo.string, partInfo);
                var afterColon = partInfo.fullId.split(':')[1];
                if (afterColon) {
                    partsMap.set(afterColon, partInfo);
                    var num = parseInt(afterColon, 10);
                    if (!isNaN(num)) partsMap.set(num, partInfo);
                }
                partsByTypeId.get(typeId).push(partInfo);
                total++;
            }
            console.log('processGameData (flattened): Loaded ' + total + ' parts in ' + typeIdMap.size + ' type IDs');
        }

        function mergeMsbtPartSupplements() {
            const supplements = [];
            if (typeof window !== 'undefined') {
                if (Array.isArray(window.MSBT_GZO_FAMILY_PART_SUPPLEMENT)) {
                    supplements.push({
                        label: 'GZO family data',
                        entries: window.MSBT_GZO_FAMILY_PART_SUPPLEMENT
                    });
                }
                if (Array.isArray(window.MSBT_OBSERVED_MODDED_PART_SUPPLEMENT)) {
                    supplements.push({
                        label: 'observed modded catalog',
                        entries: window.MSBT_OBSERVED_MODDED_PART_SUPPLEMENT
                    });
                }
            }
            if (supplements.length === 0) return 0;

            let added = 0;
            for (const supplementInfo of supplements) {
                let supplementAdded = 0;
                for (const entry of supplementInfo.entries) {
                    if (!entry || !entry.fullId) continue;
                    const fullId = String(entry.fullId);
                    if (partsMap.has(fullId)) continue;

                    const typeId = parseInt(entry.typeId, 10);
                    const partId = parseInt(entry.partId, 10);
                    if (!Number.isFinite(typeId) || !Number.isFinite(partId)) continue;

                    if (!typeIdMap.has(typeId)) {
                        const typeLabel = entry.typeLabel || `Type ${typeId}`;
                        typeIdMap.set(typeId, {
                            id: typeId,
                            name: typeLabel,
                            category: entry.category || 'Part',
                            manufacturer: entry.manufacturer || null,
                            context: entry.context || null
                        });
                    } else if (entry.typeLabel) {
                        const existing = typeIdMap.get(typeId);
                        if (existing && (!existing.name || existing.name === `Type ${typeId}`)) {
                            existing.name = entry.typeLabel;
                        }
                        if (existing && entry.category && (!existing.category || existing.category === 'Part')) {
                            existing.category = entry.category;
                        }
                        if (existing && entry.manufacturer && !existing.manufacturer) {
                            existing.manufacturer = entry.manufacturer;
                        }
                    }
                    if (!partsByTypeId.has(typeId)) {
                        partsByTypeId.set(typeId, []);
                    }

                    const typeLabel = entry.typeLabel || `Type ${typeId}`;
                    const partType = entry.partType || typeLabel;
                    const statsParts = [];
                    if (entry.description) statsParts.push(entry.description);
                    if (entry.examples && entry.examples.length) statsParts.push(`Examples: ${entry.examples.join('; ')}`);
                    if (entry.source) statsParts.push(`Source: ${entry.source}`);
                    const partInfo = {
                        id: String(partId),
                        fullId: fullId,
                        typeId: typeId,
                        name: entry.name || fullId,
                        displayName: entry.name || fullId,
                        string: entry.name || fullId,
                        spawnCode: entry.spawnCode || entry.sourceName || fullId,
                        sourceName: entry.sourceName || entry.spawnCode || entry.name || fullId,
                        stats: statsParts.join(' | '),
                        description: entry.description || '',
                        partType: partType,
                        originalPartType: partType,
                        category: entry.category || 'Part',
                        manufacturer: entry.manufacturer || null,
                        itemType: entry.itemType || null,
                        rarity: null,
                        path: entry.source || 'GZO/custom modded catalog',
                        slotKey: entry.slotKey || null,
                        searchAliases: Array.isArray(entry.searchAliases) ? entry.searchAliases.slice() : [],
                        serialIndex: partId,
                        rootSerialIndex: typeId
                    };

                    partsMap.set(fullId, partInfo);
                    if (!partsMap.has(partInfo.id)) partsMap.set(partInfo.id, partInfo);
                    if (!partsMap.has(partId)) partsMap.set(partId, partInfo);
                    if (partInfo.spawnCode && !partsMap.has(partInfo.spawnCode)) partsMap.set(partInfo.spawnCode, partInfo);
                    if (partInfo.sourceName && !partsMap.has(partInfo.sourceName)) partsMap.set(partInfo.sourceName, partInfo);
                    partsByTypeId.get(typeId).push(partInfo);
                    added++;
                    supplementAdded++;
                }
                if (supplementAdded > 0) {
                    console.log(`MSBT: added ${supplementAdded} ${supplementInfo.label} parts to Matt editor browser`);
                }
            }
            return added;
        }

        function processGameData() {
            try {
                typeIdMap.clear();
                partsMap.clear();
                partsByTypeId.clear();
                if (typeof typeIdToPartTypeOrderCache !== 'undefined' && typeIdToPartTypeOrderCache) typeIdToPartTypeOrderCache.clear();

                // Check both gameData and window.gameData (for Electron compatibility)
                if (!gameData && !window.gameData) {
                    console.error('processGameData: gameData is null or undefined');
                    throw new Error('No game data to process');
                }
                
                // Use window.gameData as fallback if gameData is not set (for Electron)
                if (!gameData && window.gameData) {
                    gameData = window.gameData;
                }
                
                // Check if id_index is available and store it globally for optimized lookups (legacy format only)
                globalIdIndex = gameData.id_index || null;
                if (globalIdIndex) {
                    console.log('processGameData: Using id_index for optimized lookups (' + Object.keys(globalIdIndex).length + ' entries)');
                } else {
                    console.log('processGameData: No id_index found, using standard traversal');
                }

                // Flattened format: metadata + parts_by_id (+ optional class_mod_skills for full skill tree)
                if (gameData.parts_by_id && (gameData.metadata && gameData.metadata.flattened || !gameData.weapons)) {
                    console.log('processGameData: Flattened format detected (parts_by_id' + (gameData.class_mod_skills ? ', class_mod_skills' : '') + ')');
                    buildFromPartsById(gameData);
                    const msbtSupplementCount = mergeMsbtPartSupplements();
                    if (msbtSupplementCount > 0) {
                        console.log(`MSBT: MSBT part supplements loaded (${msbtSupplementCount} parts)`);
                    }
                    if (typeof window !== 'undefined') window.classModSkills = gameData.class_mod_skills || null;
                    var el = document.getElementById('dataHelpText');
                    if (el) el.innerHTML = '<small style="color: #81c784;">✅ Data loaded successfully! You can now use the editor below.</small>';
                    // Note: gameData is intentionally retained; parts.js, helpers.js and item-editor-10-yaml-save.js use it for id_index/resolvePath lookups and rarity.
                    return;
                }

                // Debug: Check what's in gameData
                console.log('processGameData: Top-level keys in gameData:', Object.keys(gameData || {}));
            if (gameData && gameData.heavy_weapons) {
                console.log('processGameData: heavy_weapons found! Keys:', Object.keys(gameData.heavy_weapons));
            } else {
                console.log('processGameData: heavy_weapons NOT found in gameData');
            }

            let totalPartsExtracted = 0;
            
            // Extract typeId 234 parts from top-level "Perk" and "Firmware" sections
            // Check for both "Perk" and "perk" (case-insensitive)
            const perkSection = gameData?.Perk || gameData?.perk;
            if (perkSection) {
                console.log('Found top-level Perk section');
                const perkData = perkSection;
                // Check if it has type_id 234, or if parts have IDs starting with "234:"
                const hasTypeId234 = perkData.type_id === 234;
                const has234Parts = perkData.parts && Array.isArray(perkData.parts) && 
                                    perkData.parts.some(p => p.id && String(p.id).startsWith('234:'));
                
                if ((hasTypeId234 || has234Parts) && perkData.parts && Array.isArray(perkData.parts)) {
                    console.log(`  Extracting ${perkData.parts.length} parts from Perk (Type ID: 234)`);
                    
                    // Add typeId 234 to typeIdMap if not already present
                    if (!typeIdMap.has(234)) {
                        typeIdMap.set(234, {
                            id: 234,
                            name: 'Class Mod Substats',
                            category: 'Class Mod',
                            context: null,
                            manufacturer: null
                        });
                        console.log(`Added type ID 234: Class Mod Substats`);
                    }
                    
                    if (!partsByTypeId.has(234)) {
                        partsByTypeId.set(234, []);
                    }
                    
                    // Extract all Perk parts
                    // If the section has type_id 234, extract ALL parts (they're all typeId 234)
                    for (let idx = 0; idx < perkData.parts.length; idx++) {
                        const part = perkData.parts[idx];
                        // Extract if: part.id starts with "234:", OR section has type_id 234 (extract all parts)
                        const partIdStr = part.id ? String(part.id) : '';
                        const has234Id = partIdStr.startsWith('234:');
                        // Always extract if section has type_id 234, or if part has 234: ID
                        const shouldExtract = has234Id || hasTypeId234 || (hasTypeId234 && partIdStr !== '');
                        
                        if (shouldExtract) {
                            // Normalize part ID to "234:X" format if needed
                            let normalizedPart = part;
                            if (hasTypeId234 && !has234Id) {
                                // If section has type_id 234 but part.id doesn't start with "234:", normalize it
                                if (part.id !== null && part.id !== undefined && part.id !== '') {
                                    // Extract numeric part from existing ID if it's just a number
                                    const numericMatch = partIdStr.match(/^(\d+)$/);
                                    if (numericMatch) {
                                        normalizedPart = {...part, id: `234:${numericMatch[1]}`};
                                    } else {
                                        normalizedPart = {...part, id: `234:${partIdStr}`};
                                    }
                                } else {
                                    // If part has no id, try to extract from spawn_code or use index
                                    let fallbackId = '';
                                    if (part.spawn_code) {
                                        // Try to extract numeric ID from spawn_code (e.g., "ClassMod.stat_123" -> "123")
                                        const spawnMatch = String(part.spawn_code).match(/(\d+)/);
                                        if (spawnMatch) {
                                            fallbackId = spawnMatch[1];
                                        }
                                    }
                                    if (!fallbackId) {
                                        // Use index as last resort, but add offset to avoid conflicts
                                        fallbackId = String(idx + 1);
                                    }
                                    normalizedPart = {...part, id: `234:${fallbackId}`};
                                }
                            }
                            
                            const partInfo = extractPartInfo(normalizedPart, 234, 'Perk', 'Class Mod', null, null, null);
                            if (partInfo) {
                                // Ensure typeId is set to 234 and partType is 'Perk'
                                partInfo.typeId = 234;
                                partInfo.partType = 'Perk';
                                partInfo.path = 'Perk';
                                
                                // Ensure fullId is properly set
                                if (!partInfo.fullId || !partInfo.fullId.includes(':')) {
                                    const finalId = String(partInfo.id || normalizedPart.id || '');
                                    if (finalId && !finalId.includes(':')) {
                                        partInfo.fullId = `234:${finalId}`;
                                        partInfo.id = `234:${finalId}`;
                                    } else if (finalId.includes(':')) {
                                        partInfo.fullId = finalId;
                                    }
                                }
                                
                                // Store with multiple key formats
                                partsMap.set(partInfo.fullId, partInfo);
                                partsMap.set(partInfo.id, partInfo);
                                if (partInfo.spawnCode) {
                                    partsMap.set(partInfo.spawnCode, partInfo);
                                }
                                if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                    partsMap.set(partInfo.string, partInfo);
                                }
                                
                                // Also store by the numeric part ID after colon
                                if (partInfo.fullId.includes(':')) {
                                    const afterColon = partInfo.fullId.split(':')[1];
                                    partsMap.set(afterColon, partInfo);
                                    const numericPartId = parseInt(afterColon);
                                    if (!isNaN(numericPartId)) {
                                        partsMap.set(numericPartId, partInfo);
                                    }
                                }
                                
                                partsByTypeId.get(234).push(partInfo);
                                totalPartsExtracted++;
                                
                                // Debug: Log first few parts to verify storage
                                if (DEBUG && partsByTypeId.get(234).length <= 3) {
                                    console.log(`  [DEBUG] Stored Perk part: fullId=${partInfo.fullId}, id=${partInfo.id}, typeId=${partInfo.typeId}, partType=${partInfo.partType}, name=${partInfo.name}`);
                                }
                            } else if (DEBUG) {
                                console.log(`  [DEBUG] Failed to extract Perk part at index ${idx}:`, part);
                            }
                        } else if (DEBUG) {
                            console.log(`  [DEBUG] Skipping Perk part at index ${idx} (shouldExtract=false):`, part);
                        }
                    }
                    const extractedPerkCount = partsByTypeId.get(234).filter(p => p.partType === 'Perk').length;
                    console.log(`  ✓ Extracted ${extractedPerkCount} Perk parts for typeId 234 (expected: ${perkData.parts.length})`);
                    if (extractedPerkCount !== perkData.parts.length) {
                        console.warn(`  ⚠️ WARNING: Extracted ${extractedPerkCount} Perk parts but JSON has ${perkData.parts.length} parts. Some parts may be missing!`);
                    }
                    if (DEBUG) {
                        console.log(`  [DEBUG] Total parts in partsByTypeId.get(234) after Perk extraction: ${partsByTypeId.get(234).length}`);
                        // Verify a specific part is stored
                        const testPart = partsMap.get('234:1');
                        console.log(`  [DEBUG] Verification - partsMap.get('234:1') =`, testPart);
                        // List all extracted Perk IDs
                        const perkIds = partsByTypeId.get(234).filter(p => p.partType === 'Perk').map(p => p.fullId || p.id).sort();
                        console.log(`  [DEBUG] Extracted Perk IDs:`, perkIds.slice(0, 10), perkIds.length > 10 ? `... (${perkIds.length} total)` : '');
                    }
                } else if (DEBUG) {
                    console.log(`  [DEBUG] Perk section found but doesn't match typeId 234. type_id=${perkData.type_id}, hasParts=${!!perkData.parts}`);
                }
            } else if (DEBUG) {
                console.log('  [DEBUG] No Perk section found in gameData. Top-level keys:', Object.keys(gameData || {}));
            }
            
            // Check for both "Firmware" and "firmware" (case-insensitive)
            // First check top-level, then check class_mods.Firmware
            let firmwareSection = gameData?.Firmware || gameData?.firmware;
            if (!firmwareSection && gameData?.class_mods) {
                firmwareSection = gameData.class_mods.Firmware || gameData.class_mods.firmware;
            }
            if (firmwareSection) {
                console.log('Found Firmware section (top-level or in class_mods)');
                const firmwareData = firmwareSection;
                // Check if it has type_id 234, or if parts have IDs starting with "234:"
                const hasTypeId234 = firmwareData.type_id === 234;
                const has234Parts = firmwareData.parts && Array.isArray(firmwareData.parts) && 
                                    firmwareData.parts.some(p => p.id && String(p.id).startsWith('234:'));
                
                if ((hasTypeId234 || has234Parts) && firmwareData.parts && Array.isArray(firmwareData.parts)) {
                    console.log(`  Extracting ${firmwareData.parts.length} parts from Firmware (Type ID: 234)`);
                    
                    // Add typeId 234 to typeIdMap if not already present
                    if (!typeIdMap.has(234)) {
                        typeIdMap.set(234, {
                            id: 234,
                            name: 'Class Mod Substats',
                            category: 'Class Mod',
                            context: null,
                            manufacturer: null
                        });
                        console.log(`Added type ID 234: Class Mod Substats`);
                    }
                    
                    if (!partsByTypeId.has(234)) {
                        partsByTypeId.set(234, []);
                    }
                    
                    // Extract all Firmware parts (including skillcraft)
                    // If the section has type_id 234, extract ALL parts (they're all typeId 234)
                    for (let idx = 0; idx < firmwareData.parts.length; idx++) {
                        const part = firmwareData.parts[idx];
                        // Extract if: part.id starts with "234:", OR section has type_id 234 (extract all parts)
                        const partIdStr = part.id ? String(part.id) : '';
                        const has234Id = partIdStr.startsWith('234:');
                        // Also check spawn_code for skillcraft firmware (case-insensitive)
                        const spawnCode = String(part.spawn_code || part.spawnCode || part.string || '').toLowerCase();
                        const isSkillcraftFirmware = spawnCode.includes('part_firmware_skillcraft');
                        // Always extract if section has type_id 234, or if part has 234: ID, or is skillcraft
                        const shouldExtract = has234Id || hasTypeId234 || isSkillcraftFirmware || (hasTypeId234 && partIdStr !== '');
                        
                        if (shouldExtract) {
                            // Normalize part ID to "234:X" format if needed
                            let normalizedPart = part;
                            if (hasTypeId234 && !has234Id) {
                                // If section has type_id 234 but part.id doesn't start with "234:", normalize it
                                if (part.id !== null && part.id !== undefined && part.id !== '') {
                                    // Extract numeric part from existing ID if it's just a number
                                    const numericMatch = partIdStr.match(/^(\d+)$/);
                                    if (numericMatch) {
                                        normalizedPart = {...part, id: `234:${numericMatch[1]}`};
                                    } else {
                                        normalizedPart = {...part, id: `234:${partIdStr}`};
                                    }
                                } else if (isSkillcraftFirmware) {
                                    // For skillcraft firmware without standard ID, try to extract numeric ID from spawn_code or use spawn_code as fallback
                                    const numericMatch = spawnCode.match(/(\d+)/);
                                    if (numericMatch) {
                                        normalizedPart = {...part, id: `234:${numericMatch[1]}`};
                                    } else {
                                        // Check if it's the known skillcraft ID (103)
                                        if (spawnCode.includes('skillcraft')) {
                                            normalizedPart = {...part, id: '234:103'};
                                        } else {
                                            const skillcraftId = spawnCode.replace(/\./g, '_').replace(/[^a-z0-9_]/g, '');
                                            normalizedPart = {...part, id: `234:${skillcraftId}`};
                                        }
                                    }
                                } else {
                                    // If part has no id, try to extract from spawn_code or use index
                                    let fallbackId = '';
                                    if (part.spawn_code) {
                                        // Try to extract numeric ID from spawn_code (e.g., "ClassMod.part_firmware_123" -> "123")
                                        const spawnMatch = String(part.spawn_code).match(/(\d+)/);
                                        if (spawnMatch) {
                                            fallbackId = spawnMatch[1];
                                        }
                                    }
                                    if (!fallbackId) {
                                        // Use index as last resort, but add offset to avoid conflicts (firmware starts at 74)
                                        fallbackId = String(74 + idx);
                                    }
                                    normalizedPart = {...part, id: `234:${fallbackId}`};
                                }
                            }
                            
                            const partInfo = extractPartInfo(normalizedPart, 234, 'Firmware', 'Class Mod', null, null, null);
                            if (partInfo) {
                                // Ensure typeId is set to 234 and partType is 'Firmware'
                                partInfo.typeId = 234;
                                partInfo.partType = 'Firmware';
                                partInfo.path = 'Firmware';
                                
                                // Ensure fullId is set correctly for Skillcraft (234:103) and all firmware
                                if (!partInfo.fullId || !partInfo.fullId.includes(':')) {
                                    const partId = String(partInfo.id || normalizedPart.id || '');
                                    if (partId && !partId.includes(':')) {
                                        partInfo.fullId = `234:${partId}`;
                                        partInfo.id = `234:${partId}`;
                                    } else if (partId.includes(':')) {
                                        partInfo.fullId = partId;
                                    }
                                }
                                
                                // Store with multiple key formats
                                partsMap.set(partInfo.fullId, partInfo);
                                partsMap.set(partInfo.id, partInfo);
                                if (partInfo.spawnCode) {
                                    partsMap.set(partInfo.spawnCode, partInfo);
                                }
                                if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                    partsMap.set(partInfo.string, partInfo);
                                }
                                
                                // Also store by the numeric part ID after colon
                                if (partInfo.fullId.includes(':')) {
                                    const afterColon = partInfo.fullId.split(':')[1];
                                    partsMap.set(afterColon, partInfo);
                                    const numericPartId = parseInt(afterColon);
                                    if (!isNaN(numericPartId)) {
                                        partsMap.set(numericPartId, partInfo);
                                    }
                                }
                                
                                partsByTypeId.get(234).push(partInfo);
                                totalPartsExtracted++;
                                
                                // Debug: Log first few parts to verify storage
                                if (DEBUG && partsByTypeId.get(234).filter(p => p.partType === 'Firmware').length <= 3) {
                                    console.log(`  [DEBUG] Stored Firmware part: fullId=${partInfo.fullId}, id=${partInfo.id}, typeId=${partInfo.typeId}, partType=${partInfo.partType}, name=${partInfo.name}`);
                                }
                            } else if (DEBUG) {
                                console.log(`  [DEBUG] Failed to extract Firmware part at index ${idx}:`, part);
                            }
                        } else if (DEBUG) {
                            console.log(`  [DEBUG] Skipping Firmware part at index ${idx} (shouldExtract=false):`, part);
                        }
                    }
                    const extractedFirmwareCount = partsByTypeId.get(234).filter(p => p.partType === 'Firmware').length;
                    console.log(`  ✓ Extracted ${extractedFirmwareCount} Firmware parts for typeId 234 (expected: ${firmwareData.parts.length})`);
                    if (extractedFirmwareCount !== firmwareData.parts.length) {
                        console.warn(`  ⚠️ WARNING: Extracted ${extractedFirmwareCount} Firmware parts but JSON has ${firmwareData.parts.length} parts. Some parts may be missing!`);
                    }
                    if (DEBUG) {
                        console.log(`  [DEBUG] Total parts in partsByTypeId.get(234) after Firmware extraction: ${partsByTypeId.get(234).length}`);
                        // Verify a specific part is stored
                        const testPart = partsMap.get('234:74');
                        console.log(`  [DEBUG] Verification - partsMap.get('234:74') =`, testPart);
                        // List all extracted Firmware IDs
                        const firmwareIds = partsByTypeId.get(234).filter(p => p.partType === 'Firmware').map(p => p.fullId || p.id).sort();
                        console.log(`  [DEBUG] Extracted Firmware IDs:`, firmwareIds.slice(0, 10), firmwareIds.length > 10 ? `... (${firmwareIds.length} total)` : '');
                    }
                } else if (DEBUG) {
                    console.log(`  [DEBUG] Firmware section found but doesn't match typeId 234. type_id=${firmwareData.type_id}, hasParts=${!!firmwareData.parts}`);
                }
            } else if (DEBUG) {
                console.log('  [DEBUG] No Firmware section found in gameData. Top-level keys:', Object.keys(gameData || {}));
            }
            
            // Final verification: Log summary of typeId 234 parts
            if (partsByTypeId.has(234)) {
                const type234Parts = partsByTypeId.get(234);
                console.log(`[SUMMARY] Total typeId 234 parts extracted: ${type234Parts.length}`);
                if (type234Parts.length > 0) {
                    const perkCount = type234Parts.filter(p => p.partType === 'Perk').length;
                    const firmwareCount = type234Parts.filter(p => p.partType === 'Firmware').length;
                    console.log(`[SUMMARY] - Perk: ${perkCount}, Firmware: ${firmwareCount}`);
                    // Show sample IDs
                    const sampleIds = type234Parts.slice(0, 5).map(p => p.fullId || p.id);
                    console.log(`[SUMMARY] Sample part IDs:`, sampleIds);
                } else {
                    console.warn(`[WARNING] typeId 234 parts array is empty! Parts may not have been extracted.`);
                }
            } else {
                console.warn(`[WARNING] typeId 234 not found in partsByTypeId! Extraction may have failed.`);
            }

            // Extract from weapons
            if (gameData.weapons && gameData.weapons.manufacturers) {
                for (const [manufacturer, data] of Object.entries(gameData.weapons.manufacturers)) {
                    if (data.weapon_types) {
                        for (const [weaponType, weaponData] of Object.entries(data.weapon_types)) {
                            const typeId = weaponData.type_id;
                            if (typeId) {
                                // Always create type ID entry, even if no parts exist
                                if (!typeIdMap.has(typeId)) {
                                    typeIdMap.set(typeId, {
                                        id: typeId,
                                        name: `${weaponType}`,
                                        category: 'Weapon',
                                        manufacturer: manufacturer
                                    });
                                    console.log(`Added type ID ${typeId}: ${manufacturer} ${weaponType}`);
                                } else {
                                    // Update if we have manufacturer info
                                    const existing = typeIdMap.get(typeId);
                                    if (!existing.manufacturer && manufacturer) {
                                        existing.manufacturer = manufacturer;
                                        existing.name = `${weaponType}`;
                                    }
                                }
                                
                                if (!partsByTypeId.has(typeId)) {
                                    partsByTypeId.set(typeId, []);
                                }

                                // Extract parts from part_types (recursive to handle nested structures like Rarities.Rarity)
                                // First check for Rarities at the same level as part_types (sibling, not nested)
                                if (weaponData.Rarities) {
                                    console.log(`  Found Rarities section at top level for ${manufacturer} ${weaponType} (Type ID: ${typeId})`);
                                    const extractFromRarities = (raritiesData, currentTypeId) => {
                                        for (const [rarityKey, rarityData] of Object.entries(raritiesData)) {
                                            if (rarityData.parts && Array.isArray(rarityData.parts)) {
                                                console.log(`  Extracting ${rarityData.parts.length} parts from Rarities.${rarityKey} (Type ID: ${currentTypeId})`);
                                                for (const part of rarityData.parts) {
                                                    const partInfo = extractPartInfo(part, currentTypeId, rarityKey, 'Weapon', weaponType, manufacturer, weaponType);
                                                    if (partInfo) {
                                                        let targetTypeId = currentTypeId;
                                                        if (partInfo.fullId.includes(':')) {
                                                            const colonIndex = partInfo.fullId.indexOf(':');
                                                            const extractedTypeId = parseInt(partInfo.fullId.substring(0, colonIndex));
                                                            if (!isNaN(extractedTypeId)) {
                                                                partInfo.typeId = extractedTypeId;
                                                                targetTypeId = extractedTypeId;
                                                                const afterColon = partInfo.fullId.substring(colonIndex + 1);
                                                                partsMap.set(afterColon, partInfo);
                                                                const numericPartId = parseInt(afterColon);
                                                                if (!isNaN(numericPartId)) {
                                                                    partsMap.set(numericPartId, partInfo);
                                                                }
                                                            }
                                                        } else {
                                                            partInfo.typeId = currentTypeId;
                                                            targetTypeId = currentTypeId;
                                                        }
                                                        
                                                        partsMap.set(partInfo.fullId, partInfo);
                                                        partsMap.set(partInfo.id, partInfo);
                                                        if (partInfo.spawnCode) {
                                                            partsMap.set(partInfo.spawnCode, partInfo);
                                                        }
                                                        if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                                            partsMap.set(partInfo.string, partInfo);
                                                        }
                                                        if (!partsByTypeId.has(targetTypeId)) {
                                                            partsByTypeId.set(targetTypeId, []);
                                                        }
                                                        partsByTypeId.get(targetTypeId).push(partInfo);
                                                        totalPartsExtracted++;
                                                        
                                                        // Debug log for comp parts
                                                        if ((partInfo.spawnCode && String(partInfo.spawnCode).includes('.comp_')) || (partInfo.string && String(partInfo.string).includes('.comp_'))) {
                                                            console.log(`    ✓ Extracted comp part: ${partInfo.name} (fullId: ${partInfo.fullId}, id: ${partInfo.id}, typeId: ${partInfo.typeId}, spawnCode: ${partInfo.spawnCode}, string: ${partInfo.string})`);
                                                        }
                                                        // Debug log for part 7 in typeId 267
                                                        if ((partInfo.id === '7' || partInfo.fullId === '267:7' || partInfo.id === 7) && (currentTypeId === 267 || targetTypeId === 267)) {
                                                            console.log(`    ✓ Extracted part 7 from Rarities for typeId 267: ${partInfo.name} (fullId: ${partInfo.fullId}, id: ${partInfo.id}, typeId: ${partInfo.typeId}, targetTypeId: ${targetTypeId})`);
                                                        }
                                                    }
                                                }
                                            }
                                            if (rarityData.part_types) {
                                                extractFromRarities(rarityData.part_types, currentTypeId);
                                            }
                                        }
                                    };
                                    extractFromRarities(weaponData.Rarities, typeId);
                                }
                                
                                if (weaponData.part_types) {
                                    const extractPartsRecursive = (partTypes, currentTypeId, path = '') => {
                                        for (const [partTypeKey, partTypeData] of Object.entries(partTypes)) {
                                            const currentPath = path ? `${path}.${partTypeKey}` : partTypeKey;
                                            
                                            // Check if this is a Rarity section - log it for debugging
                                            if (partTypeKey === 'Rarity' || currentPath.includes('Rarity')) {
                                                console.log(`  Found Rarity section at ${currentPath} (Type ID: ${currentTypeId})`);
                                            }
                                            
                                            if (partTypeData.parts && Array.isArray(partTypeData.parts)) {
                                                console.log(`  Extracting ${partTypeData.parts.length} parts from ${currentPath} (Type ID: ${currentTypeId})`);
                                                for (const part of partTypeData.parts) {
                                                    const partInfo = extractPartInfo(
                                                        part, currentTypeId, partTypeKey, 'Weapon', weaponType, manufacturer, weaponType
                                                    );
                                                    
                                                    if (partInfo) {
                                                        // Set the path field for categorization
                                                        partInfo.path = currentPath;
                                                        
                                                        // If part ID contains a colon (type:value format), extract the type ID and update partInfo
                                                        let targetTypeId = currentTypeId;
                                                        if (partInfo.fullId.includes(':')) {
                                                            const colonIndex = partInfo.fullId.indexOf(':');
                                                            const extractedTypeId = parseInt(partInfo.fullId.substring(0, colonIndex));
                                                            if (!isNaN(extractedTypeId)) {
                                                                // Update the partInfo's typeId to match the extracted type ID
                                                                partInfo.typeId = extractedTypeId;
                                                                targetTypeId = extractedTypeId;
                                                                // Also store just the numeric part after colon for lookup
                                                                const afterColon = partInfo.fullId.substring(colonIndex + 1);
                                                                partsMap.set(afterColon, partInfo);
                                                                const numericPartId = parseInt(afterColon);
                                                                if (!isNaN(numericPartId)) {
                                                                    partsMap.set(numericPartId, partInfo);
                                                                }
                                                                
                                                                // Debug for part 73
                                                                if (afterColon === '73' && extractedTypeId === 13) {
                                                                    console.log(`    ✓ Storing part 73 (afterColon: ${afterColon}, numericPartId: ${numericPartId}, targetTypeId: ${targetTypeId})`);
                                                                }
                                                            }
                                                        } else {
                                                            // For simple numeric IDs (no colon), ensure typeId is set to currentTypeId
                                                            // This is important for parts from Rarities sections
                                                            partInfo.typeId = currentTypeId;
                                                            targetTypeId = currentTypeId;
                                                        }
                                                        
                                                        // Store with both fullId and simple id
                                                        partsMap.set(partInfo.fullId, partInfo);
                                                        partsMap.set(partInfo.id, partInfo);
                                                        
                                                        // If the id is in "typeId:partId" format, also store with just the partId for simple part lookups
                                                        if (partInfo.id && String(partInfo.id).includes(':')) {
                                                            const idParts = String(partInfo.id).split(':');
                                                            if (idParts.length === 2) {
                                                                const idTypeId = parseInt(idParts[0]);
                                                                const idPartId = idParts[1];
                                                                // If the typeId in the id matches the targetTypeId, store with just the partId
                                                                if (idTypeId === targetTypeId) {
                                                                    partsMap.set(idPartId, partInfo);
                                                                    const numericPartId = parseInt(idPartId);
                                                                    if (!isNaN(numericPartId)) {
                                                                        partsMap.set(numericPartId, partInfo);
                                                                    }
                                                                }
                                                            }
                                                        }
                                                        
                                                        // Store by spawn_code for string lookup
                                                        if (partInfo.spawnCode) {
                                                            partsMap.set(partInfo.spawnCode, partInfo);
                                                        }
                                                        // Also store by string field if different from spawnCode
                                                        if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                                            partsMap.set(partInfo.string, partInfo);
                                                        }
                                                        
                                                        // Store in the target type ID's collection
                                                        if (!partsByTypeId.has(targetTypeId)) {
                                                            partsByTypeId.set(targetTypeId, []);
                                                        }
                                                        partsByTypeId.get(targetTypeId).push(partInfo);
                                                        totalPartsExtracted++;
                                                        
                                                        // Debug: Verify part 73 is stored for typeId 13
                                                        if (targetTypeId === 13 || currentTypeId === 13) {
                                                            const partIdCheck = String(partInfo.id || '');
                                                            const fullIdCheck = String(partInfo.fullId || '');
                                                            if (partIdCheck.includes('73') || fullIdCheck.includes('73')) {
                                                                const collectionSize = partsByTypeId.get(targetTypeId) ? partsByTypeId.get(targetTypeId).length : 0;
                                                                console.log(`    ✓ Verified part 73 stored in partsByTypeId for typeId ${targetTypeId}. Collection now has ${collectionSize} parts. Part info: id=${partIdCheck}, fullId=${fullIdCheck}, typeId=${partInfo.typeId}`);
                                                            }
                                                        }
                                                        
                                                        // Debug log for specific parts
                                                        if (partInfo.fullId === '14:35' || partInfo.id === '14:35' || partInfo.spawnCode === 'TED_AR.comp_05_legendary_Chuck') {
                                                            console.log(`    ✓ Found part 14:35: ${partInfo.name} (fullId: ${partInfo.fullId}, id: ${partInfo.id}, typeId: ${partInfo.typeId}, targetTypeId: ${targetTypeId}, currentTypeId: ${currentTypeId}, spawnCode: ${partInfo.spawnCode})`);
                                                        }
                                                        // Debug log for part 7 in typeId 267 (Jakobs Grenade rarity)
                                                        if ((partInfo.id === '7' || partInfo.fullId === '267:7') && currentTypeId === 267) {
                                                            console.log(`    ✓ Extracted part 7 for typeId 267: ${partInfo.name} (fullId: ${partInfo.fullId}, id: ${partInfo.id}, typeId: ${partInfo.typeId}, targetTypeId: ${targetTypeId}, currentTypeId: ${currentTypeId}, partType: ${partTypeKey}, path: ${currentPath})`);
                                                        }
                                                        // Debug log for part 73 in typeId 13 (Legendary rarity)
                                                        const partIdStr = String(partInfo.id || '');
                                                        const fullIdStr = String(partInfo.fullId || '');
                                                        let afterColon = null;
                                                        let numericPartId = null;
                                                        if (partInfo.fullId.includes(':')) {
                                                            const colonIdx = partInfo.fullId.indexOf(':');
                                                            afterColon = partInfo.fullId.substring(colonIdx + 1);
                                                            numericPartId = parseInt(afterColon);
                                                        }
                                                        if ((partIdStr === '73' || partIdStr === '13:73' || fullIdStr === '13:73' || 
                                                             partIdStr.includes(':73') || fullIdStr.includes(':73') || afterColon === '73') && 
                                                            (currentTypeId === 13 || targetTypeId === 13)) {
                                                            console.log(`    ✓ Extracted part 73 for typeId 13: ${partInfo.name} (fullId: ${partInfo.fullId}, id: ${partInfo.id}, typeId: ${partInfo.typeId}, targetTypeId: ${targetTypeId}, currentTypeId: ${currentTypeId}, partType: ${partTypeKey}, path: ${currentPath}, spawnCode: ${partInfo.spawnCode})`);
                                                            console.log(`    ✓ Storing part 73 in partsByTypeId for typeId ${targetTypeId}, partsMap will have keys: ${afterColon || 'N/A'}, ${numericPartId || 'N/A'}`);
                                                        }
                                                        // Debug log for any part with id "7" to track rarity parts
                                                        if (partInfo.id === '7' || String(partInfo.id) === '7') {
                                                            console.log(`    ✓ Extracted part with id 7: ${partInfo.name} (fullId: ${partInfo.fullId}, id: ${partInfo.id}, typeId: ${partInfo.typeId}, targetTypeId: ${targetTypeId}, currentTypeId: ${currentTypeId}, partType: ${partTypeKey}, path: ${currentPath})`);
                                                        }
                                                    }
                                                }
                                            }
                                            // Special handling for Rarities sections - check if it has nested Rarity structures (Rarities.Rarity.parts)
                                            // Also check for nested structures like "Rarity" -> "Comp"
                                            if (partTypeKey === 'Rarities' || partTypeKey === 'Rarity') {
                                                // Check for nested part types under Rarity (e.g., "Rarity" -> "Comp")
                                                for (const [nestedPartTypeKey, nestedPartTypeData] of Object.entries(partTypeData)) {
                                                    // Skip non-part-type keys
                                                    if (nestedPartTypeKey === 'dlc' || nestedPartTypeKey === 'count') continue;
                                                    
                                                    // Check if this nested structure has parts array
                                                    if (nestedPartTypeData && typeof nestedPartTypeData === 'object' && nestedPartTypeData.parts && Array.isArray(nestedPartTypeData.parts)) {
                                                        const nestedPath = `${currentPath}.${nestedPartTypeKey}`;
                                                        console.log(`  Extracting ${nestedPartTypeData.parts.length} parts from ${nestedPath} (Type ID: ${currentTypeId})`);
                                                        for (const part of nestedPartTypeData.parts) {
                                                            const partInfo = extractPartInfo(part, currentTypeId, nestedPartTypeKey, 'Weapon', weaponType, manufacturer, weaponType);
                                                            if (partInfo) {
                                                                let targetTypeId = currentTypeId;
                                                                if (partInfo.fullId.includes(':')) {
                                                                    const colonIndex = partInfo.fullId.indexOf(':');
                                                                    const extractedTypeId = parseInt(partInfo.fullId.substring(0, colonIndex));
                                                                    if (!isNaN(extractedTypeId)) {
                                                                        partInfo.typeId = extractedTypeId;
                                                                        targetTypeId = extractedTypeId;
                                                                        const afterColon = partInfo.fullId.substring(colonIndex + 1);
                                                                        partsMap.set(afterColon, partInfo);
                                                                        const numericPartId = parseInt(afterColon);
                                                                        if (!isNaN(numericPartId)) {
                                                                            partsMap.set(numericPartId, partInfo);
                                                                        }
                                                                        
                                                                        // Debug for part 73
                                                                        if (afterColon === '73' && extractedTypeId === 13) {
                                                                            console.log(`    ✓ Storing part 73 from ${nestedPath} (afterColon: ${afterColon}, numericPartId: ${numericPartId}, targetTypeId: ${targetTypeId})`);
                                                                        }
                                                                    }
                                                                } else {
                                                                    partInfo.typeId = currentTypeId;
                                                                    targetTypeId = currentTypeId;
                                                                }
                                                                
                                                                // Store with both fullId and simple id
                                                                partsMap.set(partInfo.fullId, partInfo);
                                                                partsMap.set(partInfo.id, partInfo);
                                                                
                                                                // If the id is in "typeId:partId" format, also store with just the partId
                                                                if (partInfo.id && String(partInfo.id).includes(':')) {
                                                                    const idParts = String(partInfo.id).split(':');
                                                                    if (idParts.length === 2) {
                                                                        const idTypeId = parseInt(idParts[0]);
                                                                        const idPartId = idParts[1];
                                                                        if (idTypeId === targetTypeId) {
                                                                            partsMap.set(idPartId, partInfo);
                                                                            const numericPartId = parseInt(idPartId);
                                                                            if (!isNaN(numericPartId)) {
                                                                                partsMap.set(numericPartId, partInfo);
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                                
                                                                if (partInfo.spawnCode) {
                                                                    partsMap.set(partInfo.spawnCode, partInfo);
                                                                }
                                                                if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                                                    partsMap.set(partInfo.string, partInfo);
                                                                }
                                                                if (!partsByTypeId.has(targetTypeId)) {
                                                                    partsByTypeId.set(targetTypeId, []);
                                                                }
                                                                partsByTypeId.get(targetTypeId).push(partInfo);
                                                                totalPartsExtracted++;
                                                                
                                                                // Debug log for comp parts (especially part 73)
                                                                const partIdStr = String(partInfo.id || '');
                                                                const fullIdStr = String(partInfo.fullId || '');
                                                                if ((partInfo.spawnCode && String(partInfo.spawnCode).includes('.comp_')) || 
                                                                    (partInfo.string && String(partInfo.string).includes('.comp_')) ||
                                                                    partIdStr === '13:73' || fullIdStr === '13:73' ||
                                                                    partIdStr.endsWith(':73') || fullIdStr.endsWith(':73')) {
                                                                    console.log(`    ✓ Extracted comp part from ${nestedPath}: ${partInfo.name} (fullId: ${partInfo.fullId}, id: ${partInfo.id}, typeId: ${partInfo.typeId}, spawnCode: ${partInfo.spawnCode}, string: ${partInfo.string})`);
                                                                    if (partIdStr.includes('73') || fullIdStr.includes('73')) {
                                                                        const collectionSize = partsByTypeId.get(targetTypeId) ? partsByTypeId.get(targetTypeId).length : 0;
                                                                        console.log(`      ✓ Part 73 stored in partsByTypeId for typeId ${targetTypeId}. Collection now has ${collectionSize} parts.`);
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                                
                                                // Check for nested Rarity structures (Rarities.Rarity.parts)
                                                if (partTypeData.Rarity && partTypeData.Rarity.parts && Array.isArray(partTypeData.Rarity.parts)) {
                                                    console.log(`  Extracting ${partTypeData.Rarity.parts.length} parts from ${currentPath}.Rarity (Type ID: ${currentTypeId})`);
                                                    for (const part of partTypeData.Rarity.parts) {
                                                        const partInfo = extractPartInfo(part, currentTypeId, 'Rarity', 'Weapon', weaponType, manufacturer, weaponType);
                                                        if (partInfo) {
                                                            let targetTypeId = currentTypeId;
                                                            if (partInfo.fullId.includes(':')) {
                                                                const colonIndex = partInfo.fullId.indexOf(':');
                                                                const extractedTypeId = parseInt(partInfo.fullId.substring(0, colonIndex));
                                                                if (!isNaN(extractedTypeId)) {
                                                                    partInfo.typeId = extractedTypeId;
                                                                    targetTypeId = extractedTypeId;
                                                                    const afterColon = partInfo.fullId.substring(colonIndex + 1);
                                                                    partsMap.set(afterColon, partInfo);
                                                                    const numericPartId = parseInt(afterColon);
                                                                    if (!isNaN(numericPartId)) {
                                                                        partsMap.set(numericPartId, partInfo);
                                                                    }
                                                                }
                                                            } else {
                                                                partInfo.typeId = currentTypeId;
                                                                targetTypeId = currentTypeId;
                                                            }
                                                            
                                                            partsMap.set(partInfo.fullId, partInfo);
                                                            partsMap.set(partInfo.id, partInfo);
                                                            if (partInfo.spawnCode) {
                                                                partsMap.set(partInfo.spawnCode, partInfo);
                                                            }
                                                            if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                                                partsMap.set(partInfo.string, partInfo);
                                                            }
                                                            if (!partsByTypeId.has(targetTypeId)) {
                                                                partsByTypeId.set(targetTypeId, []);
                                                            }
                                                            partsByTypeId.get(targetTypeId).push(partInfo);
                                                            totalPartsExtracted++;
                                                            
                                                            // Debug log for comp parts
                                                            if ((partInfo.spawnCode && String(partInfo.spawnCode).includes('.comp_')) || (partInfo.string && String(partInfo.string).includes('.comp_'))) {
                                                                console.log(`    ✓ Extracted comp part: ${partInfo.name} (fullId: ${partInfo.fullId}, id: ${partInfo.id}, typeId: ${partInfo.typeId}, spawnCode: ${partInfo.spawnCode}, string: ${partInfo.string}, path: ${currentPath}.Rarity)`);
                                                            }
                                                        }
                                                    }
                                                }
                                                // Also check for direct parts array in Rarities (some structures might have parts directly)
                                                if (partTypeData.parts && Array.isArray(partTypeData.parts)) {
                                                    console.log(`  Extracting ${partTypeData.parts.length} parts from ${currentPath} (direct parts array) (Type ID: ${currentTypeId})`);
                                                    for (const part of partTypeData.parts) {
                                                        const partInfo = extractPartInfo(part, currentTypeId, partTypeKey, 'Weapon', weaponType, manufacturer, weaponType);
                                                        if (partInfo) {
                                                            let targetTypeId = currentTypeId;
                                                            if (partInfo.fullId.includes(':')) {
                                                                const colonIndex = partInfo.fullId.indexOf(':');
                                                                const extractedTypeId = parseInt(partInfo.fullId.substring(0, colonIndex));
                                                                if (!isNaN(extractedTypeId)) {
                                                                    partInfo.typeId = extractedTypeId;
                                                                    targetTypeId = extractedTypeId;
                                                                    const afterColon = partInfo.fullId.substring(colonIndex + 1);
                                                                    partsMap.set(afterColon, partInfo);
                                                                    const numericPartId = parseInt(afterColon);
                                                                    if (!isNaN(numericPartId)) {
                                                                        partsMap.set(numericPartId, partInfo);
                                                                    }
                                                                }
                                                            } else {
                                                                partInfo.typeId = currentTypeId;
                                                                targetTypeId = currentTypeId;
                                                            }
                                                            
                                                            partsMap.set(partInfo.fullId, partInfo);
                                                            partsMap.set(partInfo.id, partInfo);
                                                            if (partInfo.spawnCode) {
                                                                partsMap.set(partInfo.spawnCode, partInfo);
                                                            }
                                                            if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                                                partsMap.set(partInfo.string, partInfo);
                                                            }
                                                            if (!partsByTypeId.has(targetTypeId)) {
                                                                partsByTypeId.set(targetTypeId, []);
                                                            }
                                                            partsByTypeId.get(targetTypeId).push(partInfo);
                                                            totalPartsExtracted++;
                                                            
                                                            // Debug log for comp parts
                                                            if ((partInfo.spawnCode && String(partInfo.spawnCode).includes('.comp_')) || (partInfo.string && String(partInfo.string).includes('.comp_'))) {
                                                                console.log(`    ✓ Extracted comp part: ${partInfo.name} (fullId: ${partInfo.fullId}, id: ${partInfo.id}, typeId: ${partInfo.typeId}, spawnCode: ${partInfo.spawnCode}, string: ${partInfo.string}, path: ${currentPath})`);
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                            // Recursively process nested part types (e.g., "Rarity" -> "Comp")
                                            // Check if partTypeData itself contains nested part types (but not parts array)
                                            if (partTypeData && typeof partTypeData === 'object' && !Array.isArray(partTypeData) && !partTypeData.parts) {
                                                const nestedKeys = Object.keys(partTypeData).filter(key => {
                                                    if (key === 'dlc' || key === 'count') return false;
                                                    const value = partTypeData[key];
                                                    return value && typeof value === 'object' && (value.parts || (typeof value === 'object' && Object.keys(value).some(k => k !== 'dlc' && k !== 'count')));
                                                });
                                                if (nestedKeys.length > 0) {
                                                    // This is a nested part type container (like "Rarity" containing "Comp")
                                                    console.log(`  Found nested part types in ${currentPath}: ${nestedKeys.join(', ')}. Recursively processing...`);
                                                    extractPartsRecursive(partTypeData, currentTypeId, currentPath);
                                                }
                                            }
                                            
                                            // Also check if this partTypeData itself has a Rarities section (nested within part_types)
                                            if (partTypeData.Rarities) {
                                                console.log(`  Found Rarity section at ${currentPath}.Rarities (Type ID: ${currentTypeId})`);
                                                const extractFromRarities = (raritiesData, currentTypeId) => {
                                                    for (const [rarityKey, rarityData] of Object.entries(raritiesData)) {
                                                        if (rarityData.parts && Array.isArray(rarityData.parts)) {
                                                            console.log(`  Extracting ${rarityData.parts.length} parts from ${currentPath}.Rarities.${rarityKey} (Type ID: ${currentTypeId})`);
                                                            for (const part of rarityData.parts) {
                                                                const partInfo = extractPartInfo(part, currentTypeId, rarityKey, 'Weapon', weaponType, manufacturer, weaponType);
                                                                if (partInfo) {
                                                                    let targetTypeId = currentTypeId;
                                                                    if (partInfo.fullId.includes(':')) {
                                                                        const colonIndex = partInfo.fullId.indexOf(':');
                                                                        const extractedTypeId = parseInt(partInfo.fullId.substring(0, colonIndex));
                                                                        if (!isNaN(extractedTypeId)) {
                                                                            partInfo.typeId = extractedTypeId;
                                                                            targetTypeId = extractedTypeId;
                                                                            const afterColon = partInfo.fullId.substring(colonIndex + 1);
                                                                            partsMap.set(afterColon, partInfo);
                                                                            const numericPartId = parseInt(afterColon);
                                                                            if (!isNaN(numericPartId)) {
                                                                                partsMap.set(numericPartId, partInfo);
                                                                            }
                                                                        }
                                                                    } else {
                                                                        partInfo.typeId = currentTypeId;
                                                                        targetTypeId = currentTypeId;
                                                                    }
                                                                    
                                                                    partsMap.set(partInfo.fullId, partInfo);
                                                                    partsMap.set(partInfo.id, partInfo);
                                                                    if (partInfo.spawnCode) {
                                                                        partsMap.set(partInfo.spawnCode, partInfo);
                                                                    }
                                                                    if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                                                        partsMap.set(partInfo.string, partInfo);
                                                                    }
                                                                    if (!partsByTypeId.has(targetTypeId)) {
                                                                        partsByTypeId.set(targetTypeId, []);
                                                                    }
                                                                    partsByTypeId.get(targetTypeId).push(partInfo);
                                                                    totalPartsExtracted++;
                                                                    
                                                                    // Debug log for comp parts
                                                                    if ((partInfo.spawnCode && String(partInfo.spawnCode).includes('.comp_')) || (partInfo.string && String(partInfo.string).includes('.comp_'))) {
                                                                        console.log(`    ✓ Extracted comp part: ${partInfo.name} (fullId: ${partInfo.fullId}, id: ${partInfo.id}, typeId: ${partInfo.typeId}, spawnCode: ${partInfo.spawnCode}, string: ${partInfo.string}, path: ${currentPath}.Rarities.${rarityKey})`);
                                                                    }
                                                                    // Debug log for part 7 in typeId 267
                                                                    if ((partInfo.id === '7' || partInfo.fullId === '267:7' || partInfo.id === 7) && (currentTypeId === 267 || targetTypeId === 267)) {
                                                                        console.log(`    ✓ Extracted part 7 from nested Rarities for typeId 267: ${partInfo.name} (fullId: ${partInfo.fullId}, id: ${partInfo.id}, typeId: ${partInfo.typeId}, targetTypeId: ${targetTypeId}, path: ${currentPath}.Rarities.${rarityKey})`);
                                                                    }
                                                                }
                                                            }
                                                        }
                                                        if (rarityData.part_types) {
                                                            extractFromRarities(rarityData.part_types, currentTypeId);
                                                        }
                                                    }
                                                };
                                                extractFromRarities(partTypeData.Rarities, currentTypeId);
                                            }
                                            // Recursively check nested part_types (like Rarities.Rarity)
                                            if (partTypeData.part_types) {
                                                extractPartsRecursive(partTypeData.part_types, currentTypeId, currentPath);
                                            }
                                        }
                                    };
                                    extractPartsRecursive(weaponData.part_types, typeId);
                                }
                            }
                        }
                    }
                }
            }

            // Extract typeID 1 element parts (primary elements, maliwan secondary, licensed underbarrel)
            // Always add typeId 1 to typeIdMap (even if no elements found, user might want to add manually)
            if (!typeIdMap.has(1)) {
                typeIdMap.set(1, {
                    id: 1,
                    name: 'Weapon Elements',
                    category: 'Element',
                    context: null,
                    manufacturer: null
                });
                console.log('Added type ID 1: Weapon Elements');
            }
            
            if (!partsByTypeId.has(1)) {
                partsByTypeId.set(1, []);
            }
            
            if (gameData.elements) {
                console.log('Found elements section');
                console.log('Elements keys:', Object.keys(gameData.elements));
                
                // Extract from primary elements
                if (gameData.elements.primary && gameData.elements.primary.parts && Array.isArray(gameData.elements.primary.parts)) {
                    console.log(`  Extracting ${gameData.elements.primary.parts.length} parts from elements.primary (Type ID: 1)`);
                    let extractedCount = 0;
                    for (const part of gameData.elements.primary.parts) {
                        // Handle element data structure - id might be "1:10" format
                        let elementId = part.id || part.part_id;
                        
                        // Debug: log first part to see structure
                        if (extractedCount === 0) {
                            console.log(`  [DEBUG] Sample element part structure:`, {
                                id: part.id,
                                name: part.name,
                                element_name: part.element_name,
                                spawn_code: part.spawn_code,
                                category: part.category
                            });
                        }
                        
                        // Ensure ID is in "1:X" format
                        if (elementId && !elementId.includes(':')) {
                            // If ID is just a number, prepend "1:"
                            const numericId = parseInt(elementId);
                            if (!isNaN(numericId)) {
                                elementId = `1:${numericId}`;
                            }
                        }
                        
                        // Create normalized part object for extractPartInfo
                        const normalizedPart = {
                            ...part,
                            id: elementId || part.id,
                            spawn_code: part.spawn_code || part.spawnCode,
                            name: part.name || part.element_name
                        };
                        
                        const partInfo = extractPartInfo(normalizedPart, 1, 'Element', 'Weapon', null, null, null);
                        if (partInfo) {
                            partInfo.typeId = 1;
                            partInfo.partType = 'Element';
                            partInfo.path = 'elements.primary';
                            partInfo.category = part.category || 'First element';
                            
                            // Ensure fullId is in format "1:X"
                            if (partInfo.id && partInfo.id.includes(':')) {
                                partInfo.fullId = partInfo.id;
                            } else if (partInfo.id) {
                                partInfo.fullId = `1:${partInfo.id}`;
                            } else if (elementId) {
                                partInfo.fullId = elementId;
                                partInfo.id = elementId;
                            }
                            
                            // Store with multiple key formats
                            partsMap.set(partInfo.fullId, partInfo);
                            partsMap.set(partInfo.id, partInfo);
                            if (partInfo.spawnCode) {
                                partsMap.set(partInfo.spawnCode, partInfo);
                            }
                            if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                partsMap.set(partInfo.string, partInfo);
                            }
                            
                            // Also store by the numeric part ID after colon
                            if (partInfo.fullId.includes(':')) {
                                const afterColon = partInfo.fullId.split(':')[1];
                                partsMap.set(afterColon, partInfo);
                                const numericPartId = parseInt(afterColon);
                                if (!isNaN(numericPartId)) {
                                    partsMap.set(numericPartId, partInfo);
                                }
                            }
                            
                            partsByTypeId.get(1).push(partInfo);
                            totalPartsExtracted++;
                            extractedCount++;
                            
                            // Debug: log first extracted part
                            if (extractedCount === 1) {
                                console.log(`  [DEBUG] First extracted element part:`, {
                                    id: partInfo.id,
                                    fullId: partInfo.fullId,
                                    name: partInfo.name,
                                    typeId: partInfo.typeId
                                });
                            }
                        } else {
                            console.warn(`  [WARNING] Failed to extract element part:`, part);
                        }
                    }
                    console.log(`  ✓ Extracted ${extractedCount} primary element parts`);
                } else {
                    console.log(`  [DEBUG] elements.primary.parts not found or not an array`);
                }
                
                // Extract from maliwan_secondary elements
                if (gameData.elements.maliwan_secondary && gameData.elements.maliwan_secondary.parts && Array.isArray(gameData.elements.maliwan_secondary.parts)) {
                    console.log(`  Extracting ${gameData.elements.maliwan_secondary.parts.length} parts from elements.maliwan_secondary (Type ID: 1)`);
                    for (const part of gameData.elements.maliwan_secondary.parts) {
                        const partInfo = extractPartInfo(part, 1, 'Element', 'Weapon', null, 'Maliwan', null);
                        if (partInfo) {
                            partInfo.typeId = 1;
                            partInfo.partType = 'Element';
                            partInfo.path = 'elements.maliwan_secondary';
                            partInfo.category = part.category || 'Second element on Maliwan weapons';
                            partInfo.manufacturer = 'Maliwan';
                            
                            // Ensure fullId is in format "1:X"
                            if (partInfo.id && partInfo.id.includes(':')) {
                                partInfo.fullId = partInfo.id;
                            } else if (partInfo.id) {
                                partInfo.fullId = `1:${partInfo.id}`;
                            }
                            
                            // Store with multiple key formats
                            partsMap.set(partInfo.fullId, partInfo);
                            partsMap.set(partInfo.id, partInfo);
                            if (partInfo.spawnCode) {
                                partsMap.set(partInfo.spawnCode, partInfo);
                            }
                            if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                partsMap.set(partInfo.string, partInfo);
                            }
                            
                            // Also store by the numeric part ID after colon
                            if (partInfo.fullId.includes(':')) {
                                const afterColon = partInfo.fullId.split(':')[1];
                                partsMap.set(afterColon, partInfo);
                                const numericPartId = parseInt(afterColon);
                                if (!isNaN(numericPartId)) {
                                    partsMap.set(numericPartId, partInfo);
                                }
                            }
                            
                            partsByTypeId.get(1).push(partInfo);
                            totalPartsExtracted++;
                        }
                    }
                }
                
                // Extract from licensed_underbarrel elements
                if (gameData.elements.licensed_underbarrel && gameData.elements.licensed_underbarrel.parts && Array.isArray(gameData.elements.licensed_underbarrel.parts)) {
                    console.log(`  Extracting ${gameData.elements.licensed_underbarrel.parts.length} parts from elements.licensed_underbarrel (Type ID: 1)`);
                    for (const part of gameData.elements.licensed_underbarrel.parts) {
                        const partInfo = extractPartInfo(part, 1, 'Element', 'Weapon', null, 'Maliwan', null);
                        if (partInfo) {
                            partInfo.typeId = 1;
                            partInfo.partType = 'Element';
                            partInfo.path = 'elements.licensed_underbarrel';
                            // Preserve the original category from the part data
                            partInfo.category = part.category || 'Maliwan Licenced Underbarrel';
                            partInfo.manufacturer = 'Maliwan';
                            
                            // Debug: Log parts with IDs 1:29-1:49 to verify they're being loaded
                            const partId = String(partInfo.id || partInfo.fullId || '');
                            if (partId.includes(':')) {
                                const idNum = parseInt(partId.split(':')[1]);
                                if (idNum >= 29 && idNum <= 49) {
                                    console.log(`  [DEBUG licensed_underbarrel] Loaded part ${partId}: ${partInfo.name} (spawnCode: ${partInfo.spawnCode}, category: ${partInfo.category})`);
                                }
                            }
                            
                            // Ensure fullId is in format "1:X"
                            if (partInfo.id && partInfo.id.includes(':')) {
                                partInfo.fullId = partInfo.id;
                            } else if (partInfo.id) {
                                partInfo.fullId = `1:${partInfo.id}`;
                            }
                            
                            // Store with multiple key formats
                            partsMap.set(partInfo.fullId, partInfo);
                            partsMap.set(partInfo.id, partInfo);
                            if (partInfo.spawnCode) {
                                partsMap.set(partInfo.spawnCode, partInfo);
                            }
                            if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                partsMap.set(partInfo.string, partInfo);
                            }
                            
                            // Also store by the numeric part ID after colon
                            if (partInfo.fullId.includes(':')) {
                                const afterColon = partInfo.fullId.split(':')[1];
                                partsMap.set(afterColon, partInfo);
                                const numericPartId = parseInt(afterColon);
                                if (!isNaN(numericPartId)) {
                                    partsMap.set(numericPartId, partInfo);
                                }
                            }
                            
                            partsByTypeId.get(1).push(partInfo);
                            totalPartsExtracted++;
                        }
                    }
                }
                
                // Always merge fallback parts to ensure all typeId 1 parts are available
                // This ensures parts 1:15-1:22 and 1:29-1:49 are always included even if gameData is incomplete
                console.log('  [DEBUG] Merging fallback element parts to ensure completeness...');
                const existingPartIds = new Set();
                partsByTypeId.get(1).forEach(p => {
                    const id = p.fullId || p.id;
                    if (id) existingPartIds.add(id);
                });
                
                // Licensed underbarrel elements (1:15 through 1:22 - older format with part_licensed_underbarrel)
                // AND parts 1:29 through 1:49 (newer format with part_secondary_elem)

                let fallbackMerged = 0;
                for (const element of licensedUnderbarrelElements) {
                    // Only add if not already present
                    if (!existingPartIds.has(element.id)) {
                        const normalizedPart = {
                            id: element.id,
                            spawn_code: element.spawnCode,
                            name: element.name,
                            element_name: element.name,
                            category: element.category
                        };
                        
                        const partInfo = extractPartInfo(normalizedPart, 1, 'Element', 'Weapon', null, element.manufacturer || null, null);
                        if (partInfo) {
                            partInfo.typeId = 1;
                            partInfo.partType = 'Element';
                            partInfo.path = 'elements.licensed_underbarrel';
                            partInfo.category = element.category;
                            if (element.manufacturer) {
                                partInfo.manufacturer = element.manufacturer;
                            }
                            
                            // Ensure fullId is in format "1:X"
                            partInfo.fullId = element.id;
                            partInfo.id = element.id;
                            
                            // Store with multiple key formats
                            partsMap.set(partInfo.fullId, partInfo);
                            partsMap.set(partInfo.id, partInfo);
                            if (partInfo.spawnCode) {
                                partsMap.set(partInfo.spawnCode, partInfo);
                            }
                            if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                partsMap.set(partInfo.string, partInfo);
                            }
                            
                            // Also store by the numeric part ID after colon
                            if (partInfo.fullId.includes(':')) {
                                const afterColon = partInfo.fullId.split(':')[1];
                                partsMap.set(afterColon, partInfo);
                                const numericPartId = parseInt(afterColon);
                                if (!isNaN(numericPartId)) {
                                    partsMap.set(numericPartId, partInfo);
                                }
                            }
                            
                            partsByTypeId.get(1).push(partInfo);
                            totalPartsExtracted++;
                            fallbackMerged++;
                            existingPartIds.add(element.id);
                        }
                    }
                }
                
                if (fallbackMerged > 0) {
                    console.log(`  ✓ Merged ${fallbackMerged} additional licensed underbarrel parts from fallback`);
                }
                
                const totalType1Parts = partsByTypeId.get(1).length;
                console.log(`  ✓ Extracted ${totalType1Parts} element parts for typeId 1`);
                
                // Always merge fallback resistance parts to ensure all typeId 246 resistance parts are available
                // This ensures parts 246:21-246:26 are always included even if gameData is incomplete
                if (partsByTypeId.has(246)) {
                    console.log('  [DEBUG] Merging fallback resistance parts to ensure completeness...');
                    const existingPartIds = new Set();
                    partsByTypeId.get(246).forEach(p => {
                        const id = p.fullId || p.id;
                        if (id) existingPartIds.add(id);
                    });
                    
                    // Resistance parts (246:21 through 246:26)
                    const resistanceParts = [
                        { id: '246:21', name: 'PLACEHOLDER', spawnCode: 'Shield.part_resistance', category: 'Resistance', stats: 'Included when no Elemental Resistance is used' },
                        { id: '246:22', name: 'Corrosive', spawnCode: 'Shield.part_corrosive', category: 'Resistance', stats: '15% Resist' },
                        { id: '246:23', name: 'Cryo', spawnCode: 'Shield.part_cryo', category: 'Resistance', stats: '15% Resist' },
                        { id: '246:24', name: 'Fire', spawnCode: 'Shield.part_fire', category: 'Resistance', stats: '15% Resist' },
                        { id: '246:25', name: 'Radiation', spawnCode: 'Shield.part_radiation', category: 'Resistance', stats: '15% Resist' },
                        { id: '246:26', name: 'Shock', spawnCode: 'Shield.part_shock', category: 'Resistance', stats: '15% Resist' }
                    ];
                    
                    let resistanceMerged = 0;
                    for (const resistance of resistanceParts) {
                        // Only add if not already present
                        if (!existingPartIds.has(resistance.id)) {
                            const normalizedPart = {
                                id: resistance.id,
                                spawn_code: resistance.spawnCode,
                                name: resistance.name,
                                model_name: resistance.name,
                                category: resistance.category,
                                stats: resistance.stats
                            };
                            
                            const partInfo = extractPartInfo(normalizedPart, 246, 'Resistance', 'Shield', null, null, null);
                            if (partInfo) {
                                partInfo.typeId = 246;
                                partInfo.partType = 'Resistance';
                                partInfo.path = 'gadgets.shields.Resistance';
                                partInfo.category = resistance.category;
                                
                                // Ensure fullId is in format "246:X"
                                partInfo.fullId = resistance.id;
                                partInfo.id = resistance.id;
                                
                                // Store with multiple key formats
                                partsMap.set(partInfo.fullId, partInfo);
                                partsMap.set(partInfo.id, partInfo);
                                if (partInfo.spawnCode) {
                                    partsMap.set(partInfo.spawnCode, partInfo);
                                }
                                if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                    partsMap.set(partInfo.string, partInfo);
                                }
                                
                                // Also store by the numeric part ID after colon
                                if (partInfo.fullId.includes(':')) {
                                    const afterColon = partInfo.fullId.split(':')[1];
                                    partsMap.set(afterColon, partInfo);
                                    const numericPartId = parseInt(afterColon);
                                    if (!isNaN(numericPartId)) {
                                        partsMap.set(numericPartId, partInfo);
                                    }
                                }
                                
                                partsByTypeId.get(246).push(partInfo);
                                totalPartsExtracted++;
                                resistanceMerged++;
                                existingPartIds.add(resistance.id);
                            }
                        }
                    }
                    
                    if (resistanceMerged > 0) {
                        console.log(`  ✓ Merged ${resistanceMerged} additional resistance parts from fallback`);
                    }
                }
                if (totalType1Parts > 0) {
                    console.log(`  [DEBUG] TypeID 1 parts sample:`, partsByTypeId.get(1).slice(0, 3).map(p => ({
                        id: p.id,
                        fullId: p.fullId,
                        name: p.name
                    })));
                } else {
                    console.warn(`  [WARNING] TypeID 1 has 0 parts! Check element extraction.`);
                }
            } else {
                console.log('  [DEBUG] No elements section found in gameData. Top-level keys:', Object.keys(gameData || {}));
                console.log('  [DEBUG] Using fallback: creating element parts from known structure...');
                
                // Fallback: Create element parts from known structure
                // Primary elements (1:10 through 1:14)
                const primaryElements = [
                    { id: '1:10', name: 'Corrosive', spawnCode: 'Weapon.part_corrosive', category: 'First element' },
                    { id: '1:11', name: 'Cryo', spawnCode: 'Weapon.part_cryo', category: 'First element' },
                    { id: '1:12', name: 'Fire', spawnCode: 'Weapon.part_fire', category: 'First element' },
                    { id: '1:13', name: 'Radiation', spawnCode: 'Weapon.part_radiation', category: 'First element' },
                    { id: '1:14', name: 'Shock', spawnCode: 'Weapon.part_shock', category: 'First element' }
                ];
                
                // Maliwan secondary elements (1:23 through 1:28)
                const maliwanSecondaryElements = [
                    { id: '1:23', name: 'Cryo/Fire', spawnCode: 'Weapon.part_secondary_elem_cryo_fire_mal', category: 'Second element on Maliwan weapons', manufacturer: 'Maliwan' },
                    { id: '1:24', name: 'Cryo/Corrosive', spawnCode: 'Weapon.part_secondary_elem_cryo_corrosive_mal', category: 'Second element on Maliwan weapons', manufacturer: 'Maliwan' },
                    { id: '1:25', name: 'Corrosive/Shock', spawnCode: 'Weapon.part_secondary_elem_corrosive_shock_mal', category: 'Second element on Maliwan weapons', manufacturer: 'Maliwan' },
                    { id: '1:26', name: 'Corrosive/Radiation', spawnCode: 'Weapon.part_secondary_elem_corrosive_radiation_mal', category: 'Second element on Maliwan weapons', manufacturer: 'Maliwan' },
                    { id: '1:27', name: 'Corrosive/Fire', spawnCode: 'Weapon.part_secondary_elem_corrosive_fire_mal', category: 'Second element on Maliwan weapons', manufacturer: 'Maliwan' },
                    { id: '1:28', name: 'Corrosive/Cryo', spawnCode: 'Weapon.part_secondary_elem_corrosive_cryo_mal', category: 'Second element on Maliwan weapons', manufacturer: 'Maliwan' }
                ];
                
                // Licensed underbarrel elements (1:15 through 1:22 - older format with part_licensed_underbarrel)
                // AND parts 1:29 through 1:49 (newer format with part_secondary_elem)
                const licensedUnderbarrelElements = [
                    { id: '1:15', name: 'Cryo/Shock', spawnCode: 'Weapon.part_licensed_underbarrel_cryo_shock', category: 'Maliwan Licenced Underbarrel', manufacturer: 'Maliwan' },
                    { id: '1:16', name: 'Fire/Shock', spawnCode: 'Weapon.part_licensed_underbarrel_fire_shock', category: 'Maliwan Licenced Underbarrel', manufacturer: 'Maliwan' },
                    { id: '1:17', name: 'Radiation/Shock', spawnCode: 'Weapon.part_licensed_underbarrel_radiation_shock', category: 'Maliwan Licenced Underbarrel', manufacturer: 'Maliwan' },
                    { id: '1:18', name: 'Corrosive/Shock', spawnCode: 'Weapon.part_licensed_underbarrel_corrosive_shock', category: 'Maliwan Licenced Underbarrel', manufacturer: 'Maliwan' },
                    { id: '1:19', name: 'Cryo/Radiation', spawnCode: 'Weapon.part_licensed_underbarrel_cryo_radiation', category: 'Maliwan Licenced Underbarrel', manufacturer: 'Maliwan' },
                    { id: '1:20', name: 'Fire/Radiation', spawnCode: 'Weapon.part_licensed_underbarrel_fire_radiation', category: 'Maliwan Licenced Underbarrel', manufacturer: 'Maliwan' },
                    { id: '1:21', name: 'Cryo/Fire', spawnCode: 'Weapon.part_licensed_underbarrel_cryo_fire', category: 'Maliwan Licenced Underbarrel', manufacturer: 'Maliwan' },
                    { id: '1:22', name: 'Corrosive/Radiation', spawnCode: 'Weapon.part_licensed_underbarrel_corrosive_radiation', category: 'Maliwan Licenced Underbarrel', manufacturer: 'Maliwan' },
                    // Additional licensed underbarrel parts (1:29 through 1:49) with part_secondary_elem spawn codes
                    { id: '1:29', name: 'Shock/Radiation', spawnCode: 'Weapon.part_secondary_elem_shock_radiation', category: 'Maliwan Licenced Underbarrel', manufacturer: 'Maliwan' },
                    { id: '1:30', name: 'Fire Radiation', spawnCode: 'Weapon.part_secondary_elem_fire_radiation', category: 'Maliwan Licenced Underbarrel', manufacturer: 'Maliwan' },
                    { id: '1:31', name: 'Cryo/Radiation', spawnCode: 'Weapon.part_secondary_elem_cryo_radiation', category: 'Maliwan Licenced Underbarrel', manufacturer: 'Maliwan' },
                    { id: '1:32', name: 'Corrosive/Radiation', spawnCode: 'Weapon.part_secondary_elem_corrosive_radiation', category: 'Maliwan Licenced Underbarrel', manufacturer: 'Maliwan' },
                    { id: '1:33', name: 'Radiation/Corrosive', spawnCode: 'Weapon.part_secondary_elem_radiation_corrosive', category: 'Maliwan Licenced Underbarrel', manufacturer: 'Maliwan' },
                    { id: '1:34', name: 'Shock/Corrosive', spawnCode: 'Weapon.part_secondary_elem_shock_corrosive', category: 'Maliwan Licenced Underbarrel', manufacturer: 'Maliwan' },
                    { id: '1:35', name: 'Fire/Corrosive', spawnCode: 'Weapon.part_secondary_elem_fire_corrosive', category: 'Maliwan Licenced Underbarrel', manufacturer: 'Maliwan' },
                    { id: '1:36', name: 'Cryo/Corrosive', spawnCode: 'Weapon.part_secondary_elem_cryo_corrosive', category: 'Maliwan Licenced Underbarrel', manufacturer: 'Maliwan' },
                    { id: '1:37', name: 'Radiation/Cryo', spawnCode: 'Weapon.part_secondary_elem_radiation_cryo', category: 'Maliwan Licenced Underbarrel', manufacturer: 'Maliwan' },
                    { id: '1:38', name: 'Shock/Cryo', spawnCode: 'Weapon.part_secondary_elem_shock_cryo', category: 'Maliwan Licenced Underbarrel', manufacturer: 'Maliwan' },
                    { id: '1:39', name: 'Fire/Cryo', spawnCode: 'Weapon.part_secondary_elem_fire_cryo', category: 'Maliwan Licenced Underbarrel', manufacturer: 'Maliwan' },
                    { id: '1:40', name: 'Corrosive/Cryo', spawnCode: 'Weapon.part_secondary_elem_corrosive_cryo', category: 'Maliwan Licenced Underbarrel', manufacturer: 'Maliwan' },
                    { id: '1:41', name: 'Radiation/Fire', spawnCode: 'Weapon.part_secondary_elem_radiation_fire', category: 'Maliwan Licenced Underbarrel', manufacturer: 'Maliwan' },
                    { id: '1:42', name: 'Cryo/Fire', spawnCode: 'Weapon.part_secondary_elem_cryo_fire', category: 'Maliwan Licenced Underbarrel', manufacturer: 'Maliwan' },
                    { id: '1:43', name: 'Shock/Fire', spawnCode: 'Weapon.part_secondary_elem_shock_fire', category: 'Maliwan Licenced Underbarrel', manufacturer: 'Maliwan' },
                    { id: '1:44', name: 'Corrosive/Fire', spawnCode: 'Weapon.part_secondary_elem_corrosive_fire', category: 'Maliwan Licenced Underbarrel', manufacturer: 'Maliwan' },
                    { id: '1:45', name: 'Radiation/Shock', spawnCode: 'Weapon.part_secondary_elem_radiation_shock', category: 'Maliwan Licenced Underbarrel', manufacturer: 'Maliwan' },
                    { id: '1:46', name: 'Cryo/Shock', spawnCode: 'Weapon.part_secondary_elem_cryo_shock', category: 'Maliwan Licenced Underbarrel', manufacturer: 'Maliwan' },
                    { id: '1:47', name: 'Corrosive/Shock', spawnCode: 'Weapon.part_secondary_elem_corrosive_shock', category: 'Maliwan Licenced Underbarrel', manufacturer: 'Maliwan' },
                    { id: '1:49', name: 'Fire/Shock', spawnCode: 'Weapon.part_secondary_elem_fire_shock', category: 'Maliwan Licenced Underbarrel', manufacturer: 'Maliwan' },
                    // Pearl override elements (1:55 through 1:60) - Maliwan Licenced Underbarrel
                    { id: '1:55', name: 'Kinetic Override', spawnCode: 'Weapon.pearl_normal', category: 'Maliwan Licenced Underbarrel', manufacturer: 'Maliwan' },
                    { id: '1:56', name: 'Shock Override', spawnCode: 'Weapon.pearl_shock', category: 'Maliwan Licenced Underbarrel', manufacturer: 'Maliwan' },
                    { id: '1:57', name: 'Radiation Override', spawnCode: 'Weapon.pearl_radiation', category: 'Maliwan Licenced Underbarrel', manufacturer: 'Maliwan' },
                    { id: '1:58', name: 'Corrosive Override', spawnCode: 'Weapon.pearl_corrosive', category: 'Maliwan Licenced Underbarrel', manufacturer: 'Maliwan' },
                    { id: '1:59', name: 'Cryo Override', spawnCode: 'Weapon.pearl_cryo', category: 'Maliwan Licenced Underbarrel', manufacturer: 'Maliwan' },
                    { id: '1:60', name: 'Incendiary Override', spawnCode: 'Weapon.pearl_fire', category: 'Maliwan Licenced Underbarrel', manufacturer: 'Maliwan' }
                ];
                
                // Process all element arrays
                const allElements = [...primaryElements, ...maliwanSecondaryElements, ...licensedUnderbarrelElements];
                let fallbackExtracted = 0;
                
                for (const element of allElements) {
                    const normalizedPart = {
                        id: element.id,
                        spawn_code: element.spawnCode,
                        name: element.name,
                        element_name: element.name,
                        category: element.category
                    };
                    
                    const partInfo = extractPartInfo(normalizedPart, 1, 'Element', 'Weapon', null, element.manufacturer || null, null);
                    if (partInfo) {
                        partInfo.typeId = 1;
                        partInfo.partType = 'Element';
                        // Set path based on category - licensed underbarrel parts go to elements.licensed_underbarrel
                        if (element.manufacturer) {
                            if (element.category.includes('Second')) {
                                partInfo.path = 'elements.maliwan_secondary';
                            } else if (element.category.includes('Licenced') || element.category.includes('Licensed')) {
                                partInfo.path = 'elements.licensed_underbarrel';
                            } else {
                                partInfo.path = 'elements.licensed_underbarrel'; // Default for Maliwan manufacturer parts
                            }
                        } else {
                            partInfo.path = 'elements.primary';
                        }
                        partInfo.category = element.category;
                        if (element.manufacturer) {
                            partInfo.manufacturer = element.manufacturer;
                        }
                        
                        // Ensure fullId is in format "1:X"
                        partInfo.fullId = element.id;
                        partInfo.id = element.id;
                        
                        // Store with multiple key formats
                        partsMap.set(partInfo.fullId, partInfo);
                        partsMap.set(partInfo.id, partInfo);
                        if (partInfo.spawnCode) {
                            partsMap.set(partInfo.spawnCode, partInfo);
                        }
                        if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                            partsMap.set(partInfo.string, partInfo);
                        }
                        
                        // Also store by the numeric part ID after colon
                        if (partInfo.fullId.includes(':')) {
                            const afterColon = partInfo.fullId.split(':')[1];
                            partsMap.set(afterColon, partInfo);
                            const numericPartId = parseInt(afterColon);
                            if (!isNaN(numericPartId)) {
                                partsMap.set(numericPartId, partInfo);
                            }
                        }
                        
                        partsByTypeId.get(1).push(partInfo);
                        totalPartsExtracted++;
                        fallbackExtracted++;
                    }
                }
                
                // Universal Stat Modifiers (1:51–1:54) – show in Stat Modifier dropdown for any item that has that slot
                const universalStatModifiers = [
                    { id: '1:51', name: 'Pearl Damage', spawnCode: 'Weapon.pearl_damage', category: 'Universal Stat Modifier' },
                    { id: '1:52', name: 'Pearl Reload', spawnCode: 'Weapon.pearl_reload', category: 'Universal Stat Modifier' },
                    { id: '1:53', name: 'Pearl Fire Rate', spawnCode: 'Weapon.pearl_firerate', category: 'Universal Stat Modifier' },
                    { id: '1:54', name: 'Pearl Handling', spawnCode: 'Weapon.pearl_handling', category: 'Universal Stat Modifier' }
                ];
                for (const mod of universalStatModifiers) {
                    const normalizedPart = {
                        id: mod.id,
                        spawn_code: mod.spawnCode,
                        name: mod.name,
                        category: mod.category
                    };
                    const partInfo = extractPartInfo(normalizedPart, 1, 'stat modifier', mod.category, null, null, null);
                    if (partInfo) {
                        partInfo.typeId = 1;
                        partInfo.partType = 'stat modifier';
                        partInfo.path = 'universal_stat_modifier';
                        partInfo.category = mod.category;
                        partInfo.fullId = mod.id;
                        partInfo.id = mod.id;
                        partsMap.set(partInfo.fullId, partInfo);
                        partsMap.set(partInfo.id, partInfo);
                        if (partInfo.spawnCode) partsMap.set(partInfo.spawnCode, partInfo);
                        if (partInfo.fullId.includes(':')) {
                            const afterColon = partInfo.fullId.split(':')[1];
                            partsMap.set(afterColon, partInfo);
                            const numericPartId = parseInt(afterColon, 10);
                            if (!isNaN(numericPartId)) partsMap.set(numericPartId, partInfo);
                        }
                        partsByTypeId.get(1).push(partInfo);
                        totalPartsExtracted++;
                    }
                }
                
                console.log(`  ✓ Extracted ${fallbackExtracted} element parts from fallback data`);
                console.log('  [DEBUG] TypeID 1 still added to typeIdMap for manual part entry');
            }
            
            // Verify typeID 1 is in typeIdMap
            if (typeIdMap.has(1)) {
                console.log('✓ TypeID 1 verified in typeIdMap:', typeIdMap.get(1));
            } else {
                console.error('✗ ERROR: TypeID 1 NOT in typeIdMap after extraction!');
            }
            
            // Final verification: Log summary of typeId 1 parts
            if (partsByTypeId.has(1)) {
                const type1Parts = partsByTypeId.get(1);
                console.log(`[SUMMARY] Total typeId 1 parts extracted: ${type1Parts.length}`);
                if (type1Parts.length > 0) {
                    const sampleIds = type1Parts.slice(0, 5).map(p => p.fullId || p.id);
                    console.log(`[SUMMARY] Sample part IDs:`, sampleIds);
                } else {
                    console.warn(`[WARNING] typeId 1 parts array is empty! Parts may not have been extracted.`);
                }
            } else {
                console.warn(`[WARNING] typeId 1 not found in partsByTypeId! Extraction may have failed.`);
            }

            // Extract from characters/class mods
            if (gameData.characters) {
                console.log('Checking characters section...');
                for (const [charName, charData] of Object.entries(gameData.characters)) {
                    console.log(`Processing character: ${charName}`);
                    if (charData.class_mods) {
                        console.log(`  Found class_mods for ${charName}`);
                        const classModKeys = Object.keys(charData.class_mods);
                        console.log(`  class_mods keys:`, classModKeys);
                        
                        // Extract typeId 234 parts from Substats section (Perk and Firmware)
                        // Also check for Perk and Firmware at class_mods level (not nested in Substats)
                        const substats = charData.class_mods.Substats || charData.class_mods.substats;
                        const perkAtTopLevel = charData.class_mods.Perk || charData.class_mods.perk;
                        const firmwareAtTopLevel = charData.class_mods.Firmware || charData.class_mods.firmware;
                        
                        if (substats) {
                            console.log(`  Found Substats section for ${charName}`);
                            console.log(`  Substats keys:`, Object.keys(substats || {}));
                        } else {
                            console.log(`  [DEBUG] No Substats section found for ${charName}. class_mods keys:`, classModKeys);
                        }
                        if (perkAtTopLevel) {
                            console.log(`  Found Perk section at top level for ${charName}`);
                        }
                        if (firmwareAtTopLevel) {
                            console.log(`  Found Firmware section at top level for ${charName}`);
                        }
                        
                        // More aggressive search: look for any section that might contain typeId 234 parts
                        // Check all keys in class_mods for potential Perk/Firmware sections
                        for (const [key, value] of Object.entries(charData.class_mods)) {
                            const keyLower = key.toLowerCase();
                            if ((keyLower.includes('perk') || keyLower.includes('firmware') || keyLower.includes('substat')) && 
                                value && typeof value === 'object' && !Array.isArray(value)) {
                                console.log(`  [DEBUG] Found potential typeId 234 section: ${key} for ${charName}`);
                                if (value.parts && Array.isArray(value.parts)) {
                                    console.log(`  [DEBUG] Section ${key} has ${value.parts.length} parts`);
                                    // Check if any parts have typeId 234
                                    const has234Parts = value.parts.some(p => {
                                        const partId = String(p.id || '');
                                        return partId.startsWith('234:') || p.type_id === 234 || value.type_id === 234;
                                    });
                                    if (has234Parts) {
                                        console.log(`  [DEBUG] Section ${key} contains typeId 234 parts!`);
                                    }
                                }
                            }
                        }
                        
                        // Try extracting from Substats first
                        if (substats) {
                            
                            // Check for Perk subsection
                            if (substats.Perk || substats.perk) {
                                const perkData = substats.Perk || substats.perk;
                                if (perkData.parts && Array.isArray(perkData.parts)) {
                                    console.log(`    Extracting ${perkData.parts.length} Perk parts from Substats for ${charName}`);
                                    
                                    // Add typeId 234 to typeIdMap if not already present
                                    if (!typeIdMap.has(234)) {
                                        typeIdMap.set(234, {
                                            id: 234,
                                            name: 'Class Mod Substats',
                                            category: 'Class Mod',
                                            context: null,
                                            manufacturer: null
                                        });
                                        console.log(`Added type ID 234: Class Mod Substats`);
                                    }
                                    
                                    if (!partsByTypeId.has(234)) {
                                        partsByTypeId.set(234, []);
                                    }
                                    
                                    // Extract all Perk parts
                                    for (const part of perkData.parts) {
                                        // Extract parts with typeId 234
                                        // Check if part.id starts with "234:" OR if part has type_id === 234 OR if part.id is numeric and we're in a typeId 234 section
                                        const partIdStr = part.id ? String(part.id) : '';
                                        const has234Id = partIdStr.startsWith('234:');
                                        const hasTypeId234 = part.type_id === 234 || perkData.type_id === 234;
                                        const isNumericId = /^\d+$/.test(partIdStr);
                                        
                                        if (has234Id || (hasTypeId234 && (isNumericId || !partIdStr.includes(':')))) {
                                            // If part.id is just a number, normalize it to "234:X" format
                                            let normalizedPart = part;
                                            if (isNumericId && !has234Id) {
                                                normalizedPart = {...part, id: `234:${partIdStr}`};
                                            }
                                            
                                            const partInfo = extractPartInfo(normalizedPart, 234, 'Perk', 'Class Mod', charName, null, null);
                                            if (partInfo) {
                                                // Ensure typeId is set to 234 and partType is 'Perk'
                                                partInfo.typeId = 234;
                                                partInfo.partType = 'Perk';
                                                partInfo.path = 'Substats.Perk';
                                                
                                                // Store with multiple key formats
                                                partsMap.set(partInfo.fullId, partInfo);
                                                partsMap.set(partInfo.id, partInfo);
                                                if (partInfo.spawnCode) {
                                                    partsMap.set(partInfo.spawnCode, partInfo);
                                                }
                                                if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                                    partsMap.set(partInfo.string, partInfo);
                                                }
                                                
                                                // Also store by the numeric part ID after colon
                                                if (partInfo.fullId.includes(':')) {
                                                    const afterColon = partInfo.fullId.split(':')[1];
                                                    partsMap.set(afterColon, partInfo);
                                                    const numericPartId = parseInt(afterColon);
                                                    if (!isNaN(numericPartId)) {
                                                        partsMap.set(numericPartId, partInfo);
                                                    }
                                                }
                                                
                                                partsByTypeId.get(234).push(partInfo);
                                                totalPartsExtracted++;
                                                
                                                // Debug: Log first few parts
                                                if (DEBUG && partsByTypeId.get(234).filter(p => p.partType === 'Perk').length <= 3) {
                                                    console.log(`      [DEBUG] Stored Perk part: fullId=${partInfo.fullId}, id=${partInfo.id}, name=${partInfo.name}`);
                                                }
                                            }
                                        }
                                    }
                                    console.log(`    ✓ Extracted ${partsByTypeId.get(234).filter(p => p.partType === 'Perk').length} Perk parts for typeId 234`);
                                }
                            }
                            
                            // Check for Firmware subsection
                            if (substats.Firmware || substats.firmware) {
                                const firmwareData = substats.Firmware || substats.firmware;
                                if (firmwareData.parts && Array.isArray(firmwareData.parts)) {
                                    console.log(`    Extracting ${firmwareData.parts.length} Firmware parts from Substats for ${charName}`);
                                    
                                    // Add typeId 234 to typeIdMap if not already present
                                    if (!typeIdMap.has(234)) {
                                        typeIdMap.set(234, {
                                            id: 234,
                                            name: 'Class Mod Substats',
                                            category: 'Class Mod',
                                            context: null,
                                            manufacturer: null
                                        });
                                        console.log(`Added type ID 234: Class Mod Substats`);
                                    }
                                    
                                    if (!partsByTypeId.has(234)) {
                                        partsByTypeId.set(234, []);
                                    }
                                    
                                    // Extract all Firmware parts
                                    for (const part of firmwareData.parts) {
                                        // Extract parts with typeId 234
                                        // Check if part.id starts with "234:" OR if part has type_id === 234 OR if part.id is numeric and we're in a typeId 234 section
                                        const partIdStr = part.id ? String(part.id) : '';
                                        const has234Id = partIdStr.startsWith('234:');
                                        const hasTypeId234 = part.type_id === 234 || firmwareData.type_id === 234;
                                        const isNumericId = /^\d+$/.test(partIdStr);
                                        
                                        if (has234Id || (hasTypeId234 && (isNumericId || !partIdStr.includes(':')))) {
                                            // If part.id is just a number, normalize it to "234:X" format
                                            let normalizedPart = part;
                                            if (isNumericId && !has234Id) {
                                                normalizedPart = {...part, id: `234:${partIdStr}`};
                                            }
                                            
                                            const partInfo = extractPartInfo(normalizedPart, 234, 'Firmware', 'Class Mod', charName, null, null);
                                            if (partInfo) {
                                                // Ensure typeId is set to 234 and partType is 'Firmware'
                                                partInfo.typeId = 234;
                                                partInfo.partType = 'Firmware';
                                                partInfo.path = 'Substats.Firmware';
                                                
                                                // Store with multiple key formats
                                                partsMap.set(partInfo.fullId, partInfo);
                                                partsMap.set(partInfo.id, partInfo);
                                                if (partInfo.spawnCode) {
                                                    partsMap.set(partInfo.spawnCode, partInfo);
                                                }
                                                if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                                    partsMap.set(partInfo.string, partInfo);
                                                }
                                                
                                                // Also store by the numeric part ID after colon
                                                if (partInfo.fullId.includes(':')) {
                                                    const afterColon = partInfo.fullId.split(':')[1];
                                                    partsMap.set(afterColon, partInfo);
                                                    const numericPartId = parseInt(afterColon);
                                                    if (!isNaN(numericPartId)) {
                                                        partsMap.set(numericPartId, partInfo);
                                                    }
                                                }
                                                
                                                partsByTypeId.get(234).push(partInfo);
                                                totalPartsExtracted++;
                                                
                                                // Debug: Log first few parts
                                                if (DEBUG && partsByTypeId.get(234).filter(p => p.partType === 'Firmware').length <= 3) {
                                                    console.log(`      [DEBUG] Stored Firmware part: fullId=${partInfo.fullId}, id=${partInfo.id}, name=${partInfo.name}`);
                                                }
                                            }
                                        }
                                    }
                                    console.log(`    ✓ Extracted ${partsByTypeId.get(234).filter(p => p.partType === 'Firmware').length} Firmware parts for typeId 234`);
                                }
                            }
                        }
                        
                        // Also try extracting from top-level Perk and Firmware sections
                        if (perkAtTopLevel && perkAtTopLevel.parts && Array.isArray(perkAtTopLevel.parts)) {
                            console.log(`    Extracting ${perkAtTopLevel.parts.length} Perk parts from top-level for ${charName}`);
                            
                            if (!typeIdMap.has(234)) {
                                typeIdMap.set(234, {
                                    id: 234,
                                    name: 'Class Mod Substats',
                                    category: 'Class Mod',
                                    context: null,
                                    manufacturer: null
                                });
                            }
                            
                            if (!partsByTypeId.has(234)) {
                                partsByTypeId.set(234, []);
                            }
                            
                            for (const part of perkAtTopLevel.parts) {
                                const partIdStr = part.id ? String(part.id) : '';
                                const has234Id = partIdStr.startsWith('234:');
                                const hasTypeId234 = part.type_id === 234 || perkAtTopLevel.type_id === 234;
                                const isNumericId = /^\d+$/.test(partIdStr);
                                
                                if (has234Id || (hasTypeId234 && (isNumericId || !partIdStr.includes(':')))) {
                                    let normalizedPart = part;
                                    if (isNumericId && !has234Id) {
                                        normalizedPart = {...part, id: `234:${partIdStr}`};
                                    }
                                    
                                    const partInfo = extractPartInfo(normalizedPart, 234, 'Perk', 'Class Mod', charName, null, null);
                                    if (partInfo) {
                                        partInfo.typeId = 234;
                                        partInfo.partType = 'Perk';
                                        partInfo.path = 'Perk';
                                        
                                        partsMap.set(partInfo.fullId, partInfo);
                                        partsMap.set(partInfo.id, partInfo);
                                        if (partInfo.fullId.includes(':')) {
                                            const afterColon = partInfo.fullId.split(':')[1];
                                            partsMap.set(afterColon, partInfo);
                                            const numericPartId = parseInt(afterColon);
                                            if (!isNaN(numericPartId)) {
                                                partsMap.set(numericPartId, partInfo);
                                            }
                                        }
                                        
                                        partsByTypeId.get(234).push(partInfo);
                                        totalPartsExtracted++;
                                    }
                                }
                            }
                            console.log(`    ✓ Extracted ${partsByTypeId.get(234).filter(p => p.partType === 'Perk').length} Perk parts from top-level for typeId 234`);
                        }
                        
                        if (firmwareAtTopLevel && firmwareAtTopLevel.parts && Array.isArray(firmwareAtTopLevel.parts)) {
                            console.log(`    Extracting ${firmwareAtTopLevel.parts.length} Firmware parts from top-level for ${charName}`);
                            
                            if (!typeIdMap.has(234)) {
                                typeIdMap.set(234, {
                                    id: 234,
                                    name: 'Class Mod Substats',
                                    category: 'Class Mod',
                                    context: null,
                                    manufacturer: null
                                });
                            }
                            
                            if (!partsByTypeId.has(234)) {
                                partsByTypeId.set(234, []);
                            }
                            
                            for (const part of firmwareAtTopLevel.parts) {
                                const partIdStr = part.id ? String(part.id) : '';
                                const has234Id = partIdStr.startsWith('234:');
                                const hasTypeId234 = part.type_id === 234 || firmwareAtTopLevel.type_id === 234;
                                const isNumericId = /^\d+$/.test(partIdStr);
                                
                                if (has234Id || (hasTypeId234 && (isNumericId || !partIdStr.includes(':')))) {
                                    let normalizedPart = part;
                                    if (isNumericId && !has234Id) {
                                        normalizedPart = {...part, id: `234:${partIdStr}`};
                                    }
                                    
                                    const partInfo = extractPartInfo(normalizedPart, 234, 'Firmware', 'Class Mod', charName, null, null);
                                    if (partInfo) {
                                        partInfo.typeId = 234;
                                        partInfo.partType = 'Firmware';
                                        partInfo.path = 'Firmware';
                                        
                                        partsMap.set(partInfo.fullId, partInfo);
                                        partsMap.set(partInfo.id, partInfo);
                                        if (partInfo.fullId.includes(':')) {
                                            const afterColon = partInfo.fullId.split(':')[1];
                                            partsMap.set(afterColon, partInfo);
                                            const numericPartId = parseInt(afterColon);
                                            if (!isNaN(numericPartId)) {
                                                partsMap.set(numericPartId, partInfo);
                                            }
                                        }
                                        
                                        partsByTypeId.get(234).push(partInfo);
                                        totalPartsExtracted++;
                                    }
                                }
                            }
                            console.log(`    ✓ Extracted ${partsByTypeId.get(234).filter(p => p.partType === 'Firmware').length} Firmware parts from top-level for typeId 234`);
                        }
                        
                        // Check for any section that might contain typeId 234 parts (Substats, Perks, etc.)
                        // Look through all keys in class_mods for sections that might have typeId 234 parts
                        for (const [key, value] of Object.entries(charData.class_mods)) {
                            if (key !== 'part_types' && typeof value === 'object' && value !== null) {
                                // Check if this section has parts with typeId 234
                                const checkForTypeId234 = (obj, path = key) => {
                                    if (Array.isArray(obj)) {
                                        for (const item of obj) {
                                            if (item && typeof item === 'object') {
                                                if (item.id && String(item.id).startsWith('234:')) {
                                                    console.log(`  [DEBUG] Found typeId 234 part in ${path}:`, item);
                                                }
                                                checkForTypeId234(item, path);
                                            }
                                        }
                                    } else if (obj && typeof obj === 'object') {
                                        if (obj.parts && Array.isArray(obj.parts)) {
                                            for (const part of obj.parts) {
                                                if (part && part.id && String(part.id).startsWith('234:')) {
                                                    console.log(`  [DEBUG] Found typeId 234 part in ${path}.parts:`, part);
                                                }
                                            }
                                        }
                                        for (const [subKey, subValue] of Object.entries(obj)) {
                                            if (subKey !== 'type_id' && typeof subValue === 'object' && subValue !== null) {
                                                checkForTypeId234(subValue, `${path}.${subKey}`);
                                            }
                                        }
                                    }
                                };
                                checkForTypeId234(value, key);
                            }
                        }
                        
                        // Handle both old format (part_types wrapper) and new format (direct keys)
                        if (charData.class_mods.part_types) {
                            // Old format: has part_types wrapper
                            extractFromPartTypes(charData.class_mods.part_types, 'Class Mod', charName);
                            
                            // Check if Skills is inside part_types
                            console.log(`  Checking part_types for Skills...`);
                            if (charData.class_mods.part_types.Skills || charData.class_mods.part_types.skills) {
                                console.log(`  Found Skills inside part_types!`);
                            }
                        } else {
                            // New format: direct keys (Body, Rarity, Skills, etc.)
                            // Process class_mods as if it were part_types
                            extractFromPartTypes(charData.class_mods, 'Class Mod', charName);
                        }
                        
                        // Extract from Skills section (passives for class mods)
                        // Check at class_mods level
                        let skillsData = charData.class_mods.Skills || charData.class_mods.skills;
                        
                        // Also check inside part_types if not found at top level
                        if (!skillsData && charData.class_mods.part_types) {
                            skillsData = charData.class_mods.part_types.Skills || charData.class_mods.part_types.skills;
                            if (skillsData) {
                                console.log(`  Found Skills inside part_types for ${charName}`);
                            }
                        }
                        
                        // Also check all keys in part_types for Skills
                        if (!skillsData && charData.class_mods.part_types) {
                            const partTypesKeys = Object.keys(charData.class_mods.part_types);
                            console.log(`  part_types keys:`, partTypesKeys);
                            for (const key of partTypesKeys) {
                                if (key.toLowerCase().includes('skill')) {
                                    console.log(`  Found potential Skills key: ${key}`);
                                    skillsData = charData.class_mods.part_types[key];
                                    break;
                                }
                            }
                        }
                        
                        if (skillsData) {
                            console.log(`  Found Skills section for ${charName}:`, skillsData);
                            const skillsTypeId = skillsData.type_id;
                            
                            if (skillsTypeId) {
                                console.log(`  Skills Type ID: ${skillsTypeId}`);
                                // Normalize character name for consistency (use VH names)
                                // Map "Siren" to "Vex" for consistency with other class mods
                                let normalizedCharName = charName;
                                if (charName && charName.toLowerCase() === 'siren') {
                                    normalizedCharName = 'Vex';
                                }
                                
                                // Add type ID for Class Mod (use normalized character name as manufacturer)
                                if (!typeIdMap.has(skillsTypeId)) {
                                    typeIdMap.set(skillsTypeId, {
                                        id: skillsTypeId,
                                        name: `${normalizedCharName} Class Mod`,
                                        category: 'Class Mod',
                                        context: normalizedCharName,
                                        manufacturer: normalizedCharName  // Use normalized character name (Vex, Amon, Rafa, Harlowe)
                                    });
                                    console.log(`Added type ID ${skillsTypeId}: ${normalizedCharName} Class Mod`);
                                } else {
                                    // Update existing entry to ensure correct name and manufacturer
                                    const existing = typeIdMap.get(skillsTypeId);
                                    if (existing) {
                                        existing.name = `${normalizedCharName} Class Mod`;
                                        existing.manufacturer = normalizedCharName;
                                        existing.context = normalizedCharName;
                                    }
                                }
                                
                                if (!partsByTypeId.has(skillsTypeId)) {
                                    partsByTypeId.set(skillsTypeId, []);
                                }
                                
                                // Extract skills parts
                                if (skillsData.parts && Array.isArray(skillsData.parts)) {
                                    console.log(`Extracting ${skillsData.parts.length} skills for ${charName} (Type ID ${skillsTypeId})`);
                                    for (const skill of skillsData.parts) {
                                        // First, store the skill by its skill_name for reference
                                        const skillInfo = {
                                            id: String(skill.skill_name || skill.id || ''),
                                            fullId: `${skillsTypeId}:${skill.skill_name || skill.id || ''}`,
                                            typeId: skillsTypeId,
                                            name: skill.name || skill.skill_name || 'Unknown Skill',
                                            spawnCode: skill.branch || '',
                                            stats: skill.description || '',
                                            effects: skill.colors || '',
                                            partType: 'Skill',
                                            category: 'Class Mod',
                                            context: charName,
                                            manufacturer: charName,
                                            weaponType: skill.tree_name || '',
                                            legendaryName: '',
                                            perkName: skill.skill_name || '',
                                            rarity: '',
                                            string: skill.skill_name || '',
                                            type: 'skill',
                                            skillName: skill.skill_name || '',
                                            treeName: skill.tree_name || '',
                                            description: skill.description || '',
                                            limiter: skill.limiter || '',
                                            colors: skill.colors || '',
                                            skillIds: skill.skill_ids || {}
                                        };
                                        
                                        // Store with multiple key formats
                                        partsMap.set(skillInfo.fullId, skillInfo);
                                        partsMap.set(skillInfo.id, skillInfo);
                                        
                                        // Add to typeId-specific map
                                        partsByTypeId.get(skillsTypeId).push(skillInfo);
                                        totalPartsExtracted++;
                                        console.log(`  - Added skill: ${skillInfo.name} (${skillInfo.id})`);
                                        
                                        // CRITICAL: Extract each tier ID from skill_ids so they can be looked up by numeric ID
                                        // This allows {27}, {28}, etc. in item codes to find the skill
                                        if (skill.skill_ids && typeof skill.skill_ids === 'object') {
                                            for (const [tierKey, tierData] of Object.entries(skill.skill_ids)) {
                                                // Skip 'dlc' field and other non-tier keys
                                                if (tierKey === 'dlc' || !tierData || typeof tierData !== 'object' || !tierData.id) {
                                                    continue;
                                                }
                                                
                                                const tierId = tierData.id;
                                                const tierBranch = tierData.branch || '';
                                                
                                                // Create a part entry for each tier ID (these are the IDs used in item codes)
                                                const tierPartInfo = {
                                                    id: String(tierId),
                                                    fullId: `${skillsTypeId}:${tierId}`,  // Use skillsTypeId (254 or 255)
                                                    typeId: skillsTypeId,  // Use the skills typeId, not a separate one
                                                    name: `${skill.name || skill.skill_name || 'Unknown Skill'} (${tierKey.replace('tier_', 'Tier ')})`,
                                                    spawnCode: tierBranch,
                                                    stats: skill.description || '',
                                                    effects: skill.colors || '',
                                                    partType: 'Skill',
                                                    category: 'Class Mod',
                                                    context: charName,
                                                    manufacturer: charName,
                                                    weaponType: skill.tree_name || '',
                                                    legendaryName: '',
                                                    perkName: skill.skill_name || '',
                                                    rarity: tierKey.replace('tier_', ''),
                                                    string: skill.skill_name || '',
                                                    type: 'skill',
                                                    skillName: skill.skill_name || '',
                                                    treeName: skill.tree_name || '',
                                                    description: skill.description || '',
                                                    limiter: skill.limiter || '',
                                                    colors: skill.colors || '',
                                                    tier: tierKey,
                                                    branch: tierBranch
                                                };
                                                
                                                // Store by numeric ID (this is what {27}, {28}, etc. will look up)
                                                partsMap.set(String(tierId), tierPartInfo);
                                                partsMap.set(tierPartInfo.fullId, tierPartInfo);
                                                // Also store with numeric ID
                                                const numericTierId = parseInt(tierId);
                                                if (!isNaN(numericTierId)) {
                                                    partsMap.set(numericTierId, tierPartInfo);
                                                }
                                                
                                                // Add to typeId-specific map
                                                partsByTypeId.get(skillsTypeId).push(tierPartInfo);
                                                totalPartsExtracted++;
                                            }
                                        }
                                    }
                                } else {
                                    console.log(`  No parts array found in Skills for ${charName}`);
                                }
                            } else {
                                console.log(`  No type_id found in Skills for ${charName}`);
                            }
                        } else {
                            console.log(`  No Skills section found for ${charName}`);
                        }
                    } else {
                        console.log(`  No class_mods found for ${charName}`);
                        
                        // Special handling for "Perk" and "Firmware" characters - they might contain typeId 234 parts directly
                        if (charName === 'Perk' || charName === 'Firmware') {
                            console.log(`  [DEBUG] Checking ${charName} character for typeId 234 parts...`);
                            
                            // Check if the character data itself has parts
                            if (charData.parts && Array.isArray(charData.parts)) {
                                console.log(`  [DEBUG] Found ${charData.parts.length} parts in ${charName} character data`);
                                
                                // Add typeId 234 to typeIdMap if not already present
                                if (!typeIdMap.has(234)) {
                                    typeIdMap.set(234, {
                                        id: 234,
                                        name: 'Class Mod Substats',
                                        category: 'Class Mod',
                                        context: null,
                                        manufacturer: null
                                    });
                                    console.log(`Added type ID 234: Class Mod Substats`);
                                }
                                
                                if (!partsByTypeId.has(234)) {
                                    partsByTypeId.set(234, []);
                                }
                                
                                // Extract parts from this character
                                for (const part of charData.parts) {
                                    const partIdStr = part.id ? String(part.id) : '';
                                    const has234Id = partIdStr.startsWith('234:');
                                    const hasTypeId234 = part.type_id === 234 || charData.type_id === 234;
                                    const isNumericId = /^\d+$/.test(partIdStr);
                                    
                                    if (has234Id || (hasTypeId234 && (isNumericId || !partIdStr.includes(':')))) {
                                        let normalizedPart = part;
                                        if (isNumericId && !has234Id) {
                                            normalizedPart = {...part, id: `234:${partIdStr}`};
                                        }
                                        
                                        const partType = charName === 'Perk' ? 'Perk' : 'Firmware';
                                        const partInfo = extractPartInfo(normalizedPart, 234, partType, 'Class Mod', null, null, null);
                                        if (partInfo) {
                                            partInfo.typeId = 234;
                                            partInfo.partType = partType;
                                            partInfo.path = partType;
                                            
                                            partsMap.set(partInfo.fullId, partInfo);
                                            partsMap.set(partInfo.id, partInfo);
                                            if (partInfo.spawnCode) {
                                                partsMap.set(partInfo.spawnCode, partInfo);
                                            }
                                            if (partInfo.fullId.includes(':')) {
                                                const afterColon = partInfo.fullId.split(':')[1];
                                                partsMap.set(afterColon, partInfo);
                                                const numericPartId = parseInt(afterColon);
                                                if (!isNaN(numericPartId)) {
                                                    partsMap.set(numericPartId, partInfo);
                                                }
                                            }
                                            
                                            partsByTypeId.get(234).push(partInfo);
                                            totalPartsExtracted++;
                                        }
                                    }
                                }
                                console.log(`  ✓ Extracted ${partsByTypeId.get(234).filter(p => p.partType === charName).length} ${charName} parts for typeId 234`);
                            }
                            
                            // Also check if charData has a part_types structure
                            if (charData.part_types) {
                                console.log(`  [DEBUG] Found part_types in ${charName} character`);
                                // Try extracting using extractFromPartTypes
                                extractFromPartTypes(charData.part_types, 'Class Mod', charName);
                            }
                            
                            // Check all keys in charData for potential part sections
                            for (const [key, value] of Object.entries(charData)) {
                                if (key !== 'part_types' && typeof value === 'object' && value !== null && !Array.isArray(value)) {
                                    if (value.parts && Array.isArray(value.parts)) {
                                        console.log(`  [DEBUG] Found parts array in ${charName}.${key} with ${value.parts.length} parts`);
                                        // Check if any parts have typeId 234
                                        const has234Parts = value.parts.some(p => {
                                            const partId = String(p.id || '');
                                            return partId.startsWith('234:') || p.type_id === 234 || value.type_id === 234;
                                        });
                                        if (has234Parts) {
                                            console.log(`  [DEBUG] Section ${charName}.${key} contains typeId 234 parts!`);
                                            // Extract them
                                            if (!typeIdMap.has(234)) {
                                                typeIdMap.set(234, {
                                                    id: 234,
                                                    name: 'Class Mod Substats',
                                                    category: 'Class Mod',
                                                    context: null,
                                                    manufacturer: null
                                                });
                                            }
                                            if (!partsByTypeId.has(234)) {
                                                partsByTypeId.set(234, []);
                                            }
                                            
                                            for (const part of value.parts) {
                                                const partIdStr = part.id ? String(part.id) : '';
                                                const has234Id = partIdStr.startsWith('234:');
                                                const hasTypeId234 = part.type_id === 234 || value.type_id === 234;
                                                const isNumericId = /^\d+$/.test(partIdStr);
                                                
                                                if (has234Id || (hasTypeId234 && (isNumericId || !partIdStr.includes(':')))) {
                                                    let normalizedPart = part;
                                                    if (isNumericId && !has234Id) {
                                                        normalizedPart = {...part, id: `234:${partIdStr}`};
                                                    }
                                                    
                                                    const partType = charName === 'Perk' ? 'Perk' : 'Firmware';
                                                    const partInfo = extractPartInfo(normalizedPart, 234, partType, 'Class Mod', null, null, null);
                                                    if (partInfo) {
                                                        partInfo.typeId = 234;
                                                        partInfo.partType = partType;
                                                        partInfo.path = `${charName}.${key}`;
                                                        
                                                        partsMap.set(partInfo.fullId, partInfo);
                                                        partsMap.set(partInfo.id, partInfo);
                                                        if (partInfo.fullId.includes(':')) {
                                                            const afterColon = partInfo.fullId.split(':')[1];
                                                            partsMap.set(afterColon, partInfo);
                                                            const numericPartId = parseInt(afterColon);
                                                            if (!isNaN(numericPartId)) {
                                                                partsMap.set(numericPartId, partInfo);
                                                            }
                                                        }
                                                        
                                                        partsByTypeId.get(234).push(partInfo);
                                                        totalPartsExtracted++;
                                                    }
                                                }
                                            }
                                            console.log(`  ✓ Extracted ${partsByTypeId.get(234).filter(p => p.partType === charName && p.path === `${charName}.${key}`).length} ${charName} parts from ${key} for typeId 234`);
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            } else {
                console.log('No characters section found in gameData');
            }

            // Extract from top-level heavy_weapons section (if it exists separately)
            if (gameData.heavy_weapons) {
                console.log('Checking top-level heavy_weapons section...');
                console.log('Heavy weapons keys:', Object.keys(gameData.heavy_weapons));
                
                // Check if heavy_weapons has manufacturers structure
                if (gameData.heavy_weapons.manufacturers) {
                    console.log('Processing top-level heavy_weapons.manufacturers...');
                    for (const [manufacturer, data] of Object.entries(gameData.heavy_weapons.manufacturers)) {
                        let typeId = null;
                        if (data.type_id) {
                            typeId = data.type_id;
                            console.log(`Found type_id ${typeId} directly on ${manufacturer} heavy_weapons`);
                        } else {
                            const findTypeIdFromParts = (partTypes, depth = 0) => {
                                if (depth > 10) {
                                    console.log(`  findTypeIdFromParts: Max depth reached at depth ${depth}`);
                                    return null; // Prevent infinite recursion
                                }
                                console.log(`  findTypeIdFromParts: Searching at depth ${depth}, keys: ${Object.keys(partTypes).join(', ')}`);
                                for (const [partTypeKey, partTypeData] of Object.entries(partTypes)) {
                                    console.log(`  findTypeIdFromParts: Checking ${partTypeKey} at depth ${depth}`);
                                    // Check for parts array directly
                                    if (partTypeData.parts && Array.isArray(partTypeData.parts)) {
                                        console.log(`  findTypeIdFromParts: Found parts array in ${partTypeKey} with ${partTypeData.parts.length} parts`);
                                        for (const part of partTypeData.parts) {
                                            if (part.id) {
                                                let idStr = String(part.id);
                                                if (idStr.includes(':')) {
                                                    const typeIdStr = idStr.split(':')[0];
                                                    const parsedTypeId = parseInt(typeIdStr);
                                                    if (!isNaN(parsedTypeId)) {
                                                        console.log(`  Found type_id ${parsedTypeId} from part ID ${idStr} in ${partTypeKey}`);
                                                        return parsedTypeId;
                                                    }
                                                }
                                            }
                                        }
                                    }
                                    // Check nested part_types (like Rarities.part_types.Rarity)
                                    if (partTypeData.part_types) {
                                        console.log(`  findTypeIdFromParts: Found part_types in ${partTypeKey}, recursing...`);
                                        const nestedTypeId = findTypeIdFromParts(partTypeData.part_types, depth + 1);
                                        if (nestedTypeId) return nestedTypeId;
                                    }
                                    // Also check for nested structures like Rarities.Rarity.parts
                                    if (partTypeData.Rarity) {
                                        console.log(`  findTypeIdFromParts: Found Rarity in ${partTypeKey}`);
                                        if (partTypeData.Rarity.parts && Array.isArray(partTypeData.Rarity.parts)) {
                                            console.log(`  findTypeIdFromParts: Found Rarity.parts array in ${partTypeKey} with ${partTypeData.Rarity.parts.length} parts`);
                                            for (const part of partTypeData.Rarity.parts) {
                                                if (part.id) {
                                                    let idStr = String(part.id);
                                                    if (idStr.includes(':')) {
                                                        const typeIdStr = idStr.split(':')[0];
                                                        const parsedTypeId = parseInt(typeIdStr);
                                                        if (!isNaN(parsedTypeId)) {
                                                            console.log(`  Found type_id ${parsedTypeId} from Rarity part ID ${idStr} in ${partTypeKey}`);
                                                            return parsedTypeId;
                                                        }
                                                    }
                                                }
                                            }
                                        } else {
                                            console.log(`  findTypeIdFromParts: Rarity found but no parts array in ${partTypeKey}`);
                                        }
                                    }
                                }
                                console.log(`  findTypeIdFromParts: No type_id found at depth ${depth}`);
                                return null;
                            };
                            if (data.part_types) {
                                console.log(`  No type_id found on ${manufacturer} heavy_weapons, searching in parts...`);
                                typeId = findTypeIdFromParts(data.part_types);
                                if (typeId) {
                                    console.log(`  Extracted type_id ${typeId} from parts for ${manufacturer} heavy_weapons`);
                                } else {
                                    console.warn(`  Could not find type_id for ${manufacturer} heavy_weapons`);
                                }
                            } else {
                                console.warn(`  No part_types found for ${manufacturer} heavy_weapons`);
                            }
                        }
                        
                        // If typeId is still null, try to extract it during part extraction
                        if (!typeId && data.part_types) {
                            console.log(`  Type ID still null for ${manufacturer}, will try to extract during part processing...`);
                        }
                        
                        if (typeId && !typeIdMap.has(typeId)) {
                            typeIdMap.set(typeId, {
                                id: typeId,
                                name: 'Heavy Weapon',
                                category: 'Heavy Weapon',
                                manufacturer: manufacturer
                            });
                            console.log(`Added type ID ${typeId}: ${manufacturer} Heavy Weapon`);
                            if (!partsByTypeId.has(typeId)) partsByTypeId.set(typeId, []);
                        }
                        // Extract parts...
                        // If typeId is null, we'll extract it from the first part we find
                        let extractedTypeIdFromParts = typeId;
                        // Extract parts even if typeId is null (we'll extract it from parts)
                        if (data.part_types) {
                            const extractPartsRecursive = (partTypes, currentTypeId, path = '') => {
                                for (const [partTypeKey, partTypeData] of Object.entries(partTypes)) {
                                    const partTypePath = path ? `${path}.${partTypeKey}` : partTypeKey;
                                    
                                    // Special handling for Rarities sections - check if it has nested Rarity structures (Rarities.Rarity.parts)
                                    if (partTypeKey === 'Rarities' || partTypeKey === 'Rarity') {
                                        // Check for nested Rarity structures (Rarities.Rarity.parts)
                                        if (partTypeData.Rarity && partTypeData.Rarity.parts && Array.isArray(partTypeData.Rarity.parts)) {
                                            console.log(`  Extracting ${partTypeData.Rarity.parts.length} parts from ${partTypePath}.Rarity (Type ID: ${currentTypeId})`);
                                            for (const part of partTypeData.Rarity.parts) {
                                                const partInfo = extractPartInfo(part, currentTypeId, 'Rarity', 'Heavy Weapon', manufacturer, manufacturer, 'Heavy Weapon');
                                                if (partInfo) {
                                                    let targetTypeId = currentTypeId;
                                                    if (partInfo.fullId.includes(':')) {
                                                        const colonIndex = partInfo.fullId.indexOf(':');
                                                        const extractedTypeId = parseInt(partInfo.fullId.substring(0, colonIndex));
                                                        if (!isNaN(extractedTypeId)) {
                                                            partInfo.typeId = extractedTypeId;
                                                            targetTypeId = extractedTypeId;
                                                            // If we don't have a typeId yet, use this one
                                                            if (!extractedTypeIdFromParts) {
                                                                extractedTypeIdFromParts = extractedTypeId;
                                                                console.log(`  Extracted type_id ${extractedTypeIdFromParts} from part ${partInfo.fullId} for ${manufacturer} heavy_weapons`);
                                                            }
                                                            const afterColon = partInfo.fullId.substring(colonIndex + 1);
                                                            partsMap.set(afterColon, partInfo);
                                                            const numericPartId = parseInt(afterColon);
                                                            if (!isNaN(numericPartId)) {
                                                                partsMap.set(numericPartId, partInfo);
                                                            }
                                                        }
                                                    } else {
                                                        partInfo.typeId = currentTypeId || extractedTypeIdFromParts;
                                                        targetTypeId = currentTypeId || extractedTypeIdFromParts;
                                                        // If we don't have a typeId yet and currentTypeId is set, use it
                                                        if (!extractedTypeIdFromParts && currentTypeId) {
                                                            extractedTypeIdFromParts = currentTypeId;
                                                        }
                                                    }
                                                    
                                                    partsMap.set(partInfo.fullId, partInfo);
                                                    partsMap.set(partInfo.id, partInfo);
                                                    if (partInfo.spawnCode) {
                                                        partsMap.set(partInfo.spawnCode, partInfo);
                                                    }
                                                    if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                                        partsMap.set(partInfo.string, partInfo);
                                                    }
                                                    if (!partsByTypeId.has(targetTypeId)) {
                                                        partsByTypeId.set(targetTypeId, []);
                                                    }
                                                    partsByTypeId.get(targetTypeId).push(partInfo);
                                                    totalPartsExtracted++;
                                                    
                                                    // Debug log for comp parts
                                                    if ((partInfo.spawnCode && String(partInfo.spawnCode).includes('.comp_')) || (partInfo.string && String(partInfo.string).includes('.comp_'))) {
                                                        console.log(`    ✓ Extracted comp part: ${partInfo.name} (fullId: ${partInfo.fullId}, id: ${partInfo.id}, typeId: ${partInfo.typeId}, spawnCode: ${partInfo.spawnCode}, string: ${partInfo.string}, path: ${partTypePath}.Rarity)`);
                                                    }
                                                }
                                            }
                                        }
                                    }
                                    
                                    // Check for direct parts array
                                    if (partTypeData.parts && Array.isArray(partTypeData.parts)) {
                                        console.log(`  Extracting ${partTypeData.parts.length} parts from ${partTypePath} (Type ID: ${currentTypeId})`);
                                        for (const part of partTypeData.parts) {
                                            const partInfo = extractPartInfo(part, currentTypeId, partTypeKey, 'Heavy Weapon', manufacturer, manufacturer, 'Heavy Weapon');
                                            if (partInfo) {
                                                // If part ID contains a colon, extract the type ID
                                                let targetTypeId = currentTypeId;
                                                if (partInfo.fullId.includes(':')) {
                                                    const colonIndex = partInfo.fullId.indexOf(':');
                                                    const extractedTypeId = parseInt(partInfo.fullId.substring(0, colonIndex));
                                                    if (!isNaN(extractedTypeId)) {
                                                        partInfo.typeId = extractedTypeId;
                                                        targetTypeId = extractedTypeId;
                                                        // If we don't have a typeId yet, use this one
                                                        if (!extractedTypeIdFromParts) {
                                                            extractedTypeIdFromParts = extractedTypeId;
                                                            console.log(`  Extracted type_id ${extractedTypeIdFromParts} from part ${partInfo.fullId} for ${manufacturer} heavy_weapons`);
                                                        }
                                                        const afterColon = partInfo.fullId.substring(colonIndex + 1);
                                                        partsMap.set(afterColon, partInfo);
                                                        const numericPartId = parseInt(afterColon);
                                                        if (!isNaN(numericPartId)) {
                                                            partsMap.set(numericPartId, partInfo);
                                                        }
                                                    }
                                                } else {
                                                    partInfo.typeId = currentTypeId || extractedTypeIdFromParts;
                                                    targetTypeId = currentTypeId || extractedTypeIdFromParts;
                                                    // If we don't have a typeId yet and currentTypeId is set, use it
                                                    if (!extractedTypeIdFromParts && currentTypeId) {
                                                        extractedTypeIdFromParts = currentTypeId;
                                                    }
                                                }
                                                
                                                partsMap.set(partInfo.fullId, partInfo);
                                                partsMap.set(partInfo.id, partInfo);
                                                if (partInfo.spawnCode) {
                                                    partsMap.set(partInfo.spawnCode, partInfo);
                                                }
                                                if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                                    partsMap.set(partInfo.string, partInfo);
                                                }
                                                if (!partsByTypeId.has(targetTypeId)) {
                                                    partsByTypeId.set(targetTypeId, []);
                                                }
                                                partsByTypeId.get(targetTypeId).push(partInfo);
                                                totalPartsExtracted++;
                                            }
                                        }
                                    }
                                    
                                    // Recursively check nested part_types
                                    if (partTypeData.part_types) {
                                        extractPartsRecursive(partTypeData.part_types, currentTypeId || extractedTypeIdFromParts, partTypePath);
                                    }
                                }
                            };
                            extractPartsRecursive(data.part_types, typeId || extractedTypeIdFromParts);
                            
                            // If we extracted a typeId from parts, add it to the map now
                            if (extractedTypeIdFromParts && !typeIdMap.has(extractedTypeIdFromParts)) {
                                typeIdMap.set(extractedTypeIdFromParts, {
                                    id: extractedTypeIdFromParts,
                                    name: 'Heavy Weapon',
                                    category: 'Heavy Weapon',
                                    manufacturer: manufacturer
                                });
                                console.log(`Added type ID ${extractedTypeIdFromParts}: ${manufacturer} Heavy Weapon (extracted from parts)`);
                                if (!partsByTypeId.has(extractedTypeIdFromParts)) partsByTypeId.set(extractedTypeIdFromParts, []);
                            }
                        }
                    }
                } else {
                    // Direct structure - manufacturers are keys in heavy_weapons
                    console.log('Processing top-level heavy_weapons with direct manufacturer structure...');
                    for (const [manufacturer, data] of Object.entries(gameData.heavy_weapons)) {
                        if (manufacturer === 'manufacturers' || !data || typeof data !== 'object') continue;
                        let typeId = null;
                        if (data.type_id) {
                            typeId = data.type_id;
                            console.log(`Found type_id ${typeId} directly on ${manufacturer} heavy_weapons`);
                        }
                        
                        // If typeId is still null, try one more time with a more aggressive search
                        if (!typeId && data.part_types) {
                            console.log(`  Type ID still null for ${manufacturer}, trying aggressive search...`);
                            // Try to find any part with a colon-separated ID
                            const aggressiveSearch = (obj, depth = 0) => {
                                if (depth > 15) return null;
                                if (Array.isArray(obj)) {
                                    for (const item of obj) {
                                        if (item && typeof item === 'object') {
                                            if (item.id && String(item.id).includes(':')) {
                                                const typeIdStr = String(item.id).split(':')[0];
                                                const parsed = parseInt(typeIdStr);
                                                if (!isNaN(parsed)) return parsed;
                                            }
                                            const found = aggressiveSearch(item, depth + 1);
                                            if (found) return found;
                                        }
                                    }
                                } else if (obj && typeof obj === 'object') {
                                    for (const [key, value] of Object.entries(obj)) {
                                        if (key === 'id' && value && String(value).includes(':')) {
                                            const typeIdStr = String(value).split(':')[0];
                                            const parsed = parseInt(typeIdStr);
                                            if (!isNaN(parsed)) return parsed;
                                        }
                                        if (value && typeof value === 'object') {
                                            const found = aggressiveSearch(value, depth + 1);
                                            if (found) return found;
                                        }
                                    }
                                }
                                return null;
                            };
                            typeId = aggressiveSearch(data.part_types);
                            if (typeId) {
                                console.log(`  Found type_id ${typeId} using aggressive search for ${manufacturer} heavy_weapons`);
                            }
                        }
                        
                        if (typeId && !typeIdMap.has(typeId)) {
                            typeIdMap.set(typeId, {
                                id: typeId,
                                name: 'Heavy Weapon',
                                category: 'Heavy Weapon',
                                manufacturer: manufacturer
                            });
                            console.log(`Added type ID ${typeId}: ${manufacturer} Heavy Weapon`);
                            if (!partsByTypeId.has(typeId)) partsByTypeId.set(typeId, []);
                        } else if (typeId && typeIdMap.has(typeId)) {
                            console.log(`Type ID ${typeId} already exists in map for ${manufacturer} heavy_weapons`);
                        } else {
                            console.warn(`Type ID is still null for ${manufacturer} heavy_weapons after all attempts`);
                        }
                        // Extract parts...
                        if (typeId && data.part_types) {
                            const extractPartsRecursive = (partTypes, currentTypeId) => {
                                for (const [partTypeKey, partTypeData] of Object.entries(partTypes)) {
                                    if (partTypeData.parts && Array.isArray(partTypeData.parts)) {
                                        for (const part of partTypeData.parts) {
                                            const partInfo = extractPartInfo(part, currentTypeId, partTypeKey, 'Heavy Weapon', manufacturer, manufacturer, 'Heavy Weapon');
                                            if (partInfo) {
                                                let targetTypeId = currentTypeId;
                                                if (partInfo.fullId.includes(':')) {
                                                    const colonIndex = partInfo.fullId.indexOf(':');
                                                    const extractedTypeId = parseInt(partInfo.fullId.substring(0, colonIndex));
                                                    if (!isNaN(extractedTypeId)) {
                                                        partInfo.typeId = extractedTypeId;
                                                        targetTypeId = extractedTypeId;
                                                        const afterColon = partInfo.fullId.substring(colonIndex + 1);
                                                        partsMap.set(afterColon, partInfo);
                                                    }
                                                } else {
                                                    partInfo.typeId = currentTypeId;
                                                    targetTypeId = currentTypeId;
                                                }
                                                
                                                partsMap.set(partInfo.fullId, partInfo);
                                                partsMap.set(partInfo.id, partInfo);
                                                if (partInfo.spawnCode) {
                                                    partsMap.set(partInfo.spawnCode, partInfo);
                                                }
                                                if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                                    partsMap.set(partInfo.string, partInfo);
                                                }
                                                if (!partsByTypeId.has(targetTypeId)) {
                                                    partsByTypeId.set(targetTypeId, []);
                                                }
                                                partsByTypeId.get(targetTypeId).push(partInfo);
                                                totalPartsExtracted++;
                                            }
                                        }
                                    }
                                    if (partTypeData.part_types) extractPartsRecursive(partTypeData.part_types, currentTypeId);
                                }
                            };
                            extractPartsRecursive(data.part_types, typeId);
                        }
                    }
                }
            }

            // Extract from gadgets section (which contains nested structures like enhancements, shields, etc.)
            if (gameData.gadgets) {
                console.log('Checking gadgets section...');
                console.log('Gadgets keys:', Object.keys(gameData.gadgets));
                
                // gadgets.enhancements, gadgets.shields, gadgets.repkits, gadgets.ordonances, gadgets.grenades
                const gadgetSubsections = ['enhancements', 'shields', 'repkits', 'ordonances', 'grenades'];
                
                for (const subsectionName of gadgetSubsections) {
                    if (gameData.gadgets[subsectionName]) {
                        console.log(`Checking gadgets.${subsectionName}...`);
                        const subsection = gameData.gadgets[subsectionName];
                        console.log(`${subsectionName} keys:`, Object.keys(subsection));
                        
                        // Check if subsection has manufacturers structure (like shields.manufacturers)
                        // OR if manufacturers are directly in subsection (like repair_kits.Torgue)
                        let manufacturersToProcess = null;
                        if (subsection.manufacturers) {
                            console.log(`gadgets.${subsectionName} has manufacturers wrapper`);
                            manufacturersToProcess = subsection.manufacturers;
                        } else {
                            // Check if subsection contains nested structures (like ordonances.grenades, ordonances.heavy_weapons)
                            if (subsectionName === 'ordonances' && (subsection.grenades || subsection.heavy_weapons)) {
                                console.log(`gadgets.${subsectionName} contains nested structures`);
                                // Process nested grenades
                                if (subsection.grenades && subsection.grenades.manufacturers) {
                                    console.log(`Processing gadgets.ordonances.grenades...`);
                                    for (const [manufacturer, data] of Object.entries(subsection.grenades.manufacturers)) {
                                        let typeId = null;
                                        if (data.type_id) {
                                            typeId = data.type_id;
                                            console.log(`Found type_id ${typeId} directly on ${manufacturer} ordonances.grenades`);
                                        } else {
                                            const findTypeIdFromParts = (partTypes) => {
                                                for (const [partTypeKey, partTypeData] of Object.entries(partTypes)) {
                                                    if (partTypeData.parts && Array.isArray(partTypeData.parts)) {
                                                        for (const part of partTypeData.parts) {
                                                            if (part.id && typeof part.id === 'string' && part.id.includes(':')) {
                                                                const typeIdStr = part.id.split(':')[0];
                                                                const parsedTypeId = parseInt(typeIdStr);
                                                                if (!isNaN(parsedTypeId)) return parsedTypeId;
                                                            }
                                                        }
                                                    }
                                                    if (partTypeData.part_types) {
                                                        const nestedTypeId = findTypeIdFromParts(partTypeData.part_types);
                                                        if (nestedTypeId) return nestedTypeId;
                                                    }
                                                }
                                                return null;
                                            };
                                            if (data.part_types) typeId = findTypeIdFromParts(data.part_types);
                                        }
                                        if (typeId && !typeIdMap.has(typeId)) {
                                            typeIdMap.set(typeId, {
                                                id: typeId,
                                                name: 'Ordnance',
                                                category: 'Grenades',
                                                manufacturer: manufacturer
                                            });
                                            console.log(`Added type ID ${typeId}: ${manufacturer} grenades`);
                                            if (!partsByTypeId.has(typeId)) partsByTypeId.set(typeId, []);
                                        }
                                        // Extract parts...
                                        // First check for Rarities at the same level as part_types (sibling, not nested)
                                        if (typeId && data.Rarities) {
                                            console.log(`  Found Rarities section at top level for ${manufacturer} grenades (Type ID: ${typeId})`);
                                            const extractFromRarities = (raritiesData, currentTypeId) => {
                                                for (const [rarityKey, rarityData] of Object.entries(raritiesData)) {
                                                    if (rarityData.parts && Array.isArray(rarityData.parts)) {
                                                        console.log(`  Extracting ${rarityData.parts.length} parts from Rarities.${rarityKey} (Type ID: ${currentTypeId})`);
                                                        for (const part of rarityData.parts) {
                                                            const partInfo = extractPartInfo(part, currentTypeId, rarityKey, 'Grenades', manufacturer, manufacturer, 'grenades');
                                                            if (partInfo) {
                                                                // For simple numeric IDs, ensure typeId is set correctly
                                                                let targetTypeId = currentTypeId;
                                                                if (partInfo.fullId.includes(':')) {
                                                                    const colonIndex = partInfo.fullId.indexOf(':');
                                                                    const extractedTypeId = parseInt(partInfo.fullId.substring(0, colonIndex));
                                                                    if (!isNaN(extractedTypeId)) {
                                                                        partInfo.typeId = extractedTypeId;
                                                                        targetTypeId = extractedTypeId;
                                                                        const afterColon = partInfo.fullId.substring(colonIndex + 1);
                                                                        partsMap.set(afterColon, partInfo);
                                                                    }
                                                                } else {
                                                                    partInfo.typeId = currentTypeId;
                                                                    targetTypeId = currentTypeId;
                                                                }
                                                                
                                                                partsMap.set(partInfo.fullId, partInfo);
                                                                partsMap.set(partInfo.id, partInfo);
                                                                if (partInfo.spawnCode) {
                                                                    partsMap.set(partInfo.spawnCode, partInfo);
                                                                }
                                                                if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                                                    partsMap.set(partInfo.string, partInfo);
                                                                }
                                                                if (!partsByTypeId.has(targetTypeId)) {
                                                                    partsByTypeId.set(targetTypeId, []);
                                                                }
                                                                partsByTypeId.get(targetTypeId).push(partInfo);
                                                                totalPartsExtracted++;
                                                                
                                                                // Debug log for part 7 in typeId 267
                                                                if ((partInfo.id === '7' || partInfo.fullId === '267:7') && currentTypeId === 267) {
                                                                    console.log(`    ✓ Extracted part 7 from Rarities for typeId 267: ${partInfo.name} (fullId: ${partInfo.fullId}, id: ${partInfo.id}, typeId: ${partInfo.typeId})`);
                                                                }
                                                            }
                                                        }
                                                    }
                                                    // Recursively check nested structures
                                                    if (rarityData.part_types) {
                                                        extractFromRarities(rarityData.part_types, currentTypeId);
                                                    }
                                                }
                                            };
                                            extractFromRarities(data.Rarities, typeId);
                                        }
                                        
                                        if (typeId && data.part_types) {
                                            // Debug: Log the structure for Jakobs grenades
                                            if (typeId === 267 && manufacturer === 'Jakobs') {
                                                console.log(`  Debug: Jakobs grenades (267) data structure:`, Object.keys(data));
                                                console.log(`  Debug: part_types keys:`, Object.keys(data.part_types));
                                                // Check for Rarities at top level
                                                if (data.Rarities) {
                                                    console.log(`  Debug: Found Rarities at top level!`, Object.keys(data.Rarities));
                                                }
                                                // Check for Rarities nested in Base
                                                if (data.part_types && data.part_types.Base) {
                                                    console.log(`  Debug: Base keys:`, Object.keys(data.part_types.Base));
                                                    if (data.part_types.Base.part_types) {
                                                        console.log(`  Debug: Base.part_types keys:`, Object.keys(data.part_types.Base.part_types));
                                                        if (data.part_types.Base.part_types.Rarities) {
                                                            console.log(`  Debug: Found Rarities nested in Base!`, Object.keys(data.part_types.Base.part_types.Rarities));
                                                        }
                                                    }
                                                }
                                            }
                                            
                                            const extractPartsRecursive = (partTypes, currentTypeId, path = '') => {
                                                for (const [partTypeKey, partTypeData] of Object.entries(partTypes)) {
                                                    const currentPath = path ? `${path}.${partTypeKey}` : partTypeKey;
                                                    
                                            // Check if this is a Rarity section - log it for debugging
                                            if (partTypeKey === 'Rarity' || partTypeKey === 'Rarities' || currentPath.includes('Rarity')) {
                                                console.log(`  Found Rarity section at ${currentPath} (Type ID: ${currentTypeId})`);
                                            }
                                            
                                            if (partTypeData.parts && Array.isArray(partTypeData.parts)) {
                                                console.log(`  Extracting ${partTypeData.parts.length} parts from ${currentPath} (Type ID: ${currentTypeId})`);
                                                for (const part of partTypeData.parts) {
                                                    const partInfo = extractPartInfo(part, currentTypeId, partTypeKey, 'Grenades', manufacturer, manufacturer, 'grenades');
                                                    if (partInfo) {
                                                        // If part ID contains a colon (type:value format), extract the type ID and update partInfo
                                                        let targetTypeId = currentTypeId;
                                                        if (partInfo.fullId.includes(':')) {
                                                            const colonIndex = partInfo.fullId.indexOf(':');
                                                            const extractedTypeId = parseInt(partInfo.fullId.substring(0, colonIndex));
                                                            if (!isNaN(extractedTypeId)) {
                                                                partInfo.typeId = extractedTypeId;
                                                                targetTypeId = extractedTypeId;
                                                                const afterColon = partInfo.fullId.substring(colonIndex + 1);
                                                                // Store by the numeric part ID for lookup (e.g., "7" for "267:7")
                                                                partsMap.set(afterColon, partInfo);
                                                                // Also store by the numeric part ID as a number
                                                                const numericPartId = parseInt(afterColon);
                                                                if (!isNaN(numericPartId)) {
                                                                    partsMap.set(numericPartId, partInfo);
                                                                }
                                                            }
                                                        } else {
                                                            // For simple numeric IDs (no colon), ensure typeId is set to currentTypeId
                                                            partInfo.typeId = currentTypeId;
                                                            targetTypeId = currentTypeId;
                                                        }
                                                                
                                                                partsMap.set(partInfo.fullId, partInfo);
                                                                partsMap.set(partInfo.id, partInfo);
                                                                // Store by spawn_code for string lookup
                                                                if (partInfo.spawnCode) {
                                                                    partsMap.set(partInfo.spawnCode, partInfo);
                                                                }
                                                                if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                                                    partsMap.set(partInfo.string, partInfo);
                                                                }
                                                                if (!partsByTypeId.has(targetTypeId)) {
                                                                    partsByTypeId.set(targetTypeId, []);
                                                                }
                                                                partsByTypeId.get(targetTypeId).push(partInfo);
                                                                totalPartsExtracted++;
                                                                
                                                                // Debug log for part 7 in typeId 267 (Jakobs Grenade rarity)
                                                                if ((partInfo.id === '7' || partInfo.fullId === '267:7') && currentTypeId === 267) {
                                                                    console.log(`    ✓ Extracted part 7 for typeId 267: ${partInfo.name} (fullId: ${partInfo.fullId}, id: ${partInfo.id}, typeId: ${partInfo.typeId}, targetTypeId: ${targetTypeId}, currentTypeId: ${currentTypeId}, partType: ${partTypeKey}, path: ${currentPath})`);
                                                                }
                                                            }
                                                        }
                                                    }
                                                    if (partTypeData.part_types) extractPartsRecursive(partTypeData.part_types, currentTypeId, currentPath);
                                                    // Also check if this partTypeData itself has a Rarities section
                                                    if (partTypeData.Rarities) {
                                                        console.log(`  Found Rarity section at ${currentPath}.Rarities (Type ID: ${currentTypeId})`);
                                                        const extractFromRarities = (raritiesData, currentTypeId) => {
                                                            for (const [rarityKey, rarityData] of Object.entries(raritiesData)) {
                                                                if (rarityData.parts && Array.isArray(rarityData.parts)) {
                                                                    console.log(`  Extracting ${rarityData.parts.length} parts from ${currentPath}.Rarities.${rarityKey} (Type ID: ${currentTypeId})`);
                                                                    for (const part of rarityData.parts) {
                                                                        const partInfo = extractPartInfo(part, currentTypeId, rarityKey, 'Grenades', manufacturer, manufacturer, 'grenades');
                                                                        if (partInfo) {
                                                                            let targetTypeId = currentTypeId;
                                                                            if (partInfo.fullId.includes(':')) {
                                                                                const colonIndex = partInfo.fullId.indexOf(':');
                                                                                const extractedTypeId = parseInt(partInfo.fullId.substring(0, colonIndex));
                                                                                if (!isNaN(extractedTypeId)) {
                                                                                    partInfo.typeId = extractedTypeId;
                                                                                    targetTypeId = extractedTypeId;
                                                                                    const afterColon = partInfo.fullId.substring(colonIndex + 1);
                                                                                    partsMap.set(afterColon, partInfo);
                                                                                    const numericPartId = parseInt(afterColon);
                                                                                    if (!isNaN(numericPartId)) {
                                                                                        partsMap.set(numericPartId, partInfo);
                                                                                    }
                                                                                }
                                                                            } else {
                                                                                partInfo.typeId = currentTypeId;
                                                                                targetTypeId = currentTypeId;
                                                                            }
                                                                            
                                                                            partsMap.set(partInfo.fullId, partInfo);
                                                                            partsMap.set(partInfo.id, partInfo);
                                                                            if (partInfo.spawnCode) {
                                                                                partsMap.set(partInfo.spawnCode, partInfo);
                                                                            }
                                                                            if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                                                                partsMap.set(partInfo.string, partInfo);
                                                                            }
                                                                            if (!partsByTypeId.has(targetTypeId)) {
                                                                                partsByTypeId.set(targetTypeId, []);
                                                                            }
                                                                            partsByTypeId.get(targetTypeId).push(partInfo);
                                                                            totalPartsExtracted++;
                                                                            
                                                                            // Debug log for comp parts
                                                                            if ((partInfo.spawnCode && String(partInfo.spawnCode).includes('.comp_')) || (partInfo.string && String(partInfo.string).includes('.comp_'))) {
                                                                                console.log(`    ✓ Extracted comp part: ${partInfo.name} (fullId: ${partInfo.fullId}, id: ${partInfo.id}, typeId: ${partInfo.typeId}, spawnCode: ${partInfo.spawnCode}, string: ${partInfo.string}, path: ${currentPath}.Rarities.${rarityKey})`);
                                                                            }
                                                                            // Debug log for part 7 in typeId 267
                                                                            if ((partInfo.id === '7' || partInfo.fullId === '267:7' || partInfo.id === 7) && (currentTypeId === 267 || targetTypeId === 267)) {
                                                                                console.log(`    ✓ Extracted part 7 from nested Rarities for typeId 267: ${partInfo.name} (fullId: ${partInfo.fullId}, id: ${partInfo.id}, typeId: ${partInfo.typeId}, targetTypeId: ${targetTypeId}, path: ${currentPath}.Rarities.${rarityKey})`);
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                                if (rarityData.part_types) {
                                                                    extractFromRarities(rarityData.part_types, currentTypeId);
                                                                }
                                                            }
                                                        };
                                                        extractFromRarities(partTypeData.Rarities, currentTypeId);
                                                    }
                                                }
                                            };
                                            extractPartsRecursive(data.part_types, typeId);
                                            
                                            // Also check for Rarities at the same level as part_types (not nested within)
                                            if (data.Rarities) {
                                                console.log(`  Found Rarities section at top level for ${manufacturer} grenades (Type ID: ${typeId})`);
                                                const extractFromRarities = (raritiesData, currentTypeId) => {
                                                    for (const [rarityKey, rarityData] of Object.entries(raritiesData)) {
                                                        if (rarityData.parts && Array.isArray(rarityData.parts)) {
                                                            console.log(`  Extracting ${rarityData.parts.length} parts from Rarities.${rarityKey} (Type ID: ${currentTypeId})`);
                                                            for (const part of rarityData.parts) {
                                                                const partInfo = extractPartInfo(part, currentTypeId, rarityKey, 'Grenades', manufacturer, manufacturer, 'grenades');
                                                                if (partInfo) {
                                                                    // For simple numeric IDs, ensure typeId is set correctly
                                                                    let targetTypeId = currentTypeId;
                                                                    if (partInfo.fullId.includes(':')) {
                                                                        const colonIndex = partInfo.fullId.indexOf(':');
                                                                        const extractedTypeId = parseInt(partInfo.fullId.substring(0, colonIndex));
                                                                        if (!isNaN(extractedTypeId)) {
                                                                            partInfo.typeId = extractedTypeId;
                                                                            targetTypeId = extractedTypeId;
                                                                            const afterColon = partInfo.fullId.substring(colonIndex + 1);
                                                                            partsMap.set(afterColon, partInfo);
                                                                        }
                                                                    } else {
                                                                        partInfo.typeId = currentTypeId;
                                                                        targetTypeId = currentTypeId;
                                                                    }
                                                                    
                                                                    partsMap.set(partInfo.fullId, partInfo);
                                                                    partsMap.set(partInfo.id, partInfo);
                                                                    if (partInfo.spawnCode) {
                                                                        partsMap.set(partInfo.spawnCode, partInfo);
                                                                    }
                                                                    if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                                                        partsMap.set(partInfo.string, partInfo);
                                                                    }
                                                                    if (!partsByTypeId.has(targetTypeId)) {
                                                                        partsByTypeId.set(targetTypeId, []);
                                                                    }
                                                                    partsByTypeId.get(targetTypeId).push(partInfo);
                                                                    totalPartsExtracted++;
                                                                    
                                                                    // Debug log for comp parts
                                                                    if ((partInfo.spawnCode && String(partInfo.spawnCode).includes('.comp_')) || (partInfo.string && String(partInfo.string).includes('.comp_'))) {
                                                                        console.log(`    ✓ Extracted comp part: ${partInfo.name} (fullId: ${partInfo.fullId}, id: ${partInfo.id}, typeId: ${partInfo.typeId}, spawnCode: ${partInfo.spawnCode}, string: ${partInfo.string})`);
                                                                    }
                                                                    // Debug log for part 7 in typeId 267
                                                                    if ((partInfo.id === '7' || partInfo.fullId === '267:7') && currentTypeId === 267) {
                                                                        console.log(`    ✓ Extracted part 7 from Rarities for typeId 267: ${partInfo.name} (fullId: ${partInfo.fullId}, id: ${partInfo.id}, typeId: ${partInfo.typeId})`);
                                                                    }
                                                                }
                                                            }
                                                        }
                                                        // Recursively check nested structures
                                                        if (rarityData.part_types) {
                                                            extractFromRarities(rarityData.part_types, currentTypeId);
                                                        }
                                                    }
                                                };
                                                extractFromRarities(data.Rarities, typeId);
                                            }
                                        }
                                    }
                                }
                                // Process nested heavy_weapons
                                if (subsection.heavy_weapons) {
                                    console.log(`Processing gadgets.ordonances.heavy_weapons...`);
                                    console.log(`heavy_weapons structure:`, Object.keys(subsection.heavy_weapons));
                                    
                                    // Check if it has manufacturers wrapper
                                    let heavyWeaponsToProcess = null;
                                    if (subsection.heavy_weapons.manufacturers) {
                                        console.log(`heavy_weapons has manufacturers wrapper`);
                                        heavyWeaponsToProcess = subsection.heavy_weapons.manufacturers;
                                    } else {
                                        // Direct structure - manufacturers are keys
                                        console.log(`heavy_weapons has direct manufacturer structure`);
                                        heavyWeaponsToProcess = subsection.heavy_weapons;
                                    }
                                    
                                    if (heavyWeaponsToProcess) {
                                        for (const [manufacturer, data] of Object.entries(heavyWeaponsToProcess)) {
                                            if (manufacturer === 'manufacturers' || !data || typeof data !== 'object') continue;
                                            let typeId = null;
                                            if (data.type_id) {
                                                typeId = data.type_id;
                                                console.log(`Found type_id ${typeId} directly on ${manufacturer} ordonances.heavy_weapons`);
                                            } else {
                                                const findTypeIdFromParts = (partTypes) => {
                                                    for (const [partTypeKey, partTypeData] of Object.entries(partTypes)) {
                                                        if (partTypeData.parts && Array.isArray(partTypeData.parts)) {
                                                            for (const part of partTypeData.parts) {
                                                                if (part.id && typeof part.id === 'string' && part.id.includes(':')) {
                                                                    const typeIdStr = part.id.split(':')[0];
                                                                    const parsedTypeId = parseInt(typeIdStr);
                                                                    if (!isNaN(parsedTypeId)) return parsedTypeId;
                                                                }
                                                            }
                                                        }
                                                        if (partTypeData.part_types) {
                                                            const nestedTypeId = findTypeIdFromParts(partTypeData.part_types);
                                                            if (nestedTypeId) return nestedTypeId;
                                                        }
                                                    }
                                                    return null;
                                                };
                                                if (data.part_types) typeId = findTypeIdFromParts(data.part_types);
                                            }
                                            if (typeId) {
                                                if (!typeIdMap.has(typeId)) {
                                                    typeIdMap.set(typeId, {
                                                        id: typeId,
                                                        name: 'Heavy Weapon',
                                                        category: 'Heavy Weapon',
                                                        manufacturer: manufacturer
                                                    });
                                                    console.log(`Added type ID ${typeId}: ${manufacturer} Heavy Weapon`);
                                                } else {
                                                    console.log(`Type ID ${typeId} already exists, skipping`);
                                                }
                                                if (!partsByTypeId.has(typeId)) partsByTypeId.set(typeId, []);
                                                
                                                // Extract parts...
                                                if (data.part_types) {
                                                    const extractPartsRecursive = (partTypes, currentTypeId, path = '') => {
                                                        for (const [partTypeKey, partTypeData] of Object.entries(partTypes)) {
                                                            const currentPath = path ? `${path}.${partTypeKey}` : partTypeKey;
                                                            
                                                            // Check if this is a Rarity section - log it for debugging
                                                            if (partTypeKey === 'Rarity' || currentPath.includes('Rarity')) {
                                                                console.log(`  Found Rarity section at ${currentPath} (Type ID: ${currentTypeId})`);
                                                            }
                                                            
                                                            // Special handling for Rarities sections - check if it has nested Rarity structures (Rarities.Rarity.parts)
                                                            if (partTypeKey === 'Rarities' || partTypeKey === 'Rarity') {
                                                                // Check for nested Rarity structures (Rarities.Rarity.parts)
                                                                if (partTypeData.Rarity && partTypeData.Rarity.parts && Array.isArray(partTypeData.Rarity.parts)) {
                                                                    console.log(`  Extracting ${partTypeData.Rarity.parts.length} parts from ${currentPath}.Rarity (Type ID: ${currentTypeId})`);
                                                                    for (const part of partTypeData.Rarity.parts) {
                                                                        const partInfo = extractPartInfo(part, currentTypeId, 'Rarity', 'Heavy Weapon', manufacturer, manufacturer, 'Heavy Weapon');
                                                                        if (partInfo) {
                                                                            let targetTypeId = currentTypeId;
                                                                            if (partInfo.fullId.includes(':')) {
                                                                                const colonIndex = partInfo.fullId.indexOf(':');
                                                                                const extractedTypeId = parseInt(partInfo.fullId.substring(0, colonIndex));
                                                                                if (!isNaN(extractedTypeId)) {
                                                                                    partInfo.typeId = extractedTypeId;
                                                                                    targetTypeId = extractedTypeId;
                                                                                    const afterColon = partInfo.fullId.substring(colonIndex + 1);
                                                                                    partsMap.set(afterColon, partInfo);
                                                                                    const numericPartId = parseInt(afterColon);
                                                                                    if (!isNaN(numericPartId)) {
                                                                                        partsMap.set(numericPartId, partInfo);
                                                                                    }
                                                                                }
                                                                            } else {
                                                                                partInfo.typeId = currentTypeId;
                                                                                targetTypeId = currentTypeId;
                                                                            }
                                                                            
                                                                            partsMap.set(partInfo.fullId, partInfo);
                                                                            partsMap.set(partInfo.id, partInfo);
                                                                            if (partInfo.spawnCode) {
                                                                                partsMap.set(partInfo.spawnCode, partInfo);
                                                                            }
                                                                            if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                                                                partsMap.set(partInfo.string, partInfo);
                                                                            }
                                                                            if (!partsByTypeId.has(targetTypeId)) {
                                                                                partsByTypeId.set(targetTypeId, []);
                                                                            }
                                                                            partsByTypeId.get(targetTypeId).push(partInfo);
                                                                            totalPartsExtracted++;
                                                                            
                                                                            // Debug log for comp parts
                                                                            if ((partInfo.spawnCode && String(partInfo.spawnCode).includes('.comp_')) || (partInfo.string && String(partInfo.string).includes('.comp_'))) {
                                                                                console.log(`    ✓ Extracted comp part: ${partInfo.name} (fullId: ${partInfo.fullId}, id: ${partInfo.id}, typeId: ${partInfo.typeId}, spawnCode: ${partInfo.spawnCode}, string: ${partInfo.string}, path: ${currentPath}.Rarity)`);
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                                // Also check for direct parts array in Rarities
                                                                if (partTypeData.parts && Array.isArray(partTypeData.parts)) {
                                                                    console.log(`  Extracting ${partTypeData.parts.length} parts from ${currentPath} (direct parts array) (Type ID: ${currentTypeId})`);
                                                                    for (const part of partTypeData.parts) {
                                                                        const partInfo = extractPartInfo(part, currentTypeId, partTypeKey, 'Heavy Weapon', manufacturer, manufacturer, 'Heavy Weapon');
                                                                        if (partInfo) {
                                                                            let targetTypeId = currentTypeId;
                                                                            if (partInfo.fullId.includes(':')) {
                                                                                const colonIndex = partInfo.fullId.indexOf(':');
                                                                                const extractedTypeId = parseInt(partInfo.fullId.substring(0, colonIndex));
                                                                                if (!isNaN(extractedTypeId)) {
                                                                                    partInfo.typeId = extractedTypeId;
                                                                                    targetTypeId = extractedTypeId;
                                                                                    const afterColon = partInfo.fullId.substring(colonIndex + 1);
                                                                                    partsMap.set(afterColon, partInfo);
                                                                                    const numericPartId = parseInt(afterColon);
                                                                                    if (!isNaN(numericPartId)) {
                                                                                        partsMap.set(numericPartId, partInfo);
                                                                                    }
                                                                                }
                                                                            } else {
                                                                                partInfo.typeId = currentTypeId;
                                                                                targetTypeId = currentTypeId;
                                                                            }
                                                                            
                                                                            partsMap.set(partInfo.fullId, partInfo);
                                                                            partsMap.set(partInfo.id, partInfo);
                                                                            if (partInfo.spawnCode) {
                                                                                partsMap.set(partInfo.spawnCode, partInfo);
                                                                            }
                                                                            if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                                                                partsMap.set(partInfo.string, partInfo);
                                                                            }
                                                                            if (!partsByTypeId.has(targetTypeId)) {
                                                                                partsByTypeId.set(targetTypeId, []);
                                                                            }
                                                                            partsByTypeId.get(targetTypeId).push(partInfo);
                                                                            totalPartsExtracted++;
                                                                            
                                                                            // Debug log for comp parts
                                                                            if ((partInfo.spawnCode && String(partInfo.spawnCode).includes('.comp_')) || (partInfo.string && String(partInfo.string).includes('.comp_'))) {
                                                                                console.log(`    ✓ Extracted comp part: ${partInfo.name} (fullId: ${partInfo.fullId}, id: ${partInfo.id}, typeId: ${partInfo.typeId}, spawnCode: ${partInfo.spawnCode}, string: ${partInfo.string}, path: ${currentPath})`);
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                            if (partTypeData.parts && Array.isArray(partTypeData.parts)) {
                                                                console.log(`  Extracting ${partTypeData.parts.length} parts from ${currentPath} (Type ID: ${currentTypeId})`);
                                                                for (const part of partTypeData.parts) {
                                                                    const partInfo = extractPartInfo(part, currentTypeId, partTypeKey, 'Heavy Weapon', manufacturer, manufacturer, 'Heavy Weapon');
                                                                    if (partInfo) {
                                                                        let targetTypeId = currentTypeId;
                                                                        if (partInfo.fullId.includes(':')) {
                                                                            const colonIndex = partInfo.fullId.indexOf(':');
                                                                            const extractedTypeId = parseInt(partInfo.fullId.substring(0, colonIndex));
                                                                            if (!isNaN(extractedTypeId)) {
                                                                                partInfo.typeId = extractedTypeId;
                                                                                targetTypeId = extractedTypeId;
                                                                                const afterColon = partInfo.fullId.substring(colonIndex + 1);
                                                                                partsMap.set(afterColon, partInfo);
                                                                                const numericPartId = parseInt(afterColon);
                                                                                if (!isNaN(numericPartId)) {
                                                                                    partsMap.set(numericPartId, partInfo);
                                                                                }
                                                                            }
                                                                        } else {
                                                                            partInfo.typeId = currentTypeId;
                                                                            targetTypeId = currentTypeId;
                                                                        }
                                                                        
                                                                        partsMap.set(partInfo.fullId, partInfo);
                                                                        partsMap.set(partInfo.id, partInfo);
                                                                        if (partInfo.spawnCode) {
                                                                            partsMap.set(partInfo.spawnCode, partInfo);
                                                                        }
                                                                        if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                                                            partsMap.set(partInfo.string, partInfo);
                                                                        }
                                                                        if (!partsByTypeId.has(targetTypeId)) {
                                                                            partsByTypeId.set(targetTypeId, []);
                                                                        }
                                                                        partsByTypeId.get(targetTypeId).push(partInfo);
                                                                        totalPartsExtracted++;
                                                                    }
                                                                }
                                                            }
                                                            // Also check if this partTypeData itself has a Rarities section
                                                            if (partTypeData.Rarities) {
                                                                console.log(`  Found Rarity section at ${currentPath}.Rarities (Type ID: ${currentTypeId})`);
                                                                const extractFromRarities = (raritiesData, currentTypeId) => {
                                                                    for (const [rarityKey, rarityData] of Object.entries(raritiesData)) {
                                                                        if (rarityData.parts && Array.isArray(rarityData.parts)) {
                                                                            console.log(`  Extracting ${rarityData.parts.length} parts from ${currentPath}.Rarities.${rarityKey} (Type ID: ${currentTypeId})`);
                                                                            for (const part of rarityData.parts) {
                                                                                const partInfo = extractPartInfo(part, currentTypeId, rarityKey, 'Heavy Weapon', manufacturer, manufacturer, 'Heavy Weapon');
                                                                                if (partInfo) {
                                                                                    let targetTypeId = currentTypeId;
                                                                                    if (partInfo.fullId.includes(':')) {
                                                                                        const colonIndex = partInfo.fullId.indexOf(':');
                                                                                        const extractedTypeId = parseInt(partInfo.fullId.substring(0, colonIndex));
                                                                                        if (!isNaN(extractedTypeId)) {
                                                                                            partInfo.typeId = extractedTypeId;
                                                                                            targetTypeId = extractedTypeId;
                                                                                            const afterColon = partInfo.fullId.substring(colonIndex + 1);
                                                                                            partsMap.set(afterColon, partInfo);
                                                                                            const numericPartId = parseInt(afterColon);
                                                                                            if (!isNaN(numericPartId)) {
                                                                                                partsMap.set(numericPartId, partInfo);
                                                                                            }
                                                                                        }
                                                                                    } else {
                                                                                        partInfo.typeId = currentTypeId;
                                                                                        targetTypeId = currentTypeId;
                                                                                    }
                                                                                    
                                                                                    partsMap.set(partInfo.fullId, partInfo);
                                                                                    partsMap.set(partInfo.id, partInfo);
                                                                                    if (partInfo.spawnCode) {
                                                                                        partsMap.set(partInfo.spawnCode, partInfo);
                                                                                    }
                                                                                    if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                                                                        partsMap.set(partInfo.string, partInfo);
                                                                                    }
                                                                                    if (!partsByTypeId.has(targetTypeId)) {
                                                                                        partsByTypeId.set(targetTypeId, []);
                                                                                    }
                                                                                    partsByTypeId.get(targetTypeId).push(partInfo);
                                                                                    totalPartsExtracted++;
                                                                                    
                                                                                    // Debug log for comp parts
                                                                                    if ((partInfo.spawnCode && String(partInfo.spawnCode).includes('.comp_')) || (partInfo.string && String(partInfo.string).includes('.comp_'))) {
                                                                                        console.log(`    ✓ Extracted comp part: ${partInfo.name} (fullId: ${partInfo.fullId}, id: ${partInfo.id}, typeId: ${partInfo.typeId}, spawnCode: ${partInfo.spawnCode}, string: ${partInfo.string}, path: ${currentPath}.Rarities.${rarityKey})`);
                                                                                    }
                                                                                }
                                                                            }
                                                                        }
                                                                        if (rarityData.part_types) {
                                                                            extractFromRarities(rarityData.part_types, currentTypeId);
                                                                        }
                                                                    }
                                                                };
                                                                extractFromRarities(partTypeData.Rarities, currentTypeId);
                                                            }
                                                            if (partTypeData.part_types) extractPartsRecursive(partTypeData.part_types, currentTypeId, currentPath);
                                                        }
                                                    };
                                                    extractPartsRecursive(data.part_types, typeId);
                                                }
                                                
                                                // Also check for Rarities at the top level (sibling to part_types)
                                                if (data.Rarities) {
                                                    console.log(`  Found Rarities section at top level for ${manufacturer} heavy_weapons (Type ID: ${typeId})`);
                                                    const extractFromRarities = (raritiesData, currentTypeId) => {
                                                        for (const [rarityKey, rarityData] of Object.entries(raritiesData)) {
                                                            if (rarityData.parts && Array.isArray(rarityData.parts)) {
                                                                console.log(`  Extracting ${rarityData.parts.length} parts from Rarities.${rarityKey} (Type ID: ${currentTypeId})`);
                                                                for (const part of rarityData.parts) {
                                                                    const partInfo = extractPartInfo(part, currentTypeId, rarityKey, 'Heavy Weapon', manufacturer, manufacturer, 'Heavy Weapon');
                                                                    if (partInfo) {
                                                                        let targetTypeId = currentTypeId;
                                                                        if (partInfo.fullId.includes(':')) {
                                                                            const colonIndex = partInfo.fullId.indexOf(':');
                                                                            const extractedTypeId = parseInt(partInfo.fullId.substring(0, colonIndex));
                                                                            if (!isNaN(extractedTypeId)) {
                                                                                partInfo.typeId = extractedTypeId;
                                                                                targetTypeId = extractedTypeId;
                                                                                const afterColon = partInfo.fullId.substring(colonIndex + 1);
                                                                                partsMap.set(afterColon, partInfo);
                                                                                const numericPartId = parseInt(afterColon);
                                                                                if (!isNaN(numericPartId)) {
                                                                                    partsMap.set(numericPartId, partInfo);
                                                                                }
                                                                            }
                                                                        } else {
                                                                            partInfo.typeId = currentTypeId;
                                                                            targetTypeId = currentTypeId;
                                                                        }
                                                                        
                                                                        partsMap.set(partInfo.fullId, partInfo);
                                                                        partsMap.set(partInfo.id, partInfo);
                                                                        if (partInfo.spawnCode) {
                                                                            partsMap.set(partInfo.spawnCode, partInfo);
                                                                        }
                                                                        if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                                                            partsMap.set(partInfo.string, partInfo);
                                                                        }
                                                                        if (!partsByTypeId.has(targetTypeId)) {
                                                                            partsByTypeId.set(targetTypeId, []);
                                                                        }
                                                                        partsByTypeId.get(targetTypeId).push(partInfo);
                                                                        totalPartsExtracted++;
                                                                        
                                                                        // Debug log for comp parts
                                                                        if ((partInfo.spawnCode && String(partInfo.spawnCode).includes('.comp_')) || (partInfo.string && String(partInfo.string).includes('.comp_'))) {
                                                                            console.log(`    ✓ Extracted comp part: ${partInfo.name} (fullId: ${partInfo.fullId}, id: ${partInfo.id}, typeId: ${partInfo.typeId}, spawnCode: ${partInfo.spawnCode}, string: ${partInfo.string})`);
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                            if (rarityData.part_types) {
                                                                extractFromRarities(rarityData.part_types, currentTypeId);
                                                            }
                                                        }
                                                    };
                                                    extractFromRarities(data.Rarities, typeId);
                                                }
                                            } else {
                                                console.warn(`No typeId found for ${manufacturer} heavy_weapons`);
                                            }
                                        }
                                    }
                                }
                                continue; // Skip the normal processing for ordonances
                            }
                            
                            // Direct structure - manufacturers are keys in subsection
                            console.log(`gadgets.${subsectionName} has direct manufacturer structure`);
                            manufacturersToProcess = subsection;
                        }
                        
                        if (manufacturersToProcess) {
                            for (const [manufacturer, data] of Object.entries(manufacturersToProcess)) {
                                let typeId = null;
                                
                                // Check for type_id at manufacturer level
                                if (data.type_id) {
                                    typeId = data.type_id;
                                    console.log(`Found type_id ${typeId} directly on ${manufacturer} ${subsectionName}`);
                                } else {
                                    // Extract type_id from part IDs (format: "type_id:part_id")
                                    // Look through all parts to find a type_id
                                    const findTypeIdFromParts = (partTypes) => {
                                        for (const [partTypeKey, partTypeData] of Object.entries(partTypes)) {
                                            if (partTypeData.parts && Array.isArray(partTypeData.parts)) {
                                                for (const part of partTypeData.parts) {
                                                    if (part.id && typeof part.id === 'string' && part.id.includes(':')) {
                                                        const typeIdStr = part.id.split(':')[0];
                                                        const parsedTypeId = parseInt(typeIdStr);
                                                        if (!isNaN(parsedTypeId)) {
                                                            return parsedTypeId;
                                                        }
                                                    }
                                                }
                                            }
                                            // Also check nested structures (like Rarities.Rarity)
                                            if (partTypeData.part_types) {
                                                const nestedTypeId = findTypeIdFromParts(partTypeData.part_types);
                                                if (nestedTypeId) return nestedTypeId;
                                            }
                                        }
                                        return null;
                                    };
                                    
                                    if (data.part_types) {
                                        typeId = findTypeIdFromParts(data.part_types);
                                    }
                                }
                                
                                if (typeId) {
                                    if (!typeIdMap.has(typeId)) {
                                        // Known grenade/ordnance typeIds (from excelitemtype data)
                                        // These should NEVER be categorized as repkits
                                        const grenadeTypeIds = new Set([263, 267, 270, 272, 278, 291, 298, 311]); // Grenade typeIds
                                        const repkitTypeIds = new Set([261, 265, 266, 269, 274, 277, 285, 290]); // Repkit typeIds
                                        
                                        let categoryName = subsectionName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                                        
                                        // Ensure grenade typeIds are always categorized as Grenades, not Repkits
                                        if (grenadeTypeIds.has(typeId)) {
                                            categoryName = 'Grenades';
                                            console.log(`[FIX] Type ID ${typeId} is a grenade typeId, forcing category to 'Grenades' (was: ${subsectionName})`);
                                        } else if (repkitTypeIds.has(typeId) && subsectionName === 'repkits') {
                                            categoryName = 'Repkits';
                                        }
                                        
                                        typeIdMap.set(typeId, {
                                            id: typeId,
                                            name: subsectionName.slice(0, -1), // Remove 's' if plural
                                            category: categoryName,
                                            manufacturer: manufacturer
                                        });
                                        console.log(`Added type ID ${typeId}: ${manufacturer} ${subsectionName} (category: ${categoryName})`);
                                    } else {
                                        // If typeId already exists, ensure it has the correct category
                                        const existingEntry = typeIdMap.get(typeId);
                                        const grenadeTypeIds = new Set([263, 267, 270, 272, 278, 291, 298, 311]);
                                        if (grenadeTypeIds.has(typeId) && existingEntry.category !== 'Grenades') {
                                            existingEntry.category = 'Grenades';
                                            console.log(`[FIX] Updated existing type ID ${typeId} category from '${existingEntry.category}' to 'Grenades'`);
                                        }
                                    }
                                    
                                    if (!partsByTypeId.has(typeId)) {
                                        partsByTypeId.set(typeId, []);
                                    }
                                    
                                    // Extract parts from part_types (recursive to handle nested structures like Rarities.Rarity)
                                    // First check for Rarities at the same level as part_types
                                    if (data.Rarities) {
                                        console.log(`  Found Rarities section at top level for ${manufacturer} ${subsectionName} (Type ID: ${typeId})`);
                                        const extractFromRarities = (raritiesData, currentTypeId) => {
                                            for (const [rarityKey, rarityData] of Object.entries(raritiesData)) {
                                                if (rarityData.parts && Array.isArray(rarityData.parts)) {
                                                    console.log(`  Extracting ${rarityData.parts.length} parts from Rarities.${rarityKey} (Type ID: ${currentTypeId})`);
                                                    for (const part of rarityData.parts) {
                                                        const partInfo = extractPartInfo(part, currentTypeId, rarityKey, subsectionName, manufacturer, manufacturer, subsectionName);
                                                        if (partInfo) {
                                                            let targetTypeId = currentTypeId;
                                                            if (partInfo.fullId.includes(':')) {
                                                                const colonIndex = partInfo.fullId.indexOf(':');
                                                                const extractedTypeId = parseInt(partInfo.fullId.substring(0, colonIndex));
                                                                if (!isNaN(extractedTypeId)) {
                                                                    partInfo.typeId = extractedTypeId;
                                                                    targetTypeId = extractedTypeId;
                                                                    const afterColon = partInfo.fullId.substring(colonIndex + 1);
                                                                    partsMap.set(afterColon, partInfo);
                                                                    // Also store by the numeric part ID as a number
                                                                    const numericPartId = parseInt(afterColon);
                                                                    if (!isNaN(numericPartId)) {
                                                                        partsMap.set(numericPartId, partInfo);
                                                                    }
                                                                }
                                                            } else {
                                                                partInfo.typeId = currentTypeId;
                                                                targetTypeId = currentTypeId;
                                                            }
                                                            // Preserve spawn_code/string from existing part if this extraction would overwrite with a stub (e.g. part_types entry without spawn_code)
                                                            var existingPart = partsMap.get(partInfo.fullId);
                                                            if (existingPart && !(partInfo.spawnCode || partInfo.string) && (existingPart.spawnCode || existingPart.string)) {
                                                                partInfo.spawnCode = partInfo.spawnCode || existingPart.spawnCode || '';
                                                                partInfo.string = partInfo.string || existingPart.string || partInfo.spawnCode;
                                                            }
                                                            partsMap.set(partInfo.fullId, partInfo);
                                                            partsMap.set(partInfo.id, partInfo);
                                                            if (partInfo.spawnCode) {
                                                                partsMap.set(partInfo.spawnCode, partInfo);
                                                            }
                                                            if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                                                partsMap.set(partInfo.string, partInfo);
                                                            }
                                                            if (!partsByTypeId.has(targetTypeId)) {
                                                                partsByTypeId.set(targetTypeId, []);
                                                            }
                                                            partsByTypeId.get(targetTypeId).push(partInfo);
                                                            totalPartsExtracted++;
                                                            
                                                            // Debug log for part 7 in typeId 267
                                                            if ((partInfo.id === '7' || partInfo.fullId === '267:7' || partInfo.id === 7) && (currentTypeId === 267 || targetTypeId === 267)) {
                                                                console.log(`    ✓ Extracted part 7 from Rarities for typeId 267: ${partInfo.name} (fullId: ${partInfo.fullId}, id: ${partInfo.id}, typeId: ${partInfo.typeId}, targetTypeId: ${targetTypeId})`);
                                                            }
                                                        }
                                                    }
                                                }
                                                if (rarityData.part_types) {
                                                    extractFromRarities(rarityData.part_types, currentTypeId);
                                                }
                                            }
                                        };
                                        extractFromRarities(data.Rarities, typeId);
                                    }
                                    
                                    const extractPartsRecursive = (partTypes, currentTypeId, path = '') => {
                                        for (const [partTypeKey, partTypeData] of Object.entries(partTypes)) {
                                            const currentPath = path ? `${path}.${partTypeKey}` : partTypeKey;
                                            
                                            // Check if this is a Rarity section - log it for debugging
                                            if (partTypeKey === 'Rarity' || partTypeKey === 'Rarities' || currentPath.includes('Rarity')) {
                                                console.log(`  Found Rarity section at ${currentPath} (Type ID: ${currentTypeId})`);
                                            }
                                            
                                            // Check if this is a Main Body section for typeId 247 - log it for debugging
                                            if ((partTypeKey === 'Main Body' || partTypeKey === 'main body' || partTypeKey === 'MainBody') && currentTypeId === 247) {
                                                console.log(`  Found Main Body section at ${currentPath} (Type ID: ${currentTypeId})`);
                                            }
                                            
                                            if (partTypeData.parts && Array.isArray(partTypeData.parts)) {
                                                console.log(`  Extracting ${partTypeData.parts.length} parts from ${currentPath} (Type ID: ${currentTypeId})`);
                                                for (const part of partTypeData.parts) {
                                                    // For Main Body parts in typeId 247, ensure they're properly categorized
                                                    let targetTypeIdForPart = currentTypeId;
                                                    if ((partTypeKey === 'Main Body' || partTypeKey === 'main body' || partTypeKey === 'MainBody') && currentTypeId === 247) {
                                                        // Main Body parts should be typeId 247
                                                        targetTypeIdForPart = 247;
                                                    }
                                                    
                                                    const partInfo = extractPartInfo(
                                                        part, targetTypeIdForPart, partTypeKey, subsectionName, manufacturer, manufacturer, subsectionName
                                                    );
                                                    if (partInfo) {
                                                        // Set path property for better categorization
                                                        partInfo.path = currentPath;
                                                        
                                                        // Check if this is a Main Body part (typeId 247, parts 76-80)
                                                        const isMainBodyPart = partTypeKey === 'Main Body' || partTypeKey === 'main body' || partTypeKey === 'MainBody';
                                                        if (isMainBodyPart) {
                                                            partInfo.partType = 'Main Body';
                                                            partInfo.typeId = 247;
                                                        }
                                                        
                                                        // Special handling for Shield parts within repkits - they should be separate
                                                        // Shield parts have their own typeId (e.g., 321) and should not be treated as repkit parts
                                                        const isShieldPart = partTypeKey === 'Shield' || partTypeKey === 'shield';
                                                        if (isShieldPart && (currentTypeId === 243 || subsectionName === 'repkits')) {
                                                            // Shield parts within repkits should use their extracted typeId, not repkit typeId
                                                            partInfo.partType = 'Shield';
                                                            console.log(`[DEBUG] Set partType=Shield for Shield part ${partInfo.fullId || partInfo.id}: ${partInfo.name} (within repkit)`);
                                                        }
                                                        
                                                        // For repkits (typeId 243), set partType based on partTypeKey (but not for Shield parts)
                                                        if (!isShieldPart && (currentTypeId === 243 || targetTypeIdForPart === 243 || (partInfo.fullId && partInfo.fullId.startsWith('243:')))) {
                                                            if (partTypeKey === 'Resistance' || partTypeKey === 'resistance') {
                                                                partInfo.partType = 'Resistance';
                                                                console.log(`[DEBUG] Set partType=Resistance for part ${partInfo.fullId || partInfo.id}: ${partInfo.name}`);
                                                            } else if (partTypeKey === 'Immunity' || partTypeKey === 'immunity') {
                                                                partInfo.partType = 'Immunity';
                                                                console.log(`[DEBUG] Set partType=Immunity for part ${partInfo.fullId || partInfo.id}: ${partInfo.name}`);
                                                            } else if (partTypeKey === 'Splat' || partTypeKey === 'splat') {
                                                                partInfo.partType = 'Splat';
                                                                console.log(`[DEBUG] Set partType=Splat for part ${partInfo.fullId || partInfo.id}: ${partInfo.name}`);
                                                            } else if (partTypeKey === 'Nova' || partTypeKey === 'nova') {
                                                                partInfo.partType = 'Nova';
                                                                console.log(`[DEBUG] Set partType=Nova for part ${partInfo.fullId || partInfo.id}: ${partInfo.name}`);
                                                            } else if (partTypeKey === 'Size' || partTypeKey === 'size') {
                                                                partInfo.partType = 'Size';
                                                                console.log(`[DEBUG] Set partType=Size for part ${partInfo.fullId || partInfo.id}: ${partInfo.name}`);
                                                            } else if (partTypeKey === 'Elemental' || partTypeKey === 'elemental') {
                                                                // Elemental parts might be categorized differently, but set partType for reference
                                                                partInfo.partType = 'Elemental';
                                                                console.log(`[DEBUG] Set partType=Elemental for part ${partInfo.fullId || partInfo.id}: ${partInfo.name}`);
                                                            } else if (partTypeKey === 'Augment' || partTypeKey === 'augment') {
                                                                // Augment parts are body parts for repkits (same as Base)
                                                                partInfo.partType = 'Augment';
                                                                console.log(`[DEBUG] Set partType=Augment for part ${partInfo.fullId || partInfo.id}: ${partInfo.name}`);
                                                            } else if (partTypeKey === 'Base' || partTypeKey === 'base') {
                                                                // Base parts are body parts for repkits
                                                                partInfo.partType = 'Base';
                                                                console.log(`[DEBUG] Set partType=Base for part ${partInfo.fullId || partInfo.id}: ${partInfo.name}`);
                                                            }
                                                        }
                                                        
                                                        // For grenades/ordnance (typeId 245), set partType based on partTypeKey
                                                        if (currentTypeId === 245 || targetTypeIdForPart === 245 || (partInfo.fullId && partInfo.fullId.startsWith('245:'))) {
                                                            if (partTypeKey === 'Payload' || partTypeKey === 'payload') {
                                                                partInfo.partType = 'Payload';
                                                                console.log(`[DEBUG] Set partType=Payload for part ${partInfo.fullId || partInfo.id}: ${partInfo.name}`);
                                                            } else if (partTypeKey === 'Augment' || partTypeKey === 'augment') {
                                                                partInfo.partType = 'Augment';
                                                                console.log(`[DEBUG] Set partType=Augment for part ${partInfo.fullId || partInfo.id}: ${partInfo.name}`);
                                                            } else if (partTypeKey === 'Stats' || partTypeKey === 'stats' || partTypeKey === 'Stat') {
                                                                partInfo.partType = 'Stats';
                                                                console.log(`[DEBUG] Set partType=Stats for part ${partInfo.fullId || partInfo.id}: ${partInfo.name}`);
                                                            } else if (partTypeKey === 'Firmware' || partTypeKey === 'firmware') {
                                                                partInfo.partType = 'Firmware';
                                                                console.log(`[DEBUG] Set partType=Firmware for part ${partInfo.fullId || partInfo.id}: ${partInfo.name}`);
                                                            }
                                                        }
                                                        
                                                        // If part ID contains a colon (type:value format), extract the type ID and update partInfo
                                                        let targetTypeId = currentTypeId;
                                                        if (partInfo.fullId.includes(':')) {
                                                            const colonIndex = partInfo.fullId.indexOf(':');
                                                            const extractedTypeId = parseInt(partInfo.fullId.substring(0, colonIndex));
                                                            const afterColon = partInfo.fullId.substring(colonIndex + 1);
                                                            const numericPartId = parseInt(afterColon);
                                                            
                                                            // For Main Body parts (76-80), always use typeId 247
                                                            if (isMainBodyPart && numericPartId >= 76 && numericPartId <= 80) {
                                                                partInfo.typeId = 247;
                                                                targetTypeId = 247;
                                                            } else if (!isNaN(extractedTypeId)) {
                                                                // Update the partInfo's typeId to match the extracted type ID
                                                                partInfo.typeId = extractedTypeId;
                                                                targetTypeId = extractedTypeId;
                                                            }
                                                            
                                                            // Also store just the numeric part after colon for lookup
                                                            partsMap.set(afterColon, partInfo);
                                                            // Also store by the numeric part ID as a number
                                                            if (!isNaN(numericPartId)) {
                                                                partsMap.set(numericPartId, partInfo);
                                                            }
                                                        } else {
                                                            // For simple numeric IDs (no colon), check if it's a Main Body part (76-80)
                                                            const partIdNum = parseInt(partInfo.id || partInfo.fullId || '');
                                                            if (isMainBodyPart && !isNaN(partIdNum) && partIdNum >= 76 && partIdNum <= 80) {
                                                                partInfo.typeId = 247;
                                                                targetTypeId = 247;
                                                            } else {
                                                                // For simple numeric IDs (no colon), ensure typeId is set to currentTypeId
                                                                // This is important for parts from Rarities sections
                                                                partInfo.typeId = currentTypeId;
                                                                targetTypeId = currentTypeId;
                                                            }
                                                        }
                                                        
                                                        // Ensure Main Body parts are stored in typeId 247 collection
                                                        if (isMainBodyPart && partInfo.typeId === 247) {
                                                            targetTypeId = 247;
                                                            if (!partsByTypeId.has(247)) {
                                                                partsByTypeId.set(247, []);
                                                            }
                                                        }
                                                        
                                                        // Preserve spawn_code/string from existing part (e.g. from data.Rarities) if this path has a stub without it
                                                        var existingPartRec = partsMap.get(partInfo.fullId);
                                                        if (existingPartRec && !(partInfo.spawnCode || partInfo.string) && (existingPartRec.spawnCode || existingPartRec.string)) {
                                                            partInfo.spawnCode = partInfo.spawnCode || existingPartRec.spawnCode || '';
                                                            partInfo.string = partInfo.string || existingPartRec.string || partInfo.spawnCode;
                                                        }
                                                        // Store with both fullId and simple id
                                                        partsMap.set(partInfo.fullId, partInfo);
                                                        partsMap.set(partInfo.id, partInfo);
                                                        
                                                        // Store by spawn_code for string lookup
                                                        if (partInfo.spawnCode) {
                                                            partsMap.set(partInfo.spawnCode, partInfo);
                                                        }
                                                        // Also store by string field if different from spawnCode
                                                        if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                                            partsMap.set(partInfo.string, partInfo);
                                                        }
                                                        
                                                        // Store in the target type ID's collection
                                                        if (!partsByTypeId.has(targetTypeId)) {
                                                            partsByTypeId.set(targetTypeId, []);
                                                        }
                                                        partsByTypeId.get(targetTypeId).push(partInfo);
                                                        totalPartsExtracted++;
                                                        
                                                        // Debug log for Main Body parts (76-80)
                                                        if (isMainBodyPart) {
                                                            const partIdNum = parseInt(partInfo.id.split(':')[1] || partInfo.id || '');
                                                            if (!isNaN(partIdNum) && partIdNum >= 76 && partIdNum <= 80) {
                                                                console.log(`    ✓ Extracted Main Body part ${partIdNum}: ${partInfo.name} (fullId: ${partInfo.fullId}, id: ${partInfo.id}, typeId: ${partInfo.typeId}, targetTypeId: ${targetTypeId}, currentTypeId: ${currentTypeId}, partType: ${partInfo.partType}, path: ${partInfo.path})`);
                                                            }
                                                        }
                                                        
                                                        // Debug log for part 7 in typeId 267 (Jakobs Grenade rarity)
                                                        if ((partInfo.id === '7' || partInfo.fullId === '267:7') && currentTypeId === 267) {
                                                            console.log(`    ✓ Extracted part 7 for typeId 267: ${partInfo.name} (fullId: ${partInfo.fullId}, id: ${partInfo.id}, typeId: ${partInfo.typeId}, targetTypeId: ${targetTypeId}, currentTypeId: ${currentTypeId}, partType: ${partTypeKey}, path: ${currentPath})`);
                                                        }
                                                        // Debug log for any part with id "7" to track rarity parts
                                                        if (partInfo.id === '7' || String(partInfo.id) === '7') {
                                                            console.log(`    ✓ Extracted part with id 7: ${partInfo.name} (fullId: ${partInfo.fullId}, id: ${partInfo.id}, typeId: ${partInfo.typeId}, targetTypeId: ${targetTypeId}, currentTypeId: ${currentTypeId}, partType: ${partTypeKey}, path: ${currentPath})`);
                                                        }
                                                        // Debug log for Augment parts to track categorization (especially for repkits)
                                                        if (partTypeKey === 'Augment' || partTypeKey === 'augment' || currentPath.toLowerCase().includes('augment')) {
                                                            console.log(`    ✓ Extracted Augment part: ${partInfo.name} (fullId: ${partInfo.fullId}, id: ${partInfo.id}, typeId: ${partInfo.typeId}, partType: ${partInfo.partType}, path: ${partInfo.path}, spawnCode: ${partInfo.spawnCode})`);
                                                        }
                                                        // Debug log for Shield parts within repkits to track extraction
                                                        if (isShieldPart && (currentTypeId === 243 || subsectionName === 'repkits')) {
                                                            console.log(`    ✓ Extracted Shield part from repkit: ${partInfo.name} (fullId: ${partInfo.fullId}, id: ${partInfo.id}, typeId: ${partInfo.typeId}, targetTypeId: ${targetTypeId}, partType: ${partInfo.partType}, path: ${partInfo.path}, spawnCode: ${partInfo.spawnCode})`);
                                                        }
                                                    }
                                                }
                                            }
                                            // Special handling for Rarities sections - check if it has nested Rarity structures
                                            if (partTypeKey === 'Rarities' || partTypeKey === 'Rarity') {
                                                // Check for nested Rarity structures (Rarities.Rarity.parts)
                                                if (partTypeData.Rarity && partTypeData.Rarity.parts && Array.isArray(partTypeData.Rarity.parts)) {
                                                    console.log(`  Extracting ${partTypeData.Rarity.parts.length} parts from ${currentPath}.Rarity (Type ID: ${currentTypeId})`);
                                                    for (const part of partTypeData.Rarity.parts) {
                                                        const partInfo = extractPartInfo(
                                                            part, currentTypeId, 'Rarity', subsectionName, manufacturer, manufacturer, subsectionName
                                                        );
                                                        if (partInfo) {
                                                            let targetTypeId = currentTypeId;
                                                            if (partInfo.fullId.includes(':')) {
                                                                const colonIndex = partInfo.fullId.indexOf(':');
                                                                const extractedTypeId = parseInt(partInfo.fullId.substring(0, colonIndex));
                                                                if (!isNaN(extractedTypeId)) {
                                                                    partInfo.typeId = extractedTypeId;
                                                                    targetTypeId = extractedTypeId;
                                                                    const afterColon = partInfo.fullId.substring(colonIndex + 1);
                                                                    partsMap.set(afterColon, partInfo);
                                                                    const numericPartId = parseInt(afterColon);
                                                                    if (!isNaN(numericPartId)) {
                                                                        partsMap.set(numericPartId, partInfo);
                                                                    }
                                                                }
                                                            } else {
                                                                partInfo.typeId = currentTypeId;
                                                                targetTypeId = currentTypeId;
                                                            }
                                                            
                                                            partsMap.set(partInfo.fullId, partInfo);
                                                            partsMap.set(partInfo.id, partInfo);
                                                            if (partInfo.spawnCode) {
                                                                partsMap.set(partInfo.spawnCode, partInfo);
                                                            }
                                                            if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                                                partsMap.set(partInfo.string, partInfo);
                                                            }
                                                            if (!partsByTypeId.has(targetTypeId)) {
                                                                partsByTypeId.set(targetTypeId, []);
                                                            }
                                                            partsByTypeId.get(targetTypeId).push(partInfo);
                                                            totalPartsExtracted++;
                                                            
                                                            // Debug log for comp parts
                                                            if ((partInfo.spawnCode && String(partInfo.spawnCode).includes('.comp_')) || (partInfo.string && String(partInfo.string).includes('.comp_'))) {
                                                                console.log(`    ✓ Extracted comp part: ${partInfo.name} (fullId: ${partInfo.fullId}, id: ${partInfo.id}, typeId: ${partInfo.typeId}, spawnCode: ${partInfo.spawnCode}, string: ${partInfo.string}, path: ${currentPath}.Rarity)`);
                                                            }
                                                        }
                                                    }
                                                }
                                                // Also check for direct parts array in Rarities (some structures might have parts directly)
                                                if (partTypeData.parts && Array.isArray(partTypeData.parts)) {
                                                    console.log(`  Extracting ${partTypeData.parts.length} parts from ${currentPath} (direct parts array) (Type ID: ${currentTypeId})`);
                                                    for (const part of partTypeData.parts) {
                                                        const partInfo = extractPartInfo(
                                                            part, currentTypeId, partTypeKey, subsectionName, manufacturer, manufacturer, subsectionName
                                                        );
                                                        if (partInfo) {
                                                            let targetTypeId = currentTypeId;
                                                            if (partInfo.fullId.includes(':')) {
                                                                const colonIndex = partInfo.fullId.indexOf(':');
                                                                const extractedTypeId = parseInt(partInfo.fullId.substring(0, colonIndex));
                                                                if (!isNaN(extractedTypeId)) {
                                                                    partInfo.typeId = extractedTypeId;
                                                                    targetTypeId = extractedTypeId;
                                                                    const afterColon = partInfo.fullId.substring(colonIndex + 1);
                                                                    partsMap.set(afterColon, partInfo);
                                                                    const numericPartId = parseInt(afterColon);
                                                                    if (!isNaN(numericPartId)) {
                                                                        partsMap.set(numericPartId, partInfo);
                                                                    }
                                                                }
                                                            } else {
                                                                partInfo.typeId = currentTypeId;
                                                                targetTypeId = currentTypeId;
                                                            }
                                                            
                                                            partsMap.set(partInfo.fullId, partInfo);
                                                            partsMap.set(partInfo.id, partInfo);
                                                            if (partInfo.spawnCode) {
                                                                partsMap.set(partInfo.spawnCode, partInfo);
                                                            }
                                                            if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                                                partsMap.set(partInfo.string, partInfo);
                                                            }
                                                            if (!partsByTypeId.has(targetTypeId)) {
                                                                partsByTypeId.set(targetTypeId, []);
                                                            }
                                                            partsByTypeId.get(targetTypeId).push(partInfo);
                                                            totalPartsExtracted++;
                                                            
                                                            // Debug log for comp parts
                                                            if ((partInfo.spawnCode && String(partInfo.spawnCode).includes('.comp_')) || (partInfo.string && String(partInfo.string).includes('.comp_'))) {
                                                                console.log(`    ✓ Extracted comp part: ${partInfo.name} (fullId: ${partInfo.fullId}, id: ${partInfo.id}, typeId: ${partInfo.typeId}, spawnCode: ${partInfo.spawnCode}, string: ${partInfo.string}, path: ${currentPath})`);
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                            // Recursively check nested part_types (like Rarities.Rarity)
                                            if (partTypeData.part_types) {
                                                extractPartsRecursive(partTypeData.part_types, currentTypeId, currentPath);
                                            }
                                        }
                                    };
                                    
                                    if (data.part_types) {
                                        extractPartsRecursive(data.part_types, typeId);
                                    }
                                    
                                    // Also check for Rarities at the top level (sibling to part_types)
                                    if (data.Rarities) {
                                        console.log(`  Found Rarities section at top level for ${manufacturer} ${subsectionName} (Type ID: ${typeId})`);
                                        const extractFromRarities = (raritiesData, currentTypeId) => {
                                            for (const [rarityKey, rarityData] of Object.entries(raritiesData)) {
                                                if (rarityData.parts && Array.isArray(rarityData.parts)) {
                                                    console.log(`  Extracting ${rarityData.parts.length} parts from Rarities.${rarityKey} (Type ID: ${currentTypeId})`);
                                                    for (const part of rarityData.parts) {
                                                        const partInfo = extractPartInfo(part, currentTypeId, rarityKey, subsectionName, manufacturer, manufacturer, subsectionName);
                                                        if (partInfo) {
                                                            let targetTypeId = currentTypeId;
                                                            if (partInfo.fullId.includes(':')) {
                                                                const colonIndex = partInfo.fullId.indexOf(':');
                                                                const extractedTypeId = parseInt(partInfo.fullId.substring(0, colonIndex));
                                                                if (!isNaN(extractedTypeId)) {
                                                                    partInfo.typeId = extractedTypeId;
                                                                    targetTypeId = extractedTypeId;
                                                                    const afterColon = partInfo.fullId.substring(colonIndex + 1);
                                                                    partsMap.set(afterColon, partInfo);
                                                                    const numericPartId = parseInt(afterColon);
                                                                    if (!isNaN(numericPartId)) {
                                                                        partsMap.set(numericPartId, partInfo);
                                                                    }
                                                                }
                                                            } else {
                                                                partInfo.typeId = currentTypeId;
                                                                targetTypeId = currentTypeId;
                                                            }
                                                            
                                                            partsMap.set(partInfo.fullId, partInfo);
                                                            partsMap.set(partInfo.id, partInfo);
                                                            if (partInfo.spawnCode) {
                                                                partsMap.set(partInfo.spawnCode, partInfo);
                                                            }
                                                            if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                                                partsMap.set(partInfo.string, partInfo);
                                                            }
                                                            if (!partsByTypeId.has(targetTypeId)) {
                                                                partsByTypeId.set(targetTypeId, []);
                                                            }
                                                            partsByTypeId.get(targetTypeId).push(partInfo);
                                                            totalPartsExtracted++;
                                                            
                                                            // Debug log for comp parts
                                                            if ((partInfo.spawnCode && String(partInfo.spawnCode).includes('.comp_')) || (partInfo.string && String(partInfo.string).includes('.comp_'))) {
                                                                console.log(`    ✓ Extracted comp part: ${partInfo.name} (fullId: ${partInfo.fullId}, id: ${partInfo.id}, typeId: ${partInfo.typeId}, spawnCode: ${partInfo.spawnCode}, string: ${partInfo.string})`);
                                                            }
                                                        }
                                                    }
                                                }
                                                if (rarityData.part_types) {
                                                    extractFromRarities(rarityData.part_types, currentTypeId);
                                                }
                                            }
                                        };
                                        extractFromRarities(data.Rarities, typeId);
                                    }
                                    
                                    // Check for Firmware section (sibling to part_types) within manufacturer data
                                    // This handles firmware for repair kits (typeId 243), grenades (typeId 245), and heavy weapons (typeId 244)
                                    if (data.Firmware || data.firmware) {
                                        const firmwareData = data.Firmware || data.firmware;
                                        let firmwareTypeId = null;
                                        
                                        // Determine firmware typeId based on subsection
                                        if (subsectionName === 'repkits') {
                                            firmwareTypeId = 243;
                                        } else if (subsectionName === 'grenades' || (subsectionName === 'ordonances' && data.type_id)) {
                                            // For grenades, firmware uses typeId 245
                                            firmwareTypeId = 245;
                                        } else if (subsectionName === 'ordonances' && subsection.heavy_weapons) {
                                            // For heavy weapons, firmware uses typeId 244 (or the manufacturer's typeId)
                                            firmwareTypeId = typeId || 244;
                                        }
                                        
                                        if (firmwareTypeId) {
                                            console.log(`  Found Firmware section for ${manufacturer} ${subsectionName} (Type ID: ${firmwareTypeId})`);
                                            
                                            // For substat typeIds (243, 244, 245), always use 'Universal' as manufacturer for consistency
                                            const substatManufacturer = (firmwareTypeId === 243 || firmwareTypeId === 244 || firmwareTypeId === 245) ? 'Universal' : manufacturer;
                                            if (!typeIdMap.has(firmwareTypeId)) {
                                                const categoryName = subsectionName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                                                typeIdMap.set(firmwareTypeId, {
                                                    id: firmwareTypeId,
                                                    name: 'Firmware',
                                                    category: categoryName,
                                                    manufacturer: substatManufacturer
                                                });
                                                console.log(`Added type ID ${firmwareTypeId}: ${substatManufacturer} ${subsectionName} Firmware`);
                                            } else if (firmwareTypeId === 243 || firmwareTypeId === 244 || firmwareTypeId === 245) {
                                                // Update existing substat typeIds to use 'Universal' manufacturer
                                                const existingType = typeIdMap.get(firmwareTypeId);
                                                if (existingType && existingType.manufacturer !== 'Universal') {
                                                    existingType.manufacturer = 'Universal';
                                                    console.log(`Updated type ID ${firmwareTypeId} manufacturer to Universal`);
                                                }
                                            }
                                            
                                            if (!partsByTypeId.has(firmwareTypeId)) {
                                                partsByTypeId.set(firmwareTypeId, []);
                                            }
                                            
                                            // Handle different data structures
                                            let partsToExtract = [];
                                            
                                            if (firmwareData.parts && Array.isArray(firmwareData.parts)) {
                                                partsToExtract = firmwareData.parts;
                                                console.log(`  Extracting ${partsToExtract.length} Firmware parts from ${manufacturer} ${subsectionName}.Firmware (Type ID: ${firmwareTypeId}) - direct parts array`);
                                            } else if (firmwareData.part_types) {
                                                for (const [partType, partTypeData] of Object.entries(firmwareData.part_types)) {
                                                    if (partTypeData.parts && Array.isArray(partTypeData.parts)) {
                                                        partsToExtract.push(...partTypeData.parts);
                                                    }
                                                }
                                                console.log(`  Extracting ${partsToExtract.length} Firmware parts from ${manufacturer} ${subsectionName}.Firmware (Type ID: ${firmwareTypeId}) - part_types structure`);
                                            } else if (Array.isArray(firmwareData)) {
                                                partsToExtract = firmwareData;
                                                console.log(`  Extracting ${partsToExtract.length} Firmware parts from ${manufacturer} ${subsectionName}.Firmware (Type ID: ${firmwareTypeId}) - direct array`);
                                            } else {
                                                const keys = Object.keys(firmwareData || {});
                                                const numericKeys = keys.filter(k => /^\d+$/.test(k));
                                                if (numericKeys.length > 0) {
                                                    partsToExtract = numericKeys.map(k => firmwareData[k]).filter(p => p != null);
                                                    console.log(`  Extracting ${partsToExtract.length} Firmware parts from ${manufacturer} ${subsectionName}.Firmware (Type ID: ${firmwareTypeId}) - array-like object`);
                                                }
                                            }
                                            
                                            // Extract all Firmware parts (including skillcraft)
                                            for (const part of partsToExtract) {
                                                if (!part) continue;
                                                const partIdStr = part.id ? String(part.id) : '';
                                                const hasFirmwareId = partIdStr.startsWith(`${firmwareTypeId}:`);
                                                const hasTypeIdFirmware = part.type_id === firmwareTypeId || (firmwareData && firmwareData.type_id === firmwareTypeId);
                                                const isNumericId = /^\d+$/.test(partIdStr);
                                                // Also check spawn_code for skillcraft firmware (case-insensitive)
                                                const spawnCode = String(part.spawn_code || part.spawnCode || part.string || '').toLowerCase();
                                                const isSkillcraftFirmware = spawnCode.includes('part_firmware_skillcraft');
                                                
                                                if (hasFirmwareId || (hasTypeIdFirmware && (isNumericId || !partIdStr.includes(':'))) || (!hasFirmwareId && !hasTypeIdFirmware && (isNumericId || isSkillcraftFirmware))) {
                                                    let normalizedPart = part;
                                                    if (isNumericId && !hasFirmwareId) {
                                                        normalizedPart = {...part, id: `${firmwareTypeId}:${partIdStr}`};
                                                    } else if (isSkillcraftFirmware && !hasFirmwareId && !hasTypeIdFirmware) {
                                                        // For skillcraft firmware without standard ID, try to extract numeric ID from spawn_code or use spawn_code as fallback
                                                        const numericMatch = spawnCode.match(/(\d+)/);
                                                        if (numericMatch) {
                                                            normalizedPart = {...part, id: `${firmwareTypeId}:${numericMatch[1]}`};
                                                        } else {
                                                            const skillcraftId = spawnCode.replace(/\./g, '_').replace(/[^a-z0-9_]/g, '');
                                                            normalizedPart = {...part, id: `${firmwareTypeId}:${skillcraftId}`};
                                                        }
                                                    }
                                                    
                                                    const partInfo = extractPartInfo(normalizedPart, firmwareTypeId, 'Firmware', subsectionName, manufacturer, manufacturer, subsectionName);
                                                    if (partInfo) {
                                                        partInfo.typeId = firmwareTypeId;
                                                        partInfo.partType = 'Firmware';
                                                        partInfo.path = `${subsectionName}.${manufacturer}.Firmware`;
                                                        
                                                        // Ensure fullId is set correctly for Skillcraft (243:113, 244:88, 245:88) and other firmware parts
                                                        if (!partInfo.fullId || !partInfo.fullId.includes(':')) {
                                                            const partId = String(partInfo.id || normalizedPart.id || '');
                                                            if (partId && !partId.includes(':')) {
                                                                partInfo.fullId = `${firmwareTypeId}:${partId}`;
                                                                partInfo.id = `${firmwareTypeId}:${partId}`;
                                                            } else if (partId.includes(':')) {
                                                                partInfo.fullId = partId;
                                                            }
                                                        } else if (partInfo.id && !String(partInfo.id).includes(':')) {
                                                            partInfo.fullId = `${firmwareTypeId}:${partInfo.id}`;
                                                            partInfo.id = `${firmwareTypeId}:${partInfo.id}`;
                                                        }
                                                        
                                                        partsMap.set(partInfo.fullId, partInfo);
                                                        partsMap.set(partInfo.id, partInfo);
                                                        if (partInfo.spawnCode) {
                                                            partsMap.set(partInfo.spawnCode, partInfo);
                                                        }
                                                        if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                                            partsMap.set(partInfo.string, partInfo);
                                                        }
                                                        
                                                        // Also store by the numeric part ID after colon
                                                        if (partInfo.fullId.includes(':')) {
                                                            const afterColon = partInfo.fullId.split(':')[1];
                                                            partsMap.set(afterColon, partInfo);
                                                            const numericPartId = parseInt(afterColon);
                                                            if (!isNaN(numericPartId)) {
                                                                partsMap.set(numericPartId, partInfo);
                                                            }
                                                        }
                                                        
                                                        partsByTypeId.get(firmwareTypeId).push(partInfo);
                                                        totalPartsExtracted++;
                                                    }
                                                }
                                            }
                                            console.log(`  ✓ Extracted ${partsByTypeId.get(firmwareTypeId).filter(p => p.partType === 'Firmware').length} Firmware parts for typeId ${firmwareTypeId} from ${manufacturer} ${subsectionName}`);
                                        }
                                    }
                                    
                                    // Also check for Universal sections with part_types.Firmware (for repair kits, grenades, heavy weapons)
                                    // This handles firmware nested in Universal.part_types.Firmware
                                    for (const [sectionKey, sectionData] of Object.entries(data)) {
                                        // Skip sections we've already processed
                                        if (sectionKey === 'Firmware' || sectionKey === 'firmware' || 
                                            sectionKey === 'part_types' || sectionKey === 'Rarities' || 
                                            sectionKey === 'type_id' || typeof sectionData !== 'object' || !sectionData) {
                                            continue;
                                        }
                                        
                                        // Check if this section has the appropriate type_id for firmware
                                        let expectedTypeId = null;
                                        if (subsectionName === 'repkits' && sectionData.type_id === 243) {
                                            expectedTypeId = 243;
                                        } else if ((subsectionName === 'grenades' || subsectionName === 'ordonances') && sectionData.type_id === 245) {
                                            expectedTypeId = 245;
                                        } else if (subsectionName === 'ordonances' && sectionData.type_id === 244) {
                                            expectedTypeId = 244;
                                        }
                                        
                                        if (expectedTypeId && sectionData.part_types && sectionData.part_types.Firmware) {
                                            const firmwarePartType = sectionData.part_types.Firmware;
                                            if (firmwarePartType.parts && Array.isArray(firmwarePartType.parts)) {
                                                console.log(`  [DEBUG] Found Firmware parts in ${sectionKey}.part_types.Firmware for ${subsectionName} (${firmwarePartType.parts.length} parts, Type ID: ${expectedTypeId})`);
                                                
                                                if (!partsByTypeId.has(expectedTypeId)) {
                                                    partsByTypeId.set(expectedTypeId, []);
                                                }
                                                
                                                // Extract Firmware parts
                                                for (const part of firmwarePartType.parts) {
                                                    if (!part) continue;
                                                    const partIdStr = part.id ? String(part.id) : '';
                                                    const hasFirmwareId = partIdStr.startsWith(`${expectedTypeId}:`);
                                                    const hasTypeIdFirmware = part.type_id === expectedTypeId || (firmwarePartType && firmwarePartType.type_id === expectedTypeId);
                                                    const isNumericId = /^\d+$/.test(partIdStr);
                                                    // Also check spawn_code for skillcraft firmware (case-insensitive)
                                                    const spawnCode = String(part.spawn_code || part.spawnCode || part.string || '').toLowerCase();
                                                    const isSkillcraftFirmware = spawnCode.includes('part_firmware_skillcraft');
                                                    
                                                    if (hasFirmwareId || (hasTypeIdFirmware && (isNumericId || !partIdStr.includes(':'))) || (!hasFirmwareId && !hasTypeIdFirmware && (isNumericId || isSkillcraftFirmware))) {
                                                        let normalizedPart = part;
                                                        if (isNumericId && !hasFirmwareId) {
                                                            normalizedPart = {...part, id: `${expectedTypeId}:${partIdStr}`};
                                                        } else if (isSkillcraftFirmware && !hasFirmwareId && !hasTypeIdFirmware) {
                                                            // For skillcraft firmware without standard ID, try to extract numeric ID from spawn_code or use spawn_code as fallback
                                                            const numericMatch = spawnCode.match(/(\d+)/);
                                                            if (numericMatch) {
                                                                normalizedPart = {...part, id: `${expectedTypeId}:${numericMatch[1]}`};
                                                            } else {
                                                                const skillcraftId = spawnCode.replace(/\./g, '_').replace(/[^a-z0-9_]/g, '');
                                                                normalizedPart = {...part, id: `${expectedTypeId}:${skillcraftId}`};
                                                            }
                                                        }
                                                        
                                                        const partInfo = extractPartInfo(normalizedPart, expectedTypeId, 'Firmware', subsectionName, manufacturer, manufacturer, subsectionName);
                                                        if (partInfo) {
                                                            partInfo.typeId = expectedTypeId;
                                                            partInfo.partType = 'Firmware';
                                                            partInfo.path = `${subsectionName}.${sectionKey}.Firmware`;
                                                            
                                                            if (partInfo.id && !String(partInfo.id).includes(':')) {
                                                                partInfo.fullId = `${expectedTypeId}:${partInfo.id}`;
                                                                partInfo.id = `${expectedTypeId}:${partInfo.id}`;
                                                            }
                                                            
                                                            partsMap.set(partInfo.fullId, partInfo);
                                                            partsMap.set(partInfo.id, partInfo);
                                                            if (partInfo.spawnCode) {
                                                                partsMap.set(partInfo.spawnCode, partInfo);
                                                            }
                                                            if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                                                partsMap.set(partInfo.string, partInfo);
                                                            }
                                                            
                                                            if (partInfo.fullId.includes(':')) {
                                                                const afterColon = partInfo.fullId.split(':')[1];
                                                                partsMap.set(afterColon, partInfo);
                                                                const numericPartId = parseInt(afterColon);
                                                                if (!isNaN(numericPartId)) {
                                                                    partsMap.set(numericPartId, partInfo);
                                                                }
                                                            }
                                                            
                                                            partsByTypeId.get(expectedTypeId).push(partInfo);
                                                            totalPartsExtracted++;
                                                        }
                                                    }
                                                }
                                                console.log(`  ✓ Extracted ${partsByTypeId.get(expectedTypeId).filter(p => p.partType === 'Firmware' && p.path === `${subsectionName}.${sectionKey}.Firmware`).length} Firmware parts for typeId ${expectedTypeId} from ${sectionKey}.part_types.Firmware`);
                                            }
                                        }
                                    }
                                }
                            }
                            
                            // After processing manufacturers, check for top-level Universal sections in grenades (Payload, Augment, Stats, Firmware)
                            if ((subsectionName === 'grenades' || subsectionName === 'ordonances') && subsection.Universal) {
                                const universalData = subsection.Universal;
                                if (universalData.type_id === 245 && universalData.part_types) {
                                    console.log(`  [DEBUG] Found Universal section in gadgets.${subsectionName} with type_id 245`);
                                    
                                    if (!partsByTypeId.has(245)) {
                                        partsByTypeId.set(245, []);
                                    }
                                    
                                    // Extract parts from Universal.part_types (Payload, Augment, Stats, Firmware)
                                    const extractFromUniversal = (partTypes, currentTypeId, path = '') => {
                                        for (const [partTypeKey, partTypeData] of Object.entries(partTypes)) {
                                            const currentPath = path ? `${path}.${partTypeKey}` : partTypeKey;
                                            
                                            if (partTypeData.parts && Array.isArray(partTypeData.parts)) {
                                                console.log(`  Extracting ${partTypeData.parts.length} parts from Universal.${currentPath} (Type ID: ${currentTypeId})`);
                                                for (const part of partTypeData.parts) {
                                                    const partInfo = extractPartInfo(
                                                        part, currentTypeId, partTypeKey, subsectionName, 'Universal', 'Universal', subsectionName
                                                    );
                                                    if (partInfo) {
                                                        partInfo.path = `Universal.${currentPath}`;
                                                        partInfo.typeId = currentTypeId;
                                                        
                                                        // Set partType based on partTypeKey for grenades
                                                        if (partTypeKey === 'Payload' || partTypeKey === 'payload') {
                                                            partInfo.partType = 'Payload';
                                                        } else if (partTypeKey === 'Augment' || partTypeKey === 'augment') {
                                                            partInfo.partType = 'Augment';
                                                        } else if (partTypeKey === 'Stats' || partTypeKey === 'stats' || partTypeKey === 'Stat') {
                                                            partInfo.partType = 'Stats';
                                                        } else if (partTypeKey === 'Firmware' || partTypeKey === 'firmware') {
                                                            partInfo.partType = 'Firmware';
                                                        }
                                                        
                                                        // Ensure fullId is set correctly
                                                        if (partInfo.id && !String(partInfo.id).includes(':')) {
                                                            partInfo.fullId = `${currentTypeId}:${partInfo.id}`;
                                                            partInfo.id = `${currentTypeId}:${partInfo.id}`;
                                                        }
                                                        
                                                        partsMap.set(partInfo.fullId, partInfo);
                                                        partsMap.set(partInfo.id, partInfo);
                                                        if (partInfo.spawnCode) {
                                                            partsMap.set(partInfo.spawnCode, partInfo);
                                                        }
                                                        if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                                            partsMap.set(partInfo.string, partInfo);
                                                        }
                                                        if (partInfo.fullId.includes(':')) {
                                                            const afterColon = partInfo.fullId.split(':')[1];
                                                            partsMap.set(afterColon, partInfo);
                                                            const numericPartId = parseInt(afterColon);
                                                            if (!isNaN(numericPartId)) {
                                                                partsMap.set(numericPartId, partInfo);
                                                            }
                                                        }
                                                        
                                                        partsByTypeId.get(currentTypeId).push(partInfo);
                                                        totalPartsExtracted++;
                                                        
                                                        console.log(`    ✓ Extracted ${partTypeKey} part: ${partInfo.name} (fullId: ${partInfo.fullId}, id: ${partInfo.id}, typeId: ${partInfo.typeId}, partType: ${partInfo.partType})`);
                                                    }
                                                }
                                            }
                                            
                                            // Recursively process nested part_types
                                            if (partTypeData.part_types) {
                                                extractFromUniversal(partTypeData.part_types, currentTypeId, currentPath);
                                            }
                                        }
                                    };
                                    
                                    extractFromUniversal(universalData.part_types, 245);
                                    console.log(`  ✓ Extracted ${partsByTypeId.get(245).length} total parts from gadgets.${subsectionName}.Universal for typeId 245`);
                                }
                            }
                            
                            // After processing manufacturers, check for top-level sections in enhancements (Stats, Main Body)
                            if (subsectionName === 'enhancements') {
                                // Check for Stats section (typeId 247)
                                if (subsection.Stats || subsection.stats) {
                                    const statsData = subsection.Stats || subsection.stats;
                                    console.log(`  [DEBUG] Found Stats section in gadgets.enhancements`);
                                    
                                    // Add typeId 247 to typeIdMap if not already present
                                    if (!typeIdMap.has(247)) {
                                        typeIdMap.set(247, {
                                            id: 247,
                                            name: 'Enhancement Substats',
                                            category: 'Enhancement',
                                            context: null,
                                            manufacturer: null
                                        });
                                        console.log(`Added type ID 247: Enhancement Substats`);
                                    }
                                    
                                    if (!partsByTypeId.has(247)) {
                                        partsByTypeId.set(247, []);
                                    }
                                    
                                    // Handle different data structures
                                    let partsToExtract = [];
                                    
                                    if (statsData.parts && Array.isArray(statsData.parts)) {
                                        // Direct parts array
                                        partsToExtract = statsData.parts;
                                        console.log(`  Extracting ${partsToExtract.length} Stats parts from gadgets.enhancements.Stats (Type ID: 247) - direct parts array`);
                                    } else if (statsData.part_types) {
                                        // part_types structure
                                        console.log(`  [DEBUG] Stats section has part_types structure`);
                                        for (const [partType, partTypeData] of Object.entries(statsData.part_types)) {
                                            if (partTypeData.parts && Array.isArray(partTypeData.parts)) {
                                                partsToExtract.push(...partTypeData.parts);
                                            }
                                        }
                                        console.log(`  Extracting ${partsToExtract.length} Stats parts from gadgets.enhancements.Stats (Type ID: 247) - part_types structure`);
                                    } else if (Array.isArray(statsData)) {
                                        // Direct array
                                        partsToExtract = statsData;
                                        console.log(`  Extracting ${partsToExtract.length} Stats parts from gadgets.enhancements.Stats (Type ID: 247) - direct array`);
                                    } else {
                                        // Array-like object with numeric keys
                                        const keys = Object.keys(statsData);
                                        const numericKeys = keys.filter(k => /^\d+$/.test(k));
                                        if (numericKeys.length > 0) {
                                            partsToExtract = numericKeys.map(k => statsData[k]).filter(p => p != null);
                                            console.log(`  Extracting ${partsToExtract.length} Stats parts from gadgets.enhancements.Stats (Type ID: 247) - array-like object`);
                                        }
                                    }
                                    
                                    // Extract all Stats parts
                                    for (const part of partsToExtract) {
                                        if (!part) continue;
                                        const partIdStr = part.id ? String(part.id) : '';
                                        const has247Id = partIdStr.startsWith('247:');
                                        const hasTypeId247 = part.type_id === 247 || (statsData && statsData.type_id === 247);
                                        const isNumericId = /^\d+$/.test(partIdStr);
                                        
                                        if (has247Id || (hasTypeId247 && (isNumericId || !partIdStr.includes(':'))) || (!has247Id && !hasTypeId247 && isNumericId)) {
                                            let normalizedPart = part;
                                            if (isNumericId && !has247Id) {
                                                // Normalize numeric ID to "247:X" format
                                                normalizedPart = {...part, id: `247:${partIdStr}`};
                                            }
                                            
                                            const partInfo = extractPartInfo(normalizedPart, 247, 'Stats', 'Enhancement', 'Universal', 'Universal', 'enhancements');
                                            if (partInfo) {
                                                partInfo.typeId = 247;
                                                partInfo.partType = 'Stats';
                                                partInfo.path = 'enhancements.Stats';
                                                
                                                if (partInfo.id && !String(partInfo.id).includes(':')) {
                                                    partInfo.fullId = `247:${partInfo.id}`;
                                                    partInfo.id = `247:${partInfo.id}`;
                                                }
                                                
                                                partsMap.set(partInfo.fullId, partInfo);
                                                partsMap.set(partInfo.id, partInfo);
                                                if (partInfo.spawnCode) {
                                                    partsMap.set(partInfo.spawnCode, partInfo);
                                                }
                                                if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                                    partsMap.set(partInfo.string, partInfo);
                                                }
                                                
                                                if (partInfo.fullId.includes(':')) {
                                                    const afterColon = partInfo.fullId.split(':')[1];
                                                    partsMap.set(afterColon, partInfo);
                                                    const numericPartId = parseInt(afterColon);
                                                    if (!isNaN(numericPartId)) {
                                                        partsMap.set(numericPartId, partInfo);
                                                    }
                                                }
                                                
                                                partsByTypeId.get(247).push(partInfo);
                                                totalPartsExtracted++;
                                                
                                                // Debug log for parts 75 and 81
                                                if (partInfo.id === '75' || partInfo.fullId === '247:75' || partInfo.id === 75) {
                                                    console.log(`    ✓ Extracted Stats part 75: ${partInfo.name} (fullId: ${partInfo.fullId}, id: ${partInfo.id}, typeId: ${partInfo.typeId})`);
                                                }
                                                if (partInfo.id === '81' || partInfo.fullId === '247:81' || partInfo.id === 81) {
                                                    console.log(`    ✓ Extracted Stats part 81: ${partInfo.name} (fullId: ${partInfo.fullId}, id: ${partInfo.id}, typeId: ${partInfo.typeId})`);
                                                }
                                            }
                                        }
                                    }
                                    console.log(`  ✓ Extracted ${partsByTypeId.get(247).filter(p => p.partType === 'Stats' && p.path === 'enhancements.Stats').length} Stats parts for typeId 247 from top-level Stats section`);
                                }
                                
                                // Check for Main Body section (typeId 247, parts 76-80)
                                if (subsection['Main Body'] || subsection['main body'] || subsection['MainBody']) {
                                    const mainBodyData = subsection['Main Body'] || subsection['main body'] || subsection['MainBody'];
                                    console.log(`  [DEBUG] Found Main Body section in gadgets.enhancements`);
                                    
                                    if (!partsByTypeId.has(247)) {
                                        partsByTypeId.set(247, []);
                                    }
                                    
                                    // Handle different data structures
                                    let partsToExtract = [];
                                    
                                    if (mainBodyData.parts && Array.isArray(mainBodyData.parts)) {
                                        // Direct parts array
                                        partsToExtract = mainBodyData.parts;
                                        console.log(`  Extracting ${partsToExtract.length} Main Body parts from gadgets.enhancements.Main Body (Type ID: 247) - direct parts array`);
                                    } else if (mainBodyData.part_types) {
                                        // part_types structure
                                        console.log(`  [DEBUG] Main Body section has part_types structure`);
                                        for (const [partType, partTypeData] of Object.entries(mainBodyData.part_types)) {
                                            if (partTypeData.parts && Array.isArray(partTypeData.parts)) {
                                                partsToExtract.push(...partTypeData.parts);
                                            }
                                        }
                                        console.log(`  Extracting ${partsToExtract.length} Main Body parts from gadgets.enhancements.Main Body (Type ID: 247) - part_types structure`);
                                    } else if (Array.isArray(mainBodyData)) {
                                        // Direct array
                                        partsToExtract = mainBodyData;
                                        console.log(`  Extracting ${partsToExtract.length} Main Body parts from gadgets.enhancements.Main Body (Type ID: 247) - direct array`);
                                    } else {
                                        // Array-like object with numeric keys
                                        const keys = Object.keys(mainBodyData);
                                        const numericKeys = keys.filter(k => /^\d+$/.test(k));
                                        if (numericKeys.length > 0) {
                                            partsToExtract = numericKeys.map(k => mainBodyData[k]).filter(p => p != null);
                                            console.log(`  Extracting ${partsToExtract.length} Main Body parts from gadgets.enhancements.Main Body (Type ID: 247) - array-like object`);
                                        }
                                    }
                                    
                                    // Extract all Main Body parts (should be parts 76-80)
                                    for (const part of partsToExtract) {
                                        if (!part) continue;
                                        const partIdStr = part.id ? String(part.id) : '';
                                        const has247Id = partIdStr.startsWith('247:');
                                        const hasTypeId247 = part.type_id === 247 || (mainBodyData && mainBodyData.type_id === 247);
                                        const isNumericId = /^\d+$/.test(partIdStr);
                                        
                                        if (has247Id || (hasTypeId247 && (isNumericId || !partIdStr.includes(':'))) || (!has247Id && !hasTypeId247 && isNumericId)) {
                                            let normalizedPart = part;
                                            if (isNumericId && !has247Id) {
                                                // Normalize numeric ID to "247:X" format
                                                normalizedPart = {...part, id: `247:${partIdStr}`};
                                            }
                                            
                                            const partInfo = extractPartInfo(normalizedPart, 247, 'Main Body', 'Enhancement', 'Universal', 'Universal', 'enhancements');
                                            if (partInfo) {
                                                partInfo.typeId = 247;
                                                partInfo.partType = 'Main Body';
                                                partInfo.path = 'enhancements.Main Body';
                                                
                                                if (partInfo.id && !String(partInfo.id).includes(':')) {
                                                    partInfo.fullId = `247:${partInfo.id}`;
                                                    partInfo.id = `247:${partInfo.id}`;
                                                }
                                                
                                                partsMap.set(partInfo.fullId, partInfo);
                                                partsMap.set(partInfo.id, partInfo);
                                                if (partInfo.spawnCode) {
                                                    partsMap.set(partInfo.spawnCode, partInfo);
                                                }
                                                if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                                    partsMap.set(partInfo.string, partInfo);
                                                }
                                                
                                                if (partInfo.fullId.includes(':')) {
                                                    const afterColon = partInfo.fullId.split(':')[1];
                                                    partsMap.set(afterColon, partInfo);
                                                    const numericPartId = parseInt(afterColon);
                                                    if (!isNaN(numericPartId)) {
                                                        partsMap.set(numericPartId, partInfo);
                                                    }
                                                }
                                                
                                                partsByTypeId.get(247).push(partInfo);
                                                totalPartsExtracted++;
                                                
                                                // Debug log for base body parts (76-80)
                                                const partIdNum = parseInt(partInfo.id.split(':')[1] || partInfo.id);
                                                if (partIdNum >= 76 && partIdNum <= 80) {
                                                    console.log(`    ✓ Extracted Main Body part ${partIdNum}: ${partInfo.name} (fullId: ${partInfo.fullId}, id: ${partInfo.id}, typeId: ${partInfo.typeId})`);
                                                }
                                            }
                                        }
                                    }
                                    console.log(`  ✓ Extracted ${partsByTypeId.get(247).filter(p => p.partType === 'Main Body' && p.path === 'enhancements.Main Body').length} Main Body parts for typeId 247 from top-level Main Body section`);
                                }
                                
                                // Check for sections like "Universal" that have type_id: 247 and contain part_types.Main Body
                                for (const [sectionKey, sectionData] of Object.entries(subsection)) {
                                    // Skip sections we've already processed
                                    if (sectionKey === 'Stats' || sectionKey === 'stats' || 
                                        sectionKey === 'Main Body' || sectionKey === 'main body' || sectionKey === 'MainBody') {
                                        continue;
                                    }
                                    
                                    // Check if this section has type_id: 247
                                    if (sectionData && typeof sectionData === 'object' && sectionData.type_id === 247) {
                                        console.log(`  [DEBUG] Found section "${sectionKey}" with type_id 247 in gadgets.enhancements`);
                                        
                                        // Check if it has part_types.Main Body
                                        if (sectionData.part_types && sectionData.part_types['Main Body']) {
                                            const mainBodyPartType = sectionData.part_types['Main Body'];
                                            if (mainBodyPartType.parts && Array.isArray(mainBodyPartType.parts)) {
                                                console.log(`  [DEBUG] Found Main Body parts in ${sectionKey}.part_types.Main Body (${mainBodyPartType.parts.length} parts)`);
                                                
                                                if (!partsByTypeId.has(247)) {
                                                    partsByTypeId.set(247, []);
                                                }
                                                
                                                // Extract Main Body parts
                                                for (const part of mainBodyPartType.parts) {
                                                    if (!part) continue;
                                                    const partIdStr = part.id ? String(part.id) : '';
                                                    const has247Id = partIdStr.startsWith('247:');
                                                    const isNumericId = /^\d+$/.test(partIdStr);
                                                    
                                                    if (has247Id || isNumericId) {
                                                        let normalizedPart = part;
                                                        if (isNumericId && !has247Id) {
                                                            // Normalize numeric ID to "247:X" format
                                                            normalizedPart = {...part, id: `247:${partIdStr}`};
                                                        }
                                                        
                                                        const partInfo = extractPartInfo(normalizedPart, 247, 'Main Body', 'Enhancement', sectionKey, sectionKey, 'enhancements');
                                                        if (partInfo) {
                                                            partInfo.typeId = 247;
                                                            partInfo.partType = 'Main Body';
                                                            partInfo.path = `enhancements.${sectionKey}.Main Body`;
                                                            
                                                            if (partInfo.id && !String(partInfo.id).includes(':')) {
                                                                partInfo.fullId = `247:${partInfo.id}`;
                                                                partInfo.id = `247:${partInfo.id}`;
                                                            }
                                                            
                                                            partsMap.set(partInfo.fullId, partInfo);
                                                            partsMap.set(partInfo.id, partInfo);
                                                            if (partInfo.spawnCode) {
                                                                partsMap.set(partInfo.spawnCode, partInfo);
                                                            }
                                                            if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                                                partsMap.set(partInfo.string, partInfo);
                                                            }
                                                            
                                                            if (partInfo.fullId.includes(':')) {
                                                                const afterColon = partInfo.fullId.split(':')[1];
                                                                partsMap.set(afterColon, partInfo);
                                                                const numericPartId = parseInt(afterColon);
                                                                if (!isNaN(numericPartId)) {
                                                                    partsMap.set(numericPartId, partInfo);
                                                                }
                                                            }
                                                            
                                                            partsByTypeId.get(247).push(partInfo);
                                                            totalPartsExtracted++;
                                                            
                                                            // Debug log for base body parts (76-80)
                                                            const partIdNum = parseInt(partInfo.id.split(':')[1] || partInfo.id);
                                                            if (partIdNum >= 76 && partIdNum <= 80) {
                                                                console.log(`    ✓ Extracted Main Body part ${partIdNum} from ${sectionKey}: ${partInfo.name} (fullId: ${partInfo.fullId}, id: ${partInfo.id}, typeId: ${partInfo.typeId})`);
                                                            }
                                                        }
                                                    }
                                                }
                                                const mainBodyPath = `enhancements.${sectionKey}.Main Body`;
                                                console.log(`  ✓ Extracted ${partsByTypeId.get(247).filter(p => p.partType === 'Main Body' && p.path === mainBodyPath).length} Main Body parts for typeId 247 from ${sectionKey}.part_types.Main Body`);
                                            }
                                        }
                                        
                                        // Also check for part_types with lowercase/camelCase variations (skip 'Main Body' if already processed above)
                                        if (sectionData.part_types) {
                                            for (const [partTypeKey, partTypeData] of Object.entries(sectionData.part_types)) {
                                                // Extract Firmware parts from part_types.Firmware
                                                if ((partTypeKey === 'Firmware' || partTypeKey === 'firmware') && 
                                                    partTypeData.parts && Array.isArray(partTypeData.parts)) {
                                                    console.log(`  [DEBUG] Found Firmware parts in ${sectionKey}.part_types.${partTypeKey} (${partTypeData.parts.length} parts)`);
                                                    
                                                    if (!partsByTypeId.has(247)) {
                                                        partsByTypeId.set(247, []);
                                                    }
                                                    
                                                    // Extract Firmware parts
                                                    for (const part of partTypeData.parts) {
                                                        if (!part) continue;
                                                        const partIdStr = part.id ? String(part.id) : '';
                                                        const has247Id = partIdStr.startsWith('247:');
                                                        const hasTypeId247 = part.type_id === 247 || (partTypeData && partTypeData.type_id === 247);
                                                        const isNumericId = /^\d+$/.test(partIdStr);
                                                        // Also check spawn_code for skillcraft firmware (case-insensitive)
                                                        const spawnCode = String(part.spawn_code || part.spawnCode || part.string || '').toLowerCase();
                                                        const isSkillcraftFirmware = spawnCode.includes('part_firmware_skillcraft');
                                                        
                                                        if (has247Id || (hasTypeId247 && (isNumericId || !partIdStr.includes(':'))) || (!has247Id && !hasTypeId247 && (isNumericId || isSkillcraftFirmware))) {
                                                            let normalizedPart = part;
                                                            if (isNumericId && !has247Id) {
                                                                normalizedPart = {...part, id: `247:${partIdStr}`};
                                                            } else if (isSkillcraftFirmware && !has247Id && !hasTypeId247) {
                                                                // For skillcraft firmware without standard ID, try to extract numeric ID from spawn_code or use spawn_code as fallback
                                                                const numericMatch = spawnCode.match(/(\d+)/);
                                                                if (numericMatch) {
                                                                    normalizedPart = {...part, id: `247:${numericMatch[1]}`};
                                                                } else {
                                                                    const skillcraftId = spawnCode.replace(/\./g, '_').replace(/[^a-z0-9_]/g, '');
                                                                    normalizedPart = {...part, id: `247:${skillcraftId}`};
                                                                }
                                                            }
                                                            
                                                            const partInfo = extractPartInfo(normalizedPart, 247, 'Firmware', 'Enhancement', sectionKey, sectionKey, 'enhancements');
                                                            if (partInfo) {
                                                                partInfo.typeId = 247;
                                                                partInfo.partType = 'Firmware';
                                                                partInfo.path = `enhancements.${sectionKey}.Firmware`;
                                                                
                                                                if (partInfo.id && !String(partInfo.id).includes(':')) {
                                                                    partInfo.fullId = `247:${partInfo.id}`;
                                                                    partInfo.id = `247:${partInfo.id}`;
                                                                }
                                                                
                                                                partsMap.set(partInfo.fullId, partInfo);
                                                                partsMap.set(partInfo.id, partInfo);
                                                                if (partInfo.spawnCode) {
                                                                    partsMap.set(partInfo.spawnCode, partInfo);
                                                                }
                                                                if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                                                    partsMap.set(partInfo.string, partInfo);
                                                                }
                                                                
                                                                if (partInfo.fullId.includes(':')) {
                                                                    const afterColon = partInfo.fullId.split(':')[1];
                                                                    partsMap.set(afterColon, partInfo);
                                                                    const numericPartId = parseInt(afterColon);
                                                                    if (!isNaN(numericPartId)) {
                                                                        partsMap.set(numericPartId, partInfo);
                                                                    }
                                                                }
                                                                
                                                                partsByTypeId.get(247).push(partInfo);
                                                                totalPartsExtracted++;
                                                            }
                                                        }
                                                    }
                                                    console.log(`  ✓ Extracted ${partsByTypeId.get(247).filter(p => p.partType === 'Firmware' && p.path === `enhancements.${sectionKey}.Firmware`).length} Firmware parts for typeId 247 from ${sectionKey}.part_types.${partTypeKey}`);
                                                    continue;
                                                }
                                                
                                                // Skip 'Main Body' if we already processed it above
                                                if (partTypeKey === 'Main Body') {
                                                    continue;
                                                }
                                                if ((partTypeKey === 'main body' || partTypeKey === 'MainBody') && 
                                                    partTypeData.parts && Array.isArray(partTypeData.parts)) {
                                                    console.log(`  [DEBUG] Found Main Body parts in ${sectionKey}.part_types.${partTypeKey} (${partTypeData.parts.length} parts)`);
                                                    
                                                    if (!partsByTypeId.has(247)) {
                                                        partsByTypeId.set(247, []);
                                                    }
                                                    
                                                    // Extract Main Body parts
                                                    for (const part of partTypeData.parts) {
                                                        if (!part) continue;
                                                        const partIdStr = part.id ? String(part.id) : '';
                                                        const has247Id = partIdStr.startsWith('247:');
                                                        const isNumericId = /^\d+$/.test(partIdStr);
                                                        
                                                        if (has247Id || isNumericId) {
                                                            let normalizedPart = part;
                                                            if (isNumericId && !has247Id) {
                                                                // Normalize numeric ID to "247:X" format
                                                                normalizedPart = {...part, id: `247:${partIdStr}`};
                                                            }
                                                            
                                                            const partInfo = extractPartInfo(normalizedPart, 247, 'Main Body', 'Enhancement', sectionKey, sectionKey, 'enhancements');
                                                            if (partInfo) {
                                                                partInfo.typeId = 247;
                                                                partInfo.partType = 'Main Body';
                                                                partInfo.path = `enhancements.${sectionKey}.${partTypeKey}`;
                                                                
                                                                if (partInfo.id && !String(partInfo.id).includes(':')) {
                                                                    partInfo.fullId = `247:${partInfo.id}`;
                                                                    partInfo.id = `247:${partInfo.id}`;
                                                                }
                                                                
                                                                partsMap.set(partInfo.fullId, partInfo);
                                                                partsMap.set(partInfo.id, partInfo);
                                                                if (partInfo.spawnCode) {
                                                                    partsMap.set(partInfo.spawnCode, partInfo);
                                                                }
                                                                if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                                                    partsMap.set(partInfo.string, partInfo);
                                                                }
                                                                
                                                                if (partInfo.fullId.includes(':')) {
                                                                    const afterColon = partInfo.fullId.split(':')[1];
                                                                    partsMap.set(afterColon, partInfo);
                                                                    const numericPartId = parseInt(afterColon);
                                                                    if (!isNaN(numericPartId)) {
                                                                        partsMap.set(numericPartId, partInfo);
                                                                    }
                                                                }
                                                                
                                                                partsByTypeId.get(247).push(partInfo);
                                                                totalPartsExtracted++;
                                                                
                                                                // Debug log for base body parts (76-80)
                                                                const partIdNum = parseInt(partInfo.id.split(':')[1] || partInfo.id);
                                                                if (partIdNum >= 76 && partIdNum <= 80) {
                                                                    console.log(`    ✓ Extracted Main Body part ${partIdNum} from ${sectionKey}.${partTypeKey}: ${partInfo.name} (fullId: ${partInfo.fullId}, id: ${partInfo.id}, typeId: ${partInfo.typeId})`);
                                                                }
                                                            }
                                                        }
                                                    }
                                                    const partTypePath = `enhancements.${sectionKey}.${partTypeKey}`;
                                                    console.log(`  ✓ Extracted ${partsByTypeId.get(247).filter(p => p.partType === 'Main Body' && p.path === partTypePath).length} Main Body parts for typeId 247 from ${sectionKey}.part_types.${partTypeKey}`);
                                                }
                                            }
                                        }
                                    }
                                }
                                
                                // Check for Firmware section (typeId 247) in enhancements
                                if (subsection.Firmware || subsection.firmware) {
                                    const firmwareData = subsection.Firmware || subsection.firmware;
                                    console.log(`  [DEBUG] Found Firmware section in gadgets.enhancements`);
                                    
                                    if (!partsByTypeId.has(247)) {
                                        partsByTypeId.set(247, []);
                                    }
                                    
                                    // Handle different data structures
                                    let partsToExtract = [];
                                    
                                    if (firmwareData.parts && Array.isArray(firmwareData.parts)) {
                                        partsToExtract = firmwareData.parts;
                                        console.log(`  Extracting ${partsToExtract.length} Firmware parts from gadgets.enhancements.Firmware (Type ID: 247) - direct parts array`);
                                    } else if (firmwareData.part_types) {
                                        for (const [partType, partTypeData] of Object.entries(firmwareData.part_types)) {
                                            if (partTypeData.parts && Array.isArray(partTypeData.parts)) {
                                                partsToExtract.push(...partTypeData.parts);
                                            }
                                        }
                                        console.log(`  Extracting ${partsToExtract.length} Firmware parts from gadgets.enhancements.Firmware (Type ID: 247) - part_types structure`);
                                    } else if (Array.isArray(firmwareData)) {
                                        partsToExtract = firmwareData;
                                        console.log(`  Extracting ${partsToExtract.length} Firmware parts from gadgets.enhancements.Firmware (Type ID: 247) - direct array`);
                                    } else {
                                        const keys = Object.keys(firmwareData || {});
                                        const numericKeys = keys.filter(k => /^\d+$/.test(k));
                                        if (numericKeys.length > 0) {
                                            partsToExtract = numericKeys.map(k => firmwareData[k]).filter(p => p != null);
                                            console.log(`  Extracting ${partsToExtract.length} Firmware parts from gadgets.enhancements.Firmware (Type ID: 247) - array-like object`);
                                        }
                                    }
                                    
                                    // Extract all Firmware parts (including skillcraft)
                                    for (const part of partsToExtract) {
                                        if (!part) continue;
                                        const partIdStr = part.id ? String(part.id) : '';
                                        const has247Id = partIdStr.startsWith('247:');
                                        const hasTypeId247 = part.type_id === 247 || (firmwareData && firmwareData.type_id === 247);
                                        const isNumericId = /^\d+$/.test(partIdStr);
                                        // Also check spawn_code for skillcraft firmware (case-insensitive)
                                        const spawnCode = String(part.spawn_code || part.spawnCode || part.string || '').toLowerCase();
                                        const isSkillcraftFirmware = spawnCode.includes('part_firmware_skillcraft');
                                        
                                        if (has247Id || (hasTypeId247 && (isNumericId || !partIdStr.includes(':'))) || (!has247Id && !hasTypeId247 && (isNumericId || isSkillcraftFirmware))) {
                                            let normalizedPart = part;
                                            if (isNumericId && !has247Id) {
                                                normalizedPart = {...part, id: `247:${partIdStr}`};
                                            } else if (isSkillcraftFirmware && !has247Id && !hasTypeId247) {
                                                // For skillcraft firmware without standard ID, try to extract numeric ID from spawn_code or use spawn_code as fallback
                                                const numericMatch = spawnCode.match(/(\d+)/);
                                                if (numericMatch) {
                                                    normalizedPart = {...part, id: `247:${numericMatch[1]}`};
                                                } else {
                                                    const skillcraftId = spawnCode.replace(/\./g, '_').replace(/[^a-z0-9_]/g, '');
                                                    normalizedPart = {...part, id: `247:${skillcraftId}`};
                                                }
                                            }
                                            
                                            const partInfo = extractPartInfo(normalizedPart, 247, 'Firmware', 'Enhancement', null, null, null);
                                            if (partInfo) {
                                                partInfo.typeId = 247;
                                                partInfo.partType = 'Firmware';
                                                // Ensure fullId is set correctly for Skillcraft (247:248)
                                                if (!partInfo.fullId || !partInfo.fullId.includes(':')) {
                                                    const partId = String(partInfo.id || normalizedPart.id || '');
                                                    if (partId && !partId.includes(':')) {
                                                        partInfo.fullId = `247:${partId}`;
                                                    } else if (partId.includes(':')) {
                                                        partInfo.fullId = partId;
                                                    }
                                                }
                                                partInfo.path = 'gadgets.enhancements.Firmware';
                                                
                                                if (partInfo.id && !String(partInfo.id).includes(':')) {
                                                    partInfo.fullId = `247:${partInfo.id}`;
                                                    partInfo.id = `247:${partInfo.id}`;
                                                }
                                                
                                                partsMap.set(partInfo.fullId, partInfo);
                                                partsMap.set(partInfo.id, partInfo);
                                                if (partInfo.spawnCode) {
                                                    partsMap.set(partInfo.spawnCode, partInfo);
                                                }
                                                if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                                    partsMap.set(partInfo.string, partInfo);
                                                }
                                                
                                                if (partInfo.fullId.includes(':')) {
                                                    const afterColon = partInfo.fullId.split(':')[1];
                                                    partsMap.set(afterColon, partInfo);
                                                    const numericPartId = parseInt(afterColon);
                                                    if (!isNaN(numericPartId)) {
                                                        partsMap.set(numericPartId, partInfo);
                                                    }
                                                }
                                                
                                                partsByTypeId.get(247).push(partInfo);
                                                totalPartsExtracted++;
                                            }
                                        }
                                    }
                                    console.log(`  ✓ Extracted ${partsByTypeId.get(247).filter(p => p.partType === 'Firmware' && p.path === 'gadgets.enhancements.Firmware').length} Firmware parts from gadgets.enhancements for typeId 247`);
                                }
                            }
                            
                            // After processing manufacturers, check for "Perk", "Firmware", "Armor Shield", and "Energy Shield" sections in shields
                            if (subsectionName === 'shields') {
                                // Check for Perk section (typeId 246)
                                if (subsection.Perk || subsection.perk) {
                                    const perkData = subsection.Perk || subsection.perk;
                                    console.log(`  [DEBUG] Found Perk section in gadgets.shields`);
                                    
                                    // Add typeId 246 to typeIdMap if not already present
                                    if (!typeIdMap.has(246)) {
                                        typeIdMap.set(246, {
                                            id: 246,
                                            name: 'Shield Perks',
                                            category: 'Shield',
                                            context: null,
                                            manufacturer: null
                                        });
                                        console.log(`Added type ID 246: Shield Perks`);
                                    }
                                    
                                    if (!partsByTypeId.has(246)) {
                                        partsByTypeId.set(246, []);
                                    }
                                    
                                    // Handle different data structures
                                    let partsToExtract = [];
                                    
                                    if (perkData.parts && Array.isArray(perkData.parts)) {
                                        // Direct parts array
                                        partsToExtract = perkData.parts;
                                        console.log(`  Extracting ${partsToExtract.length} Perk parts from gadgets.shields.Perk (Type ID: 246) - direct parts array`);
                                    } else if (perkData.part_types) {
                                        // part_types structure (like weapons)
                                        console.log(`  [DEBUG] Perk section has part_types structure`);
                                        for (const [partType, partTypeData] of Object.entries(perkData.part_types)) {
                                            if (partTypeData.parts && Array.isArray(partTypeData.parts)) {
                                                partsToExtract.push(...partTypeData.parts);
                                            }
                                        }
                                        console.log(`  Extracting ${partsToExtract.length} Perk parts from gadgets.shields.Perk (Type ID: 246) - part_types structure`);
                                    } else if (Array.isArray(perkData)) {
                                        // Direct array
                                        partsToExtract = perkData;
                                        console.log(`  Extracting ${partsToExtract.length} Perk parts from gadgets.shields.Perk (Type ID: 246) - direct array`);
                                    } else {
                                        // Array-like object with numeric keys
                                        const keys = Object.keys(perkData || {});
                                        const numericKeys = keys.filter(k => /^\d+$/.test(k));
                                        if (numericKeys.length > 0) {
                                            partsToExtract = numericKeys.map(k => perkData[k]).filter(p => p != null);
                                            console.log(`  Extracting ${partsToExtract.length} Perk parts from gadgets.shields.Perk (Type ID: 246) - array-like object`);
                                        } else {
                                            console.log(`  [DEBUG] Perk section has unknown structure. Keys:`, keys);
                                        }
                                    }
                                    
                                    // Extract all Perk parts
                                    for (const part of partsToExtract) {
                                        if (!part) continue;
                                        const partIdStr = part.id ? String(part.id) : '';
                                        const has246Id = partIdStr.startsWith('246:');
                                        const hasTypeId246 = part.type_id === 246 || (perkData && perkData.type_id === 246);
                                        const isNumericId = /^\d+$/.test(partIdStr);
                                        
                                        if (has246Id || (hasTypeId246 && (isNumericId || !partIdStr.includes(':'))) || (!has246Id && !hasTypeId246 && isNumericId)) {
                                            let normalizedPart = part;
                                            if (isNumericId && !has246Id) {
                                                normalizedPart = {...part, id: `246:${partIdStr}`};
                                            }
                                            
                                            const partInfo = extractPartInfo(normalizedPart, 246, 'Perk', 'Shield', null, null, null);
                                            if (partInfo) {
                                                partInfo.typeId = 246;
                                                partInfo.partType = 'Perk';
                                                partInfo.path = 'gadgets.shields.Perk';
                                                
                                                partsMap.set(partInfo.fullId, partInfo);
                                                partsMap.set(partInfo.id, partInfo);
                                                if (partInfo.spawnCode) {
                                                    partsMap.set(partInfo.spawnCode, partInfo);
                                                }
                                                if (partInfo.fullId.includes(':')) {
                                                    const afterColon = partInfo.fullId.split(':')[1];
                                                    partsMap.set(afterColon, partInfo);
                                                    const numericPartId = parseInt(afterColon);
                                                    if (!isNaN(numericPartId)) {
                                                        partsMap.set(numericPartId, partInfo);
                                                    }
                                                }
                                                
                                                partsByTypeId.get(246).push(partInfo);
                                                totalPartsExtracted++;
                                            }
                                        }
                                    }
                                    console.log(`  ✓ Extracted ${partsByTypeId.get(246).filter(p => p.partType === 'Perk' && p.path === 'gadgets.shields.Perk').length} Perk parts from gadgets.shields for typeId 246`);
                                }
                                
                                // Check for Firmware section (typeId 246)
                                if (subsection.Firmware || subsection.firmware) {
                                    const firmwareData = subsection.Firmware || subsection.firmware;
                                    console.log(`  [DEBUG] Found Firmware section in gadgets.shields`);
                                    
                                    // Add typeId 246 to typeIdMap if not already present
                                    if (!typeIdMap.has(246)) {
                                        typeIdMap.set(246, {
                                            id: 246,
                                            name: 'Shield Firmware',
                                            category: 'Shield',
                                            context: null,
                                            manufacturer: null
                                        });
                                        console.log(`Added type ID 246: Shield Firmware`);
                                    }
                                    
                                    if (!partsByTypeId.has(246)) {
                                        partsByTypeId.set(246, []);
                                    }
                                    
                                    // Handle different data structures
                                    let partsToExtract = [];
                                    
                                    if (firmwareData.parts && Array.isArray(firmwareData.parts)) {
                                        partsToExtract = firmwareData.parts;
                                        console.log(`  Extracting ${partsToExtract.length} Firmware parts from gadgets.shields.Firmware (Type ID: 246) - direct parts array`);
                                    } else if (firmwareData.part_types) {
                                        for (const [partType, partTypeData] of Object.entries(firmwareData.part_types)) {
                                            if (partTypeData.parts && Array.isArray(partTypeData.parts)) {
                                                partsToExtract.push(...partTypeData.parts);
                                            }
                                        }
                                        console.log(`  Extracting ${partsToExtract.length} Firmware parts from gadgets.shields.Firmware (Type ID: 246) - part_types structure`);
                                    } else if (Array.isArray(firmwareData)) {
                                        partsToExtract = firmwareData;
                                        console.log(`  Extracting ${partsToExtract.length} Firmware parts from gadgets.shields.Firmware (Type ID: 246) - direct array`);
                                    } else {
                                        const keys = Object.keys(firmwareData || {});
                                        const numericKeys = keys.filter(k => /^\d+$/.test(k));
                                        if (numericKeys.length > 0) {
                                            partsToExtract = numericKeys.map(k => firmwareData[k]).filter(p => p != null);
                                            console.log(`  Extracting ${partsToExtract.length} Firmware parts from gadgets.shields.Firmware (Type ID: 246) - array-like object`);
                                        }
                                    }
                                    
                                    // Extract all Firmware parts (including skillcraft)
                                    for (const part of partsToExtract) {
                                        if (!part) continue;
                                        const partIdStr = part.id ? String(part.id) : '';
                                        const has246Id = partIdStr.startsWith('246:');
                                        const hasTypeId246 = part.type_id === 246 || (firmwareData && firmwareData.type_id === 246);
                                        const isNumericId = /^\d+$/.test(partIdStr);
                                        // Also check spawn_code for skillcraft firmware (case-insensitive)
                                        const spawnCode = String(part.spawn_code || part.spawnCode || part.string || '').toLowerCase();
                                        const isSkillcraftFirmware = spawnCode.includes('part_firmware_skillcraft');
                                        
                                        if (has246Id || (hasTypeId246 && (isNumericId || !partIdStr.includes(':'))) || (!has246Id && !hasTypeId246 && (isNumericId || isSkillcraftFirmware))) {
                                            let normalizedPart = part;
                                            if (isNumericId && !has246Id) {
                                                normalizedPart = {...part, id: `246:${partIdStr}`};
                                            } else if (isSkillcraftFirmware && !has246Id && !hasTypeId246) {
                                                // For skillcraft firmware without standard ID, try to extract numeric ID from spawn_code or use spawn_code as fallback
                                                const numericMatch = spawnCode.match(/(\d+)/);
                                                if (numericMatch) {
                                                    normalizedPart = {...part, id: `246:${numericMatch[1]}`};
                                                } else {
                                                    const skillcraftId = spawnCode.replace(/\./g, '_').replace(/[^a-z0-9_]/g, '');
                                                    normalizedPart = {...part, id: `246:${skillcraftId}`};
                                                }
                                            }
                                            
                                            const partInfo = extractPartInfo(normalizedPart, 246, 'Firmware', 'Shield', null, null, null);
                                            if (partInfo) {
                                                partInfo.typeId = 246;
                                                partInfo.partType = 'Firmware';
                                                partInfo.path = 'gadgets.shields.Firmware';
                                                
                                                partsMap.set(partInfo.fullId, partInfo);
                                                partsMap.set(partInfo.id, partInfo);
                                                if (partInfo.spawnCode) {
                                                    partsMap.set(partInfo.spawnCode, partInfo);
                                                }
                                                if (partInfo.fullId.includes(':')) {
                                                    const afterColon = partInfo.fullId.split(':')[1];
                                                    partsMap.set(afterColon, partInfo);
                                                    const numericPartId = parseInt(afterColon);
                                                    if (!isNaN(numericPartId)) {
                                                        partsMap.set(numericPartId, partInfo);
                                                    }
                                                }
                                                
                                                partsByTypeId.get(246).push(partInfo);
                                                totalPartsExtracted++;
                                            }
                                        }
                                    }
                                    console.log(`  ✓ Extracted ${partsByTypeId.get(246).filter(p => p.partType === 'Firmware' && p.path === 'gadgets.shields.Firmware').length} Firmware parts from gadgets.shields for typeId 246`);
                                }
                                
                                // Check for Resistance section (typeId 246)
                                if (subsection.Resistance || subsection.resistance) {
                                    const resistanceData = subsection.Resistance || subsection.resistance;
                                    console.log(`  [DEBUG] Found Resistance section in gadgets.shields`);
                                    
                                    if (Array.isArray(resistanceData)) {
                                        resistanceData.forEach(part => {
                                            const partInfo = extractPartInfo(part, 246, 'Resistance', 'Shield', null, null, null);
                                            if (partInfo) {
                                                partInfo.typeId = 246;
                                                partInfo.partType = 'Resistance';
                                                partInfo.path = 'gadgets.shields.Resistance';
                                                
                                                // Ensure fullId is in format "246:X"
                                                if (partInfo.id && partInfo.id.includes(':')) {
                                                    partInfo.fullId = partInfo.id;
                                                } else if (partInfo.id) {
                                                    partInfo.fullId = `246:${partInfo.id}`;
                                                }
                                                
                                                // Store with multiple key formats
                                                partsMap.set(partInfo.fullId, partInfo);
                                                partsMap.set(partInfo.id, partInfo);
                                                if (partInfo.spawnCode) {
                                                    partsMap.set(partInfo.spawnCode, partInfo);
                                                }
                                                if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                                    partsMap.set(partInfo.string, partInfo);
                                                }
                                                
                                                // Also store by the numeric part ID after colon
                                                if (partInfo.fullId.includes(':')) {
                                                    const afterColon = partInfo.fullId.split(':')[1];
                                                    partsMap.set(afterColon, partInfo);
                                                    const numericPartId = parseInt(afterColon);
                                                    if (!isNaN(numericPartId)) {
                                                        partsMap.set(numericPartId, partInfo);
                                                    }
                                                }
                                                
                                                partsByTypeId.get(246).push(partInfo);
                                                totalPartsExtracted++;
                                            }
                                        });
                                    }
                                    console.log(`  ✓ Extracted ${partsByTypeId.get(246).filter(p => p.partType === 'Resistance' && p.path === 'gadgets.shields.Resistance').length} Resistance parts from gadgets.shields for typeId 246`);
                                }
                                
                                // Check for Armor Shield section (typeId 237)
                                if (subsection['Armor Shield'] || subsection['armor shield'] || subsection.armorShield) {
                                    const armorData = subsection['Armor Shield'] || subsection['armor shield'] || subsection.armorShield;
                                    console.log(`  [DEBUG] Found Armor Shield section in gadgets.shields`);
                                    
                                    // Add typeId 237 to typeIdMap if not already present
                                    if (!typeIdMap.has(237)) {
                                        typeIdMap.set(237, {
                                            id: 237,
                                            name: 'Armor Shield',
                                            category: 'Shield',
                                            context: null,
                                            manufacturer: null
                                        });
                                        console.log(`Added type ID 237: Armor Shield`);
                                    }
                                    
                                    if (!partsByTypeId.has(237)) {
                                        partsByTypeId.set(237, []);
                                    }
                                    
                                    // Handle different data structures
                                    let partsToExtract = [];
                                    
                                    if (armorData.parts && Array.isArray(armorData.parts)) {
                                        partsToExtract = armorData.parts;
                                        console.log(`  Extracting ${partsToExtract.length} Armor Shield parts from gadgets.shields.Armor Shield (Type ID: 237) - direct parts array`);
                                    } else if (armorData.part_types) {
                                        for (const [partType, partTypeData] of Object.entries(armorData.part_types)) {
                                            if (partTypeData.parts && Array.isArray(partTypeData.parts)) {
                                                partsToExtract.push(...partTypeData.parts);
                                            }
                                        }
                                        console.log(`  Extracting ${partsToExtract.length} Armor Shield parts from gadgets.shields.Armor Shield (Type ID: 237) - part_types structure`);
                                    } else if (Array.isArray(armorData)) {
                                        partsToExtract = armorData;
                                        console.log(`  Extracting ${partsToExtract.length} Armor Shield parts from gadgets.shields.Armor Shield (Type ID: 237) - direct array`);
                                    } else {
                                        const keys = Object.keys(armorData || {});
                                        const numericKeys = keys.filter(k => /^\d+$/.test(k));
                                        if (numericKeys.length > 0) {
                                            partsToExtract = numericKeys.map(k => armorData[k]).filter(p => p != null);
                                            console.log(`  Extracting ${partsToExtract.length} Armor Shield parts from gadgets.shields.Armor Shield (Type ID: 237) - array-like object`);
                                        }
                                    }
                                    
                                    // Extract all Armor Shield parts
                                    for (const part of partsToExtract) {
                                        if (!part) continue;
                                        const partIdStr = part.id ? String(part.id) : '';
                                        const has237Id = partIdStr.startsWith('237:');
                                        const hasTypeId237 = part.type_id === 237 || (armorData && armorData.type_id === 237);
                                        const isNumericId = /^\d+$/.test(partIdStr);
                                        
                                        if (has237Id || (hasTypeId237 && (isNumericId || !partIdStr.includes(':'))) || (!has237Id && !hasTypeId237 && isNumericId)) {
                                            let normalizedPart = part;
                                            if (isNumericId && !has237Id) {
                                                normalizedPart = {...part, id: `237:${partIdStr}`};
                                            }
                                            
                                            const partInfo = extractPartInfo(normalizedPart, 237, 'Armor Shield', 'Shield', null, null, null);
                                            if (partInfo) {
                                                partInfo.typeId = 237;
                                                partInfo.partType = 'Armor Shield';
                                                partInfo.path = 'gadgets.shields.Armor Shield';
                                                
                                                partsMap.set(partInfo.fullId, partInfo);
                                                partsMap.set(partInfo.id, partInfo);
                                                if (partInfo.spawnCode) {
                                                    partsMap.set(partInfo.spawnCode, partInfo);
                                                }
                                                if (partInfo.fullId.includes(':')) {
                                                    const afterColon = partInfo.fullId.split(':')[1];
                                                    partsMap.set(afterColon, partInfo);
                                                    const numericPartId = parseInt(afterColon);
                                                    if (!isNaN(numericPartId)) {
                                                        partsMap.set(numericPartId, partInfo);
                                                    }
                                                }
                                                
                                                partsByTypeId.get(237).push(partInfo);
                                                totalPartsExtracted++;
                                            }
                                        }
                                    }
                                    console.log(`  ✓ Extracted ${partsByTypeId.get(237).length} Armor Shield parts from gadgets.shields for typeId 237`);
                                }
                                
                                // Check for Energy Shield section (typeId 248)
                                if (subsection['Energy Shield'] || subsection['energy shield'] || subsection.energyShield) {
                                    const energyData = subsection['Energy Shield'] || subsection['energy shield'] || subsection.energyShield;
                                    console.log(`  [DEBUG] Found Energy Shield section in gadgets.shields`);
                                    
                                    // Add typeId 248 to typeIdMap if not already present
                                    if (!typeIdMap.has(248)) {
                                        typeIdMap.set(248, {
                                            id: 248,
                                            name: 'Energy Shield',
                                            category: 'Shield',
                                            context: null,
                                            manufacturer: null
                                        });
                                        console.log(`Added type ID 248: Energy Shield`);
                                    }
                                    
                                    if (!partsByTypeId.has(248)) {
                                        partsByTypeId.set(248, []);
                                    }
                                    
                                    // Handle different data structures
                                    let partsToExtract = [];
                                    
                                    if (energyData.parts && Array.isArray(energyData.parts)) {
                                        partsToExtract = energyData.parts;
                                        console.log(`  Extracting ${partsToExtract.length} Energy Shield parts from gadgets.shields.Energy Shield (Type ID: 248) - direct parts array`);
                                    } else if (energyData.part_types) {
                                        for (const [partType, partTypeData] of Object.entries(energyData.part_types)) {
                                            if (partTypeData.parts && Array.isArray(partTypeData.parts)) {
                                                partsToExtract.push(...partTypeData.parts);
                                            }
                                        }
                                        console.log(`  Extracting ${partsToExtract.length} Energy Shield parts from gadgets.shields.Energy Shield (Type ID: 248) - part_types structure`);
                                    } else if (Array.isArray(energyData)) {
                                        partsToExtract = energyData;
                                        console.log(`  Extracting ${partsToExtract.length} Energy Shield parts from gadgets.shields.Energy Shield (Type ID: 248) - direct array`);
                                    } else {
                                        const keys = Object.keys(energyData || {});
                                        const numericKeys = keys.filter(k => /^\d+$/.test(k));
                                        if (numericKeys.length > 0) {
                                            partsToExtract = numericKeys.map(k => energyData[k]).filter(p => p != null);
                                            console.log(`  Extracting ${partsToExtract.length} Energy Shield parts from gadgets.shields.Energy Shield (Type ID: 248) - array-like object`);
                                        }
                                    }
                                    
                                    // Extract all Energy Shield parts
                                    for (const part of partsToExtract) {
                                        if (!part) continue;
                                        const partIdStr = part.id ? String(part.id) : '';
                                        const has248Id = partIdStr.startsWith('248:');
                                        const hasTypeId248 = part.type_id === 248 || (energyData && energyData.type_id === 248);
                                        const isNumericId = /^\d+$/.test(partIdStr);
                                        
                                        if (has248Id || (hasTypeId248 && (isNumericId || !partIdStr.includes(':'))) || (!has248Id && !hasTypeId248 && isNumericId)) {
                                            let normalizedPart = part;
                                            if (isNumericId && !has248Id) {
                                                normalizedPart = {...part, id: `248:${partIdStr}`};
                                            }
                                            
                                            const partInfo = extractPartInfo(normalizedPart, 248, 'Energy Shield', 'Shield', null, null, null);
                                            if (partInfo) {
                                                partInfo.typeId = 248;
                                                partInfo.partType = 'Energy Shield';
                                                partInfo.path = 'gadgets.shields.Energy Shield';
                                                
                                                partsMap.set(partInfo.fullId, partInfo);
                                                partsMap.set(partInfo.id, partInfo);
                                                if (partInfo.spawnCode) {
                                                    partsMap.set(partInfo.spawnCode, partInfo);
                                                }
                                                if (partInfo.fullId.includes(':')) {
                                                    const afterColon = partInfo.fullId.split(':')[1];
                                                    partsMap.set(afterColon, partInfo);
                                                    const numericPartId = parseInt(afterColon);
                                                    if (!isNaN(numericPartId)) {
                                                        partsMap.set(numericPartId, partInfo);
                                                    }
                                                }
                                                
                                                partsByTypeId.get(248).push(partInfo);
                                                totalPartsExtracted++;
                                            }
                                        }
                                    }
                                    console.log(`  ✓ Extracted ${partsByTypeId.get(248).length} Energy Shield parts from gadgets.shields for typeId 248`);
                                }
                            }
                        } else {
                            // Direct structure (like enhancements without manufacturers wrapper)
                            for (const [manufacturer, data] of Object.entries(subsection)) {
                                if (data && typeof data === 'object' && data.type_id) {
                                    const typeId = data.type_id;
                                    if (!typeIdMap.has(typeId)) {
                                        const categoryName = subsectionName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                                        typeIdMap.set(typeId, {
                                            id: typeId,
                                            name: subsectionName.slice(0, -1), // Remove 's' if plural
                                            category: categoryName,
                                            manufacturer: manufacturer
                                        });
                                        console.log(`Added type ID ${typeId}: ${manufacturer} ${subsectionName}`);
                                    }
                                    
                                    if (!partsByTypeId.has(typeId)) {
                                        partsByTypeId.set(typeId, []);
                                    }
                                    
                                    // Extract parts from part_types
                                    if (data.part_types) {
                                        for (const [partType, partTypeData] of Object.entries(data.part_types)) {
                                            if (partTypeData.parts && Array.isArray(partTypeData.parts)) {
                                                for (const part of partTypeData.parts) {
                                                    const partInfo = extractPartInfo(
                                                        part, typeId, partType, subsectionName, manufacturer, manufacturer, subsectionName
                                                    );
                                                    if (partInfo) {
                                                        partsMap.set(partInfo.fullId, partInfo);
                                                        partsMap.set(partInfo.id, partInfo);
                                                        if (partInfo.fullId.includes(':')) {
                                                            partsMap.set(partInfo.fullId, partInfo);
                                                        }
                                                        // Store by spawn_code for string lookup
                                                        if (partInfo.spawnCode) {
                                                            partsMap.set(partInfo.spawnCode, partInfo);
                                                        }
                                                        if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                                            partsMap.set(partInfo.string, partInfo);
                                                        }
                                                        partsByTypeId.get(typeId).push(partInfo);
                                                        totalPartsExtracted++;
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            function extractFromPartTypes(partTypes, category, context) {
                // Use iterative approach with stack to avoid recursion depth issues
                const stack = [{ obj: partTypes, path: '', parentTypeId: null, depth: 0, parentKey: '' }];
                const visited = new WeakSet();
                const maxIterations = 50000; // Increased limit
                let iterations = 0;

                while (stack.length > 0 && iterations < maxIterations) {
                    iterations++;
                    const { obj, path, parentTypeId, depth, parentKey } = stack.pop();
                    
                    if (visited.has(obj)) continue;
                    visited.add(obj);

                    if (!obj || typeof obj !== 'object' || depth > 20) continue;

                    let currentTypeId = parentTypeId;
                    let currentParentKey = parentKey;

                    // First pass: find type_id in current object
                    for (const [key, value] of Object.entries(obj)) {
                        if (key === 'type_id' && typeof value === 'number') {
                            currentTypeId = value;
                            
                            // Build a better name from context and parent key
                            let typeName = '';
                            
                            // For class mods, use just character name + "Class Mod" (same type_id used for all parts)
                            if (category === 'Class Mod' && context) {
                                typeName = `${context} Class Mod`;
                            } else {
                                // For other categories, use path or category
                                const pathParts = path.split(' > ');
                                typeName = pathParts[pathParts.length - 1] || path || category;
                            }
                            
                            // Only set if not already exists, or update if we have better context
                            if (!typeIdMap.has(currentTypeId)) {
                                typeIdMap.set(currentTypeId, {
                                    id: currentTypeId,
                                    name: typeName,
                                    category: category,
                                    context: context,
                                    fullPath: path
                                });
                            } else {
                                // Update if we have a better name (with character context)
                                const existing = typeIdMap.get(currentTypeId);
                                if (category === 'Class Mod' && context) {
                                    // Always update class mod names to use simple format
                                    if (!existing.context || existing.context !== context) {
                                        existing.name = typeName;
                                        existing.context = context;
                                    }
                                    // If same type_id for different characters (shouldn't happen, but handle it)
                                    if (existing.context && existing.context !== context) {
                                        existing.name = `${existing.name} / ${typeName}`;
                                    }
                                }
                            }
                            
                            if (!partsByTypeId.has(currentTypeId)) {
                                partsByTypeId.set(currentTypeId, []);
                            }
                            break;
                        }
                    }

                    // Second pass: process parts and add children to stack
                    for (const [key, value] of Object.entries(obj)) {
                        if (key === 'parts' && Array.isArray(value)) {
                            // Check if this is a Rarity section with its own type_id (for class mods)
                            let partsTypeId = currentTypeId;
                            if (key === 'parts' && obj.type_id && typeof obj.type_id === 'number') {
                                // This parts array belongs to an object with its own type_id (like Rarity with type_id: 247)
                                partsTypeId = obj.type_id;
                                // Debug log for class mod rarity sections
                                if (category === 'Class Mod' && partsTypeId === 247) {
                                    console.log(`  Found Rarity section with type_id ${partsTypeId} at path: ${path}, processing ${value.length} parts`);
                                }
                            }
                            
                            for (const part of value) {
                                const partInfo = extractPartInfo(
                                    part, partsTypeId, path, category, context, null, null
                                );
                                
                                if (partInfo) {
                                    // Store with multiple key formats for lookup
                                    partsMap.set(partInfo.fullId, partInfo);
                                    partsMap.set(partInfo.id, partInfo);
                                    
                                    // Store by spawn_code for string lookup
                                    if (partInfo.spawnCode) {
                                        partsMap.set(partInfo.spawnCode, partInfo);
                                    }
                                    if (partInfo.string && partInfo.string !== partInfo.spawnCode) {
                                        partsMap.set(partInfo.string, partInfo);
                                    }
                                    
                                    // If fullId is different from id, store both
                                    if (partInfo.fullId !== partInfo.id) {
                                        partsMap.set(partInfo.fullId, partInfo);
                                    }
                                    
                                    // Check if part ID contains a type_id (like "234:1" for Perk parts)
                                    if (partInfo.fullId && partInfo.fullId.includes(':')) {
                                        const partTypeId = parseInt(partInfo.fullId.split(':')[0]);
                                        if (!isNaN(partTypeId) && partTypeId !== partsTypeId) {
                                            // This is a part with its own type_id (like Perk 234)
                                            if (!typeIdMap.has(partTypeId)) {
                                                // Determine name based on context
                                                let typeName = '';
                                                if (category === 'Class Mod' && context) {
                                                    // For class mod perks, use character name + part type
                                                    const partTypeName = path.split(' > ').pop() || 'Perk';
                                                    typeName = `${context} ${partTypeName}`;
                                                } else {
                                                    typeName = path.split(' > ').pop() || 'Part';
                                                }
                                                typeIdMap.set(partTypeId, {
                                                    id: partTypeId,
                                                    name: typeName,
                                                    category: category,
                                                    context: context,
                                                    manufacturer: null
                                                });
                                                if (!partsByTypeId.has(partTypeId)) {
                                                    partsByTypeId.set(partTypeId, []);
                                                }
                                            }
                                            // Add part to the part's type_id collection
                                            if (!partsByTypeId.has(partTypeId)) {
                                                partsByTypeId.set(partTypeId, []);
                                            }
                                            partsByTypeId.get(partTypeId).push(partInfo);
                                        }
                                    }
                                    
                                    // Use partsTypeId (which may be from the parent object's type_id)
                                    const targetTypeId = partInfo.fullId && partInfo.fullId.includes(':') ? 
                                        (parseInt(partInfo.fullId.split(':')[0]) || partsTypeId) : partsTypeId;
                                    
                                    if (targetTypeId) {
                                        if (!partsByTypeId.has(targetTypeId)) {
                                            partsByTypeId.set(targetTypeId, []);
                                        }
                                        partsByTypeId.get(targetTypeId).push(partInfo);
                                        totalPartsExtracted++;
                                        
                                        // Debug log for comp parts (class mod rarity comps)
                                        // Check for both .comp_ (with dot) and comp_ (without dot) patterns
                                        const hasCompPattern = (partInfo.spawnCode && (String(partInfo.spawnCode).includes('.comp_') || String(partInfo.spawnCode).includes('comp_'))) || 
                                            (partInfo.string && (String(partInfo.string).includes('.comp_') || String(partInfo.string).includes('comp_01_common') || String(partInfo.string).includes('comp_02_uncommon') || String(partInfo.string).includes('comp_03_rare') || String(partInfo.string).includes('comp_04_epic') || String(partInfo.string).includes('comp_05_legendary')));
                                        if (hasCompPattern) {
                                            console.log(`    ✓ Extracted comp part from ${category}: ${partInfo.name || partInfo.string || partInfo.id} (fullId: ${partInfo.fullId}, id: ${partInfo.id}, typeId: ${targetTypeId}, spawnCode: ${partInfo.spawnCode}, string: ${partInfo.string}, path: ${path})`);
                                        }
                                    }
                                }
                            }
                        } else if (key !== 'type_id' && 
                                   key !== 'count' && 
                                   typeof value === 'object' && 
                                   value !== null && 
                                   !Array.isArray(value)) {
                            const newPath = path ? `${path} > ${key}` : key;
                            // Use the current key as parentKey for child objects
                            const newParentKey = (key !== 'part_types' && key !== 'Rarities') ? key : currentParentKey;
                            stack.push({ 
                                obj: value, 
                                path: newPath, 
                                parentTypeId: currentTypeId,
                                depth: depth + 1,
                                parentKey: newParentKey
                            });
                        }
                    }
                }
                
                if (iterations >= maxIterations) {
                    console.warn('Reached maximum iterations limit in extractFromPartTypes');
                }
            }
            
            console.log(`Extracted ${totalPartsExtracted} parts total`);
            console.log(`Found ${typeIdMap.size} type IDs`);
            console.log(`Parts map contains ${partsMap.size} entries`);

            // Add Daedalus ammo parts (typeId 23) - these are used with Daedalus Ammo Switch underbarrel
            if (!partsByTypeId.has(23)) {
                partsByTypeId.set(23, []);
            }
            if (!typeIdMap.has(23)) {
                typeIdMap.set(23, {
                    id: 23,
                    name: 'Daedalus Ammo',
                    category: 'Weapon',
                    context: null,
                    manufacturer: 'Daedalus'
                });
            }
            
            const daedalusAmmoParts = [
                { id: '23:62', name: 'Daedalus SMG Ammo', spawn_code: 'BOR_SR.part_secondary_ammo_smg', stats: 'Daedalus SMG Ammo' },
                { id: '23:63', name: 'Daedalus Shotgun Ammo', spawn_code: 'BOR_SR.part_secondary_ammo_sg', stats: 'Daedalus Shotgun Ammo' },
                { id: '23:64', name: 'Daedalus AR Ammo', spawn_code: 'BOR_SR.part_secondary_ammo_ar', stats: 'Daedalus AR Ammo' },
                { id: '23:65', name: 'Daedalus Pistol Ammo', spawn_code: 'BOR_SR.part_secondary_ammo_ps', stats: 'Daedalus Pistol Ammo' }
            ];
            
            for (const part of daedalusAmmoParts) {
                const partInfo = extractPartInfo(part, 23, 'Daedalus Ammo', 'Weapon', 'Daedalus', 'Daedalus', 'weapon');
                if (partInfo) {
                    partInfo.typeId = 23;
                    partInfo.partType = 'Daedalus Ammo';
                    partInfo.path = 'weapon.daedalus_ammo';
                    
                    partsMap.set(partInfo.fullId, partInfo);
                    partsMap.set(partInfo.id, partInfo);
                    if (partInfo.spawnCode) {
                        partsMap.set(partInfo.spawnCode, partInfo);
                    }
                    if (partInfo.fullId.includes(':')) {
                        const afterColon = partInfo.fullId.split(':')[1];
                        partsMap.set(afterColon, partInfo);
                        const numericPartId = parseInt(afterColon);
                        if (!isNaN(numericPartId)) {
                            partsMap.set(numericPartId, partInfo);
                        }
                    }
                    
                    partsByTypeId.get(23).push(partInfo);
                    totalPartsExtracted++;
                }
            }
            console.log(`  ✓ Added ${daedalusAmmoParts.length} Daedalus ammo parts (typeId 23)`);

            // Type IDs that have "NEW!" parts (derived from new serial IDs) - for manufacturer/type dropdown badges
            const typeIdsWithNewParts = new Set([1, 3, 4, 6, 7, 9, 11, 12, 13, 14, 17, 18, 21, 22, 23, 25, 287, 298]);
                const msbtSupplementCount = mergeMsbtPartSupplements();
                if (msbtSupplementCount > 0) {
                    console.log(`MSBT: MSBT part supplements loaded (${msbtSupplementCount} parts)`);
                }
            
            // Populate manufacturer dropdown (full Item Editor form only — save-editor / minimal layouts omit these nodes)
            const manufacturerSelect = document.getElementById('manufacturer');
            const typeIdSelect = document.getElementById('typeId');
            const manufacturers = new Set();
            const typeIdsByManufacturer = new Map();
            
            // Collect all manufacturers and group type IDs by manufacturer
            // Exclude substat categories (1, 234, 237, 246, 247, 248 and Universal items) from base item selection
            // TypeID 1 is for weapon elements (parts only), not a base item type
            // TypeIDs 237 (Armor Shield), 246 (Shield Perks), 248 (Energy Shield) are parts only, not base items
            Array.from(typeIdMap.values())
                .filter(type => {
                    // Exclude substat categories: 1 (Weapon Elements - parts only), 234 (Perk), 237 (Armor Shield), 246 (Shield Perks), 247 (Rarity/Enhancement), 248 (Energy Shield)
                    if (type.id === 1 || type.id === 234 || type.id === 237 || type.id === 246 || type.id === 247 || type.id === 248) return false;
                    if (type.manufacturer === 'Universal') return false;
                    return true;
                })
                .forEach(type => {
                    // Group class mod characters (Rafa, Amon, Harlowe, Vex) under "Class Mods"
                    let manufacturer = type.manufacturer || 'Class Mods';
                    const category = (type.category || '').toLowerCase();
                    const manufacturerLower = (manufacturer || '').toLowerCase();
                    
                    // Check if this is a class mod character
                    if (category.includes('class mod') || 
                        manufacturerLower === 'rafa' || 
                        manufacturerLower === 'amon' || 
                        manufacturerLower === 'harlowe' || 
                        manufacturerLower === 'vex' || 
                        manufacturerLower === 'siren') {
                        manufacturer = 'Class Mods';
                    }
                    
                    manufacturers.add(manufacturer);
                    if (!typeIdsByManufacturer.has(manufacturer)) {
                        typeIdsByManufacturer.set(manufacturer, []);
                    }
                    typeIdsByManufacturer.get(manufacturer).push(type);
                });
            
            // Clear and populate manufacturer dropdown
            if (manufacturerSelect) {
                manufacturerSelect.innerHTML = '<option value="">Select Manufacturer...</option>';
                const sortedManufacturers = Array.from(manufacturers).sort();
                sortedManufacturers.forEach(manufacturer => {
                    const option = document.createElement('option');
                    option.value = manufacturer;
                    const typesForManufacturer = typeIdsByManufacturer.get(manufacturer) || [];
                    const hasNewParts = typesForManufacturer.some(t => typeIdsWithNewParts.has(t.id));
                    option.textContent = hasNewParts ? manufacturer + '  NEW!' : manufacturer;
                    manufacturerSelect.appendChild(option);
                });
            }
            
            // Store typeIdsByManufacturer for filtering
            window.typeIdsByManufacturer = typeIdsByManufacturer;
            
            // Function to update Type ID dropdown based on selected manufacturer
            // Make it global so it can be called from parseItemCode
            window.updateTypeIdDropdown = function() {
                const ms = document.getElementById('manufacturer');
                const ts = document.getElementById('typeId');
                if (!ms || !ts) return;
                const selectedManufacturer = ms.value;
                
                ts.innerHTML = '<option value="">Select Type ID...</option>';
                
                if (!selectedManufacturer) {
                    ts.disabled = true;
                    ts.innerHTML = '<option value="">Select Manufacturer first...</option>';
                    return;
                }
                
                ts.disabled = false;
                
                // Get type IDs for selected manufacturer
                const typeIds = window.typeIdsByManufacturer.get(selectedManufacturer) || [];
                // Filter out Type ID 6 for Enhancements manufacturer (case-insensitive check)
                // Also filter out parts-only typeIds: 1, 237, 246, 248 (these are parts only, not base items)
                const filteredTypeIds = typeIds.filter(type => {
                    // Exclude parts-only typeIds
                    if (type.id === 1 || type.id === 237 || type.id === 246 || type.id === 248) return false;
                    // Filter out Type ID 6 for Enhancements manufacturer
                    if (selectedManufacturer && selectedManufacturer.toLowerCase().includes('enhancement') && type.id === 6) return false;
                    return true;
                });
                const sortedTypeIds = filteredTypeIds
                    .sort((a, b) => a.id - b.id);
                
                sortedTypeIds.forEach(type => {
                    const option = document.createElement('option');
                    option.value = type.id;
                    // Replace "grenade" with "Ordnance" in the display name
                    const displayName = type.name && type.name.toLowerCase() === 'grenade' ? 'Ordnance' : type.name;
                    const hasNewParts = typeIdsWithNewParts.has(type.id);
                    const label = hasNewParts ? `${type.id} - ${displayName}  NEW!` : `${type.id} - ${displayName}`;
                    option.textContent = label;
                    ts.appendChild(option);
                });
            };
            
            // Populate type ID dropdown (will be filtered by manufacturer selection)
            if (manufacturerSelect && typeIdSelect) {
                window.updateTypeIdDropdown();
            }
            
            // Only add event listeners if not already set up (check data attribute)
            if (manufacturerSelect && !manufacturerSelect.dataset.listenersSetup) {
                // Add event listener for manufacturer selection
                manufacturerSelect.addEventListener('change', function() {
                    const newManufacturer = this.value;
                    const oldManufacturer = this.dataset.previousValue || '';
                    
                    // Check if we should warn (code was parsed and there are simple parts)
                    if (parsedTypeId !== null && currentParts.length > 0) {
                        const hasSimpleParts = currentParts.some(p => p.type === 'simple');
                        if (hasSimpleParts && newManufacturer !== oldManufacturer) {
                            const confirmed = confirm('⚠️ Warning: Changing the manufacturer will change what each simple part code refers to.\n\nSimple part IDs are context-dependent based on the Type ID. Changing the manufacturer will require selecting a new Type ID, which may change the meaning of your simple part codes.\n\nDo you want to continue?');
                            if (!confirmed) {
                                // Revert to previous value
                                this.value = oldManufacturer;
                                return;
                            }
                            // Show persistent warning
                            showTypeIdChangeWarning('manufacturer');
                        }
                    }
                    
                    // Store the new value for next change
                    this.dataset.previousValue = newManufacturer;
                    
                    window.updateTypeIdDropdown();
                    // Clear type ID selection when manufacturer changes
                    const ts = document.getElementById('typeId');
                    if (ts) ts.value = '';
                    const typeIdInfoEl = document.getElementById('typeIdInfo');
                    if (typeIdInfoEl) typeIdInfoEl.textContent = '';
                    // Clear parsed Type ID when manufacturer changes (Type ID will need to be reselected)
                    parsedTypeId = null;
                    // Re-render parts with new manufacturer context (don't clear, just update display)
                    renderParts();
                    if (typeof updateGuidelinesChecklist === 'function') updateGuidelinesChecklist();
                    generateCode();
                });
                manufacturerSelect.dataset.listenersSetup = 'true';
            }

            // Populate part builder TypeID dropdown (include ALL type IDs, including substat categories)
            // Substat categories are available for adding parts, just not as base items
            const builderTypeIdSelect = document.getElementById('newPartTypeId');
            if (builderTypeIdSelect) {
                const allSortedTypeIds = Array.from(typeIdMap.values())
                    .sort((a, b) => a.id - b.id);
                builderTypeIdSelect.innerHTML = '<option value="0">All Parts</option>';
                allSortedTypeIds.forEach(type => {
                    const option = document.createElement('option');
                    option.value = type.id;
                    let label = '';
                    // Special naming for substat categories and special type IDs
                    if (type.id === 1) {
                        label = `${type.id} - Weapon Elements`;
                    } else if (type.id === 234) {
                        label = `${type.id} - Class Mod Substats`;
                    } else if (type.id === 237) {
                        label = `${type.id} - Shield Armor (Shield Part)`;
                    } else if (type.id === 243 && (type.manufacturer === 'Universal' || type.name === 'Firmware')) {
                        label = `${type.id} - Repkit Substats`;
                    } else if (type.id === 244) {
                        // Always show 244 as Heavy Weapon Substats regardless of manufacturer
                        label = `${type.id} - Heavy Weapon Substats`;
                    } else if (type.id === 245 && (type.manufacturer === 'Universal' || type.name === 'Firmware')) {
                        label = `${type.id} - Grenade Substats`;
                    } else if (type.id === 246) {
                        label = `${type.id} - Shield Perks/Firmware (Shield Part)`;
                    } else if (type.id === 248) {
                        label = `${type.id} - Shield Energy (Shield Part)`;
                    } else if (type.id === 247) {
                        label = `${type.id} - Enhancement Substats`;
                    } else {
                        label = type.manufacturer ? 
                            `${type.id} - ${type.manufacturer} ${type.name}` : 
                            `${type.id} - ${type.name}`;
                    }
                    option.textContent = label;
                    builderTypeIdSelect.appendChild(option);
                });
                
                // Debug: Log if typeID 244 is in the dropdown
                const type244Option = builderTypeIdSelect.querySelector('option[value="244"]');
                if (type244Option) {
                    console.log('✓ TypeID 244 added to part builder dropdown:', type244Option.textContent);
                } else {
                    console.warn('⚠️ TypeID 244 NOT found in part builder dropdown. typeIdMap has:', Array.from(typeIdMap.keys()).sort((a, b) => a - b));
                    // If 244 is missing, add it manually
                    if (!typeIdMap.has(244)) {
                        typeIdMap.set(244, {
                            id: 244,
                            name: 'Firmware',
                            category: 'Heavy Weapons',
                            manufacturer: 'Universal'
                        });
                        console.log('✓ Added typeID 244 to typeIdMap manually');
                        // Re-populate dropdown
                        const allSortedTypeIds2 = Array.from(typeIdMap.values()).sort((a, b) => a.id - b.id);
                        builderTypeIdSelect.innerHTML = '<option value="0">All Parts</option>';
                        allSortedTypeIds2.forEach(type => {
                            const option = document.createElement('option');
                            option.value = type.id;
                            let label = '';
                            if (type.id === 1) {
                                label = `${type.id} - Weapon Elements`;
                            } else if (type.id === 234) {
                                label = `${type.id} - Class Mod Substats`;
                            } else if (type.id === 237) {
                                label = `${type.id} - Shield Armor (Shield Part)`;
                            } else if (type.id === 243 && (type.manufacturer === 'Universal' || type.name === 'Firmware')) {
                                label = `${type.id} - Repkit Substats`;
                            } else if (type.id === 244) {
                                label = `${type.id} - Heavy Weapon Substats`;
                            } else if (type.id === 245 && (type.manufacturer === 'Universal' || type.name === 'Firmware')) {
                                label = `${type.id} - Grenade Substats`;
                            } else if (type.id === 246) {
                                label = `${type.id} - Shield Perks/Firmware (Shield Part)`;
                            } else if (type.id === 248) {
                                label = `${type.id} - Shield Energy (Shield Part)`;
                            } else if (type.id === 247) {
                                label = `${type.id} - Enhancement Substats`;
                            } else {
                                label = type.manufacturer ? 
                                    `${type.id} - ${type.manufacturer} ${type.name}` : 
                                    `${type.id} - ${type.name}`;
                            }
                            option.textContent = label;
                            builderTypeIdSelect.appendChild(option);
                        });
                    }
                }
                
                // Debug: Log if typeID 1 is in the dropdown
                const type1Option = builderTypeIdSelect.querySelector('option[value="1"]');
                if (type1Option) {
                    console.log('✓ TypeID 1 added to part builder dropdown:', type1Option.textContent);
                } else {
                    console.warn('⚠️ TypeID 1 NOT found in part builder dropdown. typeIdMap has:', Array.from(typeIdMap.keys()).sort((a, b) => a - b));
                }
            }

            // Update type ID info on change (only add once)
            if (typeIdSelect && !typeIdSelect.dataset.listenersSetup) {
                typeIdSelect.addEventListener('change', function() {
                    const typeId = parseInt(this.value);
                    const oldTypeId = parseInt(this.dataset.previousValue) || null;
                    
                    // Check if we should warn and prompt (code was parsed and Type ID is changing)
                    if (parsedTypeId !== null && typeId !== parsedTypeId && currentParts.length > 0) {
                        const hasSimpleParts = currentParts.some(p => p.type === 'simple');
                        if (hasSimpleParts) {
                            const confirmed = confirm('⚠️ Warning: Changing the item type will change what each simple part code refers to.\n\nSimple part IDs are context-dependent based on the Type ID. For example, part code {4} means different things for different item types.\n\nDo you want to continue?');
                            if (!confirmed) {
                                // Revert to previous value (or parsed value if no previous)
                                this.value = oldTypeId || parsedTypeId || '';
                                return;
                            }
                            // Show persistent warning
                            showTypeIdChangeWarning('typeId');
                        }
                    }
                    
                    // Store the new value for next change
                    this.dataset.previousValue = typeId || '';
                    
                    // Re-render parts with new typeId context (don't clear, just update display)
                    if (oldTypeId !== typeId) {
                        renderParts();
                        if (typeof updateGuidelinesChecklist === 'function') updateGuidelinesChecklist();
                    }
                    
                    const typeIdInfoEl = document.getElementById('typeIdInfo');
                    const itemGuidelinesEl = document.getElementById('itemGuidelines');
                    if (typeId && typeIdMap.has(typeId)) {
                        const typeInfo = typeIdMap.get(typeId);
                        const parts = partsByTypeId.get(typeId) || [];
                        if (typeIdInfoEl) {
                            typeIdInfoEl.innerHTML =
                            `<strong>${typeInfo.category}</strong> | ${parts.length} parts available`;
                        }
                        // Update guidelines based on category
                        updateGuidelines(typeInfo.category, typeId);
                    } else {
                        if (typeIdInfoEl) typeIdInfoEl.textContent = '';
                        if (itemGuidelinesEl) itemGuidelinesEl.style.display = 'none';
                    }
                    generateCode(); // Update code when typeId changes
                });
                typeIdSelect.dataset.listenersSetup = 'true';
            }

            console.log(`Loaded ${typeIdMap.size} type IDs and ${partsMap.size} parts`);
            
            // Debug: Log all found type IDs with details
            const foundTypeIds = Array.from(typeIdMap.keys()).sort((a, b) => a - b);
            console.log('Found Type IDs:', foundTypeIds);
            console.log('Found Type IDs with names:', foundTypeIds.map(id => {
                const info = typeIdMap.get(id);
                return `${id}: ${info.name} (${info.category})`;
            }));
            
            // Check for missing expected type IDs
            const expectedTypeIds = [2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,
                                     254,255,256,259,261,263,264,265,266,267,268,269,270,271,272,273,274,275,
                                     277,278,279,281,282,283,284,285,286,287,289,290,291,292,293,296,298,299,
                                     300,303,306,310,311,312,321];
            const missingTypeIds = expectedTypeIds.filter(id => !typeIdMap.has(id));
            if (missingTypeIds.length > 0) {
                console.warn('Missing Type IDs:', missingTypeIds);
                console.warn('Missing count:', missingTypeIds.length);
            }
            
            // Also check the raw data structure for type IDs we might have missed
            console.log('Checking data structure for type IDs...');
            if (gameData.weapons && gameData.weapons.manufacturers) {
                console.log('Weapons manufacturers:', Object.keys(gameData.weapons.manufacturers));
                for (const [manufacturer, data] of Object.entries(gameData.weapons.manufacturers)) {
                    if (data.weapon_types) {
                        for (const [weaponType, weaponData] of Object.entries(data.weapon_types)) {
                            if (weaponData.type_id && !typeIdMap.has(weaponData.type_id)) {
                                console.warn(`Found unextracted type_id ${weaponData.type_id} in ${manufacturer} ${weaponType}`);
                            }
                        }
                    }
                }
            }
            
            // Hide extra elements and simplify text when data is loaded
            const dataHelpText = document.getElementById('dataHelpText');
            
            if (dataHelpText) {
                dataHelpText.innerHTML = '<small style="color: #81c784;">✅ Data loaded successfully! You can now use the editor below.</small>';
            }
            } catch (error) {
                console.error('processGameData error:', error);
                console.error('Error stack:', error.stack);
                throw error; // Re-throw to be caught by the caller
            }
        }
