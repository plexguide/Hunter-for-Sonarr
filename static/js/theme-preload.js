(function() {
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
    
    // Preload the logo image to prevent flashing during navigation
    const preloadLogo = new Image();
    preloadLogo.src = 'https://github.com/plexguide/Huntarr/blob/main/logo/64.png?raw=true';
    preloadLogo.fetchPriority = 'high';
    
    // Create a hidden div to store the preloaded image
    window.addEventListener('DOMContentLoaded', function() {
        const imageCache = document.createElement('div');
        imageCache.style.display = 'none';
        imageCache.innerHTML = `<img src="${preloadLogo.src}" id="preloaded-logo">`;
        document.body.appendChild(imageCache);
        
        // Update all logo instances in the document
        const logoImages = document.querySelectorAll('.logo, .login-logo');
        logoImages.forEach(img => {
            img.src = preloadLogo.src;
        });
    });
})();
