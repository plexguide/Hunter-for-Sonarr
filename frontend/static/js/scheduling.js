/**
 * Scheduling functionality for Huntarr
 * Implements a SABnzbd-style scheduler for controlling Arr application behavior
 */

/**
 * Capitalize the first letter of a string
 * @param {string} string - The string to capitalize
 * @returns {string} - The capitalized string
 */
function capitalizeFirst(string) {
    if (!string) return '';
    return string.charAt(0).toUpperCase() + string.slice(1);
}

// Store schedules by app type
let schedules = {
    global: [],
    sonarr: [],
    radarr: [],
    readarr: [],
    lidarr: [],
    whisparr: [], // WhisparrV2
    eros: []      // WhisparrV3
};
let appInstances = [];

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
 * Load app instances from available app types
 */
function loadAppInstances() {
    const appTypes = [
        { id: 'sonarr', name: 'Sonarr' },
        { id: 'radarr', name: 'Radarr' },
        { id: 'readarr', name: 'Readarr' },
        { id: 'lidarr', name: 'Lidarr' },
        { id: 'whisparr', name: 'WhisparrV2' },
        { id: 'eros', name: 'WhisparrV3' }
    ];
    
    // Use the app types directly
    appInstances = appTypes;
    
    // Also update the dropdown in the UI
    const scheduleApp = document.getElementById('scheduleApp');
    if (scheduleApp) {
        // Clear existing options first
        scheduleApp.innerHTML = '';
        
        // Add the global option
        const globalOption = document.createElement('option');
        globalOption.value = 'global';
        globalOption.textContent = 'All Apps (Global)';
        scheduleApp.appendChild(globalOption);
        
        // Add each app type
        appTypes.forEach(app => {
            const option = document.createElement('option');
            option.value = app.id;
            option.textContent = app.name;
            scheduleApp.appendChild(option);
        });
    }
    
    console.debug('App types loaded successfully');
}

/**
 * Load schedules from server
 */
function loadSchedules() {
    console.debug('Loading schedules from server'); // DEBUG level per user preference
    
    // Make API call to get schedules
    fetch('/api/scheduler/load')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load schedules');
            }
            return response.json();
        })
        .then(data => {
            console.debug('Loaded schedules from server:', data);
            schedules = data;
            renderSchedules();
        })
        .catch(error => {
            console.error('Error loading schedules:', error);
            // Initialize empty schedule structure if load fails
            schedules = {
                global: [],
                sonarr: [],
                radarr: [],
                readarr: [],
                lidarr: [],
                whisparr: [],
                eros: []
            };
            renderSchedules();
        });
}

/**
 * Save schedules to server
 */
function saveSchedules() {
    console.debug('Saving schedules to server...'); // DEBUG level per user preference
    
    try {
        // Save to server via API
        fetch('/api/scheduler/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(schedules)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to save schedules');
            }
            return response.json();
        })
        .then(data => {
            console.debug('Successfully saved schedules to server');
            
            // Show success message
            const saveMessage = document.createElement('div');
            saveMessage.classList.add('save-success-message');
            saveMessage.textContent = 'Schedules saved successfully!';
            document.querySelector('.scheduler-container').appendChild(saveMessage);
            
            // Remove message after 3 seconds
            setTimeout(() => {
                if (saveMessage.parentNode) {
                    saveMessage.parentNode.removeChild(saveMessage);
                }
            }, 3000);
        })
        .catch(error => {
            console.error('Error saving schedules:', error);
            
            // Show error message
            const errorMessage = document.createElement('div');
            errorMessage.classList.add('save-error-message');
            errorMessage.textContent = 'Failed to save schedules!';
            document.querySelector('.scheduler-container').appendChild(errorMessage);
            
            // Remove message after 3 seconds
            setTimeout(() => {
                if (errorMessage.parentNode) {
                    errorMessage.parentNode.removeChild(errorMessage);
                }
            }, 3000);
        });
    } catch (error) {
        console.error('Error preparing schedules for saving:', error);
    }
}

/**
 * Render the list of schedules
 */
