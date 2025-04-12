/**
 * Settings loader for Huntarr
 * This file handles loading settings for each app tab
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize settings on page load
    initializeSettings();
    
    // Set up tab switching
    setupTabSwitching();
    
    // Set up save and reset buttons
    setupSettingsButtons();
});

// Initialize settings
function initializeSettings() {
    // Load settings for all apps
    loadAppSettings('sonarr');
    loadAppSettings('radarr');
    loadAppSettings('lidarr');
    loadAppSettings('global');
}

// Load settings for a specific app
function loadAppSettings(app) {
    fetch(`/api/settings`)
        .then(response => response.json())
        .then(allSettings => {
            // Get app-specific API settings if needed
            fetch(`/api/app-settings?app=${app}`)
                .then(response => response.json())
                .then(apiData => {
                    // Merge the API credentials with the general settings
                    const settings = allSettings;
                    if (apiData && apiData.success) {
                        settings.api_url = apiData.api_url;
                        settings.api_key = apiData.api_key;
                    }
                    
                    // Find the container for this app's settings
                    const container = document.getElementById(`${app}Settings`);
                    if (!container) return;
                    
                    // Generate the form based on the app type
                    switch(app) {
                        case 'sonarr':
                            SettingsForms.generateSonarrForm(container, settings);
                            break;
                        case 'radarr':
                            SettingsForms.generateRadarrForm(container, settings);
                            break;
                        case 'lidarr':
                            SettingsForms.generateLidarrForm(container, settings);
                            break;
                        case 'global':
                            SettingsForms.generateGlobalForm(container, settings);
                            break;
                    }
                    
                    // Update any dynamic displays
                    SettingsForms.updateDurationDisplay();
                    
                    // Set up test connection buttons
                    setupTestConnectionButtons();
                    
                    console.log(`${app} settings loaded successfully`);
                })
                .catch(error => {
                    console.error(`Error loading API settings for ${app}:`, error);
                });
        })
        .catch(error => {
            console.error(`Error loading settings for ${app}:`, error);
        });
}

// Set up tab switching
function setupTabSwitching() {
    const settingsTabs = document.querySelectorAll('.settings-tab');
    settingsTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const app = this.getAttribute('data-settings');
            
            // Update active tab
            settingsTabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            
            // Show selected settings panel
            const panels = document.querySelectorAll('.app-settings-panel');
            panels.forEach(panel => panel.classList.remove('active'));
            
            const selectedPanel = document.getElementById(`${app}Settings`);
            if (selectedPanel) {
                selectedPanel.classList.add('active');
            }
        });
    });
}

// Set up test connection buttons
function setupTestConnectionButtons() {
    // Sonarr connection test
    const sonarrTestBtn = document.getElementById('testSonarrConnection');
    if (sonarrTestBtn) {
        sonarrTestBtn.addEventListener('click', function() {
            testConnection('sonarr');
        });
    }
    
    // Radarr connection test
    const radarrTestBtn = document.getElementById('testRadarrConnection');
    if (radarrTestBtn) {
        radarrTestBtn.addEventListener('click', function() {
            testConnection('radarr');
        });
    }
    
    // Lidarr connection test
    const lidarrTestBtn = document.getElementById('testLidarrConnection');
    if (lidarrTestBtn) {
        lidarrTestBtn.addEventListener('click', function() {
            testConnection('lidarr');
        });
    }
}

// Test connection function
function testConnection(app) {
    const apiUrlElem = document.getElementById(`${app}_api_url`);
    const apiKeyElem = document.getElementById(`${app}_api_key`);
    const statusElem = document.getElementById(`${app}ConnectionStatus`);
    
    if (!apiUrlElem || !apiKeyElem || !statusElem) {
        console.error(`Missing elements for ${app} connection test`);
        return;
    }
    
    const apiUrl = apiUrlElem.value;
    const apiKey = apiKeyElem.value;
    
    if (!apiUrl || !apiKey) {
        alert(`Please enter both URL and API Key for ${app.charAt(0).toUpperCase() + app.slice(1)}`);
        return;
    }
    
    statusElem.textContent = 'Testing...';
    statusElem.className = 'connection-badge testing';
    
    fetch(`/api/${app}/test-connection`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            api_url: apiUrl,
            api_key: apiKey
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            statusElem.textContent = 'Connected';
            statusElem.className = 'connection-badge connected';
        } else {
            statusElem.textContent = data.message || 'Connection Failed';
            statusElem.className = 'connection-badge not-connected';
        }
    })
    .catch(error => {
        console.error(`Error testing ${app} connection:`, error);
        statusElem.textContent = 'Error';
        statusElem.className = 'connection-badge not-connected';
    });
}

// Set up save and reset buttons
function setupSettingsButtons() {
    // Save settings button
    const saveBtn = document.getElementById('saveSettingsButton');
    if (saveBtn) {
        saveBtn.addEventListener('click', function() {
            saveCurrentSettings();
        });
    }
    
    // Reset settings button
    const resetBtn = document.getElementById('resetSettingsButton');
    if (resetBtn) {
        resetBtn.addEventListener('click', function() {
            resetCurrentSettings();
        });
    }
}

// Save current settings
function saveCurrentSettings() {
    const activeTab = document.querySelector('.settings-tab.active');
    if (!activeTab) return;
    
    const app = activeTab.getAttribute('data-settings');
    let settings = {
        app_type: app
    };
    
    // Collect settings based on app type
    if (app === 'sonarr') {
        settings.api_url = document.getElementById('sonarr_api_url')?.value || '';
        settings.api_key = document.getElementById('sonarr_api_key')?.value || '';
        settings.huntarr = {
            hunt_missing_shows: parseInt(document.getElementById('hunt_missing_shows')?.value || 1),
            hunt_upgrade_episodes: parseInt(document.getElementById('hunt_upgrade_episodes')?.value || 0),
            sleep_duration: parseInt(document.getElementById('sleep_duration')?.value || 900),
            state_reset_interval_hours: parseInt(document.getElementById('state_reset_interval_hours')?.value || 168),
            monitored_only: document.getElementById('monitored_only')?.checked ?? true,
            skip_future_episodes: document.getElementById('skip_future_episodes')?.checked ?? true,
            skip_series_refresh: document.getElementById('skip_series_refresh')?.checked ?? false
        };
        settings.advanced = {
            random_missing: document.getElementById('random_missing')?.checked ?? true,
            random_upgrades: document.getElementById('random_upgrades')?.checked ?? true
        };
    } else if (app === 'radarr') {
        settings.api_url = document.getElementById('radarr_api_url')?.value || '';
        settings.api_key = document.getElementById('radarr_api_key')?.value || '';
        settings.huntarr = {
            hunt_missing_movies: parseInt(document.getElementById('hunt_missing_movies')?.value || 1),
            hunt_upgrade_movies: parseInt(document.getElementById('hunt_upgrade_movies')?.value || 0),
            sleep_duration: parseInt(document.getElementById('radarr_sleep_duration')?.value || 900),
            state_reset_interval_hours: parseInt(document.getElementById('radarr_state_reset_interval_hours')?.value || 168),
            monitored_only: document.getElementById('radarr_monitored_only')?.checked ?? true,
            skip_future_releases: document.getElementById('skip_future_releases')?.checked ?? true,
            skip_movie_refresh: document.getElementById('skip_movie_refresh')?.checked ?? false
        };
        settings.advanced = {
            random_missing: document.getElementById('radarr_random_missing')?.checked ?? true,
            random_upgrades: document.getElementById('radarr_random_upgrades')?.checked ?? true
        };
    } else if (app === 'lidarr') {
        settings.api_url = document.getElementById('lidarr_api_url')?.value || '';
        settings.api_key = document.getElementById('lidarr_api_key')?.value || '';
        settings.huntarr = {
            hunt_missing_albums: parseInt(document.getElementById('hunt_missing_albums')?.value || 1),
            hunt_upgrade_tracks: parseInt(document.getElementById('hunt_upgrade_tracks')?.value || 0),
            sleep_duration: parseInt(document.getElementById('lidarr_sleep_duration')?.value || 900),
            state_reset_interval_hours: parseInt(document.getElementById('lidarr_state_reset_interval_hours')?.value || 168),
            monitored_only: document.getElementById('lidarr_monitored_only')?.checked ?? true,
            skip_future_releases: document.getElementById('lidarr_skip_future_releases')?.checked ?? true,
            skip_artist_refresh: document.getElementById('skip_artist_refresh')?.checked ?? false
        };
        settings.advanced = {
            random_missing: document.getElementById('lidarr_random_missing')?.checked ?? true,
            random_upgrades: document.getElementById('lidarr_random_upgrades')?.checked ?? true
        };
    } else if (app === 'global') {
        settings.advanced = {
            debug_mode: document.getElementById('debug_mode')?.checked ?? false,
            command_wait_delay: parseInt(document.getElementById('command_wait_delay')?.value || 1),
            command_wait_attempts: parseInt(document.getElementById('command_wait_attempts')?.value || 600),
            minimum_download_queue_size: parseInt(document.getElementById('minimum_download_queue_size')?.value || -1)
        };
    }
    
    // Save settings via API
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
            alert('Settings saved successfully!');
            
            // Reload settings to reflect any changes from the server
            loadAppSettings(app);
        } else {
            alert('Error saving settings: ' + (data.message || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error saving settings:', error);
        alert('Error saving settings: ' + error.message);
    });
}

// Reset current settings to defaults
function resetCurrentSettings() {
    const activeTab = document.querySelector('.settings-tab.active');
    if (!activeTab) return;
    
    const app = activeTab.getAttribute('data-settings');
    
    if (confirm(`Are you sure you want to reset ${app} settings to defaults?`)) {
        fetch('/api/settings/reset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ app: app })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Settings reset to defaults.');
                // Reload settings to reflect the reset
                loadAppSettings(app);
            } else {
                alert('Error resetting settings: ' + (data.message || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Error resetting settings:', error);
            alert('Error resetting settings: ' + error.message);
        });
    }
}