// Direct reset script for stateful management
// This is loaded on the page and provides a global function that can be called directly

// Create a function that will keep looking for the button
function setUpResetButton() {
    console.log('Looking for reset button...');
    
    // Function to check if settings panel is visible
    function isSettingsPanelActive() {
        const settingsPanel = document.getElementById('settingsSection');
        return settingsPanel && window.getComputedStyle(settingsPanel).display !== 'none';
    }
    
    // Function to attach listeners to the reset button
    function attachResetListener() {
        // Try to find the reset button
        const resetButton = document.getElementById('reset_stateful_btn');
        
        if (resetButton) {
            console.log('Found reset button, replacing with direct implementation');
            
            // Replace the button's click event with our direct implementation
            resetButton.addEventListener('click', function(event) {
                // Prevent any default actions
                event.preventDefault();
                event.stopPropagation();
                
                // Ask for confirmation
                if (!confirm('Are you sure you want to reset stateful management? This will clear all processed media IDs.')) {
                    return;
                }
                
                // Disable button and show loading state
                this.disabled = true;
                const originalText = this.innerHTML;
                this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Resetting...';
                
                // Store button reference for closure
                const btn = this;
                
                // Make direct fetch request using the absolute URL path
                fetch('/api/stateful/reset', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Cache-Control': 'no-cache'
                    }
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`Reset failed with status ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('Reset successful:', data);
                    
                    // Show success message
                    alert('Stateful management reset successfully!');
                    
                    // Reload the page to show updated data
                    window.location.reload();
                })
                .catch(error => {
                    console.error('Reset error:', error);
                    alert('Failed to reset stateful management: ' + error.message);
                    
                    // Restore button state
                    btn.disabled = false;
                    btn.innerHTML = originalText;
                });
            }, true);  // Use capture phase to ensure our handler runs first
            
            console.log('Direct reset implementation attached to button');
            return true; // Successfully attached
        } else {
            console.log('Reset button not found yet, will try again');
            return false;
        }
    }
    
    // Try to attach immediately if we're already on the settings page
    if (isSettingsPanelActive()) {
        console.log('Settings panel active, trying to attach listener');
        if (attachResetListener()) {
            return; // Successfully attached
        }
    }
    
    // If we get here, either the settings panel isn't active or we couldn't find the button
    // Set up an event handler to check when navigation happens
    document.addEventListener('click', function(event) {
        // Look for navigation clicks that might lead to settings
        const target = event.target;
        const settingsLink = target.closest('a[href="#settings"]') || 
                            target.closest('.nav-item[data-section="settings"]');
        
        if (settingsLink) {
            console.log('Settings link clicked, waiting for panel to appear');
            
            // Wait for the panel to appear and then try to attach our listener
            setTimeout(function checkAndAttach() {
                if (isSettingsPanelActive()) {
                    attachResetListener();
                } else {
                    // Try again in a short while
                    setTimeout(checkAndAttach, 100);
                }
            }, 100);
        }
    });
    
    // Also set up a mutation observer to watch for DOM changes
    const observer = new MutationObserver(function(mutations) {
        if (isSettingsPanelActive() && document.getElementById('reset_stateful_btn')) {
            attachResetListener();
        }
    });
    
    // Start observing the document with the configured parameters
    observer.observe(document.body, { childList: true, subtree: true });
    
    // Add a window load handler as a last resort
    window.addEventListener('load', function() {
        console.log('Window fully loaded, checking for reset button');
        // Set a timer to periodically check for the button after the page is fully loaded
        const intervalId = setInterval(function() {
            if (isSettingsPanelActive()) {
                if (attachResetListener()) {
                    clearInterval(intervalId);
                }
            }
        }, 500); // Check every 500ms
        
        // Clear the interval after 10 seconds to avoid running forever
        setTimeout(function() {
            clearInterval(intervalId);
        }, 10000);
    });
}

// Set up immediately and also when DOM is loaded
setUpResetButton();
document.addEventListener('DOMContentLoaded', setUpResetButton);

// Create a global function that can be called from console for debugging
window.huntarrResetStateful = function() {
    console.log('Manual reset triggered');
    const resetButton = document.getElementById('reset_stateful_btn');
    if (resetButton) {
        resetButton.click();
    } else {
        alert('Reset button not found. Please navigate to the Settings page first.');
    }
};
