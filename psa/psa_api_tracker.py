"""
PSA API call tracking and management
"""

import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional
from config.config import Config

class PSAApiTracker:
    """Track and manage PSA API calls"""
    
    def __init__(self, config: Config):
        self.config = config
        self.log_data = self._load_log()
    
    def _load_log(self) -> Dict:
        """Load existing log or create new one"""
        if os.path.exists(self.config.api_log_file):
            with open(self.config.api_log_file, 'r') as f:
                return json.load(f)
        return {
            "daily_logs": {},
            "last_reset": None
        }
    
    def _save_log(self):
        """Save current log data"""
        with open(self.config.api_log_file, 'w') as f:
            json.dump(self.log_data, f, indent=2)
    
    def _get_current_date(self) -> str:
        """Get current date in YYYY-MM-DD format"""
        return datetime.now(timezone.utc).strftime('%Y-%m-%d')
    
    def _check_reset(self):
        """Check if daily count should be reset"""
        current_date = self._get_current_date()
        if self.log_data["last_reset"] != current_date:
            self.log_data["last_reset"] = current_date
            self.log_data["daily_logs"][current_date] = {
                "calls": 0,
                "cert_numbers": []
            }
            self._save_log()
    
    def get_calls_remaining(self) -> int:
        """Get number of API calls remaining for today"""
        self._check_reset()
        current_date = self._get_current_date()
        daily_calls = self.log_data["daily_logs"].get(current_date, {}).get("calls", 0)
        return max(0, self.config.config["psa_api"]["daily_limit"] - daily_calls)
    
    def record_api_call(self, cert_number: str):
        """Record an API call for a specific cert number"""
        self._check_reset()
        current_date = self._get_current_date()
        
        if current_date not in self.log_data["daily_logs"]:
            self.log_data["daily_logs"][current_date] = {"calls": 0, "cert_numbers": []}
        
        self.log_data["daily_logs"][current_date]["calls"] += 1
        self.log_data["daily_logs"][current_date]["cert_numbers"].append(cert_number)
        self._save_log()
    
    def get_processed_certs(self) -> List[str]:
        """Get list of all processed cert numbers for today"""
        self._check_reset()
        current_date = self._get_current_date()
        return self.log_data["daily_logs"].get(current_date, {}).get("cert_numbers", [])