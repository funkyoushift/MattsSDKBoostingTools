        // Class mod Skills: typeId 234 part IDs for Vex (254), Amon (255), Rafa (256), Harlowe (259). From game_data_export.json characters.Perk.parts.
        var CLASS_MOD_SKILL_PART_IDS = ['234:6', '234:8', '234:11', '234:12', '234:15', '234:16', '234:29', '234:32', '234:33', '234:49', '234:52', '234:53', '234:97', '234:103'];
        function updateGuidelines(category, typeId) {
            const guidelinesEl = document.getElementById('itemGuidelines');
            const contentEl = document.getElementById('guidelinesContent');
            
            if (!category) {
                guidelinesEl.style.display = 'none';
                return;
            }
            
            // Get current item properties for display in checklist items
            const currentLevel = document.getElementById('level').value || '';
            const currentManufacturer = document.getElementById('manufacturer').value || '';
            const typeIdSelect = document.getElementById('typeId');
            const currentTypeId = typeIdSelect ? (typeIdSelect.value || '') : '';
            let currentTypeName = '';
            
            // Get type name from typeIdMap if available, or from dropdown option text as fallback
            if (currentTypeId) {
                const typeIdNum = parseInt(currentTypeId);
                if (!isNaN(typeIdNum) && typeIdMap && typeIdMap.has(typeIdNum)) {
                    const typeInfo = typeIdMap.get(typeIdNum);
                    currentTypeName = typeInfo.name || `Type ID ${currentTypeId}`;
                } else if (typeIdSelect && typeIdSelect.selectedIndex > 0) {
                    // Fallback: extract name from dropdown option text (format: "310 - enhancement")
                    const optionText = typeIdSelect.options[typeIdSelect.selectedIndex].text;
                    const match = optionText.match(/^\d+\s*-\s*(.+)$/);
                    if (match && match[1]) {
                        currentTypeName = match[1].trim();
                    } else {
                        currentTypeName = `Type ID ${currentTypeId}`;
                    }
                } else if (currentTypeId) {
                    currentTypeName = `Type ID ${currentTypeId}`;
                }
            }
            
            let guidelines = '';
            
            // Determine item type from category (case-insensitive matching)
            const categoryLower = category.toLowerCase();
            const isHeavyWeapon = categoryLower.includes('heavy');
            const isRepkit = categoryLower.includes('repkit') || categoryLower.includes('rep kit');
            const isGrenade = categoryLower.includes('grenade') || categoryLower.includes('ordnance');
            const isClassMod = categoryLower.includes('class mod');
            const isShield = categoryLower.includes('shield');
            const isEnhancement = categoryLower.includes('enhancement');
            const isWeapon = categoryLower.includes('weapon') && !isHeavyWeapon;
            
            if (isHeavyWeapon) {
                guidelines = `
                    <div style="line-height: 1.8; color: #b0d4fa;">
                        <p style="color: #b0d4fa; margin-bottom: 10px;"><strong style="color: #fff;">Heavy Weapons</strong> - Similar to how weapons work. Barrels hold the Legendary perks for Heavy Weapons.</p>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-top: 15px;">
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="manufacturer"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Manufacturer${currentManufacturer ? `: ${currentManufacturer}` : ''}${currentTypeName ? ` | Type: ${currentTypeName}` : ''}</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="level"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Level${currentLevel ? `: ${currentLevel}` : ''}</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="rarity"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Rarity</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="body"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Body</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="bodyAccessories"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Body Accessories</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="barrel"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Barrel</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="barrelAccessories"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Barrel Accessories</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="firmware244"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Firmware 244</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="element"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Element (TypeID 1)</span>
                                </div>
                            </div>
                        </div>
                        <p style="margin-top: 15px; color: #b0d4fa; font-size: 13px; padding: 10px; background: rgba(79, 195, 247, 0.15); border-radius: 4px; border-left: 3px solid #4fc3f7;"><strong>Note:</strong> For ALL Items EXCEPT Enhancement & Class Mod, RARITY is either one of the 4 base rarities OR the Unique Legendary Rarity.</p>
                    </div>
                `;
            } else if (isRepkit) {
                guidelines = `
                    <div style="line-height: 1.8; color: #b0d4fa;">
                        <p style="color: #b0d4fa; margin-bottom: 10px;"><strong style="color: #fff;">Repkits</strong></p>
                        <ul style="margin: 10px 0; padding-left: 20px; color: #b0d4fa;">
                            <li style="color: #b0d4fa; margin-bottom: 5px;">All Repkits require the <strong style="color: #fff;">Body - Legendary Perk</strong></li>
                            <li style="color: #b0d4fa; margin-bottom: 5px;">Repkits use Primary and Secondary Perks. When either is not present, MUST include Parts for the Missing Perks</li>
                            <li style="color: #b0d4fa; margin-bottom: 5px;"><strong style="color: #fff;">Missing Primary:</strong> USE Lookup 243, Parts 53, 55, OR 72</li>
                            <li style="color: #b0d4fa; margin-bottom: 5px;"><strong style="color: #fff;">Missing Secondary:</strong> USE Lookup 243, Parts 76, 78, OR 95</li>
                        </ul>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-top: 15px;">
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="manufacturer"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Manufacturer${currentManufacturer ? `: ${currentManufacturer}` : ''}${currentTypeName ? ` | Type: ${currentTypeName}` : ''}</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="level"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Level${currentLevel ? `: ${currentLevel}` : ''}</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="rarity"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Rarity</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="baseBody"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Body - Legendary Perk</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="elementalResistances243"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Elemental Resistances</span>
                                </div>
                                <div class="guideline-part-dropdown" style="margin-top: 8px;">
                                    <label for="select-elementalResistances243" class="sr-only">Elemental Resistances Part Selector</label>
                                    <select id="select-elementalResistances243" name="select-elementalResistances243" data-category="elementalResistances243" style="width: 100%; padding: 6px; border: 1px solid rgba(79, 195, 247, 0.3); border-radius: 4px; font-size: 12px; background: rgba(30, 30, 46, 0.8); color: #b0d4fa;">
                                        <option value="">Select a part to add...</option>
                                    </select>
                                    <div style="display: flex; gap: 8px; align-items: center; margin-top: 8px;">
                                        <label for="quantity-elementalResistances243" class="sr-only">Quantity for Elemental Resistances</label>
                                        <input type="number" id="quantity-elementalResistances243" name="quantity-elementalResistances243" data-category="elementalResistances243" min="1" max="100" value="1" placeholder="Qty" style="width: 60px; padding: 6px; border: 1px solid rgba(79, 195, 247, 0.3); border-radius: 4px; font-size: 12px; background: rgba(30, 30, 46, 0.8); color: #b0d4fa; text-align: center;">
                                        <button id="add-btn-elementalResistances243" data-category="elementalResistances243" style="padding: 6px 16px; border: 1px solid #4fc3f7; border-radius: 4px; font-size: 12px; background: #4fc3f7; color: #fff; cursor: pointer; font-weight: 500;">Add</button>
                                    </div>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="elementalImmunities243"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Elemental Immunities</span>
                                </div>
                                <div class="guideline-part-dropdown" style="margin-top: 8px;">
                                    <label for="select-elementalImmunities243" class="sr-only">Elemental Immunities Part Selector</label>
                                    <select id="select-elementalImmunities243" name="select-elementalImmunities243" data-category="elementalImmunities243" style="width: 100%; padding: 6px; border: 1px solid rgba(79, 195, 247, 0.3); border-radius: 4px; font-size: 12px; background: rgba(30, 30, 46, 0.8); color: #b0d4fa;">
                                        <option value="">Select a part to add...</option>
                                    </select>
                                    <div style="display: flex; gap: 8px; align-items: center; margin-top: 8px;">
                                        <label for="quantity-elementalImmunities243" class="sr-only">Quantity for Elemental Immunities</label>
                                        <input type="number" id="quantity-elementalImmunities243" name="quantity-elementalImmunities243" data-category="elementalImmunities243" min="1" max="100" value="1" placeholder="Qty" style="width: 60px; padding: 6px; border: 1px solid rgba(79, 195, 247, 0.3); border-radius: 4px; font-size: 12px; background: rgba(30, 30, 46, 0.8); color: #b0d4fa; text-align: center;">
                                        <button id="add-btn-elementalImmunities243" data-category="elementalImmunities243" style="padding: 6px 16px; border: 1px solid #4fc3f7; border-radius: 4px; font-size: 12px; background: #4fc3f7; color: #fff; cursor: pointer; font-weight: 500;">Add</button>
                                    </div>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="elementalSplats243"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Elemental Splats</span>
                                </div>
                                <div class="guideline-part-dropdown" style="margin-top: 8px;">
                                    <label for="select-elementalSplats243" class="sr-only">Elemental Splats Part Selector</label>
                                    <select id="select-elementalSplats243" name="select-elementalSplats243" data-category="elementalSplats243" style="width: 100%; padding: 6px; border: 1px solid rgba(79, 195, 247, 0.3); border-radius: 4px; font-size: 12px; background: rgba(30, 30, 46, 0.8); color: #b0d4fa;">
                                        <option value="">Select a part to add...</option>
                                    </select>
                                    <div style="display: flex; gap: 8px; align-items: center; margin-top: 8px;">
                                        <label for="quantity-elementalSplats243" class="sr-only">Quantity for Elemental Splats</label>
                                        <input type="number" id="quantity-elementalSplats243" name="quantity-elementalSplats243" data-category="elementalSplats243" min="1" max="100" value="1" placeholder="Qty" style="width: 60px; padding: 6px; border: 1px solid rgba(79, 195, 247, 0.3); border-radius: 4px; font-size: 12px; background: rgba(30, 30, 46, 0.8); color: #b0d4fa; text-align: center;">
                                        <button id="add-btn-elementalSplats243" data-category="elementalSplats243" style="padding: 6px 16px; border: 1px solid #4fc3f7; border-radius: 4px; font-size: 12px; background: #4fc3f7; color: #fff; cursor: pointer; font-weight: 500;">Add</button>
                                    </div>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="elementalNovas243"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Elemental Novas</span>
                                </div>
                                <div class="guideline-part-dropdown" style="margin-top: 8px;">
                                    <label for="select-elementalNovas243" class="sr-only">Elemental Novas Part Selector</label>
                                    <select id="select-elementalNovas243" name="select-elementalNovas243" data-category="elementalNovas243" style="width: 100%; padding: 6px; border: 1px solid rgba(79, 195, 247, 0.3); border-radius: 4px; font-size: 12px; background: rgba(30, 30, 46, 0.8); color: #b0d4fa;">
                                        <option value="">Select a part to add...</option>
                                    </select>
                                    <div style="display: flex; gap: 8px; align-items: center; margin-top: 8px;">
                                        <label for="quantity-elementalNovas243" class="sr-only">Quantity for Elemental Novas</label>
                                        <input type="number" id="quantity-elementalNovas243" name="quantity-elementalNovas243" data-category="elementalNovas243" min="1" max="100" value="1" placeholder="Qty" style="width: 60px; padding: 6px; border: 1px solid rgba(79, 195, 247, 0.3); border-radius: 4px; font-size: 12px; background: rgba(30, 30, 46, 0.8); color: #b0d4fa; text-align: center;">
                                        <button id="add-btn-elementalNovas243" data-category="elementalNovas243" style="padding: 6px 16px; border: 1px solid #4fc3f7; border-radius: 4px; font-size: 12px; background: #4fc3f7; color: #fff; cursor: pointer; font-weight: 500;">Add</button>
                                    </div>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="size243"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Size</span>
                                </div>
                                <div class="guideline-part-dropdown" style="margin-top: 8px;">
                                    <label for="select-size243" class="sr-only">Size Part Selector</label>
                                    <select id="select-size243" name="select-size243" data-category="size243" style="width: 100%; padding: 6px; border: 1px solid rgba(79, 195, 247, 0.3); border-radius: 4px; font-size: 12px; background: rgba(30, 30, 46, 0.8); color: #b0d4fa;">
                                        <option value="">Select a part to add...</option>
                                    </select>
                                    <div style="display: flex; gap: 8px; align-items: center; margin-top: 8px;">
                                        <label for="quantity-size243" class="sr-only">Quantity for Size</label>
                                        <input type="number" id="quantity-size243" name="quantity-size243" data-category="size243" min="1" max="100" value="1" placeholder="Qty" style="width: 60px; padding: 6px; border: 1px solid rgba(79, 195, 247, 0.3); border-radius: 4px; font-size: 12px; background: rgba(30, 30, 46, 0.8); color: #b0d4fa; text-align: center;">
                                        <button id="add-btn-size243" data-category="size243" style="padding: 6px 16px; border: 1px solid #4fc3f7; border-radius: 4px; font-size: 12px; background: #4fc3f7; color: #fff; cursor: pointer; font-weight: 500;">Add</button>
                                    </div>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="elemental243"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Elemental Type (for splats and novas)</span>
                                </div>
                                <div class="guideline-part-dropdown" style="margin-top: 8px;">
                                    <label for="select-elemental243" class="sr-only">Elemental Type Part Selector</label>
                                    <select id="select-elemental243" name="select-elemental243" data-category="elemental243" style="width: 100%; padding: 6px; border: 1px solid rgba(79, 195, 247, 0.3); border-radius: 4px; font-size: 12px; background: rgba(30, 30, 46, 0.8); color: #b0d4fa;">
                                        <option value="">Select a part to add...</option>
                                    </select>
                                    <div style="display: flex; gap: 8px; align-items: center; margin-top: 8px;">
                                        <label for="quantity-elemental243" class="sr-only">Quantity for Elemental Type</label>
                                        <input type="number" id="quantity-elemental243" name="quantity-elemental243" data-category="elemental243" min="1" max="100" value="1" placeholder="Qty" style="width: 60px; padding: 6px; border: 1px solid rgba(79, 195, 247, 0.3); border-radius: 4px; font-size: 12px; background: rgba(30, 30, 46, 0.8); color: #b0d4fa; text-align: center;">
                                        <button id="add-btn-elemental243" data-category="elemental243" style="padding: 6px 16px; border: 1px solid #4fc3f7; border-radius: 4px; font-size: 12px; background: #4fc3f7; color: #fff; cursor: pointer; font-weight: 500;">Add</button>
                                    </div>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="parts243"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Parts 243</span>
                                </div>
                                <div class="guideline-part-dropdown" style="margin-top: 8px;">
                                    <label for="select-parts243" class="sr-only">Parts 243 Selector</label>
                                    <select id="select-parts243" name="select-parts243" data-category="parts243" style="width: 100%; padding: 6px; border: 1px solid rgba(79, 195, 247, 0.3); border-radius: 4px; font-size: 12px; background: rgba(30, 30, 46, 0.8); color: #b0d4fa;">
                                        <option value="">Select a part to add...</option>
                                    </select>
                                    <div style="display: flex; gap: 8px; align-items: center; margin-top: 8px;">
                                        <label for="quantity-parts243" class="sr-only">Quantity for Parts 243</label>
                                        <input type="number" id="quantity-parts243" name="quantity-parts243" data-category="parts243" min="1" max="100" value="1" placeholder="Qty" style="width: 60px; padding: 6px; border: 1px solid rgba(79, 195, 247, 0.3); border-radius: 4px; font-size: 12px; background: rgba(30, 30, 46, 0.8); color: #b0d4fa; text-align: center;">
                                        <button id="add-btn-parts243" data-category="parts243" style="padding: 6px 16px; border: 1px solid #4fc3f7; border-radius: 4px; font-size: 12px; background: #4fc3f7; color: #fff; cursor: pointer; font-weight: 500;">Add</button>
                                    </div>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="firmware243"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Firmware 243</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="element"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Element (TypeID 1)</span>
                                </div>
                            </div>
                        </div>
                        <p style="margin-top: 15px; color: #b0d4fa; font-size: 13px; padding: 10px; background: rgba(79, 195, 247, 0.15); border-radius: 4px; border-left: 3px solid #4fc3f7;"><strong>Note:</strong> For ALL Items EXCEPT Enhancement & Class Mod, RARITY is either one of the 4 base rarities OR the Unique Legendary Rarity.</p>
                    </div>
                `;
            } else if (isGrenade) {
                guidelines = `
                    <div style="line-height: 1.8; color: #b0d4fa;">
                        <p style="color: #b0d4fa; margin-bottom: 10px;"><strong style="color: #fff;">Ordnance</strong></p>
                        <ul style="margin: 10px 0; padding-left: 20px; color: #b0d4fa;">
                            <li style="color: #b0d4fa; margin-bottom: 5px;">All Ordnance use EITHER the <strong style="color: #fff;">Base Body</strong> OR the <strong style="color: #fff;">Legendary Body</strong></li>
                            <li style="color: #b0d4fa; margin-bottom: 5px;">Parts can be Elemental Status, Payload, Augment, Stats</li>
                        </ul>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-top: 15px;">
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="manufacturer"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Manufacturer${currentManufacturer ? `: ${currentManufacturer}` : ''}${currentTypeName ? ` | Type: ${currentTypeName}` : ''}</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="level"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Level${currentLevel ? `: ${currentLevel}` : ''}</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="rarity"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Rarity</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="body"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Body</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="parts245"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Elemental Status</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="payload245"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Payload 245</span>
                                </div>
                                <div class="guideline-part-dropdown" style="margin-top: 8px;">
                                    <select id="select-payload245" name="select-payload245" data-category="payload245" style="width: 100%; padding: 6px; border: 1px solid rgba(79, 195, 247, 0.3); border-radius: 4px; font-size: 12px; background: rgba(30, 30, 46, 0.8); color: #b0d4fa;">
                                        <option value="">Select a part to add...</option>
                                    </select>
                                    <div style="display: flex; gap: 8px; margin-top: 8px; align-items: center;">
                                        <input type="number" id="quantity-payload245" name="quantity-payload245" data-category="payload245" min="1" max="100" value="1" placeholder="Qty" style="width: 60px; padding: 6px; border: 1px solid rgba(79, 195, 247, 0.3); border-radius: 4px; font-size: 12px; background: rgba(30, 30, 46, 0.8); color: #b0d4fa; text-align: center;">
                                        <button id="add-btn-payload245" data-category="payload245" style="padding: 6px 16px; border: 1px solid #4fc3f7; border-radius: 4px; font-size: 12px; background: #4fc3f7; color: #fff; cursor: pointer; font-weight: 500;">Add</button>
                                    </div>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="stats245"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Stats 245</span>
                                </div>
                                <div class="guideline-part-dropdown" style="margin-top: 8px;">
                                    <select id="select-stats245" name="select-stats245" data-category="stats245" style="width: 100%; padding: 6px; border: 1px solid rgba(79, 195, 247, 0.3); border-radius: 4px; font-size: 12px; background: rgba(30, 30, 46, 0.8); color: #b0d4fa;">
                                        <option value="">Select a part to add...</option>
                                    </select>
                                    <div style="display: flex; gap: 8px; margin-top: 8px; align-items: center;">
                                        <input type="number" id="quantity-stats245" name="quantity-stats245" data-category="stats245" min="1" max="100" value="1" placeholder="Qty" style="width: 60px; padding: 6px; border: 1px solid rgba(79, 195, 247, 0.3); border-radius: 4px; font-size: 12px; background: rgba(30, 30, 46, 0.8); color: #b0d4fa; text-align: center;">
                                        <button id="add-btn-stats245" data-category="stats245" style="padding: 6px 16px; border: 1px solid #4fc3f7; border-radius: 4px; font-size: 12px; background: #4fc3f7; color: #fff; cursor: pointer; font-weight: 500;">Add</button>
                                    </div>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="augment245"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Augment 245</span>
                                </div>
                                <div class="guideline-part-dropdown" style="margin-top: 8px;">
                                    <select id="select-augment245" name="select-augment245" data-category="augment245" style="width: 100%; padding: 6px; border: 1px solid rgba(79, 195, 247, 0.3); border-radius: 4px; font-size: 12px; background: rgba(30, 30, 46, 0.8); color: #b0d4fa;">
                                        <option value="">Select a part to add...</option>
                                    </select>
                                    <div style="display: flex; gap: 8px; margin-top: 8px; align-items: center;">
                                        <input type="number" id="quantity-augment245" name="quantity-augment245" data-category="augment245" min="1" max="100" value="1" placeholder="Qty" style="width: 60px; padding: 6px; border: 1px solid rgba(79, 195, 247, 0.3); border-radius: 4px; font-size: 12px; background: rgba(30, 30, 46, 0.8); color: #b0d4fa; text-align: center;">
                                        <button id="add-btn-augment245" data-category="augment245" style="padding: 6px 16px; border: 1px solid #4fc3f7; border-radius: 4px; font-size: 12px; background: #4fc3f7; color: #fff; cursor: pointer; font-weight: 500;">Add</button>
                                    </div>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="firmware245"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Firmware 245</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="element"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Element (TypeID 1)</span>
                                </div>
                            </div>
                        </div>
                        <p style="margin-top: 15px; color: #b0d4fa; font-size: 13px; padding: 10px; background: rgba(79, 195, 247, 0.15); border-radius: 4px; border-left: 3px solid #4fc3f7;"><strong>Note:</strong> For ALL Items EXCEPT Enhancement & Class Mod, RARITY is either one of the 4 base rarities OR the Unique Legendary Rarity.</p>
                    </div>
                `;
            } else if (isClassMod) {
                guidelines = `
                    <div style="line-height: 1.8; color: #b0d4fa;">
                        <p style="color: #b0d4fa; margin-bottom: 10px;"><strong style="color: #fff;">Class Mods</strong></p>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-top: 15px;">
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="manufacturer"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Manufacturer${currentManufacturer ? `: ${currentManufacturer}` : ''}${currentTypeName ? ` | Type: ${currentTypeName}` : ''}</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="level"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Level${currentLevel ? `: ${currentLevel}` : ''}</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="rarity"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Rarity And Base Skin</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="body"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Body</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="skills"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Skills</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="stat234"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Stat 234</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="stat2_234"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Stat2 234</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="statspecial_234"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Statspecial 234</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="firmware234"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Firmware 234</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="element"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Element (TypeID 1)</span>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            } else if (isShield) {
                guidelines = `
                    <div style="line-height: 1.8; color: #b0d4fa;">
                        <p style="color: #b0d4fa; margin-bottom: 10px;"><strong style="color: #fff;">Shields</strong></p>
                        <ul style="margin: 10px 0; padding-left: 20px; color: #b0d4fa;">
                            <li style="color: #b0d4fa; margin-bottom: 5px;"><strong>Important:</strong> For shields, "Base Body" and "Legendary Part" are the same thing. These are the main shield body parts (e.g., parts with spawn codes like "bor_shield.part_body_energy_lightning") that come from the shield's own type ID (e.g., typeId 300 for Ripper shields).</li>
                            <li style="color: #b0d4fa; margin-bottom: 5px;">Perks are universal for all shield types, Parts are dependent on the shield type. Armor Shields get Armor Shield Parts, Energy Shields get Energy Shield Parts</li>
                            <li style="color: #b0d4fa; margin-bottom: 5px;">ALL Perks have 2 variations, a Primary and Secondary. Primary has higher values than Secondary. Can combine Primary AND Secondary for higher stats</li>
                            <li style="color: #b0d4fa; margin-bottom: 5px;">Perks can be Elemental Resist, Perks. When no Elemental Resist is used MUST USE Part 246:21</li>
                        </ul>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-top: 15px;">
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="manufacturer"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Manufacturer${currentManufacturer ? `: ${currentManufacturer}` : ''}${currentTypeName ? ` | Type: ${currentTypeName}` : ''}</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="level"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Level${currentLevel ? `: ${currentLevel}` : ''}</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="rarity"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Rarity</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="baseBody"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Body - Legendary Perk</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="resistance246"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Resistance</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="primaryPerks246"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Primary Perks 246</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="secondaryPerks246"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Secondary Perks 246</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="armor237"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Armor 237</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="energy248"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Energy 248</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="firmware246"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Firmware 246</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="element"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Element (TypeID 1)</span>
                                </div>
                            </div>
                        </div>
                        <p style="margin-top: 15px; color: #b0d4fa; font-size: 13px; padding: 10px; background: rgba(79, 195, 247, 0.15); border-radius: 4px; border-left: 3px solid #4fc3f7;"><strong>Note:</strong> For ALL Items EXCEPT Enhancement & Class Mod, RARITY is either one of the 4 base rarities OR the Unique Legendary Rarity.</p>
                    </div>
                `;
            } else if (isEnhancement) {
                guidelines = `
                    <div style="line-height: 1.8; color: #b0d4fa;">
                        <p style="color: #b0d4fa; margin-bottom: 10px;"><strong style="color: #fff;">Enhancements</strong></p>
                        <ul style="margin: 10px 0; padding-left: 20px; color: #b0d4fa;">
                            <li style="color: #b0d4fa; margin-bottom: 5px;">Enhancements use the base body that corresponds to the rarity of the Item, Lookup 247 Parts 76-80</li>
                        </ul>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-top: 15px;">
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="manufacturer"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Manufacturer${currentManufacturer ? `: ${currentManufacturer}` : ''}${currentTypeName ? ` | Type: ${currentTypeName}` : ''}</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="level"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Level${currentLevel ? `: ${currentLevel}` : ''}</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="rarity"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Rarity</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="baseBody247"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Base Body 247</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="legendaryPerks"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Manufacturer Perks</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="stat_247"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Stat 247</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="stat2_247"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Stat2 247</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="stat3_247"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Stat3 247</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="firmware247"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Firmware 247</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="element"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Element (TypeID 1)</span>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            } else if (isWeapon) {
                guidelines = `
                    <div style="line-height: 1.8; color: #b0d4fa;">
                        <p style="color: #b0d4fa; margin-bottom: 10px;"><strong style="color: #fff;">Weapons</strong></p>
                        <p style="color: #b0d4fa;">Standard weapon structure with Manufacturer, Level, Rarity, Body, Body Accessories, Barrel, Barrel Accessories, Magazine, Scope, Scope Accessory, Grip, Foregrip, Underbarrel, and Stat Modifier.</p>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-top: 15px;">
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="manufacturer"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Manufacturer${currentManufacturer ? `: ${currentManufacturer}` : ''}${currentTypeName ? ` | Type: ${currentTypeName}` : ''}</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="level"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Level${currentLevel ? `: ${currentLevel}` : ''}</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="rarity"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Rarity</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="body"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Body</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="bodyAccessories"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Body Accessories</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="barrel"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Barrel</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="barrelAccessories"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Barrel Accessories</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="magazine"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Magazine</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="scope"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Scope</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="scopeAccessory"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Scope Accessory</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="grip"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Grip</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="foregrip"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Foregrip</span>
                                </div>
                                <div style="margin-top: 8px; padding: 8px; background: rgba(255, 152, 0, 0.15); border-radius: 4px; border-left: 3px solid #ff9800; font-size: 12px; color: #ffcc80; line-height: 1.5;">
                                    <strong>Note:</strong> Foregrips are INCOMPATIBLE with Daedalus Ammo Switcher. Adding a foregrip anywhere will remove the ability to switch to the other Ammo Type.
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="underbarrel"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Underbarrel</span>
                                </div>
                            </div>
                            <div id="daedalusAmmoGuideline" class="guideline-item" style="display: none; flex-direction: column; padding: 12px; background: #f9f9f9; border-radius: 6px; border: 2px solid #e0e0e0; min-height: 60px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="daedalusAmmo"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Daedalus Ammo Type</span>
                                </div>
                                <div class="guideline-part-dropdown" style="margin-top: 8px;">
                                    <label for="select-daedalusAmmo" class="sr-only">Daedalus Ammo Type Part Selector</label>
                                    <select id="select-daedalusAmmo" name="select-daedalusAmmo" data-category="daedalusAmmo" style="width: 100%; padding: 6px; border: 1px solid rgba(79, 195, 247, 0.3); border-radius: 4px; font-size: 12px; background: rgba(30, 30, 46, 0.8); color: #b0d4fa;">
                                        <option value="">Select a part to add...</option>
                                    </select>
                                </div>
                            </div>
                            <div id="maliwanLicensedUnderbarrelGuideline" class="guideline-item" style="display: none; flex-direction: column; padding: 12px; background: #f9f9f9; border-radius: 6px; border: 2px solid #e0e0e0; min-height: 60px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="maliwanLicensedUnderbarrel"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Maliwan Licensed Underbarrel</span>
                                </div>
                                <div class="guideline-part-dropdown" style="margin-top: 8px;">
                                    <label for="select-maliwanLicensedUnderbarrel" class="sr-only">Maliwan Licensed Underbarrel Part Selector</label>
                                    <select id="select-maliwanLicensedUnderbarrel" name="select-maliwanLicensedUnderbarrel" data-category="maliwanLicensedUnderbarrel" style="width: 100%; padding: 6px; border: 1px solid rgba(79, 195, 247, 0.3); border-radius: 4px; font-size: 12px; background: rgba(30, 30, 46, 0.8); color: #b0d4fa;">
                                        <option value="">Select a part to add...</option>
                                    </select>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="licensedParts"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Licensed Parts</span>
                                </div>
                                <div class="guideline-part-dropdown" style="margin-top: 8px;">
                                    <label for="select-licensedParts" class="sr-only">Licensed Parts Selector</label>
                                    <select id="select-licensedParts" name="select-licensedParts" data-category="licensedParts" style="width: 100%; padding: 6px; border: 1px solid rgba(79, 195, 247, 0.3); border-radius: 4px; font-size: 12px; background: rgba(30, 30, 46, 0.8); color: #b0d4fa;">
                                        <option value="">Select a part to add...</option>
                                    </select>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="statModifier"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Stat Modifier (<span style="color: #00E5FF;">Pearlescent</span> Stat Bonuses)</span>
                                </div>
                            </div>
                            <div class="guideline-item" style="display: flex; flex-direction: column; padding: var(--input-pad-y) var(--input-pad-x); background: rgba(30, 30, 46, 0.6); border-radius: 6px; border: 1px solid rgba(79, 195, 247, 0.3); min-height: 48px;">
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                                    <div data-checklist="element"                                     style="width: 24px; height: 24px; border: 2px solid rgba(79, 195, 247, 0.4); border-radius: 4px; background: rgba(30, 30, 46, 0.8); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; font-size: 14px; flex-shrink: 0;"></div>
                                    <span style="font-weight: 600; color: #b0d4fa; font-size: 14px;">Element (<span style="color: #00E5FF;">Pearlescent</span> Element Overrides)</span>
                                </div>
                            </div>
                        </div>
                        <p style="margin-top: 15px; color: #b0d4fa; font-size: 13px; padding: 10px; background: rgba(79, 195, 247, 0.15); border-radius: 4px; border-left: 3px solid #4fc3f7;"><strong>Note:</strong> For ALL Items EXCEPT Enhancement & Class Mod, RARITY is either one of the 4 base rarities OR the Unique Legendary Rarity.</p>
                    </div>
                `;
            }
            
            if (guidelines) {
                contentEl.innerHTML = guidelines;
                guidelinesEl.style.display = 'block';
                // Use setTimeout to ensure DOM is updated before checking checklist
                setTimeout(() => {
                    updateGuidelinesChecklist(); // Update checklist after guidelines are displayed
                }, 100);
            } else {
                guidelinesEl.style.display = 'none';
            }
        }

        function updateGuidelinesChecklist() {
            const guidelinesEl = document.getElementById('itemGuidelines');
            const contentEl = document.getElementById('guidelinesContent');
            if (!guidelinesEl || !contentEl) {
                console.log('updateGuidelinesChecklist: Missing elements');
                return;
            }
            
            // Don't return early if guidelines are hidden - we might need to update anyway
            if (guidelinesEl.style.display === 'none') {
                console.log('updateGuidelinesChecklist: Guidelines hidden');
                return;
            }
            
            // Serials/parts that show "NEW!" badge (dropdowns, chips, same set as decode tool) - defined early for listener closure
            const newSerialIdsGuidelines = window.bl4ReleaseNewParts?.serialIds || new Set();
            const newPartKeysGuidelines = window.bl4ReleaseNewParts?.partKeys || new Set();
            
            // Set up master unlock checkbox event listener (only once)
            const masterUnlock = document.getElementById('masterUnlockGuidelines');
            if (masterUnlock && !masterUnlock.dataset.listenerAdded) {
                masterUnlock.dataset.listenerAdded = 'true';
                masterUnlock.addEventListener('change', function() {
                    // Update all dropdowns when master unlock changes
                    const allDropdowns = contentEl.querySelectorAll('.guideline-part-dropdown select');
                    allDropdowns.forEach(select => {
                        const categoryKey = select.getAttribute('data-category');
                        if (categoryKey) {
                            const isUnlocked = masterUnlock.checked;
                            const availableParts = getAvailablePartsForCategory(categoryKey, isUnlocked);
                            
                            // Deduplicate availableParts by fullId before populating dropdown
                            const seenParts = new Set();
                            const uniqueParts = availableParts.filter(partInfo => {
                                const fullId = String(partInfo.fullId || partInfo.id || '');
                                if (fullId && seenParts.has(fullId)) {
                                    return false; // Duplicate
                                }
                                if (fullId) seenParts.add(fullId);
                                return true;
                            });
                            
                            // Clear existing options
                            select.innerHTML = '';
                            
                            // Sort parts alphabetically by name, ignoring the ID prefix
                            const sortedParts = uniqueParts.sort((a, b) => {
                                // For Energy Shield parts (typeId 248), Armor Shield parts (typeId 237), Shield Perks (typeId 246), Universal Enhancements (typeId 247), and Grenade/Ordnance parts (typeId 245), prefer modelName/description for sorting
                                const getName = (part) => {
                                    if (part.typeId === 248 || part.typeId === 237 || part.typeId === 246) {
                                        // Use modelName first, then name, then fallback
                                        return String(part.modelName || part.name || 'Unknown').toLowerCase().trim();
                                    } else if (part.typeId === 247) {
                                        // For enhancements, use description or name for sorting
                                        return String(part.description || part.name || 'Unknown').toLowerCase().trim();
                                    } else if (part.typeId === 245) {
                                        // For grenade/ordnance parts, use name for sorting (already descriptive)
                                        return String(part.name || 'Unknown').toLowerCase().trim();
                                    }
                                    return String(part.name || 'Unknown').toLowerCase().trim();
                                };
                                const nameA = getName(a);
                                const nameB = getName(b);
                                return nameA.localeCompare(nameB);
                            });
                            
                            if (sortedParts.length > 0) {
                                select.disabled = false;
                                select.style.cssText = 'width: 100%; padding: 6px; border: 1px solid rgba(79, 195, 247, 0.3); border-radius: 4px; font-size: 12px; background: rgba(30, 30, 46, 0.8); color: #b0d4fa;';
                                select.innerHTML = '<option value="" style="color: #666;">Select a part to add...</option>';
                                
                                const currentTypeId = parseInt(document.getElementById('typeId').value) || 0;
                                
                                // Special handling for skills category: Show grouped skills
                                if (categoryKey === 'skills' && sortedParts.length > 0 && sortedParts[0].tiers) {
                                    // This is a grouped skill structure
                                    sortedParts.forEach(skillGroup => {
                                        const option = document.createElement('option');
                                        option.value = JSON.stringify({
                                            skillName: skillGroup.name,
                                            tiers: skillGroup.tiers,
                                            typeId: skillGroup.typeId,
                                            isSkillGroup: true
                                        });
                                        option.textContent = skillGroup.name;
                                        option.style.cssText = 'color: #b0d4fa; background: rgba(30, 30, 46, 0.95);';
                                        select.appendChild(option);
                                    });
                                } else {
                                    // Normal parts handling
                                    sortedParts.forEach(partInfo => {
                                        // Extract part ID correctly
                                        let partId = partInfo.id || '';
                                        const fullId = partInfo.fullId || '';
                                        const partTypeId = partInfo.typeId || currentTypeId;
                                        
                                        // If fullId is in format "typeId:partId", extract partId
                                        if (fullId.includes(':')) {
                                            const parts = fullId.split(':');
                                            if (parts.length === 2) {
                                                partId = parts[1];
                                            }
                                        } else if (!partId && fullId) {
                                            partId = fullId;
                                        }
                                        
                                        // If partId is still empty, try to extract from id
                                        if (!partId && partInfo.id) {
                                            const idStr = String(partInfo.id);
                                            if (idStr.includes(':')) {
                                                const parts = idStr.split(':');
                                                if (parts.length === 2) {
                                                    partId = parts[1];
                                                }
                                            } else {
                                                partId = idStr;
                                            }
                                        }
                                        
                                        const option = document.createElement('option');
                                        const fullIdOpt = fullId || `${partTypeId}:${partId}`;
                                        option.value = JSON.stringify({
                                            id: partId,
                                            typeId: partTypeId,
                                            fullId: fullIdOpt,
                                            name: partInfo.name || 'Unknown'
                                        });
                                        const partKeyFromSpawnOpt = (partInfo.spawnCode) ? String(partInfo.spawnCode).split('.').pop().toLowerCase() : '';
                                        const isNewOpt = newSerialIdsGuidelines.has(fullIdOpt) || (partKeyFromSpawnOpt && newPartKeysGuidelines.has(partKeyFromSpawnOpt));
                                        option.textContent = (isNewOpt ? 'NEW! ' : '') + formatPartForDropdown(partInfo);
                                        // Color based on rarity
                                        const rarityColor = getRarityColor(partInfo);
                                        option.style.cssText = `color: ${rarityColor}; background: rgba(30, 30, 46, 0.95);`;
                                        select.appendChild(option);
                                    });
                                }
                            } else {
                                select.innerHTML = '<option value="" style="color: #999;">No parts available for this category</option>';
                                select.disabled = true;
                                select.style.cssText = 'width: 100%; padding: 6px; border: 1px solid rgba(79, 195, 247, 0.2); border-radius: 4px; font-size: 12px; background: rgba(30, 30, 46, 0.4); color: #666; cursor: not-allowed;';
                            }
                        }
                    });
                });
            }
            
            // Set up descriptive IDs checkbox event listener (only once)
            const descriptiveIdsCheckbox = document.getElementById('descriptiveIdsGuidelines');
            if (descriptiveIdsCheckbox && !descriptiveIdsCheckbox.dataset.listenerAdded) {
                descriptiveIdsCheckbox.dataset.listenerAdded = 'true';
                descriptiveIdsCheckbox.addEventListener('change', function() {
                    // Refresh the guidelines checklist to update part IDs display
                    updateGuidelinesChecklist();
                });
            }
            
            // Initialize currentParts if it doesn't exist
            if (!currentParts) {
                currentParts = [];
            }
            
            console.log('updateGuidelinesChecklist: Starting, currentParts.length =', currentParts.length);
            
            const category = document.getElementById('typeId')?.options[document.getElementById('typeId')?.selectedIndex]?.text || '';
            const categoryLower = category.toLowerCase();
            const isHeavyWeapon = categoryLower.includes('heavy');
            const isRepkit = categoryLower.includes('repkit') || categoryLower.includes('rep kit');
            const isGrenade = categoryLower.includes('grenade') || categoryLower.includes('ordnance');
            const isClassMod = categoryLower.includes('class mod');
            const isShield = categoryLower.includes('shield');
            const isEnhancement = categoryLower.includes('enhancement');
            // Weapons include: Assault Rifle, Pistol, Shotgun, SMG, Sniper Rifle, etc.
            // Check for common weapon types (excluding Heavy Weapon, Repkit, Grenade, Class Mod, Shield, Enhancement)
            const isWeapon = !isHeavyWeapon && !isRepkit && !isGrenade && !isClassMod && !isShield && !isEnhancement &&
                (categoryLower.includes('weapon') || categoryLower.includes('assault rifle') || 
                 categoryLower.includes('pistol') || categoryLower.includes('shotgun') || 
                 categoryLower.includes('smg') || categoryLower.includes('sniper rifle') ||
                 categoryLower.includes('rifle') || categoryLower.includes('smg'));
            
            console.log('updateGuidelinesChecklist: category =', category, 'isWeapon =', isWeapon);
            
            // Helper function to format part for display
            const formatPartDisplay = (part, partIndex) => {
                if (part.type === 'simple') {
                    return `{${part.value}}`;
                } else if (part.type === 'typed') {
                    return `{${part.typeId}:${part.value}}`;
                } else if (part.type === 'array') {
                    return `{${part.typeId}:[${part.values.join(' ')}]}`;
                } else if (part.type === 'string') {
                    return `"${part.value}"`;
                }
                return `{part ${partIndex}}`;
            };
            
            // Analyze currentParts to determine what's present - track part IDs that fulfill each requirement
            const checklistStatus = {
                body: [],
                bodyAccessories: [],
                barrel: [],
                barrelAccessories: [],
                magazine: [],
                scope: [],
                scopeAccessory: [],
                grip: [],
                foregrip: [],
                underbarrel: [],
                daedalusAmmo: [],
                maliwanLicensedUnderbarrel: [],
                licensedParts: [],
                statModifier: [],
                rarity: [],
                element: [], // TypeID 1 - Element parts
                firmware244: [],
                firmware243: [],
                firmware245: [],
                firmware247: [],
                firmware234: [],
                firmware246: [],
                baseBody: [],
                baseBody247: [], // Base Body 247 (parts 76-80) for enhancements
                legendaryPart: [],
                elementalResistances243: [],
                elementalImmunities243: [],
                elementalSplats243: [],
                elementalNovas243: [],
                size243: [],
                elemental243: [],
                parts243: [],
                parts245: [],
                payload245: [],
                stats245: [],
                augment245: [],
                stat_247: [],
                stat2_247: [],
                stat3_247: [],
                stat234: [],
                stat2_234: [],
                statspecial_234: [],
                primaryPerks246: [],
                secondaryPerks246: [],
                resistance246: [],
                armor237: [],
                energy248: [],
                skills: [],
                legendaryPerks: []
            };
            
            // Detect Daedalus Ammo Switch (part {46} for Maliwan sniper, {53} for other weapons) and ammo type (23:62, 23:63, 23:64, 23:65 or simple {62}, {63}, {64}, {65})
            let hasDaedalusAmmoSwitch = false;
            let currentAmmoType = null;
            // Detect Maliwan Element Switch (part {13:60} or simple {60} when it's the Element Switch) for Maliwan Licensed Underbarrel
            let hasMaliwanElementSwitch = false;
            
            if (isWeapon && currentParts) {
                for (const part of currentParts) {
                    // Check for Daedalus Ammo Switch underbarrel (part {46} for Maliwan sniper, {53} for other weapons)
                    if (part.type === 'simple' && (part.value === 46 || part.value === 53)) {
                        hasDaedalusAmmoSwitch = true;
                    }
                    // Check for Maliwan Element Switch underbarrel (part {13:60} or simple {60})
                    if (part.type === 'typed' && part.typeId === 13 && part.value === 60) {
                        hasMaliwanElementSwitch = true;
                    } else if (part.type === 'simple' && part.value === 60) {
                        // Check if this simple {60} is actually the Maliwan Element Switch by checking partInfo
                        // We'll need to check this later when we have partInfo, but for now check if it's likely
                        // The Element Switch is typically an underbarrel part
                        const partInfo = part.partInfo || (window.partsMap ? window.partsMap.get(`13:60`) || window.partsMap.get('60') : null);
                        if (partInfo) {
                            const spawnCode = String(partInfo.spawnCode || '').toLowerCase();
                            const partName = String(partInfo.name || '').toLowerCase();
                            const partType = String(partInfo.partType || '').toLowerCase();
                            // Check if it's the Element Switch
                            if (spawnCode.includes('element_switch') || 
                                partName.includes('element switch') || 
                                partName.includes('maliwan element') ||
                                (partType === 'underbarrel' && partName.includes('maliwan'))) {
                                hasMaliwanElementSwitch = true;
                            }
                        }
                    }
                    // Check for Daedalus ammo type (typed {23:62} or simple {62}, {63}, {64}, {65})
                    if (part.type === 'typed' && part.typeId === 23) {
                        const ammoId = part.value;
                        if (ammoId === 62 || ammoId === 63 || ammoId === 64 || ammoId === 65) {
                            currentAmmoType = ammoId;
                        }
                    } else if (part.type === 'simple') {
                        // Simple parts {62}, {63}, {64}, {65} can be Daedalus ammo when Ammo Switch is present
                        const ammoId = part.value;
                        if (ammoId === 62 || ammoId === 63 || ammoId === 64 || ammoId === 65) {
                            // We'll check if Ammo Switch is present later, but store the potential ammo type
                            currentAmmoType = ammoId;
                        }
                    }
                }
            }
            
            // Show/hide Daedalus Ammo Type guideline section
            const daedalusAmmoGuideline = document.getElementById('daedalusAmmoGuideline');
            if (daedalusAmmoGuideline) {
                if (hasDaedalusAmmoSwitch && isWeapon) {
                    daedalusAmmoGuideline.style.display = 'flex';
                } else {
                    daedalusAmmoGuideline.style.display = 'none';
                }
            }
            
            // Show/hide Maliwan Licensed Underbarrel guideline section
            const maliwanLicensedUnderbarrelGuideline = document.getElementById('maliwanLicensedUnderbarrelGuideline');
            if (maliwanLicensedUnderbarrelGuideline) {
                if (hasMaliwanElementSwitch && isWeapon) {
                    maliwanLicensedUnderbarrelGuideline.style.display = 'flex';
                } else {
                    maliwanLicensedUnderbarrelGuideline.style.display = 'none';
                }
            }
            
            // Helper function to process a part for checklist categorization
            const processPartForChecklist = (part, partInfo, partDisplay, checklistStatus, isWeapon, isShield, hasMaliwanElementSwitch) => {
                const currentTypeId = parseInt(document.getElementById('typeId').value);
                
                // Check typed/array parts by typeId even without partInfo (for firmware, etc.)
                if (part.type === 'typed' || part.type === 'array') {
                    const typeId = part.typeId;
                    // TypeID 4 = Body Accessories
                    if (typeId === 4) {
                        if (!checklistStatus.bodyAccessories.includes(partDisplay)) {
                            checklistStatus.bodyAccessories.push(partDisplay);
                        }
                    }
                    // TypeID 1 = Element parts
                    if (typeId === 1) {
                        // Check if it's a Maliwan Licensed Underbarrel part (when Element Switch is present)
                        if (partInfo && hasMaliwanElementSwitch) {
                            const spawnCode = String(partInfo.spawnCode || '').toLowerCase();
                            const partPath = String(partInfo.path || '').toLowerCase();
                            const isMaliwanLicensedUnderbarrel = spawnCode.includes('part_secondary_elem') || 
                                                                  partPath.includes('licensed_underbarrel') ||
                                                                  (partInfo.category && String(partInfo.category).toLowerCase().includes('maliwan licensed'));
                            if (isMaliwanLicensedUnderbarrel) {
                                if (!checklistStatus.maliwanLicensedUnderbarrel.includes(partDisplay)) {
                                    checklistStatus.maliwanLicensedUnderbarrel.push(partDisplay);
                                }
                            }
                        }
                        // Also add to element checklist
                        if (!checklistStatus.element.includes(partDisplay)) {
                        checklistStatus.element.push(partDisplay);
                        }
                    }
                    if (typeId === 244 && !checklistStatus.firmware244.includes(partDisplay)) checklistStatus.firmware244.push(partDisplay);
                    if (typeId === 243) {
                        // Check if this is firmware or regular parts243
                        const originalPartType = (partInfo && partInfo.partType) ? String(partInfo.partType) : '';
                        const partName = (partInfo && partInfo.name) ? String(partInfo.name).toLowerCase() : '';
                        const partPath = (partInfo && partInfo.path) ? String(partInfo.path).toLowerCase() : '';
                        const spawnCode = (partInfo && partInfo.spawnCode) ? String(partInfo.spawnCode).toLowerCase() : '';
                        
                        // Extract part ID to check for Skillcraft (243:113)
                        const partIdStr = String(partInfo && partInfo.id ? partInfo.id : (partInfo && partInfo.fullId ? partInfo.fullId : ''));
                        let partIdNum = null;
                        if (partIdStr.includes(':')) {
                            const parts = partIdStr.split(':');
                            if (parts.length >= 2) {
                                partIdNum = parseInt(parts[parts.length - 1]);
                            }
                        } else if (!isNaN(parseInt(partIdStr))) {
                            partIdNum = parseInt(partIdStr);
                        }
                        const isSkillcraftById = partIdNum === 113 && typeId === 243;
                        
                        // Primary check: partType === 'Firmware'
                        // Secondary check: spawnCode/path/name contains 'firmware' or 'skillcraft', or is Skillcraft by ID
                        const isFirmware = originalPartType === 'Firmware' || 
                                         spawnCode.includes('firmware') || partPath.includes('firmware') ||
                                         spawnCode.includes('skillcraft') || partName.includes('skillcraft') || isSkillcraftById;
                        
                        if (isFirmware) {
                            if (!checklistStatus.firmware243.includes(partDisplay)) checklistStatus.firmware243.push(partDisplay);
                            } else {
                                // Categorize non-firmware parts into subcategories
                                const isResistance = originalPartType === 'Resistance' || spawnCode.includes('elemental_resist') || spawnCode.includes('resist');
                                const isImmunity = originalPartType === 'Immunity' || spawnCode.includes('immunity');
                                const isSplat = originalPartType === 'Splat' || spawnCode.includes('splat') || (partIdNum >= 32 && partIdNum <= 36);
                                const isNova = originalPartType === 'Nova' || spawnCode.includes('nova') || (partIdNum >= 37 && partIdNum <= 41);
                                const partString = String(partInfo.string || '').toLowerCase();
                                const isSize = originalPartType === 'Size' || spawnCode.includes('payload') || partString.includes('payload') || (partIdNum >= 103 && partIdNum <= 106);
                                const isElemental = originalPartType === 'Elemental' || spawnCode.includes('part_element') || (partIdNum >= 98 && partIdNum <= 102);
                                
                                if (isResistance) {
                                    if (!checklistStatus.elementalResistances243.includes(partDisplay)) checklistStatus.elementalResistances243.push(partDisplay);
                                } else if (isImmunity) {
                                    if (!checklistStatus.elementalImmunities243.includes(partDisplay)) checklistStatus.elementalImmunities243.push(partDisplay);
                                } else if (isSplat) {
                                    if (!checklistStatus.elementalSplats243.includes(partDisplay)) checklistStatus.elementalSplats243.push(partDisplay);
                                } else if (isNova) {
                                    if (!checklistStatus.elementalNovas243.includes(partDisplay)) checklistStatus.elementalNovas243.push(partDisplay);
                                } else if (isSize) {
                                    if (!checklistStatus.size243.includes(partDisplay)) checklistStatus.size243.push(partDisplay);
                                } else if (isElemental) {
                                    if (!checklistStatus.elemental243.includes(partDisplay)) checklistStatus.elemental243.push(partDisplay);
                                } else {
                                    // Everything else goes to parts243
                                    if (!checklistStatus.parts243.includes(partDisplay)) checklistStatus.parts243.push(partDisplay);
                                }
                            }
                    }
                    if (typeId === 245) {
                        // Check if this is firmware, payload, augment, or elemental status
                        const partType = (partInfo && partInfo.partType) ? String(partInfo.partType).toLowerCase() : '';
                        const partName = (partInfo && partInfo.name) ? String(partInfo.name).toLowerCase() : '';
                        const partPath = (partInfo && partInfo.path) ? String(partInfo.path).toLowerCase() : '';
                        const spawnCode = (partInfo && partInfo.spawnCode) ? String(partInfo.spawnCode).toLowerCase() : '';
                        
                        // Extract part ID number for elemental status check
                        const partIdStr = String(partInfo.id || partInfo.fullId || '');
                        let partIdNum = null;
                        if (partIdStr.includes(':')) {
                            const parts = partIdStr.split(':');
                            if (parts.length >= 2) {
                                partIdNum = parseInt(parts[parts.length - 1]);
                            }
                        } else if (!isNaN(parseInt(partIdStr))) {
                            partIdNum = parseInt(partIdStr);
                        }
                        
                        // Check for elemental status parts (245:24-28: Corrosive, Cryo, Fire, Radiation, Shock)
                        const isElementalStatus = (partType === 'status' || partName.includes('status') || partPath.includes('status') || spawnCode.includes('status')) ||
                                                 (partIdNum >= 24 && partIdNum <= 28 && typeId === 245);
                        
                        if (partType.includes('firmware') || partName.includes('firmware') || partPath.includes('firmware') || spawnCode.includes('firmware')) {
                            if (!checklistStatus.firmware245.includes(partDisplay)) checklistStatus.firmware245.push(partDisplay);
                        } else if (partType === 'augment' || partPath.includes('augment') || spawnCode.includes('augment')) {
                            if (!checklistStatus.augment245.includes(partDisplay)) checklistStatus.augment245.push(partDisplay);
                        } else if (isElementalStatus) {
                            // Elemental status parts go to parts245
                            if (!checklistStatus.parts245.includes(partDisplay)) checklistStatus.parts245.push(partDisplay);
                        } else if (partType === 'Stats' || partPath.includes('Stats') || spawnCode.includes('part_stat_')) {
                            // Stats parts go to stats245
                            if (!checklistStatus.stats245.includes(partDisplay)) checklistStatus.stats245.push(partDisplay);
                        } else {
                            // Default to payload245 for all other typeId 245 parts (Payload parts)
                            if (!checklistStatus.payload245.includes(partDisplay)) checklistStatus.payload245.push(partDisplay);
                        }
                    }
                    if (typeId === 247) {
                        // Check partType to distinguish between Stats, Body, and Firmware
                        const partType = (partInfo && partInfo.partType) ? String(partInfo.partType).toLowerCase() : '';
                        const partName = (partInfo && partInfo.name) ? String(partInfo.name).toLowerCase() : '';
                        const partPath = (partInfo && partInfo.path) ? String(partInfo.path).toLowerCase() : '';
                        
                        // First check if it's a base body part (247:76-80) by part ID
                        // Helper function to extract part ID from formats like "247:76" or "76"
                        const extractPartId = (value) => {
                            if (value === null || value === undefined) return null;
                            const str = String(value);
                            if (str.includes(':')) {
                                const parts = str.split(':');
                                const partId = parseInt(parts[parts.length - 1]);
                                return !isNaN(partId) ? partId : null;
                            }
                            const num = parseInt(str);
                            return !isNaN(num) ? num : null;
                        };
                        
                        let partValue = null;
                        if (part.type === 'typed') {
                            partValue = extractPartId(part.value);
                        } else if (partInfo) {
                            partValue = extractPartId(partInfo.id) || extractPartId(partInfo.fullId);
                        }
                        const isBaseBody247 = partValue !== null && !isNaN(partValue) && partValue >= 76 && partValue <= 80;
                        
                        if (isBaseBody247) {
                            // This is a base body part (247:76-80) for enhancements
                            if (!checklistStatus.baseBody247.includes(partDisplay)) checklistStatus.baseBody247.push(partDisplay);
                        } else if (partType.includes('firmware') || partName.includes('firmware') || partPath.includes('firmware')) {
                            if (!checklistStatus.firmware247.includes(partDisplay)) checklistStatus.firmware247.push(partDisplay);
                        } else if (partType.includes('stat') || partName.includes('stat') || 
                                   partPath.includes('stats') || partPath.includes('stats2') || partPath.includes('stats3')) {
                            const spawnCode = (partInfo && partInfo.spawnCode) ? String(partInfo.spawnCode).toLowerCase() : '';
                            if (spawnCode.includes('stat3_') || partPath.includes('stat3') || partPath.includes('stats3')) {
                                if (!checklistStatus.stat3_247.includes(partDisplay)) checklistStatus.stat3_247.push(partDisplay);
                            } else if (spawnCode.includes('stat2_') || partPath.includes('stat2') || partPath.includes('stats2')) {
                                if (!checklistStatus.stat2_247.includes(partDisplay)) checklistStatus.stat2_247.push(partDisplay);
                            } else if (spawnCode.includes('stat_') || partPath.includes('stat') || partPath.includes('stats') || partType.includes('stat') || partName.includes('stat')) {
                                if (!checklistStatus.stat_247.includes(partDisplay)) checklistStatus.stat_247.push(partDisplay);
                            }
                        } else if (partType.includes('body') || partType.includes('main body') || 
                                   partName.includes('body') || partPath.includes('main body')) {
                            // Other body parts (not base body 247:76-80)
                            if (!checklistStatus.baseBody.includes(partDisplay)) checklistStatus.baseBody.push(partDisplay);
                        }
                        // If none match, don't add to any category to prevent incorrect categorization
                    }
                    if (typeId === 234) {
                        // Check partType to distinguish between Firmware and Perks
                        const partType = (partInfo && partInfo.partType) ? String(partInfo.partType).toLowerCase() : '';
                        const partName = (partInfo && partInfo.name) ? String(partInfo.name).toLowerCase() : '';
                        const partPath = (partInfo && partInfo.path) ? String(partInfo.path).toLowerCase() : '';
                        
                        // Also check spawnCode for firmware/perk patterns
                        const spawnCode = (partInfo && partInfo.spawnCode) ? String(partInfo.spawnCode).toLowerCase() : '';
                        
                        // Determine if it's Firmware or Perk based on partType, partName, partPath, or spawnCode
                        const isFirmware = partType.includes('firmware') || partName.includes('firmware') || 
                                           partPath.includes('firmware') || spawnCode.includes('firmware');
                        const isPerk = partType.includes('perk') || partName.includes('perk') || 
                                     partPath.includes('perk') || (spawnCode.includes('stat') && !spawnCode.includes('firmware'));
                        
                        // If partInfo is not available, try to determine based on part ID ranges
                        // Perk parts: 1-68, 95-102 (based on user's data)
                        // Firmware parts: 74-94 (based on user's data)
                        if (!partInfo && part.type === 'typed' && part.value) {
                            const partValue = parseInt(part.value);
                            if (!isNaN(partValue)) {
                                if (partValue >= 74 && partValue <= 94) {
                                    // Firmware range
                                    if (!checklistStatus.firmware234.includes(partDisplay)) checklistStatus.firmware234.push(partDisplay);
                                } else if ((partValue >= 1 && partValue <= 68) || (partValue >= 95 && partValue <= 102)) {
                                    // Perk range - default to stat (can't determine stat vs stat2 from ID alone)
                                    if (!checklistStatus.stat234.includes(partDisplay)) checklistStatus.stat234.push(partDisplay);
                                }
                            }
                        } else if (isFirmware) {
                            if (!checklistStatus.firmware234.includes(partDisplay)) checklistStatus.firmware234.push(partDisplay);
                        } else if (isPerk) {
                            if (spawnCode.includes('statspecial_') || spawnCode.includes('ClassMod.statspecial')) {
                                if (!checklistStatus.statspecial_234.includes(partDisplay)) checklistStatus.statspecial_234.push(partDisplay);
                            } else if (spawnCode.includes('stat2_') || spawnCode.includes('ClassMod.stat2')) {
                                if (!checklistStatus.stat2_234.includes(partDisplay)) checklistStatus.stat2_234.push(partDisplay);
                            } else if (spawnCode.includes('stat_') || spawnCode.includes('ClassMod.stat') || spawnCode.includes('stat')) {
                                if (!checklistStatus.stat234.includes(partDisplay)) checklistStatus.stat234.push(partDisplay);
                            } else {
                                // Fallback: if it's a perk but can't determine, default to stat
                                if (!checklistStatus.stat234.includes(partDisplay)) checklistStatus.stat234.push(partDisplay);
                            }
                        } else if (partInfo) {
                            // If we have partInfo but can't determine, check spawnCode pattern
                            // Perk parts typically have spawn_code like "ClassMod.stat_*" or "ClassMod.stat2_*" or "ClassMod.statspecial_*"
                            // Firmware parts typically have spawn_code like "ClassMod.part_firmware_*"
                            if (spawnCode.includes('part_firmware')) {
                                if (!checklistStatus.firmware234.includes(partDisplay)) checklistStatus.firmware234.push(partDisplay);
                            } else if (spawnCode.includes('statspecial_') || spawnCode.includes('ClassMod.statspecial')) {
                                if (!checklistStatus.statspecial_234.includes(partDisplay)) checklistStatus.statspecial_234.push(partDisplay);
                            } else if (spawnCode.includes('stat2_') || spawnCode.includes('ClassMod.stat2')) {
                                if (!checklistStatus.stat2_234.includes(partDisplay)) checklistStatus.stat2_234.push(partDisplay);
                            } else if (spawnCode.includes('stat') || spawnCode.includes('ClassMod.stat')) {
                                if (!checklistStatus.stat234.includes(partDisplay)) checklistStatus.stat234.push(partDisplay);
                            }
                        }
                    }
                    if (typeId === 246) {
                        // Check partType to distinguish between Firmware, Resistance, and Perks
                        const partType = (partInfo && partInfo.partType) ? String(partInfo.partType).toLowerCase() : '';
                        const partName = (partInfo && partInfo.name) ? String(partInfo.name).toLowerCase() : '';
                        const partPath = (partInfo && partInfo.path) ? String(partInfo.path).toLowerCase() : '';
                        const spawnCode = (partInfo && partInfo.spawnCode) ? String(partInfo.spawnCode).toLowerCase() : '';
                        
                        // Extract part ID to check if it's a resistance part (246:21-246:26)
                        let partIdNum = null;
                        const partIdStr = String(part.value || '');
                        if (partIdStr && !isNaN(parseInt(partIdStr))) {
                            partIdNum = parseInt(partIdStr);
                        }
                        
                        // Check if it's a resistance part (IDs 21-26)
                        const isResistance = partIdNum !== null && partIdNum >= 21 && partIdNum <= 26;
                        
                        if (partType.includes('firmware') || partName.includes('firmware') || partPath.includes('firmware')) {
                            if (!checklistStatus.firmware246.includes(partDisplay)) checklistStatus.firmware246.push(partDisplay);
                        } else if (isResistance || spawnCode.includes('part_corrosive') || spawnCode.includes('part_cryo') || 
                                   spawnCode.includes('part_fire') || spawnCode.includes('part_radiation') || spawnCode.includes('part_shock') ||
                                   partName.includes('resist') || partType.includes('resist')) {
                            // Resistance parts (246:21-246:26)
                            if (!checklistStatus.resistance246.includes(partDisplay)) checklistStatus.resistance246.push(partDisplay);
                        } else if (partType.includes('perk') || partName.includes('perk') || partPath.includes('perk')) {
                            if (spawnCode.includes('_primary') || partPath.includes('primary') || partName.includes('primary')) {
                                if (!checklistStatus.primaryPerks246.includes(partDisplay)) checklistStatus.primaryPerks246.push(partDisplay);
                            } else if (spawnCode.includes('_secondary') || partPath.includes('secondary') || partName.includes('secondary')) {
                                if (!checklistStatus.secondaryPerks246.includes(partDisplay)) checklistStatus.secondaryPerks246.push(partDisplay);
                            } else {
                                // If we can't determine, default to primary (fallback)
                                if (!checklistStatus.primaryPerks246.includes(partDisplay)) checklistStatus.primaryPerks246.push(partDisplay);
                            }
                        } else {
                            // If we can't determine, don't add to either to prevent incorrect categorization
                        }
                    }
                    if (typeId === 237 && !checklistStatus.armor237.includes(partDisplay)) checklistStatus.armor237.push(partDisplay);
                    if (typeId === 248 && !checklistStatus.energy248.includes(partDisplay)) checklistStatus.energy248.push(partDisplay);
                    // Skills: Only typeId 254 and 255 are skills
                    if (typeId === 254 || typeId === 255) {
                        if (!checklistStatus.skills.includes(partDisplay)) checklistStatus.skills.push(partDisplay);
                    }
                    // Licensed Parts detection - check for ANY typeId that has "licensed" in spawn_code (not just typeId 13)
                    // Licensed parts can be typeId 9, 13, or other typeIds
                    // EXCLUDE typeId 1 elements (they go to element or maliwanLicensedUnderbarrel, not licensedParts)
                    // EXCLUDE Maliwan Licensed Underbarrel parts (they go to maliwanLicensedUnderbarrel, not licensedParts)
                    if (isWeapon && partInfo && typeId !== 1) {
                        const spawnCode = String(partInfo.spawnCode || '').toLowerCase();
                        const partPath = String(partInfo.path || '').toLowerCase();
                        const partName = String(partInfo.name || '').toLowerCase();
                        const partType = String(partInfo.partType || '').toLowerCase();
                        const partCategory = String(partInfo.category || '').toLowerCase();
                        
                        // Exclude Maliwan Licensed Underbarrel parts - they should go to maliwanLicensedUnderbarrel, not licensedParts
                        const isMaliwanLicensedUnderbarrel = spawnCode.includes('part_secondary_elem') || 
                                                             partPath.includes('licensed_underbarrel') ||
                                                             partCategory.includes('maliwan licensed');
                        
                        // Check if it's a licensed part (spawn code contains "licensed" or path/name indicates licensed)
                        // But exclude Maliwan Licensed Underbarrel parts
                        // Also include ALL parts from "Manufacturer Part" part_type (even if spawn code doesn't contain "licensed")
                        const originalPartType = String(partInfo.partType || '');
                        const originalPartPath = String(partInfo.path || '');
                        const isLicensed = !isMaliwanLicensedUnderbarrel && (
                                         spawnCode.includes('licensed') || 
                                         spawnCode.includes('_licensed_') ||
                                         partPath.includes('licensed') ||
                                         partName.includes('licensed') ||
                                         partType === 'manufacturer part' ||
                                         originalPartType === 'Manufacturer Part' ||
                                         originalPartPath.includes('Manufacturer Part') ||
                                         (partType === 'manufacturer part' && (spawnCode.includes('_licensed_') || spawnCode.includes('.licensed')))
                        );
                        
                        if (isLicensed) {
                            if (!checklistStatus.licensedParts.includes(partDisplay)) {
                                checklistStatus.licensedParts.push(partDisplay);
                            }
                        }
                    }
                }
                
                // Process partInfo if it exists - this handles both simple and typed parts
                // Also handle simple parts even if partInfo is missing (fallback categorization)
                if (partInfo || part.type === 'simple') {
                    const partType = partInfo ? String(partInfo.partType || '') : '';
                    const partTypeLower = partType.toLowerCase();
                    const partName = partInfo ? String(partInfo.name || '').toLowerCase() : '';
                    const partId = partInfo ? String(partInfo.id || '') : String(part.value || '');
                    const fullId = partInfo ? String(partInfo.fullId || '') : '';
                    const spawnCode = partInfo ? String(partInfo.spawnCode || '').toLowerCase() : '';
                    const partStats = partInfo ? String(partInfo.stats || '').toLowerCase() : '';
                    const partEffects = partInfo ? String(partInfo.effects || '').toLowerCase() : '';
                    
                    // Check for specific part types by partType field (works for both simple and typed parts)
                    // Repkit Base detection (partType === "Base" or path includes "Base")
                    // For grenades, Base should go to body, not baseBody
                    const partPath = partInfo ? String(partInfo.path || '').toLowerCase() : '';
                    
                    // Enhanced categorization: try multiple strategies to identify part type
                    // Strategy 1: Check partType field (most reliable)
                    // Strategy 2: Check path field
                    // Strategy 3: Check name field
                    // Strategy 4: Check spawnCode field
                    // Strategy 5: For simple parts without partInfo, try to infer from context
                    const isGrenadeType = currentTypeId >= 263 && currentTypeId <= 311 && 
                                         (currentTypeId === 245 || currentTypeId === 263 || currentTypeId === 267 || 
                                          currentTypeId === 270 || currentTypeId === 272 || currentTypeId === 278 || 
                                          currentTypeId === 291 || currentTypeId === 298 || currentTypeId === 311);
                    if (partTypeLower === 'base' || partPath === 'base' || partPath.includes('base')) {
                        if (isGrenadeType) {
                            // For grenades, Base goes to body
                            if (!checklistStatus.body.includes(partDisplay)) checklistStatus.body.push(partDisplay);
                        } else {
                            // For repkits, Base goes to baseBody
                            if (!checklistStatus.baseBody.includes(partDisplay)) checklistStatus.baseBody.push(partDisplay);
                        }
                    }
                    // Repkit Augment detection (partType === "Augment" or path includes "Augment") - these should be considered as bodies (same as Base)
                    if (partTypeLower === 'augment' || partPath === 'augment') {
                        if (isRepkit) {
                            // For repkits, Augment parts go to baseBody (same as Base parts)
                            if (!checklistStatus.baseBody.includes(partDisplay)) checklistStatus.baseBody.push(partDisplay);
                        } else {
                            // For other item types, Augment parts are legendary parts
                            if (!checklistStatus.legendaryPart.includes(partDisplay)) checklistStatus.legendaryPart.push(partDisplay);
                        }
                    }
                    // Shield body parts detection - CHECK BEFORE GENERAL BODY DETECTION
                    // For shields, Base Body and Legendary Part are one and the same
                    // Match when:
                    // 1. It's a shield item (isShield is true)
                    // 2. The part's typeId matches the current shield's typeId
                    // 3. AND (partType is "shield" OR spawnCode includes "part_body" OR path includes "shield")
                    let isShieldBodyPart = false;
                    if (partInfo && isShield) {
                        const partTypeId = partInfo.typeId || (part.type === 'typed' ? part.typeId : null);
                        const originalPartType = String(partInfo.partType || '');
                        const partPathOriginal = String(partInfo.path || '');
                        const originalPartTypeLower = originalPartType.toLowerCase();
                        const partPathOriginalLower = partPathOriginal.toLowerCase();
                        
                        // Check if it's a shield body part
                        isShieldBodyPart = Number(partTypeId) === Number(currentTypeId) && 
                                          (partType === 'shield' || partTypeLower === 'shield' ||
                                           spawnCode.includes('part_body') || 
                                           partPath.includes('shield') || partPathOriginalLower.includes('shield') ||
                                           originalPartType === 'Shield' || originalPartTypeLower === 'shield');
                        
                        if (isShieldBodyPart) {
                            // This is a shield body part - add to baseBody and legendaryPart
                            if (!checklistStatus.baseBody.includes(partDisplay)) {
                                checklistStatus.baseBody.push(partDisplay);
                            }
                            if (!checklistStatus.legendaryPart.includes(partDisplay)) {
                                checklistStatus.legendaryPart.push(partDisplay);
                            }
                        }
                    }
                    // Body detection - check multiple fields (prioritize descriptive fields)
                    // Skip if already identified as shield body part
                    if (!isShieldBodyPart) {
                    const isBody = (partStats.includes('body') && !partStats.includes('accessory') && !partStats.includes('base')) ||
                                  (partEffects.includes('body') && !partEffects.includes('accessory') && !partEffects.includes('base')) ||
                                  partName.includes('body') && !partName.includes('accessory') && !partName.includes('base') ||
                                  partTypeLower === 'body' || 
                                  (partTypeLower.includes('body') && !partTypeLower.includes('accessory') && !partTypeLower.includes('base')) ||
                                  (partPath.includes('body') && !partPath.includes('accessory') && !partPath.includes('base'));
                    if (isBody) {
                        if (!checklistStatus.body.includes(partDisplay)) checklistStatus.body.push(partDisplay);
                        if (!checklistStatus.baseBody.includes(partDisplay)) checklistStatus.baseBody.push(partDisplay);
                        }
                    }
                    // Body Accessory detection
                    // Check for typeId 4 (body accessories)
                    const isTypeId4 = partInfo && (partInfo.typeId === 4 || (part.type === 'typed' && part.typeId === 4));
                    // Check for Daedalus ammo switcher body parts (spawnCode includes "part_body_mag" or "part_body_a/b/c/d" for Daedalus)
                    const isDaedalusAmmoSwitcherBody = spawnCode.includes('part_body_mag') || 
                                                       (spawnCode.includes('part_body_') && (spawnCode.includes('dad_') || spawnCode.includes('daedalus'))) ||
                                                       (partTypeLower === 'manufacturer part' && spawnCode.includes('part_body_') && 
                                                        (spawnCode.includes('mag_') || spawnCode.includes('ammo')));
                    const isBodyAccessory = isTypeId4 || isDaedalusAmmoSwitcherBody ||
                                           (partStats.includes('body') && partStats.includes('accessory')) ||
                                           (partEffects.includes('body') && partEffects.includes('accessory')) ||
                                           partTypeLower === 'body accessory' || 
                                           (partTypeLower.includes('body') && partTypeLower.includes('accessory')) ||
                                           (partPath.includes('body') && partPath.includes('accessory')) ||
                                           (partName.includes('body') && partName.includes('accessory'));
                    if (isBodyAccessory) {
                        if (!checklistStatus.bodyAccessories.includes(partDisplay)) checklistStatus.bodyAccessories.push(partDisplay);
                    }
                    // Check if it's explicitly a barrel first (to prevent barrels from being misclassified as underbarrel)
                    const isExplicitlyBarrel = partTypeLower === 'barrel' || 
                                              spawnCode.includes('part_barrel') ||
                                              (partStats.includes('barrel') && !partStats.includes('underbarrel') && !partStats.includes('accessory')) ||
                                              (partEffects.includes('barrel') && !partEffects.includes('underbarrel') && !partEffects.includes('accessory'));
                    
                    // Underbarrel detection (check FIRST - most specific, before barrel)
                    // But exclude if it's explicitly a barrel
                    const isUnderbarrel = !isExplicitlyBarrel && (
                                        partStats.includes('underbarrel') ||
                                        partEffects.includes('underbarrel') ||
                                        spawnCode.includes('part_underbarrel') ||
                                        partTypeLower === 'underbarrel' || 
                                        partTypeLower === 'underbarrel accessory' ||
                                        (partTypeLower.includes('underbarrel') && !partTypeLower.includes('barrel')) ||
                                        (partPath.includes('underbarrel') && !partPath.includes('barrel')) ||
                                        (partName.includes('underbarrel') && !partName.includes('barrel'))
                    );
                    if (isUnderbarrel) {
                        if (!checklistStatus.underbarrel.includes(partDisplay)) checklistStatus.underbarrel.push(partDisplay);
                    }
                    // Daedalus Ammo Type detection - identified by spawnCode pattern or by part ID when Ammo Switch is present
                    // Can be any typeId with spawnCode containing part_secondary_ammo_sg/smg/ar/ps
                    // Or simple parts {62}, {63}, {64}, {65} when Daedalus Ammo Switch ({46} or {53}) is present
                    if (partInfo) {
                        const spawnCode = String(partInfo.spawnCode || '').toLowerCase();
                        const isDaedalusAmmo = spawnCode.includes('part_secondary_ammo_sg') ||
                                              spawnCode.includes('part_secondary_ammo_smg') ||
                                              spawnCode.includes('part_secondary_ammo_ar') ||
                                              spawnCode.includes('part_secondary_ammo_ps');
                        if (isDaedalusAmmo) {
                            if (!checklistStatus.daedalusAmmo.includes(partDisplay)) checklistStatus.daedalusAmmo.push(partDisplay);
                        }
                    } else if (part.type === 'simple' && hasDaedalusAmmoSwitch) {
                        // Simple parts {62}, {63}, {64}, {65} are Daedalus ammo when Ammo Switch ({46} or {53}) is present
                        // (fallback for parts without partInfo)
                        const ammoId = part.value;
                        if (ammoId === 62 || ammoId === 63 || ammoId === 64 || ammoId === 65) {
                            if (!checklistStatus.daedalusAmmo.includes(partDisplay)) checklistStatus.daedalusAmmo.push(partDisplay);
                        }
                    }
                    // Maliwan Licensed Underbarrel detection - identified by spawnCode pattern when Element Switch is present
                    // TypeId 1 parts with spawnCode containing part_secondary_elem or path containing licensed_underbarrel
                    if (partInfo && hasMaliwanElementSwitch) {
                        const spawnCode = String(partInfo.spawnCode || '').toLowerCase();
                        const partPath = String(partInfo.path || '').toLowerCase();
                        const partCategory = String(partInfo.category || '').toLowerCase();
                        const isMaliwanLicensedUnderbarrel = spawnCode.includes('part_secondary_elem') || 
                                                              partPath.includes('licensed_underbarrel') ||
                                                              partCategory.includes('maliwan licensed');
                        if (isMaliwanLicensedUnderbarrel) {
                            if (!checklistStatus.maliwanLicensedUnderbarrel.includes(partDisplay)) {
                                checklistStatus.maliwanLicensedUnderbarrel.push(partDisplay);
                            }
                        }
                    }
                    // Licensed Parts detection (for simple parts and parts processed via partInfo)
                    // EXCLUDE typeId 1 elements (they go to element or maliwanLicensedUnderbarrel, not licensedParts)
                    // EXCLUDE Maliwan Licensed Underbarrel parts (they go to maliwanLicensedUnderbarrel, not licensedParts)
                    if (isWeapon && partInfo) {
                        const partTypeId = partInfo.typeId || (part.type === 'typed' ? part.typeId : null);
                        const partCategory = String(partInfo.category || '').toLowerCase();
                        
                        // Exclude typeId 1 elements and Maliwan Licensed Underbarrel parts
                        const isTypeId1 = partTypeId === 1;
                        const isMaliwanLicensedUnderbarrel = spawnCode.includes('part_secondary_elem') || 
                                                             partPath.includes('licensed_underbarrel') ||
                                                             partCategory.includes('maliwan licensed');
                        
                        if (!isTypeId1 && !isMaliwanLicensedUnderbarrel) {
                            // Check if it's a licensed part (spawn code contains "licensed" or path/name indicates licensed)
                            // Also include ALL parts from "Manufacturer Part" part_type (even if spawn code doesn't contain "licensed")
                            const originalPartType = String(partInfo.partType || '');
                            const originalPartPath = String(partInfo.path || '');
                            const isLicensed = spawnCode.includes('licensed') || 
                                             spawnCode.includes('_licensed_') ||
                                             partPath.includes('licensed') ||
                                             partName.includes('licensed') ||
                                             partTypeLower === 'manufacturer part' ||
                                             originalPartType === 'Manufacturer Part' ||
                                             originalPartPath.includes('Manufacturer Part') ||
                                             (partTypeLower === 'manufacturer part' && (spawnCode.includes('_licensed_') || spawnCode.includes('.licensed')));
                            
                            if (isLicensed) {
                                if (!checklistStatus.licensedParts.includes(partDisplay)) {
                                    checklistStatus.licensedParts.push(partDisplay);
                                }
                            }
                        }
                    }
                    // Barrel Accessory detection (check SECOND - more specific than barrel)
                    const isBarrelAccessory = (partStats.includes('barrel') && partStats.includes('accessory')) ||
                                             (partEffects.includes('barrel') && partEffects.includes('accessory')) ||
                                             partTypeLower === 'barrel accessory' || 
                                             (partTypeLower.includes('barrel') && partTypeLower.includes('accessory')) ||
                                             (partPath.includes('barrel') && partPath.includes('accessory')) ||
                                             (partName.includes('barrel') && partName.includes('accessory'));
                    if (isBarrelAccessory) {
                        if (!checklistStatus.barrelAccessories.includes(partDisplay)) checklistStatus.barrelAccessories.push(partDisplay);
                    }
                    // Barrel detection - check multiple fields for better accuracy
                    // Priority: Check descriptive fields (stats, effects, name) first, then partType
                    // This handles cases where partType might say "Legendary Perks" but stats says "Barrel part"
                    // EXCLUDE if already matched as Underbarrel or Barrel Accessory (more specific categories)
                    // Also check for explicit barrel indicators (partType === 'barrel' or spawnCode includes 'part_barrel')
                    const isBarrel = !isUnderbarrel && !isBarrelAccessory && (
                                   isExplicitlyBarrel ||
                                   (partStats.includes('barrel') && !partStats.includes('accessory') && !partStats.includes('underbarrel')) ||
                                   (partEffects.includes('barrel') && !partEffects.includes('accessory') && !partEffects.includes('underbarrel')) ||
                                   (partName.includes('barrel') && !partName.includes('accessory') && !partName.includes('underbarrel')) ||
                                   (partTypeLower.includes('barrel') && !partTypeLower.includes('accessory') && !partTypeLower.includes('underbarrel')) ||
                                   (partPath.includes('barrel') && !partPath.includes('accessory') && !partPath.includes('underbarrel')) ||
                                   (spawnCode.includes('part_barrel') && !spawnCode.includes('accessory') && !spawnCode.includes('underbarrel'))
                    );
                    if (isBarrel) {
                        if (!checklistStatus.barrel.includes(partDisplay)) checklistStatus.barrel.push(partDisplay);
                    }
                    // Magazine detection
                    const isMagazine = partStats.includes('magazine') ||
                                      partEffects.includes('magazine') ||
                                      partTypeLower === 'magazine' || 
                                      (partTypeLower.includes('magazine') && !partTypeLower.includes('accessory')) ||
                                      (partPath.includes('magazine') && !partPath.includes('accessory')) ||
                                      (partName.includes('magazine') && !partName.includes('accessory'));
                    if (isMagazine) {
                        if (!checklistStatus.magazine.includes(partDisplay)) checklistStatus.magazine.push(partDisplay);
                    }
                    // Scope detection
                    const isScope = partStats.includes('scope') && !partStats.includes('accessory') ||
                                   partEffects.includes('scope') && !partEffects.includes('accessory') ||
                                   partTypeLower === 'scope' || 
                                   (partTypeLower.includes('scope') && !partTypeLower.includes('accessory')) ||
                                   (partPath.includes('scope') && !partPath.includes('accessory')) ||
                                   (partName.includes('scope') && !partName.includes('accessory'));
                    if (isScope) {
                        if (!checklistStatus.scope.includes(partDisplay)) checklistStatus.scope.push(partDisplay);
                    }
                    // Scope Accessory detection
                    const isScopeAccessory = (partStats.includes('scope') && partStats.includes('accessory')) ||
                                           (partEffects.includes('scope') && partEffects.includes('accessory')) ||
                                           partTypeLower === 'scope accessory' || 
                                           (partTypeLower.includes('scope') && partTypeLower.includes('accessory')) ||
                                           (partPath.includes('scope') && partPath.includes('accessory')) ||
                                           (partName.includes('scope') && partName.includes('accessory'));
                    if (isScopeAccessory) {
                        if (!checklistStatus.scopeAccessory.includes(partDisplay)) checklistStatus.scopeAccessory.push(partDisplay);
                    }
                    // Foregrip detection (check FIRST - more specific than grip)
                    const isForegrip = partStats.includes('foregrip') ||
                                      partEffects.includes('foregrip') ||
                                      spawnCode.includes('foregrip') ||
                                      partTypeLower === 'foregrip' || 
                                      partTypeLower.includes('foregrip') ||
                                      partPath.includes('foregrip') ||
                                      partName.includes('foregrip');
                    if (isForegrip) {
                        if (!checklistStatus.foregrip.includes(partDisplay)) checklistStatus.foregrip.push(partDisplay);
                    }
                    // Grip detection (exclude if already matched as foregrip)
                    // Also exclude if part name/path/stats contains "foregrip" (more specific)
                    const isGrip = !isForegrip && (
                                  (partStats.includes('grip') && !partStats.includes('foregrip')) ||
                                  (partEffects.includes('grip') && !partEffects.includes('foregrip')) ||
                                  (spawnCode.includes('grip') && !spawnCode.includes('foregrip')) ||
                                  (partTypeLower === 'grip' && !partTypeLower.includes('foregrip')) || 
                                  (partTypeLower.includes('grip') && !partTypeLower.includes('foregrip')) ||
                                  (partPath.includes('grip') && !partPath.includes('foregrip')) ||
                                  (partName.includes('grip') && !partName.includes('foregrip'))
                    );
                    if (isGrip) {
                        // Double-check: don't add to grip if already in foregrip (safety check)
                        if (!checklistStatus.foregrip.includes(partDisplay) && !checklistStatus.grip.includes(partDisplay)) {
                            checklistStatus.grip.push(partDisplay);
                        }
                    }
                    // Stat Modifier detection
                    const isStatModifier = (partStats.includes('stat') && partStats.includes('modifier')) ||
                                         (partEffects.includes('stat') && partEffects.includes('modifier')) ||
                                         partTypeLower === 'stat modifier' || 
                                         partTypeLower.includes('stat modifier') || 
                                         (partTypeLower.includes('stat') && partTypeLower.includes('modifier')) ||
                                         (partPath.includes('stat') && partPath.includes('modifier')) ||
                                         (partName.includes('stat') && partName.includes('modifier'));
                    if (isStatModifier) {
                        if (!checklistStatus.statModifier.includes(partDisplay)) checklistStatus.statModifier.push(partDisplay);
                    }
                    // Rarity detection
                    // Handle both "Rarity" and "Rarities" (plural) - grenades use "Rarities"
                    if (partTypeLower.includes('rarity') || partTypeLower.includes('rarities') || 
                        partName.includes('rarity') || partName.includes('rarities') || 
                        partTypeLower === 'rarity' || partTypeLower === 'rarities' || 
                        partTypeLower === 'comp' || partTypeLower.includes('comp') ||
                        partPath.includes('rarity') || partPath.includes('rarities')) {
                        if (!checklistStatus.rarity.includes(partDisplay)) checklistStatus.rarity.push(partDisplay);
                    }
                    // Check for Manufacturer Perks
                    const isManufacturerPerk = isEnhancementTypeId(currentTypeId) && 
                        (partTypeLower === 'manufacturer perk' || 
                         (part.type === 'simple' && (part.value === 1 || part.value === 2 || part.value === 3 || part.value === 9)) ||
                         (part.type === 'typed' && part.typeId === currentTypeId && (part.value === 1 || part.value === 2 || part.value === 3 || part.value === 9)));
                    
                    if (isManufacturerPerk) {
                        if (!checklistStatus.legendaryPerks.includes(partDisplay)) checklistStatus.legendaryPerks.push(partDisplay);
                    } else if (partTypeLower.includes('legendary') || partName.includes('legendary')) {
                        if (!checklistStatus.legendaryPart.includes(partDisplay)) checklistStatus.legendaryPart.push(partDisplay);
                    }
                    // Skills detection: Only categorize as skill if it's actually a skill part
                    // IMPORTANT: TypeId 254 or 255 does NOT automatically mean it's a skill!
                    // TypeId 255 can be Legendary Body parts, and typeId 254 can be other things too
                    // We must check the actual type/partType field to determine if it's really a skill
                    let isSkill = false;
                    
                    // FIRST: Check if this part was already categorized as Body (by path or other indicators)
                    // If it's a Body part, it should NOT be a Skill, regardless of partType or typeId
                    const pathLower = partPath.toLowerCase();
                    const isBodyPath = pathLower.includes('body') && !pathLower.includes('accessory') && !pathLower.includes('skill');
                    const alreadyBody = checklistStatus.body.includes(partDisplay) || isBodyPath;
                    
                    // Check the actual type field from partInfo (more reliable than typeId alone)
                    const partTypeField = partInfo ? String(partInfo.type || '').toLowerCase() : '';
                    const isLegendaryBody = partTypeField.includes('legendary body') || partTypeField === 'legendary body';
                    const isBodyType = partTypeField.includes('body') && !partTypeField.includes('accessory');
                    
                    if (part.type === 'typed') {
                        // Typed parts: Check if typeId is 254 or 255 AND it's actually a skill type
                        // Exclude if it's already categorized as Body or is a Legendary Body type
                        if ((part.typeId === 254 || part.typeId === 255) && !alreadyBody && !isLegendaryBody && !isBodyType) {
                            // Additional check: verify it's actually a skill by checking type field
                            const isSkillType = partTypeField === 'skill' || partTypeField.includes('skill');
                            const hasSkillName = partInfo && partInfo.skillName && String(partInfo.skillName).trim() !== '';
                            isSkill = isSkillType || hasSkillName;
                        }
                    } else if (part.type === 'simple' && partInfo) {
                        // Simple parts: check if partInfo explicitly indicates it's a skill
                        // For class mods, skills are simple parts that have skillName or partType === "Skill"
                        // But we must exclude body, rarity, and other non-skill parts
                        
                        // If it's already categorized as Body (by path or type), don't categorize as skill
                        if (alreadyBody || isBodyPath || isLegendaryBody || isBodyType) {
                            isSkill = false;
                        } else {
                            // Only check for skill indicators if it's not a body part by path or type
                            const hasSkillName = partInfo.skillName && String(partInfo.skillName).trim() !== '';
                            const isSkillPartType = partTypeLower === 'skill';
                            const isSkillTypeField = partTypeField === 'skill' || partTypeField.includes('skill');
                            
                            // Exclude if it's clearly a body, rarity, or other non-skill part
                            const isBody = partTypeLower.includes('body') || partName.includes('body');
                            const isRarity = partTypeLower.includes('rarity') || partTypeLower === 'comp' || 
                                            partName.includes('rarity') || partName.includes('common') || 
                                            partName.includes('uncommon') || partName.includes('rare') || 
                                            partName.includes('epic') || partName.includes('legendary');
                            const isPerk = partTypeLower.includes('perk') || partName.includes('perk');
                            
                            // For class mods, Body parts are in the "Body" section, Skills are in the "Skills" section
                            // Only categorize as skill if it has skill indicators AND is not a body/rarity/perk
                            isSkill = (hasSkillName || isSkillPartType || isSkillTypeField) && !isBody && !isRarity && !isPerk;
                        }
                    }
                    
                    if (isSkill) {
                        if (!checklistStatus.skills.includes(partDisplay)) checklistStatus.skills.push(partDisplay);
                    }
                }
                
                // Check for typed parts with specific typeIds (only when partInfo exists)
                if (partInfo && (part.type === 'typed' || part.type === 'array')) {
                    const fullId = String(partInfo.fullId || '');
                    const typeId = part.typeId || (fullId.includes(':') ? parseInt(fullId.split(':')[0]) : null);
                    if (typeId === 247) {
                        // Check partType to distinguish between Stats, Body, and Firmware
                        const partType = (partInfo && partInfo.partType) ? String(partInfo.partType).toLowerCase() : '';
                        const partName = (partInfo && partInfo.name) ? String(partInfo.name).toLowerCase() : '';
                        const partPath = (partInfo && partInfo.path) ? String(partInfo.path).toLowerCase() : '';
                        
                        if (partType.includes('firmware') || partName.includes('firmware') || partPath.includes('firmware')) {
                            if (!checklistStatus.firmware247.includes(partDisplay)) checklistStatus.firmware247.push(partDisplay);
                        } else if (partType.includes('body') || partType.includes('main body') || 
                                   partName.includes('body') || partPath.includes('main body')) {
                            if (!checklistStatus.baseBody.includes(partDisplay)) checklistStatus.baseBody.push(partDisplay);
                        } else if (partType.includes('stat') || partName.includes('stat') || 
                                   partPath.includes('stats') || partPath.includes('stats2') || partPath.includes('stats3')) {
                            const spawnCode = (partInfo && partInfo.spawnCode) ? String(partInfo.spawnCode).toLowerCase() : '';
                            if (spawnCode.includes('stat3_') || partPath.includes('stat3') || partPath.includes('stats3')) {
                                if (!checklistStatus.stat3_247.includes(partDisplay)) checklistStatus.stat3_247.push(partDisplay);
                            } else if (spawnCode.includes('stat2_') || partPath.includes('stat2') || partPath.includes('stats2')) {
                                if (!checklistStatus.stat2_247.includes(partDisplay)) checklistStatus.stat2_247.push(partDisplay);
                            } else if (spawnCode.includes('stat_') || partPath.includes('stat') || partPath.includes('stats') || partType.includes('stat') || partName.includes('stat')) {
                                if (!checklistStatus.stat_247.includes(partDisplay)) checklistStatus.stat_247.push(partDisplay);
                            }
                        }
                    }
                }
            };
            
            // Analyze each part (only if we have parts)
            for (let i = 0; i < (currentParts.length || 0); i++) {
                const part = currentParts[i];
                
                // Handle array parts by expanding them into individual typed parts
                if (part.type === 'array' && part.values && Array.isArray(part.values)) {
                    // Process each value in the array as an individual typed part
                    for (let arrayIndex = 0; arrayIndex < part.values.length; arrayIndex++) {
                        const arrayValue = part.values[arrayIndex];
                        // Create a virtual typed part for this array value
                        const virtualPart = {
                            type: 'typed',
                            typeId: part.typeId,
                            value: arrayValue
                        };
                        const virtualPartDisplay = `{${part.typeId}:${arrayValue}}`;
                        let virtualPartInfo = getPartInfo(virtualPart, i);
                        
                        // Try to find part info using the part's own typeId
                        if (!virtualPartInfo) {
                            const partTypeId = virtualPart.typeId;
                            const partId = String(arrayValue);
                            const fullId = `${partTypeId}:${partId}`;
                            
                            // First try fullId lookup (most specific)
                            virtualPartInfo = partsMap.get(fullId);
                            // Verify typeId matches if found
                            if (virtualPartInfo && virtualPartInfo.typeId !== partTypeId) {
                                virtualPartInfo = null;
                            }
                            
                            // If not found, search within this typeId's parts only
                            if (!virtualPartInfo) {
                                const typeParts = partsByTypeId.get(partTypeId) || [];
                                for (const info of typeParts) {
                                    const infoId = String(info.id);
                                    const infoFullId = String(info.fullId || '');
                                    
                                    // Match if:
                                    // 1. fullId exactly matches (e.g., "234:1")
                                    // 2. fullId ends with :partId and starts with typeId: (e.g., "234:1" for partId "1")
                                    // 3. id matches AND typeId matches (for parts where id is just the number)
                                    const fullIdMatches = infoFullId === fullId;
                                    const fullIdEndsWithPartId = infoFullId.includes(':') && 
                                                                infoFullId.startsWith(`${partTypeId}:`) && 
                                                                infoFullId.split(':')[1] === partId;
                                    const idMatches = infoId === partId && info.typeId === partTypeId;
                                    const idIsFullId = infoId === fullId;
                                    
                                    if (fullIdMatches || fullIdEndsWithPartId || idMatches || idIsFullId) {
                                        virtualPartInfo = info;
                                        break;
                                    }
                                }
                            }
                            
                            // Last resort: try numeric lookup BUT verify typeId matches
                            if (!virtualPartInfo) {
                                const numericPartId = parseInt(partId);
                                if (!isNaN(numericPartId)) {
                                    const candidate = partsMap.get(numericPartId);
                                    // Only use if typeId matches
                                    if (candidate && candidate.typeId === partTypeId) {
                                        virtualPartInfo = candidate;
                                    }
                                }
                            }
                        }
                        
                        // Process this individual part through the categorization logic
                        processPartForChecklist(virtualPart, virtualPartInfo, virtualPartDisplay, checklistStatus, isWeapon, isShield, hasMaliwanElementSwitch);
                    }
                    // Skip processing the array part itself - we've already processed each value
                    continue;
                }
                
                let partInfo = getPartInfo(part, i); // Pass index for rarity detection
                const partDisplay = formatPartDisplay(part, i);
                
                // Check for Maliwan Element Switch immediately after getting partInfo
                if (!hasMaliwanElementSwitch && isWeapon) {
                    if (part.type === 'typed' && part.typeId === 13 && part.value === 60) {
                        hasMaliwanElementSwitch = true;
                        console.log('[DEBUG] Detected Maliwan Element Switch from typed part {13:60}');
                    } else if (part.type === 'simple' && part.value === 60 && partInfo) {
                        const spawnCode = String(partInfo.spawnCode || '').toLowerCase();
                        const partName = String(partInfo.name || '').toLowerCase();
                        const partType = String(partInfo.partType || '').toLowerCase();
                        // Check if it's the Element Switch
                        if (spawnCode.includes('element_switch') || 
                            partName.includes('element switch') || 
                            partName.includes('maliwan element') ||
                            (partType === 'underbarrel' && (partName.includes('maliwan') || spawnCode.includes('maliwan')))) {
                            hasMaliwanElementSwitch = true;
                            console.log('[DEBUG] Detected Maliwan Element Switch from simple part {60} with partInfo:', partInfo.name);
                        }
                    }
                }
                
                // Debug log for first few parts
                if (i < 5) {
                    console.log(`Part ${i}:`, part, 'partInfo:', partInfo, 'partDisplay:', partDisplay);
                    if (partInfo) {
                        console.log(`  Part ${i} partType:`, partInfo.partType, 'name:', partInfo.name);
                    }
                }
                
                // Try to find part info again using the part's own typeId for typed parts
                if (!partInfo && part.type === 'typed') {
                    const partTypeId = part.typeId;
                    const partId = String(part.value);
                    const fullId = `${partTypeId}:${partId}`;
                    // Try lookup with the part's own typeId
                    partInfo = partsMap.get(fullId) || partsMap.get(partId) || partsMap.get(parseInt(partId));
                    // Also try in partsByTypeId
                    if (!partInfo) {
                        const typeParts = partsByTypeId.get(partTypeId) || [];
                        for (const info of typeParts) {
                            const infoId = String(info.id);
                            const infoFullId = String(info.fullId || '');
                            if (infoId === partId || infoFullId === fullId || 
                                (infoFullId.includes(':') && infoFullId.split(':')[1] === partId)) {
                                partInfo = info;
                                break;
                            }
                        }
                    }
                }
                
                // IMPORTANT: Check weapon parts by typeId BEFORE checking partInfo
                // This is a fallback when parts aren't in the map but we still want to detect them
                // Common weapon part typeIds based on typical weapon structure:
                // typeId 14 = Body parts
                // typeId 23 = Barrel parts  
                // typeId 4 = Body Accessories
                // typeId 17 = Barrel Accessories
                // typeId 6 = Rarity (sometimes)
                if (!partInfo && isWeapon && (part.type === 'typed' || part.type === 'array')) {
                    const partTypeId = part.typeId;
                    if (partTypeId === 14) {
                        // Body parts (typed or array)
                        if (!checklistStatus.body.includes(partDisplay)) checklistStatus.body.push(partDisplay);
                    } else if (partTypeId === 17) {
                        // Barrel Accessories (check FIRST - more specific)
                        if (!checklistStatus.barrelAccessories.includes(partDisplay)) checklistStatus.barrelAccessories.push(partDisplay);
                    } else if (partTypeId === 23 || partTypeId === 9) {
                        // Barrel parts (typeId 23) OR Licensed barrel parts (typeId 9)
                        // Check if it's actually a barrel part by spawnCode if partType is empty
                        const spawnCode = partInfo ? String(partInfo.spawnCode || '').toLowerCase() : '';
                        const isBarrelPart = partTypeId === 23 || (partTypeId === 9 && spawnCode.includes('barrel'));
                        // Only add if not already in barrelAccessories
                        if (isBarrelPart && !checklistStatus.barrelAccessories.includes(partDisplay) && !checklistStatus.barrel.includes(partDisplay)) {
                            checklistStatus.barrel.push(partDisplay);
                        }
                    } else if (partTypeId === 4) {
                        // Body Accessories
                        if (!checklistStatus.bodyAccessories.includes(partDisplay)) checklistStatus.bodyAccessories.push(partDisplay);
                    } else if (partTypeId === 6) {
                        // Rarity (sometimes, depending on manufacturer)
                        if (!checklistStatus.rarity.includes(partDisplay)) checklistStatus.rarity.push(partDisplay);
                    }
                }
                
                // Fallback for simple parts: if partInfo is missing, try multiple lookup strategies
                if (!partInfo && part.type === 'simple') {
                    const partValue = String(part.value);
                    const currentTypeId = parseInt(document.getElementById('typeId').value);
                    if (currentTypeId) {
                        // Strategy 1: Try partsMap with various key formats
                        const fullId = `${currentTypeId}:${partValue}`;
                        partInfo = partsMap.get(fullId) || partsMap.get(partValue) || partsMap.get(parseInt(partValue));
                        
                        // Strategy 2: Search in partsByTypeId
                        if (!partInfo) {
                            const typeParts = partsByTypeId.get(currentTypeId) || [];
                            for (const info of typeParts) {
                                const infoId = String(info.id || '');
                                const infoFullId = String(info.fullId || '');
                                // Check if this part matches
                                if (infoId === partValue || 
                                    infoFullId === fullId ||
                                    infoFullId === `${currentTypeId}:${partValue}` ||
                                    (infoFullId.includes(':') && infoFullId.split(':')[1] === partValue) ||
                                    (infoId.includes(':') && infoId.split(':')[1] === partValue)) {
                                    partInfo = info;
                                    console.log(`Found partInfo for simple part {${partValue}} via fallback lookup:`, partInfo);
                                    break;
                                }
                            }
                        }
                        
                        // Strategy 3: If still not found, try searching all typeIds (for cross-typeId parts that might be stored incorrectly)
                        if (!partInfo) {
                            for (const [tid, typeParts] of partsByTypeId.entries()) {
                                for (const info of typeParts) {
                                    const infoId = String(info.id || '');
                                    const infoFullId = String(info.fullId || '');
                                    // Check if this part matches by ID value (regardless of typeId)
                                    if (infoId === partValue || 
                                        (infoFullId.includes(':') && infoFullId.split(':')[1] === partValue) ||
                                        (infoId.includes(':') && infoId.split(':')[1] === partValue)) {
                                        // Only use if it's from the current typeId or a known cross-typeId
                                        if (tid === currentTypeId || 
                                            (isWeapon && (tid === 14 || tid === 23 || tid === 4 || tid === 17 || tid === 6)) ||
                                            (isShield && (tid === 246 || tid === 237 || tid === 248)) ||
                                            (isGrenade && tid === 245) ||
                                            (isRepkit && tid === 243) ||
                                            (isClassMod && tid === 234) ||
                                            (isEnhancement && tid === 247) ||
                                            (isHeavyWeapon && tid === 244)) {
                                            partInfo = info;
                                            console.log(`Found partInfo for simple part {${partValue}} via cross-typeId fallback (typeId ${tid}):`, partInfo);
                                            break;
                                        }
                                    }
                                }
                                if (partInfo) break;
                            }
                        }
                    }
                }
                
                // Process the part using the helper function
                processPartForChecklist(part, partInfo, partDisplay, checklistStatus, isWeapon, isShield, hasMaliwanElementSwitch);
            }
            
            // Re-check for Maliwan Element Switch after processing all parts (in case we found it during processing)
            // Update the guideline visibility (use existing variable declared earlier)
            if (maliwanLicensedUnderbarrelGuideline) {
                if (hasMaliwanElementSwitch && isWeapon) {
                    maliwanLicensedUnderbarrelGuideline.style.display = 'flex';
                } else {
                    maliwanLicensedUnderbarrelGuideline.style.display = 'none';
                }
            }
            
            // Helper function to get available parts for a category
            const getAvailablePartsForCategory = (categoryKey, unlocked = false) => {
                const currentTypeId = parseInt(document.getElementById('typeId').value);
                if (!currentTypeId) {
                    return [];
                }
                
                // If unlocked, get parts from ALL typeIds but still categorize them
                if (unlocked) {
                    // Known grenade/ordnance typeIds that should NEVER appear in repkit or shield categories
                    const knownGrenadeTypeIds = new Set([263, 267, 270, 272, 278, 291, 298, 311]);
                    const knownRepkitTypeIds = new Set([261, 265, 266, 269, 274, 277, 285, 290]);
                    // Known shield typeIds - ONLY these should appear in shield body categories
                    const knownShieldTypeIds = new Set([279, 283, 287, 293, 300, 306, 312, 321]);
                    // Known classmod typeIds - should be excluded from grenade body categories
                    const knownClassModTypeIds = new Set([254, 255, 256, 257, 258, 259, 402, 404]);
                    typeIdMap.forEach((info, tid) => {
                        const typeId = Number(tid);
                        if (Number.isInteger(typeId) && /^class[\s_-]*mods?$/i.test(String(info?.category || '').trim())) {
                            knownClassModTypeIds.add(typeId);
                        }
                    });
                    
                    const allParts = [];
                    partsByTypeId.forEach((parts, tid) => {
                        allParts.push(...parts);
                    });
                    
                    // Determine if current item is an enhancement
                    const typeInfo = typeIdMap.get(currentTypeId);
                    const isEnhancement = typeInfo && (typeInfo.category === 'Enhancements' || typeInfo.name?.toLowerCase().includes('enhancement'));
                    // Shield detection: Check by TypeID first, then by category name
                    const isShield = currentTypeId === 246 || currentTypeId === 237 || currentTypeId === 248 || 
                                    (typeInfo && typeInfo.category && typeInfo.category.toLowerCase().includes('shield')) ||
                                    (typeInfo && typeInfo.name && typeInfo.name.toLowerCase().includes('shield'));
                    // Grenade/Ordnance detection: Check by TypeID first, then by category name
                    const isGrenade = currentTypeId === 245 || 
                                    (typeInfo && (typeInfo.category && (typeInfo.category.toLowerCase().includes('grenade') || typeInfo.category.toLowerCase().includes('ordnance')))) ||
                                    (typeInfo && (typeInfo.name && (typeInfo.name.toLowerCase().includes('grenade') || typeInfo.name.toLowerCase().includes('ordnance'))));
                    // Weapon detection: Check by category name
                    const isWeapon = typeInfo && typeInfo.category && typeInfo.category.toLowerCase() === 'weapon';
                    
                    // Get all grenade/ordnance typeIds for master unlock mode
                    const grenadeTypeIds = new Set();
                    if (isGrenade) {
                        grenadeTypeIds.add(245); // Always include typeId 245
                        typeIdMap.forEach((info, tid) => {
                            // Exclude classmod typeIds and weapon typeIds from grenade typeIds
                            const isWeapon = info.category && info.category.toLowerCase() === 'weapon';
                            if (info.category && (info.category.toLowerCase().includes('grenade') || info.category.toLowerCase().includes('ordnance')) && 
                                !knownClassModTypeIds.has(tid) && !isWeapon) {
                                grenadeTypeIds.add(tid);
                            }
                        });
                    }
                    
                    // Debug logging for grenade/ordnance categories in unlocked path
                    if (isGrenade && (categoryKey === 'rarity' || categoryKey === 'body' || categoryKey === 'baseBody')) {
                        console.log(`[DEBUG ordnance ${categoryKey} unlocked] isGrenade=${isGrenade}, grenadeTypeIds:`, Array.from(grenadeTypeIds));
                    }
                    
                    // Debug logging for shield categories in unlocked path
                    if (categoryKey === 'primaryPerks246' || categoryKey === 'secondaryPerks246' || categoryKey === 'perks246' || categoryKey === 'firmware246' || categoryKey === 'armor237' || categoryKey === 'energy248') {
                        const type246Parts = allParts.filter(p => p.typeId === 246);
                        const type237Parts = allParts.filter(p => p.typeId === 237);
                        const type248Parts = allParts.filter(p => p.typeId === 248);
                        console.log(`[DEBUG shield ${categoryKey} unlocked] allParts.length = ${allParts.length}, typeId 246 parts: ${type246Parts.length}, typeId 237 parts: ${type237Parts.length}, typeId 248 parts: ${type248Parts.length}`);
                        if (categoryKey === 'primaryPerks246' || categoryKey === 'secondaryPerks246' || categoryKey === 'perks246') {
                            const perks246Parts = type246Parts.filter(p => !String(p.spawnCode || '').toLowerCase().includes('firmware') && !String(p.path || '').toLowerCase().includes('firmware'));
                            console.log(`[DEBUG shield ${categoryKey} unlocked] Perks 246 parts (non-firmware): ${perks246Parts.length}`);
                        } else if (categoryKey === 'firmware246') {
                            const firmware246Parts = type246Parts.filter(p => String(p.spawnCode || '').toLowerCase().includes('firmware') || String(p.path || '').toLowerCase().includes('firmware'));
                            console.log(`[DEBUG shield firmware246 unlocked] Firmware 246 parts: ${firmware246Parts.length}`);
                        }
                    }
                    
                    // Debug logging for grenade/ordnance categories in unlocked path
                    if (isGrenade && (categoryKey === 'rarity' || categoryKey === 'body' || categoryKey === 'baseBody')) {
                        const type245Parts = allParts.filter(p => p.typeId === 245);
                        const currentTypeIdParts = allParts.filter(p => p.typeId === currentTypeId);
                        console.log(`[DEBUG ordnance ${categoryKey} unlocked] allParts.length = ${allParts.length}, typeId 245 parts: ${type245Parts.length}, currentTypeId ${currentTypeId} parts: ${currentTypeIdParts.length}`);
                        if (categoryKey === 'rarity') {
                            const rarityParts = allParts.filter(p => {
                                const pt = String(p.partType || '').toLowerCase();
                                const sc = String(p.spawnCode || '').toLowerCase();
                                return (p.typeId === currentTypeId || p.typeId === 245) && 
                                       (pt.includes('rarity') || pt === 'comp' || sc.includes('comp_') || sc.includes('rarity'));
                            });
                            console.log(`[DEBUG ordnance rarity unlocked] Rarity parts (typeId ${currentTypeId} or 245): ${rarityParts.length}`);
                            if (rarityParts.length > 0) {
                                console.log(`[DEBUG ordnance rarity unlocked] Sample rarity parts:`, rarityParts.slice(0, 5).map(p => ({
                                    id: p.id,
                                    fullId: p.fullId,
                                    name: p.name,
                                    typeId: p.typeId,
                                    partType: p.partType,
                                    spawnCode: p.spawnCode
                                })));
                            }
                        } else if (categoryKey === 'body' || categoryKey === 'baseBody') {
                            const bodyParts = allParts.filter(p => {
                                const pt = String(p.partType || '').toLowerCase();
                                const pp = String(p.path || '').toLowerCase();
                                return (p.typeId === currentTypeId || p.typeId === 245) && 
                                       (pt === 'base' || pp === 'base');
                            });
                            console.log(`[DEBUG ordnance ${categoryKey} unlocked] Body parts (typeId ${currentTypeId} or 245, partType='base'): ${bodyParts.length}`);
                            if (bodyParts.length > 0) {
                                console.log(`[DEBUG ordnance ${categoryKey} unlocked] Sample body parts:`, bodyParts.slice(0, 5).map(p => ({
                                    id: p.id,
                                    fullId: p.fullId,
                                    name: p.name,
                                    typeId: p.typeId,
                                    partType: p.partType,
                                    path: p.path,
                                    spawnCode: p.spawnCode
                                })));
                            }
                        }
                    }
                    
                    // Categorize all parts regardless of typeId (same categorization logic as locked, but no typeId restrictions)
                    const categoryMap = {
                        body: [], bodyAccessory: [], bodyAccessories: [], barrel: [], barrelAccessory: [], barrelAccessories: [], magazine: [],
                        scope: [], scopeAccessory: [], grip: [], foregrip: [], underbarrel: [], daedalusAmmo: [], maliwanLicensedUnderbarrel: [], licensedParts: [],
                        statModifier: [], rarity: [], manufacturerPerk: [], shield: [], baseBody: [],
                        base: [], payload: [], augment: [], skills: [], stat234: [], stat2_234: [], statspecial_234: [], firmware234: [],
                        core: [], baseBody247: [], firmware247: [], stat_247: [], stat2_247: [], stat3_247: [], legendaryPerks: [],
                        legendaryPart: [], firmware243: [], elementalResistances243: [], elementalImmunities243: [], elementalSplats243: [], elementalNovas243: [], size243: [], elemental243: [], parts243: [], firmware244: [],
                        firmware245: [], parts245: [], payload245: [], stats245: [], augment245: [], primaryPerks246: [], secondaryPerks246: [], resistance246: [], firmware246: [], armor237: [],
                        energy248: [], element: []
                    };
                    
                    // Debug: Log all parts with "body" in their partType or path for bodyAccessory debugging
                    if (categoryKey === 'bodyAccessory') {
                        const bodyParts = allParts.filter(p => {
                            const pt = String(p.partType || '').toLowerCase();
                            const pp = String(p.path || '').toLowerCase();
                            return pt.includes('body') || pp.includes('body');
                        });
                        console.log(`[DEBUG bodyAccessory unlocked] Found ${bodyParts.length} parts with 'body' in partType or path out of ${allParts.length} total parts`);
                        if (bodyParts.length > 0) {
                            console.log(`[DEBUG bodyAccessory unlocked] Sample body-related parts:`, bodyParts.slice(0, 5).map(p => ({
                                id: p.id,
                                fullId: p.fullId,
                                name: p.name,
                                partType: p.partType,
                                path: p.path,
                                typeId: p.typeId
                            })));
                        }
                    }
                    
                    // Debug: Log all parts with "underbarrel" in their partType or path for underbarrel debugging
                    if (categoryKey === 'underbarrel') {
                        const underbarrelParts = allParts.filter(p => {
                            const pt = String(p.partType || '').toLowerCase();
                            const pp = String(p.path || '').toLowerCase();
                            const sc = String(p.spawnCode || '').toLowerCase();
                            return pt.includes('underbarrel') || pp.includes('underbarrel') || sc.includes('underbarrel') || sc.includes('part_underbarrel');
                        });
                        console.log(`[DEBUG underbarrel unlocked] Found ${underbarrelParts.length} parts with 'underbarrel' in partType/path/spawnCode out of ${allParts.length} total parts`);
                        if (underbarrelParts.length > 0) {
                            console.log(`[DEBUG underbarrel unlocked] Sample underbarrel-related parts:`, underbarrelParts.slice(0, 10).map(p => ({
                                id: p.id,
                                fullId: p.fullId,
                                name: p.name,
                                partType: p.partType,
                                path: p.path,
                                spawnCode: p.spawnCode,
                                typeId: p.typeId
                            })));
                        }
                    }
                    
                    allParts.forEach(partInfo => {
                        const partType = String(partInfo.partType || '').toLowerCase();
                        const partPath = String(partInfo.path || '').toLowerCase();
                        const partName = String(partInfo.name || '').toLowerCase();
                        const spawnCode = String(partInfo.spawnCode || '').toLowerCase();
                        const partTypeId = partInfo.typeId || currentTypeId;
                        
                        // Get original (non-lowercased) partType and path for exact matching
                        const originalPartType = String(partInfo.partType || '');
                        const originalPartPath = String(partInfo.path || '');
                        
                        // Debug: Log underbarrel parts that match spawnCode but might be caught by earlier conditions
                        if (categoryKey === 'underbarrel' && (spawnCode.includes('part_underbarrel') || spawnCode.includes('underbarrel'))) {
                            console.log(`[DEBUG underbarrel unlocked] Processing part with underbarrel in spawnCode: ${partInfo.name} (id: ${partInfo.id}, fullId: ${partInfo.fullId}, partType: ${originalPartType}, path: ${originalPartPath}, spawnCode: ${partInfo.spawnCode}, typeId: ${partTypeId})`);
                        }
                        
                        // Categorize based on part properties (same logic as locked but without typeId restrictions)
                        // IMPORTANT: Check licensed parts FIRST (can be any typeId) - these can also be barrel, magazine, etc.
                        // Licensed Parts - identified by spawnCode containing "licensed" (can be ANY typeId, not just 13)
                        // These are manufacturer parts that are licensed from other manufacturers (e.g., Jakobs Ricochet, Tediore Reload, etc.)
                        // Also include ALL parts from "Manufacturer Part" part_type (even if spawn code doesn't contain "licensed")
                        const isLicensed = (spawnCode.includes('licensed') || 
                                           spawnCode.includes('_licensed_') ||
                                           partPath.includes('licensed') ||
                                           partName.includes('licensed') ||
                                           partType === 'manufacturer part' ||
                                           originalPartType === 'Manufacturer Part' ||
                                           originalPartPath.includes('Manufacturer Part') ||
                                           (partType === 'manufacturer part' && (spawnCode.includes('_licensed_') || spawnCode.includes('.licensed'))));
                        
                        if (isLicensed && isWeapon) {
                            categoryMap.licensedParts.push(partInfo);
                            // Debug logging for licensedParts
                            if (categoryKey === 'licensedParts') {
                                console.log(`[DEBUG licensedParts unlocked] ✅ Categorized: ${partInfo.name} (id: ${partInfo.id}, fullId: ${partInfo.fullId}, typeId: ${partTypeId}, spawnCode: ${spawnCode})`);
                            }
                            // Don't return - continue categorization so licensed parts also appear in their specific category (barrel, magazine, etc.)
                        }
                        
                        // IMPORTANT: Check underbarrel BEFORE typeId 1 (Element) to prevent element underbarrel parts from being misclassified
                        if (partType === 'underbarrel' || partType.includes('underbarrel') ||
                            originalPartType === 'Underbarrel' || originalPartPath.includes('Underbarrel') ||
                            partPath.includes('underbarrel') || spawnCode.includes('underbarrel') ||
                            spawnCode.includes('part_underbarrel')) {
                            // Underbarrel check MUST come BEFORE element check to prevent element underbarrel parts from being misclassified
                            // Also check for "part_underbarrel" in spawnCode for parts with empty part_type
                            categoryMap.underbarrel.push(partInfo);
                            // Debug logging for underbarrel
                            if (categoryKey === 'underbarrel') {
                                console.log(`[DEBUG underbarrel unlocked] ✅ Categorized: ${partInfo.name} (partType: ${originalPartType}, path: ${originalPartPath}, spawnCode: ${partInfo.spawnCode})`);
                            }
                            // Skip rest of categorization to avoid duplicates (use return in forEach to skip to next iteration)
                            return;
                        // IMPORTANT: Check specific typeIds (247, 1) BEFORE generic categories to prevent misclassification
                        } else if (partTypeId === 247) {
                            // Enhancement parts (typeId 247) - categorize into baseBody247, firmware247, or stats247
                            // This check MUST come BEFORE the rarity check to prevent Main Body parts from being misclassified
                            // Enhancement parts (typeId 247) - categorize into baseBody247, firmware247, or stats247
                            // This check MUST come before the general isEnhancement check
                            // First check if it's a Main Body part by path or partType
                            const originalPartPath = String(partInfo.path || '');
                            const originalPartType = String(partInfo.partType || '');
                            const partPathLower = originalPartPath.toLowerCase();
                            const partTypeLower = originalPartType.toLowerCase();
                            
                            const isMainBodyByPath = originalPartPath.includes('Main Body') || partPathLower.includes('main body');
                            const isMainBodyByType = originalPartType === 'Main Body' || partTypeLower === 'main body';
                            
                            // Debug logging for baseBody247 category
                            if (categoryKey === 'baseBody247') {
                                console.log(`[DEBUG baseBody247 unlocked] Processing typeId 247 part:`, {
                                    id: partInfo.id,
                                    fullId: partInfo.fullId,
                                    name: partInfo.name,
                                    partType: originalPartType,
                                    path: originalPartPath,
                                    isMainBodyByPath,
                                    isMainBodyByType
                                });
                            }
                            
                            const partIdStr = String(partInfo.id || partInfo.fullId || '');
                            let partIdNum = null;
                            
                            // Extract numeric part ID from various formats
                            if (typeof partInfo.id === 'number' && !isNaN(partInfo.id)) {
                                partIdNum = partInfo.id;
                            } else if (partIdStr.includes(':')) {
                                const parts = partIdStr.split(':');
                                if (parts.length >= 2) {
                                    partIdNum = parseInt(parts[parts.length - 1]);
                                }
                            } else if (partIdStr && !isNaN(parseInt(partIdStr))) {
                                partIdNum = parseInt(partIdStr);
                            }
                            
                            // Check if it's a base body part (247:76-80) by part ID OR by partType/name/path/spawnCode
                            const isBaseBodyById = partIdNum !== null && !isNaN(partIdNum) && partIdNum >= 76 && partIdNum <= 80;
                            // Check for Main Body explicitly (case-insensitive)
                            const isMainBodyExplicit = isMainBodyByPath || isMainBodyByType;
                            const isBaseBodyByType = partType === 'main body' || (partType.includes('body') && !partType.includes('accessory') && !partType.includes('base'));
                            const isBaseBodyByName = partName.includes('legendary') || partName.includes('epic') || partName.includes('rare') || partName.includes('uncommon') || partName.includes('common');
                            const isBaseBodyByPathCheck = partPath.includes('main body') || partPath.includes('body_0');
                            const isBaseBodyBySpawnCode = spawnCode.includes('part_body_05') || spawnCode.includes('part_body_04') || spawnCode.includes('part_body_03') || spawnCode.includes('part_body_02') || spawnCode.includes('part_body_01');
                            
                            // Categorize as baseBody247 if: ID is 76-80, OR explicitly Main Body by path/type, OR matches other base body patterns
                            if (isBaseBodyById || isMainBodyExplicit || (isBaseBodyByType && isBaseBodyByName) || isBaseBodyByPathCheck || isBaseBodyBySpawnCode) {
                                // This is a base body part (247:76-80) for enhancements
                                categoryMap.baseBody247.push(partInfo);
                                if (categoryKey === 'baseBody247') {
                                    console.log(`[DEBUG baseBody247 unlocked] ✅ Categorized Main Body part: ${partInfo.name} (id: ${partInfo.id}, fullId: ${partInfo.fullId}, partIdNum: ${partIdNum}, isMainBodyExplicit: ${isMainBodyExplicit})`);
                                }
                                // Skip rest of categorization to avoid duplicates
                            } else {
                                // Check for firmware - explicitly include Skillcraft (247:248) by ID
                                const isSkillcraftById = partIdNum === 248 && partTypeId === 247;
                                const isFirmware = spawnCode.includes('firmware') || partPath.includes('firmware') || partType.includes('firmware') ||
                                                 spawnCode.includes('skillcraft') || partName.includes('skillcraft') || isSkillcraftById;
                                const isStats = partPath.includes('stats') || partPath.includes('stats2') || partPath.includes('stats3') || partType.includes('stat') || spawnCode.includes('stat');
                                
                                if (isFirmware) {
                                    categoryMap.firmware247.push(partInfo);
                                } else if (isStats) {
                                    if (spawnCode.includes('stat3_') || partPath.includes('stat3') || partPath.includes('stats3')) {
                                        categoryMap.stat3_247.push(partInfo);
                                    } else if (spawnCode.includes('stat2_') || partPath.includes('stat2') || partPath.includes('stats2')) {
                                        categoryMap.stat2_247.push(partInfo);
                                    } else if (spawnCode.includes('stat_') || partPath.includes('stat') || partPath.includes('stats') || partType.includes('stat')) {
                                        categoryMap.stat_247.push(partInfo);
                                    }
                                }
                            }
                        } else if (partTypeId === 1) {
                            // TypeID 1 = Element parts - categorize BEFORE other checks
                            categoryMap.element.push(partInfo);
                            
                            // Maliwan Licensed Underbarrel parts - identified by spawnCode pattern: part_secondary_elem or path/licensed_underbarrel
                            // Check for ALL parts with these characteristics, not just when categoryKey matches
                            // This ensures all licensed underbarrel parts are available when the category is requested
                            // Match spawn codes like "Weapon.part_secondary_elem_*" (all licensed underbarrel parts have this)
                            // OR spawn codes like "Weapon.part_licensed_underbarrel_*" (older format)
                            // OR path contains "licensed_underbarrel"
                            // OR category contains "maliwan licensed" or "maliwan licenced" (handle both spellings)
                            const partCategory = String(partInfo.category || '').toLowerCase();
                            const isMaliwanLicensedUnderbarrel = 
                                spawnCode.includes('part_secondary_elem') || 
                                spawnCode.includes('part_licensed_underbarrel') ||
                                partPath.includes('licensed_underbarrel') ||
                                partCategory.includes('maliwan licensed') ||
                                partCategory.includes('maliwan licenced'); // Handle typo "licenced" vs "licensed"
                            
                            if (isMaliwanLicensedUnderbarrel) {
                                categoryMap.maliwanLicensedUnderbarrel.push(partInfo);
                                // Debug logging for maliwanLicensedUnderbarrel
                                console.log(`[DEBUG maliwanLicensedUnderbarrel unlocked] ✅ Categorized: ${partInfo.name} (id: ${partInfo.id}, fullId: ${partInfo.fullId}, typeId: ${partTypeId}, spawnCode: ${spawnCode}, path: ${partPath}, category: ${partInfo.category})`);
                            }
                        // Daedalus Ammo parts - identified by spawnCode pattern: part_secondary_ammo_sg, part_secondary_ammo_smg, part_secondary_ammo_ar, part_secondary_ammo_ps
                        // These can be any typeId and any part ID, so we check by spawnCode (check BEFORE other typeId checks)
                        } else if (spawnCode.includes('part_secondary_ammo_sg') ||
                                   spawnCode.includes('part_secondary_ammo_smg') ||
                                   spawnCode.includes('part_secondary_ammo_ar') ||
                                   spawnCode.includes('part_secondary_ammo_ps')) {
                            categoryMap.daedalusAmmo.push(partInfo);
                            // Debug logging for daedalusAmmo
                            if (categoryKey === 'daedalusAmmo') {
                                console.log(`[DEBUG daedalusAmmo unlocked] ✅ Categorized: ${partInfo.name} (id: ${partInfo.id}, fullId: ${partInfo.fullId}, typeId: ${partTypeId}, spawnCode: ${spawnCode})`);
                            }
                            // Skip rest of categorization to avoid duplicates
                            return;
                        } else if (partType === 'body accessory' || (partType.includes('body') && partType.includes('accessory')) ||
                                   originalPartType === 'Body Accessory' || originalPartPath.includes('Body Accessory') ||
                                   partPath.includes('body accessory') || (partPath.includes('body') && partPath.includes('accessory')) ||
                                   // Body accessories have spawnCodes like "part_body_a", "part_body_b", etc. (letters, not numbers like base body parts)
                                   // BUT exclude shield body parts (they have partType === 'shield' and spawnCodes like bor_shield.part_body_energy_* or dad_shield.part_body_*)
                                   (spawnCode.includes('part_body_') && !spawnCode.match(/part_body_0[1-5]/) && !spawnCode.match(/part_body_[1-5]\b/) && 
                                    !(partType === 'shield' || originalPartType === 'Shield' || spawnCode.includes('_shield.part_body') || spawnCode.includes('shield.part_body')))) {
                            // Body Accessory check MUST come BEFORE generic body check to prevent misclassification
                            categoryMap.bodyAccessory.push(partInfo);
                            categoryMap.bodyAccessories.push(partInfo); // Also add to plural key for compatibility
                            // Debug logging for body accessory
                            if (categoryKey === 'bodyAccessory' || categoryKey === 'bodyAccessories') {
                                console.log(`[DEBUG bodyAccessory unlocked] ✅ Categorized: ${partInfo.name} (partType: ${originalPartType}, path: ${originalPartPath}, spawnCode: ${partInfo.spawnCode})`);
                            }
                            // Skip rest of categorization to avoid duplicates
                            return;
                        }
                        // Shield parts (body parts from shield manufacturers, e.g., "Shield" partType)
                        // These are the main body parts for shields (e.g., "Sparky", "Firebreak" for Ripper shields)
                        // IMPORTANT: For shields, Base Body and Legendary Part are one and the same!
                        // Match when:
                        // 1. It's a shield item (isShield is true)
                        // 2. The part's typeId is a known shield typeId (ALL shield typeIds when master unlock is enabled, not just currentTypeId)
                        // 3. AND (partType is "shield" OR spawnCode includes "part_body" OR path includes "Shield")
                        // 4. CRITICAL: ONLY allow known shield typeIds - exclude grenade and repkit typeIds
                        // This prevents grenade/repkit parts from appearing in shield body categories when master unlock is enabled
                        // Don't match parts with "shield" in spawnCode/path that are perks/firmware/armor/energy (typeIds 246/237/248)
                        // In unlocked mode, check if partTypeId is a known shield typeId OR if part doesn't have typeId and falls back to currentTypeId (which is a shield)
                        else if (isShield && 
                                 (knownShieldTypeIds.has(partTypeId) || (!partInfo.typeId && knownShieldTypeIds.has(currentTypeId))) &&
                                 !knownGrenadeTypeIds.has(partTypeId) && !knownRepkitTypeIds.has(partTypeId)) {
                            // Debug: Log that we're checking this part
                            if (categoryKey === 'baseBody') {
                                console.log(`[DEBUG shield baseBody unlocked] ✅ Reached shield body check for: ${partInfo.name || partInfo.id} (isShield: ${isShield}, partInfo.typeId: ${partInfo.typeId}, partTypeId: ${partTypeId}, currentTypeId: ${currentTypeId}, partType: ${partType}, originalPartType: ${originalPartType}, spawnCode: ${spawnCode}, partPath: ${partPath})`);
                            }
                            
                            // Exclude comp/rarity parts - check for comp/rarity indicators
                            // NOTE: "legendary" appears in body parts, augments, AND comps, so we need to check for
                            // specific comp/rarity patterns, not just the word "legendary"
                            const isCompRarityPart = partType.includes('rarity') || partType === 'comp' || 
                                                    partPath.includes('rarity') || partPath.includes('rarities') ||
                                                    spawnCode.includes('rarity') || spawnCode.includes('comp_') ||
                                                    (partInfo.string && String(partInfo.string).toLowerCase().includes('comp_')) ||
                                                    partInfo.rarity; // Has explicit rarity field
                            
                            // Check if it matches shield body part criteria (same logic as locked view)
                            // For parts without typeId that fall back to currentTypeId, be more permissive
                            const hasExplicitTypeId = partInfo.typeId !== undefined && partInfo.typeId !== null;
                            // Check for shield body patterns: part_body, part_unique (for unique shield parts), or shield in path/partType
                            const matchesShieldBody = !isCompRarityPart && (
                                partType === 'shield' || 
                                spawnCode.includes('part_body') || 
                                spawnCode.includes('part_unique') || // Include unique shield parts like "dad_shield.part_unique_SuperSoldier"
                                partPath.includes('shield') || 
                                originalPartType === 'Shield' ||
                                // For parts without explicit typeId that fall back to currentTypeId, include them if currentTypeId is a shield
                                // This handles generic parts like "6", "8", "10" that don't have typeId but should be included for shields
                                (!hasExplicitTypeId && knownShieldTypeIds.has(currentTypeId) && 
                                 !partType.includes('rarity') && !partType.includes('comp') &&
                                 !spawnCode.includes('comp_') && !spawnCode.includes('rarity'))
                            );
                            
                            if (categoryKey === 'baseBody') {
                                console.log(`[DEBUG shield baseBody unlocked] matchesShieldBody check: ${matchesShieldBody} (partType==='shield': ${partType === 'shield'}, spawnCode.includes('part_body'): ${spawnCode.includes('part_body')}, partPath.includes('shield'): ${partPath.includes('shield')}, originalPartType==='Shield': ${originalPartType === 'Shield'}, isCompRarityPart: ${isCompRarityPart}, hasExplicitTypeId: ${hasExplicitTypeId})`);
                            }
                            
                            if (matchesShieldBody) {
                                // This is a shield body part from any shield typeId (when master unlock is enabled)
                                categoryMap.shield.push(partInfo);
                                categoryMap.baseBody.push(partInfo);
                                // For shields, Base Body = Legendary Part (they are one and the same)
                                categoryMap.legendaryPart.push(partInfo);
                                // Debug logging for shield body parts
                                if (categoryKey === 'baseBody' || categoryKey === 'legendaryPart') {
                                    console.log(`[DEBUG shield ${categoryKey} unlocked] ✅✅✅ Categorized: ${partInfo.name || partInfo.id} (partInfo.typeId: ${partInfo.typeId}, partTypeId: ${partTypeId}, currentTypeId: ${currentTypeId}, partType: ${partType}, originalPartType: ${originalPartType}, spawnCode: ${spawnCode}, path: ${partPath})`);
                                }
                            } else if (categoryKey === 'baseBody' || categoryKey === 'legendaryPart') {
                                // Debug: Log why it didn't match
                                console.log(`[DEBUG shield ${categoryKey} unlocked] ❌ NOT categorized: ${partInfo.name || partInfo.id} (partInfo.typeId: ${partInfo.typeId}, partTypeId: ${partTypeId}, currentTypeId: ${currentTypeId}, partType: ${partType}, originalPartType: ${originalPartType}, spawnCode: ${spawnCode}, path: ${partPath}, matchesShieldBody: ${matchesShieldBody})`);
                            }
                        } else if (partType === 'body' || (partType.includes('body') && !partType.includes('accessory') && !partType.includes('base'))) {
                            // Generic body parts (but NOT typeId 247 Main Body, which is handled above)
                            // BUT NOT shield body parts (handled above)
                            // CRITICAL: When in grenade mode, exclude classmod and weapon bodies from generic body category
                            // CRITICAL: When in weapon mode, exclude classmod bodies from generic body category
                            // CRITICAL: Exclude parts that are clearly from other categories (barrel, scope, magazine, etc.)
                            const isOtherCategory = partType.includes('barrel') || partType.includes('scope') || 
                                                   partType.includes('magazine') || partType.includes('grip') || 
                                                   partType.includes('foregrip') || partType.includes('underbarrel') ||
                                                   spawnCode.includes('part_barrel') || spawnCode.includes('part_scope') ||
                                                   spawnCode.includes('part_magazine') || spawnCode.includes('part_grip');
                            if (!isOtherCategory) {
                                if (isGrenade) {
                                    const isClassMod = knownClassModTypeIds.has(partTypeId);
                                    const partTypeInfo = typeIdMap.get(partTypeId);
                                    const isWeaponPart = partTypeInfo && partTypeInfo.category && partTypeInfo.category.toLowerCase() === 'weapon';
                                    if (!isClassMod && !isWeaponPart) {
                                        categoryMap.body.push(partInfo);
                                        return; // Skip rest of categorization
                                    }
                                } else if (isWeapon) {
                                    // When in weapon mode, exclude classmod bodies
                                    const isClassMod = knownClassModTypeIds.has(partTypeId);
                                    if (!isClassMod) {
                                        categoryMap.body.push(partInfo);
                                        return; // Skip rest of categorization
                                    }
                                } else {
                                    categoryMap.body.push(partInfo);
                                    return; // Skip rest of categorization
                                }
                            }
                        } else if (partType === 'barrel accessory' || (partType.includes('barrel') && partType.includes('accessory')) ||
                                   originalPartType === 'Barrel Accessory' || originalPartPath.includes('Barrel Accessory') ||
                                   partPath.includes('barrel accessory') || (partPath.includes('barrel') && partPath.includes('accessory')) ||
                                   spawnCode.includes('barrel') && spawnCode.includes('accessory') ||
                                   // Check for barrel accessory spawn code pattern: part_barrel_XX_[a-z] (letter suffix indicates accessory)
                                   // Pattern matches: part_barrel_ followed by digits, underscore, and a single letter (a-z)
                                   (spawnCode.includes('part_barrel_') && /part_barrel_\d+_[a-z]\b/i.test(spawnCode))) {
                            // Barrel Accessory check MUST come BEFORE generic barrel check to prevent misclassification
                            categoryMap.barrelAccessory.push(partInfo);
                            categoryMap.barrelAccessories.push(partInfo); // Also add to plural key for compatibility
                            // Debug logging for barrel accessory
                            if (categoryKey === 'barrelAccessory' || categoryKey === 'barrelAccessories') {
                                console.log(`[DEBUG barrelAccessory unlocked] ✅ Categorized: ${partInfo.name} (partType: ${originalPartType}, path: ${originalPartPath}, spawnCode: ${partInfo.spawnCode})`);
                            }
                            // Skip rest of categorization to avoid duplicates
                            return;
                        } else if (partType === 'barrel' || (partType.includes('barrel') && !partType.includes('accessory')) ||
                                   (spawnCode.includes('barrel') && !spawnCode.includes('accessory') && !spawnCode.includes('barrel accessory') &&
                                    // Exclude barrel accessories with letter suffix pattern (part_barrel_XX_[a-z])
                                    !/part_barrel_\d+_[a-z]\b/i.test(spawnCode) &&
                                    // Exclude licensed parts - they should only appear in licensedParts category
                                    !isLicensed)) {
                            // In unlocked mode, show all barrel parts from all weapon typeIds
                            // This allows users to see and use barrels from any weapon when master unlock is enabled
                            categoryMap.barrel.push(partInfo);
                            return; // Skip rest of categorization
                        } else if (partType === 'magazine' || partType.includes('magazine')) {
                            categoryMap.magazine.push(partInfo);
                            return; // Skip rest of categorization
                        } else if (partType === 'scope' || (partType.includes('scope') && !partType.includes('accessory'))) {
                            categoryMap.scope.push(partInfo);
                            return; // Skip rest of categorization
                        } else if (partType === 'scope accessory' || (partType.includes('scope') && partType.includes('accessory')) ||
                                   originalPartType === 'Scope Accessory' || originalPartPath.includes('Scope Accessory') ||
                                   partPath.includes('scope accessory') || (partPath.includes('scope') && partPath.includes('accessory'))) {
                            categoryMap.scopeAccessory.push(partInfo);
                            // Debug logging for scope accessory
                            if (categoryKey === 'scopeAccessory') {
                                console.log(`[DEBUG scopeAccessory unlocked] ✅ Categorized: ${partInfo.name} (partType: ${originalPartType}, path: ${originalPartPath})`);
                            }
                            return; // Skip rest of categorization
                        } else if (partType === 'grip' || (partType.includes('grip') && !partType.includes('foregrip'))) {
                            categoryMap.grip.push(partInfo);
                            return; // Skip rest of categorization
                        } else if (partType === 'foregrip' || partType.includes('foregrip') ||
                                   originalPartType === 'Foregrip' || originalPartPath.includes('Foregrip') ||
                                   partPath.includes('foregrip') || spawnCode.includes('foregrip')) {
                            categoryMap.foregrip.push(partInfo);
                            // Debug logging for foregrip
                            if (categoryKey === 'foregrip') {
                                console.log(`[DEBUG foregrip unlocked] ✅ Categorized: ${partInfo.name} (partType: ${originalPartType}, path: ${originalPartPath}, spawnCode: ${partInfo.spawnCode})`);
                            }
                            return; // Skip rest of categorization
                        } else if (partType === 'stat modifier' || (partType.includes('stat') && partType.includes('modifier'))) {
                            categoryMap.statModifier.push(partInfo);
                            return; // Skip rest of categorization
                        }
                        // Parts 245 and Firmware 245 - ALL typeId 245 parts should be categorized (same as locked path)
                        // Use 'if' instead of 'else if' so parts can also be added to other categories (rarity/body) if applicable
                        if (partTypeId === 245) {
                            // Check for firmware - explicitly include Skillcraft (245:88) by ID
                            const partIdStr = String(partInfo.id || partInfo.fullId || '');
                            let partIdNum = null;
                            if (partIdStr.includes(':')) {
                                const parts = partIdStr.split(':');
                                if (parts.length >= 2) {
                                    partIdNum = parseInt(parts[parts.length - 1]);
                                }
                            } else if (!isNaN(parseInt(partIdStr))) {
                                partIdNum = parseInt(partIdStr);
                            }
                            const isSkillcraftById = partIdNum === 88 && partTypeId === 245;
                            const isFirmware = spawnCode.includes('firmware') || partPath.includes('firmware') ||
                                             spawnCode.includes('skillcraft') || partName.includes('skillcraft') || isSkillcraftById;
                            // Check for elemental status parts (245:24-28: Corrosive, Cryo, Fire, Radiation, Shock)
                            const isElementalStatus = (partType === 'status' || partName.includes('status') || partPath.includes('status') || spawnCode.includes('status')) ||
                                                     (partIdNum >= 24 && partIdNum <= 28 && partTypeId === 245);
                            if (isFirmware) {
                                categoryMap.firmware245.push(partInfo);
                                // Debug logging
                                if (categoryKey === 'firmware245') {
                                    console.log(`[DEBUG firmware245 unlocked] ✅ Categorized: ${partInfo.name || partInfo.id} (typeId: ${partTypeId}, spawnCode: ${spawnCode})`);
                                }
                            } else if (partType === 'augment' || partPath.includes('augment') || spawnCode.includes('augment')) {
                                categoryMap.augment245.push(partInfo);
                                // Debug logging
                                if (categoryKey === 'augment245') {
                                    console.log(`[DEBUG augment245 unlocked] ✅ Categorized: ${partInfo.name || partInfo.id} (typeId: ${partTypeId}, spawnCode: ${spawnCode})`);
                                }
                            } else if (isElementalStatus) {
                                // Elemental status parts (Corrosive, Cryo, Fire, Radiation, Shock) go to parts245
                                categoryMap.parts245.push(partInfo);
                                // Debug logging
                                if (categoryKey === 'parts245') {
                                    console.log(`[DEBUG parts245 unlocked] ✅ Categorized: ${partInfo.name || partInfo.id} (typeId: ${partTypeId}, spawnCode: ${spawnCode})`);
                                }
                            } else if (partType === 'Stats' || partPath.includes('Stats') || spawnCode.includes('part_stat_')) {
                                // Stats parts (Overflow, Express, Explosive, etc.) go to stats245
                                categoryMap.stats245.push(partInfo);
                                // Debug logging
                                if (categoryKey === 'stats245') {
                                    console.log(`[DEBUG stats245 unlocked] ✅ Categorized: ${partInfo.name || partInfo.id} (typeId: ${partTypeId}, spawnCode: ${spawnCode})`);
                                }
                            } else {
                                // For typeId 245, if it's not firmware, augment, elemental status, or stats, it's a payload part
                                // This includes parts like MIRV Payload, Divider Payload, Spring Payload, etc.
                                categoryMap.payload245.push(partInfo);
                                // Debug logging
                                if (categoryKey === 'payload245') {
                                    console.log(`[DEBUG payload245 unlocked] ✅ Categorized: ${partInfo.name || partInfo.id} (typeId: ${partTypeId}, spawnCode: ${spawnCode})`);
                                }
                            }
                        }
                        // Grenade/Ordnance parts - Body parts from ANY grenade typeId should be included when master unlock is checked
                        // Grenades should ONLY use body category, NOT baseBody (to keep separate from repkits)
                        // CRITICAL: Exclude classmod typeIds (254-259) and weapon typeIds to prevent classmod/weapon bodies from appearing in grenade body categories
                        else if (isGrenade && grenadeTypeIds.has(partTypeId) && !knownClassModTypeIds.has(partTypeId)) {
                            // Check if this is a weapon part by checking the typeIdMap
                            const partTypeInfo = typeIdMap.get(partTypeId);
                            const isWeapon = partTypeInfo && partTypeInfo.category && partTypeInfo.category.toLowerCase() === 'weapon';
                            
                            if (!isWeapon && (partType === 'base' || partPath === 'base' || 
                                  originalPartType === 'Base' || originalPartPath === 'Base' ||
                                  // Also check spawnCode for base parts
                                  spawnCode.includes('part_ord') || spawnCode.includes('ord_grenade') ||
                                  spawnCode.includes('grenade_gadget.part_'))) {
                                categoryMap.base.push(partInfo);
                                // For grenades, only add to body category (NOT baseBody - that's for repkits)
                                categoryMap.body.push(partInfo);
                                // Debug logging for grenade/ordnance body
                                if (categoryKey === 'body' || categoryKey === 'baseBody') {
                                    console.log(`[DEBUG ordnance ${categoryKey} unlocked] ✅ Categorized (early check): ${partInfo.name || partInfo.id} (partTypeId: ${partTypeId}, currentTypeId: ${currentTypeId}, partType: ${partType}, path: ${partPath}, spawnCode: ${spawnCode})`);
                                }
                            }
                        }
                        else if (partType.includes('rarity') || partType === 'comp' || 
                                 partPath.includes('rarity') || partName.includes('rarity') || 
                                 spawnCode.includes('rarity') || spawnCode.includes('comp_') || 
                                 (partInfo.string && String(partInfo.string).toLowerCase().includes('comp_')) ||
                                 // For enhancements, also check if partType is a rarity name
                                 (isEnhancement && (partType === 'legendary' || partType === 'epic' || partType === 'rare' || 
                                   partType === 'uncommon' || partType === 'common')) ||
                                 // Check if path indicates it's from Rarities section
                                 (isEnhancement && partPath.toLowerCase().includes('rarities')) ||
                                 // Check if partType is a rarity name (for all item types when master unlock is on)
                                 partType === 'legendary' || partType === 'epic' || partType === 'rare' || partType === 'uncommon' || partType === 'common' ||
                                 // Check if part has rarity field or is from Rarities path (for all item types when master unlock is on)
                                 partPath.includes('rarities') || partInfo.rarity) {
                            // CRITICAL: Exclude parts that are clearly from other categories (barrel, body, scope, etc.)
                            const isOtherCategory = (partType.includes('barrel') && !partType.includes('rarity')) || 
                                                   (partType.includes('body') && !partType.includes('rarity')) ||
                                                   (partType.includes('scope') && !partType.includes('rarity')) ||
                                                   (partType.includes('magazine') && !partType.includes('rarity')) ||
                                                   (partType.includes('grip') && !partType.includes('rarity')) ||
                                                   spawnCode.includes('part_barrel') || spawnCode.includes('part_body_') ||
                                                   spawnCode.includes('part_scope') || spawnCode.includes('part_magazine');
                            // CRITICAL: Exclude tier/skill parts (class mod skills, etc.) - these should NOT appear in rarity category
                            const partNameStr = String(partInfo.name || '').toLowerCase();
                            // Check if this is a tier/skill part - exclude if name contains "(Tier" or "Tier " pattern
                            const hasTierInName = partNameStr.includes('(tier') || partNameStr.includes('tier ') || 
                                                  partNameStr.match(/tier\s+\d+/i);
                            // Check if this is a skill part from class mods or other skill-based items
                            const isSkillPart = partPath.includes('skill') || spawnCode.includes('skill') || 
                                               partType.includes('skill') || partType.includes('tier');
                            // Class mod typeIds (254-259) should generally be excluded from rarity unless they're explicitly rarity parts
                            const isClassModPart = knownClassModTypeIds.has(partTypeId);
                            // Only exclude class mod parts if they're clearly tier/skill parts, not if they're actual rarity parts
                            const isTierSkillPart = hasTierInName || 
                                                   (isSkillPart && !partPath.includes('rarity') && !spawnCode.includes('comp_')) ||
                                                   (isClassModPart && (hasTierInName || isSkillPart));
                            if (!isOtherCategory && !isTierSkillPart) {
                                // When master unlock is on, show ALL rarities from ALL item types
                                categoryMap.rarity.push(partInfo);
                                // Debug logging
                                if (categoryKey === 'rarity') {
                                    console.log(`[DEBUG rarity unlocked] ✅ Categorized: ${partInfo.name || partInfo.id} (partTypeId: ${partTypeId}, currentTypeId: ${currentTypeId}, partType: ${partType}, rarity: ${partInfo.rarity}, path: ${partPath})`);
                                }
                                return; // Skip rest of categorization
                            }
                        } else if (isEnhancement) {
                            // Enhancement Manufacturer Perks (legendaryPerks) - check for parts with IDs 1, 2, 3, 9 that have part_core
                            // In unlocked mode, check all enhancement typeIds, not just currentTypeId
                            const partIdStr = String(partInfo.id || partInfo.fullId || '');
                            let partIdNum = null;
                            const partTypeInfo = typeIdMap.get(partTypeId);
                            const isPartEnhancement = partTypeInfo && (partTypeInfo.category === 'Enhancements' || partTypeInfo.name?.toLowerCase().includes('enhancement'));
                            
                            if (partIdStr.includes(':')) {
                                const parts = partIdStr.split(':');
                                if (parts.length >= 2 && isPartEnhancement) {
                                    partIdNum = parseInt(parts[parts.length - 1]);
                                }
                            } else if (isPartEnhancement) {
                                partIdNum = parseInt(partIdStr);
                            }
                            const isManufacturerPerk = !isNaN(partIdNum) && (partIdNum === 1 || partIdNum === 2 || partIdNum === 3 || partIdNum === 9);
                            const hasPartCore = spawnCode.includes('part_core') || partName.includes('part_core') || 
                                               (partInfo.string && String(partInfo.string).toLowerCase().includes('part_core'));
                            if (isManufacturerPerk && hasPartCore) {
                                categoryMap.legendaryPerks.push(partInfo);
                            }
                        }
                        // Additional explicit check for shield body parts by spawnCode pattern (fallback)
                        // This ensures we catch shield body parts even if they don't match the above conditions
                        // CRITICAL: ONLY allow known shield typeIds - exclude grenade and repkit typeIds
                        // NOTE: In unlocked mode, allow ALL shield typeIds (not just currentTypeId)
                        // Also handle parts without explicit typeId that fall back to currentTypeId
                        else if (isShield && spawnCode.includes('part_body') && 
                                 partTypeId !== 246 && partTypeId !== 237 && partTypeId !== 248 &&
                                 (knownShieldTypeIds.has(partTypeId) || (!partInfo.typeId && knownShieldTypeIds.has(currentTypeId))) &&
                                 !knownGrenadeTypeIds.has(partTypeId) && !knownRepkitTypeIds.has(partTypeId)) {
                            // Exclude comp/rarity parts from fallback check too
                            const isCompRarityPart = partType.includes('rarity') || partType === 'comp' || 
                                                    partPath.includes('rarity') || partPath.includes('rarities') ||
                                                    spawnCode.includes('rarity') || spawnCode.includes('comp_') ||
                                                    (partInfo.string && String(partInfo.string).toLowerCase().includes('comp_')) ||
                                                    partInfo.rarity; // Has explicit rarity field
                            
                            if (!isCompRarityPart) {
                                // This is a shield body part (not a perk/firmware/armor/energy part, not grenade/repkit, and not comp/rarity)
                                categoryMap.shield.push(partInfo);
                                categoryMap.baseBody.push(partInfo);
                                // For shields, Base Body = Legendary Part (they are one and the same)
                                categoryMap.legendaryPart.push(partInfo);
                                // Debug logging
                                if (categoryKey === 'baseBody' || categoryKey === 'legendaryPart') {
                                    console.log(`[DEBUG shield ${categoryKey} unlocked] ✅ Categorized (fallback): ${partInfo.name || partInfo.id} (partInfo.typeId: ${partInfo.typeId}, partTypeId: ${partTypeId}, currentTypeId: ${currentTypeId}, spawnCode: ${spawnCode})`);
                                }
                            }
                        }
                        // Shield parts (typeId 246, 237, 248) - CHECK BEFORE generic shield check
                        // These parts should be categorized by their typeId regardless of partType
                        else if (partTypeId === 246) {
                            // Extract part ID to check if it's a resistance part (246:21-246:26)
                            let partIdNum = null;
                            const partIdStr = String(partInfo.id || partInfo.fullId || '');
                            if (partIdStr.includes(':')) {
                                const parts = partIdStr.split(':');
                                if (parts.length >= 2) {
                                    partIdNum = parseInt(parts[parts.length - 1]);
                                }
                            } else if (!isNaN(parseInt(partIdStr))) {
                                partIdNum = parseInt(partIdStr);
                            }
                            
                            // Check if it's a resistance part (IDs 21-26)
                            const isResistance = partIdNum !== null && partIdNum >= 21 && partIdNum <= 26;
                            
                            if (spawnCode.includes('firmware') || partPath.includes('firmware')) {
                                categoryMap.firmware246.push(partInfo);
                                // Debug logging
                                if (categoryKey === 'firmware246') {
                                    console.log(`[DEBUG shield firmware246 unlocked] ✅ Categorized: ${partInfo.name || partInfo.id} (typeId: ${partTypeId}, spawnCode: ${spawnCode})`);
                                }
                            } else if (isResistance || spawnCode.includes('part_corrosive') || spawnCode.includes('part_cryo') || 
                                       spawnCode.includes('part_fire') || spawnCode.includes('part_radiation') || spawnCode.includes('part_shock')) {
                                // Resistance parts (246:21-246:26)
                                categoryMap.resistance246.push(partInfo);
                                // Debug logging
                                if (categoryKey === 'resistance246') {
                                    console.log(`[DEBUG shield resistance246 unlocked] ✅ Categorized: ${partInfo.name || partInfo.id} (typeId: ${partTypeId}, partId: ${partIdNum}, spawnCode: ${spawnCode})`);
                                }
                            } else {
                                if (spawnCode.includes('_primary') || partPath.includes('primary') || partName.includes('primary')) {
                                    categoryMap.primaryPerks246.push(partInfo);
                                    // Debug logging
                                    if (categoryKey === 'primaryPerks246' || categoryKey === 'perks246') {
                                        console.log(`[DEBUG shield primaryPerks246 unlocked] ✅ Categorized: ${partInfo.name || partInfo.id} (typeId: ${partTypeId}, spawnCode: ${spawnCode})`);
                                    }
                                } else if (spawnCode.includes('_secondary') || partPath.includes('secondary') || partName.includes('secondary')) {
                                    categoryMap.secondaryPerks246.push(partInfo);
                                    // Debug logging
                                    if (categoryKey === 'secondaryPerks246' || categoryKey === 'perks246') {
                                        console.log(`[DEBUG shield secondaryPerks246 unlocked] ✅ Categorized: ${partInfo.name || partInfo.id} (typeId: ${partTypeId}, spawnCode: ${spawnCode})`);
                                    }
                                } else {
                                    // If we can't determine, default to primary (fallback)
                                    categoryMap.primaryPerks246.push(partInfo);
                                    // Debug logging
                                    if (categoryKey === 'primaryPerks246' || categoryKey === 'perks246') {
                                        console.log(`[DEBUG shield primaryPerks246 unlocked] ✅ Categorized (fallback): ${partInfo.name || partInfo.id} (typeId: ${partTypeId}, spawnCode: ${spawnCode})`);
                                    }
                                }
                            }
                            // Also add to generic shield category
                            categoryMap.shield.push(partInfo);
                        } else if (partTypeId === 237) {
                            categoryMap.armor237.push(partInfo);
                            // Debug logging
                            if (categoryKey === 'armor237') {
                                console.log(`[DEBUG shield armor237 unlocked] ✅ Categorized: ${partInfo.name || partInfo.id} (typeId: ${partTypeId}, spawnCode: ${spawnCode})`);
                            }
                            // Also add to generic shield category
                            categoryMap.shield.push(partInfo);
                        } else if (partTypeId === 248) {
                            categoryMap.energy248.push(partInfo);
                            // Debug logging
                            if (categoryKey === 'energy248') {
                                console.log(`[DEBUG shield energy248 unlocked] ✅ Categorized: ${partInfo.name || partInfo.id} (typeId: ${partTypeId}, spawnCode: ${spawnCode})`);
                            }
                            // Also add to generic shield category
                            categoryMap.shield.push(partInfo);
                        } else if (partType === 'shield' || partPath.includes('shield') || spawnCode.includes('shield')) {
                            // Other shield-related parts (perks, firmware, etc.) - don't add to baseBody
                            categoryMap.shield.push(partInfo);
                        } else if (partType === 'base' || partPath === 'base' || 
                                   originalPartType === 'Base' || originalPartPath === 'Base' ||
                                   (isGrenade && (spawnCode.includes('part_ord') || spawnCode.includes('ord_grenade')))) {
                            if (isGrenade) {
                                // For grenades, include base parts from ANY grenade typeId when master unlock is checked
                                // Grenades should ONLY use body category, NOT baseBody (to keep separate from repkits)
                                if (grenadeTypeIds.has(partTypeId) || knownGrenadeTypeIds.has(partTypeId)) {
                                    categoryMap.base.push(partInfo);
                                    // For grenades, only add to body category (NOT baseBody - that's for repkits)
                                    categoryMap.body.push(partInfo);
                                    // Debug logging for grenade/ordnance body
                                    if (categoryKey === 'body' || categoryKey === 'baseBody') {
                                        console.log(`[DEBUG ordnance ${categoryKey} unlocked] ✅ Categorized: ${partInfo.name || partInfo.id} (partTypeId: ${partTypeId}, currentTypeId: ${currentTypeId}, partType: ${partType}, originalPartType: ${originalPartType}, path: ${partPath}, originalPartPath: ${originalPartPath}, spawnCode: ${spawnCode})`);
                                    }
                                } else if (categoryKey === 'body' || categoryKey === 'baseBody') {
                                    console.log(`[DEBUG ordnance ${categoryKey} unlocked] ❌ Skipped (not a grenade typeId): ${partInfo.name || partInfo.id} (partTypeId: ${partTypeId}, currentTypeId: ${currentTypeId}, grenadeTypeIds:`, Array.from(grenadeTypeIds), ')');
                                }
                            } else if (isRepkit) {
                                // For repkits, use baseBody category (separate from grenades which use body)
                                // Exclude grenade typeIds from repkit baseBody (they should be in grenade body category)
                                if (!knownGrenadeTypeIds.has(partTypeId)) {
                                    categoryMap.base.push(partInfo);
                                    categoryMap.baseBody.push(partInfo);
                                }
                            } else {
                                // For other item types, use baseBody
                                // CRITICAL: Exclude grenade and repkit typeIds from shield baseBody
                                // Only add if it's not a grenade/repkit typeId (to prevent them from appearing in shield categories)
                                if (!knownGrenadeTypeIds.has(partTypeId) && !knownRepkitTypeIds.has(partTypeId)) {
                                    categoryMap.base.push(partInfo);
                                    categoryMap.baseBody.push(partInfo);
                                }
                            }
                        } else if ((partType === 'payload' || partPath.includes('payload')) && partTypeId !== 243) {
                            // Exclude typeId 243 parts from payload category - they should be categorized as Size/Elemental/etc.
                            categoryMap.payload.push(partInfo);
                        } else if (partType === 'augment' || partPath.includes('augment') || spawnCode.includes('augment')) {
                            // For repkits, Augment parts should also be considered as baseBody (same as Base parts)
                            // In unlocked mode, include augments from ALL repkit typeIds
                            if (isRepkit && (knownRepkitTypeIds.has(partTypeId) || partTypeId === currentTypeId)) {
                                categoryMap.baseBody.push(partInfo);
                            } else {
                                categoryMap.augment.push(partInfo);
                            }
                        } else if (partTypeId === 234) {
                            // IMPORTANT: Check typeId 234 BEFORE checking for skills, because some typeId 234 parts
                            // have "skill" in their spawn_code (e.g., "ClassMod.stat_skill_cooldown_rate") and
                            // should be categorized as stat234/stat2_234/statspecial_234, not as skills
                            // Check for firmware - explicitly include Skillcraft (234:103) by ID
                            const partIdStr = String(partInfo.id || partInfo.fullId || '');
                            let partIdNum = null;
                            if (partIdStr.includes(':')) {
                                const parts = partIdStr.split(':');
                                if (parts.length >= 2) {
                                    partIdNum = parseInt(parts[parts.length - 1]);
                                }
                            } else if (!isNaN(parseInt(partIdStr))) {
                                partIdNum = parseInt(partIdStr);
                            }
                            const isSkillcraftById = partIdNum === 103 && partTypeId === 234;
                            const isFirmware = spawnCode.includes('firmware') || partPath.includes('firmware') ||
                                             spawnCode.includes('skillcraft') || partName.includes('skillcraft') || isSkillcraftById;
                            if (isFirmware) {
                                categoryMap.firmware234.push(partInfo);
                            } else {
                                if (spawnCode.includes('statspecial_') || spawnCode.includes('ClassMod.statspecial')) {
                                    categoryMap.statspecial_234.push(partInfo);
                                } else if (spawnCode.includes('stat2_') || spawnCode.includes('ClassMod.stat2')) {
                                    categoryMap.stat2_234.push(partInfo);
                                } else if (spawnCode.includes('stat_') || spawnCode.includes('ClassMod.stat') || spawnCode.includes('stat')) {
                                    categoryMap.stat234.push(partInfo);
                                } else {
                                    // Fallback: if it's a perk but can't determine, default to stat
                                    categoryMap.stat234.push(partInfo);
                                }
                            }
                        } else if (partType === 'skill' || partType === 'Skills' || partType.includes('skill') || spawnCode.includes('skill') || (partTypeId >= 254 && partTypeId <= 259 && partType !== 'body' && partType !== 'rarity')) {
                            // Exclude body and rarity parts from skills - check multiple ways they might be identified
                            // partType 'Skills' from characters.*.class_mods.Skills.parts (actual skill tiers)
                            // Also exclude typeId 234 parts (they should be handled above)
                            const isBodyPart = partType === 'body' || partType.includes('body') || 
                                             partPath.includes('body') || partPath.includes('Body') ||
                                             spawnCode.includes('body') || spawnCode.includes('Body') ||
                                             originalPartType === 'Body' || originalPartType.includes('Body');
                            const isRarityPart = partType === 'rarity' || partType === 'comp' || partType.includes('rarity') ||
                                                partPath.includes('rarity') || partPath.includes('rarities') ||
                                                spawnCode.includes('rarity') || spawnCode.includes('comp_') ||
                                                originalPartType === 'Rarity' || originalPartType.includes('Rarity') ||
                                                partInfo.rarity; // Has explicit rarity field
                            // Only add to skills if it's NOT a body part AND NOT a rarity part AND NOT typeId 234
                            if (!isBodyPart && !isRarityPart && partTypeId !== 234) {
                                categoryMap.skills.push(partInfo);
                            }
                        } else if (partType === 'core' || partPath.includes('core')) {
                            categoryMap.core.push(partInfo);
                        } else if (partTypeId === 243) {
                            // Check for firmware - primarily by partType field, then by spawnCode/path/name/Skillcraft ID
                            const originalPartType = String(partInfo.partType || '');
                            const partIdStr = String(partInfo.id || partInfo.fullId || '');
                            let partIdNum = null;
                            if (partIdStr.includes(':')) {
                                const parts = partIdStr.split(':');
                                if (parts.length >= 2) {
                                    partIdNum = parseInt(parts[parts.length - 1]);
                                }
                            } else if (!isNaN(parseInt(partIdStr))) {
                                partIdNum = parseInt(partIdStr);
                            }
                            const isSkillcraftById = partIdNum === 113 && partTypeId === 243;
                            // Primary check: partType === 'Firmware'
                            // Secondary check: spawnCode/path/name contains 'firmware' or 'skillcraft', or is Skillcraft by ID
                            const isFirmware = originalPartType === 'Firmware' || 
                                             spawnCode.includes('firmware') || partPath.includes('firmware') ||
                                             spawnCode.includes('skillcraft') || partName.includes('skillcraft') || isSkillcraftById;
                            if (isFirmware) {
                                categoryMap.firmware243.push(partInfo);
                            } else {
                                // Categorize non-firmware parts into subcategories
                                const isResistance = originalPartType === 'Resistance' || spawnCode.includes('elemental_resist') || spawnCode.includes('resist');
                                const isImmunity = originalPartType === 'Immunity' || spawnCode.includes('immunity');
                                const isSplat = originalPartType === 'Splat' || spawnCode.includes('splat') || (partIdNum >= 32 && partIdNum <= 36);
                                const isNova = originalPartType === 'Nova' || spawnCode.includes('nova') || (partIdNum >= 37 && partIdNum <= 41);
                                const partString = String(partInfo.string || '').toLowerCase();
                                const isSize = originalPartType === 'Size' || spawnCode.includes('payload') || partString.includes('payload') || (partIdNum >= 103 && partIdNum <= 106);
                                const isElemental = originalPartType === 'Elemental' || spawnCode.includes('part_element') || (partIdNum >= 98 && partIdNum <= 102);
                                
                                if (isResistance) {
                                    categoryMap.elementalResistances243.push(partInfo);
                                } else if (isImmunity) {
                                    categoryMap.elementalImmunities243.push(partInfo);
                                } else if (isSplat) {
                                    categoryMap.elementalSplats243.push(partInfo);
                                } else if (isNova) {
                                    categoryMap.elementalNovas243.push(partInfo);
                                } else if (isSize) {
                                    categoryMap.size243.push(partInfo);
                                } else if (isElemental) {
                                    categoryMap.elemental243.push(partInfo);
                                } else {
                                    // Everything else goes to parts243
                                    categoryMap.parts243.push(partInfo);
                                }
                            }
                        // Note: partTypeId === 245 is already handled earlier in the chain (parts245/firmware245)
                        } else if (partTypeId === 244) {
                            // Check for firmware - explicitly include Skillcraft (244:88 or similar) by ID and name
                            const partIdStr = String(partInfo.id || partInfo.fullId || '');
                            let partIdNum = null;
                            if (partIdStr.includes(':')) {
                                const parts = partIdStr.split(':');
                                if (parts.length >= 2) {
                                    partIdNum = parseInt(parts[parts.length - 1]);
                                }
                            } else if (!isNaN(parseInt(partIdStr))) {
                                partIdNum = parseInt(partIdStr);
                            }
                            const isSkillcraftById = partIdNum === 88 && partTypeId === 244;
                            const isFirmware = spawnCode.includes('firmware') || partPath.includes('firmware') ||
                                             spawnCode.includes('skillcraft') || partName.includes('skillcraft') || isSkillcraftById;
                            if (isFirmware) {
                                categoryMap.firmware244.push(partInfo);
                            }
                        }
                        // Note: partTypeId === 1 (Element) and partTypeId === 247 are already handled earlier in the chain
                    });
                    
                    // Deduplicate all category maps to avoid duplicates
                    Object.keys(categoryMap).forEach(key => {
                        if (categoryMap[key].length > 0) {
                            const seen = new Set();
                            categoryMap[key] = categoryMap[key].filter(partInfo => {
                                const fullId = String(partInfo.fullId || partInfo.id || '');
                                if (fullId && seen.has(fullId)) {
                                    return false; // Duplicate
                                }
                                if (fullId) seen.add(fullId);
                                return true;
                            });
                        }
                    });
                    
                    // Filter out parts that are already in currentParts
                    const currentPartsSet = new Set();
                    currentParts.forEach(part => {
                        if (part.type === 'simple') {
                            currentPartsSet.add(`${part.value}`);
                        } else if (part.type === 'typed') {
                            currentPartsSet.add(`${part.typeId}:${part.value}`);
                        } else if (part.type === 'array') {
                            part.values.forEach(val => {
                                currentPartsSet.add(`${part.typeId}:${val}`);
                            });
                        }
                    });
                    
                    // Debug logging for shield categories in unlocked path
                    if (categoryKey === 'primaryPerks246' || categoryKey === 'secondaryPerks246' || categoryKey === 'perks246' || categoryKey === 'firmware246' || categoryKey === 'armor237' || categoryKey === 'energy248') {
                        console.log(`[DEBUG shield ${categoryKey} unlocked] categoryMap[${categoryKey}] contains ${categoryMap[categoryKey]?.length || 0} parts`);
                        if (categoryMap[categoryKey] && categoryMap[categoryKey].length > 0) {
                            console.log(`[DEBUG shield ${categoryKey} unlocked] Sample parts:`, categoryMap[categoryKey].slice(0, 3).map(p => ({
                                id: p.id,
                                fullId: p.fullId,
                                name: p.name,
                                typeId: p.typeId,
                                partType: p.partType,
                                spawnCode: p.spawnCode
                            })));
                        }
                    }
                    
                    // Return parts for the requested category, filtered to exclude already-added parts
                    // Handle both singular and plural keys for compatibility
                    let categoryParts = categoryMap[categoryKey] || [];
                    // If not found, try the alternative key (singular/plural)
                    if (categoryParts.length === 0) {
                        if (categoryKey === 'bodyAccessories') {
                            categoryParts = categoryMap.bodyAccessory || [];
                        } else if (categoryKey === 'bodyAccessory') {
                            categoryParts = categoryMap.bodyAccessories || [];
                        } else if (categoryKey === 'barrelAccessories') {
                            categoryParts = categoryMap.barrelAccessory || [];
                        } else if (categoryKey === 'barrelAccessory') {
                            categoryParts = categoryMap.barrelAccessories || [];
                        }
                    }
                    
                    // Debug logging for accessory and grip categories
                    if (['bodyAccessory', 'bodyAccessories', 'barrelAccessory', 'barrelAccessories', 'scopeAccessory', 'foregrip', 'underbarrel'].includes(categoryKey)) {
                        console.log(`[DEBUG ${categoryKey} unlocked] categoryMap.${categoryKey} contains ${categoryMap[categoryKey]?.length || 0} parts (after deduplication)`);
                        if (categoryMap[categoryKey] && categoryMap[categoryKey].length > 0) {
                            console.log(`[DEBUG ${categoryKey} unlocked] Parts in categoryMap:`, categoryMap[categoryKey].slice(0, 5).map(p => ({
                                id: p.id,
                                fullId: p.fullId,
                                name: p.name,
                                partType: p.partType,
                                path: p.path,
                                typeId: p.typeId,
                                spawnCode: p.spawnCode
                            })));
                        } else {
                            // Debug: Check if any parts in allParts match the criteria
                            const matchingParts = allParts.filter(p => {
                                const pt = String(p.partType || '').toLowerCase();
                                const pp = String(p.path || '').toLowerCase();
                                const opt = String(p.partType || '');
                                const opp = String(p.path || '');
                                const sc = String(p.spawnCode || '').toLowerCase();
                                
                                if (categoryKey === 'bodyAccessory') {
                                    return pt === 'body accessory' || (pt.includes('body') && pt.includes('accessory')) ||
                                           opt === 'Body Accessory' || opp.includes('Body Accessory') ||
                                           pp.includes('body accessory') || (pp.includes('body') && pp.includes('accessory')) ||
                                           (sc.includes('body') && sc.includes('accessory'));
                                } else if (categoryKey === 'barrelAccessory') {
                                    return pt === 'barrel accessory' || (pt.includes('barrel') && pt.includes('accessory')) ||
                                           opt === 'Barrel Accessory' || opp.includes('Barrel Accessory') ||
                                           pp.includes('barrel accessory') || (pp.includes('barrel') && pp.includes('accessory'));
                                } else if (categoryKey === 'scopeAccessory') {
                                    return pt === 'scope accessory' || (pt.includes('scope') && pt.includes('accessory')) ||
                                           opt === 'Scope Accessory' || opp.includes('Scope Accessory') ||
                                           pp.includes('scope accessory') || (pp.includes('scope') && pp.includes('accessory'));
                                } else if (categoryKey === 'foregrip') {
                                    return pt === 'foregrip' || pt.includes('foregrip') ||
                                           opt === 'Foregrip' || opp.includes('Foregrip') ||
                                           pp.includes('foregrip');
                                } else if (categoryKey === 'underbarrel') {
                                    return pt === 'underbarrel' || pt.includes('underbarrel') ||
                                           opt === 'Underbarrel' || opp.includes('Underbarrel') ||
                                           pp.includes('underbarrel') || sc.includes('underbarrel') ||
                                           sc.includes('part_underbarrel');
                                }
                                return false;
                            });
                            console.log(`[DEBUG ${categoryKey} unlocked] Found ${matchingParts.length} matching parts in allParts (total: ${allParts.length})`);
                            if (matchingParts.length > 0) {
                                console.log(`[DEBUG ${categoryKey} unlocked] Sample matching parts:`, matchingParts.slice(0, 3).map(p => ({
                                    id: p.id,
                                    fullId: p.fullId,
                                    name: p.name,
                                    partType: p.partType,
                                    path: p.path,
                                    typeId: p.typeId
                                })));
                            }
                        }
                    }
                    
                    // Debug logging for baseBody247
                    if (categoryKey === 'baseBody247') {
                        console.log(`[DEBUG baseBody247 unlocked] categoryMap.baseBody247 contains ${categoryMap.baseBody247.length} parts (after deduplication)`);
                        if (categoryMap.baseBody247.length > 0) {
                            console.log(`[DEBUG baseBody247 unlocked] Parts in categoryMap:`, categoryMap.baseBody247.map(p => ({
                                id: p.id,
                                fullId: p.fullId,
                                name: p.name,
                                partType: p.partType,
                                path: p.path
                            })));
                        }
                    }
                    
                    return categoryParts.filter(partInfo => {
                        const partId = String(partInfo.id || '');
                        const fullId = String(partInfo.fullId || '');
                        const typeId = partInfo.typeId || 0;
                        
                        // Check if this part is already added
                        if (fullId.includes(':')) {
                            return !currentPartsSet.has(fullId);
                        } else if (typeId > 0) {
                            return !currentPartsSet.has(`${typeId}:${partId}`);
                        } else {
                            return !currentPartsSet.has(partId);
                        }
                    });
                }
                
                // Build partsByCategory dynamically if not available
                const buildPartsByCategory = () => {
                    // Known grenade/ordnance typeIds that should NEVER appear in repkit or shield categories
                    const knownGrenadeTypeIds = new Set([263, 267, 270, 272, 278, 291, 298, 311]);
                    const knownRepkitTypeIds = new Set([261, 265, 266, 269, 274, 277, 285, 290]);
                    // Known shield typeIds - ONLY these should appear in shield body categories
                    const knownShieldTypeIds = new Set([279, 283, 287, 293, 300, 306, 312, 321]);
                    
                    const categoryMap = {
                        // Weapon parts
                        body: [],
                        bodyAccessory: [],
                        bodyAccessories: [],
                        barrel: [],
                        barrelAccessory: [],
                        barrelAccessories: [],
                        magazine: [],
                        scope: [],
                        scopeAccessory: [],
                        grip: [],
                        foregrip: [],
                        underbarrel: [],
                        daedalusAmmo: [], maliwanLicensedUnderbarrel: [],
                        licensedParts: [],
                        statModifier: [],
                        rarity: [],
                        manufacturerPerk: [],
                        // Shield parts
                        shield: [],
                        baseBody: [],
                        // Grenade parts
                        base: [],
                        payload: [],
                        augment: [],
                        payload245: [],
                        stats245: [],
                        augment245: [],
                        // Class Mod parts
                        skills: [],
                        stat234: [],
                        stat2_234: [],
                        statspecial_234: [],
                        firmware234: [],
                        // Enhancement parts
                        core: [],
                        baseBody247: [],
                        firmware247: [],
                        stat_247: [],
                        stat2_247: [],
                        stat3_247: [],
                        legendaryPerks: [],
                        // Repkit parts
                        legendaryPart: [],
                        firmware243: [],
                        elementalResistances243: [],
                        elementalImmunities243: [],
                        elementalSplats243: [],
                        elementalNovas243: [],
                        size243: [],
                        elemental243: [],
                        parts243: [],
                        // Heavy Weapon parts
                        firmware244: [],
                        // Grenade parts (typeId 245)
                        firmware245: [],
                        parts245: [],
                        // Shield parts (typeId 246, 237, 248)
                        primaryPerks246: [],
                        secondaryPerks246: [],
                        resistance246: [],
                        firmware246: [],
                        armor237: [],
                        energy248: [],
                        // Element parts (typeId 1)
                        element: []
                    };
                    
                    // Get all parts for current typeId
                    const ownParts = partsByTypeId.get(currentTypeId) || [];
                    
                    // Determine if we're working with an enhancement
                    // Check typeIdMap first, then fallback: infer from part paths (e.g. gadgets.enhancements.Atlas) so manufacturer-specific enhancements (284, 264, etc.) are detected
                    const typeInfo = typeIdMap.get(currentTypeId);
                    var isEnhancement = currentTypeId === 247 || 
                                        (typeInfo && (typeInfo.category && typeInfo.category.toLowerCase().includes('enhancement'))) ||
                                        (typeInfo && (typeInfo.name && typeInfo.name.toLowerCase().includes('enhancement')));
                    if (!isEnhancement && ownParts.length > 0) {
                        var hasEnhancementPath = ownParts.some(function (p) {
                            var path = String(p.path || '');
                            return path.indexOf('gadgets.enhancements') !== -1;
                        });
                        if (hasEnhancementPath) isEnhancement = true;
                    }
                    const isRepkit = currentTypeId === 243 || (typeInfo && typeInfo.category && typeInfo.category.toLowerCase().includes('repkit'));
                    const isGrenade = currentTypeId === 245 || (typeInfo && typeInfo.category && (typeInfo.category.toLowerCase().includes('grenade') || typeInfo.category.toLowerCase().includes('ordnance')));
                    const isClassMod = currentTypeId >= 254 && currentTypeId <= 259;
                    const isHeavyWeapon = currentTypeId === 244 || (typeInfo && typeInfo.category && typeInfo.category.toLowerCase().includes('heavy'));
                    // Shield detection: Check by TypeID first, then by category name
                    // Note: Shields can have various TypeIDs, but always use cross-typeId parts (246, 237, 248)
                    const isShield = currentTypeId === 246 || currentTypeId === 237 || currentTypeId === 248 || 
                                    (typeInfo && typeInfo.category && typeInfo.category.toLowerCase().includes('shield')) ||
                                    (typeInfo && typeInfo.name && typeInfo.name.toLowerCase().includes('shield'));
                    
                    // Debug logging for shield detection
                    if (categoryKey === 'baseBody') {
                        console.log(`[DEBUG shield baseBody locked] isShield detection: currentTypeId=${currentTypeId}, typeInfo.category=${typeInfo?.category}, typeInfo.name=${typeInfo?.name}, isShield=${isShield}`);
                    }
                    const isWeapon = !isEnhancement && !isRepkit && !isGrenade && !isClassMod && !isHeavyWeapon && !isShield &&
                                    (typeInfo && (typeInfo.category && typeInfo.category.toLowerCase().includes('weapon')));
                    
                    // Debug logging for baseBody247
                    if (categoryKey === 'baseBody247') {
                        console.log(`[DEBUG baseBody247 buildPartsByCategory] currentTypeId: ${currentTypeId}, isEnhancement: ${isEnhancement}, typeInfo:`, typeInfo);
                    }
                    
                    // Cross-typeId parts
                    const crossTypeIds = [];
                    if (isEnhancement) {
                        crossTypeIds.push(247);
                        if (categoryKey === 'baseBody247') {
                            console.log(`[DEBUG baseBody247] Added typeId 247 to crossTypeIds because isEnhancement=${isEnhancement}`);
                        }
                    }
                    // Special case: If we're looking for baseBody247, always include typeId 247 (even if not detected as enhancement)
                    // This ensures baseBody247 parts are available regardless of enhancement detection
                    if (categoryKey === 'baseBody247' && !crossTypeIds.includes(247) && partsByTypeId.has(247)) {
                        crossTypeIds.push(247);
                        console.log(`[DEBUG baseBody247] Added typeId 247 to crossTypeIds as fallback (categoryKey=baseBody247)`);
                    }
                    if (isRepkit) crossTypeIds.push(243);
                    if (isGrenade) {
                        crossTypeIds.push(245);
                        // Debug logging for grenade cross-typeIds
                        if (categoryKey === 'rarity' || categoryKey === 'body' || categoryKey === 'baseBody') {
                            console.log(`[DEBUG ordnance ${categoryKey} locked] Added typeId 245 to crossTypeIds because isGrenade=${isGrenade}`);
                        }
                    }
                    if (isClassMod) crossTypeIds.push(234);
                    if (isHeavyWeapon) crossTypeIds.push(244);
                    if (isShield) {
                        crossTypeIds.push(246);
                        crossTypeIds.push(237);
                        crossTypeIds.push(248);
                        // Debug logging for shield detection
                        if (categoryKey && (categoryKey === 'primaryPerks246' || categoryKey === 'secondaryPerks246' || categoryKey === 'perks246' || categoryKey === 'firmware246' || categoryKey === 'armor237' || categoryKey === 'energy248' || categoryKey === 'baseBody')) {
                            console.log(`[DEBUG shield] isShield=${isShield}, currentTypeId=${currentTypeId}, typeInfo:`, typeInfo);
                            console.log(`[DEBUG shield] Added crossTypeIds: 246, 237, 248`);
                        }
                    }
                    // For weapons, include typeId 4 (Body Accessories), typeId 17 (Barrel Accessories), typeId 9 (Licensed Parts), and typeId 13 (Licensed Parts)
                    if (isWeapon) {
                        if (partsByTypeId.has(4)) crossTypeIds.push(4);
                        if (partsByTypeId.has(17)) crossTypeIds.push(17);
                        if (partsByTypeId.has(9)) crossTypeIds.push(9);  // Licensed parts (typeId 9)
                        if (partsByTypeId.has(13)) crossTypeIds.push(13);  // Licensed parts (typeId 13)
                    }
                    // Always include TypeID 1 for elements if it exists (available for all item types)
                    if (partsByTypeId.has(1)) {
                        crossTypeIds.push(1);
                    }
                    
                    // Build allParts with deduplication to avoid duplicates
                    const allParts = [...ownParts];
                    const seenParts = new Set();
                    // Track parts by fullId to avoid duplicates
                    ownParts.forEach(p => {
                        const fullId = String(p.fullId || p.id || '');
                        if (fullId) seenParts.add(fullId);
                    });
                    
                    crossTypeIds.forEach(tid => {
                        if (partsByTypeId.has(tid)) {
                            const crossParts = partsByTypeId.get(tid) || [];
                            // Debug logging for shield cross-typeIds
                            if (isShield && (tid === 246 || tid === 237 || tid === 248)) {
                                console.log(`[DEBUG shield] Adding ${crossParts.length} parts from typeId ${tid} to allParts`);
                            }
                            crossParts.forEach(p => {
                                const fullId = String(p.fullId || p.id || '');
                                // Only add if not already seen (avoid duplicates)
                                if (fullId && !seenParts.has(fullId)) {
                                    allParts.push(p);
                                    seenParts.add(fullId);
                                    // Debug logging for shield parts being added
                                    if (isShield && (tid === 246 || tid === 237 || tid === 248)) {
                                        if (((categoryKey === 'primaryPerks246' || categoryKey === 'secondaryPerks246' || categoryKey === 'perks246') && tid === 246 && !String(p.spawnCode || '').includes('firmware') && !String(p.path || '').includes('firmware')) ||
                                            (categoryKey === 'firmware246' && tid === 246 && (String(p.spawnCode || '').includes('firmware') || String(p.path || '').includes('firmware'))) ||
                                            (categoryKey === 'armor237' && tid === 237) ||
                                            (categoryKey === 'energy248' && tid === 248)) {
                                            console.log(`[DEBUG shield ${categoryKey}] Added part to allParts: ${p.name || p.id} (typeId: ${tid}, fullId: ${fullId})`);
                                        }
                                    }
                                }
                            });
                        }
                    });
                    
                    // Debug: Check if typeId 247 parts are in allParts
                    if (categoryKey === 'baseBody247') {
                        console.log(`[DEBUG baseBody247] crossTypeIds:`, crossTypeIds);
                        console.log(`[DEBUG baseBody247] ownParts: ${ownParts.length}, allParts after crossTypeIds: ${allParts.length}`);
                        const type247InAllParts = allParts.filter(p => (p.typeId || currentTypeId) === 247);
                        console.log(`[DEBUG baseBody247] allParts contains ${type247InAllParts.length} typeId 247 parts out of ${allParts.length} total parts`);
                        const mainBodyInAllParts = type247InAllParts.filter(p => {
                            const path = String(p.path || '');
                            const partType = String(p.partType || '');
                            return path.includes('Main Body') || path.toLowerCase().includes('main body') || partType === 'Main Body' || partType.toLowerCase() === 'main body';
                        });
                        console.log(`[DEBUG baseBody247] allParts contains ${mainBodyInAllParts.length} Main Body parts`);
                        if (mainBodyInAllParts.length > 0) {
                            console.log(`[DEBUG baseBody247] Sample Main Body part in allParts:`, {
                                id: mainBodyInAllParts[0].id,
                                fullId: mainBodyInAllParts[0].fullId,
                                partType: mainBodyInAllParts[0].partType,
                                path: mainBodyInAllParts[0].path,
                                typeId: mainBodyInAllParts[0].typeId
                            });
                        } else if (type247InAllParts.length > 0) {
                            console.log(`[DEBUG baseBody247] Sample typeId 247 part (not Main Body):`, {
                                id: type247InAllParts[0].id,
                                fullId: type247InAllParts[0].fullId,
                                partType: type247InAllParts[0].partType,
                                path: type247InAllParts[0].path,
                                typeId: type247InAllParts[0].typeId
                            });
                        }
                    }
                    
                    // Debug: Log all parts with "underbarrel" in their partType or path for underbarrel debugging (locked path)
                    if (categoryKey === 'underbarrel') {
                        const underbarrelParts = allParts.filter(p => {
                            const pt = String(p.partType || '').toLowerCase();
                            const pp = String(p.path || '').toLowerCase();
                            const sc = String(p.spawnCode || '').toLowerCase();
                            return pt.includes('underbarrel') || pp.includes('underbarrel') || sc.includes('underbarrel') || sc.includes('part_underbarrel');
                        });
                        console.log(`[DEBUG underbarrel locked] Found ${underbarrelParts.length} parts with 'underbarrel' in partType/path/spawnCode out of ${allParts.length} total parts`);
                        if (underbarrelParts.length > 0) {
                            console.log(`[DEBUG underbarrel locked] Sample underbarrel-related parts:`, underbarrelParts.slice(0, 10).map(p => ({
                                id: p.id,
                                fullId: p.fullId,
                                name: p.name,
                                partType: p.partType,
                                path: p.path,
                                spawnCode: p.spawnCode,
                                typeId: p.typeId,
                                currentTypeId: currentTypeId
                            })));
                        }
                    }
                    
                    // Debug: Log allParts count for shield categories
                    if (isShield && (categoryKey === 'perks246' || categoryKey === 'firmware246' || categoryKey === 'armor237' || categoryKey === 'energy248')) {
                        const relevantParts = allParts.filter(p => {
                            const tid = p.typeId || currentTypeId;
                            return ((categoryKey === 'primaryPerks246' || categoryKey === 'secondaryPerks246' || categoryKey === 'perks246') && tid === 246 && !String(p.spawnCode || '').toLowerCase().includes('firmware') && !String(p.path || '').toLowerCase().includes('firmware')) ||
                                   (categoryKey === 'firmware246' && tid === 246 && (String(p.spawnCode || '').toLowerCase().includes('firmware') || String(p.path || '').toLowerCase().includes('firmware'))) ||
                                   (categoryKey === 'armor237' && tid === 237) ||
                                   (categoryKey === 'energy248' && tid === 248);
                        });
                        console.log(`[DEBUG shield ${categoryKey}] Starting categorization. allParts.length = ${allParts.length}, relevant parts count = ${relevantParts.length}`);
                    }
                    
                    // Debug: Log allParts count for grenade/ordnance categories
                    if (isGrenade && (categoryKey === 'rarity' || categoryKey === 'body' || categoryKey === 'baseBody')) {
                        const type245Parts = allParts.filter(p => p.typeId === 245);
                        const currentTypeIdParts = allParts.filter(p => p.typeId === currentTypeId);
                        console.log(`[DEBUG ordnance ${categoryKey} locked] Starting categorization. allParts.length = ${allParts.length}, typeId 245 parts: ${type245Parts.length}, currentTypeId ${currentTypeId} parts: ${currentTypeIdParts.length}`);
                        if (categoryKey === 'rarity') {
                            const rarityParts = allParts.filter(p => {
                                const pt = String(p.partType || '').toLowerCase();
                                const sc = String(p.spawnCode || '').toLowerCase();
                                return (p.typeId === currentTypeId || p.typeId === 245) && 
                                       (pt.includes('rarity') || pt === 'comp' || sc.includes('comp_') || sc.includes('rarity'));
                            });
                            console.log(`[DEBUG ordnance rarity locked] Rarity parts (typeId ${currentTypeId} or 245): ${rarityParts.length}`);
                        } else if (categoryKey === 'body' || categoryKey === 'baseBody') {
                            const bodyParts = allParts.filter(p => {
                                const pt = String(p.partType || '').toLowerCase();
                                const pp = String(p.path || '').toLowerCase();
                                return (p.typeId === currentTypeId || p.typeId === 245) && 
                                       (pt === 'base' || pp === 'base');
                            });
                            console.log(`[DEBUG ordnance ${categoryKey} locked] Body parts (typeId ${currentTypeId} or 245, partType='base'): ${bodyParts.length}`);
                        }
                    }
                    // Debug: Log allParts for baseBody category to see if shield body parts are present
                    if (isShield && categoryKey === 'baseBody') {
                        // Find actual Shield body parts (typeId 300, partType: Shield or spawnCode with part_body)
                        const actualShieldBodyParts = allParts.filter(p => {
                            const pt = String(p.partType || '').toLowerCase();
                            const opt = String(p.partType || '');
                            const sc = String(p.spawnCode || '').toLowerCase();
                            const tid = p.typeId;
                            return tid === currentTypeId && (pt === 'shield' || opt === 'Shield' || sc.includes('part_body'));
                        });
                        // Also find any parts with shield in spawnCode/path (broader match)
                        const shieldRelatedParts = allParts.filter(p => {
                            const pt = String(p.partType || '').toLowerCase();
                            const pp = String(p.path || '').toLowerCase();
                            const sc = String(p.spawnCode || '').toLowerCase();
                            return pt === 'shield' || pp.includes('shield') || sc.includes('shield') || sc.includes('part_body');
                        });
                        console.log(`[DEBUG shield baseBody] Starting categorization. allParts.length = ${allParts.length}, currentTypeId = ${currentTypeId}, ownParts.length = ${ownParts.length}`);
                        console.log(`[DEBUG shield baseBody] Actual Shield body parts (typeId ${currentTypeId}, partType: Shield or spawnCode with part_body): ${actualShieldBodyParts.length}, shield-related parts: ${shieldRelatedParts.length}`);
                        if (actualShieldBodyParts.length > 0) {
                            console.log(`[DEBUG shield baseBody] Actual Shield body parts:`, actualShieldBodyParts.map(p => ({
                                name: p.name,
                                id: p.id,
                                fullId: p.fullId,
                                typeId: p.typeId,
                                partType: p.partType,
                                path: p.path,
                                spawnCode: p.spawnCode
                            })));
                        } else if (shieldRelatedParts.length > 0) {
                            console.log(`[DEBUG shield baseBody] No actual Shield body parts found, but found ${shieldRelatedParts.length} shield-related parts. Sample:`, shieldRelatedParts.slice(0, 5).map(p => ({
                                name: p.name,
                                id: p.id,
                                fullId: p.fullId,
                                typeId: p.typeId,
                                partType: p.partType,
                                path: p.path,
                                spawnCode: p.spawnCode
                            })));
                        } else {
                            // Check if parts from currentTypeId exist at all
                            const ownTypeIdParts = allParts.filter(p => p.typeId === currentTypeId);
                            console.log(`[DEBUG shield baseBody] No shield body parts found. Parts from currentTypeId ${currentTypeId}: ${ownTypeIdParts.length}`);
                            if (ownTypeIdParts.length > 0) {
                                console.log(`[DEBUG shield baseBody] Sample parts from currentTypeId:`, ownTypeIdParts.slice(0, 5).map(p => ({
                                    name: p.name,
                                    id: p.id,
                                    fullId: p.fullId,
                                    typeId: p.typeId,
                                    partType: p.partType,
                                    path: p.path,
                                    spawnCode: p.spawnCode
                                })));
                            }
                        }
                    }
                    
                    // Categorize parts
                    allParts.forEach(partInfo => {
                        const partType = String(partInfo.partType || '').toLowerCase();
                        const partPath = String(partInfo.path || '').toLowerCase();
                        const partName = String(partInfo.name || '').toLowerCase();
                        const spawnCode = String(partInfo.spawnCode || '').toLowerCase();
                        // IMPORTANT: Use partInfo.typeId directly, don't fallback to currentTypeId
                        // This ensures cross-typeId parts (246, 237, 248) are identified correctly
                        // Use 0 as fallback instead of currentTypeId to avoid mis-categorizing cross-typeId parts
                        const partTypeId = (partInfo.typeId !== undefined && partInfo.typeId !== null) ? partInfo.typeId : 0;
                        
                        // Debug logging for grenade/ordnance parts
                        if (isGrenade && (categoryKey === 'rarity' || categoryKey === 'body' || categoryKey === 'baseBody')) {
                            const isRarityPart = partType.includes('rarity') || partType === 'comp' || spawnCode.includes('comp_') || spawnCode.includes('rarity');
                            const isBodyPart = partType === 'base' || partPath === 'base';
                            if ((categoryKey === 'rarity' && isRarityPart && (partTypeId === currentTypeId || partTypeId === 245)) ||
                                ((categoryKey === 'body' || categoryKey === 'baseBody') && isBodyPart && (partTypeId === currentTypeId || partTypeId === 245))) {
                                console.log(`[DEBUG ordnance ${categoryKey} locked] Processing part: ${partInfo.name || partInfo.id} (partTypeId: ${partTypeId}, currentTypeId: ${currentTypeId}, partType: ${partType}, path: ${partPath}, spawnCode: ${spawnCode})`);
                            }
                        }
                        
                        // Debug: Log all parts with typeId matching currentTypeId when looking for baseBody
                        if (isShield && categoryKey === 'baseBody' && partInfo.typeId === currentTypeId) {
                            console.log(`[DEBUG shield baseBody locked] Processing part with matching typeId: ${partInfo.name || partInfo.id} (partInfo.typeId: ${partInfo.typeId}, partTypeId: ${partTypeId}, currentTypeId: ${currentTypeId}, partType: ${partType}, originalPartType: ${String(partInfo.partType || '')}, spawnCode: ${spawnCode}, path: ${partPath})`);
                        }
                        
                        // Debug logging for shield parts to verify typeId
                        if (isShield && (categoryKey === 'perks246' || categoryKey === 'firmware246' || categoryKey === 'armor237' || categoryKey === 'energy248')) {
                            if (((categoryKey === 'primaryPerks246' || categoryKey === 'secondaryPerks246' || categoryKey === 'perks246') && partTypeId === 246 && !String(partInfo.spawnCode || '').toLowerCase().includes('firmware') && !String(partInfo.path || '').toLowerCase().includes('firmware')) ||
                                (categoryKey === 'firmware246' && partTypeId === 246 && (String(partInfo.spawnCode || '').toLowerCase().includes('firmware') || String(partInfo.path || '').toLowerCase().includes('firmware'))) ||
                                (categoryKey === 'armor237' && partTypeId === 237) ||
                                (categoryKey === 'energy248' && partTypeId === 248)) {
                                console.log(`[DEBUG shield ${categoryKey}] Processing part: ${partInfo.name || partInfo.id} (partInfo.typeId: ${partInfo.typeId}, partTypeId: ${partTypeId}, currentTypeId: ${currentTypeId})`);
                            }
                        }
                        
                        // Get original (non-lowercased) partType and path for exact matching
                        const originalPartType = String(partInfo.partType || '');
                        const originalPartPath = String(partInfo.path || '');
                        
                        // Check for licensed parts BEFORE other typeId-specific checks so they're properly categorized
                        // Licensed parts can ALSO be barrel, magazine, etc., so we add to licensedParts but continue categorization
                        // Also include ALL parts from "Manufacturer Part" part_type (even if spawn code doesn't contain "licensed")
                        const isLicensed = (spawnCode.includes('licensed') || 
                                           spawnCode.includes('_licensed_') ||
                                           partPath.includes('licensed') ||
                                           partName.includes('licensed') ||
                                           partType === 'manufacturer part' ||
                                           originalPartType === 'Manufacturer Part' ||
                                           originalPartPath.includes('Manufacturer Part') ||
                                           (partType === 'manufacturer part' && (spawnCode.includes('_licensed_') || spawnCode.includes('.licensed'))));
                        
                        // Grenade/Ordnance parts - CHECK FIRST to ensure they're categorized correctly
                        // Rarity parts from grenade's own typeId OR typeId 245 should be included
                        if (isGrenade && (partTypeId === currentTypeId || partTypeId === 245) && 
                            (spawnCode.includes('comp_') || partType === 'comp' || partType.includes('rarity') || spawnCode.includes('rarity') ||
                             // Also check if it's from Rarities section (parts with rarity field or in Rarities path)
                             partPath.includes('rarities') || partInfo.rarity || 
                             // Check if partType is a rarity name
                             partType === 'legendary' || partType === 'epic' || partType === 'rare' || partType === 'uncommon' || partType === 'common')) {
                            categoryMap.rarity.push(partInfo);
                            // Debug logging for grenade/ordnance rarity
                            if (categoryKey === 'rarity') {
                                console.log(`[DEBUG ordnance rarity locked] ✅ Categorized (early check): ${partInfo.name || partInfo.id} (partTypeId: ${partTypeId}, currentTypeId: ${currentTypeId}, partType: ${partType}, spawnCode: ${spawnCode}, rarity: ${partInfo.rarity}, path: ${partPath})`);
                            }
                            // Skip to next part - don't check other conditions
                            return;
                        }
                        // Body parts from grenade's own typeId OR typeId 245 should be included
                        else if (isGrenade && (partTypeId === currentTypeId || partTypeId === 245)) {
                            // Check if it's a body/base part
                            const isBasePart = partType === 'base' || partPath === 'base' || 
                                             spawnCode.includes('part_ord') || spawnCode.includes('ord_grenade') ||
                                             originalPartType === 'Base' || originalPartPath === 'Base';
                            
                            // Debug logging for grenade/ordnance body parts being checked
                            if (categoryKey === 'body' || categoryKey === 'baseBody') {
                                console.log(`[DEBUG ordnance ${categoryKey} locked] 🔍 Checking body part: ${partInfo.name || partInfo.id} (partTypeId: ${partTypeId}, currentTypeId: ${currentTypeId}, partType: ${partType}, originalPartType: ${originalPartType}, path: ${partPath}, originalPartPath: ${originalPartPath}, spawnCode: ${spawnCode}, isBasePart: ${isBasePart})`);
                            }
                            
                            if (isBasePart) {
                                categoryMap.base.push(partInfo);
                                categoryMap.baseBody.push(partInfo);
                                // For grenades, also add to body category (body and baseBody are the same for grenades)
                                categoryMap.body.push(partInfo);
                                // Debug logging for grenade/ordnance body
                                if (categoryKey === 'body' || categoryKey === 'baseBody') {
                                    console.log(`[DEBUG ordnance ${categoryKey} locked] ✅ Categorized (early check): ${partInfo.name || partInfo.id} (partTypeId: ${partTypeId}, currentTypeId: ${currentTypeId}, partType: ${partType}, path: ${partPath}, spawnCode: ${spawnCode})`);
                                }
                                // Skip to next part - don't check other conditions
                                return;
                            }
                        }
                        
                        // Enhancement parts (current typeId) - rarity, so manufacturer-specific enhancements (284, 264, etc.) show Rarity and other parts
                        if (isEnhancement && partTypeId === currentTypeId) {
                            if (partPath.indexOf('rarities') !== -1 || partInfo.rarity || partType.indexOf('rarity') !== -1 || partType === 'comp' || spawnCode.indexOf('comp_') !== -1) {
                                categoryMap.rarity.push(partInfo);
                                return;
                            }
                        }
                        
                        // Shield parts (typeId 246, 237, 248) - CHECK FIRST to ensure they're categorized correctly
                        // These parts should always be included when isShield is true, regardless of currentTypeId
                        // IMPORTANT: Check these BEFORE all other conditions to ensure they're categorized correctly
                        // Use Number() to ensure type comparison works correctly
                        if (isShield && Number(partTypeId) === 246) {
                            // Extract part ID to check if it's a resistance part (246:21-246:26)
                            let partIdNum = null;
                            const partIdStr = String(partInfo.id || partInfo.fullId || '');
                            if (partIdStr.includes(':')) {
                                const parts = partIdStr.split(':');
                                if (parts.length >= 2) {
                                    partIdNum = parseInt(parts[parts.length - 1]);
                                }
                            } else if (!isNaN(parseInt(partIdStr))) {
                                partIdNum = parseInt(partIdStr);
                            }
                            
                            // Check if it's a resistance part (IDs 21-26)
                            const isResistance = partIdNum !== null && partIdNum >= 21 && partIdNum <= 26;
                            
                            if (spawnCode.includes('firmware') || partPath.includes('firmware')) {
                                categoryMap.firmware246.push(partInfo);
                                // Debug logging for shield parts
                                if (categoryKey === 'firmware246') {
                                    console.log(`[DEBUG shield firmware246 locked] ✅ Categorized: ${partInfo.name || partInfo.id} (typeId: ${partTypeId}, spawnCode: ${spawnCode})`);
                                }
                            } else if (isResistance || spawnCode.includes('part_corrosive') || spawnCode.includes('part_cryo') || 
                                       spawnCode.includes('part_fire') || spawnCode.includes('part_radiation') || spawnCode.includes('part_shock')) {
                                // Resistance parts (246:21-246:26)
                                categoryMap.resistance246.push(partInfo);
                                // Debug logging for shield parts
                                if (categoryKey === 'resistance246') {
                                    console.log(`[DEBUG shield resistance246 locked] ✅ Categorized: ${partInfo.name || partInfo.id} (typeId: ${partTypeId}, partId: ${partIdNum}, spawnCode: ${spawnCode})`);
                                }
                            } else {
                                if (spawnCode.includes('_primary') || partPath.includes('primary') || partName.includes('primary')) {
                                    categoryMap.primaryPerks246.push(partInfo);
                                    // Debug logging for shield parts
                                    if (categoryKey === 'primaryPerks246' || categoryKey === 'perks246') {
                                        console.log(`[DEBUG shield primaryPerks246 locked] ✅ Categorized: ${partInfo.name || partInfo.id} (typeId: ${partTypeId}, spawnCode: ${spawnCode})`);
                                    }
                                } else if (spawnCode.includes('_secondary') || partPath.includes('secondary') || partName.includes('secondary')) {
                                    categoryMap.secondaryPerks246.push(partInfo);
                                    // Debug logging for shield parts
                                    if (categoryKey === 'secondaryPerks246' || categoryKey === 'perks246') {
                                        console.log(`[DEBUG shield secondaryPerks246 locked] ✅ Categorized: ${partInfo.name || partInfo.id} (typeId: ${partTypeId}, spawnCode: ${spawnCode})`);
                                    }
                                } else {
                                    // If we can't determine, default to primary (fallback)
                                    categoryMap.primaryPerks246.push(partInfo);
                                    // Debug logging for shield parts
                                    if (categoryKey === 'primaryPerks246' || categoryKey === 'perks246') {
                                        console.log(`[DEBUG shield primaryPerks246 locked] ✅ Categorized (fallback): ${partInfo.name || partInfo.id} (typeId: ${partTypeId}, spawnCode: ${spawnCode})`);
                                    }
                                }
                            }
                            // Skip to next part - don't check other conditions
                            return;
                        } else if (isShield && Number(partTypeId) === 237) {
                            categoryMap.armor237.push(partInfo);
                            // Debug logging for shield parts
                            if (categoryKey === 'armor237') {
                                console.log(`[DEBUG shield armor237 locked] ✅ Categorized: ${partInfo.name || partInfo.id} (typeId: ${partTypeId}, spawnCode: ${spawnCode})`);
                            }
                            // Skip to next part - don't check other conditions
                            return;
                        } else if (isShield && Number(partTypeId) === 248) {
                            categoryMap.energy248.push(partInfo);
                            // Debug logging for shield parts
                            if (categoryKey === 'energy248') {
                                console.log(`[DEBUG shield energy248 locked] ✅ Categorized: ${partInfo.name || partInfo.id} (typeId: ${partTypeId}, spawnCode: ${spawnCode})`);
                            }
                            // Skip to next part - don't check other conditions
                            return;
                        }
                        
                        // Debug: Log underbarrel parts that match spawnCode but might be caught by earlier conditions (locked path)
                        if (categoryKey === 'underbarrel' && (spawnCode.includes('part_underbarrel') || spawnCode.includes('underbarrel'))) {
                            console.log(`[DEBUG underbarrel locked] Processing part with underbarrel in spawnCode: ${partInfo.name} (id: ${partInfo.id}, fullId: ${partInfo.fullId}, partType: ${originalPartType}, path: ${originalPartPath}, spawnCode: ${partInfo.spawnCode}, typeId: ${partTypeId}, currentTypeId: ${currentTypeId})`);
                        }
                        
                        // Weapon parts
                        // IMPORTANT: Check underbarrel BEFORE barrel to prevent underbarrel parts from being misclassified as barrel
                        if (partType === 'underbarrel' || partType.includes('underbarrel') ||
                            originalPartType === 'Underbarrel' || originalPartPath.includes('Underbarrel') ||
                            partPath.includes('underbarrel') || spawnCode.includes('underbarrel') ||
                            spawnCode.includes('part_underbarrel')) {
                            // Underbarrel check MUST come BEFORE barrel to prevent misclassification
                            // Also check for "part_underbarrel" in spawnCode for parts with empty part_type
                            if (partTypeId === currentTypeId) {
                                categoryMap.underbarrel.push(partInfo);
                                // Debug logging for underbarrel
                                if (categoryKey === 'underbarrel') {
                                    console.log(`[DEBUG underbarrel locked] ✅ Categorized: ${partInfo.name} (partType: ${originalPartType}, path: ${originalPartPath}, spawnCode: ${partInfo.spawnCode}, typeId: ${partTypeId}, currentTypeId: ${currentTypeId})`);
                                }
                            } else if (categoryKey === 'underbarrel') {
                                console.log(`[DEBUG underbarrel locked] ❌ Skipped (wrong typeId): ${partInfo.name} (partType: ${originalPartType}, path: ${originalPartPath}, spawnCode: ${partInfo.spawnCode}, typeId: ${partTypeId}, currentTypeId: ${currentTypeId})`);
                            }
                        } else if (partType === 'body accessory' || (partType.includes('body') && partType.includes('accessory')) ||
                            originalPartType === 'Body Accessory' || originalPartPath.includes('Body Accessory') ||
                            partPath.includes('body accessory') || (partPath.includes('body') && partPath.includes('accessory')) ||
                            // Body accessories have spawnCodes like "part_body_a", "part_body_b", etc. (letters, not numbers like base body parts)
                            // BUT exclude shield body parts (they have partType === 'shield' and spawnCodes like bor_shield.part_body_energy_*)
                            (spawnCode.includes('part_body_') && !spawnCode.match(/part_body_0[1-5]/) && !spawnCode.match(/part_body_[1-5]\b/) && 
                             !(partType === 'shield' || originalPartType === 'Shield' || spawnCode.includes('bor_shield.part_body')))) {
                            // Body Accessory check MUST come BEFORE generic body check to prevent misclassification
                            if (partTypeId === currentTypeId) {
                                categoryMap.bodyAccessory.push(partInfo);
                                categoryMap.bodyAccessories.push(partInfo); // Also add to plural key for compatibility
                                // Debug logging for body accessory
                                if (categoryKey === 'bodyAccessory' || categoryKey === 'bodyAccessories') {
                                    console.log(`[DEBUG bodyAccessory locked] ✅ Categorized: ${partInfo.name} (partType: ${originalPartType}, path: ${originalPartPath}, spawnCode: ${partInfo.spawnCode}, typeId: ${partTypeId}, currentTypeId: ${currentTypeId})`);
                                }
                            } else if (categoryKey === 'bodyAccessory' || categoryKey === 'bodyAccessories') {
                                console.log(`[DEBUG bodyAccessory locked] ❌ Skipped (wrong typeId): ${partInfo.name} (partType: ${originalPartType}, path: ${originalPartPath}, spawnCode: ${partInfo.spawnCode}, typeId: ${partTypeId}, currentTypeId: ${currentTypeId})`);
                            }
                        } else if (partType === 'body' || (partType.includes('body') && !partType.includes('accessory') && !partType.includes('base'))) {
                            if (partTypeId === currentTypeId) {
                                categoryMap.body.push(partInfo);
                                // Debug: Log if shield body parts are being caught by body check
                                if (isShield && categoryKey === 'baseBody' && (partType === 'shield' || spawnCode.includes('part_body'))) {
                                    console.log(`[DEBUG shield baseBody locked] ⚠️ Shield body part caught by body check: ${partInfo.name || partInfo.id} (partType: ${partType}, spawnCode: ${spawnCode})`);
                                }
                            }
                        } else if (partType === 'barrel accessory' || (partType.includes('barrel') && partType.includes('accessory')) ||
                                   originalPartType === 'Barrel Accessory' || originalPartPath.includes('Barrel Accessory') ||
                                   partPath.includes('barrel accessory') || (partPath.includes('barrel') && partPath.includes('accessory')) ||
                                   (spawnCode.includes('barrel') && spawnCode.includes('accessory')) ||
                                   // Check for barrel accessory spawn code pattern: part_barrel_XX_[a-z] (letter suffix indicates accessory)
                                   // Pattern matches: part_barrel_ followed by digits, underscore, and a single letter (a-z)
                                   (spawnCode.includes('part_barrel_') && /part_barrel_\d+_[a-z]\b/i.test(spawnCode))) {
                            // Barrel Accessory check MUST come BEFORE generic barrel check to prevent misclassification
                            // Also check for "part_barrel" in spawnCode for parts with empty part_type
                            if (partTypeId === currentTypeId) {
                                categoryMap.barrelAccessory.push(partInfo);
                                categoryMap.barrelAccessories.push(partInfo); // Also add to plural key for compatibility
                                // Debug logging for barrel accessory
                                if (categoryKey === 'barrelAccessory' || categoryKey === 'barrelAccessories') {
                                    console.log(`[DEBUG barrelAccessory locked] ✅ Categorized: ${partInfo.name} (partType: ${originalPartType}, path: ${originalPartPath}, spawnCode: ${partInfo.spawnCode})`);
                                }
                            }
                            // Skip rest of categorization to avoid duplicates
                            return;
                        } else if (partType === 'barrel' || (partType.includes('barrel') && !partType.includes('accessory')) ||
                                   (spawnCode.includes('barrel') && !spawnCode.includes('accessory') && !spawnCode.includes('barrel accessory') &&
                                    // Exclude barrel accessories with letter suffix pattern (part_barrel_XX_[a-z])
                                    !/part_barrel_\d+_[a-z]\b/i.test(spawnCode) &&
                                    // Exclude licensed parts - they should only appear in licensedParts category
                                    !isLicensed)) {
                            // For weapons, only show barrel parts from the current weapon's typeId
                            // Licensed barrel parts should be in the licensedParts category, not barrel category
                            if (isWeapon) {
                                // Only include barrel parts that match the current weapon's typeId
                                if (partTypeId === currentTypeId) {
                                    categoryMap.barrel.push(partInfo);
                                }
                            } else {
                                // For non-weapons, include all barrel parts
                                categoryMap.barrel.push(partInfo);
                            }
                        } else if (partType === 'magazine' || partType.includes('magazine')) {
                            if (partTypeId === currentTypeId) categoryMap.magazine.push(partInfo);
                        } else if (partType === 'scope' || (partType.includes('scope') && !partType.includes('accessory'))) {
                            if (partTypeId === currentTypeId) categoryMap.scope.push(partInfo);
                        } else if (partType === 'scope accessory' || (partType.includes('scope') && partType.includes('accessory')) ||
                                   originalPartType === 'Scope Accessory' || originalPartPath.includes('Scope Accessory') ||
                                   partPath.includes('scope accessory') || (partPath.includes('scope') && partPath.includes('accessory'))) {
                            if (partTypeId === currentTypeId) categoryMap.scopeAccessory.push(partInfo);
                        } else if (partType === 'grip' || (partType.includes('grip') && !partType.includes('foregrip'))) {
                            if (partTypeId === currentTypeId) categoryMap.grip.push(partInfo);
                        } else if (partType === 'foregrip' || partType.includes('foregrip') ||
                                   originalPartType === 'Foregrip' || originalPartPath.includes('Foregrip') ||
                                   partPath.includes('foregrip') || spawnCode.includes('foregrip')) {
                            if (partTypeId === currentTypeId) categoryMap.foregrip.push(partInfo);
                        } else if (partType === 'stat modifier' || (partType.includes('stat') && partType.includes('modifier'))) {
                            if (partTypeId === currentTypeId) {
                                categoryMap.statModifier.push(partInfo);
                                // Debug: Log if shield body parts are being caught by stat modifier check
                                if (isShield && categoryKey === 'baseBody' && (partType === 'shield' || spawnCode.includes('part_body'))) {
                                    console.log(`[DEBUG shield baseBody locked] ⚠️ Shield body part caught by stat modifier check: ${partInfo.name || partInfo.id} (partType: ${partType}, spawnCode: ${spawnCode})`);
                                }
                            }
                        }
                        // Shield body parts (from shield's own typeId, e.g., 300 for Ripper) - CHECK BEFORE RARITY
                        // These are the main body parts for shields (e.g., "Sparky", "Firebreak" for Ripper shields)
                        // IMPORTANT: For shields, Base Body and Legendary Part are one and the same!
                        // Match when:
                        // 1. It's a shield item (isShield is true)
                        // 2. The part's typeId matches the current shield's typeId (e.g., 300 for Ripper)
                        // 3. AND (partType is "shield" OR spawnCode includes "part_body" OR path includes "shield")
                        // IMPORTANT: Only match if it's actually a shield body part, not just any part with matching typeId (e.g., rarity parts)
                        else if (isShield && Number(partTypeId) === Number(currentTypeId) && 
                                 (partType === 'shield' || spawnCode.includes('part_body') || partPath.includes('shield') || originalPartType === 'Shield')) {
                            // This is a shield body part from the shield's own typeId
                            categoryMap.shield.push(partInfo);
                            categoryMap.baseBody.push(partInfo);
                            // For shields, Base Body = Legendary Part (they are one and the same)
                            categoryMap.legendaryPart.push(partInfo);
                            // Debug logging for shield body parts
                            if (categoryKey === 'baseBody' || categoryKey === 'legendaryPart') {
                                console.log(`[DEBUG shield ${categoryKey} locked] ✅✅✅ Categorized: ${partInfo.name || partInfo.id} (partInfo.typeId: ${partInfo.typeId}, partTypeId: ${partTypeId}, currentTypeId: ${currentTypeId}, partType: ${partType}, originalPartType: ${originalPartType}, spawnCode: ${spawnCode}, path: ${partPath})`);
                            }
                        }
                        // Rarity - check for enhancements first to ensure we catch all rarity parts
                        else if (partType.includes('rarity') || partType === 'comp' || 
                                 partPath.includes('rarity') || partName.includes('rarity') || 
                                 spawnCode.includes('rarity') || spawnCode.includes('comp_') || 
                                 (partInfo.string && String(partInfo.string).toLowerCase().includes('comp_')) ||
                                 // For enhancements, also check if partType is a rarity name (Legendary, Epic, Rare, Uncommon, Common)
                                 (isEnhancement && partTypeId === currentTypeId && 
                                  (partType === 'legendary' || partType === 'epic' || partType === 'rare' || 
                                   partType === 'uncommon' || partType === 'common')) ||
                                 // Check if path indicates it's from Rarities section
                                 (isEnhancement && partTypeId === currentTypeId && partPath.toLowerCase().includes('rarities')) ||
                                 // For grenades, include rarity parts from typeId 245 (cross-typeId parts)
                                 (isGrenade && partTypeId === 245 && (spawnCode.includes('comp_') || partType === 'comp' || partType.includes('rarity')))) {
                            // For grenades, include rarity parts from typeId 245 even if currentTypeId is different
                            if (partTypeId === currentTypeId || (isGrenade && partTypeId === 245)) {
                                categoryMap.rarity.push(partInfo);
                                // Debug logging for grenade/ordnance rarity
                                if (isGrenade && categoryKey === 'rarity') {
                                    console.log(`[DEBUG ordnance rarity locked] ✅ Categorized: ${partInfo.name || partInfo.id} (partTypeId: ${partTypeId}, currentTypeId: ${currentTypeId}, partType: ${partType}, spawnCode: ${spawnCode})`);
                                }
                                // Debug: Log if shield body parts are being caught by rarity check
                                if (isShield && categoryKey === 'baseBody' && (partType === 'shield' || spawnCode.includes('part_body'))) {
                                    console.log(`[DEBUG shield baseBody locked] ⚠️ Shield body part caught by rarity check: ${partInfo.name || partInfo.id} (partType: ${partType}, spawnCode: ${spawnCode})`);
                                }
                            }
                        }
                        // Enhancement Manufacturer Perks (legendaryPerks) - only current typeId when master unlock is off
                        else if (isEnhancement && partTypeId === currentTypeId) {
                            const partIdStr = String(partInfo.id || partInfo.fullId || '');
                            let partIdNum = null;
                            if (partIdStr.includes(':')) {
                                const parts = partIdStr.split(':');
                                if (parts.length >= 2 && parts[0] === String(currentTypeId)) {
                                    partIdNum = parseInt(parts[parts.length - 1]);
                                }
                            } else {
                                partIdNum = parseInt(partIdStr);
                            }
                            // Manufacturer perks are parts with IDs 1, 2, 3, 9 that have part_core in their identifiers
                            const isManufacturerPerk = !isNaN(partIdNum) && (partIdNum === 1 || partIdNum === 2 || partIdNum === 3 || partIdNum === 9);
                            const hasPartCore = spawnCode.includes('part_core') || partName.includes('part_core') || 
                                               (partInfo.string && String(partInfo.string).toLowerCase().includes('part_core'));
                            if (isManufacturerPerk && hasPartCore) {
                                categoryMap.legendaryPerks.push(partInfo);
                            }
                        }
                        // Shield parts (body parts from shield manufacturers, e.g., "Shield" partType)
                        // These are the main body parts for shields (e.g., "Sparky", "Firebreak" for Ripper shields)
                        // IMPORTANT: For shields, Base Body and Legendary Part are one and the same!
                        // Match when:
                        // 1. It's a shield item (isShield is true)
                        // 2. The part's typeId matches the current shield's typeId (e.g., 300 for Ripper)
                        // 3. AND (partType is "shield" OR spawnCode includes "part_body" OR path includes "Shield")
                        // 4. CRITICAL: ONLY allow known shield typeIds - exclude grenade and repkit typeIds
                        // This prevents grenade/repkit parts from appearing in shield body categories when master unlock is enabled
                        // Don't match parts with "shield" in spawnCode/path that are perks/firmware/armor/energy (typeIds 246/237/248)
                        else if (isShield && Number(partTypeId) === Number(currentTypeId) &&
                                 knownShieldTypeIds.has(partTypeId) && !knownGrenadeTypeIds.has(partTypeId) && !knownRepkitTypeIds.has(partTypeId)) {
                            // Debug: Log that we're checking this part
                            if (categoryKey === 'baseBody') {
                                console.log(`[DEBUG shield baseBody locked] ✅ Reached shield body check for: ${partInfo.name || partInfo.id} (isShield: ${isShield}, partTypeId: ${partTypeId}, currentTypeId: ${currentTypeId}, partType: ${partType}, originalPartType: ${originalPartType}, spawnCode: ${spawnCode}, partPath: ${partPath})`);
                            }
                            
                            // Check if it matches shield body part criteria
                            const matchesShieldBody = partType === 'shield' || spawnCode.includes('part_body') || partPath.includes('shield') || originalPartType === 'Shield';
                            
                            if (categoryKey === 'baseBody') {
                                console.log(`[DEBUG shield baseBody locked] matchesShieldBody check: ${matchesShieldBody} (partType==='shield': ${partType === 'shield'}, spawnCode.includes('part_body'): ${spawnCode.includes('part_body')}, partPath.includes('shield'): ${partPath.includes('shield')}, originalPartType==='Shield': ${originalPartType === 'Shield'})`);
                            }
                            
                            if (matchesShieldBody) {
                                // This is a shield body part from the shield's own typeId
                                categoryMap.shield.push(partInfo);
                                categoryMap.baseBody.push(partInfo);
                                // For shields, Base Body = Legendary Part (they are one and the same)
                                categoryMap.legendaryPart.push(partInfo);
                                // Debug logging for shield body parts
                                if (categoryKey === 'baseBody' || categoryKey === 'legendaryPart') {
                                    console.log(`[DEBUG shield ${categoryKey}] ✅✅✅ Categorized: ${partInfo.name || partInfo.id} (partInfo.typeId: ${partInfo.typeId}, partTypeId: ${partTypeId}, currentTypeId: ${currentTypeId}, partType: ${partType}, originalPartType: ${originalPartType}, spawnCode: ${spawnCode}, path: ${partPath})`);
                                }
                            } else if (categoryKey === 'baseBody' || categoryKey === 'legendaryPart') {
                                // Debug: Log why it didn't match
                                console.log(`[DEBUG shield ${categoryKey}] ❌ NOT categorized: ${partInfo.name || partInfo.id} (partInfo.typeId: ${partInfo.typeId}, partTypeId: ${partTypeId}, currentTypeId: ${currentTypeId}, partType: ${partType}, originalPartType: ${originalPartType}, spawnCode: ${spawnCode}, path: ${partPath}, matchesShieldBody: ${matchesShieldBody})`);
                            }
                        } else if (isShield && categoryKey === 'baseBody' && partTypeId === currentTypeId && (partType === 'shield' || spawnCode.includes('part_body') || partPath.includes('shield') || originalPartType === 'Shield')) {
                            // Debug: This part should have matched but didn't - log why
                            console.log(`[DEBUG shield baseBody locked] ⚠️ Part should match but condition failed: ${partInfo.name || partInfo.id} (isShield: ${isShield}, partTypeId: ${partTypeId}, currentTypeId: ${currentTypeId}, Number(partTypeId): ${Number(partTypeId)}, Number(currentTypeId): ${Number(currentTypeId)}, Number(partTypeId) === Number(currentTypeId): ${Number(partTypeId) === Number(currentTypeId)})`);
                        }
                        // Additional explicit check for shield body parts by spawnCode pattern
                        // This ensures we catch shield body parts even if they don't match the above conditions
                        // CRITICAL: ONLY allow known shield typeIds - exclude grenade and repkit typeIds
                        else if (isShield && spawnCode.includes('part_body') && 
                                 Number(partTypeId) === Number(currentTypeId) &&
                                 partTypeId !== 246 && partTypeId !== 237 && partTypeId !== 248 &&
                                 knownShieldTypeIds.has(partTypeId) && !knownGrenadeTypeIds.has(partTypeId) && !knownRepkitTypeIds.has(partTypeId)) {
                            // This is a shield body part (not a perk/firmware/armor/energy part, and not grenade/repkit)
                            categoryMap.shield.push(partInfo);
                            categoryMap.baseBody.push(partInfo);
                            // For shields, Base Body = Legendary Part (they are one and the same)
                            categoryMap.legendaryPart.push(partInfo);
                            // Debug logging
                            if (categoryKey === 'baseBody' || categoryKey === 'legendaryPart') {
                                console.log(`[DEBUG shield ${categoryKey}] ✅ Categorized (fallback): ${partInfo.name || partInfo.id} (partInfo.typeId: ${partInfo.typeId}, partTypeId: ${partTypeId}, currentTypeId: ${currentTypeId}, spawnCode: ${spawnCode})`);
                            }
                        }
                        // Rarity - check for enhancements first to ensure we catch all rarity parts
                        else if (partType.includes('rarity') || partType === 'comp' || 
                                 partPath.includes('rarity') || partName.includes('rarity') || 
                                 spawnCode.includes('rarity') || spawnCode.includes('comp_') || 
                                 (partInfo.string && String(partInfo.string).toLowerCase().includes('comp_')) ||
                                 // For enhancements, also check if partType is a rarity name (Legendary, Epic, Rare, Uncommon, Common)
                                 (isEnhancement && partTypeId === currentTypeId && 
                                  (partType === 'legendary' || partType === 'epic' || partType === 'rare' || 
                                   partType === 'uncommon' || partType === 'common')) ||
                                 // Check if path indicates it's from Rarities section
                                 (isEnhancement && partTypeId === currentTypeId && partPath.toLowerCase().includes('rarities'))) {
                            if (partTypeId === currentTypeId) {
                                categoryMap.rarity.push(partInfo);
                                // Debug: Log if shield body parts are being caught by rarity check
                                if (isShield && categoryKey === 'baseBody' && (partType === 'shield' || spawnCode.includes('part_body'))) {
                                    console.log(`[DEBUG shield baseBody locked] ⚠️ Shield body part caught by rarity check: ${partInfo.name || partInfo.id} (partType: ${partType}, spawnCode: ${spawnCode})`);
                                }
                            }
                        }
                        // Grenade parts
                        else if (partType === 'base' || partPath === 'base' || 
                                 originalPartType === 'Base' || originalPartPath === 'Base' ||
                                 (isGrenade && (spawnCode.includes('part_ord') || spawnCode.includes('ord_grenade')))) {
                            if (isGrenade) {
                                // For grenades/ordnance, include base parts from grenade's own typeId OR typeId 245 (cross-typeId parts)
                                // Grenades should ONLY use body category, NOT baseBody (to keep separate from repkits)
                                if (partTypeId === currentTypeId || partTypeId === 245) {
                                    categoryMap.base.push(partInfo);
                                    // For grenades, only add to body category (NOT baseBody - that's for repkits)
                                    categoryMap.body.push(partInfo);
                                    // Debug logging for grenade/ordnance body
                                    if (categoryKey === 'body' || categoryKey === 'baseBody') {
                                        console.log(`[DEBUG ordnance ${categoryKey} locked] ✅ Categorized: ${partInfo.name || partInfo.id} (partTypeId: ${partTypeId}, currentTypeId: ${currentTypeId}, partType: ${partType}, originalPartType: ${originalPartType}, path: ${partPath}, originalPartPath: ${originalPartPath}, spawnCode: ${spawnCode})`);
                                    }
                                } else if (categoryKey === 'body' || categoryKey === 'baseBody') {
                                    console.log(`[DEBUG ordnance ${categoryKey} locked] ❌ Skipped (wrong typeId): ${partInfo.name || partInfo.id} (partTypeId: ${partTypeId}, currentTypeId: ${currentTypeId})`);
                                }
                            } else if (isRepkit && partTypeId === currentTypeId) {
                                // For repkits, use baseBody category (separate from grenades which use body)
                                // Exclude grenade typeIds from repkit baseBody (they should be in grenade body category)
                                if (!knownGrenadeTypeIds.has(partTypeId)) {
                                    categoryMap.baseBody.push(partInfo);
                                }
                            }
                        }
                        // Licensed Parts - identified by spawnCode containing "licensed" (can be ANY typeId, not just 13)
                        // These are manufacturer parts that are licensed from other manufacturers (e.g., Jakobs Ricochet, Tediore Reload, etc.)
                        // Also include ALL parts from "Manufacturer Part" part_type (even if spawn code doesn't contain "licensed")
                        // Licensed parts can be from ANY typeId (10, 9, 13, etc.) - they will be filtered later by manufacturer matching
                        // Don't restrict by partTypeId === currentTypeId because licensed parts are cross-manufacturer parts
                        if (isLicensed && isWeapon) {
                            categoryMap.licensedParts.push(partInfo);
                            // Don't return - continue categorization so licensed parts also appear in their specific category (barrel, magazine, etc.)
                        } else if ((partType === 'payload' || partPath.includes('payload') || spawnCode.includes('payload')) && partTypeId !== 243) {
                            // Exclude typeId 243 parts from payload category - they should be categorized as Size/Elemental/etc.
                            // For payload245, we want to include ALL typeId 245 Payload parts, regardless of currentTypeId
                            // This allows Payload parts to show up when viewing any grenade type
                            if (partTypeId === 245) {
                                categoryMap.payload245.push(partInfo);
                            }
                            if (partTypeId === currentTypeId) {
                                categoryMap.payload.push(partInfo);
                            }
                        } else if (partType === 'augment' || partPath.includes('augment') || spawnCode.includes('augment')) {
                            // Also add to augment245 if typeId is 245
                            if (partTypeId === 245) {
                                categoryMap.augment245.push(partInfo);
                            }
                            // For repkits, Augment parts should also be considered as baseBody (same as Base parts)
                            // When master unlock is enabled, include augments from ALL repkit typeIds
                            const masterUnlock = document.getElementById('masterUnlockGuidelines');
                            const isUnlocked = masterUnlock ? masterUnlock.checked : false;
                            
                            if (isRepkit) {
                                // Check if this is a repkit typeId (for master unlock) or matches currentTypeId
                                if (isUnlocked && knownRepkitTypeIds.has(partTypeId)) {
                                    // Master unlock: include augments from all repkit typeIds
                                    categoryMap.baseBody.push(partInfo);
                                } else if (partTypeId === currentTypeId) {
                                    // Normal mode: only include augments from current repkit typeId
                                    categoryMap.baseBody.push(partInfo);
                                }
                            } else if (partTypeId === currentTypeId) {
                                categoryMap.augment.push(partInfo);
                            }
                        }
                        
                        // Continue with other categorization...
                        // IMPORTANT: Check typeId 234 BEFORE checking for skills, because some typeId 234 parts
                        // have "skill" in their spawn_code (e.g., "ClassMod.stat_skill_cooldown_rate") and
                        // should be categorized as stat234/stat2_234/statspecial_234, not as skills
                        else if (partTypeId === 234) {
                            // Check for firmware - explicitly include Skillcraft (234:103) by ID
                            const partIdStr = String(partInfo.id || partInfo.fullId || '');
                            let partIdNum = null;
                            if (partIdStr.includes(':')) {
                                const parts = partIdStr.split(':');
                                if (parts.length >= 2) {
                                    partIdNum = parseInt(parts[parts.length - 1]);
                                }
                            } else if (!isNaN(parseInt(partIdStr))) {
                                partIdNum = parseInt(partIdStr);
                            }
                            const isSkillcraftById = partIdNum === 103 && partTypeId === 234;
                            const isFirmware = spawnCode.includes('firmware') || partPath.includes('firmware') ||
                                             spawnCode.includes('skillcraft') || partName.includes('skillcraft') || isSkillcraftById;
                            if (isFirmware) {
                                categoryMap.firmware234.push(partInfo);
                            } else {
                                if (spawnCode.includes('statspecial_') || spawnCode.includes('ClassMod.statspecial')) {
                                    categoryMap.statspecial_234.push(partInfo);
                                } else if (spawnCode.includes('stat2_') || spawnCode.includes('ClassMod.stat2')) {
                                    categoryMap.stat2_234.push(partInfo);
                                } else if (spawnCode.includes('stat_') || spawnCode.includes('ClassMod.stat') || spawnCode.includes('stat')) {
                                    categoryMap.stat234.push(partInfo);
                                } else {
                                    // Fallback: if it's a perk but can't determine, default to stat
                                    categoryMap.stat234.push(partInfo);
                                }
                            }
                        } else if (partType === 'skill' || partType === 'Skills' || partType.includes('skill') || spawnCode.includes('skill') || (isClassMod && partTypeId >= 254 && partTypeId <= 259 && partType !== 'body' && partType !== 'rarity')) {
                            // Exclude body and rarity parts from skills; partType 'Skills' = class_mods.Skills.parts
                            // Also exclude typeId 234 parts (they should be handled above)
                            const isBodyPart = partType === 'body' || partType.includes('body') || 
                                             partPath.includes('body') || partPath.includes('Body') ||
                                             spawnCode.includes('body') || spawnCode.includes('Body') ||
                                             originalPartType === 'Body' || originalPartType.includes('Body');
                            const isRarityPart = partType === 'rarity' || partType === 'comp' || partType.includes('rarity') ||
                                                partPath.includes('rarity') || partPath.includes('rarities') ||
                                                spawnCode.includes('rarity') || spawnCode.includes('comp_') ||
                                                originalPartType === 'Rarity' || originalPartType.includes('Rarity') ||
                                                partInfo.rarity; // Has explicit rarity field
                            // Only add to skills if it's NOT a body part AND NOT a rarity part AND NOT typeId 234
                            if (partTypeId >= 254 && partTypeId <= 259 && !isBodyPart && !isRarityPart && partTypeId !== 234) {
                                categoryMap.skills.push(partInfo);
                            }
                        }
                        // Enhancement parts
                        else if (partType === 'core' || partPath.includes('core')) {
                            if (partTypeId === currentTypeId) categoryMap.core.push(partInfo);
                        } else if (partTypeId === 247) {
                            // IMMEDIATE CHECK: If path or partType indicates Main Body, categorize it immediately
                            // Use original case for path and partType checks (before lowercasing)
                            const partPathStr = String(partInfo.path || '');
                            const partPathStrLower = partPathStr.toLowerCase();
                            const partTypeStr = String(partInfo.partType || '');
                            const partTypeStrLower = partTypeStr.toLowerCase();
                            let isMainBodyPart = false;
                            
                            // Debug: Log ALL typeId 247 parts being processed
                            if (categoryKey === 'baseBody247') {
                                console.log(`[DEBUG baseBody247] Processing typeId 247 part:`, {
                                    id: partInfo.id,
                                    idType: typeof partInfo.id,
                                    fullId: partInfo.fullId,
                                    partType: partInfo.partType,
                                    path: partInfo.path,
                                    partPathStr: partPathStr,
                                    partTypeStr: partTypeStr
                                });
                            }
                            
                            // Check for Main Body by path or partType (check both original and lowercase)
                            if (partPathStr.includes('Main Body') || partPathStrLower.includes('main body') ||
                                partTypeStr === 'Main Body' || partTypeStrLower === 'main body') {
                                // Extract ID to verify it's 76-80 - handle both "76" and "247:76" formats
                                let quickId = null;
                                
                                // First try partInfo.id
                                if (typeof partInfo.id === 'number') {
                                    quickId = partInfo.id;
                                } else if (partInfo.id) {
                                    const idStr = String(partInfo.id || '');
                                    if (idStr.includes(':')) {
                                        // Handle "247:76" format - extract the part after the colon
                                        const parts = idStr.split(':');
                                        if (parts.length >= 2) {
                                            quickId = parseInt(parts[parts.length - 1]);
                                        }
                                    } else {
                                        // Handle simple string like "76"
                                        const parsed = parseInt(idStr);
                                        if (!isNaN(parsed)) {
                                            quickId = parsed;
                                        }
                                    }
                                }
                                
                                // Also check fullId if quickId is still null or invalid
                                if ((quickId === null || isNaN(quickId)) && partInfo.fullId) {
                                    const fullIdStr = String(partInfo.fullId || '');
                                    if (fullIdStr.includes(':')) {
                                        const parts = fullIdStr.split(':');
                                        if (parts.length >= 2) {
                                            quickId = parseInt(parts[parts.length - 1]);
                                        }
                                    } else {
                                        const parsed = parseInt(fullIdStr);
                                        if (!isNaN(parsed)) {
                                            quickId = parsed;
                                        }
                                    }
                                }
                                
                                // If ID is 76-80 OR path/type says Main Body, it's baseBody247
                                // Always categorize if path or type indicates Main Body, regardless of ID
                                if ((quickId !== null && !isNaN(quickId) && quickId >= 76 && quickId <= 80) || 
                                    partPathStr.includes('Main Body') || partPathStrLower.includes('main body') || 
                                    partTypeStr === 'Main Body' || partTypeStrLower === 'main body') {
                                    categoryMap.baseBody247.push(partInfo);
                                    console.log(`[DEBUG baseBody247] ✅ Categorized Main Body part: ${partInfo.name} (id: ${partInfo.id}, idType: ${typeof partInfo.id}, fullId: ${partInfo.fullId}, quickId: ${quickId}, path: ${partPathStr}, partType: ${partTypeStr})`);
                                    isMainBodyPart = true; // Mark as handled
                                } else {
                                    console.log(`[DEBUG baseBody247] ⚠️ Main Body part NOT categorized (quickId: ${quickId}, id: ${partInfo.id}, fullId: ${partInfo.fullId}):`, partInfo.name);
                                }
                            }
                            
                            // If we already categorized it as Main Body, skip the rest to avoid duplicates
                            if (isMainBodyPart) {
                                // Already categorized, skip rest - return to next part (forEach doesn't support continue)
                                return;
                            }
                            
                            // Continue with categorization logic for parts not yet categorized
                            
                            // Extract numeric part ID from various formats - be very aggressive
                            // Handle both numeric IDs (76) and string IDs ("76", "247:76")
                            let partIdNum = null;
                            
                            // First, try to get numeric ID directly if it's already a number
                            if (typeof partInfo.id === 'number' && !isNaN(partInfo.id)) {
                                partIdNum = partInfo.id;
                            } else {
                                // Try partId as string - handle both "76" and "247:76" formats
                                const partIdStr = String(partInfo.id || '');
                                if (partIdStr.includes(':')) {
                                    const parts = partIdStr.split(':');
                                    if (parts.length >= 2) {
                                        partIdNum = parseInt(parts[parts.length - 1]);
                                    }
                                } else if (partIdStr && partIdStr.trim() !== '' && !isNaN(parseInt(partIdStr))) {
                                    partIdNum = parseInt(partIdStr);
                                }
                                
                                // If partId didn't work, try fullId - handle "247:76" format
                                if ((partIdNum === null || isNaN(partIdNum))) {
                                    const fullIdStr = String(partInfo.fullId || '');
                                    if (fullIdStr.includes(':')) {
                                        const parts = fullIdStr.split(':');
                                        if (parts.length >= 2) {
                                            const lastPart = parts[parts.length - 1];
                                            partIdNum = parseInt(lastPart);
                                        }
                                    } else if (fullIdStr && fullIdStr.trim() !== '' && !isNaN(parseInt(fullIdStr))) {
                                        partIdNum = parseInt(fullIdStr);
                                    }
                                }
                            }
                            
                            // FINAL FALLBACK: If we still don't have a number, try extracting from any string field
                            if ((partIdNum === null || isNaN(partIdNum))) {
                                // Try extracting from spawnCode or string field (e.g., "Enhancement.Part_Body_05_Legendary" -> 76)
                                const spawnCodeStr = String(partInfo.spawnCode || partInfo.string || '');
                                if (spawnCodeStr.includes('Body_05') || spawnCodeStr.includes('Body_5')) {
                                    partIdNum = 76;
                                } else if (spawnCodeStr.includes('Body_04') || spawnCodeStr.includes('Body_4')) {
                                    partIdNum = 77;
                                } else if (spawnCodeStr.includes('Body_03') || spawnCodeStr.includes('Body_3')) {
                                    partIdNum = 78;
                                } else if (spawnCodeStr.includes('Body_02') || spawnCodeStr.includes('Body_2')) {
                                    partIdNum = 79;
                                } else if (spawnCodeStr.includes('Body_01') || spawnCodeStr.includes('Body_1')) {
                                    partIdNum = 80;
                                }
                            }
                            
                            // ULTIMATE FALLBACK: Check if partInfo.path includes "Main Body" - if so and ID is missing, check spawnCode pattern
                            if ((partIdNum === null || isNaN(partIdNum)) && partInfo.path && String(partInfo.path).includes('Main Body')) {
                                const stringField = String(partInfo.string || partInfo.spawnCode || '');
                                if (stringField.includes('Body_05') || stringField.includes('Body_5')) {
                                    partIdNum = 76;
                                } else if (stringField.includes('Body_04') || stringField.includes('Body_4')) {
                                    partIdNum = 77;
                                } else if (stringField.includes('Body_03') || stringField.includes('Body_3')) {
                                    partIdNum = 78;
                                } else if (stringField.includes('Body_02') || stringField.includes('Body_2')) {
                                    partIdNum = 79;
                                } else if (stringField.includes('Body_01') || stringField.includes('Body_1')) {
                                    partIdNum = 80;
                                }
                            }
                            
                            // Check if it's firmware or stats first (these take priority, but baseBody247 overrides)
                            // Explicitly include Skillcraft (247:248) which has spawnCode "Enhancement.part_firmware_skillcraft"
                            // Also check by part ID to ensure Skillcraft (248) is included
                            const partIdForCheck = partIdNum !== null ? partIdNum : (partInfo.id ? parseInt(String(partInfo.id).split(':').pop()) : null);
                            const isSkillcraftById = partIdForCheck === 248 && partTypeId === 247;
                            const isFirmware = spawnCode.includes('firmware') || partPath.includes('firmware') || partType.includes('firmware') || 
                                             spawnCode.includes('skillcraft') || partName.includes('skillcraft') || isSkillcraftById;
                            const isStats = partPath.includes('stats') || partPath.includes('stats2') || partPath.includes('stats3') || partType.includes('stat') || spawnCode.includes('stat');
                            
                            // SIMPLIFIED LOGIC: If ID is 76-80, it's ALWAYS baseBody247 (regardless of firmware/stats checks)
                            const isBaseBodyById = partIdNum !== null && !isNaN(partIdNum) && partIdNum >= 76 && partIdNum <= 80;
                            
                            // Debug: Log if we're processing a Main Body part
                            if (isBaseBodyById) {
                                console.log(`[DEBUG baseBody247] Found Main Body part ${partIdNum}: ${partInfo.name} (id: ${partInfo.id}, idType: ${typeof partInfo.id}, fullId: ${partInfo.fullId}, partType: ${partInfo.partType}, path: ${partInfo.path}, isFirmware: ${isFirmware}, isStats: ${isStats})`);
                            }
                            
                            // Additional checks for Main Body - check both lowercase and original case
                            const originalPartType = String(partInfo.partType || '');
                            const isMainBodyType = partType === 'main body' || partType.includes('main body') || 
                                                   originalPartType === 'Main Body' || originalPartType.includes('Main Body');
                            const isBaseBodyByPath = partPath.includes('main body') || partPath.includes('Main Body') || 
                                                     partPath.includes('enhancements.main body') || partPath.includes('enhancements.Main Body') || 
                                                     partPath.includes('enhancements.mainbody');
                            const isBaseBodyBySpawnCode = spawnCode.includes('part_body_05') || spawnCode.includes('part_body_04') || spawnCode.includes('part_body_03') || spawnCode.includes('part_body_02') || spawnCode.includes('part_body_01') ||
                                                          spawnCode.includes('part_body_5') || spawnCode.includes('part_body_4') || spawnCode.includes('part_body_3') || spawnCode.includes('part_body_2') || spawnCode.includes('part_body_1');
                            const hasMainBodyInOriginalType = originalPartType.includes('Main Body') || originalPartType.includes('main body');
                            
                            // Categorize: firmware and stats take priority, BUT baseBody247 (76-80) takes priority over everything
                            // PRIMARY: If ID is 76-80, it's ALWAYS a base body, regardless of other checks
                            // ALSO: If partType is 'Main Body' (any case) and typeId is 247, it's baseBody247
                            const isMainBodyByType = String(partInfo.partType || '').toLowerCase() === 'main body' || 
                                                     String(partInfo.partType || '') === 'Main Body';
                            
                            // Check if partType or path indicates Main Body - this should catch Main Body parts even if ID extraction failed
                            const isMainBodyByPartType = isMainBodyByType || isMainBodyType || 
                                                         partType === 'main body' || 
                                                         String(partInfo.partType || '') === 'Main Body';
                            const isMainBodyByPathCheck = isBaseBodyByPath || 
                                                          partPath.includes('main body') || 
                                                          partPath.includes('Main Body') ||
                                                          String(partInfo.path || '').includes('Main Body') ||
                                                          String(partInfo.path || '').includes('main body');
                            
                            if (isBaseBodyById || (isMainBodyByType && partTypeId === 247) || 
                                (isMainBodyByPartType && partTypeId === 247) || 
                                (isMainBodyByPathCheck && partTypeId === 247 && !isFirmware && !isStats)) {
                                categoryMap.baseBody247.push(partInfo);
                                if (categoryKey === 'baseBody247') {
                                    console.log(`[DEBUG baseBody247] ✅ Categorized via main logic: ${partInfo.name} (id: ${partInfo.id}, fullId: ${partInfo.fullId}, partIdNum: ${partIdNum}, isBaseBodyById: ${isBaseBodyById}, isMainBodyByType: ${isMainBodyByType}, isMainBodyByPartType: ${isMainBodyByPartType}, isMainBodyByPathCheck: ${isMainBodyByPathCheck})`);
                                }
                            } else if (isFirmware) {
                                categoryMap.firmware247.push(partInfo);
                            } else if (isStats) {
                                if (spawnCode.includes('stat3_') || partPath.includes('stat3') || partPath.includes('stats3')) {
                                    categoryMap.stat3_247.push(partInfo);
                                } else if (spawnCode.includes('stat2_') || partPath.includes('stat2') || partPath.includes('stats2')) {
                                    categoryMap.stat2_247.push(partInfo);
                                } else if (spawnCode.includes('stat_') || partPath.includes('stat') || partPath.includes('stats') || partType.includes('stat')) {
                                    categoryMap.stat_247.push(partInfo);
                                }
                            } else {
                                // Not firmware or stats - check if it's Main Body
                                // SECONDARY: Check by type, path, or spawnCode
                                if (isMainBodyType || isBaseBodyByPath || isBaseBodyBySpawnCode || hasMainBodyInOriginalType || 
                                    isMainBodyByPartType || isMainBodyByPathCheck) {
                                    categoryMap.baseBody247.push(partInfo);
                                    if (categoryKey === 'baseBody247') {
                                        console.log(`[DEBUG baseBody247] ✅ Categorized via secondary logic: ${partInfo.name} (id: ${partInfo.id}, fullId: ${partInfo.fullId}, partIdNum: ${partIdNum})`);
                                    }
                                } 
                                // TERTIARY: If path includes body/enhancements and it's an enhancement, treat as base body
                                else if (isEnhancement && (partPath.includes('body') || partPath.includes('enhancements') || partPath.includes('Main Body'))) {
                                    categoryMap.baseBody247.push(partInfo);
                                    if (categoryKey === 'baseBody247') {
                                        console.log(`[DEBUG baseBody247] ✅ Categorized via tertiary logic: ${partInfo.name} (id: ${partInfo.id}, fullId: ${partInfo.fullId})`);
                                    }
                                }
                            }
                        }
                        // Repkit parts (typeId 243)
                        else if (partTypeId === 243) {
                            // Check for firmware - primarily by partType field, then by spawnCode/path/name/Skillcraft ID
                            const originalPartType = String(partInfo.partType || '');
                            const partIdStr = String(partInfo.id || partInfo.fullId || '');
                            let partIdNum = null;
                            if (partIdStr.includes(':')) {
                                const parts = partIdStr.split(':');
                                if (parts.length >= 2) {
                                    partIdNum = parseInt(parts[parts.length - 1]);
                                }
                            } else if (!isNaN(parseInt(partIdStr))) {
                                partIdNum = parseInt(partIdStr);
                            }
                            const isSkillcraftById = partIdNum === 113 && partTypeId === 243;
                            // Primary check: partType === 'Firmware'
                            // Secondary check: spawnCode/path/name contains 'firmware' or 'skillcraft', or is Skillcraft by ID
                            const isFirmware = originalPartType === 'Firmware' || 
                                             spawnCode.includes('firmware') || partPath.includes('firmware') ||
                                             spawnCode.includes('skillcraft') || partName.includes('skillcraft') || isSkillcraftById;
                            if (isFirmware) {
                                categoryMap.firmware243.push(partInfo);
                            } else {
                                // Categorize non-firmware parts into subcategories
                                const isResistance = originalPartType === 'Resistance' || spawnCode.includes('elemental_resist') || spawnCode.includes('resist');
                                const isImmunity = originalPartType === 'Immunity' || spawnCode.includes('immunity');
                                const isSplat = originalPartType === 'Splat' || spawnCode.includes('splat') || (partIdNum >= 32 && partIdNum <= 36);
                                const isNova = originalPartType === 'Nova' || spawnCode.includes('nova') || (partIdNum >= 37 && partIdNum <= 41);
                                
                                const partString = String(partInfo.string || '').toLowerCase();
                                const isSize = originalPartType === 'Size' || spawnCode.includes('payload') || partString.includes('payload') || (partIdNum >= 103 && partIdNum <= 106);
                                const isElemental = originalPartType === 'Elemental' || spawnCode.includes('part_element') || (partIdNum >= 98 && partIdNum <= 102);
                                
                                if (isResistance) {
                                    categoryMap.elementalResistances243.push(partInfo);
                                } else if (isImmunity) {
                                    categoryMap.elementalImmunities243.push(partInfo);
                                } else if (isSplat) {
                                    categoryMap.elementalSplats243.push(partInfo);
                                } else if (isNova) {
                                    categoryMap.elementalNovas243.push(partInfo);
                                } else if (isSize) {
                                    categoryMap.size243.push(partInfo);
                                } else if (isElemental) {
                                    categoryMap.elemental243.push(partInfo);
                                } else {
                                    // Everything else goes to parts243
                                    categoryMap.parts243.push(partInfo);
                                }
                            }
                        }
                        // Grenade parts (typeId 245)
                        else if (partTypeId === 245) {
                            // Check for firmware - explicitly include Skillcraft (245:88) by ID
                            const partIdStr = String(partInfo.id || partInfo.fullId || '');
                            let partIdNum = null;
                            if (partIdStr.includes(':')) {
                                const parts = partIdStr.split(':');
                                if (parts.length >= 2) {
                                    partIdNum = parseInt(parts[parts.length - 1]);
                                }
                            } else if (!isNaN(parseInt(partIdStr))) {
                                partIdNum = parseInt(partIdStr);
                            }
                            const isSkillcraftById = partIdNum === 88 && partTypeId === 245;
                            const isFirmware = spawnCode.includes('firmware') || partPath.includes('firmware') ||
                                             spawnCode.includes('skillcraft') || partName.includes('skillcraft') || isSkillcraftById;
                            // Check for elemental status parts (245:24-28: Corrosive, Cryo, Fire, Radiation, Shock)
                            const isElementalStatus = (partType === 'status' || partName.includes('status') || partPath.includes('status') || spawnCode.includes('status')) ||
                                                     (partIdNum >= 24 && partIdNum <= 28 && partTypeId === 245);
                            // Get original partType before normalization (check both original and normalized)
                            const originalPartType = String(partInfo.partType || '');
                            const originalPartTypeLower = originalPartType.toLowerCase();
                            // Check for Payload parts - spawnCode patterns like grenade_gadget.part_01_, part_02_, etc.
                            // Payload parts are IDs 245:29-39 (MIRV, Divider, Spring, Artillery, Singularity, Lingering variants, Damage Amp)
                            const isPayload = partType === 'payload' || originalPartTypeLower === 'payload' || 
                                             partPath.includes('payload') || spawnCode.includes('payload') ||
                                             spawnCode.includes('grenade_gadget.part_0') || 
                                             (partIdNum >= 29 && partIdNum <= 39 && partTypeId === 245);
                            // Check for Stats parts - spawnCode patterns like grenade_gadget.part_stat_01_, etc.
                            // Stats parts are IDs 245:70-81 (Overflow, Express, Explosive, etc.)
                            const isStats = partType === 'stats' || originalPartTypeLower === 'stats' || 
                                           partPath.includes('stats') || spawnCode.includes('part_stat_') ||
                                           (partIdNum >= 70 && partIdNum <= 81 && partTypeId === 245);
                            if (isFirmware) {
                                categoryMap.firmware245.push(partInfo);
                            } else if (partType === 'augment' || partPath.includes('augment') || spawnCode.includes('augment')) {
                                categoryMap.augment245.push(partInfo);
                            } else if (isElementalStatus) {
                                // Elemental status parts (Corrosive, Cryo, Fire, Radiation, Shock) go to parts245
                                categoryMap.parts245.push(partInfo);
                            } else if (isStats) {
                                // Stats parts (Overflow, Express, Explosive, etc.) go to stats245
                                categoryMap.stats245.push(partInfo);
                            } else if (isPayload) {
                                // Payload parts (MIRV Payload, Divider Payload, Spring Payload, etc.) go to payload245
                                categoryMap.payload245.push(partInfo);
                            } else {
                                // For typeId 245, if it doesn't match any known category, default to payload245
                                // This is a fallback for any edge cases
                                categoryMap.payload245.push(partInfo);
                            }
                        }
                        // Shield body parts (from shield's own typeId, e.g., 300 for Ripper)
                        // These are the main body parts for shields (e.g., "Sparky", "Firebreak" for Ripper shields)
                        // IMPORTANT: For shields, Base Body and Legendary Part are one and the same!
                        // Match when:
                        // 1. It's a shield item (isShield is true)
                        // 2. The part's typeId matches the current shield's typeId (e.g., 300 for Ripper)
                        // 3. AND (partType is "shield" OR spawnCode includes "part_body" OR path includes "shield")
                        else if (isShield && Number(partTypeId) === Number(currentTypeId)) {
                            // Debug: Log that we're checking this part
                            if (categoryKey === 'baseBody') {
                                console.log(`[DEBUG shield baseBody locked] Checking part: ${partInfo.name || partInfo.id} (partInfo.typeId: ${partInfo.typeId}, partTypeId: ${partTypeId}, currentTypeId: ${currentTypeId}, partType: ${partType}, originalPartType: ${originalPartType}, spawnCode: ${spawnCode}, path: ${partPath})`);
                            }
                            
                            // Check if it matches shield body part criteria
                            const matchesShieldBody = partType === 'shield' || spawnCode.includes('part_body') || partPath.includes('shield') || originalPartType === 'Shield';
                            
                            if (matchesShieldBody) {
                                // This is a shield body part from the shield's own typeId
                                categoryMap.shield.push(partInfo);
                                categoryMap.baseBody.push(partInfo);
                                // For shields, Base Body = Legendary Part (they are one and the same)
                                categoryMap.legendaryPart.push(partInfo);
                                // Debug logging for shield body parts
                                if (categoryKey === 'baseBody' || categoryKey === 'legendaryPart') {
                                    console.log(`[DEBUG shield ${categoryKey} locked] ✅ Categorized: ${partInfo.name || partInfo.id} (partInfo.typeId: ${partInfo.typeId}, partTypeId: ${partTypeId}, currentTypeId: ${currentTypeId}, partType: ${partType}, originalPartType: ${originalPartType}, spawnCode: ${spawnCode}, path: ${partPath})`);
                                }
                            } else if (categoryKey === 'baseBody') {
                                // Debug: Log why it didn't match
                                console.log(`[DEBUG shield baseBody locked] ❌ NOT categorized: ${partInfo.name || partInfo.id} (partInfo.typeId: ${partInfo.typeId}, partTypeId: ${partTypeId}, currentTypeId: ${currentTypeId}, partType: ${partType}, originalPartType: ${originalPartType}, spawnCode: ${spawnCode}, path: ${partPath}, matchesShieldBody: ${matchesShieldBody}, partType==='shield'=${partType === 'shield'}, spawnCode.includes('part_body')=${spawnCode.includes('part_body')}, partPath.includes('shield')=${partPath.includes('shield')}, originalPartType==='Shield'=${originalPartType === 'Shield'})`);
                            }
                        } else if (isShield && categoryKey === 'baseBody') {
                            // Debug: Log why it didn't match the first condition
                            if (Number(partTypeId) === Number(currentTypeId)) {
                                console.log(`[DEBUG shield baseBody locked] ⚠️ Part has matching typeId but didn't reach shield body check: ${partInfo.name || partInfo.id} (partInfo.typeId: ${partInfo.typeId}, partTypeId: ${partTypeId}, currentTypeId: ${currentTypeId})`);
                            } else {
                                console.log(`[DEBUG shield baseBody locked] ❌ NOT categorized (typeId mismatch): ${partInfo.name || partInfo.id} (partInfo.typeId: ${partInfo.typeId}, partTypeId: ${partTypeId}, currentTypeId: ${currentTypeId})`);
                            }
                        }
                        // Debug: Log if we're processing shield parts but they didn't match any shield category
                        else if (isShield && (Number(partTypeId) === 246 || Number(partTypeId) === 237 || Number(partTypeId) === 248) && 
                                 (categoryKey === 'perks246' || categoryKey === 'firmware246' || categoryKey === 'armor237' || categoryKey === 'energy248')) {
                            console.log(`[DEBUG shield ${categoryKey}] ⚠️ Part NOT categorized by shield checks: ${partInfo.name || partInfo.id} (partTypeId: ${partTypeId}, Number(partTypeId): ${Number(partTypeId)}, partInfo.typeId: ${partInfo.typeId}, partType: ${partType})`);
                        }
                        // Heavy Weapon parts (typeId 244)
                        else if (partTypeId === 244) {
                            // Check for firmware - explicitly include Skillcraft (244:88 or similar) by ID and name
                            const partIdStr = String(partInfo.id || partInfo.fullId || '');
                            let partIdNum = null;
                            if (partIdStr.includes(':')) {
                                const parts = partIdStr.split(':');
                                if (parts.length >= 2) {
                                    partIdNum = parseInt(parts[parts.length - 1]);
                                }
                            } else if (!isNaN(parseInt(partIdStr))) {
                                partIdNum = parseInt(partIdStr);
                            }
                            const isSkillcraftById = partIdNum === 88 && partTypeId === 244;
                            const isFirmware = spawnCode.includes('firmware') || partPath.includes('firmware') ||
                                             spawnCode.includes('skillcraft') || partName.includes('skillcraft') || isSkillcraftById;
                            if (isFirmware) {
                                categoryMap.firmware244.push(partInfo);
                            }
                        }
                        // Element parts (typeId 1) - available for all item types
                        // This includes: primary elements (1:10-1:14), Maliwan secondary (1:23-1:28), and licensed underbarrel (1:15-1:22, 1:29-1:49)
                        else if (partTypeId === 1) {
                            categoryMap.element.push(partInfo);
                            
                            // Also check if it's a Maliwan Licensed Underbarrel part for that specific category
                            const partCategory = String(partInfo.category || '').toLowerCase();
                            const isMaliwanLicensedUnderbarrel = 
                                spawnCode.includes('part_secondary_elem') || 
                                spawnCode.includes('part_licensed_underbarrel') ||
                                partPath.includes('licensed_underbarrel') ||
                                partCategory.includes('maliwan licensed') ||
                                partCategory.includes('maliwan licenced'); // Handle typo "licenced" vs "licensed"
                            
                            if (isMaliwanLicensedUnderbarrel) {
                                categoryMap.maliwanLicensedUnderbarrel.push(partInfo);
                                // Debug logging for maliwanLicensedUnderbarrel
                                console.log(`[DEBUG maliwanLicensedUnderbarrel locked] ✅ Categorized: ${partInfo.name} (id: ${partInfo.id}, fullId: ${partInfo.fullId}, typeId: ${partTypeId}, spawnCode: ${spawnCode}, path: ${partPath}, category: ${partInfo.category})`);
                            }
                        }
                        // Daedalus Ammo parts - identified by spawnCode pattern: part_secondary_ammo_sg, part_secondary_ammo_smg, part_secondary_ammo_ar, part_secondary_ammo_ps
                        // These can be any typeId and any part ID, so we check by spawnCode
                        const isDaedalusAmmo = spawnCode.includes('part_secondary_ammo_sg') ||
                                              spawnCode.includes('part_secondary_ammo_smg') ||
                                              spawnCode.includes('part_secondary_ammo_ar') ||
                                              spawnCode.includes('part_secondary_ammo_ps');
                        if (isDaedalusAmmo) {
                            categoryMap.daedalusAmmo.push(partInfo);
                            // Debug logging for daedalusAmmo
                            if (categoryKey === 'daedalusAmmo') {
                                console.log(`[DEBUG daedalusAmmo locked] ✅ Categorized: ${partInfo.name} (id: ${partInfo.id}, fullId: ${partInfo.fullId}, typeId: ${partTypeId}, spawnCode: ${spawnCode})`);
                            }
                            // Skip rest of categorization to avoid duplicates - use return in forEach
                            return;
                        }
                    });
                    
                    // Deduplicate categoryMap.baseBody247 to avoid duplicates
                    if (categoryMap.baseBody247.length > 0) {
                        const seen = new Set();
                        categoryMap.baseBody247 = categoryMap.baseBody247.filter(partInfo => {
                            const fullId = String(partInfo.fullId || partInfo.id || '');
                            if (fullId && seen.has(fullId)) {
                                return false; // Duplicate, filter it out
                            }
                            if (fullId) seen.add(fullId);
                            return true;
                        });
                    }
                    
                    // Debug: Log final categoryMap for baseBody247
                    if (categoryKey === 'baseBody247') {
                        console.log(`[DEBUG baseBody247] Final categoryMap.baseBody247 contains ${categoryMap.baseBody247.length} parts (after deduplication)`);
                        if (categoryMap.baseBody247.length > 0) {
                            console.log(`[DEBUG baseBody247] Parts in categoryMap:`, categoryMap.baseBody247.map(p => ({
                                id: p.id,
                                fullId: p.fullId,
                                name: p.name,
                                partType: p.partType,
                                path: p.path
                            })));
                        }
                    }
                    
                    // Debug logging for shield categories
                    if (isShield && (categoryKey === 'perks246' || categoryKey === 'firmware246' || categoryKey === 'armor237' || categoryKey === 'energy248')) {
                        console.log(`[DEBUG shield ${categoryKey}] buildPartsByCategory complete. categoryMap[${categoryKey}].length = ${categoryMap[categoryKey]?.length || 0}`);
                        if (categoryMap[categoryKey] && categoryMap[categoryKey].length > 0) {
                            console.log(`[DEBUG shield ${categoryKey}] Sample parts:`, categoryMap[categoryKey].slice(0, 3).map(p => ({
                                id: p.id,
                                fullId: p.fullId,
                                name: p.name,
                                typeId: p.typeId,
                                partType: p.partType,
                                spawnCode: p.spawnCode
                            })));
                        }
                    }
                    
                    // Debug logging for grenade/ordnance categories
                    if (isGrenade && (categoryKey === 'rarity' || categoryKey === 'body' || categoryKey === 'baseBody')) {
                        console.log(`[DEBUG ordnance ${categoryKey}] buildPartsByCategory complete. categoryMap[${categoryKey}].length = ${categoryMap[categoryKey]?.length || 0}`);
                        if (categoryMap[categoryKey] && categoryMap[categoryKey].length > 0) {
                            console.log(`[DEBUG ordnance ${categoryKey}] Sample parts:`, categoryMap[categoryKey].slice(0, 3).map(p => ({
                                id: p.id,
                                fullId: p.fullId,
                                name: p.name,
                                typeId: p.typeId,
                                partType: p.partType,
                                path: p.path,
                                spawnCode: p.spawnCode
                            })));
                        }
                    }
                    
                    return categoryMap;
                };
                
                const partsByCategory = buildPartsByCategory();
                let categoryParts = partsByCategory[categoryKey] || [];
                
                // Fallback (guidelines-ui): Enhancement rarity - if categoryMap.rarity is empty but we have enhancement parts with rarities, use ownParts
                if (categoryKey === 'rarity' && categoryParts.length === 0 && isEnhancement && ownParts.length > 0) {
                    categoryParts = ownParts.filter(function (p) {
                        var path = String(p.path || '').toLowerCase();
                        var pt = String(p.partType || '').toLowerCase();
                        var sc = String(p.spawnCode || '').toLowerCase();
                        return path.indexOf('rarities') !== -1 || pt.indexOf('rarity') !== -1 || sc.indexOf('comp_') !== -1 || p.rarity;
                    });
                }
                // Fallback (guidelines-ui): Enhancement baseBody247/stat_247/firmware247 - if empty but we have typeId 247, fill from 247 parts
                if (isEnhancement && categoryParts.length === 0 && partsByTypeId.has(247)) {
                    var type247Parts = partsByTypeId.get(247) || [];
                    if (categoryKey === 'baseBody247') {
                        categoryParts = type247Parts.filter(function (p) {
                            var path = String(p.path || '').toLowerCase();
                            var pt = String(p.partType || '').toLowerCase();
                            var id = String(p.id || p.fullId || '');
                            var num = id.indexOf(':') >= 0 ? parseInt(id.split(':')[1], 10) : parseInt(id, 10);
                            return path.indexOf('main body') !== -1 || pt.indexOf('main body') !== -1 || (num >= 76 && num <= 80);
                        });
                    } else if (categoryKey === 'stat_247' || categoryKey === 'stat2_247' || categoryKey === 'stat3_247') {
                        categoryParts = type247Parts.filter(function (p) {
                            var path = String(p.path || '').toLowerCase();
                            var pt = String(p.partType || '').toLowerCase();
                            return path.indexOf('stat') !== -1 || pt.indexOf('stat') !== -1;
                        });
                    } else if (categoryKey === 'firmware247') {
                        categoryParts = type247Parts.filter(function (p) {
                            var path = String(p.path || '').toLowerCase();
                            var sc = String(p.spawnCode || '').toLowerCase();
                            return path.indexOf('firmware') !== -1 || sc.indexOf('firmware') !== -1;
                        });
                    }
                }
                // Fallback (guidelines-ui): Class mod Skills for 254/255/256/259 - show only the 14 skill-related typeId 234 parts
                if (categoryKey === 'skills' && categoryParts.length === 0 && isClassMod && partsByTypeId.has(234)) {
                    var all234 = partsByTypeId.get(234) || [];
                    var skillIdSet = {};
                    if (typeof CLASS_MOD_SKILL_PART_IDS !== 'undefined') {
                        CLASS_MOD_SKILL_PART_IDS.forEach(function (id) { skillIdSet[id] = true; });
                    }
                    categoryParts = all234.filter(function (p) {
                        var fullId = String(p.fullId || p.id || '');
                        return skillIdSet[fullId];
                    });
                    if (categoryParts.length === 0) categoryParts = all234;
                }
                
                // Fallback: Ensure repkit parts (typeId 243) appear in parts243
                if (categoryKey === 'parts243' && partsByTypeId.has(243)) {
                    const existingFullIds = new Set();
                    categoryParts.forEach(p => {
                        const fullId = String(p.fullId || p.id || '');
                        if (fullId) existingFullIds.add(fullId);
                    });
                    
                    const otherRepkitBuckets = [
                        ...(partsByCategory.firmware243 || []),
                        ...(partsByCategory.elementalResistances243 || []),
                        ...(partsByCategory.elementalImmunities243 || []),
                        ...(partsByCategory.elementalSplats243 || []),
                        ...(partsByCategory.elementalNovas243 || []),
                        ...(partsByCategory.size243 || []),
                        ...(partsByCategory.elemental243 || [])
                    ];
                    const otherBucketIds = new Set(otherRepkitBuckets.map(p => String(p.fullId || p.id || '')).filter(Boolean));
                    
                    const allType243Parts = partsByTypeId.get(243) || [];
                    const missingRepkitParts = allType243Parts.filter(partInfo => {
                        const fullId = String(partInfo.fullId || partInfo.id || '');
                        if (!fullId || existingFullIds.has(fullId) || otherBucketIds.has(fullId)) {
                            return false;
                        }
                        
                        const spawnCode = String(partInfo.spawnCode || '').toLowerCase();
                        const partPath = String(partInfo.path || '').toLowerCase();
                        const partName = String(partInfo.name || '').toLowerCase();
                        const partIdStr = String(partInfo.id || partInfo.fullId || '');
                        let partIdNum = null;
                        if (partIdStr.includes(':')) {
                            const parts = partIdStr.split(':');
                            if (parts.length >= 2) {
                                partIdNum = parseInt(parts[parts.length - 1]);
                            }
                        } else if (!isNaN(parseInt(partIdStr))) {
                            partIdNum = parseInt(partIdStr);
                        }
                        const isSkillcraftById = partIdNum === 113;
                        const isFirmware = spawnCode.includes('firmware') || partPath.includes('firmware') ||
                                           spawnCode.includes('skillcraft') || partName.includes('skillcraft') || isSkillcraftById;
                        return !isFirmware;
                    });
                    
                    if (missingRepkitParts.length > 0) {
                        categoryParts.push(...missingRepkitParts);
                    }
                }
                
                // Debug logging and FALLBACK for firmware247 category
                if (categoryKey === 'firmware247') {
                    console.log(`[DEBUG firmware247] After buildPartsByCategory, categoryParts.length = ${categoryParts.length}`);
                    console.log(`[DEBUG firmware247] categoryMap.firmware247.length = ${partsByCategory.firmware247?.length || 0}`);
                    
                    // FALLBACK: Ensure Skillcraft (247:248) is included if it's in partsByTypeId but not in categoryMap
                    if (partsByTypeId.has(247)) {
                        const allType247Parts = partsByTypeId.get(247);
                        const firmwareParts = allType247Parts.filter(partInfo => {
                            const spawnCode = String(partInfo.spawnCode || '').toLowerCase();
                            const partPath = String(partInfo.path || '').toLowerCase();
                            const partName = String(partInfo.name || '').toLowerCase();
                            const fullId = String(partInfo.fullId || partInfo.id || '');
                            let partIdNum = null;
                            if (fullId.includes(':')) {
                                const parts = fullId.split(':');
                                if (parts.length >= 2) {
                                    partIdNum = parseInt(parts[parts.length - 1]);
                                }
                            } else if (!isNaN(parseInt(fullId))) {
                                partIdNum = parseInt(fullId);
                            }
                            const isSkillcraftById = partIdNum === 248 && partInfo.typeId === 247;
                            return spawnCode.includes('firmware') || partPath.includes('firmware') || 
                                   spawnCode.includes('skillcraft') || partName.includes('skillcraft') || isSkillcraftById;
                        });
                        
                        // Create a set of existing fullIds
                        const existingFullIds = new Set();
                        categoryParts.forEach(p => {
                            const fullId = String(p.fullId || p.id || '');
                            if (fullId) existingFullIds.add(fullId);
                        });
                        
                        // Find missing firmware parts
                        const missingParts = firmwareParts.filter(partInfo => {
                            const fullId = String(partInfo.fullId || partInfo.id || '');
                            return fullId && !existingFullIds.has(fullId);
                        });
                        
                        if (missingParts.length > 0) {
                            console.log(`[DEBUG firmware247] Found ${missingParts.length} missing firmware parts, adding them...`);
                            console.log(`[DEBUG firmware247] Missing part IDs:`, missingParts.map(p => p.fullId || p.id).sort());
                            categoryParts.push(...missingParts);
                        }
                        
                        // Check specifically for Skillcraft
                        const skillcraft = categoryParts.find(p => {
                            const fullId = String(p.fullId || p.id || '');
                            return fullId === '247:248' || fullId.includes(':248') || (p.name && p.name.toLowerCase().includes('skillcraft'));
                        });
                        if (skillcraft) {
                            console.log(`[DEBUG firmware247] ✅ Skillcraft found in categoryParts:`, skillcraft);
                        } else {
                            console.log(`[DEBUG firmware247] ❌ Skillcraft NOT found in categoryParts!`);
                        }
                    }
                }
                
                // Debug logging and FALLBACK for firmware234 category
                if (categoryKey === 'firmware234') {
                    console.log(`[DEBUG firmware234] After buildPartsByCategory, categoryParts.length = ${categoryParts.length}`);
                    console.log(`[DEBUG firmware234] categoryMap.firmware234.length = ${partsByCategory.firmware234?.length || 0}`);
                    
                    // FALLBACK: Ensure Skillcraft (234:103) is included if it's in partsByTypeId but not in categoryMap
                    if (partsByTypeId.has(234)) {
                        const allType234Parts = partsByTypeId.get(234);
                        const firmwareParts = allType234Parts.filter(partInfo => {
                            const spawnCode = String(partInfo.spawnCode || '').toLowerCase();
                            const partPath = String(partInfo.path || '').toLowerCase();
                            const partName = String(partInfo.name || '').toLowerCase();
                            const fullId = String(partInfo.fullId || partInfo.id || '');
                            let partIdNum = null;
                            if (fullId.includes(':')) {
                                const parts = fullId.split(':');
                                if (parts.length >= 2) {
                                    partIdNum = parseInt(parts[parts.length - 1]);
                                }
                            } else if (!isNaN(parseInt(fullId))) {
                                partIdNum = parseInt(fullId);
                            }
                            const isSkillcraftById = partIdNum === 103 && partInfo.typeId === 234;
                            return spawnCode.includes('firmware') || partPath.includes('firmware') || 
                                   spawnCode.includes('skillcraft') || partName.includes('skillcraft') || isSkillcraftById;
                        });
                        
                        // Create a set of existing fullIds
                        const existingFullIds = new Set();
                        categoryParts.forEach(p => {
                            const fullId = String(p.fullId || p.id || '');
                            if (fullId) existingFullIds.add(fullId);
                        });
                        
                        // Find missing firmware parts
                        const missingParts = firmwareParts.filter(partInfo => {
                            const fullId = String(partInfo.fullId || partInfo.id || '');
                            return fullId && !existingFullIds.has(fullId);
                        });
                        
                        if (missingParts.length > 0) {
                            console.log(`[DEBUG firmware234] Found ${missingParts.length} missing firmware parts, adding them...`);
                            console.log(`[DEBUG firmware234] Missing part IDs:`, missingParts.map(p => p.fullId || p.id).sort());
                            categoryParts.push(...missingParts);
                        }
                        
                        // Check specifically for Skillcraft
                        const skillcraft = categoryParts.find(p => {
                            const fullId = String(p.fullId || p.id || '');
                            return fullId === '234:103' || fullId.includes(':103') || (p.name && p.name.toLowerCase().includes('skillcraft'));
                        });
                        if (skillcraft) {
                            console.log(`[DEBUG firmware234] ✅ Skillcraft found in categoryParts:`, skillcraft);
                        } else {
                            console.log(`[DEBUG firmware234] ❌ Skillcraft NOT found in categoryParts!`);
                        }
                    }
                }
                
                // Debug logging and FALLBACK for firmware243 category
                if (categoryKey === 'firmware243') {
                    console.log(`[DEBUG firmware243] After buildPartsByCategory, categoryParts.length = ${categoryParts.length}`);
                    console.log(`[DEBUG firmware243] categoryMap.firmware243.length = ${partsByCategory.firmware243?.length || 0}`);
                    
                    // FALLBACK: Ensure Skillcraft (243:113) is included if it's in partsByTypeId but not in categoryMap
                    if (partsByTypeId.has(243)) {
                        const allType243Parts = partsByTypeId.get(243);
                        const firmwareParts = allType243Parts.filter(partInfo => {
                            const spawnCode = String(partInfo.spawnCode || '').toLowerCase();
                            const partPath = String(partInfo.path || '').toLowerCase();
                            const partName = String(partInfo.name || '').toLowerCase();
                            const fullId = String(partInfo.fullId || partInfo.id || '');
                            let partIdNum = null;
                            if (fullId.includes(':')) {
                                const parts = fullId.split(':');
                                if (parts.length >= 2) {
                                    partIdNum = parseInt(parts[parts.length - 1]);
                                }
                            } else if (!isNaN(parseInt(fullId))) {
                                partIdNum = parseInt(fullId);
                            }
                            const isSkillcraftById = partIdNum === 113 && partInfo.typeId === 243;
                            return spawnCode.includes('firmware') || partPath.includes('firmware') || 
                                   spawnCode.includes('skillcraft') || partName.includes('skillcraft') || isSkillcraftById;
                        });
                        
                        // Create a set of existing fullIds
                        const existingFullIds = new Set();
                        categoryParts.forEach(p => {
                            const fullId = String(p.fullId || p.id || '');
                            if (fullId) existingFullIds.add(fullId);
                        });
                        
                        // Find missing firmware parts
                        const missingParts = firmwareParts.filter(partInfo => {
                            const fullId = String(partInfo.fullId || partInfo.id || '');
                            return fullId && !existingFullIds.has(fullId);
                        });
                        
                        if (missingParts.length > 0) {
                            console.log(`[DEBUG firmware243] Found ${missingParts.length} missing firmware parts, adding them...`);
                            console.log(`[DEBUG firmware243] Missing part IDs:`, missingParts.map(p => p.fullId || p.id).sort());
                            categoryParts.push(...missingParts);
                        }
                        
                        // Check specifically for Skillcraft
                        const skillcraft = categoryParts.find(p => {
                            const fullId = String(p.fullId || p.id || '');
                            return fullId === '243:113' || fullId.includes(':113') || (p.name && p.name.toLowerCase().includes('skillcraft'));
                        });
                        if (skillcraft) {
                            console.log(`[DEBUG firmware243] ✅ Skillcraft found in categoryParts:`, skillcraft);
                        } else {
                            console.log(`[DEBUG firmware243] ❌ Skillcraft NOT found in categoryParts!`);
                        }
                    }
                }
                
                // Debug logging and FALLBACK for firmware245 category
                if (categoryKey === 'firmware245') {
                    console.log(`[DEBUG firmware245] After buildPartsByCategory, categoryParts.length = ${categoryParts.length}`);
                    console.log(`[DEBUG firmware245] categoryMap.firmware245.length = ${partsByCategory.firmware245?.length || 0}`);
                    
                    // FALLBACK: Ensure Skillcraft (245:88) is included if it's in partsByTypeId but not in categoryMap
                    if (partsByTypeId.has(245)) {
                        const allType245Parts = partsByTypeId.get(245);
                        const firmwareParts = allType245Parts.filter(partInfo => {
                            const spawnCode = String(partInfo.spawnCode || '').toLowerCase();
                            const partPath = String(partInfo.path || '').toLowerCase();
                            const partName = String(partInfo.name || '').toLowerCase();
                            const fullId = String(partInfo.fullId || partInfo.id || '');
                            let partIdNum = null;
                            if (fullId.includes(':')) {
                                const parts = fullId.split(':');
                                if (parts.length >= 2) {
                                    partIdNum = parseInt(parts[parts.length - 1]);
                                }
                            } else if (!isNaN(parseInt(fullId))) {
                                partIdNum = parseInt(fullId);
                            }
                            const isSkillcraftById = partIdNum === 88 && partInfo.typeId === 245;
                            return spawnCode.includes('firmware') || partPath.includes('firmware') || 
                                   spawnCode.includes('skillcraft') || partName.includes('skillcraft') || isSkillcraftById;
                        });
                        
                        // Create a set of existing fullIds
                        const existingFullIds = new Set();
                        categoryParts.forEach(p => {
                            const fullId = String(p.fullId || p.id || '');
                            if (fullId) existingFullIds.add(fullId);
                        });
                        
                        // Find missing firmware parts
                        const missingParts = firmwareParts.filter(partInfo => {
                            const fullId = String(partInfo.fullId || partInfo.id || '');
                            return fullId && !existingFullIds.has(fullId);
                        });
                        
                        if (missingParts.length > 0) {
                            console.log(`[DEBUG firmware245] Found ${missingParts.length} missing firmware parts, adding them...`);
                            console.log(`[DEBUG firmware245] Missing part IDs:`, missingParts.map(p => p.fullId || p.id).sort());
                            categoryParts.push(...missingParts);
                        }
                        
                        // Check specifically for Skillcraft
                        const skillcraft = categoryParts.find(p => {
                            const fullId = String(p.fullId || p.id || '');
                            return fullId === '245:88' || fullId.includes(':88') || (p.name && p.name.toLowerCase().includes('skillcraft'));
                        });
                        if (skillcraft) {
                            console.log(`[DEBUG firmware245] ✅ Skillcraft found in categoryParts:`, skillcraft);
                        } else {
                            console.log(`[DEBUG firmware245] ❌ Skillcraft NOT found in categoryParts!`);
                        }
                    }
                }
                
                // Debug logging and FALLBACK for firmware244 category
                if (categoryKey === 'firmware244') {
                    console.log(`[DEBUG firmware244] After buildPartsByCategory, categoryParts.length = ${categoryParts.length}`);
                    console.log(`[DEBUG firmware244] categoryMap.firmware244.length = ${partsByCategory.firmware244?.length || 0}`);
                    
                    // FALLBACK: Ensure Skillcraft (244:88) is included if it's in partsByTypeId but not in categoryMap
                    if (partsByTypeId.has(244)) {
                        const allType244Parts = partsByTypeId.get(244);
                        const firmwareParts = allType244Parts.filter(partInfo => {
                            const spawnCode = String(partInfo.spawnCode || '').toLowerCase();
                            const partPath = String(partInfo.path || '').toLowerCase();
                            const partName = String(partInfo.name || '').toLowerCase();
                            const fullId = String(partInfo.fullId || partInfo.id || '');
                            let partIdNum = null;
                            if (fullId.includes(':')) {
                                const parts = fullId.split(':');
                                if (parts.length >= 2) {
                                    partIdNum = parseInt(parts[parts.length - 1]);
                                }
                            } else if (!isNaN(parseInt(fullId))) {
                                partIdNum = parseInt(fullId);
                            }
                            const isSkillcraftById = partIdNum === 88 && partInfo.typeId === 244;
                            return spawnCode.includes('firmware') || partPath.includes('firmware') || 
                                   spawnCode.includes('skillcraft') || partName.includes('skillcraft') || isSkillcraftById;
                        });
                        
                        // Create a set of existing fullIds
                        const existingFullIds = new Set();
                        categoryParts.forEach(p => {
                            const fullId = String(p.fullId || p.id || '');
                            if (fullId) existingFullIds.add(fullId);
                        });
                        
                        // Find missing firmware parts
                        const missingParts = firmwareParts.filter(partInfo => {
                            const fullId = String(partInfo.fullId || partInfo.id || '');
                            return fullId && !existingFullIds.has(fullId);
                        });
                        
                        if (missingParts.length > 0) {
                            console.log(`[DEBUG firmware244] Found ${missingParts.length} missing firmware parts, adding them...`);
                            console.log(`[DEBUG firmware244] Missing part IDs:`, missingParts.map(p => p.fullId || p.id).sort());
                            categoryParts.push(...missingParts);
                        }
                        
                        // Check specifically for Skillcraft
                        const skillcraft = categoryParts.find(p => {
                            const fullId = String(p.fullId || p.id || '');
                            return fullId === '244:88' || fullId.includes(':88') || (p.name && p.name.toLowerCase().includes('skillcraft'));
                        });
                        if (skillcraft) {
                            console.log(`[DEBUG firmware244] ✅ Skillcraft found in categoryParts:`, skillcraft);
                        } else {
                            console.log(`[DEBUG firmware244] ❌ Skillcraft NOT found in categoryParts!`);
                        }
                    }
                }
                
                // Debug logging for shield categories after build
                if (isShield && (categoryKey === 'perks246' || categoryKey === 'firmware246' || categoryKey === 'armor237' || categoryKey === 'energy248')) {
                    console.log(`[DEBUG shield ${categoryKey}] After buildPartsByCategory, categoryParts.length = ${categoryParts.length}`);
                }
                
                // FALLBACK: For resistance246 category, ensure ALL resistance typeId 246 parts (246:21-246:26) are included
                if (categoryKey === 'resistance246') {
                    console.log(`[DEBUG resistance246] categoryParts.length = ${categoryParts.length}, checking partsByTypeId.get(246)...`);
                    if (partsByTypeId.has(246)) {
                        const allType246Parts = partsByTypeId.get(246);
                        console.log(`[DEBUG resistance246] Found ${allType246Parts.length} typeId 246 parts in partsByTypeId`);
                        
                        // Filter for resistance parts (IDs 21-26)
                        const resistanceParts = allType246Parts.filter(partInfo => {
                            const partIdStr = String(partInfo.id || partInfo.fullId || '');
                            let partIdNum = null;
                            if (partIdStr.includes(':')) {
                                const parts = partIdStr.split(':');
                                if (parts.length >= 2) {
                                    partIdNum = parseInt(parts[parts.length - 1]);
                                }
                            } else if (!isNaN(parseInt(partIdStr))) {
                                partIdNum = parseInt(partIdStr);
                            }
                            
                            const spawnCode = String(partInfo.spawnCode || '').toLowerCase();
                            
                            // Check if it's a resistance part (IDs 21-26) or has resistance spawn codes
                            return (partIdNum !== null && partIdNum >= 21 && partIdNum <= 26) ||
                                   spawnCode.includes('part_corrosive') || spawnCode.includes('part_cryo') ||
                                   spawnCode.includes('part_fire') || spawnCode.includes('part_radiation') ||
                                   spawnCode.includes('part_shock');
                        });
                        
                        console.log(`[DEBUG resistance246] Found ${resistanceParts.length} resistance typeId 246 parts`);
                        console.log(`[DEBUG resistance246] Resistance part IDs:`, resistanceParts.map(p => p.fullId || p.id).sort());
                        
                        // Create a set of existing fullIds to check for missing parts
                        const existingFullIds = new Set();
                        categoryParts.forEach(p => {
                            const fullId = String(p.fullId || p.id || '');
                            if (fullId) existingFullIds.add(fullId);
                        });
                        console.log(`[DEBUG resistance246] Existing categoryParts IDs:`, Array.from(existingFullIds).sort());
                        
                        // Find missing parts
                        const missingParts = resistanceParts.filter(partInfo => {
                            const fullId = String(partInfo.fullId || partInfo.id || '');
                            return fullId && !existingFullIds.has(fullId);
                        });
                        
                        if (missingParts.length > 0) {
                            console.log(`[DEBUG resistance246] Found ${missingParts.length} missing resistance parts, adding them...`);
                            console.log(`[DEBUG resistance246] Missing part IDs:`, missingParts.map(p => p.fullId || p.id).sort());
                            // Add missing parts to categoryParts
                            categoryParts.push(...missingParts);
                        } else {
                            console.log(`[DEBUG resistance246] All resistance parts are already in categoryParts`);
                        }
                        
                        // ALWAYS use all resistance typeId 246 parts as the source of truth
                        // This ensures we never miss any parts
                        if (resistanceParts.length > 0) {
                            console.log(`[DEBUG resistance246] Using ALL ${resistanceParts.length} resistance typeId 246 parts for category`);
                            categoryParts = [...resistanceParts];
                        }
                    } else {
                        console.log(`[DEBUG resistance246] ⚠️ partsByTypeId does not have typeId 246`);
                    }
                }
                
                // FALLBACK: For perks246 category, ensure ALL non-firmware, non-resistance typeId 246 parts are included
                // This excludes resistance parts (246:21-246:26) which have their own category
                if (categoryKey === 'perks246') {
                    console.log(`[DEBUG perks246] categoryParts.length = ${categoryParts.length}, checking partsByTypeId.get(246)...`);
                    if (partsByTypeId.has(246)) {
                        const allType246Parts = partsByTypeId.get(246);
                        console.log(`[DEBUG perks246] Found ${allType246Parts.length} typeId 246 parts in partsByTypeId`);
                        
                        // Filter for non-firmware, non-resistance parts (perks only)
                        const perksParts = allType246Parts.filter(partInfo => {
                            const spawnCode = String(partInfo.spawnCode || '').toLowerCase();
                            const partPath = String(partInfo.path || '').toLowerCase();
                            
                            // Extract part ID to check if it's a resistance part (246:21-246:26)
                            let partIdNum = null;
                            const partIdStr = String(partInfo.id || partInfo.fullId || '');
                            if (partIdStr.includes(':')) {
                                const parts = partIdStr.split(':');
                                if (parts.length >= 2) {
                                    partIdNum = parseInt(parts[parts.length - 1]);
                                }
                            } else if (!isNaN(parseInt(partIdStr))) {
                                partIdNum = parseInt(partIdStr);
                            }
                            
                            // Check if it's a resistance part (IDs 21-26)
                            const isResistance = partIdNum !== null && partIdNum >= 21 && partIdNum <= 26;
                            
                            // Exclude firmware parts and resistance parts
                            return !spawnCode.includes('firmware') && 
                                   !partPath.includes('firmware') &&
                                   !isResistance &&
                                   !spawnCode.includes('part_corrosive') && 
                                   !spawnCode.includes('part_cryo') &&
                                   !spawnCode.includes('part_fire') && 
                                   !spawnCode.includes('part_radiation') &&
                                   !spawnCode.includes('part_shock');
                        });
                        
                        console.log(`[DEBUG perks246] Found ${perksParts.length} non-firmware typeId 246 parts`);
                        console.log(`[DEBUG perks246] Perks part IDs:`, perksParts.map(p => p.fullId || p.id).sort());
                        
                        // Create a set of existing fullIds to check for missing parts
                        const existingFullIds = new Set();
                        categoryParts.forEach(p => {
                            const fullId = String(p.fullId || p.id || '');
                            if (fullId) existingFullIds.add(fullId);
                        });
                        console.log(`[DEBUG perks246] Existing categoryParts IDs:`, Array.from(existingFullIds).sort());
                        
                        // Find missing parts
                        const missingParts = perksParts.filter(partInfo => {
                            const fullId = String(partInfo.fullId || partInfo.id || '');
                            return fullId && !existingFullIds.has(fullId);
                        });
                        
                        if (missingParts.length > 0) {
                            console.log(`[DEBUG perks246] Found ${missingParts.length} missing perks parts, adding them...`);
                            console.log(`[DEBUG perks246] Missing part IDs:`, missingParts.map(p => p.fullId || p.id).sort());
                            // Add missing parts to categoryParts
                            categoryParts.push(...missingParts);
                        } else {
                            console.log(`[DEBUG perks246] All perks parts are already in categoryParts`);
                        }
                        
                        // ALWAYS use all non-firmware typeId 246 parts as the source of truth
                        // This ensures we never miss any parts
                        if (perksParts.length > 0) {
                            console.log(`[DEBUG perks246] Using ALL ${perksParts.length} non-firmware typeId 246 parts for category`);
                            categoryParts = [...perksParts];
                        }
                    } else {
                        console.log(`[DEBUG perks246] ⚠️ partsByTypeId does not have typeId 246`);
                    }
                }
                
                // Debug logging for grenade/ordnance categories after build
                if (isGrenade && (categoryKey === 'rarity' || categoryKey === 'body' || categoryKey === 'baseBody')) {
                    console.log(`[DEBUG ordnance ${categoryKey}] After buildPartsByCategory, categoryParts.length = ${categoryParts.length}`);
                    if (categoryParts.length === 0) {
                        console.log(`[DEBUG ordnance ${categoryKey}] ⚠️ No parts found! Checking categoryMap...`);
                        console.log(`[DEBUG ordnance ${categoryKey}] categoryMap.rarity.length = ${partsByCategory.rarity?.length || 0}`);
                        console.log(`[DEBUG ordnance ${categoryKey}] categoryMap.body.length = ${partsByCategory.body?.length || 0}`);
                        console.log(`[DEBUG ordnance ${categoryKey}] categoryMap.baseBody.length = ${partsByCategory.baseBody?.length || 0}`);
                    }
                }
                
                // Debug logging for baseBody category
                if (isShield && categoryKey === 'baseBody') {
                    console.log(`[DEBUG shield baseBody] After buildPartsByCategory, categoryParts.length = ${categoryParts.length}`);
                    console.log(`[DEBUG shield baseBody] categoryMap.baseBody.length = ${partsByCategory.baseBody?.length || 0}`);
                    if (partsByCategory.baseBody && partsByCategory.baseBody.length > 0) {
                        console.log(`[DEBUG shield baseBody] Parts in categoryMap.baseBody:`, partsByCategory.baseBody.map(p => ({
                            name: p.name,
                            id: p.id,
                            fullId: p.fullId,
                            typeId: p.typeId,
                            partType: p.partType,
                            spawnCode: p.spawnCode
                        })));
                    }
                }
                
                // Debug logging for maliwanLicensedUnderbarrel category
                if (categoryKey === 'maliwanLicensedUnderbarrel') {
                    console.log(`[DEBUG maliwanLicensedUnderbarrel] After buildPartsByCategory, categoryParts.length = ${categoryParts.length}`);
                    console.log(`[DEBUG maliwanLicensedUnderbarrel] categoryMap.maliwanLicensedUnderbarrel.length = ${partsByCategory.maliwanLicensedUnderbarrel?.length || 0}`);
                    if (partsByCategory.maliwanLicensedUnderbarrel && partsByCategory.maliwanLicensedUnderbarrel.length > 0) {
                        console.log(`[DEBUG maliwanLicensedUnderbarrel] Parts in categoryMap:`, partsByCategory.maliwanLicensedUnderbarrel.map(p => ({
                            name: p.name,
                            id: p.id,
                            fullId: p.fullId,
                            typeId: p.typeId,
                            spawnCode: p.spawnCode,
                            path: p.path,
                            category: p.category
                        })));
                    } else {
                        console.log(`[DEBUG maliwanLicensedUnderbarrel] ⚠️ No parts found in categoryMap!`);
                    }
                }
                
                // FALLBACK: For maliwanLicensedUnderbarrel category, ensure ALL licensed underbarrel parts from typeId 1 are included
                // This includes parts 1:15-1:22 (part_licensed_underbarrel) and 1:29-1:49 (part_secondary_elem)
                if (categoryKey === 'maliwanLicensedUnderbarrel') {
                    console.log(`[DEBUG maliwanLicensedUnderbarrel] categoryParts.length = ${categoryParts.length}, checking partsByTypeId.get(1)...`);
                    if (partsByTypeId.has(1)) {
                        const allType1Parts = partsByTypeId.get(1);
                        console.log(`[DEBUG maliwanLicensedUnderbarrel] Found ${allType1Parts.length} typeId 1 parts in partsByTypeId`);
                        
                        // Filter for licensed underbarrel parts
                        const licensedUnderbarrelParts = allType1Parts.filter(partInfo => {
                            const spawnCode = String(partInfo.spawnCode || '').toLowerCase();
                            const partPath = String(partInfo.path || '').toLowerCase();
                            const partCategory = String(partInfo.category || '').toLowerCase();
                            
                            return spawnCode.includes('part_secondary_elem') || 
                                   spawnCode.includes('part_licensed_underbarrel') ||
                                   partPath.includes('licensed_underbarrel') ||
                                   partCategory.includes('maliwan licensed') ||
                                   partCategory.includes('maliwan licenced'); // Handle typo
                        });
                        
                        console.log(`[DEBUG maliwanLicensedUnderbarrel] Found ${licensedUnderbarrelParts.length} licensed underbarrel parts from typeId 1`);
                        console.log(`[DEBUG maliwanLicensedUnderbarrel] Licensed underbarrel part IDs:`, licensedUnderbarrelParts.map(p => p.fullId || p.id).sort());
                        
                        // Create a set of existing fullIds to check for missing parts
                        const existingFullIds = new Set();
                        categoryParts.forEach(p => {
                            const fullId = String(p.fullId || p.id || '');
                            if (fullId) existingFullIds.add(fullId);
                        });
                        console.log(`[DEBUG maliwanLicensedUnderbarrel] Existing categoryParts IDs:`, Array.from(existingFullIds).sort());
                        
                        // Find missing parts
                        const missingParts = licensedUnderbarrelParts.filter(partInfo => {
                            const fullId = String(partInfo.fullId || partInfo.id || '');
                            return fullId && !existingFullIds.has(fullId);
                        });
                        
                        if (missingParts.length > 0) {
                            console.log(`[DEBUG maliwanLicensedUnderbarrel] Found ${missingParts.length} missing licensed underbarrel parts, adding them...`);
                            console.log(`[DEBUG maliwanLicensedUnderbarrel] Missing part IDs:`, missingParts.map(p => p.fullId || p.id).sort());
                            // Add missing parts to categoryParts
                            categoryParts.push(...missingParts);
                        } else {
                            console.log(`[DEBUG maliwanLicensedUnderbarrel] All licensed underbarrel parts are already in categoryParts`);
                        }
                        
                        // ALWAYS use all licensed underbarrel parts as the source of truth
                        // This ensures we never miss any parts
                        if (licensedUnderbarrelParts.length > 0) {
                            console.log(`[DEBUG maliwanLicensedUnderbarrel] Using ALL ${licensedUnderbarrelParts.length} licensed underbarrel parts for category`);
                            categoryParts = [...licensedUnderbarrelParts];
                        }
                    } else {
                        console.log(`[DEBUG maliwanLicensedUnderbarrel] ⚠️ partsByTypeId does not have typeId 1`);
                    }
                }
                
                // Handle both singular and plural keys for compatibility
                if (categoryParts.length === 0) {
                    if (categoryKey === 'bodyAccessories') {
                        categoryParts = partsByCategory.bodyAccessory || [];
                    } else if (categoryKey === 'bodyAccessory') {
                        categoryParts = partsByCategory.bodyAccessories || [];
                    } else if (categoryKey === 'barrelAccessories') {
                        categoryParts = partsByCategory.barrelAccessory || [];
                    } else if (categoryKey === 'barrelAccessory') {
                        categoryParts = partsByCategory.barrelAccessories || [];
                    }
                }
                
                // FALLBACK: For licensedParts category, ensure ALL licensed parts from ALL typeIds are included
                if (categoryKey === 'licensedParts' && isWeapon) {
                    console.log(`[DEBUG licensedParts] categoryParts.length = ${categoryParts.length}, checking ALL typeIds for licensed parts...`);
                    
                    // Collect licensed parts from ALL typeIds (not just typeId 13)
                    const allLicensedParts = [];
                    partsByTypeId.forEach((parts, tid) => {
                        const licensedFromTypeId = parts.filter(partInfo => {
                            const spawnCode = String(partInfo.spawnCode || '').toLowerCase();
                            const partPath = String(partInfo.path || '').toLowerCase();
                            const partName = String(partInfo.name || '').toLowerCase();
                            const partType = String(partInfo.partType || '').toLowerCase();
                            const originalPartType = String(partInfo.partType || '');
                            const originalPartPath = String(partInfo.path || '');
                            
                            // Also include ALL parts from "Manufacturer Part" part_type (even if spawn code doesn't contain "licensed")
                            return spawnCode.includes('licensed') || 
                                   spawnCode.includes('_licensed_') ||
                                   partPath.includes('licensed') ||
                                   partName.includes('licensed') ||
                                   partType === 'manufacturer part' ||
                                   originalPartType === 'Manufacturer Part' ||
                                   originalPartPath.includes('Manufacturer Part') ||
                                   (partType === 'manufacturer part' && (spawnCode.includes('_licensed_') || spawnCode.includes('.licensed')));
                        });
                        if (licensedFromTypeId.length > 0) {
                            console.log(`[DEBUG licensedParts] Found ${licensedFromTypeId.length} licensed parts from typeId ${tid}`);
                            allLicensedParts.push(...licensedFromTypeId);
                        }
                    });
                    
                    console.log(`[DEBUG licensedParts] Found ${allLicensedParts.length} total licensed parts across all typeIds`);
                    if (allLicensedParts.length > 0) {
                        console.log(`[DEBUG licensedParts] Licensed part IDs:`, allLicensedParts.map(p => p.fullId || p.id).sort());
                        
                        // Create a set of existing fullIds to check for missing parts
                        const existingFullIds = new Set();
                        categoryParts.forEach(p => {
                            const fullId = String(p.fullId || p.id || '');
                            if (fullId) existingFullIds.add(fullId);
                        });
                        console.log(`[DEBUG licensedParts] Existing categoryParts IDs:`, Array.from(existingFullIds).sort());
                        
                        // Find missing parts
                        const missingParts = allLicensedParts.filter(partInfo => {
                            const fullId = String(partInfo.fullId || partInfo.id || '');
                            return fullId && !existingFullIds.has(fullId);
                        });
                        
                        if (missingParts.length > 0) {
                            console.log(`[DEBUG licensedParts] Found ${missingParts.length} missing licensed parts, adding them...`);
                            console.log(`[DEBUG licensedParts] Missing part IDs:`, missingParts.map(p => p.fullId || p.id).sort());
                            // Add missing parts to categoryParts
                            categoryParts.push(...missingParts);
                        } else {
                            console.log(`[DEBUG licensedParts] All licensed parts are already in categoryParts`);
                        }
                        
                        // ALWAYS use all licensed parts as the source of truth
                        // This ensures we never miss any parts
                        if (allLicensedParts.length > 0) {
                            console.log(`[DEBUG licensedParts] Using ALL ${allLicensedParts.length} licensed parts for category`);
                            categoryParts = [...allLicensedParts];
                        }
                    } else {
                        console.log(`[DEBUG licensedParts] ⚠️ No licensed parts found in any typeId`);
                    }
                }
                
                // For daedalusAmmo in locked mode, filter to only show parts matching current weapon's typeId
                if (categoryKey === 'daedalusAmmo' && !unlocked && categoryParts.length > 0) {
                    categoryParts = categoryParts.filter(partInfo => {
                        const partTypeId = partInfo.typeId || 0;
                        return partTypeId === currentTypeId;
                    });
                }
                
                // For licensedParts: in locked mode, filter to only show licensed parts from the current weapon's manufacturer
                // In unlocked mode, show all licensed parts from all manufacturers
                if (categoryKey === 'licensedParts' && isWeapon) {
                    // Get current weapon type info
                    const typeInfo = typeIdMap.get(currentTypeId);
                    let currentManufacturer = typeInfo ? String(typeInfo.manufacturer || '').toLowerCase().trim() : '';
                    
                    // Normalize manufacturer name (handle variations)
                    if (currentManufacturer) {
                        // Handle common variations
                        if (currentManufacturer.includes('jakob')) currentManufacturer = 'jakobs';
                        else if (currentManufacturer.includes('tedior')) currentManufacturer = 'tediore';
                        else if (currentManufacturer.includes('hyper')) currentManufacturer = 'hyperion';
                        else if (currentManufacturer.includes('maliw')) currentManufacturer = 'maliwan';
                        else if (currentManufacturer.includes('vlado')) currentManufacturer = 'vladof';
                        else if (currentManufacturer.includes('torgu')) currentManufacturer = 'torgue';
                        else if (currentManufacturer.includes('bandi')) currentManufacturer = 'bandit';
                        else if (currentManufacturer.includes('dahl')) currentManufacturer = 'dahl';
                        else if (currentManufacturer.includes('atlas')) currentManufacturer = 'atlas';
                        else if (currentManufacturer.includes('coastal')) currentManufacturer = 'coastal';
                        else if (currentManufacturer.includes('daedal')) currentManufacturer = 'daedalus';
                        else if (currentManufacturer.includes('pandor')) currentManufacturer = 'pandoran';
                    }
                    
                    if (!unlocked && currentManufacturer) {
                        // LOCKED MODE: Filter to only show licensed parts from the current manufacturer
                        // Licensed parts have spawnCodes like "JAK_SG.part_barrel_licensed_ted" where "JAK" is the weapon manufacturer
                        // We want to show licensed parts that are FOR this manufacturer's weapons (spawnCode starts with manufacturer prefix)
                        // Map manufacturer names to their spawnCode prefixes
                        const manufacturerPrefixMap = {
                            'jakobs': ['jak'],
                            'tediore': ['ted'],
                            'hyperion': ['hyp', 'hypr'],
                            'maliwan': ['mal'],
                            'vladof': ['vla', 'vlad'],
                            'torgue': ['tor', 'torg'],
                            'bandit': ['ban', 'band'],
                            'dahl': ['dah'],
                            'atlas': ['atl', 'atls'],
                            'coastal': ['coa', 'coast'],
                            'daedalus': ['dae', 'daed'],
                            'pandoran': ['pan', 'pand']
                        };
                        
                        const currentPrefixes = manufacturerPrefixMap[currentManufacturer] || [currentManufacturer.substring(0, 3).toLowerCase()];
                        
                        // Helper function to extract manufacturer prefix from spawnCode
                        const getSpawnCodePrefix = (spawnCode) => {
                            const sc = String(spawnCode || '').toLowerCase();
                            if (!sc) return '';
                            if (sc.includes('_')) {
                                return sc.split('_')[0];
                            } else if (sc.includes('.')) {
                                return sc.split('.')[0];
                            }
                            return sc.substring(0, Math.min(3, sc.length));
                        };
                        
                        // Helper function to check if spawnCode matches any of the current manufacturer prefixes
                        const matchesManufacturer = (spawnCode) => {
                            if (!spawnCode) return false;
                            const prefix = getSpawnCodePrefix(spawnCode);
                            if (!prefix) return false;
                            // Check if prefix exactly matches any of the current manufacturer prefixes
                            return currentPrefixes.some(p => prefix === p);
                        };
                        
                        // Keep all parts from currentTypeId (they're already correctly scoped to this weapon type/manufacturer)
                        // Only filter by manufacturer for parts from typeId 9 and 13
                        const partsFromCurrentTypeId = categoryParts.filter(partInfo => {
                            const partTypeId = partInfo.typeId || 0;
                            return partTypeId === currentTypeId;
                        });
                        
                        // Get licensed parts from typeId 9 and 13, filtering by manufacturer
                        const licensedPartsFromOtherTypeIds = [];
                        [9, 13].forEach(tid => {
                            if (partsByTypeId.has(tid) && tid !== currentTypeId) {
                                const partsFromTypeId = partsByTypeId.get(tid);
                                const licensedFromTypeId = partsFromTypeId.filter(partInfo => {
                                    const spawnCode = String(partInfo.spawnCode || '');
                                    const partPath = String(partInfo.path || '').toLowerCase();
                                    const partName = String(partInfo.name || '').toLowerCase();
                                    
                                    // Check if it's a licensed part
                                    // Also include ALL parts from "Manufacturer Part" part_type (even if spawn code doesn't contain "licensed")
                                    const partTypeCheck = String(partInfo.partType || '').toLowerCase();
                                    const originalPartTypeCheck = String(partInfo.partType || '');
                                    const originalPartPathCheck = String(partInfo.path || '');
                                    const isLicensed = spawnCode.includes('licensed') || spawnCode.includes('_licensed_') ||
                                                      partPath.includes('licensed') || partName.includes('licensed') ||
                                                      partTypeCheck === 'manufacturer part' ||
                                                      originalPartTypeCheck === 'Manufacturer Part' ||
                                                      originalPartPathCheck.includes('Manufacturer Part');
                                    if (!isLicensed) return false;
                                    
                                    // Check if it's for the current manufacturer's weapons
                                    return matchesManufacturer(spawnCode);
                                });
                                licensedPartsFromOtherTypeIds.push(...licensedFromTypeId);
                            }
                        });
                        
                        // Combine parts from currentTypeId with licensed parts from typeId 9 and 13
                        categoryParts = [...partsFromCurrentTypeId, ...licensedPartsFromOtherTypeIds];
                    }
                    // UNLOCKED MODE: Show all licensed parts (no filtering by manufacturer)
                    // categoryParts already contains all licensed parts, so no filtering needed
                }
                
                // Deduplicate categoryParts by fullId to avoid duplicates
                if (categoryParts.length > 0) {
                    const seen = new Set();
                    categoryParts = categoryParts.filter(partInfo => {
                        const fullId = String(partInfo.fullId || partInfo.id || '');
                        if (fullId && seen.has(fullId)) {
                            return false; // Duplicate, filter it out
                        }
                        if (fullId) seen.add(fullId);
                        return true;
                    });
                    
                    // For element category, sort by part ID to ensure proper ordering
                    if (categoryKey === 'element') {
                        categoryParts.sort((a, b) => {
                            // Extract numeric part ID from fullId (e.g., "1:15" -> 15)
                            const getPartIdNum = (partInfo) => {
                                const fullId = String(partInfo.fullId || partInfo.id || '');
                                if (fullId.includes(':')) {
                                    const parts = fullId.split(':');
                                    if (parts.length >= 2) {
                                        const num = parseInt(parts[parts.length - 1]);
                                        return isNaN(num) ? 0 : num;
                                    }
                                } else if (!isNaN(parseInt(fullId))) {
                                    return parseInt(fullId);
                                }
                                return 0;
                            };
                            return getPartIdNum(a) - getPartIdNum(b);
                        });
                        console.log(`[DEBUG element] After sorting: ${categoryParts.length} parts, first 5:`, categoryParts.slice(0, 5).map(p => `${p.fullId || p.id} - ${p.name}`));
                    }
                }
                
                // Special handling for skills category: Group by skill name instead of showing individual tiers
                if (categoryKey === 'skills' && categoryParts.length > 0) {
                    // Group skills by their base name (extract from "age_of_ice - Age of Ice" -> "Age of Ice")
                    const skillGroups = new Map();
                    const processedSkillGroups = new Set(); // Track skill groups that have been fully processed
                    
                    // Process skill parts - prioritize skill group parts (those with skillIds)
                    categoryParts.forEach(partInfo => {
                        // Extract skill name - prefer skillName field, then name field
                        let skillName = partInfo.skillName || partInfo.name || '';
                        
                        // If we have a skill group part with skillIds, use its skillName directly
                        if (partInfo.skillIds && partInfo.skillName) {
                            skillName = partInfo.skillName;
                        } else {
                            // For individual tier parts, extract from name
                            skillName = skillName.replace(/\s*\(Tier\s+\d+\)\s*$/i, '');
                            if (skillName.includes(' - ')) {
                                const parts = skillName.split(' - ');
                                if (parts.length >= 2) {
                                    skillName = parts.slice(1).join(' - ');
                                }
                            }
                        }
                        
                        skillName = skillName.trim();
                        
                        if (!skillName) return; // Skip if no valid name
                        
                        // If this is an individual tier part and the skill group was already processed, skip it
                        if (!partInfo.skillIds && processedSkillGroups.has(skillName)) {
                            return;
                        }
                        
                        // Get or create skill group
                        if (!skillGroups.has(skillName)) {
                            skillGroups.set(skillName, {
                                name: skillName,
                                tiers: [],
                                typeId: partInfo.typeId || currentTypeId,
                                limiter: parseInt(partInfo.limiter) || 5 // Default to 5 if no limiter specified
                            });
                        }
                        
                        // Update limiter if we have a more specific value from this partInfo
                        if (partInfo.limiter !== undefined && partInfo.limiter !== null && partInfo.limiter !== '') {
                            const limiterValue = parseInt(partInfo.limiter);
                            if (!isNaN(limiterValue)) {
                                skillGroups.get(skillName).limiter = limiterValue;
                            }
                        }
                        
                        // For skills, we need to extract tier information from skillIds
                        // If this is a skill group part (has skillIds), extract tiers from it
                        if (partInfo.skillIds && typeof partInfo.skillIds === 'object') {
                            const skillTypeId = partInfo.typeId || currentTypeId;
                            
                            // Process each tier from skillIds
                            for (const [tierKey, tierData] of Object.entries(partInfo.skillIds)) {
                                // Skip 'dlc' field and other non-tier keys
                                if (tierKey === 'dlc' || !tierData || typeof tierData !== 'object' || !tierData.id) {
                                    continue;
                                }
                                
                                // Extract numeric part ID from tier ID (format: "255:49" -> 49)
                                let tierPartId = null;
                                const tierIdStr = String(tierData.id || '');
                                
                                if (tierIdStr.includes(':')) {
                                    const parts = tierIdStr.split(':');
                                    if (parts.length >= 2) {
                                        tierPartId = parseInt(parts[parts.length - 1]);
                                    }
                                } else {
                                    tierPartId = parseInt(tierIdStr);
                                }
                                
                                if (isNaN(tierPartId) || tierPartId === 0) {
                                    console.warn(`[SKILLS] Invalid tier ID for ${skillName}, tier=${tierKey}, id=${tierData.id}`);
                                    continue;
                                }
                                
                                // Extract tier number from tier key (e.g., "tier_1" -> 1)
                                const tierNumMatch = tierKey.match(/tier_(\d+)/i);
                                const tierNum = tierNumMatch ? parseInt(tierNumMatch[1]) : 1;
                                
                                // Look up the actual tier part info from partsMap
                                const tierFullId = `${skillTypeId}:${tierPartId}`;
                                const tierPartInfo = partsMap.get(tierFullId) || partsMap.get(tierPartId) || partsMap.get(String(tierPartId));
                                
                                // Add tier to skill group
                                skillGroups.get(skillName).tiers.push({
                                    tier: tierNum,
                                    partId: tierPartId,
                                    fullId: tierFullId,
                                    typeId: skillTypeId,
                                    partInfo: tierPartInfo || {
                                        id: tierPartId,
                                        fullId: tierFullId,
                                        typeId: skillTypeId,
                                        name: `${skillName} (Tier ${tierNum})`,
                                        branch: tierData.branch || ''
                                    }
                                });
                            }
                            
                            // Sort tiers by tier number
                            skillGroups.get(skillName).tiers.sort((a, b) => a.tier - b.tier);
                            
                            // Mark this skill group as processed
                            processedSkillGroups.add(skillName);
                        } else {
                            // Fallback: This is a tier part itself (not a skill group)
                            // Extract part ID - prioritize numeric ID
                            let partId = partInfo.id || '';
                            const fullId = partInfo.fullId || '';
                            
                            // If partId is a string identifier (not numeric), try to find the numeric ID
                            if (typeof partId === 'string' && isNaN(parseInt(partId))) {
                                // Try to extract numeric ID from spawnCode if available
                                if (partInfo.spawnCode) {
                                    const spawnCodeMatch = partInfo.spawnCode.match(/\d+/);
                                    if (spawnCodeMatch) {
                                        partId = spawnCodeMatch[0];
                                    }
                                }
                                
                                // If still not numeric, try to extract from fullId
                                if (fullId.includes(':')) {
                                    const parts = fullId.split(':');
                                    if (parts.length >= 2) {
                                        const extractedId = parts[parts.length - 1];
                                        // Only use if it's numeric
                                        if (!isNaN(parseInt(extractedId))) {
                                            partId = extractedId;
                                        }
                                    }
                                }
                                
                                // If still not numeric, try looking up the part by string identifier
                                if (typeof partId === 'string' && isNaN(parseInt(partId))) {
                                    // Look up in partsMap using the string identifier
                                    const lookupPart = partsMap.get(partId) || partsMap.get(fullId);
                                    if (lookupPart) {
                                        // Try to get numeric ID from the looked-up part
                                        let lookupId = lookupPart.id;
                                        if (typeof lookupId === 'string' && !isNaN(parseInt(lookupId))) {
                                            partId = lookupId;
                                        } else if (lookupPart.fullId && lookupPart.fullId.includes(':')) {
                                            const parts = lookupPart.fullId.split(':');
                                            if (parts.length >= 2 && !isNaN(parseInt(parts[parts.length - 1]))) {
                                                partId = parts[parts.length - 1];
                                            }
                                        }
                                    }
                                }
                            } else if (fullId.includes(':')) {
                                // If fullId exists and partId might not be set correctly, extract from fullId
                                const parts = fullId.split(':');
                                if (parts.length >= 2) {
                                    const extractedId = parts[parts.length - 1];
                                    // Prefer numeric ID from fullId if partId is not numeric
                                    if (!isNaN(parseInt(extractedId)) && (isNaN(parseInt(partId)) || !partId)) {
                                        partId = extractedId;
                                    }
                                }
                            } else if (!partId && fullId) {
                                partId = fullId;
                            }
                            
                            // Ensure partId is a number (for simple parts)
                            let numericPartId = null;
                            if (typeof partId === 'string') {
                                numericPartId = parseInt(partId);
                                if (isNaN(numericPartId)) {
                                    // If still not numeric after all attempts, skip this part
                                    console.warn(`[SKILLS] Could not extract numeric partId for skill part: ${partInfo.name}, id=${partInfo.id}, fullId=${fullId}, spawnCode=${partInfo.spawnCode}`);
                                    return;
                                }
                            } else {
                                numericPartId = parseInt(partId);
                                if (isNaN(numericPartId)) {
                                    console.warn(`[SKILLS] Invalid numeric partId for skill part: ${partInfo.name}, partId=${partId}`);
                                    return;
                                }
                            }
                            
                            // Extract tier number from name (e.g., "Age of Ice (Tier 1)" -> 1)
                            let tierNum = 1;
                            const partNameStr = String(partInfo.name || '');
                            const tierMatch = partNameStr.match(/\(Tier\s+(\d+)\)/i);
                            if (tierMatch) {
                                tierNum = parseInt(tierMatch[1]);
                            } else {
                                // If no tier in name, try to infer from part ID or position
                                // For now, just use the order they appear
                                tierNum = skillGroups.get(skillName).tiers.length + 1;
                            }
                            
                            // Add tier part info - store partId as number
                            skillGroups.get(skillName).tiers.push({
                                tier: tierNum,
                                partId: numericPartId,
                                fullId: fullId || `${partInfo.typeId || currentTypeId}:${numericPartId}`,
                                typeId: partInfo.typeId || currentTypeId,
                                partInfo: partInfo
                            });
                        }
                    });
                    
                    // Sort tiers within each skill group
                    skillGroups.forEach(group => {
                        group.tiers.sort((a, b) => a.tier - b.tier);
                    });
                    
                    // Convert to array and sort by skill name
                    const groupedSkills = Array.from(skillGroups.values()).sort((a, b) => 
                        a.name.localeCompare(b.name)
                    );
                    
                    // Return grouped skills instead of individual tier parts
                    return groupedSkills;
                }
                
                // Debug logging for baseBody247
                if (categoryKey === 'baseBody247') {
                    console.log(`[DEBUG baseBody247] getAvailablePartsForCategory returning ${categoryParts.length} parts for categoryKey=${categoryKey}, unlocked=${unlocked} (after deduplication)`);
                }
                
                // FALLBACK: For statModifier category, ensure typeId 1 universal stat modifiers (pearl_damage, pearl_reload, etc.) are included
                if (categoryKey === 'statModifier' && partsByTypeId.has(1)) {
                    const type1Parts = partsByTypeId.get(1);
                    const statModifierParts = type1Parts.filter(p => {
                        const pt = String(p.partType || '').toLowerCase();
                        return pt === 'stat modifier' || (pt.includes('stat') && pt.includes('modifier'));
                    });
                    const existingIds = new Set(categoryParts.map(p => String(p.fullId || p.id || '')));
                    statModifierParts.forEach(p => {
                        const fullId = String(p.fullId || p.id || '');
                        if (fullId && !existingIds.has(fullId)) {
                            categoryParts.push(p);
                            existingIds.add(fullId);
                        }
                    });
                }
                
                // FALLBACK: For element category, ensure ALL typeId 1 parts are included
                // This ensures parts 1:15-1:22 and 1:29-1:49 are always available
                if (categoryKey === 'element') {
                    console.log(`[DEBUG element] categoryParts.length = ${categoryParts.length}, checking partsByTypeId.get(1)...`);
                    if (partsByTypeId.has(1)) {
                        const allType1Parts = partsByTypeId.get(1);
                        console.log(`[DEBUG element] Found ${allType1Parts.length} typeId 1 parts in partsByTypeId`);
                        
                        // Log all part IDs to see what we have
                        console.log(`[DEBUG element] All typeId 1 part IDs:`, allType1Parts.map(p => p.fullId || p.id).sort());
                        
                        // Create a set of existing fullIds to check for missing parts
                        const existingFullIds = new Set();
                        categoryParts.forEach(p => {
                            const fullId = String(p.fullId || p.id || '');
                            if (fullId) existingFullIds.add(fullId);
                        });
                        console.log(`[DEBUG element] Existing categoryParts IDs:`, Array.from(existingFullIds).sort());
                        
                        // Find missing parts
                        const missingParts = allType1Parts.filter(partInfo => {
                            const fullId = String(partInfo.fullId || partInfo.id || '');
                            return fullId && !existingFullIds.has(fullId);
                        });
                        
                        if (missingParts.length > 0) {
                            console.log(`[DEBUG element] Found ${missingParts.length} missing typeId 1 parts, adding them...`);
                            console.log(`[DEBUG element] Missing part IDs:`, missingParts.map(p => p.fullId || p.id).sort());
                            // Add missing parts to categoryParts
                            categoryParts.push(...missingParts);
                            
                            // Log sample of added parts
                            console.log(`[DEBUG element] Added parts:`, missingParts.slice(0, 10).map(p => ({
                                id: p.id,
                                fullId: p.fullId,
                                name: p.name
                            })));
                        } else {
                            console.log(`[DEBUG element] All typeId 1 parts are already in categoryParts`);
                        }
                        
                        // ALWAYS use all typeId 1 parts as the source of truth for element category
                        // This ensures we never miss any parts
                        if (allType1Parts.length > 0) {
                            console.log(`[DEBUG element] Using ALL ${allType1Parts.length} typeId 1 parts for element category`);
                            categoryParts = [...allType1Parts];
                        }
                        
                        // Exclude Pearl stat modifiers (1:51–1:54) from Element – they belong in Stat Modifier only
                        categoryParts = categoryParts.filter(p => {
                            const id = String(p.fullId || p.id || '');
                            return id !== '1:51' && id !== '1:52' && id !== '1:53' && id !== '1:54';
                        });
                    } else {
                        console.log(`[DEBUG element] ⚠️ partsByTypeId does not have typeId 1`);
                    }
                }
                
                // FALLBACK: If baseBody247 has no parts, try to find them directly from partsByTypeId
                if (categoryKey === 'baseBody247' && categoryParts.length === 0) {
                    console.log('[DEBUG baseBody247] No parts found in categoryMap. Trying direct lookup from partsByTypeId.get(247)...');
                    if (partsByTypeId.has(247)) {
                        const type247Parts = partsByTypeId.get(247);
                        console.log('[DEBUG baseBody247] Found', type247Parts.length, 'typeId 247 parts in partsByTypeId');
                        
                        // Directly filter for Main Body parts (IDs 76-80 or Main Body in path/type)
                        const mainBodyParts = type247Parts.filter(partInfo => {
                            const partIdStr = String(partInfo.id || '');
                            const fullIdStr = String(partInfo.fullId || '');
                            const pathStr = String(partInfo.path || '');
                            const partTypeStr = String(partInfo.partType || '');
                            
                            // Extract numeric ID
                            let partIdNum = null;
                            if (partIdStr.includes(':')) {
                                const parts = partIdStr.split(':');
                                if (parts.length >= 2) {
                                    partIdNum = parseInt(parts[parts.length - 1]);
                                }
                            } else if (!isNaN(parseInt(partIdStr))) {
                                partIdNum = parseInt(partIdStr);
                            }
                            
                            if (fullIdStr.includes(':')) {
                                const parts = fullIdStr.split(':');
                                if (parts.length >= 2 && (partIdNum === null || isNaN(partIdNum))) {
                                    partIdNum = parseInt(parts[parts.length - 1]);
                                }
                            }
                            
                            // Check if it's a Main Body part
                            const isMainBodyById = partIdNum !== null && !isNaN(partIdNum) && partIdNum >= 76 && partIdNum <= 80;
                            const isMainBodyByPath = pathStr.includes('Main Body') || pathStr.toLowerCase().includes('main body');
                            const isMainBodyByType = partTypeStr === 'Main Body' || partTypeStr.toLowerCase() === 'main body';
                            
                            return isMainBodyById || isMainBodyByPath || isMainBodyByType;
                        });
                        
                        console.log('[DEBUG baseBody247] Found', mainBodyParts.length, 'Main Body parts via direct lookup');
                        if (mainBodyParts.length > 0) {
                            // Deduplicate fallback parts
                            const seen = new Set();
                            categoryParts = mainBodyParts.filter(partInfo => {
                                const fullId = String(partInfo.fullId || partInfo.id || '');
                                if (fullId && seen.has(fullId)) {
                                    return false; // Duplicate
                                }
                                if (fullId) seen.add(fullId);
                                return true;
                            });
                            console.log('[DEBUG baseBody247] Using', categoryParts.length, 'Main Body parts as fallback (after deduplication)');
                        }
                    } else {
                        console.log('[DEBUG baseBody247] partsByTypeId does not have typeId 247');
                    }
                }
                
                if (categoryKey === 'baseBody247' && categoryParts.length === 0) {
                    console.log('[DEBUG baseBody247] Still no parts found after fallback. Checking partsByTypeId.get(247):', 
                        partsByTypeId.has(247) ? partsByTypeId.get(247).length : 0, 'parts');
                    if (partsByTypeId.has(247)) {
                        const type247Parts = partsByTypeId.get(247);
                        console.log('[DEBUG baseBody247] All typeId 247 parts:', type247Parts.length);
                        
                        // Check for parts with IDs 76-80 - handle both numeric and string IDs
                        const id76to80Parts = type247Parts.filter(p => {
                            let partIdNum = null;
                            
                            // Handle numeric ID directly
                            if (typeof p.id === 'number' && !isNaN(p.id)) {
                                partIdNum = p.id;
                            } else {
                                const idStr = String(p.id || '');
                                const fullIdStr = String(p.fullId || '');
                                
                                if (idStr.includes(':')) {
                                    const parts = idStr.split(':');
                                    if (parts.length >= 2) {
                                        partIdNum = parseInt(parts[parts.length - 1]);
                                    }
                                } else if (idStr && !isNaN(parseInt(idStr))) {
                                    partIdNum = parseInt(idStr);
                                }
                                
                                if ((partIdNum === null || isNaN(partIdNum)) && fullIdStr) {
                                    if (fullIdStr.includes(':')) {
                                        const parts = fullIdStr.split(':');
                                        if (parts.length >= 2) {
                                            partIdNum = parseInt(parts[parts.length - 1]);
                                        }
                                    } else if (fullIdStr && !isNaN(parseInt(fullIdStr))) {
                                        partIdNum = parseInt(fullIdStr);
                                    }
                                }
                            }
                            
                            return partIdNum !== null && !isNaN(partIdNum) && partIdNum >= 76 && partIdNum <= 80;
                        });
                        
                        console.log('[DEBUG baseBody247] Found', id76to80Parts.length, 'parts with IDs 76-80');
                        if (id76to80Parts.length > 0) {
                            console.log('[DEBUG baseBody247] Parts with IDs 76-80:', id76to80Parts.map(p => ({
                                id: p.id,
                                idType: typeof p.id,
                                fullId: p.fullId,
                                partType: p.partType,
                                path: p.path,
                                spawnCode: p.spawnCode,
                                typeId: p.typeId
                            })));
                            
                            // Check if these parts are in the categoryMap
                            const partsByCategory = buildPartsByCategory();
                            const categorizedBaseBody247 = partsByCategory.baseBody247 || [];
                            console.log('[DEBUG baseBody247] Parts in categoryMap.baseBody247:', categorizedBaseBody247.length);
                            if (categorizedBaseBody247.length === 0 && id76to80Parts.length > 0) {
                                console.log('[DEBUG baseBody247] ERROR: Parts exist but not categorized! Sample part:', {
                                    id: id76to80Parts[0].id,
                                    fullId: id76to80Parts[0].fullId,
                                    partType: id76to80Parts[0].partType,
                                    path: id76to80Parts[0].path,
                                    typeId: id76to80Parts[0].typeId
                                });
                            }
                        }
                        
                        const mainBodyParts = type247Parts.filter(p => {
                            const pt = String(p.partType || '').toLowerCase();
                            const path = String(p.path || '').toLowerCase();
                            return pt === 'main body' || pt.includes('main body') || path.includes('main body');
                        });
                        console.log('[DEBUG baseBody247] Found', mainBodyParts.length, 'Main Body parts in typeId 247');
                        if (mainBodyParts.length > 0) {
                            console.log('[DEBUG baseBody247] Sample Main Body parts:', mainBodyParts.slice(0, 3).map(p => ({
                                id: p.id,
                                fullId: p.fullId,
                                partType: p.partType,
                                path: p.path,
                                typeId: p.typeId
                            })));
                        }
                    }
                }
                
                return categoryParts;
            };
            
            // Helper function to format part for dropdown display
            const formatPartForDropdown = (partInfo) => {
                const currentTypeId = parseInt(document.getElementById('typeId').value) || 0;
                let partId = partInfo.id || '';
                const fullId = partInfo.fullId || '';
                const partTypeId = partInfo.typeId || currentTypeId;
                
                // Extract numeric part ID from fullId or id, handling cases where they contain colons
                if (fullId && fullId.includes(':')) {
                    const parts = fullId.split(':');
                    if (parts.length >= 2) {
                        partId = parts[parts.length - 1]; // Get the last part after colon (the actual part ID)
                    }
                } else if (!partId && fullId) {
                    partId = fullId;
                }
                
                // If partId is still empty, try to extract from id
                if (!partId && partInfo.id) {
                    const idStr = String(partInfo.id);
                    if (idStr.includes(':')) {
                        const parts = idStr.split(':');
                        if (parts.length >= 2) {
                            partId = parts[parts.length - 1]; // Get the last part after colon
                        }
                    } else {
                        partId = idStr;
                    }
                }
                
                // Ensure partId is numeric (remove any non-numeric characters if it's a string identifier)
                const numericPartId = parseInt(partId);
                if (isNaN(numericPartId)) {
                    // If it's not numeric (like "abajo"), use it as-is
                    partId = String(partId);
                } else {
                    partId = numericPartId;
                }
                
                const partName = partInfo.name || 'Unknown';
                
                // Build display ID - always construct it properly to avoid duplication
                let displayFullId;
                if (partTypeId === currentTypeId) {
                    // Same typeId as current item, use simple format
                    displayFullId = `${partId}`;
                } else {
                    // Different typeId, use typed format: typeId:partId
                    displayFullId = `${partTypeId}:${partId}`;
                }
                
                // Special handling for Energy Shield parts (typeId 248), Armor Shield parts (typeId 237), Shield Perks (typeId 246), Universal Enhancements (typeId 247), and Grenade/Ordnance parts (typeId 245) - make them more descriptive
                if (partTypeId === 248 || partTypeId === 237 || partTypeId === 246 || partTypeId === 247 || partTypeId === 245) {
                    let categoryLabel = '';
                    let displayString = `${displayFullId} - `;
                    
                    if (partTypeId === 248) {
                        categoryLabel = 'Energy Shield';
                        const modelName = partInfo.modelName || '';
                        const stats = partInfo.stats || '';
                        
                        if (modelName) {
                            displayString += `${modelName}`;
                            if (stats) {
                                displayString += ` - ${stats}`;
                            }
                        } else {
                            displayString += `${partName}`;
                            if (stats) {
                                displayString += ` - ${stats}`;
                            }
                        }
                    } else if (partTypeId === 237) {
                        categoryLabel = 'Armor Shield';
                        const modelName = partInfo.modelName || '';
                        const stats = partInfo.stats || '';
                        
                        if (modelName) {
                            displayString += `${modelName}`;
                            if (stats) {
                                displayString += ` - ${stats}`;
                            }
                        } else {
                            displayString += `${partName}`;
                            if (stats) {
                                displayString += ` - ${stats}`;
                            }
                        }
                    } else if (partTypeId === 246) {
                        categoryLabel = 'Shield Perks';
                        const modelName = partInfo.modelName || '';
                        const stats = partInfo.stats || '';
                        
                        if (modelName) {
                            displayString += `${modelName}`;
                            if (stats) {
                                displayString += ` - ${stats}`;
                            }
                        } else {
                            displayString += `${partName}`;
                            if (stats) {
                                displayString += ` - ${stats}`;
                            }
                        }
                    } else if (partTypeId === 247) {
                        categoryLabel = 'Universal enhancements';
                        // For enhancements, use description field which contains name + stat value
                        const description = partInfo.description || partInfo.stats || '';
                        
                        if (description) {
                            displayString += `${description}`;
                        } else {
                            // Fallback to partName if description not available
                            displayString += `${partName}`;
                        }
                    } else if (partTypeId === 245) {
                        // For grenade/ordnance parts (Payload, Augment, Stats), use name and stats
                        const stats = partInfo.stats || '';
                        const description = partInfo.description || '';
                        
                        // Use name (which is already descriptive like "MIRV Payload", "Duration Augment")
                        displayString += `${partName}`;
                        
                        // Add stats if available (prefer stats over description for consistency)
                        if (stats) {
                            displayString += ` - ${stats}`;
                        } else if (description && !stats) {
                            // Fallback to description if stats not available
                            displayString += ` - ${description}`;
                        }
                        
                        // Determine category label based on partType
                        const partType = String(partInfo.partType || '').toLowerCase();
                        if (partType === 'payload') {
                            categoryLabel = 'Grenade/Ordnance';
                        } else if (partType === 'augment') {
                            categoryLabel = 'Grenade/Ordnance';
                        } else if (partType === 'stats' || partType === 'stat') {
                            categoryLabel = 'Grenade/Ordnance';
                        } else {
                            // Default category label
                            const typeInfo = typeIdMap.get(partTypeId);
                            categoryLabel = typeInfo ? (typeInfo.name || typeInfo.category || 'Grenade/Ordnance') : 'Grenade/Ordnance';
                        }
                    }
                    
                    displayString += ` [${categoryLabel}]`;
                    return displayString;
                }
                
                // Get manufacturer and item type information
                const manufacturer = partInfo.manufacturer || '';
                let itemType = '';
                const typeInfo = typeIdMap.get(partTypeId);
                if (typeInfo) {
                    // Prefer name (specific type like "Shotgun", "Pistol") over category (generic like "Weapon")
                    // Also check partInfo.weaponType as a fallback
                    itemType = partInfo.weaponType || typeInfo.name || typeInfo.category || '';
                }
                
                // Build the display string with manufacturer and item type
                let displayString = `${displayFullId} - ${partName}`;
                const parts = [];
                if (manufacturer) {
                    parts.push(manufacturer);
                }
                if (itemType) {
                    parts.push(itemType);
                }
                if (parts.length > 0) {
                    displayString += ` [${parts.join(' ')}]`;
                }
                
                return displayString;
            };
            
            // Helper function to get rarity color for dropdown options
            const getRarityColor = (partInfo) => {
                if (!partInfo) return '#b0d4fa'; // Default light blue for dark backgrounds
                
                // Pearl items (stat modifiers 1:51–1:54, override elements 1:55–1:60, Pearl comp legendaries 11:82, 25:82, 6:78) – cyan so they stand out
                const fullId = String(partInfo.fullId || partInfo.id || '');
                const spawnCode = String(partInfo.spawnCode || '').toLowerCase();
                if (fullId === '1:51' || fullId === '1:52' || fullId === '1:53' || fullId === '1:54' ||
                    fullId === '1:55' || fullId === '1:56' || fullId === '1:57' || fullId === '1:58' || fullId === '1:59' || fullId === '1:60' ||
                    fullId === '11:82' || fullId === '25:82' || fullId === '6:78' ||
                    spawnCode.includes('pearl_damage') || spawnCode.includes('pearl_reload') ||
                    spawnCode.includes('pearl_firerate') || spawnCode.includes('pearl_handling') ||
                    spawnCode.includes('pearl_normal') || spawnCode.includes('pearl_shock') || spawnCode.includes('pearl_radiation') ||
                    spawnCode.includes('pearl_corrosive') || spawnCode.includes('pearl_cryo') || spawnCode.includes('pearl_fire') ||
                    spawnCode.includes('comp_05_legendary_eigenburst') || spawnCode.includes('comp_05_legendary_conflux') || spawnCode.includes('comp_05_legendary_handcannon')) {
                    return '#00E5FF'; // Bright cyan – Pearlescent
                }
                
                // Check rarity field first
                let rarityText = String(partInfo.rarity || '').toLowerCase();
                
                // If no rarity field, check the name for rarity keywords
                if (!rarityText && partInfo.name) {
                    const nameLower = String(partInfo.name).toLowerCase();
                    if (nameLower.includes('legendary')) rarityText = 'legendary';
                    else if (nameLower.includes('epic')) rarityText = 'epic';
                    else if (nameLower.includes('rare')) rarityText = 'rare';
                    else if (nameLower.includes('uncommon')) rarityText = 'uncommon';
                    else if (nameLower.includes('common')) rarityText = 'common';
                }
                
                // Return color based on rarity
                if (rarityText.includes('legendary')) return '#FFD700'; // Gold
                if (rarityText.includes('epic')) return '#DDA0DD'; // Plum
                if (rarityText.includes('rare')) return '#87CEEB'; // Sky blue
                if (rarityText.includes('uncommon')) return '#90EE90'; // Light green
                if (rarityText.includes('common')) return '#E0E0E0'; // Light gray
                return '#b0d4fa'; // Default light blue for dark backgrounds
            };
            
            // Helper function to add a part from dropdown selection
            const addPartFromGuidelineDropdown = (categoryKey, partData, allowDuplicates = false) => {
                if (!partData) return false;
                
                const currentTypeId = parseInt(document.getElementById('typeId').value);
                if (!currentTypeId) {
                    alert('Please select a Type ID first!');
                    return false;
                }
                
                // Get full part info from partsMap
                const fullId = partData.fullId || `${partData.typeId || currentTypeId}:${partData.id}`;
                let partInfo = partsMap.get(fullId);
                if (!partInfo && partData.typeId) {
                    // Try alternative key format
                    partInfo = partsMap.get(`${partData.typeId}:${partData.id}`);
                }
                if (!partInfo && partData.id) {
                    // Try simple key
                    partInfo = partsMap.get(partData.id);
                }
                
                // Determine part format based on partData
                let partToAdd = null;
                let partId = partData.id || '';
                const partTypeId = partData.typeId || (partInfo ? partInfo.typeId : currentTypeId);
                
                // Extract numeric part ID if partId contains a colon (e.g., "234:123" -> 123)
                if (typeof partId === 'string' && partId.includes(':')) {
                    const parts = partId.split(':');
                    partId = parts[parts.length - 1]; // Get the last part after colon
                }
                
                if (partTypeId === currentTypeId) {
                    // Simple part
                    const partValue = parseInt(partId);
                    if (!isNaN(partValue) && partValue !== 0) {
                        partToAdd = {
                            type: 'simple',
                            value: partValue
                        };
                    }
                } else {
                    // Typed part (cross-typeId)
                    const partValue = parseInt(partId);
                    if (!isNaN(partValue) && partValue !== 0) {
                        partToAdd = {
                            type: 'typed',
                            typeId: partTypeId,
                            value: partValue
                        };
                    }
                }
                
                if (partToAdd) {
                    // Check if this is a rarity part - only remove existing rarity parts if adding from the rarity category
                    // This prevents removing rarity parts when adding body parts that might be incorrectly identified as rarity
                    const isRarity = categoryKey === 'rarity';
                    if (isRarity) {
                        // Remove all existing rarity parts
                        currentParts = currentParts.filter(p => !isRarityPart(p));
                    }
                    
                    // Check if part already exists (only if duplicates are not allowed)
                    if (!allowDuplicates) {
                        const exists = currentParts.some(p => {
                            if (p.type === 'simple' && partToAdd.type === 'simple') {
                                return p.value === partToAdd.value;
                            } else if (p.type === 'typed' && partToAdd.type === 'typed') {
                                return p.typeId === partToAdd.typeId && p.value === partToAdd.value;
                            }
                            return false;
                        });
                        
                        if (exists) {
                            alert('This part is already added!');
                            return false;
                        }
                    }
                    
                    // For enhancements, rarity should be the first {#} in the serial
                    if (isRarity && isEnhancementTypeId(currentTypeId)) {
                        // Add rarity at the beginning for enhancements
                        currentParts.unshift(partToAdd);
                    } else {
                        // Add other parts at the end (normal behavior)
                        currentParts.push(partToAdd);
                    }
                    return true; // Return true to indicate success
                } else {
                    alert('Failed to add part. Invalid part data.');
                    return false;
                }
            };
            
            // Update checkboxes based on item type - show part IDs that fulfill each requirement
            const updateCheckbox = (key, partIds) => {
                // Get current typeId for part lookups
                const currentTypeId = parseInt(document.getElementById('typeId').value) || 0;
                
                // Search within the guidelines content element
                // For daedalusAmmo and maliwanLicensedUnderbarrel, also check if the section is hidden and make sure we can find it
                let checkbox = contentEl.querySelector(`[data-checklist="${key}"]`);
                if (!checkbox && key === 'daedalusAmmo') {
                    // Try to find it even if the parent is hidden
                    const daedalusSection = document.getElementById('daedalusAmmoGuideline');
                    if (daedalusSection) {
                        checkbox = daedalusSection.querySelector('[data-checklist="daedalusAmmo"]');
                    }
                }
                if (!checkbox && key === 'maliwanLicensedUnderbarrel') {
                    // Try to find it even if the parent is hidden
                    const maliwanSection = document.getElementById('maliwanLicensedUnderbarrelGuideline');
                    if (maliwanSection) {
                        checkbox = maliwanSection.querySelector('[data-checklist="maliwanLicensedUnderbarrel"]');
                    }
                }
                // Legacy check for daedalusAmmo (keep for backwards compatibility)
                if (!checkbox && key === 'daedalusAmmo') {
                    // Try to find it even if the parent is hidden
                    const daedalusSection = document.getElementById('daedalusAmmoGuideline');
                    if (daedalusSection) {
                        checkbox = daedalusSection.querySelector(`[data-checklist="${key}"]`);
                    }
                }
                if (!checkbox) {
                    console.log('updateCheckbox: Checkbox not found for key =', key);
                    return;
                }
                
                // For manufacturer/level, always show as checked (empty array means no part needed but requirement fulfilled)
                const checked = (key === 'manufacturer' || key === 'level') ? true : (partIds.length > 0);
                console.log(`updateCheckbox: ${key} = ${checked}, partIds.length = ${partIds.length}, partIds =`, partIds);
                
                checkbox.style.backgroundColor = checked ? '#4caf50' : '#f5f5f5';
                checkbox.style.borderColor = checked ? '#4caf50' : '#ddd';
                checkbox.innerHTML = checked ? '✓' : '';
                checkbox.style.color = checked ? '#fff' : '#666'; // Dark text when unchecked, white when checked
                
                // Find the parent guideline-item container (the card-style container)
                const guidelineItem = checkbox.closest('.guideline-item') || checkbox.closest('div[style*="flex-direction: column"]');
                if (guidelineItem) {
                    // Remove existing part ID display and dropdown if any
                    const existingParts = guidelineItem.querySelector('.part-ids-display');
                    if (existingParts) {
                        existingParts.remove();
                    }
                    const existingDropdown = guidelineItem.querySelector('.guideline-part-dropdown');
                    if (existingDropdown) {
                        existingDropdown.remove();
                    }
                    
                    // Add part IDs display if there are parts (skip for manufacturer/level since they don't need parts)
                    if (checked && partIds.length > 0 && key !== 'manufacturer' && key !== 'level') {
                        const partsContainer = document.createElement('div');
                        partsContainer.className = 'part-ids-display';
                        // For skills, use column layout; for others, use wrap
                        const isSkillsCategory = key === 'skills';
                        partsContainer.style.cssText = `margin-top: 4px; padding-top: 6px; border-top: 1px solid #e0e0e0; font-size: ${isSkillsCategory ? '13px' : '11px'}; color: #4a5568; font-family: ${isSkillsCategory ? 'inherit' : '"Courier New", monospace'}; line-height: 1.6; word-break: break-word; display: flex; flex-direction: ${isSkillsCategory ? 'column' : 'row'}; flex-wrap: ${isSkillsCategory ? 'nowrap' : 'wrap'}; gap: ${isSkillsCategory ? '4px' : '6px'}; align-items: ${isSkillsCategory ? 'stretch' : 'center'};`;
                        
                        // Check if descriptive IDs is enabled
                        const descriptiveIdsCheckbox = document.getElementById('descriptiveIdsGuidelines');
                        const showDescriptiveIds = descriptiveIdsCheckbox ? descriptiveIdsCheckbox.checked : true; // Default to true
                        
                        // Create a remove function for a specific part
                        const removePartFromGuidelines = (partToRemove) => {
                            // Handle removing individual values from array parts
                            // If partToRemove is a typed/simple part but the actual part in currentParts is an array,
                            // we need to remove that value from the array instead
                            if ((partToRemove.type === 'typed' || partToRemove.type === 'simple') && partToRemove.value !== undefined) {
                                // Try to find an array part that contains this value
                                const arrayPartIndex = currentParts.findIndex(p => {
                                    if (p.type === 'array') {
                                        // Check if this array part contains the value we want to remove
                                        if (partToRemove.type === 'typed' && p.typeId === partToRemove.typeId) {
                                            return p.values && p.values.includes(partToRemove.value);
                                        } else if (partToRemove.type === 'simple') {
                                            // For simple parts, check if currentTypeId matches and array contains the value
                                            const currentTypeId = parseInt(document.getElementById('typeId').value);
                                            if (p.typeId === currentTypeId) {
                                                return p.values && p.values.includes(partToRemove.value);
                                            }
                                        }
                                    }
                                    return false;
                                });
                                
                                if (arrayPartIndex !== -1) {
                                    // Found an array part containing this value - remove the value from the array
                                    const arrayPart = currentParts[arrayPartIndex];
                                    const valueIndex = arrayPart.values.indexOf(partToRemove.value);
                                    if (valueIndex !== -1) {
                                        arrayPart.values.splice(valueIndex, 1);
                                        
                                        // If array is now empty, remove the entire array part
                                        // If array has only one value left, keep it as an array (user can remove that last value separately)
                                        if (arrayPart.values.length === 0) {
                                            // Remove the entire array part when it becomes empty
                                            currentParts.splice(arrayPartIndex, 1);
                                        }
                                        
                                        renderParts();
                                        updateGuidelinesChecklist();
                                        generateCode();
                                        return;
                                    }
                                }
                            }
                            
                            // Standard removal for non-array parts or full array removal
                            const index = currentParts.findIndex(p => {
                                if (p.type === 'simple' && partToRemove.type === 'simple') {
                                    return p.value === partToRemove.value;
                                } else if (p.type === 'typed' && partToRemove.type === 'typed') {
                                    return p.typeId === partToRemove.typeId && p.value === partToRemove.value;
                                } else if (p.type === 'array' && partToRemove.type === 'array') {
                                    return p.typeId === partToRemove.typeId && 
                                           JSON.stringify(p.values) === JSON.stringify(partToRemove.values);
                                }
                                return false;
                            });
                            
                            if (index !== -1) {
                                currentParts.splice(index, 1);
                                renderParts();
                                updateGuidelinesChecklist();
                                generateCode();
                            }
                        };
                        
                        // Special handling for skills: Group by skill name and show points
                        if (key === 'skills') {
                            // Count occurrences from currentParts directly (handles stacked parts like {27}{27}{27})
                            // This is more accurate than using partIds which only contains unique IDs
                            const partIdCounts = new Map();
                            
                            // Filter currentParts to only skill parts (typeId 254 or 255, or simple parts that are skills)
                            currentParts.forEach((part) => {
                                let typeId = null;
                                let partId = null;
                                
                                if (part.type === 'simple') {
                                    typeId = currentTypeId;
                                    partId = part.value;
                                } else if (part.type === 'typed') {
                                    typeId = part.typeId;
                                    partId = part.value;
                                }
                                
                                if (typeId !== null && partId !== null) {
                                    const isClassMod = currentTypeId >= 254 && currentTypeId <= 259;
                                    
                                    if (part.type === 'simple' && isClassMod) {
                                        // Simple parts like {10} come from the local manufacturer (class mod's own typeId)
                                        // Use ONLY the class mod's typeId, don't try 254/255
                                        const partKey = `${currentTypeId}:${partId}`;
                                        // Verify it's actually a skill by checking partInfo
                                        let partInfo = partsMap.get(partKey) || partsMap.get(partId) || partsMap.get(parseInt(partId));
                                        
                                        if (partInfo) {
                                            const partType = String(partInfo.partType || '').toLowerCase();
                                            const hasSkillName = partInfo.skillName && String(partInfo.skillName).trim() !== '';
                                            const isSkill = partType === 'skill' || hasSkillName;
                                            
                                            if (isSkill) {
                                                partIdCounts.set(partKey, (partIdCounts.get(partKey) || 0) + 1);
                                            }
                                        } else {
                                            // If partInfo not found, assume it's a skill for class mods
                                            partIdCounts.set(partKey, (partIdCounts.get(partKey) || 0) + 1);
                                        }
                                    } else if (part.type === 'typed' && (typeId === 254 || typeId === 255)) {
                                        // Typed parts like {254:10} or {255:10} are skills from other classes
                                        // Use the explicit typeId from the part
                                        const partKey = `${typeId}:${partId}`;
                                        partIdCounts.set(partKey, (partIdCounts.get(partKey) || 0) + 1);
                                    } else if (part.type === 'simple') {
                                        // For other simple parts (non-class mods), check if it's a skill
                                        let partInfo = partsMap.get(partId) || partsMap.get(parseInt(partId)) || 
                                                      partsMap.get(`${typeId}:${partId}`);
                                        
                                        if (partInfo) {
                                            const partType = String(partInfo.partType || '').toLowerCase();
                                            const hasSkillName = partInfo.skillName && String(partInfo.skillName).trim() !== '';
                                            const isSkill = partType === 'skill' || hasSkillName;
                                            
                                            if (isSkill) {
                                                const skillTypeId = partInfo.typeId || typeId;
                                                const partKey = `${skillTypeId}:${partId}`;
                                                partIdCounts.set(partKey, (partIdCounts.get(partKey) || 0) + 1);
                                            }
                                        }
                                    }
                                }
                            });
                            
                            // Debug: Log all partIds for skills
                            console.log('[SKILLS GROUPING] Processing', currentParts.length, 'total parts, found', partIdCounts.size, 'unique skill parts from currentParts');
                            console.log('[SKILLS GROUPING] Part ID counts:', Array.from(partIdCounts.entries()).map(([k, v]) => `${k}: ${v}x`));
                            
                            // Also process unique skill parts from partIds to ensure we don't miss any skills
                            // This handles cases where skills might not be in currentParts but are in the checklist
                            // Also use partIds order to establish stable skill order
                            const uniquePartIds = new Set();
                            const partIdsSkillOrder = []; // Track skill order from partIds for stable ordering
                            partIds.forEach((id) => {
                                const cleanId = id.replace(/\s*([{}:,])\s*/g, '$1').trim();
                                
                                // Parse the part ID
                                let typeId = null;
                                let partId = null;
                                
                                if (cleanId.startsWith('{') && cleanId.endsWith('}')) {
                                    const inner = cleanId.slice(1, -1);
                                    if (inner.includes(':')) {
                                        const parts = inner.split(':');
                                        typeId = parseInt(parts[0]);
                                        partId = parseInt(parts[1]);
                                    } else if (!isNaN(parseInt(inner))) {
                                        partId = parseInt(inner);
                                        typeId = currentTypeId;
                                    }
                                }
                                
                                if (typeId !== null && partId !== null) {
                                    const isClassMod = currentTypeId >= 254 && currentTypeId <= 259;
                                    
                                    // Determine the correct typeId to use
                                    let skillTypeId = typeId;
                                    
                                    if (cleanId.includes(':')) {
                                        // Typed part like {254:10} - use the explicit typeId
                                        skillTypeId = typeId;
                                    } else if (isClassMod) {
                                        // Simple part like {10} in a class mod - use local manufacturer (class mod's typeId)
                                        skillTypeId = currentTypeId;
                                    }
                                    // For non-class mod simple parts, use the inferred typeId
                                    
                                    const partKey = `${skillTypeId}:${partId}`;
                                    uniquePartIds.add(partKey);
                                    
                                    // Only add if not already in partIdCounts (to preserve counts from currentParts)
                                    // But verify it's actually a skill part
                                    if (!partIdCounts.has(partKey)) {
                                        // Verify it's a skill by checking partInfo
                                        const partInfo = partsMap.get(partKey) || partsMap.get(partId) || partsMap.get(parseInt(partId));
                                        if (partInfo) {
                                            const partType = String(partInfo.partType || '').toLowerCase();
                                            const hasSkillName = partInfo.skillName && String(partInfo.skillName).trim() !== '';
                                            const isSkill = partType === 'skill' || hasSkillName || (skillTypeId >= 254 && skillTypeId <= 259);
                                            if (isSkill) {
                                                // Only add with count 1 if it's not already counted from currentParts
                                                // This ensures we don't miss skills that only appear in partIds
                                                partIdCounts.set(partKey, 1);
                                                
                                                // Track skill order from partIds for stable ordering
                                                let partSkillName = partInfo.skillName || partInfo.name || '';
                                                partSkillName = partSkillName.replace(/\s*\(Tier\s+\d+\)\s*$/i, '').trim();
                                                if (partSkillName && !partIdsSkillOrder.includes(partSkillName)) {
                                                    partIdsSkillOrder.push(partSkillName);
                                                }
                                            }
                                        } else if (skillTypeId >= 254 && skillTypeId <= 259) {
                                            // Assume it's a skill if typeId is 254-259
                                            partIdCounts.set(partKey, 1);
                                        }
                                    }
                                }
                            });
                            
                            console.log('[SKILLS GROUPING] Also found', uniquePartIds.size, 'unique skill parts from partIds');
                            
                            // Group skills by name and collect tier information
                            const skillGroups = new Map();
                            // Track the order skills are first encountered - use a Set to avoid duplicates
                            const skillOrderSet = new Set();
                            const skillOrder = [];
                            
                            // Process each unique part ID and count occurrences
                            partIdCounts.forEach((count, partKey) => {
                                const [typeIdStr, partIdStr] = partKey.split(':');
                                const typeId = parseInt(typeIdStr);
                                const partId = parseInt(partIdStr);
                                
                                // Try multiple lookup strategies for skill parts
                                let partInfo = partsMap.get(partKey);
                                if (!partInfo) {
                                    // Try with currentTypeId if typeId was inferred
                                    if (typeId === currentTypeId) {
                                        partInfo = partsMap.get(partId) || partsMap.get(parseInt(partId));
                                    }
                                    // For class mod skills, try both 254 and 255
                                    if (!partInfo && (currentTypeId === 254 || currentTypeId === 255)) {
                                        partInfo = partsMap.get(`254:${partId}`) || partsMap.get(`255:${partId}`);
                                    }
                                }
                                
                                if (partInfo) {
                                    // Extract skill name from part name (remove " (Tier X)" suffix)
                                    let skillName = partInfo.skillName || partInfo.name || '';
                                    skillName = skillName.replace(/\s*\(Tier\s+\d+\)\s*$/i, '').trim();
                                    
                                    if (skillName) {
                                        if (!skillGroups.has(skillName)) {
                                            skillGroups.set(skillName, {
                                                name: skillName,
                                                tiers: [],
                                                typeId: typeId,
                                                // Store a map of partId -> count for this skill
                                                partCounts: new Map()
                                            });
                                            // Track the order this skill was first encountered (avoid duplicates)
                                            if (!skillOrderSet.has(skillName)) {
                                                skillOrderSet.add(skillName);
                                                skillOrder.push(skillName);
                                            }
                                        }
                                        
                                        const group = skillGroups.get(skillName);
                                        
                                        // Extract tier number from name
                                        const tierMatch = (partInfo.name || '').match(/\(Tier\s+(\d+)\)/i);
                                        const tierNum = tierMatch ? parseInt(tierMatch[1]) : 1;
                                        
                                        // Store the count for this part ID with typeId info
                                        // Key format: "typeId:partId" to handle different typeIds
                                        const partCountKey = `${typeId}:${partId}`;
                                        if (!group.partCounts.has(partCountKey)) {
                                            group.partCounts.set(partCountKey, { count: count, typeId: typeId, partId: partId });
                                        } else {
                                            // Update count if this key already exists
                                            const existing = group.partCounts.get(partCountKey);
                                            existing.count = Math.max(existing.count, count);
                                        }
                                        
                                        // If this part ID appears multiple times (stacked), it represents multiple points
                                        // We need to find the skill group info to get all tier part IDs
                                        if (count > 1) {
                                            // This part ID appears multiple times - find the skill group to get all tier parts
                                            const skillGroupPart = Array.from(partsMap.values()).find(p => 
                                                (p.skillName === skillName || (p.name && p.name.replace(/\s*\(Tier\s+\d+\)\s*$/i, '').trim() === skillName)) &&
                                                p.skillIds && typeof p.skillIds === 'object' &&
                                                (p.typeId === typeId || !p.typeId || p.typeId === 254 || p.typeId === 255)
                                            );
                                            
                                            if (skillGroupPart && skillGroupPart.skillIds) {
                                                // We have the skill group info - add all tiers up to the count
                                                // If Tier 1 appears N times, that means N points, so add Tier 1 through Tier N
                                                for (let tier = 1; tier <= Math.min(count, 5); tier++) {
                                                    const tierKey = `tier_${tier}`;
                                                    const tierData = skillGroupPart.skillIds[tierKey];
                                                    
                                                    if (tierData && tierData.id) {
                                                        // Extract numeric part ID from tier ID
                                                        let tierPartId = null;
                                                        const tierIdStr = String(tierData.id || '');
                                                        
                                                        if (tierIdStr.includes(':')) {
                                                            const parts = tierIdStr.split(':');
                                                            if (parts.length >= 2) {
                                                                tierPartId = parseInt(parts[parts.length - 1]);
                                                            }
                                                        } else {
                                                            tierPartId = parseInt(tierIdStr);
                                                        }
                                                        
                                                        if (!isNaN(tierPartId) && tierPartId !== 0) {
                                                            // Check if this tier is already in the tiers array
                                                            const existingTier = group.tiers.find(t => t.tier === tier);
                                                            if (!existingTier) {
                                                                // Get part info for this tier
                                                                const tierFullId = `${typeId}:${tierPartId}`;
                                                                const tierPartInfo = partsMap.get(tierFullId) || partsMap.get(tierPartId) || partsMap.get(parseInt(tierPartId));
                                                                
                                                                group.tiers.push({
                                                                    tier: tier,
                                                                    partId: tierPartId,
                                                                    typeId: typeId,
                                                                    fullId: tierFullId,
                                                                    partInfo: tierPartInfo || partInfo // Fallback to original partInfo if tier info not found
                                                                });
                                                            }
                                                        }
                                                    }
                                                }
                                            } else {
                                                // Fallback: if we can't find skill group info, add the tier based on count
                                                // This handles edge cases where skill group info might not be available
                                                for (let i = 1; i <= Math.min(count, 5); i++) {
                                                    const existingTier = group.tiers.find(t => t.tier === i && t.partId === partId);
                                                    if (!existingTier) {
                                                        group.tiers.push({
                                                            tier: i,
                                                            partId: partId,
                                                            typeId: typeId,
                                                            fullId: `${typeId}:${partId}`,
                                                            partInfo: partInfo
                                                        });
                                                    }
                                                }
                                            }
                                        } else {
                                            // Single occurrence - add normally
                                            const existingTier = group.tiers.find(t => t.tier === tierNum && t.partId === partId);
                                            if (!existingTier) {
                                                group.tiers.push({
                                                    tier: tierNum,
                                                    partId: partId,
                                                    typeId: typeId,
                                                    fullId: `${typeId}:${partId}`,
                                                    partInfo: partInfo
                                                });
                                            }
                                        }
                                    } else {
                                        console.warn('[SKILLS GROUPING] Part found but no skill name:', partKey, partInfo);
                                    }
                                } else {
                                    console.warn('[SKILLS GROUPING] Part info not found for:', partKey);
                                }
                            });
                            
                            // Debug: Log grouped skills
                            console.log('[SKILLS GROUPING] Grouped into', skillGroups.size, 'skills:');
                            skillGroups.forEach((group, skillName) => {
                                console.log(`  - ${skillName}: ${group.tiers.length} points (tiers: ${group.tiers.map(t => t.tier).join(', ')})`);
                            });
                            
                            // Sort tiers within each skill group and calculate correct point count
                            skillGroups.forEach(group => {
                                group.tiers.sort((a, b) => a.tier - b.tier);
                                
                                // Calculate points: max of (max tier number, max count of any stacked part)
                                const maxTier = group.tiers.length > 0 ? Math.max(...group.tiers.map(t => t.tier)) : 0;
                                let maxCount = 0;
                                group.partCounts.forEach((data) => {
                                    const count = typeof data === 'object' ? data.count : data;
                                    maxCount = Math.max(maxCount, count);
                                });
                                group.calculatedPoints = Math.max(maxTier, maxCount, group.tiers.length);
                            });
                            
                            // Use alphabetical order for skills to ensure stable, consistent ordering
                            // This prevents jarring reordering when points are adjusted
                            const allSkillNames = Array.from(skillGroups.keys()).sort((a, b) => {
                                return a.localeCompare(b, undefined, { sensitivity: 'base' });
                            });
                            
                            // Display grouped skills with point controls in stable alphabetical order
                            allSkillNames.forEach(skillName => {
                                const group = skillGroups.get(skillName);
                                if (!group) return; // Skip if group was removed
                                
                                // Use calculated points, which accounts for stacked parts
                                const points = group.calculatedPoints || group.tiers.length;
                                
                                // Create skill display element
                                const skillElement = document.createElement('div');
                                skillElement.style.cssText = 'display: flex; align-items: center; gap: 8px; padding: 6px 10px; background: #f8f9fa; border-radius: 4px; border: 1px solid #e0e0e0; margin-bottom: 4px;';
                                
                                // Skill name and points
                                const skillText = document.createElement('span');
                                skillText.style.cssText = 'flex: 1; font-weight: 500; color: #333;';
                                skillText.textContent = `${skillName} (${points} ${points === 1 ? 'point' : 'points'})`;
                                skillElement.appendChild(skillText);
                                
                                // Points controls
                                const controlsContainer = document.createElement('div');
                                controlsContainer.style.cssText = 'display: flex; align-items: center; gap: 4px;';
                                
                                // Decrease button (-)
                                const decreaseBtn = document.createElement('button');
                                decreaseBtn.innerHTML = '−';
                                decreaseBtn.disabled = points <= 0;
                                decreaseBtn.style.cssText = `width: 28px; height: 28px; border: 1px solid ${points <= 0 ? '#ccc' : '#4fc3f7'}; border-radius: 4px; background: ${points <= 0 ? '#f5f5f5' : '#fff'}; color: ${points <= 0 ? '#999' : '#4fc3f7'}; cursor: ${points <= 0 ? 'not-allowed' : 'pointer'}; font-size: 18px; line-height: 1; display: flex; align-items: center; justify-content: center; font-weight: bold; transition: all 0.2s;`;
                                decreaseBtn.title = 'Remove 1 point';
                                decreaseBtn.onclick = (e) => {
                                    e.stopPropagation();
                                    if (points > 0) {
                                        // Check if this skill has stacked parts (same partId appears multiple times)
                                        let hasStackedParts = false;
                                        group.partCounts.forEach((data) => {
                                            const count = typeof data === 'object' ? data.count : data;
                                            if (count > 1) {
                                                hasStackedParts = true;
                                            }
                                        });
                                        
                                        if (hasStackedParts) {
                                            // For stacked parts, find the partId with the highest count and remove one instance
                                            let maxCount = 0;
                                            let partToRemoveData = null;
                                            
                                            group.partCounts.forEach((data, key) => {
                                                // data is now an object with { count, typeId, partId }
                                                const count = typeof data === 'object' ? data.count : data;
                                                if (count > maxCount) {
                                                    maxCount = count;
                                                    if (typeof data === 'object') {
                                                        partToRemoveData = data;
                                                    } else {
                                                        // Fallback for old format
                                                        const [typeIdStr, partIdStr] = key.split(':');
                                                        partToRemoveData = {
                                                            typeId: parseInt(typeIdStr) || group.typeId,
                                                            partId: parseInt(partIdStr) || parseInt(key)
                                                        };
                                                    }
                                                }
                                            });
                                            
                                            if (partToRemoveData) {
                                                // Determine if it's a simple part (local manufacturer) or typed part (other class)
                                                const isLocalManufacturer = partToRemoveData.typeId === currentTypeId;
                                                const partToRemove = isLocalManufacturer
                                                    ? { type: 'simple', value: partToRemoveData.partId }
                                                    : { type: 'typed', typeId: partToRemoveData.typeId, value: partToRemoveData.partId };
                                                
                                                // Find and remove ONE instance of the matching part from currentParts
                                                const index = currentParts.findIndex(p => {
                                                    if (p.type === 'simple' && partToRemove.type === 'simple') {
                                                        return p.value === partToRemove.value;
                                                    } else if (p.type === 'typed' && partToRemove.type === 'typed') {
                                                        return p.typeId === partToRemove.typeId && p.value === partToRemove.value;
                                                    }
                                                    return false;
                                                });
                                                
                                                if (index !== -1) {
                                                    currentParts.splice(index, 1);
                                                    renderParts();
                                                    updateGuidelinesChecklist();
                                                    generateCode();
                                                }
                                            }
                                        } else {
                                            // For non-stacked parts (different tier parts), find the highest tier that actually exists in currentParts
                                            // We need to check currentParts directly to get the actual highest tier
                                            let highestTierFound = null;
                                            let highestTierNum = 0;
                                            
                                            // Look through currentParts to find all parts belonging to this skill
                                            currentParts.forEach(part => {
                                                let partTypeId = null;
                                                let partId = null;
                                                
                                                if (part.type === 'simple') {
                                                    partTypeId = currentTypeId;
                                                    partId = part.value;
                                                } else if (part.type === 'typed') {
                                                    partTypeId = part.typeId;
                                                    partId = part.value;
                                                }
                                                
                                                if (partTypeId !== null && partId !== null) {
                                                    // Check if this part belongs to this skill
                                                    const partKey = `${partTypeId}:${partId}`;
                                                    let partInfo = partsMap.get(partKey) || partsMap.get(partId) || partsMap.get(parseInt(partId));
                                                    
                                                    // For class mods, also try 254/255 if not found
                                                    if (!partInfo && (currentTypeId >= 254 && currentTypeId <= 259)) {
                                                        partInfo = partsMap.get(`254:${partId}`) || partsMap.get(`255:${partId}`);
                                                    }
                                                    
                                                    if (partInfo) {
                                                        let partSkillName = partInfo.skillName || partInfo.name || '';
                                                        partSkillName = partSkillName.replace(/\s*\(Tier\s+\d+\)\s*$/i, '').trim();
                                                        
                                                        if (partSkillName === skillName) {
                                                            // Extract tier number
                                                            const tierMatch = (partInfo.name || '').match(/\(Tier\s+(\d+)\)/i);
                                                            const tierNum = tierMatch ? parseInt(tierMatch[1]) : 1;
                                                            
                                                            if (tierNum > highestTierNum) {
                                                                highestTierNum = tierNum;
                                                                highestTierFound = {
                                                                    tier: tierNum,
                                                                    partId: partId,
                                                                    typeId: partTypeId,
                                                                    part: part
                                                                };
                                                            }
                                                        }
                                                    }
                                                }
                                            });
                                            
                                            if (highestTierFound) {
                                                // Remove the highest tier part directly
                                                const index = currentParts.indexOf(highestTierFound.part);
                                                if (index !== -1) {
                                                    currentParts.splice(index, 1);
                                                    renderParts();
                                                    updateGuidelinesChecklist();
                                                    generateCode();
                                                }
                                            }
                                        }
                                    }
                                };
                                decreaseBtn.onmouseover = function() {
                                    if (!this.disabled) {
                                        this.style.background = '#e3f2fd';
                                        this.style.borderColor = '#29b6f6';
                                    }
                                };
                                decreaseBtn.onmouseout = function() {
                                    if (!this.disabled) {
                                        this.style.background = '#fff';
                                        this.style.borderColor = '#4fc3f7';
                                    }
                                };
                                controlsContainer.appendChild(decreaseBtn);
                                
                                // Increase button (+)
                                const increaseBtn = document.createElement('button');
                                increaseBtn.innerHTML = '+';
                                increaseBtn.disabled = points >= 5;
                                increaseBtn.style.cssText = `width: 28px; height: 28px; border: 1px solid ${points >= 5 ? '#ccc' : '#4fc3f7'}; border-radius: 4px; background: ${points >= 5 ? '#f5f5f5' : '#fff'}; color: ${points >= 5 ? '#999' : '#4fc3f7'}; cursor: ${points >= 5 ? 'not-allowed' : 'pointer'}; font-size: 18px; line-height: 1; display: flex; align-items: center; justify-content: center; font-weight: bold; transition: all 0.2s;`;
                                increaseBtn.title = 'Add 1 point';
                                increaseBtn.onclick = (e) => {
                                    e.stopPropagation();
                                    if (points < 5) {
                                        // Find the next tier to add
                                        const nextTierNum = points + 1;
                                        
                                        // Look up the skill group part info to get tier data
                                        // First try to find in partsByTypeId for the current typeId
                                        let skillGroupPart = null;
                                        if (partsByTypeId.has(group.typeId)) {
                                            const typeParts = partsByTypeId.get(group.typeId);
                                            skillGroupPart = typeParts.find(p => 
                                                p.skillName === skillName && p.skillIds && typeof p.skillIds === 'object'
                                            );
                                        }
                                        
                                        // Fallback: search all partsMap values
                                        if (!skillGroupPart) {
                                            skillGroupPart = Array.from(partsMap.values()).find(p => 
                                                p.skillName === skillName && p.skillIds && typeof p.skillIds === 'object' && 
                                                (p.typeId === group.typeId || !p.typeId)
                                            );
                                        }
                                        
                                        if (skillGroupPart && skillGroupPart.skillIds) {
                                            const tierKey = `tier_${nextTierNum}`;
                                            const tierData = skillGroupPart.skillIds[tierKey];
                                            
                                            if (tierData && tierData.id) {
                                                // Extract numeric part ID and typeId from tier ID
                                                let tierPartId = null;
                                                let tierTypeId = null;
                                                const tierIdStr = String(tierData.id || '');
                                                
                                                if (tierIdStr.includes(':')) {
                                                    const parts = tierIdStr.split(':');
                                                    if (parts.length >= 2) {
                                                        tierTypeId = parseInt(parts[0]);
                                                        tierPartId = parseInt(parts[parts.length - 1]);
                                                    }
                                                } else {
                                                    tierPartId = parseInt(tierIdStr);
                                                    // Use the group's typeId (local manufacturer for simple parts, or explicit for typed)
                                                    tierTypeId = group.typeId;
                                                }
                                                
                                                if (!isNaN(tierPartId) && tierPartId !== 0) {
                                                    // Determine if this is a local manufacturer skill (simple) or other class skill (typed)
                                                    // If the group's typeId matches currentTypeId, it's a local manufacturer skill (simple part)
                                                    // Otherwise, it's from another class (typed part with explicit typeId)
                                                    const isLocalManufacturer = (tierTypeId || group.typeId) === currentTypeId;
                                                    
                                                    const partToAdd = isLocalManufacturer
                                                        ? { type: 'simple', value: tierPartId }
                                                        : { type: 'typed', typeId: tierTypeId || group.typeId, value: tierPartId };
                                                    
                                                    // Check if part already exists
                                                    const exists = currentParts.some(p => {
                                                        if (p.type === 'simple' && partToAdd.type === 'simple') {
                                                            return p.value === partToAdd.value;
                                                        } else if (p.type === 'typed' && partToAdd.type === 'typed') {
                                                            return p.typeId === partToAdd.typeId && p.value === partToAdd.value;
                                                        }
                                                        return false;
                                                    });
                                                    
                                                    if (!exists) {
                                                        currentParts.push(partToAdd);
                                                        renderParts();
                                                        updateGuidelinesChecklist();
                                                        generateCode();
                                                    }
                                                }
                                            }
                                        }
                                    }
                                };
                                increaseBtn.onmouseover = function() {
                                    if (!this.disabled) {
                                        this.style.background = '#e3f2fd';
                                        this.style.borderColor = '#29b6f6';
                                    }
                                };
                                increaseBtn.onmouseout = function() {
                                    if (!this.disabled) {
                                        this.style.background = '#fff';
                                        this.style.borderColor = '#4fc3f7';
                                    }
                                };
                                controlsContainer.appendChild(increaseBtn);
                                
                                skillElement.appendChild(controlsContainer);
                                partsContainer.appendChild(skillElement);
                            });
                        } else {
                            // Normal part display (non-skills)
                            partIds.forEach((id, idx) => {
                                // Clean up the part ID format
                                const cleanId = id.replace(/\s*([{}:,])\s*/g, '$1').trim();
                                
                                // Try to find the part info to get the name
                                let partName = '';
                                let partToRemove = null;
                                
                                // Parse the part ID to extract typeId and partId
                                let typeId = null;
                                let partId = null;
                                
                                if (cleanId.startsWith('{') && cleanId.endsWith('}')) {
                                    const inner = cleanId.slice(1, -1);
                                    if (inner.includes(':')) {
                                        const parts = inner.split(':');
                                        typeId = parseInt(parts[0]);
                                        if (parts[1].includes('[')) {
                                            // Array part
                                            const arrayMatch = parts[1].match(/\[(.+?)\]/);
                                            if (arrayMatch) {
                                                const values = arrayMatch[1].split(/\s+/).map(v => parseInt(v)).filter(v => !isNaN(v));
                                                partToRemove = { type: 'array', typeId: typeId, values: values };
                                            }
                                            const beforeBracket = parts[1].split('[')[0];
                                            partId = parseInt(beforeBracket);
                                        } else {
                                            partId = parseInt(parts[1]);
                                            partToRemove = { type: 'typed', typeId: typeId, value: partId };
                                        }
                                    } else if (!isNaN(parseInt(inner))) {
                                        partId = parseInt(inner);
                                        typeId = currentTypeId;
                                        partToRemove = { type: 'simple', value: partId };
                                    }
                                }
                                
                                // Look up part info for display
                                let partInfo = null;
                                
                                if (typeId !== null && partId !== null) {
                                    const fullId = `${typeId}:${partId}`;
                                    partInfo = partsMap.get(fullId) || partsMap.get(partId) || partsMap.get(parseInt(partId));
                                } else if (partToRemove && partToRemove.type === 'array') {
                                    // For array parts, try to find partInfo by typeId
                                    if (partsByTypeId.has(partToRemove.typeId)) {
                                        const typeParts = partsByTypeId.get(partToRemove.typeId);
                                        // Try to find a matching part (this is approximate for array parts)
                                        partInfo = typeParts[0] || null;
                                    }
                                }
                                
                                if (partInfo && partInfo.name) {
                                    partName = partInfo.name;
                                }
                                
                                const fullIdStr = (typeId !== null && partId !== null) ? `${typeId}:${partId}` : '';
                                const partKeyFromSpawn = (partInfo && partInfo.spawnCode) ? String(partInfo.spawnCode).split('.').pop().toLowerCase() : '';
                                const isNewPart = fullIdStr && newSerialIdsGuidelines.has(fullIdStr) || (partKeyFromSpawn && newPartKeysGuidelines.has(partKeyFromSpawn));
                                
                                // Create part display element
                                const partElement = document.createElement('span');
                                partElement.style.cssText = 'display: inline-flex; align-items: center; gap: 4px; padding: 4px 8px; background: #f8f9fa; border-radius: 4px; border: 1px solid #e0e0e0; transition: all 0.2s;';
                                partElement.onmouseover = function() {
                                    this.style.background = '#f0f0f0';
                                    this.style.borderColor = '#ccc';
                                };
                                partElement.onmouseout = function() {
                                    this.style.background = '#f8f9fa';
                                    this.style.borderColor = '#e0e0e0';
                                };
                                
                                // Part ID text (prepend NEW! badge for new parts)
                                const partText = document.createElement('span');
                                const displayStr = showDescriptiveIds && partName ? `${cleanId} - ${partName}` : cleanId;
                                if (isNewPart) {
                                    partText.innerHTML = '<span style="color: #FF8C42; font-weight: 700;">NEW!</span> ' + displayStr;
                                } else {
                                    partText.textContent = displayStr;
                                }
                                partElement.appendChild(partText);
                                
                                // Remove button (X)
                                if (partToRemove) {
                                    const removeBtn = document.createElement('button');
                                    removeBtn.innerHTML = '✕';
                                    removeBtn.style.cssText = 'background: transparent; color: #999; border: 1px solid #ddd; border-radius: 3px; width: 20px; height: 20px; font-size: 12px; line-height: 1; cursor: pointer; padding: 0; display: flex; align-items: center; justify-content: center; flex-shrink: 0; transition: all 0.2s; margin-left: 4px;';
                                    removeBtn.title = 'Remove this part';
                                    removeBtn.onmouseover = function() {
                                        this.style.background = '#fee';
                                        this.style.borderColor = '#faa';
                                        this.style.color = '#c33';
                                    };
                                    removeBtn.onmouseout = function() {
                                        this.style.background = 'transparent';
                                        this.style.borderColor = '#ddd';
                                        this.style.color = '#999';
                                    };
                                    removeBtn.onclick = (e) => {
                                        e.stopPropagation();
                                        removePartFromGuidelines(partToRemove);
                                    };
                                    partElement.appendChild(removeBtn);
                                }
                                
                                partsContainer.appendChild(partElement);
                            });
                        }
                        
                        guidelineItem.appendChild(partsContainer);
                        console.log(`updateCheckbox: Added part IDs display for ${key} with remove buttons`);
                    }
                    
                    // Add dropdown for adding parts (skip for manufacturer/level)
                    // ALWAYS add dropdown for each guideline item (even if no parts available yet)
                    if (key !== 'manufacturer' && key !== 'level') {
                        // Debug logging for new 243 categories
                        if (key === 'elementalResistances243' || key === 'elementalImmunities243' || key === 'elementalSplats243' || key === 'elementalNovas243' || key === 'size243') {
                            console.log(`[DEBUG ${key} createDropdown] Creating dropdown for category: ${key}`);
                        }
                        
                        const dropdownContainer = document.createElement('div');
                        dropdownContainer.className = 'guideline-part-dropdown';
                        dropdownContainer.setAttribute('data-category', key);
                        dropdownContainer.style.cssText = 'margin-top: 8px; padding-top: 8px; border-top: 1px solid #e0e0e0;';
                        
                        // Create container for dropdown (on its own line) and quantity/add controls (on next line)
                        const controlsContainer = document.createElement('div');
                        controlsContainer.style.cssText = 'display: flex; flex-direction: column; gap: 8px;';
                        
                        // Multi-select container
                        const multiSelectContainer = document.createElement('div');
                        multiSelectContainer.className = 'multi-select-container';
                        multiSelectContainer.setAttribute('data-category', key);
                        multiSelectContainer.id = `multiselect-${key}`;
                        
                        // Multi-select button (replaces select)
                        const multiSelectButton = document.createElement('button');
                        multiSelectButton.type = 'button';
                        multiSelectButton.className = 'multi-select-button';
                        multiSelectButton.textContent = 'Select a part to add...';
                        multiSelectButton.setAttribute('data-category', key);
                        
                        // Dropdown panel
                        const dropdownPanel = document.createElement('div');
                        dropdownPanel.className = 'multi-select-dropdown';
                        dropdownPanel.setAttribute('data-category', key);
                        
                        // Chips container for selected items
                        const chipsContainer = document.createElement('div');
                        chipsContainer.className = 'selected-chips';
                        chipsContainer.setAttribute('data-category', key);
                        
                        // Store selected items (array of part data objects)
                        const selectedItems = [];
                        
                        // Container for quantity and add button (on second line)
                        const quantityButtonContainer = document.createElement('div');
                        quantityButtonContainer.style.cssText = 'display: flex; gap: 8px; align-items: center;';
                        
                        // Quantity input (or Points input for skills)
                        const isSkillsCategory = key === 'skills';
                        const quantityInput = document.createElement('input');
                        quantityInput.type = 'number';
                        if (isSkillsCategory) {
                            quantityInput.min = '1';
                            quantityInput.max = '5'; // Will be updated dynamically based on selected skill limiters
                            quantityInput.value = '1';
                            quantityInput.placeholder = 'Points';
                            quantityInput.title = 'Select number of skill points (1-5)';
                        } else {
                            quantityInput.min = '1';
                            quantityInput.max = '100';
                            quantityInput.value = '1';
                            quantityInput.placeholder = 'Qty';
                        }
                        quantityInput.id = `quantity-${key}`;
                        quantityInput.style.cssText = 'width: 60px; padding: 6px; border: 1px solid rgba(79, 195, 247, 0.3); border-radius: 4px; font-size: 12px; background: rgba(30, 30, 46, 0.8); color: #b0d4fa; text-align: center;';
                        quantityInput.setAttribute('data-category', key);
                        
                        // Add button
                        const addButton = document.createElement('button');
                        addButton.textContent = 'Add';
                        addButton.id = `add-btn-${key}`;
                        addButton.style.cssText = 'padding: 6px 16px; border: 1px solid #4fc3f7; border-radius: 4px; font-size: 12px; background: #4fc3f7; color: #fff; cursor: pointer; font-weight: 500; transition: all 0.2s;';
                        addButton.setAttribute('data-category', key);
                        addButton.onmouseover = function() {
                            this.style.background = '#29b6f6';
                            this.style.borderColor = '#29b6f7';
                        };
                        addButton.onmouseout = function() {
                            this.style.background = '#4fc3f7';
                            this.style.borderColor = '#4fc3f7';
                        };
                        
                        // Function to update button text based on selected count
                        const updateButtonText = () => {
                            const count = selectedItems.length;
                            if (count === 0) {
                                addButton.textContent = 'Add';
                                addButton.disabled = true;
                                addButton.style.opacity = '0.5';
                                addButton.style.cursor = 'not-allowed';
                            } else {
                                addButton.textContent = `Add Selected (${count})`;
                                addButton.disabled = false;
                                addButton.style.opacity = '1';
                                addButton.style.cursor = 'pointer';
                            }
                        };
                        
                        // Function to update chips display
                        const updateChips = () => {
                            chipsContainer.innerHTML = '';
                            selectedItems.forEach((item, index) => {
                                const chip = document.createElement('div');
                                chip.className = 'selected-chip';
                                chip.style.color = item.rarityColor || '#b0d4fa';
                                
                                const chipText = document.createElement('span');
                                chipText.textContent = item.displayText || item.name || 'Unknown';
                                chip.appendChild(chipText);
                                
                                const chipRemove = document.createElement('span');
                                chipRemove.className = 'selected-chip-remove';
                                chipRemove.textContent = '×';
                                chipRemove.onclick = (e) => {
                                    e.stopPropagation();
                                    selectedItems.splice(index, 1);
                                    updateChips();
                                    updateButtonText();
                                    // Uncheck the checkbox in the dropdown
                                    const checkbox = dropdownPanel.querySelector(`input[data-part-value="${item.value}"]`);
                                    if (checkbox) {
                                        checkbox.checked = false;
                                    }
                                    if (isSkillsCategory) {
                                        updateQuantityInputTitle();
                                    }
                                    updateSelectAllState();
                                };
                                chip.appendChild(chipRemove);
                                
                                chipsContainer.appendChild(chip);
                            });
                        };
                        
                        // Function to update dropdown button text
                        const updateMultiSelectButton = () => {
                            const count = selectedItems.length;
                            if (count === 0) {
                                multiSelectButton.textContent = 'Select a part to add...';
                            } else {
                                multiSelectButton.textContent = `${count} part${count !== 1 ? 's' : ''} selected`;
                            }
                        };
                        
                        // Function to update "Select All" checkbox state (will be assigned in updateDropdown)
                        let updateSelectAllState = () => {};
                        
                        // Function to update dropdown based on master unlock state
                        const updateDropdown = () => {
                            const masterUnlock = document.getElementById('masterUnlockGuidelines');
                            const isUnlocked = masterUnlock ? masterUnlock.checked : false;
                            
                            // Debug logging for baseBody247
                            if (key === 'baseBody247') {
                                console.log(`[DEBUG baseBody247 updateDropdown] key=${key}, isUnlocked=${isUnlocked}, currentTypeId=${document.getElementById('typeId').value}`);
                            }
                            
                            // Debug logging for new 243 categories
                            if (key === 'elementalResistances243' || key === 'elementalImmunities243' || key === 'elementalSplats243' || key === 'elementalNovas243' || key === 'size243') {
                                console.log(`[DEBUG ${key} updateDropdown] key=${key}, isUnlocked=${isUnlocked}, currentTypeId=${document.getElementById('typeId').value}`);
                            }
                            
                            const availableParts = getAvailablePartsForCategory(key, isUnlocked);
                            
                            // Debug logging for new 243 categories
                            if (key === 'elementalResistances243' || key === 'elementalImmunities243' || key === 'elementalSplats243' || key === 'elementalNovas243' || key === 'size243') {
                                console.log(`[DEBUG ${key} updateDropdown] getAvailablePartsForCategory returned ${availableParts.length} parts`);
                                if (availableParts.length > 0) {
                                    console.log(`[DEBUG ${key} updateDropdown] Sample parts:`, availableParts.slice(0, 3).map(p => ({
                                        id: p.id,
                                        fullId: p.fullId,
                                        name: p.name,
                                        partType: p.partType,
                                        spawnCode: p.spawnCode
                                    })));
                                }
                            }
                            
                            // Debug logging for baseBody247
                            if (key === 'baseBody247') {
                                console.log(`[DEBUG baseBody247 updateDropdown] getAvailablePartsForCategory returned ${availableParts.length} parts`);
                                if (availableParts.length > 0) {
                                    console.log(`[DEBUG baseBody247 updateDropdown] Sample part:`, {
                                        id: availableParts[0].id,
                                        fullId: availableParts[0].fullId,
                                        name: availableParts[0].name,
                                        partType: availableParts[0].partType,
                                        path: availableParts[0].path
                                    });
                                } else {
                                    console.log(`[DEBUG baseBody247 updateDropdown] No parts returned! Checking partsByTypeId.get(247):`, 
                                        partsByTypeId.has(247) ? partsByTypeId.get(247).length : 0);
                                    if (partsByTypeId.has(247)) {
                                        const type247Parts = partsByTypeId.get(247);
                                        const mainBodyParts = type247Parts.filter(p => {
                                            const path = String(p.path || '');
                                            const partType = String(p.partType || '');
                                            return path.includes('Main Body') || path.toLowerCase().includes('main body') || 
                                                   partType === 'Main Body' || partType.toLowerCase() === 'main body';
                                        });
                                        console.log(`[DEBUG baseBody247 updateDropdown] Found ${mainBodyParts.length} Main Body parts in partsByTypeId.get(247)`);
                                    }
                                }
                            }
                            
                            // Clear existing options
                            dropdownPanel.innerHTML = '';
                            
                            // Deduplicate availableParts by fullId before populating dropdown
                            const seenParts = new Set();
                            const uniqueParts = availableParts.filter(partInfo => {
                                const fullId = String(partInfo.fullId || partInfo.id || '');
                                if (fullId && seenParts.has(fullId)) {
                                    return false; // Duplicate
                                }
                                if (fullId) seenParts.add(fullId);
                                return true;
                            });
                            
                            // Sort parts alphabetically by name, ignoring the ID prefix
                            const sortedParts = uniqueParts.sort((a, b) => {
                                // For Energy Shield parts (typeId 248), Armor Shield parts (typeId 237), Shield Perks (typeId 246), Universal Enhancements (typeId 247), and Grenade/Ordnance parts (typeId 245), prefer modelName/description for sorting
                                const getName = (part) => {
                                    if (part.typeId === 248 || part.typeId === 237 || part.typeId === 246) {
                                        // Use modelName first, then name, then fallback
                                        return String(part.modelName || part.name || 'Unknown').toLowerCase().trim();
                                    } else if (part.typeId === 247) {
                                        // For enhancements, use description or name for sorting
                                        return String(part.description || part.name || 'Unknown').toLowerCase().trim();
                                    } else if (part.typeId === 245) {
                                        // For grenade/ordnance parts, use name for sorting (already descriptive)
                                        return String(part.name || 'Unknown').toLowerCase().trim();
                                    }
                                    return String(part.name || 'Unknown').toLowerCase().trim();
                                };
                                const nameA = getName(a);
                                const nameB = getName(b);
                                return nameA.localeCompare(nameB);
                            });
                            
                            if (sortedParts.length > 0) {
                                multiSelectButton.disabled = false;
                                multiSelectButton.classList.remove('disabled');
                                
                                // Add "Select All" option at the top
                                const selectAllDiv = document.createElement('div');
                                selectAllDiv.className = 'multi-select-option';
                                selectAllDiv.style.cssText = 'border-bottom: 1px solid rgba(79, 195, 247, 0.3); margin-bottom: 4px; padding-bottom: 4px;';
                                
                                const selectAllCheckbox = document.createElement('input');
                                selectAllCheckbox.type = 'checkbox';
                                selectAllCheckbox.id = `select-all-${key}`;
                                
                                const selectAllLabel = document.createElement('label');
                                selectAllLabel.setAttribute('for', selectAllCheckbox.id);
                                selectAllLabel.textContent = 'Select All';
                                selectAllLabel.style.cssText = 'font-weight: bold; color: #4fc3f7; cursor: pointer;';
                                
                                // Function to check if all items are selected
                                updateSelectAllState = () => {
                                    const allCheckboxes = dropdownPanel.querySelectorAll('input[type="checkbox"]:not(#select-all-' + key + ')');
                                    const checkedCount = Array.from(allCheckboxes).filter(cb => cb.checked).length;
                                    selectAllCheckbox.checked = allCheckboxes.length > 0 && checkedCount === allCheckboxes.length;
                                    selectAllCheckbox.indeterminate = checkedCount > 0 && checkedCount < allCheckboxes.length;
                                };
                                
                                // Update select all state based on current selections
                                selectAllCheckbox.onchange = () => {
                                    const allCheckboxes = dropdownPanel.querySelectorAll('input[type="checkbox"]:not(#select-all-' + key + ')');
                                    const shouldSelect = selectAllCheckbox.checked;
                                    
                                    // First, update all checkbox states
                                    allCheckboxes.forEach(cb => {
                                        cb.checked = shouldSelect;
                                    });
                                    
                                    // Then, update selectedItems array based on checkbox states
                                    // Clear and rebuild to avoid duplicates and ensure correct state
                                    selectedItems.length = 0;
                                    
                                    allCheckboxes.forEach(cb => {
                                        if (cb.checked) {
                                            const optionValue = cb.getAttribute('data-part-value');
                                            if (optionValue) {
                                                // Check if already added (shouldn't be, but just in case)
                                                const existingIndex = selectedItems.findIndex(item => item.value === optionValue);
                                                if (existingIndex === -1) {
                                                    try {
                                                        const parsedData = JSON.parse(optionValue);
                                                        const displayText = cb.getAttribute('data-display-text') || (parsedData.name || 'Unknown');
                                                        const rarityColor = cb.getAttribute('data-rarity-color') || '#b0d4fa';
                                                        const isSkill = cb.getAttribute('data-is-skill') === 'true';
                                                        
                                                        const itemToAdd = {
                                                            value: optionValue,
                                                            data: parsedData,
                                                            displayText: displayText,
                                                            rarityColor: rarityColor
                                                        };
                                                        
                                                        // Add limiter for skills
                                                        if (isSkill && parsedData.limiter) {
                                                            itemToAdd.limiter = parsedData.limiter;
                                                        }
                                                        
                                                        selectedItems.push(itemToAdd);
                                                    } catch (e) {
                                                        console.error('Error parsing optionValue:', e, optionValue);
                                                    }
                                                }
                                            }
                                        }
                                    });
                                    
                                    // Update UI once after all changes
                                    updateChips();
                                    updateButtonText();
                                    updateMultiSelectButton();
                                    if (isSkillsCategory) {
                                        updateQuantityInputTitle();
                                    }
                                    // Note: Don't call updateSelectAllState here as we just changed selectAllCheckbox
                                };
                                
                                selectAllDiv.appendChild(selectAllCheckbox);
                                selectAllDiv.appendChild(selectAllLabel);
                                dropdownPanel.appendChild(selectAllDiv);
                                
                                // Special handling for skills category: Show grouped skills
                                if (isSkillsCategory && sortedParts.length > 0 && sortedParts[0].tiers) {
                                    // This is a grouped skill structure
                                    sortedParts.forEach(skillGroup => {
                                        const limiter = skillGroup.limiter || 5;
                                        const optionValue = JSON.stringify({
                                            skillName: skillGroup.name,
                                            tiers: skillGroup.tiers,
                                            typeId: skillGroup.typeId,
                                            limiter: limiter,
                                            isSkillGroup: true
                                        });
                                        
                                        const optionDiv = document.createElement('div');
                                        optionDiv.className = 'multi-select-option';
                                        
                                        const checkbox = document.createElement('input');
                                        checkbox.type = 'checkbox';
                                        checkbox.id = `checkbox-${key}-${skillGroup.name.replace(/\s+/g, '-')}`;
                                        checkbox.setAttribute('data-part-value', optionValue);
                                        checkbox.setAttribute('data-limiter', limiter);
                                        checkbox.setAttribute('data-display-text', `${skillGroup.name} (Max ${limiter})`);
                                        checkbox.setAttribute('data-rarity-color', '#b0d4fa');
                                        checkbox.setAttribute('data-is-skill', 'true');
                                        checkbox.checked = selectedItems.some(item => item.value === optionValue);
                                        
                                        const label = document.createElement('label');
                                        label.setAttribute('for', checkbox.id);
                                        label.textContent = `${skillGroup.name} (Max ${limiter})`;
                                        label.style.color = '#b0d4fa';
                                        
                                        checkbox.onchange = () => {
                                            if (checkbox.checked) {
                                                // Check if item already exists before adding
                                                const existingIndex = selectedItems.findIndex(item => item.value === optionValue);
                                                if (existingIndex === -1) {
                                                    const parsedData = JSON.parse(optionValue);
                                                    selectedItems.push({
                                                        value: optionValue,
                                                        data: parsedData,
                                                        displayText: `${skillGroup.name} (Max ${parsedData.limiter || 5})`,
                                                        rarityColor: '#b0d4fa',
                                                        limiter: parsedData.limiter || 5
                                                    });
                                                }
                                            } else {
                                                const index = selectedItems.findIndex(item => item.value === optionValue);
                                                if (index > -1) {
                                                    selectedItems.splice(index, 1);
                                                }
                                            }
                                            updateChips();
                                            updateButtonText();
                                            updateMultiSelectButton();
                                            if (isSkillsCategory) {
                                                updateQuantityInputTitle();
                                            }
                                            updateSelectAllState();
                                        };
                                        
                                        optionDiv.appendChild(checkbox);
                                        optionDiv.appendChild(label);
                                        dropdownPanel.appendChild(optionDiv);
                                    });
                                } else {
                                    // Normal parts handling
                                    const currentTypeId = parseInt(document.getElementById('typeId').value) || 0;
                                    sortedParts.forEach(partInfo => {
                                        // Extract part ID correctly
                                        let partId = partInfo.id || '';
                                        const fullId = partInfo.fullId || '';
                                        const partTypeId = partInfo.typeId || currentTypeId;
                                        
                                        // If fullId is in format "typeId:partId", extract partId
                                        if (fullId.includes(':')) {
                                            const parts = fullId.split(':');
                                            if (parts.length >= 2) {
                                                partId = parts[parts.length - 1];
                                            }
                                        } else if (!partId && fullId) {
                                            partId = fullId;
                                        }
                                        
                                        // If partId is still empty, try to extract from id
                                        if (!partId && partInfo.id) {
                                            const idStr = String(partInfo.id);
                                            if (idStr.includes(':')) {
                                                const parts = idStr.split(':');
                                                if (parts.length >= 2) {
                                                    partId = parts[parts.length - 1];
                                                }
                                            } else {
                                                partId = idStr;
                                            }
                                        }
                                        
                                        const optionValue = JSON.stringify({
                                            id: partId,
                                            typeId: partTypeId,
                                            fullId: fullId || `${partTypeId}:${partId}`,
                                            name: partInfo.name || 'Unknown'
                                        });
                                        
                                        const displayText = formatPartForDropdown(partInfo);
                                        const fullIdStrMs = fullId || `${partTypeId}:${partId}`;
                                        const partKeyFromSpawnMs = (partInfo.spawnCode) ? String(partInfo.spawnCode).split('.').pop().toLowerCase() : '';
                                        const isNewPartMs = newSerialIdsGuidelines.has(fullIdStrMs) || (partKeyFromSpawnMs && newPartKeysGuidelines.has(partKeyFromSpawnMs));
                                        const displayTextWithNew = isNewPartMs ? 'NEW! ' + displayText : displayText;
                                        
                                        const rarityColor = getRarityColor(partInfo);
                                        
                                        const optionDiv = document.createElement('div');
                                        optionDiv.className = 'multi-select-option';
                                        
                                        const checkbox = document.createElement('input');
                                        checkbox.type = 'checkbox';
                                        checkbox.id = `checkbox-${key}-${partId}-${Date.now()}-${Math.random()}`;
                                        checkbox.setAttribute('data-part-value', optionValue);
                                        checkbox.setAttribute('data-display-text', displayTextWithNew);
                                        checkbox.setAttribute('data-rarity-color', rarityColor);
                                        checkbox.setAttribute('data-is-skill', 'false');
                                        checkbox.checked = selectedItems.some(item => item.value === optionValue);
                                        
                                        const label = document.createElement('label');
                                        label.setAttribute('for', checkbox.id);
                                        if (isNewPartMs) {
                                            label.innerHTML = '<span style="color: #FF8C42; font-weight: 700;">NEW!</span> ' + displayText;
                                            label.style.color = rarityColor;
                                        } else {
                                            label.textContent = displayText;
                                            label.style.color = rarityColor;
                                        }
                                        
                                        checkbox.onchange = () => {
                                            if (checkbox.checked) {
                                                selectedItems.push({
                                                    value: optionValue,
                                                    data: JSON.parse(optionValue),
                                                    displayText: displayTextWithNew,
                                                    rarityColor: rarityColor
                                                });
                                            } else {
                                                const index = selectedItems.findIndex(item => item.value === optionValue);
                                                if (index > -1) {
                                                    selectedItems.splice(index, 1);
                                                }
                                            }
                                            updateChips();
                                            updateButtonText();
                                            updateMultiSelectButton();
                                            if (isSkillsCategory) {
                                                updateQuantityInputTitle();
                                            }
                                            updateSelectAllState();
                                        };
                                        
                                        optionDiv.appendChild(checkbox);
                                        optionDiv.appendChild(label);
                                        dropdownPanel.appendChild(optionDiv);
                                    });
                                }
                                
                                updateButtonText();
                                updateSelectAllState();
                            } else {
                                multiSelectButton.disabled = true;
                                multiSelectButton.classList.add('disabled');
                                multiSelectButton.textContent = 'No parts available for this category';
                                quantityInput.disabled = true;
                                addButton.disabled = true;
                                addButton.style.opacity = '0.5';
                                addButton.style.cursor = 'not-allowed';
                            }
                        };
                        
                        // Function to add selected parts with quantity
                        const addPartWithQuantity = () => {
                            if (selectedItems.length === 0 || multiSelectButton.disabled) {
                                return;
                            }
                            
                            const quantity = parseInt(quantityInput.value) || 1;
                            
                            if (quantity < 1) {
                                alert('Quantity must be at least 1');
                                return;
                            }
                            
                            if (quantity > 100) {
                                alert('Quantity cannot exceed 100');
                                return;
                            }
                            
                            let totalSuccessCount = 0;
                            const addedParts = [];
                            
                            try {
                                // Process each selected item
                                selectedItems.forEach((selectedItem) => {
                                    const partData = selectedItem.data;
                                
                                    // Special handling for skills: Add tier parts based on points
                                    if (isSkillsCategory && partData.isSkillGroup && partData.tiers) {
                                        let points = quantity; // Use quantity as points for skills
                                        const limiter = partData.limiter || selectedItem.limiter || 5;
                                        
                                        if (points < 1) {
                                            return;
                                        }
                                        
                                        // Cap points at the limiter instead of erroring
                                        if (points > limiter) {
                                            points = limiter;
                                        }
                                    
                                        // Add tier parts 1 through points
                                        let successCount = 0;
                                        console.log(`[SKILLS DEBUG] Adding ${points} points for ${partData.skillName}. Total tiers available: ${partData.tiers.length}`);
                                        
                                        // Loop through tiers 1 to points (0-indexed, so 0 to points-1)
                                        for (let i = 0; i < points && i < partData.tiers.length; i++) {
                                            const tier = partData.tiers[i];
                                            console.log(`[SKILLS DEBUG] Processing tier ${i + 1}/${points}:`, tier);
                                        
                                            // Extract part ID correctly from tier data
                                            let partId = tier.partId;
                                        
                                            // If partId is a string identifier (not numeric), try to find the numeric ID
                                            if (typeof partId === 'string' && isNaN(parseInt(partId))) {
                                                // Try to get numeric ID from partInfo
                                                if (tier.partInfo) {
                                                    // Try spawnCode first
                                                    if (tier.partInfo.spawnCode) {
                                                        const spawnCodeMatch = tier.partInfo.spawnCode.match(/\d+/);
                                                        if (spawnCodeMatch) {
                                                            partId = spawnCodeMatch[0];
                                                        }
                                                    }
                                                    
                                                    // If still not numeric, try fullId
                                                    if (typeof partId === 'string' && isNaN(parseInt(partId))) {
                                                        const fullIdFromPartInfo = tier.partInfo.fullId || '';
                                                        if (fullIdFromPartInfo.includes(':')) {
                                                            const parts = fullIdFromPartInfo.split(':');
                                                            if (parts.length >= 2) {
                                                                const extractedId = parts[parts.length - 1];
                                                                if (!isNaN(parseInt(extractedId))) {
                                                                    partId = extractedId;
                                                                }
                                                            }
                                                        }
                                                    }
                                                    
                                                    // If still not numeric, try looking up the part
                                                    if (typeof partId === 'string' && isNaN(parseInt(partId))) {
                                                        const lookupKey = tier.fullId || tier.partInfo.fullId || partId;
                                                        const lookupPart = partsMap.get(lookupKey) || partsMap.get(partId);
                                                        if (lookupPart) {
                                                            // Try to get numeric ID from looked-up part
                                                            let lookupId = lookupPart.id;
                                                            if (typeof lookupId === 'string' && !isNaN(parseInt(lookupId))) {
                                                                partId = lookupId;
                                                            } else if (lookupPart.fullId && lookupPart.fullId.includes(':')) {
                                                                const parts = lookupPart.fullId.split(':');
                                                                if (parts.length >= 2 && !isNaN(parseInt(parts[parts.length - 1]))) {
                                                                    partId = parts[parts.length - 1];
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                                
                                                // Also try extracting from tier.fullId
                                                if (typeof partId === 'string' && isNaN(parseInt(partId)) && tier.fullId) {
                                                    if (tier.fullId.includes(':')) {
                                                        const parts = tier.fullId.split(':');
                                                        if (parts.length >= 2) {
                                                            const extractedId = parts[parts.length - 1];
                                                            if (!isNaN(parseInt(extractedId))) {
                                                                partId = extractedId;
                                                            }
                                                        }
                                                    }
                                                }
                                            } else if (partId === undefined || partId === null) {
                                                // If partId is not available, try to get it from partInfo
                                                if (tier.partInfo) {
                                                    partId = tier.partInfo.id || '';
                                                    const fullIdFromPartInfo = tier.partInfo.fullId || '';
                                                    if (fullIdFromPartInfo.includes(':')) {
                                                        const parts = fullIdFromPartInfo.split(':');
                                                        if (parts.length >= 2) {
                                                            partId = parts[parts.length - 1];
                                                        }
                                                    } else if (!partId && fullIdFromPartInfo) {
                                                        partId = fullIdFromPartInfo;
                                                    }
                                                } else {
                                                    partId = '';
                                                }
                                            } else if (typeof partId === 'number') {
                                                partId = String(partId);
                                            } else {
                                                partId = String(partId);
                                            }
                                            
                                            // Handle case where partId might still contain a colon
                                            if (typeof partId === 'string' && partId.includes(':')) {
                                                const parts = partId.split(':');
                                                partId = parts[parts.length - 1];
                                            }
                                            
                                            // Ensure partId is a valid number
                                            const numericPartId = parseInt(partId);
                                            if (isNaN(numericPartId) || numericPartId === 0) {
                                                console.error(`[SKILLS DEBUG] Invalid tier partId: ${partId} (type: ${typeof partId}) for tier ${tier.tier} of ${partData.skillName}. Tier data:`, tier);
                                                continue;
                                            }
                                            
                                            // Get typeId - prefer tier.typeId, then partData.typeId, then partInfo.typeId
                                            const tierTypeId = tier.typeId || partData.typeId || (tier.partInfo ? tier.partInfo.typeId : null);
                                            if (!tierTypeId) {
                                                console.error(`[SKILLS DEBUG] Missing typeId for tier ${tier.tier} of ${partData.skillName}. Tier data:`, tier);
                                                continue;
                                            }
                                            
                                            const tierPartData = {
                                                id: numericPartId,
                                                typeId: tierTypeId,
                                                fullId: tier.fullId || `${tierTypeId}:${numericPartId}`,
                                                name: `${partData.skillName} (Tier ${tier.tier})`
                                            };
                                            
                                            console.log(`[SKILLS DEBUG] Attempting to add tier ${tier.tier} with data:`, tierPartData);
                                            const success = addPartFromGuidelineDropdown(key, tierPartData, true);
                                            if (success) {
                                                successCount++;
                                                console.log(`[SKILLS DEBUG] Successfully added tier ${tier.tier}`);
                                            } else {
                                                console.error(`[SKILLS DEBUG] Failed to add tier ${tier.tier} for ${partData.skillName}. partData:`, tierPartData);
                                            }
                                        }
                                        
                                        if (successCount > 0) {
                                            totalSuccessCount += successCount;
                                            addedParts.push(partData.skillName || 'Unknown');
                                        }
                                    } else {
                                        // Normal part handling: Add quantity times
                                        let successCount = 0;
                                        
                                        for (let i = 0; i < quantity; i++) {
                                            const success = addPartFromGuidelineDropdown(key, partData, true); // Allow duplicates
                                            if (success) {
                                                successCount++;
                                            }
                                        }
                                        
                                        if (successCount > 0) {
                                            totalSuccessCount += successCount;
                                            addedParts.push(partData.name || 'Unknown');
                                        }
                                    }
                                });
                                
                                // Update UI after all parts are added
                                if (totalSuccessCount > 0) {
                                    renderParts();
                                    updateGuidelinesChecklist();
                                    generateCode();
                                    
                                    // Clear selections after successful add
                                    selectedItems.length = 0;
                                    updateChips();
                                    updateButtonText();
                                    updateMultiSelectButton();
                                    updateDropdown(); // Refresh dropdown to uncheck checkboxes
                                    
                                    // Show success message
                                    const partsList = addedParts.join(', ');
                                    showStatus('outputStatus', `✅ Added ${totalSuccessCount} ${totalSuccessCount === 1 ? 'part' : 'parts'}: ${partsList}`, 'success');
                                }
                            } catch (e) {
                                console.error('Error adding parts:', e);
                                alert('Error adding parts: ' + e.message);
                            }
                        };
                        
                        // Dropdown open/close handlers
                        let dropdownOpen = false;
                        
                        multiSelectButton.onclick = (e) => {
                            e.stopPropagation();
                            if (multiSelectButton.disabled) return;
                            
                            dropdownOpen = !dropdownOpen;
                            if (dropdownOpen) {
                                dropdownPanel.classList.add('open');
                                multiSelectButton.classList.add('open');
                            } else {
                                dropdownPanel.classList.remove('open');
                                multiSelectButton.classList.remove('open');
                            }
                        };
                        
                        // Close dropdown when clicking outside
                        document.addEventListener('click', (e) => {
                            if (!multiSelectContainer.contains(e.target)) {
                                dropdownOpen = false;
                                dropdownPanel.classList.remove('open');
                                multiSelectButton.classList.remove('open');
                            }
                        });
                        
                        // Stop propagation when clicking inside dropdown
                        dropdownPanel.onclick = (e) => {
                            e.stopPropagation();
                        };
                        
                        // Add button click handler
                        addButton.addEventListener('click', addPartWithQuantity);
                        
                        // Allow Enter key on quantity input to trigger add
                        quantityInput.addEventListener('keypress', function(e) {
                            if (e.key === 'Enter' && !addButton.disabled && selectedItems.length > 0) {
                                addPartWithQuantity();
                            }
                        });
                        
                        // Update title to show limiter info for skills
                        if (isSkillsCategory) {
                            quantityInput.addEventListener('input', function() {
                                const value = parseInt(this.value) || 0;
                                if (selectedItems.length > 0) {
                                    const skillItems = selectedItems.filter(item => item.limiter);
                                    if (skillItems.length > 0) {
                                        const minLimiter = Math.min(...skillItems.map(item => item.limiter));
                                        // Update title to show limiter, but don't restrict input value
                                        this.title = `Select number of skill points (1-5). Max for selected skills: ${minLimiter}`;
                                        
                                        // Show visual warning if value exceeds limiter
                                        if (value > minLimiter) {
                                            this.style.borderColor = '#ff6b6b';
                                            this.style.boxShadow = '0 0 4px rgba(255, 107, 107, 0.5)';
                                        } else {
                                            this.style.borderColor = 'rgba(79, 195, 247, 0.3)';
                                            this.style.boxShadow = 'none';
                                        }
                                    } else {
                                        this.title = 'Select number of skill points (1-5)';
                                        this.style.borderColor = 'rgba(79, 195, 247, 0.3)';
                                        this.style.boxShadow = 'none';
                                    }
                                } else {
                                    this.title = 'Select number of skill points (1-5)';
                                    this.style.borderColor = 'rgba(79, 195, 247, 0.3)';
                                    this.style.boxShadow = 'none';
                                }
                            });
                            
                            // Also update on selection changes
                            const updateQuantityInputTitle = () => {
                                if (selectedItems.length > 0) {
                                    const skillItems = selectedItems.filter(item => item.limiter);
                                    if (skillItems.length > 0) {
                                        const minLimiter = Math.min(...skillItems.map(item => item.limiter));
                                        quantityInput.title = `Select number of skill points (1-5). Max for selected skills: ${minLimiter}`;
                                    } else {
                                        quantityInput.title = 'Select number of skill points (1-5)';
                                    }
                                } else {
                                    quantityInput.title = 'Select number of skill points (1-5)';
                                }
                            };
                            
                            // Call updateQuantityInputTitle after updateChips and updateButtonText
                            // We'll modify the places where these are called to also call updateQuantityInputTitle
                        }
                        
                        // Initial dropdown population
                        updateDropdown();
                        
                        // Update dropdown when master unlock checkbox changes
                        const masterUnlock = document.getElementById('masterUnlockGuidelines');
                        if (masterUnlock) {
                            masterUnlock.addEventListener('change', updateDropdown);
                        }
                        
                        // Assemble the controls
                        multiSelectContainer.appendChild(multiSelectButton);
                        multiSelectContainer.appendChild(dropdownPanel);
                        controlsContainer.appendChild(multiSelectContainer);
                        controlsContainer.appendChild(chipsContainer);
                        quantityButtonContainer.appendChild(quantityInput);
                        quantityButtonContainer.appendChild(addButton);
                        controlsContainer.appendChild(quantityButtonContainer);
                        dropdownContainer.appendChild(controlsContainer);
                        guidelineItem.appendChild(dropdownContainer);
                    }
                } else {
                    // Fallback: try to find the old container structure
                    const container = checkbox.closest('div[style*="display: flex"]');
                    if (container) {
                        const existingParts = container.querySelector('.part-ids-display');
                        if (existingParts) {
                            existingParts.remove();
                        }
                        if (checked && partIds.length > 0 && key !== 'manufacturer' && key !== 'level') {
                            const partsSpan = document.createElement('span');
                            partsSpan.className = 'part-ids-display';
                            partsSpan.style.cssText = 'margin-left: 8px; font-size: 12px; color: #666; font-family: monospace; display: inline-block; white-space: nowrap;';
                            partsSpan.textContent = partIds.join(', ');
                            container.appendChild(partsSpan);
                        }
                    } else {
                        console.log('updateCheckbox: Container not found for', key);
                    }
                }
            };
            
            // Debug: Check what item type we detected and parts count
            // console.log('updateGuidelinesChecklist - category:', category, 'isWeapon:', isWeapon, 'currentParts.length:', currentParts.length);
            
            console.log('updateGuidelinesChecklist: checklistStatus =', checklistStatus);
            
            if (isWeapon) {
                updateCheckbox('manufacturer', []); // Always true if item is selected - no part needed
                updateCheckbox('level', []); // Always true if item is selected - no part needed
                updateCheckbox('rarity', checklistStatus.rarity);
                updateCheckbox('body', checklistStatus.body);
                updateCheckbox('bodyAccessories', checklistStatus.bodyAccessories);
                updateCheckbox('barrel', checklistStatus.barrel);
                updateCheckbox('barrelAccessories', checklistStatus.barrelAccessories);
                updateCheckbox('magazine', checklistStatus.magazine);
                updateCheckbox('scope', checklistStatus.scope);
                updateCheckbox('scopeAccessory', checklistStatus.scopeAccessory);
                updateCheckbox('grip', checklistStatus.grip);
                updateCheckbox('foregrip', checklistStatus.foregrip);
                updateCheckbox('underbarrel', checklistStatus.underbarrel);
                updateCheckbox('daedalusAmmo', checklistStatus.daedalusAmmo);
                updateCheckbox('maliwanLicensedUnderbarrel', checklistStatus.maliwanLicensedUnderbarrel);
                updateCheckbox('licensedParts', checklistStatus.licensedParts);
                updateCheckbox('statModifier', checklistStatus.statModifier);
                updateCheckbox('element', checklistStatus.element);
                console.log('updateGuidelinesChecklist: Updated weapon checkboxes');
            } else if (isHeavyWeapon) {
                updateCheckbox('manufacturer', []);
                updateCheckbox('level', []);
                updateCheckbox('rarity', checklistStatus.rarity);
                updateCheckbox('body', checklistStatus.body);
                updateCheckbox('bodyAccessories', checklistStatus.bodyAccessories);
                updateCheckbox('barrel', checklistStatus.barrel);
                updateCheckbox('barrelAccessories', checklistStatus.barrelAccessories);
                updateCheckbox('firmware244', checklistStatus.firmware244);
                updateCheckbox('element', checklistStatus.element);
            } else if (isRepkit) {
                updateCheckbox('manufacturer', []);
                updateCheckbox('level', []);
                updateCheckbox('rarity', checklistStatus.rarity);
                updateCheckbox('baseBody', checklistStatus.baseBody);
                updateCheckbox('elementalResistances243', checklistStatus.elementalResistances243);
                updateCheckbox('elementalImmunities243', checklistStatus.elementalImmunities243);
                updateCheckbox('elementalSplats243', checklistStatus.elementalSplats243);
                updateCheckbox('elementalNovas243', checklistStatus.elementalNovas243);
                updateCheckbox('size243', checklistStatus.size243);
                updateCheckbox('elemental243', checklistStatus.elemental243);
                updateCheckbox('parts243', checklistStatus.parts243);
                updateCheckbox('firmware243', checklistStatus.firmware243);
                updateCheckbox('element', checklistStatus.element);
            } else if (isGrenade) {
                updateCheckbox('manufacturer', []);
                updateCheckbox('level', []);
                updateCheckbox('rarity', checklistStatus.rarity);
                updateCheckbox('body', checklistStatus.body);
                updateCheckbox('parts245', checklistStatus.parts245);
                updateCheckbox('firmware245', checklistStatus.firmware245);
                updateCheckbox('payload245', checklistStatus.payload245);
                updateCheckbox('stats245', checklistStatus.stats245);
                updateCheckbox('augment245', checklistStatus.augment245);
                updateCheckbox('element', checklistStatus.element);
            } else if (isClassMod) {
                updateCheckbox('manufacturer', []);
                updateCheckbox('level', []);
                updateCheckbox('rarity', checklistStatus.rarity);
                updateCheckbox('body', checklistStatus.body);
                updateCheckbox('skills', checklistStatus.skills);
                updateCheckbox('stat234', checklistStatus.stat234);
                updateCheckbox('stat2_234', checklistStatus.stat2_234);
                updateCheckbox('statspecial_234', checklistStatus.statspecial_234);
                updateCheckbox('firmware234', checklistStatus.firmware234);
                updateCheckbox('element', checklistStatus.element);
            } else if (isShield) {
                updateCheckbox('manufacturer', []);
                updateCheckbox('level', []);
                updateCheckbox('rarity', checklistStatus.rarity);
                updateCheckbox('baseBody', checklistStatus.baseBody);
                updateCheckbox('legendaryPart', checklistStatus.legendaryPart);
                updateCheckbox('primaryPerks246', checklistStatus.primaryPerks246);
                updateCheckbox('secondaryPerks246', checklistStatus.secondaryPerks246);
                updateCheckbox('resistance246', checklistStatus.resistance246);
                updateCheckbox('armor237', checklistStatus.armor237);
                updateCheckbox('energy248', checklistStatus.energy248);
                updateCheckbox('firmware246', checklistStatus.firmware246);
                updateCheckbox('element', checklistStatus.element);
            } else if (isEnhancement) {
                updateCheckbox('manufacturer', []);
                updateCheckbox('level', []);
                updateCheckbox('rarity', checklistStatus.rarity);
                updateCheckbox('baseBody247', checklistStatus.baseBody247);
                updateCheckbox('legendaryPerks', checklistStatus.legendaryPerks);
                updateCheckbox('stat_247', checklistStatus.stat_247);
                updateCheckbox('stat2_247', checklistStatus.stat2_247);
                updateCheckbox('stat3_247', checklistStatus.stat3_247);
                updateCheckbox('firmware247', checklistStatus.firmware247);
                updateCheckbox('element', checklistStatus.element);
            } else {
                // Fallback: If no specific category matched, at least check manufacturer and level
                // This ensures they're always checked even if category detection fails
                updateCheckbox('manufacturer', []);
                updateCheckbox('level', []);
            }
        }

        // Function to update data status indicator (exposed for inline handlers and other scripts)