function renderSchedules() {
    const scheduleList = document.getElementById('schedule-list');
    if (!scheduleList) {
        console.error('Schedule list element not found!');
        return;
    }
    
    // Clear the list
    scheduleList.innerHTML = '';
    
    // Get no schedules message element
    const noSchedulesMessage = document.getElementById('noSchedulesMessage');
    
    // Count total schedules across all app types
    const totalSchedules = Object.values(schedules).reduce(
        (total, appSchedules) => total + appSchedules.length, 0
    );
    
    // Show appropriate message if no schedules
    if (totalSchedules === 0) {
        if (noSchedulesMessage) noSchedulesMessage.style.display = 'block';
        
        const emptyMessage = document.createElement('tr');
        emptyMessage.innerHTML = '<td colspan="6" class="text-center">No schedules found</td>';
        scheduleList.appendChild(emptyMessage);
        return;
    } else {
        if (noSchedulesMessage) noSchedulesMessage.style.display = 'none';
    }
    
    // Render schedules for each app type
    Object.entries(schedules).forEach(([appType, appSchedules]) => {
        // Skip if no schedules for this app type
        if (!appSchedules || appSchedules.length === 0) return;
        
        // Add a header row for the app type if we have multiple app types with schedules
        if (totalSchedules > appSchedules.length) {
            const headerRow = document.createElement('tr');
            headerRow.className = 'app-type-header';
            const headerCell = document.createElement('td');
            headerCell.colSpan = 6;
            headerCell.textContent = appType === 'global' ? 'Global (All Apps)' : 
                appType === 'whisparr' ? 'WhisparrV2' : 
                appType === 'eros' ? 'WhisparrV3' : 
                appType.charAt(0).toUpperCase() + appType.slice(1);
            headerRow.appendChild(headerCell);
            scheduleList.appendChild(headerRow);
        }
        
        // Render each schedule in this app type
        appSchedules.forEach(schedule => {
            const row = document.createElement('tr');
            
            // Create checkbox cell
            const checkboxCell = document.createElement('td');
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.className = 'schedule-checkbox';
            checkbox.dataset.id = schedule.id;
            checkbox.dataset.appType = appType;
            checkboxCell.appendChild(checkbox);
            row.appendChild(checkboxCell);
            
            // Time cell
            const timeCell = document.createElement('td');
            timeCell.textContent = schedule.time;
            row.appendChild(timeCell);
            
            // Days cell
            const daysCell = document.createElement('td');
            daysCell.textContent = schedule.days.map(day => day.substring(0, 3)).join(', ');
            row.appendChild(daysCell);
            
            // Action cell
            const actionCell = document.createElement('td');
            actionCell.textContent = schedule.action;
            row.appendChild(actionCell);
            
            // App cell
            const appCell = document.createElement('td');
            appCell.textContent = schedule.app;
            row.appendChild(appCell);
            
            // Action buttons cell
            const actionsCell = document.createElement('td');
            actionsCell.className = 'text-end';
            
            // Edit button
            const editButton = document.createElement('button');
            editButton.className = 'btn btn-sm btn-primary me-2';
            editButton.innerHTML = '<i class="bi bi-pencil"></i>';
            editButton.dataset.id = schedule.id;
            editButton.dataset.appType = appType;
            actionsCell.appendChild(editButton);
            
            // Delete button
            const deleteButton = document.createElement('button');
            deleteButton.className = 'btn btn-sm btn-danger';
            deleteButton.innerHTML = '<i class="bi bi-trash"></i>';
            deleteButton.dataset.id = schedule.id;
            deleteButton.dataset.appType = appType;
            actionsCell.appendChild(deleteButton);
            
            row.appendChild(actionsCell);
            scheduleList.appendChild(row);
        });
    });
}

/**
 * Add a new schedule
 */
