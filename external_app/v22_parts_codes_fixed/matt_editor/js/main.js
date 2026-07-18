        // Item roll generator removed. Legit Item Builder and Validator replace it.
        (function initDelayedInnerScrollGuard() {
            const HOVER_DELAY_MS = 500;
            const hoverStartByElement = new WeakMap();
            let lastHoverElement = null;

            function isRootScrollElement(el) {
                return el === document.body || el === document.documentElement;
            }

            function getOverflowValue(style, axis) {
                return axis === 'x' ? style.overflowX : style.overflowY;
            }

            function allowsScroll(style, axis) {
                return /auto|scroll|overlay/i.test(getOverflowValue(style, axis) || '');
            }

            function isNativeScrollable(el, axis) {
                if (!el || isRootScrollElement(el)) return false;
                const style = window.getComputedStyle(el);
                if (!allowsScroll(style, axis)) return false;
                if (axis === 'x') return el.scrollWidth > el.clientWidth + 1;
                return el.scrollHeight > el.clientHeight + 1;
            }

            function canScrollNative(el, deltaX, deltaY) {
                if (!el) return false;
                if (Math.abs(deltaY) >= Math.abs(deltaX)) {
                    if (!isNativeScrollable(el, 'y')) return false;
                    if (deltaY < 0) return el.scrollTop > 0;
                    if (deltaY > 0) return el.scrollTop + el.clientHeight < el.scrollHeight - 1;
                    return true;
                }
                if (!isNativeScrollable(el, 'x')) return false;
                if (deltaX < 0) return el.scrollLeft > 0;
                if (deltaX > 0) return el.scrollLeft + el.clientWidth < el.scrollWidth - 1;
                return true;
            }

            function closestMonacoScrollArea(target) {
                return target && target.closest && target.closest('.monaco-editor, .monaco-scrollable-element');
            }

            function closestNativeScrollable(target, deltaX, deltaY) {
                let el = target && target.nodeType === 1 ? target : target && target.parentElement;
                while (el && el !== document.body && el !== document.documentElement) {
                    if (canScrollNative(el, deltaX, deltaY)) return el;
                    el = el.parentElement;
                }
                return null;
            }

            function closestInnerScrollTarget(event) {
                const nativeScrollable = closestNativeScrollable(event.target, event.deltaX, event.deltaY);
                if (nativeScrollable) return nativeScrollable;
                return closestMonacoScrollArea(event.target);
            }

            function markHoverTarget(target) {
                if (!target) return;
                const fakeEvent = { target: target, deltaX: 0, deltaY: 1 };
                const scrollTarget = closestInnerScrollTarget(fakeEvent);
                if (!scrollTarget) {
                    lastHoverElement = null;
                    return;
                }
                if (scrollTarget !== lastHoverElement) {
                    hoverStartByElement.set(scrollTarget, performance.now());
                    lastHoverElement = scrollTarget;
                }
            }

            function scrollPageByWheel(event) {
                const left = event.shiftKey && Math.abs(event.deltaX) < Math.abs(event.deltaY)
                    ? event.deltaY
                    : event.deltaX;
                try {
                    window.scrollBy({ top: event.deltaY, left: left, behavior: 'auto' });
                } catch (err) {
                    window.scrollBy(left, event.deltaY);
                }
            }

            document.addEventListener('pointermove', function (event) {
                if (event.pointerType && event.pointerType !== 'mouse' && event.pointerType !== 'pen') return;
                markHoverTarget(event.target);
            }, true);
            document.addEventListener('mouseover', function (event) {
                markHoverTarget(event.target);
            }, true);
            document.addEventListener('wheel', function (event) {
                if (event.defaultPrevented || event.ctrlKey) return;
                const scrollTarget = closestInnerScrollTarget(event);
                if (!scrollTarget) return;
                const started = hoverStartByElement.get(scrollTarget);
                const now = performance.now();
                if (started == null) {
                    hoverStartByElement.set(scrollTarget, now);
                }
                if (started == null || now - started < HOVER_DELAY_MS) {
                    event.preventDefault();
                    event.stopPropagation();
                    scrollPageByWheel(event);
                }
            }, { capture: true, passive: false });
        })();

        function init() {}

        function showNotification(message, type = 'success', options) {
            const opts = typeof options === 'object' && options !== null ? options : {};
            const durationMs = opts.durationMs != null ? opts.durationMs : 3000;
            const replaceId = opts.replaceId;
            if (replaceId) {
                const rid = String(replaceId).replace(/["\\]/g, '');
                const old = document.querySelector(
                    '[data-notification-replace-id="' + rid + '"]'
                );
                if (old) {
                    if (old._notificationHideTimeout) {
                        clearTimeout(old._notificationHideTimeout);
                    }
                    old.remove();
                }
            }
            const bg =
                type === 'error'
                    ? '#f44336'
                    : type === 'info'
                        ? '#1565c0'
                        : '#4caf50';
            const notification = document.createElement('div');
            notification.className = 'notification';
            notification.setAttribute('role', 'status');
            if (replaceId) {
                notification.setAttribute(
                    'data-notification-replace-id',
                    String(replaceId).replace(/["\\]/g, '')
                );
            }
            notification.style.cssText = [
                'position: fixed',
                'top: var(--page-pad)',
                'left: 50%',
                'transform: translateX(-50%)',
                'z-index: 20000',
                'max-width: min(90vw, 380px)',
                'padding: var(--input-pad-y) var(--btn-pad-x)',
                'border-radius: var(--panel-radius)',
                'color: #fff',
                'font-size: var(--btn-font)',
                'font-weight: 600',
                'text-align: center',
                'box-shadow: 0 6px 24px rgba(0,0,0,0.45)',
                'pointer-events: none',
                'background: ' + bg
            ].join(';');
            notification.textContent = message;
            document.body.appendChild(notification);

            if (durationMs > 0) {
                notification._notificationHideTimeout = setTimeout(function () {
                    notification.style.opacity = '0';
                    notification.style.transition = 'opacity 0.25s ease';
                    setTimeout(function () {
                        notification.remove();
                    }, 280);
                }, durationMs);
            }
        }
        window.showNotification = showNotification;

        // Update auto-add to backpack checkbox state based on save file status
        function updateAutoAddToBackpackCheckbox() {
            if (typeof window.updateLegitValidatorBackpackButton === 'function') {
                window.updateLegitValidatorBackpackButton();
            }

            const checkbox = document.getElementById('autoAddToBackpack');
            const label = document.getElementById('autoAddToBackpackLabel');
            const text = document.getElementById('autoAddToBackpackText');
            
            if (!checkbox || !label || !text) return;
            
            const isLoaded = window.saveEditorState && window.saveEditorState.isLoaded;
            
            checkbox.disabled = !isLoaded;
            if (isLoaded) {
                label.style.cursor = 'pointer';
                label.style.opacity = '1';
                text.textContent = 'Auto-add to backpack';
                text.style.color = '#fff';
            } else {
                label.style.cursor = 'not-allowed';
                label.style.opacity = '0.5';
                text.textContent = 'Auto-add to backpack (load save first)';
                text.style.color = '#888';
                checkbox.checked = false; // Uncheck if save is unloaded
            }
            
            // Also update the Add to Backpack button text
            updateAddToBackpackButton();
        }
        
        // Update Add to Backpack button text based on save file status
        function updateAddToBackpackButton() {
            const button = document.getElementById('addToBackpackBtnRoll');
            if (!button) return;
            
            const isLoaded = window.saveEditorState && window.saveEditorState.isLoaded;
            
            if (isLoaded) {
                button.innerHTML = '<span>📦</span> Add to Backpack';
                button.disabled = false;
            } else {
                button.innerHTML = '<span>💾</span> Please Load a Save';
                button.disabled = false; // Keep enabled so user can click to load save
            }
        }

        function copyToClipboard() {
            const outputCode = document.getElementById('outputCode');
            if (!outputCode) return;
            const codeText = (outputCode.value || outputCode.textContent || '').trim();
            if (!codeText || codeText.includes('Generated code will appear here') || (!codeText.includes('|') && !codeText.includes(','))) {
                showNotification('Please generate or paste an item code in the Item Editor first.', 'error');
                return;
            }
            const text = outputCode.value || outputCode.textContent || '';
            navigator.clipboard.writeText(text).then(() => {
                showNotification('Copied to clipboard!', 'success');
                const statusDiv = document.getElementById('outputStatus');
                if (statusDiv) {
                    statusDiv.textContent = '✓ Copied to clipboard!';
                    statusDiv.className = 'status success';
                    statusDiv.style.display = 'flex';
                    setTimeout(function() { statusDiv.style.display = 'none'; }, 2000);
                }
            }).catch(function() {
                const textarea = document.createElement('textarea');
                textarea.value = text;
                document.body.appendChild(textarea);
                textarea.select();
                document.execCommand('copy');
                document.body.removeChild(textarea);
                showNotification('Copied to clipboard!', 'success');
                const statusDiv = document.getElementById('outputStatus');
                if (statusDiv) {
                    statusDiv.textContent = '✓ Copied to clipboard!';
                    statusDiv.className = 'status success';
                    statusDiv.style.display = 'flex';
                    setTimeout(function() { statusDiv.style.display = 'none'; }, 2000);
                }
            });
        }

        function getPendingYamlEditorValue(yamlContainer) {
            if (
                yamlContainer &&
                yamlContainer.dataset &&
                typeof yamlContainer.dataset.value === 'string'
            ) {
                return yamlContainer.dataset.value;
            }
            if (window.saveEditorState && typeof window.saveEditorState.yamlContent === 'string') {
                return window.saveEditorState.yamlContent;
            }
            return '';
        }

        function enableYamlEditorTextFallback(yamlContainer, value) {
            if (!yamlContainer || window.yamlMonacoEditor) return;

            const normalizedValue = value || '';
            if (yamlContainer.dataset) {
                yamlContainer.dataset.value = normalizedValue;
                yamlContainer.dataset.msbtYamlFallback = '1';
            }
            if (window.saveEditorState) {
                window.saveEditorState.yamlContent = normalizedValue;
            }

            yamlContainer.textContent = normalizedValue;
            yamlContainer.style.whiteSpace = 'pre';
            yamlContainer.style.overflow = 'auto';
            yamlContainer.style.fontFamily = 'Consolas, "Courier New", monospace';
            yamlContainer.style.fontSize = '12px';
            yamlContainer.style.lineHeight = '1.35';
            yamlContainer.style.padding = '12px';
            yamlContainer.contentEditable = 'true';

            if (!yamlContainer.dataset || yamlContainer.dataset.msbtYamlInputBound === '1') {
                return;
            }

            yamlContainer.addEventListener('input', function() {
                if (window.yamlMonacoEditor) return;
                const currentValue = yamlContainer.textContent || '';
                yamlContainer.dataset.value = currentValue;
                if (window.saveEditorState) {
                    window.saveEditorState.yamlContent = currentValue;
                }
            });
            yamlContainer.dataset.msbtYamlInputBound = '1';
        }

        // Initialize Monaco Editor for YAML textarea
        function initMonacoYamlEditor() {
            const yamlContainer = document.getElementById('save-yaml-textarea');
            if (!yamlContainer || window.window.yamlMonacoEditor) return;
            
            // Check if Monaco is loaded
            if (typeof require === 'undefined') {
                console.warn('Monaco Editor not loaded, using textarea fallback');
                enableYamlEditorTextFallback(yamlContainer, getPendingYamlEditorValue(yamlContainer));
                // Add change listener for textarea fallback
                if (yamlContainer.tagName === 'TEXTAREA') {
                    let debounceTimer = null;
                    yamlContainer.addEventListener('input', function() {
                        // Debounce to avoid too many refreshes while typing
                        if (debounceTimer) {
                            clearTimeout(debounceTimer);
                        }
                        debounceTimer = setTimeout(function() {
                            const yamlValue = yamlContainer.value;
                            if (yamlValue && typeof decodeYamlInventory === 'function') {
                                // Update the original YAML content
                                window.originalYAMLContent = yamlValue;
                                window.saveEditorState.yamlContent = yamlValue;
                                // Refresh the display
                                decodeYamlInventory(yamlValue, { showStatus: false, itemDecode: "none" }).catch(err => {
                                    console.warn('Error refreshing display from YAML changes:', err);
                                });
                            }
                        }, 1000); // Wait 1 second after user stops typing
                    });
                }
                return;
            }
            
            // Configure Monaco Editor path - use local path in Electron, CDN otherwise
            let monacoPath;
            if (typeof window !== 'undefined' && window.IS_ELECTRON_APP) {
                // In Electron, use local node_modules path (works for both dev and packaged with unpacked files)
                monacoPath = './node_modules/monaco-editor/min/vs';
                if (DEBUG) console.debug('[Monaco] Using local path for Electron:', monacoPath);
            } else {
                // In browser, use CDN
                monacoPath = 'https://cdn.jsdelivr.net/npm/monaco-editor@0.45.0/min/vs';
                if (DEBUG) console.debug('[Monaco] Using CDN path for browser:', monacoPath);
            }
            
            require.config({
                paths: { vs: monacoPath }
            });
            
            require(['vs/editor/editor.main'], function() {
                try {
                    // Setup YAML language features (same as save editor)
                    setupYamlLanguageFeaturesForItemEditor();

                    const initialYamlValue = getPendingYamlEditorValue(yamlContainer);
                    if (yamlContainer.dataset && yamlContainer.dataset.msbtYamlFallback === '1') {
                        yamlContainer.textContent = '';
                        yamlContainer.contentEditable = 'false';
                        yamlContainer.style.padding = '';
                        delete yamlContainer.dataset.msbtYamlFallback;
                    }
                    
                    window.window.yamlMonacoEditor = monaco.editor.create(yamlContainer, {
                        value: initialYamlValue,
                        language: 'yaml',
                        theme: 'vs-dark',
                        automaticLayout: true,
                        tabSize: 2,
                        minimap: { enabled: true },
                        wordWrap: 'on',
                        formatOnPaste: true,
                        formatOnType: true,
                        quickSuggestions: {
                            other: true,
                            comments: false,
                            strings: true
                        },
                        hover: { enabled: true },
                        bracketPairColorization: { enabled: true },
                        guides: {
                            bracketPairs: true,
                            indentation: true
                        }
                    });
                    
                    // Watch for container size changes and update Monaco layout
                    const resizeObserver = new ResizeObserver(function(entries) {
                        if (window.yamlMonacoEditor) {
                            window.yamlMonacoEditor.layout();
                        }
                    });
                    resizeObserver.observe(yamlContainer);
                    
                    // Note: Change listener is set up by setupYamlAutoDecode() to ensure
                    // it includes reindexBackpackSlots and other necessary logic
                    
                    console.log('✅ Monaco Editor initialized for YAML editing');
                } catch (error) {
                    console.error('Error initializing Monaco Editor:', error);
                    enableYamlEditorTextFallback(yamlContainer, getPendingYamlEditorValue(yamlContainer));
                }
            }, function(error) {
                console.error('Error loading Monaco Editor:', error);
                enableYamlEditorTextFallback(yamlContainer, getPendingYamlEditorValue(yamlContainer));
            });
        }
        
        // Setup YAML language features (copied from save editor)
        function setupYamlLanguageFeaturesForItemEditor() {
            if (typeof monaco === 'undefined') return;
            
            // Copy the same setupYamlLanguageFeatures function from save editor
            // For brevity, we'll register basic providers here
            // Full implementation would include all the context-aware features
            monaco.languages.registerCompletionItemProvider('yaml', {
                provideCompletionItems: function(model, position) {
                    return { suggestions: getBasicYamlSuggestions() };
                }
            });
            
            monaco.languages.registerHoverProvider('yaml', {
                provideHover: function(model, position) {
                    const word = model.getWordAtPosition(position);
                    if (!word) return null;
                    const hoverInfo = getBasicHoverInfo(word.word);
                    if (hoverInfo) {
                        return {
                            range: new monaco.Range(position.lineNumber, word.startColumn, position.lineNumber, word.endColumn),
                            contents: [{ value: `**${hoverInfo.title}**` }, { value: hoverInfo.description }]
                        };
                    }
                    return null;
                }
            });
        }
        
        function getBasicYamlSuggestions() {
            return [
                { label: 'state', kind: monaco.languages.CompletionItemKind.Struct, insertText: 'state:\n  ', documentation: 'Character state: name, class, experience, inventory, currencies' },
                { label: 'missions', kind: monaco.languages.CompletionItemKind.Struct, insertText: 'missions:\n  local_sets:\n    ', documentation: 'Mission progress and completion states' },
                { label: 'progression', kind: monaco.languages.CompletionItemKind.Struct, insertText: 'progression:\n  ', documentation: 'Skill trees, SDU upgrades, point pools' },
                { label: 'stats', kind: monaco.languages.CompletionItemKind.Struct, insertText: 'stats:\n  ', documentation: 'Achievements, challenges, openworld stats' },
                { label: 'gbx_discovery_pc', kind: monaco.languages.CompletionItemKind.Struct, insertText: 'gbx_discovery_pc:\n  ', documentation: 'Fog of war maps and region visit tracking' },
                { label: 'gbx_discovery_pg', kind: monaco.languages.CompletionItemKind.Struct, insertText: 'gbx_discovery_pg:\n  dlblob: ', documentation: 'Discovered points-of-interest (map markers)' },
                { label: 'globals', kind: monaco.languages.CompletionItemKind.Struct, insertText: 'globals:\n  ', documentation: 'UVH level and global character state' },
                { label: 'unlockables', kind: monaco.languages.CompletionItemKind.Struct, insertText: 'unlockables:\n  ', documentation: 'Unlocked items like hoverdrives' },
                { label: 'pips', kind: monaco.languages.CompletionItemKind.Struct, insertText: 'pips:\n  pips_list: []', documentation: 'Notification markers (remove entries to fix stuck <!>)' }
            ];
        }
        
        function getBasicHoverInfo(word) {
            const hoverData = {
                'state': { title: 'State', description: 'Character state including name, class, experience level, inventory, and currencies.' },
                'missions': { title: 'Missions', description: 'Mission progress and completion states. Organized in missionsets (quest chains).' },
                'progression': { title: 'Progression', description: 'Skill trees, SDU upgrades, and point pools (skill points, specialization tokens, echo tokens).' },
                'stats': { title: 'Statistics', description: 'Achievement progress, challenge counters, and open world tracking (activities, collectibles).' },
                'pips': { title: 'Pips', description: 'Notification markers. Remove entries from pips_list to fix stuck <!> notifications in-game.' }
            };
            return hoverData[word] || null;
        }
        
        // Resize functionality for YAML editor
        let isResizingYamlEditor = false;
        let resizeStartY = 0;
        let resizeStartHeight = 0;
        
        function initYamlEditorResize() {
            const editorContainer = document.getElementById('save-yaml-textarea');
            const resizeHandle = document.getElementById('yaml-editor-resize-handle');
            if (!editorContainer || !resizeHandle) return;
            
            // Mouse drag resize
            resizeHandle.addEventListener('mousedown', function(e) {
                e.preventDefault();
                isResizingYamlEditor = true;
                resizeStartY = e.clientY;
                resizeStartHeight = editorContainer.offsetHeight;
                
                document.addEventListener('mousemove', handleYamlEditorResize);
                document.addEventListener('mouseup', stopYamlEditorResize);
                
                document.body.style.cursor = 'nwse-resize';
                document.body.style.userSelect = 'none';
            });
            
            function handleYamlEditorResize(e) {
                if (!isResizingYamlEditor) return;
                
                const deltaY = e.clientY - resizeStartY;
                const newHeight = resizeStartHeight + deltaY;
                const minHeight = 200;
                const maxHeight = window.innerHeight * 0.9;
                
                if (newHeight >= minHeight && newHeight <= maxHeight) {
                    editorContainer.style.height = newHeight + 'px';
                    
                    // Update Monaco editor layout
                    if (window.yamlMonacoEditor) {
                        window.yamlMonacoEditor.layout();
                    }
                }
            }
            
            function stopYamlEditorResize() {
                isResizingYamlEditor = false;
                document.removeEventListener('mousemove', handleYamlEditorResize);
                document.removeEventListener('mouseup', stopYamlEditorResize);
                document.body.style.cursor = '';
                document.body.style.userSelect = '';
            }
            
            // Also enable CSS resize as fallback
            editorContainer.style.resize = 'vertical';
        }
        
        // Initialize on load
        document.addEventListener('DOMContentLoaded', function() {
            init();
            // Initialize auto-add checkbox state and button text
            updateAutoAddToBackpackCheckbox();
            updateAddToBackpackButton();
            
            // Initialize Monaco Editor after a short delay to ensure DOM is ready
            setTimeout(function() {
                initMonacoYamlEditor();
                initYamlEditorResize();
            }, 500);
        });
