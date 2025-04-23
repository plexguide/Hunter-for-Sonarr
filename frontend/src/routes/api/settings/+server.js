import fs from 'fs';
import path from 'path';
import { json } from '@sveltejs/kit';
import { invalidateCache } from '$lib/config'; // Assuming config.js handles huntarr.json read/write

const CONFIG_FILE = path.resolve('huntarr.json'); // Path to the main config file
const DEFAULT_CONFIGS_DIR = path.resolve('src/primary/default_configs'); // Path to new default configs

// Helper function to load default settings for a specific app
function loadDefaultAppSettings(appName) {
    const defaultFile = path.join(DEFAULT_CONFIGS_DIR, `${appName}.json`);
    try {
        if (fs.existsSync(defaultFile)) {
            const data = fs.readFileSync(defaultFile, 'utf8');
            return JSON.parse(data);
        } else {
            console.warn(`Default settings file not found for app: ${appName}`);
            return {};
        }
    } catch (error) {
        console.error(`Error loading default settings for ${appName}:`, error);
        return {};
    }
}

// Helper function to get all default settings combined
function getAllDefaultSettings() {
    const allDefaults = {};
    const appNames = ['sonarr', 'radarr', 'lidarr', 'readarr']; // Define known apps
    appNames.forEach(appName => {
        const defaults = loadDefaultAppSettings(appName);
        if (Object.keys(defaults).length > 0) {
            allDefaults[appName] = defaults;
        }
    });
    // Add a default 'ui' section if needed by the frontend directly
    // allDefaults.ui = { theme: 'dark', ... };
    return allDefaults;
}


// Helper to read config, creating it from defaults if it doesn't exist
function readConfig() {
    try {
        if (fs.existsSync(CONFIG_FILE)) {
            const data = fs.readFileSync(CONFIG_FILE, 'utf8');
             // Handle potentially empty file
            if (data.trim() === '') {
                 console.warn(`Config file ${CONFIG_FILE} is empty. Creating with defaults.`);
                 const defaultSettings = getAllDefaultSettings();
                 writeConfig(defaultSettings); // Write defaults back
                 return defaultSettings;
            }
            let parsedData = JSON.parse(data);

            // Optional: Merge with defaults to ensure all keys exist?
            // This might be better handled client-side or on save.
            // For now, just return what's in the file. If file is missing/empty, defaults are used.

             // Remove legacy sections if present
            if (parsedData.global) delete parsedData.global;
            // Keep UI section if it exists and is used
            // if (parsedData.ui) ...

            return parsedData;
        } else {
            // Create file with defaults if it doesn't exist
            console.log(`Config file ${CONFIG_FILE} not found. Creating with defaults.`);
            const defaultSettings = getAllDefaultSettings();
            writeConfig(defaultSettings); // Write defaults to the file
            return defaultSettings;
        }
    } catch (error) {
        console.error('Error reading or parsing config file:', error);
        // Fallback to defaults in case of error
        return getAllDefaultSettings();
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
        invalidateCache(); // Invalidate cache after writing
        return true;
    } catch (error) {
        console.error('Error writing config file:', error);
        return false;
    }
}

// GET request handler
export async function GET() {
    const config = readConfig();
    return json(config);
}

// POST request handler
export async function POST({ request }) {
    try {
        const newSettings = await request.json();

        // Optional: Validate or sanitize newSettings here

        // Read current config to potentially merge or just overwrite
        // let currentConfig = readConfig();
        // Merge logic could go here if needed, e.g., preserving a 'ui' section
        // For simplicity, this example overwrites the entire config

        if (writeConfig(newSettings)) {
            return json({ success: true, message: 'Settings saved successfully.' });
        } else {
            return json({ success: false, message: 'Failed to write settings.' }, { status: 500 });
        }
    } catch (error) {
        console.error('Error processing POST request:', error);
        return json({ success: false, message: 'Invalid request data.' }, { status: 400 });
    }
}
