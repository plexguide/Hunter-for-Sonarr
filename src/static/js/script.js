document.addEventListener('DOMContentLoaded', function() {
    // Tab functionality
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Only handle the logs tab now
            const tabName = tab.dataset.tab;
            if (tabName === 'logs') {
                document.querySelectorAll('.tab-pane').forEach(pane => {
                    pane.classList.remove('active');
                });
                document.querySelectorAll('.tab').forEach(t => {
                    t.classList.remove('active');
                });
                document.getElementById(tabName).classList.add('active');
                tab.classList.add('active');
            }
        });
    });

    // Theme toggle
    const themeToggle = document.getElementById('toggle-theme');
    themeToggle.addEventListener('click', toggleTheme);

    // Log clear button
    const clearButton = document.getElementById('clear-logs');
    clearButton.addEventListener('click', () => {
        document.getElementById('log-container').innerHTML = '';
    });
    
    // Remove all settings-related code (form submissions, etc.)
    // ...existing code for log handling...
});