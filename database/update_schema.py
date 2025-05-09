"""
Update database schema to add missing columns.
Run this script to update an existing database with new schema changes.
"""

from inventory_db import InventoryDB

def main():
    print("Updating database schema...")
    db = InventoryDB()
    
    try:
        with db.conn:
            # Check if ebay_fees column exists in pack_sales
            cursor = db.conn.execute("PRAGMA table_info(pack_sales)")
            columns = [row['name'] for row in cursor.fetchall()]
            
            if 'ebay_fees' not in columns:
                print("Adding ebay_fees column to pack_sales table...")
                db.conn.execute('''
                    ALTER TABLE pack_sales
                    ADD COLUMN ebay_fees DECIMAL NOT NULL DEFAULT 0
                ''')
                print("Successfully added ebay_fees column")
            else:
                print("ebay_fees column already exists")
                
        print("\nSchema update complete!")
        
    except Exception as e:
        print(f"Error updating schema: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    main()