function addSchedule() {
    const timeHour = document.getElementById('scheduleHour').value;
    const timeMinute = document.getElementById('scheduleMinute').value;
    const days = [];
    
    // Get selected days
    if (document.getElementById('day-monday').checked) days.push('Monday');
    if (document.getElementById('day-tuesday').checked) days.push('Tuesday');
    if (document.getElementById('day-wednesday').checked) days.push('Wednesday');
    if (document.getElementById('day-thursday').checked) days.push('Thursday');
    if (document.getElementById('day-friday').checked) days.push('Friday');
    if (document.getElementById('day-saturday').checked) days.push('Saturday');
    if (document.getElementById('day-sunday').checked) days.push('Sunday');
    
    const action = document.getElementById('scheduleAction').value;
    const app = document.getElementById('scheduleApp').value;
    
    if (!timeHour || !timeMinute || days.length === 0 || !action || !app) {
        alert('Please fill in all fields');
        return;
    }
    
    const formattedTime = `${timeHour.padStart(2, '0')}:${timeMinute.padStart(2, '0')}`;
    
    const schedule = {
        id: Date.now().toString(), // Simple unique ID
        time: formattedTime,
        days: days,
        action: action,
        app: app
    };
    
    // Add to the appropriate app type array based on the selection
    if (app === 'global') {
        schedules.global.push(schedule);
    } else if (app.includes('-all')) {
        // This is an 'all instances' option
        const appType = app.split('-')[0]; // Extract the app type
        if (schedules[appType]) {
            schedules[appType].push(schedule);
        }
    } else if (app.includes('-')) {
        // This is a specific instance
        const appParts = app.split('-');
        const appType = appParts[0];
        if (schedules[appType]) {
            schedules[appType].push(schedule);
        }
    } else {
        // Direct app type (from our simplified dropdown)
        if (schedules[app]) {
            schedules[app].push(schedule);
        } else {
            console.error('Could not find app type for', app);
        }
    }
    
    saveSchedules();
    renderSchedules();
}

/**
 * Delete a schedule
 * @param {string} id - ID of the schedule to delete
 * @param {string} appType - The app type the schedule belongs to ('global', 'sonarr', etc.)
 */
function deleteSchedule(id, appType) {
    if (schedules[appType]) {
        const index = schedules[appType].findIndex(schedule => schedule.id === id);
        if (index !== -1) {
            schedules[appType].splice(index, 1);
            saveSchedules();
            renderSchedules();
        }
        return;
    }
    
    // Remove from array
    schedules = schedules.filter(s => s.id !== scheduleId);
    
    // Update UI
    renderSchedules();
    
    console.debug('Deleted schedule ID:', scheduleId); // DEBUG level per user preference
}

/**
 * Edit a schedule in the list
 * @param {string} id - ID of the schedule to edit
 * @param {string} appType - The app type the schedule belongs to ('global', 'sonarr', etc.)
 */
function editSchedule(id, appType) {
    if (!schedules[appType]) return;
    
    const index = schedules[appType].findIndex(schedule => schedule.id === id);
    
    if (index !== -1) {
        const schedule = schedules[appType][index];
        const [hour, minute] = schedule.time.split(':');
        
        document.getElementById('scheduleHour').value = hour;
        document.getElementById('scheduleMinute').value = minute;
        
        // Uncheck all days first
        document.getElementById('day-monday').checked = false;
        document.getElementById('day-tuesday').checked = false;
        document.getElementById('day-wednesday').checked = false;
        document.getElementById('day-thursday').checked = false;
        document.getElementById('day-friday').checked = false;
        document.getElementById('day-saturday').checked = false;
        document.getElementById('day-sunday').checked = false;
        
        // Check the days from the schedule
        schedule.days.forEach(day => {
            const dayId = 'day-' + day.toLowerCase();
            const checkbox = document.getElementById(dayId);
            if (checkbox) checkbox.checked = true;
        });
        
        document.getElementById('scheduleAction').value = schedule.action;
        document.getElementById('scheduleApp').value = schedule.app;
        
        // Remove the schedule being edited
        schedules[appType].splice(index, 1);
        saveSchedules();
        renderSchedules();
        
        // Scroll to the form
        document.querySelector('.scheduler-panel').scrollIntoView({ behavior: 'smooth' });
    }
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
