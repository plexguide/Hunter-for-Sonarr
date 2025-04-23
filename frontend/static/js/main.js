// Main entry point for Huntarr application

// Wait for DOM content to be loaded before initializing the app
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the core application
    if (window.HuntarrApp) { // Changed from huntarrApp to HuntarrApp to match object name
        window.HuntarrApp.init();
    } else {
        console.error('Error: Huntarr core module not loaded');
    }
});

// Define the HuntarrApp object
const HuntarrApp = {
    // ... (keep existing properties like currentSection, currentApp, etc.) ...
    currentSection: 'home',
    currentApp: 'sonarr',
    currentSettingsTab: 'sonarr',
    autoScroll: true,
    darkMode: false,
    eventSources: {},
    configuredApps: {
        sonarr: false,
        radarr: false,
        lidarr: false
    },
    elements: {},
    originalSettings: {}, // Added to store original settings for comparison

    init: function() {
        this.cacheElements();
        this.setupEventListeners();
        this.loadTheme();
        this.loadUsername();
        this.checkAppConnections();
        this.handleHashNavigation(); // Handle initial section based on hash
        
        // Initialize settings if we're on the settings page or hash points to settings
        if (window.location.pathname === '/settings' || window.location.hash === '#settings') {
            this.initializeSettings();
        }
    },

    cacheElements: function() {
        // Cache all necessary DOM elements
        this.elements.navItems = document.querySelectorAll('.nav-item');
        this.elements.homeNav = document.getElementById('homeNav');
        this.elements.logsNav = document.getElementById('logsNav');
        this.elements.settingsNav = document.getElementById('settingsNav');
        this.elements.userNav = document.getElementById('userNav');
        
        this.elements.sections = document.querySelectorAll('.content-section');
        this.elements.homeSection = document.getElementById('homeSection');
        this.elements.logsSection = document.getElementById('logsSection');
        this.elements.settingsSection = document.getElementById('settingsSection');
        this.elements.userSection = document.getElementById('userSection'); // Assuming a user section exists

        this.elements.appTabs = document.querySelectorAll('.app-tab');
        this.elements.settingsTabs = document.querySelectorAll('.settings-tab');
        this.elements.appSettingsPanels = document.querySelectorAll('.app-settings-panel');

        this.elements.logsContainer = document.getElementById('logsContainer');
        this.elements.autoScrollCheckbox = document.getElementById('autoScrollCheckbox');
        this.elements.clearLogsButton = document.getElementById('clearLogsButton');
        this.elements.logConnectionStatus = document.getElementById('logConnectionStatus');

        this.elements.saveSettingsButton = document.getElementById('saveSettingsButton');
        this.elements.resetSettingsButton = document.getElementById('resetSettingsButton');
        
        this.elements.sonarrHomeStatus = document.getElementById('sonarrHomeStatus');
        this.elements.radarrHomeStatus = document.getElementById('radarrHomeStatus');
        this.elements.lidarrHomeStatus = document.getElementById('lidarrHomeStatus');
        this.elements.readarrHomeStatus = document.getElementById('readarrHomeStatus'); // Added Readarr status

        this.elements.startHuntButton = document.getElementById('startHuntButton');
        this.elements.stopHuntButton = document.getElementById('stopHuntButton');

        this.elements.themeToggle = document.getElementById('themeToggle');
        this.elements.currentPageTitle = document.getElementById('currentPageTitle');
        this.elements.usernameDisplay = document.getElementById('username'); // For top bar
    },

    setupEventListeners: function() {
        // Navigation
        this.elements.navItems.forEach(item => {
            item.addEventListener('click', this.handleNavigation.bind(this));
        });

        // App tabs (Logs page)
        this.elements.appTabs.forEach(tab => {
            tab.addEventListener('click', this.handleAppTabChange.bind(this));
        });

        // Settings tabs
        this.elements.settingsTabs.forEach(tab => {
            tab.addEventListener('click', this.handleSettingsTabChange.bind(this));
        });

        // Logs controls
        if (this.elements.autoScrollCheckbox) {
            this.elements.autoScrollCheckbox.addEventListener('change', (e) => {
                this.autoScroll = e.target.checked;
            });
        }
        if (this.elements.clearLogsButton) {
            this.elements.clearLogsButton.addEventListener('click', this.clearLogs.bind(this));
        }

        // Settings controls
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

        // Theme toggle
        if (this.elements.themeToggle) {
            this.elements.themeToggle.addEventListener('change', this.handleThemeToggle.bind(this));
        }

        // Window hash changes
        window.addEventListener('hashchange', this.handleHashNavigation.bind(this));
    },
    
    handleNavigation: function(e) {
        e.preventDefault();
        const target = e.currentTarget;
        const section = target.getAttribute('href').substring(1);
        window.location.hash = section; // Use hash for SPA navigation
    },

    handleHashNavigation: function() {
        const hash = window.location.hash || '#home';
        const section = hash.substring(1);
        this.switchSection(section);
    },

    switchSection: function(section) {
        this.currentSection = section;

        // Hide all sections
        this.elements.sections.forEach(s => s.classList.remove('active'));
        // Deactivate all nav items
        this.elements.navItems.forEach(n => n.classList.remove('active'));

        // Activate the target section and nav item
        const targetSection = document.getElementById(section + 'Section');
        const targetNav = document.querySelector(`.nav-item[href="#${section}"]`);

        if (targetSection) {
            targetSection.classList.add('active');
            if (this.elements.currentPageTitle) {
                this.elements.currentPageTitle.textContent = this.capitalizeFirst(section);
            }
        } else {
            // Fallback to home if section not found
            this.elements.homeSection.classList.add('active');
            section = 'home';
            if (this.elements.currentPageTitle) {
                this.elements.currentPageTitle.textContent = 'Home';
            }
        }

        if (targetNav) {
            targetNav.classList.add('active');
        }

        // Section-specific actions
        if (section === 'logs') {
            this.connectToLogs();
        } else {
            this.disconnectAllEventSources(); // Disconnect logs when leaving the page
        }
        
        if (section === 'settings') {
            this.initializeSettings(); // Load settings when entering the settings section
        }
    },
    
    initializeSettings: function() {
        console.log("Initializing settings...");
        const activeTab = document.querySelector('.settings-tab.active');
        const defaultTab = 'sonarr'; // Or load from a saved preference
        this.currentSettingsTab = activeTab ? activeTab.getAttribute('data-settings') : defaultTab;
        
        // Ensure the correct panel is visible
        this.elements.appSettingsPanels.forEach(panel => panel.classList.remove('active'));
        const activePanel = document.getElementById(`${this.currentSettingsTab}Settings`);
        if (activePanel) {
            activePanel.classList.add('active');
        }
        
        // Ensure the correct tab is highlighted
        this.elements.settingsTabs.forEach(tab => {
            if (tab.getAttribute('data-settings') === this.currentSettingsTab) {
                tab.classList.add('active');
            } else {
                tab.classList.remove('active');
            }
        });

        this.loadAllSettings(); // Load settings for all tabs
    },

    handleAppTabChange: function(e) {
        const app = e.target.getAttribute('data-app');
        if (!app || app === this.currentApp) return;

        this.currentApp = app;
        this.elements.appTabs.forEach(tab => tab.classList.remove('active'));
        e.target.classList.add('active');
        
        // Reconnect logs for the new app
        this.connectToLogs(); 
    },

    handleSettingsTabChange: function(e) {
        const tab = e.target.getAttribute('data-settings');
        if (!tab || tab === this.currentSettingsTab) return;

        this.currentSettingsTab = tab;

        // Update active tab styling
        this.elements.settingsTabs.forEach(t => t.classList.remove('active'));
        e.target.classList.add('active');

        // Show the corresponding settings panel
        this.elements.appSettingsPanels.forEach(panel => panel.classList.remove('active'));
        const panelElement = document.getElementById(`${tab}Settings`);
        if (panelElement) {
            panelElement.classList.add('active');
            // Settings for this tab should already be loaded by loadAllSettings
            // If not, call this.loadSettings(tab) here.
        }
    },

    // Logs handling
    connectToLogs: function() {
        this.disconnectAllEventSources(); // Ensure only one connection
        
        // Use the unified /logs endpoint, filtering happens server-side or client-side if needed
        // For now, assuming server sends all logs and we might filter later if necessary
        const logUrl = `/logs?app=${this.currentApp}`; // Pass current app context if needed by backend
        
        try {
            const eventSource = new EventSource(logUrl);
            this.eventSources['logs'] = eventSource; // Store under a generic key

            eventSource.onopen = () => {
                if (this.elements.logConnectionStatus) {
                    this.elements.logConnectionStatus.textContent = 'Connected';
                    this.elements.logConnectionStatus.className = 'status-connected';
                }
            };

            eventSource.onmessage = (event) => {
                // Assuming event.data is a string log line
                this.addLogMessage(event.data);
            };

            eventSource.onerror = () => {
                if (this.elements.logConnectionStatus) {
                    this.elements.logConnectionStatus.textContent = 'Disconnected';
                    this.elements.logConnectionStatus.className = 'status-disconnected';
                }
                eventSource.close();
                // Optional: Implement retry logic
                setTimeout(() => {
                    if (this.currentSection === 'logs') { // Only reconnect if still on logs page
                        this.connectToLogs();
                    }
                }, 5000);
            };
        } catch (error) {
            console.error('Error connecting to logs event source:', error);
            if (this.elements.logConnectionStatus) {
                this.elements.logConnectionStatus.textContent = 'Error';
                this.elements.logConnectionStatus.className = 'status-disconnected';
            }
        }
    },

    disconnectAllEventSources: function() {
        Object.values(this.eventSources).forEach(source => {
            if (source && source.readyState !== EventSource.CLOSED) {
                source.close();
            }
        });
        this.eventSources = {}; // Clear sources
    },

    addLogMessage: function(logLine) {
        if (!this.elements.logsContainer) return;

        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        // Add level-based coloring (similar to new-main.js)
        if (logLine.includes(' - INFO - ')) logEntry.classList.add('log-info');
        else if (logLine.includes(' - WARNING - ')) logEntry.classList.add('log-warning');
        else if (logLine.includes(' - ERROR - ')) logEntry.classList.add('log-error');
        else if (logLine.includes(' - DEBUG - ')) logEntry.classList.add('log-debug');
        
        logEntry.textContent = logLine;
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
        // Fetch combined settings
        fetch('/api/settings') // Use the combined endpoint
            .then(response => response.json())
            .then(data => {
                this.originalSettings = JSON.parse(JSON.stringify(data)); // Store originals
                // Populate forms for each app section present in the data
                ['global', 'sonarr', 'radarr', 'lidarr', 'readarr', 'ui'].forEach(app => {
                    if (data[app]) {
                        this.populateSettingsForm(app, data[app]);
                    }
                    // Populate API keys if they exist at top level (backward compatibility)
                    if (app !== 'global' && app !== 'ui' && data.api_url && data.api_key && app === data.global?.app_type) {
                         this.populateApiSettings(app, data.api_url, data.api_key);
                    }
                    // Populate API keys from the app section itself (new structure)
                    else if (data[app] && data[app].api_url !== undefined && data[app].api_key !== undefined) {
                         this.populateApiSettings(app, data[app].api_url, data[app].api_key);
                    }
                });
            })
            .catch(error => {
                console.error('Error loading all settings:', error);
                this.showNotification('Error loading settings', 'error');
            });
    },
    
    // Separate function to populate API fields to avoid duplication
    populateApiSettings: function(app, apiUrl, apiKey) {
        const urlInput = document.getElementById(`${app}_api_url`);
        const keyInput = document.getElementById(`${app}_api_key`);
        if (urlInput) urlInput.value = apiUrl || '';
        if (keyInput) keyInput.value = apiKey || '';
    },

    // Simplified loadSettings - now part of loadAllSettings
    // loadSettings: function(app) { ... }, 

    populateSettingsForm: function(app, settings) {
        const container = document.getElementById(`${app}Settings`);
        if (!container) return;

        // Use SettingsForms helper if available (assuming it exists and works)
        if (window.SettingsForms && typeof window.SettingsForms[`generate${this.capitalizeFirst(app)}Form`] === 'function') {
            container.innerHTML = ''; // Clear previous
            window.SettingsForms[`generate${this.capitalizeFirst(app)}Form`](container, settings);
        } else {
            // Basic fallback population (similar to previous logic but simplified)
            console.warn(`Settings form generator for ${app} not found. Using basic population.`);
            for (const key in settings) {
                const input = container.querySelector(`#${app}_${key}`);
                if (input) {
                    if (input.type === 'checkbox') {
                        input.checked = settings[key];
                    } else {
                        input.value = settings[key];
                    }
                }
            }
        }
        // Populate API fields separately using the dedicated function
        this.populateApiSettings(app, settings.api_url, settings.api_key);
    },

    saveSettings: function() {
        const app = this.currentSettingsTab;
        const settings = this.collectSettingsFromForm(app);
        settings.app_type = app; // Add app_type for the backend

        // Simple check for changes (can be enhanced)
        // if (JSON.stringify(settings) === JSON.stringify(this.originalSettings[app])) {
        //     this.showNotification('No changes detected.', 'info');
        //     return;
        // }

        fetch(`/api/settings`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(settings)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showNotification('Settings saved successfully', 'success');
                // Update original settings after save
                this.originalSettings = JSON.parse(JSON.stringify(data.settings || this.originalSettings));
                // Re-populate form to reflect saved state and update originals
                this.populateSettingsForm(app, this.originalSettings[app]); 
                this.populateApiSettings(app, this.originalSettings[app]?.api_url, this.originalSettings[app]?.api_key);
                // Check connections again as API keys might have changed
                this.checkAppConnections(); 
            } else {
                this.showNotification(`Error saving settings: ${data.message || 'Unknown error'}`, 'error');
            }
        })
        .catch(error => {
            console.error('Error saving settings:', error);
            this.showNotification('Error saving settings', 'error');
        });
    },

    resetSettings: function() {
        const app = this.currentSettingsTab;
        if (confirm(`Are you sure you want to reset ${app.toUpperCase()} settings to default values?`)) {
            fetch(`/api/settings/reset`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ app: app })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.showNotification(`${this.capitalizeFirst(app)} settings reset to defaults`, 'success');
                    // Reload all settings to reflect the reset
                    this.loadAllSettings(); 
                } else {
                    this.showNotification(`Error resetting settings: ${data.message || 'Unknown error'}`, 'error');
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
        const container = document.getElementById(`${app}Settings`);
        if (!container) return settings;

        const inputs = container.querySelectorAll('input, select');
        inputs.forEach(input => {
            // Extract key name correctly (e.g., from 'sonarr_api_key' to 'api_key')
            const key = input.id.startsWith(`${app}_`) ? input.id.substring(app.length + 1) : input.id;
            
            if (key) { // Ensure key is not empty
                if (input.type === 'checkbox') {
                    settings[key] = input.checked;
                } else if (input.type === 'number') {
                    // Try parsing as float first, then int, fallback to string
                    const num = parseFloat(input.value);
                    settings[key] = isNaN(num) ? input.value : num;
                } else {
                    settings[key] = input.value;
                }
            }
        });
        return settings;
    },

    // App connections
    checkAppConnections: function() {
        // Fetch the configuration status for all apps
        fetch('/api/configured-apps')
            .then(response => response.json())
            .then(data => {
                this.configuredApps = data;
                // Update status indicators based on the fetched data
                Object.keys(this.configuredApps).forEach(app => {
                    // For now, just update based on configured status
                    // A real connection check might be needed separately
                    this.updateConnectionStatus(app, this.configuredApps[app]); 
                });
            })
            .catch(error => {
                console.error('Error fetching configured apps:', error);
                // Assume all are disconnected on error
                Object.keys(this.configuredApps).forEach(app => {
                    this.updateConnectionStatus(app, false);
                });
            });
    },
    
    // Simplified connection check - maybe call a dedicated /api/status/{app} later
    // checkAppConnection: function(app) { ... },

    updateConnectionStatus: function(app, isConnected) {
        // Update status badges on the Home page
        const statusElement = this.elements[`${app}HomeStatus`];
        if (statusElement) {
            if (isConnected) {
                statusElement.className = 'status-badge connected';
                statusElement.innerHTML = '<i class="fas fa-check-circle"></i> Configured'; // Changed text
            } else {
                statusElement.className = 'status-badge not-connected';
                statusElement.innerHTML = '<i class="fas fa-times-circle"></i> Not Configured'; // Changed text
            }
        }
        // Potentially update status elsewhere (e.g., settings page)
    },

    // User actions
    startHunt: function() {
        fetch('/api/hunt/start', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                this.showNotification(data.message || (data.success ? 'Hunt started' : 'Failed to start hunt'), data.success ? 'success' : 'error');
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
                this.showNotification(data.message || (data.success ? 'Hunt stopped' : 'Failed to stop hunt'), data.success ? 'success' : 'error');
            })
            .catch(error => {
                console.error('Error stopping hunt:', error);
                this.showNotification('Error stopping hunt', 'error');
            });
    },

    // Theme handling
    loadTheme: function() {
        fetch('/api/settings/theme')
            .then(response => response.json())
            .then(data => {
                this.setTheme(data.dark_mode);
            })
            .catch(error => {
                console.error('Error loading theme:', error);
                // Default to dark mode on error?
                this.setTheme(true); 
            });
    },

    setTheme: function(isDark) {
        this.darkMode = isDark;
        if (isDark) {
            document.body.classList.add('dark-theme');
            document.body.classList.remove('light-theme');
        } else {
            document.body.classList.remove('dark-theme');
            document.body.classList.add('light-theme');
        }
        if (this.elements.themeToggle) {
            this.elements.themeToggle.checked = isDark;
        }
        // Store preference
        localStorage.setItem('huntarr-dark-mode', isDark);
    },

    handleThemeToggle: function(e) {
        const isDarkMode = e.target.checked;
        this.setTheme(isDarkMode);
        // Save theme preference to backend
        fetch('/api/settings/theme', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ dark_mode: isDarkMode })
        }).catch(error => console.error('Error saving theme:', error));
    },

    // User info
    loadUsername: function() {
        // Assuming username is fetched elsewhere or passed via template
        // If fetched via API:
        /*
        fetch('/api/user/info') // Example endpoint
            .then(response => response.json())
            .then(data => {
                if (data.username && this.elements.usernameDisplay) {
                    this.elements.usernameDisplay.textContent = data.username;
                }
            })
            .catch(error => console.error('Error loading username:', error));
        */
    },

    // Utility functions
    showNotification: function(message, type = 'info') {
        const container = document.getElementById('notification-container') || document.body;
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        // Remove existing notifications
        const existing = container.querySelector('.notification');
        if (existing) existing.remove();
        
        container.appendChild(notification);

        // Auto-remove after a delay
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => notification.remove(), 500); // Match fade-out duration
        }, 3000);
    },

    capitalizeFirst: function(string) {
        return string ? string.charAt(0).toUpperCase() + string.slice(1) : '';
    }
};