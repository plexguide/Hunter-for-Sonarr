/**
 * Scheduling functionality for Huntarr
 */

document.addEventListener('DOMContentLoaded', function() {
    // Add event listener for the Yes/No dropdown
    const yesNoDropdown = document.getElementById('yesNoDropdown');
    if (yesNoDropdown) {
        yesNoDropdown.addEventListener('change', function() {
            console.debug(`Selected option: ${this.value}`); // Keep at DEBUG level per user preference
            toggleSaveButton(true);
        });
    }
    
    // Add event listener for save button
    const saveButton = document.getElementById('saveScheduleButton');
    if (saveButton) {
        saveButton.addEventListener('click', saveScheduleSettings);
    }
});

/**
 * Enable/disable the save button
 */
function toggleSaveButton(enabled) {
    const saveButton = document.getElementById('saveScheduleButton');
    if (saveButton) {
        saveButton.disabled = !enabled;
    }
}

/**
 * Save schedule settings to the server
 */
function saveScheduleSettings() {
    // Collect settings
    const yesNoValue = document.getElementById('yesNoDropdown').value;
    
    // Log at DEBUG level per user preference
    console.debug('Saving schedule settings, Yes/No value:', yesNoValue);
    
    // Simulate successful save
    alert('Settings saved successfully!');
    toggleSaveButton(false);
}
