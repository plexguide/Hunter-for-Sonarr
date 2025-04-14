document.addEventListener('DOMContentLoaded', function() {
    // Theme toggle functionality
    const themeToggle = document.getElementById('themeToggle');
    const themeLabel = document.getElementById('themeLabel');
    
    // Check if dark mode is saved in localStorage
    const darkMode = localStorage.getItem('darkMode') === 'true';
    if (darkMode) {
        document.body.classList.add('dark-mode');
        themeToggle.checked = true;
        themeLabel.textContent = 'Dark Mode';
    }
    
    // Theme toggle event listener
    themeToggle.addEventListener('change', function() {
        document.body.classList.toggle('dark-mode');
        const isDarkMode = document.body.classList.contains('dark-mode');
        localStorage.setItem('darkMode', isDarkMode);
        themeLabel.textContent = isDarkMode ? 'Dark Mode' : 'Light Mode';
    });
    
    // Logs functionality
    const logsContainer = document.getElementById('logs');
    const clearLogsButton = document.getElementById('clearLogs');
    const autoScrollCheckbox = document.getElementById('autoScroll');
    const statusIndicator = document.getElementById('status');
    
    // Clear logs button
    clearLogsButton.addEventListener('click', function() {
        logsContainer.innerHTML = '';
    });
    
    // WebSocket connection for logs
    function connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/logs`;
        const ws = new WebSocket(wsUrl);
        
        ws.onopen = function() {
            statusIndicator.textContent = 'Connected';
            statusIndicator.className = 'status-connected';
        };
        
        ws.onclose = function() {
            statusIndicator.textContent = 'Disconnected';
            statusIndicator.className = 'status-disconnected';
            
            // Try to reconnect after 5 seconds
            setTimeout(connectWebSocket, 5000);
        };
        
        ws.onerror = function() {
            statusIndicator.textContent = 'Error';
            statusIndicator.className = 'status-error';
        };
        
        ws.onmessage = function(event) {
            try {
                const logEntry = JSON.parse(event.data);
                addLogEntry(logEntry);
            } catch (e) {
                console.error('Error parsing log message:', e);
            }
        };
        
        return ws;
    }
    
    function addLogEntry(logEntry) {
        const logLine = document.createElement('div');
        logLine.className = `log-entry ${logEntry.level.toLowerCase()}`;
        
        // Format timestamp if it exists
        if (logEntry.timestamp) {
            const timestamp = document.createElement('span');
            timestamp.className = 'log-timestamp';
            timestamp.textContent = logEntry.timestamp;
            logLine.appendChild(timestamp);
        }
        
        // Add log message
        const message = document.createElement('span');
        message.className = 'log-message';
        message.textContent = logEntry.message;
        logLine.appendChild(message);
        
        logsContainer.appendChild(logLine);
        
        // Auto-scroll if enabled
        if (autoScrollCheckbox.checked) {
            logLine.scrollIntoView({ behavior: 'smooth' });
        }
    }
    
    // Initialize WebSocket connection
    connectWebSocket();
});