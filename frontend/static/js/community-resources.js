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
    // First check if the community hub card exists
    const communityHubCard = document.querySelector('.community-hub-card');
    if (!communityHubCard) {
        console.log('[Community] Community hub card not found in DOM');
        return;
    }
    
    // Fetch general settings to determine visibility
    fetch('/api/settings/general')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('[Community] Loaded general settings:', data);
            
            // Check if the setting exists and is false
            if (data.display_community_resources === false) {
                // Hide the community hub card
                console.log('[Community] Hiding community resources section');
                communityHubCard.style.display = 'none';
            } else {
                // Show the community hub card (default)
                console.log('[Community] Showing community resources section');
                communityHubCard.style.display = '';
            }
        })
        .catch(error => {
            console.error('[Community] Error loading general settings:', error);
            // Default to showing if there's an error
            communityHubCard.style.display = '';
        });
} 