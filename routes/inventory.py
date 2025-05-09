"""
Inventory management routes
"""

import os
from flask import Blueprint, render_template, request, jsonify
from database.inventory_manager import InventoryManager

inventory_bp = Blueprint('inventory', __name__)
manager = InventoryManager(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data'))

@inventory_bp.route('/')
def index():
    """Display inventory overview"""
    opened_sets = manager.inventory["opened"]["sets"]
    stashed_sets = manager.inventory["stashed"]["sets"]
    
    # Calculate totals
    opened_totals = {
        "boxes": sum(s["boxes"]["purchased"] for s in opened_sets.values()),
        "packs": sum(s["packs"]["total"] for s in opened_sets.values()),
        "slabs": sum(s["slabs"]["total"] for s in opened_sets.values() if "slabs" in s)
    }
    
    stashed_totals = {
        "cases": sum(s["cases"]["total"] for s in stashed_sets.values()),
        "boxes": sum(s["total_boxes_stashed"] for s in stashed_sets.values())
    }
    
    return render_template('inventory.html',
                         opened_sets=opened_sets,
                         stashed_sets=stashed_sets,
                         opened_totals=opened_totals,
                         stashed_totals=stashed_totals)

@inventory_bp.route('/api/box/add', methods=['POST'])
def add_box():
    """Add a new box to inventory"""
    data = request.json
    try:
        box_id = manager.add_box(
            set_name=data['set_name'],
            purchase_date=data['purchase_date'],
            source=data['source'],
            price=float(data['price']),
            is_stashed=data.get('is_stashed', False),
            case_id=data.get('case_id')
        )
        return jsonify({"success": True, "box_id": box_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@inventory_bp.route('/api/case/add', methods=['POST'])
def add_case():
    """Add a new case to inventory"""
    data = request.json
    try:
        case_id = manager.add_case(
            set_name=data['set_name'],
            purchase_date=data['purchase_date'],
            source=data['source'],
            price_per_box=float(data['price_per_box'])
        )
        return jsonify({"success": True, "case_id": case_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@inventory_bp.route('/api/slab/add', methods=['POST'])
def add_slab():
    """Add a new slab to inventory"""
    data = request.json
    try:
        manager.add_slab(
            cert_number=data['cert_number'],
            set_name=data['set_name'],
            status=data.get('status', 'imported'),
            cert_details=data.get('cert_details')
        )
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@inventory_bp.route('/api/slab/status', methods=['PUT'])
def update_slab_status():
    """Update slab status"""
    data = request.json
    try:
        success = manager.update_slab_status(
            cert_number=data['cert_number'],
            new_status=data['status']
        )
        return jsonify({"success": success})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@inventory_bp.route('/api/sequential/add', methods=['POST'])
def add_sequential():
    """Add a sequential set"""
    data = request.json
    try:
        manager.add_sequential_set(
            type_=data['type'],
            identifier=data['identifier'],
            cert_numbers=data['cert_numbers']
        )
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})