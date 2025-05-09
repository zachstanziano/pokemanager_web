"""
Inventory management system for Pokemon TCG products
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Union

class InventoryManager:
    def __init__(self, data_dir: str):
        """Initialize the inventory manager"""
        self.data_dir = data_dir
        self.inventory_path = os.path.join(data_dir, 'inventory.json')
        self.sets_path = os.path.join(data_dir, 'pokemon_sets.json')
        self.inventory = self._load_inventory()
        self.sets_data = self._load_sets_data()

    def _load_inventory(self) -> dict:
        """Load or create inventory file"""
        if os.path.exists(self.inventory_path):
            with open(self.inventory_path, 'r') as f:
                return json.load(f)
        return {
            "metadata": {
                "last_updated": datetime.now().isoformat(),
                "version": "1.0"
            },
            "opened": {"sets": {}},
            "stashed": {"sets": {}},
            "sequential_sets": {
                "pokemon": {},
                "set_based": {}
            }
        }

    def _load_sets_data(self) -> dict:
        """Load Pokemon sets data"""
        with open(self.sets_path, 'r') as f:
            return json.load(f)

    def _save_inventory(self):
        """Save inventory to file"""
        self.inventory["metadata"]["last_updated"] = datetime.now().isoformat()
        with open(self.inventory_path, 'w') as f:
            json.dump(self.inventory, f, indent=2)

    def add_box(self, set_name: str, purchase_date: str, source: str, 
                price: float, is_stashed: bool = False, case_id: Optional[str] = None) -> str:
        """Add a new box to inventory"""
        # Verify set exists
        if not self._verify_set_exists(set_name):
            raise ValueError(f"Set {set_name} not found in sets database")

        # Generate box ID
        set_code = self._get_set_code(set_name)
        box_id = f"{set_code}-{self._generate_next_id(set_name, 'box')}"

        if is_stashed:
            if case_id:  # Part of a case
                self._add_to_case(set_name, box_id, case_id, purchase_date, source, price)
            else:  # Loose box
                self._add_loose_box(set_name, box_id, purchase_date, source, price)
        else:
            self._add_opened_box(set_name, box_id, purchase_date, source, price)

        self._save_inventory()
        return box_id

    def add_case(self, set_name: str, purchase_date: str, source: str, 
                 price_per_box: float) -> str:
        """Add a new sealed case to inventory"""
        if not self._verify_set_exists(set_name):
            raise ValueError(f"Set {set_name} not found in sets database")

        set_code = self._get_set_code(set_name)
        case_id = f"{set_code}-C{self._generate_next_id(set_name, 'case')}"

        if set_name not in self.inventory["stashed"]["sets"]:
            self.inventory["stashed"]["sets"][set_name] = {
                "boxes_per_case": self._get_boxes_per_case(set_name),
                "packs_per_box": self._get_packs_per_box(set_name),
                "cases": {"total": 0, "items": []},
                "loose_boxes": {"total": 0, "items": []},
                "total_boxes_stashed": 0
            }

        self.inventory["stashed"]["sets"][set_name]["cases"]["items"].append({
            "id": case_id,
            "purchase_date": purchase_date,
            "source": source,
            "price_per_box": price_per_box
        })
        self.inventory["stashed"]["sets"][set_name]["cases"]["total"] += 1
        self.inventory["stashed"]["sets"][set_name]["total_boxes_stashed"] += self._get_boxes_per_case(set_name)

        self._save_inventory()
        return case_id

    def add_slab(self, cert_number: str, set_name: str, status: str = "imported",
                 cert_details: Optional[Dict] = None):
        """Add a graded card slab to inventory"""
        if status not in ["imported", "ready_to_list", "listed", "stashed"]:
            raise ValueError("Invalid slab status")

        if set_name not in self.inventory["opened"]["sets"]:
            self._initialize_set(set_name)

        set_data = self.inventory["opened"]["sets"][set_name]
        if "slabs" not in set_data:
            set_data["slabs"] = {
                "total": 0,
                "status": {status: 0 for status in ["imported", "ready_to_list", "listed", "stashed"]},
                "items": []
            }

        # Add slab
        set_data["slabs"]["items"].append({
            "cert_number": cert_number,
            "status": status,
            "details": cert_details
        })
        set_data["slabs"]["total"] += 1
        set_data["slabs"]["status"][status] += 1

        self._save_inventory()

    def update_slab_status(self, cert_number: str, new_status: str):
        """Update the status of a slab"""
        for set_data in self.inventory["opened"]["sets"].values():
            if "slabs" not in set_data:
                continue
            
            for slab in set_data["slabs"]["items"]:
                if slab["cert_number"] == cert_number:
                    old_status = slab["status"]
                    slab["status"] = new_status
                    set_data["slabs"]["status"][old_status] -= 1
                    set_data["slabs"]["status"][new_status] += 1
                    self._save_inventory()
                    return True
        return False

    def add_sequential_set(self, type_: str, identifier: str, cert_numbers: List[str]):
        """Add a sequential set of slabs"""
        if type_ not in ["pokemon", "set_based"]:
            raise ValueError("Invalid sequential set type")

        if type_ == "pokemon":
            if identifier not in self.inventory["sequential_sets"]["pokemon"]:
                self.inventory["sequential_sets"]["pokemon"][identifier] = {
                    "slabs": [],
                    "total": 0
                }
            target = self.inventory["sequential_sets"]["pokemon"][identifier]
        else:
            if identifier not in self.inventory["sequential_sets"]["set_based"]:
                self.inventory["sequential_sets"]["set_based"][identifier] = {
                    "sequences": [],
                    "total": 0
                }
            target = self.inventory["sequential_sets"]["set_based"][identifier]

        # Sort cert numbers
        cert_numbers.sort()
        
        if type_ == "pokemon":
            target["slabs"].extend(cert_numbers)
            target["total"] += len(cert_numbers)
        else:
            # Find sequential ranges
            current_sequence = {"start": cert_numbers[0], "end": cert_numbers[0], "count": 1}
            for cert in cert_numbers[1:]:
                if int(cert) == int(current_sequence["end"]) + 1:
                    current_sequence["end"] = cert
                    current_sequence["count"] += 1
                else:
                    target["sequences"].append(current_sequence)
                    current_sequence = {"start": cert, "end": cert, "count": 1}
            target["sequences"].append(current_sequence)
            target["total"] += len(cert_numbers)

        self._save_inventory()

    def _verify_set_exists(self, set_name: str) -> bool:
        """Verify a set exists in the sets database"""
        for series in self.sets_data["series"].values():
            for set_type in ["main_sets", "special_sets"]:
                if set_type in series:
                    if any(s["name"] == set_name for s in series[set_type]):
                        return True
        return False

    def _get_set_code(self, set_name: str) -> str:
        """Get the set code for a given set name"""
        for series in self.sets_data["series"].values():
            for set_type in ["main_sets", "special_sets"]:
                if set_type in series:
                    for set_info in series[set_type]:
                        if set_info["name"] == set_name:
                            return set_info["code"]
        return "UNK"

    def _get_boxes_per_case(self, set_name: str) -> int:
        """Get the number of boxes per case for a set"""
        # This could be added to the sets database
        return 6  # Default for most sets

    def _get_packs_per_box(self, set_name: str) -> int:
        """Get the number of packs per box for a set"""
        # This could be added to the sets database
        return 30  # Default for most sets

    def _generate_next_id(self, set_name: str, type_: str) -> int:
        """Generate the next available ID for a box or case"""
        if type_ == "box":
            existing = []
            if set_name in self.inventory["opened"]["sets"]:
                existing.extend(b["id"].split("-")[1] for b in self.inventory["opened"]["sets"][set_name]["boxes"]["boxes"])
            if set_name in self.inventory["stashed"]["sets"]:
                existing.extend(b["id"].split("-")[1] for b in self.inventory["stashed"]["sets"][set_name]["loose_boxes"]["items"])
        else:  # case
            if set_name not in self.inventory["stashed"]["sets"]:
                return 1
            existing = [c["id"].split("-C")[1] for c in self.inventory["stashed"]["sets"][set_name]["cases"]["items"]]
        
        if not existing:
            return 1
        return max(int(i) for i in existing) + 1

    def _initialize_set(self, set_name: str):
        """Initialize a new set in the opened inventory"""
        self.inventory["opened"]["sets"][set_name] = {
            "boxes": {
                "purchased": 0,
                "processed": 0,
                "packs_per_box": self._get_packs_per_box(set_name),
                "boxes": []
            },
            "packs": {
                "total": 0,
                "ripped": 0,
                "sold": 0
            }
        }

    def _add_opened_box(self, set_name: str, box_id: str, purchase_date: str, source: str, price: float):
        """Add a box to opened inventory"""
        if set_name not in self.inventory["opened"]["sets"]:
            self._initialize_set(set_name)

        self.inventory["opened"]["sets"][set_name]["boxes"]["boxes"].append({
            "id": box_id,
            "purchase_date": purchase_date,
            "source": source,
            "price": price,
            "total_packs": self._get_packs_per_box(set_name),
            "packs_ripped": 0,
            "packs_sold": 0
        })
        self.inventory["opened"]["sets"][set_name]["boxes"]["purchased"] += 1

    def _add_loose_box(self, set_name: str, box_id: str, purchase_date: str, source: str, price: float):
        """Add a loose box to stashed inventory"""
        if set_name not in self.inventory["stashed"]["sets"]:
            self.inventory["stashed"]["sets"][set_name] = {
                "boxes_per_case": self._get_boxes_per_case(set_name),
                "packs_per_box": self._get_packs_per_box(set_name),
                "cases": {"total": 0, "items": []},
                "loose_boxes": {"total": 0, "items": []},
                "total_boxes_stashed": 0
            }

        self.inventory["stashed"]["sets"][set_name]["loose_boxes"]["items"].append({
            "id": box_id,
            "purchase_date": purchase_date,
            "source": source,
            "price": price
        })
        self.inventory["stashed"]["sets"][set_name]["loose_boxes"]["total"] += 1
        self.inventory["stashed"]["sets"][set_name]["total_boxes_stashed"] += 1

    def _add_to_case(self, set_name: str, box_id: str, case_id: str, purchase_date: str, source: str, price: float):
        """Add a box to an existing case"""
        if set_name not in self.inventory["stashed"]["sets"]:
            raise ValueError(f"No cases found for set {set_name}")

        case = None
        for c in self.inventory["stashed"]["sets"][set_name]["cases"]["items"]:
            if c["id"] == case_id:
                case = c
                break

        if not case:
            raise ValueError(f"Case {case_id} not found")

        if "boxes" not in case:
            case["boxes"] = []

        if len(case["boxes"]) >= self._get_boxes_per_case(set_name):
            raise ValueError(f"Case {case_id} is already full")

        case["boxes"].append({
            "id": box_id,
            "purchase_date": purchase_date,
            "source": source,
            "price": price
        })