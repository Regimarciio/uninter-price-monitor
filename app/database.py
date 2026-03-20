import sqlite3
from datetime import datetime
import logging
from contextlib import contextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path='prices.db'):
        self.db_path = db_path
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def init_database(self):
        """Create table if it doesn't exist"""
        with self.get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    price REAL NOT NULL,
                    currency TEXT DEFAULT 'BRL'
                )
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON prices(timestamp)
            ''')
    
    def save_price(self, price):
        """Save a new price record"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                'INSERT INTO prices (timestamp, price) VALUES (?, ?)',
                (datetime.now(), price)
            )
            logger.info(f"Price saved: R$ {price:.2f}")
            return cursor.lastrowid
    
    def get_last_price(self):
        """Get the most recent price"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM prices 
                ORDER BY timestamp DESC 
                LIMIT 1
            ''')
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_price_history(self, limit=10):
        """Get price history"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM prices 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def price_changed(self, new_price):
        """Check if price changed from last record"""
        last = self.get_last_price()
        if not last:
            return True, None
        
        changed = abs(last['price'] - new_price) > 0.01  # 1 cent tolerance
        return changed, last['price'] if not changed else None