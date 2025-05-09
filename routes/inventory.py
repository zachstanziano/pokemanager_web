from flask import Blueprint, render_template, request, jsonify
from database.inventory_db import InventoryDB
from config.config import Config
from psa.psa_processor import PSAProcessor
import os
import re

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/')
def inventory():
    """Show inventory page"""
    db = InventoryDB()
    show_all = request.args.get('show_all', '0') == '1'
    
    try:
        # Get detailed set and inventory information
        base_query = '''
            WITH box_stats AS (
                SELECT 
                    set_name,
                    COUNT(*) as total_boxes,
                    SUM(packs_opened) as total_packs_opened,
                    SUM(packs_sold) as total_packs_sold,
                    AVG(price) as avg_price
                FROM business_boxes
                GROUP BY set_name
            ),
            stash_stats AS (
                SELECT 
                    set_name,
                    COUNT(*) as total_boxes
                FROM stashed_boxes
                GROUP BY set_name
            ),
            pack_sales_stats AS (
                SELECT
                    set_name,
                    COUNT(DISTINCT id) as sale_count,
                    SUM(quantity) as packs_sold,
                    SUM(sale_price) as revenue,
                    SUM(shipping_charged - shipping_cost) as net_shipping,
                    SUM(ebay_fees) as fees
                FROM pack_sales
                GROUP BY set_name
            ),
            slab_stats AS (
                SELECT
                    set_name,
                    COUNT(*) as total_slabs,
                    SUM(CASE WHEN status = 'Ready' THEN 1 ELSE 0 END) as ready_slabs,
                    SUM(CASE WHEN status = 'Listed' THEN 1 ELSE 0 END) as listed_slabs,
                    SUM(CASE WHEN status = 'Sold' THEN 1 ELSE 0 END) as sold_slabs
                FROM slabs
                GROUP BY set_name
            )
            SELECT 
                s.*,
                -- Business inventory
                COALESCE(b.total_boxes, 0) as business_boxes,
                COALESCE(b.avg_price, 0) as avg_price_per_box,
                COALESCE(b.total_packs_opened, 0) as total_packs_opened,
                COALESCE(b.total_packs_sold, 0) as total_packs_sold,
                -- Stashed inventory
                COALESCE(st.total_boxes, 0) as stashed_boxes,
                -- Pack sales data
                COALESCE(ps.sale_count, 0) as pack_sale_count,
                COALESCE(ps.packs_sold, 0) as total_packs_sold_verified,
                COALESCE(ps.revenue, 0) as pack_sales_revenue,
                COALESCE(ps.net_shipping, 0) as pack_net_shipping,
                COALESCE(ps.fees, 0) as pack_fees,
                -- Slab data
                COALESCE(ss.total_slabs, 0) as total_slabs,
                COALESCE(ss.ready_slabs, 0) as ready_slabs,
                COALESCE(ss.listed_slabs, 0) as listed_slabs,
                COALESCE(ss.sold_slabs, 0) as sold_slabs,
                -- Calculate total packs from business boxes only
                COALESCE(b.total_boxes, 0) * s.packs_per_box as total_packs
            FROM sets s
            LEFT JOIN box_stats b ON b.set_name = s.name
            LEFT JOIN stash_stats st ON st.set_name = s.name
            LEFT JOIN pack_sales_stats ps ON ps.set_name = s.name
            LEFT JOIN slab_stats ss ON ss.set_name = s.name
        '''
        
        if not show_all:
            base_query += '''
            WHERE b.total_boxes > 0 OR st.total_boxes > 0
            '''
            
        base_query += ' ORDER BY s.series DESC, s.code DESC'
        
        sets = db.conn.execute(base_query).fetchall()
        
        # Check if there's any box data
        has_box_data = db.conn.execute('''
            SELECT EXISTS(
                SELECT 1 FROM business_boxes 
                UNION ALL 
                SELECT 1 FROM stashed_boxes
            ) as has_data
        ''').fetchone()['has_data']
        
        # Group sets by series and sort by numeric portion of code
        series_sets = {}
        for set_row in sets:
            series = set_row['series']
            if series not in series_sets:
                series_sets[series] = []
            
            # Convert row to dict and ensure numeric values are not None
            set_dict = dict(set_row)
            numeric_fields = [
                'pack_sales_revenue', 'pack_net_shipping', 'pack_fees',
                'business_boxes', 'stashed_boxes',
                'total_packs_opened', 'total_packs_sold',
                'pack_sale_count', 'total_packs_sold_verified',
                'avg_price_per_box', 'total_slabs',
                'ready_slabs', 'listed_slabs', 'sold_slabs'
            ]
            
            for field in numeric_fields:
                set_dict[field] = set_dict.get(field, 0) or 0
            
            # Calculate total packs
            set_dict['total_packs'] = set_dict['business_boxes'] * set_dict['packs_per_box']
                
            series_sets[series].append(set_dict)
        
        # Sort each series by the numeric portion of the code
        for series in series_sets:
            series_sets[series].sort(key=lambda x: extract_number(x['code']), reverse=True)
        
        # Get PSA processing status
        try:
            processor = PSAProcessor(Config())
            psa_status = {
                "calls_remaining": processor.api_tracker.get_calls_remaining(),
                "pending_slabs": db.conn.execute('''
                    SELECT COUNT(*) as count
                    FROM slabs 
                    WHERE NOT psa_details_fetched 
                       OR front_image_path IS NULL 
                       OR back_image_path IS NULL
                ''').fetchone()['count']
            }
        except ValueError:
            # PSA features not configured
            psa_status = {
                "calls_remaining": 0,
                "pending_slabs": 0,
                "not_configured": True
            }
        
        return render_template(
            'inventory.html',
            series_sets=series_sets,
            has_box_data=has_box_data,
            show_all=show_all,
            psa_status=psa_status
        )
    finally:
        db.close()

