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
 * Fetch app instances from the pre-generated list.json file
 * @returns {Promise<Object>} - Object containing app instances
 */
async function fetchAppInstances() {
    console.debug('Fetching app instances from list.json for scheduler dropdown'); // DEBUG level per user preference
    
    // Define the app types we support (for fallback)
    const appTypes = ['sonarr', 'radarr', 'lidarr', 'readarr', 'whisparr', 'eros', 'bazarr'];
    const instances = {};
    
    // Initialize all app types with empty arrays
    appTypes.forEach(appType => {
        instances[appType] = [];
    });
    
    try {
        // Add a cache-busting parameter to ensure we get fresh data
        const cacheBuster = new Date().getTime();
        const listUrl = `/config/scheduling/list.json?nocache=${cacheBuster}`;
        
        console.debug(`Loading app instances from ${listUrl}`);
        const response = await fetch(listUrl);
        
        if (response.ok) {
            const data = await response.json();
            console.debug('Successfully loaded app instances from list.json');
            
            // Process each app type from the list.json file
            for (const appType of appTypes) {
                if (data[appType] && Array.isArray(data[appType]) && data[appType].length > 0) {
                    instances[appType] = data[appType];
                    console.debug(`Added ${instances[appType].length} ${appType} instances from list.json`);
                } else {
                    // Add a fallback default instance if none found
                    console.debug(`No ${appType} instances found in list.json, adding default fallback`);
                    instances[appType] = [
                        { id: '0', name: `${capitalizeFirst(appType)} Default` }
                    ];
                }
            }
        } else {
            console.warn(`Error fetching list.json: ${response.status} ${response.statusText}`);
            // Add fallback defaults for all app types
            useDefaultInstances(instances, appTypes);
        }
    } catch (error) {
        console.warn('Error fetching app instances from list.json:', error);
        // Add fallback defaults for all app types
        useDefaultInstances(instances, appTypes);
    }
    
    console.debug('Final instances object:', instances);
    return instances;
}

/**
 * Add default instances for all app types as a fallback
 * @param {Object} instances - The instances object to populate
 * @param {Array} appTypes - Array of app types to create defaults for
 */
function useDefaultInstances(instances, appTypes) {
    console.debug('Using default instances for all app types');
    appTypes.forEach(appType => {
        instances[appType] = [
            { id: '0', name: `${capitalizeFirst(appType)} Default` }
        ];
    });
}

/**
 * Load available app instances for the scheduler
 */
function loadAppInstances() {
    console.debug('Starting to load app instances for scheduler dropdown'); // DEBUG level per user preference
    
    const scheduleApp = document.getElementById('scheduleApp');
    if (!scheduleApp) {
        console.error('Schedule app dropdown not found in DOM');
        return;
    }
    
    // Clear existing options
    scheduleApp.innerHTML = '';
    
    // Add the global option
    const globalOption = document.createElement('option');
    globalOption.value = 'global';
    globalOption.textContent = 'All Apps (Global)';
    scheduleApp.appendChild(globalOption);
    
    // Fetch app instances using our async function with force refresh
    const cacheBuster = new Date().getTime();
    // Use the web-accessible path (the web server can't access /config directly)
    const listUrl = `/static/data/app_instances.json?nocache=${cacheBuster}`;
    
    // Show loading indicator in dropdown
    const loadingOption = document.createElement('option');
    loadingOption.disabled = true;
    loadingOption.textContent = 'Loading instances...';
    scheduleApp.appendChild(loadingOption);
    
    // Fetch the data directly for immediate response
    console.debug(`Directly loading app instances from ${listUrl}`);
    fetch(listUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to load app_instances.json: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            // Success - populate from the received data
            console.debug('Successfully loaded app instances from app_instances.json:', data);
            
            // Remove loading indicator
            scheduleApp.removeChild(loadingOption);
            
            // Manually define the exact order we want
            const manualOrder = ['sonarr', 'radarr', 'readarr', 'lidarr', 'whisparr', 'eros'];
            console.debug('Using hardcoded app order for consistent display');
            
            // Filter to only include app types that actually exist in our data
            const sortedAppTypes = manualOrder.filter(appType => {
                return data[appType] && Array.isArray(data[appType]) && data[appType].length > 0;
            });
            
            // Create optgroups for each app type
            sortedAppTypes.forEach(appType => {
                // Only create optgroup if there are instances
                if (data[appType] && Array.isArray(data[appType]) && data[appType].length > 0) {
                    const optgroup = document.createElement('optgroup');
                    // Use display name if available, otherwise fallback to capitalized app type
                    const displayName = data[appType][0].display_name || capitalizeFirst(appType);
                    optgroup.label = displayName;
                    
                    // Add individual instances
                    data[appType].forEach(instance => {
                        const option = document.createElement('option');
                        option.value = `${appType}-${instance.id}`;
                        option.textContent = instance.name;
                        optgroup.appendChild(option);
                    });
                    
                    scheduleApp.appendChild(optgroup);
                }
            });
        })
        .catch(error => {
            console.error('Error loading app instances:', error);
            console.debug('Attempting fallback to fetchAppInstances()');
            // Remove loading indicator
            scheduleApp.removeChild(loadingOption);
            
            // Fall back to fetchAppInstances for backwards compatibility
            return fetchAppInstances().then(instances => {
                // Manually define the exact order we want
                const manualOrder = ['sonarr', 'radarr', 'readarr', 'lidarr', 'whisparr', 'eros'];
                console.debug('Using hardcoded app order for consistent display (fallback mode)');
                
                // Filter to only include app types that actually exist in our data
                const sortedAppTypes = manualOrder.filter(appType => {
                    return instances[appType] && Array.isArray(instances[appType]) && instances[appType].length > 0;
                });
                
                // Create optgroups for each app type
                sortedAppTypes.forEach(appType => {
                    // Only create optgroup if there are instances
                    if (instances[appType] && instances[appType].length > 0) {
                        const optgroup = document.createElement('optgroup');
                        // Use display name if available, otherwise fallback to capitalized app type
                        const displayName = instances[appType][0].display_name || capitalizeFirst(appType);
                        optgroup.label = displayName;
                        
                        // Add individual instances
                        instances[appType].forEach(instance => {
                            const option = document.createElement('option');
                            option.value = `${appType}-${instance.id}`;
                            option.textContent = instance.name;
                            optgroup.appendChild(option);
                        });
                        
                        scheduleApp.appendChild(optgroup);
                    }
                });
            });
        });
}

