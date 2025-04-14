/**
 * Settings form for Huntarr Sonarr
 * This file handles generating HTML forms for Sonarr settings
 */

const SettingsForms = {
    // Generate Sonarr settings form
    generateSonarrForm: function(container, settings = {}) {
        container.innerHTML = `
            <div class="settings-group">
                <h3>Sonarr Connection</h3>
                <div class="setting-item">
                    <label for="sonarr_api_url">URL:</label>
                    <input type="text" id="sonarr_api_url" value="${settings.api_url || ''}">
                    <p class="setting-help">Base URL for Sonarr (e.g., http://localhost:8989)</p>
                </div>
                <div class="setting-item">
                    <label for="sonarr_api_key">API Key:</label>
                    <input type="text" id="sonarr_api_key" value="${settings.api_key || ''}">
                    <p class="setting-help">API key for Sonarr</p>
                </div>
            </div>
            
            <div class="settings-group">
                <h3>Search Settings</h3>
                <div class="setting-item">
                    <label for="hunt_missing_shows">Missing Shows to Search:</label>
                    <input type="number" id="hunt_missing_shows" min="0" value="${settings.hunt_missing_shows || 1}">
                    <p class="setting-help">Number of missing shows to search per cycle (0 to disable)</p>
                </div>
                <div class="setting-item">
                    <label for="hunt_upgrade_episodes">Episodes to Upgrade:</label>
                    <input type="number" id="hunt_upgrade_episodes" min="0" value="${settings.hunt_upgrade_episodes || 0}">
                    <p class="setting-help">Number of episodes to search for quality upgrades per cycle (0 to disable)</p>
                </div>
                <div class="setting-item">
                    <label for="sleep_duration">Search Interval:</label>
                    <input type="number" id="sleep_duration" min="60" value="${settings.sleep_duration || 900}">
                    <p class="setting-help">Time between searches in seconds (<span id="sleep_duration_hours"></span>)</p>
                </div>
                <div class="setting-item">
                    <label for="state_reset_interval_hours">Reset Interval:</label>
                    <input type="number" id="state_reset_interval_hours" min="1" value="${settings.state_reset_interval_hours || 168}">
                    <p class="setting-help">Hours between state resets (default: 168 = 7 days)</p>
                </div>
            </div>
            
            <div class="settings-group">
                <h3>Additional Options</h3>
                <div class="setting-item">
                    <label for="monitored_only">Monitored Only:</label>
                    <label class="toggle-switch">
                        <input type="checkbox" id="monitored_only" ${settings.monitored_only !== false ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                    <p class="setting-help">Only search for monitored items</p>
                </div>
                <div class="setting-item">
                    <label for="skip_future_episodes">Skip Future Releases:</label>
                    <label class="toggle-switch">
                        <input type="checkbox" id="skip_future_episodes" ${settings.skip_future_episodes !== false ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                    <p class="setting-help">Skip searching for episodes with future air dates</p>
                </div>
                <div class="setting-item">
                    <label for="skip_series_refresh">Skip Series Refresh:</label>
                    <label class="toggle-switch">
                        <input type="checkbox" id="skip_series_refresh" ${settings.skip_series_refresh === true ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                    <p class="setting-help">Skip refreshing series metadata before searching</p>
                </div>
            </div>
            
            <div class="settings-group">
                <h3>Advanced Settings</h3>
                <div class="setting-item">
                    <label for="random_missing">Random Missing:</label>
                    <label class="toggle-switch">
                        <input type="checkbox" id="random_missing" ${settings.random_missing !== false ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                    <p class="setting-help">Select random missing items instead of sequential order</p>
                </div>
                <div class="setting-item">
                    <label for="random_upgrades">Random Upgrades:</label>
                    <label class="toggle-switch">
                        <input type="checkbox" id="random_upgrades" ${settings.random_upgrades !== false ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                    <p class="setting-help">Select random items for quality upgrades</p>
                </div>
                <div class="setting-item">
                    <label for="debug_mode">Debug Mode:</label>
                    <label class="toggle-switch">
                        <input type="checkbox" id="debug_mode" ${settings.debug_mode === true ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                    <p class="setting-help">Enable verbose logging for troubleshooting</p>
                </div>
                <div class="setting-item">
                    <label for="api_timeout">API Timeout:</label>
                    <input type="number" id="api_timeout" min="10" max="300" value="${settings.api_timeout || 60}">
                    <p class="setting-help">Timeout for API requests in seconds</p>
                </div>
                <div class="setting-item">
                    <label for="command_wait_delay">Command Wait Delay:</label>
                    <input type="number" id="command_wait_delay" min="1" value="${settings.command_wait_delay || 1}">
                    <p class="setting-help">Delay between checking command status in seconds</p>
                </div>
                <div class="setting-item">
                    <label for="command_wait_attempts">Command Wait Attempts:</label>
                    <input type="number" id="command_wait_attempts" min="1" value="${settings.command_wait_attempts || 600}">
                    <p class="setting-help">Maximum number of status check attempts</p>
                </div>
                <div class="setting-item">
                    <label for="minimum_download_queue_size">Min Download Queue Size:</label>
                    <input type="number" id="minimum_download_queue_size" min="-1" value="${settings.minimum_download_queue_size || -1}">
                    <p class="setting-help">Minimum download queue size to pause searching (-1 to disable)</p>
                </div>
                <div class="setting-item">
                    <label for="log_refresh_interval_seconds">Log Refresh Interval:</label>
                    <input type="number" id="log_refresh_interval_seconds" min="1" value="${settings.log_refresh_interval_seconds || 30}">
                    <p class="setting-help">Interval in seconds to refresh log display</p>
                </div>
            </div>
        `;
    },
    
    // Update duration display
    updateDurationDisplay: function() {
        // Function to update sleep duration display
        const updateSleepDisplay = function(inputId, spanId) {
            const input = document.getElementById(inputId);
            const span = document.getElementById(spanId);
            if (!input || !span) return;
            
            const seconds = parseInt(input.value);
            if (isNaN(seconds)) return;
            
            const hours = (seconds / 3600).toFixed(1);
            if (hours < 1) {
                const minutes = Math.round(seconds / 60);
                span.textContent = `${minutes} minutes`;
            } else {
                span.textContent = `${hours} hours`;
            }
        };

        // Update for Sonarr
        updateSleepDisplay('sleep_duration', 'sleep_duration_hours');
    }
};
