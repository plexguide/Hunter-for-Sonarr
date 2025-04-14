document.addEventListener('DOMContentLoaded', function() {
    // Keep only log-related functionality
    const logContainer = document.getElementById('log-container');
    const statusIndicator = document.querySelector('.status-indicator');
    const statusText = document.querySelector('.status-text');
    const autoScrollCheckbox = document.getElementById('auto-scroll-checkbox');
    
    // Theme toggle functionality
    const themeToggle = document.getElementById('toggle-theme');
    themeToggle.addEventListener('click', function() {
        document.body.classList.toggle('dark-mode');
        
        // Save theme preference
        const isDarkMode = document.body.classList.contains('dark-mode');
        fetch('/api/settings/theme', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ dark_mode: isDarkMode })
        });
        
        // Update toggle button icon
        this.textContent = isDarkMode ? '☀️' : '🌙';
    });
    
    // Load theme setting
    fetch('/api/settings/theme')
        .then(response => response.json())
        .then(data => {
            if (data.dark_mode) {
                document.body.classList.add('dark-mode');
                themeToggle.textContent = '☀️';
            } else {
                document.body.classList.remove('dark-mode');
                themeToggle.textContent = '🌙';
            }
        });
    
    // Clear logs button
    const clearLogsButton = document.getElementById('clear-logs');
    clearLogsButton.addEventListener('click', function() {
        logContainer.innerHTML = '';
    });

    // WebSocket connection for logs
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/logs`);
    
    ws.onopen = function() {
        statusIndicator.classList.add('connected');
        statusText.textContent = 'Connected';
    };
    
    ws.onclose = function() {
        statusIndicator.classList.remove('connected');
        statusText.textContent = 'Disconnected';
        
        // Attempt to reconnect after 5 seconds
        setTimeout(function() {
            window.location.reload();
        }, 5000);
    };
    
    ws.onerror = function() {
        statusIndicator.classList.remove('connected');
        statusText.textContent = 'Connection Error';
    };
    
    ws.onmessage = function(event) {
        const logEntry = JSON.parse(event.data);
        addLogEntry(logEntry);
    };
    
    function addLogEntry(logEntry) {
        const logLine = document.createElement('div');
        logLine.className = `log-line ${logEntry.level.toLowerCase()}`;
        logLine.textContent = logEntry.message;
        
        logContainer.appendChild(logLine);
        
        // Auto-scroll if enabled
        if (autoScrollCheckbox.checked) {
            logLine.scrollIntoView({ behavior: 'smooth' });
        }
    }
});