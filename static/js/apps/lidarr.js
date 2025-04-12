// Lidarr-specific functionality

(function(app) {
    // Add Lidarr-specific initialization
    const lidarrModule = {
        // DOM elements specific to Lidarr
        elements: {
            apiUrlInput: document.getElementById('lidarr_api_url'),
            apiKeyInput: document.getElementById('lidarr_api_key'),
            connectionStatus: document.getElementById('lidarrConnectionStatus'),
            testConnectionButton: document.getElementById('testLidarrConnection'),
            
            // Settings form elements
            huntMissingAlbumsInput: document.getElementById('hunt_missing_albums'),
            huntUpgradeTracksInput: document.getElementById('hunt_upgrade_tracks'),
            sleepDurationInput: document.getElementById('lidarr_sleep_duration'),
            sleepDurationHoursSpan: document.getElementById('lidarr_sleep_duration_hours'),
            stateResetIntervalInput: document.getElementById('lidarr_state_reset_interval_hours'),
            monitoredOnlyInput: document.getElementById('lidarr_monitored_only'),
            randomMissingInput: document.getElementById('lidarr_random_missing'),
            randomUpgradesInput: document.getElementById('lidarr_random_upgrades'),
            skipFutureReleasesInput: document.getElementById('lidarr_skip_future_releases'),
            skipArtistRefreshInput: document.getElementById('skip_artist_refresh'),
            
            // Advanced settings
            apiTimeoutInput: document.getElementById('lidarr_api_timeout'),
            debugModeInput: document.getElementById('lidarr_debug_mode'),
            commandWaitDelayInput: document.getElementById('lidarr_command_wait_delay'),
            commandWaitAttemptsInput: document.getElementById('lidarr_command_wait_attempts'),
            minimumDownloadQueueSizeInput: document.getElementById('lidarr_minimum_download_queue_size')
        },
        
        init: function() {
            this.setupEventListeners();
            
            // Extend the core app with Lidarr-specific implementations
            app.loadSettingsLidarr = this.loadSettings.bind(this);
            
            // Override the load settings with Lidarr implementation when Lidarr is active
            const originalLoadSettings = app.loadSettings;
            app.loadSettings = function(appType) {
                if (appType === 'lidarr') {
                    this.loadSettingsLidarr();
                } else if (originalLoadSettings) {
                    // Only call the original if we're not handling Lidarr
                    originalLoadSettings.call(this, appType);
                }
            };
            
            // Wire up the specific test connection
            if (this.elements.testConnectionButton) {
                this.elements.testConnectionButton.addEventListener('click', () => {
                    app.testConnection('lidarr', this.elements.apiUrlInput, this.elements.apiKeyInput, this.elements.connectionStatus);
                });
            }
        },
        
        setupEventListeners: function() {
            // Add input event listeners for Lidarr-specific settings
            const inputs = [
                this.elements.apiUrlInput,
                this.elements.apiKeyInput,
                this.elements.huntMissingAlbumsInput,
                this.elements.huntUpgradeTracksInput,
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
                this.elements.skipArtistRefreshInput,
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
                    const huntarr = data.huntarr || {};
                    const advanced = data.advanced || {};
                    
                    // Store original settings for comparison
                    app.originalSettings = JSON.parse(JSON.stringify(data));
                    
                    // For Lidarr, load from app-settings endpoint
                    fetch(`/api/app-settings?app=lidarr`)
                        .then(response => response.json())
                        .then(appData => {
                            if (appData.success) {
                                this.elements.apiUrlInput.value = appData.api_url || '';
                                this.elements.apiKeyInput.value = appData.api_key || '';
                                
                                // Store original values in data attributes for comparison
                                this.elements.apiUrlInput.dataset.originalValue = appData.api_url || '';
                                this.elements.apiKeyInput.dataset.originalValue = appData.api_key || '';
                                
                                // Update configured status
                                app.configuredApps.lidarr = !!(appData.api_url && appData.api_key);
                                
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
                            
                            // Lidarr-specific settings
                            if (this.elements.huntMissingAlbumsInput) {
                                this.elements.huntMissingAlbumsInput.value = huntarr.hunt_missing_albums !== undefined ? huntarr.hunt_missing_albums : 1;
                            }
                            if (this.elements.huntUpgradeTracksInput) {
                                this.elements.huntUpgradeTracksInput.value = huntarr.hunt_upgrade_tracks !== undefined ? huntarr.hunt_upgrade_tracks : 0;
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
                            if (this.elements.skipFutureReleasesInput) {
                                this.elements.skipFutureReleasesInput.checked = huntarr.skip_future_releases !== false;
                            }
                            if (this.elements.skipArtistRefreshInput) {
                                this.elements.skipArtistRefreshInput.checked = huntarr.skip_artist_refresh === true;
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
                            console.error('Error loading Lidarr settings:', error);
                            
                            // Default values
                            this.elements.apiUrlInput.value = '';
                            this.elements.apiKeyInput.value = '';
                            this.elements.apiUrlInput.dataset.originalValue = '';
                            this.elements.apiKeyInput.dataset.originalValue = '';
                            app.configuredApps.lidarr = false;
                            
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
            if (this.elements.huntMissingAlbumsInput && parseInt(this.elements.huntMissingAlbumsInput.value) !== app.originalSettings.huntarr.hunt_missing_albums) hasChanges = true;
            if (this.elements.huntUpgradeTracksInput && parseInt(this.elements.huntUpgradeTracksInput.value) !== app.originalSettings.huntarr.hunt_upgrade_tracks) hasChanges = true;
            if (this.elements.sleepDurationInput && parseInt(this.elements.sleepDurationInput.value) !== app.originalSettings.huntarr.sleep_duration) hasChanges = true;
            if (this.elements.stateResetIntervalInput && parseInt(this.elements.stateResetIntervalInput.value) !== app.originalSettings.huntarr.state_reset_interval_hours) hasChanges = true;
            if (this.elements.monitoredOnlyInput && this.elements.monitoredOnlyInput.checked !== app.originalSettings.huntarr.monitored_only) hasChanges = true;
            if (this.elements.skipFutureReleasesInput && this.elements.skipFutureReleasesInput.checked !== app.originalSettings.huntarr.skip_future_releases) hasChanges = true;
            if (this.elements.skipArtistRefreshInput && this.elements.skipArtistRefreshInput.checked !== app.originalSettings.huntarr.skip_artist_refresh) hasChanges = true;
            
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
                app_type: 'lidarr',
                api_url: this.elements.apiUrlInput ? this.elements.apiUrlInput.value || '' : '',
                api_key: this.elements.apiKeyInput ? this.elements.apiKeyInput.value || '' : '',
                huntarr: {
                    hunt_missing_albums: this.elements.huntMissingAlbumsInput ? parseInt(this.elements.huntMissingAlbumsInput.value) || 0 : 0,
                    hunt_upgrade_tracks: this.elements.huntUpgradeTracksInput ? parseInt(this.elements.huntUpgradeTracksInput.value) || 0 : 0,
                    sleep_duration: this.elements.sleepDurationInput ? parseInt(this.elements.sleepDurationInput.value) || 900 : 900,
                    state_reset_interval_hours: this.elements.stateResetIntervalInput ? parseInt(this.elements.stateResetIntervalInput.value) || 168 : 168,
                    monitored_only: this.elements.monitoredOnlyInput ? this.elements.monitoredOnlyInput.checked : true,
                    skip_future_releases: this.elements.skipFutureReleasesInput ? this.elements.skipFutureReleasesInput.checked : true,
                    skip_artist_refresh: this.elements.skipArtistRefreshInput ? this.elements.skipArtistRefreshInput.checked : false
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
    
    // Initialize Lidarr module
    lidarrModule.init();
    
    // Override app.saveSettings to handle Lidarr-specific logic when Lidarr is active
    const originalSaveSettings = app.saveSettings;
    app.saveSettings = function() {
        if (app.currentApp === 'lidarr') {
            if (!lidarrModule.checkForChanges()) {
                // If no changes, don't do anything
                return;
            }
            
            const settings = lidarrModule.getSettingsPayload();
            
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
                    if (lidarrModule.elements.apiUrlInput) lidarrModule.elements.apiUrlInput.dataset.originalValue = settings.api_url;
                    if (lidarrModule.elements.apiKeyInput) lidarrModule.elements.apiKeyInput.dataset.originalValue = settings.api_key;
                    
                    // Update the rest of originalSettings
                    if (settings.huntarr) app.originalSettings.huntarr = {...settings.huntarr};
                    if (settings.advanced) app.originalSettings.advanced = {...settings.advanced};
                    
                    // Update configuration status
                    app.configuredApps.lidarr = !!(settings.api_url && settings.api_key);
                    
                    // Update connection status
                    app.updateConnectionStatus();
                    
                    // Update home page connection status
                    app.updateHomeConnectionStatus();
                    
                    // Update logs connection status
                    app.updateLogsConnectionStatus();
                    
                    // Disable save buttons
                    lidarrModule.updateSaveButtonState(false);
                    
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
            // Call the original if we're not handling Lidarr
            originalSaveSettings.call(app);
        }
    };
    
    // Add the Lidarr module to the app for reference
    app.lidarrModule = lidarrModule;

})(window.huntarrApp);
