/**
 * Cycle Countdown Timer
 * Shows countdown timers for each app's next cycle
 */

window.CycleCountdown = (function() {
    // Cache for next cycle timestamps
    const nextCycleTimes = {};
    // Active timer intervals
    const timerIntervals = {};
    // List of apps to track
    const trackedApps = ['sonarr', 'radarr', 'lidarr', 'readarr', 'whisparr', 'whisparr-v3', 'eros'];
    
    // Get base URL for API calls, respecting subpath configuration
    function getBaseUrl() {
        return window.location.origin + window.location.pathname.replace(/\/+$/, '');
    }
    
    // Build a complete URL with the correct base path
    function buildUrl(path) {
        // Simply return path since we're using absolute paths
        // Make sure the path starts with a slash
        if (!path.startsWith('/')) {
            path = '/' + path;
        }
        
        // For API endpoints, use the current origin without any subpath manipulation
        return window.location.origin + path;
    }
    
    // Set up timer elements in the DOM
    function setupTimerElements() {
        // Create timer elements in each app status card
        trackedApps.forEach(app => {
            createTimerElement(app);
        });
    }
    
    // Initialize countdown timers for all apps
    function initialize() {
        console.log('[CycleCountdown] Initializing countdown timers');
        
        // Get references to all HTML elements
        setupTimerElements();
        
        // Set up event listeners for reset buttons
        setupResetButtonListeners();
        
        // First try to fetch from sleep.json
        fetchFromSleepJson()
            .then(data => {
                console.log('[CycleCountdown] Successfully loaded data from sleep.json');
                // Data is already processed in fetchFromSleepJson
            })
            .catch(error => {
                console.error('[CycleCountdown] Could not load from sleep.json:', error);
                // Instead of mock data, show error messages in the UI
                displayLoadError();
            });
        
        // Set up periodic refresh every 10 seconds
        setInterval(() => {
            fetchFromSleepJson().catch(error => {
                console.warn('[CycleCountdown] Refresh failed:', error);
                // Display error message if we've never successfully loaded data
                if (Object.keys(nextCycleTimes).length === 0) {
                    displayLoadError();
                }
                // Otherwise keep the existing timer data
            });
        }, 10000); // 10 seconds
    }
    
    // Fetch cycle data from sleep.json file via direct access
    function fetchFromSleepJson() {
        console.log('[CycleCountdown] Fetching cycle data from web-accessible sleep.json');
        
        // Use a direct URL to the web-accessible version of sleep.json
        const sleepJsonUrl = window.location.origin + '/static/data/sleep.json';
        
        // Add a timestamp to prevent caching
        const url = `${sleepJsonUrl}?t=${Date.now()}`;
        
        console.log(`[CycleCountdown] Requesting from URL: ${url}`);
        
        return new Promise((resolve, reject) => {
            fetch(url, {
                method: 'GET',
                headers: {
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('[CycleCountdown] Successfully fetched sleep.json:', data);
                
                // Check if we got valid data
                if (Object.keys(data).length === 0) {
                    console.warn('[CycleCountdown] Sleep.json contained no data');
                    reject(new Error('No data in sleep.json'));
                    return;
                }
                
                let dataProcessed = false;
                
                // Process the data for each app
                for (const app in data) {
                    if (trackedApps.includes(app)) {
                        // Check if data format is valid
                        if (data[app] && data[app].next_cycle) {
                            console.log(`[CycleCountdown] Processing data for ${app}:`, data[app]);
                            
                            // Convert ISO date string to Date object
                            const nextCycleTime = new Date(data[app].next_cycle);
                            
                            // Validate the date is in the future
                            if (isNaN(nextCycleTime.getTime())) {
                                console.error(`[CycleCountdown] Invalid date format for ${app}:`, data[app].next_cycle);
                                continue;
                            }
                            
                            // Store the next cycle time
                            nextCycleTimes[app] = nextCycleTime;
                            
                            // Store remaining seconds if available for more accurate display
                            if (data[app].remaining_seconds !== undefined) {
                                console.log(`[CycleCountdown] Using remaining_seconds for ${app}:`, data[app].remaining_seconds);
                                // Update the timer with exact seconds rather than calculating from next_cycle
                            }
                            
                            // Update the timer display
                            updateTimerDisplay(app);
                            
                            // Set up countdown interval if not already set
                            setupCountdown(app);
                            
                            dataProcessed = true;
                        } else {
                            console.warn(`[CycleCountdown] Invalid data format for ${app}:`, data[app]);
                        }
                    }
                }
                
                if (dataProcessed) {
                    resolve(data);
                } else {
                    console.warn('[CycleCountdown] No valid app data found in sleep.json');
                    reject(new Error('No valid app data'));
                }
            })
            .catch(error => {
                console.error('[CycleCountdown] Error fetching sleep.json:', error);
                // Display error in the UI
                displayLoadError();
                reject(error);
            });
        });
    }
    
    // Set up reset button click listeners
    function setupResetButtonListeners() {
        // Find all reset buttons
        const resetButtons = document.querySelectorAll('button.cycle-reset-button');
        
        resetButtons.forEach(button => {
            button.addEventListener('click', function() {
                const app = this.getAttribute('data-app');
                if (app) {
                    console.log(`[CycleCountdown] Reset button clicked for ${app}, will update timer in 2 seconds`);
                    
                    // Add a loading state to the timer
                    const timerElement = document.getElementById(`${app}CycleTimer`);
                    if (timerElement) {
                        const timerValue = timerElement.querySelector('.timer-value');
                        if (timerValue) {
                            timerValue.textContent = 'Refreshing';
                            timerValue.classList.add('refreshing-state');
                        }
                    }
                    
                    // Wait a moment for the backend to process the reset
                    setTimeout(() => {
                        fetchFromSleepJson();
                    }, 2000);
                }
            });
        });
    }
    
    // Display error message in the UI when sleep data can't be loaded
    function displayLoadError() {
        // For each app, display error message in timer elements
        trackedApps.forEach(app => {
            const timerElement = document.getElementById(`${app}CycleTimer`);
            if (timerElement) {
                const timerValue = timerElement.querySelector('.timer-value');
                if (timerValue) {
                    timerValue.textContent = 'Error Loading';
                    timerValue.classList.add('error');
                }
            }
        });
    }
    
    // Create timer display element in the app stats card
    function createTimerElement(app) {
        // Handle special case for whisparr-v3 - convert hyphen to be CSS compatible
        const dataApp = app;
        
        // Get the CSS class name version of the app (replacing hyphens with nothing)
        const cssClass = app.replace(/-/g, '');
        
        // Directly look for the reset cycle button by data-app attribute
        const resetButton = document.querySelector(`button.cycle-reset-button[data-app="${dataApp}"]`);
        
        if (!resetButton) {
            console.log(`[CycleCountdown] Reset button not found for ${app}`);
            return;
        }
        
        // Check if timer element already exists
        let timerElement = document.getElementById(`${app}CycleTimer`);
        if (timerElement) return;
        
        // Create a container to hold both elements side by side
        const container = document.createElement('div');
        container.className = 'reset-and-timer-container';
        container.style.display = 'flex';
        container.style.justifyContent = 'space-between';
        container.style.alignItems = 'center';
        container.style.width = '100%';
        container.style.marginTop = '8px';
        
        // Replace the button with our container
        resetButton.parentNode.insertBefore(container, resetButton);
        container.appendChild(resetButton);
        
        // Find the app card to get its parent for the app class
        const appCard = resetButton.closest('.app-card');
        
        // Create timer element
        timerElement = document.createElement('div');
        timerElement.id = `${app}CycleTimer`;
        timerElement.className = 'cycle-timer inline-timer';
        timerElement.innerHTML = '<i class="fas fa-clock"></i> <span class="timer-value">--:--:--</span>';
        
        // Apply direct styling to ensure colors show correctly
        if (app === 'eros') {
            // Apply direct styling for Whisparr V3 (eros) with !important to ensure it shows
            timerElement.style.cssText = 'border-left: 2px solid #ff45b7 !important;';
            console.log('[CycleCountdown] Applied Whisparr V3 (eros) styling');
        }
        
        // Always apply app-specific styling class
        timerElement.classList.add(cssClass);
        
        // Also add a custom data attribute for easier styling/debugging
        timerElement.setAttribute('data-app-type', app);
        
        // Add a timer icon with app-specific color
        const timerIcon = timerElement.querySelector('i');
        if (timerIcon) {
            timerIcon.classList.add(`${cssClass}-icon`);
        }
        
        console.log(`[CycleCountdown] Applied app-specific styling class: ${cssClass}`);
        
        // Add the timer to our container
        container.appendChild(timerElement);
        
        console.log(`[CycleCountdown] Timer created for ${app} next to reset button`);
    }
    
    // Fetch cycle times for all tracked apps
    function fetchAllCycleTimes() {
        // First try to get data for all apps at once
        fetchAllCycleData().catch(() => {
            // If that fails, fetch individually
            trackedApps.forEach(app => {
                fetchCycleTime(app);
            });
        });
    }
    
    // Fetch cycle data for all apps at once
    function fetchAllCycleData() {
        return new Promise((resolve, reject) => {
            // Use a completely relative URL approach to avoid any subpath issues
            const url = buildUrl('./api/cycle/status');
            
            console.log(`[CycleCountdown] Fetching all cycle times from URL: ${url}`);
            
            fetch(url, {
                method: 'GET',
                headers: {
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                // Data format should be {sonarr: {next_cycle: "...", updated_at: "..."}, ...}
                let updated = false;
                
                for (const app in data) {
                    if (trackedApps.includes(app) && data[app].next_cycle) {
                        // Store next cycle time
                        nextCycleTimes[app] = new Date(data[app].next_cycle);
                        
                        // Update timer display immediately
                        updateTimerDisplay(app);
                        
                        // Set up interval to update countdown
                        setupCountdown(app);
                        
                        updated = true;
                    }
                }
                
                if (updated) {
                    resolve(data);
                } else {
                    reject(new Error('No valid cycle data found'));
                }
            })
            .catch(error => {
                console.error('[CycleCountdown] Error fetching all cycle times:', error);
                reject(error);
            });
        });
    }
    
    // Fetch the next cycle time for a specific app
    function fetchCycleTime(app) {
        try {
            // Use a completely relative URL approach to avoid any subpath issues
            const url = buildUrl(`./api/cycle/status/${app}`);
            
            console.log(`[CycleCountdown] Fetching cycle time for ${app} from URL: ${url}`);
            
            // Use safe timeout to avoid context issues
            safeSetTimeout(() => {
                fetch(url, {
                    method: 'GET',
                    headers: {
                        'Cache-Control': 'no-cache',
                        'Pragma': 'no-cache'
                    }
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    if (data && data.next_cycle) {
                        // Store next cycle time
                        nextCycleTimes[app] = new Date(data.next_cycle);
                        
                        // Update timer display immediately
                        updateTimerDisplay(app);
                        
                        // Set up interval to update countdown
                        setupCountdown(app);
                    }
                })
                .catch(error => {
                    console.error(`[CycleCountdown] Error fetching cycle time for ${app}:`, error);
                    updateTimerError(app);
                });
            }, 50);
        } catch (error) {
            console.error(`[CycleCountdown] Error in fetchCycleTime for ${app}:`, error);
            updateTimerError(app);
        }
    }
    
    // Set up countdown interval for an app
    function setupCountdown(app) {
        // Clear any existing interval
        if (timerIntervals[app]) {
            clearInterval(timerIntervals[app]);
        }
        
        // Set up new interval to update every second
        timerIntervals[app] = setInterval(() => {
            updateTimerDisplay(app);
        }, 1000);
    }
    
    // Update the timer display for an app
    function updateTimerDisplay(app) {
        const timerElement = document.getElementById(`${app}CycleTimer`);
        if (!timerElement) return;
        
        const timerValue = timerElement.querySelector('.timer-value');
        if (!timerValue) return;
        
        const nextCycleTime = nextCycleTimes[app];
        if (!nextCycleTime) {
            timerValue.textContent = '--:--:--';
            return;
        }
        
        // Calculate time remaining
        const now = new Date();
        const timeRemaining = nextCycleTime - now;
        
        if (timeRemaining <= 0) {
            // Time has passed, fetch updated data from sleep.json
            timerValue.textContent = 'Refreshing';
            timerValue.classList.add('refreshing-state');
            
            // Apply direct styling to ensure it's scoped to just this timer
            timerValue.style.color = '#00c2ce'; // Light blue for 'Refreshing'
            
            // Remove any existing time-based classes to ensure clean state
            timerElement.classList.remove('timer-soon', 'timer-imminent', 'timer-normal');
            timerValue.classList.remove('timer-value-soon', 'timer-value-imminent', 'timer-value-normal');
            
            // Fetch the latest data from sleep.json
            console.log(`[CycleCountdown] Timer expired for ${app}, fetching new data`);
            fetchFromSleepJson()
                .then(() => {
                    console.log(`[CycleCountdown] Successfully refreshed data after timer expired`);
                    // Force a timer update after getting new data
                    updateTimerDisplay(app);
                })
                .catch(error => {
                    console.error(`[CycleCountdown] Failed to refresh data after timer expired:`, error);
                });
            
            return;
        }
        
        // Format countdown time
        const hours = Math.floor(timeRemaining / (1000 * 60 * 60));
        const minutes = Math.floor((timeRemaining % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((timeRemaining % (1000 * 60)) / 1000);
        
        // Format with leading zeros
        const formattedHours = String(hours).padStart(2, '0');
        const formattedMinutes = String(minutes).padStart(2, '0');
        const formattedSeconds = String(seconds).padStart(2, '0');
        
        // Display formatted countdown
        timerValue.textContent = `${formattedHours}:${formattedMinutes}:${formattedSeconds}`;
        
        // Remove refreshing state class and clear any inline styles to restore proper color
        timerValue.classList.remove('refreshing-state');
        // Only clear color if we're not in a time-based state
        if (!timerElement.classList.contains('timer-soon') && 
            !timerElement.classList.contains('timer-imminent') && 
            !timerElement.classList.contains('timer-normal')) {
            // Reset to default white color when no classes are applied
            timerValue.style.removeProperty('color');
        }
        
        // Add visual indicator for remaining time
        updateTimerStyle(timerElement, timeRemaining);
    }
    
    // Update timer styling based on remaining time
    function updateTimerStyle(timerElement, timeRemaining) {
        // Get the timer value element
        const timerValue = timerElement.querySelector('.timer-value');
        if (!timerValue) return;
        
        // Remove any existing time-based classes from both elements
        timerElement.classList.remove('timer-soon', 'timer-imminent', 'timer-normal');
        timerValue.classList.remove('timer-value-soon', 'timer-value-imminent', 'timer-value-normal');
        
        // Add class based on time remaining
        if (timeRemaining < 60000) { // Less than 1 minute
            timerElement.classList.add('timer-imminent');
            timerValue.classList.add('timer-value-imminent');
            timerValue.style.color = '#ff3333'; // Red - direct styling for immediate effect
        } else if (timeRemaining < 300000) { // Less than 5 minutes
            timerElement.classList.add('timer-soon');
            timerValue.classList.add('timer-value-soon');
            timerValue.style.color = '#ff8c00'; // Orange - direct styling for immediate effect
        } else {
            timerElement.classList.add('timer-normal');
            timerValue.classList.add('timer-value-normal');
            timerValue.style.color = 'white'; // White - direct styling for immediate effect
        }
    }
    
    // Show error state in timer
    function updateTimerError(app) {
        const timerElement = document.getElementById(`${app}CycleTimer`);
        if (!timerElement) return;
        
        const timerValue = timerElement.querySelector('.timer-value');
        if (!timerValue) return;
        
        timerValue.textContent = 'Unavailable';
        timerElement.classList.add('timer-error');
    }
    
    // Clean up timers when page changes
    function cleanup() {
        Object.keys(timerIntervals).forEach(app => {
            clearInterval(timerIntervals[app]);
            delete timerIntervals[app];
        });
    }
    
    // Initialize on page load - with proper binding for setTimeout
    function safeSetTimeout(callback, delay) {
        // Make sure we're using the global window object for setTimeout
        return window.setTimeout.bind(window)(callback, delay);
    }
    
    function safeSetInterval(callback, delay) {
        // Make sure we're using the global window object for setInterval
        return window.setInterval.bind(window)(callback, delay);
    }
    
    // Override the setupCountdown function to use safe timeout methods
    function setupCountdown(app) {
        // Clear any existing interval
        if (timerIntervals[app]) {
            window.clearInterval.bind(window)(timerIntervals[app]);
        }
        
        // Set up new interval to update every second
        timerIntervals[app] = safeSetInterval(() => {
            updateTimerDisplay(app);
        }, 1000);
    }
    
    document.addEventListener('DOMContentLoaded', function() {
        // Delay initialization to ensure DOM is fully loaded
        safeSetTimeout(function() {
            // Initialize when user navigates to home section
            const observer = new MutationObserver((mutations) => {
                for (const mutation of mutations) {
                    if (mutation.target.id === 'homeSection' && 
                        mutation.attributeName === 'class' && 
                        !mutation.target.classList.contains('hidden')) {
                        initialize();
                    } else if (mutation.target.id === 'homeSection' && 
                               mutation.attributeName === 'class' && 
                               mutation.target.classList.contains('hidden')) {
                        cleanup();
                    }
                }
            });
            
            const homeSection = document.getElementById('homeSection');
            if (homeSection) {
                observer.observe(homeSection, { attributes: true });
                
                // Initialize immediately if home section is visible
                if (!homeSection.classList.contains('hidden')) {
                    initialize();
                }
            }
        }, 100);
    });
    
    // Public API
    return {
        initialize: initialize,
        fetchAllCycleTimes: fetchAllCycleTimes,
        cleanup: cleanup
    };
})();
