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
    const trackedApps = ['sonarr', 'radarr', 'lidarr', 'readarr', 'whisparr', 'whisparrv3'];
    
    // Get base URL for API calls, respecting subpath configuration
    function getBaseUrl() {
        return (window.HUNTARR_BASE_URL || '');
    }
    
    // Build a complete URL with the correct base path
    function buildUrl(path) {
        // For subpath deployment, we need to use relative paths
        // So convert any absolute paths to relative
        if (path.startsWith('/')) {
            path = '.' + path;
        }
        return path;
    }
    
    // Initialize countdown timers for all apps
    function initialize() {
        console.log('[CycleCountdown] Initializing countdown timers');
        
        // Create timer elements in each app status card
        trackedApps.forEach(app => {
            createTimerElement(app);
        });
        
        // While API endpoints are being fixed, use mock data for display
        createMockTimers();
        
        // For development - uncomment when API is ready
        // fetchAllCycleTimes();
        // setInterval(fetchAllCycleTimes, 60000);
    }
    
    // Create mock timers with reasonable cycle times for display purposes
    function createMockTimers() {
        const now = new Date();
        
        // Set each app to a different countdown time for testing
        nextCycleTimes['sonarr'] = new Date(now.getTime() + 15 * 60000); // 15 minutes
        nextCycleTimes['radarr'] = new Date(now.getTime() + 8 * 60000);  // 8 minutes
        nextCycleTimes['lidarr'] = new Date(now.getTime() + 22 * 60000); // 22 minutes
        nextCycleTimes['readarr'] = new Date(now.getTime() + 5 * 60000); // 5 minutes
        nextCycleTimes['whisparr'] = new Date(now.getTime() + 2 * 60000); // 2 minutes
        
        // Set up countdown timers for all apps
        trackedApps.forEach(app => {
            updateTimerDisplay(app);
            setupCountdown(app);
        });
    }
    
    // Create timer display element in the app stats card
    function createTimerElement(app) {
        // Handle whisparrv3 as a special case
        const dataApp = app === 'whisparrv3' ? 'whisparr-v3' : app;
        
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
        
        // Create timer element
        timerElement = document.createElement('div');
        timerElement.id = `${app}CycleTimer`;
        timerElement.className = 'cycle-timer inline-timer';
        timerElement.innerHTML = '<i class="fas fa-clock"></i> <span class="timer-value">--:--:--</span>';
        
        // Add the timer to our container
        container.appendChild(timerElement);
        
        console.log(`[CycleCountdown] Timer created for ${app} next to reset button`);
    }
    
    // Fetch cycle times for all tracked apps
    function fetchAllCycleTimes() {
        trackedApps.forEach(app => {
            fetchCycleTime(app);
        });
    }
    
    // Fetch the next cycle time for a specific app
    function fetchCycleTime(app) {
        try {
            // Use a completely relative URL approach to avoid any subpath issues
            const url = `./api/cycle/status/${app}`;
            
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
            // Time has passed, fetch updated cycle time
            timerValue.textContent = 'Refreshing...';
            fetchCycleTime(app);
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
        
        // Add visual indicator for remaining time
        updateTimerStyle(timerElement, timeRemaining);
    }
    
    // Update timer styling based on remaining time
    function updateTimerStyle(timerElement, timeRemaining) {
        // Remove any existing time-based classes
        timerElement.classList.remove('timer-soon', 'timer-imminent', 'timer-normal');
        
        // Add class based on time remaining
        if (timeRemaining < 60000) { // Less than 1 minute
            timerElement.classList.add('timer-imminent');
        } else if (timeRemaining < 300000) { // Less than 5 minutes
            timerElement.classList.add('timer-soon');
        } else {
            timerElement.classList.add('timer-normal');
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
