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
                } else if (originalLoadSettings) {
                    // Only call the original if we're not handling Sonarr
                    originalLoadSettings.call(this, appType);
                }
            };
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
            
            // Wire up the specific test connection
            if (this.elements.testConnectionButton) {
                this.elements.testConnectionButton.addEventListener('click', () => {
                    app.testConnection('sonarr', this.elements.apiUrlInput, this.elements.apiKeyInput, this.elements.connectionStatus);
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
                    const huntarr = data.huntarr || {};
                    const advanced = data.advanced || {};
                    
                    // Store original settings for comparison
                    app.originalSettings = JSON.parse(JSON.stringify(data));
                    
                    // For Sonarr, load from app-settings endpoint
                    fetch(`/api/app-settings?app=sonarr`)
                        .then(response => response.json())
                        .then(appData => {
                            if (appData.success) {
                                this.elements.apiUrlInput.value = appData.api_url || '';
                                this.elements.apiKeyInput.value = appData.api_key || '';
                                
                                // Store original values in data attributes for comparison
                                this.elements.apiUrlInput.dataset.originalValue = appData.api_url || '';
                                this.elements.apiKeyInput.dataset.originalValue = appData.api_key || '';
                                
                                // Update configured status
                                app.configuredApps.sonarr = !!(appData.api_url && appData.api_key);
                                
                                // Update connection status
                                if (this.elements.connectionStatus) {
                                    if (appData.api_url && appData.api_key) {
                                        this.elements.connectionStatus.textContent = 'Configured';
                                        this.elements.connectionStatus.className = 'connection-badge connected';
                                    } else {
                                        this.elements.connectionStatus.textContent = 'Not Configured';
                                        this.elements.connectionStatus.className = 'connection-badge not-connected';
                                    }
                                }
                            }
                            
                            // Sonarr-specific settings
                            if (this.elements.huntMissingShowsInput) {
                                this.elements.huntMissingShowsInput.value = huntarr.hunt_missing_shows !== undefined ? huntarr.hunt_missing_shows : 1;
                            }
                            if (this.elements.huntUpgradeEpisodesInput) {
                                this.elements.huntUpgradeEpisodesInput.value = huntarr.hunt_upgrade_episodes !== undefined ? huntarr.hunt_upgrade_episodes : 0;
                            }
                            if (this.elements.sleepDurationInput) {
                                this.elements.sleepDurationInput.value = huntarr.sleep_duration || 900;
                                this.updateSleepDurationDisplay();
                            }
                            if (this.elements.stateResetIntervalInput) {
                                this.elements.stateResetIntervalInput.value = huntarr.state_reset_interval_hours || 168;
                            }
                            if (this.elements.monitoredOnlyInput) {
                                this.elements.monitoredOnlyInput.checked = huntarr.monitored_only !== false;
                            }
                            if (this.elements.skipFutureEpisodesInput) {
                                this.elements.skipFutureEpisodesInput.checked = huntarr.skip_future_episodes !== false;
                            }
                            if (this.elements.skipSeriesRefreshInput) {
                                this.elements.skipSeriesRefreshInput.checked = huntarr.skip_series_refresh === true;
                            }
                            
                            // Advanced settings
                            if (this.elements.apiTimeoutInput) {
                                this.elements.apiTimeoutInput.value = advanced.api_timeout || 60;
                            }
                            if (this.elements.debugModeInput) {
                                this.elements.debugModeInput.checked = advanced.debug_mode === true;
                            }
                            if (this.elements.commandWaitDelayInput) {
                                this.elements.commandWaitDelayInput.value = advanced.command_wait_delay || 1;
                            }
                            if (this.elements.commandWaitAttemptsInput) {
                                this.elements.commandWaitAttemptsInput.value = advanced.command_wait_attempts || 600;
                            }
                            if (this.elements.minimumDownloadQueueSizeInput) {
                                this.elements.minimumDownloadQueueSizeInput.value = advanced.minimum_download_queue_size || -1;
                            }
                            if (this.elements.randomMissingInput) {
                                this.elements.randomMissingInput.checked = advanced.random_missing !== false;
                            }
                            if (this.elements.randomUpgradesInput) {
                                this.elements.randomUpgradesInput.checked = advanced.random_upgrades !== false;
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
                        .catch(error => {
                            console.error('Error loading Sonarr settings:', error);
                            
                            // Default values
                            this.elements.apiUrlInput.value = '';
                            this.elements.apiKeyInput.value = '';
                            this.elements.apiUrlInput.dataset.originalValue = '';
                            this.elements.apiKeyInput.dataset.originalValue = '';
                            app.configuredApps.sonarr = false;
                            
                            if (this.elements.connectionStatus) {
                                this.elements.connectionStatus.textContent = 'Not Configured';
                                this.elements.connectionStatus.className = 'connection-badge not-connected';
                            }
                            
                            // Update home page connection status
                            app.updateHomeConnectionStatus();
                            
                            // Update log connection status if on logs page
                            if (app.elements.logsContainer && app.elements.logsContainer.style.display !== 'none') {
                                app.updateLogsConnectionStatus();
                            }
                        });
                })
                .catch(error => console.error('Error loading settings:', error));
        },
        
        checkForChanges: function() {
            if (!app.originalSettings.huntarr) return false; // Don't check if original settings not loaded
            
            let hasChanges = false;
            
            // API connection settings
            if (this.elements.apiUrlInput && this.elements.apiUrlInput.dataset.originalValue !== undefined && 
                this.elements.apiUrlInput.value !== this.elements.apiUrlInput.dataset.originalValue) hasChanges = true;
            if (this.elements.apiKeyInput && this.elements.apiKeyInput.dataset.originalValue !== undefined && 
                this.elements.apiKeyInput.value !== this.elements.apiKeyInput.dataset.originalValue) hasChanges = true;
            
            // Check Basic Settings
            if (this.elements.huntMissingShowsInput && parseInt(this.elements.huntMissingShowsInput.value) !== app.originalSettings.huntarr.hunt_missing_shows) hasChanges = true;
            if (this.elements.huntUpgradeEpisodesInput && parseInt(this.elements.huntUpgradeEpisodesInput.value) !== app.originalSettings.huntarr.hunt_upgrade_episodes) hasChanges = true;
            if (this.elements.sleepDurationInput && parseInt(this.elements.sleepDurationInput.value) !== app.originalSettings.huntarr.sleep_duration) hasChanges = true;
            if (this.elements.stateResetIntervalInput && parseInt(this.elements.stateResetIntervalInput.value) !== app.originalSettings.huntarr.state_reset_interval_hours) hasChanges = true;
            if (this.elements.monitoredOnlyInput && this.elements.monitoredOnlyInput.checked !== app.originalSettings.huntarr.monitored_only) hasChanges = true;
            if (this.elements.skipFutureEpisodesInput && this.elements.skipFutureEpisodesInput.checked !== app.originalSettings.huntarr.skip_future_episodes) hasChanges = true;
            if (this.elements.skipSeriesRefreshInput && this.elements.skipSeriesRefreshInput.checked !== app.originalSettings.huntarr.skip_series_refresh) hasChanges = true;
            
            // Check Advanced Settings
            if (this.elements.apiTimeoutInput && parseInt(this.elements.apiTimeoutInput.value) !== app.originalSettings.advanced.api_timeout) hasChanges = true;
            if (this.elements.debugModeInput && this.elements.debugModeInput.checked !== app.originalSettings.advanced.debug_mode) hasChanges = true;
            if (this.elements.commandWaitDelayInput && parseInt(this.elements.commandWaitDelayInput.value) !== app.originalSettings.advanced.command_wait_delay) hasChanges = true;
            if (this.elements.commandWaitAttemptsInput && parseInt(this.elements.commandWaitAttemptsInput.value) !== app.originalSettings.advanced.command_wait_attempts) hasChanges = true;
            if (this.elements.minimumDownloadQueueSizeInput && parseInt(this.elements.minimumDownloadQueueSizeInput.value) !== app.originalSettings.advanced.minimum_download_queue_size) hasChanges = true;
            if (this.elements.randomMissingInput && this.elements.randomMissingInput.checked !== app.originalSettings.advanced.random_missing) hasChanges = true;
            if (this.elements.randomUpgradesInput && this.elements.randomUpgradesInput.checked !== app.originalSettings.advanced.random_upgrades) hasChanges = true;
            
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
                    // Store the original values in data attributes for comparison
                    if (sonarrModule.elements.apiUrlInput) sonarrModule.elements.apiUrlInput.dataset.originalValue = settings.api_url;
                    if (sonarrModule.elements.apiKeyInput) sonarrModule.elements.apiKeyInput.dataset.originalValue = settings.api_key;
                    
                    // Update the rest of originalSettings
                    if (settings.huntarr) app.originalSettings.huntarr = {...settings.huntarr};
                    if (settings.advanced) app.originalSettings.advanced = {...settings.advanced};
                    
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
