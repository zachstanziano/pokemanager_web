"""
Initialize the inventory database with set information
"""

import os
import json
from datetime import datetime

def initialize_inventory():
    """Initialize the inventory database with set information"""
    
    # Load sets data
    with open('data/pokemon_sets.json', 'r') as f:
        sets_data = json.load(f)
    
    # Create initial inventory structure
    inventory = {
        "metadata": {
            "last_updated": datetime.now().isoformat(),
            "version": "1.0",
            "initialized_from": "pokemon_sets.json"
        },
        "opened": {
            "sets": {}
        },
        "stashed": {
            "sets": {}
        },
        "sequential_sets": {
            "pokemon": {},
            "set_based": {}
        }
    }
    
    # Initialize empty structures for each set
    for series in sets_data["series"].values():
        # Process main sets
        for set_info in series.get("main_sets", []):
            set_name = set_info["name"]
            # Initialize opened structure
            inventory["opened"]["sets"][set_name] = {
                "boxes": {
                    "purchased": 0,
                    "processed": 0,
                    "packs_per_box": 30,  # Default, can be updated later
                    "boxes": []
                },
                "packs": {
                    "total": 0,
                    "ripped": 0,
                    "sold": 0
                },
                "slabs": {
                    "total": 0,
                    "status": {
                        "imported": 0,
                        "ready_to_list": 0,
                        "listed": 0,
                        "stashed": 0
                    },
                    "items": []
                }
            }
            
            # Initialize stashed structure
            inventory["stashed"]["sets"][set_name] = {
                "boxes_per_case": 6,  # Default, can be updated later
                "packs_per_box": 30,  # Default, can be updated later
                "cases": {
                    "total": 0,
                    "items": []
                },
                "loose_boxes": {
                    "total": 0,
                    "items": []
                },
                "total_boxes_stashed": 0
            }
        
        # Process special sets
        for set_info in series.get("special_sets", []):
            set_name = set_info["name"]
            # Initialize same structures for special sets
            inventory["opened"]["sets"][set_name] = {
                "boxes": {
                    "purchased": 0,
                    "processed": 0,
                    "packs_per_box": 30,
                    "boxes": []
                },
                "packs": {
                    "total": 0,
                    "ripped": 0,
                    "sold": 0
                },
                "slabs": {
                    "total": 0,
                    "status": {
                        "imported": 0,
                        "ready_to_list": 0,
                        "listed": 0,
                        "stashed": 0
                    },
                    "items": []
                }
            }
            
            inventory["stashed"]["sets"][set_name] = {
                "boxes_per_case": 6,
                "packs_per_box": 30,
                "cases": {
                    "total": 0,
                    "items": []
                },
                "loose_boxes": {
                    "total": 0,
                    "items": []
                },
                "total_boxes_stashed": 0
            }
    
    # Save the initialized inventory
    with open('data/inventory.json', 'w') as f:
        json.dump(inventory, f, indent=2)
    
    print(f"Initialized inventory with {len(inventory['opened']['sets'])} sets")

if __name__ == '__main__':
    initialize_inventory()