def extract_number(code):
    """Extract the numeric portion of a set code for sorting"""
    match = re.search(r'\d+', code or '')
    return int(match.group()) if match else 0

@inventory_bp.route('/reset', methods=['POST'])
def reset_inventory():
    """Reset all inventory data"""
    db = InventoryDB()
    
    try:
        with db.conn:
            # Clear all business inventory
            db.conn.execute('DELETE FROM business_boxes')
            # Clear all stashed inventory
            db.conn.execute('DELETE FROM stashed_boxes')
            # Clear all sales
            db.conn.execute('DELETE FROM pack_sales')
            # Clear all slabs
            db.conn.execute('DELETE FROM slabs')
            
        return jsonify({'message': 'Inventory reset successful'}), 200
    except Exception as e:
        return jsonify({'error': f'Failed to reset inventory: {str(e)}'}), 500
    finally:
        db.close()

@inventory_bp.route('/psa-status')
def psa_status():
    """Show PSA processing status and controls"""
    db = InventoryDB()
    processor = PSAProcessor(Config())
    
    try:
        # Get slabs needing API data
        pending_slabs = db.conn.execute('''
            SELECT cert_number, set_name, card_name, grade, psa_details_fetched,
                   front_image_path, back_image_path
            FROM slabs 
            WHERE NOT psa_details_fetched 
               OR front_image_path IS NULL 
               OR back_image_path IS NULL
            ORDER BY submission_date ASC
        ''').fetchall()
        
        # Get processed slabs
        processed_slabs = db.conn.execute('''
            SELECT cert_number, set_name, card_name, grade, status
            FROM slabs 
            WHERE psa_details_fetched 
              AND front_image_path IS NOT NULL 
              AND back_image_path IS NOT NULL
              AND status = 'Submitted'
            ORDER BY submission_date ASC
        ''').fetchall()
        
        # Get API calls remaining
        calls_remaining = processor.api_tracker.get_calls_remaining()
        
        # Get today's processed certs
        processed_today = processor.api_tracker.get_processed_certs()
        
        return render_template(
            'psa_status.html',
            pending_slabs=pending_slabs,
            processed_slabs=processed_slabs,
            calls_remaining=calls_remaining,
            processed_today=processed_today
        )
    finally:
        db.close()

@inventory_bp.route('/update-slabs', methods=['POST'])
def update_slabs():
    """Update inventory with processed slab data"""
    db = InventoryDB()
    
    try:
        # Get processed slabs that need inventory update
        with db.conn:
            # Update slabs to Ready status
            cursor = db.conn.execute('''
                UPDATE slabs 
                SET status = 'Ready'
                WHERE psa_details_fetched 
                  AND front_image_path IS NOT NULL 
                  AND back_image_path IS NOT NULL
                  AND status = 'Submitted'
            ''')
            updated_count = cursor.rowcount
            
        return jsonify({
            'updated': updated_count
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@inventory_bp.route('/process-psa', methods=['POST'])
def process_psa():
    """Process pending PSA slabs up to API limit"""
    db = InventoryDB()
    processor = PSAProcessor(Config())
    
    try:
        # Get slabs that need processing
        pending_slabs = db.conn.execute('''
            SELECT cert_number, set_name, card_name, grade
            FROM slabs 
            WHERE NOT psa_details_fetched 
               OR front_image_path IS NULL 
               OR back_image_path IS NULL
            ORDER BY submission_date ASC
            LIMIT ?
        ''', (processor.api_tracker.get_calls_remaining() // 2,)).fetchall()
        
        results = {
            "processed": 0,
            "failed": 0,
            "remaining_calls": processor.api_tracker.get_calls_remaining()
        }
        
        for slab in pending_slabs:
            success, _ = processor.process_cert(slab['cert_number'])
            if success:
                results["processed"] += 1
            else:
                results["failed"] += 1
        
        return jsonify(results), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@inventory_bp.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and import"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
        
    file_type = request.form.get('type')
    if not file_type:
        return jsonify({'error': 'File type not specified'}), 400
        
    # Save uploaded file
    file_path = os.path.join('data/uploads', file.filename)
    os.makedirs('data/uploads', exist_ok=True)
    file.save(file_path)
    
    # Process file based on type
    db = InventoryDB()
    success = False
    error_msg = None
    unmatched = []
    duplicates = []
    
    try:
        if file_type == 'purchases':
            success, unmatched, duplicates = db.import_booster_purchases(file_path)
            if not success:
                error_msg = "Failed to import booster purchases"
        elif file_type == 'sales':
            success = db.import_ebay_sales(file_path)
            if not success:
                error_msg = "Failed to import eBay sales"
        elif file_type == 'psa':
            success = db.import_psa_submissions(file_path)
            if not success:
                error_msg = "Failed to import PSA submissions"
    except Exception as e:
        error_msg = str(e)
        success = False
    finally:
        db.close()
        
    if success:
        response = {'message': 'File imported successfully'}
        warnings = []
        
        if unmatched:
            warnings.append({
                'type': 'unmatched_sets',
                'message': 'Some sets could not be matched in the database:',
                'items': unmatched
            })
            
        if duplicates:
            warnings.append({
                'type': 'duplicate_purchases',
                'message': 'Some purchases were skipped as they appear to be duplicates:',
                'items': duplicates
            })
            
        if warnings:
            response['warnings'] = warnings
            
        return jsonify(response), 200
    else:
        return jsonify({'error': error_msg or 'Import failed'}), 500