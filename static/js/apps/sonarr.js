// Sonarr-specific functionality

(function(app) {
    // Add Sonarr-specific initialization
    const sonarrModule = {
        // DOM elements specific to Sonarr
        elements: {
            apiUrlInput: document.getElementById('sonarr_api_url'),
            apiKeyInput: document.getElementById('sonarr_api_key'),
            connectionStatus: document.getElementById('sonarrConnectionStatus'),
            testConnectionButton: document.getElementById('testSonarrConnection'),
            
            // Settings form elements
            huntMissingShowsInput: document.getElementById('hunt_missing_shows'),
            huntUpgradeEpisodesInput: document.getElementById('hunt_upgrade_episodes'),
            sleepDurationInput: document.getElementById('sleep_duration'),
            sleepDurationHoursSpan: document.getElementById('sleep_duration_hours'),
            stateResetIntervalInput: document.getElementById('state_reset_interval_hours'),
            monitoredOnlyInput: document.getElementById('monitored_only'),
            randomMissingInput: document.getElementById('random_missing'),
            randomUpgradesInput: document.getElementById('random_upgrades'),
            skipFutureEpisodesInput: document.getElementById('skip_future_episodes'),
            skipSeriesRefreshInput: document.getElementById('skip_series_refresh'),
            
            // Advanced settings
            apiTimeoutInput: document.getElementById('api_timeout'),
            debugModeInput: document.getElementById('debug_mode'),
            commandWaitDelayInput: document.getElementById('command_wait_delay'),
            commandWaitAttemptsInput: document.getElementById('command_wait_attempts'),
            minimumDownloadQueueSizeInput: document.getElementById('minimum_download_queue_size')
        },
        
        init: function() {
            this.setupEventListeners();
            
            // Extend the core app with Sonarr-specific implementations
            app.loadSettingsSonarr = this.loadSettings.bind(this);
            
            // Override the load settings with Sonarr implementation when Sonarr is active
            const originalLoadSettings = app.loadSettings;
            app.loadSettings = function(appType) {
                if (appType === 'sonarr') {
                    this.loadSettingsSonarr();
                } else {
                    // Only call the original if we're not handling Sonarr
                    if (originalLoadSettings) {
                        originalLoadSettings.call(this, appType);
                    }
                }
            };
            
            // Wire up the specific test connection
            if (this.elements.testConnectionButton) {
                this.elements.testConnectionButton.addEventListener('click', () => {
                    app.testConnection('sonarr', this.elements.apiUrlInput, this.elements.apiKeyInput, this.elements.connectionStatus);
                });
            }
        },
        
        setupEventListeners: function() {
            // Add input event listeners for Sonarr-specific settings
            const inputs = [
                this.elements.apiUrlInput,
                this.elements.apiKeyInput,
                this.elements.huntMissingShowsInput,
                this.elements.huntUpgradeEpisodesInput,
                this.elements.sleepDurationInput,
                this.elements.stateResetIntervalInput,
                this.elements.apiTimeoutInput,
                this.elements.commandWaitDelayInput,
                this.elements.commandWaitAttemptsInput,
                this.elements.minimumDownloadQueueSizeInput
            ];
            
            inputs.forEach(input => {
                if (input) {
                    input.addEventListener('input', this.checkForChanges.bind(this));
                }
            });
            
            const checkboxes = [
                this.elements.monitoredOnlyInput,
                this.elements.randomMissingInput,
                this.elements.randomUpgradesInput,
                this.elements.skipFutureEpisodesInput,
                this.elements.skipSeriesRefreshInput,
                this.elements.debugModeInput
            ];
            
            checkboxes.forEach(checkbox => {
                if (checkbox) {
                    checkbox.addEventListener('change', this.checkForChanges.bind(this));
                }
            });
            
            // Add special handler for sleep duration to update display
            if (this.elements.sleepDurationInput) {
                this.elements.sleepDurationInput.addEventListener('input', () => {
                    this.updateSleepDurationDisplay();
                    this.checkForChanges();
                });
            }
        },
        
        updateSleepDurationDisplay: function() {
            if (this.elements.sleepDurationInput && this.elements.sleepDurationHoursSpan) {
                const seconds = parseInt(this.elements.sleepDurationInput.value) || 900;
                app.updateDurationDisplay(seconds, this.elements.sleepDurationHoursSpan);
            }
        },
        
        loadSettings: function() {
            fetch('/api/settings')
                .then(response => response.json())
                .then(data => {
                    // Get app-specific settings from the new structure
                    const appSettings = data.sonarr || {};
                    
                    // For backward compatibility check the old structure too
                    const huntarr = data.huntarr || {};
                    const advanced = data.advanced || {};
                    
                    // Store original settings for comparison
                    app.originalSettings = JSON.parse(JSON.stringify(data));
                    
                    // Connection settings
                    if (this.elements.apiUrlInput && this.elements.apiKeyInput) {
                        this.elements.apiUrlInput.value = data.api_url || '';
                        this.elements.apiKeyInput.value = data.api_key || '';
                        
                        // Update configured status for sonarr
                        app.configuredApps.sonarr = !!(data.api_url && data.api_key);
                        
                        // Update connection status
                        if (this.elements.connectionStatus) {
                            if (data.api_url && data.api_key) {
                                this.elements.connectionStatus.textContent = 'Configured';
                                this.elements.connectionStatus.className = 'connection-badge connected';
                            } else {
                                this.elements.connectionStatus.textContent = 'Not Configured';
                                this.elements.connectionStatus.className = 'connection-badge not-connected';
                            }
                        }
                    }
                    
                    // Sonarr-specific settings - prefer the app-specific section, fall back to old structure
                    if (this.elements.huntMissingShowsInput) {
                        this.elements.huntMissingShowsInput.value = appSettings.hunt_missing_shows !== undefined ? 
                            appSettings.hunt_missing_shows : (huntarr.hunt_missing_shows !== undefined ? huntarr.hunt_missing_shows : 1);
                    }
                    if (this.elements.huntUpgradeEpisodesInput) {
                        this.elements.huntUpgradeEpisodesInput.value = appSettings.hunt_upgrade_episodes !== undefined ? 
                            appSettings.hunt_upgrade_episodes : (huntarr.hunt_upgrade_episodes !== undefined ? huntarr.hunt_upgrade_episodes : 0);
                    }
                    if (this.elements.sleepDurationInput) {
                        this.elements.sleepDurationInput.value = appSettings.sleep_duration || huntarr.sleep_duration || 900;
                        this.updateSleepDurationDisplay();
                    }
                    if (this.elements.stateResetIntervalInput) {
                        this.elements.stateResetIntervalInput.value = appSettings.state_reset_interval_hours || huntarr.state_reset_interval_hours || 168;
                    }
                    if (this.elements.monitoredOnlyInput) {
                        this.elements.monitoredOnlyInput.checked = appSettings.monitored_only !== false && huntarr.monitored_only !== false;
                    }
                    if (this.elements.skipFutureEpisodesInput) {
                        this.elements.skipFutureEpisodesInput.checked = appSettings.skip_future_episodes !== false && huntarr.skip_future_episodes !== false;
                    }
                    if (this.elements.skipSeriesRefreshInput) {
                        this.elements.skipSeriesRefreshInput.checked = appSettings.skip_series_refresh === true || huntarr.skip_series_refresh === true;
                    }
                    
                    // Advanced settings
                    if (this.elements.apiTimeoutInput) {
                        this.elements.apiTimeoutInput.value = appSettings.api_timeout || advanced.api_timeout || 60;
                    }
                    if (this.elements.debugModeInput) {
                        this.elements.debugModeInput.checked = appSettings.debug_mode === true || advanced.debug_mode === true;
                    }
                    if (this.elements.commandWaitDelayInput) {
                        this.elements.commandWaitDelayInput.value = appSettings.command_wait_delay || advanced.command_wait_delay || 1;
                    }
                    if (this.elements.commandWaitAttemptsInput) {
                        this.elements.commandWaitAttemptsInput.value = appSettings.command_wait_attempts || advanced.command_wait_attempts || 600;
                    }
                    if (this.elements.minimumDownloadQueueSizeInput) {
                        this.elements.minimumDownloadQueueSizeInput.value = appSettings.minimum_download_queue_size || advanced.minimum_download_queue_size || -1;
                    }
                    if (this.elements.randomMissingInput) {
                        this.elements.randomMissingInput.checked = appSettings.random_missing !== false && advanced.random_missing !== false;
                    }
                    if (this.elements.randomUpgradesInput) {
                        this.elements.randomUpgradesInput.checked = appSettings.random_upgrades !== false && advanced.random_upgrades !== false;
                    }
                    
                    // Update home page connection status
                    app.updateHomeConnectionStatus();
                    
                    // Update log connection status if on logs page
                    if (app.elements.logsContainer && app.elements.logsContainer.style.display !== 'none') {
                        app.updateLogsConnectionStatus();
                    }
                    
                    // Initialize save buttons state
                    this.updateSaveButtonState(false);
                })
                .catch(error => console.error('Error loading settings:', error));
        },
        
        checkForChanges: function() {
            if (!app.originalSettings) return false; // Don't check if original settings not loaded
            
            // Get settings from app-specific section first, then fall back to old structure
            const appSettings = app.originalSettings.sonarr || {};
            const huntarrSettings = app.originalSettings.huntarr || {};
            const advancedSettings = app.originalSettings.advanced || {};
            
            let hasChanges = false;
            
            // API connection settings
            if (this.elements.apiUrlInput && this.elements.apiUrlInput.value !== app.originalSettings.api_url) hasChanges = true;
            if (this.elements.apiKeyInput && this.elements.apiKeyInput.value !== app.originalSettings.api_key) hasChanges = true;
            
            // Check Basic Settings - first try app-specific settings, then fall back to old structure
            if (this.elements.huntMissingShowsInput) {
                const originalValue = appSettings.hunt_missing_shows !== undefined ? 
                    appSettings.hunt_missing_shows : huntarrSettings.hunt_missing_shows;
                if (parseInt(this.elements.huntMissingShowsInput.value) !== originalValue) hasChanges = true;
            }
            
            if (this.elements.huntUpgradeEpisodesInput) {
                const originalValue = appSettings.hunt_upgrade_episodes !== undefined ? 
                    appSettings.hunt_upgrade_episodes : huntarrSettings.hunt_upgrade_episodes;
                if (parseInt(this.elements.huntUpgradeEpisodesInput.value) !== originalValue) hasChanges = true;
            }
            
            if (this.elements.sleepDurationInput) {
                const originalValue = appSettings.sleep_duration || huntarrSettings.sleep_duration;
                if (parseInt(this.elements.sleepDurationInput.value) !== originalValue) hasChanges = true;
            }
            
            if (this.elements.stateResetIntervalInput) {
                const originalValue = appSettings.state_reset_interval_hours || huntarrSettings.state_reset_interval_hours;
                if (parseInt(this.elements.stateResetIntervalInput.value) !== originalValue) hasChanges = true;
            }
            
            if (this.elements.monitoredOnlyInput) {
                const originalValue = appSettings.monitored_only !== undefined ? 
                    appSettings.monitored_only : huntarrSettings.monitored_only;
                if (this.elements.monitoredOnlyInput.checked !== originalValue) hasChanges = true;
            }
            
            if (this.elements.skipFutureEpisodesInput) {
                const originalValue = appSettings.skip_future_episodes !== undefined ? 
                    appSettings.skip_future_episodes : huntarrSettings.skip_future_episodes;
                if (this.elements.skipFutureEpisodesInput.checked !== originalValue) hasChanges = true;
            }
            
            if (this.elements.skipSeriesRefreshInput) {
                const originalValue = appSettings.skip_series_refresh === true || huntarrSettings.skip_series_refresh === true;
                if (this.elements.skipSeriesRefreshInput.checked !== originalValue) hasChanges = true;
            }
            
            // Check Advanced Settings
            if (this.elements.apiTimeoutInput) {
                const originalValue = appSettings.api_timeout || advancedSettings.api_timeout;
                if (parseInt(this.elements.apiTimeoutInput.value) !== originalValue) hasChanges = true;
            }
            
            if (this.elements.debugModeInput) {
                const originalValue = appSettings.debug_mode === true || advancedSettings.debug_mode === true;
                if (this.elements.debugModeInput.checked !== originalValue) hasChanges = true;
            }
            
            if (this.elements.commandWaitDelayInput) {
                const originalValue = appSettings.command_wait_delay || advancedSettings.command_wait_delay;
                if (parseInt(this.elements.commandWaitDelayInput.value) !== originalValue) hasChanges = true;
            }
            
            if (this.elements.commandWaitAttemptsInput) {
                const originalValue = appSettings.command_wait_attempts || advancedSettings.command_wait_attempts;
                if (parseInt(this.elements.commandWaitAttemptsInput.value) !== originalValue) hasChanges = true;
            }
            
            if (this.elements.minimumDownloadQueueSizeInput) {
                const originalValue = appSettings.minimum_download_queue_size || advancedSettings.minimum_download_queue_size;
                if (parseInt(this.elements.minimumDownloadQueueSizeInput.value) !== originalValue) hasChanges = true;
            }
            
            if (this.elements.randomMissingInput) {
                const originalValue = appSettings.random_missing !== false && advancedSettings.random_missing !== false;
                if (this.elements.randomMissingInput.checked !== originalValue) hasChanges = true;
            }
            
            if (this.elements.randomUpgradesInput) {
                const originalValue = appSettings.random_upgrades !== false && advancedSettings.random_upgrades !== false;
                if (this.elements.randomUpgradesInput.checked !== originalValue) hasChanges = true;
            }
            
            // Update save buttons state
            this.updateSaveButtonState(hasChanges);
            
            return hasChanges;
        },
        
        updateSaveButtonState: function(hasChanges) {
            if (app.elements.saveSettingsButton && app.elements.saveSettingsBottomButton) {
                app.elements.saveSettingsButton.disabled = !hasChanges;
                app.elements.saveSettingsBottomButton.disabled = !hasChanges;
                
                if (hasChanges) {
                    app.elements.saveSettingsButton.classList.remove('disabled-button');
                    app.elements.saveSettingsBottomButton.classList.remove('disabled-button');
                } else {
                    app.elements.saveSettingsButton.classList.add('disabled-button');
                    app.elements.saveSettingsBottomButton.classList.add('disabled-button');
                }
            }
        },
        
        getSettingsPayload: function() {
            return {
                app_type: 'sonarr',
                api_url: this.elements.apiUrlInput ? this.elements.apiUrlInput.value || '' : '',
                api_key: this.elements.apiKeyInput ? this.elements.apiKeyInput.value || '' : '',
                huntarr: {
                    hunt_missing_shows: this.elements.huntMissingShowsInput ? parseInt(this.elements.huntMissingShowsInput.value) || 0 : 0,
                    hunt_upgrade_episodes: this.elements.huntUpgradeEpisodesInput ? parseInt(this.elements.huntUpgradeEpisodesInput.value) || 0 : 0,
                    sleep_duration: this.elements.sleepDurationInput ? parseInt(this.elements.sleepDurationInput.value) || 900 : 900,
                    state_reset_interval_hours: this.elements.stateResetIntervalInput ? parseInt(this.elements.stateResetIntervalInput.value) || 168 : 168,
                    monitored_only: this.elements.monitoredOnlyInput ? this.elements.monitoredOnlyInput.checked : true,
                    skip_future_episodes: this.elements.skipFutureEpisodesInput ? this.elements.skipFutureEpisodesInput.checked : true,
                    skip_series_refresh: this.elements.skipSeriesRefreshInput ? this.elements.skipSeriesRefreshInput.checked : false
                },
                advanced: {
                    debug_mode: this.elements.debugModeInput ? this.elements.debugModeInput.checked : false,
                    command_wait_delay: this.elements.commandWaitDelayInput ? parseInt(this.elements.commandWaitDelayInput.value) || 1 : 1,
                    command_wait_attempts: this.elements.commandWaitAttemptsInput ? parseInt(this.elements.commandWaitAttemptsInput.value) || 600 : 600,
                    minimum_download_queue_size: this.elements.minimumDownloadQueueSizeInput ? parseInt(this.elements.minimumDownloadQueueSizeInput.value) || -1 : -1,
                    random_missing: this.elements.randomMissingInput ? this.elements.randomMissingInput.checked : true,
                    random_upgrades: this.elements.randomUpgradesInput ? this.elements.randomUpgradesInput.checked : true,
                    api_timeout: this.elements.apiTimeoutInput ? parseInt(this.elements.apiTimeoutInput.value) || 60 : 60
                }
            };
        }
    };
    
    // Initialize Sonarr module
    sonarrModule.init();
    
    // Override app.saveSettings to handle Sonarr-specific logic when Sonarr is active
    const originalSaveSettings = app.saveSettings;
    app.saveSettings = function() {
        if (app.currentApp === 'sonarr') {
            if (!sonarrModule.checkForChanges()) {
                // If no changes, don't do anything
                return;
            }
            
            const settings = sonarrModule.getSettingsPayload();
            
            fetch('/api/settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(settings)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update original settings after successful save
                    app.originalSettings.api_url = settings.api_url;
                    app.originalSettings.api_key = settings.api_key;
                    
                    // Update the app-specific settings
                    if (!app.originalSettings.sonarr) {
                        app.originalSettings.sonarr = {};
                    }
                    
                    // Copy settings to both the app-specific section and legacy sections
                    if (settings.huntarr) {
                        // Update legacy structure
                        app.originalSettings.huntarr = {...settings.huntarr};
                        
                        // Update new app-specific structure
                        for (const key in settings.huntarr) {
                            app.originalSettings.sonarr[key] = settings.huntarr[key];
                        }
                    }
                    
                    if (settings.advanced) {
                        app.originalSettings.advanced = {...settings.advanced};
                        
                        // Copy advanced settings to app-specific section
                        for (const key in settings.advanced) {
                            app.originalSettings.sonarr[key] = settings.advanced[key];
                        }
                    }
                    
                    // Update configuration status
                    app.configuredApps.sonarr = !!(settings.api_url && settings.api_key);
                    
                    // Update connection status
                    app.updateConnectionStatus();
                    
                    // Update home page connection status
                    app.updateHomeConnectionStatus();
                    
                    // Update logs connection status
                    app.updateLogsConnectionStatus();
                    
                    // Disable save buttons
                    sonarrModule.updateSaveButtonState(false);
                    
                    // Show success message
                    if (data.changes_made) {
                        alert('Settings saved successfully and cycle restarted to apply changes!');
                    } else {
                        alert('No changes detected.');
                    }
                } else {
                    alert('Error saving settings: ' + (data.message || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Error saving settings:', error);
                alert('Error saving settings: ' + error.message);
            });
        } else if (originalSaveSettings) {
            // Call the original if we're not handling Sonarr
            originalSaveSettings.call(app);
        }
    };
    
    // Add the Sonarr module to the app for reference
    app.sonarrModule = sonarrModule;

})(window.huntarrApp);
