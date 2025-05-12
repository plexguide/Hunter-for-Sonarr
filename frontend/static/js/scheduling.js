/**
 * Scheduling functionality for Huntarr
 * Implements a SABnzbd-style scheduler for controlling Arr application behavior
 */

// Store schedules in memory (will be saved to persistent storage)
let schedules = [];

// Initialize scheduler when document is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the scheduler
    initScheduler();
    
    // Load existing schedules
    loadSchedules();
    
    // Set up event listeners
    setupEventListeners();
    
    // Load app instances dynamically
    loadAppInstances();
});

/**
 * Initialize the scheduler functionality
 */
function initScheduler() {
    console.debug('Initializing scheduler'); // DEBUG level per user preference
    
    // Initialize time inputs with current time
    const now = new Date();
    const hour = now.getHours();
    const minute = Math.floor(now.getMinutes() / 5) * 5; // Round to nearest 5 minutes
    
    const hourSelect = document.getElementById('scheduleHour');
    const minuteSelect = document.getElementById('scheduleMinute');
    
    if (hourSelect && minuteSelect) {
        hourSelect.value = hour;
        minuteSelect.value = minute;
    }
    
    // Check if we're on the scheduling section
    if (window.location.hash === '#scheduling') {
        // Make sure nav item is active
        const schedulingNav = document.getElementById('schedulingNav');
        if (schedulingNav) schedulingNav.classList.add('active');
    }
}

/**
 * Set up event listeners for the scheduler UI
 */
function setupEventListeners() {
    // Add Schedule button
    const addScheduleButton = document.getElementById('addScheduleButton');
    if (addScheduleButton) {
        addScheduleButton.addEventListener('click', addSchedule);
    }
    
    // Save Schedules button
    const saveSchedulesButton = document.getElementById('saveSchedulesButton');
    if (saveSchedulesButton) {
        saveSchedulesButton.addEventListener('click', saveSchedules);
    }
    
    // Set up delegates for edit/delete schedule buttons
    document.addEventListener('click', function(e) {
        // Delete schedule button
        if (e.target.closest('.delete-schedule')) {
            const button = e.target.closest('.delete-schedule');
            const scheduleId = button.dataset.id;
            deleteSchedule(scheduleId);
        }
        
        // Edit schedule button
        if (e.target.closest('.edit-schedule')) {
            const button = e.target.closest('.edit-schedule');
            const scheduleId = button.dataset.id;
            editSchedule(scheduleId);
        }
    });
}

/**
 * Load available app instances for the scheduler
 */
function loadAppInstances() {
    // This would typically fetch app instances from the API
    // For now, we'll use some default values
    
    console.debug('Loading app instances for scheduler'); // DEBUG level per user preference
    
    // The actual implementation would query each Arr app for its instances
    // and dynamically populate the scheduleApp select element
    const scheduleApp = document.getElementById('scheduleApp');
    if (!scheduleApp) return;
    
    // This would be populated dynamically based on configured instances
    // We'll keep the default options for now
}

/**
 * Load schedules from storage
 */
function loadSchedules() {
    console.debug('Loading schedules from storage'); // DEBUG level per user preference
    
    // In a real implementation, this would load from API/localStorage
    // For now, we'll use some example schedules
    schedules = [
        {
            id: '1',
            time: { hour: 10, minute: 0 },
            days: { monday: true, wednesday: true, friday: true },
            action: 'resume',
            app: 'global',
            enabled: true
        },
        {
            id: '2',
            time: { hour: 22, minute: 0 },
            days: { monday: true, tuesday: true, wednesday: true, thursday: true, friday: true, saturday: true, sunday: true },
            action: 'api-30',
            app: 'sonarr-1',
            enabled: true
        }
    ];
    
    // Update UI with loaded schedules
    renderSchedules();
}

/**
 * Save schedules to storage
 */
