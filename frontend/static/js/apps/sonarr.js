// Sonarr-specific functionality

(function(app) {
    if (!app) {
        console.error("Huntarr App core is not loaded!");
        return;
    }

    const sonarrModule = {
        elements: {},

        init: function() {
            // Cache elements specific to Sonarr settings
            this.cacheElements();
            // Setup event listeners specific to Sonarr settings
            this.setupEventListeners();
            // Initial population of the form is handled by new-main.js
        },

        cacheElements: function() {
            // Cache elements used by Sonarr settings form
            this.elements.apiUrlInput = document.getElementById('sonarr_api_url');
            this.elements.apiKeyInput = document.getElementById('sonarr_api_key');
            this.elements.huntMissingShowsInput = document.getElementById('hunt_missing_shows');
            this.elements.huntUpgradeEpisodesInput = document.getElementById('hunt_upgrade_episodes');
            this.elements.sleepDurationInput = document.getElementById('sleep_duration'); // Note: ID might be generic now
            this.elements.sleepDurationHoursSpan = document.getElementById('sleep_duration_hours'); // Note: ID might be generic now
            this.elements.stateResetIntervalInput = document.getElementById('state_reset_interval_hours'); // Note: ID might be generic now
            this.elements.monitoredOnlyInput = document.getElementById('monitored_only'); // Note: ID might be generic now
            this.elements.skipFutureEpisodesInput = document.getElementById('skip_future_episodes');
            this.elements.skipSeriesRefreshInput = document.getElementById('skip_series_refresh');
            this.elements.randomMissingInput = document.getElementById('random_missing'); // Note: ID might be generic now
            this.elements.randomUpgradesInput = document.getElementById('random_upgrades'); // Note: ID might be generic now
            this.elements.debugModeInput = document.getElementById('debug_mode'); // Note: ID might be generic now
            this.elements.apiTimeoutInput = document.getElementById('api_timeout'); // Note: ID might be generic now
            this.elements.commandWaitDelayInput = document.getElementById('command_wait_delay'); // Note: ID might be generic now
            this.elements.commandWaitAttemptsInput = document.getElementById('command_wait_attempts'); // Note: ID might be generic now
            this.elements.minimumDownloadQueueSizeInput = document.getElementById('minimum_download_queue_size'); // Note: ID might be generic now
            // Add other Sonarr-specific elements if any
        },

        setupEventListeners: function() {
            // Add event listeners for Sonarr-specific controls if needed
            // Example: If there were unique interactions for Sonarr settings
            // Most change detection is now handled centrally by new-main.js

            // Update sleep duration display on input change
            if (this.elements.sleepDurationInput) {
                this.elements.sleepDurationInput.addEventListener('input', () => {
                    this.updateSleepDurationDisplay();
                    // Central change detection handles the rest
                });
            }
        },

        updateSleepDurationDisplay: function() {
            // Use the central utility function for updating duration display
            if (this.elements.sleepDurationInput && this.elements.sleepDurationHoursSpan) {
                const seconds = parseInt(this.elements.sleepDurationInput.value) || 900;
                app.updateDurationDisplay(seconds, this.elements.sleepDurationHoursSpan);
            }
        },

        // REMOVED: loadSettings function (handled by new-main.js)

        // REMOVED: checkForChanges function (handled by new-main.js)

        // REMOVED: updateSaveButtonState function (handled by new-main.js)

        // REMOVED: getSettingsPayload function (handled by new-main.js)

        // REMOVED: saveSettings function (handled by new-main.js)

        // REMOVED: Overriding of app.saveSettings
    };

    // Initialize Sonarr module
    sonarrModule.init();

    // Add the Sonarr module to the app for reference if needed elsewhere
    app.sonarrModule = sonarrModule;

})(window.huntarrUI); // Use the new global object name
