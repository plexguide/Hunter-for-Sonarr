import fs from 'fs';
import path from 'path';

const CONFIG_FILE = path.resolve('huntarr.json');
let cachedConfig = null;
let lastReadTime = 0;
const CACHE_TTL = 2000; // 2 seconds cache time

// Read config from file
export function readConfig(forceRefresh = false) {
  const now = Date.now();
  
  // Use cached config if available and not forced to refresh
  if (!forceRefresh && cachedConfig && now - lastReadTime < CACHE_TTL) {
    return cachedConfig;
  }
  
  try {
    const configData = fs.readFileSync(CONFIG_FILE, 'utf8');
    cachedConfig = JSON.parse(configData);
    lastReadTime = now;
    return cachedConfig;
  } catch (error) {
    console.error('Error reading config:', error);
    // Return default config if file doesn't exist
    return {
      sonarr: {
        url: '',
        apiKey: '',
        missingEpisodesSearch: 1,
        upgradeEpisodesSearch: 0,
        searchInterval: 900
      },
      huntarr: {},
      advanced: {}
    };
  }
}

// Write config to file
export function writeConfig(config) {
  try {
    fs.writeFileSync(CONFIG_FILE, JSON.stringify(config, null, 2), 'utf8');
    // Update cache after writing
    cachedConfig = { ...config };
    lastReadTime = Date.now();
    return true;
  } catch (error) {
    console.error('Error writing config:', error);
    return false;
  }
}

// Get a specific config value with proper type conversion
export function getConfig(key, defaultValue = null) {
  const config = readConfig();
  
  if (!key) return config;
  
  const parts = key.split('.');
  let value = config;
  
  for (const part of parts) {
    if (value === undefined || value === null) {
      return defaultValue;
    }
    value = value[part];
  }
  
  // Handle numeric values
  if (typeof defaultValue === 'number' && typeof value === 'string') {
    const num = parseInt(value, 10);
    return isNaN(num) ? defaultValue : num;
  }
  
  return value !== undefined ? value : defaultValue;
}

// Invalidate config cache - call this after external updates
export function invalidateCache() {
  lastReadTime = 0;
  cachedConfig = null;
}
