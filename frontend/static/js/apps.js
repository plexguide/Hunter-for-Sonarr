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
        // Cache DOM elements
        this.cacheElements();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Initialize state
        this.settingsChanged = false;
        
        // Load apps for initial display
        this.loadApps();
        
        // Register with the main unsaved changes system if available
        this.registerUnsavedChangesHandler();
    },
    
    // Register with the main unsaved changes system
    registerUnsavedChangesHandler: function() {
        // Add our own beforeunload handler for direct page exits
        if (!window._appsBeforeUnloadHandlerRegistered) {
            const originalBeforeUnload = window.onbeforeunload;
            window.onbeforeunload = (event) => {
                // Skip check if we're currently saving
                if (window._appsCurrentlySaving) {
                    return undefined;
                }
                
                // Check if apps has unsaved changes
                if (this.settingsChanged) {
                    // Standard way to trigger the browser's confirmation dialog
                    event.preventDefault(); 
                    event.returnValue = 'You have unsaved changes. Are you sure you want to leave? Changes will be lost.';
                    return 'You have unsaved changes. Are you sure you want to leave? Changes will be lost.';
                }
                
                // Fall back to original handler if we don't have changes
                if (originalBeforeUnload) {
                    return originalBeforeUnload(event);
                }
                return undefined;
            };
            
            // Mark that we've registered the handler
            window._appsBeforeUnloadHandlerRegistered = true;
        }
        
        // Integrate with huntarrUI if available
        if (typeof huntarrUI !== 'undefined') {
            // Store original markSettingsAsChanged function if it exists
            const originalMarkChanged = huntarrUI.markSettingsAsChanged;
            
            // Override with our function that knows about both systems
            huntarrUI.markSettingsAsChanged = () => {
                // Call original if it existed
                if (originalMarkChanged) {
                    originalMarkChanged.call(huntarrUI);
                }
                
                // Set the flag for the main UI
                huntarrUI.settingsChanged = true;
            };
            
            // Listen for navigation to non-apps pages
            document.addEventListener('click', (event) => {
                const navLink = event.target.closest('a[href^="#"]');
                if (navLink) {
                    const targetPage = navLink.getAttribute('href').substring(1);
                    // If navigating away from apps page and we have changes
                    if (targetPage !== 'apps' && this.settingsChanged && !window._appsCurrentlySaving) {
                        if (!confirm('You have unsaved changes. Are you sure you want to leave? Changes will be lost.')) {
                            event.preventDefault();
                        }
                    }
                }
            });
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
            this.elements.saveAppsButton.addEventListener('click', (event) => this.saveApps(event));
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
        if (!form) return;
        
        console.log(`Adding form change listeners to form with app type: ${form.getAttribute('data-app-type')}`);
        
        // Function to handle form element changes
        const handleChange = () => {
            console.log('Form changed, enabling save button');
            this.markAppsAsChanged();
        };
        
        // Add listeners to all form inputs, selects, and textareas
        const formElements = form.querySelectorAll('input, select, textarea');
        formElements.forEach(element => {
            // Skip buttons
            if (element.type === 'button' || element.type === 'submit') return;
            
            // Remove any existing change listeners to avoid duplicates
            element.removeEventListener('change', handleChange);
            element.removeEventListener('input', handleChange);
            
            // Add change listeners
            element.addEventListener('change', handleChange);
            
            // For text and number inputs, also listen for input events
            if (element.type === 'text' || element.type === 'number' || element.type === 'textarea') {
                element.addEventListener('input', handleChange);
            }
            
            console.log(`Added change listener to ${element.tagName} with id: ${element.id || 'no-id'}`);
        });
        
        // Also add a MutationObserver to detect when instances are added or removed
        // This is needed because adding/removing instances doesn't trigger input events
        try {
            // Check if we already have an observer for this form
            if (this.observer) {
                this.observer.disconnect();
            }
            
            // Create a new MutationObserver
            this.observer = new MutationObserver((mutations) => {
                let shouldUpdate = false;
                
                mutations.forEach(mutation => {
                    // Check for elements added or removed
                    if (mutation.type === 'childList' && 
                       (mutation.addedNodes.length > 0 || mutation.removedNodes.length > 0)) {
                        shouldUpdate = true;
                    }
                });
                
                if (shouldUpdate) {
                    console.log('Instances container changed - form changed, enabling save button');
                    this.markAppsAsChanged();
                }
            });
            
            // Start observing instances container for changes
            const instancesContainers = form.querySelectorAll('.instances-container');
            instancesContainers.forEach(container => {
                this.observer.observe(container, { childList: true, subtree: true });
                console.log(`Added MutationObserver to container: ${container.className}`);
            });
        } catch (error) {
            console.error('Error setting up MutationObserver:', error);
        }
    },
    
    // Mark apps as changed
    markAppsAsChanged: function() {
        this.settingsChanged = true;
        if (this.elements.saveAppsButton) {
            this.elements.saveAppsButton.disabled = false;
            console.log('Save button enabled');
        } else {
            console.error('Save button element not found');
        }
    },
    
    // Show specific app panel and hide others
    showAppPanel: function(app) {
        console.log(`Showing app panel for ${app}`);
        // Hide all app panels
        this.elements.appAppsPanels.forEach(panel => {
            panel.style.display = 'none';
            panel.classList.remove('active');
        });
        
        // Show the selected app panel
        const appPanel = document.getElementById(`${app}Apps`);
        if (appPanel) {
            appPanel.style.display = 'block';
            appPanel.classList.add('active');
            
            // Ensure the panel has the correct data-app-type attribute
            appPanel.setAttribute('data-app-type', app);
            
            console.log(`App panel for ${app} is now active`);
        } else {
            console.error(`App panel for ${app} not found`);
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
        // Special handling for Whisparr V2
        if (selectedApp === 'whisparr') {
            displayName = 'Whisparr V2';
        }
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
    
    // Save apps settings - completely rewritten for reliability
    saveApps: function(event) {
        if (event) event.preventDefault();
        
        console.log('[Apps] Save button clicked');
        
        // Set a flag that we're in the middle of saving
        window._appsCurrentlySaving = true;
        
        // Get the current app from module state
        const appType = this.currentApp;
        if (!appType) {
            console.error('No current app selected');
            
            // Emergency fallback - try to find the visible app panel
            const visiblePanel = document.querySelector('.app-apps-panel[style*="display: block"]');
            if (visiblePanel && visiblePanel.id) {
                // Extract app type from panel ID (e.g., "sonarrApps" -> "sonarr")
                const extractedType = visiblePanel.id.replace('Apps', '');
                console.log(`Fallback: Found visible panel with ID ${visiblePanel.id}, extracted app type: ${extractedType}`);
                
                if (extractedType) {
                    // Continue with the extracted app type
                    return this.saveAppSettings(extractedType, visiblePanel);
                }
            }
            
            if (typeof huntarrUI !== 'undefined' && typeof huntarrUI.showNotification === 'function') {
                huntarrUI.showNotification('Error: Could not determine which app settings to save', 'error');
            } else {
                alert('Error: Could not determine which app settings to save');
            }
            return;
        }
        
        // Direct DOM access to find the app panel
        const appPanel = document.getElementById(`${appType}Apps`);
        if (!appPanel) {
            console.error(`App panel not found for ${appType}`);
            if (typeof huntarrUI !== 'undefined' && typeof huntarrUI.showNotification === 'function') {
                huntarrUI.showNotification(`Error: App panel not found for ${appType}`, 'error');
            } else {
                alert(`Error: App panel not found for ${appType}`);
            }
            return;
        }
        
        // Proceed with saving for the found app panel
        this.saveAppSettings(appType, appPanel);
    },
    
    // Helper function to save settings for a specific app
    saveAppSettings: function(appType, appPanel) {
        console.log(`Collecting settings for ${appType}`);
        
        let settings;
        try {
            // Make sure the app type is set on the panel for SettingsForms
            appPanel.setAttribute('data-app-type', appType);
            
            // Get settings from the form
            settings = SettingsForms.getFormSettings(appPanel, appType);
            console.log(`Collected settings for ${appType}:`, settings);
        } catch (error) {
            console.error(`Error collecting settings for ${appType}:`, error);
            if (typeof huntarrUI !== 'undefined' && typeof huntarrUI.showNotification === 'function') {
                huntarrUI.showNotification(`Error collecting settings: ${error.message}`, 'error');
            } else {
                alert(`Error collecting settings: ${error.message}`);
            }
            return;
        }
        
        // Add specific logging for settings critical to stateful management
        if (appType === 'general') {
            console.log('Stateful management settings being saved:', {
                statefulExpirationHours: settings.statefulExpirationHours,
                api_timeout: settings.api_timeout,
                command_wait_delay: settings.command_wait_delay,
                command_wait_attempts: settings.command_wait_attempts
            });
        }
        
        // Send settings to the server
        console.log(`Sending ${appType} settings to server...`);
        fetch(`/api/settings/${appType}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(settings)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log(`${appType} settings saved successfully:`, data);
            
            // Disable save button and reset state
            this.settingsChanged = false;
            if (this.elements.saveAppsButton) {
                this.elements.saveAppsButton.disabled = true;
            }
            
            // Reset the saving flag
            window._appsCurrentlySaving = false;
            
            // Show success notification
            if (typeof huntarrUI !== 'undefined' && typeof huntarrUI.showNotification === 'function') {
                huntarrUI.showNotification(`${appType} settings saved successfully`, 'success');
            } else {
                alert(`${appType} settings saved successfully`);
            }
        })
        .catch(error => {
            console.error(`Error saving ${appType} settings:`, error);
            if (typeof huntarrUI !== 'undefined' && typeof huntarrUI.showNotification === 'function') {
                huntarrUI.showNotification(`Error saving settings: ${error.message}`, 'error');
            } else {
                alert(`Error saving settings: ${error.message}`);
            }
            // Reset the saving flag
            window._appsCurrentlySaving = false;
        });
    }
};

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', () => {
    appsModule.init();
    
    // Add a direct event listener to the save button for maximum reliability
    const saveButton = document.getElementById('saveAppsButton');
    if (saveButton) {
        saveButton.addEventListener('click', function(event) {
            console.log('Save button clicked directly');
            appsModule.saveApps(event);
        });
    }
});
