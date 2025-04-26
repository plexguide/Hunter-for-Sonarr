import { json } from '@sveltejs/kit';
import fs from 'fs';
import path from 'path';

const CONFIG_FILE = path.resolve('huntarr.json');

// Helper to read config
function readConfig() {
  try {
    const configData = fs.readFileSync(CONFIG_FILE, 'utf8');
    return JSON.parse(configData);
  } catch (error) {
    console.error('Error reading config:', error);
    return {};
  }
}

// Helper to write config
function writeConfig(config) {
  try {
    fs.writeFileSync(CONFIG_FILE, JSON.stringify(config, null, 2), 'utf8');
    return true;
  } catch (error) {
    console.error('Error writing config:', error);
    return false;
  }
}

// GET handler
export async function GET() {
  const config = readConfig();
  return json(config);
}

// POST handler
export async function POST({ request }) {
  try {
    const newSettings = await request.json();
    
    // Read existing config to merge with new settings
    const existingConfig = readConfig();
    
    // Merge settings, ensuring numeric values are properly handled
    const updatedConfig = {
      ...existingConfig,
      ...newSettings
    };
    
    // Ensure numeric values are preserved correctly in nested objects
    if (newSettings.sonarr) {
      updatedConfig.sonarr = {
        ...existingConfig.sonarr,
        ...newSettings.sonarr
      };
      
      // Add explicit handling for Sonarr instances array
      if (Array.isArray(newSettings.sonarr.instances)) {
        // Use the new instances array completely, as it should contain all instances
        updatedConfig.sonarr.instances = JSON.parse(JSON.stringify(newSettings.sonarr.instances));
        console.log("Saved Sonarr instances:", updatedConfig.sonarr.instances);
      }
      
      // Explicitly handle numeric fields
      if (newSettings.sonarr.missingEpisodesSearch !== undefined) {
        updatedConfig.sonarr.missingEpisodesSearch = Number(newSettings.sonarr.missingEpisodesSearch);
      }
      if (newSettings.sonarr.upgradeEpisodesSearch !== undefined) {
        updatedConfig.sonarr.upgradeEpisodesSearch = Number(newSettings.sonarr.upgradeEpisodesSearch);
      }
      if (newSettings.sonarr.searchInterval !== undefined) {
        updatedConfig.sonarr.searchInterval = Number(newSettings.sonarr.searchInterval);
      }
    }
    
    // Handle other app settings similarly
    // ...existing code...

    // Write updated config
    const success = writeConfig(updatedConfig);
    
    if (success) {
      // Return the exact config that was saved to ensure UI consistency
      return json(readConfig());
    } else {
      return json({ error: 'Failed to save settings' }, { status: 500 });
    }
  } catch (error) {
    console.error('Error processing settings:', error);
    return json({ error: 'Server error' }, { status: 500 });
  }
}
