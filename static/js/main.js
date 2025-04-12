// Main entry point for Huntarr application

// Wait for DOM content to be loaded before initializing the app
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the core application
    if (window.huntarrApp) {
        window.huntarrApp.init();
    } else {
        console.error('Error: Huntarr core module not loaded');
    }
});