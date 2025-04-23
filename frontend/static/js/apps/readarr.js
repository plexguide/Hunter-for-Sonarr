// Readarr-specific functionality

(function(app) {
    // Add Readarr-specific initialization
    const readarrModule = {
        // DOM elements specific to Readarr
        elements: {
            apiUrlInput: document.getElementById('readarr_api_url'),
            apiKeyInput: document.getElementById('readarr_api_key'),
            
            // Settings form elements
            huntMissingBooksInput: document.getElementById('hunt_missing_books'),
            huntUpgradeBooksInput: document.getElementById('hunt_upgrade_books'),
            sleepDurationInput: document.getElementById('readarr_sleep_duration'),
            sleepDurationHoursSpan: document.getElementById('readarr_sleep_duration_hours'),
            stateResetIntervalInput: document.getElementById('readarr_state_reset_interval_hours'),
            monitoredOnlyInput: document.getElementById('readarr_monitored_only'),
            randomMissingInput: document.getElementById('readarr_random_missing'),
            randomUpgradesInput: document.getElementById('readarr_random_upgrades'),
            skipFutureReleasesInput: document.getElementById('readarr_skip_future_releases'),
            skipAuthorRefreshInput: document.getElementById('skip_author_refresh'),
            
            // Advanced settings
            apiTimeoutInput: document.getElementById('readarr_api_timeout'),
            debugModeInput: document.getElementById('readarr_debug_mode'),
            commandWaitDelayInput: document.getElementById('readarr_command_wait_delay'),
            commandWaitAttemptsInput: document.getElementById('readarr_command_wait_attempts'),
            minimumDownloadQueueSizeInput: document.getElementById('readarr_minimum_download_queue_size')
        },
        
        init: function() {
            this.setupEventListeners();
            
            // Extend the core app with Readarr-specific implementations
            app.loadSettingsReadarr = this.loadSettings.bind(this);
            
            // Override the load settings with Readarr implementation when Readarr is active
            const originalLoadSettings = app.loadSettings;
            app.loadSettings = function(appType) {
                if (appType === 'readarr') {
                    this.loadSettingsReadarr();
                } else if (originalLoadSettings) {
                    // Only call the original if we're not handling Readarr
                    originalLoadSettings.call(this, appType);
                }
            };
        },
        
        setupEventListeners: function() {
            // Add input event listeners for Readarr-specific settings
            const inputs = [
                this.elements.apiUrlInput,
                this.elements.apiKeyInput,
                this.elements.huntMissingBooksInput,
                this.elements.huntUpgradeBooksInput,
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
                this.elements.skipAuthorRefreshInput,
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
                    
                    // Get app-specific settings directly from readarr section instead of huntarr/advanced
                    const readarrSettings = data.readarr || {};
                    
                    // For Readarr, load from app-settings endpoint
                    fetch(`/api/app-settings?app=readarr`)
                        .then(response => response.json())
                        .then(appData => {
                            if (appData.success) {
                                this.elements.apiUrlInput.value = appData.api_url || '';
                                this.elements.apiKeyInput.value = appData.api_key || '';
                                
                                // Store original values in data attributes for comparison
                                this.elements.apiUrlInput.dataset.originalValue = appData.api_url || '';
                                this.elements.apiKeyInput.dataset.originalValue = appData.api_key || '';
                                
                                // Update configured status
                                app.configuredApps.readarr = !!(appData.api_url && appData.api_key);
                            }
                            
                            // Readarr-specific settings - all from readarrSettings directly
                            if (this.elements.huntMissingBooksInput) {
                                this.elements.huntMissingBooksInput.value = readarrSettings.hunt_missing_books !== undefined ? readarrSettings.hunt_missing_books : 1;
                            }
                            if (this.elements.huntUpgradeBooksInput) {
                                this.elements.huntUpgradeBooksInput.value = readarrSettings.hunt_upgrade_books !== undefined ? readarrSettings.hunt_upgrade_books : 0;
                            }
                            if (this.elements.sleepDurationInput) {
                                this.elements.sleepDurationInput.value = readarrSettings.sleep_duration || 900;
                                this.updateSleepDurationDisplay();
                            }
                            if (this.elements.stateResetIntervalInput) {
                                this.elements.stateResetIntervalInput.value = readarrSettings.state_reset_interval_hours || 168;
                            }
                            if (this.elements.monitoredOnlyInput) {
                                this.elements.monitoredOnlyInput.checked = readarrSettings.monitored_only !== false;
                            }
                            if (this.elements.skipFutureReleasesInput) {
                                this.elements.skipFutureReleasesInput.checked = readarrSettings.skip_future_releases !== false;
                            }
                            if (this.elements.skipAuthorRefreshInput) {
                                this.elements.skipAuthorRefreshInput.checked = readarrSettings.skip_author_refresh === true;
                            }
                            
                            // Advanced settings - from the same readarrSettings object
                            if (this.elements.apiTimeoutInput) {
                                this.elements.apiTimeoutInput.value = readarrSettings.api_timeout || 60;
                            }
                            if (this.elements.debugModeInput) {
                                this.elements.debugModeInput.checked = readarrSettings.debug_mode === true;
                            }
                            if (this.elements.commandWaitDelayInput) {
                                this.elements.commandWaitDelayInput.value = readarrSettings.command_wait_delay || 1;
                            }
                            if (this.elements.commandWaitAttemptsInput) {
                                this.elements.commandWaitAttemptsInput.value = readarrSettings.command_wait_attempts || 600;
                            }
                            if (this.elements.minimumDownloadQueueSizeInput) {
                                this.elements.minimumDownloadQueueSizeInput.value = readarrSettings.minimum_download_queue_size || -1;
                            }
                            if (this.elements.randomMissingInput) {
                                this.elements.randomMissingInput.checked = readarrSettings.random_missing !== false;
                            }
                            if (this.elements.randomUpgradesInput) {
                                this.elements.randomUpgradesInput.checked = readarrSettings.random_upgrades !== false;
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
                            console.error('Error loading Readarr settings:', error);
                            
                            // Default values
                            this.elements.apiUrlInput.value = '';
                            this.elements.apiKeyInput.value = '';
                            this.elements.apiUrlInput.dataset.originalValue = '';
                            this.elements.apiKeyInput.dataset.originalValue = '';
                            app.configuredApps.readarr = false;
                            
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
            if (!app.originalSettings.readarr) return false; // Don't check if original settings not loaded
            
            let hasChanges = false;
            const readarrSettings = app.originalSettings.readarr || {};
            
            // API connection settings
            if (this.elements.apiUrlInput && this.elements.apiUrlInput.dataset.originalValue !== undefined && 
                this.elements.apiUrlInput.value !== this.elements.apiUrlInput.dataset.originalValue) hasChanges = true;
            if (this.elements.apiKeyInput && this.elements.apiKeyInput.dataset.originalValue !== undefined && 
                this.elements.apiKeyInput.value !== this.elements.apiKeyInput.dataset.originalValue) hasChanges = true;
            
            // Check all settings directly from the readarr object
            if (this.elements.huntMissingBooksInput && parseInt(this.elements.huntMissingBooksInput.value) !== readarrSettings.hunt_missing_books) hasChanges = true;
            if (this.elements.huntUpgradeBooksInput && parseInt(this.elements.huntUpgradeBooksInput.value) !== readarrSettings.hunt_upgrade_books) hasChanges = true;
            if (this.elements.sleepDurationInput && parseInt(this.elements.sleepDurationInput.value) !== readarrSettings.sleep_duration) hasChanges = true;
            if (this.elements.stateResetIntervalInput && parseInt(this.elements.stateResetIntervalInput.value) !== readarrSettings.state_reset_interval_hours) hasChanges = true;
            if (this.elements.monitoredOnlyInput && this.elements.monitoredOnlyInput.checked !== readarrSettings.monitored_only) hasChanges = true;
            if (this.elements.skipFutureReleasesInput && this.elements.skipFutureReleasesInput.checked !== readarrSettings.skip_future_releases) hasChanges = true;
            if (this.elements.skipAuthorRefreshInput && this.elements.skipAuthorRefreshInput.checked !== readarrSettings.skip_author_refresh) hasChanges = true;
            
            // Check Advanced Settings directly from the readarr object as well
            if (this.elements.apiTimeoutInput && parseInt(this.elements.apiTimeoutInput.value) !== readarrSettings.api_timeout) hasChanges = true;
            if (this.elements.debugModeInput && this.elements.debugModeInput.checked !== readarrSettings.debug_mode) hasChanges = true;
            if (this.elements.commandWaitDelayInput && parseInt(this.elements.commandWaitDelayInput.value) !== readarrSettings.command_wait_delay) hasChanges = true;
            if (this.elements.commandWaitAttemptsInput && parseInt(this.elements.commandWaitAttemptsInput.value) !== readarrSettings.command_wait_attempts) hasChanges = true;
            if (this.elements.minimumDownloadQueueSizeInput && parseInt(this.elements.minimumDownloadQueueSizeInput.value) !== readarrSettings.minimum_download_queue_size) hasChanges = true;
            if (this.elements.randomMissingInput && this.elements.randomMissingInput.checked !== readarrSettings.random_missing) hasChanges = true;
            if (this.elements.randomUpgradesInput && this.elements.randomUpgradesInput.checked !== readarrSettings.random_upgrades) hasChanges = true;
            
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
                app_type: 'readarr',
                api_url: this.elements.apiUrlInput ? this.elements.apiUrlInput.value || '' : '',
                api_key: this.elements.apiKeyInput ? this.elements.apiKeyInput.value || '' : '',
                // Combined settings - all at top level, no nesting
                hunt_missing_books: this.elements.huntMissingBooksInput ? parseInt(this.elements.huntMissingBooksInput.value) || 0 : 0,
                hunt_upgrade_books: this.elements.huntUpgradeBooksInput ? parseInt(this.elements.huntUpgradeBooksInput.value) || 0 : 0,
                sleep_duration: this.elements.sleepDurationInput ? parseInt(this.elements.sleepDurationInput.value) || 900 : 900,
                state_reset_interval_hours: this.elements.stateResetIntervalInput ? parseInt(this.elements.stateResetIntervalInput.value) || 168 : 168,
                monitored_only: this.elements.monitoredOnlyInput ? this.elements.monitoredOnlyInput.checked : true,
                skip_future_releases: this.elements.skipFutureReleasesInput ? this.elements.skipFutureReleasesInput.checked : true,
                skip_author_refresh: this.elements.skipAuthorRefreshInput ? this.elements.skipAuthorRefreshInput.checked : false,
                
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
        },
        
        saveSettings: function() {
            const payload = this.getSettingsPayload();
            
            // Use POST /api/settings endpoint
            fetch('/api/settings', { 
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update original settings and API key data attributes after successful save
                    const settings = data.settings || {}; // Assuming backend returns the saved settings
                    if (readarrModule.elements.apiUrlInput) readarrModule.elements.apiUrlInput.dataset.originalValue = settings.api_url;
                    if (readarrModule.elements.apiKeyInput) readarrModule.elements.apiKeyInput.dataset.originalValue = settings.api_key;
                    
                    // Update the rest of originalSettings
                    if (settings.readarr) app.originalSettings.readarr = {...settings.readarr};
                    
                    // Update configuration status
                    app.configuredApps.readarr = !!(settings.api_url && settings.api_key);
                    
                    // Update connection status
                    app.updateConnectionStatus();
                    
                    // Update home page connection status
                    app.updateHomeConnectionStatus();
                    
                    // Update logs connection status
                    app.updateLogsConnectionStatus();
                    
                    // Disable save buttons
                    readarrModule.updateSaveButtonState(false);
                    
                    // Show success message
                    if (data.changes_made) {
                        alert('Settings saved successfully and cycle restarted to apply changes!');
                    } else {
                        // Even if no changes were made according to backend, confirm save
                        alert('Settings saved successfully.'); 
                    }
                } else {
                    alert('Error saving settings: ' + (data.message || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Error saving settings:', error);
                alert('Error saving settings: ' + error.message);
            });
        }
    };
    
    // Initialize Readarr module
    readarrModule.init();
    
    // Override app.saveSettings to handle Readarr-specific logic when Readarr is active
    const originalSaveSettings = app.saveSettings;
    app.saveSettings = function() {
        if (app.currentApp === 'readarr') {
            if (!readarrModule.checkForChanges()) {
                // If no changes, don't do anything
                return;
            }
            
            const settings = readarrModule.getSettingsPayload();
            
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
                    if (readarrModule.elements.apiUrlInput) readarrModule.elements.apiUrlInput.dataset.originalValue = settings.api_url;
                    if (readarrModule.elements.apiKeyInput) readarrModule.elements.apiKeyInput.dataset.originalValue = settings.api_key;
                    
                    // Update the rest of originalSettings
                    if (settings.readarr) app.originalSettings.readarr = {...settings.readarr};
                    
                    // Update configuration status
                    app.configuredApps.readarr = !!(settings.api_url && settings.api_key);
                    
                    // Update connection status
                    app.updateConnectionStatus();
                    
                    // Update home page connection status
                    app.updateHomeConnectionStatus();
                    
                    // Update logs connection status
                    app.updateLogsConnectionStatus();
                    
                    // Disable save buttons
                    readarrModule.updateSaveButtonState(false);
                    
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
            // Call the original if we're not handling Readarr
            originalSaveSettings.call(app);
        }
    };
    
    // Attach Readarr-specific methods to the global app object
    app.readarrModule = readarrModule;
    
    // Override the global saveSettings function for Readarr
    app.saveSettings = function() {
        const payload = readarrModule.getSettingsPayload();
        
        // Use POST /api/settings endpoint
        fetch('/api/settings', { 
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update original values after successful save
                if (readarrModule.elements.apiUrlInput) readarrModule.elements.apiUrlInput.dataset.originalValue = settings.api_url;
                if (readarrModule.elements.apiKeyInput) readarrModule.elements.apiKeyInput.dataset.originalValue = settings.api_key;
                
                // Update the rest of originalSettings
                if (settings.readarr) app.originalSettings.readarr = {...settings.readarr};
                
                // Update configuration status
                app.configuredApps.readarr = !!(settings.api_url && settings.api_key);
                
                // Update connection status
                app.updateConnectionStatus();
                
                // Update home page connection status
                app.updateHomeConnectionStatus();
                
                // Update logs connection status
                app.updateLogsConnectionStatus();
                
                // Disable save buttons
                readarrModule.updateSaveButtonState(false);
                
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
    };

})(window.huntarrApp); // Pass the global app object
