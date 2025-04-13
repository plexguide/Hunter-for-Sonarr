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
                        case 'readarr':
                            SettingsForms.generateReadarrForm(container, settings);
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

// Set up test connection buttons - remove this function or empty it
function setupTestConnectionButtons() {
    // Function emptied - no longer setting up test connection buttons
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
        
        // Now add all settings directly under the app key instead of nested
        settings.sonarr = {
            hunt_missing_shows: parseInt(document.getElementById('hunt_missing_shows')?.value || 1),
            hunt_upgrade_episodes: parseInt(document.getElementById('hunt_upgrade_episodes')?.value || 0),
            sleep_duration: parseInt(document.getElementById('sleep_duration')?.value || 900),
            state_reset_interval_hours: parseInt(document.getElementById('state_reset_interval_hours')?.value || 168),
            monitored_only: document.getElementById('monitored_only')?.checked ?? true,
            skip_future_episodes: document.getElementById('skip_future_episodes')?.checked ?? true,
            skip_series_refresh: document.getElementById('skip_series_refresh')?.checked ?? false,
            random_missing: document.getElementById('random_missing')?.checked ?? true,
            random_upgrades: document.getElementById('random_upgrades')?.checked ?? true,
            debug_mode: document.getElementById('debug_mode')?.checked ?? false,
            api_timeout: parseInt(document.getElementById('api_timeout')?.value || 60),
            command_wait_delay: parseInt(document.getElementById('command_wait_delay')?.value || 1),
            command_wait_attempts: parseInt(document.getElementById('command_wait_attempts')?.value || 600),
            minimum_download_queue_size: parseInt(document.getElementById('minimum_download_queue_size')?.value || -1)
        };
    } else if (app === 'radarr') {
        settings.api_url = document.getElementById('radarr_api_url')?.value || '';
        settings.api_key = document.getElementById('radarr_api_key')?.value || '';
        
        settings.radarr = {
            hunt_missing_movies: parseInt(document.getElementById('hunt_missing_movies')?.value || 1),
            hunt_upgrade_movies: parseInt(document.getElementById('hunt_upgrade_movies')?.value || 0),
            sleep_duration: parseInt(document.getElementById('radarr_sleep_duration')?.value || 900),
            state_reset_interval_hours: parseInt(document.getElementById('radarr_state_reset_interval_hours')?.value || 168),
            monitored_only: document.getElementById('radarr_monitored_only')?.checked ?? true,
            skip_future_releases: document.getElementById('skip_future_releases')?.checked ?? true,
            skip_movie_refresh: document.getElementById('skip_movie_refresh')?.checked ?? false,
            random_missing: document.getElementById('radarr_random_missing')?.checked ?? true,
            random_upgrades: document.getElementById('radarr_random_upgrades')?.checked ?? true,
            debug_mode: document.getElementById('radarr_debug_mode')?.checked ?? false,
            api_timeout: parseInt(document.getElementById('radarr_api_timeout')?.value || 60),
            command_wait_delay: parseInt(document.getElementById('radarr_command_wait_delay')?.value || 1),
            command_wait_attempts: parseInt(document.getElementById('radarr_command_wait_attempts')?.value || 600),
            minimum_download_queue_size: parseInt(document.getElementById('radarr_minimum_download_queue_size')?.value || -1)
        };
    } else if (app === 'lidarr') {
        settings.api_url = document.getElementById('lidarr_api_url')?.value || '';
        settings.api_key = document.getElementById('lidarr_api_key')?.value || '';
        
        settings.lidarr = {
            hunt_missing_albums: parseInt(document.getElementById('hunt_missing_albums')?.value || 1),
            hunt_upgrade_tracks: parseInt(document.getElementById('hunt_upgrade_tracks')?.value || 0),
            sleep_duration: parseInt(document.getElementById('lidarr_sleep_duration')?.value || 900),
            state_reset_interval_hours: parseInt(document.getElementById('lidarr_state_reset_interval_hours')?.value || 168),
            monitored_only: document.getElementById('lidarr_monitored_only')?.checked ?? true,
            skip_future_releases: document.getElementById('lidarr_skip_future_releases')?.checked ?? true,
            skip_artist_refresh: document.getElementById('skip_artist_refresh')?.checked ?? false,
            random_missing: document.getElementById('lidarr_random_missing')?.checked ?? true,
            random_upgrades: document.getElementById('lidarr_random_upgrades')?.checked ?? true,
            debug_mode: document.getElementById('lidarr_debug_mode')?.checked ?? false,
            api_timeout: parseInt(document.getElementById('lidarr_api_timeout')?.value || 60),
            command_wait_delay: parseInt(document.getElementById('lidarr_command_wait_delay')?.value || 1),
            command_wait_attempts: parseInt(document.getElementById('lidarr_command_wait_attempts')?.value || 600),
            minimum_download_queue_size: parseInt(document.getElementById('lidarr_minimum_download_queue_size')?.value || -1)
        };
    } else if (app === 'readarr') {
        settings.api_url = document.getElementById('readarr_api_url')?.value || '';
        settings.api_key = document.getElementById('readarr_api_key')?.value || '';
        
        settings.readarr = {
            hunt_missing_books: parseInt(document.getElementById('hunt_missing_books')?.value || 1),
            hunt_upgrade_books: parseInt(document.getElementById('hunt_upgrade_books')?.value || 0),
            sleep_duration: parseInt(document.getElementById('readarr_sleep_duration')?.value || 900),
            state_reset_interval_hours: parseInt(document.getElementById('readarr_state_reset_interval_hours')?.value || 168),
            monitored_only: document.getElementById('readarr_monitored_only')?.checked ?? true,
            skip_future_releases: document.getElementById('readarr_skip_future_releases')?.checked ?? true,
            skip_author_refresh: document.getElementById('skip_author_refresh')?.checked ?? false,
            random_missing: document.getElementById('readarr_random_missing')?.checked ?? true,
            random_upgrades: document.getElementById('readarr_random_upgrades')?.checked ?? true,
            debug_mode: document.getElementById('readarr_debug_mode')?.checked ?? false,
            api_timeout: parseInt(document.getElementById('readarr_api_timeout')?.value || 60),
            command_wait_delay: parseInt(document.getElementById('readarr_command_wait_delay')?.value || 1),
            command_wait_attempts: parseInt(document.getElementById('readarr_command_wait_attempts')?.value || 600),
            minimum_download_queue_size: parseInt(document.getElementById('readarr_minimum_download_queue_size')?.value || -1)
        };
    } else if (app === 'global') {
        settings.global = {
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
            // Show a non-blocking notification instead of an alert
            showNotification('Settings saved successfully!', 'success');
            
            // Immediately reload settings from server without waiting for user interaction
            reloadSettingsFromServer(app);
        } else {
            showNotification('Error saving settings: ' + (data.message || 'Unknown error'), 'error');
        }
    })
    .catch(error => {
        console.error('Error saving settings:', error);
        showNotification('Error saving settings: ' + error.message, 'error');
    });
}

