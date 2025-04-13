// Sonarr-specific functionality

(function(app) {
    // Add Sonarr-specific initialization
    const sonarrModule = {
        // DOM elements specific to Sonarr
        elements: {
            apiUrlInput: document.getElementById('sonarr_api_url'),
            apiKeyInput: document.getElementById('sonarr_api_key'),
            
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
                    // Store original settings for comparison
                    app.originalSettings = JSON.parse(JSON.stringify(data));
                    
                    // Get app-specific settings directly from sonarr section instead of huntarr/advanced
                    const sonarrSettings = data.sonarr || {};
                    
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
                            }
                            
                            // Sonarr-specific settings - all from sonarrSettings directly
                            if (this.elements.huntMissingShowsInput) {
                                this.elements.huntMissingShowsInput.value = sonarrSettings.hunt_missing_shows !== undefined ? sonarrSettings.hunt_missing_shows : 1;
                            }
                            if (this.elements.huntUpgradeEpisodesInput) {
                                this.elements.huntUpgradeEpisodesInput.value = sonarrSettings.hunt_upgrade_episodes !== undefined ? sonarrSettings.hunt_upgrade_episodes : 0;
                            }
                            if (this.elements.sleepDurationInput) {
                                this.elements.sleepDurationInput.value = sonarrSettings.sleep_duration || 900;
                                this.updateSleepDurationDisplay();
                            }
                            if (this.elements.stateResetIntervalInput) {
                                this.elements.stateResetIntervalInput.value = sonarrSettings.state_reset_interval_hours || 168;
                            }
                            if (this.elements.monitoredOnlyInput) {
                                this.elements.monitoredOnlyInput.checked = sonarrSettings.monitored_only !== false;
                            }
                            if (this.elements.skipFutureEpisodesInput) {
                                this.elements.skipFutureEpisodesInput.checked = sonarrSettings.skip_future_episodes !== false;
                            }
                            if (this.elements.skipSeriesRefreshInput) {
                                this.elements.skipSeriesRefreshInput.checked = sonarrSettings.skip_series_refresh === true;
                            }
                            
                            // Advanced settings - from the same sonarrSettings object
                            if (this.elements.apiTimeoutInput) {
                                this.elements.apiTimeoutInput.value = sonarrSettings.api_timeout || 60;
                            }
                            if (this.elements.debugModeInput) {
                                this.elements.debugModeInput.checked = sonarrSettings.debug_mode === true;
                            }
                            if (this.elements.commandWaitDelayInput) {
                                this.elements.commandWaitDelayInput.value = sonarrSettings.command_wait_delay || 1;
                            }
                            if (this.elements.commandWaitAttemptsInput) {
                                this.elements.commandWaitAttemptsInput.value = sonarrSettings.command_wait_attempts || 600;
                            }
                            if (this.elements.minimumDownloadQueueSizeInput) {
                                this.elements.minimumDownloadQueueSizeInput.value = sonarrSettings.minimum_download_queue_size || -1;
                            }
                            if (this.elements.randomMissingInput) {
                                this.elements.randomMissingInput.checked = sonarrSettings.random_missing !== false;
                            }
                            if (this.elements.randomUpgradesInput) {
                                this.elements.randomUpgradesInput.checked = sonarrSettings.random_upgrades !== false;
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
            if (!app.originalSettings.sonarr) return false; // Don't check if original settings not loaded
            
            let hasChanges = false;
            const sonarrSettings = app.originalSettings.sonarr || {};
            
            // API connection settings
            if (this.elements.apiUrlInput && this.elements.apiUrlInput.dataset.originalValue !== undefined && 
                this.elements.apiUrlInput.value !== this.elements.apiUrlInput.dataset.originalValue) hasChanges = true;
            if (this.elements.apiKeyInput && this.elements.apiKeyInput.dataset.originalValue !== undefined && 
                this.elements.apiKeyInput.value !== this.elements.apiKeyInput.dataset.originalValue) hasChanges = true;
            
            // Check all settings directly from the sonarr object
            if (this.elements.huntMissingShowsInput && parseInt(this.elements.huntMissingShowsInput.value) !== sonarrSettings.hunt_missing_shows) hasChanges = true;
            if (this.elements.huntUpgradeEpisodesInput && parseInt(this.elements.huntUpgradeEpisodesInput.value) !== sonarrSettings.hunt_upgrade_episodes) hasChanges = true;
            if (this.elements.sleepDurationInput && parseInt(this.elements.sleepDurationInput.value) !== sonarrSettings.sleep_duration) hasChanges = true;
            if (this.elements.stateResetIntervalInput && parseInt(this.elements.stateResetIntervalInput.value) !== sonarrSettings.state_reset_interval_hours) hasChanges = true;
            if (this.elements.monitoredOnlyInput && this.elements.monitoredOnlyInput.checked !== sonarrSettings.monitored_only) hasChanges = true;
            if (this.elements.skipFutureEpisodesInput && this.elements.skipFutureEpisodesInput.checked !== sonarrSettings.skip_future_episodes) hasChanges = true;
            if (this.elements.skipSeriesRefreshInput && this.elements.skipSeriesRefreshInput.checked !== sonarrSettings.skip_series_refresh) hasChanges = true;
            
            // Check Advanced Settings directly from the sonarr object as well
            if (this.elements.apiTimeoutInput && parseInt(this.elements.apiTimeoutInput.value) !== sonarrSettings.api_timeout) hasChanges = true;
            if (this.elements.debugModeInput && this.elements.debugModeInput.checked !== sonarrSettings.debug_mode) hasChanges = true;
            if (this.elements.commandWaitDelayInput && parseInt(this.elements.commandWaitDelayInput.value) !== sonarrSettings.command_wait_delay) hasChanges = true;
            if (this.elements.commandWaitAttemptsInput && parseInt(this.elements.commandWaitAttemptsInput.value) !== sonarrSettings.command_wait_attempts) hasChanges = true;
            if (this.elements.minimumDownloadQueueSizeInput && parseInt(this.elements.minimumDownloadQueueSizeInput.value) !== sonarrSettings.minimum_download_queue_size) hasChanges = true;
            if (this.elements.randomMissingInput && this.elements.randomMissingInput.checked !== sonarrSettings.random_missing) hasChanges = true;
            if (this.elements.randomUpgradesInput && this.elements.randomUpgradesInput.checked !== sonarrSettings.random_upgrades) hasChanges = true;
            
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
                // Combined settings - all at top level, no nesting
                hunt_missing_shows: this.elements.huntMissingShowsInput ? parseInt(this.elements.huntMissingShowsInput.value) || 0 : 0,
                hunt_upgrade_episodes: this.elements.huntUpgradeEpisodesInput ? parseInt(this.elements.huntUpgradeEpisodesInput.value) || 0 : 0,
                sleep_duration: this.elements.sleepDurationInput ? parseInt(this.elements.sleepDurationInput.value) || 900 : 900,
                state_reset_interval_hours: this.elements.stateResetIntervalInput ? parseInt(this.elements.stateResetIntervalInput.value) || 168 : 168,
                monitored_only: this.elements.monitoredOnlyInput ? this.elements.monitoredOnlyInput.checked : true,
                skip_future_episodes: this.elements.skipFutureEpisodesInput ? this.elements.skipFutureEpisodesInput.checked : true,
                skip_series_refresh: this.elements.skipSeriesRefreshInput ? this.elements.skipSeriesRefreshInput.checked : false,
                
                // Include advanced settings at the same level
                debug_mode: this.elements.debugModeInput ? this.elements.debugModeInput.checked : false,
                command_wait_delay: this.elements.commandWaitDelayInput ? parseInt(this.elements.commandWaitDelayInput.value) || 1 : 1,
                command_wait_attempts: this.elements.commandWaitAttemptsInput ? parseInt(this.elements.commandWaitAttemptsInput.value) || 600 : 600,
                minimum_download_queue_size: this.elements.minimumDownloadQueueSizeInput ? parseInt(this.elements.minimumDownloadQueueSizeInput.value) || -1 : -1,
                random_missing: this.elements.randomMissingInput ? this.elements.randomMissingInput.checked : true,
                random_upgrades: this.elements.randomUpgradesInput ? this.elements.randomUpgradesInput.checked : true,
                api_timeout: this.elements.apiTimeoutInput ? parseInt(this.elements.apiTimeoutInput.value) || 60 : 60,
                log_refresh_interval_seconds: 30 // Default value
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
                    if (settings.sonarr) app.originalSettings.sonarr = {...settings.sonarr};
                    
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
