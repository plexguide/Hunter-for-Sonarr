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
    
    // Load apps for initial display
    loadApps: function() {
        // Load the currently selected app
        this.loadAppSettings(this.currentApp);
    },
    
    // Load app settings
    loadAppSettings: function(app) {
        console.log(`[Apps] Loading settings for ${app}`);
        
        // Get the container to put the settings in
        const appPanel = document.getElementById(app + 'Apps');
        if (!appPanel) {
            console.error(`App panel not found for ${app}`);
            return;
        }
        
        // Clear existing content
        appPanel.innerHTML = '<div class="loading-panel"><i class="fas fa-spinner fa-spin"></i> Loading settings...</div>';
        
        // Fetch settings for this app
        fetch(`/api/settings/${app}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(appSettings => {
                console.log(`[Apps] Received settings for ${app}:`, appSettings);
                
                // Clear loading message
                appPanel.innerHTML = '';
                
                // Create a form container with the app-type attribute
                const formElement = document.createElement('form');
                formElement.classList.add('settings-form');
                formElement.setAttribute('data-app-type', app);
                appPanel.appendChild(formElement);
                
                // Generate the form using SettingsForms module
                if (typeof SettingsForms !== 'undefined') {
                    const formFunction = SettingsForms[`generate${app.charAt(0).toUpperCase()}${app.slice(1)}Form`];
                    if (typeof formFunction === 'function') {
                        // Use .call() to set the 'this' context correctly
                        formFunction.call(SettingsForms, formElement, appSettings);
                        
                        // Update duration displays for this app
                        if (typeof SettingsForms.updateDurationDisplay === 'function') {
                            SettingsForms.updateDurationDisplay();
                        }
                        
                        // Add change listener to detect modifications
                        this.addFormChangeListeners(formElement);
                    } else {
                        console.warn(`Form generation function not found for ${app}`);
                        appPanel.innerHTML = `<div class="settings-message">Settings for ${app.charAt(0).toUpperCase() + app.slice(1)} are not available.</div>`;
                    }
                } else {
                    console.error('SettingsForms module not found');
                    appPanel.innerHTML = '<div class="error-panel">Unable to generate settings form. Please reload the page.</div>';
                }
            })
            .catch(error => {
                console.error(`Error loading ${app} settings:`, error);
                appPanel.innerHTML = `<div class="error-panel"><i class="fas fa-exclamation-triangle"></i> Error loading settings: ${error.message}</div>`;
            });
    },
    
    // Add change event listeners to form elements
    addFormChangeListeners: function(form) {
        const elementsToWatch = form.querySelectorAll('input, select, textarea');
        elementsToWatch.forEach(element => {
            element.addEventListener('change', () => {
                console.log('Form element changed, marking settings as changed');
                this.markAppsAsChanged();
            });
        });
        
        // Add mutation observer to detect when instances are added or removed
        const instancesContainer = form.querySelector('.instances-container');
        if (instancesContainer) {
            console.log('Setting up mutation observer for instances container');
            
            // Create a mutation observer to watch for changes to the instances container
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    // If nodes were added or removed, mark settings as changed
                    if (mutation.type === 'childList' && 
                        (mutation.addedNodes.length > 0 || mutation.removedNodes.length > 0)) {
                        console.log('Instances container changed:', 
                            mutation.addedNodes.length > 0 ? 'Added nodes' : 'Removed nodes');
                        this.markAppsAsChanged();
                        
                        // If nodes were added, also add change listeners to them
                        if (mutation.addedNodes.length > 0) {
                            mutation.addedNodes.forEach(node => {
                                if (node.querySelectorAll) {
                                    const newInputs = node.querySelectorAll('input, select, textarea');
                                    newInputs.forEach(input => {
                                        input.addEventListener('change', () => {
                                            console.log('New input changed, marking settings as changed');
                                            this.markAppsAsChanged();
                                        });
                                    });
                                }
                            });
                        }
                    }
                });
            });
            
            // Start observing
            observer.observe(instancesContainer, { childList: true, subtree: true });
        }
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
        
        // Load the newly selected app's settings
        this.loadAppSettings(selectedApp);
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
        
        // Get the app panel for the current app
        const appPanel = document.getElementById(this.currentApp + 'Apps');
        if (!appPanel) {
            console.error(`App panel not found for ${this.currentApp}`);
            return;
        }
        
        // Get the form element
        const appForm = appPanel.querySelector('form.settings-form');
        if (!appForm) {
            console.error(`Settings form not found for ${this.currentApp}`);
            return;
        }
        
        // Check that the form has the correct data-app-type attribute
        if (appForm.getAttribute('data-app-type') !== this.currentApp) {
            console.error(`Form has incorrect app type: ${appForm.getAttribute('data-app-type')}, expected: ${this.currentApp}`);
            appForm.setAttribute('data-app-type', this.currentApp);
        }
        
        // Get settings using SettingsForms
        let appSettings = null;
        if (typeof SettingsForms !== 'undefined' && typeof SettingsForms.getFormSettings === 'function') {
            appSettings = SettingsForms.getFormSettings(appForm);
            if (!appSettings) {
                console.error(`Could not get settings for ${this.currentApp}`);
                alert(`Error: Could not collect settings from the form. Please try again.`);
                return;
            }
        } else {
            console.error('SettingsForms module or getFormSettings function not found');
            alert('Error: Settings module not found. Please refresh the page and try again.');
            return;
        }
        
        console.log(`[Apps] Sending settings for ${this.currentApp}:`, appSettings);
        console.log(`[Apps] Number of instances found for ${this.currentApp}:`, appSettings.instances?.length || 0);
        console.log(`[Apps] Instances detail:`, JSON.stringify(appSettings.instances, null, 2));
        
        // Send settings update request to the correct app-specific endpoint
        fetch(`/api/settings/${this.currentApp}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(appSettings)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Settings saved:', data);
            
            // Disable save button
            this.settingsChanged = false;
            if (this.elements.saveAppsButton) {
                this.elements.saveAppsButton.disabled = true;
            }
            
            // Show success message
            alert('Settings saved successfully!');
        })
        .catch(error => {
            console.error('Error saving settings:', error);
            alert(`Error saving settings: ${error.message}`);
        });
    }
};

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', () => {
    appsModule.init();
});
