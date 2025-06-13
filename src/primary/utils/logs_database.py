#!/usr/bin/env python3
"""
Logs Database Manager for Huntarr
Handles all log storage operations in a separate logs.db database
"""

import sqlite3
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from contextlib import contextmanager
import threading

# Don't import logger here to avoid circular dependencies during initialization
# from src.primary.utils.logger import get_logger
# logger = get_logger(__name__)

class LogsDatabase:
    """Database manager for log storage"""
    
    def __init__(self):
        self.db_path = self._get_database_path()
        self.ensure_database_exists()
    
    def _get_database_path(self) -> Path:
        """Get the path to the logs database file"""
        # Use simple fallback approach to avoid import issues
        import os
        config_dir = os.environ.get('CONFIG_DIR', '/config')
        db_path = Path(config_dir) / "logs.db"
        return db_path
    
    def ensure_database_exists(self):
        """Create the logs database and tables if they don't exist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Create logs table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME NOT NULL,
                        level TEXT NOT NULL,
                        app_type TEXT NOT NULL,
                        message TEXT NOT NULL,
                        logger_name TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create indexes for better performance
                conn.execute('CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_logs_app_type ON logs(app_type)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_logs_app_level ON logs(app_type, level)')
                
                conn.commit()
        except Exception as e:
            print(f"Failed to initialize logs database: {e}")
            raise
    
    def insert_log(self, timestamp: datetime, level: str, app_type: str, message: str, logger_name: str = None):
        """Insert a new log entry"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO logs (timestamp, level, app_type, message, logger_name)
                    VALUES (?, ?, ?, ?, ?)
                ''', (timestamp.isoformat(), level, app_type, message, logger_name))
                conn.commit()
        except Exception as e:
            # Don't use logger here to avoid infinite recursion
            print(f"Error inserting log entry: {e}")
    
    def get_logs(self, app_type: str = None, level: str = None, limit: int = 100, offset: int = 0, search: str = None) -> List[Dict[str, Any]]:
        """Get logs with optional filtering"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Build query with filters
                query = "SELECT * FROM logs WHERE 1=1"
                params = []
                
                if app_type:
                    query += " AND app_type = ?"
                    params.append(app_type)
                
                if level:
                    query += " AND level = ?"
                    params.append(level)
                
                if search:
                    query += " AND message LIKE ?"
                    params.append(f"%{search}%")
                
                query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error getting logs: {e}")
            return []
    
    def get_log_count(self, app_type: str = None, level: str = None, search: str = None) -> int:
        """Get total count of logs matching filters"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT COUNT(*) FROM logs WHERE 1=1"
                params = []
                
                if app_type:
                    query += " AND app_type = ?"
                    params.append(app_type)
                
                if level:
                    query += " AND level = ?"
                    params.append(level)
                
                if search:
                    query += " AND message LIKE ?"
                    params.append(f"%{search}%")
                
                cursor = conn.execute(query, params)
                return cursor.fetchone()[0]
        except Exception as e:
            print(f"Error getting log count: {e}")
            return 0
    
    def cleanup_old_logs(self, days_to_keep: int = 30, max_entries_per_app: int = 10000):
        """Clean up old logs based on age and count limits"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Time-based cleanup
                cutoff_date = datetime.now() - timedelta(days=days_to_keep)
                cursor = conn.execute(
                    "DELETE FROM logs WHERE timestamp < ?",
                    (cutoff_date.isoformat(),)
                )
                deleted_by_age = cursor.rowcount
                
                # Count-based cleanup per app type
                app_types = ['system', 'sonarr', 'radarr', 'lidarr', 'readarr', 'whisparr', 'eros', 'swaparr']
                total_deleted_by_count = 0
                
                for app_type in app_types:
                    cursor = conn.execute('''
                        DELETE FROM logs 
                        WHERE app_type = ? AND id NOT IN (
                            SELECT id FROM logs 
                            WHERE app_type = ? 
                            ORDER BY timestamp DESC 
                            LIMIT ?
                        )
                    ''', (app_type, app_type, max_entries_per_app))
                    total_deleted_by_count += cursor.rowcount
                
                conn.commit()
                
                if deleted_by_age > 0 or total_deleted_by_count > 0:
                    print(f"Cleaned up logs: {deleted_by_age} by age, {total_deleted_by_count} by count")
                
                return deleted_by_age + total_deleted_by_count
        except Exception as e:
            print(f"Error cleaning up logs: {e}")
            return 0
    
    def get_app_types(self) -> List[str]:
        """Get list of all app types that have logs"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT DISTINCT app_type FROM logs ORDER BY app_type")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting app types: {e}")
            return []
    
    def get_log_levels(self) -> List[str]:
        """Get list of all log levels that exist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT DISTINCT level FROM logs ORDER BY level")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting log levels: {e}")
            return []
    
    def clear_logs(self, app_type: str = None):
        """Clear logs for a specific app type or all logs"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if app_type:
                    cursor = conn.execute("DELETE FROM logs WHERE app_type = ?", (app_type,))
                else:
                    cursor = conn.execute("DELETE FROM logs")
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                print(f"Cleared {deleted_count} logs" + (f" for {app_type}" if app_type else ""))
                return deleted_count
        except Exception as e:
            print(f"Error clearing logs: {e}")
            return 0


# Global instance
_logs_db = None
_logs_db_lock = threading.Lock()

def get_logs_database() -> LogsDatabase:
    """Get the global logs database instance (thread-safe singleton)"""
    global _logs_db
    if _logs_db is None:
        with _logs_db_lock:
            # Double-check locking pattern
            if _logs_db is None:
                _logs_db = LogsDatabase()
    return _logs_db


def schedule_log_cleanup():
    """Schedule periodic log cleanup - call this from background tasks"""
    import threading
    import time
    
    def cleanup_worker():
        """Background worker to clean up logs periodically"""
        while True:
            try:
                time.sleep(3600)  # Run every hour
                logs_db = get_logs_database()
                deleted_count = logs_db.cleanup_old_logs(days_to_keep=30, max_entries_per_app=10000)
                if deleted_count > 0:
                    print(f"Scheduled cleanup removed {deleted_count} old log entries")
            except Exception as e:
                print(f"Error in scheduled log cleanup: {e}")
    
    # Start cleanup thread
    cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
    cleanup_thread.start()
    print("Scheduled log cleanup thread started") 