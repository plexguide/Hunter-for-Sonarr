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
        
        // Render rows
        data.entries.forEach(entry => {
            const row = document.createElement('tr');
            
            // Format the instance name to include app type (capitalize first letter of app type)
            const appType = entry.app_type ? entry.app_type.charAt(0).toUpperCase() + entry.app_type.slice(1) : '';
            const formattedInstance = appType ? `${appType} - ${entry.instance_name}` : entry.instance_name;
            
            row.innerHTML = `
                <td>${this.escapeHtml(entry.processed_info)}</td>
                <td>${this.formatHuntStatus(entry.hunt_status)}</td>
                <td>${this.formatOperationType(entry.operation_type)}</td>
                <td>${this.escapeHtml(formattedInstance)}</td>
                <td>${this.escapeHtml(entry.how_long_ago)}</td>
            `;
            
            tableBody.appendChild(row);
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
        if (!huntStatus) {
            return '<span class="hunt-status-unknown">Not Tracked</span>';
        }
        
        const statusLower = huntStatus.toLowerCase();
        switch (statusLower) {
            case 'searching':
                return '<span class="hunt-status-searching">Searching</span>';
            case 'found':
                return '<span class="hunt-status-found">Found</span>';
            case 'downloaded':
                return '<span class="hunt-status-downloaded">Downloaded</span>';
            case 'failed':
                return '<span class="hunt-status-failed">Failed</span>';
            default:
                return `<span class="hunt-status-unknown">${this.escapeHtml(huntStatus)}</span>`;
        }
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
