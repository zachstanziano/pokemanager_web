"""
Database interface for Pokemon TCG Inventory System
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class InventoryDB:
    """SQLite database interface for inventory management"""
    
    def __init__(self, db_path: str = "data/inventory.db"):
        """Initialize database connection"""
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        
        # Initialize database tables
        self._init_tables()
        
        # Load initial set data if database is empty
        if not self._has_sets():
            self._load_initial_sets()
    
    def _init_tables(self):
        """Initialize database tables"""
        with self.conn:
            # Sets table
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS sets (
                    name TEXT PRIMARY KEY,
                    code TEXT,
                    series TEXT,
                    packs_per_box INTEGER DEFAULT 36
                )
            ''')
            
            # Business boxes table (for inventory)
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS business_boxes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    set_name TEXT,
                    purchase_date DATE,
                    source TEXT,
                    price REAL,
                    packs_opened INTEGER DEFAULT 0,
                    packs_sold INTEGER DEFAULT 0,
                    FOREIGN KEY (set_name) REFERENCES sets (name)
                )
            ''')
            
            # Stashed boxes table (for personal collection)
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS stashed_boxes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    set_name TEXT,
                    purchase_date DATE,
                    source TEXT,
                    price REAL,
                    FOREIGN KEY (set_name) REFERENCES sets (name)
                )
            ''')
            
            # Slabs table (for PSA graded cards)
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS slabs (
                    cert_number TEXT PRIMARY KEY,
                    set_name TEXT,
                    card_number TEXT,
                    card_name TEXT,
                    grade INTEGER,
                    submission_date DATE,
                    status TEXT,
                    psa_details_fetched BOOLEAN DEFAULT 0,
                    front_image_path TEXT,
                    back_image_path TEXT,
                    FOREIGN KEY (set_name) REFERENCES sets (name)
                )
            ''')
    
    def _has_sets(self) -> bool:
        """Check if sets table has data"""
        return bool(self.conn.execute('SELECT 1 FROM sets LIMIT 1').fetchone())
    
    def _load_initial_sets(self):
        """Load initial set data from JSON"""
        try:
            with open('data/pokemon_sets.json', 'r') as f:
                data = json.load(f)
                
            with self.conn:
                for series_name, series_data in data['series'].items():
                    # Process main sets
                    for set_info in series_data.get('main_sets', []):
                        self.conn.execute('''
                            INSERT OR REPLACE INTO sets (
                                name, code, series
                            ) VALUES (?, ?, ?)
                        ''', (
                            set_info['name'],
                            set_info.get('code', ''),
                            series_name.replace('_', ' ').title()
                        ))
        except Exception as e:
            print(f"Error loading initial sets: {str(e)}")
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def get_sets_by_series(self, series: Optional[str] = None) -> List[Dict]:
        """Get all sets, optionally filtered by series"""
        query = '''
            SELECT 
                s.name,
                s.code,
                s.series,
                s.packs_per_box,
                COUNT(bb.id) as business_boxes,
                COUNT(sb.id) as stashed_boxes,
                SUM(CASE WHEN bb.id IS NOT NULL 
                    THEN s.packs_per_box - bb.packs_opened - bb.packs_sold 
                    ELSE 0 END) as available_packs,
                SUM(CASE WHEN bb.id IS NOT NULL 
                    THEN bb.packs_sold 
                    ELSE 0 END) as packs_sold,
                COUNT(sl.cert_number) as slab_count,
                CASE WHEN bb.id IS NOT NULL 
                    THEN ROUND(AVG(bb.price), 2)
                    ELSE NULL END as avg_box_price
            FROM sets s
            LEFT JOIN business_boxes bb ON s.name = bb.set_name
            LEFT JOIN stashed_boxes sb ON s.name = sb.set_name
            LEFT JOIN slabs sl ON s.name = sl.set_name
        '''
        
        if series:
            query += ' WHERE s.series = ?'
            query += ' GROUP BY s.name ORDER BY s.name'
            rows = self.conn.execute(query, (series,)).fetchall()
        else:
            query += ' GROUP BY s.name ORDER BY s.name'
            rows = self.conn.execute(query).fetchall()
            
        return [dict(row) for row in rows]
    
    def get_all_series(self) -> List[str]:
        """Get list of all series in database"""
        rows = self.conn.execute('SELECT DISTINCT series FROM sets ORDER BY series').fetchall()
        return [row[0] for row in rows]
    
    def import_booster_purchases(self, file_path: str) -> Tuple[bool, List[str], List[str]]:
        """Import booster box purchases from CSV"""
        from database.booster_imports import import_booster_purchases
        return import_booster_purchases(self, file_path)
    
    def import_ebay_sales(self, file_path: str) -> bool:
        """Import eBay sales data from CSV"""
        from database.ebay_imports import import_ebay_sales
        return import_ebay_sales(self, file_path)
    
    def import_psa_submissions(self, file_path: str) -> bool:
        """Import PSA submissions from CSV"""
        from database.psa_imports import import_psa_submissions
        return import_psa_submissions(self, file_path)