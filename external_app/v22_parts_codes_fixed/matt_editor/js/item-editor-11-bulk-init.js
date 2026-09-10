        // Helper function to ensure trailing pipe
        function ensureTrailingPipe(str) {
            if (!str) return '';
            str = str.trim();
            if (!str.endsWith('|')) {
                return str + '|';
            }
            return str;
        }

        const NICNL_API_DEFAULT = 'https://save-editor.be/nicnl/api.php';
        function nicnlApiBase() {
            return (typeof window.API_BASE_URL === 'string' && window.API_BASE_URL) || NICNL_API_DEFAULT;
        }
        function nicnlApiFallback() {
            return (typeof window.API_FALLBACK_URL === 'string' && window.API_FALLBACK_URL) || NICNL_API_DEFAULT;
        }

        // Helper function to serialize deserialized code
        async function serializeDeserialized(deserialized) {
            const API_BASE_URL = nicnlApiBase();
            const API_FALLBACK_URL = nicnlApiFallback();
            // Try local API first
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 30000);

                const response = await fetch(API_BASE_URL, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ deserialized: deserialized }),
                    signal: controller.signal,
                });
                clearTimeout(timeoutId);

                if (response.ok) {
                    const result = await response.json();
                    if (result.serial_b85) {
                        return result.serial_b85;
                    }
                }
            } catch (error) {
                console.warn(
                    "Local API serialize failed, trying fallback:",
                    error.message
                );
            }

            // Fallback to alternative API
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 30000);

                const response = await fetch(API_FALLBACK_URL, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ deserialized: deserialized }),
                    signal: controller.signal,
                });
                clearTimeout(timeoutId);

                if (response.ok) {
                    const result = await response.json();
                    if (result.serial_b85) {
                        return result.serial_b85;
                    }
                }
                throw new Error("Fallback API returned invalid response");
            } catch (error) {
                throw new Error(
                    `Both serialize APIs failed. Last error: ${error.message}`
                );
            }
        }

        // Copy to clipboard helper function
        window.copyToClipboardHelper = function copyToClipboardHelper(text, type = 'text') {
            if (!text) return false;
            
            // Try modern clipboard API first
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(text).then(() => {
                    // Show brief success feedback
                    const statusEl = document.getElementById('save-decrypt-status');
                    if (statusEl) {
                        const originalText = statusEl.textContent;
                        statusEl.textContent = `✅ Copied ${type} to clipboard!`;
                        statusEl.style.display = 'block';
                        setTimeout(() => {
                            statusEl.textContent = originalText;
                        }, 2000);
                    }
                }).catch(() => {
                    // Fallback to old method
                    fallbackCopy(text);
                });
                return true;
            } else {
                // Fallback for older browsers
                return fallbackCopy(text);
            }
        };
        
        function fallbackCopy(text) {
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            textArea.style.top = '-999999px';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            try {
                const successful = document.execCommand('copy');
                document.body.removeChild(textArea);
                if (successful) {
                    const statusEl = document.getElementById('save-decrypt-status');
                    if (statusEl) {
                        const originalText = statusEl.textContent;
                        statusEl.textContent = `✅ Copied to clipboard!`;
                        statusEl.style.display = 'block';
                        setTimeout(() => {
                            statusEl.textContent = originalText;
                        }, 2000);
                    }
                }
                return successful;
            } catch (err) {
                document.body.removeChild(textArea);
                return false;
            }
        }

        // Bulk Serial Status
        function setBulkSerialStatus(message, tone = 'info') {
            const statusEl = document.getElementById('bulk-serial-status');
            if (!statusEl) return;

            if (!message) {
                statusEl.style.display = 'none';
                statusEl.textContent = '';
                return;
            }

            const palette =
                tone === 'error'
                    ? {
                        background: 'rgba(255, 100, 100, 0.2)',
                        border: 'rgba(255, 100, 100, 0.45)',
                    }
                    : tone === 'success'
                    ? {
                        background: 'rgba(100, 255, 180, 0.18)',
                        border: 'rgba(100, 255, 180, 0.45)',
                    }
                    : {
                        background: 'rgba(66, 165, 245, 0.18)',
                        border: 'rgba(66, 165, 245, 0.45)',
                    };

            statusEl.style.display = 'block';
            statusEl.style.background = palette.background;
            statusEl.style.borderColor = palette.border;
            statusEl.style.color = '#fff';
            statusEl.textContent = message;
        }

        // Parse bulk input - extracts serials from multiple formats (same as bulk item adder)
        function parseBulkInput(value) {
            const serials = [];
            const input = value.trim();
            const lines = input.split("\n");

            // Try parsing as JavaScript object (e.g., 'Harlowe': [{ code: '...', name: '...' }])
            try {
                const cleanedInput = input.trim();
                // Check if it looks like a JavaScript object with code properties
                if (
                    cleanedInput.includes("code:") ||
                    cleanedInput.includes("'Harlowe'") ||
                    cleanedInput.includes('"Harlowe"')
                ) {
                    // Try to extract code values from object format
                    // Match: code: '...' or code: "..." or code: `...`
                    const codeMatches = cleanedInput.match(
                        /code:\s*['"`]([^'"`]+)['"`]/g
                    );
                    if (codeMatches && codeMatches.length > 0) {
                        codeMatches.forEach((match) => {
                            const codeMatch = match.match(/['"`]([^'"`]+)['"`]/);
                            if (codeMatch && codeMatch[1]) {
                                const code = codeMatch[1].trim();
                                // Make sure it's not empty and looks like a serial
                                if (
                                    code &&
                                    (code.startsWith("@Ug") ||
                                        /^\d+,\s*\d+,\s*\d+,\s*\d+\|/.test(code))
                                ) {
                                    serials.push(code);
                                }
                            }
                        });
                    }
                }
            } catch (e) {
                // Not a JavaScript object, continue with other formats
            }

            // If no serials found from object format, try other formats
            if (serials.length === 0) {
                // Try parsing as YAML format (inventory.items.backpack.slot_X.serial)
                const yamlSerialMatches = input.match(
                    /serial:\s*['"]?(@Ug[^\s\n]+)['"]?/g
                );
                if (yamlSerialMatches) {
                    yamlSerialMatches.forEach((match) => {
                        const serialMatch = match.match(
                            /serial:\s*['"]?(@Ug[^\s\n]+)['"]?/
                        );
                        if (serialMatch && serialMatch[1]) {
                            let serial = serialMatch[1];
                            // Remove trailing quotes if present
                            serial = serial.replace(/['"]+$/, "");
                            // Validate Base85 characters
                            const base85Part = serial.substring(3);
                            const base85Regex =
                                /^[A-Za-z0-9+/=!$%&*@()\[\]{}~`^_<>?#;-]+$/;
                            if (
                                serial.startsWith("@Ug") &&
                                serial.length >= 10 &&
                                base85Regex.test(base85Part)
                            ) {
                                serials.push(serial);
                            }
                        }
                    });
                }

                // If still no serials, parse line by line
                if (serials.length === 0) {
                    for (const line of lines) {
                        const trimmed = line.trim();
                        if (
                            !trimmed ||
                            trimmed.startsWith("#") ||
                            trimmed.startsWith("//")
                        )
                            continue;

                        // Check if line contains a serial
                        if (trimmed.startsWith("@Ug")) {
                            // Extract the full Base85 serial (match until whitespace, then validate)
                            const match = trimmed.match(/@Ug[^\s\n\r]+/);
                            if (match) {
                                let serial = match[0];
                                // Remove trailing quotes
                                serial = serial.replace(/['"]+$/, "");
                                // Validate Base85 characters
                                const base85Part = serial.substring(3);
                                const base85Regex =
                                    /^[A-Za-z0-9+/=!$%&*@()\[\]{}~`^_<>?#;-]+$/;
                                if (serial.length >= 10 && base85Regex.test(base85Part)) {
                                    serials.push(serial);
                                }
                            }
                        }
                        // Decoded format: starts with numbers like "259, 0, 1, 50|"
                        else if (/^\d+,\s*\d+,\s*\d+,\s*\d+\|/.test(trimmed)) {
                            // Extract the full decoded serial (until end of line or next pattern)
                            const match = trimmed.match(/^[^@\n]+/);
                            if (match) {
                                serials.push(match[0].trim());
                            }
                        }
                        // YAML format: serial: '@Ug...'
                        else if (trimmed.includes("serial:")) {
                            const serialMatch = trimmed.match(
                                /serial:\s*['"]?(@Ug[^\s\n]+)['"]?/
                            );
                            if (serialMatch && serialMatch[1]) {
                                let serial = serialMatch[1];
                                // Remove trailing quotes
                                serial = serial.replace(/['"]+$/, "");
                                // Validate Base85 characters
                                const base85Part = serial.substring(3);
                                const base85Regex =
                                    /^[A-Za-z0-9+/=!$%&*@()\[\]{}~`^_<>?#;-]+$/;
                                if (
                                    serial.startsWith("@Ug") &&
                                    serial.length >= 10 &&
                                    base85Regex.test(base85Part)
                                ) {
                                    serials.push(serial);
                                }
                            }
                        }
                    }
                }
            }

            return serials;
        }

        // Normalize bulk input (legacy function for simple line-by-line parsing)
        function normalizeBulkInput(value) {
            return value
                .split(/\r?\n/)
                .map((line) => line.trim())
                .filter(Boolean);
        }

        // Process serials sequentially
        async function processSerialsSequentially(items, handler) {
            const results = [];
            for (let i = 0; i < items.length; i++) {
                const item = items[i];
                try {
                    const result = await handler(item, i);
                    results.push(result);
                } catch (error) {
                    results.push(
                        `#${i + 1} ERROR: ${error?.message || error || 'Unknown error'}`
                    );
                }
            }
            return results;
        }

        // Bulk Deserialize Serials
        window.bulkDeserializeSerials = async function bulkDeserializeSerials() {
            const inputEl = document.getElementById('bulk-serial-input');
            const outputEl = document.getElementById('bulk-serial-output');
            if (!inputEl || !outputEl) return;

            // Parse input to extract serials from multiple formats
            const parsedSerials = parseBulkInput(inputEl.value);
            if (!parsedSerials.length) {
                setBulkSerialStatus(
                    'No valid serials found. Supports: Base85 (@Ug...), decoded format (259, 0, 1, 50|...), YAML format, or JavaScript object format.',
                    'error'
                );
                return;
            }

            setBulkSerialStatus(
                `Decoding ${parsedSerials.length} serial${parsedSerials.length !== 1 ? 's' : ''}...`,
                'info'
            );

            try {
                const API_BASE_URL = nicnlApiBase();
                const API_FALLBACK_URL = nicnlApiFallback();
                // Separate Base85 serials and decoded serials
                const base85Serials = [];
                const decodedSerials = [];
                const serialIndexMap = new Map(); // Map to track original order

                parsedSerials.forEach((serial, index) => {
                    if (serial.startsWith('@Ug')) {
                        base85Serials.push(serial);
                        serialIndexMap.set(serial, { type: 'base85', index });
                    } else if (/^\d+,\s*\d+,\s*\d+,\s*\d+\|/.test(serial)) {
                        decodedSerials.push(serial);
                        serialIndexMap.set(serial, { type: 'decoded', index });
                    }
                });

                // Normalize Base85 serials (ensure @ prefix)
                const normalizedBase85Serials = base85Serials.map(serial => {
                    return serial.startsWith('@') ? serial : `@${serial}`;
                });

                // Deserialize Base85 serials via API
                let base85Results = {};
                let apiError = null;
                const isFileProtocol = window.location.protocol === 'file:';
                const isRemoteApi = API_BASE_URL && (API_BASE_URL.startsWith('http://') || API_BASE_URL.startsWith('https://')) && !API_BASE_URL.includes(window.location.hostname);
                
                if (normalizedBase85Serials.length > 0) {
                    // Skip primary API if it's a remote API that might require auth (when using file://)
                    let triedPrimary = false;
                    if (!(isFileProtocol && isRemoteApi)) {
                        try {
                            triedPrimary = true;
                            const controller = new AbortController();
                            const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 second timeout for bulk

                            const response = await fetch(API_BASE_URL, {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({ serials: normalizedBase85Serials }),
                                signal: controller.signal,
                            });
                            clearTimeout(timeoutId);

                            if (response.ok) {
                                const data = await response.json();
                                // api.php returns { results: { ... } }
                                if (data.results && typeof data.results === 'object') {
                                    base85Results = data.results;
                                    apiError = null; // Success, clear any error
                                } else if (data && typeof data === 'object') {
                                    // Fallback: if results is at root level
                                    base85Results = data;
                                    apiError = null; // Success, clear any error
                                }
                            } else if (response.status === 401) {
                                // 401 means authentication required - skip to fallback silently
                                console.warn("Primary API requires authentication, trying fallback...");
                            } else {
                                const errorText = await response.text();
                                apiError = `API responded with ${response.status}: ${errorText}`;
                            }
                        } catch (error) {
                            console.warn("Primary API bulk deserialize failed:", error.message);
                            // Only set error if it's not a network/abort error
                            if (!error.message.includes('aborted') && !error.message.includes('Failed to fetch')) {
                                apiError = error.message;
                            }
                        }
                    }
                    
                    // Try fallback API if we don't have results yet and fallback is different from primary
                    const hasResults = Object.keys(base85Results).length > 0;
                    const fallbackIsDifferent = API_FALLBACK_URL !== API_BASE_URL;
                    
                    if (!hasResults && (fallbackIsDifferent || !triedPrimary)) {
                        try {
                            const controller = new AbortController();
                            const timeoutId = setTimeout(() => controller.abort(), 60000);

                            const response = await fetch(API_FALLBACK_URL, {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({ serials: normalizedBase85Serials }),
                                signal: controller.signal,
                            });
                            clearTimeout(timeoutId);

                            if (response.ok) {
                                const data = await response.json();
                                if (data.results && typeof data.results === 'object') {
                                    base85Results = data.results;
                                    apiError = null; // Success, clear error
                                } else if (data && typeof data === 'object') {
                                    base85Results = data;
                                    apiError = null; // Success, clear error
                                }
                            } else if (response.status === 401) {
                                // Fallback also requires auth - show user-friendly message
                                apiError = 'API requires authentication. Please use a local server or ensure API credentials are configured.';
                            } else {
                                const errorText = await response.text();
                                apiError = `Fallback API responded with ${response.status}: ${errorText}`;
                            }
                        } catch (fallbackError) {
                            if (!apiError) {
                                apiError = `Both APIs failed. Last error: ${fallbackError.message}`;
                            }
                        }
                    }
                }

                // Process results and build output in original order
                const decoded = [];
                for (let i = 0; i < parsedSerials.length; i++) {
                    const serial = parsedSerials[i];
                    const serialInfo = serialIndexMap.get(serial);
                    
                    if (serialInfo.type === 'decoded') {
                        // Already decoded, just use it
                        decoded.push(serial);
                    } else if (serialInfo.type === 'base85') {
                        // Look up deserialized result
                        const normalizedSerial = serial.startsWith('@') ? serial : `@${serial}`;
                        const result = base85Results[normalizedSerial] || base85Results[serial] || base85Results[serial.replace('@', '')];
                        
                        if (result && result.success && result.deserialized) {
                            decoded.push(result.deserialized);
                        } else if (result && result.error) {
                            decoded.push(`#${i + 1} ERROR: ${result.error}`);
                        } else {
                            decoded.push(`#${i + 1} ERROR: Serial not found in response${apiError ? ` (${apiError})` : ''}`);
                        }
                    } else {
                        decoded.push(`#${i + 1} ERROR: Unknown serial format`);
                    }
                }

            outputEl.value = decoded.join('\n');
            const errors = decoded.filter((entry) => entry.startsWith('#')).length;
            setBulkSerialStatus(
                errors
                    ? `Decoded with ${errors} error${errors !== 1 ? 's' : ''}. Check the output for details.`
                        : `Successfully decoded ${parsedSerials.length} serial${parsedSerials.length !== 1 ? 's' : ''}.`,
                errors ? 'error' : 'success'
            );
            } catch (error) {
                setBulkSerialStatus(
                    `Failed to decode serials: ${error.message}`,
                    'error'
                );
                outputEl.value = `# ERROR: ${error.message}`;
            }
        };

        // Bulk Serialize Serials
        window.bulkSerializeSerials = async function bulkSerializeSerials() {
            const inputEl = document.getElementById('bulk-serial-input');
            const outputEl = document.getElementById('bulk-serial-output');
            if (!inputEl || !outputEl) return;

            // Parse input to extract serials from multiple formats
            const parsedSerials = parseBulkInput(inputEl.value);
            if (!parsedSerials.length) {
                setBulkSerialStatus(
                    'No valid serials found. Supports: Base85 (@Ug...), decoded format (259, 0, 1, 50|...), YAML format, or JavaScript object format.',
                    'error'
                );
                return;
            }

            setBulkSerialStatus(
                `Encoding ${parsedSerials.length} item${parsedSerials.length !== 1 ? 's' : ''}...`,
                'info'
            );

            try {
                const API_BASE_URL = nicnlApiBase();
                const API_FALLBACK_URL = nicnlApiFallback();
                // Separate Base85 serials (already serialized) and decoded serials (need serialization)
                const base85Serials = [];
                const decodedSerials = [];
                const serialIndexMap = new Map(); // Map to track original order

                parsedSerials.forEach((serial, index) => {
                    if (serial.startsWith('@Ug')) {
                        base85Serials.push(serial);
                        serialIndexMap.set(serial, { type: 'base85', index });
                    } else if (/^\d+,\s*\d+,\s*\d+,\s*\d+\|/.test(serial)) {
                        decodedSerials.push(serial);
                        serialIndexMap.set(serial, { type: 'decoded', index });
                    }
                });

                // Normalize decoded serials (ensure trailing pipe) for serialization
                const normalizedDecodedStrings = decodedSerials.map(line => ensureTrailingPipe(line));

                // Serialize decoded strings via API
                let serializedDecoded = [];
                let apiError = null;
                
                if (normalizedDecodedStrings.length > 0) {
                    // Try local API first (api.php - no API key required)
                    try {
                        const controller = new AbortController();
                        const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 second timeout for bulk

                        const response = await fetch(API_BASE_URL, {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ deserialized_strings: normalizedDecodedStrings }),
                            signal: controller.signal,
                        });
                        clearTimeout(timeoutId);

                        if (response.ok) {
                            const data = await response.json();
                            // api.php returns an array of serials for bulk serialize
                            if (Array.isArray(data)) {
                                serializedDecoded = data;
                                apiError = null; // Success
                            } else {
                                apiError = 'Local API returned invalid format (expected array)';
                                throw new Error(apiError); // Trigger fallback
                            }
                        } else {
                            const errorText = await response.text();
                            apiError = `Local API responded with ${response.status}: ${errorText}`;
                            throw new Error(apiError); // Trigger fallback
                        }
                    } catch (error) {
                        console.warn("Local API bulk serialize failed:", error.message);
                        apiError = error.message;
                        
                        // Try fallback API (also doesn't require API key)
                        try {
                            const controller = new AbortController();
                            const timeoutId = setTimeout(() => controller.abort(), 60000);

                            const response = await fetch(API_FALLBACK_URL, {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({ deserialized_strings: normalizedDecodedStrings }),
                                signal: controller.signal,
                            });
                            clearTimeout(timeoutId);

                            if (response.ok) {
                                const data = await response.json();
                                if (Array.isArray(data)) {
                                    serializedDecoded = data;
                                    apiError = null; // Success
                                } else {
                                    apiError = 'Fallback API returned invalid format (expected array)';
                                }
                            } else {
                                const errorText = await response.text();
                                apiError = `Fallback API responded with ${response.status}: ${errorText}`;
                            }
                        } catch (fallbackError) {
                            apiError = `Both APIs failed. Last error: ${fallbackError.message}`;
                        }
                    }
                }

                // Process results and build output in original order
                const output = [];
                let decodedIndex = 0;
                
                for (let i = 0; i < parsedSerials.length; i++) {
                    const serial = parsedSerials[i];
                    const serialInfo = serialIndexMap.get(serial);
                    
                    if (serialInfo.type === 'base85') {
                        // Already serialized, just pass through
                        output.push(serial);
                    } else if (serialInfo.type === 'decoded') {
                        // Use serialized result
                        if (serializedDecoded[decodedIndex] && serializedDecoded[decodedIndex].trim()) {
                            output.push(serializedDecoded[decodedIndex]);
                        } else {
                            output.push(`#${i + 1} ERROR: Serialization failed${apiError ? ` (${apiError})` : ''}`);
                        }
                        decodedIndex++;
                    } else {
                        output.push(`#${i + 1} ERROR: Unknown serial format`);
                    }
                }

                outputEl.value = output.join('\n');
                const errors = output.filter((entry) => entry.startsWith('#')).length;
            setBulkSerialStatus(
                errors
                    ? `Encoded with ${errors} error${errors !== 1 ? 's' : ''}. Check the output for details.`
                    : `Successfully encoded ${output.length} item${output.length !== 1 ? 's' : ''}.`,
                errors ? 'error' : 'success'
            );
            } catch (error) {
                setBulkSerialStatus(
                    `Failed to encode serials: ${error.message}`,
                    'error'
                );
                outputEl.value = `# ERROR: ${error.message}`;
            }
        };

        // Copy Bulk Serial Output
        window.copyBulkSerialOutput = function copyBulkSerialOutput() {
            const outputEl = document.getElementById('bulk-serial-output');
            if (!outputEl) return;

            const text = outputEl.value.trim();
            if (!text) {
                setBulkSerialStatus(
                    'Nothing to copy yet — run Deserialize or Serialize first.',
                    'error'
                );
                return;
            }

            navigator.clipboard
                .writeText(text)
                .then(() =>
                    setBulkSerialStatus('Output copied to clipboard.', 'success')
                )
                .catch((err) =>
                    setBulkSerialStatus(
                        `Failed to copy: ${err?.message || err}`,
                        'error'
                    )
                );
        };

        // Clear Bulk Serial Fields
        window.clearBulkSerialFields = function clearBulkSerialFields() {
            const inputEl = document.getElementById('bulk-serial-input');
            const outputEl = document.getElementById('bulk-serial-output');
            if (inputEl) inputEl.value = '';
            if (outputEl) outputEl.value = '';
            setBulkSerialStatus('Cleared input and output.', 'info');
        };

        // Trigger Bulk Serial File Input
        window.triggerBulkSerialFile = function triggerBulkSerialFile() {
            const fileInput = document.getElementById('bulk-serial-file');
            if (fileInput) {
                fileInput.value = '';
                fileInput.click();
            }
        };

        // Handle bulk serial file input
        document.addEventListener('change', (event) => {
            const { target } = event;
            if (
                target &&
                target.id === 'bulk-serial-file' &&
                target.files &&
                target.files.length > 0
            ) {
                const file = target.files[0];
                const reader = new FileReader();
                reader.onload = (e) => {
                    const inputEl = document.getElementById('bulk-serial-input');
                    if (inputEl) {
                        inputEl.value = e.target.result;
                    }
                };
                reader.readAsText(file);
            }
        });

        // Random Item Generator Functions
        window.showRandomItemModal = function() {
            const modal = document.getElementById('randomItemModal');
            if (!modal) return;
            
            // Populate item type dropdown
            const select = document.getElementById('randomItemTypeSelect');
            if (!select) return;
            
            // Add "Random" option as default
            select.innerHTML = '<option value="random">🎲 Random (All Types)</option>';
            
            // Get all item type IDs (include all categories: weapons, shields, grenades, class mods, enhancements, repkits, etc.)
            // Filter out substat categories (1, 234, 243, 244, 245, 246, 247, 248) and special categories as they're not base items
            // TypeID 1 is for weapon elements (parts only), not a base item type
            // TypeID 244 is for heavy weapon firmware (parts only), not a base item type
            const excludedTypeIds = new Set([1, 234, 243, 244, 245, 246, 247, 237, 248]); // Substats and special categories (1 = Weapon Elements - parts only, 244 = Heavy Weapon Firmware - parts only)
            const allItemTypes = Array.from(typeIdMap.entries())
                .filter(([id, info]) => {
                    // Convert id to number to ensure proper comparison
                    const typeIdNum = typeof id === 'number' ? id : parseInt(id, 10);
                    return !excludedTypeIds.has(typeIdNum);
                })
                .map(([id, info]) => ({
                    id: id,
                    name: info.name || `Type ${id}`,
                    manufacturer: info.manufacturer || 'Unknown',
                    category: info.category || 'Item'
                }))
                .sort((a, b) => {
                    // Sort by category first, then manufacturer, then name
                    if (a.category !== b.category) {
                        return a.category.localeCompare(b.category);
                    }
                    if (a.manufacturer !== b.manufacturer) {
                        return a.manufacturer.localeCompare(b.manufacturer);
                    }
                    return a.name.localeCompare(b.name);
                });
            
            // Store all valid typeIds for random selection (used when "random" is selected)
            window.validRandomTypeIds = allItemTypes.map(t => t.id);
            
            // Setup quantity change handler and save file check
            const quantityInput = document.getElementById('randomItemQuantity');
            
            if (quantityInput) {
                quantityInput.addEventListener('input', updateRandomItemModalButtonStates);
                quantityInput.addEventListener('change', updateRandomItemModalButtonStates);
            }
            updateRandomItemModalButtonStates(); // Initial state
            
            
            // Group by category for better organization
            // Known grenade/ordnance typeIds that should NEVER be in Repkits category
            const grenadeTypeIds = new Set([263, 267, 270, 272, 278, 291, 298, 311]);
            const repkitTypeIds = new Set([261, 265, 266, 269, 274, 277, 285, 290]);
            
            const groupedByCategory = {};
            allItemTypes.forEach(type => {
                let category = type.category;
                const typeIdNum = typeof type.id === 'number' ? type.id : parseInt(type.id, 10);
                
                // Force correct category for grenade typeIds
                if (grenadeTypeIds.has(typeIdNum)) {
                    category = 'Grenades';
                    // Also update the type object to fix it
                    type.category = 'Grenades';
                } else if (repkitTypeIds.has(typeIdNum) && category !== 'Repkits') {
                    category = 'Repkits';
                    type.category = 'Repkits';
                }
                
                if (!groupedByCategory[category]) {
                    groupedByCategory[category] = [];
                }
                groupedByCategory[category].push(type);
            });
            
            // Add optgroups for each category
            Object.keys(groupedByCategory).sort().forEach(category => {
                const optgroup = document.createElement('optgroup');
                optgroup.label = category;
                groupedByCategory[category].forEach(type => {
                    const option = document.createElement('option');
                    option.value = type.id;
                    // For class mods, don't duplicate the character name (manufacturer is already in name)
                    let displayText;
                    if (type.category === 'Class Mod' && type.manufacturer && type.name) {
                        // If name already contains the manufacturer, just use the name
                        const manufacturerLower = type.manufacturer.toLowerCase();
                        const nameLower = type.name.toLowerCase();
                        if (nameLower.includes(manufacturerLower)) {
                            displayText = `${type.id} - ${type.name}`;
                        } else {
                            displayText = `${type.id} - ${type.manufacturer} ${type.name}`;
                        }
                    } else {
                        displayText = `${type.id} - ${type.manufacturer} ${type.name}`;
                    }
                    option.textContent = displayText;
                    optgroup.appendChild(option);
                });
                select.appendChild(optgroup);
            });
            
            // Reset progress bar and re-enable buttons when modal opens
            const progressContainer = document.getElementById('randomItemProgressContainer');
            const progressBar = document.getElementById('randomItemProgressBar');
            const progressText = document.getElementById('randomItemProgressText');
            const progressCount = document.getElementById('randomItemProgressCount');
            const generateAndParseBtn = document.getElementById('generateAndParseBtn');
            const generateAndAddBtn = document.getElementById('generateAndAddBtn');
            const cancelBtn = document.getElementById('randomItemCancelBtn');
            
            if (progressContainer) {
                progressContainer.style.display = 'none';
            }
            if (progressBar) {
                progressBar.style.width = '0%';
            }
            if (progressText) {
                progressText.textContent = 'Generating items...';
            }
            if (progressCount) {
                progressCount.textContent = '0 / 0';
            }
            if (generateAndParseBtn) generateAndParseBtn.disabled = false;
            if (generateAndAddBtn) generateAndAddBtn.disabled = false;
            if (cancelBtn) cancelBtn.disabled = false;
            
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        };
        
        // Function to update random item modal button states (can be called externally)
        window.updateRandomItemModalButtonStates = function() {
            const quantityInput = document.getElementById('randomItemQuantity');
            const generateAndParseBtn = document.getElementById('generateAndParseBtn');
            const generateAndAddBtn = document.getElementById('generateAndAddBtn');
            const saveFileNote = document.getElementById('randomItemSaveFileNote');
            const typeSelect = document.getElementById('randomItemTypeSelect');
            
            if (!quantityInput) return; // Modal not initialized yet
            
            const quantity = parseInt(quantityInput.value) || 1;
            const isSaveLoaded = window.saveEditorState && window.saveEditorState.isLoaded;
            const isRandomType = typeSelect && typeSelect.value === 'random';
            
            // Update "Generate and Parse" button based on quantity
            if (generateAndParseBtn) {
                if (quantity > 1) {
                    generateAndParseBtn.disabled = true;
                    generateAndParseBtn.title = 'Generate and Parse only supports 1 item at a time. Use "Generate and Add to Backpack" for multiple items.';
                    generateAndParseBtn.style.opacity = '0.6';
                    generateAndParseBtn.style.cursor = 'not-allowed';
                } else {
                    generateAndParseBtn.disabled = false;
                    generateAndParseBtn.title = '';
                    generateAndParseBtn.style.opacity = '1';
                    generateAndParseBtn.style.cursor = 'pointer';
                }
            }
            
            // Update "Generate and Add to Backpack" button based on save file
            if (generateAndAddBtn) {
                if (!isSaveLoaded) {
                    // Change button to "Load Save" when no save is loaded
                    generateAndAddBtn.disabled = false;
                    generateAndAddBtn.innerHTML = '<span>💾</span> Load Save';
                    generateAndAddBtn.onclick = function() {
                        hideRandomItemModal();
                        switchTab('save-editor-tab');
                    };
                    generateAndAddBtn.title = 'Click to go to Save Editor and load a save file';
                    generateAndAddBtn.style.opacity = '1';
                    generateAndAddBtn.style.cursor = 'pointer';
                    generateAndAddBtn.style.background = 'linear-gradient(135deg, #ff9800, #f57c00)';
                } else {
                    // Restore original "Generate and Add to Backpack" functionality
                    generateAndAddBtn.innerHTML = '<span>📦</span> Generate and Add to Backpack';
                    generateAndAddBtn.onclick = function() {
                        generateRandomItemAndAddToBackpack();
                    };
                    generateAndAddBtn.title = '';
                    generateAndAddBtn.style.opacity = '1';
                    generateAndAddBtn.style.cursor = 'pointer';
                    generateAndAddBtn.style.background = 'linear-gradient(135deg, #2196f3, #1976d2)';
                }
            }
            
            // Update notification message
            if (saveFileNote) {
                if (quantity > 1) {
                    if (!isSaveLoaded) {
                        saveFileNote.style.display = 'block';
                        saveFileNote.innerHTML = '⚠️ <strong>Note:</strong> When generating multiple items, you can only add them to backpack. Click "Load Save" to go to the Save Editor and load a save file first.';
                        saveFileNote.style.background = 'rgba(255, 152, 0, 0.2)';
                        saveFileNote.style.borderColor = 'rgba(255, 152, 0, 0.5)';
                        saveFileNote.style.color = '#ffa500';
                    } else {
                        saveFileNote.style.display = 'block';
                        saveFileNote.innerHTML = 'ℹ️ <strong>Note:</strong> When generating multiple items, you can only add them to backpack (not parse).';
                        saveFileNote.style.background = 'rgba(79, 195, 247, 0.2)';
                        saveFileNote.style.borderColor = 'rgba(79, 195, 247, 0.5)';
                        saveFileNote.style.color = '#4fc3f7';
                    }
                } else {
                    if (!isSaveLoaded) {
                        saveFileNote.style.display = 'block';
                        saveFileNote.innerHTML = 'ℹ️ <strong>Note:</strong> Click "Load Save" to go to the Save Editor and load a save file to use "Generate and Add to Backpack".';
                        saveFileNote.style.background = 'rgba(79, 195, 247, 0.2)';
                        saveFileNote.style.borderColor = 'rgba(79, 195, 247, 0.5)';
                        saveFileNote.style.color = '#4fc3f7';
                    } else {
                        saveFileNote.style.display = 'none';
                    }
                }
            }
        };

        window.hideRandomItemModal = function() {
            const modal = document.getElementById('randomItemModal');
            if (modal) {
                modal.classList.remove('active');
                document.body.style.overflow = '';
            }
        };

        window.generateRandomItem = function() {
            const select = document.getElementById('randomItemTypeSelect');
            if (!select || !select.value) {
                alert('Please select an item type first!');
                return;
            }
            
            // Handle "random" selection - pick a random typeId
            let typeId = null;
            if (select.value === 'random') {
                let validTypeIds = window.validRandomTypeIds || [];
                
                if (validTypeIds.length === 0) {
                    alert('No valid item types available for random selection!');
                    return;
                }
                typeId = validTypeIds[Math.floor(Math.random() * validTypeIds.length)];
            } else {
                typeId = parseInt(select.value);
            }
            
            if (!typeId || !partsByTypeId.has(typeId)) {
                alert('Invalid item type selected!');
                return;
            }
            
            // Get item category to determine which part categories to use
            let typeInfo = typeIdMap.get(typeId);
            const itemCategory = (typeInfo?.category || '').toLowerCase();
            const isHeavyWeapon = itemCategory.includes('heavy weapon') || itemCategory.includes('heavy');
            const isWeapon = itemCategory.includes('weapon') && !isHeavyWeapon;
            const isShield = itemCategory.includes('shield');
            const isGrenade = itemCategory.includes('grenade');
            const isClassMod = itemCategory.includes('class mod') || typeId >= 254 && typeId <= 259;
            const isEnhancement = itemCategory.includes('enhancement');
            const isRepkit = itemCategory.includes('repkit') || itemCategory.includes('rep kit');
            
            // Unified part collection system - get parts from ALL relevant sources
            const allPartsMap = new Map(); // Use Map to avoid duplicates
            
            // 1. Parts from the item's own typeId
            const ownParts = partsByTypeId.get(typeId) || [];
            ownParts.forEach(p => {
                const key = `${p.typeId || typeId}:${p.id || p.fullId || ''}`;
                if (!allPartsMap.has(key)) allPartsMap.set(key, p);
            });
            
            // 2. Cross-typeId parts that may be needed
            const crossTypeIds = [];
            if (isEnhancement) crossTypeIds.push(247); // Base body, stats, firmware
            if (isRepkit) crossTypeIds.push(243); // Parts, firmware
            if (isGrenade) crossTypeIds.push(245); // Parts, firmware
            if (isClassMod) crossTypeIds.push(234); // Perks, firmware
            if (isHeavyWeapon) crossTypeIds.push(244); // Firmware
            if (isShield) {
                crossTypeIds.push(246); // Perks and Firmware (universal for all shields)
                crossTypeIds.push(237); // Armor Shield parts
                crossTypeIds.push(248); // Energy Shield parts
            }
            
            // Add cross-typeId parts
            crossTypeIds.forEach(crossTypeId => {
                if (partsByTypeId.has(crossTypeId)) {
                    const crossParts = partsByTypeId.get(crossTypeId) || [];
                    crossParts.forEach(p => {
                        const key = `${p.typeId || crossTypeId}:${p.id || p.fullId || ''}`;
                        if (!allPartsMap.has(key)) allPartsMap.set(key, p);
                    });
                }
            });
            
            // Convert map back to array
            const allParts = Array.from(allPartsMap.values());
            
            // Group parts by category (support all item types)
            const partsByCategory = {
                // Weapon parts
                body: [],
                bodyAccessory: [],
                barrel: [],
                barrelAccessory: [],
                magazine: [],
                scope: [],
                scopeAccessory: [],
                grip: [],
                foregrip: [],
                underbarrel: [],
                statModifier: [],
                // Common parts
                rarity: [],
                manufacturerPerk: [],
                // Shield parts
                shield: [],
                // Grenade parts
                base: [],
                payload: [],
                augment: [],
                // Class Mod parts
                skills: [],
                perks234: [],
                stat234: [],
                stat2_234: [],
                statspecial_234: [],
                firmware234: [],
                // Enhancement parts
                core: [],
                baseBody247: [], // Base Body 247 (parts 76-80) for enhancements
                firmware247: [],
                stat_247: [],
                stat2_247: [],
                stat3_247: [],
                // Repkit parts
                baseBody: [],
                legendaryPart: [],
                firmware243: [],
                elementalResistances243: [],
                elementalImmunities243: [],
                elementalSplats243: [],
                elementalNovas243: [],
                size243: [],
                parts243: [],
                // Heavy Weapon parts
                firmware244: [],
                // Grenade parts (typeId 245)
                firmware245: [],
                parts245: [],
                // Shield parts (typeId 246, 237, 248)
                primaryPerks246: [],
                secondaryPerks246: [],
                firmware246: [],
                armor237: [],
                energy248: []
            };
            
            // Categorize parts (handle all item types)
            allParts.forEach(partInfo => {
                const partType = String(partInfo.partType || '').toLowerCase();
                const partPath = String(partInfo.path || '').toLowerCase();
                const partName = String(partInfo.name || '').toLowerCase();
                const spawnCode = String(partInfo.spawnCode || '').toLowerCase();
                
                // Weapon parts
                if (partType === 'body' || (partType.includes('body') && !partType.includes('accessory') && !partType.includes('base'))) {
                    partsByCategory.body.push(partInfo);
                } else if (partType === 'body accessory' || (partType.includes('body') && partType.includes('accessory'))) {
                    partsByCategory.bodyAccessory.push(partInfo);
                } else if (partType === 'barrel' || (partType.includes('barrel') && !partType.includes('accessory'))) {
                    partsByCategory.barrel.push(partInfo);
                } else if (partType === 'barrel accessory' || (partType.includes('barrel') && partType.includes('accessory'))) {
                    partsByCategory.barrelAccessory.push(partInfo);
                } else if (partType === 'magazine' || partType.includes('magazine')) {
                    partsByCategory.magazine.push(partInfo);
                } else if (partType === 'scope' || (partType.includes('scope') && !partType.includes('accessory'))) {
                    partsByCategory.scope.push(partInfo);
                } else if (partType === 'scope accessory' || (partType.includes('scope') && partType.includes('accessory'))) {
                    partsByCategory.scopeAccessory.push(partInfo);
                } else if (partType === 'grip' || partType.includes('grip')) {
                    partsByCategory.grip.push(partInfo);
                } else if (partType === 'foregrip' || partType.includes('foregrip')) {
                    partsByCategory.foregrip.push(partInfo);
                } else if (partType === 'underbarrel' || partType.includes('underbarrel')) {
                    partsByCategory.underbarrel.push(partInfo);
                } else if (partType === 'stat modifier' || (partType.includes('stat') && partType.includes('modifier'))) {
                    partsByCategory.statModifier.push(partInfo);
                }
                // Shield parts (body parts from shield manufacturers, e.g., "Shield" partType)
                // These are the main body parts for shields (e.g., "Sparky", "Firebreak" for Ripper shields)
                // IMPORTANT: For shields, Base Body and Legendary Part are one and the same!
                else if (isShield && partInfo.typeId === typeId && 
                         (partType === 'shield' || spawnCode.includes('part_body') || partPath.includes('shield') || String(partInfo.partType || '') === 'Shield')) {
                    // This is a shield body part from the shield's own typeId
                    partsByCategory.shield.push(partInfo);
                    partsByCategory.baseBody.push(partInfo);
                    // For shields, Base Body = Legendary Part (they are one and the same)
                    partsByCategory.legendaryPart.push(partInfo);
                } else if (partType === 'shield' || partPath.includes('shield') || spawnCode.includes('shield')) {
                    // Other shield-related parts (perks, firmware, etc.)
                    partsByCategory.shield.push(partInfo);
                }
                // Grenade parts
                else if (partType === 'base' || partPath === 'base') {
                    if (isGrenade) {
                        partsByCategory.base.push(partInfo);
                    } else if (isRepkit) {
                        partsByCategory.baseBody.push(partInfo);
                    } else {
                        partsByCategory.body.push(partInfo);
                    }
                } else if (partType === 'payload' || partPath.includes('payload')) {
                    partsByCategory.payload.push(partInfo);
                } else if (partType === 'augment' || partPath === 'augment' || 
                           String(partType).toLowerCase() === 'augment' || 
                           String(partPath).toLowerCase() === 'augment' ||
                           String(partPath).toLowerCase().includes('augment') ||
                           String(spawnCode).toLowerCase().includes('augment')) {
                    partsByCategory.augment.push(partInfo);
                }
                // Class Mod parts
                // Class Mod body parts: body parts from class mod's own typeId (254-259)
                // These should be identified by partType === 'Body' or path containing 'Body'
                else if (isClassMod && partInfo.typeId === typeId && 
                         (partType === 'body' || String(partInfo.partType || '') === 'Body' || 
                          partPath.includes('body') || partPath.includes('Body'))) {
                    partsByCategory.body.push(partInfo);
                } else if (partType === 'skill' || spawnCode.includes('skill') || (isClassMod && partInfo.typeId === typeId && partType !== 'body' && partType !== 'Body' && partType !== 'rarity' && !partPath.includes('body') && !partPath.includes('Body') && !partPath.includes('Rarity'))) {
                    partsByCategory.skills.push(partInfo);
                } else if (partInfo.typeId === 234) {
                    if (spawnCode.includes('firmware') || partPath.includes('firmware')) {
                        partsByCategory.firmware234.push(partInfo);
                    } else {
                        if (spawnCode.includes('statspecial_') || spawnCode.includes('ClassMod.statspecial')) {
                            partsByCategory.statspecial_234.push(partInfo);
                        } else if (spawnCode.includes('stat2_') || spawnCode.includes('ClassMod.stat2')) {
                            partsByCategory.stat2_234.push(partInfo);
                        } else if (spawnCode.includes('stat_') || spawnCode.includes('ClassMod.stat') || spawnCode.includes('stat')) {
                            partsByCategory.stat234.push(partInfo);
                        } else {
                            // Fallback: if it's a perk but can't determine, default to stat
                            partsByCategory.stat234.push(partInfo);
                        }
                    }
                }
                // Enhancement parts
                else if (partType === 'core' || partPath.includes('core')) {
                    partsByCategory.core.push(partInfo);
                } else if (partInfo.typeId === 247) {
                    // Check for base body (parts 76-80) first
                    const partIdStr = String(partInfo.id || partInfo.fullId || '');
                    const partName = String(partInfo.name || '').toLowerCase();
                    let partIdNum = null;
                    if (partIdStr.includes(':')) {
                        const parts = partIdStr.split(':');
                        // Extract the last part (the actual part ID) regardless of format
                        if (parts.length >= 2) {
                            const lastPart = parts[parts.length - 1].trim();
                            partIdNum = parseInt(lastPart);
                        }
                    } else {
                        // Check if it's a simple part with value 76-80
                        partIdNum = parseInt(partIdStr);
                    }
                    
                    // Check if it's a base body part (247:76-80) by part ID OR by partType/name/path/spawnCode
                    const isBaseBodyById = partIdNum !== null && !isNaN(partIdNum) && partIdNum >= 76 && partIdNum <= 80;
                    const isBaseBodyByType = partType.includes('main body') || (partType.includes('body') && !partType.includes('accessory'));
                    const isBaseBodyByName = partName.includes('legendary') || partName.includes('epic') || partName.includes('rare') || partName.includes('uncommon') || partName.includes('common');
                    const isBaseBodyByPath = partPath.includes('main body') || partPath.includes('body_0');
                    const isBaseBodyBySpawnCode = spawnCode.includes('part_body_05') || spawnCode.includes('part_body_04') || spawnCode.includes('part_body_03') || spawnCode.includes('part_body_02') || spawnCode.includes('part_body_01');
                    
                    // Debug logging for base body parts
                    if (isEnhancement && (partIdNum >= 76 && partIdNum <= 80)) {
                        console.log(`[CATEGORIZATION DEBUG] Found potential base body part: id=${partInfo.id}, fullId=${partInfo.fullId}, partIdNum=${partIdNum}, partType=${partType}, partName=${partName}, partPath=${partPath}, spawnCode=${spawnCode}`);
                        console.log(`[CATEGORIZATION DEBUG] isBaseBodyById=${isBaseBodyById}, isBaseBodyByType=${isBaseBodyByType}, isBaseBodyByName=${isBaseBodyByName}, isBaseBodyByPath=${isBaseBodyByPath}, isBaseBodyBySpawnCode=${isBaseBodyBySpawnCode}`);
                    }
                    
                    if (isBaseBodyById || (isBaseBodyByType && isBaseBodyByName) || isBaseBodyByPath || isBaseBodyBySpawnCode) {
                        // This is a base body part (247:76-80) for enhancements
                        partsByCategory.baseBody247.push(partInfo);
                        if (isEnhancement) {
                            console.log(`[CATEGORIZATION DEBUG] Added to baseBody247: ${partInfo.fullId} (${partInfo.name})`);
                        }
                    } else if (spawnCode.includes('firmware') || partPath.includes('firmware') || partType.includes('firmware')) {
                        partsByCategory.firmware247.push(partInfo);
                    } else if (partPath.includes('stats') || partPath.includes('stats2') || partPath.includes('stats3') || partType.includes('stat') || spawnCode.includes('stat')) {
                        if (spawnCode.includes('stat3_') || partPath.includes('stat3') || partPath.includes('stats3')) {
                            partsByCategory.stat3_247.push(partInfo);
                        } else if (spawnCode.includes('stat2_') || partPath.includes('stat2') || partPath.includes('stats2')) {
                            partsByCategory.stat2_247.push(partInfo);
                        } else if (spawnCode.includes('stat_') || partPath.includes('stat') || partPath.includes('stats') || partType.includes('stat')) {
                            partsByCategory.stat_247.push(partInfo);
                        }
                    }
                }
                // Repkit parts (typeId 243)
                else if (partInfo.typeId === 243) {
                    if (spawnCode.includes('firmware') || partPath.includes('firmware')) {
                        partsByCategory.firmware243.push(partInfo);
                    } else {
                        partsByCategory.parts243.push(partInfo);
                    }
                }
                // Grenade parts (typeId 245)
                else if (partInfo.typeId === 245) {
                    if (spawnCode.includes('firmware') || partPath.includes('firmware')) {
                        partsByCategory.firmware245.push(partInfo);
                    } else {
                        partsByCategory.parts245.push(partInfo);
                    }
                }
                // Heavy Weapon firmware (typeId 244)
                else if (partInfo.typeId === 244) {
                    partsByCategory.firmware244.push(partInfo);
                }
                // Shield parts (typeId 246 - Perks and Firmware)
                else if (partInfo.typeId === 246) {
                    // Check if it's firmware or perk based on partType, partPath, or spawnCode
                    const partType = String(partInfo.partType || '').toLowerCase();
                    const partPath = String(partInfo.path || '').toLowerCase();
                    const spawnCode = String(partInfo.spawnCode || '').toLowerCase();
                    
                    if (partType.includes('firmware') || partPath.includes('firmware') || spawnCode.includes('firmware')) {
                        partsByCategory.firmware246.push(partInfo);
                    } else if (partType.includes('perk') || partPath.includes('perk') || spawnCode.includes('perk')) {
                        if (spawnCode.includes('_primary') || partPath.includes('primary') || partName.includes('primary')) {
                            partsByCategory.primaryPerks246.push(partInfo);
                        } else if (spawnCode.includes('_secondary') || partPath.includes('secondary') || partName.includes('secondary')) {
                            partsByCategory.secondaryPerks246.push(partInfo);
                        } else {
                            // If we can't determine, default to primary (fallback)
                            partsByCategory.primaryPerks246.push(partInfo);
                        }
                    } else {
                        // Default: if spawnCode contains "stat" it's likely a perk, otherwise default to primary perk
                        // (most shield parts from typeId 246 are perks)
                        if (spawnCode.includes('_primary') || partPath.includes('primary') || partName.includes('primary')) {
                            partsByCategory.primaryPerks246.push(partInfo);
                        } else if (spawnCode.includes('_secondary') || partPath.includes('secondary') || partName.includes('secondary')) {
                            partsByCategory.secondaryPerks246.push(partInfo);
                        } else {
                            partsByCategory.primaryPerks246.push(partInfo);
                        }
                    }
                }
                // Armor Shield parts (typeId 237)
                else if (partInfo.typeId === 237) {
                    partsByCategory.armor237.push(partInfo);
                }
                // Energy Shield parts (typeId 248)
                else if (partInfo.typeId === 248) {
                    partsByCategory.energy248.push(partInfo);
                }
                // Common parts (rarity, manufacturer perks)
                // For enhancements, exclude typeId 247 parts from rarity (rarity must come from enhancement's own typeId)
                if (partType.includes('rarity') || partType === 'comp' || partName.includes('rarity') || 
                    partName.includes('common') || partName.includes('uncommon') || partName.includes('rare') || 
                    partName.includes('epic') || partName.includes('legendary')) {
                    // For enhancements, only add rarity if it's from the enhancement's typeId, not 247
                    if (isEnhancement) {
                        const partTypeId = partInfo.typeId || typeId;
                        if (partTypeId === typeId && partTypeId !== 247) {
                            partsByCategory.rarity.push(partInfo);
                        }
                    } else {
                        partsByCategory.rarity.push(partInfo);
                    }
                }
                if (partType === 'manufacturer perk' || partType.includes('legendary perk')) {
                    partsByCategory.manufacturerPerk.push(partInfo);
                }
            });
            
            // Helper function to get random item from array
            const getRandomItem = (arr) => {
                if (!arr || arr.length === 0) return null;
                return arr[Math.floor(Math.random() * arr.length)];
            };
            
            // Helper function to extract part ID from partInfo
            const getPartId = (partInfo) => {
                if (!partInfo) return null;
                // Try fullId first (e.g., "13:73")
                if (partInfo.fullId) {
                    const parts = String(partInfo.fullId).split(':');
                    if (parts.length === 2) {
                        return { typeId: parseInt(parts[0]), partId: parts[1] };
                    }
                    return { typeId: typeId, partId: partInfo.fullId };
                }
                // Try id
                if (partInfo.id) {
                    const idStr = String(partInfo.id);
                    if (idStr.includes(':')) {
                        const parts = idStr.split(':');
                        return { typeId: parseInt(parts[0]), partId: parts[1] };
                    }
                    return { typeId: typeId, partId: idStr };
                }
                return null;
            };
            
            // Build random parts array
            let randomParts = [];
            
            // Helper function to check if parts exist for a category
            const categoryHasParts = (category) => {
                const categoryParts = partsByCategory[category] || [];
                if (categoryParts.length === 0) return false;
                
                // Filter to only parts for this typeId (unless it's a cross-typeId category)
                const crossTypeIdCategories = ['firmware243', 'parts243', 'firmware245', 'parts245', 
                                               'firmware247', 'stat_247', 'stat2_247', 'stat3_247', 'baseBody247', 'stat234', 'stat2_234', 'statspecial_234', 
                                               'firmware234', 'primaryPerks246', 'secondaryPerks246', 'firmware246', 'armor237', 
                                               'energy248', 'skills', 'firmware244'];
                if (!crossTypeIdCategories.includes(category)) {
                    const filtered = categoryParts.filter(p => {
                        const partTypeId = p.typeId || typeId;
                        return partTypeId === typeId;
                    });
                    return filtered.length > 0;
                }
                return true;
            };
            
            // Define required vs optional categories based on item type and guidelines
            // Only include categories that actually have parts available
            let requiredCategories = [];
            let optionalCategories = [];
            
            if (isWeapon) {
                // Weapons: ALL parts shown in guidelines are required (only if they exist)
                const weaponRequired = ['rarity', 'body', 'bodyAccessory', 'barrel', 'barrelAccessory', 
                                    'magazine', 'scope', 'scopeAccessory', 'grip', 'foregrip', 
                                    'underbarrel', 'statModifier'];
                requiredCategories = weaponRequired.filter(cat => categoryHasParts(cat));
                optionalCategories = ['manufacturerPerk'];
            } else if (isHeavyWeapon) {
                // Heavy Weapons: All parts shown in guidelines are required (only if they exist)
                const heavyRequired = ['rarity', 'body', 'bodyAccessory', 'barrel', 'barrelAccessory', 'firmware244'];
                requiredCategories = heavyRequired.filter(cat => categoryHasParts(cat));
                optionalCategories = [];
            } else if (isShield) {
                // Shields: Required parts are rarity, baseBody, primaryPerks246, secondaryPerks246, firmware246 (only if they exist)
                const shieldRequired = ['rarity', 'baseBody', 'primaryPerks246', 'secondaryPerks246', 'firmware246'];
                requiredCategories = shieldRequired.filter(cat => categoryHasParts(cat));
                optionalCategories = ['legendaryPart'];
            } else if (isGrenade) {
                // Grenades: All parts shown in guidelines are required (only if they exist)
                const grenadeRequired = ['rarity', 'body', 'parts245', 'firmware245'];
                requiredCategories = grenadeRequired.filter(cat => categoryHasParts(cat));
                optionalCategories = ['payload', 'augment'];
            } else if (isClassMod) {
                // Class Mods: All parts shown in guidelines are required (only if they exist)
                const classModRequired = ['rarity', 'body', 'skills', 'stat234', 'stat2_234', 'statspecial_234', 'firmware234'];
                requiredCategories = classModRequired.filter(cat => categoryHasParts(cat));
                optionalCategories = [];
            } else if (isEnhancement) {
                // Enhancements: All parts shown in guidelines are required (only if they exist)
                const enhancementRequired = ['rarity', 'baseBody', 'legendaryPerks', 'stat_247', 'stat2_247', 'stat3_247', 'firmware247'];
                requiredCategories = enhancementRequired.filter(cat => categoryHasParts(cat));
                optionalCategories = [];
            } else if (isRepkit) {
                // Repkits: All parts shown in guidelines are required (only if they exist)
                const repkitRequired = ['rarity', 'baseBody', 'elementalResistances243', 'elementalImmunities243', 'elementalSplats243', 'elementalNovas243', 'size243', 'elemental243', 'parts243', 'firmware243'];
                requiredCategories = repkitRequired.filter(cat => categoryHasParts(cat));
                optionalCategories = ['legendaryPart'];
            } else {
                // Fallback: try all categories, prioritize rarity (only if they exist)
                const fallbackRequired = ['rarity'];
                requiredCategories = fallbackRequired.filter(cat => categoryHasParts(cat));
                const fallbackOptional = ['body', 'bodyAccessory', 'barrel', 'barrelAccessory', 'magazine', 
                                    'scope', 'scopeAccessory', 'grip', 'foregrip', 'underbarrel', 
                                    'statModifier', 'manufacturerPerk', 'shield', 'base', 
                                    'payload', 'augment', 'core', 'skills', 'stat234', 'stat2_234', 'statspecial_234', 'firmware234',
                                    'firmware247', 'stat_247', 'stat2_247', 'stat3_247', 'baseBody', 'legendaryPart', 'firmware243', 'parts243'];
                optionalCategories = fallbackOptional.filter(cat => categoryHasParts(cat));
            }
            
            // Helper function to check if a part matches a category (matches guidelines checklist logic)
            const partMatchesCategory = (part, partInfo, category) => {
                if (!partInfo) return false;
                
                const partType = String(partInfo.partType || '').toLowerCase();
                const partPath = String(partInfo.path || '').toLowerCase();
                const partName = String(partInfo.name || '').toLowerCase();
                const spawnCode = String(partInfo.spawnCode || '').toLowerCase();
                const partTypeId = partInfo.typeId || typeId;
                
                // Handle typed parts with specific typeIds
                if (part.type === 'typed' || part.type === 'array') {
                    if (category === 'firmware244' && part.typeId === 244) return true;
                    // Firmware 243: Check for firmware - primarily by partType field, then by spawnCode/path/name/Skillcraft ID
                    if (category === 'firmware243' && part.typeId === 243) {
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
                        return isFirmware;
                    }
                    if (category === 'firmware245' && part.typeId === 245 && 
                        (partType.includes('firmware') || partName.includes('firmware') || partPath.includes('firmware') || spawnCode.includes('firmware'))) return true;
                    if (category === 'firmware247' && part.typeId === 247 && 
                        (partType.includes('firmware') || partName.includes('firmware') || partPath.includes('firmware'))) return true;
                    if (category === 'firmware234' && part.typeId === 234 && 
                        (partType.includes('firmware') || partName.includes('firmware') || partPath.includes('firmware') || spawnCode.includes('firmware'))) return true;
                    if (category === 'firmware246' && part.typeId === 246 && 
                        (partType.includes('firmware') || partName.includes('firmware') || partPath.includes('firmware'))) return true;
                    // Elemental Resistances 243: Parts with Resistance type
                    if (category === 'elementalResistances243' && part.typeId === 243) {
                        const originalPartType = String(partInfo.partType || '');
                        const spawnCode = String(partInfo.spawnCode || '').toLowerCase();
                        return originalPartType === 'Resistance' || spawnCode.includes('elemental_resist') || spawnCode.includes('resist');
                    }
                    // Elemental Immunities 243: Parts with Immunity type
                    if (category === 'elementalImmunities243' && part.typeId === 243) {
                        const originalPartType = String(partInfo.partType || '');
                        const spawnCode = String(partInfo.spawnCode || '').toLowerCase();
                        return originalPartType === 'Immunity' || spawnCode.includes('immunity');
                    }
                    // Elemental Splats 243: Parts with Splat type or IDs 32-36
                    if (category === 'elementalSplats243' && part.typeId === 243) {
                        const originalPartType = String(partInfo.partType || '');
                        const spawnCode = String(partInfo.spawnCode || '').toLowerCase();
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
                        return originalPartType === 'Splat' || spawnCode.includes('splat') || (partIdNum >= 32 && partIdNum <= 36);
                    }
                    // Elemental Novas 243: Parts with Nova type or IDs 37-41
                    if (category === 'elementalNovas243' && part.typeId === 243) {
                        const originalPartType = String(partInfo.partType || '');
                        const spawnCode = String(partInfo.spawnCode || '').toLowerCase();
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
                        return originalPartType === 'Nova' || spawnCode.includes('nova') || (partIdNum >= 37 && partIdNum <= 41);
                    }
                    // Size 243: Parts with Size type or IDs 103-106
                    if (category === 'size243' && part.typeId === 243) {
                        const originalPartType = String(partInfo.partType || '');
                        const spawnCode = String(partInfo.spawnCode || '').toLowerCase();
                        const partString = String(partInfo.string || '').toLowerCase();
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
                        return originalPartType === 'Size' || spawnCode.includes('payload') || partString.includes('payload') || (partIdNum >= 103 && partIdNum <= 106);
                    }
                    // Elemental 243: Parts with Elemental type or IDs 98-102
                    if (category === 'elemental243' && part.typeId === 243) {
                        const originalPartType = String(partInfo.partType || '');
                        const spawnCode = String(partInfo.spawnCode || '').toLowerCase();
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
                        return originalPartType === 'Elemental' || spawnCode.includes('part_element') || (partIdNum >= 98 && partIdNum <= 102);
                    }
                    // Parts 243: Exclude firmware and subcategories - only show remaining parts
                    if (category === 'parts243' && part.typeId === 243) {
                        const originalPartType = String(partInfo.partType || '');
                        const partIdStr = String(partInfo.id || partInfo.fullId || '');
                        const spawnCode = String(partInfo.spawnCode || '').toLowerCase();
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
                        // Check if it's one of the subcategories
                        const isResistance = originalPartType === 'Resistance' || spawnCode.includes('elemental_resist') || spawnCode.includes('resist');
                        const isImmunity = originalPartType === 'Immunity' || spawnCode.includes('immunity');
                        const isSplat = originalPartType === 'Splat' || spawnCode.includes('splat') || (partIdNum >= 32 && partIdNum <= 36);
                        const isNova = originalPartType === 'Nova' || spawnCode.includes('nova') || (partIdNum >= 37 && partIdNum <= 41);
                        const isSize = originalPartType === 'Size' || spawnCode.includes('payload') || (partIdNum >= 103 && partIdNum <= 106);
                        const isElemental = originalPartType === 'Elemental' || spawnCode.includes('part_element') || (partIdNum >= 98 && partIdNum <= 102);
                        // Only return true if it's NOT firmware and NOT one of the subcategories
                        return !isFirmware && !isResistance && !isImmunity && !isSplat && !isNova && !isSize && !isElemental;
                    }
                    if (category === 'parts245' && part.typeId === 245 && 
                        !(partType.includes('firmware') || partName.includes('firmware') || partPath.includes('firmware') || spawnCode.includes('firmware'))) return true;
                    if ((category === 'stat_247' || category === 'stat2_247' || category === 'stat3_247') && part.typeId === 247) {
                        const spawnCode = String(part.spawnCode || '').toLowerCase();
                        if (category === 'stat3_247' && (spawnCode.includes('stat3_') || partPath.includes('stat3') || partPath.includes('stats3'))) return true;
                        if (category === 'stat2_247' && (spawnCode.includes('stat2_') || partPath.includes('stat2') || partPath.includes('stats2'))) return true;
                        if (category === 'stat_247' && (spawnCode.includes('stat_') || partPath.includes('stat') || partPath.includes('stats') || partType.includes('stat') || partName.includes('stat'))) return true;
                    }
                    if ((category === 'stat234' || category === 'stat2_234' || category === 'statspecial_234') && part.typeId === 234) {
                        // Check if it matches the category - be more permissive for stat234
                        if (partType.includes('perk') || partName.includes('perk') || spawnCode.includes('stat') || spawnCode.includes('ClassMod')) {
                            if (category === 'statspecial_234' && (spawnCode.includes('statspecial_') || spawnCode.includes('ClassMod.statspecial'))) return true;
                            if (category === 'stat2_234' && (spawnCode.includes('stat2_') || spawnCode.includes('ClassMod.stat2'))) return true;
                            if (category === 'stat234') {
                                // For stat234, check for stat_ pattern OR ClassMod.stat pattern OR just 'stat' (but not stat2_ or statspecial_)
                                const hasStat_ = spawnCode.includes('stat_') || spawnCode.includes('ClassMod.stat');
                                const hasStat2 = spawnCode.includes('stat2_') || spawnCode.includes('ClassMod.stat2');
                                const hasStatspecial = spawnCode.includes('statspecial_') || spawnCode.includes('ClassMod.statspecial');
                                // Match if it has stat_ or ClassMod.stat, but NOT if it has stat2_ or statspecial_ (those go to other categories)
                                if (hasStat_ && !hasStat2 && !hasStatspecial) return true;
                                // Also match if it just has 'stat' and is typeId 234 (fallback)
                                if (spawnCode.includes('stat') && !hasStat2 && !hasStatspecial) return true;
                                // Final fallback: if it's a perk and typeId 234, default to stat234
                                if ((partType.includes('perk') || partName.includes('perk')) && !hasStat2 && !hasStatspecial) return true;
                            }
                        }
                    }
                    if ((category === 'primaryPerks246' || category === 'secondaryPerks246') && part.typeId === 246) {
                        const spawnCode = String(part.spawnCode || '').toLowerCase();
                        const partPath = String(part.path || '').toLowerCase();
                        const partName = String(part.name || '').toLowerCase();
                        if (category === 'primaryPerks246' && (spawnCode.includes('_primary') || partPath.includes('primary') || partName.includes('primary'))) return true;
                        if (category === 'secondaryPerks246' && (spawnCode.includes('_secondary') || partPath.includes('secondary') || partName.includes('secondary'))) return true;
                        // Fallback: if it's a perk but can't determine, default to primary
                        if (category === 'primaryPerks246' && (partType.includes('perk') || partName.includes('perk'))) return true;
                    }
                    if (category === 'armor237' && part.typeId === 237) return true;
                    if (category === 'energy248' && part.typeId === 248) return true;
                    if (category === 'skills' && (part.typeId === 254 || part.typeId === 255 || part.typeId === 256 || part.typeId === 259)) {
                        // Skills should NOT be body or rarity parts - check partInfo to exclude them
                        const partInfoPartType = String(partInfo?.partType || '').toLowerCase();
                        const partInfoPath = String(partInfo?.path || '').toLowerCase();
                        const partInfoSpawnCode = String(partInfo?.spawnCode || '').toLowerCase();
                        const partInfoOriginalPartType = String(partInfo?.partType || '');
                        const isBodyPart = partInfoPartType === 'body' || partInfoPartType.includes('body') || 
                                          partInfoPath.includes('body') || partInfoPath.includes('Body') ||
                                          partInfoSpawnCode.includes('body') || partInfoSpawnCode.includes('Body') ||
                                          partInfoOriginalPartType === 'Body' || partInfoOriginalPartType.includes('Body');
                        const isRarityPart = partInfoPartType === 'rarity' || partInfoPartType === 'comp' || partInfoPartType.includes('rarity') ||
                                            partInfoPath.includes('rarity') || partInfoPath.includes('rarities') ||
                                            partInfoSpawnCode.includes('rarity') || partInfoSpawnCode.includes('comp_') ||
                                            partInfoOriginalPartType === 'Rarity' || partInfoOriginalPartType.includes('Rarity') ||
                                            partInfo?.rarity; // Has explicit rarity field
                        return !isBodyPart && !isRarityPart; // Return true if it's NOT a body part AND NOT a rarity part
                    }
                }
                
                // Handle category-specific matching
                if (category === 'rarity' || category === 'rarities') {
                    return partType.includes('rarity') || partType === 'comp' || 
                           partName.includes('rarity') || partName.includes('common') || 
                           partName.includes('uncommon') || partName.includes('rare') || 
                           partName.includes('epic') || partName.includes('legendary') ||
                           partPath.includes('rarity') || partPath.includes('comp');
                }
                if (category === 'body') {
                    // For class mods, check if it's a body part from the class mod's own typeId
                    if (isClassMod && partInfo.typeId === typeId) {
                        return (partType === 'body' || partType === 'Body' || 
                                String(partInfo.partType || '') === 'Body' ||
                                partPath.includes('body') || partPath.includes('Body')) &&
                               !partType.includes('accessory') && !partType.includes('base');
                    }
                    // For other item types, use standard body check
                    return (partType === 'body' || partType.includes('body')) && 
                           !partType.includes('accessory') && !partType.includes('base');
                }
                if (category === 'bodyAccessory' || category === 'bodyAccessories') {
                    return partType === 'body accessory' || (partType.includes('body') && partType.includes('accessory'));
                }
                if (category === 'barrel') {
                    return partType === 'barrel' || (partType.includes('barrel') && !partType.includes('accessory'));
                }
                if (category === 'barrelAccessory' || category === 'barrelAccessories') {
                    return partType === 'barrel accessory' || (partType.includes('barrel') && partType.includes('accessory'));
                }
                if (category === 'magazine') {
                    return partType === 'magazine' || partType.includes('magazine');
                }
                if (category === 'scope') {
                    return partType === 'scope' || (partType.includes('scope') && !partType.includes('accessory'));
                }
                if (category === 'scopeAccessory') {
                    return partType === 'scope accessory' || (partType.includes('scope') && partType.includes('accessory'));
                }
                if (category === 'grip') {
                    return partType === 'grip' || partType.includes('grip');
                }
                if (category === 'foregrip') {
                    return partType === 'foregrip' || partType.includes('foregrip');
                }
                if (category === 'underbarrel') {
                    return partType === 'underbarrel' || partType.includes('underbarrel');
                }
                if (category === 'statModifier') {
                    return partType === 'stat modifier' || (partType.includes('stat') && partType.includes('modifier'));
                }
                if (category === 'baseBody' || category === 'baseBody247') {
                    if (part.type === 'typed' && part.typeId === 247) {
                        // For enhancements, base body parts are 247:76-80
                        const partIdNum = parseInt(part.value);
                        if (!isNaN(partIdNum) && partIdNum >= 76 && partIdNum <= 80) {
                            return true;
                        }
                        // Also check by name/path for other cases
                        return (partType.includes('body') || partType.includes('main body') || 
                                partName.includes('body') || partPath.includes('main body'));
                    }
                    // For shields, 'Shield' partType should match baseBody
                    if (isShield && (partType === 'shield' || partPath.includes('shield'))) {
                        return true;
                    }
                    return partType === 'base' || partPath === 'base' || partPath.includes('base');
                }
                if (category === 'base') {
                    return partType === 'base' || partPath === 'base' || partPath.includes('base');
                }
                if (category === 'legendaryPart') {
                    return partType === 'augment' || partPath === 'augment' || 
                           partType.includes('legendary') || partName.includes('legendary');
                }
                if (category === 'legendaryPerks') {
                    return (isEnhancement && (part.value === 1 || part.value === 2 || part.value === 3 || part.value === 9)) ||
                           (partType === 'manufacturer perk' || partType === 'core');
                }
                if (category === 'shield') {
                    return partType === 'shield' || partPath.includes('shield');
                }
                if (category === 'core') {
                    return partType === 'core' || partPath.includes('core');
                }
                if (category === 'payload') {
                    return partType === 'payload' || partPath.includes('payload');
                }
                if (category === 'augment') {
                    return partType === 'augment' || partPath.includes('augment');
                }
                // Shield-specific categories
                if (category === 'primaryPerks246' || category === 'secondaryPerks246') {
                    // Parts from typeId 246 that are Perks (primary or secondary)
                    if (partTypeId === 246 && (partType.includes('perk') || partName.includes('perk'))) {
                        const spawnCode = String(part.spawnCode || '').toLowerCase();
                        const partPath = String(part.path || '').toLowerCase();
                        const partName = String(part.name || '').toLowerCase();
                        if (category === 'primaryPerks246') {
                            return spawnCode.includes('_primary') || partPath.includes('primary') || partName.includes('primary');
                        } else if (category === 'secondaryPerks246') {
                            return spawnCode.includes('_secondary') || partPath.includes('secondary') || partName.includes('secondary');
                        }
                        // Fallback: if it's a perk but can't determine, default to primary
                        return category === 'primaryPerks246';
                    }
                    return false;
                }
                if (category === 'firmware246') {
                    // Parts from typeId 246 that are Firmware
                    // Check partInfo first (this is the actual part data)
                    const partInfoTypeId = partInfo?.typeId;
                    if (partInfoTypeId === 246) {
                        return partType.includes('firmware') || partPath.includes('firmware') || 
                               (spawnCode && spawnCode.includes('firmware'));
                    }
                    // Also check if part object specifies typeId 246
                    if (part.type === 'typed' && part.typeId === 246) {
                        return true; // If it's a typed part with typeId 246, check partInfo for perk/firmware
                    }
                    return false;
                }
                if (category === 'armor237') {
                    // Parts from typeId 237 (Armor Shield)
                    // Check partInfo first (this is the actual part data)
                    const partInfoTypeId = partInfo?.typeId;
                    if (partInfoTypeId === 237) {
                        return true;
                    }
                    // Also check if part object specifies typeId 237
                    if (part.type === 'typed' && part.typeId === 237) {
                        return true;
                    }
                    return false;
                }
                if (category === 'energy248') {
                    // Parts from typeId 248 (Energy Shield)
                    // Check partInfo first (this is the actual part data)
                    const partInfoTypeId = partInfo?.typeId;
                    if (partInfoTypeId === 248) {
                        return true;
                    }
                    // Also check if part object specifies typeId 248
                    if (part.type === 'typed' && part.typeId === 248) {
                        return true;
                    }
                    return false;
                }
                
                return false;
            };
            
            // Helper function to check if a part already exists in randomParts
            const partAlreadyExists = (partToAdd) => {
                if (partToAdd.type === 'simple') {
                    return randomParts.some(p => 
                        p.type === 'simple' && p.value === partToAdd.value
                    );
                } else if (partToAdd.type === 'typed') {
                    return randomParts.some(p => 
                        p.type === 'typed' && p.typeId === partToAdd.typeId && p.value === partToAdd.value
                    );
                } else if (partToAdd.type === 'array') {
                    // For arrays, check if we already have an array with the same typeId
                    // (arrays can have different values, so we allow multiple arrays of same typeId)
                    // But check if this exact array already exists
                    return randomParts.some(p => 
                        p.type === 'array' && 
                        p.typeId === partToAdd.typeId && 
                        JSON.stringify(p.values?.sort()) === JSON.stringify(partToAdd.values?.sort())
                    );
                }
                return false;
            };
            
            // Helper function to safely add a part (with validation and duplicate checking)
            const safeAddPart = (partToAdd) => {
                // First check if part already exists
                if (partAlreadyExists(partToAdd)) {
                    return false; // Don't add duplicate
                }
                
                // CRITICAL: Only one firmware part per item, and NO firmware for weapons
                // Check if this is a firmware part
                let isFirmwarePart = false;
                if (partToAdd.type === 'typed') {
                    const partKey = `${partToAdd.typeId}:${partToAdd.value}`;
                    const partInfo = partsMap.get(partKey);
                    if (partInfo) {
                        const spawnCode = String(partInfo.spawnCode || '').toLowerCase();
                        const partPath = String(partInfo.path || '').toLowerCase();
                        const partType = String(partInfo.partType || '').toLowerCase();
                        isFirmwarePart = spawnCode.includes('firmware') || partPath.includes('firmware') || partType.includes('firmware');
                    }
                } else if (partToAdd.type === 'simple') {
                    const partInfo = partsMap.get(`${typeId}:${partToAdd.value}`) || partsMap.get(partToAdd.value);
                    if (partInfo) {
                        const spawnCode = String(partInfo.spawnCode || '').toLowerCase();
                        const partPath = String(partInfo.path || '').toLowerCase();
                        const partType = String(partInfo.partType || '').toLowerCase();
                        isFirmwarePart = spawnCode.includes('firmware') || partPath.includes('firmware') || partType.includes('firmware');
                    }
                }
                
                // If this is a firmware part:
                if (isFirmwarePart) {
                    // 1. Weapons cannot have firmware
                    if (isWeapon || isHeavyWeapon) {
                        return false; // Reject firmware for weapons
                    }
                    
                    // 2. Check if there's already a firmware part in randomParts
                    const hasFirmware = randomParts.some(p => {
                        if (p.type === 'typed') {
                            const pKey = `${p.typeId}:${p.value}`;
                            const pInfo = partsMap.get(pKey);
                            if (pInfo) {
                                const pSpawnCode = String(pInfo.spawnCode || '').toLowerCase();
                                const pPath = String(pInfo.path || '').toLowerCase();
                                const pType = String(pInfo.partType || '').toLowerCase();
                                return pSpawnCode.includes('firmware') || pPath.includes('firmware') || pType.includes('firmware');
                            }
                        } else if (p.type === 'simple') {
                            const pInfo = partsMap.get(`${typeId}:${p.value}`) || partsMap.get(p.value);
                            if (pInfo) {
                                const pSpawnCode = String(pInfo.spawnCode || '').toLowerCase();
                                const pPath = String(pInfo.path || '').toLowerCase();
                                const pType = String(pInfo.partType || '').toLowerCase();
                                return pSpawnCode.includes('firmware') || pPath.includes('firmware') || pType.includes('firmware');
                            }
                        }
                        return false;
                    });
                    
                    if (hasFirmware) {
                        return false; // Reject - already have a firmware part
                    }
                }
                
                // CRITICAL: Never allow 0 as a part ID unless explicitly valid
                // Check if 0 is valid by looking it up in partsMap
                const isValidZero = (typeId, partId) => {
                    if (partId === 0) {
                        // Check if 0 is actually a valid part ID
                        const zeroKey = `${typeId}:0`;
                        return partsMap.has(zeroKey);
                    }
                    return true; // Non-zero values are allowed (will be validated below)
                };
                
                // Validate the part exists in partsMap
                let partExists = false;
                if (partToAdd.type === 'simple') {
                    const partValue = parseInt(partToAdd.value);
                    // Reject 0 unless it's explicitly valid
                    if (!isValidZero(typeId, partValue)) {
                        return false;
                    }
                    // Check if part exists in partsMap
                    partExists = partsMap.has(`${typeId}:${partValue}`) || partsMap.has(partValue);
                    // Also verify the part actually exists by checking the partInfo
                    if (partExists) {
                        const partInfo = partsMap.get(`${typeId}:${partValue}`) || partsMap.get(partValue);
                        if (!partInfo) {
                            partExists = false;
                        }
                    }
                } else if (partToAdd.type === 'typed') {
                    const partValue = parseInt(partToAdd.value);
                    const partTypeId = parseInt(partToAdd.typeId);
                    // Reject 0 unless it's explicitly valid
                    if (!isValidZero(partTypeId, partValue)) {
                        return false;
                    }
                    // Check if part exists in partsMap
                    const partKey = `${partTypeId}:${partValue}`;
                    partExists = partsMap.has(partKey);
                    // Also verify the part actually exists by checking the partInfo
                    if (partExists) {
                        const partInfo = partsMap.get(partKey);
                        if (!partInfo) {
                            partExists = false;
                        }
                    }
                } else if (partToAdd.type === 'array') {
                    // For arrays, validate all values exist and filter out invalid ones
                    if (partToAdd.values && partToAdd.values.length > 0) {
                        const partTypeId = parseInt(partToAdd.typeId);
                        // Filter out invalid values (0 unless valid, and values that don't exist)
                        const validValues = partToAdd.values.filter(val => {
                            const partValue = parseInt(val);
                            // Reject 0 unless explicitly valid
                            if (!isValidZero(partTypeId, partValue)) {
                                return false;
                            }
                            // Check if value exists in partsMap
                            const partKey = `${partTypeId}:${partValue}`;
                            if (!partsMap.has(partKey)) {
                                return false;
                            }
                            // Verify the part actually exists
                            const partInfo = partsMap.get(partKey);
                            return !!partInfo;
                        });
                        
                        // Only consider the array valid if we have at least 2 valid values
                        // (arrays need at least 2 values to be meaningful)
                        if (validValues.length >= 2) {
                            // Update the partToAdd with filtered values
                            partToAdd.values = validValues.sort((a, b) => a - b);
                            partExists = true;
                        } else {
                            // Not enough valid values, reject the array
                            return false;
                        }
                    } else {
                        // Empty array, reject
                        return false;
                    }
                }
                
                if (partExists) {
                    randomParts.push(partToAdd);
                    return true;
                }
                return false;
            };
            
            // Helper function to add a part from a category
            const addPartFromCategory = (category, required = false) => {
                // Special check for rarity: ensure we NEVER add more than one rarity part
                if (category === 'rarity' || category === 'rarities') {
                    const hasRarityPart = randomParts.some(p => {
                        if (p.type === 'simple') {
                            const partInfo = partsMap.get(`${typeId}:${p.value}`) || partsMap.get(p.value);
                            if (partInfo) {
                                const partType = String(partInfo.partType || '').toLowerCase();
                                const partName = String(partInfo.name || '').toLowerCase();
                                const partPath = String(partInfo.path || '').toLowerCase();
                                return partType.includes('rarity') || partType === 'comp' || 
                                       partName.includes('rarity') || partName.includes('common') || 
                                       partName.includes('uncommon') || partName.includes('rare') || 
                                       partName.includes('epic') || partName.includes('legendary') ||
                                       partPath.includes('rarity') || partPath.includes('comp');
                            }
                        } else if (p.type === 'typed') {
                            const partInfo = partsMap.get(`${p.typeId}:${p.value}`);
                            if (partInfo) {
                                const partType = String(partInfo.partType || '').toLowerCase();
                                const partName = String(partInfo.name || '').toLowerCase();
                                const partPath = String(partInfo.path || '').toLowerCase();
                                return partType.includes('rarity') || partType === 'comp' || 
                                       partName.includes('rarity') || partName.includes('common') || 
                                       partName.includes('uncommon') || partName.includes('rare') || 
                                       partName.includes('epic') || partName.includes('legendary') ||
                                       partPath.includes('rarity') || partPath.includes('comp');
                            }
                        }
                        return false;
                    });
                    
                    // If we already have a rarity part, DO NOT add another one
                    if (hasRarityPart) {
                        return true;
                    }
                }
                
                // First check if we already have a part from this category (using comprehensive matching)
                const hasPartFromCategory = randomParts.some(p => {
                    let partInfo = null;
                    if (p.type === 'simple') {
                        partInfo = partsMap.get(`${typeId}:${p.value}`) || partsMap.get(p.value);
                    } else if (p.type === 'typed') {
                        partInfo = partsMap.get(`${p.typeId}:${p.value}`);
                    } else if (p.type === 'array') {
                        // For arrays, check each value
                        for (const val of p.values || []) {
                            const arrayPartInfo = partsMap.get(`${p.typeId}:${val}`);
                            if (arrayPartInfo && partMatchesCategory({type: 'typed', typeId: p.typeId, value: val}, arrayPartInfo, category)) {
                                return true;
                            }
                        }
                        return false;
                    }
                    return partInfo && partMatchesCategory(p, partInfo, category);
                });
                
                // If we already have a part from this category, requirement is satisfied
                if (hasPartFromCategory) {
                    return true;
                }
                
                // Try to find parts from the category
                // For shields looking for baseBody, prioritize searching the shield's own typeId directly
                let parts = null;
                if (isShield && category === 'baseBody') {
                    // First try partsByCategory.baseBody
                    parts = partsByCategory[category] || [];
                    // If empty, try partsByCategory.shield filtered to this shield's typeId
                    if (parts.length === 0) {
                        const shieldParts = partsByCategory['shield'] || [];
                        parts = shieldParts.filter(p => {
                            const partTypeId = p.typeId || typeId;
                            return partTypeId === typeId;
                        });
                    }
                    // If still empty, search directly in partsByTypeId for shield's own typeId
                    if (parts.length === 0 && partsByTypeId.has(typeId)) {
                        const shieldParts = partsByTypeId.get(typeId) || [];
                        parts = shieldParts.filter(p => {
                            const partType = String(p.partType || '').toLowerCase();
                            const partPath = String(p.path || '').toLowerCase();
                            return partType === 'shield' || partPath.includes('shield');
                        });
                    }
                } else {
                    parts = partsByCategory[category];
                }
                
                if (!parts || parts.length === 0) {
                    // If category not found in partsByCategory, search by partType/path
                    // For cross-typeId categories, also search in the relevant cross-typeId
                    const crossTypeIdCategories = ['firmware243', 'parts243', 'firmware245', 'parts245', 
                                                   'firmware247', 'stat_247', 'stat2_247', 'stat3_247', 'baseBody247', 'perks234', 
                                                   'firmware234', 'perks246', 'firmware246', 'armor237', 
                                                   'energy248', 'skills', 'firmware244'];
                    const isCrossTypeIdCategory = crossTypeIdCategories.includes(category);
                    
                    // Determine which typeIds to search
                    const typeIdsToSearch = [typeId];
                    if (isCrossTypeIdCategory) {
                        // Add relevant cross-typeIds based on category
                        if (category === 'primaryPerks246' || category === 'secondaryPerks246' || category === 'perks246' || category === 'firmware246') {
                            typeIdsToSearch.push(246);
                        } else if (category === 'armor237') {
                            typeIdsToSearch.push(237);
                        } else if (category === 'energy248') {
                            typeIdsToSearch.push(248);
                        } else if (category === 'stat234' || category === 'stat2_234' || category === 'statspecial_234' || category === 'perks234' || category === 'firmware234') {
                            typeIdsToSearch.push(234);
                        } else if (category === 'firmware243' || category === 'parts243') {
                            typeIdsToSearch.push(243);
                        } else if (category === 'firmware245' || category === 'parts245') {
                            typeIdsToSearch.push(245);
                        } else if (category === 'firmware247' || category === 'stat_247' || category === 'stat2_247' || category === 'stat3_247' || category === 'baseBody247') {
                            typeIdsToSearch.push(247);
                        } else if (category === 'firmware244') {
                            typeIdsToSearch.push(244);
                        } else if (category === 'skills') {
                            typeIdsToSearch.push(254, 255);
                        }
                    }
                    
                    // Collect parts from all relevant typeIds
                    const allParts = [];
                    typeIdsToSearch.forEach(tid => {
                        const typeParts = partsByTypeId.get(tid) || [];
                        allParts.push(...typeParts);
                    });
                    
                    parts = allParts.filter(p => {
                        // For shields looking for baseBody, check for 'Shield' partType from the shield's own typeId
                        if (isShield && category === 'baseBody') {
                            const partType = String(p.partType || '').toLowerCase();
                            const partPath = String(p.path || '').toLowerCase();
                            const partTypeId = p.typeId || typeId;
                            // Must be from the shield's own typeId and have 'shield' partType
                            if (partTypeId === typeId && (partType === 'shield' || partPath.includes('shield'))) {
                                return true;
                            }
                        }
                        // For shield-specific categories, check partInfo directly
                        if (category === 'perks246' || category === 'firmware246' || category === 'armor237' || category === 'energy248') {
                            // Create a part object based on the partInfo's typeId
                            let partObj;
                            if (p.typeId === 246 || p.typeId === 237 || p.typeId === 248) {
                                // This is a cross-typeId part, create a typed part object
                                partObj = {type: 'typed', typeId: p.typeId, value: parseInt(p.id || p.fullId?.split(':')[1] || 0)};
                            } else {
                                partObj = {type: 'simple', value: p.id || p.fullId};
                            }
                            return partMatchesCategory(partObj, p, category);
                        }
                        return partMatchesCategory({type: 'simple', value: p.id || p.fullId}, p, category);
                    });
                }
                
                // For shields, if looking for baseBody and no parts found, try 'shield' category
                // (This is a final fallback after the main search logic)
                if (isShield && category === 'baseBody' && (!parts || parts.length === 0)) {
                    // Try partsByCategory.shield filtered to this shield's typeId
                    const shieldParts = partsByCategory['shield'] || [];
                    parts = shieldParts.filter(p => {
                        const partTypeId = p.typeId || typeId;
                        return partTypeId === typeId;
                    });
                    // If still no parts, search directly in partsByTypeId for shield's own typeId
                    if ((!parts || parts.length === 0) && partsByTypeId.has(typeId)) {
                        const typeIdParts = partsByTypeId.get(typeId) || [];
                        parts = typeIdParts.filter(p => {
                            const partType = String(p.partType || '').toLowerCase();
                            const partPath = String(p.path || '').toLowerCase();
                            const spawnCode = String(p.spawnCode || '').toLowerCase();
                            // Match parts with 'shield' partType or path containing 'shield'
                            return partType === 'shield' || partPath.includes('shield') || spawnCode.includes('shield');
                        });
                    }
                }
                
                if (parts && parts.length > 0) {
                    // For enhancements, filter out typeId 247 parts from rarity category
                    if (isEnhancement && category === 'rarity') {
                        parts = parts.filter(p => {
                            const partTypeId = p.typeId || typeId;
                            return partTypeId === typeId && partTypeId !== 247;
                        });
                    }
                    
                    // Filter parts to only those for this typeId (unless it's a cross-typeId category)
                    const crossTypeIdCategories = ['firmware243', 'parts243', 'firmware245', 'parts245', 
                                                   'firmware247', 'stat_247', 'stat2_247', 'stat3_247', 'baseBody247', 'perks234', 
                                                   'firmware234', 'perks246', 'firmware246', 'armor237', 
                                                   'energy248', 'skills', 'firmware244'];
                    if (!crossTypeIdCategories.includes(category)) {
                        parts = parts.filter(p => {
                            const partTypeId = p.typeId || typeId;
                            return partTypeId === typeId;
                        });
                    }
                    
                    if (parts.length > 0) {
                        const randomPart = getRandomItem(parts);
                        const partId = getPartId(randomPart);
                        if (partId) {
                            // For enhancements, ensure rarity is NOT from 247
                            if (isEnhancement && category === 'rarity' && partId.typeId === 247) {
                                // Skip this part, try to find one from the enhancement's typeId
                                const localParts = partsByCategory.rarity.filter(p => {
                                    const partTypeId = p.typeId || typeId;
                                    return partTypeId === typeId && partTypeId !== 247;
                                });
                                if (localParts.length > 0) {
                                    const localPart = getRandomItem(localParts);
                                    const localPartId = getPartId(localPart);
                                    if (localPartId && localPartId.typeId === typeId && localPartId.typeId !== 247) {
                                        const partValue = parseInt(localPartId.partId);
                                        // CRITICAL: Reject 0 values unless explicitly valid
                                        if (!isNaN(partValue) && (partValue !== 0 || partsMap.has(`${typeId}:0`))) {
                                            const partToAdd = {
                                                type: 'simple',
                                                value: partValue || localPartId.partId
                                            };
                                            if (safeAddPart(partToAdd)) {
                                                return true;
                                            }
                                        }
                                    }
                                }
                                return false;
                            }
                            
                            // Try up to 10 times to find a valid, non-duplicate part
                            let attempts = 0;
                            let added = false;
                            while (attempts < 10 && parts.length > 0 && !added) {
                                const testPart = attempts === 0 ? randomPart : getRandomItem(parts);
                                const testPartId = getPartId(testPart);
                                if (testPartId) {
                                    const partValue = parseInt(testPartId.partId);
                                    // CRITICAL: Reject 0 values unless explicitly valid
                                    if (isNaN(partValue) || partValue === 0) {
                                        // Check if 0 is valid for this typeId
                                        const checkTypeId = testPartId.typeId === typeId ? typeId : testPartId.typeId;
                                        const zeroKey = `${checkTypeId}:0`;
                                        if (!partsMap.has(zeroKey)) {
                                            // 0 is not valid, skip this part
                                            const index = parts.indexOf(testPart);
                                            if (index > -1) {
                                                parts.splice(index, 1);
                                            }
                                            attempts++;
                                            continue;
                                        }
                                    }
                                    
                                    let partToAdd;
                                    if (testPartId.typeId === typeId) {
                                        partToAdd = {
                                            type: 'simple',
                                            value: partValue || testPartId.partId
                                        };
                                    } else {
                                        partToAdd = {
                                            type: 'typed',
                                            typeId: testPartId.typeId,
                                            value: partValue || testPartId.partId
                                        };
                                    }
                                    
                                    // Try to add the part (this will validate and check for duplicates)
                                    if (safeAddPart(partToAdd)) {
                                        added = true;
                                        return true;
                                    }
                                }
                                
                                // Remove tested part from list and try again
                                const index = parts.indexOf(testPart);
                                if (index > -1) {
                                    parts.splice(index, 1);
                                }
                                attempts++;
                            }
                            
                            // If we couldn't add a valid part after 10 attempts
                            if (!added && required) {
                                console.warn(`Warning: Required category '${category}' has no valid, non-duplicate parts for typeId ${typeId}`);
                            }
                            return added;
                        }
                    }
                }
                // If required part is missing, log a warning but continue
                if (required) {
                    console.warn(`Warning: Required category '${category}' has no available parts for typeId ${typeId}`);
                }
                return false;
            };
            
            // Track which required categories were successfully added
            const addedRequiredCategories = [];
            
            // First, add all required parts (these MUST be included if available)
            requiredCategories.forEach(category => {
                const wasAdded = addPartFromCategory(category, true);
                if (wasAdded) {
                    addedRequiredCategories.push(category);
                }
            });
            
            // Note: requiredCategories already filters out categories that don't have parts
            // So we don't need to check if rarity was required but doesn't exist - it simply won't be in requiredCategories
            
            // Ensure rarity is ALWAYS added (critical for all item types)
            // For enhancements, make sure rarity is from local typeId, not 247
            // IMPORTANT: Only add rarity if we don't already have one (prevent duplicates)
            const hasRarity = randomParts.some(p => {
                if (p.type === 'simple') {
                    const partInfo = partsMap.get(`${typeId}:${p.value}`) || partsMap.get(p.value);
                    if (partInfo) {
                        const partTypeId = partInfo.typeId || typeId;
                        // For enhancements, exclude 247
                        if (isEnhancement && partTypeId === 247) return false;
                        const partType = String(partInfo.partType || '').toLowerCase();
                        const partName = String(partInfo.name || '').toLowerCase();
                        const partPath = String(partInfo.path || '').toLowerCase();
                        return partType.includes('rarity') || partType === 'comp' || 
                               partName.includes('rarity') || partName.includes('common') || 
                               partName.includes('uncommon') || partName.includes('rare') || 
                               partName.includes('epic') || partName.includes('legendary') ||
                               partPath.includes('rarity') || partPath.includes('comp');
                    }
                } else if (p.type === 'typed') {
                    // For enhancements, exclude 247
                    if (isEnhancement && p.typeId === 247) return false;
                    const partInfo = partsMap.get(`${p.typeId}:${p.value}`);
                    if (partInfo) {
                        const partType = String(partInfo.partType || '').toLowerCase();
                        const partName = String(partInfo.name || '').toLowerCase();
                        const partPath = String(partInfo.path || '').toLowerCase();
                        return partType.includes('rarity') || partType === 'comp' || 
                               partName.includes('rarity') || partName.includes('common') || 
                               partName.includes('uncommon') || partName.includes('rare') || 
                               partName.includes('epic') || partName.includes('legendary') ||
                               partPath.includes('rarity') || partPath.includes('comp');
                    }
                }
                return false;
            });
            
            // Only add rarity if we don't already have one (prevent duplicates)
            if (!hasRarity) {
                // Try to find rarity from item's own parts
                const ownParts = partsByTypeId.get(typeId) || [];
                const rarityPart = ownParts.find(p => {
                    // For enhancements, make sure it's from the enhancement's typeId, not 247
                    const partTypeId = p.typeId || typeId;
                    if (isEnhancement && partTypeId === 247) return false;
                    
                    const partType = String(p.partType || '').toLowerCase();
                    const partName = String(p.name || '').toLowerCase();
                    const partPath = String(p.path || '').toLowerCase();
                    return partType.includes('rarity') || partType === 'comp' || 
                           partName.includes('rarity') || partName.includes('common') || 
                           partName.includes('uncommon') || partName.includes('rare') || 
                           partName.includes('epic') || partName.includes('legendary') ||
                           partPath.includes('rarity') || partPath.includes('comp');
                });
                
                if (rarityPart) {
                    const partId = getPartId(rarityPart);
                    if (partId) {
                        // For enhancements, ensure it's NOT from 247
                        if (isEnhancement && partId.typeId === 247) {
                            // Skip, will be handled in enhancement special handling
                            return;
                        }
                        
                        // Use safeAddPart to validate and prevent duplicates
                        const partValue = parseInt(partId.partId);
                        // CRITICAL: Reject 0 values unless explicitly valid
                        if (isNaN(partValue) || (partValue === 0 && !partsMap.has(`${partId.typeId}:0`))) {
                            // Invalid part value, skip
                            return;
                        }
                        
                        let partToAdd;
                        if (partId.typeId === typeId) {
                            partToAdd = {
                                type: 'simple',
                                value: partValue || partId.partId
                            };
                        } else {
                            partToAdd = {
                                type: 'typed',
                                typeId: partId.typeId,
                                value: partValue || partId.partId
                            };
                        }
                        safeAddPart(partToAdd);
                    }
                } else if (partsByCategory.rarity.length > 0) {
                    // Fallback: use any rarity from categorized parts
                    // For enhancements, this will filter out 247 in addPartFromCategory
                    addPartFromCategory('rarity', true);
                }
            }
            
            // Then, randomly add optional parts (70% chance for each optional category)
            optionalCategories.forEach(category => {
                if (Math.random() < 0.7) { // 70% chance to include optional parts
                    addPartFromCategory(category, false);
                }
            });
            
            // Special handling for Shields: Add either Armor 237 OR Energy 248 (not both, but one is required)
            // Determine which one to add based on what's available
            if (isShield) {
                // Check if we already have armor237 or energy248
                const hasArmor237 = randomParts.some(p => 
                    p.type === 'typed' && p.typeId === 237
                );
                const hasEnergy248 = randomParts.some(p => 
                    p.type === 'typed' && p.typeId === 248
                );
                
                // If we don't have either, try to add one (required)
                if (!hasArmor237 && !hasEnergy248) {
                    // Try armor237 first, then energy248 if armor237 fails
                    const armorAdded = addPartFromCategory('armor237', true);
                    if (!armorAdded) {
                        // If armor237 couldn't be added, try energy248 (required)
                        addPartFromCategory('energy248', true);
                    }
                }
            }
            
            // Special handling for Enhancements: Base Body 247 must match rarity (parts 76-80)
            // Also ensure stats247 and firmware247 are always added
            // IMPORTANT: Rarity must come from the enhancement's own typeId, NOT from 247
            if (isEnhancement) {
                // Ensure rarity is added from enhancement's own typeId (not 247)
                const hasRarity = randomParts.some(p => {
                    if (p.type === 'simple') {
                        // Simple parts are from the same typeId
                        const partInfo = partsMap.get(p.value);
                        if (partInfo) {
                            // Make sure it's from the enhancement's typeId, not 247
                            const partTypeId = partInfo.typeId || typeId;
                            if (partTypeId === typeId && partTypeId !== 247) {
                                const partType = String(partInfo.partType || '').toLowerCase();
                                const partName = String(partInfo.name || '').toLowerCase();
                                const partPath = String(partInfo.path || '').toLowerCase();
                                return partType.includes('rarity') || partType === 'comp' || 
                                       partName.includes('rarity') || partName.includes('common') || 
                                       partName.includes('uncommon') || partName.includes('rare') || 
                                       partName.includes('epic') || partName.includes('legendary') ||
                                       partPath.includes('rarity') || partPath.includes('rarities');
                            }
                        }
                    } else if (p.type === 'typed') {
                        // Typed parts - make sure it's from enhancement's typeId, not 247
                        if (p.typeId === typeId && p.typeId !== 247) {
                            const partInfo = partsMap.get(`${p.typeId}:${p.value}`);
                            if (partInfo) {
                                const partType = String(partInfo.partType || '').toLowerCase();
                                const partName = String(partInfo.name || '').toLowerCase();
                                const partPath = String(partInfo.path || '').toLowerCase();
                                return partType.includes('rarity') || partType === 'comp' || 
                                       partName.includes('rarity') || partName.includes('common') || 
                                       partName.includes('uncommon') || partName.includes('rare') || 
                                       partName.includes('epic') || partName.includes('legendary') ||
                                       partPath.includes('rarity') || partPath.includes('rarities');
                            }
                        }
                    }
                    return false;
                });
                
                if (!hasRarity) {
                    // Get rarity ONLY from enhancement's own typeId (not 247)
                    const enhancementParts = partsByTypeId.get(typeId) || [];
                    const rarityPart = enhancementParts.find(p => {
                        // Make sure it's from the enhancement's typeId
                        const partTypeId = p.typeId || typeId;
                        if (partTypeId !== typeId || partTypeId === 247) return false;
                        
                        const partType = String(p.partType || '').toLowerCase();
                        const partName = String(p.name || '').toLowerCase();
                        const partPath = String(p.path || '').toLowerCase();
                        return partType.includes('rarity') || partType === 'comp' || 
                               partName.includes('rarity') || partName.includes('common') || 
                               partName.includes('uncommon') || partName.includes('rare') || 
                               partName.includes('epic') || partName.includes('legendary') ||
                               partPath.includes('rarity') || partPath.includes('rarities');
                    });
                    
                    if (rarityPart) {
                        const partId = getPartId(rarityPart);
                        if (partId && partId.typeId === typeId && partId.typeId !== 247) {
                            const partValue = parseInt(partId.partId);
                            // CRITICAL: Reject 0 values unless explicitly valid
                            if (!isNaN(partValue) && (partValue !== 0 || partsMap.has(`${typeId}:0`))) {
                                const partToAdd = {
                                    type: 'simple',
                                    value: partValue || partId.partId
                                };
                                safeAddPart(partToAdd);
                            }
                        }
                    } else {
                        // Fallback: look in categorized rarity but filter out 247 parts
                        const localRarityParts = partsByCategory.rarity.filter(p => {
                            const partTypeId = p.typeId || typeId;
                            return partTypeId === typeId && partTypeId !== 247;
                        });
                        
                        if (localRarityParts.length > 0) {
                            const randomRarity = getRandomItem(localRarityParts);
                            if (randomRarity) {
                                const partId = getPartId(randomRarity);
                                if (partId && partId.typeId === typeId && partId.typeId !== 247) {
                                    const partValue = parseInt(partId.partId);
                                    // CRITICAL: Reject 0 values unless explicitly valid
                                    if (!isNaN(partValue) && (partValue !== 0 || partsMap.has(`${typeId}:0`))) {
                                        const partToAdd = {
                                            type: 'simple',
                                            value: partValue || partId.partId
                                        };
                                        safeAddPart(partToAdd);
                                    }
                                }
                            }
                        }
                    }
                }
                
                // Find the rarity part we added (or just added)
                const addedRarityPart = randomParts.find(p => {
                    if (p.type === 'simple') {
                        const partInfo = partsMap.get(`${typeId}:${p.value}`) || partsMap.get(p.value);
                        if (partInfo) {
                            const partTypeId = partInfo.typeId || typeId;
                            // Make sure it's from the enhancement's typeId, not 247
                            if (partTypeId === typeId && partTypeId !== 247) {
                                return partsByCategory.rarity.includes(partInfo) || 
                                       String(partInfo.partType || '').toLowerCase().includes('rarity') ||
                                       String(partInfo.name || '').toLowerCase().includes('rarity') ||
                                       String(partInfo.name || '').toLowerCase().includes('common') ||
                                       String(partInfo.name || '').toLowerCase().includes('uncommon') ||
                                       String(partInfo.name || '').toLowerCase().includes('rare') ||
                                       String(partInfo.name || '').toLowerCase().includes('epic') ||
                                       String(partInfo.name || '').toLowerCase().includes('legendary');
                            }
                        }
                    } else if (p.type === 'typed') {
                        // Typed parts - make sure it's from enhancement's typeId, not 247
                        if (p.typeId === typeId && p.typeId !== 247) {
                            const partInfo = partsMap.get(`${p.typeId}:${p.value}`);
                            if (partInfo) {
                                return partsByCategory.rarity.includes(partInfo) ||
                                       String(partInfo.partType || '').toLowerCase().includes('rarity') ||
                                       String(partInfo.name || '').toLowerCase().includes('rarity') ||
                                       String(partInfo.name || '').toLowerCase().includes('common') ||
                                       String(partInfo.name || '').toLowerCase().includes('uncommon') ||
                                       String(partInfo.name || '').toLowerCase().includes('rare') ||
                                       String(partInfo.name || '').toLowerCase().includes('epic') ||
                                       String(partInfo.name || '').toLowerCase().includes('legendary');
                            }
                        }
                    }
                    return false;
                });
                
                // ALWAYS add baseBody247 - map rarity to base body part (247:76-80)
                // Base Body mapping: 76=Legendary, 77=Epic, 78=Rare, 79=Uncommon, 80=Common
                // Rarity values: 5=Common, 6=Uncommon, 7=Rare, 8=Epic, 9=Legendary
                let baseBodyPartId = null;
                
                // Check if we already added a base body
                const hasBaseBody = randomParts.some(p => {
                    if (p.type === 'typed' && p.typeId === 247) {
                        const partIdNum = parseInt(p.value);
                        return partIdNum >= 76 && partIdNum <= 80;
                    }
                    return false;
                });
                
                // Try to determine base body part ID from rarity (if available)
                if (!hasBaseBody && addedRarityPart) {
                    // First, try to get the numeric rarity value directly (5, 6, 7, 8, 9)
                    const rarityValue = parseInt(addedRarityPart.value);
                    if (!isNaN(rarityValue) && rarityValue >= 5 && rarityValue <= 9) {
                        // Map numeric rarity to base body part ID
                        // Rarity 5 (Common) → 80, 6 (Uncommon) → 79, 7 (Rare) → 78, 8 (Epic) → 77, 9 (Legendary) → 76
                        if (rarityValue === 5) baseBodyPartId = 80; // Common
                        else if (rarityValue === 6) baseBodyPartId = 79; // Uncommon
                        else if (rarityValue === 7) baseBodyPartId = 78; // Rare
                        else if (rarityValue === 8) baseBodyPartId = 77; // Epic
                        else if (rarityValue === 9) baseBodyPartId = 76; // Legendary
                    } else {
                        // Fallback: Get the part info to determine rarity level from name/partType/spawnCode
                        let rarityPartInfo = null;
                        if (addedRarityPart.type === 'simple') {
                            rarityPartInfo = partsMap.get(`${typeId}:${addedRarityPart.value}`) || partsMap.get(addedRarityPart.value);
                        } else if (addedRarityPart.type === 'typed') {
                            rarityPartInfo = partsMap.get(`${addedRarityPart.typeId}:${addedRarityPart.value}`);
                        }
                        
                        if (rarityPartInfo) {
                            const partName = String(rarityPartInfo.name || '').toLowerCase();
                            const partType = String(rarityPartInfo.partType || '').toLowerCase();
                            const spawnCode = String(rarityPartInfo.spawnCode || '').toLowerCase();
                            
                            // Determine rarity level from name/partType/spawnCode
                            // Map to correct base body part IDs: 76=Legendary, 77=Epic, 78=Rare, 79=Uncommon, 80=Common
                            if (partName.includes('common') || spawnCode.includes('comp_01') || spawnCode.includes('common') || spawnCode.includes('body_01')) {
                                baseBodyPartId = 80; // Common
                            } else if (partName.includes('uncommon') || spawnCode.includes('comp_02') || spawnCode.includes('uncommon') || spawnCode.includes('body_02')) {
                                baseBodyPartId = 79; // Uncommon
                            } else if (partName.includes('rare') || spawnCode.includes('comp_03') || spawnCode.includes('rare') || spawnCode.includes('body_03')) {
                                baseBodyPartId = 78; // Rare
                            } else if (partName.includes('epic') || spawnCode.includes('comp_04') || spawnCode.includes('epic') || spawnCode.includes('body_04')) {
                                baseBodyPartId = 77; // Epic
                            } else if (partName.includes('legendary') || spawnCode.includes('comp_05') || spawnCode.includes('legendary') || spawnCode.includes('body_05')) {
                                baseBodyPartId = 76; // Legendary
                            }
                        }
                    }
                }
                
                // ALWAYS add base body if not already present
                // First, try using addPartFromCategory which is the most reliable method
                if (!hasBaseBody) {
                    console.log(`[ENHANCEMENT DEBUG] Attempting to add base body. hasBaseBody=${hasBaseBody}`);
                    console.log(`[ENHANCEMENT DEBUG] partsByCategory.baseBody247 has ${partsByCategory.baseBody247.length} parts`);
                    console.log(`[ENHANCEMENT DEBUG] partsByTypeId.get(247) has ${(partsByTypeId.get(247) || []).length} parts`);
                    
                    // Try using addPartFromCategory first (most reliable)
                    let added = addPartFromCategory('baseBody247', true);
                    console.log(`[ENHANCEMENT DEBUG] addPartFromCategory('baseBody247') returned: ${added}`);
                    
                    // Verify it was actually added
                    if (added) {
                        const verifyBaseBody = randomParts.some(p => {
                            if (p.type === 'typed' && p.typeId === 247) {
                                const partIdNum = parseInt(p.value);
                                return partIdNum >= 76 && partIdNum <= 80;
                            }
                            return false;
                        });
                        console.log(`[ENHANCEMENT DEBUG] Verification: base body actually in randomParts: ${verifyBaseBody}`);
                        if (!verifyBaseBody) {
                            console.warn(`[ENHANCEMENT DEBUG] addPartFromCategory returned true but part not in randomParts!`);
                            added = false; // Reset to try other methods
                        }
                    }
                    
                    // If that didn't work, try to determine base body part ID from rarity and add directly
                    if (!added && addedRarityPart) {
                        // Determine base body part ID from rarity
                        const rarityValue = parseInt(addedRarityPart.value);
                        if (!isNaN(rarityValue) && rarityValue >= 5 && rarityValue <= 9) {
                            // Map numeric rarity to base body part ID
                            if (rarityValue === 5) baseBodyPartId = 80; // Common
                            else if (rarityValue === 6) baseBodyPartId = 79; // Uncommon
                            else if (rarityValue === 7) baseBodyPartId = 78; // Rare
                            else if (rarityValue === 8) baseBodyPartId = 77; // Epic
                            else if (rarityValue === 9) baseBodyPartId = 76; // Legendary
                        } else {
                            // Fallback: Get the part info to determine rarity level from name/partType/spawnCode
                            let rarityPartInfo = null;
                            if (addedRarityPart.type === 'simple') {
                                rarityPartInfo = partsMap.get(`${typeId}:${addedRarityPart.value}`) || partsMap.get(addedRarityPart.value);
                            } else if (addedRarityPart.type === 'typed') {
                                rarityPartInfo = partsMap.get(`${addedRarityPart.typeId}:${addedRarityPart.value}`);
                            }
                            
                            if (rarityPartInfo) {
                                const partName = String(rarityPartInfo.name || '').toLowerCase();
                                const partType = String(rarityPartInfo.partType || '').toLowerCase();
                                const spawnCode = String(rarityPartInfo.spawnCode || '').toLowerCase();
                                
                                // Map to correct base body part IDs: 76=Legendary, 77=Epic, 78=Rare, 79=Uncommon, 80=Common
                                if (partName.includes('common') || spawnCode.includes('comp_01') || spawnCode.includes('common') || spawnCode.includes('body_01')) {
                                    baseBodyPartId = 80; // Common
                                } else if (partName.includes('uncommon') || spawnCode.includes('comp_02') || spawnCode.includes('uncommon') || spawnCode.includes('body_02')) {
                                    baseBodyPartId = 79; // Uncommon
                                } else if (partName.includes('rare') || spawnCode.includes('comp_03') || spawnCode.includes('rare') || spawnCode.includes('body_03')) {
                                    baseBodyPartId = 78; // Rare
                                } else if (partName.includes('epic') || spawnCode.includes('comp_04') || spawnCode.includes('epic') || spawnCode.includes('body_04')) {
                                    baseBodyPartId = 77; // Epic
                                } else if (partName.includes('legendary') || spawnCode.includes('comp_05') || spawnCode.includes('legendary') || spawnCode.includes('body_05')) {
                                    baseBodyPartId = 76; // Legendary
                                }
                            }
                        }
                        
                        // If we determined a base body part ID, try to add it
                        if (baseBodyPartId !== null) {
                            const baseBodyKey = `247:${baseBodyPartId}`;
                            console.log(`[ENHANCEMENT DEBUG] Determined baseBodyPartId=${baseBodyPartId}, checking if ${baseBodyKey} exists in partsMap: ${partsMap.has(baseBodyKey)}`);
                            
                            if (partsMap.has(baseBodyKey)) {
                                const partToAdd = {
                                    type: 'typed',
                                    typeId: 247,
                                    value: baseBodyPartId
                                };
                                console.log(`[ENHANCEMENT DEBUG] Attempting to add base body part:`, partToAdd);
                                added = safeAddPart(partToAdd);
                                console.log(`[ENHANCEMENT DEBUG] safeAddPart returned: ${added}`);
                            }
                        }
                    }
                    
                    // If still not added, try all base body IDs (76-80) until one works
                    // BUT prioritize the determined baseBodyPartId if available
                    if (!added) {
                        console.log(`[ENHANCEMENT DEBUG] Trying all base body IDs (76-80) as fallback, baseBodyPartId=${baseBodyPartId}`);
                        // If we have a determined baseBodyPartId, try it first
                        let baseBodyIds = [76, 77, 78, 79, 80];
                        if (baseBodyPartId !== null && baseBodyPartId >= 76 && baseBodyPartId <= 80) {
                            // Put the determined ID first
                            baseBodyIds = [baseBodyPartId, ...baseBodyIds.filter(id => id !== baseBodyPartId)];
                            console.log(`[ENHANCEMENT DEBUG] Prioritizing determined baseBodyPartId ${baseBodyPartId}`);
                        }
                        for (const bodyId of baseBodyIds) {
                            const key = `247:${bodyId}`;
                            if (partsMap.has(key)) {
                                const partToAdd = {
                                    type: 'typed',
                                    typeId: 247,
                                    value: bodyId
                                };
                                added = safeAddPart(partToAdd);
                                if (added) {
                                    console.log(`[ENHANCEMENT] Successfully added base body part ${key}`);
                                    break;
                                }
                            }
                        }
                    }
                    
                    // Final fallback: directly add from partsByCategory if available
                    if (!added && partsByCategory.baseBody247.length > 0) {
                        const baseBodyPart = partsByCategory.baseBody247[0];
                        const partId = getPartId(baseBodyPart);
                        if (partId && partId.typeId === 247) {
                            const partIdNum = parseInt(partId.partId);
                            if (!isNaN(partIdNum) && partIdNum >= 76 && partIdNum <= 80) {
                                const partToAdd = {
                                    type: 'typed',
                                    typeId: 247,
                                    value: partIdNum
                                };
                                // Use safeAddPart first, but if it fails, add directly
                                if (safeAddPart(partToAdd)) {
                                    added = true;
                                    console.log(`[ENHANCEMENT] Fallback: Added base body part 247:${partIdNum} via safeAddPart`);
                                } else {
                                    // If safeAddPart fails (maybe duplicate check), add directly anyway
                                    randomParts.push(partToAdd);
                                    added = true;
                                    console.log(`[ENHANCEMENT] Fallback: Directly added base body part 247:${partIdNum} (bypassed safeAddPart)`);
                                }
                            }
                        }
                    }
                    
                    // Ultimate fallback: if baseBodyPartId was determined, add it directly
                    if (!added && baseBodyPartId !== null) {
                        const partToAdd = {
                            type: 'typed',
                            typeId: 247,
                            value: baseBodyPartId
                        };
                        const partKey = `247:${baseBodyPartId}`;
                        if (partsMap.has(partKey)) {
                            if (safeAddPart(partToAdd)) {
                                added = true;
                                console.log(`[ENHANCEMENT] Ultimate fallback: Added base body part ${partKey} via safeAddPart`);
                            } else {
                                // If safeAddPart fails, add directly anyway
                                randomParts.push(partToAdd);
                                added = true;
                                console.log(`[ENHANCEMENT] Ultimate fallback: Directly added base body part ${partKey} (bypassed safeAddPart)`);
                            }
                        }
                    }
                    
                    // Last resort: add default (78 = Rare) if nothing else worked
                    if (!added) {
                        const defaultPartId = 78; // Default to Rare
                        const defaultKey = `247:${defaultPartId}`;
                        if (partsMap.has(defaultKey)) {
                            const partToAdd = {
                                type: 'typed',
                                typeId: 247,
                                value: defaultPartId
                            };
                            if (safeAddPart(partToAdd)) {
                                added = true;
                                console.log(`[ENHANCEMENT] Last resort: Added default base body part ${defaultKey} via safeAddPart`);
                            } else {
                                // If safeAddPart fails, add directly anyway
                                randomParts.push(partToAdd);
                                added = true;
                                console.log(`[ENHANCEMENT] Last resort: Directly added default base body part ${defaultKey} (bypassed safeAddPart)`);
                            }
                        } else {
                            console.error(`[ENHANCEMENT] CRITICAL: Failed to add any base body part (247:76-80) after all attempts.`);
                            console.error(`[ENHANCEMENT] partsByCategory.baseBody247.length: ${partsByCategory.baseBody247.length}`);
                            console.error(`[ENHANCEMENT] partsByTypeId.get(247).length: ${(partsByTypeId.get(247) || []).length}`);
                            console.error(`[ENHANCEMENT] partsMap.has('247:78'): ${partsMap.has('247:78')}`);
                            console.error(`[ENHANCEMENT] Current randomParts:`, randomParts);
                        }
                    } else {
                        console.log(`[ENHANCEMENT] Successfully added base body part`);
                    }
                    
                    // CRITICAL: Verify the base body part is actually in randomParts
                    const verifyBaseBodyInRandomParts = randomParts.some(p => {
                        if (p.type === 'typed' && p.typeId === 247) {
                            const partIdNum = parseInt(p.value);
                            return partIdNum >= 76 && partIdNum <= 80;
                        }
                        return false;
                    });
                    console.log(`[ENHANCEMENT DEBUG] Final verification: base body in randomParts = ${verifyBaseBodyInRandomParts}`);
                    if (!verifyBaseBodyInRandomParts) {
                        console.error(`[ENHANCEMENT] CRITICAL ERROR: Base body part was not added to randomParts!`);
                        console.error(`[ENHANCEMENT] randomParts contents:`, randomParts);
                        // Force add it directly
                        const forceAddId = baseBodyPartId || 78; // Use determined ID or default to 78
                        const forceAddKey = `247:${forceAddId}`;
                        if (partsMap.has(forceAddKey)) {
                            randomParts.push({
                                type: 'typed',
                                typeId: 247,
                                value: forceAddId
                            });
                            console.log(`[ENHANCEMENT] Force-added base body part ${forceAddKey} directly to randomParts`);
                        } else {
                            // Try any base body ID
                            for (const bodyId of [76, 77, 78, 79, 80]) {
                                const key = `247:${bodyId}`;
                                if (partsMap.has(key)) {
                                    randomParts.push({
                                        type: 'typed',
                                        typeId: 247,
                                        value: bodyId
                                    });
                                    console.log(`[ENHANCEMENT] Force-added base body part ${key} directly to randomParts`);
                                    break;
                                }
                            }
                        }
                    }
                } else {
                    console.log(`[ENHANCEMENT DEBUG] Base body already exists, skipping addition`);
                }
                
                // ALWAYS add stats247 if available and not already present
                // First check if we already have a stats247 part
                const hasStats247 = randomParts.some(p => {
                    if (p.type === 'typed' && p.typeId === 247) {
                        const partIdNum = parseInt(p.value);
                        // Check if it's NOT a base body (76-80)
                        if (partIdNum < 76 || partIdNum > 80) {
                            const partInfo = partsMap.get(`247:${p.value}`);
                            if (partInfo) {
                                const partPath = String(partInfo.path || '').toLowerCase();
                                const partType = String(partInfo.partType || '').toLowerCase();
                                const spawnCode = String(partInfo.spawnCode || '').toLowerCase();
                                // Check if it's a stats part (not firmware, not base body)
                                const isFirmware = spawnCode.includes('firmware') || partPath.includes('firmware');
                                const isStats = partPath.includes('stats') || partPath.includes('stats2') || partPath.includes('stats3') ||
                                              partType.includes('stats') || partType.includes('stat');
                                return isStats && !isFirmware;
                            }
                        }
                    }
                    return false;
                });
                
                if (!hasStats247 && partsByTypeId.has(247)) {
                    // Get ALL parts from typeId 247 and find stats parts
                    const parts247 = partsByTypeId.get(247) || [];
                    const stats247Parts = parts247.filter(p => {
                        // Get part ID number
                        const partIdStr = String(p.id || p.fullId || '');
                        let partIdNum = null;
                        if (partIdStr.includes(':')) {
                            const parts = partIdStr.split(':');
                            if (parts.length === 2 && parts[0] === '247') {
                                partIdNum = parseInt(parts[1]);
                            }
                        } else {
                            partIdNum = parseInt(partIdStr);
                        }
                        
                        // Exclude base body parts (76-80)
                        const isBaseBody = partIdNum !== null && !isNaN(partIdNum) && partIdNum >= 76 && partIdNum <= 80;
                        if (isBaseBody) return false;
                        
                        // Check if it's firmware
                        const spawnCode = String(p.spawnCode || '').toLowerCase();
                        const partPath = String(p.path || '').toLowerCase();
                        const partType = String(p.partType || '').toLowerCase();
                        const isFirmware = spawnCode.includes('firmware') || partPath.includes('firmware');
                        if (isFirmware) return false;
                        
                        // Check if it's a stats part
                        const isStats = partPath.includes('stats') || partPath.includes('stats2') || partPath.includes('stats3') ||
                                       partType.includes('stats') || partType.includes('stat') ||
                                       partPath.includes('main body') === false; // Main body is not stats
                        
                        return isStats;
                    });
                    
                    if (stats247Parts.length > 0) {
                        const randomStats = getRandomItem(stats247Parts);
                        if (randomStats) {
                            const partId = getPartId(randomStats);
                            if (partId && partId.typeId === 247) {
                                const partIdNum = parseInt(partId.partId);
                                // Double check it's not base body
                                if (partIdNum < 76 || partIdNum > 80) {
                                    // Use safeAddPart to validate and prevent duplicates
                                    const partToAdd = {
                                        type: 'typed',
                                        typeId: 247,
                                        value: partIdNum
                                    };
                                    safeAddPart(partToAdd);
                                }
                            }
                        }
                    } else {
                        // Last resort: get ANY part from 247 that's not base body (76-80) and not firmware
                        const anyNonBaseBodyPart = parts247.find(p => {
                            const partIdStr = String(p.id || p.fullId || '');
                            let partIdNum = null;
                            if (partIdStr.includes(':')) {
                                const parts = partIdStr.split(':');
                                if (parts.length === 2 && parts[0] === '247') {
                                    partIdNum = parseInt(parts[1]);
                                }
                            } else {
                                partIdNum = parseInt(partIdStr);
                            }
                            const isBaseBody = partIdNum !== null && !isNaN(partIdNum) && partIdNum >= 76 && partIdNum <= 80;
                            const spawnCode = String(p.spawnCode || '').toLowerCase();
                            const partPath = String(p.path || '').toLowerCase();
                            const isFirmware = spawnCode.includes('firmware') || partPath.includes('firmware');
                            return !isBaseBody && !isFirmware;
                        });
                        
                        if (anyNonBaseBodyPart) {
                            const partId = getPartId(anyNonBaseBodyPart);
                            if (partId && partId.typeId === 247) {
                                const partIdNum = parseInt(partId.partId);
                                if (partIdNum < 76 || partIdNum > 80) {
                                    // Use safeAddPart to validate and prevent duplicates
                                    const partToAdd = {
                                        type: 'typed',
                                        typeId: 247,
                                        value: partIdNum
                                    };
                                    safeAddPart(partToAdd);
                                }
                            }
                        }
                    }
                }
                
                // Always add firmware247 if available and not already present
                // SKIP firmware for weapons (weapons don't use firmware)
                if (!isWeapon && !isHeavyWeapon) {
                    // Get firmware247 parts directly from typeId 247 if not in categorized parts
                    let firmware247Parts = partsByCategory.firmware247;
                    if (firmware247Parts.length === 0 && partsByTypeId.has(247)) {
                        const parts247 = partsByTypeId.get(247) || [];
                        firmware247Parts = parts247.filter(p => {
                            const spawnCode = String(p.spawnCode || '').toLowerCase();
                            const partPath = String(p.path || '').toLowerCase();
                            const partName = String(p.name || '').toLowerCase();
                            // Also check by part ID to ensure Skillcraft (247:248) is included
                            const fullId = String(p.fullId || p.id || '');
                            let partIdNum = null;
                            if (fullId.includes(':')) {
                                const parts = fullId.split(':');
                                if (parts.length >= 2) {
                                    partIdNum = parseInt(parts[parts.length - 1]);
                                }
                            } else if (!isNaN(parseInt(fullId))) {
                                partIdNum = parseInt(fullId);
                            }
                            const isSkillcraftById = partIdNum === 248 && (p.typeId === 247 || p.typeId === undefined);
                            return spawnCode.includes('firmware') || partPath.includes('firmware') || 
                                   spawnCode.includes('skillcraft') || partName.includes('skillcraft') || isSkillcraftById;
                        });
                    }
                    
                    const hasFirmware247 = randomParts.some(p => {
                        if (p.type === 'typed' && p.typeId === 247) {
                            const partInfo = partsMap.get(`247:${p.value}`);
                            if (partInfo) {
                                const spawnCode = String(partInfo.spawnCode || '').toLowerCase();
                                const partPath = String(partInfo.path || '').toLowerCase();
                                return spawnCode.includes('firmware') || partPath.includes('firmware');
                            }
                        }
                        return false;
                    });
                    
                    // Only add firmware if we don't already have one (only one firmware per item)
                    if (!hasFirmware247 && firmware247Parts.length > 0) {
                        const randomFirmware = getRandomItem(firmware247Parts);
                        if (randomFirmware) {
                            const partId = getPartId(randomFirmware);
                            if (partId && partId.typeId === 247) {
                                const partIdNum = parseInt(partId.partId) || partId.partId;
                                // Use safeAddPart to validate and prevent duplicates (also checks for existing firmware)
                                const partToAdd = {
                                    type: 'typed',
                                    typeId: 247,
                                    value: partIdNum
                                };
                                safeAddPart(partToAdd);
                            }
                        }
                    }
                }
            }
            
            // Special handling for Grenades: Ensure rarity and base (body) are ALWAYS added
            if (isGrenade) {
                const DEBUG = true;
                if (DEBUG) console.log(`[GRENADE DEBUG] Starting grenade special handling for typeId ${typeId}`);
                if (DEBUG) console.log(`[GRENADE DEBUG] Current randomParts:`, randomParts);
                if (DEBUG) console.log(`[GRENADE DEBUG] partsByCategory.rarity length:`, partsByCategory.rarity.length);
                if (DEBUG) console.log(`[GRENADE DEBUG] partsByCategory.base length:`, partsByCategory.base.length);
                if (DEBUG) console.log(`[GRENADE DEBUG] partsByTypeId.get(${typeId}) length:`, (partsByTypeId.get(typeId) || []).length);
                
                // Ensure rarity is added from grenade's own typeId
                const hasRarity = randomParts.some(p => {
                    if (p.type === 'simple') {
                        const partInfo = partsMap.get(p.value);
                        if (partInfo) {
                            const partTypeId = partInfo.typeId || typeId;
                            if (partTypeId === typeId) {
                                const partType = String(partInfo.partType || '').toLowerCase();
                                const partName = String(partInfo.name || '').toLowerCase();
                                const partPath = String(partInfo.path || '').toLowerCase();
                                return partType.includes('rarity') || partType === 'comp' || 
                                       partName.includes('rarity') || partName.includes('common') || 
                                       partName.includes('uncommon') || partName.includes('rare') || 
                                       partName.includes('epic') || partName.includes('legendary') ||
                                       partPath.includes('rarity') || partPath.includes('rarities');
                            }
                        }
                    } else if (p.type === 'typed') {
                        if (p.typeId === typeId) {
                            const partInfo = partsMap.get(`${p.typeId}:${p.value}`);
                            if (partInfo) {
                                const partType = String(partInfo.partType || '').toLowerCase();
                                const partName = String(partInfo.name || '').toLowerCase();
                                const partPath = String(partInfo.path || '').toLowerCase();
                                return partType.includes('rarity') || partType === 'comp' || 
                                       partName.includes('rarity') || partName.includes('common') || 
                                       partName.includes('uncommon') || partName.includes('rare') || 
                                       partName.includes('epic') || partName.includes('legendary') ||
                                       partPath.includes('rarity') || partPath.includes('rarities');
                            }
                        }
                    }
                    return false;
                });
                
                if (DEBUG) console.log(`[GRENADE DEBUG] hasRarity:`, hasRarity);
                
                if (!hasRarity) {
                    // Get rarity from grenade's own parts - search directly
                    const grenadeParts = partsByTypeId.get(typeId) || [];
                    if (DEBUG) console.log(`[GRENADE DEBUG] Searching ${grenadeParts.length} grenade parts for rarity`);
                    if (DEBUG) console.log(`[GRENADE DEBUG] Sample grenade parts:`, grenadeParts.slice(0, 3).map(p => ({
                        id: p.id,
                        fullId: p.fullId,
                        typeId: p.typeId,
                        partType: p.partType,
                        name: p.name,
                        path: p.path
                    })));
                    
                    let rarityPart = grenadeParts.find(p => {
                        const partType = String(p.partType || '').toLowerCase();
                        const partName = String(p.name || '').toLowerCase();
                        const partPath = String(p.path || '').toLowerCase();
                        return partType.includes('rarity') || partType === 'comp' || 
                               partName.includes('rarity') || partName.includes('common') || 
                               partName.includes('uncommon') || partName.includes('rare') || 
                               partName.includes('epic') || partName.includes('legendary') ||
                               partPath.includes('rarity') || partPath.includes('rarities');
                    });
                    
                    if (DEBUG) console.log(`[GRENADE DEBUG] First rarity search result:`, rarityPart ? {
                        id: rarityPart.id,
                        fullId: rarityPart.fullId,
                        typeId: rarityPart.typeId,
                        partType: rarityPart.partType,
                        name: rarityPart.name,
                        path: rarityPart.path
                    } : 'NOT FOUND');
                    
                    if (!rarityPart) {
                        // Try searching by path patterns
                        rarityPart = grenadeParts.find(p => {
                            const partPath = String(p.path || '').toLowerCase();
                            return partPath.includes('rarities') || partPath.includes('rarity');
                        });
                        if (DEBUG) console.log(`[GRENADE DEBUG] Second rarity search (by path) result:`, rarityPart ? {
                            id: rarityPart.id,
                            fullId: rarityPart.fullId,
                            typeId: rarityPart.typeId,
                            partType: rarityPart.partType,
                            name: rarityPart.name,
                            path: rarityPart.path
                        } : 'NOT FOUND');
                    }
                    
                    if (rarityPart) {
                        if (DEBUG) console.log(`[GRENADE DEBUG] Found rarity part, adding to randomParts`);
                        const partId = getPartId(rarityPart);
                        if (partId) {
                            let partToAdd;
                            if (partId.typeId === typeId) {
                                partToAdd = {
                                    type: 'simple',
                                    value: parseInt(partId.partId) || partId.partId
                                };
                            } else {
                                partToAdd = {
                                    type: 'typed',
                                    typeId: partId.typeId,
                                    value: parseInt(partId.partId) || partId.partId
                                };
                            }
                            safeAddPart(partToAdd);
                        }
                    } else {
                        if (DEBUG) console.log(`[GRENADE DEBUG] No rarity found in grenade parts, trying categorized rarity`);
                        // Last resort: use categorized rarity (filtered for grenade's typeId)
                        const localRarityParts = partsByCategory.rarity.filter(p => {
                            const partTypeId = p.typeId || typeId;
                            return partTypeId === typeId;
                        });
                        if (DEBUG) console.log(`[GRENADE DEBUG] Filtered localRarityParts length:`, localRarityParts.length);
                        if (localRarityParts.length > 0) {
                            if (DEBUG) console.log(`[GRENADE DEBUG] Using categorized rarity part`);
                            const randomRarity = getRandomItem(localRarityParts);
                            if (randomRarity) {
                                const partId = getPartId(randomRarity);
                                if (partId) {
                                    let partToAdd;
                                    if (partId.typeId === typeId) {
                                        partToAdd = {
                                            type: 'simple',
                                            value: parseInt(partId.partId) || partId.partId
                                        };
                                    } else {
                                        partToAdd = {
                                            type: 'typed',
                                            typeId: partId.typeId,
                                            value: parseInt(partId.partId) || partId.partId
                                        };
                                    }
                                    safeAddPart(partToAdd);
                                }
                            }
                        } else {
                            if (DEBUG) console.log(`[GRENADE DEBUG] WARNING: No rarity found at all for grenade typeId ${typeId}`);
                        }
                    }
                }
                
                // Ensure base (body) is added
                if (DEBUG) console.log(`[GRENADE DEBUG] Checking for base (body)...`);
                const hasBase = randomParts.some(p => {
                    if (p.type === 'simple') {
                        const partInfo = partsMap.get(p.value);
                        if (partInfo) {
                            const partType = String(partInfo.partType || '').toLowerCase();
                            const partPath = String(partInfo.path || '').toLowerCase();
                            return partType === 'base' || partPath === 'base' || partPath.includes('base');
                        }
                    } else if (p.type === 'typed') {
                        if (p.typeId === typeId) {
                            const partInfo = partsMap.get(`${p.typeId}:${p.value}`);
                            if (partInfo) {
                                const partType = String(partInfo.partType || '').toLowerCase();
                                const partPath = String(partInfo.path || '').toLowerCase();
                                return partType === 'base' || partPath === 'base' || partPath.includes('base');
                            }
                        }
                    }
                    return false;
                });
                
                if (DEBUG) console.log(`[GRENADE DEBUG] hasBase:`, hasBase);
                if (DEBUG) console.log(`[GRENADE DEBUG] partsByCategory.base length:`, partsByCategory.base.length);
                
                if (!hasBase) {
                    // First try categorized base parts
                    if (partsByCategory.base.length > 0) {
                        if (DEBUG) console.log(`[GRENADE DEBUG] Trying to add base from categorized parts`);
                        const added = addPartFromCategory('base', true);
                        if (DEBUG) console.log(`[GRENADE DEBUG] addPartFromCategory('base') returned:`, added);
                    }
                    
                    // Check again if base was added
                    const hasBaseAfterCategory = randomParts.some(p => {
                        if (p.type === 'simple') {
                            const partInfo = partsMap.get(p.value);
                            if (partInfo) {
                                const partType = String(partInfo.partType || '').toLowerCase();
                                const partPath = String(partInfo.path || '').toLowerCase();
                                return partType === 'base' || partPath === 'base' || partPath.includes('base');
                            }
                        } else if (p.type === 'typed') {
                            if (p.typeId === typeId) {
                                const partInfo = partsMap.get(`${p.typeId}:${p.value}`);
                                if (partInfo) {
                                    const partType = String(partInfo.partType || '').toLowerCase();
                                    const partPath = String(partInfo.path || '').toLowerCase();
                                    return partType === 'base' || partPath === 'base' || partPath.includes('base');
                                }
                            }
                        }
                        return false;
                    });
                    
                    // If still no base, search directly in grenade's parts
                    if (!hasBaseAfterCategory) {
                        if (DEBUG) console.log(`[GRENADE DEBUG] Still no base, searching grenade parts directly`);
                        const grenadeParts = partsByTypeId.get(typeId) || [];
                        if (DEBUG) console.log(`[GRENADE DEBUG] Searching ${grenadeParts.length} grenade parts for base`);
                        if (DEBUG) console.log(`[GRENADE DEBUG] Sample grenade parts for base search:`, grenadeParts.slice(0, 5).map(p => ({
                            id: p.id,
                            fullId: p.fullId,
                            typeId: p.typeId,
                            partType: p.partType,
                            name: p.name,
                            path: p.path
                        })));
                        
                        let basePart = grenadeParts.find(p => {
                            const partType = String(p.partType || '').toLowerCase();
                            const partPath = String(p.path || '').toLowerCase();
                            return partType === 'base' || partPath === 'base' || partPath.includes('base');
                        });
                        
                        if (DEBUG) console.log(`[GRENADE DEBUG] Base part search result:`, basePart ? {
                            id: basePart.id,
                            fullId: basePart.fullId,
                            typeId: basePart.typeId,
                            partType: basePart.partType,
                            name: basePart.name,
                            path: basePart.path
                        } : 'NOT FOUND');
                        
                        if (basePart) {
                            if (DEBUG) console.log(`[GRENADE DEBUG] Found base part, adding to randomParts`);
                            const partId = getPartId(basePart);
                            if (partId) {
                                let partToAdd;
                                if (partId.typeId === typeId) {
                                    partToAdd = {
                                        type: 'simple',
                                        value: parseInt(partId.partId) || partId.partId
                                    };
                                    if (DEBUG) console.log(`[GRENADE DEBUG] Adding base as simple part:`, parseInt(partId.partId) || partId.partId);
                                } else {
                                    partToAdd = {
                                        type: 'typed',
                                        typeId: partId.typeId,
                                        value: parseInt(partId.partId) || partId.partId
                                    };
                                    if (DEBUG) console.log(`[GRENADE DEBUG] Adding base as typed part:`, partId.typeId, parseInt(partId.partId) || partId.partId);
                                }
                                if (safeAddPart(partToAdd)) {
                                    if (DEBUG) console.log(`[GRENADE DEBUG] Successfully added base part`);
                                } else {
                                    if (DEBUG) console.log(`[GRENADE DEBUG] Failed to add base part (duplicate or invalid)`);
                                }
                            }
                        } else {
                            if (DEBUG) console.log(`[GRENADE DEBUG] WARNING: No base found at all for grenade typeId ${typeId}`);
                        }
                    }
                }
                
                if (DEBUG) {
                    const finalHasRarity = randomParts.some(p => {
                        if (p.type === 'simple') {
                            const partInfo = partsMap.get(p.value);
                            if (partInfo) {
                                const partTypeId = partInfo.typeId || typeId;
                                if (partTypeId === typeId) {
                                    const partType = String(partInfo.partType || '').toLowerCase();
                                    const partName = String(partInfo.name || '').toLowerCase();
                                    const partPath = String(partInfo.path || '').toLowerCase();
                                    return partType.includes('rarity') || partType === 'comp' || 
                                           partName.includes('rarity') || partName.includes('common') || 
                                           partName.includes('uncommon') || partName.includes('rare') || 
                                           partName.includes('epic') || partName.includes('legendary') ||
                                           partPath.includes('rarity') || partPath.includes('rarities');
                                }
                            }
                        } else if (p.type === 'typed' && p.typeId === typeId) {
                            const partInfo = partsMap.get(`${p.typeId}:${p.value}`);
                            if (partInfo) {
                                const partType = String(partInfo.partType || '').toLowerCase();
                                const partName = String(partInfo.name || '').toLowerCase();
                                const partPath = String(partInfo.path || '').toLowerCase();
                                return partType.includes('rarity') || partType === 'comp' || 
                                       partName.includes('rarity') || partName.includes('common') || 
                                       partName.includes('uncommon') || partName.includes('rare') || 
                                       partName.includes('epic') || partName.includes('legendary') ||
                                       partPath.includes('rarity') || partPath.includes('rarities');
                            }
                        }
                        return false;
                    });
                    
                    const finalHasBase = randomParts.some(p => {
                        if (p.type === 'simple') {
                            const partInfo = partsMap.get(p.value);
                            if (partInfo) {
                                const partType = String(partInfo.partType || '').toLowerCase();
                                const partPath = String(partInfo.path || '').toLowerCase();
                                return partType === 'base' || partPath === 'base' || partPath.includes('base');
                            }
                        } else if (p.type === 'typed' && p.typeId === typeId) {
                            const partInfo = partsMap.get(`${p.typeId}:${p.value}`);
                            if (partInfo) {
                                const partType = String(partInfo.partType || '').toLowerCase();
                                const partPath = String(partInfo.path || '').toLowerCase();
                                return partType === 'base' || partPath === 'base' || partPath.includes('base');
                            }
                        }
                        return false;
                    });
                    
                    console.log(`[GRENADE DEBUG] FINAL CHECK - hasRarity:`, finalHasRarity, `hasBase:`, finalHasBase);
                    console.log(`[GRENADE DEBUG] Final randomParts:`, randomParts);
                }
                
                // Check if firmware245 is already added
                const hasFirmware245 = randomParts.some(p => {
                    if (p.type === 'typed' && p.typeId === 245) {
                        const partInfo = partsMap.get(`245:${p.value}`);
                        if (partInfo) {
                            const spawnCode = String(partInfo.spawnCode || '').toLowerCase();
                            const partPath = String(partInfo.path || '').toLowerCase();
                            return spawnCode.includes('firmware') || partPath.includes('firmware');
                        }
                    }
                    return false;
                });
                
                // Only add firmware if we don't already have one, and NOT for weapons
                if (!isWeapon && !isHeavyWeapon && !hasFirmware245 && partsByCategory.firmware245.length > 0) {
                    addPartFromCategory('firmware245', false);
                }
                
                // Check if parts245 is already added
                const hasParts245 = randomParts.some(p => {
                    if (p.type === 'typed' && p.typeId === 245) {
                        const partInfo = partsMap.get(`245:${p.value}`);
                        if (partInfo) {
                            const spawnCode = String(partInfo.spawnCode || '').toLowerCase();
                            const partPath = String(partInfo.path || '').toLowerCase();
                            return !spawnCode.includes('firmware') && !partPath.includes('firmware');
                        }
                    }
                    return false;
                });
                
                if (!hasParts245 && partsByCategory.parts245.length > 0) {
                    addPartFromCategory('parts245', false);
                }
            }
            
            // Special handling for Repkits: If rarity is legendary, add legendary part (Augment)
            // Also ensure firmware243 and parts243 are added if available
            if (isRepkit) {
                const DEBUG_REPKIT = true;
                if (DEBUG_REPKIT) console.log(`[REPKIT DEBUG] Starting repkit special handling for typeId ${typeId}`);
                if (DEBUG_REPKIT) console.log(`[REPKIT DEBUG] Current randomParts:`, randomParts);
                
                // Check ALL rarity parts to see if ANY are legendary
                // Get all rarity parts from randomParts
                const allRarityParts = randomParts.filter(p => {
                    if (p.type === 'simple') {
                        // Try fullId first, then fallback to just value
                        let partInfo = partsMap.get(`${typeId}:${p.value}`);
                        if (!partInfo) {
                            partInfo = partsMap.get(p.value);
                        }
                        if (partInfo) {
                            const partTypeId = partInfo.typeId || typeId;
                            if (partTypeId === typeId) {
                                const partType = String(partInfo.partType || '').toLowerCase();
                                const partName = String(partInfo.name || '').toLowerCase();
                                const partPath = String(partInfo.path || '').toLowerCase();
                                return (partType.includes('rarity') || partType === 'comp' || 
                                       partName.includes('rarity') || partName.includes('common') || 
                                       partName.includes('uncommon') || partName.includes('rare') || 
                                       partName.includes('epic') || partName.includes('legendary') ||
                                       partPath.includes('rarity') || partPath.includes('rarities')) &&
                                       !partType.includes('skill') && !partPath.includes('skill');
                            }
                        }
                    } else if (p.type === 'typed' && p.typeId === typeId) {
                        const partInfo = partsMap.get(`${p.typeId}:${p.value}`);
                        if (partInfo) {
                            const partType = String(partInfo.partType || '').toLowerCase();
                            const partName = String(partInfo.name || '').toLowerCase();
                            const partPath = String(partInfo.path || '').toLowerCase();
                            return (partType.includes('rarity') || partType === 'comp' || 
                                   partName.includes('rarity') || partName.includes('common') || 
                                   partName.includes('uncommon') || partName.includes('rare') || 
                                   partName.includes('epic') || partName.includes('legendary') ||
                                   partPath.includes('rarity') || partPath.includes('rarities')) &&
                                   !partType.includes('skill') && !partPath.includes('skill');
                        }
                    }
                    return false;
                });
                
                if (DEBUG_REPKIT) console.log(`[REPKIT DEBUG] Found ${allRarityParts.length} rarity parts:`, allRarityParts);
                
                // Get all rarity parts for this repkit to find the max value
                const repkitRarityParts = (partsByTypeId.get(typeId) || []).filter(p => {
                    const pt = String(p.partType || '').toLowerCase();
                    const pn = String(p.name || '').toLowerCase();
                    const pp = String(p.path || '').toLowerCase();
                    return pt.includes('rarity') || pt === 'comp' || pn.includes('rarity') || 
                           pn.includes('common') || pn.includes('uncommon') || pn.includes('rare') || 
                           pn.includes('epic') || pn.includes('legendary') || pp.includes('rarity');
                });
                
                let maxRarityValue = 0;
                repkitRarityParts.forEach(p => {
                    const partIdStr = String(p.id || p.fullId || '');
                    let partIdNum = null;
                    if (partIdStr.includes(':')) {
                        const parts = partIdStr.split(':');
                        if (parts.length === 2 && parts[0] === String(typeId)) {
                            partIdNum = parseInt(parts[1]);
                        }
                    } else {
                        partIdNum = parseInt(partIdStr);
                    }
                    if (partIdNum !== null && !isNaN(partIdNum) && partIdNum > maxRarityValue) {
                        maxRarityValue = partIdNum;
                    }
                });
                
                if (DEBUG_REPKIT) console.log(`[REPKIT DEBUG] maxRarityValue for typeId ${typeId}: ${maxRarityValue}`);
                
                // SIMPLE LOGIC: If any rarity part has value == maxRarityValue, it's legendary
                let isLegendary = false;
                for (const rarityPart of allRarityParts) {
                    const partValue = parseInt(rarityPart.value) || 0;
                    if (DEBUG_REPKIT) console.log(`[REPKIT DEBUG] Checking rarity part value: ${partValue} (raw: ${rarityPart.value}) vs maxRarityValue: ${maxRarityValue}`);
                    if (partValue === maxRarityValue && maxRarityValue > 0) {
                        isLegendary = true;
                        if (DEBUG_REPKIT) console.log(`[REPKIT DEBUG] Legendary detected: rarity value ${partValue} equals maxRarityValue ${maxRarityValue}`);
                        break;
                    }
                }
                
                if (DEBUG_REPKIT) console.log(`[REPKIT DEBUG] Final isLegendary: ${isLegendary}`);
                
                // Check if Augment (legendary part) is already added
                const hasAugment = randomParts.some(p => {
                    if (p.type === 'simple') {
                        let partInfo = partsMap.get(`${typeId}:${p.value}`);
                        if (!partInfo) {
                            partInfo = partsMap.get(p.value);
                        }
                        if (partInfo) {
                            const partTypeId = partInfo.typeId || typeId;
                            if (partTypeId === typeId) {
                                const partType = String(partInfo.partType || '').toLowerCase();
                                const partPath = String(partInfo.path || '').toLowerCase();
                                return partType === 'augment' || partPath === 'augment' || partPath.includes('augment');
                            }
                        }
                    } else if (p.type === 'typed' && p.typeId === typeId) {
                        const partInfo = partsMap.get(`${p.typeId}:${p.value}`);
                        if (partInfo) {
                            const partType = String(partInfo.partType || '').toLowerCase();
                            const partPath = String(partInfo.path || '').toLowerCase();
                            return partType === 'augment' || partPath === 'augment' || partPath.includes('augment');
                        }
                    }
                    return false;
                });
                
                // If rarity is legendary, ALWAYS add Augment (legendary part)
                if (isLegendary && !hasAugment) {
                    if (DEBUG_REPKIT) console.log(`[REPKIT DEBUG] Legendary rarity detected, attempting to add Augment`);
                    
                    // SIMPLE: Get Augment directly from repkit's own typeId
                    const repkitParts = partsByTypeId.get(typeId) || [];
                    const augmentParts = repkitParts.filter(p => {
                        const partType = String(p.partType || '').toLowerCase();
                        const partPath = String(p.path || '').toLowerCase();
                        const spawnCode = String(p.spawnCode || '').toLowerCase();
                        return partType === 'augment' || partPath === 'augment' || partPath.includes('augment') || spawnCode.includes('augment') || spawnCode.includes('part_augment');
                    });
                    
                    if (DEBUG_REPKIT) console.log(`[REPKIT DEBUG] Found ${augmentParts.length} augment parts for typeId ${typeId}`);
                    
                    if (augmentParts.length > 0) {
                        const randomAugment = getRandomItem(augmentParts);
                        if (randomAugment) {
                            // Extract part value from id (format: "1" or "290:1")
                            let partValue = null;
                            const idStr = String(randomAugment.id || '');
                            if (idStr.includes(':')) {
                                partValue = parseInt(idStr.split(':')[1]);
                            } else {
                                partValue = parseInt(idStr);
                            }
                            
                            if (partValue !== null && !isNaN(partValue)) {
                                const partToAdd = {
                                    type: 'simple',
                                    value: partValue
                                };
                                if (safeAddPart(partToAdd)) {
                                    if (DEBUG_REPKIT) console.log(`[REPKIT DEBUG] Added augment part: ${partValue} (${randomAugment.name})`);
                                } else {
                                    if (DEBUG_REPKIT) console.log(`[REPKIT DEBUG] Failed to add augment part: ${partValue} (duplicate or invalid)`);
                                }
                            } else {
                                if (DEBUG_REPKIT) console.log(`[REPKIT DEBUG] ERROR: Could not extract part value from augment:`, randomAugment);
                            }
                        }
                    } else {
                        if (DEBUG_REPKIT) console.log(`[REPKIT DEBUG] ERROR: No augment parts found for typeId ${typeId}`);
                    }
                } else {
                    if (DEBUG_REPKIT) console.log(`[REPKIT DEBUG] Not adding augment - isLegendary: ${isLegendary}, hasAugment: ${hasAugment}`);
                }
                
                // Check if firmware243 is already added
                const hasFirmware243 = randomParts.some(p => {
                    if (p.type === 'typed' && p.typeId === 243) {
                        const partInfo = partsMap.get(`243:${p.value}`);
                        if (partInfo) {
                            const spawnCode = String(partInfo.spawnCode || '').toLowerCase();
                            const partPath = String(partInfo.path || '').toLowerCase();
                            return spawnCode.includes('firmware') || partPath.includes('firmware');
                        }
                    }
                    return false;
                });
                
                // Only add firmware if we don't already have one, and NOT for weapons
                if (!isWeapon && !isHeavyWeapon && !hasFirmware243 && partsByCategory.firmware243.length > 0) {
                    addPartFromCategory('firmware243', false);
                }
                
                // Check if parts243 is already added
                const hasParts243 = randomParts.some(p => {
                    if (p.type === 'typed' && p.typeId === 243) {
                        const partInfo = partsMap.get(`243:${p.value}`);
                        if (partInfo) {
                            const spawnCode = String(partInfo.spawnCode || '').toLowerCase();
                            const partPath = String(partInfo.path || '').toLowerCase();
                            return !spawnCode.includes('firmware') && !partPath.includes('firmware');
                        }
                    }
                    return false;
                });
                
                if (!hasParts243 && partsByCategory.parts243.length > 0) {
                    addPartFromCategory('parts243', false);
                }
            }
            
            // Special handling for Class Mods: Ensure rarity, body, skills, perks234, and firmware234 are added
            if (isClassMod) {
                const DEBUG_CLASSMOD = true;
                if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] Starting class mod special handling for typeId ${typeId}`);
                if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] Current randomParts:`, randomParts);
                if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] partsByCategory.rarity length:`, partsByCategory.rarity.length);
                if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] partsByCategory.body length:`, partsByCategory.body.length);
                if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] partsByCategory.skills length:`, partsByCategory.skills.length);
                if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] partsByCategory.stat234 length:`, partsByCategory.stat234.length);
                if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] partsByCategory.stat2_234 length:`, partsByCategory.stat2_234.length);
                if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] partsByCategory.statspecial_234 length:`, partsByCategory.statspecial_234.length);
                if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] partsByCategory.firmware234 length:`, partsByCategory.firmware234.length);
                if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] partsByTypeId.get(${typeId}) length:`, (partsByTypeId.get(typeId) || []).length);
                
                // Ensure rarity is added from class mod's own typeId
                const hasRarity = randomParts.some(p => {
                    if (p.type === 'simple') {
                        // Try fullId first, then fallback to just value
                        let partInfo = partsMap.get(`${typeId}:${p.value}`);
                        if (!partInfo) {
                            partInfo = partsMap.get(p.value);
                        }
                        if (partInfo) {
                            const partTypeId = partInfo.typeId || typeId;
                            if (partTypeId === typeId) {
                                const partType = String(partInfo.partType || '').toLowerCase();
                                const partName = String(partInfo.name || '').toLowerCase();
                                const partPath = String(partInfo.path || '').toLowerCase();
                                // Check if this is actually a rarity part (not a skill with same ID)
                                const isRarity = (partType.includes('rarity') || partType === 'comp' || 
                                               partName.includes('rarity') || partName.includes('common') || 
                                               partName.includes('uncommon') || partName.includes('rare') || 
                                               partName.includes('epic') || partName.includes('legendary') ||
                                               partPath.includes('rarity')) &&
                                               !partType.includes('skill') && !partPath.includes('skill');
                                return isRarity;
                            }
                        }
                    } else if (p.type === 'typed' && p.typeId === typeId) {
                        const partInfo = partsMap.get(`${p.typeId}:${p.value}`);
                        if (partInfo) {
                            const partType = String(partInfo.partType || '').toLowerCase();
                            const partName = String(partInfo.name || '').toLowerCase();
                            const partPath = String(partInfo.path || '').toLowerCase();
                            // Check if this is actually a rarity part (not a skill with same ID)
                            const isRarity = (partType.includes('rarity') || partType === 'comp' || 
                                           partName.includes('rarity') || partName.includes('common') || 
                                           partName.includes('uncommon') || partName.includes('rare') || 
                                           partName.includes('epic') || partName.includes('legendary') ||
                                           partPath.includes('rarity')) &&
                                           !partType.includes('skill') && !partPath.includes('skill');
                            return isRarity;
                        }
                    }
                    return false;
                });
                
                if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] hasRarity:`, hasRarity);
                
                if (!hasRarity) {
                    // Get rarity from class mod's own parts
                    const classModParts = partsByTypeId.get(typeId) || [];
                    const rarityPart = classModParts.find(p => {
                        const partType = String(p.partType || '').toLowerCase();
                        const partName = String(p.name || '').toLowerCase();
                        const partPath = String(p.path || '').toLowerCase();
                        return partType.includes('rarity') || partType === 'comp' || 
                               partName.includes('rarity') || partName.includes('common') || 
                               partName.includes('uncommon') || partName.includes('rare') || 
                               partName.includes('epic') || partName.includes('legendary') ||
                               partPath.includes('rarity');
                    });
                    
                    if (rarityPart) {
                        if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] Found rarity part:`, rarityPart);
                        const partId = getPartId(rarityPart);
                        if (partId && partId.typeId === typeId) {
                            const partToAdd = {
                                type: 'simple',
                                value: parseInt(partId.partId) || partId.partId
                            };
                            if (safeAddPart(partToAdd)) {
                                if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] Added rarity part`);
                            }
                        }
                    } else {
                        // Fallback: use categorized rarity
                        const localRarityParts = partsByCategory.rarity.filter(p => {
                            const partTypeId = p.typeId || typeId;
                            return partTypeId === typeId;
                        });
                        if (localRarityParts.length > 0) {
                            const randomRarity = getRandomItem(localRarityParts);
                            if (randomRarity) {
                                const partId = getPartId(randomRarity);
                                if (partId && partId.typeId === typeId) {
                                    const partToAdd = {
                                        type: 'simple',
                                        value: parseInt(partId.partId) || partId.partId
                                    };
                                    if (safeAddPart(partToAdd)) {
                                        if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] Added rarity from categorized parts`);
                                    }
                                }
                            }
                        } else {
                            if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] WARNING: No rarity found for class mod typeId ${typeId}`);
                        }
                    }
                }
                
                // Ensure body is added
                const hasBody = randomParts.some(p => {
                    if (p.type === 'simple') {
                        const partInfo = partsMap.get(`${typeId}:${p.value}`) || partsMap.get(p.value);
                        if (partInfo && partInfo.typeId === typeId) {
                            const partType = String(partInfo.partType || '').toLowerCase();
                            const partPath = String(partInfo.path || '').toLowerCase();
                            return (partType.includes('body') || partType === 'body' || partPath.includes('body')) && 
                                   !partType.includes('accessory') && !partType.includes('legendary') && !partType.includes('special');
                        }
                    } else if (p.type === 'typed' && p.typeId === typeId) {
                        const partInfo = partsMap.get(`${p.typeId}:${p.value}`);
                        if (partInfo) {
                            const partType = String(partInfo.partType || '').toLowerCase();
                            const partPath = String(partInfo.path || '').toLowerCase();
                            return (partType.includes('body') || partType === 'body' || partPath.includes('body')) && 
                                   !partType.includes('accessory') && !partType.includes('legendary') && !partType.includes('special');
                        }
                    }
                    return false;
                });
                
                if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] hasBody:`, hasBody);
                
                if (!hasBody && partsByCategory.body.length > 0) {
                    if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] Trying to add body from categorized parts`);
                    addPartFromCategory('body', true);
                } else if (!hasBody) {
                    // Fallback: find body from class mod's own parts
                    const classModParts = partsByTypeId.get(typeId) || [];
                    const bodyPart = classModParts.find(p => {
                        const partType = String(p.partType || '').toLowerCase();
                        const partPath = String(p.path || '').toLowerCase();
                        return (partType.includes('body') || partType === 'body' || String(p.partType || '') === 'Body' || partPath.includes('body') || partPath.includes('Body')) && 
                               !partType.includes('accessory') && !partType.includes('legendary') && !partType.includes('special');
                    });
                    
                    if (bodyPart) {
                        if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] Found body part:`, bodyPart);
                        const partId = getPartId(bodyPart);
                        if (partId && partId.typeId === typeId) {
                            const partToAdd = {
                                type: 'simple',
                                value: parseInt(partId.partId) || partId.partId
                            };
                            if (safeAddPart(partToAdd)) {
                                if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] Added body part`);
                            }
                        }
                    } else {
                        if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] WARNING: No body found for class mod typeId ${typeId}`);
                    }
                }
                
                // Check if stat234 or stat2_234 is already added
                const hasStat234 = randomParts.some(p => {
                    if (p.type === 'typed' && p.typeId === 234) {
                        const partInfo = partsMap.get(`234:${p.value}`);
                        if (partInfo) {
                            const spawnCode = String(partInfo.spawnCode || '').toLowerCase();
                            const partPath = String(partInfo.path || '').toLowerCase();
                            const partType = String(partInfo.partType || '').toLowerCase();
                            return (!spawnCode.includes('firmware') && !partPath.includes('firmware') && 
                                    (partType.includes('perk') || spawnCode.includes('stat') || partPath.includes('perk')));
                        }
                    }
                    return false;
                });
                
                const hasStat2_234 = randomParts.some(p => {
                    if (p.type === 'typed' && p.typeId === 234) {
                        const partInfo = partsMap.get(`234:${p.value}`);
                        if (partInfo) {
                            const spawnCode = String(partInfo.spawnCode || '').toLowerCase();
                            return (!spawnCode.includes('firmware') && (spawnCode.includes('stat2_') || spawnCode.includes('ClassMod.stat2')));
                        }
                    }
                    return false;
                });
                
                if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] hasStat234:`, hasStat234);
                if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] hasStat2_234:`, hasStat2_234);
                
                if (!hasStat234) {
                    // First try categorized parts
                    if (partsByCategory.stat234.length > 0) {
                        if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] Adding stat234 from categorized parts`);
                        addPartFromCategory('stat234', false);
                    }
                }
                
                if (!hasStat2_234) {
                    // First try categorized parts
                    if (partsByCategory.stat2_234.length > 0) {
                        if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] Adding stat2_234 from categorized parts`);
                        addPartFromCategory('stat2_234', false);
                    }
                }
                
                // Legacy fallback for backwards compatibility
                if (!hasStat234 && !hasStat2_234) {
                    // First try categorized parts
                    if (partsByCategory.stat234.length > 0 || partsByCategory.stat2_234.length > 0) {
                        if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] Adding stat234/stat2_234 from categorized parts (fallback)`);
                        if (partsByCategory.stat234.length > 0) {
                            addPartFromCategory('stat234', false);
                        } else if (partsByCategory.stat2_234.length > 0) {
                            addPartFromCategory('stat2_234', false);
                        }
                    } else {
                        // Fallback: get perks234 directly from typeId 234
                        if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] No perks234 in categorized parts, searching typeId 234 directly`);
                        if (partsByTypeId.has(234)) {
                            const parts234 = partsByTypeId.get(234) || [];
                            if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] Found ${parts234.length} total parts in typeId 234`);
                            const perkParts = parts234.filter(p => {
                                const spawnCode = String(p.spawnCode || '').toLowerCase();
                                const partPath = String(p.path || '').toLowerCase();
                                const partType = String(p.partType || '').toLowerCase();
                                const partName = String(p.name || '').toLowerCase();
                                return !spawnCode.includes('firmware') && !partPath.includes('firmware') && !partType.includes('firmware') &&
                                       (partType.includes('perk') || spawnCode.includes('stat') || partPath.includes('perk') || partName.includes('perk'));
                            });
                            
                            if (perkParts.length > 0) {
                                if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] Found ${perkParts.length} perk parts from typeId 234`);
                                const randomPerk = getRandomItem(perkParts);
                                if (randomPerk) {
                                    const partId = getPartId(randomPerk);
                                    if (partId && partId.typeId === 234) {
                                        const partToAdd = {
                                            type: 'typed',
                                            typeId: 234,
                                            value: parseInt(partId.partId) || partId.partId
                                        };
                                        if (safeAddPart(partToAdd)) {
                                            if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] Added perks234 part:`, parseInt(partId.partId) || partId.partId);
                                        }
                                    }
                                }
                            } else {
                                if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] WARNING: No perk parts found in typeId 234. Total parts: ${parts234.length}`);
                                if (DEBUG_CLASSMOD && parts234.length > 0) {
                                    console.log(`[CLASS MOD DEBUG] Sample parts:`, parts234.slice(0, 3).map(p => ({
                                        id: p.id,
                                        fullId: p.fullId,
                                        partType: p.partType,
                                        path: p.path,
                                        name: p.name
                                    })));
                                }
                            }
                        } else {
                            if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] ERROR: typeId 234 not found in partsByTypeId! Parts were not extracted.`);
                        }
                    }
                }
                
                // Check if firmware234 is already added
                const hasFirmware234 = randomParts.some(p => {
                    if (p.type === 'typed' && p.typeId === 234) {
                        const partInfo = partsMap.get(`234:${p.value}`);
                        if (partInfo) {
                            const spawnCode = String(partInfo.spawnCode || '').toLowerCase();
                            const partPath = String(partInfo.path || '').toLowerCase();
                            const partType = String(partInfo.partType || '').toLowerCase();
                            return spawnCode.includes('firmware') || partPath.includes('firmware') || partType.includes('firmware');
                        }
                    }
                    return false;
                });
                
                if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] hasFirmware234:`, hasFirmware234);
                
                // Only add firmware if we don't already have one, and NOT for weapons
                if (!isWeapon && !isHeavyWeapon && !hasFirmware234) {
                    // First try categorized parts
                    if (partsByCategory.firmware234.length > 0) {
                        if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] Adding firmware234 from categorized parts`);
                        addPartFromCategory('firmware234', false);
                    } else {
                        // Fallback: get firmware234 directly from typeId 234
                        if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] No firmware234 in categorized parts, searching typeId 234 directly`);
                        if (partsByTypeId.has(234)) {
                            const parts234 = partsByTypeId.get(234) || [];
                            if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] Found ${parts234.length} total parts in typeId 234`);
                            const firmwareParts = parts234.filter(p => {
                                const spawnCode = String(p.spawnCode || '').toLowerCase();
                                const partPath = String(p.path || '').toLowerCase();
                                const partType = String(p.partType || '').toLowerCase();
                                const partName = String(p.name || '').toLowerCase();
                                return spawnCode.includes('firmware') || partPath.includes('firmware') || partType.includes('firmware') || partName.includes('firmware');
                            });
                            
                            if (firmwareParts.length > 0) {
                                if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] Found ${firmwareParts.length} firmware parts from typeId 234`);
                                const randomFirmware = getRandomItem(firmwareParts);
                                if (randomFirmware) {
                                    const partId = getPartId(randomFirmware);
                                    if (partId && partId.typeId === 234) {
                                        const partToAdd = {
                                            type: 'typed',
                                            typeId: 234,
                                            value: parseInt(partId.partId) || partId.partId
                                        };
                                        if (safeAddPart(partToAdd)) {
                                            if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] Added firmware234 part:`, parseInt(partId.partId) || partId.partId);
                                        }
                                    }
                                }
                            } else {
                                if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] WARNING: No firmware parts found in typeId 234. Total parts: ${parts234.length}`);
                                if (DEBUG_CLASSMOD && parts234.length > 0) {
                                    console.log(`[CLASS MOD DEBUG] Sample parts:`, parts234.slice(0, 3).map(p => ({
                                        id: p.id,
                                        fullId: p.fullId,
                                        partType: p.partType,
                                        path: p.path,
                                        name: p.name
                                    })));
                                }
                            }
                        } else {
                            if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] ERROR: typeId 234 not found in partsByTypeId! Parts were not extracted.`);
                        }
                    }
                }
                
                // Ensure skills are added
                const hasSkills = randomParts.some(p => {
                    if (p.type === 'simple') {
                        const partInfo = partsMap.get(p.value);
                        if (partInfo) {
                            const partTypeId = partInfo.typeId || typeId;
                            if (partTypeId === typeId) {
                                const partType = String(partInfo.partType || '').toLowerCase();
                                const partPath = String(partInfo.path || '').toLowerCase();
                                return partType.includes('skill') || partPath.includes('skill');
                            }
                        }
                    } else if (p.type === 'typed' && p.typeId === typeId) {
                        const partInfo = partsMap.get(`${p.typeId}:${p.value}`);
                        if (partInfo) {
                            const partType = String(partInfo.partType || '').toLowerCase();
                            const partPath = String(partInfo.path || '').toLowerCase();
                            return partType.includes('skill') || partPath.includes('skill');
                        }
                    }
                    return false;
                });
                
                if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] hasSkills:`, hasSkills);
                
                if (!hasSkills) {
                    // First try categorized parts
                    if (partsByCategory.skills.length > 0) {
                        if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] Adding skills from categorized parts`);
                        addPartFromCategory('skills', true);
                    } else {
                        // Fallback: get skills directly from class mod's own typeId
                        if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] No skills in categorized parts, searching typeId ${typeId} directly`);
                        const classModParts = partsByTypeId.get(typeId) || [];
                        if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] Found ${classModParts.length} total parts in typeId ${typeId}`);
                        const skillParts = classModParts.filter(p => {
                            const partType = String(p.partType || '').toLowerCase();
                            const partPath = String(p.path || '').toLowerCase();
                            const partName = String(p.name || '').toLowerCase();
                            return partType.includes('skill') || partPath.includes('skill') || partName.includes('tier');
                        });
                        
                        if (skillParts.length > 0) {
                            if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] Found ${skillParts.length} skill parts from typeId ${typeId}`);
                            // Add 1-3 random skills
                            const numSkills = Math.floor(Math.random() * 3) + 1; // 1-3 skills
                            const selectedSkills = [];
                            for (let i = 0; i < numSkills && i < skillParts.length; i++) {
                                const availableSkills = skillParts.filter(s => !selectedSkills.includes(s));
                                if (availableSkills.length === 0) break;
                                const randomSkill = getRandomItem(availableSkills);
                                if (randomSkill) {
                                    selectedSkills.push(randomSkill);
                                    const partId = getPartId(randomSkill);
                                    if (partId && partId.typeId === typeId) {
                                        const partToAdd = {
                                            type: 'simple',
                                            value: parseInt(partId.partId) || partId.partId
                                        };
                                        if (safeAddPart(partToAdd)) {
                                            if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] Added skill part:`, parseInt(partId.partId) || partId.partId);
                                        }
                                    }
                                }
                            }
                        } else {
                            if (DEBUG_CLASSMOD) console.log(`[CLASS MOD DEBUG] WARNING: No skill parts found in typeId ${typeId}. Total parts: ${classModParts.length}`);
                            if (DEBUG_CLASSMOD && classModParts.length > 0) {
                                console.log(`[CLASS MOD DEBUG] Sample parts:`, classModParts.slice(0, 3).map(p => ({
                                    id: p.id,
                                    fullId: p.fullId,
                                    partType: p.partType,
                                    path: p.path,
                                    name: p.name
                                })));
                            }
                        }
                    }
                }
                
                if (DEBUG_CLASSMOD) {
                    const finalHasRarity = randomParts.some(p => {
                        if (p.type === 'simple') {
                            // Try fullId first, then fallback to just value
                            let partInfo = partsMap.get(`${typeId}:${p.value}`);
                            if (!partInfo) {
                                partInfo = partsMap.get(p.value);
                            }
                            if (partInfo) {
                                const partTypeId = partInfo.typeId || typeId;
                                if (partTypeId === typeId) {
                                    const partType = String(partInfo.partType || '').toLowerCase();
                                    const partPath = String(partInfo.path || '').toLowerCase();
                                    // Check if this is actually a rarity part (not a skill with same ID)
                                    return (partType.includes('rarity') || partType === 'comp' || partPath.includes('rarity')) &&
                                           !partType.includes('skill') && !partPath.includes('skill');
                                }
                            }
                        } else if (p.type === 'typed' && p.typeId === typeId) {
                            const partInfo = partsMap.get(`${p.typeId}:${p.value}`);
                            if (partInfo) {
                                const partType = String(partInfo.partType || '').toLowerCase();
                                const partPath = String(partInfo.path || '').toLowerCase();
                                // Check if this is actually a rarity part (not a skill with same ID)
                                return (partType.includes('rarity') || partType === 'comp' || partPath.includes('rarity')) &&
                                       !partType.includes('skill') && !partPath.includes('skill');
                            }
                        }
                        return false;
                    });
                    
                    const finalHasBody = randomParts.some(p => {
                        if (p.type === 'simple') {
                            const partInfo = partsMap.get(p.value);
                            if (partInfo) {
                                const partType = String(partInfo.partType || '').toLowerCase();
                                return partType.includes('body') && !partType.includes('accessory');
                            }
                        }
                        return false;
                    });
                    
                    const finalHasSkills = randomParts.some(p => {
                        if (p.type === 'simple') {
                            const partInfo = partsMap.get(p.value);
                            if (partInfo) {
                                const partTypeId = partInfo.typeId || typeId;
                                if (partTypeId === typeId) {
                                    const partType = String(partInfo.partType || '').toLowerCase();
                                    const partPath = String(partInfo.path || '').toLowerCase();
                                    return partType.includes('skill') || partPath.includes('skill');
                                }
                            }
                        } else if (p.type === 'typed' && p.typeId === typeId) {
                            const partInfo = partsMap.get(`${p.typeId}:${p.value}`);
                            if (partInfo) {
                                const partType = String(partInfo.partType || '').toLowerCase();
                                const partPath = String(partInfo.path || '').toLowerCase();
                                return partType.includes('skill') || partPath.includes('skill');
                            }
                        }
                        return false;
                    });
                    
                    console.log(`[CLASS MOD DEBUG] FINAL CHECK - hasRarity:`, finalHasRarity, `hasBody:`, finalHasBody, `hasSkills:`, finalHasSkills);
                    console.log(`[CLASS MOD DEBUG] Final randomParts:`, randomParts);
                }
            }
            
            // Special handling for Heavy Weapons: Ensure firmware244 is added if available
            if (isHeavyWeapon) {
                // Check if firmware244 is already added
                const hasFirmware244 = randomParts.some(p => {
                    if (p.type === 'typed' && p.typeId === 244) {
                        return true;
                    }
                    return false;
                });
                
                if (!hasFirmware244 && partsByCategory.firmware244.length > 0) {
                    addPartFromCategory('firmware244', false);
                }
            }
            
            // Set manufacturer and type ID FIRST
            // typeInfo already declared above
            if (typeInfo) {
                // For class mods, use "Class Mods" as manufacturer (dropdown groups all class mod characters under "Class Mods")
                let manufacturer = typeInfo.manufacturer || '';
                if (isClassMod) {
                    // Always use "Class Mods" for class mods since the dropdown groups them this way
                    manufacturer = 'Class Mods';
                }
                // Ensure manufacturer is properly set for heavy weapons
                if (isHeavyWeapon) {
                    // Heavy weapons should have manufacturer in typeInfo, but if missing, try to get from parts
                    if (!manufacturer || manufacturer.trim() === '') {
                        // Try to extract from first body part's spawnCode (e.g., "JAK_HW.part_body...")
                        const bodyParts = partsByCategory.body || [];
                        if (bodyParts.length > 0) {
                            const firstBodyPart = bodyParts[0];
                            const spawnCode = String(firstBodyPart.spawnCode || '').toUpperCase();
                            // Extract manufacturer prefix (e.g., "JAK", "TED", "VLAD")
                            const manufacturerPrefixes = {
                                'JAK': 'Jakobs', 'TED': 'Tediore', 'VLAD': 'Vladof', 
                                'MAL': 'Maliwan', 'TOR': 'Torgue', 'HYP': 'Hyperion',
                                'DAH': 'Dahl', 'COV': 'CoV', 'ATL': 'Atlas'
                            };
                            for (const [prefix, name] of Object.entries(manufacturerPrefixes)) {
                                if (spawnCode.startsWith(prefix + '_')) {
                                    manufacturer = name;
                                    break;
                                }
                            }
                        }
                        // If still no manufacturer, use a default or leave empty
                        if (!manufacturer || manufacturer.trim() === '') {
                            console.warn(`[RANDOM GENERATOR] Heavy weapon typeId ${typeId} has no manufacturer in typeInfo`);
                        }
                    }
                }
                const manufacturerSelect = document.getElementById('manufacturer');
                if (manufacturerSelect && manufacturer && manufacturer.trim() !== '') {
                    manufacturerSelect.value = manufacturer;
                    // Store previous value for change detection
                    manufacturerSelect.dataset.previousValue = manufacturer;
                    // Trigger change event to update typeId dropdown
                    manufacturerSelect.dispatchEvent(new Event('change', { bubbles: true }));
                }
                if (window.updateTypeIdDropdown) {
                    window.updateTypeIdDropdown();
                }
                const typeIdSelect = document.getElementById('typeId');
                if (typeIdSelect) {
                    typeIdSelect.value = String(typeId);
                    // Trigger change event to ensure UI updates and any listeners are notified
                    typeIdSelect.dispatchEvent(new Event('change', { bubbles: true }));
                }
            } else if (isClassMod) {
                // Fallback for class mods if typeInfo doesn't exist
                const manufacturerSelect = document.getElementById('manufacturer');
                if (manufacturerSelect) {
                    manufacturerSelect.value = 'Class Mods';
                    manufacturerSelect.dataset.previousValue = 'Class Mods';
                    manufacturerSelect.dispatchEvent(new Event('change', { bubbles: true }));
                }
                if (window.updateTypeIdDropdown) {
                    window.updateTypeIdDropdown();
                }
                const typeIdSelect = document.getElementById('typeId');
                if (typeIdSelect) {
                    typeIdSelect.value = String(typeId);
                    typeIdSelect.dispatchEvent(new Event('change', { bubbles: true }));
                }
            } else if (isHeavyWeapon) {
                // Fallback for heavy weapons if typeInfo doesn't exist
                const manufacturerSelect = document.getElementById('manufacturer');
                let manufacturer = '';
                if (typeIdMap.has(typeId)) {
                    const typeInfoFromMap = typeIdMap.get(typeId);
                    manufacturer = typeInfoFromMap?.manufacturer || '';
                    // Try to extract from parts if manufacturer is still missing
                    if (!manufacturer || manufacturer.trim() === '') {
                        const bodyParts = partsByCategory.body || [];
                        if (bodyParts.length > 0) {
                            const firstBodyPart = bodyParts[0];
                            const spawnCode = String(firstBodyPart.spawnCode || '').toUpperCase();
                            const manufacturerPrefixes = {
                                'JAK': 'Jakobs', 'TED': 'Tediore', 'VLAD': 'Vladof', 
                                'MAL': 'Maliwan', 'TOR': 'Torgue', 'HYP': 'Hyperion',
                                'DAH': 'Dahl', 'COV': 'CoV', 'ATL': 'Atlas'
                            };
                            for (const [prefix, name] of Object.entries(manufacturerPrefixes)) {
                                if (spawnCode.startsWith(prefix + '_')) {
                                    manufacturer = name;
                                    break;
                                }
                            }
                        }
                    }
                }
                if (manufacturerSelect && manufacturer && manufacturer.trim() !== '') {
                    manufacturerSelect.value = manufacturer;
                    manufacturerSelect.dataset.previousValue = manufacturer;
                    manufacturerSelect.dispatchEvent(new Event('change', { bubbles: true }));
                }
                if (window.updateTypeIdDropdown) {
                    window.updateTypeIdDropdown();
                }
                const typeIdSelect = document.getElementById('typeId');
                if (typeIdSelect) {
                    typeIdSelect.value = String(typeId);
                    typeIdSelect.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }
            
            // Set level - use selected level from modal, or randomize if not selected
            const selectedLevelInput = document.getElementById('randomItemLevel');
            let levelToUse;
            if (selectedLevelInput && selectedLevelInput.value && selectedLevelInput.value.trim() !== '') {
                const parsedLevel = parseInt(selectedLevelInput.value);
                if (!isNaN(parsedLevel) && parsedLevel >= 1 && parsedLevel <= ITEM_MAX_LEVEL) {
                    levelToUse = parsedLevel;
                } else {
                    // Invalid level, randomize
                    levelToUse = Math.floor(Math.random() * ITEM_MAX_LEVEL) + 1;
                }
            } else {
                // No level selected, randomize
                levelToUse = Math.floor(Math.random() * ITEM_MAX_LEVEL) + 1;
            }
            document.getElementById('level').value = levelToUse;
            
            // Set random seed (1-4096) - use permanent seed if set, otherwise randomize
            const permanentSeed = localStorage.getItem('permanentSeed');
            let randomSeed;
            if (permanentSeed) {
                const seedValue = parseInt(permanentSeed);
                if (!isNaN(seedValue) && seedValue >= 1 && seedValue <= 4096) {
                    randomSeed = seedValue;
                } else {
                    randomSeed = Math.floor(Math.random() * 4096) + 1;
                }
            } else {
                randomSeed = Math.floor(Math.random() * 4096) + 1;
            }
            document.getElementById('seed').value = randomSeed;
            
            // Set firmware lock - DISABLED for all generated items
            // Firmware lock should not be randomized, always disabled
            const firmwareLockElement = document.getElementById('firmwareLock');
            firmwareLockElement.checked = false;
            const buybackFlagElement = document.getElementById('buybackFlag');
            if (buybackFlagElement) {
                buybackFlagElement.checked = false;
            }
            
            // Apply modification level - add extra parts based on mod level
            const modLevelSelect = document.getElementById('randomItemModLevel');
            const modLevel = modLevelSelect ? parseInt(modLevelSelect.value) || 0 : 0;
            
            // Helper function to check if a part is compatible with the current item type
            const isPartCompatible = (part, partTypeId) => {
                if (!part) return false;
                
                // Skills (typeId 254) should ONLY be on class mods (typeId 234)
                if (partTypeId === 254 && typeId !== 234) {
                    return false;
                }
                
                // Perks (typeId 234) should ONLY be on class mods (typeId 234)
                // But we allow perks234 to be added to class mods via the normal flow, not as random cross-typeId
                // So we'll allow it here since it's already handled separately
                
                // Check for rarity parts
                const partType = String(part.partType || '').toLowerCase();
                const partPath = String(part.path || '').toLowerCase();
                const partName = String(part.name || '').toLowerCase();
                const spawnCode = String(part.spawnCode || '').toLowerCase();
                
                // Exclude any part that is a rarity part
                if (partType.includes('rarity') || 
                    partPath.includes('rarity') || 
                    partName.includes('rarity') ||
                    spawnCode.includes('rarity') ||
                    partType === 'comp' && partPath.includes('rarity') ||
                    partName.toLowerCase().includes('common') ||
                    partName.toLowerCase().includes('uncommon') ||
                    partName.toLowerCase().includes('rare') ||
                    partName.toLowerCase().includes('epic') ||
                    partName.toLowerCase().includes('legendary')) {
                    return false;
                }
                
                return true;
            };
            
            if (modLevel > 0) {
                // Determine how many extra parts to add based on mod level
                let extraPartsCount = 0;
                let arrayPartsCount = 0;
                
                switch(modLevel) {
                    case 1: // Light: +1-2 extra parts
                        extraPartsCount = Math.floor(Math.random() * 2) + 1;
                        break;
                    case 2: // Moderate: +3-5 extra parts
                        extraPartsCount = Math.floor(Math.random() * 3) + 3;
                        break;
                    case 3: // Heavy: +6-10 extra parts
                        extraPartsCount = Math.floor(Math.random() * 5) + 6;
                        break;
                    case 4: // Extreme: +11-15 extra parts + 1-2 arrays
                        extraPartsCount = Math.floor(Math.random() * 5) + 11;
                        arrayPartsCount = Math.floor(Math.random() * 2) + 1;
                        break;
                    case 5: // Maximum: +20+ extra parts + 3-5 arrays
                        extraPartsCount = Math.floor(Math.random() * 10) + 20;
                        arrayPartsCount = Math.floor(Math.random() * 3) + 3;
                        break;
                    case 6: // Ultra: +30-40 extra parts + 6-8 arrays
                        extraPartsCount = Math.floor(Math.random() * 11) + 30;
                        arrayPartsCount = Math.floor(Math.random() * 3) + 6;
                        break;
                    case 7: // Insane: +50-60 extra parts + 10-12 arrays
                        extraPartsCount = Math.floor(Math.random() * 11) + 50;
                        arrayPartsCount = Math.floor(Math.random() * 3) + 10;
                        break;
                    case 8: // Chaotic: +75-100 extra parts + 15-20 arrays
                        extraPartsCount = Math.floor(Math.random() * 26) + 75;
                        arrayPartsCount = Math.floor(Math.random() * 6) + 15;
                        break;
                    case 9: // Absolute: +100-150 extra parts + 25-35 arrays
                        extraPartsCount = Math.floor(Math.random() * 51) + 100;
                        arrayPartsCount = Math.floor(Math.random() * 11) + 25;
                        break;
                }
                
                // Get local parts pool (70% weight)
                // Group items by type: weapons/heavy weapons share pool, grenades share pool, etc.
                let localTypeIds = [typeId];
                
                if (isWeapon || isHeavyWeapon) {
                    // Get all weapon and heavy weapon typeIds (same pool)
                    localTypeIds = Array.from(partsByTypeId.keys()).filter(tid => {
                        const tidInfo = typeIdMap.get(tid);
                        if (!tidInfo) return false;
                        const tidCategory = (tidInfo.category || '').toLowerCase();
                        return (tidCategory.includes('weapon') || tidCategory.includes('heavy weapon')) && tid !== 1;
                    });
                } else if (isGrenade) {
                    // Get all grenade typeIds (same pool)
                    localTypeIds = Array.from(partsByTypeId.keys()).filter(tid => {
                        const tidInfo = typeIdMap.get(tid);
                        if (!tidInfo) return false;
                        const tidCategory = (tidInfo.category || '').toLowerCase();
                        return tidCategory.includes('grenade') || tidCategory.includes('ordnance');
                    });
                } else if (isClassMod) {
                    // Get all class mod typeIds (234 for perks, 254-259 for character class mods)
                    localTypeIds = Array.from(partsByTypeId.keys()).filter(tid => {
                        const tidInfo = typeIdMap.get(tid);
                        if (!tidInfo) return false;
                        const tidCategory = (tidInfo.category || '').toLowerCase();
                        return tidCategory.includes('class mod') || (tid >= 254 && tid <= 259) || tid === 234;
                    });
                } else if (isEnhancement) {
                    // Get all enhancement typeIds (same pool)
                    localTypeIds = Array.from(partsByTypeId.keys()).filter(tid => {
                        const tidInfo = typeIdMap.get(tid);
                        if (!tidInfo) return false;
                        const tidCategory = (tidInfo.category || '').toLowerCase();
                        return tidCategory.includes('enhancement');
                    });
                } else if (isRepkit) {
                    // Get all repkit typeIds (same pool)
                    localTypeIds = Array.from(partsByTypeId.keys()).filter(tid => {
                        const tidInfo = typeIdMap.get(tid);
                        if (!tidInfo) return false;
                        const tidCategory = (tidInfo.category || '').toLowerCase();
                        return tidCategory.includes('repkit') || tidCategory.includes('rep kit');
                    });
                } else if (isShield) {
                    // Get all shield typeIds (same pool) - includes 237, 246, 248, and manufacturer shields
                    localTypeIds = Array.from(partsByTypeId.keys()).filter(tid => {
                        const tidInfo = typeIdMap.get(tid);
                        if (!tidInfo) return false;
                        const tidCategory = (tidInfo.category || '').toLowerCase();
                        return tidCategory.includes('shield') || tid === 237 || tid === 246 || tid === 248;
                    });
                }
                
                // Get local parts (from item's own typeId or weapon/heavy weapon pool)
                const localParts = [];
                localTypeIds.forEach(tid => {
                    if (partsByTypeId.has(tid)) {
                        const parts = partsByTypeId.get(tid) || [];
                        // Filter out rarity parts and incompatible parts
                        const filtered = parts.filter(p => isPartCompatible(p, tid));
                        localParts.push(...filtered);
                    }
                });
                
                // Get cross-typeId parts pool (30% weight)
                const allTypeIds = Array.from(partsByTypeId.keys()).filter(tid => {
                    // Exclude skills (254) unless this is a class mod (234)
                    if (tid === 254 && typeId !== 234) {
                        return false;
                    }
                    // Exclude local typeIds (all items in the same category share pool)
                    return tid !== typeId && !localTypeIds.includes(tid);
                });
                
                // Get all cross-typeId parts
                const crossParts = [];
                allTypeIds.forEach(tid => {
                    if (partsByTypeId.has(tid)) {
                        const parts = partsByTypeId.get(tid) || [];
                        // Filter out rarity parts and incompatible parts
                        const filtered = parts.filter(p => isPartCompatible(p, tid));
                        crossParts.push(...filtered);
                    }
                });
                
                // Add extra random parts with 70% local / 30% cross weighting
                for (let i = 0; i < extraPartsCount; i++) {
                    // Weighted selection: 70% local, 30% cross
                    const useLocal = Math.random() < 0.7;
                    let selectedPart = null;
                    let selectedTypeId = null;
                    
                    if (useLocal && localParts.length > 0) {
                        // 70% chance: select from local parts
                        selectedPart = getRandomItem(localParts);
                        if (selectedPart) {
                            selectedTypeId = selectedPart.typeId || typeId;
                        }
                    } else if (crossParts.length > 0) {
                        // 30% chance: select from cross-typeId parts
                        selectedPart = getRandomItem(crossParts);
                        if (selectedPart) {
                            selectedTypeId = selectedPart.typeId;
                        }
                    }
                    
                    if (selectedPart && selectedTypeId) {
                        const partId = getPartId(selectedPart);
                        if (partId) {
                            const partValue = parseInt(partId.partId);
                            // CRITICAL: Reject 0 values and validate that the part actually exists in partsMap
                            if (isNaN(partValue) || (partValue === 0 && !partsMap.has(`${partId.typeId}:0`))) {
                                // Skip invalid part (0 is not valid unless explicitly in partsMap), try another
                                continue;
                            }
                            
                            // CRITICAL: Validate that the part actually exists in partsMap
                            const partExists = partsMap.has(`${partId.typeId}:${partValue}`);
                            if (!partExists) {
                                // Skip invalid part, try another
                                continue;
                            }
                            
                            // Use safeAddPart to validate and prevent duplicates
                            let partToAdd;
                            if (partId.typeId === typeId) {
                                partToAdd = {
                                    type: 'simple',
                                    value: partValue || partId.partId
                                };
                            } else {
                                partToAdd = {
                                    type: 'typed',
                                    typeId: partId.typeId,
                                    value: partValue || partId.partId
                                };
                            }
                            safeAddPart(partToAdd);
                        }
                    }
                }
                
                // Add array-based parts (format: {typeId:[value1 value2 value3]}) - EXCLUDE RARITY PARTS AND INCOMPATIBLE PARTS
                // Use 70% local / 30% cross weighting
                for (let i = 0; i < arrayPartsCount; i++) {
                    // Weighted selection: 70% local, 30% cross
                    const useLocal = Math.random() < 0.7;
                    let randomTypeId = null;
                    let filteredParts = [];
                    
                    if (useLocal && localParts.length >= 2) {
                        // 70% chance: select from local parts
                        // Group local parts by typeId for array creation
                        const localPartsByTypeId = new Map();
                        localParts.forEach(p => {
                            const tid = p.typeId || typeId;
                            if (!localPartsByTypeId.has(tid)) {
                                localPartsByTypeId.set(tid, []);
                            }
                            localPartsByTypeId.get(tid).push(p);
                        });
                        
                        // Find a typeId with at least 2 parts
                        const validLocalTypeIds = Array.from(localPartsByTypeId.keys()).filter(tid => 
                            localPartsByTypeId.get(tid).length >= 2
                        );
                        
                        if (validLocalTypeIds.length > 0) {
                            randomTypeId = getRandomItem(validLocalTypeIds);
                            filteredParts = localPartsByTypeId.get(randomTypeId) || [];
                        }
                    } else if (crossParts.length >= 2) {
                        // 30% chance: select from cross-typeId parts
                        // Group cross parts by typeId for array creation
                        const crossPartsByTypeId = new Map();
                        crossParts.forEach(p => {
                            const tid = p.typeId;
                            if (!crossPartsByTypeId.has(tid)) {
                                crossPartsByTypeId.set(tid, []);
                            }
                            crossPartsByTypeId.get(tid).push(p);
                        });
                        
                        // Find a typeId with at least 2 parts
                        const validCrossTypeIds = Array.from(crossPartsByTypeId.keys()).filter(tid => 
                            crossPartsByTypeId.get(tid).length >= 2
                        );
                        
                        if (validCrossTypeIds.length > 0) {
                            randomTypeId = getRandomItem(validCrossTypeIds);
                            filteredParts = crossPartsByTypeId.get(randomTypeId) || [];
                        }
                    }
                    
                    if (randomTypeId && filteredParts.length >= 2) {
                        // Select 2-5 random parts from this typeId to form an array
                        const arraySize = Math.min(Math.floor(Math.random() * 4) + 2, filteredParts.length); // 2-5 parts, but not more than available
                        const selectedParts = [];
                        const usedIndices = new Set();
                        
                        for (let j = 0; j < arraySize && usedIndices.size < filteredParts.length; j++) {
                            // Pick a random index we haven't used yet
                            let randomIndex;
                            do {
                                randomIndex = Math.floor(Math.random() * filteredParts.length);
                            } while (usedIndices.has(randomIndex) && usedIndices.size < filteredParts.length);
                            
                            if (!usedIndices.has(randomIndex)) {
                                usedIndices.add(randomIndex);
                                const randomPart = filteredParts[randomIndex];
                                if (randomPart) {
                                    const partId = getPartId(randomPart);
                                    if (partId && partId.typeId === randomTypeId) {
                                        const partValue = parseInt(partId.partId);
                                        // CRITICAL: Reject 0 and invalid values, and ensure part exists in partsMap
                                        if (!isNaN(partValue) && partValue !== 0 && !selectedParts.includes(partValue)) {
                                            // Validate the part exists in partsMap before adding to array
                                            const partKey = `${randomTypeId}:${partValue}`;
                                            if (partsMap.has(partKey)) {
                                                const partInfo = partsMap.get(partKey);
                                                if (partInfo) {
                                                    selectedParts.push(partValue);
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                        
                        if (selectedParts.length >= 2) {
                            // CRITICAL: Validate that all values in the array exist in partsMap
                            const validValues = selectedParts.filter(val => {
                                return partsMap.has(`${randomTypeId}:${val}`);
                            });
                            
                            // Only add array if we have at least 2 valid values
                            if (validValues.length >= 2) {
                                // Use safeAddPart to validate and prevent duplicates
                                const partToAdd = {
                                    type: 'array',
                                    typeId: randomTypeId,
                                    values: validValues.sort((a, b) => a - b) // Sort for consistency
                                };
                                safeAddPart(partToAdd);
                            }
                        }
                    }
                }
            }
            
            // Final safety check: Remove any duplicate rarity parts (should never happen, but safety first)
            const rarityParts = [];
            const nonRarityParts = [];
            
            randomParts.forEach(p => {
                let isRarity = false;
                if (p.type === 'simple') {
                    const partInfo = partsMap.get(`${typeId}:${p.value}`) || partsMap.get(p.value);
                    if (partInfo) {
                        const partType = String(partInfo.partType || '').toLowerCase();
                        const partName = String(partInfo.name || '').toLowerCase();
                        const partPath = String(partInfo.path || '').toLowerCase();
                        isRarity = partType.includes('rarity') || partType === 'comp' || 
                                  partName.includes('rarity') || partName.includes('common') || 
                                  partName.includes('uncommon') || partName.includes('rare') || 
                                  partName.includes('epic') || partName.includes('legendary') ||
                                  partPath.includes('rarity') || partPath.includes('comp');
                    }
                } else if (p.type === 'typed') {
                    const partInfo = partsMap.get(`${p.typeId}:${p.value}`);
                    if (partInfo) {
                        const partType = String(partInfo.partType || '').toLowerCase();
                        const partName = String(partInfo.name || '').toLowerCase();
                        const partPath = String(partInfo.path || '').toLowerCase();
                        isRarity = partType.includes('rarity') || partType === 'comp' || 
                                  partName.includes('rarity') || partName.includes('common') || 
                                  partName.includes('uncommon') || partName.includes('rare') || 
                                  partName.includes('epic') || partName.includes('legendary') ||
                                  partPath.includes('rarity') || partPath.includes('comp');
                    }
                }
                
                if (isRarity) {
                    rarityParts.push(p);
                } else {
                    nonRarityParts.push(p);
                }
            });
            
            // Keep only the first rarity part, discard any duplicates
            const finalRarityPart = rarityParts.length > 0 ? [rarityParts[0]] : [];
            
            // Reconstruct randomParts with only one rarity part
            randomParts = [...finalRarityPart, ...nonRarityParts];
            
            // CRITICAL: For enhancements, ensure base body part (247:76-80) is present
            if (isEnhancement) {
                const hasBaseBody = randomParts.some(p => {
                    if (p.type === 'typed' && p.typeId === 247) {
                        const partIdNum = parseInt(p.value);
                        return partIdNum >= 76 && partIdNum <= 80;
                    }
                    return false;
                });
                
                console.log(`[ENHANCEMENT DEBUG] After rarity deduplication, hasBaseBody = ${hasBaseBody}`);
                console.log(`[ENHANCEMENT DEBUG] randomParts contents:`, randomParts.map(p => `${p.type === 'typed' ? p.typeId + ':' : ''}${p.value}`));
                
                if (!hasBaseBody) {
                    console.warn(`[ENHANCEMENT] CRITICAL: Base body part missing after rarity deduplication! Adding it now...`);
                    // Determine base body part ID from rarity
                    let targetBaseBodyId = null;
                    const rarityPart = randomParts.find(p => {
                        if (p.type === 'simple') {
                            const partInfo = partsMap.get(`${typeId}:${p.value}`) || partsMap.get(p.value);
                            if (partInfo) {
                                const partTypeId = partInfo.typeId || typeId;
                                if (partTypeId === typeId && partTypeId !== 247) {
                                    const partType = String(partInfo.partType || '').toLowerCase();
                                    const partName = String(partInfo.name || '').toLowerCase();
                                    return partType.includes('rarity') || partType === 'comp' || 
                                           partName.includes('rarity') || partName.includes('common') || 
                                           partName.includes('uncommon') || partName.includes('rare') || 
                                           partName.includes('epic') || partName.includes('legendary');
                                }
                            }
                        }
                        return false;
                    });
                    
                    if (rarityPart) {
                        // Try to get numeric rarity value
                        const rarityValue = parseInt(rarityPart.value);
                        if (!isNaN(rarityValue) && rarityValue >= 5 && rarityValue <= 9) {
                            // Map: 5=Common→80, 6=Uncommon→79, 7=Rare→78, 8=Epic→77, 9=Legendary→76
                            if (rarityValue === 5) targetBaseBodyId = 80;
                            else if (rarityValue === 6) targetBaseBodyId = 79;
                            else if (rarityValue === 7) targetBaseBodyId = 78;
                            else if (rarityValue === 8) targetBaseBodyId = 77;
                            else if (rarityValue === 9) targetBaseBodyId = 76;
                        } else {
                            // Fallback: check part info
                            const rarityPartInfo = partsMap.get(`${typeId}:${rarityPart.value}`) || partsMap.get(rarityPart.value);
                            if (rarityPartInfo) {
                                const partName = String(rarityPartInfo.name || '').toLowerCase();
                                const spawnCode = String(rarityPartInfo.spawnCode || '').toLowerCase();
                                if (partName.includes('common') || spawnCode.includes('comp_01') || spawnCode.includes('body_01')) {
                                    targetBaseBodyId = 80;
                                } else if (partName.includes('uncommon') || spawnCode.includes('comp_02') || spawnCode.includes('body_02')) {
                                    targetBaseBodyId = 79;
                                } else if (partName.includes('rare') || spawnCode.includes('comp_03') || spawnCode.includes('body_03')) {
                                    targetBaseBodyId = 78;
                                } else if (partName.includes('epic') || spawnCode.includes('comp_04') || spawnCode.includes('body_04')) {
                                    targetBaseBodyId = 77;
                                } else if (partName.includes('legendary') || spawnCode.includes('comp_05') || spawnCode.includes('body_05')) {
                                    targetBaseBodyId = 76;
                                }
                            }
                        }
                    }
                    
                    // Try to add base body part - prioritize determined ID, then try all
                    const baseBodyIds = targetBaseBodyId !== null ? 
                        [targetBaseBodyId, ...([76, 77, 78, 79, 80].filter(id => id !== targetBaseBodyId))] :
                        [76, 77, 78, 79, 80];
                    let added = false;
                    for (const bodyId of baseBodyIds) {
                        const key = `247:${bodyId}`;
                        if (partsMap.has(key)) {
                            // Check if it's already in randomParts (shouldn't be, but check anyway)
                            const alreadyExists = randomParts.some(p => 
                                p.type === 'typed' && p.typeId === 247 && p.value === bodyId
                            );
                            if (!alreadyExists) {
                                randomParts.push({
                                    type: 'typed',
                                    typeId: 247,
                                    value: bodyId
                                });
                                added = true;
                                console.log(`[ENHANCEMENT] Added base body part ${key} (${targetBaseBodyId === bodyId ? 'matched rarity' : 'fallback'}) directly to randomParts after rarity deduplication`);
                                break;
                            }
                        }
                    }
                    if (!added) {
                        console.error(`[ENHANCEMENT] CRITICAL: Failed to add base body part after rarity deduplication!`);
                    }
                }
            }
            
            // Debug: Log all parts before setting currentParts
            if (isEnhancement) {
                console.log(`[ENHANCEMENT DEBUG] Final randomParts before setting currentParts:`, randomParts.map(p => {
                    if (p.type === 'typed' && p.typeId === 247) {
                        const partIdNum = parseInt(p.value);
                        if (partIdNum >= 76 && partIdNum <= 80) {
                            return `BASE BODY: ${p.typeId}:${p.value}`;
                        }
                    }
                    return `${p.type === 'typed' ? p.typeId + ':' : ''}${p.value}`;
                }));
            }
            
            // Final validation: Ensure we have at least some parts (critical for item generation)
            if (randomParts.length === 0) {
                console.error(`[RANDOM GENERATOR] CRITICAL: No parts were generated for typeId ${typeId}! Item generation failed.`);
                alert(`Failed to generate item: No parts could be added for the selected item type. This may indicate missing part data for typeId ${typeId}.`);
                return; // Abort generation if no parts were added
            }
            
            // Log warning if many required categories were missing
            const missingRequired = requiredCategories.filter(cat => !addedRequiredCategories.includes(cat));
            if (missingRequired.length > 0 && missingRequired.length > requiredCategories.length / 2) {
                console.warn(`[RANDOM GENERATOR] Warning: ${missingRequired.length} out of ${requiredCategories.length} required categories were not added for typeId ${typeId}:`, missingRequired);
            }
            
            // Set current parts BEFORE updating guidelines
            currentParts = randomParts;
            
            // NOW update guidelines (after level and parts are set)
            if (typeInfo) {
                updateGuidelines(typeInfo.category, typeId);
            }
            
            // Render parts and generate code
            renderParts();
            generateCode();
            
            // Update guidelines checklist to reflect the actual parts and level
            if (window.updateGuidelinesChecklist) {
                updateGuidelinesChecklist();
            }
            
            // Close modal
            hideRandomItemModal();
            
            // Show success message
            showStatus('outputStatus', `✅ Generated random ${typeInfo?.name || 'item'} (Level ${levelToUse})!`, 'success');
        };
        
        // Generate random item and parse it (send to item editor)
        window.generateRandomItemAndParse = async function() {
            const select = document.getElementById('randomItemTypeSelect');
            if (!select || !select.value) {
                alert('Please select an item type first!');
                return;
            }
            
            const quantityInput = document.getElementById('randomItemQuantity');
            const quantity = quantityInput ? parseInt(quantityInput.value) || 1 : 1;
            
            if (quantity > 1) {
                alert('Generate and Parse only supports 1 item at a time. Please set quantity to 1 or use "Generate and Add to Backpack" for multiple items.');
                return;
            }
            
            // If "random" is selected, pick a random typeId
            let typeId = null;
            if (select.value === 'random') {
                const validTypeIds = window.validRandomTypeIds || [];
                if (validTypeIds.length === 0) {
                    alert('No valid item types available for random selection!');
                    return;
                }
                typeId = validTypeIds[Math.floor(Math.random() * validTypeIds.length)];
                // Temporarily set the select to the chosen typeId for generation
                const savedValue = select.value;
                select.value = typeId;
                generateRandomItem();
                select.value = savedValue; // Restore "random" selection
            } else {
                // Generate the item (this will populate the item editor)
                generateRandomItem();
            }
            
            // Switch to item editor tab
            switchTab('item-editor-tab');
        };
        
        // Generate random items and add directly to backpack
        window.generateRandomItemAndAddToBackpack = async function() {
            const select = document.getElementById('randomItemTypeSelect');
            if (!select || !select.value) {
                alert('Please select an item type first!');
                return;
            }
            
            const quantityInput = document.getElementById('randomItemQuantity');
            const quantity = quantityInput ? parseInt(quantityInput.value) || 1 : 1;
            
            if (quantity < 1 || quantity > 100) {
                alert('Quantity must be between 1 and 100.');
                return;
            }
            
            // Check if save file is loaded
            if (!window.saveEditorState || !window.saveEditorState.isLoaded) {
                alert('Please load a save file first in the Save Editor tab!');
                switchTab('save-editor-tab');
                return;
            }
            
            // Check if "random" is selected
            const isRandomType = select.value === 'random';
            const validTypeIds = isRandomType ? (window.validRandomTypeIds || []) : [];
            
            if (isRandomType && validTypeIds.length === 0) {
                alert('No valid item types available for random selection!');
                return;
            }
            
            // If not random, validate the selected typeId
            if (!isRandomType) {
                const typeId = parseInt(select.value);
                if (!typeId || !partsByTypeId.has(typeId)) {
                    alert('Invalid item type selected!');
                    return;
                }
            }
            
            // Get settings
            const levelInput = document.getElementById('randomItemLevel');
            const modLevelSelect = document.getElementById('randomItemModLevel');
            const level = levelInput ? (levelInput.value.trim() ? parseInt(levelInput.value) : null) : null;
            const modLevel = modLevelSelect ? parseInt(modLevelSelect.value) || 0 : 0;
            
            // Show progress bar and disable buttons
            const progressContainer = document.getElementById('randomItemProgressContainer');
            const progressBar = document.getElementById('randomItemProgressBar');
            const progressText = document.getElementById('randomItemProgressText');
            const progressCount = document.getElementById('randomItemProgressCount');
            const generateAndParseBtn = document.getElementById('generateAndParseBtn');
            const generateAndAddBtn = document.getElementById('generateAndAddBtn');
            const cancelBtn = document.getElementById('randomItemCancelBtn');
            
            if (progressContainer) {
                progressContainer.style.display = 'block';
            }
            if (progressBar) {
                progressBar.style.width = '0%';
            }
            if (progressText) {
                progressText.textContent = 'Generating items...';
            }
            if (progressCount) {
                progressCount.textContent = `0 / ${quantity}`;
            }
            
            // Disable buttons during generation
            if (generateAndParseBtn) generateAndParseBtn.disabled = true;
            if (generateAndAddBtn) generateAndAddBtn.disabled = true;
            if (cancelBtn) cancelBtn.disabled = true;
            
            const generatedSerials = [];
            let successCount = 0;
            let failCount = 0;
            
            // Save original state
            const originalTab = document.querySelector('.tab-button.active')?.getAttribute('onclick')?.match(/'([^']+)'/)?.[1] || 'item-editor-tab';
            const originalOutputCode = getOutputCode() || '';
            const originalSerialized = document.getElementById('serializedOutput')?.textContent || '';
            
            // Generate all items quickly and collect their codes (no serialization yet)
            const generatedCodes = [];
            
            // Temporarily override hideRandomItemModal and serializeCode to prevent auto-serialization
            const originalHide = window.hideRandomItemModal;
            const originalSerializeCode = window.serializeCode;
            window.hideRandomItemModal = function() {}; // Don't close modal during generation
            window.serializeCode = function() {}; // Disable auto-serialization during bulk generation
            
            // Save original UI state
            const savedCurrentParts = [...currentParts];
            const savedTypeId = document.getElementById('typeId')?.value || '';
            const savedLevel = document.getElementById('level')?.value || String(ITEM_MAX_LEVEL);
            const savedSeed = document.getElementById('seed')?.value || '1';
            const savedSelectValue = select.value;
            
            // Generate all items quickly
            for (let i = 0; i < quantity; i++) {
                try {
                    // Update progress bar
                    const currentProgress = ((i + 1) / quantity) * 50; // First 50% for generation
                    if (progressBar) {
                        progressBar.style.width = `${currentProgress}%`;
                    }
                    if (progressCount) {
                        progressCount.textContent = `${i + 1} / ${quantity}`;
                    }
                    
                    // Determine the typeId for this item
                    let itemTypeId = null;
                    if (isRandomType) {
                        if (validTypeIds.length === 0) {
                            console.warn(`Skipping item ${i + 1}: No valid types available`);
                            failCount++;
                            continue;
                        }
                        
                        // Randomly select a typeId
                        itemTypeId = validTypeIds[Math.floor(Math.random() * validTypeIds.length)];
                        if (progressText) {
                            const typeInfo = typeIdMap.get(itemTypeId);
                            const typeName = typeInfo?.name || `Type ${itemTypeId}`;
                            progressText.textContent = `Generating item ${i + 1} of ${quantity} (${typeName})...`;
                        }
                    } else {
                        itemTypeId = parseInt(select.value);
                        if (progressText) {
                            progressText.textContent = `Generating item ${i + 1} of ${quantity}...`;
                        }
                    }
                    
                    // Validate the typeId
                    if (!itemTypeId || !partsByTypeId.has(itemTypeId)) {
                        console.warn(`Skipping item ${i + 1}: Invalid typeId ${itemTypeId}`);
                        failCount++;
                        continue;
                    }
                    
                    // Set the select value temporarily to the chosen typeId
                    select.value = itemTypeId;
                    
                    // Generate the item (this will populate the UI)
                    try {
                        generateRandomItem();
                        
                        // Wait a tiny bit for generateCode() to complete (it's synchronous but setTimeout in it needs time)
                        await new Promise(resolve => setTimeout(resolve, 200));
                        
                        // Get the generated code directly (generateCode() is called by generateRandomItem)
                        const code = getOutputCode()?.trim();
                        
                        // Validate the generated code - it should not be empty or placeholder text
                        // Also check that we have parts (basic validation)
                        if (code && 
                            code !== 'Generated code will appear here...' && 
                            code !== 'Please select a Type ID first' &&
                            code.length > 10 && // Basic sanity check - valid codes are longer
                            currentParts && currentParts.length > 0) { // Ensure parts were actually added
                            generatedCodes.push(code);
                            successCount++;
                        } else {
                            console.warn(`Item ${i + 1} generation failed: Invalid code or missing parts. Code: "${code}", Parts: ${currentParts?.length || 0}`);
                            failCount++;
                        }
                    } catch (genError) {
                        console.error(`Error during generation of item ${i + 1}:`, genError);
                        failCount++;
                    }
                } catch (error) {
                    console.error(`Error generating item ${i + 1}:`, error);
                    failCount++;
                }
            }
            
            // Restore original functions and state
            window.hideRandomItemModal = originalHide;
            window.serializeCode = originalSerializeCode;
            // Restore select value (if it was "random", keep it as "random")
            select.value = savedSelectValue || (isRandomType ? 'random' : savedSelectValue);
            currentParts = savedCurrentParts;
            if (document.getElementById('typeId')) {
                document.getElementById('typeId').value = savedTypeId;
            }
            if (document.getElementById('level')) {
                document.getElementById('level').value = savedLevel;
            }
            if (document.getElementById('seed')) {
                document.getElementById('seed').value = savedSeed;
            }
            
            // Restore original output code
            setOutputCode(originalOutputCode);
            document.getElementById('serializedOutput').textContent = originalSerialized;
            
            if (generatedCodes.length === 0) {
                if (progressText) {
                    progressText.textContent = '❌ Failed to generate any items.';
                }
                // Re-enable buttons
                if (generateAndParseBtn) generateAndParseBtn.disabled = false;
                if (generateAndAddBtn) generateAndAddBtn.disabled = false;
                if (cancelBtn) cancelBtn.disabled = false;
                showStatus('outputStatus', `❌ Failed to generate any items.`, 'error');
                // Hide progress after a delay
                setTimeout(() => {
                    if (progressContainer) {
                        progressContainer.style.display = 'none';
                    }
                }, 3000);
                return;
            }
            
            // Now serialize all codes in bulk
            if (progressText) {
                progressText.textContent = `Serializing ${generatedCodes.length} item${generatedCodes.length > 1 ? 's' : ''}...`;
            }
            
            // Try bulk serialization first (send all codes in one request)
            // The API expects deserialized_strings as an array and returns an array of serials
            try {
                const bulkResponse = await fetch('https://save-editor.be/nicnl/api.php', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        deserialized_strings: generatedCodes // Send as array of codes
                    })
                });

                if (bulkResponse.ok) {
                    const bulkData = await bulkResponse.json();
                    
                    // The API returns a simple array of serialized strings: ["@Ug...", "@Ug...", ...]
                    if (Array.isArray(bulkData)) {
                        bulkData.forEach((serial, index) => {
                            if (serial && typeof serial === 'string' && serial.startsWith('@Ug')) {
                                generatedSerials.push(serial);
                                // Don't increment successCount here - it's already been incremented during generation
                            } else if (serial === '') {
                                // Empty string means serialization failed for this item
                                failCount++;
                            } else {
                                failCount++;
                            }
                            
                            // Update progress
                            const progress = 50 + ((index + 1) / generatedCodes.length) * 50;
                            if (progressBar) {
                                progressBar.style.width = `${Math.min(progress, 100)}%`;
                            }
                            if (progressCount) {
                                progressCount.textContent = `${index + 1} / ${generatedCodes.length}`;
                            }
                        });
                    } else {
                        throw new Error('Bulk response is not an array');
                    }
                } else {
                    throw new Error(`Bulk request failed with status ${bulkResponse.status}`);
                }
            } catch (bulkError) {
                // Bulk request failed or unsupported, fall back to individual requests
                console.log('Bulk serialization not supported, falling back to batched requests:', bulkError);
                
                // Fall back to batched parallel requests (larger batches, minimal delay)
                const batchSize = 50;
                
                for (let i = 0; i < generatedCodes.length; i += batchSize) {
                    const batch = generatedCodes.slice(i, i + batchSize);
                    
                    if (i > 0) {
                        await new Promise(resolve => setTimeout(resolve, 30));
                    }
                    
                    const batchPromises = batch.map(async (code, batchIndex) => {
                        try {
                            const response = await fetch('https://save-editor.be/nicnl/api.php', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json'
                                },
                                body: JSON.stringify({
                                    deserialized: code
                                })
                            });

                            if (!response.ok) {
                                throw new Error(`HTTP error! status: ${response.status}`);
                            }

                            const responseText = await response.text();
                            let data;
                            
                            try {
                                data = JSON.parse(responseText);
                            } catch (parseError) {
                                throw new Error('Invalid response format from API');
                            }
                            
                            if (data.error) {
                                throw new Error(data.error);
                            }

                            if (data.serial_b85 && typeof data.serial_b85 === 'string') {
                                // Update progress as each item completes
                                const completed = i + batchIndex + 1;
                                const serializationProgress = 50 + (completed / generatedCodes.length) * 50;
                                if (progressBar) {
                                    progressBar.style.width = `${Math.min(serializationProgress, 100)}%`;
                                }
                                if (progressCount) {
                                    progressCount.textContent = `${completed} / ${generatedCodes.length}`;
                                }
                                return data.serial_b85;
                            } else {
                                throw new Error('No serial_b85 in response');
                            }
                        } catch (error) {
                            console.error(`Error serializing code ${i + batchIndex + 1}:`, error);
                            return null;
                        }
                    });
                    
                    // Process this batch in parallel
                    const batchResults = await Promise.all(batchPromises);
                    
                    // Collect successful serials from this batch
                    batchResults.forEach((serial) => {
                        if (serial && serial.startsWith('@Ug')) {
                            generatedSerials.push(serial);
                            // Don't increment successCount here - it's already been incremented during generation
                        } else {
                            failCount++;
                        }
                    });
                }
            }
            
            // Restore original state
            setOutputCode(originalOutputCode);
            document.getElementById('serializedOutput').textContent = originalSerialized;
            
            // Update progress bar to 100%
            if (progressBar) {
                progressBar.style.width = '100%';
            }
            if (progressCount) {
                progressCount.textContent = `${quantity} / ${quantity}`;
            }
            
            if (generatedSerials.length === 0) {
                if (progressText) {
                    progressText.textContent = '❌ Failed to generate any items.';
                }
                // Re-enable buttons
                if (generateAndParseBtn) generateAndParseBtn.disabled = false;
                if (generateAndAddBtn) generateAndAddBtn.disabled = false;
                if (cancelBtn) cancelBtn.disabled = false;
                showStatus('outputStatus', `❌ Failed to generate any items.`, 'error');
                // Hide progress after a delay
                setTimeout(() => {
                    if (progressContainer) {
                        progressContainer.style.display = 'none';
                    }
                }, 3000);
                return;
            }
            
            // Update progress text - use generatedSerials.length since that's the actual count of successfully serialized items
            const serializedCount = generatedSerials.length;
            if (progressText) {
                progressText.textContent = `✅ Adding ${serializedCount} item${serializedCount > 1 ? 's' : ''} to backpack...`;
            }
            
            // Add all items to backpack using bulk add functionality
            const bulkInput = document.getElementById('save-bulk-items-input');
            if (bulkInput) {
                bulkInput.value = generatedSerials.join('\n');
                
                // Call the bulk add function
                if (window.addBulkItems) {
                    await window.addBulkItems();
                    
                    // Switch to save editor tab and scroll to backpack slots
                    switchTab('save-editor-tab');
                    
                    // Scroll to backpack slots after a short delay
                    setTimeout(() => {
                        const decodedItemsContainer = document.getElementById('save-decoded-items-content');
                        if (decodedItemsContainer) {
                            decodedItemsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
                        }
                    }, 500);
                    
                    // Update progress text with final status - use serializedCount instead of successCount
                    const finalSerializedCount = generatedSerials.length;
                    if (progressText) {
                        progressText.textContent = `✅ Successfully added ${finalSerializedCount} item${finalSerializedCount > 1 ? 's' : ''} to backpack!${failCount > 0 ? ` (${failCount} failed)` : ''}`;
                    }
                    
                    showStatus('outputStatus', `✅ Generated and added ${finalSerializedCount} item${finalSerializedCount > 1 ? 's' : ''} to backpack!${failCount > 0 ? ` (${failCount} failed)` : ''}`, 'success');
                    
                    // Re-enable buttons
                    if (generateAndParseBtn) generateAndParseBtn.disabled = false;
                    if (generateAndAddBtn) generateAndAddBtn.disabled = false;
                    if (cancelBtn) cancelBtn.disabled = false;
                    
                    // Close modal after a short delay
                    setTimeout(() => {
                        hideRandomItemModal();
                        // Hide progress bar
                        if (progressContainer) {
                            progressContainer.style.display = 'none';
                        }
                    }, 2000);
                } else {
                    if (progressText) {
                        progressText.textContent = '❌ Bulk add function not available.';
                    }
                    // Re-enable buttons
                    if (generateAndParseBtn) generateAndParseBtn.disabled = false;
                    if (generateAndAddBtn) generateAndAddBtn.disabled = false;
                    if (cancelBtn) cancelBtn.disabled = false;
                    showStatus('outputStatus', `❌ Bulk add function not available.`, 'error');
                    setTimeout(() => {
                        if (progressContainer) {
                            progressContainer.style.display = 'none';
                        }
                    }, 3000);
                }
            } else {
                if (progressText) {
                    progressText.textContent = '❌ Bulk items input not found.';
                }
                // Re-enable buttons
                if (generateAndParseBtn) generateAndParseBtn.disabled = false;
                if (generateAndAddBtn) generateAndAddBtn.disabled = false;
                if (cancelBtn) cancelBtn.disabled = false;
                showStatus('outputStatus', `❌ Bulk items input not found.`, 'error');
                setTimeout(() => {
                    if (progressContainer) {
                        progressContainer.style.display = 'none';
                    }
                }, 3000);
            }
        };
