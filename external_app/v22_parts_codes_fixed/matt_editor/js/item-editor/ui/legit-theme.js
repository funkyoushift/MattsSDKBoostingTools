

        function changeTheme(themeName) {
            // Remove all theme classes
            document.body.className = document.body.className.replace(/theme-\w+/g, '').trim();
            // Add new theme class
            document.body.classList.add(themeName);
            
            // Update selector to match
            const selector = document.getElementById('themeSelector');
            if (selector) {
                selector.value = themeName;
            }
            
            // Update particle effects (skip for plain theme)
            if (themeName !== 'theme-plain') {
                const particles = themeParticles[themeName] || themeParticles['theme-default'];
                createBackdropEffect(particles);
                createHeaderParticles(particles);
            } else {
                // Clear all effects for plain theme
                const backdropEffect = document.getElementById('backdropEffect');
                const headerParticles = document.getElementById('headerParticles');
                if (backdropEffect) backdropEffect.innerHTML = '';
                if (headerParticles) headerParticles.innerHTML = '';
            }
            
            // Save to localStorage
            localStorage.setItem('selectedTheme', themeName);
        }

        // Squiggs easter egg - click counter for theme unlock
        let squiggsClickCount = 0;
        let squiggsClickTimeout = null;

        // Venom easter egg - click counter for both GIF background and theme unlock
        let venomClickCount = 0;
        let venomClickTimeout = null;
        let venomBackgroundActive = false;

        // Mattmab easter egg - click counter for both GIF background and theme unlock
        let mattmabClickCount = 0;
        let mattmabClickTimeout = null;
        let mattmabBackgroundActive = false;

        // Reset unlocks easter egg - click counter for reset
        let resetClickCount = 0;
        let resetClickTimeout = null;

        function showThemeAlreadyUnlockedPopup() {
            // Create a simpler, quicker notification
            const overlay = document.createElement('div');
            overlay.id = 'theme-already-unlocked-popup';
            overlay.style.cssText = `
                position: fixed;
                top: var(--page-pad);
                right: var(--page-pad);
                background: linear-gradient(135deg, rgba(0, 243, 255, 0.2), rgba(154, 77, 255, 0.2));
                border: 2px solid rgba(0, 243, 255, 0.6);
                border-radius: var(--panel-radius);
                padding: var(--section-gap) var(--panel-pad);
                text-align: center;
                box-shadow: 0 0 16px rgba(0, 243, 255, 0.5);
                z-index: 10000;
                animation: slideInRight 0.3s ease;
            `;
            
            // Add keyframe animation if not already present
            if (!document.getElementById('theme-unlock-animations')?.textContent.includes('slideInRight')) {
                const style = document.getElementById('theme-unlock-animations') || document.createElement('style');
                if (!document.getElementById('theme-unlock-animations')) {
                    style.id = 'theme-unlock-animations';
                    document.head.appendChild(style);
                }
                style.textContent += `
                    @keyframes slideInRight {
                        from { transform: translateX(100%); opacity: 0; }
                        to { transform: translateX(0); opacity: 1; }
                    }
                `;
            }
            
            overlay.innerHTML = `
                <div style="color: #00f3ff; font-size: var(--panel-title-size); font-weight: 600; text-shadow: 0 0 10px rgba(0, 243, 255, 0.8);">
                    Theme already Unlocked
                </div>
            `;
            
            document.body.appendChild(overlay);
            
            // Auto-close after 2 seconds
            setTimeout(() => {
                if (overlay.parentNode) {
                    overlay.style.animation = 'fadeOut 0.3s ease';
                    setTimeout(() => overlay.remove(), 300);
                }
            }, 2000);
        }

        function showThemeUnlockPopup(themeName = '🛴🧰 Scooters Toolbox 🛴🧰') {
            // Create popup overlay
            const overlay = document.createElement('div');
            overlay.id = 'theme-unlock-popup-overlay';
            overlay.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.7);
                z-index: 10000;
                display: flex;
                align-items: center;
                justify-content: center;
                animation: fadeIn 0.3s ease;
            `;
            
            // Create popup content
            const popup = document.createElement('div');
            popup.style.cssText = `
                background: linear-gradient(135deg, rgba(0, 243, 255, 0.2), rgba(154, 77, 255, 0.2));
                border: 2px solid rgba(0, 243, 255, 0.6);
                border-radius: var(--header-radius);
                padding: var(--header-pad-y) var(--header-pad-x);
                text-align: center;
                box-shadow: 0 0 28px rgba(0, 243, 255, 0.5), 0 0 56px rgba(154, 77, 255, 0.35);
                max-width: min(500px, 92vw);
                animation: slideIn 0.4s ease;
            `;
            
            // Add keyframe animations if not already in style
            if (!document.getElementById('theme-unlock-animations')) {
                const style = document.createElement('style');
                style.id = 'theme-unlock-animations';
                style.textContent = `
                    @keyframes fadeIn {
                        from { opacity: 0; }
                        to { opacity: 1; }
                    }
                    @keyframes slideIn {
                        from { transform: translateY(-50px); opacity: 0; }
                        to { transform: translateY(0); opacity: 1; }
                    }
                `;
                document.head.appendChild(style);
            }
            
            // Popup content
            popup.innerHTML = `
                <div style="font-size: 2rem; margin-bottom: var(--section-gap);">🎉</div>
                <h2 style="color: #00f3ff; margin: 0 0 var(--form-gap) 0; font-size: var(--title-size); text-shadow: 0 0 10px rgba(0, 243, 255, 0.8);">
                    New Theme Unlocked!
                </h2>
                <p style="color: #fff; font-size: var(--subtitle-size); margin: 0 0 var(--section-gap-bottom) 0;">
                    ${themeName}
                </p>
                <button onclick="this.closest('#theme-unlock-popup-overlay').remove()" 
                        style="padding: var(--btn-pad-y) var(--btn-pad-x); background: linear-gradient(135deg, #00f3ff, #9a4dff); 
                               color: #fff; border: none; border-radius: var(--panel-radius); font-size: var(--btn-font); 
                               font-weight: 600; cursor: pointer; box-shadow: 0 4px 12px rgba(0, 243, 255, 0.35);
                               transition: all 0.3s;">
                    Awesome!
                </button>
            `;
            
            overlay.appendChild(popup);
            document.body.appendChild(overlay);
            
            // Auto-close after 5 seconds
            setTimeout(() => {
                if (overlay.parentNode) {
                    overlay.style.animation = 'fadeOut 0.3s ease';
                    setTimeout(() => overlay.remove(), 300);
                }
            }, 5000);
            
            // Add fadeOut animation
            if (!document.getElementById('theme-unlock-animations')?.textContent.includes('fadeOut')) {
                const style = document.getElementById('theme-unlock-animations');
                if (style) {
                    style.textContent += `
                        @keyframes fadeOut {
                            from { opacity: 1; }
                            to { opacity: 0; }
                        }
                    `;
                }
            }
        }

        function handleSquiggsClick() {
            // Check if theme is already unlocked
            const isAlreadyUnlocked = localStorage.getItem('theme-scooters-unlocked') === 'true';
            
            // If already unlocked, just switch to it and show message
            if (isAlreadyUnlocked) {
                // Switch to the theme
                changeTheme('theme-scooters');
                
                // Show quick "already unlocked" popup
                showThemeAlreadyUnlockedPopup();
                
                return;
            }
            
            squiggsClickCount++;
            
            // Clear any existing timeout
            if (squiggsClickTimeout) {
                clearTimeout(squiggsClickTimeout);
            }
            
            // Reset counter after 3 seconds of no clicks
            squiggsClickTimeout = setTimeout(() => {
                squiggsClickCount = 0;
            }, 3000);
            
            // If clicked 3 times, unlock the theme
            if (squiggsClickCount >= 3) {
                // Unlock the theme
                localStorage.setItem('theme-scooters-unlocked', 'true');
                
                // Add theme to selector if not already present
                const selector = document.getElementById('themeSelector');
                if (selector) {
                    // Check if option already exists
                    const existingOption = selector.querySelector('option[value="theme-scooters"]');
                    if (!existingOption) {
                        const option = document.createElement('option');
                        option.value = 'theme-scooters';
                        option.textContent = '🛴🧰 Scooters Toolbox 🛴🧰';
                        selector.appendChild(option);
                    }
                }
                
                // Automatically switch to the new theme immediately
                changeTheme('theme-scooters');
                
                // Show popup notification after a brief delay to ensure theme is applied
                setTimeout(() => {
                    showThemeUnlockPopup('🛴🧰 Scooters Toolbox 🛴🧰');
                }, 100);
                
                // Reset counter
                squiggsClickCount = 0;
                if (squiggsClickTimeout) {
                    clearTimeout(squiggsClickTimeout);
                }
            }
        }

        function handleResetUnlocksClick() {
            resetClickCount++;
            
            // Clear any existing timeout
            if (resetClickTimeout) {
                clearTimeout(resetClickTimeout);
            }
            
            // Reset counter after 3 seconds of no clicks
            resetClickTimeout = setTimeout(() => {
                resetClickCount = 0;
            }, 3000);
            
            // If clicked 10 times, reset all unlocks
            if (resetClickCount >= 10) {
                // Clear all theme unlock flags
                localStorage.removeItem('theme-scooters-unlocked');
                localStorage.removeItem('theme-midnight-unlocked');
                localStorage.removeItem('theme-mattmab-unlocked');
                localStorage.removeItem('theme-venom-unlocked');
                localStorage.removeItem('theme-skippy-unlocked');
                localStorage.removeItem('theme-dunkie-unlocked');
                
                // Remove unlocked themes from selector
                const selector = document.getElementById('themeSelector');
                if (selector) {
                    const scootersOption = selector.querySelector('option[value="theme-scooters"]');
                    if (scootersOption) {
                        scootersOption.remove();
                    }
                    const midnightOption = selector.querySelector('option[value="theme-midnight"]');
                    if (midnightOption) {
                        midnightOption.remove();
                    }
                    const mattmabOption = selector.querySelector('option[value="theme-mattmab"]');
                    if (mattmabOption) {
                        mattmabOption.remove();
                    }
                    const venomOption = selector.querySelector('option[value="theme-venom"]');
                    if (venomOption) {
                        venomOption.remove();
                    }
                    const skippyOption = selector.querySelector('option[value="theme-skippy"]');
                    if (skippyOption) {
                        skippyOption.remove();
                    }
                    const dunkieOption = selector.querySelector('option[value="theme-dunkie"]');
                    if (dunkieOption) {
                        dunkieOption.remove();
                    }
                }
                
                // Show confirmation popup
                showResetUnlocksPopup();
                
                // Reset counter
                resetClickCount = 0;
                if (resetClickTimeout) {
                    clearTimeout(resetClickTimeout);
                }
            }
        }

        function showResetUnlocksPopup() {
            // Create popup overlay
            const overlay = document.createElement('div');
            overlay.id = 'reset-unlocks-popup-overlay';
            overlay.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.7);
                z-index: 10000;
                display: flex;
                align-items: center;
                justify-content: center;
                animation: fadeIn 0.3s ease;
            `;
            
            // Create popup content
            const popup = document.createElement('div');
            popup.style.cssText = `
                background: linear-gradient(135deg, rgba(255, 107, 107, 0.2), rgba(255, 69, 0, 0.2));
                border: 2px solid rgba(255, 107, 107, 0.6);
                border-radius: var(--header-radius);
                padding: var(--header-pad-y) var(--header-pad-x);
                text-align: center;
                box-shadow: 0 0 28px rgba(255, 107, 107, 0.5), 0 0 56px rgba(255, 69, 0, 0.35);
                max-width: min(500px, 92vw);
                animation: slideIn 0.4s ease;
            `;
            
            // Popup content
            popup.innerHTML = `
                <div style="font-size: 2rem; margin-bottom: var(--section-gap);">🔄</div>
                <h2 style="color: #ff6b6b; margin: 0 0 var(--form-gap) 0; font-size: var(--title-size); text-shadow: 0 0 10px rgba(255, 107, 107, 0.8);">
                    Theme Unlocks Reset!
                </h2>
                <p style="color: #fff; font-size: var(--subtitle-size); margin: 0 0 var(--section-gap-bottom) 0;">
                    All theme unlocks have been cleared.<br>
                    You can unlock them again by clicking the names in the credits.
                </p>
                <button onclick="this.closest('#reset-unlocks-popup-overlay').remove()" 
                        style="padding: var(--btn-pad-y) var(--btn-pad-x); background: linear-gradient(135deg, #ff6b6b, #ff4757); 
                               color: #fff; border: none; border-radius: var(--panel-radius); font-size: var(--btn-font); 
                               font-weight: 600; cursor: pointer; box-shadow: 0 4px 12px rgba(255, 107, 107, 0.35);
                               transition: all 0.3s;">
                    Got it!
                </button>
            `;
            
            overlay.appendChild(popup);
            document.body.appendChild(overlay);
        }

        function handleVenomClick() {
            // If background is already active, toggle it off
            if (venomBackgroundActive) {
                disableVenomBackground();
                return;
            }
            
            venomClickCount++;
            
            // Clear any existing timeout
            if (venomClickTimeout) {
                clearTimeout(venomClickTimeout);
            }
            
            // Reset counter after 3 seconds of no clicks
            venomClickTimeout = setTimeout(() => {
                venomClickCount = 0;
            }, 3000);
            
            // If clicked 3 times, activate GIF background
            if (venomClickCount >= 3 && venomClickCount < 5) {
                enableVenomBackground();
                
                // Don't reset counter yet - allow it to continue to 5 for theme unlock
            }
            
            // If clicked 5 times, unlock the theme (in addition to GIF background)
            if (venomClickCount >= 5) {
                // Check if theme is already unlocked
                const isAlreadyUnlocked = localStorage.getItem('theme-venom-unlocked') === 'true';
                
                if (!isAlreadyUnlocked) {
                    // Unlock the theme
                    localStorage.setItem('theme-venom-unlocked', 'true');
                    
                    // Add theme to selector if not already present
                    const selector = document.getElementById('themeSelector');
                    if (selector) {
                        // Check if option already exists
                        const existingOption = selector.querySelector('option[value="theme-venom"]');
                        if (!existingOption) {
                            const option = document.createElement('option');
                            option.value = 'theme-venom';
                            option.textContent = '🕷️ Venom';
                            selector.appendChild(option);
                        }
                    }
                    
                    // Automatically switch to the new theme immediately
                    changeTheme('theme-venom');
                    
                    // Show popup notification after a brief delay to ensure theme is applied
                    setTimeout(() => {
                        showThemeUnlockPopup('🕷️ Venom');
                    }, 100);
                } else {
                    // Theme already unlocked, just show "already unlocked" popup
                    showThemeAlreadyUnlockedPopup();
                }
                
                // Reset counter
                venomClickCount = 0;
                if (venomClickTimeout) {
                    clearTimeout(venomClickTimeout);
                }
            }
        }

        function enableVenomBackground() {
            // Disable other easter eggs if active
            if (skippyBackgroundActive) {
                disableSkippyBackground();
            }
            if (hobamjBackgroundActive) {
                disableHobamjBackground();
            }
            if (mattmabBackgroundActive) {
                disableMattmabBackground();
            }
            if (sinBackgroundActive) {
                disableSinBackground();
            }
            if (ynotBackgroundActive) {
                disableYnotBackground();
            }
            if (dunkieBackgroundActive) {
                disableDunkieBackground();
            }
            if (mrUserBackgroundActive) {
                disableMrUserBackground();
            }
            if (lShiftBackgroundActive) {
                disableLShiftBackground();
            }
            
            venomBackgroundActive = true;
            
            // Save to localStorage
            localStorage.setItem('venom-background-active', 'true');
            
            // Set body background to Venom GIF
            document.body.style.backgroundImage = 'url(https://save-editor.be/Venom.gif)';
            document.body.style.backgroundSize = 'cover';
            document.body.style.backgroundPosition = 'center';
            document.body.style.backgroundRepeat = 'no-repeat';
            document.body.style.backgroundAttachment = 'fixed';
            
            // Hide backdrop effect to see the GIF background
            const backdropEffect = document.getElementById('backdropEffect');
            if (backdropEffect) {
                backdropEffect.style.display = 'none';
            }
            
            // Create close button
            createVenomCloseButton();
        }

        function disableVenomBackground() {
            venomBackgroundActive = false;
            
            // Remove from localStorage
            localStorage.removeItem('venom-background-active');
            
            // Reset body background to default (let theme handle it)
            document.body.style.backgroundImage = '';
            document.body.style.backgroundSize = '';
            document.body.style.backgroundPosition = '';
            document.body.style.backgroundRepeat = '';
            document.body.style.backgroundAttachment = '';
            
            // Show backdrop effect again
            const backdropEffect = document.getElementById('backdropEffect');
            if (backdropEffect) {
                backdropEffect.style.display = '';
            }
            
            // Remove close button
            const closeBtn = document.getElementById('venom-close-btn');
            if (closeBtn) {
                closeBtn.remove();
            }
        }

        function createVenomCloseButton() {
            // Remove existing button if any
            const existingBtn = document.getElementById('venom-close-btn');
            if (existingBtn) {
                existingBtn.remove();
            }
            
            // Create close button
            const closeBtn = document.createElement('div');
            closeBtn.id = 'venom-close-btn';
            closeBtn.innerHTML = '✕';
            closeBtn.title = 'Click to disable secret background';
            closeBtn.style.cssText = `
                position: fixed;
                top: var(--page-pad);
                right: var(--page-pad);
                width: 34px;
                height: 34px;
                background: rgba(244, 67, 54, 0.8);
                border: 2px solid rgba(244, 67, 54, 1);
                border-radius: 50%;
                color: white;
                font-size: 18px;
                font-weight: bold;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                z-index: 10000;
                transition: all 0.2s;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
            `;
            
            closeBtn.onmouseover = function() {
                this.style.background = 'rgba(244, 67, 54, 1)';
                this.style.transform = 'scale(1.1)';
            };
            
            closeBtn.onmouseout = function() {
                this.style.background = 'rgba(244, 67, 54, 0.8)';
                this.style.transform = 'scale(1)';
            };
            
            closeBtn.onclick = function() {
                disableVenomBackground();
            };
            
            document.body.appendChild(closeBtn);
        }

        function handleMattmabClick() {
            // If background is already active, toggle it off
            if (mattmabBackgroundActive) {
                disableMattmabBackground();
                return;
            }
            
            mattmabClickCount++;
            
            // Clear any existing timeout
            if (mattmabClickTimeout) {
                clearTimeout(mattmabClickTimeout);
            }
            
            // Reset counter after 3 seconds of no clicks
            mattmabClickTimeout = setTimeout(() => {
                mattmabClickCount = 0;
            }, 3000);
            
            // If clicked 3 times, activate video background
            if (mattmabClickCount >= 3 && mattmabClickCount < 5) {
                enableMattmabBackground();
                
                // Don't reset counter yet - allow it to continue to 5 for theme unlock
            }
            
            // If clicked 5 times, unlock the theme (in addition to video background)
            if (mattmabClickCount >= 5) {
                // Check if theme is already unlocked
                const isAlreadyUnlocked = localStorage.getItem('theme-mattmab-unlocked') === 'true';
                
                if (!isAlreadyUnlocked) {
                    // Unlock the theme
                    localStorage.setItem('theme-mattmab-unlocked', 'true');
                    
                    // Add theme to selector if not already present
                    const selector = document.getElementById('themeSelector');
                    if (selector) {
                        // Check if option already exists
                        const existingOption = selector.querySelector('option[value="theme-mattmab"]');
                        if (!existingOption) {
                            const option = document.createElement('option');
                            option.value = 'theme-mattmab';
                            option.textContent = '⚡🌌 Cosmic Plasma Forge';
                            selector.appendChild(option);
                        }
                    }
                    
                    // Automatically switch to the new theme immediately
                    changeTheme('theme-mattmab');
                    
                    // Show popup notification after a brief delay to ensure theme is applied
                    setTimeout(() => {
                        showThemeUnlockPopup('⚡🌌 Cosmic Plasma Forge');
                    }, 100);
                } else {
                    // Theme already unlocked, just show "already unlocked" popup
                    showThemeAlreadyUnlockedPopup();
                }
                
                // Reset counter
                mattmabClickCount = 0;
                if (mattmabClickTimeout) {
                    clearTimeout(mattmabClickTimeout);
                }
            }
        }

        function enableMattmabBackground() {
            // Disable other easter eggs if active
            if (skippyBackgroundActive) {
                disableSkippyBackground();
            }
            if (hobamjBackgroundActive) {
                disableHobamjBackground();
            }
            if (venomBackgroundActive) {
                disableVenomBackground();
            }
            if (sinBackgroundActive) {
                disableSinBackground();
            }
            if (ynotBackgroundActive) {
                disableYnotBackground();
            }
            if (dunkieBackgroundActive) {
                disableDunkieBackground();
            }
            if (mrUserBackgroundActive) {
                disableMrUserBackground();
            }
            if (lShiftBackgroundActive) {
                disableLShiftBackground();
            }
            
            mattmabBackgroundActive = true;
            
            // Save to localStorage
            localStorage.setItem('mattmab-background-active', 'true');
            
            // Reset body background (video layer used instead, like nicnl)
            document.body.style.backgroundImage = '';
            document.body.style.backgroundSize = '';
            document.body.style.backgroundPosition = '';
            document.body.style.backgroundRepeat = '';
            document.body.style.backgroundAttachment = '';
            
            // Ensure there is only one video background element
            const existingVideo = document.getElementById('mattmab-video-bg');
            if (existingVideo) {
                existingVideo.remove();
            }
            
            // Create full-screen looping video background (match nicnl style); random 1 to MATTMAB_VIDEO_COUNT
            const MATTMAB_VIDEO_COUNT = 5; // mattmab1.mp4 … mattmab4.mp4; increase when you add more files
            const mattmabIndex = Math.floor(Math.random() * MATTMAB_VIDEO_COUNT) + 1;
            const video = document.createElement('video');
            video.id = 'mattmab-video-bg';
            video.src = `https://save-editor.be/mattmab${mattmabIndex}.mp4`;
            video.autoplay = true;
            video.loop = true;
            video.muted = false;
            video.volume = 1;
            video.playsInline = true;
            video.setAttribute('playsinline', '');
            video.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                object-fit: cover;
                pointer-events: none;
                z-index: -1;
            `;
            document.body.prepend(video);
            
            video.play().catch((err) => {
                console.warn('Mattmab easter egg video playback was blocked:', err);
            });
            
            // Hide backdrop effect to see the background clearly
            const backdropEffect = document.getElementById('backdropEffect');
            if (backdropEffect) {
                backdropEffect.style.display = 'none';
            }
            
            // Create close button
            createMattmabCloseButton();
        }

        function disableMattmabBackground() {
            mattmabBackgroundActive = false;
            
            // Remove from localStorage
            localStorage.removeItem('mattmab-background-active');
            
            // Remove Mattmab video element
            const video = document.getElementById('mattmab-video-bg');
            if (video) {
                video.remove();
            }
            
            // Show backdrop effect again
            const backdropEffect = document.getElementById('backdropEffect');
            if (backdropEffect) {
                backdropEffect.style.display = '';
            }
            
            // Remove close button
            const closeBtn = document.getElementById('mattmab-close-btn');
            if (closeBtn) {
                closeBtn.remove();
            }
        }

        function createMattmabCloseButton() {
            // Remove existing button if any
            const existingBtn = document.getElementById('mattmab-close-btn');
            if (existingBtn) {
                existingBtn.remove();
            }
            
            // Create close button
            const closeBtn = document.createElement('div');
            closeBtn.id = 'mattmab-close-btn';
            closeBtn.innerHTML = '✕';
            closeBtn.title = 'Click to disable secret background';
            closeBtn.style.cssText = `
                position: fixed;
                top: var(--page-pad);
                right: var(--page-pad);
                width: 34px;
                height: 34px;
                background: rgba(244, 67, 54, 0.8);
                border: 2px solid rgba(244, 67, 54, 1);
                border-radius: 50%;
                color: white;
                font-size: 18px;
                font-weight: bold;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                z-index: 10000;
                transition: all 0.2s;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
            `;
            
            closeBtn.onmouseover = function() {
                this.style.background = 'rgba(244, 67, 54, 1)';
                this.style.transform = 'scale(1.1)';
            };
            
            closeBtn.onmouseout = function() {
                this.style.background = 'rgba(244, 67, 54, 0.8)';
                this.style.transform = 'scale(1)';
            };
            
            closeBtn.onclick = function() {
                disableMattmabBackground();
            };
            
            document.body.appendChild(closeBtn);
        }

        // Load saved theme on page load
        document.addEventListener('DOMContentLoaded', function() {

            // FIRST: Check if Scooters theme is unlocked and add to selector BEFORE loading theme
            // This ensures the option exists when changeTheme tries to set the selector value
            const scootersUnlocked = localStorage.getItem('theme-scooters-unlocked') === 'true';
            if (scootersUnlocked) {
                const selector = document.getElementById('themeSelector');
                if (selector) {
                    // Check if option already exists
                    const existingOption = selector.querySelector('option[value="theme-scooters"]');
                    if (!existingOption) {
                        const option = document.createElement('option');
                        option.value = 'theme-scooters';
                        option.textContent = '🛴🧰 Scooters Toolbox 🛴🧰';
                        selector.appendChild(option);
                    }
                }
            }

            // Check if Midnight Blue theme is unlocked and add to selector (legacy)
            const midnightUnlocked = localStorage.getItem('theme-midnight-unlocked') === 'true';
            if (midnightUnlocked) {
                const selector = document.getElementById('themeSelector');
                if (selector) {
                    // Check if option already exists
                    const existingOption = selector.querySelector('option[value="theme-midnight"]');
                    if (!existingOption) {
                        const option = document.createElement('option');
                        option.value = 'theme-midnight';
                        option.textContent = '🌙 Midnight Blue';
                        selector.appendChild(option);
                    }
                }
            }

            // Check if Cosmic Plasma Forge theme is unlocked and add to selector
            const mattmabUnlocked = localStorage.getItem('theme-mattmab-unlocked') === 'true';
            if (mattmabUnlocked) {
                const selector = document.getElementById('themeSelector');
                if (selector) {
                    // Check if option already exists
                    const existingOption = selector.querySelector('option[value="theme-mattmab"]');
                    if (!existingOption) {
                        const option = document.createElement('option');
                        option.value = 'theme-mattmab';
                        option.textContent = '⚡🌌 Cosmic Plasma Forge';
                        selector.appendChild(option);
                    }
                }
            }
            
            // Load Venom theme if unlocked
            const venomUnlocked = localStorage.getItem('theme-venom-unlocked') === 'true';
            if (venomUnlocked) {
                const selector = document.getElementById('themeSelector');
                if (selector) {
                    // Check if option already exists
                    const existingOption = selector.querySelector('option[value="theme-venom"]');
                    if (!existingOption) {
                        const option = document.createElement('option');
                        option.value = 'theme-venom';
                        option.textContent = '🕷️ Venom';
                        selector.appendChild(option);
                    }
                }
            }

            const skippyUnlocked = localStorage.getItem('theme-skippy-unlocked') === 'true';
            if (skippyUnlocked) {
                const selector = document.getElementById('themeSelector');
                if (selector) {
                    // Check if option already exists
                    const existingOption = selector.querySelector('option[value="theme-skippy"]');
                    if (!existingOption) {
                        const option = document.createElement('option');
                        option.value = 'theme-skippy';
                        option.textContent = '🔥💀 Skullmasher';
                        selector.appendChild(option);
                    }
                }
            }

            const dunkieUnlocked = localStorage.getItem('theme-dunkie-unlocked') === 'true';
            if (dunkieUnlocked) {
                const selector = document.getElementById('themeSelector');
                if (selector) {
                    // Check if option already exists
                    const existingOption = selector.querySelector('option[value="theme-dunkie"]');
                    if (!existingOption) {
                        const option = document.createElement('option');
                        option.value = 'theme-dunkie';
                        option.textContent = '💖 Lootlobby Queen';
                        selector.appendChild(option);
                    }
                }
            }
            
            // THEN: Load saved theme (now the selector has all options available)
            const savedTheme = localStorage.getItem('selectedTheme') || 'theme-default';
            changeTheme(savedTheme);
            
            // Ensure selector value is set correctly (safety check)
            const selector = document.getElementById('themeSelector');
            if (selector && selector.value !== savedTheme) {
                selector.value = savedTheme;
            }
            
            // Add click handler to RDP/Squiggs span (if not already set in HTML)
            const squiggsSpan = Array.from(document.querySelectorAll('span')).find(span => 
                span.textContent === 'RDP/Squiggs'
            );
            if (squiggsSpan && !squiggsSpan.onclick) {
                squiggsSpan.style.cursor = 'pointer';
                squiggsSpan.onclick = handleSquiggsClick;
            }

            // Add click handler to Venom span (if not already set in HTML)
            const venomSpan = Array.from(document.querySelectorAll('span')).find(span => 
                span.textContent === 'VΣПӨM ӨG' || span.textContent === 'VENOM OG' || span.textContent.includes('VENOM')
            );
            if (venomSpan && !venomSpan.onclick) {
                venomSpan.style.cursor = 'pointer';
                venomSpan.onclick = handleVenomClick;
            }
            
            // Add click handler to Mattmab span (if not already set in HTML)
            const mattmabSpan = Array.from(document.querySelectorAll('span')).find(span => 
                span.textContent === 'Mattmab'
            );
            if (mattmabSpan && !mattmabSpan.onclick) {
                mattmabSpan.style.cursor = 'pointer';
                mattmabSpan.onclick = handleMattmabClick;
            }
            
            // Scroll to top on page load/refresh
            window.scrollTo(0, 0);
            
            // Setup save file input handler
            setupSaveFileInput();
        });
        
        // Also scroll to top when page is fully loaded
        window.addEventListener('load', function() {
            window.scrollTo(0, 0);
            
            // Restore active background from localStorage
            restoreActiveBackground();
        });

        // Restore active background on page load
        function restoreActiveBackground() {
            // Clear video-background state on load so we never try to autoplay (browsers block it)
            localStorage.removeItem('mattmab-background-active');
            localStorage.removeItem('nicnl-background-active');

            // Check each background in order of priority (first one found wins); video eggs are not restored
            if (localStorage.getItem('skippy-background-active') === 'true') {
                enableSkippyBackground();
            } else if (localStorage.getItem('hobamj-background-active') === 'true') {
                enableHobamjBackground();
            } else if (localStorage.getItem('venom-background-active') === 'true') {
                enableVenomBackground();
            } else if (localStorage.getItem('sin-background-active') === 'true') {
                enableSinBackground();
            } else if (localStorage.getItem('ynot-background-active') === 'true') {
                enableYnotBackground();
            } else if (localStorage.getItem('dunkie-background-active') === 'true') {
                enableDunkieBackground();
            } else if (localStorage.getItem('mruser-background-active') === 'true') {
                enableMrUserBackground();
            } else if (localStorage.getItem('lshift-background-active') === 'true') {
                enableLShiftBackground();
            }
        }

        // ===== SAVE EDITOR STATE =====
        window.saveEditorState = {
            isLoaded: false,
            yamlContent: null,
            decodedItems: [],
            backpackSlotsData: {},
            originalFileName: null,
            originalFileHandle: null,  // For File System Access API
            originalDirectoryHandle: null,  // For File System Access API - stores the directory
            isProcessing: false  // Track if any background process is running
        };

        // Helper function to set processing state and update UI
        function setSaveProcessingState(isProcessing, processName = '') {
            window.saveEditorState.isProcessing = isProcessing;
            const encryptBtn = document.querySelector('button[onclick="encryptSaveFile()"]');
            const overwriteBtn = document.getElementById('overwrite-save-btn');
            
            if (encryptBtn) {
                encryptBtn.disabled = isProcessing;
                encryptBtn.style.opacity = isProcessing ? '0.5' : '1';
                encryptBtn.style.cursor = isProcessing ? 'not-allowed' : 'pointer';
                if (isProcessing) {
                    encryptBtn.title = `⏳ Processing: ${processName || 'Please wait...'}`;
                } else {
                    encryptBtn.title = '';
                }
            }
            
            if (overwriteBtn) {
                overwriteBtn.disabled = isProcessing;
                overwriteBtn.style.opacity = isProcessing ? '0.5' : '1';
                overwriteBtn.style.cursor = isProcessing ? 'not-allowed' : 'pointer';
                if (isProcessing) {
                    overwriteBtn.title = `⏳ Processing: ${processName || 'Please wait...'}`;
                } else {
                    overwriteBtn.title = '';
                }
            }
        }

        // ===== SAVE EDITOR FUNCTIONS =====
        const DEFAULT_SAVE_API_BASE_URL = "https://save-editor.be/blcrypt/api.php";

        function getSaveApiBaseUrl() {
            return window.SAVE_API_BASE_URL || DEFAULT_SAVE_API_BASE_URL;
        }
        
        // Handle file input change - auto-decrypt when file is selected
        function setupSaveFileInput() {
            const fileInput = document.getElementById('save-file-input');
            const fileNameText = document.getElementById('save-file-name-text');
            const fileSelectedDiv = document.getElementById('save-file-selected-name');
            
            if (fileInput) {
                fileInput.addEventListener('change', async function(e) {
                    if (e.target.files && e.target.files.length > 0) {
                        const file = e.target.files[0];
                        window.saveEditorState.originalFileName = file.name;
                        window.saveEditorState.originalFileHandle = null; // Clear handle when using regular input
                        window.saveEditorState.originalDirectoryHandle = null;
                        
                        if (fileNameText) fileNameText.textContent = file.name;
                        if (fileSelectedDiv) fileSelectedDiv.style.display = 'block';
                        
                        // Auto-decrypt the selected file
                        await decryptSaveFile();
                        // Update auto-add checkbox state after save is loaded
                        if (typeof updateAutoAddToBackpackCheckbox === 'function') {
                            updateAutoAddToBackpackCheckbox();
                        }
                    } else {
                        if (fileSelectedDiv) fileSelectedDiv.style.display = 'none';
                    }
                });
            }
        }
        
        async function decryptSaveFile() {
            const fileInput = document.getElementById('save-file-input');
            const steamIdInput = document.getElementById('save-steamid');
            const statusEl = document.getElementById('save-decrypt-status');
            const yamlContent = document.getElementById('save-yaml-content');
            const progressSection = document.getElementById('save-decode-progress');
            
            let file = null;
            let fileHandle = null;
            
            // Check if file is already selected in the file input (from auto-decrypt)
            if (fileInput && fileInput.files && fileInput.files.length > 0) {
                file = fileInput.files[0];
                window.saveEditorState.originalFileName = file.name;
                window.saveEditorState.originalFileHandle = null; // Regular input doesn't provide file handle
                window.saveEditorState.originalDirectoryHandle = null;
            } else {
                // No file selected yet - try to use File System Access API if available (when button is clicked manually)
                if ('showOpenFilePicker' in window) {
                    try {
                        const [handle] = await window.showOpenFilePicker({
                            types: [{
                                description: 'Bl4 Save / YAML / Text',
                                accept: { 
                                    'application/octet-stream': ['.sav'],
                                    'text/yaml': ['.yaml', '.yml'],
                                    'application/x-yaml': ['.yaml', '.yml'],
                                    'text/plain': ['.txt']
                                }
                            }],
                            multiple: false
                        });
                        
                        fileHandle = handle;
                        file = await handle.getFile();
                        
                        // Store file handle for overwrite functionality
                        window.saveEditorState.originalFileHandle = fileHandle;
                        window.saveEditorState.originalFileName = file.name;
                        
                        // Try to get and store the directory handle
                        try {
                            // Get the directory by querying the parent directory
                            const directoryHandle = await handle.getParent();
                            if (directoryHandle) {
                                window.saveEditorState.originalDirectoryHandle = directoryHandle;
                            }
                        } catch (dirError) {
                            console.warn('Could not get directory handle:', dirError);
                            // Continue anyway - directory handle is optional
                        }
                        
                        // Update the file input display
                        const fileNameText = document.getElementById('save-file-name-text');
                        const fileSelectedDiv = document.getElementById('save-file-selected-name');
                        if (fileNameText) fileNameText.textContent = file.name;
                        if (fileSelectedDiv) fileSelectedDiv.style.display = 'block';
                        
                    } catch (error) {
                        // User cancelled or error
                        if (error.name !== 'AbortError') {
                            console.warn('File System Access API failed:', error);
                        }
                        return; // Don't proceed if user cancelled
                    }
                } else {
                    // No file selected and no File System Access API - show error
                    showSaveStatus('save-decrypt-status', '❌ Please select a .sav, .yaml, or .txt file first.', false);
                    return;
                }
            }

            if (!file) {
                return;
            }

            const fileExtension = file.name.split('.').pop().toLowerCase();
            const isTextImport =
                fileExtension === 'yaml' || fileExtension === 'yml' || fileExtension === 'txt';

            let steamId = '';
            if (!isTextImport) {
                steamId = steamIdInput ? steamIdInput.value.trim() : '';
                if (!steamId) {
                    showSaveStatus(
                        'save-decrypt-status',
                        '❌ Please enter your Steam ID or Epic ID to decrypt .sav files.',
                        false
                    );
                    return;
                }
                if (typeof window.trackEvent === 'function') {
                    window.trackEvent('decrypt_attempt');
                }
                try {
                    localStorage.setItem('lastSteamEpicId', steamId);
                } catch (e) {
                    console.warn('Failed to cache Steam/Epic ID:', e);
                }
            }

            const decryptStartTime = performance.now();
            
            try {
                // Track save load attempt
                const loadStartTime = performance.now();
                if (typeof window.trackEvent === 'function') {
                    window.trackEvent('save_load_attempt', { source: 'file_picker' });
                }

                const notifySaveLoad =
                    typeof window.showNotification === 'function' ? window.showNotification : null;
                if (notifySaveLoad) {
                    notifySaveLoad('Loading save…', 'info', {
                        replaceId: 'save-load-indicator',
                        durationMs: 0
                    });
                }
                await new Promise(function (resolve) {
                    requestAnimationFrame(function () {
                        requestAnimationFrame(resolve);
                    });
                });

                let yamlText;
                
                if (isTextImport) {
                    // Read YAML or plain-text export directly (no Steam ID / API)
                    showSaveStatus('save-decrypt-status', '⏳ Loading file...<br><small style="color: #ffa726; margin-top: 5px; display: block;">⚠️ Save files with many items may take a long time to parse and the page may display as unresponsive. Please wait and be patient.</small>', true);
                    yamlText = await file.text();
                } else {
                    // Decrypt .sav file
                    showSaveStatus('save-decrypt-status', '⏳ Decrypting save file...<br><small style="color: #ffa726; margin-top: 5px; display: block;">⚠️ Save files with many items may take a long time to parse and the page may display as unresponsive. Please wait and be patient.</small>', true);
                    
                    // Read file as base64
                    const fileReader = new FileReader();
                    const fileData = await new Promise((resolve, reject) => {
                        fileReader.onload = (e) => resolve(e.target.result);
                        fileReader.onerror = reject;
                        fileReader.readAsDataURL(file);
                    });
                    
                    // Extract base64 data (remove data:application/octet-stream;base64, prefix)
                    const base64Data = fileData.split(',')[1];
                    
                    const requestBody = {
                        command: 'decrypt',
                        steamid: steamId,
                        sav_data: base64Data
                    };
                
                    const response = await fetch(getSaveApiBaseUrl(), {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(requestBody)
                    });
                    
                    if (!response.ok) {
                        const errorText = await response.text();
                        throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
                    }
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        yamlText = data.yaml_content || (data.yaml_data ? JSON.stringify(data.yaml_data, null, 2) : '');
                    } else {
                        throw new Error(data.error || 'Failed to decrypt save file');
                    }
                }
                
                if (!yamlText || !String(yamlText).trim()) {
                    throw new Error('Decrypt succeeded, but no YAML content was returned.');
                }

                // Process YAML content (from either .sav decryption or direct .yaml file)
                window.saveEditorState.isLoaded = true;
                window.saveEditorState.yamlContent = yamlText;
                
                setYamlTextareaValue(yamlText);
                yamlContent.style.display = 'block';
                const decodeItemsDisplayBtn = document.getElementById('decode-items-display-btn');
                if (decodeItemsDisplayBtn) decodeItemsDisplayBtn.style.display = 'block';
                window.originalYAMLContent = yamlText;
                
                // Initialize Monaco Editor if not already initialized
                if (!window.yamlMonacoEditor) {
                    setTimeout(initMonacoYamlEditor, 100);
                } else {
                    // Update Monaco editor with the loaded content
                    window.yamlMonacoEditor.setValue(yamlText);
                }
                
                // Update auto-add to backpack checkbox state
                updateAutoAddToBackpackCheckbox();
                
                // Show overwrite button if we have an original file name
                const overwriteBtn = document.getElementById('overwrite-save-btn');
                const overwriteNote = document.getElementById('overwrite-save-note');
                if (overwriteBtn && window.saveEditorState.originalFileName) {
                    overwriteBtn.style.display = 'block';
                    if (overwriteNote) overwriteNote.style.display = 'block';
                }
                
                // Set up auto-decode on YAML changes
                setupYamlAutoDecode();
                
                // Decode item serials
                await decodeYamlInventory(yamlText, {
                    itemDecode: "none",
                    notifyDecodePhases: true,
                });
                
                // Extract and set equipped slots data
                window.equippedSlotsData = extractEquippedSlotsFromYAML(yamlText);
                
                // Update preset input fields with current values
                setTimeout(() => updatePresetInputs(), 200);
                
                // Update button visibility
                updateBackpackButtons();
                // Update bank buttons
                if (typeof updateBankButtons === 'function') {
                    updateBankButtons();
                }
                
                // Update bulk adder overlay
                setBulkAdderAvailability(true);
                
                // Update random item modal button states if modal is open
                updateRandomItemModalButtonStates();
                
                // Track save load success
                const loadDuration_ms = Math.round(performance.now() - loadStartTime);
                if (typeof window.trackEvent === 'function') {
                    window.trackEvent('save_load_success', { 
                        duration_ms: loadDuration_ms, 
                        source: 'file_picker' 
                    });
                }
                
                const successMessage = isTextImport
                    ? '✅ File loaded successfully!'
                    : '✅ Save file decrypted successfully!';
                showSaveStatus('save-decrypt-status', successMessage, true);

                if (notifySaveLoad) {
                    const rawName = window.saveEditorState.originalFileName || 'Save';
                    const safeName = String(rawName).replace(/[/\\]/g, '');
                    const shortName =
                        safeName.length > 44 ? safeName.slice(0, 41) + '…' : safeName;
                    notifySaveLoad('Save loaded · ' + shortName, 'success', {
                        replaceId: 'save-load-indicator',
                        durationMs: 5000
                    });
                }
                    
                    // Hide overlays for sections (sections are now always visible)
                    const equippedSlotsOverlay = document.getElementById('equippedSlotsOverlay');
                    if (equippedSlotsOverlay) {
                        equippedSlotsOverlay.style.display = 'none';
                    }
                    
                    const missionEditorOverlay = document.getElementById('missionEditorOverlay');
                    if (missionEditorOverlay) {
                        missionEditorOverlay.style.display = 'none';
                    }
                    
                    // Hide mass edit tools overlay
                    const massEditToolsOverlay = document.getElementById('massEditToolsOverlay');
                    if (massEditToolsOverlay) {
                        massEditToolsOverlay.style.display = 'none';
                    }
                    
                    // Hide presets overlay and render presets
                    const presetsSection = document.getElementById('save-presets-section');
                    if (presetsSection) {
                        document.getElementById('presetSectionOverlay').style.display = 'none';
                        renderPresets();
                    }
                    
                    const editValuesSection = document.getElementById('save-edit-values-section');
                    if (editValuesSection) {
                        const overlay = document.getElementById('editValuesSectionOverlay');
                        if (overlay) overlay.style.display = 'none';
                        renderEditValues();
                    }
                    
                    // Hide backpack and lost loot overlays
                    const backpackOverlay = document.getElementById('backpackOverlay');
                    if (backpackOverlay) {
                        backpackOverlay.style.display = 'none';
                    }
                    
                    const lostLootOverlay = document.getElementById('lostLootOverlay');
                    if (lostLootOverlay) {
                        lostLootOverlay.style.display = 'none';
                    }
                    
                    // Hide bulk adder overlay
                    const bulkAdderOverlay = document.getElementById('bulk-adder-overlay');
                    if (bulkAdderOverlay) {
                        bulkAdderOverlay.style.display = 'none';
                    }
            } catch (error) {
                console.error('Decrypt error:', error);

                const notifySaveErr =
                    typeof window.showNotification === 'function' ? window.showNotification : null;
                if (notifySaveErr) {
                    const errFull = error && error.message ? String(error.message) : String(error);
                    const truncated =
                        errFull.length > 120 ? errFull.slice(0, 117) + '…' : errFull;
                    notifySaveErr('Save failed: ' + truncated, 'error', {
                        replaceId: 'save-load-indicator',
                        durationMs: 8000
                    });
                }
                
                // Track decrypt failure if not already tracked
                const duration_ms = Math.round(performance.now() - decryptStartTime);
                if (typeof window.trackEvent === 'function') {
                    const errorMsg = error.message || String(error);
                    window.trackEvent('decrypt_fail', { 
                        duration_ms, 
                        error_code: errorMsg.substring(0, 80),
                        reason: errorMsg.substring(0, 200)
                    });
                }
                
                // Check for Zlib decompression error (incorrect Steam/Epic ID)
                if (error.message && error.message.includes('Zlib decompression failed')) {
                    const friendlyMessage = 'Please Check Steam or Epic ID and verify that this .sav or .yaml is valid.';
                    showSaveStatus('save-decrypt-status', `❌ Error: ${friendlyMessage}`, false);
                    showSteamIdErrorPopup();
                } else {
                    showSaveStatus('save-decrypt-status', `❌ Error: ${error.message}`, false);
                }
            }
        }

        async function encryptSaveFile() {
            // Check if any process is running
            if (window.saveEditorState.isProcessing) {
                showSaveStatus('save-encrypt-status', '❌ Cannot encrypt while a process is running. Please wait for the current operation to complete.', false);
                return;
            }
            
            const steamIdInput = document.getElementById('save-steamid');
            const yamlTextarea = document.getElementById('save-yaml-textarea');
            const statusEl = document.getElementById('save-encrypt-status');
            
            const steamId = steamIdInput.value.trim();
            if (!steamId) {
                showSaveStatus('save-encrypt-status', '❌ Please enter your Steam ID or Epic ID first.', false);
                return;
            }
            
            const yamlContent = getYamlTextareaValue().trim();
            if (!yamlContent) {
                showSaveStatus('save-encrypt-status', '❌ No YAML content to encrypt.', false);
                return;
            }
            
            // Track encrypt attempt
            const encryptStartTime = performance.now();
            if (typeof window.trackEvent === 'function') {
                window.trackEvent('encrypt_attempt');
            }
            
            // Set processing state
            setSaveProcessingState(true, 'Encrypting save file');
            
            try {
                showSaveStatus('save-encrypt-status', '⏳ Encrypting save file...', true);
                
                // Try yaml_content first, API might also accept yaml_data
                const requestBody = {
                    command: 'encrypt',
                    steamid: steamId,
                    yaml_content: yamlContent,
                    yaml_data: yamlContent  // Fallback field name
                };
                
                const response = await fetch(getSaveApiBaseUrl(), {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(requestBody)
                });
                
                if (!response.ok) {
                    const errorText = await response.text();
                    throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
                }
                
                // Check content type before parsing
                const contentType = response.headers.get('content-type');
                let data;
                
                if (contentType && contentType.includes('application/json')) {
                    data = await response.json();
                } else {
                    // Try to parse as JSON anyway, but handle errors
                    const text = await response.text();
                    try {
                        data = JSON.parse(text);
                    } catch (e) {
                        throw new Error(`Invalid response format. Expected JSON but got: ${contentType || 'unknown'}. Response: ${text.substring(0, 200)}`);
                    }
                }
                
                // Log response for debugging
                if (DEBUG) {
                    console.log('Encrypt API response:', data);
                }
                
                // Check for success and encrypted data (try multiple possible field names)
                const encryptedData = data.encrypted || data.encrypted_data || data.sav_data || data.data;
                
                if (data.success && encryptedData) {
                    // Track encrypt success
                    const duration_ms = Math.round(performance.now() - encryptStartTime);
                    if (typeof window.trackEvent === 'function') {
                        window.trackEvent('encrypt_success', { duration_ms });
                        window.trackEvent('save_export');
                    }
                    
                    // Convert base64 to blob and download
                    const binaryString = atob(encryptedData);
                    const bytes = new Uint8Array(binaryString.length);
                    for (let i = 0; i < binaryString.length; i++) {
                        bytes[i] = binaryString.charCodeAt(i);
                    }
                    const blob = new Blob([bytes], { type: 'application/octet-stream' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    // Use original filename if available, otherwise use default
                    // Always use .sav extension when encrypting
                    let fileName = window.saveEditorState.originalFileName || 'save_encrypted.sav';
                    // Replace .yaml/.yml with .sav extension
                    if (fileName.toLowerCase().endsWith('.yaml') || fileName.toLowerCase().endsWith('.yml')) {
                        fileName = fileName.replace(/\.(yaml|yml)$/i, '.sav');
                    } else if (!fileName.toLowerCase().endsWith('.sav')) {
                        // If no extension or different extension, add .sav
                        fileName = fileName.replace(/\.[^.]*$/, '') + '.sav';
                    }
                    a.download = fileName;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                    showSaveStatus('save-encrypt-status', `✅ Save file encrypted and downloaded as "${fileName}"!`, true);
                } else {
                    // Always log the response for debugging
                    console.error('Encrypt API failed. Full response:', data);
                    console.error('Response keys:', Object.keys(data || {}));
                    console.error('Success value:', data.success);
                    console.error('Encrypted data present:', !!encryptedData);
                    
                    // Provide detailed error message
                    const errorMsg = data.error || data.message || data.reason || 
                        `API returned success: ${data.success}, encrypted data present: ${!!encryptedData}. Check console for full response.`;
                    throw new Error(errorMsg || 'Failed to encrypt save file');
                }
            } catch (error) {
                console.error('Encrypt error:', error);
                showSaveStatus('save-encrypt-status', `❌ Error: ${error.message}`, false);
            } finally {
                // Clear processing state
                setSaveProcessingState(false);
            }
        }

        // Profile Editor Functions
        function getProfileYamlTextElement() {
            return document.getElementById('profile-yaml-textarea');
        }

        function readProfileYamlDomValue() {
            const textarea = getProfileYamlTextElement();
            if (!textarea) {
                return window.profileYAMLContent || '';
            }
            if (typeof textarea.value === 'string') {
                return textarea.value || '';
            }
            if (typeof textarea.__msbtProfileYamlValue === 'string') {
                return textarea.__msbtProfileYamlValue;
            }
            return textarea.textContent || window.profileYAMLContent || '';
        }

        function writeProfileYamlDomValue(value) {
            const normalizedValue = value || '';
            window.profileYAMLContent = normalizedValue;
            const textarea = getProfileYamlTextElement();
            if (!textarea) {
                return;
            }
            textarea.__msbtProfileYamlValue = normalizedValue;
            if (typeof textarea.value === 'string') {
                textarea.value = normalizedValue;
            } else {
                textarea.textContent = normalizedValue;
                textarea.contentEditable = 'true';
                textarea.tabIndex = 0;
                textarea.style.whiteSpace = 'pre';
                textarea.style.overflow = 'auto';
                textarea.style.fontFamily = 'Consolas, "Courier New", monospace';
                textarea.style.fontSize = '12px';
                textarea.style.lineHeight = '1.35';
                textarea.style.padding = '12px';
                textarea.style.boxSizing = 'border-box';
            }
            if (!textarea.__msbtProfileYamlInputBound) {
                textarea.addEventListener('input', function () {
                    const nextValue = typeof textarea.value === 'string'
                        ? (textarea.value || '')
                        : (textarea.textContent || '');
                    textarea.__msbtProfileYamlValue = nextValue;
                    window.profileYAMLContent = nextValue;
                });
                textarea.__msbtProfileYamlInputBound = true;
            }
        }

        function ensureProfileYamlEditorFallback(value) {
            if (
                window.profileMonacoEditor &&
                typeof window.profileMonacoEditor.getValue === 'function' &&
                typeof window.profileMonacoEditor.setValue === 'function'
            ) {
                if (typeof value === 'string') {
                    window.profileMonacoEditor.setValue(value);
                }
                return window.profileMonacoEditor;
            }

            writeProfileYamlDomValue(typeof value === 'string' ? value : readProfileYamlDomValue());
            window.profileMonacoEditor = {
                __msbtFallback: true,
                getValue: function () {
                    return readProfileYamlDomValue();
                },
                setValue: function (nextValue) {
                    writeProfileYamlDomValue(nextValue || '');
                },
                layout: function () {},
                dispose: function () {},
                onDidChangeModelContent: function (handler) {
                    const textarea = getProfileYamlTextElement();
                    if (!textarea || typeof handler !== 'function') {
                        return { dispose: function () {} };
                    }
                    const listener = function () {
                        handler();
                    };
                    textarea.addEventListener('input', listener);
                    return {
                        dispose: function () {
                            textarea.removeEventListener('input', listener);
                        }
                    };
                }
            };
            return window.profileMonacoEditor;
        }

        function getProfileYamlEditorValue() {
            if (window.profileMonacoEditor && typeof window.profileMonacoEditor.getValue === 'function') {
                return window.profileMonacoEditor.getValue() || '';
            }
            return readProfileYamlDomValue();
        }

        function setProfileYamlEditorValue(value) {
            const editor = ensureProfileYamlEditorFallback(value || '');
            if (editor && typeof editor.setValue === 'function') {
                editor.setValue(value || '');
            }
        }

        async function decryptProfileFile() {
            const fileInput = document.getElementById('profile-file-input');
            const steamIdInput = document.getElementById('profile-steamid');
            const statusEl = document.getElementById('profile-decrypt-status');
            const yamlContent = document.getElementById('profile-yaml-content');
            
            const steamId = steamIdInput.value.trim();
            if (!steamId) {
                showSaveStatus('profile-decrypt-status', '❌ Please enter your Steam ID or Epic ID first.', false);
                return;
            }
            
            // Cache the Steam/Epic ID for future use
            try {
                localStorage.setItem('lastSteamEpicId', steamId);
            } catch (e) {
                console.warn('Failed to cache Steam/Epic ID:', e);
            }
            
            let file = null;
            
            // Check if file is already selected
            if (fileInput && fileInput.files && fileInput.files.length > 0) {
                file = fileInput.files[0];
            } else {
                // No file selected - try to use File System Access API if available
                if ('showOpenFilePicker' in window) {
                    try {
                        const [handle] = await window.showOpenFilePicker({
                            types: [{
                                description: 'Bl4 Profile File',
                                accept: { 
                                    'application/octet-stream': ['.sav'],
                                    'text/yaml': ['.yaml', '.yml'],
                                    'application/x-yaml': ['.yaml', '.yml']
                                }
                            }],
                            multiple: false
                        });
                        
                        file = await handle.getFile();
                        
                        // Update the file input display
                        const fileNameText = document.getElementById('profile-file-name-text');
                        const fileSelectedDiv = document.getElementById('profile-file-selected-name');
                        if (fileNameText) fileNameText.textContent = file.name;
                        if (fileSelectedDiv) fileSelectedDiv.style.display = 'block';
                        
                    } catch (error) {
                        if (error.name !== 'AbortError') {
                            console.warn('File System Access API failed:', error);
                        }
                        return;
                    }
                } else {
                    showSaveStatus('profile-decrypt-status', '❌ Please select a profile.sav or .yaml file first.', false);
                    return;
                }
            }
            
            try {
                const fileExtension = file.name.split('.').pop().toLowerCase();
                const isYamlFile = fileExtension === 'yaml' || fileExtension === 'yml';
                
                let yamlText;
                
                if (isYamlFile) {
                    showSaveStatus('profile-decrypt-status', '⏳ Loading YAML file...', true);
                    yamlText = await file.text();
                    // Normalize YAML - remove !tags which jsyaml can't handle
                    if (yamlText) {
                        yamlText = yamlText.replace(/:\s*!tags/g, ':');
                        yamlText = yamlText.replace(/:\s*!<[^>]+>/g, ':');
                        
                        // Try to parse and re-dump to normalize formatting
                        try {
                            const parsed = jsyaml.load(yamlText);
                            yamlText = jsyaml.dump(parsed, { lineWidth: -1, noRefs: true });
                        } catch (e) {
                            console.warn('Could not normalize YAML, using original:', e);
                        }
                    }
                } else {
                    showSaveStatus('profile-decrypt-status', '⏳ Decrypting profile file...', true);
                    
                    const fileReader = new FileReader();
                    const fileData = await new Promise((resolve, reject) => {
                        fileReader.onload = (e) => resolve(e.target.result);
                        fileReader.onerror = reject;
                        fileReader.readAsDataURL(file);
                    });
                    
                    const base64Data = fileData.split(',')[1];
                    
                    const requestBody = {
                        command: 'decrypt',
                        steamid: steamId,
                        sav_data: base64Data
                    };
                
                    const response = await fetch(getSaveApiBaseUrl(), {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(requestBody)
                    });
                    
                    if (!response.ok) {
                        const errorText = await response.text();
                        throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
                    }
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        yamlText = data.yaml_content || (data.yaml_data ? JSON.stringify(data.yaml_data, null, 2) : '');
                    } else {
                        throw new Error(data.error || 'Failed to decrypt profile file');
                    }
                }
                
                if (!yamlText || !String(yamlText).trim()) {
                    throw new Error('Decrypt succeeded, but no YAML content was returned.');
                }

                // Normalize YAML - remove !tags which jsyaml can't handle
                if (yamlText) {
                    yamlText = yamlText.replace(/:\s*!tags/g, ':');
                    yamlText = yamlText.replace(/:\s*!<[^>]+>/g, ':');
                    
                    // Try to parse and re-dump to normalize formatting
                    try {
                        const parsed = jsyaml.load(yamlText);
                        yamlText = jsyaml.dump(parsed, { lineWidth: -1, noRefs: true });
                    } catch (e) {
                        console.warn('Could not normalize YAML, using original:', e);
                    }
                }
                
                setProfileYamlEditorValue(yamlText);
                if (typeof ensureProfileProgressionMonacoContentListener === 'function') {
                    ensureProfileProgressionMonacoContentListener();
                }
                if (typeof ensureProfileBlackMarketMonacoListener === 'function') {
                    ensureProfileBlackMarketMonacoListener();
                }
                if (typeof ensureProfilePcSharedMonacoContentListener === 'function') {
                    ensureProfilePcSharedMonacoContentListener();
                }
                setTimeout(function () {
                    if (typeof refreshProgressionSharedPanel === 'function') {
                        refreshProgressionSharedPanel();
                    }
                    if (typeof refreshBlackMarketItemsPanel === 'function') {
                        refreshBlackMarketItemsPanel();
                    }
                    if (typeof refreshProfilePcSharedFoddatasPanel === 'function') {
                        refreshProfilePcSharedFoddatasPanel();
                    }
                }, 0);
                
                yamlContent.style.display = 'block';
                window.profileYAMLContent = yamlText;
                
                // Decode bank and cosmetics
                setTimeout(() => {
                    decodeProfileBankAndCosmetics(yamlText);
                    // Update bank buttons after profile is loaded
                    if (typeof updateBankButtons === 'function') {
                        updateBankButtons();
                    }
                }, 100);
                
                const successMessage = isYamlFile 
                    ? '✅ YAML file loaded successfully!'
                    : '✅ Profile file decrypted successfully!';
                showSaveStatus('profile-decrypt-status', successMessage, true);
                
            } catch (error) {
                console.error('Profile decrypt error:', error);
                
                if (error.message && error.message.includes('Zlib decompression failed')) {
                    const friendlyMessage = 'Please Check Steam or Epic ID and verify that this profile.sav or .yaml is valid.';
                    showSaveStatus('profile-decrypt-status', `❌ Error: ${friendlyMessage}`, false);
                } else {
                    showSaveStatus('profile-decrypt-status', `❌ Error: ${error.message}`, false);
                }
            }
        }

        async function encryptProfileFile() {
            const steamIdInput = document.getElementById('profile-steamid');
            const statusEl = document.getElementById('profile-encrypt-status');
            
            const steamId = steamIdInput.value.trim();
            if (!steamId) {
                showSaveStatus('profile-encrypt-status', '❌ Please enter your Steam ID or Epic ID first.', false);
                return;
            }
            
            let yamlContent = getProfileYamlEditorValue().trim();
            
            if (!yamlContent) {
                showSaveStatus('profile-encrypt-status', '❌ No YAML content to encrypt.', false);
                return;
            }
            
            try {
                showSaveStatus('profile-encrypt-status', '⏳ Encrypting profile file...', true);
                
                const requestBody = {
                    command: 'encrypt',
                    steamid: steamId,
                    yaml_content: yamlContent,
                    yaml_data: yamlContent
                };
                
                const response = await fetch(getSaveApiBaseUrl(), {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(requestBody)
                });
                
                if (!response.ok) {
                    const errorText = await response.text();
                    throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
                }
                
                const contentType = response.headers.get('content-type');
                let data;
                
                if (contentType && contentType.includes('application/json')) {
                    data = await response.json();
                } else {
                    const text = await response.text();
                    try {
                        data = JSON.parse(text);
                    } catch (e) {
                        throw new Error(`Invalid response format. Expected JSON but got: ${contentType || 'unknown'}. Response: ${text.substring(0, 200)}`);
                    }
                }
                
                const encryptedData = data.encrypted || data.encrypted_data || data.sav_data || data.data;
                
                if (data.success && encryptedData) {
                    const binaryString = atob(encryptedData);
                    const bytes = new Uint8Array(binaryString.length);
                    for (let i = 0; i < binaryString.length; i++) {
                        bytes[i] = binaryString.charCodeAt(i);
                    }
                    const blob = new Blob([bytes], { type: 'application/octet-stream' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'profile_encrypted.sav';
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                    
                    showSaveStatus('profile-encrypt-status', '✅ Profile file encrypted and downloaded as "profile_encrypted.sav"!', true);
                } else {
                    const errorMsg = data.error || data.message || data.reason || 'Failed to encrypt profile file';
                    throw new Error(errorMsg);
                }
            } catch (error) {
                console.error('Profile encrypt error:', error);
                showSaveStatus('profile-encrypt-status', `❌ Error: ${error.message}`, false);
            }
        }

        function copyProfileYamlToClipboard() {
            let yamlContent = getProfileYamlEditorValue();
            
            if (!yamlContent) {
                alert('No YAML content to copy.');
                return;
            }
            
            navigator.clipboard.writeText(yamlContent).then(() => {
                showSaveStatus('profile-encrypt-status', '✅ YAML copied to clipboard!', true);
                // Track clipboard copy
                if (typeof window.trackEvent === 'function') {
                    window.trackEvent('copy_clipboard', { source: 'button' });
                }
            }).catch(err => {
                console.error('Failed to copy:', err);
                showSaveStatus('profile-encrypt-status', '❌ Failed to copy to clipboard.', false);
            });
        }

        function downloadProfileYamlFile() {
            let yamlContent = getProfileYamlEditorValue();
            
            if (!yamlContent) {
                alert('No YAML content to download.');
                return;
            }
            
            const blob = new Blob([yamlContent], { type: 'text/yaml' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'profile.yaml';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }

        function applyProfilePreset(presetType) {
            if (!window.profileMonacoEditor) {
                showSaveStatus('profile-preset-status', '❌ Please decrypt a profile file first.', false);
                return;
            }
            
            try {
                const yamlContent = getProfileYamlEditorValue();
                // Clean YAML before parsing
                let cleanedYaml = yamlContent.replace(/:\s*!tags/g, ':');
                cleanedYaml = cleanedYaml.replace(/:\s*!<[^>]+>/g, ':');
                
                let data;
                try {
                    data = jsyaml.load(cleanedYaml);
                } catch (parseError) {
                    // Try with more aggressive cleaning
                    cleanedYaml = cleanedYaml.replace(/!<[^>]+>/g, '');
                    data = jsyaml.load(cleanedYaml);
                }
                
                if (!data || typeof data === 'string') {
                    showSaveStatus('profile-preset-status', '⚠️ This preset requires YAML parsing. Please ensure js-yaml is loaded.', false);
                    return;
                }
                
                // Check if this is a profile save (not character)
                if (data.domains && data.domains.local && data.domains.local.shared) {
                    // This is a profile save
                    if (presetType === 'unlockAllCosmetics') {
                        const nexusCosmetics = getNexusCosmeticsList();
                        if (nexusCosmetics.length === 0) {
                            showSaveStatus(
                                'profile-preset-status',
                                '⚠️ No cosmetics catalog loaded. Open the Legit Builder tab so Nexus Resident JSON loads, or load those files manually.',
                                false
                            );
                            return;
                        }
                        nexusCosmetics.forEach(cosmeticKey => {
                            addCosmeticToUnlockables(data, cosmeticKey);
                        });
                        
                        const newYaml = jsyaml.dump(data, { lineWidth: -1, noRefs: true });
                        window.profileMonacoEditor.setValue(newYaml);
                        
                        // Refresh cosmetics display
                        const result = getAllCosmeticsFromUnlockables(data);
                        renderCosmetics(result.cosmetics, result.cosmeticsBySource);
                        
                        showSaveStatus('profile-preset-status', `✅ All ${nexusCosmetics.length} cosmetics unlocked!`, true);
                        return; // Early return since we already updated YAML
                    }
                    
                    const newYaml = jsyaml.dump(data, { lineWidth: -1, noRefs: true });
                    window.profileMonacoEditor.setValue(newYaml);
                } else {
                    showSaveStatus('profile-preset-status', '⚠️ This does not appear to be a profile save file.', false);
                }
            } catch (error) {
                console.error('Profile preset error:', error);
                showSaveStatus('profile-preset-status', `❌ Error: ${error.message}`, false);
            }
        }

        // Bank Editor Functions
        function clearProfileBankCosmeticsUi() {
            const bankContainer = document.getElementById('bank-items-container');
            const bankCountEl = document.getElementById('bank-items-count');
            const cosmeticsContainer = document.getElementById('cosmetics-items-container');
            const cosmeticsCountEl = document.getElementById('cosmetics-items-count');

            if (bankContainer) bankContainer.innerHTML = '';
            if (bankCountEl) bankCountEl.textContent = '(0 items)';
            if (cosmeticsContainer) cosmeticsContainer.innerHTML = '';
            if (cosmeticsCountEl) cosmeticsCountEl.textContent = '(0 unlocked)';

            const bankStatus = document.getElementById('bank-items-status');
            const cosmeticsStatus = document.getElementById('cosmetics-items-status');
            const currenciesStatus = document.getElementById('currencies-items-status');
            if (bankStatus) {
                bankStatus.style.display = 'none';
                bankStatus.textContent = '';
            }
            if (cosmeticsStatus) {
                cosmeticsStatus.style.display = 'none';
                cosmeticsStatus.textContent = '';
            }
            if (currenciesStatus) {
                currenciesStatus.style.display = 'none';
                currenciesStatus.textContent = '';
            }

            const spContainer = document.getElementById('shared-progress-items-container');
            const spCountEl = document.getElementById('shared-progress-items-count');
            if (spContainer) spContainer.innerHTML = '';
            if (spCountEl) spCountEl.textContent = '(0 unlocked)';
            const spStatus = document.getElementById('shared-progress-items-status');
            if (spStatus) {
                spStatus.style.display = 'none';
                spStatus.textContent = '';
            }
            const spSelect = document.getElementById('shared-progress-select');
            if (spSelect) {
                spSelect.innerHTML = '<option value="">Select an entry...</option>';
            }
            const spManual = document.getElementById('shared-progress-manual-input');
            if (spManual) spManual.value = '';

            const tokensInput = document.getElementById('vaultcard-tokens-input');
            const levelInput = document.getElementById('vaultcard-level-input');
            const pointsInput = document.getElementById('vaultcard-points-input');
            if (tokensInput) tokensInput.value = '';
            if (levelInput) levelInput.value = '';
            if (pointsInput) pointsInput.value = '';
            const tokens02Input = document.getElementById('vaultcard02-tokens-input');
            const level02Input = document.getElementById('vaultcard02-level-input');
            const points02Input = document.getElementById('vaultcard02-points-input');
            if (tokens02Input) tokens02Input.value = '';
            if (level02Input) level02Input.value = '';
            if (points02Input) points02Input.value = '';
            const tokens03Input = document.getElementById('vaultcard03-tokens-input');
            const level03Input = document.getElementById('vaultcard03-level-input');
            const points03Input = document.getElementById('vaultcard03-points-input');
            if (tokens03Input) tokens03Input.value = '';
            if (level03Input) level03Input.value = '';
            if (points03Input) points03Input.value = '';

            const bmHost = document.getElementById('profile-blackmarket-slots-host');
            if (bmHost) bmHost.innerHTML = '';
            const bmStatus = document.getElementById('profile-blackmarket-status');
            if (bmStatus) {
                bmStatus.style.display = 'none';
                bmStatus.textContent = '';
            }
        }

        function showProfileSectionLoadOverlays() {
            const html =
                '<div style="color: #fff; font-weight: 500; font-size: 0.9em;">Load a profile file first</div>';
            [
                'sharedProgressOverlay',
                'sharedDiscoveryOverlay',
                'pcSharedOverlay',
                'progressionSharedOverlay',
                'blackMarketOverlay'
            ].forEach(
                id => {
                    const el = document.getElementById(id);
                    if (el) {
                        el.innerHTML = html;
                        el.style.display = 'flex';
                    }
                }
            );
        }

        function hideProfileSectionLoadOverlays() {
            [
                'sharedProgressOverlay',
                'sharedDiscoveryOverlay',
                'pcSharedOverlay',
                'progressionSharedOverlay',
                'blackMarketOverlay'
            ].forEach(id => {
                const el = document.getElementById(id);
                if (el) el.style.display = 'none';
            });
        }

        function setProfileSectionErrorOverlays(message) {
            const html =
                '<div style="color: #ff6b6b; font-weight: 500; font-size: 0.9em; padding: 20px; text-align: center;">' +
                message +
                '</div>';
            [
                'sharedProgressOverlay',
                'sharedDiscoveryOverlay',
                'pcSharedOverlay',
                'progressionSharedOverlay',
                'blackMarketOverlay'
            ].forEach(
                id => {
                    const el = document.getElementById(id);
                    if (el) {
                        el.innerHTML = html;
                        el.style.display = 'flex';
                    }
                }
            );
        }

        window.clearProfileEditorWorkspace = function clearProfileEditorWorkspace() {
            setProfileYamlEditorValue('');
            const yamlContent = document.getElementById('profile-yaml-content');
            if (yamlContent) yamlContent.style.display = 'none';
            const profileFileInput = document.getElementById('profile-file-input');
            if (profileFileInput) profileFileInput.value = '';
            const profileFileSelected = document.getElementById('profile-file-selected-name');
            const profileFileNameText = document.getElementById('profile-file-name-text');
            if (profileFileSelected) profileFileSelected.style.display = 'none';
            if (profileFileNameText) profileFileNameText.textContent = '';
            window.profileYAMLContent = '';
            clearProfileBankCosmeticsUi();
            showProfileSectionLoadOverlays();
            const profileDecryptStatus = document.getElementById('profile-decrypt-status');
            if (profileDecryptStatus) {
                profileDecryptStatus.innerHTML = '';
                profileDecryptStatus.style.display = 'none';
            }
        };

        async function decodeProfileBankAndCosmetics(yamlText) {
            if (!yamlText) {
                yamlText = getProfileYamlEditorValue();
                if (!yamlText) return;
            }

            clearProfileBankCosmeticsUi();

            try {
                // Remove !tags which jsyaml can't handle. These don't seem to be needed.
                let cleanedYaml = yamlText.replace(/:\s*!tags/g, ':');
                // Also handle other unknown tags by removing them
                cleanedYaml = cleanedYaml.replace(/:\s*!<[^>]+>/g, ':');
                
                let data;
                try {
                    data = jsyaml.load(cleanedYaml);
                } catch (parseError) {
                    console.error('YAML parse error:', parseError);
                    // Try with more aggressive cleaning
                    cleanedYaml = cleanedYaml.replace(/!<[^>]+>/g, '');
                    try {
                        data = jsyaml.load(cleanedYaml);
                    } catch (e2) {
                        console.error('YAML parse error after cleaning:', e2);
                        return;
                    }
                }
                
                if (!data || typeof data === 'string') return;
                
                // Check if this is a profile save (not a character save)
                // Profile saves have domains.local.shared, character saves have domains.local.characters
                const isProfileSave = data.domains && data.domains.local && data.domains.local.shared;
                const isCharacterSave = data.domains && data.domains.local && data.domains.local.characters;
                
                if (isCharacterSave && !isProfileSave) {
                    // This is a character save, not a profile save
                    const errorMsg = '❌ This is a player save file (character save), not a profile save file. Please load a profile.sav file instead.';
                    showSaveStatus('profile-decrypt-status', errorMsg, false);
                    
                    // Show error in bank and cosmetics sections
                    const bankOverlay = document.getElementById('bankOverlay');
                    if (bankOverlay) {
                        bankOverlay.innerHTML = '<div style="color: #ff6b6b; font-weight: 500; font-size: 0.9em; padding: 20px; text-align: center;">❌ This is a player save file, not a profile save file.<br>Please load a profile.sav file instead.</div>';
                        bankOverlay.style.display = 'block';
                    }
                    
                    const cosmeticsOverlay = document.getElementById('cosmeticsOverlay');
                    if (cosmeticsOverlay) {
                        cosmeticsOverlay.innerHTML = '<div style="color: #ff6b6b; font-weight: 500; font-size: 0.9em; padding: 20px; text-align: center;">❌ This is a player save file, not a profile save file.<br>Please load a profile.sav file instead.</div>';
                        cosmeticsOverlay.style.display = 'block';
                    }

                    setProfileSectionErrorOverlays(
                        '❌ This is a player save file, not a profile save file.<br>Please load a profile.sav file instead.'
                    );
                    
                    const currenciesOverlay = document.getElementById('currenciesOverlay');
                    if (currenciesOverlay) {
                        currenciesOverlay.innerHTML = '<div style="color: #ff6b6b; font-weight: 500; font-size: 0.9em; padding: 20px; text-align: center;">❌ This is a player save file, not a profile save file.<br>Please load a profile.sav file instead.</div>';
                        currenciesOverlay.style.display = 'block';
                    }
                    
                    return;
                }
                
                if (!isProfileSave) {
                    // Unknown file type - not a profile save
                    const errorMsg = '❌ Please load a profile.sav file.';
                    showSaveStatus('profile-decrypt-status', errorMsg, false);
                    
                    // Show error in bank and cosmetics sections
                    const bankOverlay = document.getElementById('bankOverlay');
                    if (bankOverlay) {
                        bankOverlay.innerHTML = '<div style="color: #ff6b6b; font-weight: 500; font-size: 0.9em; padding: 20px; text-align: center;">❌ Please load a profile.sav file.</div>';
                        bankOverlay.style.display = 'block';
                    }
                    
                    const cosmeticsOverlay = document.getElementById('cosmeticsOverlay');
                    if (cosmeticsOverlay) {
                        cosmeticsOverlay.innerHTML = '<div style="color: #ff6b6b; font-weight: 500; font-size: 0.9em; padding: 20px; text-align: center;">❌ Please load a profile.sav file.</div>';
                        cosmeticsOverlay.style.display = 'block';
                    }

                    setProfileSectionErrorOverlays('❌ Please load a profile.sav file.');
                    
                    const currenciesOverlay = document.getElementById('currenciesOverlay');
                    if (currenciesOverlay) {
                        currenciesOverlay.innerHTML = '<div style="color: #ff6b6b; font-weight: 500; font-size: 0.9em; padding: 20px; text-align: center;">❌ Please load a profile.sav file.</div>';
                        currenciesOverlay.style.display = 'block';
                    }
                    
                    return;
                }
                
                // Decode bank items
                if (data.domains.local.shared.inventory && data.domains.local.shared.inventory.items && data.domains.local.shared.inventory.items.bank) {
                    const bank = data.domains.local.shared.inventory.items.bank;
                    renderBankItems(bank);
                    
                    // Hide bank overlay
                    const bankOverlay = document.getElementById('bankOverlay');
                    if (bankOverlay) bankOverlay.style.display = 'none';
                } else {
                    // No bank found - show message in container and reset count, but keep section accessible
                    const bankCountEl = document.getElementById('bank-items-count');
                    if (bankCountEl) {
                        bankCountEl.textContent = '(0 items)';
                    }
                    
                    // Hide overlay so section remains accessible
                    const bankOverlay = document.getElementById('bankOverlay');
                    if (bankOverlay) {
                        bankOverlay.style.display = 'none';
                    }
                    
                    // Show message in container instead
                    const bankContainer = document.getElementById('bank-items-container');
                    if (bankContainer) {
                        bankContainer.innerHTML = '<div style="color: rgba(129, 212, 250, 0.6); font-weight: 500; font-size: 0.9em; padding: 20px; text-align: center; border: 1px dashed rgba(129, 212, 250, 0.3); border-radius: 4px;">No bank items found in this profile. Use "Add to Bank" below to add items.</div>';
                    }
                }
                
                // Decode cosmetics - check both cosmetics object and unlockables structure
                if (data.domains && data.domains.local) {
                    const result = getAllCosmeticsFromUnlockables(data);
                    const cosmetics = result.cosmetics;
                    window.cosmeticsBySource = result.cosmeticsBySource;
                    
                    console.log('Loaded cosmetics:', Object.keys(cosmetics).length, 'items');
                    console.log('Cosmetics by source:', result.cosmeticsBySource);
                    
                    // Always render cosmetics (even if empty) and hide overlay when profile is loaded
                    renderCosmetics(cosmetics, result.cosmeticsBySource);
                    
                    // Hide cosmetics overlay
                    const cosmeticsOverlay = document.getElementById('cosmeticsOverlay');
                    if (cosmeticsOverlay) cosmeticsOverlay.style.display = 'none';
                }

                if (data.domains && data.domains.local) {
                    const spResult = getAllAccountChallengeUnlocksFromUnlockables(data);
                    renderSharedProgress(spResult.sharedProgress, spResult.bySection);
                    hideProfileSectionLoadOverlays();
                }

                if (typeof refreshSharedDiscoveryDlmdCountDisplay === 'function') {
                    refreshSharedDiscoveryDlmdCountDisplay();
                }

                if (typeof refreshProgressionSharedPanel === 'function') {
                    setTimeout(function () {
                        refreshProgressionSharedPanel();
                    }, 0);
                    setTimeout(function () {
                        refreshProgressionSharedPanel();
                    }, 400);
                }

                if (typeof refreshBlackMarketItemsPanel === 'function') {
                    setTimeout(function () {
                        refreshBlackMarketItemsPanel();
                    }, 0);
                    setTimeout(function () {
                        refreshBlackMarketItemsPanel();
                    }, 400);
                }

                const bmOv = document.getElementById('blackMarketOverlay');
                if (bmOv) bmOv.style.display = 'none';
                
                // Decode currencies
                renderCurrencies(data);
                
                // Hide currencies overlay
                const currenciesOverlay = document.getElementById('currenciesOverlay');
                if (currenciesOverlay) currenciesOverlay.style.display = 'none';
            } catch (error) {
                console.error('Error decoding profile bank and cosmetics:', error);
                // Don't show error to user - just log it, as this is called automatically
            }
        }

        async function renderBankItems(bank) {
            const container = document.getElementById('bank-items-container');
            const countEl = document.getElementById('bank-items-count');
            if (!container) return;

            const escapeHtml = (value) => {
                if (value === null || value === undefined) return '';
                const str = String(value);
                const div = document.createElement('div');
                div.textContent = str;
                return div.innerHTML;
            };

            let bankItems = Object.entries(bank || {}).filter(([, slotData]) => slotData && slotData.serial);
            bankItems.sort(([a], [b]) => {
                const ma = String(a).match(/^slot_(\d+)$/);
                const mb = String(b).match(/^slot_(\d+)$/);
                if (ma && mb) return parseInt(ma[1], 10) - parseInt(mb[1], 10);
                return String(a).localeCompare(String(b));
            });

            if (countEl) {
                countEl.textContent = `(${bankItems.length} items)`;
            }

            const stateFlagsOptions = [
                { value: '', label: '⚫ Unseen' },
                { value: '1', label: '👁️ Seen' },
                { value: '3', label: '⭐ Marked for Favorite' },
                { value: '5', label: '🗑️ Marked for Trash' },
                { value: '9', label: '🐷 Bank' },
                { value: '17', label: '🟠🏷️ Tag Group 1', color: '#ff9800' },
                { value: '33', label: '🔵🏷️ Tag Group 2', color: '#2196f3' },
                { value: '65', label: '🟣🏷️ Tag Group 3', color: '#9c27b0' },
                { value: '129', label: '🟢🏷️ Tag Group 4', color: '#4caf50' }
            ];

            const H = window.__saveEditorBankUiHelpers;
            const decodedRows = [];

            if (bankItems.length > 0 && typeof deserializeSerialHelper === 'function') {
                const results = await Promise.all(
                    bankItems.map(async ([slotKey, slotData]) => {
                        const raw = String(slotData.serial || '').trim();
                        if (!raw) {
                            return { slotKey, slotData, decoded: '', normSerial: '' };
                        }
                        try {
                            const result = await deserializeSerialHelper(raw);
                            const dec =
                                result && result.success && result.deserialized
                                    ? String(result.deserialized).trim()
                                    : '';
                            const norm = raw.startsWith('@') ? raw : '@' + raw;
                            return { slotKey, slotData, decoded: dec, normSerial: norm };
                        } catch (e) {
                            const norm = raw.startsWith('@') ? raw : '@' + raw;
                            return { slotKey, slotData, decoded: '', normSerial: norm };
                        }
                    })
                );
                results.forEach((r) => decodedRows.push(r));
            } else {
                bankItems.forEach(([slotKey, slotData]) => {
                    const raw = String(slotData.serial || '').trim();
                    const norm = raw.startsWith('@') ? raw : '@' + raw;
                    decodedRows.push({ slotKey, slotData, decoded: '', normSerial: norm });
                });
            }

            const finalDecodedList = decodedRows
                .filter((r) => r.normSerial)
                .map((r) => ({ serial: r.normSerial, deserialized: r.decoded }));

            if (
                H &&
                typeof H.warmValidatorForList === 'function' &&
                finalDecodedList.length > 0
            ) {
                await H.warmValidatorForList(finalDecodedList, { mergeIntoExisting: true });
            }

            if (!window.decodedItemsData) window.decodedItemsData = {};
            decodedRows.forEach((r) => {
                if (!r.normSerial) return;
                const rawSer = String(r.slotData.serial || '').trim();
                window.decodedItemsData[rawSer] = {
                    serial: rawSer,
                    deserialized: r.decoded
                };
                window.decodedItemsData[r.normSerial] = {
                    serial: rawSer,
                    deserialized: r.decoded
                };
            });

            let html = '<div id="bank-slots-inner" class="backpack-slots-stack">';
            decodedRows.forEach((r) => {
                const { slotKey, slotData, decoded: decodedSerial } = r;
                const serial = String(slotData.serial || '').trim();
                const serialKeyForValidation =
                    !serial || !String(serial).trim()
                        ? ''
                        : String(serial).trim().startsWith('@')
                          ? String(serial).trim()
                          : '@' + String(serial).trim();

                const stateFlags =
                    slotData.state_flags !== null && slotData.state_flags !== undefined
                        ? slotData.state_flags
                        : 1;
                const stateFlagsStr = String(stateFlags);
                const opts = [...stateFlagsOptions];
                const knownValues = stateFlagsOptions.map((opt) => opt.value);
                if (stateFlagsStr !== '' && !knownValues.includes(stateFlagsStr)) {
                    opts.push({
                        value: stateFlagsStr,
                        label: `Unknown state flag: ${stateFlagsStr}`
                    });
                }

                const encodedDecodedMin = btoa(
                    unescape(encodeURIComponent(decodedSerial || ''))
                );
                const validatorStatusMin =
                    typeof window.getValidatorValidStatus === 'function'
                        ? window.getValidatorValidStatus(decodedSerial)
                        : 'Invalid';
                const showReorderMin = validatorStatusMin === 'Reorder to make legit';
                const bankFilterSearch =
                    typeof window.buildSaveInventoryFilterSearchText === 'function'
                        ? window.buildSaveInventoryFilterSearchText(
                              serialKeyForValidation || serial,
                              decodedSerial || '',
                              {}
                          )
                        : `${(serial || '').toLowerCase()}`;
                const shellStyle =
                    H && typeof H.getMinimalCardShellStyle === 'function'
                        ? H.getMinimalCardShellStyle(serialKeyForValidation)
                        : 'box-sizing:border-box;border:1px solid rgba(255,255,255,0.14);border-radius:8px;padding:8px 10px;margin-bottom:8px;background:rgba(255,255,255,0.04);';
                const mfgChip =
                    H && typeof H.buildMfgTypeChip === 'function'
                        ? H.buildMfgTypeChip(serialKeyForValidation, decodedSerial, escapeHtml)
                        : '';
                const uniqueChip =
                    H && typeof H.buildHeaderUniqueChip === 'function'
                        ? H.buildHeaderUniqueChip(serialKeyForValidation, escapeHtml)
                        : '';
                const validityRow =
                    H && typeof H.buildValidityRow === 'function'
                        ? H.buildValidityRow(serialKeyForValidation, escapeHtml, {
                              ...H.validityMinimalOpts,
                              decodedSerial: decodedSerial || '',
                          })
                        : '';

                html += `<div class="backpack-slot-item backpack-slot-shell backpack-slot--minimal-ui backpack-slot--compact bank-slot-row" data-slot="${escapeHtml(slotKey)}" data-bank-slot="${escapeHtml(slotKey)}" data-inv-base85-serial="${escapeHtml(serialKeyForValidation || serial)}" data-search-text="${escapeHtml(bankFilterSearch)}" style="${escapeHtml(shellStyle)}">`;
                html += `<div class="backpack-slot-header-minimal" style="display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin-bottom:4px;width:100%;">`;
                html += `<span style="color:#81d4fa;font-weight:600;font-size:0.88em;">${escapeHtml(slotKey)}</span>${mfgChip}${uniqueChip}`;
                html += `<span style="flex:1;min-width:6px;"></span>`;
                html += `<button type="button" class="btn btn-secondary save-inv-open-legit-builder-btn" data-encoded-decoded="${encodedDecodedMin}" style="padding:2px 8px;font-size:0.68em;white-space:nowrap;" title="Edit in Legit Builder (strict push when valid; otherwise opens validator)" onclick="openSaveInventoryInLegitBuilder(this)">Edit in Legit Builder</button>`;
                html += `<button type="button" class="btn btn-secondary save-inv-open-modded-btn" data-encoded-decoded="${encodedDecodedMin}" style="padding:2px 8px;font-size:0.68em;white-space:nowrap;" title="Edit in Modded builder" onclick="openSaveInventoryInModdedBuilder(this)">Edit in Modded builder</button>`;
                if (showReorderMin) {
                    html += `<button type="button" class="btn btn-secondary save-inv-reorder-btn" data-context="bank" data-encoded-decoded="${encodedDecodedMin}" style="padding:2px 8px;font-size:0.68em;white-space:nowrap;" title="Apply canonical part order and update this slot in the profile bank" onclick="applyLegitReorderFromSaveInventory(this)">Reorder here</button>`;
                }
                html += `<button type="button" class="btn btn-secondary backpack-slot-toggle-expand" aria-expanded="false" style="padding:2px 8px;font-size:0.68em;">▼ Details</button>`;
                html += `<button type="button" class="btn btn-secondary remove-bank-slot-btn" data-bank-slot="${escapeHtml(slotKey)}" style="padding:2px 8px;font-size:0.68em;">Remove</button>`;
                html += `</div>`;
                html +=
                    typeof window.buildBackpackCompactSummaryHtml === 'function'
                        ? window.buildBackpackCompactSummaryHtml(decodedSerial, escapeHtml)
                        : '';
                html += validityRow;
                html += `<div class="backpack-slot-body">`;
                html += `<div class="backpack-slot-row backpack-slot-serial-row">`;
                html += `<label class="backpack-slot-field-label">Serial</label>`;
                html += `<input type="text" class="backpack-slot-serial backpack-slot-input-serial" data-slot="${escapeHtml(slotKey)}" value="${escapeHtml(serial)}" placeholder="Base85 serial">`;
                html += `<button type="button" class="btn btn-secondary" onclick="copyToClipboardHelper(this.previousElementSibling.value, 'serial')" style="padding: 6px 10px; font-size: 0.85em;">📋</button>`;
                html += `</div>`;
                html +=
                    typeof window.formatSaveEditorDecodedReadonlyHtmlLazy === 'function'
                        ? window.formatSaveEditorDecodedReadonlyHtmlLazy()
                        : '';
                html += `<input type="text" class="backpack-slot-decoded backpack-slot-input-decoded" data-slot="${escapeHtml(slotKey)}" value="${escapeHtml(decodedSerial)}" readonly placeholder="Decoded (after bulk validate)" style="display:none" aria-hidden="true">`;
                html += `<div class="backpack-slot-row"><label class="backpack-slot-field-label">State Flags</label>`;
                html += `<select class="backpack-slot-state-flags backpack-slot-state-select" data-slot="${escapeHtml(slotKey)}" data-serial="${escapeHtml(serial)}">`;
                opts.forEach((option) => {
                    const selected = stateFlagsStr === option.value ? 'selected' : '';
                    const colorStyle = option.color ? `style="color: ${option.color};"` : '';
                    html += `<option value="${escapeHtml(String(option.value))}" ${selected} ${colorStyle}>${option.label}</option>`;
                });
                html += `</select></div>`;
                html += `</div></div>`;
            });
            html += '</div>';
            container.innerHTML = html;

            if (typeof window.applyAllSaveInventorySearchFilters === 'function') {
                window.applyAllSaveInventorySearchFilters();
            }

            setupBankSlotInteractivity();
            container.querySelectorAll('.remove-bank-slot-btn').forEach((btn) => {
                btn.addEventListener('click', function () {
                    const sk = this.dataset.bankSlot;
                    if (sk && typeof removeBankSlot === 'function') {
                        removeBankSlot(sk);
                    }
                });
            });
        }

        window.refreshProfileBankItemsPanel = async function refreshProfileBankItemsPanel() {
            if (!window.profileMonacoEditor || typeof jsyaml === 'undefined') return;
            try {
                let yamlContent = window.profileMonacoEditor.getValue();
                let cleanedYaml = yamlContent.replace(/:\s*!tags/g, ':');
                cleanedYaml = cleanedYaml.replace(/:\s*!<[^>]+>/g, ':');
                let data;
                try {
                    data = jsyaml.load(cleanedYaml);
                } catch (parseError) {
                    cleanedYaml = cleanedYaml.replace(/!<[^>]+>/g, '');
                    data = jsyaml.load(cleanedYaml);
                }
                const bank =
                    data &&
                    data.domains &&
                    data.domains.local &&
                    data.domains.local.shared &&
                    data.domains.local.shared.inventory &&
                    data.domains.local.shared.inventory.items &&
                    data.domains.local.shared.inventory.items.bank;
                if (bank) {
                    await renderBankItems(bank);
                }
            } catch (e) {
                console.warn('refreshProfileBankItemsPanel:', e);
            }
        };

        function setupBankSlotInteractivity() {
            const container = document.getElementById('bank-items-container');
            if (!container) return;
            
            // Bank filter: delegated from item-editor-10-yaml-save.js (applyInventorySearchFilter)

            // Listen for changes to serial, decoded serial, and state flags
            container.querySelectorAll('.backpack-slot-serial, .backpack-slot-decoded, .backpack-slot-state-flags').forEach(el => {
                el.addEventListener('change', () => {
                    updateBankSlotsData();
                });
                el.addEventListener('input', () => {
                    // For decoded serial, auto-reserialize on input
                    if (el.classList.contains('backpack-slot-decoded')) {
                        const slotKey = el.dataset.slot;
                        const decodedValue = el.value.trim();
                        if (decodedValue && typeof ItemDecoder !== 'undefined' && ItemDecoder.encodeItemSerial) {
                            try {
                                // Parse decoded serial and re-encode
                                const parts = decodedValue.match(/\{(\d+):(\d+)\}/g) || [];
                                if (parts.length > 0) {
                                    // This is a simplified version - full encoding would need full ItemDecoder logic
                                    // For now, just update the YAML when user changes decoded serial
                                    setTimeout(() => updateBankSlotsData(), 500);
                                }
                            } catch (e) {
                                console.warn('Could not reserialize decoded bank serial:', e);
                            }
                        }
                    }
                });
            });
        }

        function updateBankSlotsData() {
            if (!window.profileMonacoEditor) return;
            
            try {
                const yamlContent = window.profileMonacoEditor.getValue();
                // Clean YAML before parsing
                let cleanedYaml = yamlContent.replace(/:\s*!tags/g, ':');
                cleanedYaml = cleanedYaml.replace(/:\s*!<[^>]+>/g, ':');
                
                let data;
                try {
                    data = jsyaml.load(cleanedYaml);
                } catch (parseError) {
                    cleanedYaml = cleanedYaml.replace(/!<[^>]+>/g, '');
                    data = jsyaml.load(cleanedYaml);
                }
                
                if (!data || typeof data === 'string' || !data.domains || !data.domains.local || !data.domains.local.shared || !data.domains.local.shared.inventory || !data.domains.local.shared.inventory.items) {
                    return;
                }
                
                if (!data.domains.local.shared.inventory.items.bank) {
                    data.domains.local.shared.inventory.items.bank = {};
                }
                
                const bank = data.domains.local.shared.inventory.items.bank;
                const container = document.getElementById('bank-items-container');
                
                if (container) {
                    container.querySelectorAll('.backpack-slot-item').forEach(slotDiv => {
                        const slotKey = slotDiv.querySelector('.backpack-slot-serial')?.dataset.slot;
                        if (!slotKey) return;
                        
                        const serialInput = slotDiv.querySelector('.backpack-slot-serial');
                        const decodedInput = slotDiv.querySelector('.backpack-slot-decoded');
                        const stateFlagsSelect = slotDiv.querySelector('.backpack-slot-state-flags');
                        
                        const serial = serialInput?.value?.trim() || '';
                        const decodedSerial = decodedInput?.value?.trim() || '';
                        const stateFlags = stateFlagsSelect ? parseInt(stateFlagsSelect.value || '1', 10) : 1;
                        
                        // If decoded serial was changed, try to encode it
                        let finalSerial = serial;
                        if (decodedSerial && decodedSerial !== serial && typeof ItemDecoder !== 'undefined' && ItemDecoder.encodeItemSerial) {
                            try {
                                // Try to encode the decoded serial
                                // This is simplified - full implementation would parse the decoded serial properly
                                // For now, if user edits decoded serial, we'll try to encode it
                                if (decodedSerial.includes('{') && decodedSerial.includes('}')) {
                                    // User edited decoded serial - try to encode it
                                    // Note: This requires full ItemDecoder implementation
                                    // For now, we'll keep the original serial unless user explicitly changes it
                                }
                            } catch (e) {
                                console.warn('Could not encode decoded bank serial:', e);
                            }
                        }
                        
                        if (finalSerial) {
                            bank[slotKey] = { serial: finalSerial, state_flags: stateFlags };
                        } else {
                            delete bank[slotKey];
                        }
                    });
                }
                
                const newYaml = jsyaml.dump(data, { lineWidth: -1, noRefs: true });
                window.profileMonacoEditor.setValue(newYaml);
            } catch (error) {
                console.error('Error updating bank slots:', error);
            }
        }

        async function addSerialToBank() {
            const input = document.getElementById('add-to-bank-serial-input');
            if (!input || !input.value.trim()) {
                showSaveStatus('bank-items-status', '❌ Please enter a serial.', false);
                return;
            }
            
            if (!window.profileMonacoEditor) {
                showSaveStatus('bank-items-status', '❌ Please decrypt a profile file first.', false);
                return;
            }
            
            try {
                let serial = input.value.trim();
                
                // Check if input is deserialized format (contains commas and |, or starts with numbers)
                // Deserialized format: "274, 0, 1, 50| 2, 1422|| {22} {#}|"
                // Serialized format: "@Uge8Cmm/)}}!g!pZI;cvuFsPLV^*i;..."
                const isDeserialized = (serial.includes(',') && serial.includes('|')) || 
                                      (!serial.startsWith('@') && /^\d/.test(serial.trim()));
                
                // If deserialized, serialize it first
                if (isDeserialized) {
                    showSaveStatus('bank-items-status', '⏳ Serializing item code...', true);
                    
                    try {
                        const response = await fetch('https://save-editor.be/nicnl/api.php', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                deserialized: serial
                            })
                        });
                        
                        if (!response.ok) {
                            throw new Error(`HTTP error! status: ${response.status}`);
                        }
                        
                        const data = await response.json();
                        
                        if (data.error) {
                            throw new Error(data.error);
                        }
                        
                        if (data.serial_b85 && typeof data.serial_b85 === 'string') {
                            serial = data.serial_b85;
                        } else {
                            throw new Error('No serial_b85 in response');
                        }
                    } catch (serializeError) {
                        console.error('Error serializing code:', serializeError);
                        showSaveStatus('bank-items-status', `❌ Error serializing code: ${serializeError.message}`, false);
                        return;
                    }
                }
                
                const yamlContent = window.profileMonacoEditor.getValue();
                // Clean YAML before parsing
                let cleanedYaml = yamlContent.replace(/:\s*!tags/g, ':');
                cleanedYaml = cleanedYaml.replace(/:\s*!<[^>]+>/g, ':');
                
                let data;
                try {
                    data = jsyaml.load(cleanedYaml);
                } catch (parseError) {
                    cleanedYaml = cleanedYaml.replace(/!<[^>]+>/g, '');
                    data = jsyaml.load(cleanedYaml);
                }
                
                if (!data || typeof data === 'string' || !data.domains || !data.domains.local || !data.domains.local.shared) {
                    showSaveStatus('bank-items-status', '❌ Invalid profile data.', false);
                    return;
                }
                
                if (!data.domains.local.shared.inventory) {
                    data.domains.local.shared.inventory = { items: {} };
                }
                if (!data.domains.local.shared.inventory.items) {
                    data.domains.local.shared.inventory.items = {};
                }
                if (!data.domains.local.shared.inventory.items.bank) {
                    data.domains.local.shared.inventory.items.bank = {};
                }
                
                const bank = data.domains.local.shared.inventory.items.bank;
                
                // Find next available slot
                const nums = Object.keys(bank)
                    .map(k => {
                        const m = k.match(/^slot_(\d+)$/);
                        return m ? parseInt(m[1], 10) : null;
                    })
                    .filter(n => n !== null);
                const nextIndex = nums.length ? Math.max(...nums) + 1 : 0;
                const slotKey = `slot_${nextIndex}`;
                
                bank[slotKey] = { serial, state_flags: 1 };
                
                const newYaml = jsyaml.dump(data, { lineWidth: -1, noRefs: true });
                window.profileMonacoEditor.setValue(newYaml);
                
                input.value = '';
                renderBankItems(bank);
                showSaveStatus('bank-items-status', `✅ Item added to bank at ${slotKey}!`, true);
                
                // Track add_to_backpack event (bank is a type of inventory)
                if (typeof window.trackEvent === 'function') {
                    window.trackEvent('add_to_backpack', { 
                        count: 1, 
                        category: 'bank',
                        source: 'button'
                    });
                }
            } catch (error) {
                console.error('Error adding to bank:', error);
                showSaveStatus('bank-items-status', `❌ Error: ${error.message}`, false);
            }
        }

        function removeBankSlot(slotKey) {
            if (!window.profileMonacoEditor) return;
            
            try {
                const yamlContent = window.profileMonacoEditor.getValue();
                // Clean YAML before parsing
                let cleanedYaml = yamlContent.replace(/:\s*!tags/g, ':');
                cleanedYaml = cleanedYaml.replace(/:\s*!<[^>]+>/g, ':');
                
                let data;
                try {
                    data = jsyaml.load(cleanedYaml);
                } catch (parseError) {
                    cleanedYaml = cleanedYaml.replace(/!<[^>]+>/g, '');
                    data = jsyaml.load(cleanedYaml);
                }
                
                if (!data || typeof data === 'string' || !data.domains || !data.domains.local || !data.domains.local.shared || !data.domains.local.shared.inventory || !data.domains.local.shared.inventory.items || !data.domains.local.shared.inventory.items.bank) {
                    return;
                }
                
                const bank = data.domains.local.shared.inventory.items.bank;
                delete bank[slotKey];
                
                const newYaml = jsyaml.dump(data, { lineWidth: -1, noRefs: true });
                window.profileMonacoEditor.setValue(newYaml);
                
                renderBankItems(bank);
            } catch (error) {
                console.error('Error removing bank slot:', error);
            }
        }

        // Cosmetics Functions — catalog populated by Legit Builder from Nexus-Data-Resident*.json (window.NEXUS_ALL_COSMETICS)
        function getNexusCosmeticsList() {
            return Array.isArray(window.NEXUS_ALL_COSMETICS) ? window.NEXUS_ALL_COSMETICS : [];
        }

        function refreshCosmeticsDropdownIfProfileOpen() {
            if (!window.profileMonacoEditor) return;
            const yamlContent = window.profileMonacoEditor.getValue();
            if (!yamlContent || !String(yamlContent).trim()) return;
            let cleanedYaml = yamlContent.replace(/:\s*!tags/g, ':');
            cleanedYaml = cleanedYaml.replace(/:\s*!<[^>]+>/g, ':');
            let data;
            try {
                data = jsyaml.load(cleanedYaml);
            } catch (parseError) {
                cleanedYaml = cleanedYaml.replace(/!<[^>]+>/g, '');
                try {
                    data = jsyaml.load(cleanedYaml);
                } catch (_) {
                    return;
                }
            }
            if (!data || typeof data === 'string' || !data.domains || !data.domains.local) return;
            const result = getAllCosmeticsFromUnlockables(data);
            populateCosmeticsDropdown(result.cosmetics);
        }

        window.addEventListener('nexus-cosmetics-updated', function () {
            refreshCosmeticsDropdownIfProfileOpen();
        });

        function getNexusSharedProgressList() {
            return Array.isArray(window.NEXUS_ALL_SHARED_PROGRESS) ? window.NEXUS_ALL_SHARED_PROGRESS : [];
        }

        function getNexusChallengeUnlockCatalog() {
            return Array.isArray(window.NEXUS_ALL_CHALLENGE_UNLOCKABLES) ? window.NEXUS_ALL_CHALLENGE_UNLOCKABLES : [];
        }

        function getChallengeUnlockFilterValue() {
            const el = document.getElementById('challenge-unlock-family-filter');
            return (el && el.value) || 'all';
        }

        function filterNexusChallengeCatalog(list, filter) {
            const f = filter || 'all';
            if (f === 'all') return list.slice();
            return list.filter(item => {
                const sk = item.sectionKey || '';
                if (f === 'sharedprogress') return sk.indexOf('sharedprogress_') === 0;
                if (f === 'echo') return sk.indexOf('echo_') === 0;
                if (f === 'vault') return sk.indexOf('vault_') === 0;
                return true;
            });
        }

        function normalizeAccountChallengeUnlockId(rawId) {
            if (!rawId || typeof rawId !== 'string') return '';
            let id = rawId.trim();
            if (id.startsWith('SharedProgress_')) {
                const dot = id.indexOf('.');
                if (dot === -1) return id;
                return id.slice(0, dot + 1) + id.slice(dot + 1).toLowerCase();
            }
            return id.toLowerCase();
        }

        function normalizeSharedProgressEntryId(rawId) {
            return normalizeAccountChallengeUnlockId(rawId);
        }

        function getAccountChallengeUnlockSection(profileEntry) {
            const id = normalizeAccountChallengeUnlockId(profileEntry);
            if (id.startsWith('SharedProgress_')) {
                const m = /^SharedProgress_([^.]+)\./.exec(id);
                return m ? 'sharedprogress_' + m[1].toLowerCase() : null;
            }
            const dot = id.indexOf('.');
            if (dot === -1) return null;
            return id.slice(0, dot);
        }

        function getSharedProgressSection(profileEntry) {
            return getAccountChallengeUnlockSection(profileEntry);
        }

        function isAccountChallengeUnlockSectionKey(key) {
            if (!key || typeof key !== 'string') return false;
            if (key.startsWith('sharedprogress_')) return true;
            if (key.endsWith('_challenges')) return true;
            return false;
        }

        function accountChallengeSectionLabel(sectionKey) {
            if (!sectionKey || typeof sectionKey !== 'string') return sectionKey;
            if (sectionKey.startsWith('sharedprogress_')) {
                const rest = sectionKey.replace(/^sharedprogress_/i, '');
                if (!rest) return sectionKey;
                return 'Shared ' + rest.charAt(0).toUpperCase() + rest.slice(1);
            }
            return sectionKey.replace(/_/g, ' ');
        }

        function sharedProgressSectionLabel(sectionKey) {
            return accountChallengeSectionLabel(sectionKey);
        }

        function addAccountChallengeUnlockToUnlockables(data, entryId) {
            if (!data.domains || !data.domains.local) return false;
            const id = normalizeAccountChallengeUnlockId(entryId);
            const section = getAccountChallengeUnlockSection(id);
            if (!section) return false;
            if (!data.domains.local.unlockables) data.domains.local.unlockables = {};
            if (!data.domains.local.unlockables[section]) {
                data.domains.local.unlockables[section] = { entries: [] };
            }
            if (!data.domains.local.unlockables[section].entries) {
                data.domains.local.unlockables[section].entries = [];
            }
            if (!data.domains.local.unlockables[section].entries.includes(id)) {
                data.domains.local.unlockables[section].entries.push(id);
            }
            data.domains.local.unlockables[section].entries.sort();
            return true;
        }

        function addSharedProgressToUnlockables(data, entryId) {
            return addAccountChallengeUnlockToUnlockables(data, entryId);
        }

        function removeAccountChallengeUnlockFromUnlockables(data, entryId) {
            if (!data.domains || !data.domains.local || !data.domains.local.unlockables) return false;
            const id = normalizeAccountChallengeUnlockId(entryId);
            const section = getAccountChallengeUnlockSection(id);
            if (!section || !data.domains.local.unlockables[section] || !Array.isArray(data.domains.local.unlockables[section].entries)) {
                return false;
            }
            const entries = data.domains.local.unlockables[section].entries;
            const idx = entries.indexOf(id);
            if (idx === -1) return false;
            entries.splice(idx, 1);
            return true;
        }

        function removeSharedProgressFromUnlockables(data, entryId) {
            return removeAccountChallengeUnlockFromUnlockables(data, entryId);
        }

        function getAllAccountChallengeUnlocksFromUnlockables(data) {
            const sharedProgress = {};
            const bySection = {};
            if (!data.domains || !data.domains.local || !data.domains.local.unlockables) {
                return { sharedProgress, bySection };
            }
            Object.keys(data.domains.local.unlockables).forEach(sectionKey => {
                if (!isAccountChallengeUnlockSectionKey(sectionKey)) return;
                const block = data.domains.local.unlockables[sectionKey];
                if (!block || !Array.isArray(block.entries)) return;
                block.entries.forEach(entry => {
                    if (entry && typeof entry === 'string') {
                        const nid = normalizeAccountChallengeUnlockId(entry);
                        const sec = getAccountChallengeUnlockSection(nid);
                        if (!sec) return;
                        sharedProgress[nid] = { section: sec };
                        if (!bySection[sec]) bySection[sec] = {};
                        bySection[sec][nid] = true;
                    }
                });
            });
            return { sharedProgress, bySection };
        }

        function getAllSharedProgressFromUnlockables(data) {
            return getAllAccountChallengeUnlocksFromUnlockables(data);
        }

        /** Region buckets for challenge ids (echo_log *_city_ / *_gra_ / … and echo_upgrade *_grasslands_ / …). */
        const CHALLENGE_REGION_BUCKET_ORDER = ['city', 'gra', 'sha', 'mtn', 'other'];
        const CHALLENGE_REGION_BUCKET_LABELS = {
            city: 'Dominion',
            gra: 'The Fadefields',
            sha: 'Carcadia Burn',
            mtn: 'Terminus Range',
            other: 'Other / unknown region'
        };

        function inferChallengeRegionBucket(progressId) {
            if (!progressId || typeof progressId !== 'string') return 'other';
            const dot = progressId.indexOf('.');
            const s = (dot >= 0 ? progressId.slice(dot + 1) : progressId).toLowerCase();
            if (s.indexOf('_grasslands') !== -1) return 'gra';
            if (s.indexOf('_shatteredlands') !== -1) return 'sha';
            if (s.indexOf('_mountains') !== -1) return 'mtn';
            if (/_mtn(?:_|$)/.test(s)) return 'mtn';
            if (/_sha(?:_|$)/.test(s)) return 'sha';
            if (/_gra(?:_|$)/.test(s)) return 'gra';
            if (/_city(?:_|$)/.test(s)) return 'city';
            if (s.indexOf('_city') !== -1) return 'city';
            return 'other';
        }

        function shouldSubgroupAccountChallengesByRegion(sectionKey) {
            return !!(sectionKey && typeof sectionKey === 'string' && sectionKey.endsWith('_challenges'));
        }

        function appendSharedProgressRow(container, progressId) {
            const row = document.createElement('div');
            row.style.cssText =
                'padding: var(--input-pad-y) var(--input-pad-x); background: rgba(79, 195, 247, 0.1); border: 1px solid rgba(79, 195, 247, 0.3); border-radius: 6px; display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--input-pad-y); margin-left: 12px;';
            const escapedKey = progressId.replace(/'/g, "\\'").replace(/"/g, '&quot;');
            row.innerHTML =
                '<div style="color: #81d4fa; font-weight: 500; font-size: 0.95em;">' +
                escapeHtmlProgressionUi(progressId) +
                '</div><button type="button" onclick="removeSharedProgress(\'' +
                escapedKey +
                '\')" style="padding: 4px 8px; background: rgba(255, 100, 100, 0.3); border: 1px solid rgba(255, 100, 100, 0.5); border-radius: 4px; color: #ff6b6b; cursor: pointer; font-size: 0.85em;">Remove</button>';
            container.appendChild(row);
        }

        function populateSharedProgressDropdown(unlockedMap) {
            const select = document.getElementById('shared-progress-select');
            if (!select) return;
            while (select.options.length > 1) select.remove(1);
            const unlocked = new Set(Object.keys(unlockedMap || {}));
            const filter = getChallengeUnlockFilterValue();
            let catalog = filterNexusChallengeCatalog(getNexusChallengeUnlockCatalog(), filter);
            if (catalog.length === 0) {
                const legacy = getNexusSharedProgressList()
                    .map(id => ({
                        normalized: id,
                        sectionKey: getAccountChallengeUnlockSection(id),
                        rawNcs: id
                    }))
                    .filter(x => x.sectionKey);
                catalog = filterNexusChallengeCatalog(legacy, filter);
            }
            if (catalog.length === 0) {
                const option = document.createElement('option');
                option.value = '';
                option.textContent = 'Load Nexus (challenge + discovery) via Legit Builder first';
                option.disabled = true;
                select.appendChild(option);
                return;
            }
            const toShow = catalog.filter(c => c && c.normalized && !unlocked.has(c.normalized));
            toShow.forEach(c => {
                const option = document.createElement('option');
                option.value = c.normalized;
                option.textContent = '[' + c.sectionKey + '] ' + c.normalized;
                select.appendChild(option);
            });
            if (toShow.length === 0) {
                const option = document.createElement('option');
                option.value = '';
                option.textContent = 'All matching catalog entries are already unlocked';
                option.disabled = true;
                select.appendChild(option);
            }
        }

        function renderSharedProgress(sharedProgress, bySection) {
            const container = document.getElementById('shared-progress-items-container');
            const countEl = document.getElementById('shared-progress-items-count');
            if (!container) return;
            container.innerHTML = '';
            const entries = Object.entries(sharedProgress || {});
            if (countEl) countEl.textContent = '(' + entries.length + ' unlocked)';
            populateSharedProgressDropdown(sharedProgress);
            const sectionMap = {};
            Object.keys(bySection || {}).forEach(sk => {
                sectionMap[sk] = { ...(bySection[sk] || {}) };
            });
            entries.forEach(([key]) => {
                const sec = getAccountChallengeUnlockSection(key);
                if (!sec) return;
                if (!sectionMap[sec]) sectionMap[sec] = {};
                sectionMap[sec][key] = true;
            });
            const keysToRender = Object.keys(sectionMap).sort();
            keysToRender.forEach(sectionKey => {
                const ids = Object.keys(sectionMap[sectionKey] || {}).sort();
                if (ids.length === 0) return;
                const sectionHeader = document.createElement('div');
                sectionHeader.style.cssText = 'margin-top: var(--section-gap-bottom); margin-bottom: var(--input-pad-y); padding: var(--input-pad-y) var(--input-pad-x); background: rgba(79, 195, 247, 0.2); border-left: 3px solid rgba(79, 195, 247, 0.6); border-radius: 4px;';
                sectionHeader.innerHTML =
                    '<h4 style="margin: 0; color: #81d4fa; font-size: var(--panel-title-size); font-weight: 600;">' +
                    accountChallengeSectionLabel(sectionKey) +
                    ' <span style="font-weight: normal; opacity: 0.8; font-size: 0.88em;">(' +
                    ids.length +
                    ')</span></h4>';
                container.appendChild(sectionHeader);
                if (shouldSubgroupAccountChallengesByRegion(sectionKey)) {
                    const byBucket = {};
                    ids.forEach(function (progressId) {
                        const b = inferChallengeRegionBucket(progressId);
                        if (!byBucket[b]) byBucket[b] = [];
                        byBucket[b].push(progressId);
                    });
                    CHALLENGE_REGION_BUCKET_ORDER.forEach(function (bucket) {
                        const groupIds = byBucket[bucket];
                        if (!groupIds || groupIds.length === 0) return;
                        groupIds.sort();
                        const sub = document.createElement('div');
                        sub.style.cssText =
                            'margin-top: 8px; margin-bottom: 6px; margin-left: 4px; padding: 8px 10px; background: rgba(79, 195, 247, 0.08); border-left: 2px solid rgba(129, 212, 250, 0.45); border-radius: 4px;';
                        sub.innerHTML =
                            '<h5 style="margin: 0; color: #b3e5fc; font-size: 0.95em; font-weight: 600;">' +
                            escapeHtmlProgressionUi(CHALLENGE_REGION_BUCKET_LABELS[bucket] || bucket) +
                            ' <span style="font-weight: normal; opacity: 0.78; font-size: 0.88em;">(' +
                            groupIds.length +
                            ')</span></h5>';
                        container.appendChild(sub);
                        groupIds.forEach(function (progressId) {
                            appendSharedProgressRow(container, progressId);
                        });
                    });
                } else {
                    ids.forEach(function (progressId) {
                        const row = document.createElement('div');
                        row.style.cssText =
                            'padding: var(--input-pad-y) var(--input-pad-x); background: rgba(79, 195, 247, 0.1); border: 1px solid rgba(79, 195, 247, 0.3); border-radius: 6px; display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--input-pad-y);';
                        const escapedKey = progressId.replace(/'/g, "\\'").replace(/"/g, '&quot;');
                        row.innerHTML =
                            '<div style="color: #81d4fa; font-weight: 500; font-size: 0.95em;">' +
                            escapeHtmlProgressionUi(progressId) +
                            '</div><button type="button" onclick="removeSharedProgress(\'' +
                            escapedKey +
                            '\')" style="padding: 4px 8px; background: rgba(255, 100, 100, 0.3); border: 1px solid rgba(255, 100, 100, 0.5); border-radius: 4px; color: #ff6b6b; cursor: pointer; font-size: 0.85em;">Remove</button>';
                        container.appendChild(row);
                    });
                }
            });
            if (entries.length === 0) {
                const emptyMsg = document.createElement('div');
                emptyMsg.style.cssText = 'padding: var(--panel-pad); text-align: center; color: rgba(129, 212, 250, 0.6); font-style: italic; font-size: 0.9em;';
                emptyMsg.textContent = 'No account challenge unlocks yet. Add from the catalog or enter an id.';
                container.appendChild(emptyMsg);
            }
        }

        function refreshSharedProgressDropdownIfProfileOpen() {
            if (!window.profileMonacoEditor) return;
            const yamlContent = window.profileMonacoEditor.getValue();
            if (!yamlContent || !String(yamlContent).trim()) return;
            let cleanedYaml = yamlContent.replace(/:\s*!tags/g, ':');
            cleanedYaml = cleanedYaml.replace(/:\s*!<[^>]+>/g, ':');
            let data;
            try {
                data = jsyaml.load(cleanedYaml);
            } catch (parseError) {
                cleanedYaml = cleanedYaml.replace(/!<[^>]+>/g, '');
                try {
                    data = jsyaml.load(cleanedYaml);
                } catch (_) {
                    return;
                }
            }
            if (!data || typeof data === 'string' || !data.domains || !data.domains.local) return;
            const result = getAllAccountChallengeUnlocksFromUnlockables(data);
            populateSharedProgressDropdown(result.sharedProgress);
        }

        window.addEventListener('nexus-shared-progress-updated', function () {
            refreshSharedProgressDropdownIfProfileOpen();
        });
        window.addEventListener('nexus-challenge-unlockables-updated', function () {
            refreshSharedProgressDropdownIfProfileOpen();
        });

        function addSelectedSharedProgress() {
            const select = document.getElementById('shared-progress-select');
            if (!select || !select.value) {
                showSaveStatus('shared-progress-items-status', '❌ Please select an entry.', false);
                return;
            }
            addSharedProgressToProfile(select.value);
        }

        function addManualSharedProgress() {
            const input = document.getElementById('shared-progress-manual-input');
            if (!input || !input.value.trim()) {
                showSaveStatus('shared-progress-items-status', '❌ Please enter an id.', false);
                return;
            }
            const raw = input.value.trim();
            input.value = '';
            addSharedProgressToProfile(raw);
        }

        function ensureProfileYamlLocalShared(data) {
            if (!data.domains) data.domains = {};
            if (!data.domains.local) data.domains.local = {};
            if (!data.domains.local.shared) data.domains.local.shared = {};
        }

        function parseProfileYamlFromMonaco() {
            let yamlContent = getProfileYamlEditorValue();
            let cleanedYaml = yamlContent.replace(/:\s*!tags/g, ':');
            cleanedYaml = cleanedYaml.replace(/:\s*!<[^>]+>/g, ':');
            let data;
            try {
                data = jsyaml.load(cleanedYaml);
            } catch (parseError) {
                cleanedYaml = cleanedYaml.replace(/!<[^>]+>/g, '');
                data = jsyaml.load(cleanedYaml);
            }
            return data;
        }

        function parseProfileYamlStringForProfileEditor(yamlContent) {
            if (!yamlContent || typeof yamlContent !== 'string' || !yamlContent.trim()) return null;
            let cleanedYaml = yamlContent.replace(/:\s*!tags/g, ':');
            cleanedYaml = cleanedYaml.replace(/:\s*!<[^>]+>/g, ':');
            let data;
            try {
                data = jsyaml.load(cleanedYaml);
            } catch (parseError) {
                cleanedYaml = cleanedYaml.replace(/!<[^>]+>/g, '');
                try {
                    data = jsyaml.load(cleanedYaml);
                } catch (e2) {
                    return null;
                }
            }
            return data;
        }

        function getParsedProfileDataForProgressionUi() {
            let yamlContent = '';
            if (window.profileMonacoEditor && typeof window.profileMonacoEditor.getValue === 'function') {
                yamlContent = window.profileMonacoEditor.getValue() || '';
            }
            if (!yamlContent.trim() && typeof window.profileYAMLContent === 'string') {
                yamlContent = window.profileYAMLContent;
            }
            return parseProfileYamlStringForProfileEditor(yamlContent);
        }

        function onChallengeUnlockFilterChanged() {
            refreshSharedProgressDropdownIfProfileOpen();
        }

        function addSharedProgressToProfile(entryId) {
            if (!window.profileMonacoEditor) {
                showSaveStatus('shared-progress-items-status', '❌ Please decrypt a profile file first.', false);
                return;
            }
            const id = normalizeAccountChallengeUnlockId(entryId);
            if (!getAccountChallengeUnlockSection(id)) {
                showSaveStatus(
                    'shared-progress-items-status',
                    '❌ Id must be SharedProgress_*.x or *._challenges.x (see profile echo/vault sections).',
                    false
                );
                return;
            }
            try {
                const data = parseProfileYamlFromMonaco();
                if (!data || typeof data === 'string' || !data.domains || !data.domains.local) {
                    showSaveStatus('shared-progress-items-status', '❌ Invalid profile data.', false);
                    return;
                }
                ensureProfileYamlLocalShared(data);
                if (!addAccountChallengeUnlockToUnlockables(data, id)) {
                    showSaveStatus('shared-progress-items-status', '❌ Could not add entry (check id format).', false);
                    return;
                }
                const newYaml = jsyaml.dump(data, { lineWidth: -1, noRefs: true });
                window.profileMonacoEditor.setValue(newYaml);
                const result = getAllAccountChallengeUnlocksFromUnlockables(data);
                renderSharedProgress(result.sharedProgress, result.bySection);
                showSaveStatus('shared-progress-items-status', '✅ Added "' + id + '"', true);
            } catch (error) {
                console.error('Error adding account challenge unlock:', error);
                showSaveStatus('shared-progress-items-status', '❌ Error: ' + error.message, false);
            }
        }

        function addAllSharedProgress() {
            if (!window.profileMonacoEditor) {
                showSaveStatus('shared-progress-items-status', '❌ Please decrypt a profile file first.', false);
                return;
            }
            const filter = getChallengeUnlockFilterValue();
            let catalog = filterNexusChallengeCatalog(getNexusChallengeUnlockCatalog(), filter);
            if (catalog.length === 0) {
                const legacy = getNexusSharedProgressList();
                catalog = legacy.map(id => ({
                    normalized: id,
                    sectionKey: getAccountChallengeUnlockSection(id),
                    rawNcs: id
                })).filter(x => x.sectionKey);
                catalog = filterNexusChallengeCatalog(catalog, filter);
            }
            if (catalog.length === 0) {
                showSaveStatus(
                    'shared-progress-items-status',
                    '❌ No catalog for this filter. Load Nexus challenge + discovery via Legit Builder.',
                    false
                );
                return;
            }
            try {
                const data = parseProfileYamlFromMonaco();
                if (!data || typeof data === 'string' || !data.domains || !data.domains.local) {
                    showSaveStatus('shared-progress-items-status', '❌ Invalid profile data.', false);
                    return;
                }
                ensureProfileYamlLocalShared(data);
                catalog.forEach(c => addAccountChallengeUnlockToUnlockables(data, c.normalized));
                const newYaml = jsyaml.dump(data, { lineWidth: -1, noRefs: true });
                window.profileMonacoEditor.setValue(newYaml);
                const result = getAllAccountChallengeUnlocksFromUnlockables(data);
                renderSharedProgress(result.sharedProgress, result.bySection);
                showSaveStatus('shared-progress-items-status', '✅ Added ' + catalog.length + ' catalog entries.', true);
            } catch (error) {
                console.error('Error adding all account challenge unlocks:', error);
                showSaveStatus('shared-progress-items-status', '❌ Error: ' + error.message, false);
            }
        }

        function removeAllSharedProgress() {
            if (!window.profileMonacoEditor) {
                showSaveStatus('shared-progress-items-status', '❌ Please decrypt a profile file first.', false);
                return;
            }
            if (!confirm('Remove all account challenge unlocks (SharedProgress + echo/vault *_challenges) from this profile?')) return;
            try {
                const data = parseProfileYamlFromMonaco();
                if (!data || typeof data === 'string' || !data.domains || !data.domains.local) {
                    showSaveStatus('shared-progress-items-status', '❌ Invalid profile data.', false);
                    return;
                }
                if (data.domains.local.unlockables) {
                    Object.keys(data.domains.local.unlockables).forEach(k => {
                        if (isAccountChallengeUnlockSectionKey(k) && data.domains.local.unlockables[k]) {
                            data.domains.local.unlockables[k].entries = [];
                        }
                    });
                }
                const newYaml = jsyaml.dump(data, { lineWidth: -1, noRefs: true });
                window.profileMonacoEditor.setValue(newYaml);
                renderSharedProgress({}, {});
                showSaveStatus('shared-progress-items-status', '✅ All account challenge unlocks removed.', true);
            } catch (error) {
                console.error('Error removing account challenge unlocks:', error);
                showSaveStatus('shared-progress-items-status', '❌ Error: ' + error.message, false);
            }
        }

        function removeSharedProgress(entryId) {
            if (!window.profileMonacoEditor) return;
            try {
                const data = parseProfileYamlFromMonaco();
                if (!data || typeof data === 'string' || !data.domains || !data.domains.local) return;
                removeAccountChallengeUnlockFromUnlockables(data, entryId);
                const newYaml = jsyaml.dump(data, { lineWidth: -1, noRefs: true });
                window.profileMonacoEditor.setValue(newYaml);
                const result = getAllAccountChallengeUnlocksFromUnlockables(data);
                renderSharedProgress(result.sharedProgress, result.bySection);
            } catch (error) {
                console.error('Error removing account challenge unlock:', error);
            }
        }

        let __progressionSharedManifestCache = null;
        window.addEventListener('nexus-progression-shared-manifest-updated', function () {
            __progressionSharedManifestCache = null;
        });
        function loadProgressionSharedManifest() {
            if (__progressionSharedManifestCache) return Promise.resolve(__progressionSharedManifestCache);
            function getNexusProgressionManifest() {
                const m = window.NEXUS_PROGRESSION_SHARED_MANIFEST;
                return m && Array.isArray(m.graphs) && m.graphs.length > 0 ? m : null;
            }
            function getEmbeddedManifest() {
                const fn = window.profileDataGetProgressionSharedManifestEmbedded;
                if (typeof fn !== 'function') return null;
                const m = fn();
                return m && Array.isArray(m.graphs) ? m : null;
            }
            function cacheAndReturn(m) {
                __progressionSharedManifestCache = m;
                return m;
            }
            const nexusM = getNexusProgressionManifest();
            if (nexusM) return Promise.resolve(cacheAndReturn(nexusM));

            const isFile = typeof location !== 'undefined' && location.protocol === 'file:';
            if (isFile) {
                const emb = getEmbeddedManifest();
                if (emb) return Promise.resolve(cacheAndReturn(emb));
                return Promise.reject(new Error('embedded manifest not loaded (yaml-save script missing?)'));
            }
            const urls = [
                'js/item-editor/data/progression-shared-manifest.json',
                './js/item-editor/data/progression-shared-manifest.json'
            ];
            function tryFetch(i) {
                if (i >= urls.length) {
                    const emb = getEmbeddedManifest();
                    if (emb) return Promise.resolve(cacheAndReturn(emb));
                    return Promise.reject(new Error('Failed to fetch'));
                }
                return fetch(urls[i])
                    .then(r => {
                        if (!r.ok) throw new Error('HTTP ' + r.status);
                        return r.json();
                    })
                    .then(j => cacheAndReturn(j))
                    .catch(() => tryFetch(i + 1));
            }
            return tryFetch(0);
        }

        const PROGRESSION_SDU_ROW_DEFS = [
            { prefix: 'Ammo_Pistol', label: 'Pistol', maxTier: 7 },
            { prefix: 'Ammo_SMG', label: 'SMG', maxTier: 7 },
            { prefix: 'Ammo_AR', label: 'Assault rifle', maxTier: 7 },
            { prefix: 'Ammo_SG', label: 'Shotgun', maxTier: 7 },
            { prefix: 'Ammo_SR', label: 'Sniper', maxTier: 7 },
            { prefix: 'Backpack', label: 'Backpack', maxTier: 8 },
            { prefix: 'Bank', label: 'Bank', maxTier: 8 },
            { prefix: 'Lost_Loot', label: 'Lost loot', maxTier: 8 }
        ];

        function escapeHtmlProgressionUi(s) {
            if (s === null || s === undefined) return '';
            const d = document.createElement('div');
            d.textContent = String(s);
            return d.innerHTML;
        }

        function ensureProfileProgressionMonacoContentListener() {
            const ed = window.profileMonacoEditor;
            if (!ed || typeof ed.onDidChangeModelContent !== 'function') return;
            if (ed.__progressionSharedYamlListenerAttached) return;
            ed.__progressionSharedYamlListenerAttached = true;
            let debounceTimer = null;
            ed.onDidChangeModelContent(function () {
                const inner = document.getElementById('progression-shared-inner');
                if (!inner || inner.style.display === 'none') return;
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(function () {
                    if (typeof window.refreshProgressionSharedPanel === 'function') {
                        window.refreshProgressionSharedPanel();
                    }
                }, 450);
            });
        }

        function collectProgressionSharedUiFromDom() {
            const vault = {};
            document.querySelectorAll('input.profile-progression-vault-cb[data-vault-name]').forEach(function (el) {
                const name = el.getAttribute('data-vault-name');
                if (name) vault[name] = !!el.checked;
            });
            const sduTiers = {};
            document.querySelectorAll('select.profile-progression-sdu-tier[data-sdu-prefix]').forEach(function (el) {
                const prefix = el.getAttribute('data-sdu-prefix');
                if (!prefix) return;
                const v = parseInt(el.value, 10);
                sduTiers[prefix] = Number.isFinite(v) ? v : 0;
            });
            const echoEl = document.getElementById('profile-progression-echo-points');
            const echoPoints =
                echoEl && echoEl.value !== '' && echoEl.value != null ? echoEl.value : null;
            return { vault, sduTiers, echoPoints };
        }

        function writeProfileYamlFromProgressionSharedData(data) {
            window.profileMonacoEditor.setValue(jsyaml.dump(data, { lineWidth: -1, noRefs: true }));
        }

        function applyProfileProgressionSharedGranularFromDom(showStatus) {
            if (!window.profileMonacoEditor || typeof window.profileDataApplyProgressionSharedUi !== 'function') return;
            loadProgressionSharedManifest()
                .then(function (manifest) {
                    try {
                        const data = parseProfileYamlFromMonaco();
                        if (!data || !data.domains || !data.domains.local) {
                            if (showStatus) {
                                showSaveStatus('profile-progression-shared-status', '❌ Invalid profile.', false);
                            }
                            return;
                        }
                        ensureProfileYamlLocalShared(data);
                        const ui = collectProgressionSharedUiFromDom();
                        const res = window.profileDataApplyProgressionSharedUi(data, manifest, ui);
                        if (!res.ok) {
                            if (showStatus) {
                                showSaveStatus(
                                    'profile-progression-shared-status',
                                    '❌ ' + (res.error || 'Failed'),
                                    false
                                );
                            }
                            return;
                        }
                        writeProfileYamlFromProgressionSharedData(data);
                        if (showStatus) {
                            showSaveStatus(
                                'profile-progression-shared-status',
                                '✅ Updated progression_shared.',
                                true
                            );
                        }
                    } catch (e) {
                        if (showStatus) {
                            showSaveStatus('profile-progression-shared-status', '❌ ' + e.message, false);
                        }
                    }
                })
                .catch(function (e) {
                    if (showStatus) {
                        showSaveStatus('profile-progression-shared-status', '❌ Manifest: ' + e.message, false);
                    }
                });
        }

        function refreshProgressionSharedPanel() {
            if (!window.profileMonacoEditor) return;
            ensureProfileProgressionMonacoContentListener();
            ensureProgressionSharedVaultSduDelegation();
            bindProfileProgressionEchoInputOnce();
            const vaultHost = document.getElementById('profile-progression-vault-list');
            const sduHost = document.getElementById('profile-progression-sdu-tiers');
            const echoInput = document.getElementById('profile-progression-echo-points');
            if (!vaultHost || !sduHost) return;

            loadProgressionSharedManifest()
                .then(function (manifest) {
                    let data = getParsedProfileDataForProgressionUi();
                    if (!data) {
                        vaultHost.innerHTML =
                            '<span style="opacity:0.8">Could not parse profile YAML.</span>';
                        sduHost.innerHTML = '';
                        return;
                    }
                    const derive =
                        typeof window.profileDataDeriveProgressionSharedUiState === 'function'
                            ? window.profileDataDeriveProgressionSharedUiState(data, manifest)
                            : null;
                    if (!derive || !derive.ok) {
                        vaultHost.innerHTML =
                            '<span style="opacity:0.8">' +
                            escapeHtmlProgressionUi((derive && derive.error) || 'Invalid manifest.') +
                            '</span>';
                        sduHost.innerHTML = '';
                        return;
                    }

                    const vKeys = Object.keys(derive.vault);
                    if (vKeys.length === 0) {
                        vaultHost.innerHTML =
                            '<span style="opacity:0.8">No vault power nodes in manifest.</span>';
                    } else {
                        vaultHost.innerHTML = vKeys
                            .map(function (name) {
                                const id =
                                    'prog-vault-' +
                                    name.replace(/[^a-zA-Z0-9]+/g, '_').replace(/^_|_$/g, '');
                                const checked = derive.vault[name] ? ' checked' : '';
                                return (
                                    '<div class="profile-progression-vault-row">' +
                                    '<input type="checkbox" class="profile-progression-vault-cb" data-vault-name="' +
                                    escapeHtmlProgressionUi(name) +
                                    '" id="' +
                                    id +
                                    '"' +
                                    checked +
                                    ' />' +
                                    '<label class="profile-progression-vault-text" for="' +
                                    id +
                                    '">' +
                                    escapeHtmlProgressionUi(name) +
                                    '</label></div>'
                                );
                            })
                            .join('');
                    }

                    sduHost.innerHTML = PROGRESSION_SDU_ROW_DEFS.map(function (row) {
                        const tierNum = Number(derive.sduTiers[row.prefix]) || 0;
                        const opts = [
                            '<option value="0"' +
                                (tierNum === 0 ? ' selected' : '') +
                                '>0 — none</option>'
                        ];
                        for (let t = 1; t <= row.maxTier; t++) {
                            opts.push(
                                '<option value="' +
                                    t +
                                    '"' +
                                    (t === tierNum ? ' selected' : '') +
                                    '>Tier ' +
                                    t +
                                    '</option>'
                            );
                        }
                        return (
                            '<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">' +
                            '<span style="min-width:120px;color:#b3e5fc;">' +
                            escapeHtmlProgressionUi(row.label) +
                            '</span>' +
                            '<select class="profile-progression-sdu-tier" data-sdu-prefix="' +
                            escapeHtmlProgressionUi(row.prefix) +
                            '" style="padding:6px 10px;background:rgba(0,0,0,0.5);border:1px solid rgba(79,195,247,0.35);border-radius:4px;color:#81d4fa;">' +
                            opts.join('') +
                            '</select></div>'
                        );
                    }).join('');

                    if (echoInput) {
                        const ep = derive.echoPoints;
                        echoInput.value =
                            ep != null && ep !== '' ? String(ep) : '';
                    }
                })
                .catch(function (err) {
                    vaultHost.innerHTML =
                        '<span style="opacity:0.8">Could not load progression manifest.</span>';
                    sduHost.innerHTML = '';
                });
        }

        window.refreshProgressionSharedPanel = refreshProgressionSharedPanel;

        function getLegitBlackMarketOptions() {
            if (typeof window.legitBuilderGetUniqueLegendaryCompOptions === 'function') {
                try {
                    return window.legitBuilderGetUniqueLegendaryCompOptions() || [];
                } catch (_) {
                    return [];
                }
            }
            return window.__legitBuilderUniqueLegendaryComps || [];
        }

        function blackMarketLabelForComp(comp) {
            const c = (comp || '').trim();
            if (!c) return '';
            const opts = getLegitBlackMarketOptions();
            for (let i = 0; i < opts.length; i++) {
                if (opts[i].value === c) return opts[i].label || c;
            }
            return c;
        }

        function getBlackMarketRowsFromDom() {
            const rows = [];
            document.querySelectorAll('.profile-blackmarket-slot-row').forEach(function (row) {
                const hid = row.querySelector('.profile-blackmarket-comp-hidden');
                const gsEl = row.querySelector('.profile-blackmarket-gs');
                const comp = hid && hid.value ? String(hid.value).trim() : '';
                const gsRaw = gsEl && gsEl.value !== '' ? parseInt(gsEl.value, 10) : 60;
                rows.push({
                    itemcomp: comp,
                    gamestage: Number.isFinite(gsRaw) ? gsRaw : 60
                });
            });
            return rows;
        }

        function renderBlackMarketSlotRows(rows) {
            const host = document.getElementById('profile-blackmarket-slots-host');
            if (!host) return;
            const html = rows
                .map(function (row, i) {
                    const comp = (row.itemcomp || '').trim();
                    const gs = row.gamestage != null ? row.gamestage : 60;
                    const vis = blackMarketLabelForComp(comp);
                    return (
                        '<div class="profile-blackmarket-slot-row" style="position:relative;border:1px solid rgba(79,195,247,0.22);padding:10px 12px;border-radius:4px;background:rgba(0,0,0,0.2);">' +
                        '<div style="font-size:0.8em;color:#81d4fa;margin-bottom:6px;font-weight:600;">Slot ' +
                        (i + 1) +
                        '</div>' +
                        '<div style="display:flex;flex-wrap:wrap;gap:10px;align-items:flex-start;">' +
                        '<div style="flex:1;min-width:220px;position:relative;">' +
                        '<input type="search" class="profile-blackmarket-search" placeholder="Type to search unique legendaries…" autocomplete="off" value="' +
                        escapeHtmlProgressionUi(vis) +
                        '" style="width:100%;box-sizing:border-box;padding:8px;background:rgba(0,0,0,0.5);border:1px solid rgba(79,195,247,0.35);border-radius:4px;color:#81d4fa;font-size:12px;" />' +
                        '<input type="hidden" class="profile-blackmarket-comp-hidden" value="' +
                        escapeHtmlProgressionUi(comp) +
                        '" />' +
                        '<div class="profile-blackmarket-suggest" style="display:none;position:absolute;z-index:30;left:0;right:0;top:100%;max-height:240px;overflow-y:auto;background:#141e24;border:1px solid rgba(79,195,247,0.45);border-radius:4px;margin-top:2px;box-shadow:0 8px 24px rgba(0,0,0,0.45);"></div>' +
                        '</div>' +
                        '<label style="font-size:0.8em;color:#b3e5fc;white-space:nowrap;display:flex;align-items:center;gap:6px;">Game stage ' +
                        '<input type="number" class="profile-blackmarket-gs" min="1" max="100" value="' +
                        escapeHtmlProgressionUi(String(gs)) +
                        '" style="width:68px;padding:6px;background:rgba(0,0,0,0.5);border:1px solid rgba(79,195,247,0.35);border-radius:4px;color:#81d4fa;" />' +
                        '</label>' +
                        '</div></div>'
                    );
                })
                .join('');
            host.innerHTML = html;
        }

        function updateBlackMarketSuggestRow(row, query) {
            const sug = row.querySelector('.profile-blackmarket-suggest');
            if (!sug) return;
            const opts = getLegitBlackMarketOptions();
            const q = (query || '').trim().toLowerCase();
            let list = opts;
            if (q) {
                list = opts.filter(function (o) {
                    const hay =
                        o.searchText ||
                        [o.label, o.value, o.compKey].filter(Boolean).join(' ').toLowerCase();
                    return hay.indexOf(q) >= 0;
                });
            }
            list = list.slice(0, 80);
            if (opts.length === 0) {
                sug.innerHTML =
                    '<div style="padding:10px;color:#ffab91;font-size:12px;line-height:1.4;">No legendary list yet. Load Nexus JSON in the Legit Builder tab (merge), then return here.</div>';
                sug.style.display = 'block';
                return;
            }
            if (list.length === 0) {
                sug.innerHTML =
                    '<div style="padding:8px;color:#888;font-size:12px;">No matches. Try another search.</div>';
                sug.style.display = 'block';
                return;
            }
            sug.innerHTML = list
                .map(function (o) {
                    return (
                        '<div class="profile-blackmarket-suggest-item" role="option" data-comp="' +
                        escapeHtmlProgressionUi(o.value) +
                        '" data-label="' +
                        escapeHtmlProgressionUi(o.label || o.value) +
                        '" style="padding:8px 10px;cursor:pointer;font-size:12px;border-bottom:1px solid rgba(79,195,247,0.12);color:#e0f7fa;line-height:1.35;">' +
                        escapeHtmlProgressionUi(o.label || o.value) +
                        '</div>'
                    );
                })
                .join('');
            sug.style.display = 'block';
        }

        function ensureBlackMarketSlotsDelegation() {
            const host = document.getElementById('profile-blackmarket-slots-host');
            if (!host || host.__bmSlotsDeleg) return;
            host.__bmSlotsDeleg = true;
            host.addEventListener('input', function (e) {
                const inp = e.target.closest('.profile-blackmarket-search');
                if (!inp) return;
                const row = inp.closest('.profile-blackmarket-slot-row');
                if (!row) return;
                const hid = row.querySelector('.profile-blackmarket-comp-hidden');
                const comp = hid && hid.value ? String(hid.value).trim() : '';
                const expected = comp ? blackMarketLabelForComp(comp) : '';
                const typed = inp.value.trim();
                if (hid && comp && typed !== comp && typed !== expected) {
                    hid.value = '';
                }
                updateBlackMarketSuggestRow(row, inp.value);
            });
            host.addEventListener('focusin', function (e) {
                const inp = e.target.closest('.profile-blackmarket-search');
                if (!inp) return;
                const row = inp.closest('.profile-blackmarket-slot-row');
                if (row) updateBlackMarketSuggestRow(row, inp.value);
            });
            host.addEventListener('mousedown', function (e) {
                const pick = e.target.closest('.profile-blackmarket-suggest-item');
                if (!pick) return;
                e.preventDefault();
                const row = pick.closest('.profile-blackmarket-slot-row');
                if (!row) return;
                const comp = pick.getAttribute('data-comp') || '';
                const label = pick.getAttribute('data-label') || comp;
                const inp = row.querySelector('.profile-blackmarket-search');
                const hid = row.querySelector('.profile-blackmarket-comp-hidden');
                if (hid) hid.value = comp;
                if (inp) inp.value = label;
                const sug = row.querySelector('.profile-blackmarket-suggest');
                if (sug) sug.style.display = 'none';
            });
            host.addEventListener('focusout', function (e) {
                const inp = e.target.closest('.profile-blackmarket-search');
                if (!inp) return;
                setTimeout(function () {
                    const row = inp.closest('.profile-blackmarket-slot-row');
                    if (!row) return;
                    const sug = row.querySelector('.profile-blackmarket-suggest');
                    if (!sug || sug.style.display === 'none') return;
                    const ae = document.activeElement;
                    if (ae && sug.contains(ae)) return;
                    sug.style.display = 'none';
                }, 180);
            });
        }

        function ensureBlackMarketApplyListener() {
            const btn = document.getElementById('profile-blackmarket-apply-btn');
            if (!btn || btn.__bmApplyBound) return;
            btn.__bmApplyBound = true;
            btn.addEventListener('click', function () {
                if (typeof window.profileApplyBlackMarketSlotsFromUi !== 'function') {
                    showSaveStatus('profile-blackmarket-status', '❌ Editor helpers not loaded.', false);
                    return;
                }
                const rows = getBlackMarketRowsFromDom();
                const res = window.profileApplyBlackMarketSlotsFromUi(rows);
                if (!res.ok) {
                    showSaveStatus('profile-blackmarket-status', '❌ ' + (res.error || 'Failed'), false);
                    return;
                }
                showSaveStatus(
                    'profile-blackmarket-status',
                    '✅ Updated blackmarket_items (2 slots).',
                    true
                );
                refreshBlackMarketItemsPanel();
            });
        }

        function ensureProfileBlackMarketMonacoListener() {
            const ed = window.profileMonacoEditor;
            if (!ed || typeof ed.onDidChangeModelContent !== 'function') return;
            if (ed.__blackMarketYamlListenerAttached) return;
            ed.__blackMarketYamlListenerAttached = true;
            let debounceTimer = null;
            ed.onDidChangeModelContent(function () {
                const inner = document.getElementById('profile-blackmarket-inner');
                if (!inner || inner.style.display === 'none') return;
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(function () {
                    if (typeof window.refreshBlackMarketItemsPanel === 'function') {
                        window.refreshBlackMarketItemsPanel();
                    }
                }, 450);
            });
        }

        function refreshBlackMarketItemsPanel() {
            if (!window.profileMonacoEditor) return;
            ensureProfileBlackMarketMonacoListener();
            ensureBlackMarketSlotsDelegation();
            ensureBlackMarketApplyListener();

            const BM_SLOT_COUNT = 2;
            let yamlRows = [];
            if (typeof window.loadProfileYamlDataForMassEdit === 'function' && window.profileDataGetBlackMarketItemsArray) {
                const data = window.loadProfileYamlDataForMassEdit();
                if (data) {
                    const raw = window.profileDataGetBlackMarketItemsArray(data);
                    yamlRows = raw.map(function (row) {
                        if (typeof window.profileDataParseBlackMarketRow === 'function') {
                            return window.profileDataParseBlackMarketRow(row);
                        }
                        return { itemcomp: '', itemtype: '', gamestage: 60 };
                    });
                }
            }

            const rows = [];
            for (let i = 0; i < BM_SLOT_COUNT; i++) {
                rows.push(
                    yamlRows[i] || {
                        itemcomp: '',
                        gamestage: 60
                    }
                );
            }
            renderBlackMarketSlotRows(rows);
        }

        window.refreshBlackMarketItemsPanel = refreshBlackMarketItemsPanel;

        if (!window.__legitBlackMarketCompsEventBound) {
            window.__legitBlackMarketCompsEventBound = true;
            window.addEventListener('legit-builder-unique-legendary-comps-updated', function () {
                if (typeof window.refreshBlackMarketItemsPanel === 'function') {
                    window.refreshBlackMarketItemsPanel();
                }
            });
        }

        function bindProfileProgressionEchoInputOnce() {
            const echoInput = document.getElementById('profile-progression-echo-points');
            if (!echoInput || echoInput.__progressionEchoBound) return;
            echoInput.__progressionEchoBound = true;
            echoInput.addEventListener('change', function () {
                applyProfileProgressionSharedGranularFromDom(true);
            });
        }

        function ensureProgressionSharedVaultSduDelegation() {
            const vaultHost = document.getElementById('profile-progression-vault-list');
            if (vaultHost && !vaultHost.__progressionChangeDeleg) {
                vaultHost.__progressionChangeDeleg = true;
                vaultHost.addEventListener('change', function (e) {
                    const t = e.target;
                    if (t && t.classList && t.classList.contains('profile-progression-vault-cb')) {
                        applyProfileProgressionSharedGranularFromDom(true);
                    }
                });
            }
            const sduHost = document.getElementById('profile-progression-sdu-tiers');
            if (sduHost && !sduHost.__progressionChangeDeleg) {
                sduHost.__progressionChangeDeleg = true;
                sduHost.addEventListener('change', function (e) {
                    const t = e.target;
                    if (t && t.classList && t.classList.contains('profile-progression-sdu-tier')) {
                        applyProfileProgressionSharedGranularFromDom(true);
                    }
                });
            }
        }

        ensureProgressionSharedVaultSduDelegation();
        bindProfileProgressionEchoInputOnce();

        function mergeSharedProfileDiscoveryDlblob() {
            if (!window.profileMonacoEditor) {
                showSaveStatus('profile-shared-discovery-status', '❌ Load a profile first.', false);
                return;
            }
            const tokens = window.NEXUS_ALL_DISCOVERY_DLMD;
            if (!Array.isArray(tokens) || tokens.length === 0) {
                showSaveStatus(
                    'profile-shared-discovery-status',
                    '❌ No discovery tokens. Merge Nexus gbx_discovery_location_meta_data in Legit Builder.',
                    false
                );
                return;
            }
            if (typeof window.profileDataMergeNexusDlmdIntoPgShared !== 'function') {
                showSaveStatus('profile-shared-discovery-status', '❌ YAML helpers not loaded.', false);
                return;
            }
            try {
                const data = parseProfileYamlFromMonaco();
                if (!data || typeof data === 'string' || !data.domains || !data.domains.local) {
                    showSaveStatus('profile-shared-discovery-status', '❌ Invalid profile YAML.', false);
                    return;
                }
                ensureProfileYamlLocalShared(data);
                window.profileDataMergeNexusDlmdIntoPgShared(data, tokens);
                window.profileMonacoEditor.setValue(jsyaml.dump(data, { lineWidth: -1, noRefs: true }));
                refreshSharedDiscoveryDlmdCountDisplay();
                showSaveStatus(
                    'profile-shared-discovery-status',
                    '✅ Unlocked all Discovery points (' + tokens.length + ' tokens in gbx_discovery_pg_shared.dlblob).',
                    true
                );
            } catch (e) {
                showSaveStatus('profile-shared-discovery-status', '❌ ' + e.message, false);
            }
        }

        function clearSharedProfileDiscoveryDlblob() {
            if (!window.profileMonacoEditor) {
                showSaveStatus('profile-shared-discovery-status', '❌ Load a profile first.', false);
                return;
            }
            if (typeof window.profileDataClearAllPgSharedDiscoveryDlmd !== 'function') {
                showSaveStatus('profile-shared-discovery-status', '❌ YAML helpers not loaded.', false);
                return;
            }
            try {
                const data = parseProfileYamlFromMonaco();
                if (!data || typeof data === 'string' || !data.domains || !data.domains.local) {
                    showSaveStatus('profile-shared-discovery-status', '❌ Invalid profile YAML.', false);
                    return;
                }
                ensureProfileYamlLocalShared(data);
                window.profileDataClearAllPgSharedDiscoveryDlmd(data);
                window.profileMonacoEditor.setValue(jsyaml.dump(data, { lineWidth: -1, noRefs: true }));
                refreshSharedDiscoveryDlmdCountDisplay();
                showSaveStatus(
                    'profile-shared-discovery-status',
                    '✅ Cleared all discovery points from gbx_discovery_pg_shared.dlblob.',
                    true
                );
            } catch (e) {
                showSaveStatus('profile-shared-discovery-status', '❌ ' + e.message, false);
            }
        }

        function getTokensForDiscoveryCategory(catKey) {
            const groups = window.NEXUS_DISCOVERY_DLMD_GROUPS;
            if (!Array.isArray(groups) || !catKey) return [];
            for (let i = 0; i < groups.length; i++) {
                if (groups[i].key === catKey) return groups[i].tokens || [];
            }
            return [];
        }

        function getProfileDlmdTokenSetFromMonaco() {
            try {
                const data = getParsedProfileDataForProgressionUi();
                if (typeof window.profileDataCollectGbxDiscoveryPgSharedDlmdTokens === 'function') {
                    return window.profileDataCollectGbxDiscoveryPgSharedDlmdTokens(data);
                }
                return new Set();
            } catch (_) {
                return new Set();
            }
        }

        function renderSharedDiscoveryCategories() {
            const host = document.getElementById('profile-shared-discovery-categories-host');
            if (!host) return;
            const groups = window.NEXUS_DISCOVERY_DLMD_GROUPS;
            if (!Array.isArray(groups) || groups.length === 0) {
                host.innerHTML =
                    '<p style="opacity:0.85;font-size:0.85em;margin:0;">Load Nexus <code>gbx_discovery_location_meta_data</code> in Legit Builder to categorize tokens.</p>';
                return;
            }
            const inProfile = getProfileDlmdTokenSetFromMonaco();
            const parts = [];
            for (let i = 0; i < groups.length; i++) {
                const g = groups[i];
                const tokens = g.tokens || [];
                let inCount = 0;
                for (let ti = 0; ti < tokens.length; ti++) {
                    if (inProfile.has(tokens[ti])) inCount++;
                }
                const catKey = g.key;
                const typeName = escapeHtmlProgressionUi(g.label || catKey);
                const previewLines = tokens.slice(0, 60);
                let preview = previewLines.map(function (t) {
                    return escapeHtmlProgressionUi(t);
                }).join('\n');
                if (tokens.length > 60) {
                    preview += '\n… +' + (tokens.length - 60) + ' more';
                }
                parts.push(
                    '<div class="profile-discovery-cat" data-cat="' +
                        escapeHtmlProgressionUi(catKey) +
                        '" style="border:1px solid rgba(79,195,247,0.22);margin-bottom:10px;padding:10px 12px;border-radius:4px;background:rgba(0,0,0,0.2);">' +
                        '<div style="display:flex;flex-wrap:wrap;align-items:center;gap:10px;justify-content:space-between;">' +
                        '<div><strong style="color:#81d4fa;">' +
                        escapeHtmlProgressionUi(g.label || catKey) +
                        '</strong> <span style="opacity:0.85;font-size:0.85em;">Nexus <strong>' +
                        tokens.length +
                        '</strong> · In profile <strong>' +
                        inCount +
                        '</strong></span></div>' +
                        '<div style="display:flex;gap:8px;flex-wrap:wrap;">' +
                        '<button type="button" class="btn btn-primary" onclick="sharedDiscoveryCategoryMerge(\'' +
                        catKey +
                        '\')" style="padding:6px 12px;font-size:0.85em;background:rgba(76,175,80,0.3);border-color:rgba(76,175,80,0.5);color:#81c784;">➕ Add all ' +
                        typeName +
                        ' to profile</button>' +
                        '<button type="button" class="btn btn-secondary" onclick="sharedDiscoveryCategoryRemove(\'' +
                        catKey +
                        '\')" style="padding:6px 12px;font-size:0.85em;">➖ Remove all ' +
                        typeName +
                        ' From profile</button>' +
                        '</div></div>' +
                        '<details style="margin-top:8px;font-size:0.8em;color:#b3e5fc;"><summary style="cursor:pointer;">Token preview (' +
                        tokens.length +
                        ')</summary><pre style="margin:8px 0 0;max-height:160px;overflow:auto;white-space:pre-wrap;word-break:break-all;font-size:0.75em;opacity:0.9;">' +
                        preview +
                        '</pre></details></div>'
                );
            }
            host.innerHTML = parts.length ? parts.join('') : '<p style="opacity:0.85;">No categories.</p>';
        }

        function sharedDiscoveryCategoryMerge(catKey) {
            if (!window.profileMonacoEditor) {
                showSaveStatus('profile-shared-discovery-status', '❌ Load a profile first.', false);
                return;
            }
            const tokens = getTokensForDiscoveryCategory(catKey);
            if (!tokens.length) {
                showSaveStatus(
                    'profile-shared-discovery-status',
                    '❌ No tokens in this category (load Nexus discovery meta in Legit Builder).',
                    false
                );
                return;
            }
            if (typeof window.profileDataMergeNexusDlmdIntoPgShared !== 'function') {
                showSaveStatus('profile-shared-discovery-status', '❌ YAML helpers not loaded.', false);
                return;
            }
            try {
                const data = parseProfileYamlFromMonaco();
                if (!data || typeof data === 'string' || !data.domains || !data.domains.local) {
                    showSaveStatus('profile-shared-discovery-status', '❌ Invalid profile YAML.', false);
                    return;
                }
                ensureProfileYamlLocalShared(data);
                window.profileDataMergeNexusDlmdIntoPgShared(data, tokens);
                window.profileMonacoEditor.setValue(jsyaml.dump(data, { lineWidth: -1, noRefs: true }));
                refreshSharedDiscoveryDlmdCountDisplay();
                showSaveStatus(
                    'profile-shared-discovery-status',
                    '✅ Merged ' + tokens.length + ' token(s) — ' + catKey + '.',
                    true
                );
            } catch (e) {
                showSaveStatus('profile-shared-discovery-status', '❌ ' + e.message, false);
            }
        }

        function sharedDiscoveryCategoryRemove(catKey) {
            if (!window.profileMonacoEditor) {
                showSaveStatus('profile-shared-discovery-status', '❌ Load a profile first.', false);
                return;
            }
            const tokens = getTokensForDiscoveryCategory(catKey);
            if (!tokens.length) {
                showSaveStatus(
                    'profile-shared-discovery-status',
                    '❌ No tokens in this category (load Nexus discovery meta).',
                    false
                );
                return;
            }
            if (typeof window.profileDataRemoveNexusDlmdFromPgShared !== 'function') {
                showSaveStatus('profile-shared-discovery-status', '❌ YAML helpers not loaded.', false);
                return;
            }
            try {
                const data = parseProfileYamlFromMonaco();
                if (!data || typeof data === 'string' || !data.domains || !data.domains.local) {
                    showSaveStatus('profile-shared-discovery-status', '❌ Invalid profile YAML.', false);
                    return;
                }
                ensureProfileYamlLocalShared(data);
                window.profileDataRemoveNexusDlmdFromPgShared(data, tokens);
                window.profileMonacoEditor.setValue(jsyaml.dump(data, { lineWidth: -1, noRefs: true }));
                refreshSharedDiscoveryDlmdCountDisplay();
                showSaveStatus(
                    'profile-shared-discovery-status',
                    '✅ Removed ' + tokens.length + ' token(s) — ' + catKey + '.',
                    true
                );
            } catch (e) {
                showSaveStatus('profile-shared-discovery-status', '❌ ' + e.message, false);
            }
        }

        function refreshSharedDiscoveryDlmdCountDisplay() {
            const el = document.getElementById('profile-shared-dlmd-count');
            const nexusEl = document.getElementById('profile-shared-dlmd-nexus-count');
            if (nexusEl) {
                const n = Array.isArray(window.NEXUS_ALL_DISCOVERY_DLMD) ? window.NEXUS_ALL_DISCOVERY_DLMD.length : 0;
                nexusEl.textContent = String(n);
            }
            if (el) {
                try {
                    const data = getParsedProfileDataForProgressionUi();
                    if (
                        data &&
                        typeof window.profileDataCollectGbxDiscoveryPgSharedDlmdTokens === 'function'
                    ) {
                        const s = window.profileDataCollectGbxDiscoveryPgSharedDlmdTokens(data);
                        el.textContent = String(s.size);
                    } else {
                        el.textContent = '—';
                    }
                } catch (_) {
                    el.textContent = '—';
                }
            }
            renderSharedDiscoveryCategories();
        }

        window.addEventListener('nexus-discovery-dlmd-updated', function () {
            refreshSharedDiscoveryDlmdCountDisplay();
        });

        window.addEventListener('nexus-discovery-worlds-updated', function () {
            if (typeof refreshProfilePcSharedFoddatasPanel === 'function') {
                refreshProfilePcSharedFoddatasPanel();
            }
        });

        function ensureProfilePcSharedMonacoContentListener() {
            const ed = window.profileMonacoEditor;
            if (!ed || typeof ed.onDidChangeModelContent !== 'function') return;
            if (ed.__pcSharedFogYamlListenerAttached) return;
            ed.__pcSharedFogYamlListenerAttached = true;
            let debounceTimer = null;
            ed.onDidChangeModelContent(function () {
                const inner = document.getElementById('shared-pc-shared-inner');
                if (!inner || inner.style.display === 'none') return;
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(function () {
                    if (typeof refreshProfilePcSharedFoddatasPanel === 'function') {
                        refreshProfilePcSharedFoddatasPanel();
                    }
                }, 450);
            });
        }

        function ensureProfilePcSharedFogClickDelegation() {
            const panel = document.getElementById('shared-pc-shared-inner');
            if (!panel || panel.__pcFogClickBound) return;
            panel.__pcFogClickBound = true;
            panel.addEventListener('click', function (ev) {
                const t = ev.target.closest('[data-pc-fog-action]');
                if (!t || !panel.contains(t)) return;
                const action = t.getAttribute('data-pc-fog-action');
                const enc = t.getAttribute('data-levelname') || '';
                let levelname = '';
                try {
                    levelname = decodeURIComponent(enc);
                } catch (err) {
                    return;
                }
                if (!action || !levelname) return;
                if (
                    !window.profileMonacoEditor ||
                    typeof window.profileDataSetPcSharedLevelFoddataMode !== 'function' ||
                    typeof window.profileDataAddPcSharedFoddatasRow !== 'function'
                ) {
                    return;
                }
                try {
                    const data = parseProfileYamlFromMonaco();
                    if (!data || !data.domains || !data.domains.local) {
                        showSaveStatus('profile-pc-shared-status', '❌ Invalid profile.', false);
                        return;
                    }
                    ensureProfileYamlLocalShared(data);
                    let res;
                    if (action === 'add-placeholder') {
                        res = window.profileDataAddPcSharedFoddatasRow(data, levelname, 'placeholder');
                    } else if (action === 'add-empty') {
                        res = window.profileDataAddPcSharedFoddatasRow(data, levelname, 'empty');
                    } else if (action === 'mode-placeholder') {
                        res = window.profileDataSetPcSharedLevelFoddataMode(data, levelname, 'placeholder');
                    } else if (action === 'mode-empty') {
                        res = window.profileDataSetPcSharedLevelFoddataMode(data, levelname, 'empty');
                    } else {
                        return;
                    }
                    if (!res || !res.ok) {
                        showSaveStatus(
                            'profile-pc-shared-status',
                            '❌ ' + ((res && res.error) || 'Update failed'),
                            false
                        );
                        return;
                    }
                    window.profileMonacoEditor.setValue(jsyaml.dump(data, { lineWidth: -1, noRefs: true }));
                    refreshProfilePcSharedFoddatasPanel();
                    showSaveStatus('profile-pc-shared-status', '✅ Updated fog row for ' + levelname + '.', true);
                } catch (e) {
                    showSaveStatus('profile-pc-shared-status', '❌ ' + e.message, false);
                }
            });
        }

        function refreshProfilePcSharedFoddatasPanel() {
            const host = document.getElementById('profile-pc-shared-foddatas-host');
            const missingHost = document.getElementById('profile-pc-shared-foddatas-missing-host');
            if (!host) return;
            ensureProfilePcSharedMonacoContentListener();
            ensureProfilePcSharedFogClickDelegation();
            if (!window.profileMonacoEditor) {
                host.innerHTML =
                    '<span style="opacity:0.85;font-size:0.9em;">Load a profile to edit per-level fog.</span>';
                if (missingHost) missingHost.innerHTML = '';
                return;
            }
            if (
                typeof window.profileDataGetOrCreateGbxDiscoveryPcSharedOnLocalDomain !== 'function' ||
                typeof window.classifyPcSharedFoddataRow !== 'function'
            ) {
                host.innerHTML =
                    '<span style="opacity:0.85;font-size:0.9em;">PC shared fog helpers not loaded.</span>';
                if (missingHost) missingHost.innerHTML = '';
                return;
            }
            const data = getParsedProfileDataForProgressionUi();
            if (!data || !data.domains || !data.domains.local) {
                host.innerHTML =
                    '<span style="opacity:0.85;font-size:0.9em;">Could not parse profile YAML.</span>';
                if (missingHost) missingHost.innerHTML = '';
                return;
            }
            window.profileDataGetOrCreateGbxDiscoveryPcSharedOnLocalDomain(data);
            const pc = data.domains.local.gbx_discovery_pc_shared;
            let rows = Array.isArray(pc && pc.foddatas)
                ? pc.foddatas.filter(function (r) {
                      return r && r.levelname;
                  })
                : [];
            rows = rows.slice().sort(function (a, b) {
                return String(a.levelname).localeCompare(String(b.levelname));
            });
            const statusLabel = {
                placeholder: 'Full clear map',
                empty: 'Reset map fog',
                custom: 'Custom / from save'
            };
            const rowStyle =
                'display:flex;flex-wrap:wrap;align-items:center;gap:10px;padding:10px 8px;border-bottom:1px solid rgba(79,195,247,0.15);font-size:0.88em;';
            const btnStyle =
                'padding:6px 10px;background:rgba(0,0,0,0.45);border:1px solid rgba(79,195,247,0.35);border-radius:4px;color:#81d4fa;cursor:pointer;font-size:0.85em;';
            let html = '';
            if (rows.length === 0) {
                html =
                    '<span style="opacity:0.85;font-size:0.9em;">No <code>foddatas</code> rows yet. Add a missing world from Nexus below, or paste-merge YAML.</span>';
            } else {
                html = rows
                    .map(function (row) {
                        const ln = String(row.levelname);
                        const enc = encodeURIComponent(ln);
                        const cls = window.classifyPcSharedFoddataRow(row);
                        const st = statusLabel[cls] || statusLabel.custom;
                        return (
                            '<div class="profile-pc-fog-row" style="' +
                            rowStyle +
                            '">' +
                            '<span style="min-width:140px;font-weight:600;color:#b3e5fc;">' +
                            escapeHtmlProgressionUi(ln) +
                            '</span>' +
                            '<span style="opacity:0.9;flex:1;min-width:160px;">' +
                            escapeHtmlProgressionUi(st) +
                            '</span>' +
                            '<button type="button" data-pc-fog-action="mode-placeholder" data-levelname="' +
                            enc +
                            '" style="' +
                            btnStyle +
                            '" title="Minimal zlib stub; not real discovered fog from a save.">Clear all map fog</button>' +
                            '<button type="button" data-pc-fog-action="mode-empty" data-levelname="' +
                            enc +
                            '" style="' +
                            btnStyle +
                            '" title="Removes zlib blob; game uses default or undiscovered behavior.">Reset map fog</button>' +
                            '</div>'
                        );
                    })
                    .join('');
            }
            host.innerHTML = html;
            if (missingHost) {
                const profileSet = new Set();
                for (let i = 0; i < rows.length; i++) {
                    if (rows[i].levelname) profileSet.add(rows[i].levelname);
                }
                const nexus = Array.isArray(window.NEXUS_DISCOVERY_WORLD_MAP_NAMES)
                    ? window.NEXUS_DISCOVERY_WORLD_MAP_NAMES
                    : [];
                const missing = nexus.filter(function (n) {
                    return n && !profileSet.has(n);
                });
                if (missing.length === 0) {
                    missingHost.innerHTML =
                        '<span style="opacity:0.8;font-size:0.88em;">No Nexus worlds missing from this profile (or discovery meta not loaded).</span>';
                } else {
                    missingHost.innerHTML =
                        '<div style="font-size:0.82em;opacity:0.9;margin-bottom:8px;">Worlds in Nexus location meta not present in <code>foddatas</code>:</div>' +
                        missing
                            .map(function (name) {
                                const enc = encodeURIComponent(name);
                                return (
                                    '<div class="profile-pc-fog-missing-row" style="' +
                                    rowStyle +
                                    '">' +
                                    '<span style="min-width:140px;font-weight:600;color:#ffe082;">' +
                                    escapeHtmlProgressionUi(name) +
                                    '</span>' +
                                    '<button type="button" data-pc-fog-action="add-placeholder" data-levelname="' +
                                    enc +
                                    '" style="' +
                                    btnStyle +
                                    '">Add row (full clear map)</button>' +
                                    '<button type="button" data-pc-fog-action="add-empty" data-levelname="' +
                                    enc +
                                    '" style="' +
                                    btnStyle +
                                    '">Add row (reset map fog)</button>' +
                                    '</div>'
                                );
                            })
                            .join('');
                }
            }
        }

        window.refreshProfilePcSharedFoddatasPanel = refreshProfilePcSharedFoddatasPanel;

        function applyProfilePcSharedClearMapFogAllLevels() {
            if (!window.profileMonacoEditor || typeof window.profileDataSetFullClearMapFogOnAllPcSharedLevels !== 'function') {
                return;
            }
            try {
                const data = parseProfileYamlFromMonaco();
                if (!data || !data.domains || !data.domains.local) {
                    showSaveStatus('profile-pc-shared-status', '❌ Invalid profile.', false);
                    return;
                }
                ensureProfileYamlLocalShared(data);
                const res = window.profileDataSetFullClearMapFogOnAllPcSharedLevels(data);
                if (!res.ok) {
                    showSaveStatus('profile-pc-shared-status', '❌ ' + (res.error || 'Failed'), false);
                    return;
                }
                window.profileMonacoEditor.setValue(jsyaml.dump(data, { lineWidth: -1, noRefs: true }));
                if (typeof refreshProfilePcSharedFoddatasPanel === 'function') {
                    refreshProfilePcSharedFoddatasPanel();
                }
                showSaveStatus(
                    'profile-pc-shared-status',
                    '✅ Full clear map on ' + (res.count || 0) + ' level(s).',
                    true
                );
            } catch (e) {
                showSaveStatus('profile-pc-shared-status', '❌ ' + e.message, false);
            }
        }

        function applyProfilePcSharedResetFogAllLevels() {
            if (!window.profileMonacoEditor || typeof window.profileDataClearFogOnAllPcSharedLevels !== 'function') {
                return;
            }
            try {
                const data = parseProfileYamlFromMonaco();
                if (!data || !data.domains || !data.domains.local) {
                    showSaveStatus('profile-pc-shared-status', '❌ Invalid profile.', false);
                    return;
                }
                ensureProfileYamlLocalShared(data);
                const res = window.profileDataClearFogOnAllPcSharedLevels(data);
                if (!res.ok) {
                    showSaveStatus('profile-pc-shared-status', '❌ ' + (res.error || 'Failed'), false);
                    return;
                }
                window.profileMonacoEditor.setValue(jsyaml.dump(data, { lineWidth: -1, noRefs: true }));
                if (typeof refreshProfilePcSharedFoddatasPanel === 'function') {
                    refreshProfilePcSharedFoddatasPanel();
                }
                showSaveStatus(
                    'profile-pc-shared-status',
                    '✅ Reset map fog on ' + (res.count || 0) + ' level(s) (empty foddata).',
                    true
                );
            } catch (e) {
                showSaveStatus('profile-pc-shared-status', '❌ ' + e.message, false);
            }
        }

        function applyProfilePcSharedPasteMerge() {
            if (!window.profileMonacoEditor || typeof window.profileDataMergePcSharedFromYamlFragment !== 'function') return;
            const ta = document.getElementById('profile-pc-shared-paste');
            const text = ta && ta.value ? ta.value.trim() : '';
            if (!text) {
                showSaveStatus('profile-pc-shared-status', '❌ Paste a YAML fragment with gbx_discovery_pc_shared.', false);
                return;
            }
            try {
                const data = parseProfileYamlFromMonaco();
                if (!data || !data.domains || !data.domains.local) {
                    showSaveStatus('profile-pc-shared-status', '❌ Invalid profile.', false);
                    return;
                }
                ensureProfileYamlLocalShared(data);
                const res = window.profileDataMergePcSharedFromYamlFragment(data, text);
                if (!res.ok) {
                    showSaveStatus('profile-pc-shared-status', '❌ ' + (res.error || 'Merge failed'), false);
                    return;
                }
                window.profileMonacoEditor.setValue(jsyaml.dump(data, { lineWidth: -1, noRefs: true }));
                if (typeof refreshProfilePcSharedFoddatasPanel === 'function') {
                    refreshProfilePcSharedFoddatasPanel();
                }
                showSaveStatus('profile-pc-shared-status', '✅ Merged pasted gbx_discovery_pc_shared into domains.local.', true);
            } catch (e) {
                showSaveStatus('profile-pc-shared-status', '❌ ' + e.message, false);
            }
        }

        function applyProfileProgressionSharedPreset() {
            if (!window.profileMonacoEditor || typeof window.profileDataApplyProgressionSharedPreset !== 'function') return;
            const input = document.getElementById('profile-progression-echo-points');
            const raw = input && input.value !== '' ? input.value : null;
            loadProgressionSharedManifest()
                .then(manifest => {
                    try {
                        const data = parseProfileYamlFromMonaco();
                        if (!data || !data.domains || !data.domains.local) {
                            showSaveStatus('profile-progression-shared-status', '❌ Invalid profile.', false);
                            return;
                        }
                        ensureProfileYamlLocalShared(data);
                        const res = window.profileDataApplyProgressionSharedPreset(data, manifest, raw);
                        if (!res.ok) {
                            showSaveStatus('profile-progression-shared-status', '❌ ' + (res.error || 'Failed'), false);
                            return;
                        }
                        window.profileMonacoEditor.setValue(jsyaml.dump(data, { lineWidth: -1, noRefs: true }));
                        showSaveStatus(
                            'profile-progression-shared-status',
                            '✅ Applied progression_shared (max SDU + vault from manifest, echo points as set).',
                            true
                        );
                        if (typeof refreshProgressionSharedPanel === 'function') {
                            refreshProgressionSharedPanel();
                        }
                    } catch (e) {
                        showSaveStatus('profile-progression-shared-status', '❌ ' + e.message, false);
                    }
                })
                .catch(e => showSaveStatus('profile-progression-shared-status', '❌ Manifest: ' + e.message, false));
        }

        // Helper function to get unlockable section from cosmetic key
        function getUnlockableSection(cosmeticKey) {
            if (cosmeticKey.startsWith('Unlockable_DarkSiren.')) return 'unlockable_darksiren';
            if (cosmeticKey.startsWith('Unlockable_ExoSoldier.')) return 'unlockable_exosoldier';
            if (cosmeticKey.startsWith('Unlockable_Gravitar.')) return 'unlockable_gravitar';
            if (cosmeticKey.startsWith('Unlockable_Paladin.')) return 'unlockable_paladin';
            if (cosmeticKey.startsWith('Unlockable_RoboDealer.')) return 'unlockable_robodealer';
            if (cosmeticKey.startsWith('Unlockable_Echo4.')) return 'unlockable_echo4';
            if (cosmeticKey.startsWith('Unlockable_Weapons.')) return 'unlockable_weapons';
            if (cosmeticKey.startsWith('Unlockable_Vehicles.')) return 'unlockable_vehicles';
            if (cosmeticKey.startsWith('Unlockable_HoverDrives.')) return 'unlockable_hoverdrives';
            return null;
        }

        // Helper function to map cosmetic ID to pips_list entry
        function getPipsListEntry(cosmeticKey) {
            if (cosmeticKey.startsWith('Unlockable_Echo4.Attachment')) {
                return cosmeticKey.replace('Unlockable_Echo4.', 'profile.echo4customization.Cosmetics_Echo4_Attachment.');
            } else if (cosmeticKey.startsWith('Unlockable_Echo4.Skin')) {
                return cosmeticKey.replace('Unlockable_Echo4.', 'profile.echo4customization.Cosmetics_Echo4_Skin.');
            } else if (cosmeticKey.startsWith('Unlockable_Weapons.')) {
                return 'profile.weaponcustomization.' + cosmeticKey;
            } else if (cosmeticKey.startsWith('Unlockable_Vehicles.')) {
                return cosmeticKey.replace('Unlockable_Vehicles.', 'profile.vehiclecustomization.Cosmetics_Vehicle.');
            }
            return null;
        }

        // Helper function to add cosmetic to unlockables structure
        function addCosmeticToUnlockables(data, cosmeticKey) {
            if (!data.domains || !data.domains.local) {
                return false;
            }
            
            // Ensure unlockables structure exists - CORRECT PATH: domains.local.unlockables
            if (!data.domains.local.unlockables) {
                data.domains.local.unlockables = {};
            }
            
            const section = getUnlockableSection(cosmeticKey);
            if (!section) {
                // Fallback: use cosmetics object for unknown types
                if (!data.domains.local.shared) {
                    data.domains.local.shared = {};
                }
                if (!data.domains.local.shared.cosmetics) {
                    data.domains.local.shared.cosmetics = {};
                }
                data.domains.local.shared.cosmetics[cosmeticKey] = true;
                return true;
            }
            
            // Add to unlockables entries
            if (!data.domains.local.unlockables[section]) {
                data.domains.local.unlockables[section] = { entries: [] };
            }
            
            if (!data.domains.local.unlockables[section].entries) {
                data.domains.local.unlockables[section].entries = [];
            }
            
            // Add if not already present
            if (!data.domains.local.unlockables[section].entries.includes(cosmeticKey)) {
                data.domains.local.unlockables[section].entries.push(cosmeticKey);
            }
            
            // Also add to vaultcard_purchases if it's a DLC cosmetic (holiday/seasonal + vault card 2)
            const isDlcCosmetic = cosmeticKey.includes('Head21_Reindeeer') || 
                                 cosmeticKey.includes('Head26_Giftbox') || 
                                 cosmeticKey.includes('Head27_Nutcracker') || 
                                 cosmeticKey.includes('Head28_Krampus') ||
                                 cosmeticKey.includes('Head29_Kalamari') || 
                                 cosmeticKey.includes('Head30_Lizard') || 
                                 cosmeticKey.includes('Head31_TinHead') || 
                                 cosmeticKey.includes('Head32_PowerHelmet') ||
                                 cosmeticKey.includes('Skin46_') || 
                                 cosmeticKey.includes('Skin47_') || 
                                 cosmeticKey.includes('Skin48_') || 
                                 cosmeticKey.includes('Skin49_') ||
                                 cosmeticKey.includes('Skin57_') || 
                                 cosmeticKey.includes('Skin58_') || 
                                 cosmeticKey.includes('Skin59_') || 
                                 cosmeticKey.includes('Skin60_') ||
                                 cosmeticKey.includes('Attachment14_') || 
                                 cosmeticKey.includes('Attachment15_') ||
                                 (cosmeticKey.includes('Unlockable_Echo4.Attachment16') || cosmeticKey.includes('Unlockable_Echo4.Attachment17')) ||
                                 cosmeticKey.includes('Mat41_') || 
                                 cosmeticKey.includes('Mat42_') || 
                                 cosmeticKey.includes('Mat43_') || 
                                 cosmeticKey.includes('Mat44_') || 
                                 cosmeticKey.includes('Mat45_') ||
                                 cosmeticKey.includes('Mat46_') || 
                                 cosmeticKey.includes('Mat47_') || 
                                 cosmeticKey.includes('Mat48_') || 
                                 cosmeticKey.includes('Mat49_') || 
                                 cosmeticKey.includes('Mat50_') ||
                                 cosmeticKey.includes('Mat53_') || 
                                 cosmeticKey.includes('Mat54_') || 
                                 cosmeticKey.includes('Mat55_') || 
                                 cosmeticKey.includes('Mat56_') || 
                                 cosmeticKey.includes('Mat57_') ||
                                 cosmeticKey.includes('Unlockable_Vehicles.Mat58') || 
                                 cosmeticKey.includes('Unlockable_Vehicles.Mat59') || 
                                 cosmeticKey.includes('Unlockable_Vehicles.Mat60') || 
                                 cosmeticKey.includes('Unlockable_Vehicles.Mat61') || 
                                 cosmeticKey.includes('Unlockable_Vehicles.Mat62');
            
            if (isDlcCosmetic) {
                const vcp = getOrCreateVaultcardPurchases(data);
                if (!vcp.includes(cosmeticKey)) {
                    vcp.push(cosmeticKey);
                }
            }
            
            // Also add to pips_list for certain cosmetics
            const pipsEntry = getPipsListEntry(cosmeticKey);
            if (pipsEntry) {
                if (!data.pips) data.pips = {};
                if (!data.pips.pips_list) data.pips.pips_list = [];
                
                if (!data.pips.pips_list.includes(pipsEntry)) {
                    data.pips.pips_list.push(pipsEntry);
                }
            }
            
            return true;
        }

        // Helper function to remove cosmetic from unlockables structure
        function removeCosmeticFromUnlockables(data, cosmeticKey) {
            if (!data.domains || !data.domains.local) {
                return false;
            }
            
            let removed = false;
            
            const section = getUnlockableSection(cosmeticKey);
            // CORRECT PATH: domains.local.unlockables (not shared.unlockables)
            if (section && data.domains.local.unlockables && 
                data.domains.local.unlockables[section] && 
                data.domains.local.unlockables[section].entries) {
                const entries = data.domains.local.unlockables[section].entries;
                const index = entries.indexOf(cosmeticKey);
                if (index !== -1) {
                    entries.splice(index, 1);
                    removed = true;
                }
            }
            
            // Remove from vaultcard_purchases
            const vcp = getVaultcardPurchases(data);
            if (vcp && Array.isArray(vcp)) {
                const vcpIndex = vcp.indexOf(cosmeticKey);
                if (vcpIndex !== -1) {
                    vcp.splice(vcpIndex, 1);
                    removed = true;
                }
            }
            
            // Remove from pips_list
            const pipsEntry = getPipsListEntry(cosmeticKey);
            if (pipsEntry && data.pips && data.pips.pips_list && Array.isArray(data.pips.pips_list)) {
                const pipsIndex = data.pips.pips_list.indexOf(pipsEntry);
                if (pipsIndex !== -1) {
                    data.pips.pips_list.splice(pipsIndex, 1);
                    removed = true;
                }
            }
            
            // Fallback: remove from cosmetics object
            if (data.domains.local.shared && 
                data.domains.local.shared.cosmetics && 
                data.domains.local.shared.cosmetics[cosmeticKey]) {
                delete data.domains.local.shared.cosmetics[cosmeticKey];
                removed = true;
            }
            
            return removed;
        }

        // Helper function to get vaultcard_purchases array from either YAML structure
        function getVaultcardPurchases(data) {
            // Try nested structure first: data.oak.ui.dlc_data.ui_dlc_data.vaultcard_purchases
            if (data.oak && data.oak.ui && data.oak.ui.dlc_data && 
                data.oak.ui.dlc_data.ui_dlc_data && 
                data.oak.ui.dlc_data.ui_dlc_data.vaultcard_purchases) {
                return data.oak.ui.dlc_data.ui_dlc_data.vaultcard_purchases;
            }
            // Try flat structure: data['oak.ui.dlc_data'].ui_dlc_data.vaultcard_purchases
            if (data['oak.ui.dlc_data'] && data['oak.ui.dlc_data'].ui_dlc_data && 
                data['oak.ui.dlc_data'].ui_dlc_data.vaultcard_purchases) {
                return data['oak.ui.dlc_data'].ui_dlc_data.vaultcard_purchases;
            }
            return null;
        }
        
        // Helper function to get or create vaultcard_purchases array (returns the array and the parent object)
        function getOrCreateVaultcardPurchases(data) {
            // Try nested structure first
            if (data.oak) {
                if (!data.oak.ui) data.oak.ui = {};
                if (!data.oak.ui.dlc_data) data.oak.ui.dlc_data = {};
                if (!data.oak.ui.dlc_data.ui_dlc_data) data.oak.ui.dlc_data.ui_dlc_data = {};
                if (!data.oak.ui.dlc_data.ui_dlc_data.vaultcard_purchases) {
                    data.oak.ui.dlc_data.ui_dlc_data.vaultcard_purchases = [];
                }
                return data.oak.ui.dlc_data.ui_dlc_data.vaultcard_purchases;
            }
            // Try flat structure
            if (!data['oak.ui.dlc_data']) data['oak.ui.dlc_data'] = {};
            if (!data['oak.ui.dlc_data'].ui_dlc_data) data['oak.ui.dlc_data'].ui_dlc_data = {};
            if (!data['oak.ui.dlc_data'].ui_dlc_data.vaultcard_purchases) {
                data['oak.ui.dlc_data'].ui_dlc_data.vaultcard_purchases = [];
            }
            return data['oak.ui.dlc_data'].ui_dlc_data.vaultcard_purchases;
        }
        
        // Helper function to clear vaultcard_purchases in both structures
        function clearVaultcardPurchases(data) {
            // Clear nested structure
            if (data.oak && data.oak.ui && data.oak.ui.dlc_data && 
                data.oak.ui.dlc_data.ui_dlc_data) {
                data.oak.ui.dlc_data.ui_dlc_data.vaultcard_purchases = [];
            }
            // Clear flat structure
            if (data['oak.ui.dlc_data'] && data['oak.ui.dlc_data'].ui_dlc_data) {
                data['oak.ui.dlc_data'].ui_dlc_data.vaultcard_purchases = [];
            }
            // Ensure nested structure exists and is cleared (for new entries)
            if (!data.oak) data.oak = {};
            if (!data.oak.ui) data.oak.ui = {};
            if (!data.oak.ui.dlc_data) data.oak.ui.dlc_data = {};
            if (!data.oak.ui.dlc_data.ui_dlc_data) data.oak.ui.dlc_data.ui_dlc_data = {};
            data.oak.ui.dlc_data.ui_dlc_data.vaultcard_purchases = [];
        }
        
        // Helper function to get all cosmetics from unlockables structure with source tracking
        function getAllCosmeticsFromUnlockables(data) {
            const cosmetics = {};
            const cosmeticsBySource = {
                unlockables: {},
                vaultcard_purchases: {},
                pips_list: {},
                shared_cosmetics: {}
            };
            
            if (!data.domains || !data.domains.local) {
                return { cosmetics, cosmeticsBySource };
            }
            
            // Get from cosmetics object if it exists (fallback)
            if (data.domains.local.shared && data.domains.local.shared.cosmetics) {
                Object.entries(data.domains.local.shared.cosmetics).forEach(([key, value]) => {
                    cosmetics[key] = { source: 'shared_cosmetics' };
                    cosmeticsBySource.shared_cosmetics[key] = true;
                });
            }
            
            // Get from unlockables structure - CORRECT PATH: domains.local.unlockables (not shared.unlockables)
            if (data.domains.local.unlockables) {
                const unlockableSections = [
                    'unlockable_darksiren', 'unlockable_exosoldier', 'unlockable_gravitar',
                    'unlockable_paladin', 'unlockable_robodealer', 'unlockable_echo4', 'unlockable_weapons', 'unlockable_vehicles',
                    'unlockable_hoverdrives'
                ];
                
                unlockableSections.forEach(section => {
                    if (data.domains.local.unlockables[section] && 
                        data.domains.local.unlockables[section].entries && 
                        Array.isArray(data.domains.local.unlockables[section].entries)) {
                        data.domains.local.unlockables[section].entries.forEach(entry => {
                            if (entry && typeof entry === 'string') {
                                cosmetics[entry] = { source: 'unlockables', section: section };
                                if (!cosmeticsBySource.unlockables[section]) {
                                    cosmeticsBySource.unlockables[section] = {};
                                }
                                cosmeticsBySource.unlockables[section][entry] = true;
                            }
                        });
                    }
                });
            }
            
            // Get from vaultcard_purchases (DLC cosmetics)
            const vcp = getVaultcardPurchases(data);
            if (vcp && Array.isArray(vcp)) {
                vcp.forEach(entry => {
                    if (entry && typeof entry === 'string' && entry.startsWith('Unlockable_')) {
                        cosmetics[entry] = { source: 'vaultcard_purchases' };
                        cosmeticsBySource.vaultcard_purchases[entry] = true;
                    }
                });
            }
            
            // Get from pips_list (profile unlocks that map to cosmetics)
            if (data.pips && data.pips.pips_list && Array.isArray(data.pips.pips_list)) {
                data.pips.pips_list.forEach(entry => {
                    if (entry && typeof entry === 'string') {
                        let cosmeticId = null;
                        // Map pips_list entries to cosmetic IDs
                        if (entry.includes('Cosmetics_Echo4_Attachment.')) {
                            cosmeticId = entry.replace('profile.echo4customization.Cosmetics_Echo4_Attachment.', 'Unlockable_Echo4.');
                        } else if (entry.includes('Cosmetics_Echo4_Skin.')) {
                            cosmeticId = entry.replace('profile.echo4customization.Cosmetics_Echo4_Skin.', 'Unlockable_Echo4.');
                        } else if (entry.includes('Unlockable_Weapons.')) {
                            cosmeticId = entry.replace('profile.weaponcustomization.', '');
                        } else if (entry.includes('Cosmetics_Vehicle.')) {
                            cosmeticId = entry.replace('profile.vehiclecustomization.Cosmetics_Vehicle.', 'Unlockable_Vehicles.');
                        }
                        
                        if (cosmeticId) {
                            cosmetics[cosmeticId] = { source: 'pips_list' };
                            cosmeticsBySource.pips_list[cosmeticId] = true;
                        }
                    }
                });
            }
            
            return { cosmetics, cosmeticsBySource };
        }

        function populateCosmeticsDropdown(cosmetics) {
            const select = document.getElementById('cosmetic-select');
            if (!select) return;
            
            // Clear existing options except the first one
            while (select.options.length > 1) {
                select.remove(1);
            }
            
            // Get list of already unlocked cosmetics
            const unlockedCosmetics = new Set(Object.keys(cosmetics || {}));
            const nexusList = getNexusCosmeticsList();

            if (nexusList.length === 0) {
                const option = document.createElement('option');
                option.value = '';
                option.textContent = 'Load Legit Builder Nexus data (Nexus-Data-Resident*.json) first';
                option.disabled = true;
                select.appendChild(option);
                return;
            }

            const availableCosmetics = nexusList.filter(cosmeticKey => !unlockedCosmetics.has(cosmeticKey));

            availableCosmetics.forEach(cosmeticKey => {
                const option = document.createElement('option');
                option.value = cosmeticKey;
                option.textContent = cosmeticKey;
                select.appendChild(option);
            });

            if (availableCosmetics.length === 0) {
                const option = document.createElement('option');
                option.value = '';
                option.textContent = 'All cosmetics are already unlocked';
                option.disabled = true;
                select.appendChild(option);
            }
        }

        function renderCosmetics(cosmetics, cosmeticsBySource) {
            const container = document.getElementById('cosmetics-items-container');
            const countEl = document.getElementById('cosmetics-items-count');
            if (!container) return;
            
            container.innerHTML = '';
            const cosmeticEntries = Object.entries(cosmetics || {});
            
            console.log('Rendering cosmetics:', cosmeticEntries.length, 'entries');
            
            if (countEl) {
                countEl.textContent = `(${cosmeticEntries.length} unlocked)`;
            }
            
            // Populate dropdown with cosmetics
            populateCosmeticsDropdown(cosmetics);
            
            // Group cosmetics by unlockable section
            const sectionGroups = {
                'unlockable_darksiren': { label: 'Dark Siren', items: [] },
                'unlockable_exosoldier': { label: 'ExoSoldier', items: [] },
                'unlockable_gravitar': { label: 'Gravitar', items: [] },
                'unlockable_paladin': { label: 'Paladin', items: [] },
                'unlockable_robodealer': { label: 'RoboDealer', items: [] },
                'unlockable_echo4': { label: 'Echo4', items: [] },
                'unlockable_weapons': { label: 'Weapons', items: [] },
                'unlockable_vehicles': { label: 'Vehicles', items: [] },
                'unlockable_hoverdrives': { label: 'Hover drives', items: [] },
                'other': { label: 'Other', items: [] }
            };
            
            // Group cosmetics by section
            cosmeticEntries.forEach(([cosmeticKey, cosmeticValue]) => {
                const section = getUnlockableSection(cosmeticKey);
                if (section && sectionGroups[section]) {
                    sectionGroups[section].items.push(cosmeticKey);
                } else {
                    sectionGroups.other.items.push(cosmeticKey);
                    console.log('Uncategorized cosmetic:', cosmeticKey, 'section:', section);
                }
            });
            
            console.log('Section groups:', Object.entries(sectionGroups).map(([k, v]) => `${k}: ${v.items.length}`).join(', '));
            
            // Render each section in order
            const sectionOrder = [
                'unlockable_darksiren', 'unlockable_exosoldier', 'unlockable_gravitar',
                'unlockable_paladin', 'unlockable_robodealer', 'unlockable_echo4', 'unlockable_weapons',
                'unlockable_vehicles', 'unlockable_hoverdrives', 'other'
            ];
            
            sectionOrder.forEach(sectionKey => {
                const sectionData = sectionGroups[sectionKey];
                if (!sectionData || sectionData.items.length === 0) return; // Skip empty sections
                
                // Section header
                const sectionHeader = document.createElement('div');
                sectionHeader.style.cssText = 'margin-top: var(--section-gap-bottom); margin-bottom: var(--input-pad-y); padding: var(--input-pad-y) var(--input-pad-x); background: rgba(79, 195, 247, 0.2); border-left: 3px solid rgba(79, 195, 247, 0.6); border-radius: 4px;';
                sectionHeader.innerHTML = `<h4 style="margin: 0; color: #81d4fa; font-size: var(--panel-title-size); font-weight: 600;">${sectionData.label} <span style="font-weight: normal; opacity: 0.8; font-size: 0.88em;">(${sectionData.items.length})</span></h4>`;
                container.appendChild(sectionHeader);
                
                // Section items
                sectionData.items.forEach(cosmeticKey => {
                    const cosmeticDiv = document.createElement('div');
                    cosmeticDiv.style.cssText = 'padding: var(--input-pad-y) var(--input-pad-x); background: rgba(79, 195, 247, 0.1); border: 1px solid rgba(79, 195, 247, 0.3); border-radius: 6px; display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--input-pad-y);';
                    
                    // Escape quotes properly for onclick
                    const escapedKey = cosmeticKey.replace(/'/g, "\\'").replace(/"/g, '&quot;');
                    
                    cosmeticDiv.innerHTML = `
                        <div style="color: #81d4fa; font-weight: 500; font-size: 0.95em;">${cosmeticKey}</div>
                        <button 
                            onclick="removeCosmetic('${escapedKey}')" 
                            style="padding: 4px 8px; background: rgba(255, 100, 100, 0.3); border: 1px solid rgba(255, 100, 100, 0.5); border-radius: 4px; color: #ff6b6b; cursor: pointer; font-size: 0.85em;"
                        >
                            Remove
                        </button>
                    `;
                    
                    container.appendChild(cosmeticDiv);
                });
            });
            
            // Show message if no cosmetics
            if (cosmeticEntries.length === 0) {
                const emptyMsg = document.createElement('div');
                emptyMsg.style.cssText = 'padding: var(--panel-pad); text-align: center; color: rgba(129, 212, 250, 0.6); font-style: italic; font-size: 0.9em;';
                emptyMsg.textContent = 'No cosmetics unlocked yet. Use "Add All" or select individual cosmetics to unlock them.';
                container.appendChild(emptyMsg);
            }
        }

        function addSelectedCosmetic() {
            const select = document.getElementById('cosmetic-select');
            if (!select || !select.value) {
                showSaveStatus('cosmetics-items-status', '❌ Please select a cosmetic.', false);
                return;
            }
            
            addCosmeticToProfile(select.value);
        }

        function addManualCosmetic() {
            const input = document.getElementById('cosmetic-manual-input');
            if (!input || !input.value.trim()) {
                showSaveStatus('cosmetics-items-status', '❌ Please enter a cosmetic ID.', false);
                return;
            }
            
            const cosmeticKey = input.value.trim();
            addCosmeticToProfile(cosmeticKey);
            input.value = '';
        }

        function addCosmeticToProfile(cosmeticKey) {
            if (!window.profileMonacoEditor) {
                showSaveStatus('cosmetics-items-status', '❌ Please decrypt a profile file first.', false);
                return;
            }
            
            if (!cosmeticKey) {
                showSaveStatus('cosmetics-items-status', '❌ Please provide a cosmetic ID.', false);
                return;
            }
            
            try {
                const yamlContent = window.profileMonacoEditor.getValue();
                // Clean YAML before parsing
                let cleanedYaml = yamlContent.replace(/:\s*!tags/g, ':');
                cleanedYaml = cleanedYaml.replace(/:\s*!<[^>]+>/g, ':');
                
                let data;
                try {
                    data = jsyaml.load(cleanedYaml);
                } catch (parseError) {
                    cleanedYaml = cleanedYaml.replace(/!<[^>]+>/g, '');
                    data = jsyaml.load(cleanedYaml);
                }
                
                if (!data || typeof data === 'string' || !data.domains || !data.domains.local || !data.domains.local.shared) {
                    showSaveStatus('cosmetics-items-status', '❌ Invalid profile data.', false);
                    return;
                }
                
                addCosmeticToUnlockables(data, cosmeticKey);
                
                const newYaml = jsyaml.dump(data, { lineWidth: -1, noRefs: true });
                window.profileMonacoEditor.setValue(newYaml);
                
                const result = getAllCosmeticsFromUnlockables(data);
                renderCosmetics(result.cosmetics, result.cosmeticsBySource);
                showSaveStatus('cosmetics-items-status', `✅ Cosmetic "${cosmeticKey}" added!`, true);
            } catch (error) {
                console.error('Error adding cosmetic:', error);
                showSaveStatus('cosmetics-items-status', `❌ Error: ${error.message}`, false);
            }
        }

        function addAllCosmetics() {
            if (!window.profileMonacoEditor) {
                showSaveStatus('cosmetics-items-status', '❌ Please decrypt a profile file first.', false);
                return;
            }
            
            try {
                const yamlContent = window.profileMonacoEditor.getValue();
                // Clean YAML before parsing
                let cleanedYaml = yamlContent.replace(/:\s*!tags/g, ':');
                cleanedYaml = cleanedYaml.replace(/:\s*!<[^>]+>/g, ':');
                
                let data;
                try {
                    data = jsyaml.load(cleanedYaml);
                } catch (parseError) {
                    cleanedYaml = cleanedYaml.replace(/!<[^>]+>/g, '');
                    data = jsyaml.load(cleanedYaml);
                }
                
                if (!data || typeof data === 'string' || !data.domains || !data.domains.local || !data.domains.local.shared) {
                    showSaveStatus('cosmetics-items-status', '❌ Invalid profile data.', false);
                    return;
                }
                
                const nexusCosmetics = getNexusCosmeticsList();
                if (nexusCosmetics.length === 0) {
                    showSaveStatus(
                        'cosmetics-items-status',
                        '❌ No cosmetics catalog loaded. Load Nexus-Data-Resident*.json via Legit Builder (auto-load or folder pick).',
                        false
                    );
                    return;
                }
                nexusCosmetics.forEach(cosmeticKey => {
                    addCosmeticToUnlockables(data, cosmeticKey);
                });
                
                const newYaml = jsyaml.dump(data, { lineWidth: -1, noRefs: true });
                window.profileMonacoEditor.setValue(newYaml);
                
                const result = getAllCosmeticsFromUnlockables(data);
                renderCosmetics(result.cosmetics, result.cosmeticsBySource);
                showSaveStatus('cosmetics-items-status', `✅ All ${nexusCosmetics.length} cosmetics added!`, true);
            } catch (error) {
                console.error('Error adding all cosmetics:', error);
                showSaveStatus('cosmetics-items-status', `❌ Error: ${error.message}`, false);
            }
        }

        function removeAllCosmetics() {
            if (!window.profileMonacoEditor) {
                showSaveStatus('cosmetics-items-status', '❌ Please decrypt a profile file first.', false);
                return;
            }
            
            if (!confirm('Are you sure you want to remove all cosmetics?')) {
                return;
            }
            
            try {
                const yamlContent = window.profileMonacoEditor.getValue();
                // Clean YAML before parsing
                let cleanedYaml = yamlContent.replace(/:\s*!tags/g, ':');
                cleanedYaml = cleanedYaml.replace(/:\s*!<[^>]+>/g, ':');
                
                let data;
                try {
                    data = jsyaml.load(cleanedYaml);
                } catch (parseError) {
                    cleanedYaml = cleanedYaml.replace(/!<[^>]+>/g, '');
                    data = jsyaml.load(cleanedYaml);
                }
                
                if (!data || typeof data === 'string' || !data.domains || !data.domains.local || !data.domains.local.shared) {
                    showSaveStatus('cosmetics-items-status', '❌ Invalid profile data.', false);
                    return;
                }
                
                // Clear cosmetics object (fallback)
                if (data.domains.local.shared && data.domains.local.shared.cosmetics) {
                    data.domains.local.shared.cosmetics = {};
                }
                
                // Clear all unlockables entries - CORRECT PATH: domains.local.unlockables
                if (data.domains.local.unlockables) {
                    const unlockableSections = [
                        'unlockable_darksiren', 'unlockable_exosoldier', 'unlockable_gravitar',
                        'unlockable_paladin', 'unlockable_robodealer', 'unlockable_echo4', 'unlockable_weapons', 'unlockable_vehicles',
                        'unlockable_hoverdrives'
                    ];
                    
                    unlockableSections.forEach(section => {
                        if (data.domains.local.unlockables[section] && 
                            data.domains.local.unlockables[section].entries) {
                            data.domains.local.unlockables[section].entries = [];
                        }
                    });
                }
                
                // Clear vaultcard_purchases - handle both possible YAML structures
                clearVaultcardPurchases(data);
                
                // Clear pips_list (but keep non-cosmetic entries like profile.DLC.preorder)
                if (data.pips && data.pips.pips_list && Array.isArray(data.pips.pips_list)) {
                    data.pips.pips_list = data.pips.pips_list.filter(entry => {
                        // Keep non-cosmetic entries
                        return !entry.includes('Cosmetics_') && 
                               !entry.includes('Unlockable_') &&
                               !entry.includes('weaponcustomization') &&
                               !entry.includes('vehiclecustomization') &&
                               !entry.includes('echo4customization');
                    });
                }
                
                const newYaml = jsyaml.dump(data, { lineWidth: -1, noRefs: true });
                window.profileMonacoEditor.setValue(newYaml);
                
                renderCosmetics({}, {});
                showSaveStatus('cosmetics-items-status', '✅ All cosmetics removed!', true);
            } catch (error) {
                console.error('Error removing all cosmetics:', error);
                showSaveStatus('cosmetics-items-status', `❌ Error: ${error.message}`, false);
            }
        }

        function removeCosmetic(cosmeticKey) {
            if (!window.profileMonacoEditor) return;
            
            try {
                const yamlContent = window.profileMonacoEditor.getValue();
                // Clean YAML before parsing
                let cleanedYaml = yamlContent.replace(/:\s*!tags/g, ':');
                cleanedYaml = cleanedYaml.replace(/:\s*!<[^>]+>/g, ':');
                
                let data;
                try {
                    data = jsyaml.load(cleanedYaml);
                } catch (parseError) {
                    cleanedYaml = cleanedYaml.replace(/!<[^>]+>/g, '');
                    data = jsyaml.load(cleanedYaml);
                }
                
                if (!data || typeof data === 'string' || !data.domains || !data.domains.local || !data.domains.local.shared) {
                    return;
                }
                
                removeCosmeticFromUnlockables(data, cosmeticKey);
                
                const newYaml = jsyaml.dump(data, { lineWidth: -1, noRefs: true });
                window.profileMonacoEditor.setValue(newYaml);
                
                const result = getAllCosmeticsFromUnlockables(data);
                renderCosmetics(result.cosmetics, result.cosmeticsBySource);
            } catch (error) {
                console.error('Error removing cosmetic:', error);
            }
        }

        // Currency Management Functions
        function renderCurrencies(data) {
            if (!data || typeof data === 'string') return;
            
            // Check if this is a profile save with the correct structure
            if (!data.domains || !data.domains.local || !data.domains.local.shared) {
                return;
            }
            
            const shared = data.domains.local.shared;
            
            // Initialize currencies structure if it doesn't exist
            if (!shared.currencies) {
                shared.currencies = {};
            }
            if (!shared.experience) {
                shared.experience = [];
            }
            
            // Get Vault Card 1 tokens and experience
            const tokens = shared.currencies.vaultcard01_tokens || 0;
            let vaultCardExp = shared.experience.find(exp => exp.type === 'VaultCard01_Experience');
            if (!vaultCardExp) {
                vaultCardExp = { type: 'VaultCard01_Experience', level: 1, points: 0 };
                shared.experience.push(vaultCardExp);
            }
            const level = vaultCardExp.level || 1;
            const points = vaultCardExp.points || 0;
            
            // Get Vault Card 2 tokens and experience
            const tokens02 = shared.currencies.vaultcard02_tokens || 0;
            let vaultCard02Exp = shared.experience.find(exp => exp.type === 'VaultCard02_Experience');
            if (!vaultCard02Exp) {
                vaultCard02Exp = { type: 'VaultCard02_Experience', level: 1, points: 0 };
                shared.experience.push(vaultCard02Exp);
            }
            const level02 = vaultCard02Exp.level || 1;
            const points02 = vaultCard02Exp.points || 0;

            // Get Vault Card 3 tokens and experience
            const tokens03 = shared.currencies.vaultcard03_tokens || 0;
            let vaultCard03Exp = shared.experience.find(exp => exp.type === 'VaultCard03_Experience');
            if (!vaultCard03Exp) {
                vaultCard03Exp = { type: 'VaultCard03_Experience', level: 1, points: 0 };
                shared.experience.push(vaultCard03Exp);
            }
            const level03 = vaultCard03Exp.level || 1;
            const points03 = vaultCard03Exp.points || 0;
            
            // Update input fields
            const tokensInput = document.getElementById('vaultcard-tokens-input');
            const levelInput = document.getElementById('vaultcard-level-input');
            const pointsInput = document.getElementById('vaultcard-points-input');
            if (tokensInput) tokensInput.value = tokens;
            if (levelInput) levelInput.value = level;
            if (pointsInput) pointsInput.value = points;
            
            const tokens02Input = document.getElementById('vaultcard02-tokens-input');
            const level02Input = document.getElementById('vaultcard02-level-input');
            const points02Input = document.getElementById('vaultcard02-points-input');
            if (tokens02Input) tokens02Input.value = tokens02;
            if (level02Input) level02Input.value = level02;
            if (points02Input) points02Input.value = points02;

            const tokens03Input = document.getElementById('vaultcard03-tokens-input');
            const level03Input = document.getElementById('vaultcard03-level-input');
            const points03Input = document.getElementById('vaultcard03-points-input');
            if (tokens03Input) tokens03Input.value = tokens03;
            if (level03Input) level03Input.value = level03;
            if (points03Input) points03Input.value = points03;
        }

        function updateVaultCardLevel() {
            const levelInput = document.getElementById('vaultcard-level-input');
            if (!levelInput) return;
            
            const level = parseInt(levelInput.value, 10);
            if (isNaN(level) || level < 1) {
                showSaveStatus('currencies-items-status', '❌ Level must be at least 1.', false);
                return;
            }
            
            // Calculate experience points based on level using specialization XP curve
            const points = calculateSpecializationXp(level);
            
            // Update points input
            const pointsInput = document.getElementById('vaultcard-points-input');
            if (pointsInput) {
                pointsInput.value = points;
            }
            
            // Update YAML
            updateCurrencies();
        }

        function updateVaultCard02Level() {
            const levelInput = document.getElementById('vaultcard02-level-input');
            if (!levelInput) return;
            
            const level = parseInt(levelInput.value, 10);
            if (isNaN(level) || level < 1) {
                showSaveStatus('currencies-items-status', '❌ Level must be at least 1.', false);
                return;
            }
            
            const points = calculateSpecializationXp(level);
            const pointsInput = document.getElementById('vaultcard02-points-input');
            if (pointsInput) {
                pointsInput.value = points;
            }
            updateCurrencies();
        }

        function updateVaultCard03Level() {
            const levelInput = document.getElementById('vaultcard03-level-input');
            if (!levelInput) return;

            const level = parseInt(levelInput.value, 10);
            if (isNaN(level) || level < 1) {
                showSaveStatus('currencies-items-status', '❌ Level must be at least 1.', false);
                return;
            }

            const points = calculateSpecializationXp(level);
            const pointsInput = document.getElementById('vaultcard03-points-input');
            if (pointsInput) {
                pointsInput.value = points;
            }
            updateCurrencies();
        }

        function updateCurrencies() {
            if (!window.profileMonacoEditor) {
                showSaveStatus('currencies-items-status', '❌ Please decrypt a profile file first.', false);
                return;
            }
            
            try {
                const tokensInput = document.getElementById('vaultcard-tokens-input');
                const levelInput = document.getElementById('vaultcard-level-input');
                const pointsInput = document.getElementById('vaultcard-points-input');
                const tokens02Input = document.getElementById('vaultcard02-tokens-input');
                const level02Input = document.getElementById('vaultcard02-level-input');
                const points02Input = document.getElementById('vaultcard02-points-input');
                const tokens03Input = document.getElementById('vaultcard03-tokens-input');
                const level03Input = document.getElementById('vaultcard03-level-input');
                const points03Input = document.getElementById('vaultcard03-points-input');
                
                if (!tokensInput || !levelInput || !pointsInput) return;
                
                const tokens = parseInt(tokensInput.value, 10) || 0;
                const level = parseInt(levelInput.value, 10) || 1;
                const points = parseInt(pointsInput.value, 10) || 0;
                const tokens02 = tokens02Input ? (parseInt(tokens02Input.value, 10) || 0) : 0;
                const level02 = level02Input ? (parseInt(level02Input.value, 10) || 1) : 1;
                const points02 = points02Input ? (parseInt(points02Input.value, 10) || 0) : 0;
                const tokens03 = tokens03Input ? (parseInt(tokens03Input.value, 10) || 0) : 0;
                const level03 = level03Input ? (parseInt(level03Input.value, 10) || 1) : 1;
                const points03 = points03Input ? (parseInt(points03Input.value, 10) || 0) : 0;
                
                const yamlContent = window.profileMonacoEditor.getValue();
                // Clean YAML before parsing
                let cleanedYaml = yamlContent.replace(/:\s*!tags/g, ':');
                cleanedYaml = cleanedYaml.replace(/:\s*!<[^>]+>/g, ':');
                
                let data;
                try {
                    data = jsyaml.load(cleanedYaml);
                } catch (parseError) {
                    cleanedYaml = cleanedYaml.replace(/!<[^>]+>/g, '');
                    data = jsyaml.load(cleanedYaml);
                }
                
                if (!data || typeof data === 'string' || !data.domains || !data.domains.local || !data.domains.local.shared) {
                    showSaveStatus('currencies-items-status', '❌ Invalid profile data.', false);
                    return;
                }
                
                const shared = data.domains.local.shared;
                
                // Initialize currencies if needed
                if (!shared.currencies) {
                    shared.currencies = {};
                }
                if (!shared.experience) {
                    shared.experience = [];
                }
                
                // Update tokens
                shared.currencies.vaultcard01_tokens = tokens;
                shared.currencies.vaultcard02_tokens = tokens02;
                shared.currencies.vaultcard03_tokens = tokens03;
                
                // Update or create Vault Card 1 experience entry
                let vaultCardExp = shared.experience.find(exp => exp.type === 'VaultCard01_Experience');
                if (!vaultCardExp) {
                    vaultCardExp = { type: 'VaultCard01_Experience', level: level, points: points };
                    shared.experience.push(vaultCardExp);
                } else {
                    vaultCardExp.level = level;
                    vaultCardExp.points = points;
                }
                
                // Update or create Vault Card 2 experience entry
                let vaultCard02Exp = shared.experience.find(exp => exp.type === 'VaultCard02_Experience');
                if (!vaultCard02Exp) {
                    vaultCard02Exp = { type: 'VaultCard02_Experience', level: level02, points: points02 };
                    shared.experience.push(vaultCard02Exp);
                } else {
                    vaultCard02Exp.level = level02;
                    vaultCard02Exp.points = points02;
                }

                // Update or create Vault Card 3 experience entry
                let vaultCard03Exp = shared.experience.find(exp => exp.type === 'VaultCard03_Experience');
                if (!vaultCard03Exp) {
                    vaultCard03Exp = { type: 'VaultCard03_Experience', level: level03, points: points03 };
                    shared.experience.push(vaultCard03Exp);
                } else {
                    vaultCard03Exp.level = level03;
                    vaultCard03Exp.points = points03;
                }
                
                const newYaml = jsyaml.dump(data, { lineWidth: -1, noRefs: true });
                window.profileMonacoEditor.setValue(newYaml);
                
                showSaveStatus('currencies-items-status', '✅ Currencies updated!', true);
            } catch (error) {
                console.error('Error updating currencies:', error);
                showSaveStatus('currencies-items-status', `❌ Error: ${error.message}`, false);
            }
        }

        async function overwriteExistingSave() {
            // Prevent double execution - check if already processing
            if (window.saveEditorState.isProcessing) {
                showSaveStatus('save-encrypt-status', '❌ Cannot overwrite while a process is running. Please wait for the current operation to complete.', false);
                return;
            }
            
            // Show confirmation prompt about backing up saves
            const confirmed = confirm(
                '⚠️ IMPORTANT: We recommend backing up your save file before making any edits.\n\n' +
                'This will overwrite your existing save file. Are you sure you want to continue?'
            );
            
            if (!confirmed) {
                return; // User cancelled
            }
            
            // Double-check processing state after confirmation (in case state changed during confirmation)
            if (window.saveEditorState.isProcessing) {
                showSaveStatus('save-encrypt-status', '❌ Cannot overwrite while a process is running. Please wait for the current operation to complete.', false);
                return;
            }
            
            const steamIdInput = document.getElementById('save-steamid');
            const yamlTextarea = document.getElementById('save-yaml-textarea');
            const statusEl = document.getElementById('save-encrypt-status');
            
            const steamId = steamIdInput.value.trim();
            if (!steamId) {
                showSaveStatus('save-encrypt-status', '❌ Please enter your Steam ID or Epic ID first.', false);
                return;
            }
            
            const yamlContent = getYamlTextareaValue().trim();
            if (!yamlContent) {
                showSaveStatus('save-encrypt-status', '❌ No YAML content to encrypt.', false);
                return;
            }
            
            if (!window.saveEditorState.originalFileName) {
                showSaveStatus('save-encrypt-status', '❌ No original file selected. Please decrypt a save file first.', false);
                return;
            }
            
            // Set processing state
            setSaveProcessingState(true, 'Overwriting save file');
            
            try {
                showSaveStatus('save-encrypt-status', '⏳ Encrypting and overwriting save file...', true);
                
                // Encrypt the YAML content (same as encryptSaveFile)
                const requestBody = {
                    command: 'encrypt',
                    steamid: steamId,
                    yaml_content: yamlContent,
                    yaml_data: yamlContent
                };
                
                const response = await fetch(getSaveApiBaseUrl(), {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(requestBody)
                });
                
                if (!response.ok) {
                    const errorText = await response.text();
                    throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
                }
                
                const contentType = response.headers.get('content-type');
                let data;
                
                if (contentType && contentType.includes('application/json')) {
                    data = await response.json();
                } else {
                    const text = await response.text();
                    try {
                        data = JSON.parse(text);
                    } catch (e) {
                        throw new Error(`Invalid response format. Expected JSON but got: ${contentType || 'unknown'}. Response: ${text.substring(0, 200)}`);
                    }
                }
                
                const encryptedData = data.encrypted || data.encrypted_data || data.sav_data || data.data;
                
                if (data.success && encryptedData) {
                    // Convert base64 to blob
                    const binaryString = atob(encryptedData);
                    const bytes = new Uint8Array(binaryString.length);
                    for (let i = 0; i < binaryString.length; i++) {
                        bytes[i] = binaryString.charCodeAt(i);
                    }
                    const blob = new Blob([bytes], { type: 'application/octet-stream' });
                    
                    // Validate blob has content before proceeding
                    if (!blob || blob.size === 0) {
                        throw new Error('Encrypted data is empty. Please try again.');
                    }
                    
                    // Track if we've successfully written the file to prevent double writes
                    let fileWritten = false;
                    
                    // Check if we're in Electron - use native dialog instead of File System Access API
                    const isElectron = window.IS_ELECTRON_APP === true || (window.electronAPI && window.electronAPI.isElectron && window.electronAPI.isElectron());
                    
                    // In Electron, ALWAYS use native dialog to avoid double-dialog issues
                    if (isElectron && window.electronAPI && window.electronAPI.showSaveDialog && !fileWritten) {
                        // Use Electron's native save dialog
                        try {
                            // Double-check blob is ready and has content
                            if (!blob || blob.size === 0) {
                                throw new Error('Blob is empty, cannot save file');
                            }
                            
                            // Convert blob to ArrayBuffer for Electron
                            const arrayBuffer = await blob.arrayBuffer();
                            const buffer = Array.from(new Uint8Array(arrayBuffer));
                            
                            // Always use .sav extension when encrypting
                            let defaultPath = window.saveEditorState.originalFileName || 'save_encrypted.sav';
                            // Replace .yaml/.yml with .sav extension
                            if (defaultPath.toLowerCase().endsWith('.yaml') || defaultPath.toLowerCase().endsWith('.yml')) {
                                defaultPath = defaultPath.replace(/\.(yaml|yml)$/i, '.sav');
                            } else if (!defaultPath.toLowerCase().endsWith('.sav')) {
                                // If no extension or different extension, add .sav
                                defaultPath = defaultPath.replace(/\.[^.]*$/, '') + '.sav';
                            }
                            
                            // Show Electron's native save dialog
                            const result = await window.electronAPI.showSaveDialog({
                                title: 'Save Bl4 Save File',
                                defaultPath: defaultPath,
                                filters: [
                                    { name: 'Bl4 Save Files', extensions: ['sav'] },
                                    { name: 'All Files', extensions: ['*'] }
                                ]
                            });
                            
                            if (!result.canceled && result.filePath) {
                                // Write file using Electron's file system
                                const writeResult = await window.electronAPI.writeFile(result.filePath, buffer);
                                
                                if (writeResult.success) {
                                    fileWritten = true;
                                    showSaveStatus('save-encrypt-status', '✅ Save file encrypted and saved successfully!', true);
                                    return; // Explicit return to prevent fallthrough
                                } else {
                                    throw new Error(writeResult.error || 'Failed to write file');
                                }
                            } else {
                                // User cancelled
                                showSaveStatus('save-encrypt-status', '❌ Save cancelled.', false);
                                return;
                            }
                        } catch (error) {
                            console.warn('Failed to save using Electron native dialog, falling back to download:', error);
                            fileWritten = false;
                        }
                    }
                    
                    // Try to use original file handle first (if file was selected via File System Access API)
                    // This will overwrite the file in the same location without showing a dialog
                    // Only in non-Electron environments
                    if (!isElectron && window.saveEditorState.originalFileHandle && !fileWritten) {
                        try {
                            // Double-check blob is ready and has content
                            if (!blob || blob.size === 0) {
                                throw new Error('Blob is empty, cannot write file');
                            }
                            
                            const writable = await window.saveEditorState.originalFileHandle.createWritable();
                            // Ensure blob is fully ready before writing - write the blob directly
                            await writable.write(blob);
                            await writable.close();
                            
                            // Verify the write completed successfully by checking blob size was written
                            if (blob.size > 0) {
                                fileWritten = true;
                                showSaveStatus('save-encrypt-status', '✅ Save file encrypted and overwritten successfully!', true);
                                return; // Explicit return to prevent fallthrough
                            } else {
                                throw new Error('File write completed but blob was empty');
                            }
                        } catch (error) {
                            console.warn('Failed to write using original file handle, trying save dialog:', error);
                            // Clear the handle if it's invalid so we don't try again
                            if (error.name === 'NotFoundError' || error.name === 'InvalidStateError') {
                                window.saveEditorState.originalFileHandle = null;
                            }
                            // Reset fileWritten flag if write failed
                            fileWritten = false;
                            // Continue to showSaveFilePicker as fallback
                        }
                    }
                    
                    // Try to use File System Access API if available (modern browsers, non-Electron)
                    // Only if we haven't already written the file
                    if (!isElectron && 'showSaveFilePicker' in window && !fileWritten) {
                        try {
                            // Double-check blob is ready and has content before showing dialog
                            if (!blob || blob.size === 0) {
                                throw new Error('Blob is empty, cannot save file');
                            }
                            
                            const fileHandle = await window.showSaveFilePicker({
                                suggestedName: window.saveEditorState.originalFileName,
                                types: [{
                                    description: 'Bl4 Save File',
                                    accept: { 'application/octet-stream': ['.sav'] }
                                }]
                            });
                            
                            // Re-validate blob before writing (in case something changed)
                            if (!blob || blob.size === 0) {
                                throw new Error('Blob became empty before write');
                            }
                            
                            const writable = await fileHandle.createWritable();
                            // Ensure blob is fully ready before writing
                            await writable.write(blob);
                            await writable.close();
                            
                            // Verify the write completed successfully
                            if (blob.size > 0) {
                                fileWritten = true;
                                
                                // Store the file handle and directory handle for future overwrites
                                window.saveEditorState.originalFileHandle = fileHandle;
                                try {
                                    const directoryHandle = await fileHandle.getParent();
                                    if (directoryHandle) {
                                        window.saveEditorState.originalDirectoryHandle = directoryHandle;
                                    }
                                } catch (dirError) {
                                    // Directory handle is optional, continue anyway
                                }
                                
                                showSaveStatus('save-encrypt-status', '✅ Save file encrypted and saved successfully!', true);
                                return; // Explicit return to prevent fallthrough
                            } else {
                                throw new Error('File write completed but blob was empty');
                            }
                        } catch (error) {
                            // User cancelled or error occurred, fall back to download
                            if (error.name !== 'AbortError') {
                                console.warn('Failed to save using File System Access API, falling back to download:', error);
                            }
                            // If user cancelled, don't fall through to download
                            if (error.name === 'AbortError') {
                                showSaveStatus('save-encrypt-status', '❌ Save cancelled.', false);
                                return;
                            }
                            // Reset fileWritten flag if write failed
                            fileWritten = false;
                        }
                    }
                    
                    // Fallback: Download with .sav extension
                    let fileName = window.saveEditorState.originalFileName || 'save_encrypted.sav';
                    // Replace .yaml/.yml with .sav extension
                    if (fileName.toLowerCase().endsWith('.yaml') || fileName.toLowerCase().endsWith('.yml')) {
                        fileName = fileName.replace(/\.(yaml|yml)$/i, '.sav');
                    } else if (!fileName.toLowerCase().endsWith('.sav')) {
                        // If no extension or different extension, add .sav
                        fileName = fileName.replace(/\.[^.]*$/, '') + '.sav';
                    }
                    
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = fileName;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                    
                    showSaveStatus('save-encrypt-status', `✅ Save file encrypted and downloaded as "${fileName}"! Replace your original file with this one.`, true);
                } else {
                    const errorMsg = data.error || data.message || data.reason || 
                        `API returned success: ${data.success}, encrypted data present: ${!!encryptedData}. Check console for full response.`;
                    throw new Error(errorMsg || 'Failed to encrypt save file');
                }
            } catch (error) {
                console.error('Overwrite error:', error);
                showSaveStatus('save-encrypt-status', `❌ Error: ${error.message}`, false);
            } finally {
                // Clear processing state
                setSaveProcessingState(false);
            }
        }

        function showSaveStatus(elementId, message, isSuccess) {
            const statusEl = document.getElementById(elementId);
            if (!statusEl) return;
            
            statusEl.style.display = 'block';
            statusEl.style.background = isSuccess 
                ? 'rgba(76, 175, 80, 0.2)' 
                : 'rgba(244, 67, 54, 0.2)';
            statusEl.style.border = isSuccess 
                ? '2px solid rgba(76, 175, 80, 0.5)' 
                : '2px solid rgba(244, 67, 54, 0.5)';
            statusEl.style.color = isSuccess ? '#4caf50' : '#f44336';
            
            // Support HTML messages (check if message contains HTML tags)
            if (message.includes('<') && message.includes('>')) {
                statusEl.innerHTML = message;
            } else {
                statusEl.textContent = message;
            }
        }

        // ===== PRESET SYSTEM =====
        /**
         * Defines available preset modifications for save files.
         * Each preset contains:
         * - handler: Function name to execute
         * - title: Display name in UI
         * - desc: Detailed description of the modification
         * - saveType: Whether it applies to 'character' or 'profile' saves
         * - group: UI grouping category
         */
        const PRESETS = [
            {
                handler: 'setCharacterLevelPrompt',
                title: 'Set Character Level',
                desc: 'Sets character level to a specified value (1-60).',
                saveType: 'character',
                group: 'Character',
            },
            {
                handler: 'setSpecializationLevelPrompt',
                title: 'Set Specialization Level',
                desc: 'Sets specialization level to a specified value (1-701).',
                saveType: 'character',
                group: 'Character',
            },
            {
                handler: 'showChangeClassPopup',
                title: 'Change Character Class',
                desc: 'Changes character class (select from list).',
                saveType: 'character',
                group: 'Character',
            },
            {
                handler: 'setCashPrompt',
                title: 'Set Cash',
                desc: 'Sets cash currency to a specified value.',
                saveType: 'character',
                group: 'Character',
            },
            {
                handler: 'setEridiumPrompt',
                title: 'Set Eridium',
                desc: 'Sets eridium currency to a specified value.',
                saveType: 'character',
                group: 'Character',
            },
            {
                handler: 'setAssaultRifleAmmoPrompt',
                title: 'Set Assault Rifle Ammo',
                desc: 'Sets assault rifle ammo to a specified value.',
                saveType: 'character',
                group: 'Character',
            },
            {
                handler: 'setPistolAmmoPrompt',
                title: 'Set Pistol Ammo',
                desc: 'Sets pistol ammo to a specified value.',
                saveType: 'character',
                group: 'Character',
            },
            {
                handler: 'setShotgunAmmoPrompt',
                title: 'Set Shotgun Ammo',
                desc: 'Sets shotgun ammo to a specified value.',
                saveType: 'character',
                group: 'Character',
            },
            {
                handler: 'setSMGAmmoPrompt',
                title: 'Set SMG Ammo',
                desc: 'Sets SMG ammo to a specified value.',
                saveType: 'character',
                group: 'Character',
            },
            {
                handler: 'setSniperAmmoPrompt',
                title: 'Set Sniper Ammo',
                desc: 'Sets sniper ammo to a specified value.',
                saveType: 'character',
                group: 'Character',
            },
            {
                handler: 'unlockAllSpecialization',
                title: 'Unlock All Specializations',
                desc: 'Unlocks the specialization system and all skills.',
                saveType: 'character',
                group: 'Character',
            },
            {
                handler: 'resetSpecializations',
                title: 'Reset Specializations',
                desc: 'Removes all specialization data (opposite of Unlock All Specializations).',
                saveType: 'character',
                group: 'Reset',
            },
            {
                handler: 'unlockPostgame',
                title: 'Unlock UVHM / Postgame',
                desc: 'Sets flags to unlock UVH mode and post-game activities.',
                saveType: 'character',
                group: 'Character',
            },
            {
                handler: 'completeAllChallenges',
                title: 'Complete All Challenges',
                desc: "Completes all challenges (doesn't grant rewards).",
                saveType: 'character',
                group: 'World',
            },
            {
                handler: 'completeAllAchievements',
                title: 'Complete All Achievements',
                desc: 'Completes all achievements.',
                saveType: 'character',
                group: 'World',
            },
            {
                handler: 'completeAllStoryMissions',
                title: 'Skip Story Missions',
                desc: 'Completes all main story missions.',
                saveType: 'character',
                group: 'World',
            },
            {
                handler: 'completeAllMissions',
                title: 'Skip All Missions',
                desc: 'Completes all main and side missions (including activities).',
                saveType: 'character',
                group: 'World',
            },
            {
                handler: 'resetAllMissions',
                title: 'Reset All Missions',
                desc: 'Removes all mission data from the save (opposite of Skip All Missions).',
                saveType: 'character',
                group: 'Reset',
            },
            {
                handler: 'resetAllMissionsSkipPrologue',
                title: 'Reset All Missions (Skip Prologue)',
                desc: 'Removes all mission data but keeps the prison prologue mission completed.',
                saveType: 'character',
                group: 'Reset',
            },
            {
                handler: 'resetChallenges',
                title: 'Reset Challenges',
                desc: 'Removes all challenge data from the save (opposite of Complete All Challenges).',
                saveType: 'character',
                group: 'Reset',
            },
            {
                handler: 'resetEverything',
                title: 'Reset Everything',
                desc: 'Resets challenges, missions (optional prologue keep), and specializations.',
                saveType: 'character',
                group: 'Reset',
            },
            {
                handler: 'unlockMaxEverything',
                title: 'Unlock / Max Everything',
                desc: 'Runs a sequence of presets: ammo, currency, missions, postgame, specializations, challenges, and max character level.',
                saveType: 'character',
                group: 'Misc',
            },
        ];

        /**
         * Helper function to get YAML data from textarea
         */
        // Monaco Editor instance for YAML editing
        window.window.yamlMonacoEditor = null;
        
        // Helper function to get YAML text (works with Monaco or textarea)
        function getYamlTextareaValue() {
            const yamlTextarea = document.getElementById('save-yaml-textarea');
            if (!yamlTextarea) {
                return window.saveEditorState && typeof window.saveEditorState.yamlContent === 'string'
                    ? window.saveEditorState.yamlContent
                    : '';
            }
            
            if (window.yamlMonacoEditor) {
                return window.yamlMonacoEditor.getValue();
            } else if (yamlTextarea.tagName === 'TEXTAREA') {
                return yamlTextarea.value;
            } else if (
                yamlTextarea.dataset &&
                yamlTextarea.dataset.msbtYamlFallback === '1' &&
                typeof yamlTextarea.textContent === 'string'
            ) {
                return yamlTextarea.textContent;
            } else if (yamlTextarea.dataset && typeof yamlTextarea.dataset.value === 'string') {
                return yamlTextarea.dataset.value;
            } else if (window.saveEditorState && typeof window.saveEditorState.yamlContent === 'string') {
                return window.saveEditorState.yamlContent;
            }
            return '';
        }
        
        // Helper function to set YAML text (works with Monaco or textarea)
        function setYamlTextareaValue(value) {
            const yamlTextarea = document.getElementById('save-yaml-textarea');
            const normalizedValue = value || '';

            if (window.saveEditorState) {
                window.saveEditorState.yamlContent = normalizedValue;
            }

            if (!yamlTextarea) return;
            
            if (window.yamlMonacoEditor) {
                window.yamlMonacoEditor.setValue(normalizedValue);
            } else if (yamlTextarea.tagName === 'TEXTAREA') {
                yamlTextarea.value = normalizedValue;
                yamlTextarea.dispatchEvent(new Event('input', { bubbles: true }));
            } else if (yamlTextarea.dataset) {
                yamlTextarea.dataset.value = normalizedValue;
                if (!window.yamlMonacoEditor) {
                    yamlTextarea.dataset.msbtYamlFallback = '1';
                    yamlTextarea.textContent = normalizedValue;
                    yamlTextarea.style.whiteSpace = 'pre';
                    yamlTextarea.style.overflow = 'auto';
                    yamlTextarea.style.fontFamily = 'Consolas, "Courier New", monospace';
                    yamlTextarea.style.fontSize = '12px';
                    yamlTextarea.style.lineHeight = '1.35';
                    yamlTextarea.style.padding = '12px';
                    yamlTextarea.contentEditable = 'true';

                    if (yamlTextarea.dataset.msbtYamlInputBound !== '1') {
                        yamlTextarea.addEventListener('input', function() {
                            if (window.yamlMonacoEditor) return;
                            const currentValue = yamlTextarea.textContent || '';
                            yamlTextarea.dataset.value = currentValue;
                            if (window.saveEditorState) {
                                window.saveEditorState.yamlContent = currentValue;
                            }
                        });
                        yamlTextarea.dataset.msbtYamlInputBound = '1';
                    }
                }
            }
        }

        window.clearSaveEditorWorkspace = async function clearSaveEditorWorkspace() {
            setSaveProcessingState(false);
            window.saveEditorState = {
                isLoaded: false,
                yamlContent: null,
                decodedItems: [],
                backpackSlotsData: {},
                originalFileName: null,
                originalFileHandle: null,
                originalDirectoryHandle: null,
                isProcessing: false
            };
            setYamlTextareaValue('');
            window.saveEditorState.isLoaded = false;
            const yamlContentEl = document.getElementById('save-yaml-content');
            if (yamlContentEl) yamlContentEl.style.display = 'none';
            const decodeItemsDisplayBtnClear = document.getElementById('decode-items-display-btn');
            if (decodeItemsDisplayBtnClear) decodeItemsDisplayBtnClear.style.display = 'none';
            const saveFileInput = document.getElementById('save-file-input');
            if (saveFileInput) saveFileInput.value = '';
            const saveFileSelected = document.getElementById('save-file-selected-name');
            const saveFileNameText = document.getElementById('save-file-name-text');
            if (saveFileSelected) saveFileSelected.style.display = 'none';
            if (saveFileNameText) saveFileNameText.textContent = '';
            window.originalYAMLContent = '';
            window.equippedSlotsData = {};
            window.backpackSlotsData = {};
            window.decodedItemsList = [];
            window.__lastRenderedDecodedList = null;
            window.__lastRenderDecodedMeta = null;
            window.__lastDecodedYamlSuccessKey = null;
            window.__saveEditorItemDecode = 'none';
            try {
                window.decodedItemsData = {};
            } catch (e) {}
            if (typeof window.renderDecodedItems === 'function') {
                await window.renderDecodedItems([], { itemDecode: "none" });
            }
            if (typeof setBulkAdderAvailability === 'function') {
                setBulkAdderAvailability(false);
            }
            if (typeof updateBackpackButtons === 'function') {
                updateBackpackButtons();
            }
            const overwriteBtn = document.getElementById('overwrite-save-btn');
            const overwriteNote = document.getElementById('overwrite-save-note');
            if (overwriteBtn) overwriteBtn.style.display = 'none';
            if (overwriteNote) overwriteNote.style.display = 'none';
            const saveDecryptStatus = document.getElementById('save-decrypt-status');
            if (saveDecryptStatus) {
                saveDecryptStatus.innerHTML = '';
                saveDecryptStatus.style.display = 'none';
            }
            if (typeof updateAutoAddToBackpackCheckbox === 'function') {
                updateAutoAddToBackpackCheckbox();
            }
            if (typeof updateRandomItemModalButtonStates === 'function') {
                updateRandomItemModalButtonStates();
            }
        };
        
        // Function to refresh backpack and equipped items display from YAML
        function refreshBackpackFromYaml() {
            const yamlValue = getYamlTextareaValue();
            if (!yamlValue || !yamlValue.trim()) {
                alert('No YAML content to refresh from.');
                return;
            }
            
            if (typeof decodeYamlInventory === 'function') {
                // Update the original YAML content
                window.originalYAMLContent = yamlValue;
                window.saveEditorState.yamlContent = yamlValue;
                // Refresh the display
                decodeYamlInventory(yamlValue, { 
                    showStatus: true,
                    baseMessage: '✅ Display refreshed from YAML',
                    itemDecode: "none",
                    notifyDecodePhases: true,
                }).catch(err => {
                    console.error('Error refreshing display from YAML:', err);
                    alert('Error refreshing display. Please check the YAML syntax.');
                });
            } else {
                alert('Decode function not available. Please reload the page.');
            }
        }
        
        function getYamlDataFromTextarea() {
            const yamlTextarea = document.getElementById('save-yaml-textarea');
            if (!yamlTextarea) {
                return null;
            }
            
            // Get YAML text from Monaco, textarea, or MSBT's visible div fallback.
            let yamlText = typeof getYamlTextareaValue === 'function'
                ? getYamlTextareaValue()
                : '';
            
            if (!yamlText) {
                if (DEBUG) console.debug('[Preset] No YAML content found. Please decrypt a save file first.');
                return null;
            }
            
            try {
                // Try to parse as YAML if js-yaml is available, otherwise return as text
                if (typeof jsyaml !== 'undefined') {
                    // Remove !tags which js-yaml can't handle (same as reference implementation)
                    yamlText = yamlText.replace(/:\s*!tags/g, ':');
                    
                    if (DEBUG) console.debug('[Preset] Parsing YAML content...');
                    return jsyaml.load(yamlText);
                } else {
                    // Fallback: return raw text if js-yaml not available
                    if (DEBUG) console.warn('[Preset] js-yaml not available, presets may have limited functionality');
                    return yamlText;
                }
            } catch (e) {
                if (DEBUG) console.error('[Preset] Failed to parse YAML:', e.message, e);
                return yamlText;
            }
        }

        /**
         * Highlights and scrolls to a specific section in the YAML textarea
         * @param {string} searchText - Text to search for and highlight
         * @param {string} message - Status message to show
         * @param {string} fallbackSearchText - Fallback text if primary search fails
         */
        function highlightYamlSection(searchText, message, fallbackSearchText = null) {
            const yamlTextarea = document.getElementById('save-yaml-textarea');
            if (!yamlTextarea) {
                if (DEBUG) console.warn('[Preset] YAML textarea not found');
                return;
            }
            
            // Store the currently focused element to restore it later (don't steal focus)
            const activeElement = document.activeElement;
            
            // Small delay to ensure DOM is ready
            setTimeout(() => {
                
                const yamlText = getYamlTextareaValue();
                const lines = yamlText.split('\n');
                
                // Find the line containing the search text
                let targetLine = -1;
                let targetIndex = -1;
                let usedSearchText = searchText;
                
                // First try exact search (could be multi-line)
                if (yamlText.includes(searchText)) {
                    targetIndex = yamlText.indexOf(searchText);
                    // Calculate which line this is on
                    const textBefore = yamlText.substring(0, targetIndex);
                    targetLine = textBefore.split('\n').length - 1;
                } else {
                    // Try single-line search - also check for YAML formatting (with colon, spaces, etc.)
                    const searchPatterns = [
                        searchText,  // Exact match
                        searchText + ':',  // With colon (YAML key)
                        '  ' + searchText,  // With indentation
                        '    ' + searchText,  // With more indentation
                    ];
                    
                    for (let pattern of searchPatterns) {
                        for (let i = 0; i < lines.length; i++) {
                            if (lines[i].includes(pattern)) {
                                targetLine = i;
                                // Calculate character index
                                let charCount = 0;
                                for (let j = 0; j < i; j++) {
                                    charCount += lines[j].length + 1; // +1 for newline
                                }
                                targetIndex = charCount + lines[i].indexOf(pattern);
                                usedSearchText = pattern;
                                break;
                            }
                        }
                        if (targetLine !== -1) break;
                    }
                }
                
                // If not found and we have a fallback, try that
                if (targetLine === -1 && fallbackSearchText) {
                    usedSearchText = fallbackSearchText;
                    if (yamlText.includes(fallbackSearchText)) {
                        targetIndex = yamlText.indexOf(fallbackSearchText);
                        const textBefore = yamlText.substring(0, targetIndex);
                        targetLine = textBefore.split('\n').length - 1;
                    } else {
                        // Try case-insensitive search with fallback
                        const lowerSearch = fallbackSearchText.toLowerCase();
                        for (let i = 0; i < lines.length; i++) {
                            if (lines[i].toLowerCase().includes(lowerSearch)) {
                                targetLine = i;
                                // Calculate character index
                                let charCount = 0;
                                for (let j = 0; j < i; j++) {
                                    charCount += lines[j].length + 1; // +1 for newline
                                }
                                targetIndex = charCount + lines[i].toLowerCase().indexOf(lowerSearch);
                                break;
                            }
                        }
                    }
                } else if (targetLine === -1) {
                    // Try case-insensitive search
                    const lowerSearch = searchText.toLowerCase();
                    for (let i = 0; i < lines.length; i++) {
                        if (lines[i].toLowerCase().includes(lowerSearch)) {
                            targetLine = i;
                            // Calculate character index
                            let charCount = 0;
                            for (let j = 0; j < i; j++) {
                                charCount += lines[j].length + 1; // +1 for newline
                            }
                            targetIndex = charCount + lines[i].toLowerCase().indexOf(lowerSearch);
                            break;
                        }
                    }
                }
                
                if (targetLine !== -1) {
                    // Calculate actual line height from computed style
                    const computedStyle = window.getComputedStyle(yamlTextarea);
                    const fontSize = parseFloat(computedStyle.fontSize) || 14;
                    const lineHeight = parseFloat(computedStyle.lineHeight) || fontSize * 1.2;
                    
                    // Calculate scroll position - scroll to show the line in the middle of visible area
                    const textareaHeight = yamlTextarea.clientHeight;
                    const linesVisible = Math.floor(textareaHeight / lineHeight);
                    const scrollPosition = Math.max(0, (targetLine - Math.floor(linesVisible / 3)) * lineHeight);
                    
                    // Scroll to the position
                    yamlTextarea.scrollTop = scrollPosition;
                    
                    // Also try to select/highlight the text if possible
                    if (targetIndex !== -1) {
                        try {
                            const searchLength = usedSearchText.length;
                            yamlTextarea.setSelectionRange(targetIndex, targetIndex + searchLength);
                        } catch (e) {
                            // Selection might not work in all browsers, that's okay
                            if (DEBUG) console.debug('[Preset] Could not set text selection:', e);
                        }
                    }
                    
                    // Show status message
                    if (message) {
                        showSaveStatus('save-preset-status', message, true);
                    }
                    
                    // Temporarily highlight the textarea with animation
                    yamlTextarea.style.transition = 'box-shadow 0.3s ease';
                    yamlTextarea.style.boxShadow = '0 0 20px rgba(79, 195, 247, 0.8), inset 0 0 10px rgba(79, 195, 247, 0.2)';
                    
                    // Scroll again after a brief delay to ensure it worked
                    setTimeout(() => {
                        yamlTextarea.scrollTop = scrollPosition;
                        // Restore focus to the previously focused element (input field)
                        if (activeElement && activeElement !== yamlTextarea) {
                            activeElement.focus();
                        }
                    }, 100);
                    
                    setTimeout(() => {
                        yamlTextarea.style.boxShadow = '';
                    }, 1500);
                    
                    if (DEBUG) console.debug(`[Preset] Scrolled to line ${targetLine + 1} (search: "${usedSearchText}")`);
                } else {
                    // Don't warn if we couldn't find the text - it might be formatted differently in YAML
                    // Just show the success message without scrolling
                    if (message) {
                        showSaveStatus('save-preset-status', message, true);
                    }
                    if (DEBUG) console.debug(`[Preset] Could not find search text: "${searchText}"${fallbackSearchText ? ` or fallback: "${fallbackSearchText}"` : ''} - showing message anyway`);
                }
            }, 50); // Small delay for focus
        }

        // Closure-scoped flag for batch mode (more reliable than window global in bundled Electron apps)

        (function () {
            var pillEl = null;
            var pending = null;
            var rafId = null;
            function getPill() {
                if (!pillEl) pillEl = document.getElementById("legit-activity-pill");
                return pillEl;
            }
            function flush() {
                rafId = null;
                if (!pending) return;
                var el = getPill();
                if (!el) return;
                var p = pending;
                pending = null;
                var phase = p.phase || "";
                var cur = p.current;
                var tot = p.total;
                var hint =
                    p.hint != null
                        ? String(p.hint).replace(/\s+/g, " ").trim()
                        : "";
                if (hint.length > 52) hint = hint.slice(0, 49) + "…";
                var parts = [phase];
                if (cur != null && tot != null)
                    parts.push(String(cur) + "/" + String(tot));
                if (hint) parts.push(hint);
                el.textContent = parts.join(" · ");
                el.style.display = "block";
            }
            window.showLegitActivityPill = function (opts) {
                pending = opts && typeof opts === "object" ? opts : {};
                if (rafId != null) return;
                if (typeof requestAnimationFrame !== "undefined") {
                    rafId = requestAnimationFrame(flush);
                } else {
                    rafId = setTimeout(function () {
                        rafId = null;
                        flush();
                    }, 0);
                }
            };
            window.hideLegitActivityPill = function () {
                pending = null;
                if (rafId != null) {
                    if (typeof cancelAnimationFrame === "function")
                        cancelAnimationFrame(rafId);
                    clearTimeout(rafId);
                    rafId = null;
                }
                var el = getPill();
                if (el) el.style.display = "none";
            };
        })();

