/**
 * Huntarr Logs Module
 * Handles all logging functionality including streaming, filtering, search, and display
 */

window.LogsModule = {
    // Current state
    eventSources: {},
    currentLogApp: 'all',
    autoScroll: true,
    autoScrollWasEnabled: false,
    
    // Element references
    elements: {},
    
    // Initialize the logs module
    init: function() {
        console.log('[LogsModule] Initializing logs module...');
        this.cacheElements();
        this.setupEventListeners();
    },
    
    // Cache DOM elements for better performance
    cacheElements: function() {
        // Logs elements
        this.elements.logsContainer = document.getElementById('logsContainer');
        this.elements.autoScrollCheckbox = document.getElementById('autoScrollCheckbox');
        this.elements.clearLogsButton = document.getElementById('clearLogsButton');
        this.elements.logConnectionStatus = document.getElementById('logConnectionStatus');
        
        // Log search elements
        this.elements.logSearchInput = document.getElementById('logSearchInput');
        this.elements.logSearchButton = document.getElementById('logSearchButton');
        this.elements.clearSearchButton = document.getElementById('clearSearchButton');
        this.elements.logSearchResults = document.getElementById('logSearchResults');
        
        // Log level filter element
        this.elements.logLevelSelect = document.getElementById('logLevelSelect');
        
        // Log dropdown elements
        this.elements.logOptions = document.querySelectorAll('.log-option');
        this.elements.currentLogApp = document.getElementById('current-log-app');
        this.elements.logDropdownBtn = document.querySelector('.log-dropdown-btn');
        this.elements.logDropdownContent = document.querySelector('.log-dropdown-content');
    },
    
    // Set up event listeners for logging functionality
    setupEventListeners: function() {
        // Log auto-scroll setting
        if (this.elements.autoScrollCheckbox) {
            this.elements.autoScrollCheckbox.addEventListener('change', (e) => {
                this.autoScroll = e.target.checked;
            });
        }
        
        // Clear logs button
        if (this.elements.clearLogsButton) {
            this.elements.clearLogsButton.addEventListener('click', () => this.clearLogs());
        }
        
        // Log search functionality
        if (this.elements.logSearchButton) {
            this.elements.logSearchButton.addEventListener('click', () => this.searchLogs());
        }
        
        if (this.elements.logSearchInput) {
            this.elements.logSearchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.searchLogs();
                }
            });
            
            // Clear search when input is emptied
            this.elements.logSearchInput.addEventListener('input', (e) => {
                if (e.target.value.trim() === '') {
                    this.clearLogSearch();
                }
            });
        }
        
        // Clear search button
        if (this.elements.clearSearchButton) {
            this.elements.clearSearchButton.addEventListener('click', () => this.clearLogSearch());
        }
        
        // Log options dropdown
        this.elements.logOptions.forEach(option => {
            option.addEventListener('click', (e) => this.handleLogOptionChange(e));
        });
        
        // Log dropdown toggle
        if (this.elements.logDropdownBtn) {
            this.elements.logDropdownBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.elements.logDropdownContent.classList.toggle('show');
            });
            
            // Close dropdown when clicking outside
            document.addEventListener('click', (e) => {
                if (!e.target.closest('.log-dropdown') && this.elements.logDropdownContent.classList.contains('show')) {
                    this.elements.logDropdownContent.classList.remove('show');
                }
            });
        }
        
        // LOG LEVEL FILTER: Listen for change on #logLevelSelect
        const logLevelSelect = document.getElementById('logLevelSelect');
        if (logLevelSelect) {
            logLevelSelect.addEventListener('change', (e) => {
                this.filterLogsByLevel(e.target.value);
            });
        }
        
        // LOGS: Listen for change on #logAppSelect
        const logAppSelect = document.getElementById('logAppSelect');
        if (logAppSelect) {
            logAppSelect.addEventListener('change', (e) => {
                const app = e.target.value;
                this.handleLogOptionChange(app);
            });
        }
    },
    
    // Handle log option dropdown changes
    handleLogOptionChange: function(app) {
        if (app && app.target && typeof app.target.value === 'string') {
            app = app.target.value;
        } else if (app && app.target && typeof app.target.getAttribute === 'function') {
            app = app.target.getAttribute('data-app');
        }
        if (!app || app === this.currentLogApp) return;
        
        // Update the select value
        const logAppSelect = document.getElementById('logAppSelect');
        if (logAppSelect) logAppSelect.value = app;
        
        // Update the current log app text with proper capitalization
        let displayName = app.charAt(0).toUpperCase() + app.slice(1);
        if (app === 'whisparr') displayName = 'Whisparr V2';
        else if (app === 'eros') displayName = 'Whisparr V3';
        else if (app === 'hunting') displayName = 'Hunt Manager';
        if (this.elements.currentLogApp) this.elements.currentLogApp.textContent = displayName;
        
        // Switch to the selected app logs
        this.currentLogApp = app;
        this.clearLogs();
        this.connectToLogs();
    },
    
    // Connect to logs stream
    connectToLogs: function() {
        // Disconnect any existing event sources
        this.disconnectAllEventSources();
        
        // Connect to logs stream for the currentLogApp
        this.connectEventSource(this.currentLogApp);
        if (this.elements.logConnectionStatus) {
            this.elements.logConnectionStatus.textContent = 'Connecting...';
            this.elements.logConnectionStatus.className = '';
        }
    },
    
    // Connect to event source for streaming logs
    connectEventSource: function(appType) {
        // Close any existing event source
        if (this.eventSources.logs) {
            this.eventSources.logs.close();
        }
        
        try {
            // Append the app type to the URL
            const eventSource = new EventSource(`./logs?app=${appType}`);
            
            eventSource.onopen = () => {
                if (this.elements.logConnectionStatus) {
                    this.elements.logConnectionStatus.textContent = 'Connected';
                    this.elements.logConnectionStatus.className = 'status-connected';
                }
            };
            
            eventSource.onmessage = (event) => {
                if (!this.elements.logsContainer) return;
                
                try {
                    const logString = event.data;
                    
                    // Filter out broken JSON fragments and other non-log content
                    if (this.isJsonFragment(logString) || this.isInvalidLogLine(logString)) {
                        return; // Skip processing this line
                    }
                    
                    // Updated regex to handle timezone-aware timestamps
                    // Example: 2025-06-05 01:28:03 America/New_York - huntarr.radarr - INFO - Message
                    const logRegex = /^(?:\[(\w+)\]\s)?([^\s]+\s[^\s:]+(?:\s[^\s-]+)?)\s*-\s+([\w\.]+)\s+-\s+(\w+)\s+-\s+(.*)$/;
                    const match = logString.match(logRegex);

                    // Determine the app type for this log message
                    let logAppType = 'system';
                    
                    if (match && match[1]) {
                        logAppType = match[1].toLowerCase();
                    } else if (match && match[3]) {
                        const loggerParts = match[3].split('.');
                        if (loggerParts.length > 1) {
                            const possibleApp = loggerParts[1].toLowerCase();
                            if (['sonarr', 'radarr', 'lidarr', 'readarr', 'whisparr', 'eros', 'swaparr', 'hunting'].includes(possibleApp)) {
                                logAppType = possibleApp;
                            }
                        }
                    } else {
                        // Fallback detection patterns
                        const appTagMatch = logString.match(/^\[(\w+)\]/);
                        if (appTagMatch) {
                            const possibleApp = appTagMatch[1].toLowerCase();
                            if (['sonarr', 'radarr', 'lidarr', 'readarr', 'whisparr', 'eros', 'swaparr', 'hunting'].includes(possibleApp)) {
                                logAppType = possibleApp;
                            }
                        }
                        
                        if (logString.includes('[hunting]')) {
                            logAppType = 'hunting';
                        }
                    }
                    
                    // Check if this log should be displayed based on the selected app
                    const currentApp = this.currentLogApp === 'hunting' ? 'hunting' : this.currentLogApp;
                    const shouldDisplay = this.currentLogApp === 'all' || currentApp === logAppType;

                    if (!shouldDisplay) return;

                    const logEntry = document.createElement('div');
                    logEntry.className = 'log-entry';

                    if (match) {
                        const [, appName, timestamp, loggerName, level, message] = match;
                        
                        // Parse timestamp to extract date and time (ignore timezone for display)
                        let date = '';
                        let time = '';
                        
                        if (timestamp) {
                            const parts = timestamp.split(' ');
                            date = parts[0] || '';
                            time = parts[1] || '';
                        }
                        
                        // Create level badge
                        const levelClass = level.toLowerCase();
                        let levelBadge = '';
                        
                        switch(levelClass) {
                            case 'error':
                                levelBadge = `<span class="log-level-badge log-level-error">Error</span>`;
                                break;
                            case 'warning':
                            case 'warn':
                                levelBadge = `<span class="log-level-badge log-level-warning">Warning</span>`;
                                break;
                            case 'info':
                                levelBadge = `<span class="log-level-badge log-level-info">Information</span>`;
                                break;
                            case 'debug':
                                levelBadge = `<span class="log-level-badge log-level-debug">Debug</span>`;
                                break;
                            case 'fatal':
                            case 'critical':
                                levelBadge = `<span class="log-level-badge log-level-fatal">Fatal</span>`;
                                break;
                            default:
                                levelBadge = `<span class="log-level-badge log-level-info">Information</span>`;
                        }
                        
                        // Determine app source for display
                        let appSource = 'SYSTEM';
                        if (loggerName.includes('.')) {
                            const parts = loggerName.split('.');
                            if (parts.length > 1) {
                                if (this.currentLogApp !== 'all' && this.currentLogApp !== 'system') {
                                    appSource = 'SYSTEM';
                                } else {
                                    appSource = parts[1].toUpperCase();
                                }
                            }
                        }
                        
                        logEntry.innerHTML = `
                            <div class="log-entry-row">
                                <span class="log-timestamp">
                                    <span class="date">${date}</span>
                                    <span class="time">${time}</span>
                                </span>
                                ${levelBadge}
                                <span class="log-source">${appSource}</span>
                                <span class="log-message">${message}</span>
                            </div>
                        `;
                        logEntry.classList.add(`log-${levelClass}`);
                    } else {
                        // Fallback for lines that don't match the expected format
                        let fallbackTime = '--:--:--';
                        let fallbackDate = '--';
                        
                        // Try to extract timestamp from raw string
                        const timeMatch = logString.match(/(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})/);
                        if (timeMatch) {
                            fallbackDate = timeMatch[1];
                            fallbackTime = timeMatch[2];
                        }
                        
                        logEntry.innerHTML = `
                            <div class="log-entry-row">
                                <span class="log-timestamp">
                                    <span class="date">${fallbackDate}</span>
                                    <span class="time">${fallbackTime}</span>
                                </span>
                                <span class="log-level-badge log-level-info">Information</span>
                                <span class="log-source">SYSTEM</span>
                                <span class="log-message">${logString}</span>
                            </div>
                        `;
                        
                        // Basic level detection
                        if (logString.includes('ERROR')) logEntry.classList.add('log-error');
                        else if (logString.includes('WARN') || logString.includes('WARNING')) logEntry.classList.add('log-warning');
                        else if (logString.includes('DEBUG')) logEntry.classList.add('log-debug');
                        else logEntry.classList.add('log-info');
                    }
                    
                    // Add to logs container
                    this.insertLogInChronologicalOrder(logEntry);
                    
                    // Apply current log level filter
                    const currentLogLevel = this.elements.logLevelSelect ? this.elements.logLevelSelect.value : 'all';
                    if (currentLogLevel !== 'all') {
                        this.applyFilterToSingleEntry(logEntry, currentLogLevel);
                    }
                    
                    // Special event dispatching for Swaparr logs
                    if (logAppType === 'swaparr' && this.currentLogApp === 'swaparr') {
                        const swaparrEvent = new CustomEvent('swaparrLogReceived', {
                            detail: {
                                logData: match && match[5] ? match[5] : logString
                            }
                        });
                        document.dispatchEvent(swaparrEvent);
                    }
                    
                    // Auto-scroll to top
                    if (this.autoScroll) {
                        window.scrollTo({
                            top: 0,
                            behavior: 'smooth'
                        });
                    }
                } catch (error) {
                    console.error('[LogsModule] Error processing log message:', error, 'Data:', event.data);
                }
            };
            
            eventSource.onerror = (err) => {
                console.error(`[LogsModule] EventSource error for app ${this.currentLogApp}:`, err);
                if (this.elements.logConnectionStatus) {
                    this.elements.logConnectionStatus.textContent = 'Error/Disconnected';
                    this.elements.logConnectionStatus.className = 'status-error';
                }
                
                if (this.eventSources.logs) {
                    this.eventSources.logs.close();
                }
                
                // Auto-reconnect logic
                setTimeout(() => {
                    if (window.huntarrUI && window.huntarrUI.currentSection === 'logs') {
                        this.connectToLogs();
                    }
                }, 5000);
            };
            
            this.eventSources.logs = eventSource;
        } catch (e) {
            console.error(`[LogsModule] Failed to create EventSource for app ${appType}:`, e);
            if (this.elements.logConnectionStatus) {
                this.elements.logConnectionStatus.textContent = 'Failed to connect';
                this.elements.logConnectionStatus.className = 'status-error';
            }
        }
    },
    
    // Disconnect all event sources
    disconnectAllEventSources: function() {
        Object.keys(this.eventSources).forEach(key => {
            const source = this.eventSources[key];
            if (source) {
                try {
                    if (source.readyState !== EventSource.CLOSED) {
                        source.close();
                        console.log(`[LogsModule] Closed event source for ${key}.`);
                    }
                } catch (e) {
                    console.error(`[LogsModule] Error closing event source for ${key}:`, e);
                }
            }
            delete this.eventSources[key];
        });
        
        if (this.elements.logConnectionStatus) {
            this.elements.logConnectionStatus.textContent = 'Disconnected';
            this.elements.logConnectionStatus.className = 'status-disconnected';
        }
    },
    
    // Clear all logs
    clearLogs: function() {
        if (this.elements.logsContainer) {
            this.elements.logsContainer.innerHTML = '';
        }
    },
    
    // Insert log entry in chronological order
    insertLogInChronologicalOrder: function(newLogEntry) {
        if (!this.elements.logsContainer || !newLogEntry) return;
        
        const newTimestamp = this.parseLogTimestamp(newLogEntry);
        
        if (!newTimestamp) {
            this.elements.logsContainer.appendChild(newLogEntry);
            return;
        }
        
        const existingEntries = Array.from(this.elements.logsContainer.children);
        
        if (existingEntries.length === 0) {
            this.elements.logsContainer.appendChild(newLogEntry);
            return;
        }
        
        let insertPosition = null;
        
        for (let i = 0; i < existingEntries.length; i++) {
            const existingTimestamp = this.parseLogTimestamp(existingEntries[i]);
            
            if (!existingTimestamp) continue;
            
            if (newTimestamp > existingTimestamp) {
                insertPosition = existingEntries[i];
                break;
            }
        }
        
        if (insertPosition) {
            this.elements.logsContainer.insertBefore(newLogEntry, insertPosition);
        } else {
            this.elements.logsContainer.appendChild(newLogEntry);
        }
    },
    
    // Parse timestamp from log entry DOM element
    parseLogTimestamp: function(logEntry) {
        if (!logEntry) return null;
        
        try {
            const dateSpan = logEntry.querySelector('.log-timestamp .date');
            const timeSpan = logEntry.querySelector('.log-timestamp .time');
            
            if (!dateSpan || !timeSpan) return null;
            
            const dateText = dateSpan.textContent.trim();
            const timeText = timeSpan.textContent.trim();
            
            if (!dateText || !timeText || dateText === '--' || timeText === '--:--:--') {
                return null;
            }
            
            const timestampString = `${dateText} ${timeText}`;
            const timestamp = new Date(timestampString);
            
            return isNaN(timestamp.getTime()) ? null : timestamp;
        } catch (error) {
            console.warn('[LogsModule] Error parsing log timestamp:', error);
            return null;
        }
    },
    
    // Search logs functionality
    searchLogs: function() {
        if (!this.elements.logsContainer || !this.elements.logSearchInput) return;
        
        const searchText = this.elements.logSearchInput.value.trim().toLowerCase();
        
        if (!searchText) {
            this.clearLogSearch();
            return;
        }
        
        if (this.elements.clearSearchButton) {
            this.elements.clearSearchButton.style.display = 'block';
        }
        
        const logEntries = Array.from(this.elements.logsContainer.querySelectorAll('.log-entry'));
        let matchCount = 0;
        
        const MAX_ENTRIES_TO_PROCESS = 300;
        const processedLogEntries = logEntries.slice(0, MAX_ENTRIES_TO_PROCESS);
        const remainingCount = Math.max(0, logEntries.length - MAX_ENTRIES_TO_PROCESS);
        
        processedLogEntries.forEach((entry, index) => {
            const entryText = entry.textContent.toLowerCase();
            
            if (entryText.includes(searchText)) {
                entry.style.display = '';
                matchCount++;
                this.simpleHighlightMatch(entry, searchText);
            } else {
                entry.style.display = 'none';
            }
        });
        
        if (remainingCount > 0) {
            logEntries.slice(MAX_ENTRIES_TO_PROCESS).forEach(entry => {
                const entryText = entry.textContent.toLowerCase();
                if (entryText.includes(searchText)) {
                    entry.style.display = '';
                    matchCount++;
                } else {
                    entry.style.display = 'none';
                }
            });
        }
        
        if (this.elements.logSearchResults) {
            let resultsText = `Found ${matchCount} matching log entries`;
            this.elements.logSearchResults.textContent = resultsText;
            this.elements.logSearchResults.style.display = 'block';
        }
        
        if (this.elements.autoScrollCheckbox && this.elements.autoScrollCheckbox.checked) {
            this.autoScrollWasEnabled = true;
            this.elements.autoScrollCheckbox.checked = false;
        }
    },
    
    // Simple highlighting method
    simpleHighlightMatch: function(logEntry, searchText) {
        if (searchText.length < 2) return;
        
        if (!logEntry.hasAttribute('data-original-html')) {
            logEntry.setAttribute('data-original-html', logEntry.innerHTML);
        }
        
        const html = logEntry.getAttribute('data-original-html');
        const escapedSearchText = searchText.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        
        const regex = new RegExp(`(${escapedSearchText})`, 'gi');
        const newHtml = html.replace(regex, '<span class="search-highlight">$1</span>');
        
        logEntry.innerHTML = newHtml;
    },
    
    // Clear log search
    clearLogSearch: function() {
        if (!this.elements.logsContainer) return;
        
        if (this.elements.logSearchInput) {
            this.elements.logSearchInput.value = '';
        }
        
        if (this.elements.clearSearchButton) {
            this.elements.clearSearchButton.style.display = 'none';
        }
        
        if (this.elements.logSearchResults) {
            this.elements.logSearchResults.style.display = 'none';
        }
        
        const allLogEntries = this.elements.logsContainer.querySelectorAll('.log-entry');
        
        Array.from(allLogEntries).forEach(entry => {
            entry.style.display = '';
            
            if (entry.hasAttribute('data-original-html')) {
                entry.innerHTML = entry.getAttribute('data-original-html');
            }
        });
        
        if (this.autoScrollWasEnabled && this.elements.autoScrollCheckbox) {
            this.elements.autoScrollCheckbox.checked = true;
            this.autoScrollWasEnabled = false;
        }
    },
    
    // Filter logs by level
    filterLogsByLevel: function(selectedLevel) {
        if (!this.elements.logsContainer) return;
        
        const allLogEntries = this.elements.logsContainer.querySelectorAll('.log-entry');
        let visibleCount = 0;
        let totalCount = allLogEntries.length;
        
        console.log(`[LogsModule] Filtering logs by level: ${selectedLevel}, total entries: ${totalCount}`);
        
        allLogEntries.forEach(entry => {
            entry.removeAttribute('data-hidden-by-filter');
        });
        
        allLogEntries.forEach(entry => {
            if (selectedLevel === 'all') {
                entry.style.display = '';
                visibleCount++;
            } else {
                const levelBadge = entry.querySelector('.log-level-badge, .log-level, .log-level-error, .log-level-warning, .log-level-info, .log-level-debug');
                
                if (levelBadge) {
                    let entryLevel = '';
                    const badgeText = levelBadge.textContent.toLowerCase().trim();
                    
                    switch(badgeText) {
                        case 'information':
                        case 'info':
                            entryLevel = 'info';
                            break;
                        case 'warning':
                        case 'warn':
                            entryLevel = 'warning';
                            break;
                        case 'error':
                            entryLevel = 'error';
                            break;
                        case 'debug':
                            entryLevel = 'debug';
                            break;
                        case 'fatal':
                        case 'critical':
                            entryLevel = 'error';
                            break;
                        default:
                            if (levelBadge.classList.contains('log-level-error')) {
                                entryLevel = 'error';
                            } else if (levelBadge.classList.contains('log-level-warning')) {
                                entryLevel = 'warning';
                            } else if (levelBadge.classList.contains('log-level-info')) {
                                entryLevel = 'info';
                            } else if (levelBadge.classList.contains('log-level-debug')) {
                                entryLevel = 'debug';
                            } else {
                                entryLevel = null;
                            }
                    }
                    
                    if (entryLevel && entryLevel === selectedLevel) {
                        entry.style.display = '';
                        visibleCount++;
                    } else {
                        entry.style.display = 'none';
                        entry.setAttribute('data-hidden-by-filter', 'true');
                    }
                } else {
                    entry.style.display = 'none';
                    entry.setAttribute('data-hidden-by-filter', 'true');
                }
            }
        });
        
        if (this.autoScroll && this.elements.autoScrollCheckbox && this.elements.autoScrollCheckbox.checked && visibleCount > 0) {
            setTimeout(() => {
                window.scrollTo({
                    top: 0,
                    behavior: 'smooth'
                });
            }, 100);
        }
        
        console.log(`[LogsModule] Filtered logs by level '${selectedLevel}': showing ${visibleCount}/${totalCount} entries`);
    },
    
    // Apply filter to single entry
    applyFilterToSingleEntry: function(logEntry, selectedLevel) {
        const levelBadge = logEntry.querySelector('.log-level-badge, .log-level, .log-level-error, .log-level-warning, .log-level-info, .log-level-debug');
        
        logEntry.removeAttribute('data-hidden-by-filter');
        
        if (levelBadge) {
            let entryLevel = '';
            const badgeText = levelBadge.textContent.toLowerCase().trim();
            
            switch(badgeText) {
                case 'information':
                case 'info':
                    entryLevel = 'info';
                    break;
                case 'warning':
                case 'warn':
                    entryLevel = 'warning';
                    break;
                case 'error':
                    entryLevel = 'error';
                    break;
                case 'debug':
                    entryLevel = 'debug';
                    break;
                case 'fatal':
                case 'critical':
                    entryLevel = 'error';
                    break;
                default:
                    if (levelBadge.classList.contains('log-level-error')) {
                        entryLevel = 'error';
                    } else if (levelBadge.classList.contains('log-level-warning')) {
                        entryLevel = 'warning';
                    } else if (levelBadge.classList.contains('log-level-info')) {
                        entryLevel = 'info';
                    } else if (levelBadge.classList.contains('log-level-debug')) {
                        entryLevel = 'debug';
                    } else {
                        entryLevel = null;
                    }
            }
            
            if (entryLevel && entryLevel === selectedLevel) {
                logEntry.style.display = '';
            } else {
                logEntry.style.display = 'none';
                logEntry.setAttribute('data-hidden-by-filter', 'true');
            }
        } else {
            logEntry.style.display = 'none';
            logEntry.setAttribute('data-hidden-by-filter', 'true');
        }
    },
    
    // Helper method to detect JSON fragments
    isJsonFragment: function(logString) {
        if (!logString || typeof logString !== 'string') return false;
        
        const trimmed = logString.trim();
        
        const jsonPatterns = [
            /^"[^"]*":\s*"[^"]*",?$/,
            /^"[^"]*":\s*\d+,?$/,
            /^"[^"]*":\s*true|false,?$/,
            /^"[^"]*":\s*null,?$/,
            /^"[^"]*":\s*\[[^\]]*\],?$/,
            /^"[^"]*":\s*\{[^}]*\},?$/,
            /^\s*\{?\s*$/,
            /^\s*\}?,?\s*$/,
            /^\s*\[?\s*$/,
            /^\s*\]?,?\s*$/,
            /^,?\s*$/,
            /^[^"]*':\s*[^,]*,.*'.*':/,
            /^[a-zA-Z_][a-zA-Z0-9_]*':\s*\d+,/,
            /^[a-zA-Z_][a-zA-Z0-9_]*':\s*True|False,/,
            /^[a-zA-Z_][a-zA-Z0-9_]*':\s*'[^']*',/,
            /.*':\s*\d+,.*':\s*\d+,/,
            /.*':\s*True,.*':\s*False,/,
            /.*':\s*'[^']*',.*':\s*'[^']*',/,
            /^"[^"]*":\s*\[$/,
            /^[a-zA-Z_][a-zA-Z0-9_\s]*:\s*\[$/,
            /^[a-zA-Z_][a-zA-Z0-9_\s]*:\s*\{$/,
            /^[a-zA-Z_][a-zA-Z0-9_\s]*:\s*(True|False)$/i,
            /^[a-zA-Z_][a-zA-Z0-9_\s]*:\s*\d+$/,
            /^[a-zA-Z_]+\s+(Mode|Setting|Config|Option):\s*(True|False|\d+)$/i,
            /^[a-zA-Z_]+\s*Mode:\s*(True|False)$/i,
            /^[a-zA-Z_]+\s*Setting:\s*.*$/i,
            /^[a-zA-Z_]+\s*Config:\s*.*$/i
        ];
        
        return jsonPatterns.some(pattern => pattern.test(trimmed));
    },
    
    // Helper method to detect invalid log lines
    isInvalidLogLine: function(logString) {
        if (!logString || typeof logString !== 'string') return true;
        
        const trimmed = logString.trim();
        
        if (trimmed.length === 0) return true;
        if (trimmed.length < 10) return true;
        if (/^(HTTP\/|Content-|Connection:|Host:|User-Agent:)/i.test(trimmed)) return true;
        if (/^[a-zA-Z]{1,5}\s+(Mode|Setting|Config|Debug|Info|Error|Warning):/i.test(trimmed)) return true;
        if (/^[a-zA-Z]{1,8}$/i.test(trimmed)) return true;
        if (/^[a-z]{1,8}\s*[A-Z]/i.test(trimmed) && trimmed.includes(':')) return true;
        
        return false;
    },
    
    // Reset logs to default state
    resetToDefaults: function() {
        this.currentLogApp = 'all';
        
        const logAppSelect = document.getElementById('logAppSelect');
        if (logAppSelect && logAppSelect.value !== 'all') {
            logAppSelect.value = 'all';
        }
        
        const logLevelSelect = document.getElementById('logLevelSelect');
        if (logLevelSelect && logLevelSelect.value !== 'info') {
            logLevelSelect.value = 'info';
            this.filterLogsByLevel('info');
        }
        
        const logSearchInput = document.getElementById('logSearchInput');
        if (logSearchInput && logSearchInput.value) {
            logSearchInput.value = '';
            this.clearLogSearch();
        }
        
        console.log('[LogsModule] Reset logs to defaults: All apps, INFO level, cleared search');
    }
};

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (window.LogsModule) {
        window.LogsModule.init();
    }
}); 