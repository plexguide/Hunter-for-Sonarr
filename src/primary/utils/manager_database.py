"""
Manager Database for Huntarr
Handles Hunt Manager (history) operations in a separate manager.db database
"""

import os
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import time

logger = logging.getLogger(__name__)

class ManagerDatabase:
    """Database manager for Hunt Manager functionality"""
    
    def __init__(self):
        self.db_path = self._get_database_path()
        self.ensure_database_exists()
    
    def _get_database_path(self) -> Path:
        """Get database path - use /config for Docker, local data directory for development"""
        # Check if running in Docker (config directory exists)
        config_dir = Path("/config")
        if config_dir.exists() and config_dir.is_dir():
            # Running in Docker - use persistent config directory
            return config_dir / "manager.db"
        else:
            # For local development, use data directory in project root
            project_root = Path(__file__).parent.parent.parent.parent
            data_dir = project_root / "data"
            
            # Ensure directory exists
            data_dir.mkdir(parents=True, exist_ok=True)
            return data_dir / "manager.db"
    
    def ensure_database_exists(self):
        """Create database and all tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('PRAGMA foreign_keys = ON')
            
            # Create hunt_history table for tracking processed media history
            conn.execute('''
                CREATE TABLE IF NOT EXISTS hunt_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    app_type TEXT NOT NULL,
                    instance_name TEXT NOT NULL,
                    media_id TEXT NOT NULL,
                    processed_info TEXT NOT NULL,
                    operation_type TEXT DEFAULT 'missing',
                    discovered BOOLEAN DEFAULT FALSE,
                    date_time INTEGER NOT NULL,
                    date_time_readable TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for better performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_hunt_history_app_instance ON hunt_history(app_type, instance_name)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_hunt_history_date_time ON hunt_history(date_time)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_hunt_history_media_id ON hunt_history(media_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_hunt_history_operation_type ON hunt_history(operation_type)')
            
            conn.commit()
            logger.info(f"Manager database initialized at: {self.db_path}")

    def add_hunt_history_entry(self, app_type: str, instance_name: str, media_id: str, 
                         processed_info: str, operation_type: str = "missing", 
                         discovered: bool = False, date_time: int = None) -> Dict[str, Any]:
        """Add a new hunt history entry to the database"""
        if date_time is None:
            date_time = int(time.time())
        
        date_time_readable = datetime.fromtimestamp(date_time).strftime('%Y-%m-%d %H:%M:%S')
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                INSERT INTO hunt_history 
                (app_type, instance_name, media_id, processed_info, operation_type, discovered, date_time, date_time_readable)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (app_type, instance_name, media_id, processed_info, operation_type, discovered, date_time, date_time_readable))
            
            entry_id = cursor.lastrowid
            conn.commit()
            
            # Return the created entry
            entry = {
                "id": entry_id,
                "app_type": app_type,
                "instance_name": instance_name,
                "media_id": media_id,
                "processed_info": processed_info,
                "operation_type": operation_type,
                "discovered": discovered,
                "date_time": date_time,
                "date_time_readable": date_time_readable
            }
            
            logger.info(f"Added hunt history entry for {app_type}-{instance_name}: {processed_info}")
            return entry

    def get_hunt_history(self, app_type: str = None, search_query: str = None, 
                   page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """Get hunt history entries with pagination and filtering"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Build the base query
            where_conditions = []
            params = []
            
            if app_type and app_type != "all":
                where_conditions.append("app_type = ?")
                params.append(app_type)
            
            if search_query and search_query.strip():
                search_query = search_query.lower()
                where_conditions.append("""
                    (LOWER(processed_info) LIKE ? OR 
                     LOWER(instance_name) LIKE ? OR 
                     LOWER(media_id) LIKE ?)
                """)
                search_param = f"%{search_query}%"
                params.extend([search_param, search_param, search_param])
            
            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)
            
            # Get total count
            count_query = f"SELECT COUNT(*) FROM hunt_history {where_clause}"
            cursor = conn.execute(count_query, params)
            total_entries = cursor.fetchone()[0]
            
            # Calculate pagination
            total_pages = (total_entries + page_size - 1) // page_size if total_entries > 0 else 1
            
            # Adjust page if out of bounds
            if page < 1:
                page = 1
            elif page > total_pages:
                page = total_pages
            
            # Get paginated entries
            offset = (page - 1) * page_size
            entries_query = f"""
                SELECT * FROM hunt_history {where_clause}
                ORDER BY date_time DESC
                LIMIT ? OFFSET ?
            """
            cursor = conn.execute(entries_query, params + [page_size, offset])
            
            entries = []
            current_time = int(time.time())
            
            for row in cursor.fetchall():
                entry = dict(row)
                # Calculate "how long ago"
                seconds_ago = current_time - entry["date_time"]
                entry["how_long_ago"] = self._format_time_ago(seconds_ago)
                entries.append(entry)
            
            return {
                "entries": entries,
                "total_entries": total_entries,
                "total_pages": total_pages,
                "current_page": page
            }

    def clear_hunt_history(self, app_type: str = None):
        """Clear hunt history entries"""
        with sqlite3.connect(self.db_path) as conn:
            if app_type and app_type != "all":
                conn.execute("DELETE FROM hunt_history WHERE app_type = ?", (app_type,))
                logger.info(f"Cleared hunt history for {app_type}")
            else:
                conn.execute("DELETE FROM hunt_history")
                logger.info("Cleared all hunt history")
            conn.commit()

    def handle_instance_rename(self, app_type: str, old_instance_name: str, new_instance_name: str):
        """Handle renaming of an instance by updating hunt history entries"""
        if old_instance_name == new_instance_name:
            return True
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                UPDATE hunt_history 
                SET instance_name = ?
                WHERE app_type = ? AND instance_name = ?
            ''', (new_instance_name, app_type, old_instance_name))
            
            updated_count = cursor.rowcount
            conn.commit()
            
            logger.info(f"Updated {updated_count} hunt history entries for {app_type}: {old_instance_name} -> {new_instance_name}")
            return True

    def migrate_from_huntarr_db(self, huntarr_db_path: Path):
        """Migrate existing history data from huntarr.db to manager.db"""
        if not huntarr_db_path.exists():
            logger.info("No existing huntarr.db found, skipping migration")
            return
        
        try:
            # Connect to source database
            with sqlite3.connect(huntarr_db_path) as source_conn:
                source_conn.row_factory = sqlite3.Row
                
                # Check if history table exists
                cursor = source_conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='history'
                """)
                
                if not cursor.fetchone():
                    logger.info("No history table found in huntarr.db, skipping migration")
                    return
                
                # Get all history entries
                cursor = source_conn.execute("SELECT * FROM history ORDER BY date_time")
                history_entries = cursor.fetchall()
                
                if not history_entries:
                    logger.info("No history entries to migrate")
                    return
                
                # Insert into manager database
                with sqlite3.connect(self.db_path) as dest_conn:
                    for entry in history_entries:
                        dest_conn.execute('''
                            INSERT INTO hunt_history 
                            (app_type, instance_name, media_id, processed_info, operation_type, discovered, date_time, date_time_readable)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            entry['app_type'],
                            entry['instance_name'],
                            entry['media_id'],
                            entry['processed_info'],
                            entry['operation_type'],
                            entry['discovered'],
                            entry['date_time'],
                            entry['date_time_readable']
                        ))
                    
                    dest_conn.commit()
                    logger.info(f"Migrated {len(history_entries)} history entries to manager.db")
                
                # Drop the history table from huntarr.db
                source_conn.execute("DROP TABLE IF EXISTS history")
                source_conn.commit()
                logger.info("Removed history table from huntarr.db")
                
        except Exception as e:
            logger.error(f"Error during history migration: {e}")
            raise

    def _format_time_ago(self, seconds: int) -> str:
        """Format seconds into a human-readable 'time ago' string"""
        if seconds < 60:
            return f"{seconds} second{'s' if seconds != 1 else ''} ago"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif seconds < 86400:
            hours = seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            days = seconds // 86400
            return f"{days} day{'s' if days != 1 else ''} ago"


# Global manager database instance
_manager_database_instance = None

def get_manager_database() -> ManagerDatabase:
    """Get the global manager database instance"""
    global _manager_database_instance
    if _manager_database_instance is None:
        _manager_database_instance = ManagerDatabase()
    return _manager_database_instance 