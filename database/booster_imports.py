"""
Import handler for booster box purchases
"""

import os
import json
from datetime import datetime
from typing import Tuple, List, Dict
from database.inventory_db import InventoryDB

def load_sets_database() -> Dict[str, str]:
    """Load the sets database and create a mapping of normalized names to actual names"""
    sets_map = {}
    try:
        with open('data/pokemon_sets.json', 'r') as f:
            data = json.load(f)
            for series_data in data['series'].values():
                for set_info in series_data.get('main_sets', []):
                    set_name = set_info['name']
                    # Create mapping for both normal and normalized versions
                    sets_map[set_name.lower()] = set_name
                    # Also map without 'ex' if it exists
                    if ' ex' in set_name.lower():
                        sets_map[set_name.lower().replace(' ex', '')] = set_name
    except Exception as e:
        print(f"Error loading sets database: {str(e)}")
        return {}
    return sets_map

def normalize_set_name(name: str, sets_map: Dict[str, str]) -> str:
    """Normalize set name to match database format"""
    normalized = name.lower().strip()
    # Try exact match first
    if normalized in sets_map:
        return sets_map[normalized]
    # Try without 'ex' if present
    if ' ex' in normalized:
        base_name = normalized.replace(' ex', '')
        if base_name in sets_map:
            return sets_map[base_name]
    # Return original if no match found
    return name

def import_booster_purchases(db: InventoryDB, file_path: str) -> Tuple[bool, List[str], List[str]]:
    """
    Import booster box purchases from CSV
    
    Expected format:
    Source,Purchase Date,Boxes Purchased,Business Boxes,Stashed Boxes,Per Box USD,Total,Set,Packs Per Box,Business Packs
    Swivel,2025-02-07,2,2,0,$38.00,$76.00,Mask of Change,30,60
    
    Returns:
    - success: bool
    - unmatched_sets: List of set names not found in database
    - duplicate_entries: List of entries already in database
    """
    try:
        unmatched_sets = []
        duplicate_entries = []
        
        # Load sets mapping
        sets_map = load_sets_database()
        print("Loaded sets mapping:", sets_map)  # Debug
        
        print(f"Opening file: {file_path}")  # Debug
        
        # First, let's aggregate all purchases by set
        set_totals = {}
        
        # Clear existing data
        with db.conn:
            db.conn.execute('DELETE FROM business_boxes')
            db.conn.execute('DELETE FROM stashed_boxes')
        
        with open(file_path, 'r') as f:
            # Skip header
            header = next(f)
            print(f"Header: {header}")  # Debug
            
            for line_num, line in enumerate(f, 2):
                print(f"\nProcessing line {line_num}: {line.strip()}")  # Debug
                
                # Parse CSV line
                parts = [p.strip().strip('"$,') for p in line.strip().split(',')]
                if len(parts) < 10:  # Updated for new column count
                    print(f"Skipping line {line_num}: insufficient columns")
                    continue
                
                try:
                    source = parts[0]
                    date_str = parts[1]
                    total_boxes = int(parts[2])  # Boxes Purchased
                    business_boxes = int(parts[3])  # Business Boxes
                    stashed_boxes = int(parts[4])  # Stashed Boxes
                    price_per_box = float(parts[5].replace('$', '').replace(',', '').strip())
                    set_name = normalize_set_name(parts[7], sets_map)
                    packs_per_box = int(parts[8])
                    
                    print(f"Parsed values:")  # Debug
                    print(f"  Source: {source}")
                    print(f"  Date: {date_str}")
                    print(f"  Total Boxes: {total_boxes}")
                    print(f"  Business Boxes: {business_boxes}")
                    print(f"  Stashed Boxes: {stashed_boxes}")
                    print(f"  Price/Box: {price_per_box}")
                    print(f"  Set: {set_name}")
                    print(f"  Packs/Box: {packs_per_box}")
                    
                    # Verify total boxes matches sum of business and stashed
                    if total_boxes != (business_boxes + stashed_boxes):
                        print(f"Warning: Total boxes ({total_boxes}) doesn't match sum of business ({business_boxes}) and stashed ({stashed_boxes})")
                        continue
                    
                    # Verify set exists
                    set_exists = db.conn.execute('''
                        SELECT 1 FROM sets WHERE name = ?
                    ''', (set_name,)).fetchone()
                    
                    if not set_exists:
                        print(f"Set not found: {set_name}")  # Debug
                        if set_name not in unmatched_sets:
                            unmatched_sets.append(set_name)
                        continue
                    
                    # Update packs per box
                    with db.conn:
                        db.conn.execute('''
                            UPDATE sets 
                            SET packs_per_box = ?
                            WHERE name = ?
                        ''', (packs_per_box, set_name))
                        
                        # Insert business boxes
                        for _ in range(business_boxes):
                            db.conn.execute('''
                                INSERT INTO business_boxes (
                                    set_name, purchase_date, source, price,
                                    packs_opened, packs_sold
                                ) VALUES (?, ?, ?, ?, 0, 0)
                            ''', (
                                set_name,
                                datetime.strptime(date_str, '%Y-%m-%d').date(),
                                source,
                                price_per_box
                            ))
                        
                        # Insert stashed boxes
                        for _ in range(stashed_boxes):
                            db.conn.execute('''
                                INSERT INTO stashed_boxes (
                                    set_name, purchase_date, source, price
                                ) VALUES (?, ?, ?, ?)
                            ''', (
                                set_name,
                                datetime.strptime(date_str, '%Y-%m-%d').date(),
                                source,
                                price_per_box
                            ))
                    
                    # Track totals for verification
                    if set_name not in set_totals:
                        set_totals[set_name] = {
                            'business': 0,
                            'stashed': 0,
                            'total': 0,
                            'price': 0
                        }
                    set_totals[set_name]['business'] += business_boxes
                    set_totals[set_name]['stashed'] += stashed_boxes
                    set_totals[set_name]['total'] += total_boxes
                    set_totals[set_name]['price'] = price_per_box  # Keep most recent price
                    
                except ValueError as e:
                    print(f"Error processing line {line_num}: {str(e)}")  # Debug
                    continue
                except Exception as e:
                    print(f"Unexpected error on line {line_num}: {str(e)}")  # Debug
                    raise
        
        # Print final totals for verification
        print("\nFinal totals:")
        for set_name, totals in set_totals.items():
            print(f"{set_name}:")
            print(f"  Total boxes: {totals['total']}")
            print(f"  Business boxes: {totals['business']}")
            print(f"  Stashed boxes: {totals['stashed']}")
            print(f"  Price per box: ${totals['price']:.2f}")
        
        return True, unmatched_sets, duplicate_entries
        
    except Exception as e:
        print(f"Error importing booster purchases: {str(e)}")  # Debug
        raise