function saveSchedules() {
    console.debug('Saving schedules to storage:', schedules); // DEBUG level per user preference
    
    // In a real implementation, this would save to API/localStorage
    // For now, we'll just show a success message
    
    // Show success message
    alert('Schedules saved successfully!');
}

/**
 * Render schedules in the UI
 */
function renderSchedules() {
    const schedulesContainer = document.getElementById('schedulesContainer');
    const noSchedulesMessage = document.getElementById('noSchedulesMessage');
    
    if (!schedulesContainer || !noSchedulesMessage) return;
    
    // Clear current schedules
    schedulesContainer.innerHTML = '';
    
    // Show message if no schedules
    if (schedules.length === 0) {
        schedulesContainer.style.display = 'none';
        noSchedulesMessage.style.display = 'block';
        return;
    }
    
    // Show schedules and hide message
    schedulesContainer.style.display = 'block';
    noSchedulesMessage.style.display = 'none';
    
    // Add each schedule to the UI
    schedules.forEach(schedule => {
        const scheduleItem = document.createElement('div');
        scheduleItem.className = 'schedule-item';
        
        // Format time
        const formattedTime = `${String(schedule.time.hour).padStart(2, '0')}:${String(schedule.time.minute).padStart(2, '0')}`;
        
        // Format days
        let daysText = '';
        const allDays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
        const selectedDays = allDays.filter(day => schedule.days[day]);
        
        if (selectedDays.length === 7) {
            daysText = 'Daily';
        } else if (selectedDays.length === 0) {
            daysText = 'None';
        } else {
            // Format day names nicely (e.g., 'Mon, Wed, Fri')
            daysText = selectedDays.map(day => day.substring(0, 3).charAt(0).toUpperCase() + day.substring(1, 3)).join(', ');
        }
        
        // Format action name
        let actionText = '';
        if (schedule.action === 'resume') {
            actionText = 'Resume';
        } else if (schedule.action === 'pause') {
            actionText = 'Pause';
        } else if (schedule.action.startsWith('api-')) {
            const limit = schedule.action.split('-')[1];
            actionText = `API Limit: ${limit}`;
        }
        
        // Format app name
        let appText = '';
        if (schedule.app === 'global') {
            appText = 'All Apps';
        } else {
            // Format app name nicely (e.g., 'Sonarr Instance 1')
            const [app, instance] = schedule.app.split('-');
            if (instance === 'all') {
                appText = `All ${app.charAt(0).toUpperCase() + app.slice(1)} Instances`;
            } else {
                appText = `${app.charAt(0).toUpperCase() + app.slice(1)} Instance ${instance}`;
            }
        }
        
        // Build the schedule item HTML
        scheduleItem.innerHTML = `
            <div class="schedule-item-checkbox">
                <input type="checkbox" id="schedule-${schedule.id}" ${schedule.enabled ? 'checked' : ''}>
                <label for="schedule-${schedule.id}"></label>
            </div>
            <div class="schedule-item-time">${formattedTime}</div>
            <div class="schedule-item-days">${daysText}</div>
            <div class="schedule-item-action">${actionText}</div>
            <div class="schedule-item-app">${appText}</div>
            <div class="schedule-item-actions">
                <button class="icon-button edit-schedule" data-id="${schedule.id}"><i class="fas fa-edit"></i></button>
                <button class="icon-button delete-schedule" data-id="${schedule.id}"><i class="fas fa-trash"></i></button>
            </div>
        `;
        
        // Add event listener for enable/disable checkbox
        const checkbox = scheduleItem.querySelector(`#schedule-${schedule.id}`);
        if (checkbox) {
            checkbox.addEventListener('change', function() {
                toggleScheduleEnabled(schedule.id, this.checked);
            });
        }
        
        // Add to container
        schedulesContainer.appendChild(scheduleItem);
    });
}

/**
 * Add a new schedule
 */
