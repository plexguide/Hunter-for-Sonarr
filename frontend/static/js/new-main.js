/**
 * Huntarr - New UI Implementation
 * Main JavaScript file for handling UI interactions and API communication
 */

const HuntarrUI = {
    // Current state
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
        this.loadTheme();
        this.loadUsername();
        this.checkAppConnections();
        this.handleHashNavigation();
        
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
        
        // App tabs
        this.elements.appTabs = document.querySelectorAll('.app-tab');
        this.elements.settingsTabs = document.querySelectorAll('.settings-tab');
        this.elements.appSettingsPanels = document.querySelectorAll('.app-settings-panel');
        
        // Logs
        this.elements.logsContainer = document.getElementById('logsContainer');
        this.elements.autoScrollCheckbox = document.getElementById('autoScrollCheckbox');
        this.elements.clearLogsButton = document.getElementById('clearLogsButton');
        this.elements.logConnectionStatus = document.getElementById('logConnectionStatus');
        
        // Settings
        this.elements.saveSettingsButton = document.getElementById('saveSettingsButton');
        this.elements.resetSettingsButton = document.getElementById('resetSettingsButton');
        
        // Status elements
        this.elements.sonarrHomeStatus = document.getElementById('sonarrHomeStatus');
        this.elements.radarrHomeStatus = document.getElementById('radarrHomeStatus');
        this.elements.lidarrHomeStatus = document.getElementById('lidarrHomeStatus');
        
        // Actions
        this.elements.startHuntButton = document.getElementById('startHuntButton');
        this.elements.stopHuntButton = document.getElementById('stopHuntButton');
        
        // Theme
        this.elements.themeToggle = document.getElementById('themeToggle');
        this.elements.currentPageTitle = document.getElementById('currentPageTitle');
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
        if (this.elements.themeToggle) {
            this.elements.themeToggle.addEventListener('change', this.handleThemeToggle.bind(this));
        }
        
        // Handle window hash change
        window.addEventListener('hashchange', this.handleHashNavigation.bind(this));
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
    
    handleHashNavigation: function() {
        const hash = window.location.hash || '#home';
        const section = hash.substring(1);
        
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
        if (section === 'home' && this.elements.homeSection) {
            this.elements.homeSection.classList.add('active');
            this.elements.homeNav.classList.add('active');
            this.elements.currentPageTitle.textContent = 'Home';
            this.currentSection = 'home';
        } else if (section === 'logs' && this.elements.logsSection) {
            this.elements.logsSection.classList.add('active');
            this.elements.logsNav.classList.add('active');
            this.elements.currentPageTitle.textContent = 'Logs';
            this.currentSection = 'logs';
            this.connectToLogs();
        } else if (section === 'settings' && this.elements.settingsSection) {
            this.elements.settingsSection.classList.add('active');
            this.elements.settingsNav.classList.add('active');
            this.elements.currentPageTitle.textContent = 'Settings';
            this.currentSection = 'settings';
            this.loadAllSettings();
        } else {
            // Default to home
            this.elements.homeSection.classList.add('active');
            this.elements.homeNav.classList.add('active');
            this.elements.currentPageTitle.textContent = 'Home';
            this.currentSection = 'home';
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
        });
        
        const panelElement = document.getElementById(`${tab}Settings`);
        if (panelElement) {
            panelElement.classList.add('active');
            this.currentSettingsTab = tab;
            this.loadSettings(tab);
        }
    },
    
    // Logs handling
    connectToLogs: function() {
        // Disconnect any existing event sources
        this.disconnectAllEventSources();
        
        // Connect to unified logs stream
        this.connectEventSource();
        this.elements.logConnectionStatus.textContent = 'Connecting...';
        this.elements.logConnectionStatus.className = '';
    },
    
    connectEventSource: function() {
        // Close any existing event source
        if (this.eventSources.logs) {
            this.eventSources.logs.close();
        }
        
        try {
            const eventSource = new EventSource(`/logs`);
            
            eventSource.onopen = () => {
                this.elements.logConnectionStatus.textContent = 'Connected';
                this.elements.logConnectionStatus.className = 'status-connected';
            };
            
            eventSource.onmessage = (event) => {
                const logEntry = document.createElement('div');
                logEntry.className = 'log-entry';
                
                // Add appropriate class for log level
                if (event.data.includes(' - INFO - ')) {
                    logEntry.classList.add('log-info');
                } else if (event.data.includes(' - WARNING - ')) {
                    logEntry.classList.add('log-warning');
                } else if (event.data.includes(' - ERROR - ')) {
                    logEntry.classList.add('log-error');
                } else if (event.data.includes(' - DEBUG - ')) {
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
                    if (this.currentSection === 'logs') {
                        this.connectEventSource();
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
        this.loadSettings('global');
        this.loadSettings('sonarr');
        this.loadSettings('radarr');
        this.loadSettings('lidarr');
    },
    
    loadSettings: function(app) {
        fetch(`/api/settings/${app}`)
            .then(response => response.json())
            .then(data => {
                this.populateSettingsForm(app, data);
            })
            .catch(error => {
                console.error(`Error loading ${app} settings:`, error);
            });
    },
    
    populateSettingsForm: function(app, settings) {
        const container = document.getElementById(`${app}Settings`);
        if (!container) return;
        
        // If we already populated this container, don't do it again
        if (container.querySelector('.settings-group')) return;
        
        // Create groups based on settings categories
        const groups = {};
        
        // For demonstration, create some example settings
        // In reality, this would dynamically create settings based on the API response
        if (app === 'sonarr' || app === 'radarr' || app === 'lidarr') {
            container.innerHTML = `
                <div class="settings-group">
                    <h3>${this.capitalizeFirst(app)} Connection</h3>
                    <div class="setting-item">
                        <label for="${app}_url">URL:</label>
                        <input type="text" id="${app}_url" value="${settings.url || ''}">
                        <p class="setting-help">Base URL for ${this.capitalizeFirst(app)} (e.g., http://localhost:8989)</p>
                    </div>
                    <div class="setting-item">
                        <label for="${app}_api_key">API Key:</label>
                        <input type="text" id="${app}_api_key" value="${settings.api_key || ''}">
                        <p class="setting-help">API key for ${this.capitalizeFirst(app)}</p>
                    </div>
                </div>
                
                <div class="settings-group">
                    <h3>Search Settings</h3>
                    <div class="setting-item">
                        <label for="${app}_search_type">Search Type:</label>
                        <select id="${app}_search_type">
                            <option value="random" ${settings.search_type === 'random' ? 'selected' : ''}>Random</option>
                            <option value="sequential" ${settings.search_type === 'sequential' ? 'selected' : ''}>Sequential</option>
                        </select>
                        <p class="setting-help">How to select items to search</p>
                    </div>
                    <div class="setting-item">
                        <label for="${app}_search_interval">Search Interval:</label>
                        <input type="number" id="${app}_search_interval" value="${settings.search_interval || 15}" min="1">
                        <p class="setting-help">Interval between searches (seconds)</p>
                    </div>
                    <div class="setting-item">
                        <label for="${app}_enabled">Enable ${this.capitalizeFirst(app)}:</label>
                        <label class="toggle-switch">
                            <input type="checkbox" id="${app}_enabled" ${settings.enabled ? 'checked' : ''}>
                            <span class="toggle-slider"></span>
                        </label>
                        <p class="setting-help">Toggle ${this.capitalizeFirst(app)} functionality</p>
                    </div>
                </div>
            `;
        }
    },
    
    saveSettings: function() {
        const app = this.currentSettingsTab;
        const settings = this.collectSettingsFromForm(app);
        
        fetch(`/api/settings/${app}`, {
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
                
                // Update connection status if connection settings changed
                if (app !== 'global') {
                    this.checkAppConnection(app);
                }
            } else {
                this.showNotification('Error saving settings', 'error');
            }
        })
        .catch(error => {
            console.error('Error saving settings:', error);
            this.showNotification('Error saving settings', 'error');
        });
    },
    
    resetSettings: function() {
        if (confirm('Are you sure you want to reset these settings to default values?')) {
            const app = this.currentSettingsTab;
            
            fetch(`/api/settings/${app}/reset`, {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.showNotification('Settings reset to defaults', 'success');
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
    
    // Theme handling
    loadTheme: function() {
        fetch('/api/settings/theme')
            .then(response => response.json())
            .then(data => {
                const isDarkMode = data.dark_mode || false;
                // Save to localStorage for page transitions
                localStorage.setItem('huntarr-dark-mode', isDarkMode);
                this.setTheme(isDarkMode);
            })
            .catch(error => {
                console.error('Error loading theme:', error);
            });
    },
    
    // Update theme functions to always use dark theme
    setTheme: function(isDark) {
        // Always force dark mode, ignore isDark parameter
        document.body.classList.add('dark-theme');
        document.body.classList.remove('light-theme');
        localStorage.setItem('huntarr-dark-mode', 'true');
        
        // Update the toggle if it exists
        if (this.elements.themeToggle) {
            this.elements.themeToggle.checked = true;
        }
    },

    handleThemeToggle: function(e) {
        // Force dark mode regardless of toggle state
        this.setTheme(true);
        
        // Store preference in localStorage immediately for page transitions
        localStorage.setItem('huntarr-dark-mode', 'true');
        
        fetch('/api/settings/theme', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ dark_mode: true })
        })
        .catch(error => {
            console.error('Error saving theme:', error);
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
    }
};

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', function() {
    HuntarrUI.init();
    
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
