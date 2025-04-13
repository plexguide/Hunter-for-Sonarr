<script>
  import { onMount } from 'svelte';
  import { writable } from 'svelte/store';

  let settings = writable({});
  let showSuccessMessage = false;
  let showErrorMessage = false;
  let errorMessage = "";
  let isSaving = false;

  // Ensure settings are properly loaded on component mount
  onMount(async () => {
    try {
      const response = await fetch('/api/settings');
      if (response.ok) {
        const data = await response.json();
        settings.set(ensureNumericValues(data));
      }
    } catch (error) {
      console.error('Error loading settings:', error);
    }
  });
  
  async function loadSettings() {
    try {
      const response = await fetch('/api/settings');
      if (response.ok) {
        const data = await response.json();
        // Ensure all numeric values are properly handled
        settings.set(ensureNumericValues(data));
      }
    } catch (error) {
      console.error('Error loading settings:', error);
    }
  }

  // Helper to ensure numeric values are handled correctly
  function ensureNumericValues(data) {
    const numericFields = [
      'missingEpisodesSearch', 'upgradeEpisodesSearch', 'searchInterval',
      'hunt_missing_shows', 'hunt_upgrade_episodes', 'sleep_duration'
    ];
    
    const result = { ...data };
    
    // Process top level numeric fields
    numericFields.forEach(field => {
      if (result[field] !== undefined) {
        result[field] = parseInt(result[field], 10);
      }
    });
    
    // Process nested objects
    ['sonarr', 'radarr', 'lidarr', 'readarr', 'huntarr', 'advanced'].forEach(section => {
      if (result[section]) {
        numericFields.forEach(field => {
          if (result[section][field] !== undefined) {
            result[section][field] = parseInt(result[section][field], 10);
          }
        });
      }
    });
    
    return result;
  }

  // Modify the save function to ensure it updates the UI state
  async function saveSettings() {
    if (isSaving) return; // Prevent multiple simultaneous saves
    
    isSaving = true;
    try {
      const settingsValue = $settings;
      
      const response = await fetch('/api/settings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(settingsValue)
      });
      
      if (!response.ok) {
        throw new Error('Failed to save settings');
      }
      
      // Update local settings state with the saved values
      const savedSettings = await response.json();
      settings.set(ensureNumericValues(savedSettings));
      
      showSuccessMessage = true;
      setTimeout(() => {
        showSuccessMessage = false;
      }, 3000);
    } catch (error) {
      console.error('Error saving settings:', error);
      errorMessage = error.message || "Unknown error occurred";
      showErrorMessage = true;
      setTimeout(() => {
        showErrorMessage = false;
      }, 3000);
    } finally {
      isSaving = false;
    }
  }

  // Manually trigger reload of settings
  async function refreshSettings() {
    await loadSettings();
  }

  // ... existing code for the rest of the component ...
</script>

<!-- ... existing template code ... -->