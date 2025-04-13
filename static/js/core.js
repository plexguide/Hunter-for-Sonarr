// Core functionality used across all application modules

// Global state
const huntarrApp = {
    // Current selected app
    currentApp: 'sonarr',
    
    // Track which apps are configured
    configuredApps: {
        sonarr: false,
        radarr: false,
        lidarr: false,
        readarr: false
    },
    
    // Store original settings values
    originalSettings: {},
    
    // Event source for logs
    eventSource: null,
    
    // DOM references to common elements
    elements: {},
    
    // Initialize the application
    init: function() {
        // Cache DOM elements
        this.cacheElements();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Initialize theme
        this.loadTheme();
        
        // Update sleep duration displays
        this.updateSleepDurationDisplay();
        
        // Get user info for welcome page
        this.getUserInfo();
        
        // Load settings for initial app
        this.loadSettings(this.currentApp);
        
        // Navigate based on URL path
        this.handleNavigation();
    },
    
    // Cache DOM elements
    cacheElements: function() {
        // Navigation elements
        this.elements.homeButton = document.getElementById('homeButton');
        this.elements.logsButton = document.getElementById('logsButton');
        this.elements.settingsButton = document.getElementById('settingsButton');
        this.elements.userButton = document.getElementById('userButton');
        
        // Container elements
        this.elements.homeContainer = document.getElementById('homeContainer');
        this.elements.logsContainer = document.getElementById('logsContainer');
        this.elements.settingsContainer = document.getElementById('settingsContainer');
        
        // Logs elements
        this.elements.logsElement = document.getElementById('logs');
        this.elements.statusElement = document.getElementById('status');
        this.elements.clearLogsButton = document.getElementById('clearLogs');
        this.elements.autoScrollCheckbox = document.getElementById('autoScroll');
        
        // Theme elements
        this.elements.themeToggle = document.getElementById('themeToggle');
        this.elements.themeLabel = document.getElementById('themeLabel');
        
        // App tabs
        this.elements.appTabs = document.querySelectorAll('.app-tab');
        this.elements.appSettings = document.querySelectorAll('.app-settings');
        
        // Connection status elements
        this.elements.sonarrHomeStatus = document.getElementById('sonarrHomeStatus');
        this.elements.radarrHomeStatus = document.getElementById('radarrHomeStatus');
        this.elements.lidarrHomeStatus = document.getElementById('lidarrHomeStatus');
        this.elements.readarrHomeStatus = document.getElementById('readarrHomeStatus');
        
        // Save and reset buttons
        this.elements.saveSettingsButton = document.getElementById('saveSettings');
        this.elements.resetSettingsButton = document.getElementById('resetSettings');
        this.elements.saveSettingsBottomButton = document.getElementById('saveSettingsBottom');
        this.elements.resetSettingsBottomButton = document.getElementById('resetSettingsBottom');
    },
    
    // Set up event listeners
    setupEventListeners: function() {
        // App tab selection
        this.elements.appTabs.forEach(tab => {
            tab.addEventListener('click', this.handleAppTabClick.bind(this));
        });
        
        // Navigation
        if (this.elements.homeButton && this.elements.logsButton && this.elements.settingsButton) {
            this.elements.homeButton.addEventListener('click', this.navigateToHome.bind(this));
            this.elements.logsButton.addEventListener('click', this.navigateToLogs.bind(this));
            this.elements.settingsButton.addEventListener('click', this.navigateToSettings.bind(this));
            this.elements.userButton.addEventListener('click', this.navigateToUser.bind(this));
        }
        
        // Log management
        if (this.elements.clearLogsButton) {
            this.elements.clearLogsButton.addEventListener('click', this.clearLogs.bind(this));
        }
        
        // Auto-scroll
        if (this.elements.logsElement) {
            this.elements.logsElement.addEventListener('scroll', this.handleLogsScroll.bind(this));
        }
        
        if (this.elements.autoScrollCheckbox) {
            this.elements.autoScrollCheckbox.addEventListener('change', this.handleAutoScrollChange.bind(this));
        }
        
        // Theme toggle
        if (this.elements.themeToggle) {
            this.elements.themeToggle.addEventListener('change', this.handleThemeToggle.bind(this));
        }
        
        // Save and reset settings
        if (this.elements.saveSettingsButton && this.elements.resetSettingsButton) {
            this.elements.saveSettingsButton.addEventListener('click', this.saveSettings.bind(this));
            this.elements.resetSettingsButton.addEventListener('click', this.resetSettings.bind(this));
            this.elements.saveSettingsBottomButton.addEventListener('click', this.saveSettings.bind(this));
            this.elements.resetSettingsBottomButton.addEventListener('click', this.resetSettings.bind(this));
        }
    },
    
    // Handle app tab click
    handleAppTabClick: function(event) {
        const app = event.currentTarget.dataset.app;
        
        // If it's already the active app, do nothing
        if (app === this.currentApp) return;
        
        // Update active tab
        this.elements.appTabs.forEach(t => t.classList.remove('active'));
        event.currentTarget.classList.add('active');
        
        // Update active settings panel if on settings page
        if (this.elements.settingsContainer && this.elements.settingsContainer.style.display !== 'none') {
            this.elements.appSettings.forEach(s => s.style.display = 'none');
            document.getElementById(`${app}Settings`).style.display = 'block';
        }
        
        // Update current app
        this.currentApp = app;
        
        // Load settings for this app
        this.loadSettings(app);
        
        // For logs, refresh the log stream
        if (this.elements.logsElement && this.elements.logsContainer && this.elements.logsContainer.style.display !== 'none') {
            // Clear the logs first
            this.elements.logsElement.innerHTML = '';
            
            // Update connection status based on configuration
            this.updateLogsConnectionStatus();
            
            // Reconnect the event source only if app is configured
            if (this.configuredApps[app]) {
                this.connectEventSource(app);
            }
        }
    },
    
    // Navigation functions
    navigateToHome: function() {
        this.elements.homeContainer.style.display = 'flex';
        this.elements.logsContainer.style.display = 'none';
        this.elements.settingsContainer.style.display = 'none';
        
        this.elements.homeButton.classList.add('active');
        this.elements.logsButton.classList.remove('active');
        this.elements.settingsButton.classList.remove('active');
        this.elements.userButton.classList.remove('active');
        
        // Update connection status on home page
        this.updateHomeConnectionStatus();
    },
    
    navigateToLogs: function() {
        this.elements.homeContainer.style.display = 'none';
        this.elements.logsContainer.style.display = 'flex';
        this.elements.settingsContainer.style.display = 'none';
        
        this.elements.homeButton.classList.remove('active');
        this.elements.logsButton.classList.add('active');
        this.elements.settingsButton.classList.remove('active');
        this.elements.userButton.classList.remove('active');
        
        // Update the connection status based on configuration
        this.updateLogsConnectionStatus();
        
        // Reconnect to logs for the current app if configured
        if (this.elements.logsElement && this.configuredApps[this.currentApp]) {
            this.connectEventSource(this.currentApp);
        }
    },
    
    navigateToSettings: function() {
        this.elements.homeContainer.style.display = 'none';
        this.elements.logsContainer.style.display = 'none';
        this.elements.settingsContainer.style.display = 'flex';
        
        this.elements.homeButton.classList.remove('active');
        this.elements.logsButton.classList.remove('active');
        this.elements.settingsButton.classList.add('active');
        this.elements.userButton.classList.remove('active');
        
        // Show the settings for the current app
        this.elements.appSettings.forEach(s => s.style.display = 'none');
        document.getElementById(`${this.currentApp}Settings`).style.display = 'block';
        
        // Make sure settings are loaded
        this.loadSettings(this.currentApp);
    },
    
    navigateToUser: function() {
        window.location.href = '/user';
    },
    
    // Handle navigation based on URL path
    handleNavigation: function() {
        const path = window.location.pathname;
        
        if (path === '/settings') {
            this.navigateToSettings();
        } else if (path === '/') {
            this.navigateToHome();
        }
        
        // Connect to logs if we're on the logs page and the current app is configured
        if (this.elements.logsElement && this.elements.logsContainer && 
            this.elements.logsContainer.style.display !== 'none' && 
            this.configuredApps[this.currentApp]) {
            this.connectEventSource(this.currentApp);
        }
    },
    
    // Theme management
    loadTheme: function() {
        fetch('/api/settings/theme')
            .then(response => response.json())
            .then(data => {
                const isDarkMode = data.dark_mode || false;
                this.setTheme(isDarkMode);
                if (this.elements.themeToggle) this.elements.themeToggle.checked = isDarkMode;
                if (this.elements.themeLabel) this.elements.themeLabel.textContent = isDarkMode ? 'Dark Mode' : 'Light Mode';
            })
            .catch(error => console.error('Error loading theme:', error));
    },
    
    setTheme: function(isDark) {
        if (isDark) {
            document.body.classList.add('dark-theme');
            if (this.elements.themeLabel) this.elements.themeLabel.textContent = 'Dark Mode';
        } else {
            document.body.classList.remove('dark-theme');
            if (this.elements.themeLabel) this.elements.themeLabel.textContent = 'Light Mode';
        }
    },
    
    handleThemeToggle: function(event) {
        const isDarkMode = event.target.checked;
        this.setTheme(isDarkMode);
        
        fetch('/api/settings/theme', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ dark_mode: isDarkMode })
        })
        .catch(error => console.error('Error saving theme:', error));
    },
    
    // Log management
    clearLogs: function() {
        if (this.elements.logsElement) {
            this.elements.logsElement.innerHTML = '';
        }
    },
    
    scrollToBottom: function() {
        if (this.elements.autoScrollCheckbox && this.elements.autoScrollCheckbox.checked && this.elements.logsElement) {
            this.elements.logsElement.scrollTop = this.elements.logsElement.scrollHeight;
        }
    },
    
    handleLogsScroll: function() {
        // If we're at the bottom or near it (within 20px), ensure auto-scroll stays on
        const atBottom = (this.elements.logsElement.scrollHeight - this.elements.logsElement.scrollTop - this.elements.logsElement.clientHeight) < 20;
        if (!atBottom && this.elements.autoScrollCheckbox && this.elements.autoScrollCheckbox.checked) {
            // User manually scrolled up, disable auto-scroll
            this.elements.autoScrollCheckbox.checked = false;
        }
    },
    
    handleAutoScrollChange: function(event) {
        if (event.target.checked) {
            this.scrollToBottom();
        }
    },
    
    // Event source for logs
    connectEventSource: function(app) {
        if (!this.elements.logsElement) return; // Skip if not on logs page
        
        if (this.eventSource) {
            this.eventSource.close();
        }
        
        this.eventSource = new EventSource(`/logs`);
        
        this.eventSource.onopen = () => {
            if (this.elements.statusElement) {
                this.elements.statusElement.textContent = 'Connected';
                this.elements.statusElement.className = 'status-connected';
            }
        };
        
        this.eventSource.onerror = () => {
            if (this.elements.statusElement) {
                this.elements.statusElement.textContent = 'Disconnected';
                this.elements.statusElement.className = 'status-disconnected';
            }
            
            // Attempt to reconnect after 5 seconds
            setTimeout(() => {
                this.connectEventSource();
            }, 5000);
        };
        
        this.eventSource.onmessage = (event) => {
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
            this.elements.logsElement.appendChild(logEntry);
            
            // Auto-scroll to bottom if enabled
            this.scrollToBottom();
        };
    },
    
    // Status updates
    updateHomeConnectionStatus: function() {
        // Check current configured state
        fetch('/api/configured-apps')
            .then(response => response.json())
            .then(data => {
                // Update the configuredApps object
                this.configuredApps.sonarr = data.sonarr || false;
                this.configuredApps.radarr = data.radarr || false;
                this.configuredApps.lidarr = data.lidarr || false;
                this.configuredApps.readarr = data.readarr || false;
                
                // Update UI elements
                this.updateStatusElement(this.elements.sonarrHomeStatus, this.configuredApps.sonarr);
                this.updateStatusElement(this.elements.radarrHomeStatus, this.configuredApps.radarr);
                this.updateStatusElement(this.elements.lidarrHomeStatus, this.configuredApps.lidarr);
                this.updateStatusElement(this.elements.readarrHomeStatus, this.configuredApps.readarr);
            })
            .catch(error => console.error('Error checking configured apps:', error));
    },
    
    updateStatusElement: function(element, isConfigured) {
        if (element) {
            if (isConfigured) {
                element.textContent = 'Configured';
                element.className = 'connection-badge connected';
            } else {
                element.textContent = 'Not Configured';
                element.className = 'connection-badge not-connected';
            }
        }
    },
    
    updateLogsConnectionStatus: function() {
        if (this.elements.statusElement) {
            if (this.configuredApps[this.currentApp]) {
                this.elements.statusElement.textContent = 'Connected';
                this.elements.statusElement.className = 'status-connected';
            } else {
                this.elements.statusElement.textContent = 'Disconnected';
                this.elements.statusElement.className = 'status-disconnected';
            }
        }
    },
    
    updateConnectionStatus: function() {
        const appConnectionElements = {
            'sonarr': document.getElementById('sonarrConnectionStatus'),
            'radarr': document.getElementById('radarrConnectionStatus'),
            'lidarr': document.getElementById('lidarrConnectionStatus'),
            'readarr': document.getElementById('readarrConnectionStatus')
        };
        
        const connectionElement = appConnectionElements[this.currentApp];
        if (connectionElement) {
            this.updateStatusElement(connectionElement, this.configuredApps[this.currentApp]);
        }
    },
    
    // User info
    getUserInfo: function() {
        const username = document.getElementById('username');
        if (username) {
            username.textContent = 'User'; // Default placeholder
        }
    },
    
    // Settings functions - generic common operations (app-specific logic in app modules)
    loadSettings: function(app) {
        // This function will be overridden by app-specific modules
        // Each app module will attach its own implementation to huntarrApp
    },
    
    saveSettings: function() {
        // This function will be overridden by app-specific modules
        // Each app module will attach its own implementation to huntarrApp
    },
    
    resetSettings: function() {
        if (confirm('Are you sure you want to reset all settings to default values?')) {
            fetch('/api/settings/reset', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    app: this.currentApp
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Settings reset to defaults and cycle restarted.');
                    this.loadSettings(this.currentApp);
                    
                    // Update home page connection status
                    this.updateHomeConnectionStatus();
                    
                    // Update logs connection status
                    this.updateLogsConnectionStatus();
                } else {
                    alert('Error resetting settings: ' + (data.message || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Error resetting settings:', error);
                alert('Error resetting settings: ' + error.message);
            });
        }
    },
    
    // Test connection function - works for all apps
    testConnection: function(app, urlInput, keyInput, statusElement) {
        const apiUrl = urlInput.value;
        const apiKey = keyInput.value;
        
        if (!apiUrl || !apiKey) {
            alert(`Please enter both API URL and API Key for ${app.charAt(0).toUpperCase() + app.slice(1)} before testing the connection.`);
            return;
        }
        
        // Test API connection
        if (statusElement) {
            statusElement.textContent = 'Testing...';
            statusElement.className = 'connection-badge';
        }
        
        // Use the correct endpoint URL based on the app type
        fetch(`/${app}/test-connection`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                api_url: apiUrl,
                api_key: apiKey
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (statusElement) {
                    statusElement.textContent = 'Connected';
                    statusElement.className = 'connection-badge connected';
                }
                
                // Update configuration status
                this.configuredApps[app] = true;
                
                // Update home page status
                this.updateHomeConnectionStatus();
            } else {
                if (statusElement) {
                    statusElement.textContent = 'Connection Failed';
                    statusElement.className = 'connection-badge not-connected';
                }
                
                // Update configuration status
                this.configuredApps[app] = false;
                
                alert(`Connection failed: ${data.message}`);
            }
        })
        .catch(error => {
            console.error(`Error testing ${app} connection:`, error);
            if (statusElement) {
                statusElement.textContent = 'Connection Error';
                statusElement.className = 'connection-badge not-connected';
            }
            
            // Update configuration status
            this.configuredApps[app] = false;
            
            alert(`Error testing ${app} connection: ` + error.message);
        });
    },
    
    // Duration utility function
    updateSleepDurationDisplay: function() {
        // This will be called from app-specific modules
    },
    
    updateDurationDisplay: function(seconds, spanElement) {
        if (!spanElement) return;
        
        let displayText = '';
        
        if (seconds < 60) {
            displayText = `${seconds} seconds`;
        } else if (seconds < 3600) {
            const minutes = Math.floor(seconds / 60);
            displayText = `≈ ${minutes} minute${minutes !== 1 ? 's' : ''}`;
        } else {
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            if (minutes === 0) {
                displayText = `≈ ${hours} hour${hours !== 1 ? 's' : ''}`;
            } else {
                displayText = `≈ ${hours} hour${hours !== 1 ? 's' : ''} ${minutes} minute${minutes !== 1 ? 's' : ''}`;
            }
        }
        
        spanElement.textContent = displayText;
    }
};

// Export the huntarrApp object for use in other modules
window.huntarrApp = huntarrApp;