function addSchedule() {
    // Get form values
    const hour = parseInt(document.getElementById('scheduleHour').value);
    const minute = parseInt(document.getElementById('scheduleMinute').value);
    const action = document.getElementById('scheduleAction').value;
    const app = document.getElementById('scheduleApp').value;
    
    // Get selected days
    const days = {
        monday: document.getElementById('day-monday').checked,
        tuesday: document.getElementById('day-tuesday').checked,
        wednesday: document.getElementById('day-wednesday').checked,
        thursday: document.getElementById('day-thursday').checked,
        friday: document.getElementById('day-friday').checked,
        saturday: document.getElementById('day-saturday').checked,
        sunday: document.getElementById('day-sunday').checked
    };
    
    // Validate at least one day is selected
    const anyDaySelected = Object.values(days).some(day => day);
    if (!anyDaySelected) {
        alert('Please select at least one day for the schedule.');
        return;
    }
    
    // Create new schedule
    const newSchedule = {
        id: String(Date.now()), // Simple ID generation
        time: { hour, minute },
        days,
        action,
        app,
        enabled: true
    };
    
    // Add to schedules array
    schedules.push(newSchedule);
    
    // Update UI
    renderSchedules();
    
    // Log at DEBUG level
    console.debug('Added new schedule:', newSchedule); // DEBUG level per user preference
    
    // Reset day checkboxes
    resetDayCheckboxes();
}

/**
 * Edit an existing schedule
 */
function editSchedule(scheduleId) {
    // Find the schedule
    const schedule = schedules.find(s => s.id === scheduleId);
    if (!schedule) return;
    
    console.debug('Editing schedule:', schedule); // DEBUG level per user preference
    
    // Set form values
    document.getElementById('scheduleHour').value = schedule.time.hour;
    document.getElementById('scheduleMinute').value = schedule.time.minute;
    document.getElementById('scheduleAction').value = schedule.action;
    document.getElementById('scheduleApp').value = schedule.app;
    
    // Set day checkboxes
    document.getElementById('day-monday').checked = schedule.days.monday;
    document.getElementById('day-tuesday').checked = schedule.days.tuesday;
    document.getElementById('day-wednesday').checked = schedule.days.wednesday;
    document.getElementById('day-thursday').checked = schedule.days.thursday;
    document.getElementById('day-friday').checked = schedule.days.friday;
    document.getElementById('day-saturday').checked = schedule.days.saturday;
    document.getElementById('day-sunday').checked = schedule.days.sunday;
    
    // Remove the schedule (will be re-added when user clicks Add)
    deleteSchedule(scheduleId, true); // Silent delete (no confirmation)
    
    // Scroll to the Add Schedule panel
    document.querySelector('.scheduler-panel').scrollIntoView({ behavior: 'smooth' });
}

/**
 * Delete a schedule
 */
function deleteSchedule(scheduleId, silent = false) {
    // Confirm delete (unless silent mode)
    if (!silent && !confirm('Are you sure you want to delete this schedule?')) {
        return;
    }
    
    // Remove from array
    schedules = schedules.filter(s => s.id !== scheduleId);
    
    // Update UI
    renderSchedules();
    
    console.debug('Deleted schedule ID:', scheduleId); // DEBUG level per user preference
}

/**
 * Toggle a schedule's enabled state
 */
function toggleScheduleEnabled(scheduleId, enabled) {
    // Find and update the schedule
    const schedule = schedules.find(s => s.id === scheduleId);
    if (schedule) {
        schedule.enabled = enabled;
        console.debug(`Schedule ${scheduleId} ${enabled ? 'enabled' : 'disabled'}`); // DEBUG level per user preference
    }
}

/**
 * Reset day checkboxes to unchecked
 */
function resetDayCheckboxes() {
    document.getElementById('day-monday').checked = false;
    document.getElementById('day-tuesday').checked = false;
    document.getElementById('day-wednesday').checked = false;
    document.getElementById('day-thursday').checked = false;
    document.getElementById('day-friday').checked = false;
    document.getElementById('day-saturday').checked = false;
    document.getElementById('day-sunday').checked = false;
}
