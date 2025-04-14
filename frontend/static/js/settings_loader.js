/**
 * Settings loader for Huntarr Sonarr
 * This file handles loading Sonarr settings
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize settings on page load
    initializeSettings();
    
    // Set up save and reset buttons
    setupSettingsButtons();
});

// Initialize settings
function initializeSettings() {
    // Load Sonarr settings
    loadSonarrSettings();
}

// Load Sonarr settings
function loadSonarrSettings() {
    fetch(`/api/settings`)
        .then(response => response.json())
        .then(allSettings => {
            // Extract the Sonarr-specific settings
            let settings = allSettings.sonarr || {};
            
            // Get Sonarr API settings
            fetch(`/api/app-settings`)
                .then(response => response.json())
                .then(apiData => {
                    // Merge the API credentials with the settings
                    if (apiData && apiData.success) {
                        settings.api_url = apiData.api_url;
                        settings.api_key = apiData.api_key;
                    }
                    
                    // Find the container for Sonarr settings
                    const container = document.getElementById('sonarrSettings');
                    if (!container) return;
                    
                    // Generate the Sonarr settings form
                    SettingsForms.generateSonarrForm(container, settings);
                    
                    // Update any dynamic displays
                    SettingsForms.updateDurationDisplay();
                    
                    console.log('Sonarr settings loaded successfully', settings);
                })
                .catch(error => {
                    console.error('Error loading API settings for Sonarr:', error);
                    
                    // If API settings fetch fails, still try to load the form with what we have
                    const container = document.getElementById('sonarrSettings');
                    if (!container) return;
                    
                    // Generate the form with what we have
                    SettingsForms.generateSonarrForm(container, settings);
                    
                    // Update any dynamic displays
                    SettingsForms.updateDurationDisplay();
                });
        })
        .catch(error => {
            console.error('Error loading settings for Sonarr:', error);
            
            // If the settings fetch fails entirely, try to load with default empty settings
            const container = document.getElementById('sonarrSettings');
            if (!container) return;
            
            // Generate the form with default values
            SettingsForms.generateSonarrForm(container, getDefaultSettings());
            
            // Update any dynamic displays
            SettingsForms.updateDurationDisplay();
        });
}

// Helper function to get default Sonarr settings
function getDefaultSettings() {
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
}

// Set up save and reset buttons
function setupSettingsButtons() {
    // Save settings buttons
    const saveButtons = document.querySelectorAll('#saveSettings, #saveSettingsBottom');
    saveButtons.forEach(button => {
        button.addEventListener('click', function() {
            saveSettings();
        });
    });
    
    // Reset settings buttons
    const resetButtons = document.querySelectorAll('#resetSettings, #resetSettingsBottom');
    resetButtons.forEach(button => {
        button.addEventListener('click', function() {
            resetSettings();
        });
    });
}

// Save settings
function saveSettings() {
    let settings = {
        app_type: 'sonarr',
        api_url: document.getElementById('sonarr_api_url')?.value || '',
        api_key: document.getElementById('sonarr_api_key')?.value || '',
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
        minimum_download_queue_size: parseInt(document.getElementById('minimum_download_queue_size')?.value || -1),
        log_refresh_interval_seconds: parseInt(document.getElementById('log_refresh_interval_seconds')?.value || 30)
    };
    
    console.log('Saving settings:', settings);
    
    // Send the settings to the server
    fetch('/api/settings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(settings)
    })
    .then(response => {
        // Check if the response is valid JSON
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return response.json().catch(err => {
                console.error('Error parsing JSON response:', err);
                throw new Error('Invalid JSON response from server');
            });
        } else {
            // If not JSON, get the text and throw an error
            return response.text().then(text => {
                console.error('Received non-JSON response:', text.substring(0, 300));
                throw new Error(`Server responded with non-JSON data: ${text.substring(0, 100)}...`);
            });
        }
    })
    .then(data => {
        if (data.success) {
            showNotification('Settings saved successfully!', 'success');
            
            // Reload settings to ensure consistency
            setTimeout(() => {
                loadSonarrSettings();
            }, 1000);
        } else {
            showNotification('Error saving settings: ' + (data.message || 'Unknown error'), 'error');
            console.error('Error details:', data.details || 'No details provided');
        }
    })
    .catch(error => {
        console.error('Error saving settings:', error);
        showNotification('Error saving settings: ' + error.message, 'error');
    });
}

// Reset settings to defaults
function resetSettings() {
    if (confirm('Are you sure you want to reset Sonarr settings to defaults?')) {
        fetch('/api/settings/reset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Settings reset to defaults', 'success');
                // Reload settings to reflect the reset
                loadSonarrSettings();
            } else {
                showNotification('Error resetting settings: ' + (data.message || 'Unknown error'), 'error');
            }
        })
        .catch(error => {
            console.error('Error resetting settings:', error);
            showNotification('Error resetting settings: ' + error.message, 'error');
        });
    }
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