/**
 * Hourly API Cap Handling for Huntarr
 * Fetches and updates the hourly API usage indicators on the dashboard
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initial load of hourly cap data
    loadHourlyCapData();
    
    // Set up polling to refresh the hourly cap data every 30 seconds
    setInterval(loadHourlyCapData, 30000);
});

/**
 * Load hourly API cap data from the server
 */
function loadHourlyCapData() {
    fetch('/api/hourly-caps')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.success && data.caps) {
                updateHourlyCapDisplay(data.caps, data.limit || 20);
            } else {
                console.error('Failed to load hourly API cap data:', data.message || 'Unknown error');
            }
        })
        .catch(error => {
            console.error('Error fetching hourly API cap data:', error);
        });
}

/**
 * Update the hourly API cap indicators for each app
 * 
 * @param {Object} caps - Object containing hourly API usage for each app
 * @param {Number} limit - The maximum hourly API limit (from settings)
 */
function updateHourlyCapDisplay(caps, limit) {
    // Update each app's API cap indicator
    const apps = ['sonarr', 'radarr', 'lidarr', 'readarr', 'whisparr', 'eros'];
    
    apps.forEach(app => {
        // If we have data for this app
        if (caps[app]) {
            // Update the API count
            const countElement = document.getElementById(`${app}-api-count`);
            if (countElement) {
                countElement.textContent = caps[app].api_hits || 0;
            }
            
            // Update the API limit
            const limitElement = document.getElementById(`${app}-api-limit`);
            if (limitElement) {
                limitElement.textContent = limit;
            }
            
            // Update the status indicator
            const statusElement = document.getElementById(`${app}-hourly-cap`);
            if (statusElement) {
                const usage = caps[app].api_hits || 0;
                const percentage = (usage / limit) * 100;
                
                // Remove existing status classes
                statusElement.classList.remove('good', 'warning', 'danger');
                
                // Add appropriate status class based on usage percentage
                if (percentage >= 100) {
                    statusElement.classList.add('danger');
                } else if (percentage >= 75) {
                    statusElement.classList.add('warning');
                } else {
                    statusElement.classList.add('good');
                }
            }
        }
    });
}
