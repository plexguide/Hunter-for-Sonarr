// Core functionality for Huntarr Sonarr
// Simplified to support only Sonarr

// Global state
const huntarrApp = {
    // Current app is always sonarr
    currentApp: 'sonarr',
    
    // Track if Sonarr is configured
    configuredApps: {
        sonarr: false
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
        
        // Load settings
        this.loadSettings();
        
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
        
        // Connection status elements
        this.elements.sonarrHomeStatus = document.getElementById('sonarrHomeStatus');
        
        // Save and reset buttons
        this.elements.saveSettingsButton = document.getElementById('saveSettings');
        this.elements.resetSettingsButton = document.getElementById('resetSettings');
        this.elements.saveSettingsBottomButton = document.getElementById('saveSettingsBottom');
        this.elements.resetSettingsBottomButton = document.getElementById('resetSettingsBottom');
    },
    
    // Set up event listeners
    setupEventListeners: function() {
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
        
        // Reconnect to logs if configured
        if (this.elements.logsElement && this.configuredApps.sonarr) {
            this.connectEventSource();
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
        
        // Show Sonarr settings
        document.getElementById('sonarrSettings').style.display = 'block';
        
        // Make sure settings are loaded
        this.loadSettings();
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
        
        // Connect to logs if we're on the logs page and sonarr is configured
        if (this.elements.logsElement && this.elements.logsContainer && 
            this.elements.logsContainer.style.display !== 'none' && 
            this.configuredApps.sonarr) {
            this.connectEventSource();
        }
    },
    
    // Theme management
    loadTheme: function() {
        // Always set to dark mode
        this.setTheme(true);
        
        // Update server setting to dark mode
        fetch('/api/settings/theme', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ dark_mode: true })
        })
        .catch(error => console.error('Error saving theme:', error));
    },
    
    setTheme: function(isDark) {
        // Always force dark mode
        document.body.classList.add('dark-theme');
        document.body.classList.remove('light-theme');
        
        if (this.elements.themeToggle) {
            this.elements.themeToggle.checked = true;
        }
        
        if (this.elements.themeLabel) {
            this.elements.themeLabel.textContent = 'Dark Mode';
        }
    },

    handleThemeToggle: function(e) {
        // Force dark mode regardless of toggle
        this.setTheme(true);
        
        // Save to localStorage
        localStorage.setItem('huntarr-dark-mode', 'true');
        
        // Send theme preference to server
        fetch('/api/settings/theme', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ dark_mode: true })
        })
        .catch(error => {
            console.error('Error saving theme preference:', error);
        });
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
    connectEventSource: function() {
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
                
                // Update UI elements
                this.updateStatusElement(this.elements.sonarrHomeStatus, this.configuredApps.sonarr);
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
            if (this.configuredApps.sonarr) {
                this.elements.statusElement.textContent = 'Connected';
                this.elements.statusElement.className = 'status-connected';
            } else {
                this.elements.statusElement.textContent = 'Disconnected';
                this.elements.statusElement.className = 'status-disconnected';
            }
        }
    },
    
    updateConnectionStatus: function() {
        const connectionElement = document.getElementById('sonarrConnectionStatus');
        if (connectionElement) {
            this.updateStatusElement(connectionElement, this.configuredApps.sonarr);
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
    loadSettings: function() {
        // This function will be overridden by app-specific module
        // The sonarr module will attach its own implementation to huntarrApp
    },
    
    saveSettings: function() {
        // This function will be overridden by app-specific module
        // The sonarr module will attach its own implementation to huntarrApp
    },
    
    resetSettings: function() {
        if (confirm('Are you sure you want to reset all settings to default values?')) {
            fetch('/api/settings/reset', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Settings reset to defaults and cycle restarted.');
                    this.loadSettings();
                    
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
    
    // Test connection function for Sonarr
    testConnection: function(urlInput, keyInput, statusElement) {
        const apiUrl = urlInput.value;
        const apiKey = keyInput.value;
        
        if (!apiUrl || !apiKey) {
            alert('Please enter both API URL and API Key for Sonarr before testing the connection.');
            return;
        }
        
        // Test API connection
        if (statusElement) {
            statusElement.textContent = 'Testing...';
            statusElement.className = 'connection-badge';
        }
        
        fetch('/sonarr/test-connection', {
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
                this.configuredApps.sonarr = true;
                
                // Update home page status
                this.updateHomeConnectionStatus();
            } else {
                if (statusElement) {
                    statusElement.textContent = 'Connection Failed';
                    statusElement.className = 'connection-badge not-connected';
                }
                
                // Update configuration status
                this.configuredApps.sonarr = false;
                
                alert(`Connection failed: ${data.message}`);
            }
        })
        .catch(error => {
            console.error('Error testing Sonarr connection:', error);
            if (statusElement) {
                statusElement.textContent = 'Connection Error';
                statusElement.className = 'connection-badge not-connected';
            }
            
            // Update configuration status
            this.configuredApps.sonarr = false;
            
            alert('Error testing Sonarr connection: ' + error.message);
        });
    },
    
    // Duration utility function
    updateSleepDurationDisplay: function() {
        // This will be called from the sonarr app-specific module
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
