(function() {
    // Check for dark mode preference from API stored in localStorage
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
})();
