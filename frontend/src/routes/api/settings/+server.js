import { json } from '@sveltejs/kit';
import fs from 'fs';
import path from 'path';

const CONFIG_FILE = path.resolve('/config/huntarr.json');
const DEFAULT_SETTINGS = {
    "ui": {
        "dark_mode": true
    },
    "app_type": "sonarr",
    "connections": {},
    "global": {
        "debug_mode": false,
        "command_wait_delay": 1,
        "command_wait_attempts": 600,
        "minimum_download_queue_size": -1,
        "log_refresh_interval_seconds": 30
    },
    "sonarr": {
        "hunt_missing_shows": 1,
        "hunt_upgrade_episodes": 0,
        "sleep_duration": 900,
        "state_reset_interval_hours": 168,
        "monitored_only": true,
        "skip_future_episodes": true,
        "skip_series_refresh": false,
        "random_missing": true,
        "random_upgrades": true,
        "debug_mode": false,
        "api_timeout": 60,
        "command_wait_delay": 1,
        "command_wait_attempts": 600,
        "minimum_download_queue_size": -1,
        "log_refresh_interval_seconds": 30
    },
    "radarr": {
        "hunt_missing_movies": 1,
        "hunt_upgrade_movies": 0,
        "sleep_duration": 900,
        "state_reset_interval_hours": 168,
        "monitored_only": true,
        "skip_future_releases": true,
        "skip_movie_refresh": false,
        "random_missing": true,
        "random_upgrades": true,
        "debug_mode": false,
        "api_timeout": 60,
        "command_wait_delay": 1,
        "command_wait_attempts": 600,
        "minimum_download_queue_size": -1,
        "log_refresh_interval_seconds": 30
    },
    "lidarr": {
        "hunt_missing_albums": 1,
        "hunt_upgrade_tracks": 0,
        "sleep_duration": 900,
        "state_reset_interval_hours": 168,
        "monitored_only": true,
        "skip_future_releases": true,
        "skip_artist_refresh": false,
        "random_missing": true,
        "random_upgrades": true,
        "debug_mode": false,
        "api_timeout": 60,
        "command_wait_delay": 1,
        "command_wait_attempts": 600,
        "minimum_download_queue_size": -1,
        "log_refresh_interval_seconds": 30
    },
    "readarr": {
        "hunt_missing_books": 1,
        "hunt_upgrade_books": 0,
        "sleep_duration": 900,
        "state_reset_interval_hours": 168,
        "monitored_only": true,
        "skip_future_releases": true,
        "skip_author_refresh": false,
        "random_missing": true,
        "random_upgrades": true,
        "debug_mode": false,
        "api_timeout": 60,
        "command_wait_delay": 1,
        "command_wait_attempts": 600,
        "minimum_download_queue_size": -1,
        "log_refresh_interval_seconds": 30
    }
};

// Helper to read config
function readConfig() {
    try {
        if (fs.existsSync(CONFIG_FILE)) {
            const data = fs.readFileSync(CONFIG_FILE, 'utf8');
            return JSON.parse(data);
        } else {
            // Create file with defaults if it doesn't exist
            const defaultSettings = DEFAULT_SETTINGS;
            fs.writeFileSync(CONFIG_FILE, JSON.stringify(defaultSettings, null, 2), 'utf8');
            return defaultSettings;
        }
    } catch (error) {
        console.error('Error reading config file:', error);
        return DEFAULT_SETTINGS;
    }
}

// Helper to write config
function writeConfig(config) {
    try {
        const configDir = path.dirname(CONFIG_FILE);
        if (!fs.existsSync(configDir)) {
            fs.mkdirSync(configDir, { recursive: true });
        }
        fs.writeFileSync(CONFIG_FILE, JSON.stringify(config, null, 2), 'utf8');
        return true;
    } catch (error) {
        console.error('Error writing config file:', error);
        return false;
    }
}

// GET handler
export async function GET({ url }) {
    const app = url.searchParams.get('app');
    const config = readConfig();
    
    if (app) {
        // Return app-specific settings
        return json(config[app] || {});
    } else {
        // Return all settings
        return json(config);
    }
}

// POST handler
export async function POST({ request }) {
    const data = await request.json();
    const app = data.app || data.app_type;
    
    if (!app) {
        return json({ success: false, message: 'No app type specified' });
    }
    
    try {
        const config = readConfig();
        const changes_made = {};
        
        // Handle global app selection
        if (data.app_type) {
            config.app_type = data.app_type;
            changes_made.app_type = true;
        }
        
        // Handle API settings for specific apps
        if (app !== 'global' && app !== 'ui') {
            if (data.api_url !== undefined || data.api_key !== undefined) {
                // Store the API credentials
                if (!config.connections) config.connections = {};
                if (!config.connections[app]) config.connections[app] = {};
                
                if (data.api_url !== undefined) {
                    config.connections[app].api_url = data.api_url;
                    changes_made.api_url = true;
                }
                
                if (data.api_key !== undefined) {
                    config.connections[app].api_key = data.api_key;
                    changes_made.api_key = true;
                }
            }
            
            // Update app-specific settings - maintain flat structure
            if (!config[app]) config[app] = {};
            
            // Remove API url/key from data before merging (since we handle them separately)
            const settingsCopy = { ...data };
            delete settingsCopy.api_url;
            delete settingsCopy.api_key;
            delete settingsCopy.app;
            delete settingsCopy.app_type;
            
            // Check if there's a nested structure with the app name and eliminate it
            if (data[app]) {
                Object.keys(data[app]).forEach(key => {
                    config[app][key] = data[app][key];
                    changes_made[key] = true;
                });
                
                // Remove the app-nested structure we just processed
                delete settingsCopy[app];
            }
            
            // Process any remaining flat keys
            Object.keys(settingsCopy).forEach(key => {
                config[app][key] = settingsCopy[key];
                changes_made[key] = true;
            });
        } else if (app === 'global') {
            // Update global settings
            if (!config.global) config.global = {};
            
            // Remove app info before merging
            const settingsCopy = { ...data };
            delete settingsCopy.app;
            delete settingsCopy.app_type;
            
            // Process UI settings separately
            if (settingsCopy.ui) {
                if (!config.ui) config.ui = {};
                Object.keys(settingsCopy.ui).forEach(key => {
                    config.ui[key] = settingsCopy.ui[key];
                    changes_made['ui.' + key] = true;
                });
                delete settingsCopy.ui;
            }
            
            // Process remaining global settings
            Object.keys(settingsCopy).forEach(key => {
                config.global[key] = settingsCopy[key];
                changes_made[key] = true;
            });
        }
        
        // Write the updated config
        const success = writeConfig(config);
        
        return json({
            success: success,
            changes_made: Object.keys(changes_made).length > 0,
            message: success ? 'Settings saved successfully' : 'Error saving settings'
        });
    } catch (error) {
        console.error('Error handling settings update:', error);
        return json({
            success: false,
            message: 'Error updating settings: ' + error.message
        });
    }
}
