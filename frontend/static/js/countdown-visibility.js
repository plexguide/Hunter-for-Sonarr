/**
 * Countdown Timer Visibility Controller
 * Controls the visibility of countdown timers based on user settings
 */

window.CountdownVisibility = (function() {
    // Track if countdown timers should be shown
    let showCountdownTimer = true; // Default to showing timers
    
    // Get base URL for API calls
    function buildUrl(path) {
        if (!path.startsWith('/')) {
            path = '/' + path;
        }
        return window.location.origin + path;
    }
    
    // Check the user's setting for countdown timer visibility
    function checkTimerVisibility() {
        const apiUrl = buildUrl('/api/settings/general');
        
        fetch(apiUrl, {
            method: 'GET',
            headers: {
                'Cache-Control': 'no-cache'
            }
        })
        .then(response => response.json())
        .then(config => {
            // Check if show_countdown_timer setting is explicitly set to false
            if (config && config.show_countdown_timer === false) {
                showCountdownTimer = false;
                hideAllTimers();
            } else {
                showCountdownTimer = true;
                showAllTimers();
            }
        })
        .catch(error => {
            console.error('[CountdownVisibility] Error checking timer visibility setting:', error);
            // Default to showing timers if there's an error
            showCountdownTimer = true;
        });
    }
    
    // Hide all countdown timers
    function hideAllTimers() {
        // First, try to hide by class (more reliable)
        const timerElements = document.querySelectorAll('.cycle-timer');
        if (timerElements.length > 0) {
            console.log('[CountdownVisibility] Hiding ' + timerElements.length + ' timers by class');
            timerElements.forEach(element => {
                if (element) {
                    element.style.display = 'none';
                }
            });
        } else {
            // Fallback to ID-based selector
            const timerElementsById = document.querySelectorAll('[id$="CycleTimer"]');
            console.log('[CountdownVisibility] Hiding ' + timerElementsById.length + ' timers by ID');
            timerElementsById.forEach(element => {
                if (element) {
                    element.style.display = 'none';
                }
            });
        }
    }
    
    // Show all countdown timers
    function showAllTimers() {
        // First, try to show by class (more reliable)
        const timerElements = document.querySelectorAll('.cycle-timer');
        if (timerElements.length > 0) {
            console.log('[CountdownVisibility] Showing ' + timerElements.length + ' timers by class');
            timerElements.forEach(element => {
                if (element) {
                    element.style.display = '';
                }
            });
        } else {
            // Fallback to ID-based selector
            const timerElementsById = document.querySelectorAll('[id$="CycleTimer"]');
            console.log('[CountdownVisibility] Showing ' + timerElementsById.length + ' timers by ID');
            timerElementsById.forEach(element => {
                if (element) {
                    element.style.display = '';
                }
            });
        }
    }
    
    // Initialize the visibility controller
    function initialize() {
        // Check the setting on page load
        checkTimerVisibility();
        
        // Set up an observer to watch for changes to the settings
        if (window.huntarrUI && window.huntarrUI.onSettingsSaved) {
            window.huntarrUI.onSettingsSaved('general', function(settings) {
                if ('show_countdown_timer' in settings) {
                    // Recheck visibility when the setting changes
                    checkTimerVisibility();
                }
            });
        }
    }
    
    // Public API
    return {
        initialize: initialize,
        checkVisibility: checkTimerVisibility
    };
})();

// Initialize when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Wait a moment to ensure all other scripts have initialized
    setTimeout(function() {
        window.CountdownVisibility.initialize();
        
        // Add a MutationObserver to detect when timers are added to the page
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.addedNodes.length > 0) {
                    // Check if any timers were added
                    mutation.addedNodes.forEach(function(node) {
                        if (node.classList && node.classList.contains('cycle-timer')) {
                            // Re-apply visibility settings when new timer elements are added
                            window.CountdownVisibility.checkVisibility();
                        }
                    });
                }
            });
        });
        
        // Start observing the document with the configured parameters
        observer.observe(document.body, { childList: true, subtree: true });
        
        // Also check periodically for the first minute
        let checkCount = 0;
        const intervalId = setInterval(function() {
            window.CountdownVisibility.checkVisibility();
            checkCount++;
            if (checkCount >= 6) { // Check 6 times (every 2 seconds for 12 seconds)
                clearInterval(intervalId);
            }
        }, 2000);
    }, 1000); // Increased delay to ensure all scripts are loaded
});
