"""
Import handler for PSA submissions
"""

import os
from database.inventory_db import InventoryDB

def import_psa_submissions(db: InventoryDB, file_path: str) -> bool:
    """
    Import PSA submissions from CSV file and create initial folders
    
    Expected format:
    YEAR,SET,CARD NUMBER,CARD NAME,-,GRADE,PSA SUBMISSION NUMBER
    2025,POKEMON JAPANESE SV9-BATTLE PARTNERS,123,BROCK'S SCOUTING SUPER RARE,-,PSA 10,110975567
    
    Returns:
    - success: bool
    """
    try:
        # Ensure PSA slab info directory exists
        psa_data_dir = os.path.join(os.path.dirname(db.db_path), 'psa_slab_info')
        os.makedirs(psa_data_dir, exist_ok=True)
        
        imported_count = 0
        with open(file_path, 'r') as f:
            # Skip header row
            next(f)
            
            # Process each row
            for line in f:
                # Split on comma and strip quotes
                parts = [p.strip().strip("'") for p in line.strip().split(',')]
                
                if len(parts) < 7:
                    continue
                    
                # Extract data
                year = parts[0]
                set_name = parts[1]
                card_number = parts[2]
                card_name = parts[3]
                grade = int(parts[5].replace('PSA ', ''))
                cert_number = parts[6]
                
                # Create slab directory
                slab_dir = os.path.join(psa_data_dir, cert_number)
                os.makedirs(slab_dir, exist_ok=True)
                
                # Insert into slabs table
                with db.conn:
                    # Check if slab already exists
                    existing = db.conn.execute('''
                        SELECT 1 FROM slabs WHERE cert_number = ?
                    ''', (cert_number,)).fetchone()
                    
                    if not existing:
                        db.conn.execute('''
                            INSERT INTO slabs (
                                cert_number,
                                set_name,
                                card_number,
                                card_name,
                                grade,
                                submission_date,
                                status,
                                psa_details_fetched
                            ) VALUES (?, ?, ?, ?, ?, date('now'), 'Submitted', 0)
                        ''', (
                            cert_number,
                            set_name,
                            card_number,
                            card_name,
                            grade
                        ))
                        imported_count += 1
        
        print(f"Imported {imported_count} new PSA submissions")
        return True
        
    except Exception as e:
        print(f"Error importing PSA submissions: {str(e)}")
        return False