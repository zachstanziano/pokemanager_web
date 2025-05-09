"""
Import handler for sets database
"""

import json
from typing import Dict, Any
from database.inventory_db import InventoryDB

def import_sets_database(db: InventoryDB, file_path: str) -> bool:
    """Import sets from JSON database"""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        with db.conn:
            for set_name, set_data in data['sets'].items():
                # Get series from set data
                series = set_data.get('series', '')
                
                # Get code - for now we'll use a simplified version
                code = set_name.lower().replace(' ', '')
                
                # Get packs per box
                packs_per_box = set_data.get('packs_per_box', 30)
                
                db.conn.execute('''
                    INSERT OR REPLACE INTO sets (
                        name, code, series, packs_per_box
                    ) VALUES (?, ?, ?, ?)
                ''', (
                    set_name,
                    code,
                    series,
                    packs_per_box
                ))
        
        return True
    except Exception as e:
        print(f"Error importing sets database: {str(e)}")
        return False