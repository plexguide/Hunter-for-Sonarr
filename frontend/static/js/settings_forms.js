/**
 * Settings forms for Huntarr
 * This file handles generating HTML forms for each app's settings
 */

const SettingsForms = {
    // Generate Sonarr settings form
    generateSonarrForm: function(container, settings = {}) {
        // Add data-app-type attribute to container
        container.setAttribute('data-app-type', 'sonarr');
        
        // Make sure the instances array exists
        if (!settings.instances || !Array.isArray(settings.instances) || settings.instances.length === 0) {
            settings.instances = [{
                name: "Default",
                api_url: settings.api_url || "", // Legacy support
                api_key: settings.api_key || "", // Legacy support
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
                            <button type="button" class="test-connection-btn" data-instance="${index}" style="margin-left: 10px;">
                                <i class="fas fa-plug"></i> Test Connection
                            </button>
                        </div>
                    </div>
                    <div class="instance-content">
                        <div class="setting-item">
                            <label for="sonarr-name-${index}">Name:</label>
                            <input type="text" id="sonarr-name-${index}" name="name" value="${instance.name || ''}" placeholder="Friendly name for this Sonarr instance">
                            <p class="setting-help">Friendly name for this Sonarr instance</p>
                        </div>
                        <div class="setting-item">
                            <label for="sonarr-url-${index}">URL:</label>
                            <input type="text" id="sonarr-url-${index}" name="api_url" value="${instance.api_url || ''}" placeholder="Base URL for Sonarr (e.g., http://localhost:8989)">
                            <p class="setting-help">Base URL for Sonarr (e.g., http://localhost:8989)</p>
                        </div>
                        <div class="setting-item">
                            <label for="sonarr-key-${index}">API Key:</label>
                            <input type="text" id="sonarr-key-${index}" name="api_key" value="${instance.api_key || ''}" placeholder="API key for Sonarr">
                            <p class="setting-help">API key for Sonarr</p>
                        </div>
                        <div class="setting-item">
                            <label for="sonarr-enabled-${index}">Enabled:</label>
                            <label class="toggle-switch">
                                <input type="checkbox" id="sonarr-enabled-${index}" name="enabled" ${instance.enabled !== false ? 'checked' : ''}>
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                    </div>
                </div>
            `;
        });

        instancesHtml += `
                </div> <!-- instances-container -->
                <div class="button-container" style="text-align: center; margin-top: 15px;">
                    <button type="button" class="add-instance-btn add-sonarr-instance-btn">
                        <i class="fas fa-plus"></i> Add Sonarr Instance (${settings.instances.length}/9)
                    </button>
                </div>
            </div> <!-- settings-group -->
        `;

        // Search Settings
        let searchSettingsHtml = `
            <div class="settings-group">
                <h3>Search Settings</h3>
                <div class="setting-item">
                    <label for="sonarr-hunt-missing-mode">Missing Search Mode:</label>
                    <select id="sonarr-hunt-missing-mode" name="hunt_missing_mode">
                        <option value="episodes" ${settings.hunt_missing_mode === 'episodes' ? 'selected' : ''}>Episodes</option>
                        <option value="seasons_packs" ${settings.hunt_missing_mode === 'seasons_packs' ? 'selected' : ''}>Season Packs</option>
                        <option value="shows" ${settings.hunt_missing_mode === 'shows' ? 'selected' : ''}>Shows</option>
                    </select>
                    <p class="setting-help">How to search for missing Sonarr content (Season Packs recommended for torrent users)</p>
                </div>
                <div class="setting-item">
                    <label for="sonarr-hunt-missing-items">Missing Items to Search:</label>
                    <input type="number" id="sonarr-hunt-missing-items" name="hunt_missing_items" min="0" value="${settings.hunt_missing_items !== undefined ? settings.hunt_missing_items : 1}">
                    <p class="setting-help">Number of missing items to search per cycle (0 to disable)</p>
                </div>
                <div class="setting-item">
                    <label for="sonarr-hunt-upgrade-items">Upgrade Items to Search:</label>
                    <input type="number" id="sonarr-hunt-upgrade-items" name="hunt_upgrade_items" min="0" value="${settings.hunt_upgrade_items !== undefined ? settings.hunt_upgrade_items : 0}">
                    <p class="setting-help">Number of episodes to upgrade per cycle (0 to disable)</p>
                </div>
                <div class="setting-item">
                    <label for="sonarr_sleep_duration">Sleep Duration:</label>
                    <input type="number" id="sonarr_sleep_duration" name="sleep_duration" min="60" value="${settings.sleep_duration !== undefined ? settings.sleep_duration : 900}">
                    <p class="setting-help">Time in seconds between processing cycles</p>
                </div>
            </div>
            
            <div class="settings-group">
                <h3>Additional Options</h3>
                <div class="setting-item">
                    <label for="sonarr_monitored_only">Monitored Only:</label>
                    <label class="toggle-switch">
                        <input type="checkbox" id="sonarr_monitored_only" name="monitored_only" ${settings.monitored_only !== false ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                    <p class="setting-help">Only search for monitored items</p>
                </div>
                <div class="setting-item">
                    <label for="sonarr_skip_future_episodes">Skip Future Episodes:</label>
                    <label class="toggle-switch">
                        <input type="checkbox" id="sonarr_skip_future_episodes" name="skip_future_episodes" ${settings.skip_future_episodes !== false ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                    <p class="setting-help">Skip searching for episodes with future air dates</p>
                </div>
                <div class="setting-item">
                    <label for="sonarr_skip_series_refresh">Skip Series Refresh:</label>
                    <label class="toggle-switch">
                        <input type="checkbox" id="sonarr_skip_series_refresh" name="skip_series_refresh" ${settings.skip_series_refresh === true ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                    <p class="setting-help">Skip refreshing series metadata before searching</p>
                </div>
            </div>
        `;

        // Set the content
        container.innerHTML = instancesHtml + searchSettingsHtml;

        // Setup instance management (add/remove/test)
        SettingsForms.setupInstanceManagement(container, 'sonarr', settings.instances.length);
    },
    
    // Generate Radarr settings form
    generateRadarrForm: function(container, settings = {}) {
        // Add data-app-type attribute to container
        container.setAttribute('data-app-type', 'radarr');
        
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
                            <button type="button" class="test-connection-btn" data-instance="${index}" style="margin-left: 10px;">
                                <i class="fas fa-plug"></i> Test Connection
                            </button>
                        </div>
                    </div>
                    <div class="instance-content">
                        <div class="setting-item">
                            <label for="radarr-name-${index}">Name:</label>
                            <input type="text" id="radarr-name-${index}" name="name" value="${instance.name || ''}" placeholder="Friendly name for this Radarr instance">
                            <p class="setting-help">Friendly name for this Radarr instance</p>
                        </div>
                        <div class="setting-item">
                            <label for="radarr-url-${index}">URL:</label>
                            <input type="text" id="radarr-url-${index}" name="api_url" value="${instance.api_url || ''}" placeholder="Base URL for Radarr (e.g., http://localhost:7878)">
                            <p class="setting-help">Base URL for Radarr (e.g., http://localhost:7878)</p>
                        </div>
                        <div class="setting-item">
                            <label for="radarr-key-${index}">API Key:</label>
                            <input type="text" id="radarr-key-${index}" name="api_key" value="${instance.api_key || ''}" placeholder="API key for Radarr">
                            <p class="setting-help">API key for Radarr</p>
                        </div>
                        <div class="setting-item">
                            <label for="radarr-enabled-${index}">Enabled:</label>
                            <label class="toggle-switch">
                                <input type="checkbox" id="radarr-enabled-${index}" name="enabled" ${instance.enabled !== false ? 'checked' : ''}>
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                    </div>
                </div>
            `;
        });
        
        // Add a button to add new instances (limit to 9 total)
        instancesHtml += `
                </div> <!-- instances-container -->
                <div class="button-container" style="text-align: center; margin-top: 15px;">
                    <button type="button" class="add-instance-btn add-radarr-instance-btn">
                        <i class="fas fa-plus"></i> Add Radarr Instance (${settings.instances.length}/9)
                    </button>
                </div>
            </div> <!-- settings-group -->
        `;
        
        // Continue with the rest of the settings form
        container.innerHTML = `
            ${instancesHtml}
            
            <div class="settings-group">
                <h3>Search Settings</h3>
                <div class="setting-item">
                    <label for="radarr_hunt_missing_movies">Missing Movies to Search:</label>
                    <input type="number" id="radarr_hunt_missing_movies" name="hunt_missing_movies" min="0" value="${settings.hunt_missing_movies || 1}">
                    <p class="setting-help">Number of missing movies to search per cycle (0 to disable)</p>
                </div>
                <div class="setting-item">
                    <label for="radarr_hunt_upgrade_movies">Movies to Upgrade:</label>
                    <input type="number" id="radarr_hunt_upgrade_movies" name="hunt_upgrade_movies" min="0" value="${settings.hunt_upgrade_movies || 0}">
                    <p class="setting-help">Number of movies to search for quality upgrades per cycle (0 to disable)</p>
                </div>
                <div class="setting-item">
                    <label for="radarr_sleep_duration">Sleep Duration:</label>
                    <input type="number" id="radarr_sleep_duration" name="sleep_duration" min="60" value="${settings.sleep_duration !== undefined ? settings.sleep_duration : 900}">
                    <p class="setting-help">Time in seconds between processing cycles</p>
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
        `;

        // Add event listeners for the instance management
        SettingsForms.setupInstanceManagement(container, 'radarr', settings.instances.length);
    },
    
    // Generate Lidarr settings form
    generateLidarrForm: function(container, settings = {}) {
        // Add data-app-type attribute to container
        container.setAttribute('data-app-type', 'lidarr');
        
        // Make sure the instances array exists
        if (!settings.instances || !Array.isArray(settings.instances) || settings.instances.length === 0) {
            settings.instances = [{
                name: "Default",
                api_url: settings.api_url || "", // Legacy support
                api_key: settings.api_key || "", // Legacy support
                enabled: true
            }];
        }
        
        // Create a container for instances
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
                            <button type="button" class="test-connection-btn" data-instance="${index}" style="margin-left: 10px;">
                                <i class="fas fa-plug"></i> Test Connection
                            </button>
                        </div>
                    </div>
                    <div class="instance-content">
                        <div class="setting-item">
                            <label for="lidarr-name-${index}">Name:</label>
                            <input type="text" id="lidarr-name-${index}" name="name" value="${instance.name || ''}" placeholder="Friendly name for this Lidarr instance">
                            <p class="setting-help">Friendly name for this Lidarr instance</p>
                        </div>
                        <div class="setting-item">
                            <label for="lidarr-url-${index}">URL:</label>
                            <input type="text" id="lidarr-url-${index}" name="api_url" value="${instance.api_url || ''}" placeholder="Base URL for Lidarr (e.g., http://localhost:8686)">
                            <p class="setting-help">Base URL for Lidarr (e.g., http://localhost:8686)</p>
                        </div>
                        <div class="setting-item">
                            <label for="lidarr-key-${index}">API Key:</label>
                            <input type="text" id="lidarr-key-${index}" name="api_key" value="${instance.api_key || ''}" placeholder="API key for Lidarr">
                            <p class="setting-help">API key for Lidarr</p>
                        </div>
                        <div class="setting-item">
                            <label for="lidarr-enabled-${index}">Enabled:</label>
                            <label class="toggle-switch">
                                <input type="checkbox" id="lidarr-enabled-${index}" name="enabled" ${instance.enabled !== false ? 'checked' : ''}>
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                    </div>
                </div>
            `;
        });

        instancesHtml += `
                </div> <!-- instances-container -->
                <div class="button-container" style="text-align: center; margin-top: 15px;">
                    <button type="button" class="add-instance-btn add-lidarr-instance-btn">
                        <i class="fas fa-plus"></i> Add Lidarr Instance (${settings.instances.length}/9)
                    </button>
                </div>
            </div> <!-- settings-group -->
        `;
        
        // Continue with the rest of the settings form
        container.innerHTML = `
            ${instancesHtml}
            
            <div class="settings-group">
                <h3>Search Settings</h3>
                <div class="setting-item">
                    <label for="lidarr_hunt_missing_mode">Missing Search Mode:</label>
                    <select id="lidarr_hunt_missing_mode" name="hunt_missing_mode">
                        <option value="artist" ${settings.hunt_missing_mode === 'artist' ? 'selected' : ''}>Artist</option>
                        <option value="album" ${settings.hunt_missing_mode === 'album' ? 'selected' : ''}>Album</option>
                    </select>
                    <p class="setting-help">Whether to search by artist (all missing albums for artist) or individual albums</p>
                </div>
                <div class="setting-item">
                    <label for="lidarr_hunt_missing_items">Missing Items to Search:</label>
                    <input type="number" id="lidarr_hunt_missing_items" name="hunt_missing_items" min="0" value="${settings.hunt_missing_items || 1}">
                    <p class="setting-help">Number of artists with missing albums to search per cycle (0 to disable)</p>
                </div>
                
                <div class="setting-item">
                    <label for="lidarr_hunt_upgrade_items">Items to Upgrade:</label>
                    <input type="number" id="lidarr_hunt_upgrade_items" name="hunt_upgrade_items" min="0" value="${settings.hunt_upgrade_items || 0}">
                    <p class="setting-help">Number of albums to search for quality upgrades per cycle (0 to disable)</p>
                </div>
                <div class="setting-item">
                    <label for="lidarr_sleep_duration">Sleep Duration:</label>
                    <input type="number" id="lidarr_sleep_duration" name="sleep_duration" min="60" value="${settings.sleep_duration !== undefined ? settings.sleep_duration : 900}">
                    <p class="setting-help">Time in seconds between processing cycles</p>
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
        `;

        // Add event listeners for the instance management
        SettingsForms.setupInstanceManagement(container, 'lidarr', settings.instances.length);
    },
    
    // Generate Readarr settings form
    generateReadarrForm: function(container, settings = {}) {
        // Add data-app-type attribute to container
        container.setAttribute('data-app-type', 'readarr');
        
        // Make sure the instances array exists
        if (!settings.instances || !Array.isArray(settings.instances) || settings.instances.length === 0) {
            settings.instances = [{
                name: "Default",
                api_url: settings.api_url || "", // Legacy support
                api_key: settings.api_key || "", // Legacy support
                enabled: true
            }];
        }
        
        // Create a container for instances
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
                            <button type="button" class="test-connection-btn" data-instance="${index}" style="margin-left: 10px;">
                                <i class="fas fa-plug"></i> Test Connection
                            </button>
                        </div>
                    </div>
                    <div class="instance-content">
                        <div class="setting-item">
                            <label for="readarr-name-${index}">Name:</label>
                            <input type="text" id="readarr-name-${index}" name="name" value="${instance.name || ''}" placeholder="Friendly name for this Readarr instance">
                            <p class="setting-help">Friendly name for this Readarr instance</p>
                        </div>
                        <div class="setting-item">
                            <label for="readarr-url-${index}">URL:</label>
                            <input type="text" id="readarr-url-${index}" name="api_url" value="${instance.api_url || ''}" placeholder="Base URL for Readarr (e.g., http://localhost:8787)">
                            <p class="setting-help">Base URL for Readarr (e.g., http://localhost:8787)</p>
                        </div>
                        <div class="setting-item">
                            <label for="readarr-key-${index}">API Key:</label>
                            <input type="text" id="readarr-key-${index}" name="api_key" value="${instance.api_key || ''}" placeholder="API key for Readarr">
                            <p class="setting-help">API key for Readarr</p>
                        </div>
                        <div class="setting-item">
                            <label for="readarr-enabled-${index}">Enabled:</label>
                            <label class="toggle-switch">
                                <input type="checkbox" id="readarr-enabled-${index}" name="enabled" ${instance.enabled !== false ? 'checked' : ''}>
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                    </div>
                </div>
            `;
        });

        instancesHtml += `
                </div> <!-- instances-container -->
                <div class="button-container" style="text-align: center; margin-top: 15px;">
                    <button type="button" class="add-instance-btn add-readarr-instance-btn">
                        <i class="fas fa-plus"></i> Add Readarr Instance (${settings.instances.length}/9)
                    </button>
                </div>
            </div> <!-- settings-group -->
        `;
        
        // Continue with the rest of the settings form
        container.innerHTML = `
            ${instancesHtml}
            
            <div class="settings-group">
                <h3>Search Settings</h3>
                <div class="setting-item">
                    <label for="readarr_hunt_missing_books">Missing Books to Search:</label>
                    <input type="number" id="readarr_hunt_missing_books" min="0" value="${settings.hunt_missing_books || 1}">
                    <p class="setting-help">Number of missing books to search per cycle (0 to disable)</p>
                </div>
                <div class="setting-item">
                    <label for="readarr_hunt_upgrade_books">Books to Upgrade:</label>
                    <input type="number" id="readarr_hunt_upgrade_books" min="0" value="${settings.hunt_upgrade_books || 0}">
                    <p class="setting-help">Number of books to search for quality upgrades per cycle (0 to disable)</p>
                </div>
                <div class="setting-item">
                    <label for="readarr_sleep_duration">Sleep Duration:</label>
                    <input type="number" id="readarr_sleep_duration" name="sleep_duration" min="60" value="${settings.sleep_duration !== undefined ? settings.sleep_duration : 900}">
                    <p class="setting-help">Time in seconds between processing cycles</p>
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
        `;

        // Add event listeners for the instance management
        SettingsForms.setupInstanceManagement(container, 'readarr', settings.instances.length);
    },
    
    // Generate Whisparr settings form
    generateWhisparrForm: function(container, settings = {}) {
        // Add data-app-type attribute to container
        container.setAttribute('data-app-type', 'whisparr');
        
        // Make sure the instances array exists
        if (!settings.instances || !Array.isArray(settings.instances) || settings.instances.length === 0) {
            settings.instances = [{
                name: "Default",
                api_url: settings.api_url || "", // Legacy support
                api_key: settings.api_key || "", // Legacy support
                enabled: true
            }];
        }
        
        // Create a container for instances
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
                            <button type="button" class="test-connection-btn" data-instance="${index}" style="margin-left: 10px;">
                                <i class="fas fa-plug"></i> Test Connection
                            </button>
                        </div>
                    </div>
                    <div class="instance-content">
                        <div class="setting-item">
                            <label for="whisparr-name-${index}">Name:</label>
                            <input type="text" id="whisparr-name-${index}" name="name" value="${instance.name || ''}" placeholder="Friendly name for this Whisparr instance">
                            <p class="setting-help">Friendly name for this Whisparr instance</p>
                        </div>
                        <div class="setting-item">
                            <label for="whisparr-url-${index}">URL:</label>
                            <input type="text" id="whisparr-url-${index}" name="api_url" value="${instance.api_url || ''}" placeholder="Base URL for Whisparr (e.g., http://localhost:6969)">
                            <p class="setting-help">Base URL for Whisparr (e.g., http://localhost:6969)</p>
                        </div>
                        <div class="setting-item">
                            <label for="whisparr-key-${index}">API Key:</label>
                            <input type="text" id="whisparr-key-${index}" name="api_key" value="${instance.api_key || ''}" placeholder="API key for Whisparr">
                            <p class="setting-help">API key for Whisparr</p>
                        </div>
                        <div class="setting-item">
                            <label for="whisparr-enabled-${index}">Enabled:</label>
                            <label class="toggle-switch">
                                <input type="checkbox" id="whisparr-enabled-${index}" name="enabled" ${instance.enabled !== false ? 'checked' : ''}>
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                    </div>
                </div>
            `;
        });

        instancesHtml += `
                </div> <!-- instances-container -->
                <div class="button-container" style="text-align: center; margin-top: 15px;">
                    <button type="button" class="add-instance-btn add-whisparr-instance-btn">
                        <i class="fas fa-plus"></i> Add Whisparr Instance (${settings.instances.length}/9)
                    </button>
                </div>
            </div> <!-- settings-group -->
        `;
        
        // Continue with the rest of the settings form
        container.innerHTML = `
            ${instancesHtml}
            
            <div class="settings-group">
                <h3>Search Settings</h3>
                <div class="setting-item">
                    <label for="whisparr_hunt_missing_items">Missing Items to Search:</label>
                    <input type="number" id="whisparr_hunt_missing_items" min="0" value="${settings.hunt_missing_items || settings.hunt_missing_scenes || 1}">
                    <p class="setting-help">Number of missing items to search per cycle (0 to disable)</p>
                </div>
                <div class="setting-item">
                    <label for="whisparr_hunt_upgrade_items">Items to Upgrade:</label>
                    <input type="number" id="whisparr_hunt_upgrade_items" min="0" value="${settings.hunt_upgrade_items || settings.hunt_upgrade_scenes || 0}">
                    <p class="setting-help">Number of items to search for quality upgrades per cycle (0 to disable)</p>
                </div>
                <div class="setting-item">
                    <label for="whisparr_sleep_duration">Sleep Duration:</label>
                    <input type="number" id="whisparr_sleep_duration" name="sleep_duration" min="60" value="${settings.sleep_duration !== undefined ? settings.sleep_duration : 900}">
                    <p class="setting-help">Time in seconds between processing cycles</p>
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
            </div>
        `;

        // Add event listeners for the instance management
        SettingsForms.setupInstanceManagement(container, 'whisparr', settings.instances.length);
    },
    
    // Generate Swaparr settings form
    generateSwaparrForm: function(container, settings = {}) {
        // Add data-app-type attribute to container
        container.setAttribute('data-app-type', 'swaparr');
        
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
                console.error('Error loading Swaparr status:', error);
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
        } else if (!resetStrikesBtn) {
            console.warn('Could not find #reset_swaparr_strikes to attach listener.');
        } else {
             console.warn('huntarrUI or huntarrUI.resetStatefulManagement is not available.');
        }

        // Add confirmation dialog for local access bypass toggle
        const localAccessBypassCheckbox = container.querySelector('#local_access_bypass');
        if (localAccessBypassCheckbox) {
            // Store original state
            const originalState = localAccessBypassCheckbox.checked;
            
            localAccessBypassCheckbox.addEventListener('change', function() {
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

    // Get settings from form
    getFormSettings: function(container, appType) {
        let settings = {};
        
        // Helper function to get input value with fallback
        function getInputValue(selector, defaultValue) {
            const element = container.querySelector(selector);
            if (!element) return defaultValue;
            
            if (element.type === 'checkbox') {
                return element.checked;
            } else if (element.type === 'number') {
                const parsedValue = parseInt(element.value);
                return !isNaN(parsedValue) ? parsedValue : defaultValue;
            } else {
                return element.value || defaultValue;
            }
        }
        
        // For the general settings form, collect settings including advanced settings
        if (appType === 'general') {
            settings.themeName = getInputValue('#theme-select', 'dark');
            settings.resetInterval = getInputValue('#resetInterval', 168);
            settings.clearCache = getInputValue('#clearCache', false);
            settings.refreshSchedule = getInputValue('#refreshSchedule', false);
            settings.disableSorting = getInputValue('#disableSorting', false);
            settings.disableNotifications = getInputValue('#disableNotifications', false);
            settings.openInNewTab = getInputValue('#openInNewTab', false);
            settings.saveColumnSortState = getInputValue('#saveColumnSortState', true);
            settings.disableAnimation = getInputValue('#disableAnimation', false);
            settings.useCompactLayout = getInputValue('#useCompactLayout', false);
            settings.disableAllowListPopup = getInputValue('#disableAllowListPopup', false);
            settings.maxHistoryItems = getInputValue('#maxHistoryItems', 100);
            settings.maxLogItems = getInputValue('#maxLogItems', 200);
            settings.statefulExpirationHours = getInputValue('#statefulExpirationHours', 168);
            settings.autoLoginWithoutPassword = getInputValue('#autoLoginWithoutPassword', false);
            
            // Add collection of advanced settings
            settings.api_timeout = getInputValue('#api_timeout', 120);
            settings.command_wait_delay = getInputValue('#command_wait_delay', 1);
            settings.command_wait_attempts = getInputValue('#command_wait_attempts', 600);
            settings.minimum_download_queue_size = getInputValue('#minimum_download_queue_size', -1);
            settings.log_refresh_interval_seconds = getInputValue('#log_refresh_interval_seconds', 30);
        }
        
        // For other app types, collect settings
        else {
            // Handle instances differently
            const instances = [];
            // Find instance containers with both old and new class names
            const instanceContainers = container.querySelectorAll('.instance-item, .instance-panel');
            
            // Collect instance data with improved error handling
            instanceContainers.forEach((instance, index) => {
                const nameInput = instance.querySelector('input[name="name"]');
                const urlInput = instance.querySelector('input[name="api_url"]');
                const keyInput = instance.querySelector('input[name="api_key"]');
                const enabledInput = instance.querySelector('input[name="enabled"]');
                
                const name = nameInput ? nameInput.value : null;
                const url = urlInput ? urlInput.value : null;
                const key = keyInput ? keyInput.value : null;
                const enabled = enabledInput ? enabledInput.checked : true; // Default to enabled if checkbox not found
                
                if (!name || !url || !key) {
                    console.warn(`Instance ${index} is missing required fields`);
                }
                
                const instanceObj = {
                    name: name || `Instance ${index + 1}`,
                    api_url: url || "",
                    api_key: key || "",
                    enabled: enabled
                };
                
                instances.push(instanceObj);
            });
            
            // Ensure we always have at least one instance
            if (instances.length === 0) {
                console.warn('No instances found, adding a default empty instance');
                instances.push({
                    name: 'Default',
                    api_url: '',
                    api_key: '',
                    enabled: true
                });
            }
            
            settings.instances = instances;
            
            // Add app-specific settings
            if (appType === 'sonarr') {
                settings.hunt_missing_mode = getInputValue('#sonarr-hunt-missing-mode', 'episodes');
                settings.hunt_missing_items = getInputValue('#sonarr-hunt-missing-items', 1);
                settings.hunt_upgrade_items = getInputValue('#sonarr-hunt-upgrade-items', 0);
                settings.sleep_duration = getInputValue('#sonarr_sleep_duration', 900);
                settings.monitored_only = getInputValue('#sonarr_monitored_only', true);
                settings.skip_future_episodes = getInputValue('#sonarr_skip_future_episodes', true);
                settings.skip_series_refresh = getInputValue('#sonarr_skip_series_refresh', false);
            } 
            else if (appType === 'radarr') {
                settings.hunt_missing_movies = getInputValue('#radarr_hunt_missing_movies', 1);
                settings.hunt_upgrade_movies = getInputValue('#radarr_hunt_upgrade_movies', 0);
                settings.monitored_only = getInputValue('#radarr_monitored_only', true);
                settings.skip_future_releases = getInputValue('#skip_future_releases', true);
                settings.skip_movie_refresh = getInputValue('#skip_movie_refresh', false);
                settings.sleep_duration = getInputValue('#radarr_sleep_duration', 900);
            } 
            else if (appType === 'lidarr') {
                settings.hunt_missing_items = getInputValue('#lidarr_hunt_missing_items', 1);
                settings.hunt_upgrade_items = getInputValue('#lidarr_hunt_upgrade_items', 0);
                settings.hunt_missing_mode = getInputValue('#lidarr_hunt_missing_mode', 'artist');
                settings.monitored_only = getInputValue('#lidarr_monitored_only', true);
                settings.sleep_duration = getInputValue('#lidarr_sleep_duration', 900);
            } 
            else if (appType === 'readarr') {
                settings.hunt_missing_books = getInputValue('#readarr_hunt_missing_books', 1);
                settings.hunt_upgrade_books = getInputValue('#readarr_hunt_upgrade_books', 0);
                settings.monitored_only = getInputValue('#readarr_monitored_only', true);
                settings.sleep_duration = getInputValue('#readarr_sleep_duration', 900);
            } 
            else if (appType === 'whisparr') {
                settings.hunt_missing_items = getInputValue('#whisparr_hunt_missing_items', 1);
                settings.hunt_upgrade_items = getInputValue('#whisparr_hunt_upgrade_items', 0);
                settings.monitored_only = getInputValue('#whisparr_monitored_only', true);
                settings.whisparr_version = getInputValue('#whisparr-api-version', 'v3');
                settings.skip_future_releases = getInputValue('#whisparr_skip_future_releases', true);
                settings.sleep_duration = getInputValue('#whisparr_sleep_duration', 900);
            }
        }
        
        console.log('Collected settings for', appType, settings);
        return settings;
    },
    
    // Generate General settings form
    generateGeneralForm: function(container, settings = {}) {
        // Add data-app-type attribute to container
        container.setAttribute('data-app-type', 'general');
        
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
                    <input type="number" id="log_refresh_interval_seconds" class="short-number-input" min="1" value="${settings.log_refresh_interval_seconds || 30}">
                    <p class="setting-help">Interval in seconds to refresh log display (applies to all apps)</p>
                </div>
            </div>
            
            <div class="settings-group">
                <div class="stateful-header-row">
                    <h3>Stateful Management</h3>
                    <button id="reset_stateful_btn"><i class="fas fa-trash"></i> Reset</button>
                </div>
                <div id="stateful-section" class="setting-info-block">
                    <div id="stateful-notification" class="notification error" style="display: none;">
                        Failed to load stateful management info. Check logs for details.
                    </div>
                    <div class="info-container">
                        <div class="date-info-block">
                            <div class="date-label">Initial State Created:</div>
                            <div id="stateful_initial_state" class="date-value">Loading...</div>
                        </div>
                        <div class="date-info-block">
                            <div class="date-label">State Reset Date:</div>
                            <div id="stateful_expires_date" class="date-value">Loading...</div>
                        </div>
                    </div>
                </div>
                <div class="setting-item">
                    <label for="stateful_management_hours">State Reset Interval (Hours):</label>
                    <input type="number" id="stateful_management_hours" min="1" value="${settings.stateful_management_hours || 168}">
                    <p class="setting-help">Hours before resetting processed media state (<span id="stateful_management_days">${((settings.stateful_management_hours || 168) / 24).toFixed(1)} days</span>)</p>
                    <p class="setting-help reset-help">Reset clears all processed media IDs to allow reprocessing</p>
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
            
            <div class="settings-group">
                <h3>Advanced Settings</h3>
                <div class="setting-item">
                    <label for="api_timeout">API Timeout:</label>
                    <input type="number" id="api_timeout" min="10" value="${settings.api_timeout !== undefined ? settings.api_timeout : 120}">
                    <p class="setting-help">API request timeout in seconds</p>
                </div>
                <div class="setting-item">
                    <label for="command_wait_delay">Command Wait Delay:</label>
                    <input type="number" id="command_wait_delay" min="1" value="${settings.command_wait_delay !== undefined ? settings.command_wait_delay : 1}">
                    <p class="setting-help">Delay between command status checks in seconds</p>
                </div>
                <div class="setting-item">
                    <label for="command_wait_attempts">Command Wait Attempts:</label>
                    <input type="number" id="command_wait_attempts" min="1" value="${settings.command_wait_attempts !== undefined ? settings.command_wait_attempts : 600}">
                    <p class="setting-help">Maximum number of attempts to check command status</p>
                </div>
                <div class="setting-item">
                    <label for="minimum_download_queue_size">Minimum Download Queue Size:</label>
                    <input type="number" id="minimum_download_queue_size" min="-1" value="${settings.minimum_download_queue_size !== undefined ? settings.minimum_download_queue_size : -1}">
                    <p class="setting-help">Minimum size of download queue before processing (-1 to disable)</p>
                </div>
                <div class="setting-item">
                    <label for="log_refresh_interval_seconds">Log Refresh Interval:</label>
                    <input type="number" id="log_refresh_interval_seconds" min="5" value="${settings.log_refresh_interval_seconds !== undefined ? settings.log_refresh_interval_seconds : 30}">
                    <p class="setting-help">How often Huntarr refreshes logs from apps (seconds)</p>
                </div>
            </div>
        `;
        
        // Add listener for stateful management hours input
        const statefulHoursInput = container.querySelector('#stateful_management_hours');
        const statefulDaysSpan = container.querySelector('#stateful_management_days');
        
        if (statefulHoursInput && statefulDaysSpan) {
            statefulHoursInput.addEventListener('input', function() {
                const hours = parseInt(this.value);
                const days = (hours / 24).toFixed(1);
                statefulDaysSpan.textContent = `${days} days`;
            });
        }
        
        // Load stateful management info
        const createdDateEl = document.getElementById('stateful_initial_state');
        const expiresDateEl = document.getElementById('stateful_expires_date');

        // Set initial state to Loading...
        if (createdDateEl) createdDateEl.textContent = 'Loading...';
        if (expiresDateEl) expiresDateEl.textContent = 'Loading...';

        fetch('/api/stateful/info')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
             })
            .then(data => {
                if (createdDateEl && data.created_date) {
                    createdDateEl.textContent = data.created_date;
                } else if (createdDateEl) {
                    createdDateEl.textContent = 'N/A'; // Handle missing data
                }
                
                if (expiresDateEl && data.expires_date) {
                    expiresDateEl.textContent = data.expires_date;
                } else if (expiresDateEl) {
                    expiresDateEl.textContent = 'N/A'; // Handle missing data
                }
            })
            .catch(error => {
                console.error('Error loading stateful management info:', error);
                if (createdDateEl) createdDateEl.textContent = 'Error loading';
                if (expiresDateEl) expiresDateEl.textContent = 'Error loading';
                // const notificationEl = document.getElementById('stateful-notification');
                // if (notificationEl) {
                //     notificationEl.style.display = 'block';
                // }
            });
        
        // Add listener for reset stateful button
        const resetStatefulBtn = container.querySelector('#reset_stateful_btn');
        if (resetStatefulBtn && typeof huntarrUI !== 'undefined' && typeof huntarrUI.resetStatefulManagement === 'function') {
            resetStatefulBtn.addEventListener('click', function() {
                if (confirm('Are you sure you want to reset stateful management? This will clear all processed media IDs.')) {
                    huntarrUI.resetStatefulManagement();
                }
            });
        } else if (!resetStatefulBtn) {
            console.warn('Could not find #reset_stateful_btn to attach listener.');
        } else {
             console.warn('huntarrUI or huntarrUI.resetStatefulManagement is not available.');
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
    setupInstanceManagement: function(container, appType, initialCount) {
        console.log(`Setting up instance management for ${appType} with ${initialCount} instances`);
        
        // Make sure container has the app type set
        const form = container.closest('.settings-form');
        if (form && !form.hasAttribute('data-app-type')) {
            form.setAttribute('data-app-type', appType);
        }
        
        // Add listeners for test connection buttons
        const testButtons = container.querySelectorAll('.test-connection-btn');
        testButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                // Prevent any default form submission
                e.preventDefault();
                
                console.log('Test connection button clicked');
                
                // Get the instance panel containing this button - look for both old and new class names
                const instancePanel = button.closest('.instance-item') || button.closest('.instance-panel');
                if (!instancePanel) {
                    console.error('Could not find instance panel for test button', button);
                    alert('Error: Could not find instance panel');
                    return;
                }
                
                // Get the URL and API key inputs directly within this instance panel
                const urlInput = instancePanel.querySelector('input[name="api_url"]');
                const keyInput = instancePanel.querySelector('input[name="api_key"]');
                
                console.log('Found inputs:', urlInput, keyInput);
                
                if (!urlInput || !keyInput) {
                    console.error('Could not find URL or API key inputs in panel', instancePanel);
                    alert('Error: Could not find URL or API key inputs');
                    return;
                }
                
                const url = urlInput.value.trim();
                const apiKey = keyInput.value.trim();
                
                console.log(`Testing connection for ${appType} - URL: ${url}, API Key: ${apiKey.substring(0, 5)}...`);
                
                if (!url) {
                    alert('Please enter a valid URL');
                    urlInput.focus();
                    return;
                }
                
                if (!apiKey) {
                    alert('Please enter a valid API key');
                    keyInput.focus();
                    return;
                }
                
                // Show testing status
                const originalButtonHTML = button.innerHTML;
                button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing...';
                button.disabled = true;
                
                // Make the API request
                fetch(`/api/${appType}/test-connection`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        api_url: url,
                        api_key: apiKey
                    })
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error ${response.status}: ${response.statusText}`);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log(`Test connection response:`, data);
                    
                    // Reset button
                    button.disabled = false;
                    
                    if (data.success) {
                        // Success
                        button.innerHTML = '<i class="fas fa-check"></i> Connected!';
                        button.classList.add('test-success');
                        
                        let successMessage = `Successfully connected to ${appType.charAt(0).toUpperCase() + appType.slice(1)}`;
                        if (data.version) {
                            successMessage += ` (version ${data.version})`;
                        }
                        
                        // Alert the user of success
                        alert(successMessage);
                        
                        // Reset button after delay
                        setTimeout(() => {
                            button.innerHTML = originalButtonHTML;
                            button.classList.remove('test-success');
                        }, 3000);
                    } else {
                        // Failure
                        button.innerHTML = '<i class="fas fa-times"></i> Failed';
                        button.classList.add('test-failed');
                        
                        alert(`Connection failed: ${data.message || 'Unknown error'}`);
                        
                        setTimeout(() => {
                            button.innerHTML = originalButtonHTML;
                            button.classList.remove('test-failed');
                        }, 3000);
                    }
                })
                .catch(error => {
                    console.error(`Test connection error:`, error);
                    
                    button.disabled = false;
                    button.innerHTML = '<i class="fas fa-times"></i> Error';
                    button.classList.add('test-failed');
                    
                    alert(`Connection test failed: ${error.message}`);
                    
                    setTimeout(() => {
                        button.innerHTML = originalButtonHTML;
                        button.classList.remove('test-failed');
                    }, 3000);
                });
            });
        });
        
        // Add a button to add new instances (limit to 9 total)
        const addBtn = container.querySelector(`.add-${appType}-instance-btn`);
        if (addBtn) {
            // Function to update the button text with current instance count
            const updateAddButtonText = () => {
                const instancesContainer = container.querySelector('.instances-container');
                if (!instancesContainer) return;
                const currentCount = instancesContainer.querySelectorAll('.instance-item').length;
                addBtn.innerHTML = `<i class="fas fa-plus"></i> Add ${appType.charAt(0).toUpperCase() + appType.slice(1)} Instance (${currentCount}/9)`;
                
                // Disable button if we've reached the maximum
                if (currentCount >= 9) {
                    addBtn.disabled = true;
                    addBtn.title = "Maximum number of instances reached";
                } else {
                    addBtn.disabled = false;
                    addBtn.title = "";
                }
            };
            
            // Initialize button text
            updateAddButtonText();
            
            addBtn.addEventListener('click', function() {
                const instancesContainer = container.querySelector('.instances-container');
                if (!instancesContainer) return;
                
                // Count current instances
                const currentCount = instancesContainer.querySelectorAll('.instance-item').length;
                
                // Don't add more if we have 9 already
                if (currentCount >= 9) {
                    alert("Maximum of 9 instances allowed");
                    return;
                }
                
                // Create new instance div
                const newInstanceDiv = document.createElement('div');
                newInstanceDiv.className = 'instance-item'; // Use instance-item
                newInstanceDiv.dataset.instanceId = currentCount;
                
                // Set content for the new instance using the updated structure
                newInstanceDiv.innerHTML = `
                    <div class="instance-header">
                        <h4>Instance ${currentCount + 1}: Instance ${currentCount + 1}</h4>
                        <div class="instance-actions">
                             <button type="button" class="remove-instance-btn">Remove</button>
                             <button type="button" class="test-connection-btn" data-instance="${currentCount}" style="margin-left: 10px;">
                                <i class="fas fa-plug"></i> Test Connection
                            </button>
                        </div>
                    </div>
                    <div class="instance-content">
                        <div class="setting-item">
                            <label for="${appType}-name-${currentCount}">Name:</label>
                            <input type="text" id="${appType}-name-${currentCount}" name="name" value="Instance ${currentCount + 1}" placeholder="Friendly name for this instance">
                            <p class="setting-help">Friendly name for this ${appType} instance</p>
                        </div>
                        <div class="setting-item">
                            <label for="${appType}-url-${currentCount}">URL:</label>
                            <input type="text" id="${appType}-url-${currentCount}" name="api_url" value="" placeholder="Base URL (e.g., http://localhost:8989)">
                             <p class="setting-help">Base URL for ${appType} (e.g., http://localhost:8989)</p>
                        </div>
                        <div class="setting-item">
                            <label for="${appType}-key-${currentCount}">API Key:</label>
                            <input type="text" id="${appType}-key-${currentCount}" name="api_key" value="" placeholder="API key">
                             <p class="setting-help">API key for ${appType}</p>
                        </div>
                        <div class="setting-item">
                            <label for="${appType}-enabled-${currentCount}">Enabled:</label>
                            <label class="toggle-switch">
                                <input type="checkbox" id="${appType}-enabled-${currentCount}" name="enabled" checked>
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                    </div>
                `;
                
                // Add the new instance to the container
                instancesContainer.appendChild(newInstanceDiv);
                
                // Update the button text with new count
                updateAddButtonText();
                
                // Add event listener for the remove button
                const removeBtn = newInstanceDiv.querySelector('.remove-instance-btn');
                if (removeBtn) {
                    removeBtn.addEventListener('click', function() {
                        instancesContainer.removeChild(newInstanceDiv);
                        
                        // Update the add button text after removing
                        updateAddButtonText();
                        
                        // Trigger change event to update save button state
                        const changeEvent = new Event('change');
                        container.dispatchEvent(changeEvent);
                    });
                }
                
                // Add event listener for test connection button
                const testBtn = newInstanceDiv.querySelector('.test-connection-btn');
                if (testBtn) {
                    testBtn.addEventListener('click', function() {
                        // Get the URL and API key inputs from the parent instance item
                        const instanceContainer = testBtn.closest('.instance-item') || testBtn.closest('.instance-panel');
                        if (!instanceContainer) {
                            alert('Error: Could not find instance container');
                            return;
                        }
                        
                        const urlInput = instanceContainer.querySelector('input[name="api_url"]');
                        const keyInput = instanceContainer.querySelector('input[name="api_key"]');
                        
                        if (!urlInput || !keyInput) {
                            alert('Error: Could not find URL or API key inputs');
                            return;
                        }
                        
                        const url = urlInput.value.trim();
                        const apiKey = keyInput.value.trim();
                        
                        if (!url) {
                            alert('Please enter a valid URL');
                            urlInput.focus();
                            return;
                        }
                        
                        if (!apiKey) {
                            alert('Please enter a valid API key');
                            keyInput.focus();
                            return;
                        }
                        
                        // Call the test connection function
                        SettingsForms.testConnection(appType, url, apiKey, testBtn);
                    });
                }
                
                // Trigger change event to update save button state
                const changeEvent = new Event('change');
                container.dispatchEvent(changeEvent);
            });
        }
        
        // Set up remove buttons for existing instances
        const removeButtons = container.querySelectorAll('.remove-instance-btn');
        removeButtons.forEach(btn => {
            btn.addEventListener('click', function() {
                const instancePanel = btn.closest('.instance-item') || btn.closest('.instance-panel');
                if (instancePanel && instancePanel.parentNode) {
                    instancePanel.parentNode.removeChild(instancePanel);
                    
                    // Update the button text with new count if updateAddButtonText exists
                    if (typeof updateAddButtonText === 'function') {
                        updateAddButtonText();
                    }
                    
                    // Trigger change event to update save button state
                    const changeEvent = new Event('change');
                    container.dispatchEvent(changeEvent);
                }
            });
        });
    },
    
    // Test connection to an *arr API
    testConnection: function(app, url, apiKey, buttonElement) {
        // Show testing indicator on button
        const originalButtonText = buttonElement.innerHTML;
        buttonElement.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing...';
        buttonElement.disabled = true;
        
        console.log(`Testing connection for ${app} - URL: ${url}, API Key: ${apiKey.substring(0, 5)}...`);
        
        if (!url) {
            alert('Please enter a valid URL');
            urlInput.focus();
            return;
        }
        
        if (!apiKey) {
            alert('Please enter a valid API key');
            keyInput.focus();
            return;
        }
        
        // Show testing status
        const originalButtonHTML = buttonElement.innerHTML;
        buttonElement.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing...';
        buttonElement.disabled = true;
        
        // Make the API request
        fetch(`/api/${app}/test-connection`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                api_url: url,
                api_key: apiKey
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log(`Test connection response:`, data);
            
            // Reset button
            buttonElement.disabled = false;
            
            if (data.success) {
                // Success
                buttonElement.innerHTML = '<i class="fas fa-check"></i> Connected!';
                buttonElement.classList.add('test-success');
                
                let successMessage = `Successfully connected to ${app.charAt(0).toUpperCase() + app.slice(1)}`;
                if (data.version) {
                    successMessage += ` (version ${data.version})`;
                }
                
                // Alert the user of success
                alert(successMessage);
                
                // Reset button after delay
                setTimeout(() => {
                    buttonElement.innerHTML = originalButtonHTML;
                    buttonElement.classList.remove('test-success');
                }, 3000);
            } else {
                // Failure
                buttonElement.innerHTML = '<i class="fas fa-times"></i> Failed';
                buttonElement.classList.add('test-failed');
                
                alert(`Connection failed: ${data.message || 'Unknown error'}`);
                
                setTimeout(() => {
                    buttonElement.innerHTML = originalButtonHTML;
                    buttonElement.classList.remove('test-failed');
                }, 3000);
            }
        })
        .catch(error => {
            console.error(`Test connection error:`, error);
            
            buttonElement.disabled = false;
            buttonElement.innerHTML = '<i class="fas fa-times"></i> Error';
            buttonElement.classList.add('test-failed');
            
            alert(`Connection test failed: ${error.message}`);
            
            setTimeout(() => {
                buttonElement.innerHTML = originalButtonHTML;
                buttonElement.classList.remove('test-failed');
            }, 3000);
        });
    },
};