/**
 * Format app instances data to a consistent structure
 * @param {Object} data Raw app instances data
 * @returns {Object} Formatted app instances data
 */
function formatAppInstances(data) {
    const formatted = {};
    
    // Check if data is in the expected format
    if (typeof data !== 'object') {
        throw new Error('Invalid app instances data format');
    }
    
    // Process different potential formats
    if (Array.isArray(data)) {
        // Handle array format - group by app type
        data.forEach(instance => {
            if (!instance.type) return;
            
            const appType = instance.type.toLowerCase();
            if (!formatted[appType]) {
                formatted[appType] = [];
            }
            
            formatted[appType].push({
                id: instance.id || formatted[appType].length + 1,
                name: instance.name || `${capitalizeFirst(appType)} Instance ${instance.id || formatted[appType].length + 1}`
            });
        });
    } else {
        // Handle object format with app types as keys
        Object.keys(data).forEach(appType => {
            const normalizedType = appType.toLowerCase();
            
            if (Array.isArray(data[appType])) {
                formatted[normalizedType] = data[appType].map((instance, index) => {
                    // Handle if instance is just a string or object
                    if (typeof instance === 'string') {
                        return {
                            id: (index + 1).toString(),
                            name: instance
                        };
                    } else if (typeof instance === 'object') {
                        return {
                            id: instance.id || (index + 1).toString(),
                            name: instance.name || `${capitalizeFirst(normalizedType)} Instance ${instance.id || index + 1}`
                        };
                    }
                }).filter(Boolean); // Remove any undefined entries
            } else if (typeof data[appType] === 'object' && data[appType] !== null) {
                // Handle object with instance IDs as keys
                formatted[normalizedType] = Object.keys(data[appType]).map((id) => {
                    const instance = data[appType][id];
                    return {
                        id: id,
                        name: instance.name || `${capitalizeFirst(normalizedType)} Instance ${id}`
                    };
                });
            }
        });
    }
    
    return formatted;
}

/**
 * Load schedules from storage
 */
function loadSchedules() {
    console.debug('Loading schedules from storage'); // DEBUG level per user preference
    
    // Try to load from localStorage if available
    try {
        const storedSchedules = localStorage.getItem('huntarr-schedules');
        if (storedSchedules) {
            schedules = JSON.parse(storedSchedules);
            console.debug(`Loaded ${schedules.length} schedules from localStorage`);
        } else {
            // Start with empty schedules array
            schedules = [];
            console.debug('No saved schedules found, starting with empty list');
        }
    } catch (error) {
        // If any error occurs, start with an empty array
        console.warn('Error loading schedules from storage:', error);
        schedules = [];
    }
    
    // Update UI with loaded schedules
    renderSchedules();
}

/**
 * Save schedules to storage
 */
function saveSchedules() {
    console.debug('Saving schedules to storage...'); // DEBUG level per user preference
    
    try {
        // Save to localStorage
        localStorage.setItem('huntarr-schedules', JSON.stringify(schedules));
        console.debug(`Successfully saved ${schedules.length} schedules to localStorage`);
        
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
    } catch (error) {
        console.error('Error saving schedules:', error);
    }
    
    // Re-render the list
    renderSchedules();
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
            actionText = `API Limits ${limit}`;
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
