/**
 * Huntarr - New UI Implementation
 * Main JavaScript file for handling UI interactions and API communication
 */

const huntarrUI = {
    // Current state
    eventSources: {},
    currentSection: 'home', // Default section
    currentLogApp: 'all', // Default log app
    autoScroll: true,
    configuredApps: {
        sonarr: false,
        radarr: false,
        lidarr: false,
        readarr: false, // Added readarr
        whisparr: false // Added whisparr
    },
    originalSettings: {}, // Store the full original settings object
    settingsChanged: false, // Flag to track unsaved settings changes
    
    // Logo URL
    logoUrl: '/static/logo/64.png',
    
    // Element references
    elements: {},
    
    // Initialize the application
    init: function() {
        // Apply any preloaded theme immediately to avoid flashing
        const prefersDarkMode = localStorage.getItem('huntarr-dark-mode') === 'true';
        if (prefersDarkMode) {
            document.body.classList.add('dark-theme');
        }
        
        // Ensure logo is visible immediately
        this.logoUrl = localStorage.getItem('huntarr-logo-url') || this.logoUrl;
        
        this.cacheElements();
        this.setupEventListeners();
        this.loadUsername();
        this.checkAppConnections();
        this.loadMediaStats(); // Load media statistics
        
        // Ensure logo is applied
        if (typeof window.applyLogoToAllElements === 'function') {
            window.applyLogoToAllElements();
        }
        
        // Initialize instance event handlers
        this.setupInstanceEventHandlers();
    },
    
    // Cache DOM elements for better performance
    cacheElements: function() {
        // Navigation
        this.elements.navItems = document.querySelectorAll('.nav-item');
        this.elements.homeNav = document.getElementById('homeNav');
        this.elements.logsNav = document.getElementById('logsNav');
        this.elements.settingsNav = document.getElementById('settingsNav');
        this.elements.userNav = document.getElementById('userNav');
        
        // Sections
        this.elements.sections = document.querySelectorAll('.content-section');
        this.elements.homeSection = document.getElementById('homeSection');
        this.elements.logsSection = document.getElementById('logsSection');
        this.elements.settingsSection = document.getElementById('settingsSection');
        
        // App tabs & Settings Tabs
        this.elements.appTabs = document.querySelectorAll('.app-tab'); // For logs section
        this.elements.logTabs = document.querySelectorAll('.log-tab'); // Added log tabs
        this.elements.settingsTabs = document.querySelectorAll('.settings-tab');
        this.elements.appSettingsPanels = document.querySelectorAll('.app-settings-panel');
        
        // Logs
        this.elements.logsContainer = document.getElementById('logsContainer');
        this.elements.autoScrollCheckbox = document.getElementById('autoScrollCheckbox');
        this.elements.clearLogsButton = document.getElementById('clearLogsButton');
        this.elements.logConnectionStatus = document.getElementById('logConnectionStatus');
        
        // Settings
        this.elements.saveSettingsButton = document.getElementById('saveSettingsButton'); // Corrected ID
        
        // Status elements
        this.elements.sonarrHomeStatus = document.getElementById('sonarrHomeStatus');
        this.elements.radarrHomeStatus = document.getElementById('radarrHomeStatus');
        this.elements.lidarrHomeStatus = document.getElementById('lidarrHomeStatus');
        this.elements.readarrHomeStatus = document.getElementById('readarrHomeStatus'); // Added readarr
        this.elements.whisparrHomeStatus = document.getElementById('whisparrHomeStatus'); // Added whisparr
        
        // Actions
        this.elements.startHuntButton = document.getElementById('startHuntButton');
        this.elements.stopHuntButton = document.getElementById('stopHuntButton');
        
        // Theme
        // this.elements.themeToggle = document.getElementById('themeToggle'); // Removed theme toggle
        
        // Logout
        this.elements.logoutLink = document.getElementById('logoutLink'); // Added logout link
    },
    
    // Set up event listeners
    setupEventListeners: function() {
        // Navigation
        this.elements.navItems.forEach(item => {
            item.addEventListener('click', this.handleNavigation.bind(this));
        });
        
        // App tabs
        this.elements.appTabs.forEach(tab => {
            tab.addEventListener('click', this.handleAppTabChange.bind(this));
        });
        
        // Settings tabs
        this.elements.settingsTabs.forEach(tab => {
            tab.addEventListener('click', this.handleSettingsTabChange.bind(this));
        });
        
        // Log tabs (New)
        this.elements.logTabs.forEach(tab => {
            tab.addEventListener('click', this.handleLogTabChange.bind(this));
        });
        
        // Logs
        if (this.elements.autoScrollCheckbox) {
            this.elements.autoScrollCheckbox.addEventListener('change', (e) => {
                this.autoScroll = e.target.checked;
            });
        }
        
        if (this.elements.clearLogsButton) {
            this.elements.clearLogsButton.addEventListener('click', this.clearLogs.bind(this));
        }
        
        // Settings
        if (this.elements.saveSettingsButton) {
            this.elements.saveSettingsButton.addEventListener('click', this.saveSettings.bind(this));
        }
        
        // Actions
        if (this.elements.startHuntButton) {
            this.elements.startHuntButton.addEventListener('click', this.startHunt.bind(this));
        }
        
        if (this.elements.stopHuntButton) {
            this.elements.stopHuntButton.addEventListener('click', this.stopHunt.bind(this));
        }
        
        // Theme
        // if (this.elements.themeToggle) { // Removed theme toggle
        //     this.elements.themeToggle.addEventListener('change', this.handleThemeToggle.bind(this));
        // }
        
        // Logout
        if (this.elements.logoutLink) { // Added listener for logout
            this.elements.logoutLink.addEventListener('click', this.logout.bind(this));
        }
        
        // Handle window hash change
        window.addEventListener('hashchange', () => this.handleHashNavigation(window.location.hash)); // Ensure hash is passed

        // Settings form delegation
        const settingsFormContainer = document.querySelector('.settings-form');
        if (settingsFormContainer) {
            settingsFormContainer.addEventListener('input', (event) => {
                if (event.target.closest('.app-settings-panel.active')) {
                    // Check if the target is an input, select, or textarea within the active panel
                    if (event.target.matches('input, select, textarea')) {
                        this.markSettingsAsChanged(); // Use the new function
                    }
                }
            });
             settingsFormContainer.addEventListener('change', (event) => {
                 if (event.target.closest('.app-settings-panel.active')) {
                    // Handle changes for checkboxes and selects that use 'change' event
                    if (event.target.matches('input[type="checkbox"], select')) {
                         this.markSettingsAsChanged(); // Use the new function
                    }
                 }
            });
        }

        // Add listener for unsaved changes prompt (External Navigation)
        window.onbeforeunload = (event) => {
            if (this.settingsChanged) {
                // Standard way to trigger the browser's confirmation dialog
                event.preventDefault(); 
                // Chrome requires returnValue to be set
                event.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
                return 'You have unsaved changes. Are you sure you want to leave?'; // For older browsers
            }
            // If no changes, return undefined to allow navigation without prompt
            return undefined; 
        };

        // Initial setup based on hash or default to home
        const initialHash = window.location.hash || '#home';
        this.handleHashNavigation(initialHash);
    },
    
    // Setup logo handling to prevent flashing during navigation
    setupLogoHandling: function() {
        // Get the logo image
        const logoImg = document.querySelector('.sidebar .logo');
        if (logoImg) {
            // Cache the source
            this.logoSrc = logoImg.src;
            
            // Ensure it's fully loaded
            if (!logoImg.complete) {
                logoImg.onload = () => {
                    // Once loaded, store the source
                    this.logoSrc = logoImg.src;
                };
            }
        }
        
        // Also add event listener to ensure logo is preserved during navigation
        window.addEventListener('beforeunload', () => {
            // Store logo src in session storage to persist across page loads
            if (this.logoSrc) {
                sessionStorage.setItem('huntarr-logo-src', this.logoSrc);
            }
        });
    },
    
    // Navigation handling
    handleNavigation: function(e) {
        e.preventDefault();
        const targetElement = e.currentTarget; // Get the clicked nav item
        const href = targetElement.getAttribute('href'); 

        if (!href) return; // Exit if no href

        let targetSection = null;
        let isInternalLink = href.startsWith('#');

        if (isInternalLink) {
            targetSection = href.substring(1) || 'home'; // Get section from hash, default to 'home' if only '#' 
        } else {
             // Handle external links (like /user) or non-hash links if needed
             // For now, assume non-hash links navigate away
        }

        // Check for unsaved changes ONLY if navigating INTERNALLY away from settings
        if (isInternalLink && this.currentSection === 'settings' && targetSection !== 'settings' && this.settingsChanged) {
            if (!confirm('You have unsaved changes. Are you sure you want to leave? Changes will be lost.')) {
                return; // Stop navigation if user cancels
            }
             // User confirmed, reset flag before navigating
            this.settingsChanged = false;
            this.updateSaveResetButtonState(false); 
        }

        // Proceed with navigation
        if (isInternalLink) {
            window.location.hash = href; // Change hash to trigger handleHashNavigation
        } else {
            // If it's an external link (like /user), just navigate normally
            window.location.href = href;
        }
    },
    
    handleHashNavigation: function(hash) {
        const section = hash.substring(1) || 'home';
        this.switchSection(section);
    },
    
    switchSection: function(section) {
        // Update active section
        this.elements.sections.forEach(s => {
            s.classList.remove('active');
        });
        
        // Update navigation
        this.elements.navItems.forEach(item => {
            item.classList.remove('active');
        });
        
        // Show selected section
        let newTitle = 'Home'; // Default title
        const sponsorsSection = document.getElementById('sponsorsSection'); // Get sponsors section element
        const sponsorsNav = document.getElementById('sponsorsNav'); // Get sponsors nav element

        if (section === 'home' && this.elements.homeSection) {
            this.elements.homeSection.classList.add('active');
            if (this.elements.homeNav) this.elements.homeNav.classList.add('active');
            newTitle = 'Home';
            this.currentSection = 'home';
            // Disconnect logs if switching away from logs
            this.disconnectAllEventSources(); 
        } else if (section === 'logs' && this.elements.logsSection) {
            this.elements.logsSection.classList.add('active');
            if (this.elements.logsNav) this.elements.logsNav.classList.add('active');
            newTitle = 'Logs';
            this.currentSection = 'logs';
            this.connectToLogs();
        } else if (section === 'settings' && this.elements.settingsSection) {
            this.elements.settingsSection.classList.add('active');
            if (this.elements.settingsNav) this.elements.settingsNav.classList.add('active');
            newTitle = 'Settings';
            this.currentSection = 'settings';
            
            // Ensure default settings tab is set if none is active
            if (!this.currentSettingsTab) {
                this.currentSettingsTab = 'sonarr'; // Default to sonarr tab
                
                // Set the sonarr tab as active
                const sonarrTab = document.querySelector('.settings-tab[data-settings="sonarr"]');
                if (sonarrTab) {
                    this.elements.settingsTabs.forEach(t => {
                        t.classList.remove('active');
                    });
                    sonarrTab.classList.add('active');
                    
                    // Also set the sonarr panel as visible
                    this.elements.appSettingsPanels.forEach(panel => {
                        panel.classList.remove('active');
                        panel.style.display = 'none';
                    });
                    
                    const sonarrPanel = document.getElementById('sonarrSettings');
                    if (sonarrPanel) {
                        sonarrPanel.classList.add('active');
                        sonarrPanel.style.display = 'block';
                    }
                }
            }
            
            this.loadAllSettings();
            // Disconnect logs if switching away from logs
            this.disconnectAllEventSources(); 
        } else if (section === 'sponsors' && sponsorsSection) { // ADDED sponsors case
            sponsorsSection.classList.add('active');
            if (sponsorsNav) sponsorsNav.classList.add('active');
            newTitle = 'Project Sponsors';
            this.currentSection = 'sponsors';
            // Set the iframe source when switching to this section
            const sponsorsFrame = document.getElementById('sponsorsFrame');
            if (sponsorsFrame && (!sponsorsFrame.src || sponsorsFrame.src === 'about:blank')) { // Set src only if not already set or blank
                sponsorsFrame.src = 'https://github.com/sponsors/plexguide';
            }
            // Disconnect logs if switching away from logs
            this.disconnectAllEventSources();
        } else {
            // Default to home if section is unknown or element missing
            if (this.elements.homeSection) this.elements.homeSection.classList.add('active');
            if (this.elements.homeNav) this.elements.homeNav.classList.add('active');
            newTitle = 'Home';
            this.currentSection = 'home';
            // Disconnect logs if switching away from logs
            this.disconnectAllEventSources(); 
        }

        // Update the page title
        const pageTitleElement = document.getElementById('currentPageTitle');
        if (pageTitleElement) {
            pageTitleElement.textContent = newTitle;
        } else {
            console.warn("[huntarrUI] currentPageTitle element not found during section switch.");
        }
    },
    
    // App tab switching
    handleAppTabChange: function(e) {
        const app = e.target.getAttribute('data-app');
        if (!app) return;
        
        // Update active tab
        this.elements.appTabs.forEach(tab => {
            tab.classList.remove('active');
        });
        e.target.classList.add('active');
        
        // Switch to the selected app logs
        this.currentApp = app;
        this.connectToLogs();
    },
    
    // Log tab switching (New)
    handleLogTabChange: function(e) {
        const app = e.target.getAttribute('data-app');
        if (!app || app === this.currentLogApp) return; // Do nothing if same tab clicked
        
        // Update active tab
        this.elements.logTabs.forEach(tab => {
            tab.classList.remove('active');
        });
        e.target.classList.add('active');
        
        // Switch to the selected app logs
        this.currentLogApp = app;
        this.clearLogs(); // Clear existing logs before switching
        this.connectToLogs(); // Reconnect to the new log source
    },

    // Settings tab switching
    handleSettingsTabChange: function(e) {
        // Use currentTarget to ensure we get the button, not the inner element
        const targetTab = e.currentTarget;
        const app = targetTab.dataset.app; // Use dataset.app as added in SettingsForms

        if (!app) {
             console.error("Settings tab clicked, but no data-app attribute found.");
             return; // Should not happen if HTML is correct
        }
        e.preventDefault(); // Prevent default if it was an anchor

        // Check for unsaved changes before switching tabs
        if (this.settingsChanged) {
            if (!confirm('You have unsaved changes on the current tab. Switch tabs anyway? Changes will be lost.')) {
                return; // Stop tab switch if user cancels
            }
             // User confirmed, reset flag before switching
            this.settingsChanged = false;
            this.updateSaveResetButtonState(false);
        }

        // Remove active class from all tabs and panels
        this.elements.settingsTabs.forEach(tab => tab.classList.remove('active'));
        this.elements.appSettingsPanels.forEach(panel => {
            panel.classList.remove('active');
            panel.style.display = 'none'; // Explicitly hide
        });

        // Set the target tab as active
        targetTab.classList.add('active');

        // Show the corresponding settings panel
        const panelElement = document.getElementById(`${app}Settings`);
        if (panelElement) {
            panelElement.classList.add('active');
            panelElement.style.display = 'block'; // Explicitly show
            this.currentSettingsTab = app; // Update current tab state
            // Ensure settings are populated for this tab using the stored originalSettings
            this.populateSettingsForm(app, this.originalSettings[app] || {});
            // Reset save button state when switching tabs (already done above if confirmed)
            this.updateSaveResetButtonState(false); // Ensure it's disabled on new tab
        } else {
             console.error(`Settings panel not found for app: ${app}`);
        }
    },
    
    // Logs handling
    connectToLogs: function() {
        // Disconnect any existing event sources
        this.disconnectAllEventSources();
        
        // Connect to logs stream for the currentLogApp
        this.connectEventSource(this.currentLogApp); // Pass the selected app
        this.elements.logConnectionStatus.textContent = 'Connecting...';
        this.elements.logConnectionStatus.className = '';
    },
    
    connectEventSource: function(appType) {
        // Close any existing event source
        if (this.eventSources.logs) {
            this.eventSources.logs.close();
        }
        
        try {
            // Append the app type to the URL
            const eventSource = new EventSource(`/logs?app=${appType}`); 
            
            eventSource.onopen = () => {
                this.elements.logConnectionStatus.textContent = 'Connected';
                this.elements.logConnectionStatus.className = 'status-connected';
            };
            
            eventSource.onmessage = (event) => {
                if (!this.elements.logsContainer) return;
                
                try {
                    // Create log entry element
                    const logEntry = document.createElement('div');
                    logEntry.className = 'log-entry';
                    
                    // The event.data should be used directly - server sends it as plain text
                    logEntry.textContent = event.data;
                    
                    // Detect log level from content for styling
                    if (event.data.includes('[ERROR]') || event.data.includes('Error:')) {
                        logEntry.classList.add('log-error');
                    } else if (event.data.includes('[WARNING]') || event.data.includes('Warning:')) {
                        logEntry.classList.add('log-warning');
                    } else if (event.data.includes('[DEBUG]')) {
                        logEntry.classList.add('log-debug');
                    } else {
                        logEntry.classList.add('log-info');
                    }
                    
                    // Add to logs container
                    this.elements.logsContainer.appendChild(logEntry);
                    
                    // Auto-scroll to bottom if enabled
                    if (this.autoScroll) {
                        this.elements.logsContainer.scrollTop = this.elements.logsContainer.scrollHeight;
                    }
                } catch (error) {
                    console.error('[huntarrUI] Error processing log message:', error);
                }
            };
            
            eventSource.onerror = (err) => {
                console.error(`[huntarrUI] EventSource error for app ${this.currentLogApp}:`, err); // Use currentLogApp
                if (this.elements.logConnectionStatus) {
                    this.elements.logConnectionStatus.textContent = 'Error/Disconnected';
                    this.elements.logConnectionStatus.className = 'status-disconnected';
                }
                
                // Close the potentially broken source before reconnecting
                if (this.eventSources.logs) {
                    this.eventSources.logs.close();
                    this.eventSources.logs = null; // Clear reference
                    console.log(`[huntarrUI] Closed potentially broken log EventSource for ${this.currentLogApp}.`);
                }

                // Always attempt to reconnect after a delay
                console.log(`[huntarrUI] Attempting to reconnect log stream for ${this.currentLogApp} in 5 seconds...`);
                // Use a variable to store the timeout ID so it can be cleared if needed
                if (this.logReconnectTimeout) {
                    clearTimeout(this.logReconnectTimeout);
                }
                this.logReconnectTimeout = setTimeout(() => {
                    // Check if we are *still* supposed to be connected to logs before reconnecting
                    if (this.currentSection === 'logs') {
                         console.log(`[huntarrUI] Reconnecting log stream for ${this.currentLogApp}.`);
                         this.connectEventSource(this.currentLogApp); 
                    } else {
                         console.log(`[huntarrUI] Log reconnect cancelled; user navigated away from logs section.`);
                    }
                    this.logReconnectTimeout = null; // Clear the timeout ID after execution
                }, 5000);
            };
            
            this.eventSources.logs = eventSource;
        } catch (error) {
            console.error('Error connecting to event source:', error);
            if (this.elements.logConnectionStatus) {
                this.elements.logConnectionStatus.textContent = 'Connection Error';
                this.elements.logConnectionStatus.className = 'status-disconnected';
            }
        }
    },
    
    disconnectAllEventSources: function() {
        console.log('[huntarrUI] Disconnecting all event sources...');
        // Clear any pending reconnect timeout
        if (this.logReconnectTimeout) {
            clearTimeout(this.logReconnectTimeout);
            this.logReconnectTimeout = null;
            console.log('[huntarrUI] Cleared pending log reconnect timeout.');
        }
        Object.keys(this.eventSources).forEach(key => {
            const source = this.eventSources[key];
            if (source && typeof source.close === 'function') {
                 try {
                     if (source.readyState !== EventSource.CLOSED) {
                         source.close();
                         console.log(`[huntarrUI] Closed event source for ${key}.`);
                     } else {
                         console.log(`[huntarrUI] Event source for ${key} was already closed.`);
                     }
                 } catch (e) {
                     console.error(`[huntarrUI] Error closing event source for ${key}:`, e);
                 }
            }
            // Clear the reference
            delete this.eventSources[key]; // Use delete
        });
         // Reset status indicator if logs aren't the active section
         if (this.currentSection !== 'logs' && this.elements.logConnectionStatus) {
             this.elements.logConnectionStatus.textContent = 'Disconnected';
             this.elements.logConnectionStatus.className = 'status-disconnected';
         }
    },
    
    addLogMessage: function(logData) {
        if (!this.elements.logsContainer) return;
        
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry log-${logData.level.toLowerCase()}`;
        logEntry.textContent = logData.message;
        
        this.elements.logsContainer.appendChild(logEntry);
        
        if (this.autoScroll) {
            this.elements.logsContainer.scrollTop = this.elements.logsContainer.scrollHeight;
        }
    },
    
    clearLogs: function() {
        if (this.elements.logsContainer) {
            this.elements.logsContainer.innerHTML = '';
        }
    },
    
    // Settings handling
    loadAllSettings: function() {
        // Ensure buttons are disabled and flag is reset when loading settings section
        this.settingsChanged = false;
        this.updateSaveResetButtonState(false);
        
        console.log("[huntarrUI] Loading all settings...");
        fetch(`/api/settings`) // Fetch the entire settings object
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log("[huntarrUI] All settings loaded:", data);
                this.originalSettings = JSON.parse(JSON.stringify(data)); // Store deep copy

                // Populate the currently active settings form
                this.populateSettingsForm(this.currentSettingsTab, this.originalSettings[this.currentSettingsTab] || {});
                // Optionally pre-populate others if needed, but might be redundant if done on tab switch
            })
            .catch(error => {
                console.error(`Error loading all settings:`, error);
                this.showNotification(`Error loading settings: ${error.message}`, 'error');
                this.originalSettings = {}; // Reset on error
            });
    },
    
    populateSettingsForm: function(app, appSettings) {
        // Cache the form for this app
        const form = document.getElementById(`${app}Settings`);
        if (!form) return;
        
        // Check if SettingsForms is loaded to generate the form
        if (typeof SettingsForms !== 'undefined') {
            const formFunction = SettingsForms[`generate${app.charAt(0).toUpperCase()}${app.slice(1)}Form`];
            if (typeof formFunction === 'function') {
                formFunction(form, appSettings);
                
                // For ANY app with instances, set up the instance management
                // Check if instances exist and it's an array
                if (appSettings && Array.isArray(appSettings.instances) && typeof SettingsForms.setupInstanceManagement === 'function') {
                    try {
                        // Pass the actual app name and the number of instances found
                        SettingsForms.setupInstanceManagement(form, app, appSettings.instances.length);
                    } catch (e) {
                        console.error(`[huntarrUI] Error setting up instance management for ${app}:`, e);
                    }
                }
                
                // Update duration displays for this app
                if (typeof SettingsForms.updateDurationDisplay === 'function') {
                    try {
                        SettingsForms.updateDurationDisplay();
                    } catch (e) {
                        console.error(`[huntarrUI] Error updating duration display:`, e);
                    }
                }
            } else {
                console.error(`[huntarrUI] Form generator function not found for app: ${app}`);
            }
        } else {
            console.error('[huntarrUI] SettingsForms is not defined');
            return;
        }
    },
    
    // Called when any setting input changes in the active tab
    markSettingsAsChanged() {
        if (!this.settingsChanged) {
            console.log("[huntarrUI] Settings marked as changed.");
            this.settingsChanged = true;
            this.updateSaveResetButtonState(true); // Enable buttons
        }
    },

    saveSettings: function() {
        const app = this.currentSettingsTab;
        console.log(`[huntarrUI] saveSettings called for app: ${app}`);
        
        // Use getFormSettings for all apps, as it handles different structures
        let settings = this.getFormSettings(app);

        if (!settings) {
            console.error(`[huntarrUI] Failed to collect settings for app: ${app}`);
            this.showNotification('Error collecting settings from form.', 'error');
            return;
        }

        console.log(`[huntarrUI] Collected settings for ${app}:`, settings);

        // Add app_type to the payload if needed by backend
        const payload = { [app]: settings };

        console.log(`[huntarrUI] Sending settings payload for ${app}:`, payload);

        // Use the correct endpoint /api/settings
        fetch(`/api/settings`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        })
        .then(response => {
            if (!response.ok) {
                // Try to get error message from response body
                return response.json().then(errData => {
                    throw new Error(errData.error || `HTTP error! status: ${response.status}`);
                }).catch(() => {
                    // Fallback if response body is not JSON or empty
                    throw new Error(`HTTP error! status: ${response.status}`);
                });
            }
            return response.json();
        })
        .then(savedConfig => {
            console.log('[huntarrUI] Settings saved successfully. Full config received:', savedConfig);
            this.showNotification('Settings saved successfully', 'success');

            // Update original settings state with the full config returned from backend
            if (typeof savedConfig === 'object' && savedConfig !== null) {
                this.originalSettings = JSON.parse(JSON.stringify(savedConfig));
            } else {
                console.error('[huntarrUI] Invalid config received from backend after save:', savedConfig);
                this.loadAllSettings();
                return;
            }

            // Re-populate the form with the saved data
            const currentAppSettings = this.originalSettings[app] || {};
            
            // Preserve instances data if missing in the response but was in our sent data
            if (app === 'sonarr' && !currentAppSettings.instances && settings.instances) {
                currentAppSettings.instances = settings.instances;
            }
            
            this.populateSettingsForm(app, currentAppSettings);

            // Update connection status and UI
            this.checkAppConnection(app);
            this.updateHomeConnectionStatus();
            this.settingsChanged = false; // Reset flag after successful save
            this.updateSaveResetButtonState(false); // Disable buttons after save
        })
        .catch(error => {
            console.error('Error saving settings:', error);
            this.showNotification(`Error saving settings: ${error.message}`, 'error');
        });
    },

    // Add or modify this function to handle enabling/disabling save/reset
    updateSaveResetButtonState(enable) { // Changed signature
        const saveButton = this.elements.saveSettingsButton;

        if (saveButton) {
            saveButton.disabled = !enable;
            // Optional: Add/remove class for styling
            if (enable) {
                saveButton.classList.remove('disabled-button');
            } else {
                saveButton.classList.add('disabled-button');
            }
        }
    },

    // Get settings from the form, updated to handle instances consistently
    getFormSettings: function(app) {
        const settings = {};
        const form = document.getElementById(`${app}Settings`);
        if (!form) {
            console.error(`[huntarrUI] Form not found for app: ${app}`);
            return null; // Return null if form doesn't exist
        }

        settings.instances = []; // Always initialize instances array

        // Check if multi-instance UI elements exist (like Sonarr)
        const instanceItems = form.querySelectorAll('.instance-item');
        if (instanceItems.length > 0) {
            console.log(`[huntarrUI] Found ${instanceItems.length} instance items for ${app}. Processing multi-instance mode.`);
            // Multi-instance logic (current Sonarr logic)
            instanceItems.forEach((item, index) => {
                const instanceId = item.dataset.instanceId; // Assumes Sonarr uses data-instance-id
                const nameInput = form.querySelector(`#${app}_instance_${instanceId}_name`);
                const urlInput = form.querySelector(`#${app}_instance_${instanceId}_api_url`);
                const keyInput = form.querySelector(`#${app}_instance_${instanceId}_api_key`);
                const enabledInput = item.querySelector('.instance-enabled'); // Assumes Sonarr uses this class for enable toggle

                if (urlInput && keyInput) { // Need URL and Key at least
                    settings.instances.push({
                        // Use nameInput value if available, otherwise generate a default
                        name: nameInput && nameInput.value.trim() !== '' ? nameInput.value.trim() : `Instance ${index + 1}`,
                        api_url: urlInput.value.trim(),
                        api_key: keyInput.value.trim(),
                        // Default to true if toggle doesn't exist or is checked
                        enabled: enabledInput ? enabledInput.checked : true
                    });
                }
            });
        } else {
            console.log(`[huntarrUI] No instance items found for ${app}. Processing single-instance mode.`);
            // Single-instance logic (for Radarr, Lidarr, etc.)
            // Look for the standard IDs used in their forms
            const nameInput = form.querySelector(`#${app}_instance_name`); // Check for a specific name field
            const urlInput = form.querySelector(`#${app}_api_url`);
            const keyInput = form.querySelector(`#${app}_api_key`);
            // Assuming single instances might have an enable toggle like #app_enabled
            const enabledInput = form.querySelector(`#${app}_enabled`);

            // Only add if URL and Key have values
            if (urlInput && urlInput.value.trim() && keyInput && keyInput.value.trim()) {
                 settings.instances.push({
                     name: nameInput && nameInput.value.trim() !== '' ? nameInput.value.trim() : `${app} Instance 1`, // Default name
                     api_url: urlInput.value.trim(),
                     api_key: keyInput.value.trim(),
                     // Default to true if toggle doesn't exist or is checked
                     enabled: enabledInput ? enabledInput.checked : true
                 });
            }
        }

        console.log(`[huntarrUI] Processed instances for ${app}:`, settings.instances);

        // Now collect any OTHER settings NOT part of the instance structure
        const allInputs = form.querySelectorAll('input, select');
        const handledInstanceFieldIds = new Set();

        // Identify IDs used in instance collection to avoid double-adding them
        if (instanceItems.length > 0) {
            // Multi-instance: Iterate items again to get IDs
            instanceItems.forEach((item) => {
                const instanceId = item.dataset.instanceId;
                if(instanceId) {
                    handledInstanceFieldIds.add(`${app}_instance_${instanceId}_name`);
                    handledInstanceFieldIds.add(`${app}_instance_${instanceId}_api_url`);
                    handledInstanceFieldIds.add(`${app}_instance_${instanceId}_api_key`);
                    const enabledToggle = item.querySelector('.instance-enabled');
                    if (enabledToggle && enabledToggle.id) handledInstanceFieldIds.add(enabledToggle.id);
                }
            });
        } else {
            // Single-instance: Check for standard IDs
             if (form.querySelector(`#${app}_instance_name`)) handledInstanceFieldIds.add(`${app}_instance_name`);
             if (form.querySelector(`#${app}_api_url`)) handledInstanceFieldIds.add(`${app}_api_url`);
             if (form.querySelector(`#${app}_api_key`)) handledInstanceFieldIds.add(`${app}_api_key`);
             if (form.querySelector(`#${app}_enabled`)) handledInstanceFieldIds.add(`${app}_enabled`);
        }

        allInputs.forEach(input => {
            // Skip buttons and fields already processed as part of an instance
            if (input.type === 'button' || handledInstanceFieldIds.has(input.id)) {
                return;
            }

            // Get the field key (remove app prefix)
            let key = input.id;
            if (key.startsWith(`${app}_`)) {
                key = key.substring(app.length + 1);
            }

            // Skip empty keys or keys that are just numbers (unlikely but possible)
            if (!key || /^\d+$/.test(key)) return;

            // Store the value
            if (input.type === 'checkbox') {
                settings[key] = input.checked;
            } else if (input.type === 'number') {
                // Handle potential empty string for numbers, store as null or default?
                settings[key] = input.value === '' ? null : parseInt(input.value, 10);
            } else {
                settings[key] = input.value.trim();
            }
        });

        console.log(`[huntarrUI] Final collected settings for ${app}:`, settings);
        return settings;
    },

    // Handle instance management events
    setupInstanceEventHandlers: function() {
        const settingsPanels = document.querySelectorAll('.app-settings-panel');
        
        settingsPanels.forEach(panel => {
            panel.addEventListener('addInstance', (e) => {
                this.addAppInstance(e.detail.appName);
            });
            
            panel.addEventListener('removeInstance', (e) => {
                this.removeAppInstance(e.detail.appName, e.detail.instanceId);
            });
            
            panel.addEventListener('testConnection', (e) => {
                this.testInstanceConnection(e.detail.appName, e.detail.instanceId, e.detail.url, e.detail.apiKey);
            });
        });
    },
    
    // Add a new instance to the app
    addAppInstance: function(appName) {
        const container = document.getElementById(`${appName}Settings`);
        if (!container) return;
        
        // Get current settings
        const currentSettings = this.getFormSettings(appName);
        
        // Add new instance
        if (!currentSettings.instances) {
            currentSettings.instances = [];
        }
        
        // Limit to 9 instances
        if (currentSettings.instances.length >= 9) {
            this.showNotification('Maximum of 9 instances allowed', 'error');
            return;
        }
        
        // Add new instance with a default name
        currentSettings.instances.push({
            name: `Instance ${currentSettings.instances.length + 1}`,
            api_url: '',
            api_key: '',
            enabled: true
        });
        
        // Regenerate form with new instance
        SettingsForms[`generate${appName.charAt(0).toUpperCase()}${appName.slice(1)}Form`](container, currentSettings);
        
        // Update controls like duration displays
        SettingsForms.updateDurationDisplay();
        
        this.showNotification('New instance added', 'success');
    },
    
    // Remove an instance
    removeAppInstance: function(appName, instanceId) {
        const container = document.getElementById(`${appName}Settings`);
        if (!container) return;
        
        // Get current settings
        const currentSettings = this.getFormSettings(appName);
        
        // Remove the instance
        if (currentSettings.instances && instanceId >= 0 && instanceId < currentSettings.instances.length) {
            // Keep at least one instance
            if (currentSettings.instances.length > 1) {
                const removedName = currentSettings.instances[instanceId].name;
                currentSettings.instances.splice(instanceId, 1);
                
                // Regenerate form
                SettingsForms[`generate${appName.charAt(0).toUpperCase()}${appName.slice(1)}Form`](container, currentSettings);
                
                // Update controls like duration displays
                SettingsForms.updateDurationDisplay();
                
                this.showNotification(`Instance "${removedName}" removed`, 'info');
            } else {
                this.showNotification('Cannot remove the last instance', 'error');
            }
        }
    },
    
    // Test connection for a specific instance
    testInstanceConnection: function(appName, instanceId, url, apiKey) {
        console.log(`Testing connection for ${appName} instance ${instanceId} with URL: ${url}`);
        
        // Make sure instanceId is treated as a number
        instanceId = parseInt(instanceId, 10);
        
        // Find the status span where we'll display the result
        const statusSpan = document.getElementById(`${appName}_instance_${instanceId}_status`);
        if (!statusSpan) {
            console.error(`Status span not found for ${appName} instance ${instanceId}`);
            return;
        }
        
        // Show testing status
        statusSpan.textContent = 'Testing...';
        statusSpan.className = 'connection-status testing';
        
        // Validate URL and API key
        if (!url || !apiKey) {
            statusSpan.textContent = 'Missing URL or API key';
            statusSpan.className = 'connection-status error';
            return;
        }
        
        // Check if URL is properly formatted
        if (!url.startsWith('http://') && !url.startsWith('https://')) {
            statusSpan.textContent = 'URL must start with http:// or https://';
            statusSpan.className = 'connection-status error';
            return;
        }
        
        // Clean up the URL by removing trailing slashes
        url = url.trim().replace(/\/+$/, '');
        
        // Make the API request to test the connection
        fetch(`/api/${appName}/test-connection`, {
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
                return response.json().then(errorData => {
                    throw new Error(errorData.message || this.getConnectionErrorMessage(response.status));
                }).catch(() => {
                    // Fallback if response body is not JSON or empty
                    throw new Error(this.getConnectionErrorMessage(response.status));
                });
            }
            return response.json();
        })
        .then(data => {
            console.log(`Connection test response data for ${appName} instance ${instanceId}:`, data);
            if (data.success) {
                statusSpan.textContent = data.message || 'Connected';
                statusSpan.className = 'connection-status success';
                
                // If a version was returned, display it
                if (data.version) {
                    statusSpan.textContent += ` (v${data.version})`;
                }
            } else {
                statusSpan.textContent = data.message || 'Failed';
                statusSpan.className = 'connection-status error';
            }
        })
        .catch(error => {
            console.error(`Error testing connection for ${appName} instance ${instanceId}:`, error);
            
            // Extract the most relevant part of the error message
            let errorMessage = error.message || 'Unknown error';
            if (errorMessage.includes('Name or service not known')) {
                errorMessage = 'Unable to resolve hostname. Check the URL.';
            } else if (errorMessage.includes('Connection refused')) {
                errorMessage = 'Connection refused. Check that the service is running.';
            } else if (errorMessage.includes('connect ETIMEDOUT') || errorMessage.includes('timeout')) {
                errorMessage = 'Connection timed out. Check URL and port.';
            } else if (errorMessage.includes('401') || errorMessage.includes('Authentication failed')) {
                errorMessage = 'Invalid API key';
            } else if (errorMessage.includes('404') || errorMessage.includes('not found')) {
                errorMessage = 'URL endpoint not found. Check the URL.';
            } else if (errorMessage.startsWith('HTTP error!')) {
                errorMessage = 'Connection failed. Check URL and port.';
            }
            
            statusSpan.textContent = errorMessage;
            statusSpan.className = 'connection-status error';
        });
    },
    
    // Helper function to translate HTTP error codes to user-friendly messages
    getConnectionErrorMessage: function(status) {
        switch(status) {
            case 400:
                return 'Invalid request. Check URL format.';
            case 401:
                return 'Invalid API key';
            case 403:
                return 'Access forbidden. Check permissions.';
            case 404:
                return 'Service not found at this URL. Check address.';
            case 500:
                return 'Server error. Check if the service is working properly.';
            case 502:
                return 'Bad gateway. Check network connectivity.';
            case 503:
                return 'Service unavailable. Check if the service is running.';
            case 504:
                return 'Gateway timeout. Check network connectivity.';
            default:
                return `Connection error. Check URL and port.`;
        }
    },
    
    // App connections
    checkAppConnections: function() {
        this.checkAppConnection('sonarr');
        this.checkAppConnection('radarr');
        this.checkAppConnection('lidarr');
        this.checkAppConnection('readarr'); // Added readarr
        this.checkAppConnection('whisparr'); // Added whisparr
    },
    
    checkAppConnection: function(app) {
        fetch(`/api/status/${app}`)
            .then(response => response.json())
            .then(data => {
                // Pass the whole data object for all apps
                this.updateConnectionStatus(app, data); 

                // Still update the configuredApps flag for potential other uses, but after updating status
                this.configuredApps[app] = data.configured === true; // Ensure it's a boolean
            })
            .catch(error => {
                console.error(`Error checking ${app} connection:`, error);
                // Pass a default 'not configured' status object on error
                this.updateConnectionStatus(app, { configured: false, connected: false }); 
            });
    },
    
    updateConnectionStatus: function(app, statusData) {
        const statusElement = this.elements[`${app}HomeStatus`];
        if (!statusElement) return;

        // Find the parent container for the whole app status box
        const appBox = statusElement.closest('.app-stats-card'); // CORRECTED SELECTOR
        if (!appBox) {
            // If the card structure changes, this might fail. Log a warning.
            console.warn(`[huntarrUI] Could not find parent '.app-stats-card' element for ${app}`);
        }

        let isConfigured = false;
        let isConnected = false;

        // Try to determine configured and connected status from statusData object
        // Default to false if properties are missing
        isConfigured = statusData?.configured === true;
        isConnected = statusData?.connected === true;

        // Special handling for Sonarr's multi-instance connected count
        let sonarrConnectedCount = statusData?.connected_count ?? 0;
        let sonarrTotalConfigured = statusData?.total_configured ?? 0;
        if (app === 'sonarr') {
            isConfigured = sonarrTotalConfigured > 0;
            // For Sonarr, 'isConnected' means at least one instance is connected
            isConnected = isConfigured && sonarrConnectedCount > 0; 
        }

        // --- Visibility Logic --- 
        if (isConfigured) {
            // Ensure the box is visible
            if (appBox) appBox.style.display = ''; 
        } else {
            // Not configured - HIDE the box
            if (appBox) appBox.style.display = 'none';
            // Update badge even if hidden (optional, but good practice)
            statusElement.className = 'status-badge not-configured';
            statusElement.innerHTML = '<i class="fas fa-times-circle"></i> Not Configured';
            return; // No need to update badge further if not configured
        }

        // --- Badge Update Logic (only runs if configured) ---
        if (app === 'sonarr') {
            // Sonarr specific badge text (already checked isConfigured)
            statusElement.innerHTML = `<i class="fas fa-plug"></i> Connected ${sonarrConnectedCount}/${sonarrTotalConfigured}`;
            if (sonarrConnectedCount > 0) {
                if (sonarrConnectedCount < sonarrTotalConfigured) {
                    statusElement.className = 'status-badge partially-connected';
                } else {
                    statusElement.className = 'status-badge connected';
                }
            } else {
                statusElement.className = 'status-badge not-connected';
            }
        } else {
            // Standard badge update for other configured apps
            if (isConnected) {
                statusElement.className = 'status-badge connected';
                statusElement.innerHTML = '<i class="fas fa-check-circle"></i> Connected';
            } else {
                statusElement.className = 'status-badge not-connected';
                statusElement.innerHTML = '<i class="fas fa-times-circle"></i> Not Connected';
            }
        }
    },
    
    // User actions
    startHunt: function() {
        fetch('/api/hunt/start', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.showNotification('Hunt started successfully', 'success');
                } else {
                    this.showNotification('Failed to start hunt', 'error');
                }
            })
            .catch(error => {
                console.error('Error starting hunt:', error);
                this.showNotification('Error starting hunt', 'error');
            });
    },
    
    stopHunt: function() {
        fetch('/api/hunt/stop', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.showNotification('Hunt stopped successfully', 'success');
                } else {
                    this.showNotification('Failed to stop hunt', 'error');
                }
            })
            .catch(error => {
                console.error('Error stopping hunt:', error);
                this.showNotification('Error stopping hunt', 'error');
            });
    },
    
    // User
    loadUsername: function() {
        const usernameElement = document.getElementById('username');
        if (!usernameElement) return;
        
        fetch('/api/user/info')
            .then(response => response.json())
            .then(data => {
                if (data.username) {
                    usernameElement.textContent = data.username;
                }
            })
            .catch(error => {
                console.error('Error loading username:', error);
            });
    },
    
    logout: function(e) { // Added logout function
        e.preventDefault(); // Prevent default link behavior
        console.log('[huntarrUI] Logging out...');
        fetch('/logout', { // Use the correct endpoint defined in Flask
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('[huntarrUI] Logout successful, redirecting to login.');
                window.location.href = '/login'; // Redirect to login page
            } else {
                console.error('[huntarrUI] Logout failed:', data.message);
                this.showNotification('Logout failed. Please try again.', 'error');
            }
        })
        .catch(error => {
            console.error('Error during logout:', error);
            this.showNotification('An error occurred during logout.', 'error');
        });
    },
    
    // Media statistics handling
    loadMediaStats: function() {
        fetch('/api/stats')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.success && data.stats) {
                    this.updateStatsDisplay(data.stats);
                } else {
                    console.error('Failed to load statistics:', data.message || 'Unknown error');
                }
            })
            .catch(error => {
                console.error('Error fetching statistics:', error);
            });
    },
    
    updateStatsDisplay: function(stats) {
        // Update each app's statistics
        const apps = ['sonarr', 'radarr', 'lidarr', 'readarr', 'whisparr'];
        const statTypes = ['hunted', 'upgraded'];
        
        apps.forEach(app => {
            if (stats[app]) {
                statTypes.forEach(type => {
                    const element = document.getElementById(`${app}-${type}`);
                    if (element) {
                        // Animate the number change
                        this.animateNumber(element, parseInt(element.textContent), stats[app][type] || 0);
                    }
                });
            }
        });
    },
    
    animateNumber: function(element, start, end) {
        const duration = 1000; // Animation duration in milliseconds
        const startTime = performance.now();
        
        const updateNumber = (currentTime) => {
            const elapsedTime = currentTime - startTime;
            const progress = Math.min(elapsedTime / duration, 1);
            
            // Easing function for smooth animation
            const easeOutQuad = progress * (2 - progress);
            
            const currentValue = Math.floor(start + (end - start) * easeOutQuad);
            element.textContent = currentValue;
            
            if (progress < 1) {
                requestAnimationFrame(updateNumber);
            } else {
                element.textContent = end; // Ensure we end with the exact target number
            }
        };
        
        requestAnimationFrame(updateNumber);
    },
    
    resetMediaStats: function(appType = null) {
        const confirmMessage = appType 
            ? `Are you sure you want to reset statistics for ${appType}?` 
            : 'Are you sure you want to reset all media statistics?';
            
        if (!confirm(confirmMessage)) {
            return;
        }
        
        const requestBody = appType ? { app_type: appType } : {};
        
        fetch('/api/stats/reset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showNotification(data.message, 'success');
                this.loadMediaStats(); // Refresh the stats display
            } else {
                this.showNotification(data.message || 'Failed to reset statistics', 'error');
            }
        })
        .catch(error => {
            console.error('Error resetting statistics:', error);
            this.showNotification('Error resetting statistics', 'error');
        });
    },
    
    // Utility functions
    showNotification: function(message, type) {
        // Create a notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        // Add to the document
        document.body.appendChild(notification);
        
        // Ensure any existing notification is removed first to prevent stacking
        const existingNotifications = document.querySelectorAll('.notification');
        existingNotifications.forEach(n => {
            if (n !== notification) {
                n.classList.remove('show');
                setTimeout(() => n.remove(), 300);
            }
        });
        
        // Fade in
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        // Remove after a delay
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    },
    
    capitalizeFirst: function(string) {
        return string.charAt(0).toUpperCase() + string.slice(1);
    },

    // Add or modify this function to handle enabling/disabling save/reset
    updateSaveResetButtonState(enable) { // Changed signature
        const saveButton = this.elements.saveSettingsButton;

        if (saveButton) {
            saveButton.disabled = !enable;
            // Optional: Add/remove class for styling
            if (enable) {
                saveButton.classList.remove('disabled-button');
            } else {
                saveButton.classList.add('disabled-button');
            }
        }
    },

    // Add updateHomeConnectionStatus if it doesn't exist or needs adjustment
    updateHomeConnectionStatus: function() {
        console.log('[huntarrUI] Updating home connection statuses...');
        // This function should ideally call checkAppConnection for all relevant apps
        // or use the stored configuredApps status if checkAppConnection updates it.
        this.checkAppConnections(); // Re-check all connections after a save might be simplest
    },
};

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', () => {
    huntarrUI.init();
    
    // Add event listeners for media statistics buttons
    const refreshStatsButton = document.getElementById('refresh-stats');
    if (refreshStatsButton) {
        refreshStatsButton.addEventListener('click', () => {
            huntarrUI.loadMediaStats();
        });
    }
    
    const resetStatsButton = document.getElementById('reset-stats');
    if (resetStatsButton) {
        resetStatsButton.addEventListener('click', () => {
            huntarrUI.resetMediaStats();
        });
    }
    
    // Restore logo from session storage if available
    const cachedLogoSrc = sessionStorage.getItem('huntarr-logo-src');
    if (cachedLogoSrc) {
        const logoImg = document.querySelector('.sidebar .logo');
        if (logoImg) {
            logoImg.src = cachedLogoSrc;
        }
    }
    
    // Also apply logo on page load
    if (typeof window.applyLogoToAllElements === 'function') {
        window.applyLogoToAllElements();
    }
});

// Expose huntarrUI to the global scope for access by app modules
window.huntarrUI = huntarrUI;
