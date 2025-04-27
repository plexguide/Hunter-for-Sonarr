/**
 * Huntarr - User Settings Page
 * Handles user profile management functionality
 */

// Immediately execute this function to avoid global scope pollution
(function() {
    // Wait for the DOM to be fully loaded
    document.addEventListener('DOMContentLoaded', function() {
        console.log('User settings page loaded');
        
        // Initialize user settings functionality
        initUserPage();
    });
    
    function initUserPage() {
        // Set active nav item
        const navItems = document.querySelectorAll('.nav-item');
        navItems.forEach(item => item.classList.remove('active'));
        const userNav = document.getElementById('userNav');
        if (userNav) userNav.classList.add('active');
        
        const pageTitleElement = document.getElementById('currentPageTitle');
        if (pageTitleElement) pageTitleElement.textContent = 'User Settings';
        
        // Apply dark mode
        document.body.classList.add('dark-theme');
        localStorage.setItem('huntarr-dark-mode', 'true');
        
        // Fetch user data
        fetchUserInfo();
    }
    
    // Function to fetch user information
    function fetchUserInfo() {
        fetch('/api/user/info')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                // Update username elements
                updateUsernameElements(data.username);
                
                // Update 2FA status
                update2FAStatus(data.is_2fa_enabled);
            })
            .catch(error => {
                console.error('Error loading user info:', error);
                // Show error state in the UI
                showErrorState();
            });
    }
    
    // Helper functions
    function updateUsernameElements(username) {
        if (!username) return;
        
        const usernameElements = [
            document.getElementById('username'),
            document.getElementById('currentUsername')
        ];
        
        usernameElements.forEach(element => {
            if (element) {
                element.textContent = username;
            }
        });
    }
    
    function update2FAStatus(isEnabled) {
        const statusElement = document.getElementById('twoFactorEnabled');
        if (statusElement) {
            statusElement.textContent = isEnabled ? 'Enabled' : 'Disabled';
        }
        
        // Update visibility of relevant sections
        updateVisibility('enableTwoFactorSection', !isEnabled);
        updateVisibility('setupTwoFactorSection', false);
        updateVisibility('disableTwoFactorSection', isEnabled);
    }
    
    function updateVisibility(elementId, isVisible) {
        const element = document.getElementById(elementId);
        if (element) {
            element.style.display = isVisible ? 'block' : 'none';
        }
    }
    
    function showErrorState() {
        const usernameElement = document.getElementById('currentUsername');
        if (usernameElement) {
            usernameElement.textContent = 'Error loading username';
        }
        
        const statusElement = document.getElementById('twoFactorEnabled');
        if (statusElement) {
            statusElement.textContent = 'Error loading status';
        }
    }
})();
