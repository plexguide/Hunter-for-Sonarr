(function() {
    // Store logo URL consistently across the app
    const LOGO_URL = 'https://github.com/plexguide/Huntarr/blob/main/logo/64.png?raw=true';
    
    // Immediately inject a hidden logo element to preload it
    document.write(`<img src="${LOGO_URL}" style="display: none;" id="preloaded-logo" />`);
    
    // Check for dark mode preference from localStorage
    const prefersDarkMode = localStorage.getItem('huntarr-dark-mode') === 'true';
    
    // Apply dark theme immediately if needed
    if (prefersDarkMode) {
        document.documentElement.classList.add('dark-theme');
        
        // Add inline style to immediately set background color
        // This prevents flash before the CSS files load
        const style = document.createElement('style');
        style.textContent = `
            body, html { 
                background-color: #1a1d24 !important; 
                color: #f8f9fa !important;
            }
            .sidebar {
                background-color: #121212 !important;
            }
            .top-bar {
                background-color: #252a34 !important;
            }
        `;
        document.head.appendChild(style);
    }
    
    // Store the logo URL in localStorage for persistence across page loads
    localStorage.setItem('huntarr-logo-url', LOGO_URL);
    
    // Create a global function to apply the logo to all logo elements
    window.applyLogoToAllElements = function() {
        const logoUrl = localStorage.getItem('huntarr-logo-url') || LOGO_URL;
        const logoElements = document.querySelectorAll('.logo, .login-logo');
        
        logoElements.forEach(img => {
            // Set src immediately and ensure it's loaded
            img.src = logoUrl;
            
            // Add inline style to prevent layout shift
            img.style.visibility = 'visible';
        });
    };
    
    // Apply logo as soon as DOM is interactive
    document.addEventListener('DOMContentLoaded', function() {
        window.applyLogoToAllElements();
        
        // Also set up MutationObserver to catch any dynamically added logo elements
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.addedNodes.length) {
                    window.applyLogoToAllElements();
                }
            });
        });
        
        observer.observe(document.body, { childList: true, subtree: true });
    });
    
    // Ensure logo is loaded when navigating with AJAX
    window.addEventListener('load', window.applyLogoToAllElements);
})();
