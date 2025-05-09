"""
Initialize the inventory database with schema and test data.
This script should be run once to set up the initial database structure.
"""

import os
import json
from datetime import datetime
from pprint import pprint
import sys

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.inventory_db import InventoryDB
from database.sets_database import import_sets_database

def main():
    # Initialize the database
    print("Initializing database...")
    db = InventoryDB()
    
    # Create tables
    print("\nCreating database schema...")
    with db.conn:
        # Sets table
        db.conn.execute('''
        CREATE TABLE IF NOT EXISTS sets (
            name TEXT PRIMARY KEY,
            code TEXT,
            series TEXT,
            packs_per_box INTEGER DEFAULT 30
        )''')
        
        # Business boxes table
        db.conn.execute('''
        CREATE TABLE IF NOT EXISTS business_boxes (
            id INTEGER PRIMARY KEY,
            set_name TEXT NOT NULL,
            purchase_date DATE NOT NULL,
            source TEXT NOT NULL,
            price DECIMAL NOT NULL,
            packs_opened INTEGER DEFAULT 0,
            packs_sold INTEGER DEFAULT 0,
            FOREIGN KEY (set_name) REFERENCES sets(name)
        )''')
        
        # Stashed boxes table
        db.conn.execute('''
        CREATE TABLE IF NOT EXISTS stashed_boxes (
            id INTEGER PRIMARY KEY,
            set_name TEXT NOT NULL,
            purchase_date DATE NOT NULL,
            source TEXT NOT NULL,
            price DECIMAL NOT NULL,
            FOREIGN KEY (set_name) REFERENCES sets(name)
        )''')
        
        # Pack sales table
        db.conn.execute('''
        CREATE TABLE IF NOT EXISTS pack_sales (
            id INTEGER PRIMARY KEY,
            set_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            sale_price DECIMAL NOT NULL,
            shipping_charged DECIMAL NOT NULL,
            shipping_cost DECIMAL NOT NULL,
            ebay_fees DECIMAL NOT NULL,
            sale_date DATE NOT NULL,
            FOREIGN KEY (set_name) REFERENCES sets(name)
        )''')
        
        # Slabs table
        db.conn.execute('''
        CREATE TABLE IF NOT EXISTS slabs (
            id INTEGER PRIMARY KEY,
            cert_number TEXT UNIQUE NOT NULL,
            set_name TEXT NOT NULL,
            card_number TEXT NOT NULL,
            card_name TEXT NOT NULL,
            grade INTEGER NOT NULL,
            submission_date DATE NOT NULL,
            return_date DATE,
            status TEXT CHECK(status IN ('Submitted', 'Ready', 'Listed', 'Sold', 'Stashed')),
            
            -- PSA API Data
            psa_details_fetched BOOLEAN DEFAULT FALSE,
            psa_pop_higher INTEGER,
            psa_total_pop INTEGER,
            psa_label_type TEXT,
            
            -- Image Status
            front_image_path TEXT,
            back_image_path TEXT,
            
            -- Sales Info (when sold)
            sale_price DECIMAL,
            shipping_charged DECIMAL,
            shipping_cost DECIMAL,
            ebay_fees DECIMAL,
            sale_date DATE,
            
            FOREIGN KEY (set_name) REFERENCES sets(name)
        )''')
        
        # PSA API usage tracking
        db.conn.execute('''
        CREATE TABLE IF NOT EXISTS psa_api_usage (
            id INTEGER PRIMARY KEY,
            date DATE UNIQUE NOT NULL,
            calls_made INTEGER DEFAULT 0
        )''')
    
    # Import sets database
    print("\nImporting sets database...")
    from database.sets_database import import_sets_database
    if import_sets_database(db, 'data/sets_database.json'):
        print("Successfully imported sets database")
    else:
        print("Failed to import sets database")
    
    # Done
    print("\nDatabase initialization complete!")
    db.close()

if __name__ == "__main__":
    main()