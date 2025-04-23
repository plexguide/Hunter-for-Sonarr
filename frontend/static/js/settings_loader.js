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
            // Extract the app-specific settings
            let settings = {};
            
            // Get general settings
            if (app === 'global') {
                settings = allSettings.global || {};
                if (allSettings.ui) {
                    settings.ui = allSettings.ui;
                }
            } else {
                // Extract app-specific settings
                settings = allSettings[app] || {};
            }
            
            // Get app-specific API settings if needed
            fetch(`/api/app-settings?app=${app}`)
                .then(response => response.json())
                .then(apiData => {
                    // Merge the API credentials with the settings
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
                    
                    console.log(`${app} settings loaded successfully`, settings);
                })
                .catch(error => {
                    console.error(`Error loading API settings for ${app}:`, error);
                    
                    // If API settings fetch fails, still try to load the form with what we have
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
                });
        })
        .catch(error => {
            console.error(`Error loading settings for ${app}:`, error);
            
            // If the settings fetch fails entirely, try to load with default empty settings
            const container = document.getElementById(`${app}Settings`);
            if (!container) return;
            
            // Generate the form with default values
            switch(app) {
                case 'sonarr':
                    SettingsForms.generateSonarrForm(container, getDefaultSettings('sonarr'));
                    break;
                case 'radarr':
                    SettingsForms.generateRadarrForm(container, getDefaultSettings('radarr'));
                    break;
                case 'lidarr':
                    SettingsForms.generateLidarrForm(container, getDefaultSettings('lidarr'));
                    break;
                case 'readarr':
                    SettingsForms.generateReadarrForm(container, getDefaultSettings('readarr'));
                    break;
                case 'global':
                    SettingsForms.generateGlobalForm(container, getDefaultSettings('global'));
                    break;
            }
            
            // Update any dynamic displays
            SettingsForms.updateDurationDisplay();
        });
}

// Helper function to get default settings for any app
function getDefaultSettings(app) {
    switch (app) {
        case 'sonarr':
            return {
                api_url: '',
                api_key: '',
                hunt_missing_shows: 1,
                hunt_upgrade_episodes: 0,
                sleep_duration: 900,
                state_reset_interval_hours: 168,
                monitored_only: true,
                skip_future_episodes: true,
                skip_series_refresh: false,
                random_missing: true,
                random_upgrades: true,
                debug_mode: false,
                api_timeout: 60,
                command_wait_delay: 1,
                command_wait_attempts: 600,
                minimum_download_queue_size: -1,
                log_refresh_interval_seconds: 30
            };
        case 'radarr':
            return {
                api_url: '',
                api_key: '',
                hunt_missing_movies: 1,
                hunt_upgrade_movies: 0,
                sleep_duration: 900,
                state_reset_interval_hours: 168,
                monitored_only: true,
                skip_future_releases: true,
                skip_movie_refresh: false,
                random_missing: true,
                random_upgrades: true,
                debug_mode: false,
                api_timeout: 60,
                command_wait_delay: 1,
                command_wait_attempts: 600,
                minimum_download_queue_size: -1,
                log_refresh_interval_seconds: 30
            };
        case 'lidarr':
            return {
                api_url: '',
                api_key: '',
                hunt_missing_albums: 1,
                hunt_upgrade_tracks: 0,
                sleep_duration: 900,
                state_reset_interval_hours: 168,
                monitored_only: true,
                skip_future_releases: true,
                skip_artist_refresh: false,
                random_missing: true,
                random_upgrades: true,
                debug_mode: false,
                api_timeout: 60,
                command_wait_delay: 1,
                command_wait_attempts: 600,
                minimum_download_queue_size: -1,
                log_refresh_interval_seconds: 30
            };
        case 'readarr':
            return {
                api_url: '',
                api_key: '',
                hunt_missing_books: 1,
                hunt_upgrade_books: 0,
                sleep_duration: 900,
                state_reset_interval_hours: 168,
                monitored_only: true,
                skip_future_releases: true,
                skip_author_refresh: false,
                random_missing: true,
                random_upgrades: true,
                debug_mode: false,
                api_timeout: 60,
                command_wait_delay: 1,
                command_wait_attempts: 600,
                minimum_download_queue_size: -1,
                log_refresh_interval_seconds: 30
            };
        default:
            // Return a generic structure or handle unknown apps
            console.warn(`Requesting default settings for unknown app: ${app}`);
            return {
                api_url: '',
                api_key: '',
                // Add other common fields if applicable, or leave empty
            };
    }
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