// Helper function to reload settings from server
function reloadSettingsFromServer(app) {
    // Force a full reload of all settings from the server
    fetch('/api/settings/refresh', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(refreshResponse => refreshResponse.json())
    .then(refreshData => {
        console.log('Settings refreshed from server');
        
        // Now reload the app settings to display the current values
        loadAppSettings(app);
        
        // If we're using a module-specific loadSettings function, call that too
        if (window.huntarrApp && window.huntarrApp.currentApp === app) {
            if (app === 'sonarr' && window.huntarrApp.sonarrModule && window.huntarrApp.sonarrModule.loadSettings) {
                window.huntarrApp.sonarrModule.loadSettings();
            } else if (app === 'radarr' && window.huntarrApp.radarrModule && window.huntarrApp.radarrModule.loadSettings) {
                window.huntarrApp.radarrModule.loadSettings();
            } else if (app === 'lidarr' && window.huntarrApp.lidarrModule && window.huntarrApp.lidarrModule.loadSettings) {
                window.huntarrApp.lidarrModule.loadSettings();
            } else if (app === 'readarr' && window.huntarrApp.readarrModule && window.huntarrApp.readarrModule.loadSettings) {
                window.huntarrApp.readarrModule.loadSettings();
            }
        }
    })
    .catch(refreshError => {
        console.error('Error refreshing settings:', refreshError);
        // Still try to reload the settings
        loadAppSettings(app);
    });
}

// Show a non-blocking notification instead of using alert()
function showNotification(message, type = 'info') {
    // Create or find the notification container
    let notificationContainer = document.getElementById('notification-container');
    if (!notificationContainer) {
        notificationContainer = document.createElement('div');
        notificationContainer.id = 'notification-container';
        notificationContainer.style.position = 'fixed';
        notificationContainer.style.top = '20px';
        notificationContainer.style.right = '20px';
        notificationContainer.style.zIndex = '1000';
        document.body.appendChild(notificationContainer);
    }
    
    // Create the notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    notification.style.backgroundColor = type === 'success' ? 'rgba(46, 204, 113, 0.9)' : 
                                         type === 'error' ? 'rgba(231, 76, 60, 0.9)' : 
                                         'rgba(52, 152, 219, 0.9)';
    notification.style.color = 'white';
    notification.style.padding = '12px 20px';
    notification.style.marginBottom = '10px';
    notification.style.borderRadius = '4px';
    notification.style.boxShadow = '0 2px 10px rgba(0,0,0,0.2)';
    notification.style.display = 'block';
    notification.style.opacity = '0';
    notification.style.transition = 'opacity 0.3s ease-in-out';
    
    // Add the notification to the container
    notificationContainer.appendChild(notification);
    
    // Fade in
    setTimeout(() => {
        notification.style.opacity = '1';
    }, 10);
    
    // Remove after delay
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => {
            notification.remove();
            // Remove container if empty
            if (notificationContainer.children.length === 0) {
                notificationContainer.remove();
            }
        }, 300);
    }, 3000);
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