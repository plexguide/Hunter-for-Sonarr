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
                <h3>Whisparr Instances <span style="color: red; font-weight: bold;">(NOT READY)</span></h3>
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
                <h3>Search Settings</h3>
                <div class="setting-item">
                    <label for="hunt_missing_scenes">Missing Scenes to Search:</label>
                    <input type="number" id="hunt_missing_scenes" min="0" value="${settings.hunt_missing_scenes || 1}">
                    <p class="setting-help">Number of missing scenes to search per cycle (0 to disable)</p>
                </div>
                <div class="setting-item">
                    <label for="hunt_upgrade_scenes">Scenes to Upgrade:</label>
                    <input type="number" id="hunt_upgrade_scenes" min="0" value="${settings.hunt_upgrade_scenes || 0}">
                    <p class="setting-help">Number of scenes to search for quality upgrades per cycle (0 to disable)</p>
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
