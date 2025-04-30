/**
 * Settings forms for Huntarr
 * This file handles generating HTML forms for each app's settings
 */

const SettingsForms = {
    // Generate Sonarr settings form - Updated to use direct app settings without nesting
    generateSonarrForm: function(container, settings = {}) {
        // Make sure the instances array exists
        if (!settings.instances || !Array.isArray(settings.instances) || settings.instances.length === 0) {
            settings.instances = [{
                name: "Default",
                api_url: settings.api_url || "",
                api_key: settings.api_key || "",
                enabled: true
            }];
        }
        
        // Create a container for instances
        let instancesHtml = `
            <div class="settings-group">
                <h3>Sonarr Instances</h3>
                <div class="instances-container">
        `;
        
        // Generate form elements for each instance
        settings.instances.forEach((instance, index) => {
            instancesHtml += `
                <div class="instance-item" data-instance-id="${index}">
                    <div class="instance-header">
                        <h4>Instance ${index + 1}: ${instance.name || 'Unnamed'}</h4>
                        <div class="instance-actions">
                            ${index > 0 ? '<button type="button" class="remove-instance-btn">Remove</button>' : ''}
                        </div>
                    </div>
                    <div class="instance-content">
                        <div class="setting-item">
                            <label for="sonarr_instance_${index}_name">Name:</label>
                            <input type="text" id="sonarr_instance_${index}_name" value="${instance.name || ''}">
                            <p class="setting-help">Friendly name for this Sonarr instance</p>
                        </div>
                        <div class="setting-item">
                            <label for="sonarr_instance_${index}_api_url">URL:</label>
                            <input type="text" id="sonarr_instance_${index}_api_url" value="${instance.api_url || ''}">
                            <p class="setting-help">Base URL for Sonarr (e.g., http://localhost:8989)</p>
                        </div>
                        <div class="setting-item">
                            <label for="sonarr_instance_${index}_api_key">API Key:</label>
                            <input type="text" id="sonarr_instance_${index}_api_key" value="${instance.api_key || ''}">
                            <p class="setting-help">API key for Sonarr</p>
                        </div>
                        <div class="setting-item">
                            <label for="sonarr_instance_${index}_enabled">Enabled:</label>
                            <label class="toggle-switch">
                                <input type="checkbox" id="sonarr_instance_${index}_enabled" class="instance-enabled" ${instance.enabled !== false ? 'checked' : ''}>
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                        <div class="setting-item">
                            <button type="button" class="test-connection-btn" data-instance-id="${index}">Test Connection</button>
                            <span class="connection-status" id="sonarr_instance_${index}_status"></span>
                        </div>
                    </div>
                </div>
            `;
        });
        
        // Add a button to add new instances (limit to 9 total)
        instancesHtml += `
                    <div class="add-instance-container">
                        <button type="button" id="add-sonarr-instance" class="add-instance-btn" ${settings.instances.length >= 9 ? 'disabled' : ''}> 
                            Add Sonarr Instance (${settings.instances.length}/9)
                        </button>
                    </div>
                </div>
            </div>
        `; // Close settings-group
        
        // Original structure: Combine HTML sequentially
        container.innerHTML = `
            ${instancesHtml}
            
            <div class="settings-group">
                <h3>Search Settings</h3>
                <div class="setting-item">
                    <label for="hunt_missing_mode">Missing Search Mode:</label>
                    <select id="hunt_missing_mode">
                        <option value="episodes" ${settings.hunt_missing_mode === 'episodes' ? 'selected' : ''}>Episodes</option>
                        <option value="seasons_packs" ${settings.hunt_missing_mode === 'seasons_packs' ? 'selected' : ''}>Season [Packs]</option>
                        <option value="seasons" ${settings.hunt_missing_mode === 'seasons' ? 'selected' : ''}>Season [Solo]</option>
                        <option value="shows" ${settings.hunt_missing_mode === 'shows' ? 'selected' : ''}>Shows</option>
                    </select>
                    <p class="setting-help">How to group and search for missing items (Season Packs recommended for torrent users)</p>
                </div>
                <div class="setting-item">
                    <label for="hunt_missing_items">Missing Items to Search:</label>
                    <input type="number" id="hunt_missing_items" min="0" value="${settings.hunt_missing_items || settings.hunt_missing_shows || 1}">
                    <p class="setting-help">Number of missing items to search per cycle (0 to disable)</p>
                </div>
                <div class="setting-item">
                    <label for="hunt_upgrade_items">Episodes to Upgrade:</label>
                    <input type="number" id="hunt_upgrade_items" min="0" value="${settings.hunt_upgrade_items || settings.hunt_upgrade_episodes || 0}">
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
            </div>
        `;

        // Add event listeners for the instance management
        SettingsForms.setupInstanceManagement(container, 'sonarr', settings.instances.length);
    },
    
    // Generate Radarr settings form
    generateRadarrForm: function(container, settings = {}) {
        // Make sure the instances array exists
        if (!settings.instances || !Array.isArray(settings.instances) || settings.instances.length === 0) {
            settings.instances = [{
                name: "Default",
                api_url: settings.api_url || "",
                api_key: settings.api_key || "",
                enabled: true
            }];
        }
        
        // Create a container for instances with a scrollable area for many instances
        let instancesHtml = `
            <div class="settings-group">
                <h3>Radarr Instances</h3>
                <div class="instances-container">
        `;
        
        // Generate form elements for each instance
        settings.instances.forEach((instance, index) => {
            instancesHtml += `
                <div class="instance-item" data-instance-id="${index}">
                    <div class="instance-header">
                        <h4>Instance ${index + 1}: ${instance.name || 'Unnamed'}</h4>
                        <div class="instance-actions">
                            ${index > 0 ? '<button type="button" class="remove-instance-btn">Remove</button>' : ''}
                        </div>
                    </div>
                    <div class="instance-content">
                        <div class="setting-item">
                            <label for="radarr_instance_${index}_name">Name:</label>
                            <input type="text" id="radarr_instance_${index}_name" value="${instance.name || ''}">
                            <p class="setting-help">Friendly name for this Radarr instance</p>
                        </div>
                        <div class="setting-item">
                            <label for="radarr_instance_${index}_api_url">URL:</label>
                            <input type="text" id="radarr_instance_${index}_api_url" value="${instance.api_url || ''}">
                            <p class="setting-help">Base URL for Radarr (e.g., http://localhost:7878)</p>
                        </div>
                        <div class="setting-item">
                            <label for="radarr_instance_${index}_api_key">API Key:</label>
                            <input type="text" id="radarr_instance_${index}_api_key" value="${instance.api_key || ''}">
                            <p class="setting-help">API key for Radarr</p>
                        </div>
                        <div class="setting-item">
                            <label for="radarr_instance_${index}_enabled">Enabled:</label>
                            <label class="toggle-switch">
                                <input type="checkbox" id="radarr_instance_${index}_enabled" class="instance-enabled" ${instance.enabled !== false ? 'checked' : ''}>
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                        <div class="setting-item">
                            <button type="button" class="test-connection-btn" data-instance-id="${index}">Test Connection</button>
                            <span class="connection-status" id="radarr_instance_${index}_status"></span>
                        </div>
                    </div>
                </div>
            `;
        });
        
        // Add a button to add new instances (limit to 9 total)
        instancesHtml += `
                <div class="add-instance-container">
                    <button type="button" id="add-radarr-instance" class="add-instance-btn" ${settings.instances.length >= 9 ? 'disabled' : ''}>
                        Add Radarr Instance (${settings.instances.length}/9)
                    </button>
                </div>
            </div>
        </div>
        `;
        
        // Continue with the rest of the settings form
        container.innerHTML = `
            ${instancesHtml}
            
            <div class="settings-group">
                <h3>Search Settings</h3>
                <div class="setting-item">
                    <label for="hunt_missing_movies">Missing Movies to Search:</label>
                    <input type="number" id="hunt_missing_movies" min="0" value="${settings.hunt_missing_movies || 1}">
                    <p class="setting-help">Number of missing movies to search per cycle (0 to disable)</p>
                </div>
                <div class="setting-item">
                    <label for="hunt_upgrade_movies">Movies to Upgrade:</label>
                    <input type="number" id="hunt_upgrade_movies" min="0" value="${settings.hunt_upgrade_movies || 0}">
                    <p class="setting-help">Number of movies to search for quality upgrades per cycle (0 to disable)</p>
                </div>
                <div class="setting-item">
                    <label for="radarr_sleep_duration">Search Interval:</label>
                    <input type="number" id="radarr_sleep_duration" min="60" value="${settings.sleep_duration || 900}">
                    <p class="setting-help">Time between searches in seconds (<span id="radarr_sleep_duration_hours"></span>)</p>
                </div>
                <div class="setting-item">
                    <label for="radarr_state_reset_interval_hours">Reset Interval:</label>
                    <input type="number" id="radarr_state_reset_interval_hours" min="1" value="${settings.state_reset_interval_hours || 168}">
                    <p class="setting-help">Hours between state resets (default: 168 = 7 days)</p>
                </div>
            </div>
            
            <div class="settings-group">
                <h3>Additional Options</h3>
                <div class="setting-item">
                    <label for="radarr_monitored_only">Monitored Only:</label>
                    <label class="toggle-switch">
                        <input type="checkbox" id="radarr_monitored_only" ${settings.monitored_only !== false ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                    <p class="setting-help">Only search for monitored items</p>
                </div>
                <div class="setting-item">
                    <label for="skip_future_releases">Skip Future Releases:</label>
                    <label class="toggle-switch">
                        <input type="checkbox" id="skip_future_releases" ${settings.skip_future_releases !== false ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                    <p class="setting-help">Skip searching for movies with future release dates</p>
                </div>
                <div class="setting-item">
                    <label for="skip_movie_refresh">Skip Movie Refresh:</label>
                    <label class="toggle-switch">
                        <input type="checkbox" id="skip_movie_refresh" ${settings.skip_movie_refresh === true ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                    <p class="setting-help">Skip refreshing movie metadata before searching</p>
                </div>
            </div>
            
            <div class="settings-group">
                <h3>Advanced Settings</h3>
                <div class="setting-item">
                    <label for="radarr_random_missing">Random Missing:</label>
                    <label class="toggle-switch">
                        <input type="checkbox" id="radarr_random_missing" ${settings.random_missing !== false ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                    <p class="setting-help">Select random missing items instead of sequential order</p>
                </div>
                <div class="setting-item">
                    <label for="radarr_random_upgrades">Random Upgrades:</label>
                    <label class="toggle-switch">
                        <input type="checkbox" id="radarr_random_upgrades" ${settings.random_upgrades !== false ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                    <p class="setting-help">Select random items for quality upgrades</p>
                </div>
                <div class="setting-item">
                    <label for="radarr_api_timeout">API Timeout:</label>
                    <input type="number" id="radarr_api_timeout" min="10" max="300" value="${settings.api_timeout || 60}">
                    <p class="setting-help">Timeout for API requests in seconds</p>
                </div>
                <div class="setting-item">
                    <label for="radarr_command_wait_delay">Command Wait Delay:</label>
                    <input type="number" id="radarr_command_wait_delay" min="1" value="${settings.command_wait_delay || 1}">
                    <p class="setting-help">Delay between checking command status in seconds</p>
                </div>
                <div class="setting-item">
                    <label for="radarr_command_wait_attempts">Command Wait Attempts:</label>
                    <input type="number" id="radarr_command_wait_attempts" min="1" value="${settings.command_wait_attempts || 600}">
                    <p class="setting-help">Maximum number of status check attempts</p>
                </div>
                <div class="setting-item">
                    <label for="radarr_minimum_download_queue_size">Min Download Queue Size:</label>
                    <input type="number" id="radarr_minimum_download_queue_size" min="-1" value="${settings.minimum_download_queue_size || -1}">
                    <p class="setting-help">Minimum download queue size to pause searching (-1 to disable)</p>
                </div>
            </div>
        `;

        // Add event listeners for the instance management
        SettingsForms.setupInstanceManagement(container, 'radarr', settings.instances.length);
    },
    
    // Generate Lidarr settings form
    generateLidarrForm: function(container, settings = {}) {
        // Make sure the instances array exists
        if (!settings.instances || !Array.isArray(settings.instances) || settings.instances.length === 0) {
            settings.instances = [{
                name: "Default",
                api_url: settings.api_url || "",
                api_key: settings.api_key || "",
                enabled: true
            }];
        }
        
        // Create a container for instances with a scrollable area for many instances
        let instancesHtml = `
            <div class="settings-group">
                <h3>Lidarr Instances</h3>
                <div class="instances-container">
        `;
        
        // Generate form elements for each instance
        settings.instances.forEach((instance, index) => {
            instancesHtml += `
                <div class="instance-item" data-instance-id="${index}">
                    <div class="instance-header">
                        <h4>Instance ${index + 1}: ${instance.name || 'Unnamed'}</h4>
                        <div class="instance-actions">
                            ${index > 0 ? '<button type="button" class="remove-instance-btn">Remove</button>' : ''}
                        </div>
                    </div>
                    <div class="instance-content">
                        <div class="setting-item">
                            <label for="lidarr_instance_${index}_name">Name:</label>
                            <input type="text" id="lidarr_instance_${index}_name" value="${instance.name || ''}">
                            <p class="setting-help">Friendly name for this Lidarr instance</p>
                        </div>
                        <div class="setting-item">
                            <label for="lidarr_instance_${index}_api_url">URL:</label>
                            <input type="text" id="lidarr_instance_${index}_api_url" value="${instance.api_url || ''}">
                            <p class="setting-help">Base URL for Lidarr (e.g., http://localhost:8686)</p>
                        </div>
                        <div class="setting-item">
                            <label for="lidarr_instance_${index}_api_key">API Key:</label>
                            <input type="text" id="lidarr_instance_${index}_api_key" value="${instance.api_key || ''}">
                            <p class="setting-help">API key for Lidarr</p>
                        </div>
                        <div class="setting-item">
                            <label for="lidarr_instance_${index}_enabled">Enabled:</label>
                            <label class="toggle-switch">
                                <input type="checkbox" id="lidarr_instance_${index}_enabled" class="instance-enabled" ${instance.enabled !== false ? 'checked' : ''}>
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                        <div class="setting-item">
                            <button type="button" class="test-connection-btn" data-instance-id="${index}">Test Connection</button>
                            <span class="connection-status" id="lidarr_instance_${index}_status"></span>
                        </div>
                    </div>
                </div>
            `;
        });
        
        // Add a button to add new instances (limit to 9 total)
        instancesHtml += `
                <div class="add-instance-container">
                    <button type="button" id="add-lidarr-instance" class="add-instance-btn" ${settings.instances.length >= 9 ? 'disabled' : ''}>
                        Add Lidarr Instance (${settings.instances.length}/9)
                    </button>
                </div>
            </div>
        </div>
        `;
        
        // Continue with the rest of the settings form
        container.innerHTML = `
            ${instancesHtml}
            
            <div class="settings-group">
                <h3>Search Settings</h3>
                <div class="setting-item">
                    <label for="hunt_missing_mode">Missing Search Mode:</label>
                    <select id="hunt_missing_mode">
                        <option value="artist" ${settings.hunt_missing_mode === 'album' ? '' : 'selected'}>Artist</option>
                        <option value="album" ${settings.hunt_missing_mode === 'album' ? 'selected' : ''}>Album</option>
                    </select>
                    <p class="setting-help">Whether to search by artist (all missing albums for artist) or individual albums</p>
                </div>
                <div class="setting-item">
                    <label for="hunt_missing_items">Missing Items to Search:</label>
                    <input type="number" id="hunt_missing_items" min="0" value="${settings.hunt_missing_items || 1}">
                    <p class="setting-help">Number of artists with missing albums to search per cycle (0 to disable)</p>
                </div>
                
                <div class="setting-item">
                    <label for="hunt_upgrade_items">Items to Upgrade:</label>
                    <input type="number" id="hunt_upgrade_items" min="0" value="${settings.hunt_upgrade_items || 0}">
                    <p class="setting-help">Number of albums to search for quality upgrades per cycle (0 to disable)</p>
                </div>
                <div class="setting-item">
                    <label for="lidarr_sleep_duration">Search Interval:</label>
                    <input type="number" id="lidarr_sleep_duration" min="60" value="${settings.sleep_duration || 900}">
                    <p class="setting-help">Time between searches in seconds (<span id="lidarr_sleep_duration_hours"></span>)</p>
                </div>
                <div class="setting-item">
                    <label for="lidarr_state_reset_interval_hours">Reset Interval:</label>
                    <input type="number" id="lidarr_state_reset_interval_hours" min="1" value="${settings.state_reset_interval_hours || 168}">
                    <p class="setting-help">Hours between state resets (default: 168 = 7 days)</p>
                </div>
            </div>
            
            <div class="settings-group">
                <h3>Additional Options</h3>
                <div class="setting-item">
                    <label for="lidarr_monitored_only">Monitored Only:</label>
                    <label class="toggle-switch">
                        <input type="checkbox" id="lidarr_monitored_only" ${settings.monitored_only !== false ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                    <p class="setting-help">Only search for monitored items</p>
                </div>
                <div class="setting-item">
                    <label for="lidarr_skip_future_releases">Skip Future Releases:</label>
                    <label class="toggle-switch">
                        <input type="checkbox" id="lidarr_skip_future_releases" ${settings.skip_future_releases !== false ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                    <p class="setting-help">Skip searching for albums with future release dates</p>
                </div>
                <div class="setting-item">
                    <label for="skip_artist_refresh">Skip Artist Refresh:</label>
                    <label class="toggle-switch">
                        <input type="checkbox" id="skip_artist_refresh" ${settings.skip_artist_refresh === true ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                    <p class="setting-help">Skip refreshing artist metadata before searching</p>
                </div>
            </div>
            
            <div class="settings-group">
                <h3>Advanced Settings</h3>
                <div class="setting-item">
                    <label for="lidarr_random_missing">Random Missing:</label>
                    <label class="toggle-switch">
                        <input type="checkbox" id="lidarr_random_missing" ${settings.random_missing !== false ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                    <p class="setting-help">Select random missing items instead of sequential order</p>
                </div>
                <div class="setting-item">
                    <label for="lidarr_random_upgrades">Random Upgrades:</label>
                    <label class="toggle-switch">
                        <input type="checkbox" id="lidarr_random_upgrades" ${settings.random_upgrades !== false ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                    <p class="setting-help">Select random items for quality upgrades</p>
                </div>
                <div class="setting-item">
                    <label for="lidarr_api_timeout">API Timeout:</label>
                    <input type="number" id="lidarr_api_timeout" min="10" max="300" value="${settings.api_timeout || 60}">
                    <p class="setting-help">Timeout for API requests in seconds</p>
                </div>
                <div class="setting-item">
                    <label for="lidarr_command_wait_delay">Command Wait Delay:</label>
                    <input type="number" id="lidarr_command_wait_delay" min="1" value="${settings.command_wait_delay || 1}">
                    <p class="setting-help">Delay between checking command status in seconds</p>
                </div>
                <div class="setting-item">
                    <label for="lidarr_command_wait_attempts">Command Wait Attempts:</label>
                    <input type="number" id="lidarr_command_wait_attempts" min="1" value="${settings.command_wait_attempts || 600}">
                    <p class="setting-help">Maximum number of status check attempts</p>
                </div>
                <div class="setting-item">
                    <label for="lidarr_minimum_download_queue_size">Min Download Queue Size:</label>
                    <input type="number" id="lidarr_minimum_download_queue_size" min="-1" value="${settings.minimum_download_queue_size || -1}">
                    <p class="setting-help">Minimum download queue size to pause searching (-1 to disable)</p>
                </div>
            </div>
        `;

        // Add event listeners for the instance management
        SettingsForms.setupInstanceManagement(container, 'lidarr', settings.instances.length);
    },
    
    // Generate Readarr settings form
    generateReadarrForm: function(container, settings = {}) {
        // Make sure the instances array exists
        if (!settings.instances || !Array.isArray(settings.instances) || settings.instances.length === 0) {
            settings.instances = [{
                name: "Default",
                api_url: settings.api_url || "",
                api_key: settings.api_key || "",
                enabled: true
            }];
        }
        
        // Create a container for instances with a scrollable area for many instances
        let instancesHtml = `
            <div class="settings-group">
                <h3>Readarr Instances</h3>
                <div class="instances-container">
        `;
        
        // Generate form elements for each instance
        settings.instances.forEach((instance, index) => {
            instancesHtml += `
                <div class="instance-item" data-instance-id="${index}">
                    <div class="instance-header">
                        <h4>Instance ${index + 1}: ${instance.name || 'Unnamed'}</h4>
                        <div class="instance-actions">
                            ${index > 0 ? '<button type="button" class="remove-instance-btn">Remove</button>' : ''}
                        </div>
                    </div>
                    <div class="instance-content">
                        <div class="setting-item">
                            <label for="readarr_instance_${index}_name">Name:</label>
                            <input type="text" id="readarr_instance_${index}_name" value="${instance.name || ''}">
                            <p class="setting-help">Friendly name for this Readarr instance</p>
                        </div>
                        <div class="setting-item">
                            <label for="readarr_instance_${index}_api_url">URL:</label>
                            <input type="text" id="readarr_instance_${index}_api_url" value="${instance.api_url || ''}">
                            <p class="setting-help">Base URL for Readarr (e.g., http://localhost:8787)</p>
                        </div>
                        <div class="setting-item">
                            <label for="readarr_instance_${index}_api_key">API Key:</label>
                            <input type="text" id="readarr_instance_${index}_api_key" value="${instance.api_key || ''}">
                            <p class="setting-help">API key for Readarr</p>
                        </div>
                        <div class="setting-item">
                            <label for="readarr_instance_${index}_enabled">Enabled:</label>
                            <label class="toggle-switch">
                                <input type="checkbox" id="readarr_instance_${index}_enabled" class="instance-enabled" ${instance.enabled !== false ? 'checked' : ''}>
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                        <div class="setting-item">
                            <button type="button" class="test-connection-btn" data-instance-id="${index}">Test Connection</button>
                            <span class="connection-status" id="readarr_instance_${index}_status"></span>
                        </div>
                    </div>
                </div>
            `;
        });
        
        // Add a button to add new instances (limit to 9 total)
        instancesHtml += `
                <div class="add-instance-container">
                    <button type="button" id="add-readarr-instance" class="add-instance-btn" ${settings.instances.length >= 9 ? 'disabled' : ''}>
                        Add Readarr Instance (${settings.instances.length}/9)
                    </button>
                </div>
            </div>
        </div>
        `;
        
        // Continue with the rest of the settings form
        container.innerHTML = `
            ${instancesHtml}
            
            <div class="settings-group">
                <h3>Search Settings</h3>
                <div class="setting-item">
                    <label for="hunt_missing_books">Missing Books to Search:</label>
                    <input type="number" id="hunt_missing_books" min="0" value="${settings.hunt_missing_books || 1}">
                    <p class="setting-help">Number of missing books to search per cycle (0 to disable)</p>
                </div>
                <div class="setting-item">
                    <label for="hunt_upgrade_books">Books to Upgrade:</label>
                    <input type="number" id="hunt_upgrade_books" min="0" value="${settings.hunt_upgrade_books || 0}">
                    <p class="setting-help">Number of books to search for quality upgrades per cycle (0 to disable)</p>
                </div>
                <div class="setting-item">
                    <label for="readarr_sleep_duration">Search Interval:</label>
                    <input type="number" id="readarr_sleep_duration" min="60" value="${settings.sleep_duration || 900}">
                    <p class="setting-help">Time between searches in seconds (<span id="readarr_sleep_duration_hours"></span>)</p>
                </div>
                <div class="setting-item">
                    <label for="readarr_state_reset_interval_hours">Reset Interval:</label>
                    <input type="number" id="readarr_state_reset_interval_hours" min="1" value="${settings.state_reset_interval_hours || 168}">
                    <p class="setting-help">Hours between state resets (default: 168 = 7 days)</p>
                </div>
            </div>
            
            <div class="settings-group">
                <h3>Additional Options</h3>
                <div class="setting-item">
                    <label for="readarr_monitored_only">Monitored Only:</label>
                    <label class="toggle-switch">
                        <input type="checkbox" id="readarr_monitored_only" ${settings.monitored_only !== false ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                    <p class="setting-help">Only search for monitored items</p>
                </div>
                <div class="setting-item">
                    <label for="readarr_skip_future_releases">Skip Future Releases:</label>
                    <label class="toggle-switch">
                        <input type="checkbox" id="readarr_skip_future_releases" ${settings.skip_future_releases !== false ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                    <p class="setting-help">Skip searching for books with future release dates</p>
                </div>
                <div class="setting-item">
                    <label for="skip_author_refresh">Skip Author Refresh:</label>
                    <label class="toggle-switch">
                        <input type="checkbox" id="skip_author_refresh" ${settings.skip_author_refresh === true ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                    <p class="setting-help">Skip refreshing author metadata before searching</p>
                </div>
            </div>
            
            <div class="settings-group">
                <h3>Advanced Settings</h3>
                <div class="setting-item">
                    <label for="readarr_random_missing">Random Missing:</label>
                    <label class="toggle-switch">
                        <input type="checkbox" id="readarr_random_missing" ${settings.random_missing !== false ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                    <p class="setting-help">Select random missing items instead of sequential order</p>
                </div>
                <div class="setting-item">
                    <label for="readarr_random_upgrades">Random Upgrades:</label>
                    <label class="toggle-switch">
                        <input type="checkbox" id="readarr_random_upgrades" ${settings.random_upgrades !== false ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                    <p class="setting-help">Select random items for quality upgrades</p>
                </div>
                <div class="setting-item">
                    <label for="readarr_api_timeout">API Timeout:</label>
                    <input type="number" id="readarr_api_timeout" min="10" max="300" value="${settings.api_timeout || 60}">
                    <p class="setting-help">Timeout for API requests in seconds</p>
                </div>
                <div class="setting-item">
                    <label for="readarr_command_wait_delay">Command Wait Delay:</label>
                    <input type="number" id="readarr_command_wait_delay" min="1" value="${settings.command_wait_delay || 1}">
                    <p class="setting-help">Delay between checking command status in seconds</p>
                </div>
                <div class="setting-item">
                    <label for="readarr_command_wait_attempts">Command Wait Attempts:</label>
                    <input type="number" id="readarr_command_wait_attempts" min="1" value="${settings.command_wait_attempts || 600}">
                    <p class="setting-help">Maximum number of status check attempts</p>
                </div>
                <div class="setting-item">
                    <label for="readarr_minimum_download_queue_size">Min Download Queue Size:</label>
                    <input type="number" id="readarr_minimum_download_queue_size" min="-1" value="${settings.minimum_download_queue_size || -1}">
                    <p class="setting-help">Minimum download queue size to pause searching (-1 to disable)</p>
                </div>
            </div>
        `;

        // Add event listeners for the instance management
        SettingsForms.setupInstanceManagement(container, 'readarr', settings.instances.length);
    },
    
    // Generate Whisparr settings form
    generateWhisparrForm: function(container, settings = {}) {
        // Make sure the instances array exists
        if (!settings.instances || !Array.isArray(settings.instances) || settings.instances.length === 0) {
            settings.instances = [{
                name: "Default",
                api_url: settings.api_url || "",
                api_key: settings.api_key || "",
                enabled: true
            }];
        }
        
        // Create a container for instances with a scrollable area for many instances
        let instancesHtml = `
            <div class="settings-group">
                <h3>Whisparr Instances</h3>
                <div class="instances-container">
        `;
        
        // Generate form elements for each instance
        settings.instances.forEach((instance, index) => {
            instancesHtml += `
                <div class="instance-item" data-instance-id="${index}">
                    <div class="instance-header">
                        <h4>Instance ${index + 1}: ${instance.name || 'Unnamed'}</h4>
                        <div class="instance-actions">
                            ${index > 0 ? '<button type="button" class="remove-instance-btn">Remove</button>' : ''}
                        </div>
                    </div>
                    <div class="instance-content">
                        <div class="setting-item">
                            <label for="whisparr_instance_${index}_name">Name:</label>
                            <input type="text" id="whisparr_instance_${index}_name" value="${instance.name || ''}">
                            <p class="setting-help">Friendly name for this Whisparr instance</p>
                        </div>
                        <div class="setting-item">
                            <label for="whisparr_instance_${index}_api_url">URL:</label>
                            <input type="text" id="whisparr_instance_${index}_api_url" value="${instance.api_url || ''}">
                            <p class="setting-help">Base URL for Whisparr (e.g., http://localhost:6969)</p>
                        </div>
                        <div class="setting-item">
                            <label for="whisparr_instance_${index}_api_key">API Key:</label>
                            <input type="text" id="whisparr_instance_${index}_api_key" value="${instance.api_key || ''}">
                            <p class="setting-help">API key for Whisparr</p>
                        </div>
                        <div class="setting-item">
                            <label for="whisparr_instance_${index}_enabled">Enabled:</label>
                            <label class="toggle-switch">
                                <input type="checkbox" id="whisparr_instance_${index}_enabled" class="instance-enabled" ${instance.enabled !== false ? 'checked' : ''}>
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                        <div class="setting-item">
                            <button type="button" class="test-connection-btn" data-instance-id="${index}">Test Connection</button>
                            <span class="connection-status" id="whisparr_instance_${index}_status"></span>
                        </div>
                    </div>
                </div>
            `;
        });
        
        // Add a button to add new instances (limit to 9 total)
        instancesHtml += `
                <div class="add-instance-container">
                    <button type="button" id="add-whisparr-instance" class="add-instance-btn" ${settings.instances.length >= 9 ? 'disabled' : ''}>
                        Add Whisparr Instance (${settings.instances.length}/9)
                    </button>
                </div>
            </div>
        </div>
        `;
        
        // Continue with the rest of the settings form
        container.innerHTML = `
            ${instancesHtml}
            
            <div class="settings-group">
                <h3>API Version</h3>
                <div class="setting-item">
                    <label for="whisparr_version">Whisparr Version:</label>
                    <select id="whisparr_version">
                        <option value="v3" ${settings.whisparr_version === 'v3' || !settings.whisparr_version ? 'selected' : ''}>v3 (Eros)</option>
                        <option value="v2" ${settings.whisparr_version === 'v2' ? 'selected' : ''}>v2 (Legacy)</option>
                    </select>
                    <p class="setting-help">Select the API version of your Whisparr installation. Default is v3 (Eros). NOTE: Only v2 works for now!</p>
                </div>
            </div>
            
            <div class="settings-group">
                <h3>Search Settings</h3>
                <div class="setting-item">
                    <label for="hunt_missing_items">Missing Items to Search:</label>
                    <input type="number" id="hunt_missing_items" min="0" value="${settings.hunt_missing_items || settings.hunt_missing_scenes || 1}">
                    <p class="setting-help">Number of missing items to search per cycle (0 to disable)</p>
                </div>
                <div class="setting-item">
                    <label for="hunt_upgrade_items">Items to Upgrade:</label>
                    <input type="number" id="hunt_upgrade_items" min="0" value="${settings.hunt_upgrade_items || settings.hunt_upgrade_scenes || 0}">
                    <p class="setting-help">Number of items to search for quality upgrades per cycle (0 to disable)</p>
                </div>
                <div class="setting-item">
                    <label for="whisparr_sleep_duration">Search Interval:</label>
                    <input type="number" id="whisparr_sleep_duration" min="60" value="${settings.sleep_duration || 900}">
                    <p class="setting-help">Time between searches in seconds (<span id="whisparr_sleep_duration_hours"></span>)</p>
                </div>
                <div class="setting-item">
                    <label for="whisparr_state_reset_interval_hours">Reset Interval:</label>
                    <input type="number" id="whisparr_state_reset_interval_hours" min="1" value="${settings.state_reset_interval_hours || 168}">
                    <p class="setting-help">Hours between state resets (default: 168 = 7 days)</p>
                </div>
            </div>
            
            <div class="settings-group">
                <h3>Additional Options</h3>
                <div class="setting-item">
                    <label for="whisparr_monitored_only">Monitored Only:</label>
                    <label class="toggle-switch">
                        <input type="checkbox" id="whisparr_monitored_only" ${settings.monitored_only !== false ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                    <p class="setting-help">Only search for monitored items</p>
                </div>
                <div class="setting-item">
                    <label for="whisparr_skip_future_releases">Skip Future Releases:</label>
                    <label class="toggle-switch">
                        <input type="checkbox" id="whisparr_skip_future_releases" ${settings.skip_future_releases !== false ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                    <p class="setting-help">Skip searching for scenes with future release dates</p>
                </div>
                <div class="setting-item">
                    <label for="skip_scene_refresh">Skip Scene Refresh:</label>
                    <label class="toggle-switch">
                        <input type="checkbox" id="skip_scene_refresh" ${settings.skip_scene_refresh === true ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                    <p class="setting-help">Skip refreshing scene metadata before searching</p>
                </div>
            </div>
            
            <div class="settings-group">
                <h3>Advanced Settings</h3>
                <div class="setting-item">
                    <label for="whisparr_random_missing">Random Missing:</label>
                    <label class="toggle-switch">
                        <input type="checkbox" id="whisparr_random_missing" ${settings.random_missing !== false ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                    <p class="setting-help">Select random missing items instead of sequential order</p>
                </div>
                <div class="setting-item">
                    <label for="whisparr_random_upgrades">Random Upgrades:</label>
                    <label class="toggle-switch">
                        <input type="checkbox" id="whisparr_random_upgrades" ${settings.random_upgrades !== false ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                    <p class="setting-help">Select random items for quality upgrades</p>
                </div>
                <div class="setting-item">
                    <label for="whisparr_api_timeout">API Timeout:</label>
                    <input type="number" id="whisparr_api_timeout" min="10" max="300" value="${settings.api_timeout || 120}">
                    <p class="setting-help">Timeout for API requests in seconds</p>
                </div>
                <div class="setting-item">
                    <label for="whisparr_command_wait_delay">Command Wait Delay:</label>
                    <input type="number" id="whisparr_command_wait_delay" min="1" value="${settings.command_wait_delay || 1}">
                    <p class="setting-help">Delay between checking command status in seconds</p>
                </div>
                <div class="setting-item">
                    <label for="whisparr_command_wait_attempts">Command Wait Attempts:</label>
                    <input type="number" id="whisparr_command_wait_attempts" min="1" value="${settings.command_wait_attempts || 600}">
                    <p class="setting-help">Maximum number of status check attempts</p>
                </div>
                <div class="setting-item">
                    <label for="whisparr_minimum_download_queue_size">Min Download Queue Size:</label>
                    <input type="number" id="whisparr_minimum_download_queue_size" min="-1" value="${settings.minimum_download_queue_size || -1}">
                    <p class="setting-help">Minimum download queue size to pause searching (-1 to disable)</p>
                </div>
            </div>
        `;

        // Add event listeners for the instance management
        SettingsForms.setupInstanceManagement(container, 'whisparr', settings.instances.length);
    },
    
    // Generate Swaparr settings form
    generateSwaparrForm: function(container, settings = {}) {
        // Create the HTML for the Swaparr settings form
        container.innerHTML = `
            <div class="settings-group">
                <h3>Swaparr (Beta) - Only For Torrent Users</h3>
                <div class="setting-item">
                    <p>Swaparr addresses the issue of stalled downloads and I rewrote it to support Huntarr. Visit Swaparr's <a href="https://github.com/ThijmenGThN/swaparr" target="_blank">GitHub</a> for more information and support the developer!</p>
                </div>
            </div>

            <div class="settings-group">
                <h3>Swaparr Settings</h3>
                <div class="setting-item">
                    <label for="swaparr_enabled">Enable Swaparr:</label>
                    <label class="toggle-switch">
                        <input type="checkbox" id="swaparr_enabled" ${settings.enabled ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                    <p class="setting-help">Enable automatic handling of stalled downloads</p>
                </div>
                <div class="setting-item">
                    <label for="swaparr_max_strikes">Maximum Strikes:</label>
                    <input type="number" id="swaparr_max_strikes" min="1" max="10" value="${settings.max_strikes || 3}">
                    <p class="setting-help">Number of strikes before removing a stalled download</p>
                </div>
                <div class="setting-item">
                    <label for="swaparr_max_download_time">Max Download Time:</label>
                    <input type="text" id="swaparr_max_download_time" value="${settings.max_download_time || '2h'}">
                    <p class="setting-help">Maximum time a download can be stalled (e.g., 30m, 2h, 1d)</p>
                </div>
                <div class="setting-item">
                    <label for="swaparr_ignore_above_size">Ignore Above Size:</label>
                    <input type="text" id="swaparr_ignore_above_size" value="${settings.ignore_above_size || '25GB'}">
                    <p class="setting-help">Ignore files larger than this size (e.g., 1GB, 25GB, 1TB)</p>
                </div>
                <div class="setting-item">
                    <label for="swaparr_remove_from_client">Remove From Client:</label>
                    <label class="toggle-switch">
                        <input type="checkbox" id="swaparr_remove_from_client" ${settings.remove_from_client !== false ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                    <p class="setting-help">Remove the download from the torrent/usenet client when removed</p>
                </div>
                <div class="setting-item">
                    <label for="swaparr_dry_run">Dry Run Mode:</label>
                    <label class="toggle-switch">
                        <input type="checkbox" id="swaparr_dry_run" ${settings.dry_run === true ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                    <p class="setting-help">Log actions but don't actually remove downloads. Useful for testing the first time!</p>
                </div>
            </div>
            
            <div class="settings-group">
                <h3>Swaparr Status</h3>
                <div id="swaparr_status_container">
                    <div class="button-container" style="display: flex; justify-content: flex-end; margin-bottom: 15px;">
                        <button type="button" id="reset_swaparr_strikes" style="background-color: #e74c3c; color: white; border: none; padding: 5px 10px; border-radius: 4px; font-size: 0.9em; cursor: pointer;">
                            <i class="fas fa-trash"></i> Reset
                        </button>
                    </div>
                    <div id="swaparr_status" class="status-display">
                        <p>Loading Swaparr status...</p>
                    </div>
                </div>
            </div>
        `;

        // Load Swaparr status automatically
        const resetStrikesBtn = container.querySelector('#reset_swaparr_strikes');
        const statusContainer = container.querySelector('#swaparr_status');
        
        fetch('/api/swaparr/status')
            .then(response => response.json())
            .then(data => {
                let statusHTML = '';
                
                // Add stats for each app if available
                if (data.statistics && Object.keys(data.statistics).length > 0) {
                    statusHTML += '<ul>';
                    
                    for (const [app, stats] of Object.entries(data.statistics)) {
                        statusHTML += `<li><strong>${app.toUpperCase()}</strong>: `;
                        if (stats.error) {
                            statusHTML += `Error: ${stats.error}</li>`;
                        } else {
                            statusHTML += `${stats.currently_striked} currently striked, ${stats.removed} removed (${stats.total_tracked} total tracked)</li>`;
                        }
                    }
                    
                    statusHTML += '</ul>';
                } else {
                    statusHTML += '<p>No statistics available yet.</p>';
                }
                
                statusContainer.innerHTML = statusHTML;
            })
            .catch(error => {
                statusContainer.innerHTML = `<p>Error fetching status: ${error.message}</p>`;
            });
            
        // Add event listener for the Reset Strikes button
        if (resetStrikesBtn) {
            resetStrikesBtn.addEventListener('click', function() {
                if (confirm('Are you sure you want to reset all Swaparr strikes? This will clear the strike history for all apps.')) {
                    statusContainer.innerHTML = '<p>Resetting strikes...</p>';
                    
                    fetch('/api/swaparr/reset', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({})
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            statusContainer.innerHTML = `<p>Success: ${data.message}</p>`;
                            // Reload status after a short delay
                            setTimeout(() => {
                                fetch('/api/swaparr/status')
                                    .then(response => response.json())
                                    .then(data => {
                                        let statusHTML = '';
                                        if (data.statistics && Object.keys(data.statistics).length > 0) {
                                            statusHTML += '<ul>';
                                            for (const [app, stats] of Object.entries(data.statistics)) {
                                                statusHTML += `<li><strong>${app.toUpperCase()}</strong>: `;
                                                if (stats.error) {
                                                    statusHTML += `Error: ${stats.error}</li>`;
                                                } else {
                                                    statusHTML += `${stats.currently_striked} currently striked, ${stats.removed} removed (${stats.total_tracked} total tracked)</li>`;
                                                }
                                            }
                                            statusHTML += '</ul>';
                                        } else {
                                            statusHTML += '<p>No statistics available yet.</p>';
                                        }
                                        statusContainer.innerHTML = statusHTML;
                                    });
                            }, 1000);
                        } else {
                            statusContainer.innerHTML = `<p>Error: ${data.message}</p>`;
                        }
                    })
                    .catch(error => {
                        statusContainer.innerHTML = `<p>Error resetting strikes: ${error.message}</p>`;
                    });
                }
            });
        }
    },
    
    // Generate General settings form
    generateGeneralForm: function(container, settings = {}) {
        container.innerHTML = `
            <div class="settings-group">
                <h3>System Settings</h3>
                <div class="setting-item">
                    <label for="check_for_updates">Check for Updates:</label>
                    <label class="toggle-switch">
                        <input type="checkbox" id="check_for_updates" ${settings.check_for_updates !== false ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                    <p class="setting-help">Automatically check for Huntarr updates</p>
                </div>
                <div class="setting-item">
                    <label for="debug_mode">Debug Mode:</label>
                    <label class="toggle-switch">
                        <input type="checkbox" id="debug_mode" ${settings.debug_mode === true ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                    <p class="setting-help">Enable verbose logging for troubleshooting (applies to all apps)</p>
                </div>
                <div class="setting-item">
                    <label for="log_refresh_interval_seconds">Log Refresh Interval:</label>
                    <input type="number" id="log_refresh_interval_seconds" min="1" value="${settings.log_refresh_interval_seconds || 30}">
                    <p class="setting-help">Interval in seconds to refresh log display (applies to all apps)</p>
                </div>
            </div>
            
            <div class="settings-group">
                <h3>Stateful Management</h3>
                <div id="stateful-section" class="setting-info-block">
                    <div id="stateful-notification" class="notification error" style="display: none;">
                        Failed to load stateful management info. Check logs for details.
                    </div>
                    <div class="info-row">
                        <span>Initial State Created:</span>
                        <span id="stateful_initial_state">Loading...</span>
                    </div>
                    <div class="info-row">
                        <span>State Reset Date:</span>
                        <span id="stateful_expires_date">Loading...</span>
                    </div>
                </div>
                <div class="setting-item">
                    <label for="stateful_management_hours">State Reset Interval (Hours):</label>
                    <input type="number" id="stateful_management_hours" min="1" value="${settings.stateful_management_hours || 168}">
                    <p class="setting-help">Hours before resetting processed media state (<span id="stateful_management_days">${((settings.stateful_management_hours || 168) / 24).toFixed(1)} days</span>)</p>
                </div>
                <div class="setting-item">
                    <button id="reset_stateful_btn" class="danger-button">Reset Stateful Management</button>
                    <p class="setting-help">Reset stateful management and clear all processed media IDs</p>
                </div>
            </div>
            
            <div class="settings-group">
                <h3>Security</h3>
                <div class="setting-item">
                    <label for="local_access_bypass">Local Network Auth Bypass:</label>
                    <label class="toggle-switch">
                        <input type="checkbox" id="local_access_bypass" ${settings.local_access_bypass === true ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                    <p class="setting-help">Allow access without login when connecting from local network IP addresses (e.g., 192.168.x.x, 10.x.x.x)</p>
                </div>
            </div>
        `;
        
        // Add listener for stateful management hours input
        const statefulHoursInput = container.querySelector('#stateful_management_hours');
        const statefulDaysSpan = container.querySelector('#stateful_management_days');
        
        if (statefulHoursInput && statefulDaysSpan) {
            statefulHoursInput.addEventListener('input', function() {
                const hours = parseInt(this.value) || 168;
                const days = (hours / 24).toFixed(1);
                statefulDaysSpan.textContent = `${days} days`;
            });
        }
        
        // Add listener for reset stateful button
        const resetStatefulBtn = container.querySelector('#reset_stateful_btn');
        if (resetStatefulBtn) {
            resetStatefulBtn.addEventListener('click', function() {
                if (confirm('Are you sure you want to reset stateful management? This will clear all processed media IDs.')) {
                    // Dispatch event for main.js to handle the reset
                    const event = new CustomEvent('resetStateful', {});
                    container.dispatchEvent(event);
                }
            });
        }
        
        // Load stateful management info
        fetch('/api/stateful/info')
            .then(response => response.json())
            .then(data => {
                const createdDateEl = document.getElementById('stateful_initial_state');
                const expiresDateEl = document.getElementById('stateful_expires_date');
                
                if (createdDateEl && data.created_date) {
                    createdDateEl.textContent = data.created_date;
                }
                
                if (expiresDateEl && data.expires_date) {
                    expiresDateEl.textContent = data.expires_date;
                }
            })
            .catch(error => {
                console.error('Error loading stateful management info:', error);
                const notificationEl = document.getElementById('stateful-notification');
                if (notificationEl) {
                    notificationEl.style.display = 'block';
                }
            });
        
        // Add confirmation dialog for local access bypass toggle
        const localAccessBypassCheckbox = container.querySelector('#local_access_bypass');
        if (localAccessBypassCheckbox) {
            // Store original state
            const originalState = localAccessBypassCheckbox.checked;
            
            localAccessBypassCheckbox.addEventListener('change', function(event) {
                const newState = this.checked;
                
                // Preview the UI changes immediately, but they'll be reverted if user doesn't save
                if (typeof huntarrUI !== 'undefined' && typeof huntarrUI.updateUIForLocalAccessBypass === 'function') {
                    huntarrUI.updateUIForLocalAccessBypass(newState);
                }
                // Also ensure the main app knows settings have changed if the preview runs
                if (typeof huntarrUI !== 'undefined' && typeof huntarrUI.markSettingsAsChanged === 'function') {
                     huntarrUI.markSettingsAsChanged();
                }
            });
        }
    },

    // Update duration display - e.g., convert seconds to hours
    updateDurationDisplay: function() {
        // Function to update a specific sleep duration display
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

        // Update for each app
        updateSleepDisplay('sleep_duration', 'sleep_duration_hours');
        updateSleepDisplay('radarr_sleep_duration', 'radarr_sleep_duration_hours');
        updateSleepDisplay('lidarr_sleep_duration', 'lidarr_sleep_duration_hours');
        updateSleepDisplay('readarr_sleep_duration', 'readarr_sleep_duration_hours');
        updateSleepDisplay('whisparr_sleep_duration', 'whisparr_sleep_duration_hours'); // Added Whisparr
    },
    
    // Setup instance management - test connection buttons and add/remove instance buttons
    setupInstanceManagement: function(container, appName, instanceCount) {
        console.log(`Setting up instance management for ${appName} with ${instanceCount} instances`);
        
        // Add listeners for test connection buttons
        const testButtons = container.querySelectorAll('.test-connection-btn');
        testButtons.forEach(button => {
            button.addEventListener('click', () => {
                const instanceId = button.getAttribute('data-instance-id');
                const urlInput = document.getElementById(`${appName}_instance_${instanceId}_api_url`);
                const keyInput = document.getElementById(`${appName}_instance_${instanceId}_api_key`);
                
                if (urlInput && keyInput) {
                    // Dispatch event for main.js to handle the API call
                    const event = new CustomEvent('testConnection', {
                        detail: {
                            appName: appName,
                            instanceId: instanceId,
                            url: urlInput.value,
                            apiKey: keyInput.value
                        }
                    });
                    container.dispatchEvent(event);
                }
            });
        });
        
        // Add listener for adding new instance
        const addButton = container.querySelector(`#add-${appName}-instance`);
        if (addButton) {
            addButton.addEventListener('click', () => {
                // Dispatch event for main.js to handle adding an instance
                const event = new CustomEvent('addInstance', {
                    detail: {
                        appName: appName
                    }
                });
                container.dispatchEvent(event);
            });
        }
        
        // Add listeners for removing instances
        const removeButtons = container.querySelectorAll('.remove-instance-btn');
        removeButtons.forEach(button => {
            button.addEventListener('click', () => {
                const instanceItem = button.closest('.instance-item');
                if (instanceItem) {
                    const instanceId = instanceItem.getAttribute('data-instance-id');
                    
                    // Dispatch event for main.js to handle removing the instance
                    const event = new CustomEvent('removeInstance', {
                        detail: {
                            appName: appName,
                            instanceId: instanceId
                        }
                    });
                    container.dispatchEvent(event);
                }
            });
        });
    }
};
