#!/usr/bin/env python3
import os
import json
from src.utils.logger import logger
import time
from datetime import datetime, timedelta


# Get environment variables
CONFIG_DIR = os.environ.get('CONFIG_DIR', '/config')
STATE_RESET_HOURS = int(os.environ.get('STATE_RESET_HOURS', 168))

# Define state file paths
MISSING_STATE_FILE = os.path.join(CONFIG_DIR, 'stateful', 'processed_missing_shows.json')
UPGRADE_STATE_FILE = os.path.join(CONFIG_DIR, 'stateful', 'processed_upgrade_episodes.json')


def ensure_state_dir():
    """Ensure the state directory exists."""
    os.makedirs(os.path.join(CONFIG_DIR, 'stateful'), exist_ok=True)


def load_state(state_file):
    """Load the state from a file."""
    ensure_state_dir()

    if not os.path.exists(state_file):
        return {}

    try:
        with open(state_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Error loading state file {state_file}: {e}")
        return {}


def save_state(state_data, state_file):
    """Save the state to a file."""
    ensure_state_dir()

    try:
        with open(state_file, 'w') as f:
            json.dump(state_data, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving state file {state_file}: {e}")


def mark_show_processed(show_id):
    """Mark a show as processed for missing episodes."""
    state = load_state(MISSING_STATE_FILE)
    state[str(show_id)] = {
        'processed_at': datetime.now().isoformat(),
        'expires_at': (datetime.now() + timedelta(hours=STATE_RESET_HOURS)).isoformat()
    }
    save_state(state, MISSING_STATE_FILE)
    logger.debug(f"Marked show ID {show_id} as processed")


def mark_episode_processed(episode_id):
    """Mark an episode as processed for quality upgrades."""
    state = load_state(UPGRADE_STATE_FILE)
    state[str(episode_id)] = {
        'processed_at': datetime.now().isoformat(),
        'expires_at': (datetime.now() + timedelta(hours=STATE_RESET_HOURS)).isoformat()
    }
    save_state(state, UPGRADE_STATE_FILE)
    logger.debug(f"Marked episode ID {episode_id} as processed")


def is_show_processed(show_id):
    """Check if a show has been processed for missing episodes."""
    state = load_state(MISSING_STATE_FILE)
    if str(show_id) not in state:
        return False

    try:
        expires_at = datetime.fromisoformat(state[str(show_id)]['expires_at'])
        if expires_at < datetime.now():
            return False
        return True
    except (KeyError, ValueError):
        return False


def is_episode_processed(episode_id):
    """Check if an episode has been processed for quality upgrades."""
    state = load_state(UPGRADE_STATE_FILE)
    if str(episode_id) not in state:
        return False

    try:
        expires_at = datetime.fromisoformat(state[str(episode_id)]['expires_at'])
        if expires_at < datetime.now():
            return False
        return True
    except (KeyError, ValueError):
        return False


def clean_expired_state():
    """Remove expired entries from state files."""
    # Clean missing shows state
    missing_state = load_state(MISSING_STATE_FILE)
    cleaned_missing = {}
    for show_id, data in missing_state.items():
        try:
            expires_at = datetime.fromisoformat(data['expires_at'])
            if expires_at > datetime.now():
                cleaned_missing[show_id] = data
        except (KeyError, ValueError):
            # Skip invalid entries
            pass

    if len(missing_state) != len(cleaned_missing):
        logger.info(f"Cleaned {len(missing_state) - len(cleaned_missing)} expired shows from state")
        save_state(cleaned_missing, MISSING_STATE_FILE)

    # Clean upgrade episodes state
    upgrade_state = load_state(UPGRADE_STATE_FILE)
    cleaned_upgrade = {}
    for episode_id, data in upgrade_state.items():
        try:
            expires_at = datetime.fromisoformat(data['expires_at'])
            if expires_at > datetime.now():
                cleaned_upgrade[episode_id] = data
        except (KeyError, ValueError):
            # Skip invalid entries
            pass

    if len(upgrade_state) != len(cleaned_upgrade):
        logger.info(f"Cleaned {len(upgrade_state) - len(cleaned_upgrade)} expired episodes from state")
        save_state(cleaned_upgrade, UPGRADE_STATE_FILE)


def reset_all_state():
    """Reset all state files."""
    logger.info("Resetting all state files")
    save_state({}, MISSING_STATE_FILE)
    save_state({}, UPGRADE_STATE_FILE)
