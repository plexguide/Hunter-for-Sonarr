/**
 * Huntarr - Apps Module
 * Handles displaying and managing app settings for media server applications
 */

const appsModule = {
    // State
    currentApp: 'sonarr',
    isLoading: false,
    settingsChanged: false,
    originalSettings: {},
    
    // DOM elements
    elements: {},
    
    // Initialize the apps module
    init: function() {
        this.cacheElements();
        this.setupEventListeners();
        
        // Initial load if apps is active section
        if (huntarrUI && huntarrUI.currentSection === 'apps') {
            this.loadApps();
        }
    },
    
    // Cache DOM elements
    cacheElements: function() {
        this.elements = {
            // Apps dropdown
            appsOptions: document.querySelectorAll('#appsSection .log-option'),
            currentAppsApp: document.getElementById('current-apps-app'),
            appsDropdownBtn: document.querySelector('#appsSection .log-dropdown-btn'),
            appsDropdownContent: document.querySelector('#appsSection .log-dropdown-content'),
            
            // Apps panels
            appAppsPanels: document.querySelectorAll('.app-apps-panel'),
            
            // Controls
            saveAppsButton: document.getElementById('saveAppsButton')
        };
    },
    
    // Set up event listeners
    setupEventListeners: function() {
        // App selection
        if (this.elements.appsOptions) {
            this.elements.appsOptions.forEach(option => {
                option.addEventListener('click', e => this.handleAppsAppChange(e));
            });
        }
        
        // Dropdown toggle
        if (this.elements.appsDropdownBtn) {
            this.elements.appsDropdownBtn.addEventListener('click', () => {
                this.elements.appsDropdownContent.classList.toggle('show');
                
                // Close all other dropdowns
                document.querySelectorAll('.log-dropdown-content.show').forEach(dropdown => {
                    if (dropdown !== this.elements.appsDropdownContent) {
                        dropdown.classList.remove('show');
                    }
                });
            });
        }
        
        // Close dropdown when clicking outside
        document.addEventListener('click', e => {
            if (!e.target.matches('#appsSection .log-dropdown-btn') && 
                !e.target.closest('#appsSection .log-dropdown-btn')) {
                if (this.elements.appsDropdownContent && this.elements.appsDropdownContent.classList.contains('show')) {
                    this.elements.appsDropdownContent.classList.remove('show');
                }
            }
        });

        // Save button
        if (this.elements.saveAppsButton) {
            this.elements.saveAppsButton.addEventListener('click', () => this.saveApps());
        }
    },
    
    // Load apps data when section becomes active
    loadApps: function() {
        console.log('[Apps] Loading apps data for ' + this.currentApp);
        
        // Disable save button until changes are made
        if (this.elements.saveAppsButton) {
            this.elements.saveAppsButton.disabled = true;
        }
        this.settingsChanged = false;
        
        // Get all settings to populate forms
        fetch('/api/settings')
            .then(response => response.json())
            .then(data => {
                console.log('Loaded settings:', data);
                
                // Store original settings for comparison
                this.originalSettings = data;
                
                // Ensure current app panel is visible
                this.showAppPanel(this.currentApp);
                
                // Populate each app's settings form
                this.populateAllAppPanels(data);
            })
            .catch(error => {
                console.error('Error loading settings:', error);
                const appPanel = document.getElementById(this.currentApp + 'Apps');
                if (appPanel) {
                    appPanel.innerHTML = '<div class="error-panel"><i class="fas fa-exclamation-triangle"></i> Failed to load app settings. Please try again.</div>';
                }
            });
    },
    
    // Populate all app panels with settings
    populateAllAppPanels: function(data) {
        // Clear existing panels
        this.elements.appAppsPanels.forEach(panel => {
            panel.innerHTML = '';
        });
        
        // Populate each app panel
        if (data.sonarr) this.populateAppPanel('sonarr', data.sonarr);
        if (data.radarr) this.populateAppPanel('radarr', data.radarr);
        if (data.lidarr) this.populateAppPanel('lidarr', data.lidarr);
        if (data.readarr) this.populateAppPanel('readarr', data.readarr);
        if (data.whisparr) this.populateAppPanel('whisparr', data.whisparr);
        if (data.swaparr) this.populateAppPanel('swaparr', data.swaparr);
    },
    
    // Populate a specific app panel with settings
    populateAppPanel: function(app, appSettings) {
        const appPanel = document.getElementById(app + 'Apps');
        if (!appPanel) return;
        
        // Create settings container
        const settingsContainer = document.createElement('div');
        settingsContainer.className = 'settings-group';
        
        // Create settings form
        const settingsForm = document.createElement('div');
        settingsForm.id = app + 'SettingsForm';
        settingsForm.className = 'settings-form';
        
        // Add to container and panel
        settingsContainer.appendChild(settingsForm);
        appPanel.appendChild(settingsContainer);
        
        // Generate the form using SettingsForms module
        if (typeof SettingsForms !== 'undefined') {
            const formFunction = SettingsForms[`generate${app.charAt(0).toUpperCase()}${app.slice(1)}Form`];
            if (typeof formFunction === 'function') {
                formFunction(settingsForm, appSettings);
                
                // Update duration displays for this app
                if (typeof SettingsForms.updateDurationDisplay === 'function') {
                    SettingsForms.updateDurationDisplay();
                }
                
                // Add change listener to detect modifications
                this.addFormChangeListeners(settingsForm);
            } else {
                console.warn(`Form generation function not found for ${app}`);
                settingsForm.innerHTML = `<div class="settings-message">Settings for ${app.charAt(0).toUpperCase() + app.slice(1)} are not available.</div>`;
            }
        } else {
            console.error('SettingsForms module not found');
            settingsForm.innerHTML = '<div class="error-panel">Unable to generate settings form. Please reload the page.</div>';
        }
    },
    
    // Add change event listeners to form elements
    addFormChangeListeners: function(form) {
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('change', () => this.markAppsAsChanged());
            // For text inputs, also listen for input event
            if (input.type === 'text' || input.type === 'password' || input.type === 'number' || input.tagName.toLowerCase() === 'textarea') {
                input.addEventListener('input', () => this.markAppsAsChanged());
            }
        });
    },
    
    // Show specific app panel and hide others
    showAppPanel: function(app) {
        // Hide all app panels
        this.elements.appAppsPanels.forEach(panel => {
            panel.classList.remove('active');
            panel.style.display = 'none';
        });
        
        // Show the selected app's panel
        const selectedPanel = document.getElementById(app + 'Apps');
        if (selectedPanel) {
            selectedPanel.classList.add('active');
            selectedPanel.style.display = 'block';
        }
    },
    
    // Handle app selection changes
    handleAppsAppChange: function(e) {
        e.preventDefault();
        
        const selectedApp = e.target.getAttribute('data-app');
        if (!selectedApp || selectedApp === this.currentApp) return;
        
        // Check if there are unsaved changes
        if (this.settingsChanged) {
            const confirmSwitch = confirm('You have unsaved changes. Do you want to continue without saving?');
            if (!confirmSwitch) {
                return;
            }
        }
        
        // Update UI
        this.elements.appsOptions.forEach(option => {
            option.classList.remove('active');
        });
        e.target.classList.add('active');
        
        // Update the current app text with proper capitalization
        let displayName = selectedApp.charAt(0).toUpperCase() + selectedApp.slice(1);
        this.elements.currentAppsApp.textContent = displayName;
        
        // Close the dropdown
        this.elements.appsDropdownContent.classList.remove('show');
        
        // Show the selected app's panel
        this.showAppPanel(selectedApp);
        
        this.currentApp = selectedApp;
        console.log(`[Apps] Switched app to: ${this.currentApp}`);
        
        // Reset changed state
        this.settingsChanged = false;
        this.elements.saveAppsButton.disabled = true;
    },
    
    // Mark apps as changed
    markAppsAsChanged: function() {
        this.settingsChanged = true;
        if (this.elements.saveAppsButton) {
            this.elements.saveAppsButton.disabled = false;
        }
    },
    
    // Save apps settings
    saveApps: function() {
        console.log('[Apps] Saving app settings for ' + this.currentApp);
        
        // Gather settings from all app forms
        const allSettings = {};
        const apps = ['sonarr', 'radarr', 'lidarr', 'readarr', 'whisparr', 'swaparr'];
        
        // Loop through each app and collect settings
        apps.forEach(app => {
            const appPanel = document.getElementById(app + 'Apps');
            if (!appPanel) return;
            
            const appForm = appPanel.querySelector('.settings-form');
            if (!appForm) return;
            
            // Get settings using SettingsForms
            if (typeof SettingsForms !== 'undefined' && typeof SettingsForms.getFormSettings === 'function') {
                const appSettings = SettingsForms.getFormSettings(appForm);
                if (appSettings) {
                    allSettings[app] = appSettings;
                }
            }
        });
        
        // Send settings update request
        fetch('/api/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ [this.currentApp]: allSettings[this.currentApp] })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Settings saved:', data);
            
            // Disable save button
            this.settingsChanged = false;
            if (this.elements.saveAppsButton) {
                this.elements.saveAppsButton.disabled = true;
            }
            
            // Show success message
            alert('Settings saved successfully!');
            
            // Update original settings
            this.originalSettings = data;
        })
        .catch(error => {
            console.error('Error saving settings:', error);
            alert('Error saving settings. Please try again.');
        });
    }
};

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', () => {
    appsModule.init();
});
