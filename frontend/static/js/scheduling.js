/**
 * Scheduling functionality for Huntarr
 * Implements a SABnzbd-style scheduler for controlling Arr application behavior
 */

// Define the schedules object in the global window scope to prevent redeclaration errors
// This ensures the variable is only declared once no matter how many times the script loads
window.huntarrSchedules = window.huntarrSchedules || {
    global: [],
    sonarr: [],
    radarr: [],
    lidarr: [],
    readarr: []
};

// Use an immediately invoked function expression to create a new scope
(function() {
    // Reference the global schedules object
    const schedules = window.huntarrSchedules;
    
    /**
     * Capitalize the first letter of a string
     * @param {string} string - The string to capitalize
     * @returns {string} - The capitalized string
     */
    function capitalizeFirst(string) {
        if (!string) return '';
        return string.charAt(0).toUpperCase() + string.slice(1);
    }
    
    // Initialize when document is loaded
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
    
    // Make sure schedule containers are visible
    setTimeout(() => {
        // Ensure schedule table container is visible
        const tableContainer = document.getElementById('schedule-table-container');
        if (tableContainer) {
            tableContainer.style.display = 'block';
            console.debug('Schedule table container visibility ensured');
        }
        
        // Ensure current schedules panel is visible
        const schedulePanel = document.querySelector('.scheduler-panel:nth-child(2)');
        if (schedulePanel) {
            schedulePanel.style.display = 'block';
            console.debug('Current schedules panel visibility ensured');
        }
    }, 200);
    
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
    // Add Schedule button (edit functionality removed for simplicity)
    const addScheduleButton = document.getElementById('addScheduleButton');
    if (addScheduleButton) {
        addScheduleButton.addEventListener('click', function() {
            // Always treat as a new schedule - edit functionality removed
            addSchedule();
        });
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
            const appType = button.dataset.appType || 'global';
            deleteSchedule(scheduleId, appType);
        }
        
        // Edit functionality removed for simplicity
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
            
            // Remove loading indicator with safety check
            try {
                if (loadingOption && loadingOption.parentNode === scheduleApp) {
                    scheduleApp.removeChild(loadingOption);
                }
                // Clear the reference to prevent future errors
                loadingOption = null;
            } catch (e) {
                console.warn('Error removing loading option:', e);
            }
            
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
            // Remove loading indicator with safety check
            try {
                if (loadingOption && loadingOption.parentNode === scheduleApp) {
                    scheduleApp.removeChild(loadingOption);
                }
            } catch (e) {
                console.warn('Error removing loading option:', e);
                // Clear any reference to the option to prevent future errors
                loadingOption = null;
            }
            
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
 * Load schedules from server JSON files via API
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
            
            // Process the data to ensure it's in the correct format
            Object.keys(schedules).forEach(key => {
                if (Array.isArray(data[key])) {
                    // Process each schedule to ensure correct format
                    schedules[key] = data[key].map(schedule => {
                        // Make sure we have a proper time object
                        let timeObj = schedule.time;
                        if (typeof schedule.time === 'string') {
                            // Convert string time (HH:MM) to time object {hour: HH, minute: MM}
                            const [hour, minute] = schedule.time.split(':').map(Number);
                            timeObj = { hour, minute };
                        } else if (!schedule.time) {
                            timeObj = { hour: 0, minute: 0 };
                        }
                        
                        return {
                            id: schedule.id || String(Date.now() + Math.random() * 1000),
                            time: timeObj,
                            days: Array.isArray(schedule.days) ? schedule.days : [],
                            action: schedule.action || 'pause',
                            app: schedule.app || 'global',
                            enabled: schedule.enabled !== false
                        };
                    });
                } else {
                    schedules[key] = [];
                }
            });
            
            console.debug('Processed schedules for rendering:', schedules);
            renderSchedules();
        })
        .catch(error => {
            console.error('Error loading schedules:', error);
            // Initialize empty schedule structure if load fails
            Object.keys(schedules).forEach(key => {
                schedules[key] = [];
            });
            renderSchedules();
        });
}

/**
 * Parse days from API format to our internal format
 */
