/**
 * Settings Initializer
 * Ensures settings forms are properly loaded on page load
 */

document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the settings page
    if (window.location.pathname === '/settings' || window.location.hash === '#settings') {
        console.log('Settings page detected, initializing settings...');
        
        // Initialize active tab settings
        initializeActiveTabSettings();
        
        // Set up tab switching
        setupTabSwitching();
    }
});

// Initialize settings for the active tab
function initializeActiveTabSettings() {
    const activeTab = document.querySelector('.settings-tab.active');
    if (!activeTab) {
        console.warn('No active settings tab found');
        return;
    }
    
    const app = activeTab.getAttribute('data-settings');
    if (!app) {
        console.warn('Active tab has no data-settings attribute');
        return;
    }
    
    console.log(`Loading settings for active tab: ${app}`);
    loadAppSettings(app);
}

// Load settings for a specific app
function loadAppSettings(app) {
    console.log(`Fetching settings for ${app}...`);
    
    // First get general settings
    fetch('/api/settings')
        .then(response => response.json())
        .then(allSettings => {
            console.log('All settings loaded:', allSettings);
            
            // Then get app-specific API settings if needed
            fetch(`/api/app-settings?app=${app}`)
                .then(response => response.json())
                .then(apiData => {
                    console.log(`API data for ${app}:`, apiData);
                    
                    // Prepare settings object
                    const settings = allSettings;
                    
                    // Add API credentials if available
                    if (apiData && apiData.success) {
                        settings.api_url = apiData.api_url;
                        settings.api_key = apiData.api_key;
                    }
                    
                    // Find the container for this app's settings
                    const container = document.getElementById(`${app}Settings`);
                    if (!container) {
                        console.error(`Container for ${app} settings not found`);
                        return;
                    }
                    
                    console.log(`Generating form for ${app}...`);
                    
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
                        default:
                            console.error(`Unknown app type: ${app}`);
                            return;
                    }
                    
                    // Update any dynamic displays
                    if (typeof SettingsForms.updateDurationDisplay === 'function') {
                        SettingsForms.updateDurationDisplay();
                    }
                    
                    console.log(`${app} settings form generated successfully`);
                })
                .catch(error => {
                    console.error(`Error loading API settings for ${app}:`, error);
                    const container = document.getElementById(`${app}Settings`);
                    if (container) {
                        container.innerHTML = `<div class="error-message">Error loading API settings: ${error.message}</div>`;
                    }
                });
        })
        .catch(error => {
            console.error(`Error loading settings:`, error);
            const container = document.getElementById(`${app}Settings`);
            if (container) {
                container.innerHTML = `<div class="error-message">Error loading settings: ${error.message}</div>`;
            }
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
                
                // Check if settings are already loaded
                if (!selectedPanel.querySelector('.settings-group')) {
                    loadAppSettings(app);
                }
            }
        });
    });
}
