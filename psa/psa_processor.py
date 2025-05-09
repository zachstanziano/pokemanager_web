"""
PSA data processing and image downloading with database integration
"""

import os
import csv
import json
import time
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from config.config import Config
from psa.psa_api_tracker import PSAApiTracker
from database.inventory_db import InventoryDB

class PSAProcessor:
    """Handle PSA data processing and image downloading"""
    
    def __init__(self, config: Config):
        self.config = config
        self.api_tracker = PSAApiTracker(config)
        self.db = InventoryDB()  # Database connection
        self._load_oauth_token()
        
        # Ensure required directories exist
        self.psa_data_dir = os.path.join(config.data_dir, 'psa')
        self.image_dir = os.path.join(self.psa_data_dir, 'images')
        os.makedirs(self.psa_data_dir, exist_ok=True)
        os.makedirs(self.image_dir, exist_ok=True)
        
        # API configuration
        self.api_headers = {
            'Authorization': f'Bearer {self.oauth_token}',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json'
        }
    
    def _load_oauth_token(self):
        """Load OAuth token from config or file"""
        # Try to get from config first
        self.oauth_token = self.config.config.get("psa_api", {}).get("oauth_token")
        
        if not self.oauth_token:
            # Check for token file
            token_file = os.path.join(self.config.data_dir, 'oauthtoken')
            if os.path.exists(token_file):
                with open(token_file, 'r') as f:
                    self.oauth_token = f.read().strip()
            else:
                raise ValueError("No OAuth token found in config or token file")
    
    def _log_debug(self, message: str):
        """Log debug message with timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        log_file = os.path.join(self.psa_data_dir, 'debug.log')
        with open(log_file, 'a') as f:
            f.write(f"[{timestamp}] {message}\n")
    
    def is_cert_complete(self, cert_number: str) -> bool:
        """Check if a certificate has been fully processed"""
        # First check database for the slab
        slab = self.db.get_slab_by_cert(cert_number)
        if not slab:
            return False
            
        # Then verify the image files exist
        cert_dir = os.path.join(self.image_dir, cert_number)
        if os.path.exists(cert_dir):
            has_front = os.path.exists(os.path.join(cert_dir, f'{cert_number}_front.jpg'))
            has_back = os.path.exists(os.path.join(cert_dir, f'{cert_number}_back.jpg'))
            return has_front and has_back
        
        return False
    
    def get_cert_details(self, cert_number: str) -> Optional[Dict]:
        """Get certificate details from PSA API"""
        url = f'https://api.psacard.com/publicapi/cert/GetByCertNumber/{cert_number}'
        self._log_debug(f"Requesting cert details for {cert_number}")
        
        try:
            response = requests.get(url, headers=self.api_headers, timeout=10)
            if response.status_code == 200:
                self.api_tracker.record_api_call(cert_number)
                return response.json()
            else:
                self._log_debug(f"Error {response.status_code}: {response.text}")
                return None
        except Exception as e:
            self._log_debug(f"Error getting cert details: {str(e)}")
            return None
    
    def get_cert_images(self, cert_number: str) -> Optional[Dict]:
        """Get certificate images from PSA API"""
        url = f'https://api.psacard.com/publicapi/cert/GetImagesByCertNumber/{cert_number}'
        self._log_debug(f"Requesting images for {cert_number}")
        
        try:
            response = requests.get(url, headers=self.api_headers, timeout=10)
            if response.status_code == 200:
                self.api_tracker.record_api_call(cert_number)
                return response.json()
            else:
                self._log_debug(f"Error {response.status_code}: {response.text}")
                return None
        except Exception as e:
            self._log_debug(f"Error getting cert images: {str(e)}")
            return None
    
    def download_image(self, url: str, save_path: str) -> bool:
        """Download image from URL"""
        self._log_debug(f"Downloading image from {url}")
        
        headers = {
            'User-Agent': self.api_headers['User-Agent'],
            'Referer': 'https://www.psacard.com/'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200 and len(response.content) > 1000:
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                return True
            return False
        except Exception as e:
            self._log_debug(f"Error downloading image: {str(e)}")
            return False
    
    def process_cert(self, cert_number: str) -> Tuple[bool, Optional[Dict]]:
        """Process a single certificate"""
        self._log_debug(f"Processing certificate {cert_number}")
        
        # Check if already processed
        if self.is_cert_complete(cert_number):
            self._log_debug(f"Certificate {cert_number} already completely processed")
            slab = self.db.get_slab_by_cert(cert_number)
            return True, slab
        
        # Create cert directory
        cert_dir = os.path.join(self.image_dir, cert_number)
        os.makedirs(cert_dir, exist_ok=True)
        
        # Get and save details
        details = self.get_cert_details(cert_number)
        if details:
            # Save to database
            self.db.save_slab_details(details, cert_dir)
        
        # Get and save images
        images = self.get_cert_images(cert_number)
        success = False
        if images:
            success = True
            for image in images:
                if image.get('ImageURL'):
                    suffix = 'front' if image.get('IsFrontImage') else 'back'
                    image_path = os.path.join(cert_dir, f'{cert_number}_{suffix}.jpg')
                    if not self.download_image(image.get('ImageURL'), image_path):
                        success = False
        
        return success and bool(details), details
    
    def process_submission_file(self, file_path: str) -> Dict:
        """Process a PSA submission file"""
        self._log_debug(f"Processing submission file: {file_path}")
        
        results = {
            "processed": 0,
            "skipped": 0,
            "failed": 0,
            "already_complete": 0,
            "details": []
        }
        
        # Copy file to import directory with timestamp
        filename = os.path.basename(file_path)
        import_path = self.config.get_import_path(filename)
        os.makedirs(os.path.dirname(import_path), exist_ok=True)
        with open(file_path, 'r') as src, open(import_path, 'w') as dst:
            dst.write(src.read())
        
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cert_number = row.get('PSA SUBMISSION NUMBER', '').strip()
                if not cert_number:
                    results["skipped"] += 1
                    continue
                
                # Check if already processed
                if self.is_cert_complete(cert_number):
                    results["already_complete"] += 1
                    continue
                
                # Check API call limit
                if self.api_tracker.get_calls_remaining() < 2:
                    break
                
                success, details = self.process_cert(cert_number)
                if success:
                    results["processed"] += 1
                    results["details"].append({
                        "cert_number": cert_number,
                        "details": details
                    })
                else:
                    results["failed"] += 1
                
                time.sleep(1)  # Rate limiting
        
        return results
    
    def get_processing_stats(self) -> Dict:
        """Get current processing statistics"""
        return {
            "total_slabs": self.db.get_slab_count(),
            "complete_slabs": self.db.get_complete_slab_count(),
            "incomplete_slabs": self.db.get_incomplete_slab_count(),
            "api_calls_remaining": self.api_tracker.get_calls_remaining(),
            "pending_certs": self.db.get_pending_cert_numbers()
        }