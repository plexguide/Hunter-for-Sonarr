// Lidarr-specific functionality

(function(app) {
    if (!app) {
        console.error("Huntarr App core is not loaded!");
        return;
    }

    const lidarrModule = {
        elements: {},

        init: function() {
            console.log('[Lidarr Module] Initializing...');
            this.cacheElements();
            this.setupEventListeners();
            // Settings are now loaded centrally by huntarrUI.loadAllSettings
            // this.loadSettings(); // REMOVED
        },

        cacheElements: function() {
            // Cache elements specific to the Lidarr settings form
            this.elements.apiUrlInput = document.getElementById('lidarr_api_url');
            this.elements.apiKeyInput = document.getElementById('lidarr_api_key');
            this.elements.huntMissingAlbumsInput = document.getElementById('hunt_missing_albums');
            this.elements.huntUpgradeTracksInput = document.getElementById('hunt_upgrade_tracks');
            this.elements.sleepDurationInput = document.getElementById('lidarr_sleep_duration');
            this.elements.sleepDurationHoursSpan = document.getElementById('lidarr_sleep_duration_hours');
            this.elements.stateResetIntervalInput = document.getElementById('lidarr_state_reset_interval_hours');
            this.elements.monitoredOnlyInput = document.getElementById('lidarr_monitored_only');
            this.elements.skipFutureReleasesInput = document.getElementById('lidarr_skip_future_releases');
            this.elements.skipArtistRefreshInput = document.getElementById('skip_artist_refresh');
            this.elements.randomMissingInput = document.getElementById('lidarr_random_missing');
            this.elements.randomUpgradesInput = document.getElementById('lidarr_random_upgrades');
            this.elements.debugModeInput = document.getElementById('lidarr_debug_mode');
            this.elements.apiTimeoutInput = document.getElementById('lidarr_api_timeout');
            this.elements.commandWaitDelayInput = document.getElementById('lidarr_command_wait_delay');
            this.elements.commandWaitAttemptsInput = document.getElementById('lidarr_command_wait_attempts');
            this.elements.minimumDownloadQueueSizeInput = document.getElementById('lidarr_minimum_download_queue_size');
            // Add any other Lidarr-specific elements
        },

        setupEventListeners: function() {
            // Keep listeners ONLY for elements with specific UI updates beyond simple value changes
            if (this.elements.sleepDurationInput) {
                this.elements.sleepDurationInput.addEventListener('input', () => {
                    this.updateSleepDurationDisplay();
                    // No need to call checkForChanges here, handled by delegation
                });
            }
            // Remove other input listeners previously used for checkForChanges
        },

        updateSleepDurationDisplay: function() {
            // This function remains as it updates a specific UI element
            if (this.elements.sleepDurationInput && this.elements.sleepDurationHoursSpan) {
                const seconds = parseInt(this.elements.sleepDurationInput.value) || 900;
                // Assuming app.updateDurationDisplay exists and is accessible
                if (app && typeof app.updateDurationDisplay === 'function') {
                     app.updateDurationDisplay(seconds, this.elements.sleepDurationHoursSpan);
                } else {
                    console.warn("app.updateDurationDisplay not found, sleep duration text might not update.");
                }
            }
        },

        // REMOVED loadSettings - Handled by huntarrUI.loadAllSettings
        // loadSettings: function() { ... },

        // REMOVED checkForChanges - Handled by huntarrUI.handleSettingChange and updateSaveResetButtonState
        // checkForChanges: function() { ... },

        // REMOVED updateSaveButtonState - Handled by huntarrUI.updateSaveResetButtonState
        // updateSaveButtonState: function(hasChanges) { ... },

        // REMOVED getSettingsPayload - Handled by huntarrUI.collectSettingsFromForm
        // getSettingsPayload: function() { ... },

        // REMOVED saveSettings override - Handled by huntarrUI.saveSettings
        // const originalSaveSettings = app.saveSettings;
        // app.saveSettings = function() { ... };
    };

    // Initialize Lidarr module
    document.addEventListener('DOMContentLoaded', () => {
        if (document.getElementById('lidarrSettings')) {
            lidarrModule.init();
            if (app) {
                app.lidarrModule = lidarrModule;
            }
        }
    });

})(window.huntarrUI); // Pass the global UI object
