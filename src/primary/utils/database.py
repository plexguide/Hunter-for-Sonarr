"""
SQLite Database Manager for Huntarr
Replaces all JSON file operations with SQLite database for better performance and reliability.
Handles both app configurations, general settings, and stateful management data.
"""

import os
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class HuntarrDatabase:
    """Database manager for all Huntarr configurations and settings"""
    
    def __init__(self):
        self.db_path = self._get_database_path()
        self.ensure_database_exists()
    
    def _get_database_path(self) -> Path:
        """Get database path - use local data directory for development"""
        # For local development, use data directory in project root
        project_root = Path(__file__).parent.parent.parent.parent
        data_dir = project_root / "data"
        
        # Ensure directory exists
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir / "huntarr.db"
    
    def ensure_database_exists(self):
        """Create database and all tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('PRAGMA foreign_keys = ON')
            
            # Create app_configs table for all app settings
            conn.execute('''
                CREATE TABLE IF NOT EXISTS app_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    app_type TEXT NOT NULL UNIQUE,
                    config_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create general_settings table for general/global settings
            conn.execute('''
                CREATE TABLE IF NOT EXISTS general_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_key TEXT NOT NULL UNIQUE,
                    setting_value TEXT NOT NULL,
                    setting_type TEXT DEFAULT 'string',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create stateful_lock table for stateful management lock info
            conn.execute('''
                CREATE TABLE IF NOT EXISTS stateful_lock (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    created_at INTEGER NOT NULL,
                    expires_at INTEGER NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create stateful_processed_ids table for processed media IDs
            conn.execute('''
                CREATE TABLE IF NOT EXISTS stateful_processed_ids (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    app_type TEXT NOT NULL,
                    instance_name TEXT NOT NULL,
                    media_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(app_type, instance_name, media_id)
                )
            ''')
            
            # Create indexes for better performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_app_configs_type ON app_configs(app_type)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_general_settings_key ON general_settings(setting_key)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_stateful_processed_app_instance ON stateful_processed_ids(app_type, instance_name)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_stateful_processed_media_id ON stateful_processed_ids(media_id)')
            
            conn.commit()
            logger.info(f"Database initialized at: {self.db_path}")
    
    def get_app_config(self, app_type: str) -> Optional[Dict[str, Any]]:
        """Get app configuration from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT config_data FROM app_configs WHERE app_type = ?',
                (app_type,)
            )
            row = cursor.fetchone()
            
            if row:
                try:
                    return json.loads(row[0])
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON for {app_type}: {e}")
                    return None
            return None
    
    def save_app_config(self, app_type: str, config_data: Dict[str, Any]):
        """Save app configuration to database"""
        config_json = json.dumps(config_data, indent=2)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO app_configs (app_type, config_data, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (app_type, config_json))
            conn.commit()
            logger.info(f"Saved {app_type} configuration to database")
    
    def get_general_settings(self) -> Dict[str, Any]:
        """Get all general settings as a dictionary"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                'SELECT setting_key, setting_value, setting_type FROM general_settings'
            )
            
            settings = {}
            for row in cursor.fetchall():
                key = row['setting_key']
                value = row['setting_value']
                setting_type = row['setting_type']
                
                # Convert value based on type
                if setting_type == 'boolean':
                    settings[key] = value.lower() == 'true'
                elif setting_type == 'integer':
                    settings[key] = int(value)
                elif setting_type == 'float':
                    settings[key] = float(value)
                elif setting_type == 'json':
                    try:
                        settings[key] = json.loads(value)
                    except json.JSONDecodeError:
                        settings[key] = value
                else:  # string
                    settings[key] = value
            
            return settings
    
    def save_general_settings(self, settings: Dict[str, Any]):
        """Save general settings to database"""
        with sqlite3.connect(self.db_path) as conn:
            for key, value in settings.items():
                # Determine type and convert value
                if isinstance(value, bool):
                    setting_type = 'boolean'
                    setting_value = str(value).lower()
                elif isinstance(value, int):
                    setting_type = 'integer'
                    setting_value = str(value)
                elif isinstance(value, float):
                    setting_type = 'float'
                    setting_value = str(value)
                elif isinstance(value, (list, dict)):
                    setting_type = 'json'
                    setting_value = json.dumps(value)
                else:
                    setting_type = 'string'
                    setting_value = str(value)
                
                conn.execute('''
                    INSERT OR REPLACE INTO general_settings 
                    (setting_key, setting_value, setting_type, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''', (key, setting_value, setting_type))
            
            conn.commit()
            logger.info("Saved general settings to database")
    
    def get_general_setting(self, key: str, default: Any = None) -> Any:
        """Get a specific general setting"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT setting_value, setting_type FROM general_settings WHERE setting_key = ?',
                (key,)
            )
            row = cursor.fetchone()
            
            if row:
                value, setting_type = row
                
                # Convert value based on type
                if setting_type == 'boolean':
                    return value.lower() == 'true'
                elif setting_type == 'integer':
                    return int(value)
                elif setting_type == 'float':
                    return float(value)
                elif setting_type == 'json':
                    try:
                        return json.loads(value)
                    except json.JSONDecodeError:
                        return value
                else:  # string
                    return value
            
            return default
    
    def set_general_setting(self, key: str, value: Any):
        """Set a specific general setting"""
        # Determine type and convert value
        if isinstance(value, bool):
            setting_type = 'boolean'
            setting_value = str(value).lower()
        elif isinstance(value, int):
            setting_type = 'integer'
            setting_value = str(value)
        elif isinstance(value, float):
            setting_type = 'float'
            setting_value = str(value)
        elif isinstance(value, (list, dict)):
            setting_type = 'json'
            setting_value = json.dumps(value)
        else:
            setting_type = 'string'
            setting_value = str(value)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO general_settings 
                (setting_key, setting_value, setting_type, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (key, setting_value, setting_type))
            conn.commit()
            logger.debug(f"Set general setting {key} = {value}")
    
    def get_all_app_types(self) -> List[str]:
        """Get list of all app types in database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT app_type FROM app_configs ORDER BY app_type')
            return [row[0] for row in cursor.fetchall()]
    
    def initialize_from_defaults(self, defaults_dir: Path):
        """Initialize database with default configurations if empty"""
        app_types = ['sonarr', 'radarr', 'lidarr', 'readarr', 'whisparr', 'eros', 'swaparr', 'general']
        
        for app_type in app_types:
            # Check if config already exists
            existing_config = self.get_app_config(app_type) if app_type != 'general' else self.get_general_settings()
            
            if not existing_config:
                # Load default config
                default_file = defaults_dir / f"{app_type}.json"
                if default_file.exists():
                    try:
                        with open(default_file, 'r') as f:
                            default_config = json.load(f)
                        
                        if app_type == 'general':
                            self.save_general_settings(default_config)
                        else:
                            self.save_app_config(app_type, default_config)
                        
                        logger.info(f"Initialized {app_type} with default configuration")
                    except Exception as e:
                        logger.error(f"Failed to initialize {app_type} from defaults: {e}")
    
    def backup_to_json(self, backup_dir: Path):
        """Backup database configurations to JSON files"""
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup app configs
        for app_type in self.get_all_app_types():
            config = self.get_app_config(app_type)
            if config:
                backup_file = backup_dir / f"{app_type}.json"
                with open(backup_file, 'w') as f:
                    json.dump(config, f, indent=2)
                logger.info(f"Backed up {app_type} to {backup_file}")
        
        # Backup general settings
        general_settings = self.get_general_settings()
        if general_settings:
            backup_file = backup_dir / "general.json"
            with open(backup_file, 'w') as f:
                json.dump(general_settings, f, indent=2)
            logger.info(f"Backed up general settings to {backup_file}")

    # Stateful Management Methods
    
    def get_stateful_lock_info(self) -> Dict[str, Any]:
        """Get stateful management lock information"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT created_at, expires_at FROM stateful_lock WHERE id = 1')
            row = cursor.fetchone()
            
            if row:
                return {
                    "created_at": row[0],
                    "expires_at": row[1]
                }
            return {}
    
    def set_stateful_lock_info(self, created_at: int, expires_at: int):
        """Set stateful management lock information"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO stateful_lock (id, created_at, expires_at, updated_at)
                VALUES (1, ?, ?, CURRENT_TIMESTAMP)
            ''', (created_at, expires_at))
            conn.commit()
            logger.debug(f"Set stateful lock: created_at={created_at}, expires_at={expires_at}")
    
    def get_processed_ids(self, app_type: str, instance_name: str) -> Set[str]:
        """Get processed media IDs for a specific app instance"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT media_id FROM stateful_processed_ids 
                WHERE app_type = ? AND instance_name = ?
            ''', (app_type, instance_name))
            
            return {row[0] for row in cursor.fetchall()}
    
    def add_processed_id(self, app_type: str, instance_name: str, media_id: str) -> bool:
        """Add a processed media ID for a specific app instance"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR IGNORE INTO stateful_processed_ids 
                    (app_type, instance_name, media_id)
                    VALUES (?, ?, ?)
                ''', (app_type, instance_name, str(media_id)))
                conn.commit()
                logger.debug(f"Added processed ID {media_id} for {app_type}/{instance_name}")
                return True
        except Exception as e:
            logger.error(f"Error adding processed ID {media_id} for {app_type}/{instance_name}: {e}")
            return False
    
    def is_processed(self, app_type: str, instance_name: str, media_id: str) -> bool:
        """Check if a media ID has been processed for a specific app instance"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT 1 FROM stateful_processed_ids 
                WHERE app_type = ? AND instance_name = ? AND media_id = ?
            ''', (app_type, instance_name, str(media_id)))
            
            return cursor.fetchone() is not None
    
    def clear_all_stateful_data(self):
        """Clear all stateful management data (for reset)"""
        with sqlite3.connect(self.db_path) as conn:
            # Clear processed IDs
            conn.execute('DELETE FROM stateful_processed_ids')
            # Clear lock info
            conn.execute('DELETE FROM stateful_lock')
            conn.commit()
            logger.info("Cleared all stateful management data from database")
    
    def get_stateful_summary(self, app_type: str, instance_name: str) -> Dict[str, Any]:
        """Get summary of stateful data for an app instance"""
        processed_ids = self.get_processed_ids(app_type, instance_name)
        return {
            "processed_count": len(processed_ids),
            "has_processed_items": len(processed_ids) > 0
        }

# Global database instance
_database_instance = None

def get_database() -> HuntarrDatabase:
    """Get the global database instance"""
    global _database_instance
    if _database_instance is None:
        _database_instance = HuntarrDatabase()
    return _database_instance 