"""
Import handler for eBay sales data
"""

from datetime import datetime
from database.inventory_db import InventoryDB

def import_ebay_sales(db: InventoryDB, file_path: str) -> bool:
    """
    Import eBay sales data from CSV
    
    Expected format:
    set_name,quantity,sale_price,shipping_charged,shipping_cost,ebay_fees,date
    Pokemon Japanese SV9-Battle Partners,2,15.99,4.99,3.50,2.50,2025-04-18
    
    Returns:
    - success: bool
    """
    try:
        with open(file_path, 'r') as f:
            # Skip header
            next(f)
            
            for line in f:
                # Parse CSV line
                parts = line.strip().split(',')
                if len(parts) < 7:
                    continue
                
                set_name, quantity, sale_price, shipping_charged, shipping_cost, fees, date_str = parts[:7]
                try:
                    # Parse date
                    sale_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    
                    # Insert sale
                    with db.conn:
                        db.conn.execute('''
                            INSERT INTO pack_sales (
                                set_name, quantity, sale_price, shipping_charged,
                                shipping_cost, ebay_fees, sale_date
                            ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            set_name, quantity, sale_price, shipping_charged,
                            shipping_cost, fees, sale_date
                        ))
                        
                except ValueError:
                    print(f"Error parsing date: {date_str}")
                    continue
        
        return True
        
    except Exception as e:
        print(f"Error importing eBay sales: {str(e)}")
        return False