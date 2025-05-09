"""
Configuration management for Pokemon TCG Inventory System
"""

import os
import json
from datetime import datetime
from typing import Dict, Any

class Config:
    """Configuration management class"""
    
    DEFAULT_CONFIG = {
        "data_dir": "data",
        "import_dir": "data/imported",
        "api_log_file": "data/psa_api_calls.json",
        "external_paths": {
            "psa_submissions": "",  # Path to PSA submission CSV files
            "psa_downloader": "",   # Path to PSA image downloader script
            "booster_data": ""      # Path to booster purchase data
        },
        "psa_api": {
            "daily_limit": 100,
            "reset_hour": 0  # Midnight UTC
        }
    }
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.config = self._load_config()
        self._ensure_directories()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                # Merge with defaults to ensure all keys exist
                return {**self.DEFAULT_CONFIG, **config}
        else:
            # Save default config
            self.save_config(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG
    
    def save_config(self, config: Dict[str, Any]):
        """Save configuration to file"""
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)
        self.config = config
    
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        for dir_path in [self.data_dir, self.import_dir]:
            os.makedirs(dir_path, exist_ok=True)
    
    @property
    def data_dir(self) -> str:
        """Get absolute path to data directory"""
        return os.path.join(self.base_dir, self.config["data_dir"])
    
    @property
    def import_dir(self) -> str:
        """Get absolute path to import directory"""
        return os.path.join(self.base_dir, self.config["import_dir"])
    
    @property
    def api_log_file(self) -> str:
        """Get absolute path to API log file"""
        return os.path.join(self.base_dir, self.config["api_log_file"])
    
    def get_external_path(self, key: str) -> str:
        """Get configured external path"""
        return self.config["external_paths"].get(key, "")
    
    def set_external_path(self, key: str, path: str):
        """Set external path in configuration"""
        self.config["external_paths"][key] = path
        self.save_config(self.config)
    
    def get_import_path(self, filename: str) -> str:
        """Generate timestamped path for imported file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base, ext = os.path.splitext(filename)
        return os.path.join(self.import_dir, f"{base}_{timestamp}{ext}")