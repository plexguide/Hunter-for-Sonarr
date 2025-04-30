// Swaparr-specific functionality

(function(app) {
    if (!app) {
        console.error("Huntarr App core is not loaded!");
        return;
    }

    const swaparrModule = {
        elements: {},
        isTableView: true, // Default to table view for Swaparr logs
        hasRenderedAnyContent: false, // Track if we've rendered any content
        
        // Store data for display
        logData: {
            config: {
                platform: '',
                maxStrikes: 3,
                scanInterval: '10m',
                maxDownloadTime: '2h',
                ignoreAboveSize: '25 GB'
            },
            downloads: [],  // Will store download status records
            rawLogs: []     // Store raw logs for backup display
        },

        init: function() {
            console.log('[Swaparr Module] Initializing...');
            this.setupLogProcessor();
            
            // Add a listener for when the log tab changes to Swaparr
            const swaparrTab = document.querySelector('.log-tab[data-app="swaparr"]');
            if (swaparrTab) {
                swaparrTab.addEventListener('click', () => {
                    console.log('[Swaparr Module] Swaparr tab clicked');
                    // Small delay to ensure everything is ready
                    setTimeout(() => {
                        this.ensureContentRendered();
                    }, 200);
                });
            }
        },

        setupLogProcessor: function() {
            // Setup a listener for custom event from huntarrUI's log processing
            document.addEventListener('swaparrLogReceived', (event) => {
                console.log('[Swaparr Module] Received log event:', event.detail.logData.substring(0, 100) + '...');
                this.processLogLine(event.detail.logData);
            });
        },

        processLogLine: function(logLine) {
            // Always store raw logs for backup display
            this.logData.rawLogs.push(logLine);
            
            // Limit raw logs storage to prevent memory issues
            if (this.logData.rawLogs.length > 500) {
                this.logData.rawLogs.shift();
            }
            
            // Process log lines specific to Swaparr
            if (!logLine) return;

            // Check if this looks like a Swaparr config line and extract information
            if (logLine.includes('Platform:') && logLine.includes('Max strikes:')) {
                this.extractConfigInfo(logLine);
                this.renderConfigPanel();
                return;
            }
            
            // Look for strike-related logs from system
            if (logLine.includes('Added strike') || 
                logLine.includes('Max strikes reached') || 
                logLine.includes('removing download') ||
                logLine.includes('Would have removed')) {
                
                this.processStrikeLog(logLine);
                return;
            }

            // Check if this is a table header/separator line
            if (logLine.includes('strikes') && logLine.includes('status') && logLine.includes('name') && logLine.includes('size') && logLine.includes('eta')) {
                // This is the header line, we can ignore it or use it to confirm table format
                return;
            }

            // Try to match download info line
            // Format: [strikes/max] status name size eta
            // Example: 2/3 Striked MyDownload.mkv 1.5 GB 2h 15m
            const downloadLinePattern = /(\d+\/\d+)\s+(\w+)\s+(.+?)\s+(\d+(?:\.\d+)?)\s*(\w+)\s+([\ddhms\s]+|Infinite)/;
            const match = logLine.match(downloadLinePattern);
            
            if (match) {
                // Extract download information
                const downloadInfo = {
                    strikes: match[1],
                    status: match[2],
                    name: match[3],
                    size: match[4] + ' ' + match[5],
                    eta: match[6]
                };
                
                // Update or add to our list of downloads
                this.updateDownloadsList(downloadInfo);
                this.renderTableView();
            }
            
            // If we're viewing the Swaparr tab, always ensure content is rendered
            if (app.currentLogApp === 'swaparr') {
                this.ensureContentRendered();
            }
        },
        
        // Process strike-related logs from system logs
        processStrikeLog: function(logLine) {
            // Try to extract download name and strike info
            let downloadName = '';
            let strikes = '1/3'; // Default value
            let status = 'Striked';
            
            // Extract download name
            if (logLine.includes('Added strike')) {
                const match = logLine.match(/Added strike \((\d+)\/(\d+)\) to (.+?) - Reason:/);
                if (match) {
                    strikes = `${match[1]}/${match[2]}`;
                    downloadName = match[3];
                    status = 'Striked';
                }
            } else if (logLine.includes('Max strikes reached')) {
                const match = logLine.match(/Max strikes reached for (.+?), removing download/);
                if (match) {
                    downloadName = match[1];
                    status = 'Removed';
                }
            } else if (logLine.includes('Would have removed')) {
                const match = logLine.match(/Would have removed (.+?) after (\d+) strikes/);
                if (match) {
                    downloadName = match[1];
                    status = 'Pending Removal';
                    strikes = `${match[2]}/3`;
                }
            }
            
            if (downloadName) {
                // Create a download info object with partial information
                const downloadInfo = {
                    strikes: strikes,
                    status: status,
                    name: downloadName,
                    size: 'Unknown',
                    eta: 'Unknown'
                };
                
                // Update downloads list
                this.updateDownloadsList(downloadInfo);
                this.renderTableView();
            }
        },

        extractConfigInfo: function(logLine) {
            // Extract the config data from the log line
            const platformMatch = logLine.match(/Platform:\s+(\w+)/);
            const maxStrikesMatch = logLine.match(/Max strikes:\s+(\d+)/);
            const scanIntervalMatch = logLine.match(/Scan interval:\s+(\d+\w+)/);
            const maxDownloadTimeMatch = logLine.match(/Max download time:\s+(\d+\w+)/);
            const ignoreSizeMatch = logLine.match(/Ignore above size:\s+(\d+\s*\w+)/);
            
            if (platformMatch) this.logData.config.platform = platformMatch[1];
            if (maxStrikesMatch) this.logData.config.maxStrikes = maxStrikesMatch[1];
            if (scanIntervalMatch) this.logData.config.scanInterval = scanIntervalMatch[1];
            if (maxDownloadTimeMatch) this.logData.config.maxDownloadTime = maxDownloadTimeMatch[1];
            if (ignoreSizeMatch) this.logData.config.ignoreAboveSize = ignoreSizeMatch[1];
        },

        updateDownloadsList: function(downloadInfo) {
            // Find if this download already exists in our list
            const existingIndex = this.logData.downloads.findIndex(item => 
                item.name.trim() === downloadInfo.name.trim()
            );
            
            if (existingIndex >= 0) {
                // Update existing entry
                this.logData.downloads[existingIndex] = downloadInfo;
            } else {
                // Add new entry
                this.logData.downloads.push(downloadInfo);
            }
        },

        renderConfigPanel: function() {
            // Find the logs container
            const logsContainer = document.getElementById('logsContainer');
            if (!logsContainer) return;
            
            // If the user has selected swaparr logs, show the config panel at the top
            if (app.currentLogApp === 'swaparr') {
                // Check if config panel already exists
                let configPanel = document.getElementById('swaparr-config-panel');
                if (!configPanel) {
                    // Create the panel
                    configPanel = document.createElement('div');
                    configPanel.id = 'swaparr-config-panel';
                    configPanel.classList.add('swaparr-panel');
                    logsContainer.appendChild(configPanel);
                }
                
                // Update the panel content
                configPanel.innerHTML = `
                    <div class="swaparr-config">
                        <h3>Swaparr${this.logData.config.platform ? ' — ' + this.logData.config.platform : ''}</h3>
                        <div class="swaparr-config-content">
                            <span>Max strikes: ${this.logData.config.maxStrikes}</span>
                            <span>Scan interval: ${this.logData.config.scanInterval}</span>
                            <span>Max download time: ${this.logData.config.maxDownloadTime}</span>
                            <span>Ignore above size: ${this.logData.config.ignoreAboveSize}</span>
                        </div>
                    </div>
                `;
                
                this.hasRenderedAnyContent = true;
            }
        },

        renderTableView: function() {
            // Find the logs container
            const logsContainer = document.getElementById('logsContainer');
            if (!logsContainer || app.currentLogApp !== 'swaparr') return;
            
            // Check if table already exists
            let tableView = document.getElementById('swaparr-table-view');
            if (!tableView) {
                // Create the table
                tableView = document.createElement('div');
                tableView.id = 'swaparr-table-view';
                tableView.classList.add('swaparr-table');
                logsContainer.appendChild(tableView);
            }
            
            // Only render table if we have downloads to show
            if (this.logData.downloads.length > 0) {
                // Generate table HTML
                let tableHTML = `
                    <table>
                        <thead>
                            <tr>
                                <th>Strikes</th>
                                <th>Status</th>
                                <th>Name</th>
                                <th>Size</th>
                                <th>ETA</th>
                            </tr>
                        </thead>
                        <tbody>
                `;
                
                // Add each download as a row
                this.logData.downloads.forEach(download => {
                    // Apply status-specific CSS class
                    let statusClass = download.status.toLowerCase();
                    
                    // Normalize some status values
                    if (statusClass === 'pending removal') statusClass = 'pending';
                    if (statusClass === 'removed') statusClass = 'removed';
                    if (statusClass === 'striked') statusClass = 'striked';
                    if (statusClass === 'normal') statusClass = 'normal';
                    if (statusClass === 'ignored') statusClass = 'ignored';
                    
                    tableHTML += `
                        <tr class="swaparr-status-${statusClass}">
                            <td>${download.strikes}</td>
                            <td>${download.status}</td>
                            <td>${download.name}</td>
                            <td>${download.size}</td>
                            <td>${download.eta}</td>
                        </tr>
                    `;
                });
                
                tableHTML += `
                        </tbody>
                    </table>
                `;
                
                tableView.innerHTML = tableHTML;
                this.hasRenderedAnyContent = true;
            }
        },
        
        // Render raw logs if we don't have structured content
        renderRawLogs: function() {
            // Only show raw logs if we have no other content
            if (this.hasRenderedAnyContent) return;
            
            const logsContainer = document.getElementById('logsContainer');
            if (!logsContainer || app.currentLogApp !== 'swaparr') return;
            
            // Start with a message
            const noDataMessage = document.createElement('div');
            noDataMessage.classList.add('swaparr-panel');
            noDataMessage.innerHTML = `
                <div class="swaparr-config">
                    <h3>Swaparr Logs</h3>
                    <p>Waiting for structured Swaparr data. Showing raw logs below:</p>
                </div>
            `;
            logsContainer.appendChild(noDataMessage);
            
            // Add raw logs
            for (const logLine of this.logData.rawLogs) {
                const logEntry = document.createElement('div');
                logEntry.className = 'log-entry';
                logEntry.innerHTML = `<span class="log-message">${logLine}</span>`;
                
                // Basic level detection
                if (logLine.includes('ERROR')) logEntry.classList.add('log-error');
                else if (logLine.includes('WARN') || logLine.includes('WARNING')) logEntry.classList.add('log-warning');
                else if (logLine.includes('DEBUG')) logEntry.classList.add('log-debug');
                else logEntry.classList.add('log-info');
                
                logsContainer.appendChild(logEntry);
            }
            
            this.hasRenderedAnyContent = true;
        },
        
        // Make sure we display something in the Swaparr tab
        ensureContentRendered: function() {
            console.log('[Swaparr Module] Ensuring content is rendered, has content:', this.hasRenderedAnyContent);
            
            // Reset rendered flag
            this.hasRenderedAnyContent = false;
            
            // Check if we're viewing Swaparr tab
            if (app.currentLogApp !== 'swaparr') return;
            
            // First try to render structured content
            this.renderConfigPanel();
            this.renderTableView();
            
            // If no structured content, show raw logs
            if (!this.hasRenderedAnyContent) {
                this.renderRawLogs();
            }
        },

        // Clear the data when switching log views
        clearData: function() {
            this.logData.downloads = [];
            // Keep raw logs for now
            this.hasRenderedAnyContent = false;
        }
    };

    // Initialize the module
    document.addEventListener('DOMContentLoaded', () => {
        swaparrModule.init();
        
        if (app) {
            app.swaparrModule = swaparrModule;
            
            // Setup a handler for when log tabs are changed
            document.querySelectorAll('.log-tab').forEach(tab => {
                tab.addEventListener('click', (e) => {
                    // If switching to swaparr tab, make sure we render the view
                    if (e.target.getAttribute('data-app') === 'swaparr') {
                        console.log('[Swaparr Module] Swaparr tab clicked via delegation');
                        // Small delay to allow logs to load
                        setTimeout(() => {
                            swaparrModule.ensureContentRendered();
                        }, 200);
                    }
                    // If switching away from swaparr tab, clear the data
                    else if (app.currentLogApp === 'swaparr') {
                        swaparrModule.clearData();
                    }
                });
            });
        }
    });

})(window.huntarrUI); // Pass the global UI object