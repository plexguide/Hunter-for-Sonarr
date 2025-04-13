/**
 * Huntarr Settings Synchronization Utility
 * 
 * This module prevents race conditions between different parts of the app
 * that might try to update settings simultaneously.
 */

(function() {
    // Track when settings are being loaded/saved to prevent conflicts
    let settingsLock = false;
    let pendingReloads = {};
    
    // Function to acquire lock
    window.acquireSettingsLock = function(timeoutMs = 5000) {
        if (settingsLock) {
            console.log('Settings lock already acquired, waiting...');
            return new Promise((resolve) => {
                // Wait for the lock to be released
                const checkInterval = setInterval(() => {
                    if (!settingsLock) {
                        clearInterval(checkInterval);
                        settingsLock = true;
                        resolve(true);
                    }
                }, 100);
                
                // Set a timeout to prevent infinite waiting
                setTimeout(() => {
                    clearInterval(checkInterval);
                    console.warn('Settings lock timeout exceeded, forcing acquisition');
                    settingsLock = true;
                    resolve(true);
                }, timeoutMs);
            });
        }
        
        settingsLock = true;
        return Promise.resolve(true);
    };
    
    // Function to release lock
    window.releaseSettingsLock = function() {
        settingsLock = false;
        
        // Process any pending reloads
        Object.keys(pendingReloads).forEach(app => {
            if (pendingReloads[app]) {
                console.log(`Processing pending reload for ${app}`);
                pendingReloads[app] = false;
                
                // Determine which reload function to call
                if (app === 'sonarr' && window.huntarrApp?.sonarrModule?.loadSettings) {
                    window.huntarrApp.sonarrModule.loadSettings();
                } else if (app === 'radarr' && window.huntarrApp?.radarrModule?.loadSettings) {
                    window.huntarrApp.radarrModule.loadSettings();
                } else if (app === 'lidarr' && window.huntarrApp?.lidarrModule?.loadSettings) {
                    window.huntarrApp.lidarrModule.loadSettings();
                } else if (app === 'readarr' && window.huntarrApp?.readarrModule?.loadSettings) {
                    window.huntarrApp.readarrModule.loadSettings();
                }
            }
        });
    };
    
    // Function to schedule a reload
    window.scheduleSettingsReload = function(app) {
        pendingReloads[app] = true;
        
        // If lock is not active, process immediately
        if (!settingsLock) {
            window.releaseSettingsLock();
        }
    };
    
    // Add to document load to ensure settings are loaded properly on page load
    document.addEventListener('DOMContentLoaded', function() {
        // Ensure all modules hook into the lock system
        const originalFetch = window.fetch;
        window.fetch = function(url, options) {
            // If this is a settings API call, manage the lock
            if (typeof url === 'string' && 
                (url.includes('/api/settings') || url.includes('/api/app-settings'))) {
                    
                if (options?.method === 'POST') {
                    // For POST requests, acquire lock before and release after
                    return acquireSettingsLock()
                        .then(() => originalFetch(url, options))
                        .then(response => {
                            // Don't release lock until response is processed
                            return response.clone().json()
                                .then(data => {
                                    setTimeout(() => releaseSettingsLock(), 200);
                                    return response;
                                })
                                .catch(() => {
                                    setTimeout(() => releaseSettingsLock(), 200);
                                    return response;
                                });
                        })
                        .catch(err => {
                            releaseSettingsLock();
                            throw err;
                        });
                } else {
                    // For GET requests, just manage the lock
                    return acquireSettingsLock()
                        .then(() => originalFetch(url, options))
                        .then(response => {
                            setTimeout(() => releaseSettingsLock(), 200);
                            return response;
                        })
                        .catch(err => {
                            releaseSettingsLock();
                            throw err;
                        });
                }
            }
            
            // For non-settings requests, just pass through
            return originalFetch(url, options);
        };
    });
})();
