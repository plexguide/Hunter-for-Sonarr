// Main entry point for Huntarr application

// Wait for DOM content to be loaded before initializing the app
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the core application
    if (window.huntarrApp) {
        window.huntarrApp.init();
    } else {
        console.error('Error: Huntarr core module not loaded');
    }
});

// Add to the initialization section
const HuntarrApp = {
    init: function() {
        // ...existing code...
        
        // Initialize settings if we're on the settings page
        if (window.location.pathname === '/settings' || window.location.hash === '#settings') {
            this.initializeSettings();
        }
    },
    
    // ...existing code...
    
    // Add this new method
    initializeSettings: function() {
        console.log("Initializing settings...");
        
        // Make sure the settings tab buttons exist
        const settingsTabs = document.querySelectorAll('.settings-tab');
        if (settingsTabs.length > 0) {
            // Find the active tab
            const activeTab = document.querySelector('.settings-tab.active');
            if (activeTab) {
                const tabName = activeTab.getAttribute('data-settings');
                console.log("Loading settings for: " + tabName);
                
                // Load settings for the active tab
                this.loadSettings(tabName);
                
                // Set up event listeners for tab switching if not already done
                settingsTabs.forEach(tab => {
                    tab.addEventListener('click', (e) => {
                        // Update active tab
                        settingsTabs.forEach(t => t.classList.remove('active'));
                        e.target.classList.add('active');
                        
                        // Show selected settings panel
                        const app = e.target.getAttribute('data-settings');
                        const panels = document.querySelectorAll('.app-settings-panel');
                        panels.forEach(panel => panel.classList.remove('active'));
                        
                        const selectedPanel = document.getElementById(`${app}Settings`);
                        if (selectedPanel) {
                            selectedPanel.classList.add('active');
                            this.loadSettings(app);
                        }
                    });
                });
            }
        }
    },
    
    // Modify the loadSettings method to ensure it's logging and running correctly
    loadSettings: function(app) {
        console.log(`Loading settings for ${app}...`);
        
        fetch(`/api/settings/${app}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to fetch settings');
                }
                return response.json();
            })
            .then(data => {
                console.log(`Settings data for ${app}:`, data);
                const container = document.getElementById(`${app}Settings`);
                if (!container) {
                    console.error(`Container for ${app} settings not found`);
                    return;
                }
                
                // Clear previous content
                container.innerHTML = '';
                
                // Use the appropriate form generator based on app
                switch(app) {
                    case 'sonarr':
                        SettingsForms.generateSonarrForm(container, data);
                        break;
                    case 'radarr':
                        SettingsForms.generateRadarrForm(container, data);
                        break;
                    case 'lidarr':
                        SettingsForms.generateLidarrForm(container, data);
                        break;
                    case 'readarr':
                        SettingsForms.generateReadarrForm(container, data);
                        break;
                    case 'global':
                        SettingsForms.generateGlobalForm(container, data);
                        break;
                }
                
                // Update any duration displays
                if (typeof SettingsForms.updateDurationDisplay === 'function') {
                    SettingsForms.updateDurationDisplay();
                }
            })
            .catch(error => {
                console.error(`Error loading ${app} settings:`, error);
                const container = document.getElementById(`${app}Settings`);
                if (container) {
                    container.innerHTML = `<div class="error-message">Error loading settings: ${error.message}</div>`;
                }
            });
    },
    
    // ...existing code...
};

// Initialize the app when the DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    HuntarrApp.init();
});

// ...existing code...
            panelElement.classList.add('active');
            this.currentSettingsTab = tab;
            this.loadSettings(tab);
        }
    },
    
    // Logs handling
    connectToLogs: function() {
        // Disconnect any existing event sources
        this.disconnectAllEventSources();
        
        if (this.configuredApps[this.currentApp]) {
            this.connectEventSource(this.currentApp);
            this.elements.logConnectionStatus.textContent = 'Connecting...';
            this.elements.logConnectionStatus.className = '';
        } else {
            this.elements.logConnectionStatus.textContent = 'Not Configured';
            this.elements.logConnectionStatus.className = 'status-disconnected';
        }
    },
    
    connectEventSource: function(app) {
        if (this.eventSources[app]) {
            this.eventSources[app].close();
        }
        
        try {
            const eventSource = new EventSource(`/api/logs/${app}`);
            
            eventSource.onopen = () => {
                this.elements.logConnectionStatus.textContent = 'Connected';
                this.elements.logConnectionStatus.className = 'status-connected';
            };
            
            eventSource.onmessage = (event) => {
                const logData = JSON.parse(event.data);
                this.addLogMessage(logData);
            };
            
            eventSource.onerror = () => {
                this.elements.logConnectionStatus.textContent = 'Disconnected';
                this.elements.logConnectionStatus.className = 'status-disconnected';
                
                // Try to reconnect after a delay
                setTimeout(() => {
                    if (this.currentSection === 'logs' && this.currentApp === app) {
                        this.connectEventSource(app);
                    }
                }, 5000);
            };
            
            this.eventSources[app] = eventSource;
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
                this.setTheme(isDarkMode);
            })
            .catch(error => {
                console.error('Error loading theme:', error);
            });
    },
    
    setTheme: function(isDark) {
        this.darkMode = isDark;
        
        if (isDark) {
            document.body.classList.add('dark-theme');
        } else {
            document.body.classList.remove('dark-theme');
        }
        
        if (this.elements.themeToggle) {
            this.elements.themeToggle.checked = isDark;
        }
    },
    
    handleThemeToggle: function(e) {
        const isDarkMode = e.target.checked;
        this.setTheme(isDarkMode);
        
        fetch('/api/settings/theme', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ dark_mode: isDarkMode })
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
});