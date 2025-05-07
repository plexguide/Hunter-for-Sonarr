/**
 * Huntarr - History Module
 * Handles displaying and managing history entries for all media apps
 */

const historyModule = {
    // State
    currentApp: 'all',
    currentPage: 1,
    totalPages: 1,
    pageSize: 20,
    searchQuery: '',
    isLoading: false,
    
    // DOM elements
    elements: {},
    
    // Initialize the history module
    init: function() {
        this.cacheElements();
        this.setupEventListeners();
        
        // Initial load if history is active section
        if (huntarrUI && huntarrUI.currentSection === 'history') {
            this.loadHistory();
        }
    },
    
    // Cache DOM elements
    cacheElements: function() {
        this.elements = {
            // History dropdown
            historyOptions: document.querySelectorAll('.history-option'),
            currentHistoryApp: document.getElementById('current-history-app'),
            historyDropdownBtn: document.querySelector('.history-dropdown-btn'),
            historyDropdownContent: document.querySelector('.history-dropdown-content'),
            
            // Table and containers
            historyTable: document.querySelector('.history-table'),
            historyTableBody: document.getElementById('historyTableBody'),
            historyContainer: document.querySelector('.history-container'),
            
            // Controls
            historySearchInput: document.getElementById('historySearchInput'),
            historySearchButton: document.getElementById('historySearchButton'),
            historyPageSize: document.getElementById('historyPageSize'),
            clearHistoryButton: document.getElementById('clearHistoryButton'),
            
            // Pagination
            historyPrevPage: document.getElementById('historyPrevPage'),
            historyNextPage: document.getElementById('historyNextPage'),
            historyCurrentPage: document.getElementById('historyCurrentPage'),
            historyTotalPages: document.getElementById('historyTotalPages'),
            
            // State displays
            historyEmptyState: document.getElementById('historyEmptyState'),
            historyLoading: document.getElementById('historyLoading')
        };
    },
    
    // Set up event listeners
    setupEventListeners: function() {
        // App selection (native select)
        const historyAppSelect = document.getElementById('historyAppSelect');
        if (historyAppSelect) {
            historyAppSelect.addEventListener('change', (e) => {
                this.handleHistoryAppChange(e.target.value);
            });
        }
        // App selection (legacy click)
        this.elements.historyOptions.forEach(option => {
            option.addEventListener('click', e => this.handleHistoryAppChange(e));
        });
        
        // Search
        this.elements.historySearchButton.addEventListener('click', () => this.handleSearch());
        this.elements.historySearchInput.addEventListener('keypress', e => {
            if (e.key === 'Enter') this.handleSearch();
        });
        
        // Page size
        this.elements.historyPageSize.addEventListener('change', () => this.handlePageSizeChange());
        
        // Clear history
        this.elements.clearHistoryButton.addEventListener('click', () => this.handleClearHistory());
        
        // Pagination
        this.elements.historyPrevPage.addEventListener('click', () => this.handlePagination('prev'));
        this.elements.historyNextPage.addEventListener('click', () => this.handlePagination('next'));
    },
    
    // Load history data when section becomes active
    loadHistory: function() {
        if (this.elements.historyContainer) {
            this.fetchHistoryData();
        }
    },
    
    // Handle app selection changes
    handleHistoryAppChange: function(eOrValue) {
        let selectedApp;
        if (typeof eOrValue === 'string') {
            selectedApp = eOrValue;
        } else if (eOrValue && eOrValue.target) {
            selectedApp = eOrValue.target.getAttribute('data-app');
            eOrValue.preventDefault();
        }
        if (!selectedApp || selectedApp === this.currentApp) return;
        // Update UI (for legacy click)
        if (this.elements.historyOptions) {
            this.elements.historyOptions.forEach(option => {
                option.classList.remove('active');
                if (option.getAttribute('data-app') === selectedApp) {
                    option.classList.add('active');
                }
            });
        }
        // Update dropdown text (if present)
        if (this.elements.currentHistoryApp) {
            const displayName = selectedApp.charAt(0).toUpperCase() + selectedApp.slice(1);
            this.elements.currentHistoryApp.textContent = displayName;
        }
        // Reset pagination
        this.currentPage = 1;
        // Update state and fetch data
        this.currentApp = selectedApp;
        this.fetchHistoryData();
    },
    
    // Handle search
    handleSearch: function() {
        const newSearchQuery = this.elements.historySearchInput.value.trim();
        
        // Only fetch if search query changed
        if (newSearchQuery !== this.searchQuery) {
            this.searchQuery = newSearchQuery;
            this.currentPage = 1; // Reset to first page
            this.fetchHistoryData();
        }
    },
    
    // Handle page size change
    handlePageSizeChange: function() {
        const newPageSize = parseInt(this.elements.historyPageSize.value);
        if (newPageSize !== this.pageSize) {
            this.pageSize = newPageSize;
            this.currentPage = 1; // Reset to first page
            this.fetchHistoryData();
        }
    },
    
    // Handle pagination
    handlePagination: function(direction) {
        if (direction === 'prev' && this.currentPage > 1) {
            this.currentPage--;
            this.fetchHistoryData();
        } else if (direction === 'next' && this.currentPage < this.totalPages) {
            this.currentPage++;
            this.fetchHistoryData();
        }
    },
    
    // Handle clear history
    handleClearHistory: function() {
        if (confirm(`Are you sure you want to clear ${this.currentApp === 'all' ? 'all history' : this.currentApp + ' history'}?`)) {
            this.clearHistory();
        }
    },
    
    // Fetch history data from API
    fetchHistoryData: function() {
        this.setLoading(true);
        
        // Construct URL with parameters
        let url = `/api/history/${this.currentApp}?page=${this.currentPage}&page_size=${this.pageSize}`;
        if (this.searchQuery) {
            url += `&search=${encodeURIComponent(this.searchQuery)}`;
        }
        
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                this.totalPages = data.total_pages;
                this.renderHistoryData(data);
                this.updatePaginationUI();
                this.setLoading(false);
            })
            .catch(error => {
                console.error('Error fetching history data:', error);
                this.showError('Failed to load history data. Please try again later.');
                this.setLoading(false);
            });
    },
    
    // Clear history
    clearHistory: function() {
        this.setLoading(true);
        
        fetch(`/api/history/${this.currentApp}`, {
            method: 'DELETE',
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(() => {
                // Reload data
                this.fetchHistoryData();
            })
            .catch(error => {
                console.error('Error clearing history:', error);
                this.showError('Failed to clear history. Please try again later.');
                this.setLoading(false);
            });
    },
    
    // Render history data to table
    renderHistoryData: function(data) {
        const tableBody = this.elements.historyTableBody;
        tableBody.innerHTML = '';
        
        if (!data.entries || data.entries.length === 0) {
            this.showEmptyState();
            return;
        }
        
        // Hide empty state
        this.elements.historyEmptyState.style.display = 'none';
        this.elements.historyTable.style.display = 'table';
        
        // Make sure we have the tooltip container
        this.ensureTooltipContainer();
        
        // Render rows
        data.entries.forEach(entry => {
            const row = document.createElement('tr');
            
            // Format the instance name to include app type (capitalize first letter of app type)
            const appType = entry.app_type ? entry.app_type.charAt(0).toUpperCase() + entry.app_type.slice(1) : '';
            const formattedInstance = appType ? `${appType} - ${entry.instance_name}` : entry.instance_name;
            
            // Store the full JSON data as a data attribute
            row.dataset.fullJson = JSON.stringify(entry);
            
            row.innerHTML = `
                <td>
                    <div class="title-with-info">
                        ${this.escapeHtml(entry.processed_info)}
                        <span class="info-badge" title="View full details">info</span>
                    </div>
                </td>
                <td>${this.formatHuntStatus(entry.hunt_status)}</td>
                <td>${this.formatOperationType(entry.operation_type)}</td>
                <td>${this.escapeHtml(formattedInstance)}</td>
                <td>${this.escapeHtml(entry.how_long_ago)}</td>
            `;
            
            tableBody.appendChild(row);
            
            // Add hover events to the info badge
            const infoBadge = row.querySelector('.info-badge');
            if (infoBadge) {
                infoBadge.addEventListener('mouseover', (e) => this.showJsonTooltip(e, row));
                infoBadge.addEventListener('mouseout', () => this.hideJsonTooltip());
                infoBadge.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.toggleJsonTooltip(e, row);
                });
            }
        });
    },
    
    // Update pagination UI
    updatePaginationUI: function() {
        this.elements.historyCurrentPage.textContent = this.currentPage;
        this.elements.historyTotalPages.textContent = this.totalPages;
        
        // Enable/disable pagination buttons
        this.elements.historyPrevPage.disabled = this.currentPage <= 1;
        this.elements.historyNextPage.disabled = this.currentPage >= this.totalPages;
    },
    
    // Show empty state
    showEmptyState: function() {
        this.elements.historyTable.style.display = 'none';
        this.elements.historyEmptyState.style.display = 'flex';
    },
    
    // Show error
    showError: function(message) {
        // Use huntarrUI's notification system if available
        if (typeof huntarrUI !== 'undefined' && typeof huntarrUI.showNotification === 'function') {
            huntarrUI.showNotification(message, 'error');
        } else {
            alert(message);
        }
    },
    
    // Set loading state
    setLoading: function(isLoading) {
        this.isLoading = isLoading;
        
        if (isLoading) {
            this.elements.historyLoading.style.display = 'flex';
            this.elements.historyTable.style.display = 'none';
            this.elements.historyEmptyState.style.display = 'none';
        } else {
            this.elements.historyLoading.style.display = 'none';
        }
    },
    
    // Helper function to escape HTML
    escapeHtml: function(text) {
        if (text === null || text === undefined) return '';
        
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        
        return String(text).replace(/[&<>"']/g, function(m) { return map[m]; });
    },
    
    // Helper function to format operation type
    formatOperationType: function(operationType) {
        switch (operationType) {
            case 'missing':
                return '<span class="operation-missing">Missing</span>';
            case 'upgrade':
                return '<span class="operation-upgrade">Upgrade</span>';
            default:
                return operationType ? this.escapeHtml(operationType.charAt(0).toUpperCase() + operationType.slice(1)) : 'Unknown';
        }
    },
    
    // Helper function to format hunt status
    formatHuntStatus: function(huntStatus) {
        if (!huntStatus) return '<span class="status-badge status-unknown">Unknown</span>';
        
        let badgeClass = 'status-unknown';
        let displayText = huntStatus;
        
        // Format based on status
        switch(huntStatus.toLowerCase()) {
            case 'searching':
                badgeClass = 'status-searching';
                break;
            case 'downloaded':
                badgeClass = 'status-downloaded';
                break;
            case 'downloading':
                badgeClass = 'status-downloading';
                break;
            case 'error':
                badgeClass = 'status-error';
                break;
        }
        
        return `<span class="status-badge ${badgeClass}">${displayText}</span>`;
    },
    
    // Ensure tooltip container exists
    ensureTooltipContainer: function() {
        // Check if container already exists
        if (document.getElementById('json-tooltip')) return;
        
        // Create tooltip container
        const tooltipContainer = document.createElement('div');
        tooltipContainer.id = 'json-tooltip';
        tooltipContainer.className = 'json-tooltip';
        tooltipContainer.style.display = 'none';
        document.body.appendChild(tooltipContainer);
        
        // Add styles for the tooltip
        if (!document.getElementById('tooltip-styles')) {
            const styleEl = document.createElement('style');
            styleEl.id = 'tooltip-styles';
            styleEl.textContent = `
                .json-tooltip {
                    position: absolute;
                    z-index: 1000;
                    max-width: 600px;
                    max-height: 400px;
                    overflow: auto;
                    background: rgba(30, 38, 55, 0.95);
                    color: #fff;
                    border-radius: 8px;
                    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
                    padding: 15px;
                    font-family: monospace;
                    white-space: pre-wrap;
                    font-size: 12px;
                    border: 1px solid rgba(90, 109, 137, 0.4);
                    backdrop-filter: blur(5px);
                }
                .title-with-info {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                .info-badge {
                    display: inline-block;
                    background-color: #4b6bff;
                    color: white;
                    border-radius: 4px;
                    padding: 2px 6px;
                    font-size: 11px;
                    cursor: pointer;
                    text-transform: uppercase;
                    font-weight: bold;
                    letter-spacing: 0.5px;
                    opacity: 0.8;
                    transition: all 0.2s ease;
                }
                .info-badge:hover {
                    opacity: 1;
                    transform: scale(1.05);
                    background-color: #5f7dff;
                }
                .json-key {
                    color: #9cdcfe;
                }
                .json-string {
                    color: #ce9178;
                }
                .json-number {
                    color: #b5cea8;
                }
                .json-boolean {
                    color: #569cd6;
                }
                .json-null {
                    color: #569cd6;
                }
            `;
            document.head.appendChild(styleEl);
        }
    },
    
    // Show JSON tooltip
    showJsonTooltip: function(event, row) {
        const tooltip = document.getElementById('json-tooltip');
        if (!tooltip || !row.dataset.fullJson) return;
        
        try {
            // Parse JSON data
            const jsonData = JSON.parse(row.dataset.fullJson);
            
            // Format JSON with syntax highlighting
            const formattedJson = this.formatJsonForDisplay(jsonData);
            
            // Set tooltip content
            tooltip.innerHTML = formattedJson;
            
            // Position tooltip near cursor
            const x = event.clientX + 15;
            let y = event.clientY + 15;
            
            // Check if tooltip would go off screen and adjust accordingly
            const rightEdge = x + tooltip.offsetWidth;
            const bottomEdge = y + tooltip.offsetHeight;
            
            if (rightEdge > window.innerWidth) {
                tooltip.style.left = (x - tooltip.offsetWidth) + 'px';
            } else {
                tooltip.style.left = x + 'px';
            }
            
            if (bottomEdge > window.innerHeight) {
                tooltip.style.top = (y - tooltip.offsetHeight) + 'px';
            } else {
                tooltip.style.top = y + 'px';
            }
            
            // Show tooltip
            tooltip.style.display = 'block';
        } catch (error) {
            console.error('Error parsing JSON for tooltip:', error);
        }
    },
    
    // Hide JSON tooltip
    hideJsonTooltip: function() {
        const tooltip = document.getElementById('json-tooltip');
        if (tooltip) {
            tooltip.style.display = 'none';
        }
    },
    
    // Toggle JSON tooltip on click
    toggleJsonTooltip: function(event, row) {
        const tooltip = document.getElementById('json-tooltip');
        if (!tooltip || !row.dataset.fullJson) return;
        
        // If tooltip is already visible, hide it
        if (tooltip.style.display === 'block') {
            this.hideJsonTooltip();
            return;
        }
        
        // Otherwise show it (reuse the show method)
        this.showJsonTooltip(event, row);
    },
    
    // Format JSON with syntax highlighting
    formatJsonForDisplay: function(obj) {
        // Convert to formatted string with 2-space indentation
        const jsonString = JSON.stringify(obj, null, 2);
        
        // Add syntax highlighting by replacing with HTML
        return jsonString
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"([^"]+)":/g, '<span class="json-key">"$1"</span>:') // Keys
            .replace(/: "([^"]+)"/g, ': <span class="json-string">"$1"</span>') // String values
            .replace(/: ([0-9]+)/g, ': <span class="json-number">$1</span>') // Number values
            .replace(/: (true|false)/g, ': <span class="json-boolean">$1</span>') // Boolean values
            .replace(/: null/g, ': <span class="json-null">null</span>'); // Null values
    }
};

// Initialize when huntarrUI is ready
document.addEventListener('DOMContentLoaded', () => {
    historyModule.init();
    
    // Connect with main app
    if (typeof huntarrUI !== 'undefined') {
        // Add loadHistory to the section switch handler
        const originalSwitchSection = huntarrUI.switchSection;
        
        huntarrUI.switchSection = function(section) {
            // Call original function
            originalSwitchSection.call(huntarrUI, section);
            
            // Load history data when switching to history section
            if (section === 'history') {
                historyModule.loadHistory();
            }
        };
    }
});
