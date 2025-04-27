/**
 * Huntarr - New UI Implementation
 * Main JavaScript file for handling UI interactions and API communication
 */

const huntarrUI = {
    // Current state
    currentSection: 'home',
    currentApp: 'sonarr',
    currentSettingsTab: 'sonarr',
    currentLogApp: 'sonarr', // Added currentLogApp to track the selected log tab
    autoScroll: true,
    darkMode: false,
    eventSources: {},
    configuredApps: {
        sonarr: false,
        radarr: false,
        lidarr: false,
        readarr: false, // Added readarr
        whisparr: false // Added whisparr
    },
    originalSettings: {}, // Store the full original settings object
    
    // Logo URL
    logoUrl: '/static/logo/64.png',
    
    // Element references
    elements: {},
    
    // Initialize the application
    init: function() {
        // Apply any preloaded theme immediately to avoid flashing
        const prefersDarkMode = localStorage.getItem('huntarr-dark-mode') === 'true';
        if (prefersDarkMode) {
            document.body.classList.add('dark-theme');
        }
        
        // Ensure logo is visible immediately
        this.logoUrl = localStorage.getItem('huntarr-logo-url') || this.logoUrl;
        
        this.cacheElements();
        this.setupEventListeners();
        this.loadUsername();
        this.checkAppConnections();
        this.loadMediaStats(); // Load media statistics
        
        // Ensure logo is applied
        if (typeof window.applyLogoToAllElements === 'function') {
            window.applyLogoToAllElements();
        }
    },
    
    // Cache DOM elements for better performance
    cacheElements: function() {
        // Navigation
        this.elements.navItems = document.querySelectorAll('.nav-item');
        this.elements.homeNav = document.getElementById('homeNav');
        this.elements.logsNav = document.getElementById('logsNav');
        this.elements.settingsNav = document.getElementById('settingsNav');
        this.elements.userNav = document.getElementById('userNav');
        
        // Sections
        this.elements.sections = document.querySelectorAll('.content-section');
        this.elements.homeSection = document.getElementById('homeSection');
        this.elements.logsSection = document.getElementById('logsSection');
        this.elements.settingsSection = document.getElementById('settingsSection');
        
        // App tabs & Settings Tabs
        this.elements.appTabs = document.querySelectorAll('.app-tab'); // For logs section
        this.elements.logTabs = document.querySelectorAll('.log-tab'); // Added log tabs
        this.elements.settingsTabs = document.querySelectorAll('.settings-tab');
        this.elements.appSettingsPanels = document.querySelectorAll('.app-settings-panel');
        
        // Logs
        this.elements.logsContainer = document.getElementById('logsContainer');
        this.elements.autoScrollCheckbox = document.getElementById('autoScrollCheckbox');
        this.elements.clearLogsButton = document.getElementById('clearLogsButton');
        this.elements.logConnectionStatus = document.getElementById('logConnectionStatus');
        
        // Settings
        this.elements.saveSettingsButton = document.getElementById('saveSettingsButton'); // Corrected ID
        this.elements.resetSettingsButton = document.getElementById('resetSettingsButton'); // Corrected ID
        
        // Status elements
        this.elements.sonarrHomeStatus = document.getElementById('sonarrHomeStatus');
        this.elements.radarrHomeStatus = document.getElementById('radarrHomeStatus');
        this.elements.lidarrHomeStatus = document.getElementById('lidarrHomeStatus');
        this.elements.readarrHomeStatus = document.getElementById('readarrHomeStatus'); // Added readarr
        this.elements.whisparrHomeStatus = document.getElementById('whisparrHomeStatus'); // Added whisparr
        
        // Actions
        this.elements.startHuntButton = document.getElementById('startHuntButton');
        this.elements.stopHuntButton = document.getElementById('stopHuntButton');
        
        // Theme
        // this.elements.themeToggle = document.getElementById('themeToggle'); // Removed theme toggle
        
        // Logout
        this.elements.logoutLink = document.getElementById('logoutLink'); // Added logout link
    },
    
    // Set up event listeners
    setupEventListeners: function() {
        // Navigation
        this.elements.navItems.forEach(item => {
            item.addEventListener('click', this.handleNavigation.bind(this));
        });
        
        // App tabs
        this.elements.appTabs.forEach(tab => {
            tab.addEventListener('click', this.handleAppTabChange.bind(this));
        });
        
        // Settings tabs
        this.elements.settingsTabs.forEach(tab => {
            tab.addEventListener('click', this.handleSettingsTabChange.bind(this));
        });
        
        // Log tabs (New)
        this.elements.logTabs.forEach(tab => {
            tab.addEventListener('click', this.handleLogTabChange.bind(this));
        });
        
        // Logs
        if (this.elements.autoScrollCheckbox) {
            this.elements.autoScrollCheckbox.addEventListener('change', (e) => {
                this.autoScroll = e.target.checked;
            });
        }
        
        if (this.elements.clearLogsButton) {
            this.elements.clearLogsButton.addEventListener('click', this.clearLogs.bind(this));
        }
        
        // Settings
        if (this.elements.saveSettingsButton) {
            this.elements.saveSettingsButton.addEventListener('click', this.saveSettings.bind(this));
        }
        
        if (this.elements.resetSettingsButton) {
            this.elements.resetSettingsButton.addEventListener('click', this.resetSettings.bind(this));
        }
        
        // Actions
        if (this.elements.startHuntButton) {
            this.elements.startHuntButton.addEventListener('click', this.startHunt.bind(this));
        }
        
        if (this.elements.stopHuntButton) {
            this.elements.stopHuntButton.addEventListener('click', this.stopHunt.bind(this));
        }
        
        // Theme
        // if (this.elements.themeToggle) { // Removed theme toggle
        //     this.elements.themeToggle.addEventListener('change', this.handleThemeToggle.bind(this));
        // }
        
        // Logout
        if (this.elements.logoutLink) { // Added listener for logout
            this.elements.logoutLink.addEventListener('click', this.logout.bind(this));
        }
        
        // Handle window hash change
        window.addEventListener('hashchange', () => this.handleHashNavigation(window.location.hash)); // Ensure hash is passed

        // Settings form delegation
        const settingsFormContainer = document.querySelector('.settings-form');
        if (settingsFormContainer) {
            settingsFormContainer.addEventListener('input', (event) => {
                if (event.target.closest('.app-settings-panel.active')) {
                    // Check if the target is an input, select, or textarea within the active panel
                    if (event.target.matches('input, select, textarea')) {
                        this.handleSettingChange();
                    }
                }
            });
             settingsFormContainer.addEventListener('change', (event) => {
                 if (event.target.closest('.app-settings-panel.active')) {
                    // Handle changes for checkboxes and selects that use 'change' event
                    if (event.target.matches('input[type="checkbox"], select')) {
                         this.handleSettingChange();
                    }
                 }
            });
        }

        // Initial setup based on hash or default to home
        const initialHash = window.location.hash || '#home';
        this.handleHashNavigation(initialHash);
    },
    
    // Setup logo handling to prevent flashing during navigation
    setupLogoHandling: function() {
        // Get the logo image
        const logoImg = document.querySelector('.sidebar .logo');
        if (logoImg) {
            // Cache the source
            this.logoSrc = logoImg.src;
            
            // Ensure it's fully loaded
            if (!logoImg.complete) {
                logoImg.onload = () => {
                    // Once loaded, store the source
                    this.logoSrc = logoImg.src;
                };
            }
        }
        
        // Also add event listener to ensure logo is preserved during navigation
        window.addEventListener('beforeunload', () => {
            // Store logo src in session storage to persist across page loads
            if (this.logoSrc) {
                sessionStorage.setItem('huntarr-logo-src', this.logoSrc);
            }
        });
    },
    
    // Navigation handling
    handleNavigation: function(e) {
        e.preventDefault();
        const href = e.currentTarget.getAttribute('href');
        
        if (href.startsWith('#')) {
            // Internal navigation
            window.location.hash = href;
        } else {
            // External navigation - preserve state
            localStorage.setItem('huntarr-logo-url', this.logoUrl);
            window.location.href = href;
        }
    },
    
    handleHashNavigation: function(hash) {
        const section = hash.substring(1) || 'home';
        this.switchSection(section);
    },
    
    switchSection: function(section) {
        // Update active section
        this.elements.sections.forEach(s => {
            s.classList.remove('active');
        });
        
        // Update navigation
        this.elements.navItems.forEach(item => {
            item.classList.remove('active');
        });
        
        // Show selected section
        let newTitle = 'Home'; // Default title
        const sponsorsSection = document.getElementById('sponsorsSection'); // Get sponsors section element
        const sponsorsNav = document.getElementById('sponsorsNav'); // Get sponsors nav element

        if (section === 'home' && this.elements.homeSection) {
            this.elements.homeSection.classList.add('active');
            if (this.elements.homeNav) this.elements.homeNav.classList.add('active');
            newTitle = 'Home';
            this.currentSection = 'home';
            // Disconnect logs if switching away from logs
            this.disconnectAllEventSources(); 
        } else if (section === 'logs' && this.elements.logsSection) {
            this.elements.logsSection.classList.add('active');
            if (this.elements.logsNav) this.elements.logsNav.classList.add('active');
            newTitle = 'Logs';
            this.currentSection = 'logs';
            this.connectToLogs();
        } else if (section === 'settings' && this.elements.settingsSection) {
            this.elements.settingsSection.classList.add('active');
            if (this.elements.settingsNav) this.elements.settingsNav.classList.add('active');
            newTitle = 'Settings';
            this.currentSection = 'settings';
            this.loadAllSettings();
            // Disconnect logs if switching away from logs
            this.disconnectAllEventSources(); 
        } else if (section === 'sponsors' && sponsorsSection) { // ADDED sponsors case
            sponsorsSection.classList.add('active');
            if (sponsorsNav) sponsorsNav.classList.add('active');
            newTitle = 'Project Sponsors';
            this.currentSection = 'sponsors';
            // Set the iframe source when switching to this section
            const sponsorsFrame = document.getElementById('sponsorsFrame');
            if (sponsorsFrame && (!sponsorsFrame.src || sponsorsFrame.src === 'about:blank')) { // Set src only if not already set or blank
                sponsorsFrame.src = 'https://github.com/sponsors/plexguide';
            }
            // Disconnect logs if switching away from logs
            this.disconnectAllEventSources();
        } else {
            // Default to home if section is unknown or element missing
            if (this.elements.homeSection) this.elements.homeSection.classList.add('active');
            if (this.elements.homeNav) this.elements.homeNav.classList.add('active');
            newTitle = 'Home';
            this.currentSection = 'home';
            // Disconnect logs if switching away from logs
            this.disconnectAllEventSources(); 
        }

        // Update the page title
        const pageTitleElement = document.getElementById('currentPageTitle');
        if (pageTitleElement) {
            pageTitleElement.textContent = newTitle;
        } else {
            console.warn("[huntarrUI] currentPageTitle element not found during section switch.");
        }
    },
    
    // App tab switching
    handleAppTabChange: function(e) {
        const app = e.target.getAttribute('data-app');
        if (!app) return;
        
        // Update active tab
        this.elements.appTabs.forEach(tab => {
            tab.classList.remove('active');
        });
        e.target.classList.add('active');
        
        // Switch to the selected app logs
        this.currentApp = app;
        this.connectToLogs();
    },
    
    // Log tab switching (New)
    handleLogTabChange: function(e) {
        const app = e.target.getAttribute('data-app');
        if (!app || app === this.currentLogApp) return; // Do nothing if same tab clicked
        
        // Update active tab
        this.elements.logTabs.forEach(tab => {
            tab.classList.remove('active');
        });
        e.target.classList.add('active');
        
        // Switch to the selected app logs
        this.currentLogApp = app;
        this.clearLogs(); // Clear existing logs before switching
        this.connectToLogs(); // Reconnect to the new log source
    },

    // Settings tab switching
    handleSettingsTabChange: function(e) {
        const tab = e.target.getAttribute('data-settings');
        if (!tab) return;
        
        // Update active tab
        this.elements.settingsTabs.forEach(t => {
            t.classList.remove('active');
        });
        e.target.classList.add('active');
        
        // Switch to the selected settings panel
        this.elements.appSettingsPanels.forEach(panel => {
            panel.classList.remove('active');
            panel.style.display = 'none'; // Explicitly hide
        });
        
        const panelElement = document.getElementById(`${tab}Settings`);
        if (panelElement) {
            panelElement.classList.add('active');
            panelElement.style.display = 'block'; // Explicitly show
            this.currentSettingsTab = tab;
            // Ensure settings are populated for this tab using the stored originalSettings
            this.populateSettingsForm(tab, this.originalSettings[tab] || {});
            // Reset save button state when switching tabs
            this.updateSaveResetButtonState(tab, false);
        }
    },
    
    // Logs handling
    connectToLogs: function() {
        // Disconnect any existing event sources
        this.disconnectAllEventSources();
        
        // Connect to logs stream for the currentLogApp
        this.connectEventSource(this.currentLogApp); // Pass the selected app
        this.elements.logConnectionStatus.textContent = 'Connecting...';
        this.elements.logConnectionStatus.className = '';
    },
    
    connectEventSource: function(appType = 'all') { // Default to 'all', accept appType
        // Close any existing event source
        if (this.eventSources.logs) {
            this.eventSources.logs.close();
        }
        
        try {
            // Append the app type to the URL
            const eventSource = new EventSource(`/logs?app=${appType}`); 
            
            eventSource.onopen = () => {
                this.elements.logConnectionStatus.textContent = 'Connected';
                this.elements.logConnectionStatus.className = 'status-connected';
            };
            
            eventSource.onmessage = (event) => {
                if (!this.elements.logsContainer) return;
                
                const logEntry = document.createElement('div');
                logEntry.className = 'log-entry';
                
                // Add appropriate class for log level
                // Simplified check - adjust if log format changes
                const lowerData = event.data.toLowerCase();
                if (lowerData.includes('info')) {
                    logEntry.classList.add('log-info');
                } else if (lowerData.includes('warning')) {
                    logEntry.classList.add('log-warning');
                } else if (lowerData.includes('error')) {
                    logEntry.classList.add('log-error');
                } else if (lowerData.includes('debug')) {
                    logEntry.classList.add('log-debug');
                }
                
                logEntry.textContent = event.data;
                this.elements.logsContainer.appendChild(logEntry);
                
                // Auto-scroll to bottom if enabled
                if (this.autoScroll) {
                    this.elements.logsContainer.scrollTop = this.elements.logsContainer.scrollHeight;
                }
            };
            
            eventSource.onerror = () => {
                this.elements.logConnectionStatus.textContent = 'Disconnected';
                this.elements.logConnectionStatus.className = 'status-disconnected';
                
                // Try to reconnect after a delay
                setTimeout(() => {
                    // Only reconnect if the logs section is still active
                    if (this.currentSection === 'logs') {
                        this.connectEventSource(this.currentLogApp); // Use current app type
                    }
                }, 5000);
            };
            
            this.eventSources.logs = eventSource;
        } catch (error) {
            console.error('Error connecting to event source:', error);
            this.elements.logConnectionStatus.textContent = 'Connection Error';
            this.elements.logConnectionStatus.className = 'status-disconnected';
        }
    },
    
    disconnectAllEventSources: function() {
        Object.values(this.eventSources).forEach(source => {
            if (source && source.readyState !== 2) {
                source.close();
            }
        });
    },
    
    addLogMessage: function(logData) {
        if (!this.elements.logsContainer) return;
        
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry log-${logData.level.toLowerCase()}`;
        logEntry.textContent = logData.message;
        
        this.elements.logsContainer.appendChild(logEntry);
        
        if (this.autoScroll) {
            this.elements.logsContainer.scrollTop = this.elements.logsContainer.scrollHeight;
        }
    },
    
    clearLogs: function() {
        if (this.elements.logsContainer) {
            this.elements.logsContainer.innerHTML = '';
        }
    },
    
    // Settings handling
    loadAllSettings: function() {
        console.log("[huntarrUI] Loading all settings...");
        fetch(`/api/settings`) // Fetch the entire settings object
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log("[huntarrUI] All settings loaded:", data);
                this.originalSettings = JSON.parse(JSON.stringify(data)); // Store deep copy

                // Populate the currently active settings form
                this.populateSettingsForm(this.currentSettingsTab, this.originalSettings[this.currentSettingsTab] || {});
                // Optionally pre-populate others if needed, but might be redundant if done on tab switch
            })
            .catch(error => {
                console.error(`Error loading all settings:`, error);
                this.showNotification(`Error loading settings: ${error.message}`, 'error');
                this.originalSettings = {}; // Reset on error
            });
    },
    
    populateSettingsForm: function(app, appSettings) {
        const container = document.getElementById(`${app}Settings`);
        if (!container) {
            console.warn(`[huntarrUI] Container not found for populating settings: ${app}Settings`);
            return;
        }
        console.log(`[huntarrUI] Populating settings form for ${app}`, appSettings);

        // Use SettingsForms to generate the form structure if not already present
        // This assumes SettingsForms is available globally or imported
        if (typeof SettingsForms !== 'undefined' && !container.querySelector('.settings-group')) {
             const formGenerator = SettingsForms[`generate${this.capitalizeFirst(app)}Form`];
             if (formGenerator) {
                 console.log(`[huntarrUI] Generating form structure for ${app}`);
                 formGenerator(container, appSettings); // Generate structure AND populate initial values
             } else {
                 console.warn(`[huntarrUI] Form generator not found for ${app}`);
             }
        } else {
             // If form structure exists, just update values
             console.log(`[huntarrUI] Updating existing form values for ${app}`);
             const inputs = container.querySelectorAll('input, select, textarea');
             inputs.forEach(input => {
                 const key = input.id.replace(`${app}_`, ''); // Get the setting key from the ID

                 if (appSettings.hasOwnProperty(key)) {
                     const value = appSettings[key];
                     if (input.type === 'checkbox') {
                         input.checked = value === true;
                     } else if (input.type === 'radio') {
                         // Handle radio buttons if necessary (check by value)
                         if (input.value === String(value)) {
                             input.checked = true;
                         }
                     } else {
                         input.value = value;
                     }
                 } else {
                      // Optional: Clear or set default for fields not in settings?
                      // console.warn(`[huntarrUI] Setting key "${key}" not found in settings for ${app}`);
                 }
             });
        }

        // Special handling for duration displays if needed (might be better in SettingsForms)
        if (typeof SettingsForms !== 'undefined' && typeof SettingsForms.updateDurationDisplay === 'function') {
            SettingsForms.updateDurationDisplay();
        }

        // Initialize app-specific JS handlers after form is populated/generated
        if (app === 'sonarr' && typeof setupSonarrForm === 'function') {
            setupSonarrForm();
        } else if (app === 'radarr' && typeof setupRadarrForm === 'function') {
            setupRadarrForm();
        } else if (app === 'lidarr' && typeof setupLidarrForm === 'function') {
            setupLidarrForm();
        } else if (app === 'readarr' && typeof setupReadarrForm === 'function') {
            setupReadarrForm();
        } else if (app === 'whisparr' && typeof setupWhisparrForm === 'function') { // Added Whisparr
            setupWhisparrForm();
        }

        // Ensure save/reset buttons are initially disabled after populating
        this.updateSaveResetButtonState(app, false);
    },

    // Called when any setting input changes in the active tab
    handleSettingChange: function() {
        console.log(`[huntarrUI] Setting change detected in tab: ${this.currentSettingsTab}`);
        this.updateSaveResetButtonState(this.currentSettingsTab, true); // Enable save button
    },

    saveSettings: function() {
        const app = this.currentSettingsTab;
        console.log(`[huntarrUI] saveSettings called for app: ${app}`);
        const settings = this.collectSettingsFromForm(app);

        if (!settings) {
            console.error(`[huntarrUI] Failed to collect settings for app: ${app}`);
            this.showNotification('Error collecting settings from form.', 'error');
            return;
        }

        console.log(`[huntarrUI] Collected settings for ${app}:`, settings);

        // Add app_type to the payload if needed by backend (confirm backend logic)
        // Assuming the backend merges based on the top-level key matching the app name
        const payload = { [app]: settings };

        console.log(`[huntarrUI] Sending settings payload for ${app}:`, payload);

        // Use the correct endpoint /api/settings
        fetch(`/api/settings`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload) // Send payload structured as { appName: { settings... } }
        })
        .then(response => {
            if (!response.ok) {
                // Try to get error message from response body
                return response.json().then(errData => {
                    throw new Error(errData.error || `HTTP error! status: ${response.status}`);
                }).catch(() => {
                    // Fallback if response body is not JSON or empty
                    throw new Error(`HTTP error! status: ${response.status}`);
                });
            }
            return response.json();
        })
        .then(savedConfig => { // Backend returns the full, updated config
            console.log('[huntarrUI] Settings saved successfully. Full config received:', savedConfig);
            this.showNotification('Settings saved successfully', 'success');

            // Update original settings state with the full config returned from backend
            // Ensure savedConfig is the full object { sonarr: {...}, radarr: {...}, ... }
            if (typeof savedConfig === 'object' && savedConfig !== null) {
                 this.originalSettings = JSON.parse(JSON.stringify(savedConfig));
            } else {
                console.error('[huntarrUI] Invalid config received from backend after save:', savedConfig);
                // Attempt to reload all settings as a fallback
                this.loadAllSettings();
                return; // Avoid further processing with invalid data
            }

            // Re-populate the current form with the saved data for consistency
            const currentAppSettings = this.originalSettings[app] || {};
            this.populateSettingsForm(app, currentAppSettings);

            // Update connection status for the saved app
            this.checkAppConnection(app);

            // Update general UI elements like home page statuses
            this.updateHomeConnectionStatus(); // Assuming this function exists and works

            // Disable save/reset buttons as changes are now saved
            this.updateSaveResetButtonState(app, false);

        })
        .catch(error => {
            console.error('Error saving settings:', error);
            this.showNotification(`Error saving settings: ${error.message}`, 'error');
        });
    },

    resetSettings: function() {
        if (confirm('Are you sure you want to reset these settings to default values?')) {
            const app = this.currentSettingsTab;
            
            // Use POST /api/settings/reset and send app name in body
            fetch(`/api/settings/reset`, { 
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ app: app }) // Send app name in body
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.showNotification('Settings reset to defaults', 'success');
                    // Reload settings for the current app
                    this.loadSettings(app); 
                } else {
                    this.showNotification('Error resetting settings', 'error');
                }
            })
            .catch(error => {
                console.error('Error resetting settings:', error);
                this.showNotification('Error resetting settings', 'error');
            });
        }
    },
    
    collectSettingsFromForm: function(app) {
        const settings = {};
        
        // Collect all input values for the current app
        const container = document.getElementById(`${app}Settings`);
        if (!container) return settings;
        
        // Get all inputs
        const inputs = container.querySelectorAll('input, select');
        inputs.forEach(input => {
            const id = input.id;
            const key = id.replace(`${app}_`, '');
            
            // Handle different input types
            if (input.type === 'checkbox') {
                settings[key] = input.checked;
            } else if (input.type === 'number') {
                settings[key] = parseInt(input.value, 10);
            } else {
                settings[key] = input.value;
            }
        });
        
        return settings;
    },
    
    // App connections
    checkAppConnections: function() {
        this.checkAppConnection('sonarr');
        this.checkAppConnection('radarr');
        this.checkAppConnection('lidarr');
        this.checkAppConnection('readarr'); // Added readarr
        this.checkAppConnection('whisparr'); // Added whisparr
    },
    
    checkAppConnection: function(app) {
        fetch(`/api/status/${app}`)
            .then(response => response.json())
            .then(data => {
                this.updateConnectionStatus(app, data.connected);
                this.configuredApps[app] = data.configured;
            })
            .catch(error => {
                console.error(`Error checking ${app} connection:`, error);
                this.updateConnectionStatus(app, false);
            });
    },
    
    updateConnectionStatus: function(app, connected) {
        const statusElement = this.elements[`${app}HomeStatus`];
        if (!statusElement) return;
        
        if (connected) {
            statusElement.className = 'status-badge connected';
            statusElement.innerHTML = '<i class="fas fa-check-circle"></i> Connected';
        } else {
            statusElement.className = 'status-badge not-connected';
            statusElement.innerHTML = '<i class="fas fa-times-circle"></i> Not Connected';
        }
    },
    
    // User actions
    startHunt: function() {
        fetch('/api/hunt/start', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.showNotification('Hunt started successfully', 'success');
                } else {
                    this.showNotification('Failed to start hunt', 'error');
                }
            })
            .catch(error => {
                console.error('Error starting hunt:', error);
                this.showNotification('Error starting hunt', 'error');
            });
    },
    
    stopHunt: function() {
        fetch('/api/hunt/stop', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.showNotification('Hunt stopped successfully', 'success');
                } else {
                    this.showNotification('Failed to stop hunt', 'error');
                }
            })
            .catch(error => {
                console.error('Error stopping hunt:', error);
                this.showNotification('Error stopping hunt', 'error');
            });
    },
    
    // User
    loadUsername: function() {
        const usernameElement = document.getElementById('username');
        if (!usernameElement) return;
        
        fetch('/api/user/info')
            .then(response => response.json())
            .then(data => {
                if (data.username) {
                    usernameElement.textContent = data.username;
                }
            })
            .catch(error => {
                console.error('Error loading username:', error);
            });
    },
    
    logout: function(e) { // Added logout function
        e.preventDefault(); // Prevent default link behavior
        console.log('[huntarrUI] Logging out...');
        fetch('/logout', { // Use the correct endpoint defined in Flask
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('[huntarrUI] Logout successful, redirecting to login.');
                window.location.href = '/login'; // Redirect to login page
            } else {
                console.error('[huntarrUI] Logout failed:', data.message);
                this.showNotification('Logout failed. Please try again.', 'error');
            }
        })
        .catch(error => {
            console.error('Error during logout:', error);
            this.showNotification('An error occurred during logout.', 'error');
        });
    },
    
    // Media statistics handling
    loadMediaStats: function() {
        fetch('/api/stats')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.success && data.stats) {
                    this.updateStatsDisplay(data.stats);
                } else {
                    console.error('Failed to load statistics:', data.message || 'Unknown error');
                }
            })
            .catch(error => {
                console.error('Error fetching statistics:', error);
            });
    },
    
    updateStatsDisplay: function(stats) {
        // Update each app's statistics
        const apps = ['sonarr', 'radarr', 'lidarr', 'readarr', 'whisparr'];
        const statTypes = ['hunted', 'upgraded'];
        
        apps.forEach(app => {
            if (stats[app]) {
                statTypes.forEach(type => {
                    const element = document.getElementById(`${app}-${type}`);
                    if (element) {
                        // Animate the number change
                        this.animateNumber(element, parseInt(element.textContent), stats[app][type] || 0);
                    }
                });
            }
        });
    },
    
    animateNumber: function(element, start, end) {
        const duration = 1000; // Animation duration in milliseconds
        const startTime = performance.now();
        
        const updateNumber = (currentTime) => {
            const elapsedTime = currentTime - startTime;
            const progress = Math.min(elapsedTime / duration, 1);
            
            // Easing function for smooth animation
            const easeOutQuad = progress * (2 - progress);
            
            const currentValue = Math.floor(start + (end - start) * easeOutQuad);
            element.textContent = currentValue;
            
            if (progress < 1) {
                requestAnimationFrame(updateNumber);
            } else {
                element.textContent = end; // Ensure we end with the exact target number
            }
        };
        
        requestAnimationFrame(updateNumber);
    },
    
    resetMediaStats: function(appType = null) {
        const confirmMessage = appType 
            ? `Are you sure you want to reset statistics for ${appType}?` 
            : 'Are you sure you want to reset all media statistics?';
            
        if (!confirm(confirmMessage)) {
            return;
        }
        
        const requestBody = appType ? { app_type: appType } : {};
        
        fetch('/api/stats/reset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.showNotification(data.message, 'success');
                    this.loadMediaStats(); // Refresh the stats display
                } else {
                    this.showNotification(data.message || 'Failed to reset statistics', 'error');
                }
            })
            .catch(error => {
                console.error('Error resetting statistics:', error);
                this.showNotification('Error resetting statistics', 'error');
            });
    },
    
    // Utility functions
    showNotification: function(message, type) {
        // Create a notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        // Add to the document
        document.body.appendChild(notification);
        
        // Ensure any existing notification is removed first to prevent stacking
        const existingNotifications = document.querySelectorAll('.notification');
        existingNotifications.forEach(n => {
            if (n !== notification) {
                n.classList.remove('show');
                setTimeout(() => n.remove(), 300);
            }
        });
        
        // Fade in
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        // Remove after a delay
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    },
    
    capitalizeFirst: function(string) {
        return string.charAt(0).toUpperCase() + string.slice(1);
    },

    // Add or modify this function to handle enabling/disabling save/reset
    updateSaveResetButtonState: function(app, hasChanges) {
        // Find buttons relevant to the current app context if they exist
        // This might need adjustment based on actual button IDs/classes
        const saveButton = this.elements.saveSettingsButton; // Assuming a general save button
        const resetButton = this.elements.resetSettingsButton; // Assuming a general reset button

        if (saveButton) {
            saveButton.disabled = !hasChanges;
            // Add/remove a class for styling disabled state if needed
            if (hasChanges) {
                saveButton.classList.remove('disabled-button'); // Example class
            } else {
                saveButton.classList.add('disabled-button'); // Example class
            }
        }
        // Reset button logic (enable/disable based on changes or always enabled?)
        // if (resetButton) {
        //     resetButton.disabled = !hasChanges;
        // }
    },

    // Add updateHomeConnectionStatus if it doesn't exist or needs adjustment
    updateHomeConnectionStatus: function() {
        console.log('[huntarrUI] Updating home connection statuses...');
        // This function should ideally call checkAppConnection for all relevant apps
        // or use the stored configuredApps status if checkAppConnection updates it.
        this.checkAppConnections(); // Re-check all connections after a save might be simplest
    },
};

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', () => {
    huntarrUI.init();
    
    // Add event listeners for media statistics buttons
    const refreshStatsButton = document.getElementById('refresh-stats');
    if (refreshStatsButton) {
        refreshStatsButton.addEventListener('click', () => {
            huntarrUI.loadMediaStats();
        });
    }
    
    const resetStatsButton = document.getElementById('reset-stats');
    if (resetStatsButton) {
        resetStatsButton.addEventListener('click', () => {
            huntarrUI.resetMediaStats();
        });
    }
    
    // Restore logo from session storage if available
    const cachedLogoSrc = sessionStorage.getItem('huntarr-logo-src');
    if (cachedLogoSrc) {
        const logoImg = document.querySelector('.sidebar .logo');
        if (logoImg) {
            logoImg.src = cachedLogoSrc;
        }
    }
    
    // Also apply logo on page load
    if (typeof window.applyLogoToAllElements === 'function') {
        window.applyLogoToAllElements();
    }
});

// Expose huntarrUI to the global scope for access by app modules
window.huntarrUI = huntarrUI;
