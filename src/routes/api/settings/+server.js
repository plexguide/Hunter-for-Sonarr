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

// Parse numeric settings properly
function parseNumericSettings(settings) {
  if (!settings) return {};
  
  const result = { ...settings };
  
  // Define which fields should be numeric
  const numericFields = [
    'missingEpisodesSearch', 'upgradeEpisodesSearch', 'searchInterval',
    'hunt_missing_shows', 'hunt_upgrade_episodes', 'sleep_duration',
    'hunt_missing_movies', 'hunt_upgrade_movies', 'state_reset_interval_hours',
    'hunt_missing_albums', 'hunt_upgrade_tracks', 'hunt_missing_books', 
    'hunt_upgrade_books', 'api_timeout', 'command_wait_delay',
    'command_wait_attempts', 'minimum_download_queue_size'
  ];
  
  // Parse any numeric fields at the root level
  numericFields.forEach(field => {
    if (result[field] !== undefined) {
      result[field] = parseInt(result[field], 10);
    }
  });
  
  // Parse nested objects
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

// GET handler
export async function GET() {
  const config = readConfig();
  return json(config);
}

// POST handler
export async function POST({ request }) {
  try {
    let newSettings = await request.json();
    
    // Parse numeric values consistently
    newSettings = parseNumericSettings(newSettings);
    
    // Read existing config to merge with new settings
    const existingConfig = readConfig();
    
    // Create deep merged config to preserve nested structures
    const updatedConfig = deepMerge(existingConfig, newSettings);
    
    // Write updated config
    const success = writeConfig(updatedConfig);
    
    if (success) {
      // Return the fully updated config so UI can refresh with correct values
      return json(updatedConfig);
    } else {
      return json({ error: 'Failed to save settings' }, { status: 500 });
    }
  } catch (error) {
    console.error('Error processing settings:', error);
    return json({ error: 'Server error' }, { status: 500 });
  }
}

// Helper for deep merging objects
function deepMerge(target, source) {
  const output = { ...target };
  
  if (isObject(target) && isObject(source)) {
    Object.keys(source).forEach(key => {
      if (isObject(source[key])) {
        if (!(key in target)) {
          output[key] = source[key];
        } else {
          output[key] = deepMerge(target[key], source[key]);
        }
      } else {
        output[key] = source[key];
      }
    });
  }
  
  return output;
}

function isObject(item) {
  return (item && typeof item === 'object' && !Array.isArray(item));
}
