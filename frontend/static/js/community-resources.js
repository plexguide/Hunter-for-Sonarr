/**
 * Huntarr - Community Resources Module
 * Handles showing/hiding the Community Resources section on the home page
 * based on user settings.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the community resources visibility
    initCommunityResourcesVisibility();
    
    // Also listen for settings changes that might affect visibility
    window.addEventListener('settings-saved', function() {
        initCommunityResourcesVisibility();
    });
});

/**
 * Initializes the visibility of the Community Resources section
 * based on the display_community_resources setting in general.json
 */
function initCommunityResourcesVisibility() {
    // Check if the community hub card exists
    const communityHubCard = document.querySelector('.community-hub-card');
    if (!communityHubCard) {
        console.log('[Community] Community hub card not found in DOM');
        return;
    }
    
    // Check if the Huntarr support section exists
    const huntarrSupportSection = document.querySelector('#huntarr-support-section');
    if (!huntarrSupportSection) {
        console.log('[Community] Huntarr support section not found in DOM');
    }
    
    // Fetch general settings to determine visibility
    HuntarrUtils.fetchWithTimeout('./api/settings/general')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('[Community] Loaded general settings:', data);
            
            // Handle Community Resources visibility
            if (data.display_community_resources === false) {
                // Hide the community hub card
                console.log('[Community] Hiding community resources section');
                communityHubCard.style.display = 'none';
            } else {
                // Show the community hub card (default)
                console.log('[Community] Showing community resources section');
                communityHubCard.style.display = '';
            }
            
            // Handle Huntarr Support visibility (defaults to true)
            if (huntarrSupportSection) {
                if (data.display_huntarr_support === false) {
                    // Hide the Huntarr support section
                    console.log('[Community] Hiding Huntarr support section');
                    huntarrSupportSection.style.display = 'none';
                } else {
                    // Show the Huntarr support section (default)
                    console.log('[Community] Showing Huntarr support section');
                    huntarrSupportSection.style.display = '';
                }
            }
        })
        .catch(error => {
            console.error('[Community] Error loading general settings:', error);
            // Default to showing if there's an error
            communityHubCard.style.display = '';
            if (huntarrSupportSection) {
                huntarrSupportSection.style.display = '';
            }
        });
} 