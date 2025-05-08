// Hunt Status Management
class HuntStatusManager {
    constructor() {
        this.statusContainer = document.querySelector('.hunt-status-container');
        this.updateInterval = 30000; // Update every 30 seconds
        this.startUpdates();
    }

    async updateHuntStatuses() {
        try {
            const response = await fetch('/api/hunt/status');
            const data = await response.json();
            
            if (data.status === 'success') {
                this.renderStatuses(data.data);
            } else {
                console.error('Failed to fetch hunt statuses:', data.message);
            }
        } catch (error) {
            console.error('Error updating hunt statuses:', error);
        }
    }

    renderStatuses(statuses) {
        if (!this.statusContainer) return;

        if (!statuses || statuses.length === 0) {
            this.statusContainer.innerHTML = `
                <div class="no-hunt-status">
                    <p>No hunt statuses available</p>
                </div>
            `;
            return;
        }

        const statusList = document.createElement('div');
        statusList.className = 'hunt-status-list';

        statuses.forEach(status => {
            const statusItem = document.createElement('div');
            statusItem.className = 'hunt-status-item';
            
            statusItem.innerHTML = `
                <div class="hunt-status-header">
                    <span class="hunt-app-name">${this.capitalizeFirst(status.app_name)}</span>
                    <span class="hunt-instance-name">${status.instance_name}</span>
                </div>
                <div class="hunt-status-content">
                    <div class="hunt-media-name">${status.media_name}</div>
                    <div class="hunt-status-badge ${status.status.toLowerCase()}">${status.status}</div>
                </div>
                <div class="hunt-status-footer">
                    <span class="hunt-time">Requested: ${this.formatDateTime(status.time_requested)}</span>
                    <span class="hunt-id">ID: ${status.id}</span>
                </div>
            `;
            
            statusList.appendChild(statusItem);
        });

        this.statusContainer.innerHTML = '';
        this.statusContainer.appendChild(statusList);
    }

    capitalizeFirst(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    formatDateTime(dateTimeStr) {
        const date = new Date(dateTimeStr);
        return date.toLocaleString();
    }

    startUpdates() {
        // Initial update
        this.updateHuntStatuses();
        
        // Set up periodic updates
        setInterval(() => this.updateHuntStatuses(), this.updateInterval);
    }
}

// Initialize hunt status manager when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new HuntStatusManager();
}); 