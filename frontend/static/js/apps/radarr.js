// Radarr-specific functionality

(function(app) {
    // Add Radarr-specific initialization
    const radarrModule = {
        // DOM elements specific to Radarr
        elements: {
            apiUrlInput: document.getElementById('radarr_api_url'),
            apiKeyInput: document.getElementById('radarr_api_key'),
            
            // Settings form elements
            huntMissingMoviesInput: document.getElementById('hunt_missing_movies'),
            huntUpgradeMoviesInput: document.getElementById('hunt_upgrade_movies'),
            sleepDurationInput: document.getElementById('radarr_sleep_duration'),
            sleepDurationHoursSpan: document.getElementById('radarr_sleep_duration_hours'),
            stateResetIntervalInput: document.getElementById('radarr_state_reset_interval_hours'),
            monitoredOnlyInput: document.getElementById('radarr_monitored_only'),
            randomMissingInput: document.getElementById('radarr_random_missing'),
            randomUpgradesInput: document.getElementById('radarr_random_upgrades'),
            skipFutureReleasesInput: document.getElementById('skip_future_releases'),
            skipMovieRefreshInput: document.getElementById('skip_movie_refresh'),
            
            // Advanced settings
            apiTimeoutInput: document.getElementById('radarr_api_timeout'),
            debugModeInput: document.getElementById('radarr_debug_mode'),
            commandWaitDelayInput: document.getElementById('radarr_command_wait_delay'),
            commandWaitAttemptsInput: document.getElementById('radarr_command_wait_attempts'),
            minimumDownloadQueueSizeInput: document.getElementById('radarr_minimum_download_queue_size')
        },
        
        init: function() {
            this.setupEventListeners();
            
            // Extend the core app with Radarr-specific implementations
            app.loadSettingsRadarr = this.loadSettings.bind(this);
            
            // Override the load settings with Radarr implementation when Radarr is active
            const originalLoadSettings = app.loadSettings;
            app.loadSettings = function(appType) {
                if (appType === 'radarr') {
                    this.loadSettingsRadarr();
                } else if (originalLoadSettings) {
                    // Only call the original if we're not handling Radarr
                    originalLoadSettings.call(this, appType);
                }
            };
        },
        
        setupEventListeners: function() {
            // Add input event listeners for Radarr-specific settings
            const inputs = [
                this.elements.apiUrlInput,
                this.elements.apiKeyInput,
                this.elements.huntMissingMoviesInput,
                this.elements.huntUpgradeMoviesInput,
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
                this.elements.skipFutureReleasesInput,
                this.elements.skipMovieRefreshInput,
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
                    
                    // Get app-specific settings directly from radarr section instead of huntarr/advanced
                    const radarrSettings = data.radarr || {};
                    
                    // For Radarr, load from app-settings endpoint
                    fetch(`/api/app-settings?app=radarr`)
                        .then(response => response.json())
                        .then(appData => {
                            if (appData.success) {
                                this.elements.apiUrlInput.value = appData.api_url || '';
                                this.elements.apiKeyInput.value = appData.api_key || '';
                                
                                // Store original values in data attributes for comparison
                                this.elements.apiUrlInput.dataset.originalValue = appData.api_url || '';
                                this.elements.apiKeyInput.dataset.originalValue = appData.api_key || '';
                                
                                // Update configured status
                                app.configuredApps.radarr = !!(appData.api_url && appData.api_key);
                            }
                            
                            // Radarr-specific settings - all from radarrSettings directly
                            if (this.elements.huntMissingMoviesInput) {
                                this.elements.huntMissingMoviesInput.value = radarrSettings.hunt_missing_movies !== undefined ? radarrSettings.hunt_missing_movies : 1;
                            }
                            if (this.elements.huntUpgradeMoviesInput) {
                                this.elements.huntUpgradeMoviesInput.value = radarrSettings.hunt_upgrade_movies !== undefined ? radarrSettings.hunt_upgrade_movies : 0;
                            }
                            if (this.elements.sleepDurationInput) {
                                this.elements.sleepDurationInput.value = radarrSettings.sleep_duration || 900;
                                this.updateSleepDurationDisplay();
                            }
                            if (this.elements.stateResetIntervalInput) {
                                this.elements.stateResetIntervalInput.value = radarrSettings.state_reset_interval_hours || 168;
                            }
                            if (this.elements.monitoredOnlyInput) {
                                this.elements.monitoredOnlyInput.checked = radarrSettings.monitored_only !== false;
                            }
                            if (this.elements.skipFutureReleasesInput) {
                                this.elements.skipFutureReleasesInput.checked = radarrSettings.skip_future_releases !== false;
                            }
                            if (this.elements.skipMovieRefreshInput) {
                                this.elements.skipMovieRefreshInput.checked = radarrSettings.skip_movie_refresh === true;
                            }
                            
                            // Advanced settings - from the same radarrSettings object
                            if (this.elements.apiTimeoutInput) {
                                this.elements.apiTimeoutInput.value = radarrSettings.api_timeout || 60;
                            }
                            if (this.elements.debugModeInput) {
                                this.elements.debugModeInput.checked = radarrSettings.debug_mode === true;
                            }
                            if (this.elements.commandWaitDelayInput) {
                                this.elements.commandWaitDelayInput.value = radarrSettings.command_wait_delay || 1;
                            }
                            if (this.elements.commandWaitAttemptsInput) {
                                this.elements.commandWaitAttemptsInput.value = radarrSettings.command_wait_attempts || 600;
                            }
                            if (this.elements.minimumDownloadQueueSizeInput) {
                                this.elements.minimumDownloadQueueSizeInput.value = radarrSettings.minimum_download_queue_size || -1;
                            }
                            if (this.elements.randomMissingInput) {
                                this.elements.randomMissingInput.checked = radarrSettings.random_missing !== false;
                            }
                            if (this.elements.randomUpgradesInput) {
                                this.elements.randomUpgradesInput.checked = radarrSettings.random_upgrades !== false;
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
                            console.error('Error loading Radarr settings:', error);
                            
                            // Default values
                            this.elements.apiUrlInput.value = '';
                            this.elements.apiKeyInput.value = '';
                            this.elements.apiUrlInput.dataset.originalValue = '';
                            this.elements.apiKeyInput.dataset.originalValue = '';
                            app.configuredApps.radarr = false;
                            
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
            if (!app.originalSettings.radarr) return false; // Don't check if original settings not loaded
            
            let hasChanges = false;
            const radarrSettings = app.originalSettings.radarr || {};
            
            // API connection settings
            if (this.elements.apiUrlInput && this.elements.apiUrlInput.dataset.originalValue !== undefined && 
                this.elements.apiUrlInput.value !== this.elements.apiUrlInput.dataset.originalValue) hasChanges = true;
            if (this.elements.apiKeyInput && this.elements.apiKeyInput.dataset.originalValue !== undefined && 
                this.elements.apiKeyInput.value !== this.elements.apiKeyInput.dataset.originalValue) hasChanges = true;
            
            // Check all settings directly from the radarr object
            if (this.elements.huntMissingMoviesInput && parseInt(this.elements.huntMissingMoviesInput.value) !== radarrSettings.hunt_missing_movies) hasChanges = true;
            if (this.elements.huntUpgradeMoviesInput && parseInt(this.elements.huntUpgradeMoviesInput.value) !== radarrSettings.hunt_upgrade_movies) hasChanges = true;
            if (this.elements.sleepDurationInput && parseInt(this.elements.sleepDurationInput.value) !== radarrSettings.sleep_duration) hasChanges = true;
            if (this.elements.stateResetIntervalInput && parseInt(this.elements.stateResetIntervalInput.value) !== radarrSettings.state_reset_interval_hours) hasChanges = true;
            if (this.elements.monitoredOnlyInput && this.elements.monitoredOnlyInput.checked !== radarrSettings.monitored_only) hasChanges = true;
            if (this.elements.skipFutureReleasesInput && this.elements.skipFutureReleasesInput.checked !== radarrSettings.skip_future_releases) hasChanges = true;
            if (this.elements.skipMovieRefreshInput && this.elements.skipMovieRefreshInput.checked !== radarrSettings.skip_movie_refresh) hasChanges = true;
            
            // Check Advanced Settings directly from the radarr object as well
            if (this.elements.apiTimeoutInput && parseInt(this.elements.apiTimeoutInput.value) !== radarrSettings.api_timeout) hasChanges = true;
            if (this.elements.debugModeInput && this.elements.debugModeInput.checked !== radarrSettings.debug_mode) hasChanges = true;
            if (this.elements.commandWaitDelayInput && parseInt(this.elements.commandWaitDelayInput.value) !== radarrSettings.command_wait_delay) hasChanges = true;
            if (this.elements.commandWaitAttemptsInput && parseInt(this.elements.commandWaitAttemptsInput.value) !== radarrSettings.command_wait_attempts) hasChanges = true;
            if (this.elements.minimumDownloadQueueSizeInput && parseInt(this.elements.minimumDownloadQueueSizeInput.value) !== radarrSettings.minimum_download_queue_size) hasChanges = true;
            if (this.elements.randomMissingInput && this.elements.randomMissingInput.checked !== radarrSettings.random_missing) hasChanges = true;
            if (this.elements.randomUpgradesInput && this.elements.randomUpgradesInput.checked !== radarrSettings.random_upgrades) hasChanges = true;
            
            // Update save buttons state
            this.updateSaveButtonState(hasChanges);
            
            return hasChanges;
        },
        
        updateSaveButtonState: function(hasChanges) {
            // Use the HuntarrUI instance to access elements
            const saveButton = window.HuntarrUI?.elements?.saveSettingsButton;
            if (saveButton) {
                saveButton.disabled = !hasChanges;
                if (hasChanges) {
                    saveButton.classList.remove('disabled-button'); // Assuming 'disabled-button' class handles visual state
                } else {
                    saveButton.classList.add('disabled-button');
                }
            }
            // Remove references to non-existent bottom button
        },
        
        getSettingsPayload: function() {
            return {
                app_type: 'radarr',
                api_url: this.elements.apiUrlInput ? this.elements.apiUrlInput.value || '' : '',
                api_key: this.elements.apiKeyInput ? this.elements.apiKeyInput.value || '' : '',
                // Combined settings - all at top level, no nesting
                hunt_missing_movies: this.elements.huntMissingMoviesInput ? parseInt(this.elements.huntMissingMoviesInput.value) || 0 : 0,
                hunt_upgrade_movies: this.elements.huntUpgradeMoviesInput ? parseInt(this.elements.huntUpgradeMoviesInput.value) || 0 : 0,
                sleep_duration: this.elements.sleepDurationInput ? parseInt(this.elements.sleepDurationInput.value) || 900 : 900,
                state_reset_interval_hours: this.elements.stateResetIntervalInput ? parseInt(this.elements.stateResetIntervalInput.value) || 168 : 168,
                monitored_only: this.elements.monitoredOnlyInput ? this.elements.monitoredOnlyInput.checked : true,
                skip_future_releases: this.elements.skipFutureReleasesInput ? this.elements.skipFutureReleasesInput.checked : true,
                skip_movie_refresh: this.elements.skipMovieRefreshInput ? this.elements.skipMovieRefreshInput.checked : false,
                
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
    
    // Initialize Radarr module
    radarrModule.init();
    
    // Override app.saveSettings to handle Radarr-specific logic when Radarr is active
    const originalSaveSettings = app.saveSettings;
    app.saveSettings = function() {
        if (app.currentApp === 'radarr') {
            if (!radarrModule.checkForChanges()) {
                // If no changes, don't do anything
                return;
            }
            
            const settings = radarrModule.getSettingsPayload();
            
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
                    if (radarrModule.elements.apiUrlInput) radarrModule.elements.apiUrlInput.dataset.originalValue = settings.api_url;
                    if (radarrModule.elements.apiKeyInput) radarrModule.elements.apiKeyInput.dataset.originalValue = settings.api_key;
                    
                    // Update the rest of originalSettings
                    if (settings.radarr) app.originalSettings.radarr = {...settings.radarr};
                    
                    // Update configuration status
                    app.configuredApps.radarr = !!(settings.api_url && settings.api_key);
                    
                    // Update connection status
                    app.updateConnectionStatus();
                    
                    // Update home page connection status
                    app.updateHomeConnectionStatus();
                    
                    // Update logs connection status
                    app.updateLogsConnectionStatus();
                    
                    // Disable save buttons
                    radarrModule.updateSaveButtonState(false);
                    
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
            // Call the original if we're not handling Radarr
            originalSaveSettings.call(app);
        }
    };
    
    // Add the Radarr module to the app for reference
    app.radarrModule = radarrModule;

})(window.huntarrApp);
