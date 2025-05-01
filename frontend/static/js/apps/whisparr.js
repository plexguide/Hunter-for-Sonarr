/**
 * Whisparr.js - Handles Whisparr settings and interactions in the Huntarr UI
 */

document.addEventListener("DOMContentLoaded", function() {
    // Don't call setupWhisparrForm here, new-main.js will call it when the tab is active
    // setupWhisparrForm(); 
    // setupWhisparrLogs(); // Assuming logs are handled by the main logs section
    // setupClearProcessedButtons('whisparr'); // Assuming this is handled elsewhere or not needed immediately
});

/**
 * Setup Whisparr settings form and connection test
 * This function is now called by new-main.js when the Whisparr settings tab is shown.
 */
function setupWhisparrForm() {
    // Use querySelector within the active panel to be safe, though IDs should be unique
    const panel = document.getElementById('whisparrSettings'); 
    if (!panel) {
        console.warn("[whisparr.js] Whisparr settings panel not found.");
        return;
    }

    const testWhisparrButton = panel.querySelector('#test-whisparr-button');
    const whisparrStatusIndicator = panel.querySelector('#whisparr-connection-status');
    const whisparrVersionDisplay = panel.querySelector('#whisparr-version');
    const apiUrlInput = panel.querySelector('#whisparr_api_url');
    const apiKeyInput = panel.querySelector('#whisparr_api_key');

    // Check if elements exist and if listener already attached to prevent duplicates
    if (!testWhisparrButton || testWhisparrButton.dataset.listenerAttached === 'true') {
         console.log("[whisparr.js] Test button not found or listener already attached.");
        return;
    }
     console.log("[whisparr.js] Setting up Whisparr form listeners.");
     testWhisparrButton.dataset.listenerAttached = 'true'; // Mark as attached

    // Test connection button
    testWhisparrButton.addEventListener('click', function() {
        const apiUrl = apiUrlInput ? apiUrlInput.value.trim() : '';
        const apiKey = apiKeyInput ? apiKeyInput.value.trim() : '';
        
        if (!apiUrl || !apiKey) {
            // Use the main UI notification system if available
            if (typeof huntarrUI !== 'undefined' && huntarrUI.showNotification) {
                huntarrUI.showNotification('Please enter both API URL and API Key for Whisparr', 'error');
            } else {
                alert('Please enter both API URL and API Key for Whisparr');
            }
            return;
        }
        
        testWhisparrButton.disabled = true;
        if (whisparrStatusIndicator) {
            whisparrStatusIndicator.className = 'connection-status pending';
            whisparrStatusIndicator.textContent = 'Testing...';
        }
        
        // First check API version to ensure it's v3 (Eros)
        checkWhisparrApiVersion(apiUrl, apiKey)
            .then(isErosApi => {
                if (!isErosApi) {
                    // Show error if not using Eros API
                    if (whisparrStatusIndicator) {
                        whisparrStatusIndicator.className = 'connection-status failure';
                        whisparrStatusIndicator.textContent = 'Legacy API Detected';
                    }
                    
                    if (typeof huntarrUI !== 'undefined' && huntarrUI.showNotification) {
                        huntarrUI.showNotification('Incompatible Whisparr version detected. Please upgrade to Whisparr Eros (v3) to use this integration.', 'error');
                    }
                    
                    testWhisparrButton.disabled = false;
                    return Promise.reject('Legacy API detected');
                }
                
                // If using Eros API, proceed with connection test
                return fetch('/api/whisparr/test-connection', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        api_url: apiUrl,
                        api_key: apiKey
                    })
                });
            })
            .then(response => response.json())
            .then(data => {
                if (whisparrStatusIndicator) {
                    if (data.success) {
                        whisparrStatusIndicator.className = 'connection-status success';
                        whisparrStatusIndicator.textContent = 'Connected';
                        if (typeof huntarrUI !== 'undefined' && huntarrUI.showNotification) {
                             huntarrUI.showNotification('Successfully connected to Whisparr Eros', 'success');
                        }
                        getWhisparrVersion(); // Fetch version after successful connection
                    } else {
                        whisparrStatusIndicator.className = 'connection-status failure';
                        whisparrStatusIndicator.textContent = 'Failed';
                         if (typeof huntarrUI !== 'undefined' && huntarrUI.showNotification) {
                            huntarrUI.showNotification('Connection to Whisparr failed: ' + data.message, 'error');
                        }
                    }
                }
            })
            .catch(error => {
                // Skip additional error notification if it's the legacy API error we already handled
                if (error !== 'Legacy API detected') {
                    if (whisparrStatusIndicator) {
                        whisparrStatusIndicator.className = 'connection-status failure';
                        whisparrStatusIndicator.textContent = 'Error';
                    }
                    if (typeof huntarrUI !== 'undefined' && huntarrUI.showNotification) {
                        huntarrUI.showNotification('Error testing Whisparr connection: ' + error, 'error');
                    }
                }
            })
            .finally(() => {
                if (testWhisparrButton.disabled) {
                    testWhisparrButton.disabled = false;
                }
            });
    });

    // Get Whisparr version if connection details are present and version display exists
    if (apiUrlInput && apiKeyInput && whisparrVersionDisplay && apiUrlInput.value && apiKeyInput.value) {
        getWhisparrVersion();
    }

    // Function to get Whisparr version
    function getWhisparrVersion() {
         if (!whisparrVersionDisplay) return; // Check if element exists

        fetch('/api/whisparr/get-versions')
            .then(response => response.json())
            .then(data => {
                if (data.success && data.version) {
                    whisparrVersionDisplay.textContent = `v${data.version}`; // Prepend 'v'
                } else {
                    whisparrVersionDisplay.textContent = 'Unknown';
                }
            })
            .catch(error => {
                whisparrVersionDisplay.textContent = 'Error';
                console.error('Error fetching Whisparr version:', error);
            });
    }
}

// Helper function for escaping HTML (keep if needed elsewhere, e.g., if logs are added here later)
function escapeHtml(unsafe) {
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}

// Function to check Whisparr API version
function checkWhisparrApiVersion(apiUrl, apiKey) {
    // Use the Eros API endpoint to check version
    return fetch(`${apiUrl}/api/v3/system/status`, {
        method: 'GET',
        headers: {
            'X-Api-Key': apiKey,
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        // Check if response is OK
        if (!response.ok) {
            // If we get a 404, it might be a non-Eros API
            if (response.status === 404) {
                return false;
            }
            // For other status codes, throw to trigger the catch
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        // Check if the response contains version info that starts with 3 (Eros)
        if (data && data.version && data.version.startsWith('3')) {
            return true;
        }
        return false;
    })
    .catch(() => {
        // Any error means the API is not compatible
        return false;
    });
}