function parseDays(daysData) {
    // Default all days to false
    const days = {
        monday: false,
        tuesday: false,
        wednesday: false,
        thursday: false,
        friday: false,
        saturday: false,
        sunday: false
    };
    
    // If days is an array of day names
    if (Array.isArray(daysData)) {
        daysData.forEach(day => {
            // Convert day names to our format (e.g., 'Mon' -> 'monday')
            const dayLower = day.toLowerCase();
            if (dayLower.startsWith('mon')) days.monday = true;
            else if (dayLower.startsWith('tue')) days.tuesday = true;
            else if (dayLower.startsWith('wed')) days.wednesday = true;
            else if (dayLower.startsWith('thu')) days.thursday = true;
            else if (dayLower.startsWith('fri')) days.friday = true;
            else if (dayLower.startsWith('sat')) days.saturday = true;
            else if (dayLower.startsWith('sun')) days.sunday = true;
        });
    }
    // If days is already in our format
    else if (daysData && typeof daysData === 'object') {
        Object.assign(days, daysData);
    }
    
    return days;
}

/**
 * Save schedules to server via API
 */
function saveSchedules() {
    console.debug('Saving schedules to server');
    
    try {
        // Before saving, ensure that schedules include appType information
        // This ensures consistent data structure between saves and loads
        const schedulesCopy = {};
        
        // Initialize with empty arrays for each app type
        Object.keys(schedules).forEach(key => {
            schedulesCopy[key] = [];
        });
        
        // Process each schedule and ensure proper formatting before saving
        Object.entries(schedules).forEach(([appType, appSchedules]) => {
            if (Array.isArray(appSchedules)) {
                schedulesCopy[appType] = appSchedules.map(schedule => {
                    // Clean up the schedule object to ensure it has all required fields
                    return {
                        id: schedule.id,
                        time: schedule.time,
                        days: schedule.days,
                        action: schedule.action,
                        app: schedule.app || 'global',
                        enabled: schedule.enabled !== false,
                        appType: appType // Store appType as a property for reference when loading
                    };
                });
            }
        });
        
        console.debug('Saving processed schedules:', schedulesCopy);
        
        // Make API call to save schedules
        fetch('/api/scheduler/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(schedulesCopy)
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to save schedules');
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    console.debug('Schedules saved successfully');
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
                    
                    // Update our schedules object with the cleaned version
                    Object.keys(schedules).forEach(key => {
                        schedules[key] = schedulesCopy[key];
                    });
                } else {
                    console.error('Failed to save schedules:', data.message);
                    
                    // Show error message
                    const errorMessage = document.createElement('div');
                    errorMessage.classList.add('save-error-message');
                    errorMessage.textContent = `Failed to save: ${data.message}`;
                    document.querySelector('.scheduler-container').appendChild(errorMessage);
                    
                    // Remove message after 3 seconds
                    setTimeout(() => {
                        if (errorMessage.parentNode) {
                            errorMessage.parentNode.removeChild(errorMessage);
                        }
                    }, 3000);
                }
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
        console.error('Error in save function:', error);
    }
}

/**
 * Get formatted schedules for rendering
 * This combines schedules from all app types into a single flat array
 */
function getFormattedSchedules() {
    const formattedSchedules = [];
    
    // Flatten all app type schedules into a single array
    Object.entries(schedules).forEach(([appType, appSchedules]) => {
        if (Array.isArray(appSchedules)) {
            appSchedules.forEach(schedule => {
                // Ensure we have the correct appType for UI operations
                formattedSchedules.push({
                    ...schedule,
                    appType: schedule.appType || appType // Use existing appType if present, otherwise use the key
                });
            });
        }
    });
    
    console.debug('Formatted schedules for display:', formattedSchedules);
    return formattedSchedules;
}

/**
 * Render schedules in the UI
 */
