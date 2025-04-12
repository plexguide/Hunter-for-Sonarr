document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const homeButton = document.getElementById('homeButton');
    const logsButton = document.getElementById('logsButton');
    const settingsButton = document.getElementById('settingsButton');
    const userButton = document.getElementById('userButton');
    const homeContainer = document.getElementById('homeContainer');
    const logsContainer = document.getElementById('logsContainer');
    const settingsContainer = document.getElementById('settingsContainer');
    const logsElement = document.getElementById('logs');
    const statusElement = document.getElementById('status');
    const clearLogsButton = document.getElementById('clearLogs');
    const autoScrollCheckbox = document.getElementById('autoScroll');
    const themeToggle = document.getElementById('themeToggle');
    const themeLabel = document.getElementById('themeLabel');
    
    // App tabs
    const appTabs = document.querySelectorAll('.app-tab');
    const appSettings = document.querySelectorAll('.app-settings');
    
    // Connection status elements on home page
    const sonarrHomeStatus = document.getElementById('sonarrHomeStatus');
    const radarrHomeStatus = document.getElementById('radarrHomeStatus');
    const lidarrHomeStatus = document.getElementById('lidarrHomeStatus');
    const readarrHomeStatus = document.getElementById('readarrHomeStatus');
    
    // Current selected app
    let currentApp = 'sonarr';
    
    // App settings - Sonarr
    const sonarrApiUrlInput = document.getElementById('sonarr_api_url');
    const sonarrApiKeyInput = document.getElementById('sonarr_api_key');
    const sonarrConnectionStatus = document.getElementById('sonarrConnectionStatus');
    const testSonarrConnectionButton = document.getElementById('testSonarrConnection');
    
    // App settings - Radarr
    const radarrApiUrlInput = document.getElementById('radarr_api_url');
    const radarrApiKeyInput = document.getElementById('radarr_api_key');
    const radarrConnectionStatus = document.getElementById('radarrConnectionStatus');
    const testRadarrConnectionButton = document.getElementById('testRadarrConnection');
    
    // App settings - Lidarr
    const lidarrApiUrlInput = document.getElementById('lidarr_api_url');
    const lidarrApiKeyInput = document.getElementById('lidarr_api_key');
    const lidarrConnectionStatus = document.getElementById('lidarrConnectionStatus');
    const testLidarrConnectionButton = document.getElementById('testLidarrConnection');
    
    // App settings - Readarr
    const readarrApiUrlInput = document.getElementById('readarr_api_url');
    const readarrApiKeyInput = document.getElementById('readarr_api_key');
    const readarrConnectionStatus = document.getElementById('readarrConnectionStatus');
    const testReadarrConnectionButton = document.getElementById('testReadarrConnection');
    
    // Settings form elements - Basic settings (Sonarr)
    const huntMissingShowsInput = document.getElementById('hunt_missing_shows');
    const huntUpgradeEpisodesInput = document.getElementById('hunt_upgrade_episodes');
    const sleepDurationInput = document.getElementById('sleep_duration');
    const sleepDurationHoursSpan = document.getElementById('sleep_duration_hours');
    const stateResetIntervalInput = document.getElementById('state_reset_interval_hours');
    const monitoredOnlyInput = document.getElementById('monitored_only');
    const randomMissingInput = document.getElementById('random_missing');
    const randomUpgradesInput = document.getElementById('random_upgrades');
    const skipFutureEpisodesInput = document.getElementById('skip_future_episodes');
    const skipSeriesRefreshInput = document.getElementById('skip_series_refresh');
    
    // Settings form elements - Advanced settings
    const apiTimeoutInput = document.getElementById('api_timeout');
    const debugModeInput = document.getElementById('debug_mode');
    const commandWaitDelayInput = document.getElementById('command_wait_delay');
    const commandWaitAttemptsInput = document.getElementById('command_wait_attempts');
    const minimumDownloadQueueSizeInput = document.getElementById('minimum_download_queue_size');
    
    // Button elements for saving and resetting settings
    const saveSettingsButton = document.getElementById('saveSettings');
    const resetSettingsButton = document.getElementById('resetSettings');
    const saveSettingsBottomButton = document.getElementById('saveSettingsBottom');
    const resetSettingsBottomButton = document.getElementById('resetSettingsBottom');
    
    // Store original settings values
    let originalSettings = {};
    
    // Track which apps are configured
    const configuredApps = {
        sonarr: false,
        radarr: false,
        lidarr: false,
        readarr: false
    };
    
    // Settings form elements - Radarr settings
    const huntMissingMoviesInput = document.getElementById('hunt_missing_movies');
    const huntUpgradeMoviesInput = document.getElementById('hunt_upgrade_movies');
    const radarrSleepDurationInput = document.getElementById('radarr_sleep_duration');
    const radarrSleepDurationHoursSpan = document.getElementById('radarr_sleep_duration_hours');
    const radarrStateResetIntervalInput = document.getElementById('radarr_state_reset_interval_hours');
    const radarrMonitoredOnlyInput = document.getElementById('radarr_monitored_only');
    const radarrRandomMissingInput = document.getElementById('radarr_random_missing');
    const radarrRandomUpgradesInput = document.getElementById('radarr_random_upgrades');
    const skipFutureReleasesInput = document.getElementById('skip_future_releases');
    const skipMovieRefreshInput = document.getElementById('skip_movie_refresh');
    const radarrApiTimeoutInput = document.getElementById('radarr_api_timeout');
    const radarrDebugModeInput = document.getElementById('radarr_debug_mode');
    const radarrCommandWaitDelayInput = document.getElementById('radarr_command_wait_delay');
    const radarrCommandWaitAttemptsInput = document.getElementById('radarr_command_wait_attempts');
    const radarrMinimumDownloadQueueSizeInput = document.getElementById('radarr_minimum_download_queue_size');
    
    // Settings form elements - Lidarr settings
    const huntMissingAlbumsInput = document.getElementById('hunt_missing_albums');
    const huntUpgradeTracksInput = document.getElementById('hunt_upgrade_tracks');
    const lidarrSleepDurationInput = document.getElementById('lidarr_sleep_duration');
    const lidarrSleepDurationHoursSpan = document.getElementById('lidarr_sleep_duration_hours');
    const lidarrStateResetIntervalInput = document.getElementById('lidarr_state_reset_interval_hours');
    const lidarrMonitoredOnlyInput = document.getElementById('lidarr_monitored_only');
    const lidarrRandomMissingInput = document.getElementById('lidarr_random_missing');
    const lidarrRandomUpgradesInput = document.getElementById('lidarr_random_upgrades');
    const lidarrSkipFutureReleasesInput = document.getElementById('lidarr_skip_future_releases');
    const skipArtistRefreshInput = document.getElementById('skip_artist_refresh');
    const lidarrApiTimeoutInput = document.getElementById('lidarr_api_timeout');
    const lidarrDebugModeInput = document.getElementById('lidarr_debug_mode');
    const lidarrCommandWaitDelayInput = document.getElementById('lidarr_command_wait_delay');
    const lidarrCommandWaitAttemptsInput = document.getElementById('lidarr_command_wait_attempts');
    const lidarrMinimumDownloadQueueSizeInput = document.getElementById('lidarr_minimum_download_queue_size');
    
    // Settings form elements - Readarr settings
    const huntMissingBooksInput = document.getElementById('hunt_missing_books');
    const huntUpgradeBooksInput = document.getElementById('hunt_upgrade_books');
    const readarrSleepDurationInput = document.getElementById('readarr_sleep_duration');
    const readarrSleepDurationHoursSpan = document.getElementById('readarr_sleep_duration_hours');
    const readarrStateResetIntervalInput = document.getElementById('readarr_state_reset_interval_hours');
    const readarrMonitoredOnlyInput = document.getElementById('readarr_monitored_only');
    const readarrRandomMissingInput = document.getElementById('readarr_random_missing');
    const readarrRandomUpgradesInput = document.getElementById('readarr_random_upgrades');
    const readarrSkipFutureReleasesInput = document.getElementById('readarr_skip_future_releases');
    const skipAuthorRefreshInput = document.getElementById('skip_author_refresh');
    const readarrApiTimeoutInput = document.getElementById('readarr_api_timeout');
    const readarrDebugModeInput = document.getElementById('readarr_debug_mode');
    const readarrCommandWaitDelayInput = document.getElementById('readarr_command_wait_delay');
    const readarrCommandWaitAttemptsInput = document.getElementById('readarr_command_wait_attempts');
    const readarrMinimumDownloadQueueSizeInput = document.getElementById('readarr_minimum_download_queue_size');
    
    // App selection handler
    appTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const app = this.dataset.app;
            
            // If it's already the active app, do nothing
            if (app === currentApp) return;
            
            // Update active tab
            appTabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            
            // Update active settings panel if on settings page
            if (settingsContainer && settingsContainer.style.display !== 'none') {
                appSettings.forEach(s => s.style.display = 'none');
                document.getElementById(`${app}Settings`).style.display = 'block';
            }
            
            // Update current app
            currentApp = app;
            
            // Load settings for this app
            loadSettings(app);
            
            // For logs, we need to refresh the log stream
            if (logsElement && logsContainer && logsContainer.style.display !== 'none') {
                // Clear the logs first
                logsElement.innerHTML = '';
                
                // Update connection status based on configuration
                if (statusElement) {
                    if (configuredApps[app]) {
                        statusElement.textContent = 'Connected';
                        statusElement.className = 'status-connected';
                    } else {
                        statusElement.textContent = 'Disconnected';
                        statusElement.className = 'status-disconnected';
                    }
                }
                
                // Reconnect the event source only if app is configured
                if (configuredApps[app]) {
                    connectEventSource(app);
                }
            }
        });
    });
    
    // Update sleep duration display
    function updateSleepDurationDisplay() {
        if (sleepDurationInput && sleepDurationHoursSpan) {
            const seconds = parseInt(sleepDurationInput.value) || 900;
            updateDurationDisplay(seconds, sleepDurationHoursSpan);
        }
        
        if (radarrSleepDurationInput && radarrSleepDurationHoursSpan) {
            const seconds = parseInt(radarrSleepDurationInput.value) || 900;
            updateDurationDisplay(seconds, radarrSleepDurationHoursSpan);
        }
        
        if (lidarrSleepDurationInput && lidarrSleepDurationHoursSpan) {
            const seconds = parseInt(lidarrSleepDurationInput.value) || 900;
            updateDurationDisplay(seconds, lidarrSleepDurationHoursSpan);
        }
        
        if (readarrSleepDurationInput && readarrSleepDurationHoursSpan) {
            const seconds = parseInt(readarrSleepDurationInput.value) || 900;
            updateDurationDisplay(seconds, readarrSleepDurationHoursSpan);
        }
    }
    
    function updateDurationDisplay(seconds, spanElement) {
        let displayText = '';
        
        if (seconds < 60) {
            displayText = `${seconds} seconds`;
        } else if (seconds < 3600) {
            const minutes = Math.floor(seconds / 60);
            displayText = `≈ ${minutes} minute${minutes !== 1 ? 's' : ''}`;
        } else {
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            if (minutes === 0) {
                displayText = `≈ ${hours} hour${hours !== 1 ? 's' : ''}`;
            } else {
                displayText = `≈ ${hours} hour${hours !== 1 ? 's' : ''} ${minutes} minute${minutes !== 1 ? 's' : ''}`;
            }
        }
        
        spanElement.textContent = displayText;
    }
    
    if (sleepDurationInput) {
        sleepDurationInput.addEventListener('input', function() {
            updateSleepDurationDisplay();
            checkForChanges();
        });
    }
    
    if (radarrSleepDurationInput) {
        radarrSleepDurationInput.addEventListener('input', function() {
            updateSleepDurationDisplay();
            checkForChanges();
        });
    }
    
    if (lidarrSleepDurationInput) {
        lidarrSleepDurationInput.addEventListener('input', function() {
            updateSleepDurationDisplay();
            checkForChanges();
        });
    }
    
    if (readarrSleepDurationInput) {
        readarrSleepDurationInput.addEventListener('input', function() {
            updateSleepDurationDisplay();
            checkForChanges();
        });
    }
    
    // Theme management
    function loadTheme() {
        fetch('/api/settings/theme')
            .then(response => response.json())
            .then(data => {
                const isDarkMode = data.dark_mode || false;
                setTheme(isDarkMode);
                if (themeToggle) themeToggle.checked = isDarkMode;
                if (themeLabel) themeLabel.textContent = isDarkMode ? 'Dark Mode' : 'Light Mode';
            })
            .catch(error => console.error('Error loading theme:', error));
    }
    
    function setTheme(isDark) {
        if (isDark) {
            document.body.classList.add('dark-theme');
            if (themeLabel) themeLabel.textContent = 'Dark Mode';
        } else {
            document.body.classList.remove('dark-theme');
            if (themeLabel) themeLabel.textContent = 'Light Mode';
        }
    }
    
    if (themeToggle) {
        themeToggle.addEventListener('change', function() {
            const isDarkMode = this.checked;
            setTheme(isDarkMode);
            
            fetch('/api/settings/theme', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ dark_mode: isDarkMode })
            })
            .catch(error => console.error('Error saving theme:', error));
        });
    }
    
    // Get user's name for welcome message
    function getUserInfo() {
        // This is a placeholder - in a real implementation, you'd likely have an API
        // to get the current user's information
        const username = document.getElementById('username');
        if (username) {
            username.textContent = 'User'; // Default placeholder
        }
    }
    
    // Update connection status on the home page
    function updateHomeConnectionStatus() {
        // Check current configured state
        fetch('/api/configured-apps')
            .then(response => response.json())
            .then(data => {
                // Update the configuredApps object
                configuredApps.sonarr = data.sonarr || false;
                configuredApps.radarr = data.radarr || false;
                configuredApps.lidarr = data.lidarr || false;
                configuredApps.readarr = data.readarr || false;
                
                // Update UI elements
                // Sonarr status
                if (sonarrHomeStatus) {
                    if (configuredApps.sonarr) {
                        sonarrHomeStatus.textContent = 'Configured';
                        sonarrHomeStatus.className = 'connection-badge connected';
                    } else {
                        sonarrHomeStatus.textContent = 'Not Configured';
                        sonarrHomeStatus.className = 'connection-badge not-connected';
                    }
                }
                
                // Radarr status
                if (radarrHomeStatus) {
                    if (configuredApps.radarr) {
                        radarrHomeStatus.textContent = 'Configured';
                        radarrHomeStatus.className = 'connection-badge connected';
                    } else {
                        radarrHomeStatus.textContent = 'Not Configured';
                        radarrHomeStatus.className = 'connection-badge not-connected';
                    }
                }
                
                // Lidarr status
                if (lidarrHomeStatus) {
                    if (configuredApps.lidarr) {
                        lidarrHomeStatus.textContent = 'Configured';
                        lidarrHomeStatus.className = 'connection-badge connected';
                    } else {
                        lidarrHomeStatus.textContent = 'Not Configured';
                        lidarrHomeStatus.className = 'connection-badge not-connected';
                    }
                }
                
                // Readarr status
                if (readarrHomeStatus) {
                    if (configuredApps.readarr) {
                        readarrHomeStatus.textContent = 'Configured';
                        readarrHomeStatus.className = 'connection-badge connected';
                    } else {
                        readarrHomeStatus.textContent = 'Not Configured';
                        readarrHomeStatus.className = 'connection-badge not-connected';
                    }
                }
            })
            .catch(error => console.error('Error checking configured apps:', error));
    }
    
    // Update logs connection status
    function updateLogsConnectionStatus() {
        if (statusElement) {
            if (configuredApps[currentApp]) {
                statusElement.textContent = 'Connected';
                statusElement.className = 'status-connected';
            } else {
                statusElement.textContent = 'Disconnected';
                statusElement.className = 'status-disconnected';
            }
        }
    }
    
    // Tab switching - Toggle visibility of containers
    if (homeButton && logsButton && settingsButton && homeContainer && logsContainer && settingsContainer) {
        homeButton.addEventListener('click', function() {
            homeContainer.style.display = 'flex';
            logsContainer.style.display = 'none';
            settingsContainer.style.display = 'none';
            homeButton.classList.add('active');
            logsButton.classList.remove('active');
            settingsButton.classList.remove('active');
            userButton.classList.remove('active');
            
            // Update connection status on home page
            updateHomeConnectionStatus();
        });
        
        logsButton.addEventListener('click', function() {
            homeContainer.style.display = 'none';
            logsContainer.style.display = 'flex';
            settingsContainer.style.display = 'none';
            homeButton.classList.remove('active');
            logsButton.classList.add('active');
            settingsButton.classList.remove('active');
            userButton.classList.remove('active');
            
            // Update the connection status based on configuration
            updateLogsConnectionStatus();
            
            // Reconnect to logs for the current app if configured
            if (logsElement && configuredApps[currentApp]) {
                connectEventSource(currentApp);
            }
        });
        
        settingsButton.addEventListener('click', function() {
            homeContainer.style.display = 'none';
            logsContainer.style.display = 'none';
            settingsContainer.style.display = 'flex';
            homeButton.classList.remove('active');
            logsButton.classList.remove('active');
            settingsButton.classList.add('active');
            userButton.classList.remove('active');
            
            // Show the settings for the current app
            appSettings.forEach(s => s.style.display = 'none');
            document.getElementById(`${currentApp}Settings`).style.display = 'block';
            
            // Make sure settings are loaded
            loadSettings(currentApp);
        });
        
        userButton.addEventListener('click', function() {
            window.location.href = '/user';
        });
    }
    
    // Log management
    if (clearLogsButton) {
        clearLogsButton.addEventListener('click', function() {
            if (logsElement) logsElement.innerHTML = '';
        });
    }
    
    // Auto-scroll function
    function scrollToBottom() {
        if (autoScrollCheckbox && autoScrollCheckbox.checked && logsElement) {
            logsElement.scrollTop = logsElement.scrollHeight;
        }
    }
    
    // Test connection functions
    function testConnection(app, urlInput, keyInput, statusElement) {
        const apiUrl = urlInput.value;
        const apiKey = keyInput.value;
        
        if (!apiUrl || !apiKey) {
            alert(`Please enter both API URL and API Key for ${app.charAt(0).toUpperCase() + app.slice(1)} before testing the connection.`);
            return;
        }
        
        // Test API connection
        if (statusElement) {
            statusElement.textContent = 'Testing...';
            statusElement.className = 'connection-badge';
        }
        
        // Use the correct endpoint URL based on the app type
        fetch(`/${app}/test-connection`, {
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
                if (statusElement) {
                    statusElement.textContent = 'Connected';
                    statusElement.className = 'connection-badge connected';
                }
                
                // Update configuration status
                configuredApps[app] = true;
                
                // Update home page status
                updateHomeConnectionStatus();
            } else {
                if (statusElement) {
                    statusElement.textContent = 'Connection Failed';
                    statusElement.className = 'connection-badge not-connected';
                }
                
                // Update configuration status
                configuredApps[app] = false;
                
                alert(`Connection failed: ${data.message}`);
            }
        })
        .catch(error => {
            console.error(`Error testing ${app} connection:`, error);
            if (statusElement) {
                statusElement.textContent = 'Connection Error';
                statusElement.className = 'connection-badge not-connected';
            }
            
            // Update configuration status
            configuredApps[app] = false;
            
            alert(`Error testing ${app} connection: ` + error.message);
        });
    }
    
    // Test connection for all apps
    if (testSonarrConnectionButton) {
        testSonarrConnectionButton.addEventListener('click', function() {
            testConnection('sonarr', sonarrApiUrlInput, sonarrApiKeyInput, sonarrConnectionStatus);
        });
    }
    
    if (testRadarrConnectionButton) {
        testRadarrConnectionButton.addEventListener('click', function() {
            testConnection('radarr', radarrApiUrlInput, radarrApiKeyInput, radarrConnectionStatus);
        });
    }
    
    if (testLidarrConnectionButton) {
        testLidarrConnectionButton.addEventListener('click', function() {
            testConnection('lidarr', lidarrApiUrlInput, lidarrApiKeyInput, lidarrConnectionStatus);
        });
    }
    
    if (testReadarrConnectionButton) {
        testReadarrConnectionButton.addEventListener('click', function() {
            testConnection('readarr', readarrApiUrlInput, readarrApiKeyInput, readarrConnectionStatus);
        });
    }
    
    // Function to check if settings have changed from original values
    function checkForChanges() {
        if (!originalSettings.huntarr) return false; // Don't check if original settings not loaded
        
        let hasChanges = false;
        
        // API connection settings
        if (currentApp === 'sonarr') {
            if (sonarrApiUrlInput && sonarrApiUrlInput.value !== originalSettings.api_url) hasChanges = true;
            if (sonarrApiKeyInput && sonarrApiKeyInput.value !== originalSettings.api_key) hasChanges = true;
        } else if (currentApp === 'radarr') {
            if (radarrApiUrlInput && radarrApiUrlInput.dataset.originalValue !== undefined && 
                radarrApiUrlInput.value !== radarrApiUrlInput.dataset.originalValue) hasChanges = true;
            if (radarrApiKeyInput && radarrApiKeyInput.dataset.originalValue !== undefined && 
                radarrApiKeyInput.value !== radarrApiKeyInput.dataset.originalValue) hasChanges = true;
        } else if (currentApp === 'lidarr') {
            if (lidarrApiUrlInput && lidarrApiUrlInput.dataset.originalValue !== undefined && 
                lidarrApiUrlInput.value !== lidarrApiUrlInput.dataset.originalValue) hasChanges = true;
            if (lidarrApiKeyInput && lidarrApiKeyInput.dataset.originalValue !== undefined && 
                lidarrApiKeyInput.value !== lidarrApiKeyInput.dataset.originalValue) hasChanges = true;
        } else if (currentApp === 'readarr') {
            if (readarrApiUrlInput && readarrApiUrlInput.dataset.originalValue !== undefined && 
                readarrApiUrlInput.value !== readarrApiUrlInput.dataset.originalValue) hasChanges = true;
            if (readarrApiKeyInput && readarrApiKeyInput.dataset.originalValue !== undefined && 
                readarrApiKeyInput.value !== readarrApiKeyInput.dataset.originalValue) hasChanges = true;
        }
        
        // Check Sonarr Settings
        if (currentApp === 'sonarr') {
            // Check Basic Settings
            if (huntMissingShowsInput && parseInt(huntMissingShowsInput.value) !== originalSettings.huntarr.hunt_missing_shows) hasChanges = true;
            if (huntUpgradeEpisodesInput && parseInt(huntUpgradeEpisodesInput.value) !== originalSettings.huntarr.hunt_upgrade_episodes) hasChanges = true;
            if (sleepDurationInput && parseInt(sleepDurationInput.value) !== originalSettings.huntarr.sleep_duration) hasChanges = true;
            if (stateResetIntervalInput && parseInt(stateResetIntervalInput.value) !== originalSettings.huntarr.state_reset_interval_hours) hasChanges = true;
            if (monitoredOnlyInput && monitoredOnlyInput.checked !== originalSettings.huntarr.monitored_only) hasChanges = true;
            if (skipFutureEpisodesInput && skipFutureEpisodesInput.checked !== originalSettings.huntarr.skip_future_episodes) hasChanges = true;
            if (skipSeriesRefreshInput && skipSeriesRefreshInput.checked !== originalSettings.huntarr.skip_series_refresh) hasChanges = true;
            
            // Check Advanced Settings
            if (apiTimeoutInput && parseInt(apiTimeoutInput.value) !== originalSettings.advanced.api_timeout) hasChanges = true;
            if (debugModeInput && debugModeInput.checked !== originalSettings.advanced.debug_mode) hasChanges = true;
            if (commandWaitDelayInput && parseInt(commandWaitDelayInput.value) !== originalSettings.advanced.command_wait_delay) hasChanges = true;
            if (commandWaitAttemptsInput && parseInt(commandWaitAttemptsInput.value) !== originalSettings.advanced.command_wait_attempts) hasChanges = true;
            if (minimumDownloadQueueSizeInput && parseInt(minimumDownloadQueueSizeInput.value) !== originalSettings.advanced.minimum_download_queue_size) hasChanges = true;
            if (randomMissingInput && randomMissingInput.checked !== originalSettings.advanced.random_missing) hasChanges = true;
            if (randomUpgradesInput && randomUpgradesInput.checked !== originalSettings.advanced.random_upgrades) hasChanges = true;
        } else if (currentApp === 'radarr') {
            // Check Basic Settings for Radarr
            if (huntMissingMoviesInput && parseInt(huntMissingMoviesInput.value) !== originalSettings.huntarr.hunt_missing_movies) hasChanges = true;
            if (huntUpgradeMoviesInput && parseInt(huntUpgradeMoviesInput.value) !== originalSettings.huntarr.hunt_upgrade_movies) hasChanges = true;
            if (radarrSleepDurationInput && parseInt(radarrSleepDurationInput.value) !== originalSettings.huntarr.sleep_duration) hasChanges = true;
            if (radarrStateResetIntervalInput && parseInt(radarrStateResetIntervalInput.value) !== originalSettings.huntarr.state_reset_interval_hours) hasChanges = true;
            if (radarrMonitoredOnlyInput && radarrMonitoredOnlyInput.checked !== originalSettings.huntarr.monitored_only) hasChanges = true;
            if (skipFutureReleasesInput && skipFutureReleasesInput.checked !== originalSettings.huntarr.skip_future_releases) hasChanges = true;
            if (skipMovieRefreshInput && skipMovieRefreshInput.checked !== originalSettings.huntarr.skip_movie_refresh) hasChanges = true;
            
            // Check Advanced Settings for Radarr
            if (radarrApiTimeoutInput && parseInt(radarrApiTimeoutInput.value) !== originalSettings.advanced.api_timeout) hasChanges = true;
            if (radarrDebugModeInput && radarrDebugModeInput.checked !== originalSettings.advanced.debug_mode) hasChanges = true;
            if (radarrCommandWaitDelayInput && parseInt(radarrCommandWaitDelayInput.value) !== originalSettings.advanced.command_wait_delay) hasChanges = true;
            if (radarrCommandWaitAttemptsInput && parseInt(radarrCommandWaitAttemptsInput.value) !== originalSettings.advanced.command_wait_attempts) hasChanges = true;
            if (radarrMinimumDownloadQueueSizeInput && parseInt(radarrMinimumDownloadQueueSizeInput.value) !== originalSettings.advanced.minimum_download_queue_size) hasChanges = true;
            if (radarrRandomMissingInput && radarrRandomMissingInput.checked !== originalSettings.advanced.random_missing) hasChanges = true;
            if (radarrRandomUpgradesInput && radarrRandomUpgradesInput.checked !== originalSettings.advanced.random_upgrades) hasChanges = true;
        } else if (currentApp === 'lidarr') {
            // Check Basic Settings for Lidarr
            if (huntMissingAlbumsInput && parseInt(huntMissingAlbumsInput.value) !== originalSettings.huntarr.hunt_missing_albums) hasChanges = true;
            if (huntUpgradeTracksInput && parseInt(huntUpgradeTracksInput.value) !== originalSettings.huntarr.hunt_upgrade_tracks) hasChanges = true;
            if (lidarrSleepDurationInput && parseInt(lidarrSleepDurationInput.value) !== originalSettings.huntarr.sleep_duration) hasChanges = true;
            if (lidarrStateResetIntervalInput && parseInt(lidarrStateResetIntervalInput.value) !== originalSettings.huntarr.state_reset_interval_hours) hasChanges = true;
            if (lidarrMonitoredOnlyInput && lidarrMonitoredOnlyInput.checked !== originalSettings.huntarr.monitored_only) hasChanges = true;
            if (lidarrSkipFutureReleasesInput && lidarrSkipFutureReleasesInput.checked !== originalSettings.huntarr.skip_future_releases) hasChanges = true;
            if (skipArtistRefreshInput && skipArtistRefreshInput.checked !== originalSettings.huntarr.skip_artist_refresh) hasChanges = true;
            
            // Check Advanced Settings for Lidarr
            if (lidarrApiTimeoutInput && parseInt(lidarrApiTimeoutInput.value) !== originalSettings.advanced.api_timeout) hasChanges = true;
            if (lidarrDebugModeInput && lidarrDebugModeInput.checked !== originalSettings.advanced.debug_mode) hasChanges = true;
            if (lidarrCommandWaitDelayInput && parseInt(lidarrCommandWaitDelayInput.value) !== originalSettings.advanced.command_wait_delay) hasChanges = true;
            if (lidarrCommandWaitAttemptsInput && parseInt(lidarrCommandWaitAttemptsInput.value) !== originalSettings.advanced.command_wait_attempts) hasChanges = true;
            if (lidarrMinimumDownloadQueueSizeInput && parseInt(lidarrMinimumDownloadQueueSizeInput.value) !== originalSettings.advanced.minimum_download_queue_size) hasChanges = true;
            if (lidarrRandomMissingInput && lidarrRandomMissingInput.checked !== originalSettings.advanced.random_missing) hasChanges = true;
            if (lidarrRandomUpgradesInput && lidarrRandomUpgradesInput.checked !== originalSettings.advanced.random_upgrades) hasChanges = true;
        } else if (currentApp === 'readarr') {
            // Check Basic Settings for Readarr
            if (huntMissingBooksInput && parseInt(huntMissingBooksInput.value) !== originalSettings.huntarr.hunt_missing_books) hasChanges = true;
            if (huntUpgradeBooksInput && parseInt(huntUpgradeBooksInput.value) !== originalSettings.huntarr.hunt_upgrade_books) hasChanges = true;
            if (readarrSleepDurationInput && parseInt(readarrSleepDurationInput.value) !== originalSettings.huntarr.sleep_duration) hasChanges = true;
            if (readarrStateResetIntervalInput && parseInt(readarrStateResetIntervalInput.value) !== originalSettings.huntarr.state_reset_interval_hours) hasChanges = true;
            if (readarrMonitoredOnlyInput && readarrMonitoredOnlyInput.checked !== originalSettings.huntarr.monitored_only) hasChanges = true;
            if (readarrSkipFutureReleasesInput && readarrSkipFutureReleasesInput.checked !== originalSettings.huntarr.skip_future_releases) hasChanges = true;
            if (skipAuthorRefreshInput && skipAuthorRefreshInput.checked !== originalSettings.huntarr.skip_author_refresh) hasChanges = true;
            
            // Check Advanced Settings for Readarr
            if (readarrApiTimeoutInput && parseInt(readarrApiTimeoutInput.value) !== originalSettings.advanced.api_timeout) hasChanges = true;
            if (readarrDebugModeInput && readarrDebugModeInput.checked !== originalSettings.advanced.debug_mode) hasChanges = true;
            if (readarrCommandWaitDelayInput && parseInt(readarrCommandWaitDelayInput.value) !== originalSettings.advanced.command_wait_delay) hasChanges = true;
            if (readarrCommandWaitAttemptsInput && parseInt(readarrCommandWaitAttemptsInput.value) !== originalSettings.advanced.command_wait_attempts) hasChanges = true;
            if (readarrMinimumDownloadQueueSizeInput && parseInt(readarrMinimumDownloadQueueSizeInput.value) !== originalSettings.advanced.minimum_download_queue_size) hasChanges = true;
            if (readarrRandomMissingInput && readarrRandomMissingInput.checked !== originalSettings.advanced.random_missing) hasChanges = true;
            if (readarrRandomUpgradesInput && readarrRandomUpgradesInput.checked !== originalSettings.advanced.random_upgrades) hasChanges = true;
        }
        
        // Enable/disable save buttons based on whether there are changes
        if (saveSettingsButton && saveSettingsBottomButton) {
            saveSettingsButton.disabled = !hasChanges;
            saveSettingsBottomButton.disabled = !hasChanges;
            
            // Apply visual indicator based on disabled state
            if (hasChanges) {
                saveSettingsButton.classList.remove('disabled-button');
                saveSettingsBottomButton.classList.remove('disabled-button');
            } else {
                saveSettingsButton.classList.add('disabled-button');
                saveSettingsBottomButton.classList.add('disabled-button');
            }
        }
        
        return hasChanges;
    }
    
    // Add change event listeners for Sonarr form elements
    if (sonarrApiUrlInput && sonarrApiKeyInput) {
        sonarrApiUrlInput.addEventListener('input', checkForChanges);
        sonarrApiKeyInput.addEventListener('input', checkForChanges);
    }
    
    // Add change event listeners for Radarr form elements
    if (radarrApiUrlInput && radarrApiKeyInput) {
        radarrApiUrlInput.addEventListener('input', checkForChanges);
        radarrApiKeyInput.addEventListener('input', checkForChanges);
    }
    
    // Add change event listeners for Lidarr form elements
    if (lidarrApiUrlInput && lidarrApiKeyInput) {
        lidarrApiUrlInput.addEventListener('input', checkForChanges);
        lidarrApiKeyInput.addEventListener('input', checkForChanges);
    }
    
    // Add change event listeners for Readarr form elements
    if (readarrApiUrlInput && readarrApiKeyInput) {
        readarrApiUrlInput.addEventListener('input', checkForChanges);
        readarrApiKeyInput.addEventListener('input', checkForChanges);
    }
    
    if (huntMissingShowsInput && huntUpgradeEpisodesInput && stateResetIntervalInput && 
        apiTimeoutInput && commandWaitDelayInput && commandWaitAttemptsInput && 
        minimumDownloadQueueSizeInput) {
        
        [huntMissingShowsInput, huntUpgradeEpisodesInput, stateResetIntervalInput, 
         apiTimeoutInput, commandWaitDelayInput, commandWaitAttemptsInput, 
         minimumDownloadQueueSizeInput].forEach(input => {
            input.addEventListener('input', checkForChanges);
        });
    }
    
    if (monitoredOnlyInput && randomMissingInput && randomUpgradesInput && 
        skipFutureEpisodesInput && skipSeriesRefreshInput && debugModeInput) {
        
        [monitoredOnlyInput, randomMissingInput, randomUpgradesInput, 
         skipFutureEpisodesInput, skipSeriesRefreshInput, debugModeInput].forEach(checkbox => {
            checkbox.addEventListener('change', checkForChanges);
        });
    }
    
    // Add event listeners for the Radarr form elements
    if (huntMissingMoviesInput && huntUpgradeMoviesInput && radarrSleepDurationInput && 
        radarrStateResetIntervalInput && radarrApiTimeoutInput && radarrCommandWaitDelayInput && 
        radarrCommandWaitAttemptsInput && radarrMinimumDownloadQueueSizeInput) {
        
        [huntMissingMoviesInput, huntUpgradeMoviesInput, radarrSleepDurationInput, 
         radarrStateResetIntervalInput, radarrApiTimeoutInput, radarrCommandWaitDelayInput, 
         radarrCommandWaitAttemptsInput, radarrMinimumDownloadQueueSizeInput].forEach(input => {
            input.addEventListener('input', checkForChanges);
        });
    }

    if (radarrMonitoredOnlyInput && radarrRandomMissingInput && radarrRandomUpgradesInput && 
        skipFutureReleasesInput && skipMovieRefreshInput && radarrDebugModeInput) {
        
        [radarrMonitoredOnlyInput, radarrRandomMissingInput, radarrRandomUpgradesInput,
         skipFutureReleasesInput, skipMovieRefreshInput, radarrDebugModeInput].forEach(checkbox => {
            checkbox.addEventListener('change', checkForChanges);
        });
    }

    // Add event listeners for the Lidarr form elements
    if (huntMissingAlbumsInput && huntUpgradeTracksInput && lidarrSleepDurationInput && 
        lidarrStateResetIntervalInput && lidarrApiTimeoutInput && lidarrCommandWaitDelayInput && 
        lidarrCommandWaitAttemptsInput && lidarrMinimumDownloadQueueSizeInput) {
        
        [huntMissingAlbumsInput, huntUpgradeTracksInput, lidarrSleepDurationInput, 
         lidarrStateResetIntervalInput, lidarrApiTimeoutInput, lidarrCommandWaitDelayInput, 
         lidarrCommandWaitAttemptsInput, lidarrMinimumDownloadQueueSizeInput].forEach(input => {
            input.addEventListener('input', checkForChanges);
        });
    }

    if (lidarrMonitoredOnlyInput && lidarrRandomMissingInput && lidarrRandomUpgradesInput && 
        lidarrSkipFutureReleasesInput && skipArtistRefreshInput && lidarrDebugModeInput) {
        
        [lidarrMonitoredOnlyInput, lidarrRandomMissingInput, lidarrRandomUpgradesInput,
         lidarrSkipFutureReleasesInput, skipArtistRefreshInput, lidarrDebugModeInput].forEach(checkbox => {
            checkbox.addEventListener('change', checkForChanges);
        });
    }

    // Add event listeners for the Readarr form elements
    if (huntMissingBooksInput && huntUpgradeBooksInput && readarrSleepDurationInput && 
        readarrStateResetIntervalInput && readarrApiTimeoutInput && readarrCommandWaitDelayInput && 
        readarrCommandWaitAttemptsInput && readarrMinimumDownloadQueueSizeInput) {
        
        [huntMissingBooksInput, huntUpgradeBooksInput, readarrSleepDurationInput, 
         readarrStateResetIntervalInput, readarrApiTimeoutInput, readarrCommandWaitDelayInput, 
         readarrCommandWaitAttemptsInput, readarrMinimumDownloadQueueSizeInput].forEach(input => {
            input.addEventListener('input', checkForChanges);
        });
    }

    if (readarrMonitoredOnlyInput && readarrRandomMissingInput && readarrRandomUpgradesInput && 
        readarrSkipFutureReleasesInput && skipAuthorRefreshInput && readarrDebugModeInput) {
        
        [readarrMonitoredOnlyInput, readarrRandomMissingInput, readarrRandomUpgradesInput,
         readarrSkipFutureReleasesInput, skipAuthorRefreshInput, readarrDebugModeInput].forEach(checkbox => {
            checkbox.addEventListener('change', checkForChanges);
        });
    }
    
    // Load settings from API
    function loadSettings(app = 'sonarr') {
        fetch('/api/settings')
            .then(response => response.json())
            .then(data => {
                const huntarr = data.huntarr || {};
                const advanced = data.advanced || {};
                
                // Store original settings for comparison
                originalSettings = JSON.parse(JSON.stringify(data));
                
                // Connection settings for the current app
                if (app === 'sonarr' && sonarrApiUrlInput && sonarrApiKeyInput) {
                    sonarrApiUrlInput.value = data.api_url || '';
                    sonarrApiKeyInput.value = data.api_key || '';
                    
                    // Update configured status for sonarr
                    configuredApps.sonarr = !!(data.api_url && data.api_key);
                    
                    // Update connection status
                    if (sonarrConnectionStatus) {
                        if (data.api_url && data.api_key) {
                            sonarrConnectionStatus.textContent = 'Configured';
                            sonarrConnectionStatus.className = 'connection-badge connected';
                        } else {
                            sonarrConnectionStatus.textContent = 'Not Configured';
                            sonarrConnectionStatus.className = 'connection-badge not-connected';
                        }
                    }
                    
                    // Sonarr-specific settings
                    if (huntMissingShowsInput) {
                        huntMissingShowsInput.value = huntarr.hunt_missing_shows !== undefined ? huntarr.hunt_missing_shows : 1;
                    }
                    if (huntUpgradeEpisodesInput) {
                        huntUpgradeEpisodesInput.value = huntarr.hunt_upgrade_episodes !== undefined ? huntarr.hunt_upgrade_episodes : 5;
                    }
                    if (sleepDurationInput) {
                        sleepDurationInput.value = huntarr.sleep_duration || 900;
                        updateSleepDurationDisplay();
                    }
                    if (stateResetIntervalInput) {
                        stateResetIntervalInput.value = huntarr.state_reset_interval_hours || 168;
                    }
                    if (monitoredOnlyInput) {
                        monitoredOnlyInput.checked = huntarr.monitored_only !== false;
                    }
                    if (skipFutureEpisodesInput) {
                        skipFutureEpisodesInput.checked = huntarr.skip_future_episodes !== false;
                    }
                    if (skipSeriesRefreshInput) {
                        skipSeriesRefreshInput.checked = huntarr.skip_series_refresh === true;
                    }
                    
                    // Advanced settings
                    if (apiTimeoutInput) {
                        apiTimeoutInput.value = advanced.api_timeout || 60;
                    }
                    if (debugModeInput) {
                        debugModeInput.checked = advanced.debug_mode === true;
                    }
                    if (commandWaitDelayInput) {
                        commandWaitDelayInput.value = advanced.command_wait_delay || 1;
                    }
                    if (commandWaitAttemptsInput) {
                        commandWaitAttemptsInput.value = advanced.command_wait_attempts || 600; else if (currentApp === 'radarr') {
                    }
                    if (minimumDownloadQueueSizeInput) {                hunt_missing_movies: document.getElementById('hunt_missing_movies') ? parseInt(document.getElementById('hunt_missing_movies').value) || 0 : 0,
                        minimumDownloadQueueSizeInput.value = advanced.minimum_download_queue_size || -1;ies: document.getElementById('hunt_upgrade_movies') ? parseInt(document.getElementById('hunt_upgrade_movies').value) || 0 : 0,
                    }ion: document.getElementById('radarr_sleep_duration') ? parseInt(document.getElementById('radarr_sleep_duration').value) || 900 : 900,
                    if (randomMissingInput) {reset_interval_hours: document.getElementById('radarr_state_reset_interval_hours') ? parseInt(document.getElementById('radarr_state_reset_interval_hours').value) || 168 : 168,
                        randomMissingInput.checked = advanced.random_missing !== false;tById('radarr_monitored_only') ? document.getElementById('radarr_monitored_only').checked : true,
                    }  skip_future_releases: document.getElementById('skip_future_releases') ? document.getElementById('skip_future_releases').checked : true,
                    if (randomUpgradesInput) {nt.getElementById('skip_movie_refresh') ? document.getElementById('skip_movie_refresh').checked : false
                        randomUpgradesInput.checked = advanced.random_upgrades !== false;  };
                    }
                } else if (app === 'radarr' && radarrApiUrlInput && radarrApiKeyInput) {ode: document.getElementById('radarr_debug_mode') ? document.getElementById('radarr_debug_mode').checked : false,
                    // For Radarr (and other non-Sonarr apps), load from app-settings endpointlay: document.getElementById('radarr_command_wait_delay') ? parseInt(document.getElementById('radarr_command_wait_delay').value) || 1 : 1,
                    fetch(`/api/app-settings?app=radarr`)adarr_command_wait_attempts') ? parseInt(document.getElementById('radarr_command_wait_attempts').value) || 600 : 600,
                        .then(response => response.json())ocument.getElementById('radarr_minimum_download_queue_size') ? parseInt(document.getElementById('radarr_minimum_download_queue_size').value) || -1 : -1,
                        .then(appData => {random_missing') ? document.getElementById('radarr_random_missing').checked : true,
                            if (appData.success) {_random_upgrades') ? document.getElementById('radarr_random_upgrades').checked : true,
                                radarrApiUrlInput.value = appData.api_url || '';timeout: document.getElementById('radarr_api_timeout') ? parseInt(document.getElementById('radarr_api_timeout').value) || 60 : 60
                                radarrApiKeyInput.value = appData.api_key || '';
                                
                                // Store original values in data attributes for comparison
                                radarrApiUrlInput.dataset.originalValue = appData.api_url || '';entById('hunt_missing_albums') ? parseInt(document.getElementById('hunt_missing_albums').value) || 0 : 0,
                                radarrApiKeyInput.dataset.originalValue = appData.api_key || '';) ? parseInt(document.getElementById('hunt_upgrade_tracks').value) || 0 : 0,
                                etElementById('lidarr_sleep_duration').value) || 900 : 900,
                                // Update configured status') ? parseInt(document.getElementById('lidarr_state_reset_interval_hours').value) || 168 : 168,
                                configuredApps.radarr = !!(appData.api_url && appData.api_key);Id('lidarr_monitored_only') ? document.getElementById('lidarr_monitored_only').checked : true,
                                releases') ? document.getElementById('lidarr_skip_future_releases').checked : true,
                                // Update connection statusentById('skip_artist_refresh').checked : false
                                if (radarrConnectionStatus) {
                                    if (appData.api_url && appData.api_key) {
                                        radarrConnectionStatus.textContent = 'Configured';t.getElementById('lidarr_debug_mode').checked : false,
                                        radarrConnectionStatus.className = 'connection-badge connected';ment.getElementById('lidarr_command_wait_delay').value) || 1 : 1,
                                    } else {t(document.getElementById('lidarr_command_wait_attempts').value) || 600 : 600,
                                        radarrConnectionStatus.textContent = 'Not Configured';inimum_download_queue_size: document.getElementById('lidarr_minimum_download_queue_size') ? parseInt(document.getElementById('lidarr_minimum_download_queue_size').value) || -1 : -1,
                                        radarrConnectionStatus.className = 'connection-badge not-connected';random_missing: document.getElementById('lidarr_random_missing') ? document.getElementById('lidarr_random_missing').checked : true,
                                    }rades') ? document.getElementById('lidarr_random_upgrades').checked : true,
                                }ntById('lidarr_api_timeout') ? parseInt(document.getElementById('lidarr_api_timeout').value) || 60 : 60
                            }
                        })
                        .catch(error => {
                            console.error('Error loading Radarr settings:', error);ntById('hunt_missing_books') ? parseInt(document.getElementById('hunt_missing_books').value) || 0 : 0,
                            arseInt(document.getElementById('hunt_upgrade_books').value) || 0 : 0,
                            // Default valuesd('readarr_sleep_duration') ? parseInt(document.getElementById('readarr_sleep_duration').value) || 900 : 900,
                            radarrApiUrlInput.value = '';et_interval_hours') ? parseInt(document.getElementById('readarr_state_reset_interval_hours').value) || 168 : 168,
                            radarrApiKeyInput.value = '';onitored_only: document.getElementById('readarr_monitored_only') ? document.getElementById('readarr_monitored_only').checked : true,
                            radarrApiUrlInput.dataset.originalValue = '';skip_future_releases: document.getElementById('readarr_skip_future_releases') ? document.getElementById('readarr_skip_future_releases').checked : true,
                            radarrApiKeyInput.dataset.originalValue = '';nt.getElementById('skip_author_refresh') ? document.getElementById('skip_author_refresh').checked : false
                            configuredApps.radarr = false;
                            ings.advanced = {
                            if (radarrConnectionStatus) {readarr_debug_mode') ? document.getElementById('readarr_debug_mode').checked : false,
                                radarrConnectionStatus.textContent = 'Not Configured';getElementById('readarr_command_wait_delay') ? parseInt(document.getElementById('readarr_command_wait_delay').value) || 1 : 1,
                                radarrConnectionStatus.className = 'connection-badge not-connected';command_wait_attempts: document.getElementById('readarr_command_wait_attempts') ? parseInt(document.getElementById('readarr_command_wait_attempts').value) || 600 : 600,
                            }ument.getElementById('readarr_minimum_download_queue_size') ? parseInt(document.getElementById('readarr_minimum_download_queue_size').value) || -1 : -1,
                        });lementById('readarr_random_missing') ? document.getElementById('readarr_random_missing').checked : true,
                } else if (app === 'lidarr' && lidarrApiUrlInput && lidarrApiKeyInput) {random_upgrades: document.getElementById('readarr_random_upgrades') ? document.getElementById('readarr_random_upgrades').checked : true,
                    // Load Lidarr settingsetElementById('readarr_api_timeout') ? parseInt(document.getElementById('readarr_api_timeout').value) || 60 : 60
                    fetch(`/api/app-settings?app=lidarr`)
                        .then(response => response.json())
                        .then(appData => {
                            if (appData.success) {
                                lidarrApiUrlInput.value = appData.api_url || '';
                                lidarrApiKeyInput.value = appData.api_key || '';rs: {
                                'Content-Type': 'application/json'
                                // Store original values in data attributes for comparison
                                lidarrApiUrlInput.dataset.originalValue = appData.api_url || '';s)
                                lidarrApiKeyInput.dataset.originalValue = appData.api_key || '';
                                > response.json())
                                // Update configured status
                                configuredApps.lidarr = !!(appData.api_url && appData.api_key);ata.success) {
                                pdate original settings after successful save
                                // Update connection status
                                if (lidarrConnectionStatus) {       originalSettings.api_url = settings.api_url;
                                    if (appData.api_url && appData.api_key) {          originalSettings.api_key = settings.api_key;
                                        lidarrConnectionStatus.textContent = 'Configured';
                                        lidarrConnectionStatus.className = 'connection-badge connected';
                                    } else {ntarr = {...settings.huntarr};
                                        lidarrConnectionStatus.textContent = 'Not Configured';         if (settings.advanced) originalSettings.advanced = {...settings.advanced};
                                        lidarrConnectionStatus.className = 'connection-badge not-connected';           } else if (currentApp === 'radarr') {
                                    }                // Store the original values in data attributes for comparison
                                }radarrApiUrlInput.dataset.originalValue = settings.api_url;
                            }ut) radarrApiKeyInput.dataset.originalValue = settings.api_key;
                        })
                        .catch(error => {l values in data attributes for comparison
                            console.error('Error loading Lidarr settings:', error);et.originalValue = settings.api_url;
                            ue = settings.api_key;
                            // Default valuesse if (currentApp === 'readarr') {
                            lidarrApiUrlInput.value = '';r comparison
                            lidarrApiKeyInput.value = ''; = settings.api_url;
                            lidarrApiUrlInput.dataset.originalValue = '';       if (readarrApiKeyInput) readarrApiKeyInput.dataset.originalValue = settings.api_key;
                            lidarrApiKeyInput.dataset.originalValue = '';
                            configuredApps.lidarr = false;
                            d API key
                            if (lidarrConnectionStatus) {
                                lidarrConnectionStatus.textContent = 'Not Configured';configuredApps.sonarr = !!(settings.api_url && settings.api_key);
                                lidarrConnectionStatus.className = 'connection-badge not-connected';
                            };
                        });   } else if (currentApp === 'lidarr') {
                } else if (app === 'readarr' && readarrApiUrlInput && readarrApiKeyInput) {ings.api_key);
                    // Load Readarr settings= 'readarr') {
                    fetch(`/api/app-settings?app=readarr`)& settings.api_key);
                        .then(response => response.json())
                        .then(appData => {
                            if (appData.success) {
                                readarrApiUrlInput.value = appData.api_url || '';
                                readarrApiKeyInput.value = appData.api_key || '';   
                                
                                // Store original values in data attributes for comparisons();
                                readarrApiUrlInput.dataset.originalValue = appData.api_url || '';
                                readarrApiKeyInput.dataset.originalValue = appData.api_key || '';
                                teLogsConnectionStatus();
                                // Update configured status
                                configuredApps.readarr = !!(appData.api_url && appData.api_key);
                                   if (saveSettingsButton && saveSettingsBottomButton) {
                                // Update connection status           saveSettingsButton.disabled = true;
                                if (readarrConnectionStatus) {               saveSettingsBottomButton.disabled = true;
                                    if (appData.api_url && appData.api_key) {                saveSettingsButton.classList.add('disabled-button');
                                        readarrConnectionStatus.textContent = 'Configured';ottomButton.classList.add('disabled-button');
                                        readarrConnectionStatus.className = 'connection-badge connected';
                                    } else {
                                        readarrConnectionStatus.textContent = 'Not Configured';
                                        readarrConnectionStatus.className = 'connection-badge not-connected';s_made) {
                                    }'Settings saved successfully and cycle restarted to apply changes!');
                                }
                            }  alert('No changes detected.');
                        })
                        .catch(error => {
                            console.error('Error loading Readarr settings:', error);ert('Error saving settings: ' + (data.message || 'Unknown error'));
                            
                            // Default values
                            readarrApiUrlInput.value = '';
                            readarrApiKeyInput.value = '';ving settings:', error);
                            readarrApiUrlInput.dataset.originalValue = '';
                            readarrApiKeyInput.dataset.originalValue = '';
                            configuredApps.readarr = false;
                            
                            if (readarrConnectionStatus) {
                                readarrConnectionStatus.textContent = 'Not Configured';onnectionStatus() {
                                readarrConnectionStatus.className = 'connection-badge not-connected';ionStatus) {
                            }
                        });nnectionStatus.textContent = 'Configured';
                }
                e {
                // Update home page connection status  sonarrConnectionStatus.textContent = 'Not Configured';
                updateHomeConnectionStatus();ionStatus.className = 'connection-badge not-connected';
                
                // Update log connection status if on logs page) {
                if (logsContainer && logsContainer.style.display !== 'none') {(configuredApps.radarr) {
                    updateLogsConnectionStatus();       radarrConnectionStatus.textContent = 'Configured';
                }           radarrConnectionStatus.className = 'connection-badge connected';
                        } else {
                // Initialize save buttons statetent = 'Not Configured';
                if (saveSettingsButton && saveSettingsBottomButton) {
                    saveSettingsButton.disabled = true;
                    saveSettingsBottomButton.disabled = true; {
                    saveSettingsButton.classList.add('disabled-button');    if (configuredApps.lidarr) {
                    saveSettingsBottomButton.classList.add('disabled-button');
                }ted';
            })       } else {
            .catch(error => console.error('Error loading settings:', error));            lidarrConnectionStatus.textContent = 'Not Configured';
    }tionStatus.className = 'connection-badge not-connected';
    
    // Function to save settings    } else if (currentApp === 'readarr' && readarrConnectionStatus) {
    function saveSettings() {
        if (!checkForChanges()) {ured';
            // If no changes, don't do anythingonnected';
            return;    } else {
        }nectionStatus.textContent = 'Not Configured';
nStatus.className = 'connection-badge not-connected';
        // Prepare settings object based on current app   }
        let settings = {}
            app_type: currentApp
        };

        // Add API connection settings
        if (currentApp === 'sonarr' && sonarrApiUrlInput && sonarrApiKeyInput) {settings to default values?')) {
            settings.api_url = sonarrApiUrlInput.value || '';
            settings.api_key = sonarrApiKeyInput.value || '';   method: 'POST',
        } else if (currentApp === 'radarr' && radarrApiUrlInput && radarrApiKeyInput) {      headers: {
            settings.api_url = radarrApiUrlInput.value || '';            'Content-Type': 'application/json'
            settings.api_key = radarrApiKeyInput.value || '';
        } else if (currentApp === 'lidarr' && lidarrApiUrlInput && lidarrApiKeyInput) {gify({ 
            settings.api_url = lidarrApiUrlInput.value || '';
            settings.api_key = lidarrApiKeyInput.value || '';
        } else if (currentApp === 'readarr' && readarrApiUrlInput && readarrApiKeyInput) {)
            settings.api_url = readarrApiUrlInput.value || '';.then(response => response.json())
            settings.api_key = readarrApiKeyInput.value || '';
        }ss) {
to defaults and cycle restarted.');
        // Add other settings based on which app is active;
        if (currentApp === 'sonarr') {   
            settings.huntarr = {/ Update home page connection status
                hunt_missing_shows: huntMissingShowsInput ? parseInt(huntMissingShowsInput.value) || 0 : 0,          updateHomeConnectionStatus();
                hunt_upgrade_episodes: huntUpgradeEpisodesInput ? parseInt(huntUpgradeEpisodesInput.value) || 0 : 0,            
                sleep_duration: sleepDurationInput ? parseInt(sleepDurationInput.value) || 900 : 900,tus
                state_reset_interval_hours: stateResetIntervalInput ? parseInt(stateResetIntervalInput.value) || 168 : 168,
                monitored_only: monitoredOnlyInput ? monitoredOnlyInput.checked : true,
                skip_future_episodes: skipFutureEpisodesInput ? skipFutureEpisodesInput.checked : true,        alert('Error resetting settings: ' + (data.message || 'Unknown error'));
                skip_series_refresh: skipSeriesRefreshInput ? skipSeriesRefreshInput.checked : false
            };
            settings.advanced = {
                debug_mode: debugModeInput ? debugModeInput.checked : false,or);
                command_wait_delay: commandWaitDelayInput ? parseInt(commandWaitDelayInput.value) || 1 : 1,rror.message);
                command_wait_attempts: commandWaitAttemptsInput ? parseInt(commandWaitAttemptsInput.value) || 600 : 600,
                minimumDownloadQueueSize: minimumDownloadQueueSizeInput ? parseInt(minimumDownloadQueueSizeInput.value) || -1 : -1,
                random_missing: randomMissingInput ? randomMissingInput.checked : true,
                random_upgrades: randomUpgradesInput ? randomUpgradesInput.checked : true,
                api_timeout: apiTimeoutInput ? parseInt(apiTimeoutInput.value) || 60 : 60ent listeners to both button sets
            };SettingsButton && resetSettingsButton && saveSettingsBottomButton && resetSettingsBottomButton) {
        } else if (currentApp === 'radarr') {lick', saveSettings);
            settings.huntarr = {click', resetSettings);
                hunt_missing_movies: huntMissingMoviesInput ? parseInt(huntMissingMoviesInput.value) || 0 : 0,
                hunt_upgrade_movies: huntUpgradeMoviesInput ? parseInt(huntUpgradeMoviesInput.value) || 0 : 0,er('click', saveSettings);
                sleep_duration: radarrSleepDurationInput ? parseInt(radarrSleepDurationInput.value) || 900 : 900,tton.addEventListener('click', resetSettings);
                state_reset_interval_hours: radarrStateResetIntervalInput ? parseInt(radarrStateResetIntervalInput.value) || 168 : 168,
                monitored_only: radarrMonitoredOnlyInput ? radarrMonitoredOnlyInput.checked : true,
                skip_future_releases: skipFutureReleasesInput ? skipFutureReleasesInput.checked : true,// Event source for logs
                skip_movie_refresh: skipMovieRefreshInput ? skipMovieRefreshInput.checked : false
            };
            settings.advanced = {
                debug_mode: radarrDebugModeInput ? radarrDebugModeInput.checked : false,
                command_wait_delay: radarrCommandWaitDelayInput ? parseInt(radarrCommandWaitDelayInput.value) || 1 : 1,
                command_wait_attempts: radarrCommandWaitAttemptsInput ? parseInt(radarrCommandWaitAttemptsInput.value) || 600 : 600,
                minimumDownloadQueueSize: radarrMinimumDownloadQueueSizeInput ? parseInt(radarrMinimumDownloadQueueSizeInput.value) || -1 : -1,
                random_missing: radarrRandomMissingInput ? radarrRandomMissingInput.checked : true,
                random_upgrades: radarrRandomUpgradesInput ? radarrRandomUpgradesInput.checked : true,
                api_timeout: radarrApiTimeoutInput ? parseInt(radarrApiTimeoutInput.value) || 60 : 60
            };   eventSource = new EventSource(`/logs?app=${app}`);
        } else if (currentApp === 'lidarr') {    
            settings.huntarr = {
                hunt_missing_albums: huntMissingAlbumsInput ? parseInt(huntMissingAlbumsInput.value) || 0 : 0,) {
                hunt_upgrade_tracks: huntUpgradeTracksInput ? parseInt(huntUpgradeTracksInput.value) || 0 : 0,
                sleep_duration: lidarrSleepDurationInput ? parseInt(lidarrSleepDurationInput.value) || 900 : 900,lassName = 'status-connected';
                state_reset_interval_hours: lidarrStateResetIntervalInput ? parseInt(lidarrStateResetIntervalInput.value) || 168 : 168,
                monitored_only: lidarrMonitoredOnlyInput ? lidarrMonitoredOnlyInput.checked : true,
                skip_future_releases: lidarrSkipFutureReleasesInput ? lidarrSkipFutureReleasesInput.checked : true,
                skip_artist_refresh: skipArtistRefreshInput ? skipArtistRefreshInput.checked : false   eventSource.onerror = function() {
            };        if (statusElement) {
            settings.advanced = {
                debug_mode: lidarrDebugModeInput ? lidarrDebugModeInput.checked : false,
                command_wait_delay: lidarrCommandWaitDelayInput ? parseInt(lidarrCommandWaitDelayInput.value) || 1 : 1,
                command_wait_attempts: lidarrCommandWaitAttemptsInput ? parseInt(lidarrCommandWaitAttemptsInput.value) || 600 : 600,
                minimumDownloadQueueSize: lidarrMinimumDownloadQueueSizeInput ? parseInt(lidarrMinimumDownloadQueueSizeInput.value) || -1 : -1,            // Attempt to reconnect after 5 seconds if app is still configured
                random_missing: lidarrRandomMissingInput ? lidarrRandomMissingInput.checked : true,
                random_upgrades: lidarrRandomUpgradesInput ? lidarrRandomUpgradesInput.checked : true,                if (configuredApps[app]) {
                api_timeout: lidarrApiTimeoutInput ? parseInt(lidarrApiTimeoutInput.value) || 60 : 60
            };
        } else if (currentApp === 'readarr') {
            settings.huntarr = {
                hunt_missing_books: huntMissingBooksInput ? parseInt(huntMissingBooksInput.value) || 0 : 0,
                hunt_upgrade_books: huntUpgradeBooksInput ? parseInt(huntUpgradeBooksInput.value) || 0 : 0,onmessage = function(event) {
                sleep_duration: readarrSleepDurationInput ? parseInt(readarrSleepDurationInput.value) || 900 : 900,
                state_reset_interval_hours: readarrStateResetIntervalInput ? parseInt(readarrStateResetIntervalInput.value) || 168 : 168,ogEntry.className = 'log-entry';
                monitored_only: readarrMonitoredOnlyInput ? readarrMonitoredOnlyInput.checked : true,
                skip_future_releases: readarrSkipFutureReleasesInput ? readarrSkipFutureReleasesInput.checked : true,       // Add appropriate class for log level
                skip_author_refresh: skipAuthorRefreshInput ? skipAuthorRefreshInput.checked : false            if (event.data.includes(' - INFO - ')) {
            };
            settings.advanced = {
                debug_mode: readarrDebugModeInput ? readarrDebugModeInput.checked : false,
                command_wait_delay: readarrCommandWaitDelayInput ? parseInt(readarrCommandWaitDelayInput.value) || 1 : 1,       } else if (event.data.includes(' - ERROR - ')) {
                command_wait_attempts: readarrCommandWaitAttemptsInput ? parseInt(readarrCommandWaitAttemptsInput.value) || 600 : 600,            logEntry.classList.add('log-error');
                minimumDownloadQueueSize: readarrMinimumDownloadQueueSizeInput ? parseInt(readarrMinimumDownloadQueueSizeInput.value) || -1 : -1,e if (event.data.includes(' - DEBUG - ')) {
                random_missing: readarrRandomMissingInput ? readarrRandomMissingInput.checked : true,logEntry.classList.add('log-debug');
                random_upgrades: readarrRandomUpgradesInput ? readarrRandomUpgradesInput.checked : true,
                api_timeout: readarrApiTimeoutInput ? parseInt(readarrApiTimeoutInput.value) || 60 : 60
            };       logEntry.textContent = event.data;
        }        logsElement.appendChild(logEntry);

        fetch('/api/settings', {o-scroll to bottom if enabled
            method: 'POST',        scrollToBottom();
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(settings)
        })
        .then(response => response.json())    logsElement.addEventListener('scroll', function() {
        .then(data => { (within 20px), ensure auto-scroll stays on
            if (data.success) {ogsElement.scrollHeight - logsElement.scrollTop - logsElement.clientHeight) < 20;
                // Update original settings after successful saveautoScrollCheckbox && autoScrollCheckbox.checked) {
                if (currentApp === 'sonarr') {l
                    originalSettings.api_url = settings.api_url;
                    originalSettings.api_key = settings.api_key;
                    });
                    // Update the rest of originalSettings
                    if (settings.huntarr) originalSettings.huntarr = {...settings.huntarr};
                    if (settings.advanced) originalSettings.advanced = {...settings.advanced};
                } else if (currentApp === 'radarr') {
                    // Store the original values in data attributes for comparisonEventListener('change', function() {
                    if (radarrApiUrlInput) radarrApiUrlInput.dataset.originalValue = settings.api_url;
                    if (radarrApiKeyInput) radarrApiKeyInput.dataset.originalValue = settings.api_key;
                } else if (currentApp === 'lidarr') {
                    // Store the original values in data attributes for comparison
                    if (lidarrApiUrlInput) lidarrApiUrlInput.dataset.originalValue = settings.api_url;
                    if (lidarrApiKeyInput) lidarrApiKeyInput.dataset.originalValue = settings.api_key;
                } else if (currentApp === 'readarr') {s page
                    // Store the original values in data attributes for comparison
                    if (readarrApiUrlInput) readarrApiUrlInput.dataset.originalValue = settings.api_url;ountdown');
                    if (readarrApiKeyInput) readarrApiKeyInput.dataset.originalValue = settings.api_key;if (!countdownElement || refreshInterval <= 0) return;
                }
                tion;
                // Update configuration status based on API URL and API key
                if (currentApp === 'sonarr') {    const interval = setInterval(() => {
                    configuredApps.sonarr = !!(settings.api_url && settings.api_key);
                } else if (currentApp === 'radarr') {
                    configuredApps.radarr = !!(settings.api_url && settings.api_key);ntent = 'Cycle starting...';
                } else if (currentApp === 'lidarr') {           clearInterval(interval);
                    configuredApps.lidarr = !!(settings.api_url && settings.api_key);         } else {








































































































































































































































































});    }        connectEventSource(currentApp);    if (logsElement && logsContainer && logsContainer.style.display !== 'none' && configuredApps[currentApp]) {    // Connect to logs if we're on the logs page and the current app is configured        }        updateHomeConnectionStatus();        // Update connection status on home page                if (userButton) userButton.classList.remove('active');        if (settingsButton) settingsButton.classList.remove('active');        if (logsButton) logsButton.classList.remove('active');        if (homeButton) homeButton.classList.add('active');                if (settingsContainer) settingsContainer.style.display = 'none';        if (logsContainer) logsContainer.style.display = 'none';        if (homeContainer) homeContainer.style.display = 'flex';        // Default to home page    } else if (path === '/') {        if (userButton) userButton.classList.remove('active');        if (settingsButton) settingsButton.classList.add('active');        if (logsButton) logsButton.classList.remove('active');        if (homeButton) homeButton.classList.remove('active');                if (settingsContainer) settingsContainer.style.display = 'flex';        if (logsContainer) logsContainer.style.display = 'none';        if (homeContainer) homeContainer.style.display = 'none';        // Show settings page    if (path === '/settings') {    // Show proper content based on path or hash        const path = window.location.pathname;    // Check if we're on the settings page by URL path        loadSettings(currentApp);    // Load settings for initial app        getUserInfo();    // Get user info for welcome page        }        updateSleepDurationDisplay();    if (sleepDurationInput) {    loadTheme();    // Initialize        }        startLogCountdown(sleepDuration, logRefreshInterval);    if (logsContainer && logsContainer.style.display !== 'none') {    // Call this function only when the logs page is active    }        }, refreshInterval * 1000);            }                countdownElement.textContent = `Next cycle in ${remainingTime} seconds`;            } else {                clearInterval(interval);                countdownElement.textContent = 'Cycle starting...';            if (remainingTime <= 0) {            remainingTime -= refreshInterval;        const interval = setInterval(() => {        let remainingTime = sleepDuration;        if (!countdownElement || refreshInterval <= 0) return;        const countdownElement = document.getElementById('logCountdown');    function startLogCountdown(sleepDuration, refreshInterval) {    // Add countdown logic for log refresh specific to the logs page        }        });            }                scrollToBottom();            if (this.checked) {        autoScrollCheckbox.addEventListener('change', function() {    if (autoScrollCheckbox) {    // Re-enable auto-scroll when checkbox is checked        }        });            }                autoScrollCheckbox.checked = false;                // User manually scrolled up, disable auto-scroll            if (!atBottom && autoScrollCheckbox && autoScrollCheckbox.checked) {            const atBottom = (logsElement.scrollHeight - logsElement.scrollTop - logsElement.clientHeight) < 20;            // If we're at the bottom or near it (within 20px), ensure auto-scroll stays on        logsElement.addEventListener('scroll', function() {    if (logsElement) {    // Observe scroll event to detect manual scrolling        }        };            scrollToBottom();            // Auto-scroll to bottom if enabled                        logsElement.appendChild(logEntry);            logEntry.textContent = event.data;                        }                logEntry.classList.add('log-debug');            } else if (event.data.includes(' - DEBUG - ')) {                logEntry.classList.add('log-error');            } else if (event.data.includes(' - ERROR - ')) {                logEntry.classList.add('log-warning');            } else if (event.data.includes(' - WARNING - ')) {                logEntry.classList.add('log-info');            if (event.data.includes(' - INFO - ')) {            // Add appropriate class for log level                        logEntry.className = 'log-entry';            const logEntry = document.createElement('div');        eventSource.onmessage = function(event) {                };            }, 5000);                }                    connectEventSource(app);                if (configuredApps[app]) {            setTimeout(() => {            // Attempt to reconnect after 5 seconds if app is still configured                        }                statusElement.className = 'status-disconnected';                statusElement.textContent = 'Disconnected';            if (statusElement) {        eventSource.onerror = function() {                };            }                statusElement.className = 'status-connected';                statusElement.textContent = 'Connected';            if (statusElement) {        eventSource.onopen = function() {                eventSource = new EventSource(`/logs?app=${app}`);                }            eventSource.close();        if (eventSource) {                if (!configuredApps[app]) return; // Skip if app not configured        if (!logsElement) return; // Skip if not on logs page    function connectEventSource(app = 'sonarr') {        let eventSource;    // Event source for logs        }        resetSettingsBottomButton.addEventListener('click', resetSettings);        saveSettingsBottomButton.addEventListener('click', saveSettings);                resetSettingsButton.addEventListener('click', resetSettings);        saveSettingsButton.addEventListener('click', saveSettings);    if (saveSettingsButton && resetSettingsButton && saveSettingsBottomButton && resetSettingsBottomButton) {    // Add event listeners to both button sets        }        }            });                alert('Error resetting settings: ' + error.message);                console.error('Error resetting settings:', error);            .catch(error => {            })                }                    alert('Error resetting settings: ' + (data.message || 'Unknown error'));                } else {                    updateLogsConnectionStatus();                    // Update logs connection status                                        updateHomeConnectionStatus();                    // Update home page connection status                                        loadSettings(currentApp);                    alert('Settings reset to defaults and cycle restarted.');                if (data.success) {            .then(data => {            .then(response => response.json())            })                })                    app: currentApp                body: JSON.stringify({                 },                    'Content-Type': 'application/json'                headers: {                method: 'POST',            fetch('/api/settings/reset', {        if (confirm('Are you sure you want to reset all settings to default values?')) {    function resetSettings() {    // Function to reset settings        }        }            }                readarrConnectionStatus.className = 'connection-badge not-connected';                readarrConnectionStatus.textContent = 'Not Configured';            } else {                readarrConnectionStatus.className = 'connection-badge connected';                readarrConnectionStatus.textContent = 'Configured';            if (configuredApps.readarr) {        } else if (currentApp === 'readarr' && readarrConnectionStatus) {            }                lidarrConnectionStatus.className = 'connection-badge not-connected';                lidarrConnectionStatus.textContent = 'Not Configured';            } else {                lidarrConnectionStatus.className = 'connection-badge connected';                lidarrConnectionStatus.textContent = 'Configured';            if (configuredApps.lidarr) {        } else if (currentApp === 'lidarr' && lidarrConnectionStatus) {            }                radarrConnectionStatus.className = 'connection-badge not-connected';                radarrConnectionStatus.textContent = 'Not Configured';            } else {                radarrConnectionStatus.className = 'connection-badge connected';                radarrConnectionStatus.textContent = 'Configured';            if (configuredApps.radarr) {        } else if (currentApp === 'radarr' && radarrConnectionStatus) {            }                sonarrConnectionStatus.className = 'connection-badge not-connected';                sonarrConnectionStatus.textContent = 'Not Configured';            } else {                sonarrConnectionStatus.className = 'connection-badge connected';                sonarrConnectionStatus.textContent = 'Configured';            if (configuredApps.sonarr) {        if (currentApp === 'sonarr' && sonarrConnectionStatus) {    function updateConnectionStatus() {    // Function to update connection status        }        });            alert('Error saving settings: ' + error.message);            console.error('Error saving settings:', error);        .catch(error => {        })            }                alert('Error saving settings: ' + (data.message || 'Unknown error'));            } else {                }                    alert('No changes detected.');                } else {                    alert('Settings saved successfully and cycle restarted to apply changes!');                if (data.changes_made) {                // Show success message                                }                    saveSettingsBottomButton.classList.add('disabled-button');                    saveSettingsButton.classList.add('disabled-button');                    saveSettingsBottomButton.disabled = true;                    saveSettingsButton.disabled = true;                if (saveSettingsButton && saveSettingsBottomButton) {                // Disable save buttons                                updateLogsConnectionStatus();                // Update logs connection status                                updateHomeConnectionStatus();                // Update home page connection status                                updateConnectionStatus();                // Update connection status                                }                    configuredApps.readarr = !!(settings.api_url && settings.api_key);                } else if (currentApp === 'readarr') {                countdownElement.textContent = `Next cycle in ${remainingTime} seconds`;
            }
        }, refreshInterval * 1000);
    }

    // Call this function only when the logs page is active
    if (logsContainer && logsContainer.style.display !== 'none') {
        startLogCountdown(sleepDuration, logRefreshInterval);
    }
    
    // Initialize
    loadTheme();
    if (sleepDurationInput) {
        updateSleepDurationDisplay();
    }
    
    // Get user info for welcome page
    getUserInfo();
    
    // Load settings for initial app
    loadSettings(currentApp);
    
    // Check if we're on the settings page by URL path
    const path = window.location.pathname;
    
    // Show proper content based on path or hash
    if (path === '/settings') {
        // Show settings page
        if (homeContainer) homeContainer.style.display = 'none';
        if (logsContainer) logsContainer.style.display = 'none';
        if (settingsContainer) settingsContainer.style.display = 'flex';
        
        if (homeButton) homeButton.classList.remove('active');
        if (logsButton) logsButton.classList.remove('active');
        if (settingsButton) settingsButton.classList.add('active');
        if (userButton) userButton.classList.remove('active');
    } else if (path === '/') {
        // Default to home page
        if (homeContainer) homeContainer.style.display = 'flex';
        if (logsContainer) logsContainer.style.display = 'none';
        if (settingsContainer) settingsContainer.style.display = 'none';
        
        if (homeButton) homeButton.classList.add('active');
        if (logsButton) logsButton.classList.remove('active');
        if (settingsButton) settingsButton.classList.remove('active');
        if (userButton) userButton.classList.remove('active');
        
        // Update connection status on home page
        updateHomeConnectionStatus();
    }
    
    // Connect to logs if we're on the logs page and the current app is configured
    if (logsElement && logsContainer && logsContainer.style.display !== 'none' && configuredApps[currentApp]) {
        connectEventSource(currentApp);
    }
});