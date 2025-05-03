/**
 * Huntarr - New UI Implementation
 * Main JavaScript file for handling UI interactions and API communication
 */

let huntarrUI = {
    // Current state
    eventSources: {},
    currentSection: 'home', // Default section
    currentLogApp: 'all', // Default log app
    currentHistoryApp: 'all', // Default history app
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

        const resetButton = document.getElementById('reset-stats');
        if (resetButton) {
            resetButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.resetMediaStats();
            });
        }
        // Ensure logo is visible immediately
        this.logoUrl = localStorage.getItem('huntarr-logo-url') || this.logoUrl;
        
        this.cacheElements();
        this.setupEventListeners();
        this.loadUsername();
        this.checkLocalAccessBypassStatus(); // Add this line
        this.checkAppConnections();
        this.loadMediaStats(); // Load media statistics
        this.loadCurrentVersion(); // Load current version
        this.loadLatestVersion(); // Load latest version from GitHub
        this.loadGitHubStarCount(); // Load GitHub star count
        
        // Preload stateful management info so it's ready when needed
        this.loadStatefulInfo();
        
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
        this.elements.historyNav = document.getElementById('historyNav');
        this.elements.settingsNav = document.getElementById('settingsNav');
        this.elements.userNav = document.getElementById('userNav');
        
        // Sections
        this.elements.sections = document.querySelectorAll('.content-section');
        this.elements.homeSection = document.getElementById('homeSection');
        this.elements.logsSection = document.getElementById('logsSection');
        this.elements.historySection = document.getElementById('historySection');
        this.elements.settingsSection = document.getElementById('settingsSection');
        
        // App tabs & Settings Tabs
        this.elements.appTabs = document.querySelectorAll('.app-tab'); // For logs section
        this.elements.logOptions = document.querySelectorAll('.log-option'); // New: replaced logTabs with logOptions
        this.elements.currentLogApp = document.getElementById('current-log-app'); // New: dropdown current selection text
        this.elements.logDropdownBtn = document.querySelector('.log-dropdown-btn'); // New: dropdown toggle button
        this.elements.logDropdownContent = document.querySelector('.log-dropdown-content'); // New: dropdown content
        
        // History dropdown elements
        this.elements.historyOptions = document.querySelectorAll('.history-option'); // History dropdown options
        this.elements.currentHistoryApp = document.getElementById('current-history-app'); // Current history app text
        this.elements.historyDropdownBtn = document.querySelector('.history-dropdown-btn'); // History dropdown button
        this.elements.historyDropdownContent = document.querySelector('.history-dropdown-content'); // History dropdown content
        this.elements.historyPlaceholderText = document.getElementById('history-placeholder-text'); // Placeholder text for history
        
        // Settings dropdown elements
        this.elements.settingsOptions = document.querySelectorAll('.settings-option'); // New: settings dropdown options
        this.elements.currentSettingsApp = document.getElementById('current-settings-app'); // New: current settings app text
        this.elements.settingsDropdownBtn = document.querySelector('.settings-dropdown-btn'); // New: settings dropdown button
        this.elements.settingsDropdownContent = document.querySelector('.settings-dropdown-content'); // New: dropdown content
        
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
            item.addEventListener('click', (e) => this.handleNavigation(e));
        });
        
        // Log auto-scroll setting
        if (this.elements.autoScrollCheckbox) {
            this.elements.autoScrollCheckbox.addEventListener('change', (e) => {
                this.autoScroll = e.target.checked;
            });
        }
        
        // Clear logs button
        if (this.elements.clearLogsButton) {
            this.elements.clearLogsButton.addEventListener('click', () => this.clearLogs());
        }
        
        // App tabs in logs section
        this.elements.appTabs.forEach(tab => {
            tab.addEventListener('click', (e) => this.handleAppTabChange(e));
        });
        
        // Log options dropdown
        this.elements.logOptions.forEach(option => {
            option.addEventListener('click', (e) => this.handleLogOptionChange(e));
        });
        
        // Log dropdown toggle
        if (this.elements.logDropdownBtn) {
            this.elements.logDropdownBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.elements.logDropdownContent.classList.toggle('show');
            });
            
            // Close dropdown when clicking outside
            document.addEventListener('click', (e) => {
                if (!e.target.closest('.log-dropdown') && this.elements.logDropdownContent.classList.contains('show')) {
                    this.elements.logDropdownContent.classList.remove('show');
                }
            });
        }
        
        // History dropdown toggle
        if (this.elements.historyDropdownBtn) {
            this.elements.historyDropdownBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.elements.historyDropdownContent.classList.toggle('show');
            });
            
            // Close dropdown when clicking outside
            document.addEventListener('click', (e) => {
                if (!e.target.closest('.history-dropdown') && this.elements.historyDropdownContent.classList.contains('show')) {
                    this.elements.historyDropdownContent.classList.remove('show');
                }
            });
        }
        
        // History options
        this.elements.historyOptions.forEach(option => {
            option.addEventListener('click', (e) => this.handleHistoryOptionChange(e));
        });
        
        // Settings dropdown toggle
        if (this.elements.settingsDropdownBtn) {
            this.elements.settingsDropdownBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.elements.settingsDropdownContent.classList.toggle('show');
            });
            
            // Close dropdown when clicking outside
            document.addEventListener('click', (e) => {
                if (!e.target.closest('.settings-dropdown') && this.elements.settingsDropdownContent.classList.contains('show')) {
                    this.elements.settingsDropdownContent.classList.remove('show');
                }
            });
        }
        
        // Settings options
        this.elements.settingsOptions.forEach(option => {
            option.addEventListener('click', (e) => this.handleSettingsOptionChange(e));
        });
        
        // Save settings button
        if (this.elements.saveSettingsButton) {
            this.elements.saveSettingsButton.addEventListener('click', () => this.saveSettings());
        }
        
        // Start hunt button
        if (this.elements.startHuntButton) {
            this.elements.startHuntButton.addEventListener('click', () => this.startHunt());
        }
        
        // Stop hunt button
        if (this.elements.stopHuntButton) {
            this.elements.stopHuntButton.addEventListener('click', () => this.stopHunt());
        }
        
        // Logout button
        if (this.elements.logoutLink) {
            this.elements.logoutLink.addEventListener('click', (e) => this.logout(e));
        }
        
        // Dark mode toggle
        const darkModeToggle = document.getElementById('darkModeToggle');
        if (darkModeToggle) {
            const prefersDarkMode = localStorage.getItem('huntarr-dark-mode') === 'true';
            darkModeToggle.checked = prefersDarkMode;
            
            darkModeToggle.addEventListener('change', function() {
                const isDarkMode = this.checked;
                document.body.classList.toggle('dark-theme', isDarkMode);
                localStorage.setItem('huntarr-dark-mode', isDarkMode);
            });
        }
        
        // Settings inputs change tracking
        document.querySelectorAll('#settingsSection input, #settingsSection select').forEach(element => {
            element.addEventListener('change', () => this.markSettingsAsChanged());
        });
        
        // Monitor for window beforeunload to warn about unsaved settings
        window.addEventListener('beforeunload', (e) => {
            if (this.settingsChanged && this.hasFormChanges(this.currentSettingsTab)) {
                // Standard way to show a confirmation dialog when navigating away
                e.preventDefault();
                e.returnValue = ''; // Chrome requires returnValue to be set
                return ''; // Legacy browsers
            }
        });
        
        // Stateful management reset button
        const resetStatefulBtn = document.getElementById('reset_stateful_btn');
        if (resetStatefulBtn) {
            resetStatefulBtn.addEventListener('click', () => this.resetStatefulManagement());
        }
        
        // Stateful management hours input
        const statefulHoursInput = document.getElementById('stateful_management_hours');
        if (statefulHoursInput) {
            statefulHoursInput.addEventListener('change', () => {
                this.updateStatefulExpirationOnUI();
            });
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
        const targetElement = e.currentTarget; // Get the clicked nav item
        const href = targetElement.getAttribute('href');
        const target = targetElement.getAttribute('target');
        
        // Allow links with target="_blank" to open in a new window (return early)
        if (target === '_blank') {
            return; // Let the default click behavior happen
        }
        
        // For all other links, prevent default behavior and handle internally
        e.preventDefault();

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
            // Use our new comparison function to check if there are actual changes
            const hasRealChanges = this.hasFormChanges(this.currentSettingsTab);
            
            if (hasRealChanges && !confirm('You have unsaved changes. Are you sure you want to leave? Changes will be lost.')) {
                return; // Stop navigation if user cancels
            }
            
            // User confirmed or no real changes, reset flag before navigating
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
        } else if (section === 'history' && this.elements.historySection) {
            this.elements.historySection.classList.add('active');
            if (this.elements.historyNav) this.elements.historyNav.classList.add('active');
            newTitle = 'History';
            this.currentSection = 'history';
            // Disconnect logs if switching away from logs
            this.disconnectAllEventSources(); 
        } else if (section === 'apps' && document.getElementById('appsSection')) {
            document.getElementById('appsSection').classList.add('active');
            if (document.getElementById('appsNav')) document.getElementById('appsNav').classList.add('active');
            newTitle = 'Apps';
            this.currentSection = 'apps';
            // Disconnect logs if switching away from logs
            this.disconnectAllEventSources();
            
            // Load apps if the apps module exists
            if (typeof appsModule !== 'undefined') {
                appsModule.loadApps();
            }
        } else if (section === 'settings' && this.elements.settingsSection) {
            this.elements.settingsSection.classList.add('active');
            if (this.elements.settingsNav) this.elements.settingsNav.classList.add('active');
            newTitle = 'Settings';
            this.currentSection = 'settings';
            
            // Ensure default settings tab is set if none is active
            if (!this.currentSettingsTab) {
                this.currentSettingsTab = 'general'; // Default to general tab
                
                // Set the general tab as active
                const generalTab = document.querySelector('.settings-tab[data-app="general"]');
                if (generalTab) {
                    this.elements.settingsTabs.forEach(t => {
                        t.classList.remove('active');
                    });
                    generalTab.classList.add('active');
                    
                    // Also set the general panel as visible
                    this.elements.appSettingsPanels.forEach(panel => {
                        panel.classList.remove('active');
                        panel.style.display = 'none';
                    });
                    
                    const generalPanel = document.getElementById('generalSettings');
                    if (generalPanel) {
                        generalPanel.classList.add('active');
                        generalPanel.style.display = 'block';
                    }
                }
            }
            
            // Load stateful info immediately, don't wait for loadAllSettings to complete
            this.loadStatefulInfo();
            
            // Load all settings after stateful info has started loading
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
    
    // Log option dropdown handling
    handleLogOptionChange: function(e) {
        e.preventDefault(); // Prevent default anchor behavior
        
        const app = e.target.getAttribute('data-app');
        if (!app || app === this.currentLogApp) return; // Do nothing if same tab clicked
        
        // Update active option
        this.elements.logOptions.forEach(option => {
            option.classList.remove('active');
        });
        e.target.classList.add('active');
        
        // Update the current log app text with proper capitalization
        let displayName = app.charAt(0).toUpperCase() + app.slice(1);
        // Special handling for Whisparr V2
        if (app === 'whisparr') {
            displayName = 'Whisparr V2';
        }
        this.elements.currentLogApp.textContent = displayName;
        
        // Close the dropdown
        this.elements.logDropdownContent.classList.remove('show');
        
        // Switch to the selected app logs
        this.currentLogApp = app;
        this.clearLogs(); // Clear existing logs before switching
        this.connectToLogs(); // Reconnect to the new log source
    },
    
    // History option dropdown handling
    handleHistoryOptionChange: function(e) {
        e.preventDefault(); // Prevent default anchor behavior
        
        const app = e.target.getAttribute('data-app');
        if (!app || app === this.currentHistoryApp) return; // Do nothing if same tab clicked
        
        // Update active option
        this.elements.historyOptions.forEach(option => {
            option.classList.remove('active');
        });
        e.target.classList.add('active');
        
        // Update the current history app text with proper capitalization
        let displayName = app.charAt(0).toUpperCase() + app.slice(1);
        this.elements.currentHistoryApp.textContent = displayName;
        
        // Close the dropdown
        this.elements.historyDropdownContent.classList.remove('show');
        
        // Switch to the selected app history
        this.currentHistoryApp = app;
        // this.clearHistory(); // Clear existing history before switching
        // this.connectToHistory(); // Reconnect to the new history source
        
        // Update the placeholder text based on the selected app
        this.updateHistoryPlaceholder(app);
    },
    
    // Update the history placeholder text based on the selected app
    updateHistoryPlaceholder: function(app) {
        if (!this.elements.historyPlaceholderText) return;
        
        let message = "";
        if (app === 'all') {
            message = "The History feature will be available in a future update. Stay tuned for enhancements that will allow you to view your media processing history.";
        } else {
            let displayName = this.capitalizeFirst(app);
            message = `The ${displayName} History feature is under development and will be available in a future update. You'll be able to track your ${displayName} media processing history here.`;
        }
        
        this.elements.historyPlaceholderText.textContent = message;
    },
    
    // Settings option handling
    handleSettingsOptionChange: function(e) {
        e.preventDefault(); // Prevent default anchor behavior
        
        const app = e.target.getAttribute('data-app');
        if (!app || app === this.currentSettingsApp) return; // Do nothing if same tab clicked
        
        // Update active option
        this.elements.settingsOptions.forEach(option => {
            option.classList.remove('active');
        });
        e.target.classList.add('active');
        
        // Update the current settings app text with proper capitalization
        let displayName = app.charAt(0).toUpperCase() + app.slice(1);
        this.elements.currentSettingsApp.textContent = displayName;
        
        // Close the dropdown
        this.elements.settingsDropdownContent.classList.remove('show');
        
        // Hide all settings panels
        this.elements.appSettingsPanels.forEach(panel => {
            panel.classList.remove('active');
            panel.style.display = 'none';
        });
        
        // Show the selected app's settings panel
        const selectedPanel = document.getElementById(app + 'Settings');
        if (selectedPanel) {
            selectedPanel.classList.add('active');
            selectedPanel.style.display = 'block';
        }
        
        this.currentSettingsTab = app;
        console.log(`[huntarrUI] Switched settings tab to: ${this.currentSettingsTab}`); // Added logging
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
                    const logString = event.data;
                    // Regex to parse log lines: Optional [APP], Timestamp, Logger, Level, Message
                    // Example: [SONARR] 2024-01-01 12:00:00 - huntarr.sonarr - INFO - Message content
                    // Example: 2024-01-01 12:00:00 - huntarr - DEBUG - System message
                    const logRegex = /^(?:\\[(\\w+)\\]\\s)?([\\d\\-]+\\s[\\d:]+)\\s-\\s([\\w\\.]+)\\s-\\s(\\w+)\\s-\\s(.*)$/;
                    const match = logString.match(logRegex);

                    // First determine the app type for this log message
                    let logAppType = 'system'; // Default to system
                    
                    if (match && match[1]) {
                        // If we have a match with app tag like [SONARR], use that
                        logAppType = match[1].toLowerCase();
                    } else if (match && match[3]) {
                        // Otherwise try to determine from the logger name (e.g., huntarr.sonarr)
                        const loggerParts = match[3].split('.');
                        if (loggerParts.length > 1) {
                            const possibleApp = loggerParts[1].toLowerCase();
                            if (['sonarr', 'radarr', 'lidarr', 'readarr', 'whisparr', 'swaparr'].includes(possibleApp)) {
                                logAppType = possibleApp;
                            }
                        }
                    }
                    
                    // Special case for system logs that may contain app-specific patterns
                    if (logAppType === 'system') {
                        // App-specific patterns that may appear in system logs
                        const patterns = {
                            'sonarr': ['episode', 'series', 'tv show', 'sonarr'],
                            'radarr': ['movie', 'film', 'radarr'],
                            'lidarr': ['album', 'artist', 'track', 'music', 'lidarr'],
                            'readarr': ['book', 'author', 'readarr'],
                            'whisparr': ['scene', 'adult', 'whisparr'],
                            'swaparr': ['added strike', 'max strikes reached', 'would have removed', 'strikes, removing download', 'processing stalled downloads', 'swaparr']
                        };
                        
                        // Check each app's patterns
                        for (const [app, appPatterns] of Object.entries(patterns)) {
                            if (appPatterns.some(pattern => logString.toLowerCase().includes(pattern))) {
                                logAppType = app;
                                break;
                            }
                        }
                    }

                    // Determine if this log should be displayed based on the selected app tab
                    const shouldDisplay = 
                        this.currentLogApp === 'all' || 
                        this.currentLogApp === logAppType;

                    if (!shouldDisplay) return;

                    const logEntry = document.createElement('div');
                    logEntry.className = 'log-entry';

                    if (match) {
                        const [, appName, timestamp, loggerName, level, message] = match;
                        
                        logEntry.innerHTML = ` 
                            <span class="log-timestamp" title="${timestamp}">${timestamp.split(' ')[1]}</span> 
                            ${appName ? `<span class="log-app" title="Source: ${appName}">[${appName}]</span>` : ''}
                            <span class="log-level log-level-${level.toLowerCase()}" title="Level: ${level}">${level}</span>
                            <span class="log-logger" title="Logger: ${loggerName}">(${loggerName.replace('huntarr.', '')})</span>
                            <span class="log-message">${message}</span>
                        `;
                        logEntry.classList.add(`log-${level.toLowerCase()}`);
                    } else {
                        // Fallback for lines that don't match the expected format
                        logEntry.innerHTML = `<span class="log-message">${logString}</span>`;
                        
                        // Basic level detection for fallback
                        if (logString.includes('ERROR')) logEntry.classList.add('log-error');
                        else if (logString.includes('WARN') || logString.includes('WARNING')) logEntry.classList.add('log-warning');
                        else if (logString.includes('DEBUG')) logEntry.classList.add('log-debug');
                        else logEntry.classList.add('log-info');
                    }
                    
                    // Add to logs container
                    this.elements.logsContainer.appendChild(logEntry);
                    
                    // Special event dispatching for Swaparr logs
                    if (logAppType === 'swaparr' && this.currentLogApp === 'swaparr') {
                        // Dispatch a custom event for swaparr.js to process
                        const swaparrEvent = new CustomEvent('swaparrLogReceived', {
                            detail: {
                                logData: match && match[5] ? match[5] : logString
                            }
                        });
                        document.dispatchEvent(swaparrEvent);
                    }
                    
                    // Auto-scroll to bottom if enabled
                    if (this.autoScroll) {
                        this.elements.logsContainer.scrollTop = this.elements.logsContainer.scrollHeight;
                    }
                } catch (error) {
                    console.error('[huntarrUI] Error processing log message:', error, 'Data:', event.data);
                }
            };
            
            eventSource.onerror = (err) => {
                console.error(`[huntarrUI] EventSource error for app ${this.currentLogApp}:`, err);
                if (this.elements.logConnectionStatus) {
                    this.elements.logConnectionStatus.textContent = 'Error/Disconnected';
                    this.elements.logConnectionStatus.className = 'status-error'; // Use a specific error class
                }
                // Close the potentially broken connection
                if (this.eventSources.logs) {
                    this.eventSources.logs.close();
                    console.log(`[huntarrUI] Closed potentially broken log EventSource for ${this.currentLogApp}.`);
                }
                // Attempt to reconnect after a delay, but only if still on the logs page
                if (this.currentSection === 'logs') {
                    console.log(`[huntarrUI] Attempting to reconnect log stream for ${this.currentLogApp} in 5 seconds...`);
                    setTimeout(() => {
                        // Double-check if still on logs page before reconnecting
                        if (this.currentSection === 'logs') {
                             console.log(`[huntarrUI] Reconnecting log stream for ${this.currentLogApp}.`);
                             this.connectToLogs(); // Re-initiate connection
                        } else {
                             console.log(`[huntarrUI] Log reconnect cancelled; user navigated away from logs section.`);
                        }
                    }, 5000); // 5-second delay
                }
            }; // Added missing semicolon
            
            this.eventSources.logs = eventSource; // Store the reference
        } catch (e) {
            console.error(`[huntarrUI] Failed to create EventSource for app ${appType}:`, e);
            if (this.elements.logConnectionStatus) {
                this.elements.logConnectionStatus.textContent = 'Failed to connect';
                this.elements.logConnectionStatus.className = 'status-error';
            }
        }
    },
    
    disconnectAllEventSources: function() {
        Object.keys(this.eventSources).forEach(key => {
            const source = this.eventSources[key];
            if (source) {
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
    
    clearLogs: function() {
        if (this.elements.logsContainer) {
            this.elements.logsContainer.innerHTML = '';
        }
    },
    
    // Settings handling
    loadAllSettings: function() {
        // Disable save button until changes are made
        this.updateSaveResetButtonState(false);
        this.settingsChanged = false;
        
        // Get all settings to populate forms
        fetch('/api/settings')
            .then(response => response.json())
            .then(data => {
                console.log('Loaded settings:', data);
                
                // Store original settings for comparison
                this.originalSettings = data;
                
                // Populate each app's settings form
                if (data.sonarr) this.populateSettingsForm('sonarr', data.sonarr);
                if (data.radarr) this.populateSettingsForm('radarr', data.radarr);
                if (data.lidarr) this.populateSettingsForm('lidarr', data.lidarr);
                if (data.readarr) this.populateSettingsForm('readarr', data.readarr);
                if (data.whisparr) this.populateSettingsForm('whisparr', data.whisparr);
                if (data.swaparr) this.populateSettingsForm('swaparr', data.swaparr);
                if (data.general) this.populateSettingsForm('general', data.general);
                
                // Update duration displays (like sleep durations)
                if (typeof SettingsForms !== 'undefined' && 
                    typeof SettingsForms.updateDurationDisplay === 'function') {
                    SettingsForms.updateDurationDisplay();
                }
                
                // Load stateful info immediately, don't wait for loadAllSettings to complete
                this.loadStatefulInfo();
            })
            .catch(error => {
                console.error('Error loading settings:', error);
                this.showNotification('Error loading settings. Please try again.', 'error');
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
                formFunction(form, appSettings); // This function already calls setupInstanceManagement internally
                
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
        
        // Clear the unsaved changes flag BEFORE sending the request
        // This prevents the "unsaved changes" dialog from appearing
        this.settingsChanged = false;
        this.updateSaveResetButtonState(false);
        
        // Use getFormSettings for all apps, as it handles different structures
        let settings = this.getFormSettings(app);

        if (!settings) {
            console.error(`[huntarrUI] Failed to collect settings for app: ${app}`);
            this.showNotification('Error collecting settings from form.', 'error');
            return;
        }

        console.log(`[huntarrUI] Collected settings for ${app}:`, settings);
        
        // Check if this is general settings and if local_access_bypass is being changed
        const isLocalAccessBypassChanged = app === 'general' && 
            this.originalSettings && 
            this.originalSettings.general && 
            this.originalSettings.general.local_access_bypass !== settings.local_access_bypass;
            
        console.log(`[huntarrUI] Local access bypass changed: ${isLocalAccessBypassChanged}`);

        console.log(`[huntarrUI] Sending settings payload for ${app}:`, settings);

        // Use the correct endpoint based on app type
        const endpoint = app === 'general' ? '/api/settings/general' : `/api/settings/${app}`;
        
        fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(settings)
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
            
            // If local access bypass setting was changed, reload the page
            if (isLocalAccessBypassChanged) {
                this.showNotification('Settings saved successfully. Reloading page to apply authentication changes...', 'success');
                setTimeout(() => {
                    window.location.href = '/'; // Redirect to home page after a brief delay
                }, 1500);
                return;
            }
            
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
            
            // If general settings were saved, refresh the stateful info display
            if (app === 'general') {
                this.loadStatefulInfo();
            }
        })
        .catch(error => {
            console.error('Error saving settings:', error);
            this.showNotification(`Error saving settings: ${error.message}`, 'error');
            // If there was an error, mark settings as changed again
            this.settingsChanged = true;
            this.updateSaveResetButtonState(true);
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
            console.error(`[huntarrUI] Settings form for ${app} not found.`);
            return null;
        }

        // Special handling for Swaparr which has a different structure
        if (app === 'swaparr') {
            // Get all inputs directly without filtering for instance fields
            const inputs = form.querySelectorAll('input, select');
            inputs.forEach(input => {
                // Extract the field name without the app prefix
                let key = input.id;
                if (key.startsWith(`${app}_`)) {
                    key = key.substring(app.length + 1);
                }
                
                // Store the value based on input type
                if (input.type === 'checkbox') {
                    settings[key] = input.checked;
                } else if (input.type === 'number') {
                    settings[key] = input.value === '' ? null : parseInt(input.value, 10);
                } else {
                    settings[key] = input.value.trim();
                }
            });
            
            console.log(`[huntarrUI] Collected Swaparr settings:`, settings);
            return settings;
        }

        // Handle apps that use instances (Sonarr, Radarr, etc.)
        // Get all instance items in the form
        const instanceItems = form.querySelectorAll('.instance-item');
        settings.instances = [];
        
        // Check if multi-instance UI elements exist (like Sonarr)
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
            // Handle special case for Whisparr version
            if (input.id === 'whisparr_version') {
                if (app === 'whisparr') {
                    settings['whisparr_version'] = input.value.trim();
                    return; // Skip further processing for this field
                }
            }

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
        console.log("DEBUG: setupInstanceEventHandlers called"); // Added logging
        const settingsPanels = document.querySelectorAll('.app-settings-panel');
        
        settingsPanels.forEach(panel => {
            console.log(`DEBUG: Adding listeners to panel '${panel.id}'`); // Added logging
            panel.addEventListener('addInstance', (e) => {
                console.log(`DEBUG: addInstance event listener fired for panel '${panel.id}'. Event detail:`, e.detail);
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
        console.log(`DEBUG: addAppInstance called for app '${appName}'`);
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
        
        // Check for trailing slashes in URL
        if (url.endsWith('/') || url.endsWith('\\')) {
            statusSpan.textContent = 'Remove trailing slash from URL (/ or \\)';
            statusSpan.className = 'status-error';
            return;
        }
        
        // Clean up the URL by removing trailing slashes (redundant but kept for safety)
        url = url.trim().replace(/[/\\]+$/, '');
        
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

        // Special handling for *arr apps' multi-instance connected count
        let connectedCount = statusData?.connected_count ?? 0;
        let totalConfigured = statusData?.total_configured ?? 0;
        
        // For all *arr apps, 'isConfigured' means at least one instance is configured
        if (['sonarr', 'radarr', 'lidarr', 'readarr', 'whisparr'].includes(app)) {
            isConfigured = totalConfigured > 0;
            // For *arr apps, 'isConnected' means at least one instance is connected
            isConnected = isConfigured && connectedCount > 0; 
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
        if (['sonarr', 'radarr', 'lidarr', 'readarr', 'whisparr'].includes(app)) {
            // *Arr specific badge text (already checked isConfigured)
            statusElement.innerHTML = `<i class="fas fa-plug"></i> Connected ${connectedCount}/${totalConfigured}`;
            statusElement.className = 'status-badge ' + (isConnected ? 'connected' : 'error');
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
                
                // Check if local access bypass is enabled and update UI visibility
                this.checkLocalAccessBypassStatus();
            })
            .catch(error => {
                console.error('Error loading username:', error);
                
                // Still check local access bypass status even if username loading failed
                this.checkLocalAccessBypassStatus();
            });
    },
    
    // Check if local access bypass is enabled and update UI accordingly
    checkLocalAccessBypassStatus: function() {
        console.log("Checking local access bypass status...");
        fetch('/api/get_local_access_bypass_status') // Corrected URL
            .then(response => {
                if (!response.ok) {
                    // Log error if response is not OK (e.g., 404, 500)
                    console.error(`Error fetching bypass status: ${response.status} ${response.statusText}`);
                    // Attempt to read response body for more details, if available
                    response.text().then(text => console.error('Response body:', text));
                    // Throw an error to trigger the catch block with a clearer message
                    throw new Error(`HTTP error ${response.status}`); 
                }
                return response.json(); // Only parse JSON if response is OK
            })
            .then(data => {
                if (data && typeof data.isEnabled === 'boolean') {
                    console.log("Local access bypass status received:", data.isEnabled);
                    this.updateUIForLocalAccessBypass(data.isEnabled);
                } else {
                    // Handle cases where response is JSON but not the expected format
                    console.error('Invalid data format received for bypass status:', data);
                    this.updateUIForLocalAccessBypass(false); // Default to disabled/showing elements
                }
            })
            .catch(error => {
                 // Catch network errors and the error thrown from !response.ok
                console.error('Error checking local access bypass status:', error);
                // Default to showing elements if we can't determine status
                this.updateUIForLocalAccessBypass(false);
            });
    },
    
    // Update UI elements visibility based on local access bypass status
    updateUIForLocalAccessBypass: function(isEnabled) {
        console.log("Updating UI for local access bypass:", isEnabled);
        
        // Get the user info container in topbar (username and logout button)
        const userInfoContainer = document.getElementById('userInfoContainer');
        
        // Get the user nav item in sidebar
        const userNav = document.getElementById('userNav');
        
        // Set display style explicitly based on local access bypass setting
        if (isEnabled === true) {
            console.log("Local access bypass is ENABLED - hiding user elements");
            
            // Hide user info in topbar
            if (userInfoContainer) {
                userInfoContainer.style.display = 'none';
                console.log("  • Hidden userInfoContainer");
            } else {
                console.warn("  ⚠ userInfoContainer not found");
            }
            
            // Hide user nav in sidebar
            if (userNav) {
                userNav.style.display = 'none';
                console.log("  • Hidden userNav");
            } else {
                console.warn("  ⚠ userNav not found");
            }
        } else {
            console.log("Local access bypass is DISABLED - showing user elements");
            
            // Show user info in topbar
            if (userInfoContainer) {
                userInfoContainer.style.display = '';
                console.log("  • Showing userInfoContainer");
            } else {
                console.warn("  ⚠ userInfoContainer not found");
            }
            
            // Show user nav in sidebar
            if (userNav) {
                userNav.style.display = '';
                console.log("  • Showing userNav");
            } else {
                console.warn("  ⚠ userNav not found");
            }
        }
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
        // Directly update the UI first to provide immediate feedback
        const stats = {
            'sonarr': {'hunted': 0, 'upgraded': 0},
            'radarr': {'hunted': 0, 'upgraded': 0},
            'lidarr': {'hunted': 0, 'upgraded': 0},
            'readarr': {'hunted': 0, 'upgraded': 0},
            'whisparr': {'hunted': 0, 'upgraded': 0}
        };
        
        // Immediately update UI before even showing the confirmation
        if (appType) {
            // Only reset the specific app's stats
            this.updateStatsDisplay({
                [appType]: stats[appType]
            });
        } else {
            // Reset all stats
            this.updateStatsDisplay(stats);
        }
        
        // Show a success notification
        this.showNotification('Statistics reset successfully', 'success');
        
        // Try to send the reset to the server, but don't depend on it
        try {
            const requestBody = appType ? { app_type: appType } : {};
            
            fetch('/api/stats/reset', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestBody)
            })
            .then(response => {
                // Just log the response, don't rely on it for UI feedback
                if (!response.ok) {
                    console.warn('Server responded with non-OK status for stats reset');
                }
                return response.json().catch(() => ({}));
            })
            .then(data => {
                console.log('Stats reset response:', data);
            })
            .catch(error => {
                console.warn('Error communicating with server for stats reset:', error);
            });
        } catch (error) {
            console.warn('Error in stats reset:', error);
        }
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

    // Load current version from version.txt
    loadCurrentVersion: function() {
        fetch('/version.txt')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to load version.txt');
                }
                return response.text();
            })
            .then(version => {
                const versionElement = document.getElementById('version-value');
                if (versionElement) {
                    versionElement.textContent = version.trim();
                }
            })
            .catch(error => {
                console.error('Error loading current version:', error);
                const versionElement = document.getElementById('version-value');
                if (versionElement) {
                    versionElement.textContent = 'Error';
                }
            });
    },

    // Load latest version from GitHub releases
    loadLatestVersion: function() {
        fetch('https://api.github.com/repos/plexguide/Huntarr.io/releases/latest')
            .then(response => {
                if (!response.ok) {
                    // Handle rate limiting or other errors
                    if (response.status === 403) {
                        console.warn('GitHub API rate limit likely exceeded.');
                        throw new Error('Rate limited');
                    }
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                const latestVersionElement = document.getElementById('latest-version-value');
                if (latestVersionElement && data && data.tag_name) {
                    // Remove potential 'v' prefix for consistency if needed, or keep it
                    latestVersionElement.textContent = data.tag_name; 
                } else if (latestVersionElement) {
                     latestVersionElement.textContent = 'N/A';
                }
            })
            .catch(error => {
                console.error('Error loading latest version from GitHub:', error);
                const latestVersionElement = document.getElementById('latest-version-value');
                if (latestVersionElement) {
                    latestVersionElement.textContent = error.message === 'Rate limited' ? 'Rate Limited' : 'Error';
                }
            });
    },

    // Load GitHub star count
    loadGitHubStarCount: function() {
        const starsElement = document.getElementById('github-stars-value');
        if (!starsElement) return;
        
        starsElement.textContent = 'Loading...';
        
        // GitHub API endpoint for repository information
        const apiUrl = 'https://api.github.com/repos/plexguide/huntarr';
        
        fetch(apiUrl)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`GitHub API error: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data && data.stargazers_count !== undefined) {
                    // Format the number with commas for thousands
                    const formattedStars = data.stargazers_count.toLocaleString();
                    starsElement.textContent = formattedStars;
                    
                    // Store in localStorage to avoid excessive API requests
                    const cacheData = {
                        stars: data.stargazers_count,
                        timestamp: Date.now()
                    };
                    localStorage.setItem('huntarr-github-stars', JSON.stringify(cacheData));
                } else {
                    throw new Error('Star count not found in response');
                }
            })
            .catch(error => {
                console.error('Error fetching GitHub stars:', error);
                
                // Try to load from cache if we have it
                const cachedData = localStorage.getItem('huntarr-github-stars');
                if (cachedData) {
                    try {
                        const parsed = JSON.parse(cachedData);
                        starsElement.textContent = parsed.stars.toLocaleString();
                    } catch (e) {
                        starsElement.textContent = 'N/A';
                    }
                } else {
                    starsElement.textContent = 'N/A';
                }
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

    // Add updateHomeConnectionStatus if it doesn't exist or needs adjustment
    updateHomeConnectionStatus: function() {
        console.log('[huntarrUI] Updating home connection statuses...');
        // This function should ideally call checkAppConnection for all relevant apps
        // or use the stored configuredApps status if checkAppConnection updates it.
        this.checkAppConnections(); // Re-check all connections after a save might be simplest
    },
    
    // Load stateful management info
    loadStatefulInfo: function(attempts = 0) {
        const initialStateEl = document.getElementById('stateful_initial_state');
        const expiresDateEl = document.getElementById('stateful_expires_date');
        const intervalInput = document.getElementById('stateful_management_hours');
        const intervalDaysSpan = document.getElementById('stateful_management_days');
        
        // Max retry attempts - increased for better reliability
        const maxAttempts = 5;
        
        console.log(`[StatefulInfo] Loading stateful info (attempt ${attempts + 1})`);
        
        // Update UI to show loading state instead of N/A
        if (attempts === 0) {
            if (initialStateEl) initialStateEl.textContent = 'Loading...';
            if (expiresDateEl) expiresDateEl.textContent = 'Loading...';
        }
        
        fetch('/api/stateful/info', { 
            cache: 'no-cache',
            headers: {
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                if (initialStateEl && data.created_at_ts) {
                    const createdDate = new Date(data.created_at_ts * 1000);
                    initialStateEl.textContent = this.formatDateNicely(createdDate);
                } else if (initialStateEl) {
                    initialStateEl.textContent = 'N/A';
                    
                    // If we got N/A but this is not our last attempt, retry with shorter delay
                    if (attempts < maxAttempts && !data.created_at_ts) {
                        console.log(`[StatefulInfo] No timestamp data, will retry (${attempts + 1}/${maxAttempts})`);
                        setTimeout(() => this.loadStatefulInfo(attempts + 1), 300); // Retry after 300ms
                        return;
                    }
                }
                
                if (expiresDateEl && data.expires_at_ts) {
                    const expiresDate = new Date(data.expires_at_ts * 1000);
                    expiresDateEl.textContent = this.formatDateNicely(expiresDate);
                } else if (expiresDateEl) {
                    expiresDateEl.textContent = 'N/A';
                    
                    // If we got N/A but this is not our last attempt, retry 
                    if (attempts < maxAttempts && !data.expires_at_ts) {
                        // We already scheduled a retry above, no need to do it again
                        return;
                    }
                }
                
                // Update interval input and days display
                if (intervalInput && data.interval_hours) {
                    intervalInput.value = data.interval_hours;
                    if (intervalDaysSpan) {
                        const days = (data.interval_hours / 24).toFixed(1);
                        intervalDaysSpan.textContent = `${days} days`;
                    }
                }
                
                // Hide error notification if it was visible
                const notification = document.getElementById('stateful-notification');
                if (notification) {
                    notification.style.display = 'none';
                }
                
                // Store the data for future reference
                this._cachedStatefulData = data;
            } else {
                throw new Error(data.message || 'Failed to load stateful info');
            }
        })
        .catch(error => {
            console.error(`Error loading stateful info (attempt ${attempts + 1}/${maxAttempts + 1}):`, error);
            
            // Retry if we haven't reached max attempts with shorter delay
            if (attempts < maxAttempts) {
                console.log(`[StatefulInfo] Retrying in 300ms (attempt ${attempts + 1}/${maxAttempts})`);
                setTimeout(() => this.loadStatefulInfo(attempts + 1), 300);
                return;
            }
            
            if (initialStateEl) initialStateEl.textContent = 'Error loading data';
            if (expiresDateEl) expiresDateEl.textContent = 'Error loading data';
            
            // Show error notification
            const notification = document.getElementById('stateful-notification');
            if (notification) {
                notification.textContent = 'Failed to load stateful management info. Check logs for details.';
                notification.style.display = 'block';
                notification.className = 'notification error'; // Ensure class is set
            }
        });
    },
    
    // Format date nicely with time, day, and relative time indication
    formatDateNicely: function(date) {
        if (!(date instanceof Date) || isNaN(date)) {
            return 'Invalid date';
        }
        
        const options = { 
            weekday: 'short',
            year: 'numeric', 
            month: 'short', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        };
        
        const formattedDate = date.toLocaleDateString(undefined, options);
        
        // Add relative time indicator (e.g., "in 6 days" or "7 days ago")
        const now = new Date();
        const diffTime = date.getTime() - now.getTime();
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        
        let relativeTime = '';
        if (diffDays > 0) {
            relativeTime = ` (in ${diffDays} day${diffDays !== 1 ? 's' : ''})`;
        } else if (diffDays < 0) {
            relativeTime = ` (${Math.abs(diffDays)} day${Math.abs(diffDays) !== 1 ? 's' : ''} ago)`;
        } else {
            relativeTime = ' (today)';
        }
        
        return `${formattedDate}${relativeTime}`;
    },
    
    // Reset stateful management - clear all processed IDs
    resetStatefulManagement: function() {
        // Show a loading indicator or disable the button
        const resetBtn = document.getElementById('reset_stateful_btn');
        if (resetBtn) {
            resetBtn.disabled = true;
            resetBtn.textContent = 'Resetting...';
        }
        
        fetch('/api/stateful/reset', {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            cache: 'no-cache' // Add cache control to prevent caching
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                this.showNotification('Stateful management reset successfully', 'success');
                // Wait a moment before reloading the info to ensure it's refreshed
                setTimeout(() => {
                    this.loadStatefulInfo(); // Reload stateful info to update the UI
                }, 500);
            } else {
                throw new Error(data.message || 'Unknown error resetting stateful management');
            }
        })
        .catch(error => {
            console.error('Error resetting stateful management:', error);
            this.showNotification(`Failed to reset stateful management: ${error.message}`, 'error');
        })
        .finally(() => {
            // Restore the button state
            if (resetBtn) {
                resetBtn.disabled = false;
                resetBtn.textContent = 'Reset Stateful Management';
            }
        });
    },
    
    // Update stateful management expiration based on hours input
    updateStatefulExpirationOnUI: function() {
        const hoursInput = document.getElementById('stateful_management_hours');
        if (!hoursInput) return;
        
        const hours = parseInt(hoursInput.value) || 168;
        
        // Show updating indicator
        const expiresDateEl = document.getElementById('stateful_expires_date');
        if (expiresDateEl) {
            expiresDateEl.textContent = 'Updating...';
        }
        
        fetch('/api/stateful/update-expiration', {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ hours: hours }),
            cache: 'no-cache'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                this.showNotification(`Updated expiration to ${hours} hours`, 'success');
                // Reload the stateful info after a short delay
                setTimeout(() => {
                    this.loadStatefulInfo();
                }, 500);
            } else {
                throw new Error(data.message || 'Unknown error updating expiration');
            }
        })
        .catch(error => {
             console.error('Error updating stateful expiration:', error);
             this.showNotification(`Failed to update expiration: ${error.message}`, 'error');
             // Reset the UI
             if (expiresDateEl) {
                 expiresDateEl.textContent = 'Error updating';
             }
        });
    },

    // Add a proper hasFormChanges function to compare form values with original values
    hasFormChanges: function(app) {
        if (!app || !this.originalSettings || !this.originalSettings[app]) return false;
        
        const form = document.getElementById(`${app}Settings`);
        if (!form) return false;
        
        const currentSettings = this.getFormSettings(app);
        if (!currentSettings) return false;
        
        // Deep comparison of current settings with original settings
        // For complex objects like instances, we need to stringify them for comparison
        const originalJSON = JSON.stringify(this.originalSettings[app]);
        const currentJSON = JSON.stringify(currentSettings);
        
        return originalJSON !== currentJSON;
    },
};

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', () => {
    huntarrUI.init();
    
    // Remove the version loading from scripts.html as it's now in new-main.js
    // ... existing event listeners ...
});

// Expose huntarrUI to the global scope for access by app modules
window.huntarrUI = huntarrUI;