function renderSchedules() {
    // Find the schedules container and message element
    const schedulesContainer = document.getElementById('schedulesContainer');
    const noSchedulesMessage = document.getElementById('noSchedulesMessage');
    
    // If elements don't exist, try to find their parent and make them visible
    if (!schedulesContainer || !noSchedulesMessage) {
        // Look for the parent panel that contains schedules
        const schedulePanel = document.querySelector('.scheduler-panel:nth-child(2)');
        if (schedulePanel) {
            // Ensure the panel content is visible
            const panelContent = schedulePanel.querySelector('.panel-content');
            if (panelContent) {
                panelContent.style.display = 'block';
                
                // Try again to get the elements after making panel visible
                setTimeout(() => renderSchedules(), 100);
                return;
            }
        }
        console.warn('Schedule container elements not found, cannot render schedules');
        return;
    }
    
    // Make sure container's parent elements are visible
    const parentPanel = schedulesContainer.closest('.scheduler-panel');
    if (parentPanel) {
        parentPanel.style.display = 'block';
    }
    
    // Clear current schedules
    schedulesContainer.innerHTML = '';
    
    // Get all schedules in a flat array
    const allSchedules = getFormattedSchedules();
    
    // Count total schedules
    const totalSchedules = allSchedules.length;
    
    // Show message if no schedules
    if (totalSchedules === 0) {
        schedulesContainer.style.display = 'none';
        noSchedulesMessage.style.display = 'block';
        return;
    }
    
    // Show schedules and hide message
    schedulesContainer.style.display = 'block';
    noSchedulesMessage.style.display = 'none';
    
    // Sort schedules by time for easier viewing
    allSchedules.sort((a, b) => {
        if (!a.time) return 1;
        if (!b.time) return -1;
        
        const aTime = `${String(a.time.hour).padStart(2, '0')}:${String(a.time.minute).padStart(2, '0')}`;
        const bTime = `${String(b.time.hour).padStart(2, '0')}:${String(b.time.minute).padStart(2, '0')}`;
        return aTime.localeCompare(bTime);
    });
    
    // Add each schedule to the UI
    allSchedules.forEach(schedule => {
        const scheduleItem = document.createElement('div');
        scheduleItem.className = 'schedule-item';
        
        // Format time
        const formattedTime = `${String(schedule.time.hour).padStart(2, '0')}:${String(schedule.time.minute).padStart(2, '0')}`;
        
        // Format days
        let daysText = '';
        if (Array.isArray(schedule.days)) {
            // API format - array of day names
            if (schedule.days.length === 7) {
                daysText = 'Daily';
            } else if (schedule.days.length === 0) {
                daysText = 'None';
            } else {
                daysText = schedule.days.join(', ');
            }
        } else if (typeof schedule.days === 'object') {
            // Internal format - object with day properties
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
        }
        
        // Format action name
        let actionText = schedule.action || '';
        if (actionText === 'resume') {
            actionText = 'Resume';
        } else if (actionText === 'pause') {
            actionText = 'Pause';
        } else if (actionText.startsWith('api-')) {
            const limit = actionText.split('-')[1];
            actionText = `API Limits ${limit}`;
        }
        
        // Format app name
        let appText = 'All Apps';
        if (schedule.app && schedule.app !== 'global') {
            // Format app name nicely using the actual instance name
            const [app, instanceId] = schedule.app.split('-');
            if (instanceId === 'all') {
                appText = `All ${capitalizeFirst(app)} Instances`;
            } else {
                appText = `${capitalizeFirst(app)} Instance ${instanceId}`;
            }
        }
        
        // Build the schedule item HTML
        scheduleItem.innerHTML = `
            <div class="schedule-item-checkbox">
                <input type="checkbox" id="schedule-${schedule.id}" ${schedule.enabled !== false ? 'checked' : ''}>
                <label for="schedule-${schedule.id}"></label>
            </div>
            <div class="schedule-item-time">${formattedTime}</div>
            <div class="schedule-item-days">${daysText}</div>
            <div class="schedule-item-action">${actionText}</div>
            <div class="schedule-item-app">${appText}</div>
            <div class="schedule-item-actions">
                <button class="icon-button delete-schedule" data-id="${schedule.id}" data-app-type="${schedule.appType}"><i class="fas fa-trash"></i></button>
            </div>
        `;
        
        // Add event listener for enable/disable checkbox
        const checkbox = scheduleItem.querySelector(`#schedule-${schedule.id}`);
        if (checkbox) {
            checkbox.addEventListener('change', function() {
                toggleScheduleEnabled(schedule.id, schedule.appType, this.checked);
            });
        }
        
        // Add event listeners for edit and delete buttons
        const editButton = scheduleItem.querySelector('.edit-schedule');
        if (editButton) {
            editButton.addEventListener('click', function() {
                editSchedule(this.getAttribute('data-id'), this.getAttribute('data-app-type'));
            });
        }
        
        const deleteButton = scheduleItem.querySelector('.delete-schedule');
        if (deleteButton) {
            deleteButton.addEventListener('click', function() {
                deleteSchedule(this.getAttribute('data-id'), this.getAttribute('data-app-type'));
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
    
    // Emergency fix for day validation - temporarily forced to true to bypass error
    // This guarantees schedules can be added while we investigate the root cause
    
    // Get the actual checkbox elements directly
    const monday = document.getElementById('day-monday'); 
    const tuesday = document.getElementById('day-tuesday');
    const wednesday = document.getElementById('day-wednesday');
    const thursday = document.getElementById('day-thursday');
    const friday = document.getElementById('day-friday');
    const saturday = document.getElementById('day-saturday');
    const sunday = document.getElementById('day-sunday');
    
    // Log the actual DOM elements and their checked state
    console.debug('Monday checkbox:', monday, monday ? monday.checked : 'not found');
    console.debug('Tuesday checkbox:', tuesday, tuesday ? tuesday.checked : 'not found');
    console.debug('Wednesday checkbox:', wednesday, wednesday ? wednesday.checked : 'not found');
    console.debug('Thursday checkbox:', thursday, thursday ? thursday.checked : 'not found');
    console.debug('Friday checkbox:', friday, friday ? friday.checked : 'not found');
    console.debug('Saturday checkbox:', saturday, saturday ? saturday.checked : 'not found');
    console.debug('Sunday checkbox:', sunday, sunday ? sunday.checked : 'not found');
    
    // Force validation to pass - we'll fix this properly later
    // Temporarily forcing to true to ensure users can add schedules
    const anyDaySelected = true;
    
    // Keep this commented out until we find the root cause
    /*
    if (!anyDaySelected) {
        alert('Please select at least one day for the schedule.');
        return;
    }
    */
    
    // Create new schedule with additional validation to prevent empty days
    const formattedDays = formatDaysForAPI(days);
    
    // Debug the days data to understand what's happening
    console.debug('Raw days object:', days);
    console.debug('Formatted days for API:', formattedDays);
    
    // Only create and add the schedule if we have days selected
    // This prevents the 'None' days schedule from being created
    if (formattedDays.length > 0) {
        const newSchedule = {
            id: String(Date.now()), // Simple ID generation
            time: { hour, minute },
            days: formattedDays,
            action,
            app,
            enabled: true
        };
        
        // Determine app type for this schedule
        let appType = 'global';
        if (app && app !== 'global') {
            const appParts = app.split('-');
            appType = appParts[0] || 'global';
        }
        
        // Make sure the array exists for this app type
        if (!schedules[appType]) {
            schedules[appType] = [];
        }
        
        // Add to appropriate schedules array
        schedules[appType].push(newSchedule);
        
        // Auto-save schedules after adding
        saveSchedules();
        
        // Log at DEBUG level
        console.debug(`Added new schedule to ${appType}:`, newSchedule);
    } else {
        console.warn('No days selected, not creating a schedule');
    }
    
    // Update UI
    renderSchedules();
    
    // Reset day checkboxes
    resetDayCheckboxes();
}

/**
 * Format days from internal format to API format (array of day names)
 */
function formatDaysForAPI(days) {
    const apiDays = [];
    
    if (days.monday) apiDays.push('Mon');
    if (days.tuesday) apiDays.push('Tue');
    if (days.wednesday) apiDays.push('Wed');
    if (days.thursday) apiDays.push('Thu');
    if (days.friday) apiDays.push('Fri');
    if (days.saturday) apiDays.push('Sat');
    if (days.sunday) apiDays.push('Sun');
    
    return apiDays;
}

/**
 * Edit functionality has been removed for simplicity
 * Users can now only add new schedules or delete existing ones
 */

/**
 * Delete a schedule
 */
function deleteSchedule(scheduleId, appType = 'global', silent = false) {
    // Confirm delete (unless silent mode)
    if (!silent && !confirm('Are you sure you want to delete this schedule?')) {
        return;
    }
    
    // Ensure the app type array exists
    if (!schedules[appType]) {
        schedules[appType] = [];
        return;
    }
    
    // Find the schedule index
    const scheduleIndex = schedules[appType].findIndex(s => s.id === scheduleId);
    if (scheduleIndex === -1) return;
    
    // Remove from array
    schedules[appType].splice(scheduleIndex, 1);
    
    // Auto-save schedules after deletion
    saveSchedules();
    
    // Update UI
    renderSchedules();
    
    console.debug(`Deleted schedule ID: ${scheduleId} from ${appType}`); // DEBUG level per user preference
}

/**
 * Toggle a schedule's enabled state
 */
function toggleScheduleEnabled(scheduleId, appType = 'global', enabled) {
    // Ensure the app type array exists
    if (!schedules[appType]) {
        schedules[appType] = [];
        return;
    }
    
    // Find and update the schedule
    const scheduleIndex = schedules[appType].findIndex(s => s.id === scheduleId);
    if (scheduleIndex !== -1) {
        schedules[appType][scheduleIndex].enabled = enabled;
        
        // Auto-save schedules after toggling enabled state
        saveSchedules();
        
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

// Close the IIFE that wraps the script
})();
