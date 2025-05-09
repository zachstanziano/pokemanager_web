# Pokemon TCG Business Operations & Implementation

## Current Implementation

### 1. Data Sources and Processing
```plaintext
[Input Files]                    [Processors]                 [Storage]
eBayListingsSalesReport.csv     → analyze_sales.py    → data/sales_analysis.csv
submission_MMDDYYYY.csv         → psa_processor.py    → data/psa/{cert_number}/
                                                        ├── details.json
                                                        ├── {cert}_front.jpg
                                                        └── {cert}_back.jpg
BoosterBoxPurchases.csv         → data_processors.py  → data/booster_purchases.json
```

### 2. Database Structure
```sql
-- Core tables for inventory tracking
CREATE TABLE sets (
    name TEXT PRIMARY KEY,
    release_date DATE,
    series TEXT,
    total_cards INTEGER,
    box_msrp REAL,
    packs_per_box INTEGER,
    cards_per_pack INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE key_cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    set_name TEXT,
    card_number TEXT,
    card_name TEXT,
    estimated_psa10 REAL,
    submission_count INTEGER,
    high_grade_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (set_name) REFERENCES sets(name)
);

CREATE TABLE cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    set_name TEXT,
    purchase_date DATE,
    source TEXT,
    boxes_per_case INTEGER,
    price_per_case REAL,
    quantity INTEGER,
    is_sealed BOOLEAN DEFAULT 1,
    notes TEXT,
    source_order_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (set_name) REFERENCES sets(name)
);

CREATE TABLE boxes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    set_name TEXT,
    purchase_date DATE,
    source TEXT,
    price REAL,
    is_sealed BOOLEAN DEFAULT 1,
    case_id INTEGER,
    notes TEXT,
    source_order_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (set_name) REFERENCES sets(name),
    FOREIGN KEY (case_id) REFERENCES cases(id)
);

CREATE TABLE packs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    set_name TEXT,
    box_id INTEGER,
    sale_date DATE,
    sale_price REAL,
    shipping_charged REAL,
    shipping_cost REAL,
    platform TEXT,
    is_sealed BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (set_name) REFERENCES sets(name),
    FOREIGN KEY (box_id) REFERENCES boxes(id)
);

CREATE TABLE slabs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    set_name TEXT,
    card_number TEXT,
    card_name TEXT,
    grade INTEGER,
    cert_number TEXT UNIQUE,
    submission_date DATE,
    return_date DATE,
    sale_date DATE,
    sale_price REAL,
    grading_cost REAL,
    shipping_charged REAL,
    shipping_cost REAL,
    platform TEXT,
    notes TEXT,
    image_folder TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (set_name) REFERENCES sets(name)
);

CREATE TABLE folder_contents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slab_id INTEGER,
    file_name TEXT,
    file_type TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (slab_id) REFERENCES slabs(id)
);
```

### 3. API Limitations and Handling
- PSA API:
  * 100 calls per day limit
  * Each cert requires 2 calls (details + images)
  * Reset at midnight UTC
  * Tracking implemented in psa_api_tracker.py
  * Queue system for processing large submissions

### 4. File Management
```plaintext
pokemanager_web/
├── data/
│   ├── imported/           # Timestamped copies of imported files
│   ├── inventory.db        # SQLite database
│   ├── psa/               # PSA-related data
│   │   ├── images/        # Certificate images by cert number
│   │   ├── api_calls.json # API call tracking
│   │   └── debug.log      # Processing log
│   └── oauthtoken         # PSA API OAuth token
├── static/                # Static web assets
└── templates/            # Web interface templates
```

### 5. Web Interface Features
- Dashboard:
  * Set performance metrics
  * Inventory status
  * Recent sales tracking
- Import Management:
  * File upload interface
  * Import status tracking
  * Error reporting
- PSA Processing:
  * API call monitoring
  * Manual rescan capability
  * Queue management
  * Processing status display

## Implementation Plan

1. **Phase 1: Data Management** ✓
   - SQLite database implementation
   - File import processing
   - Data validation and error handling

2. **Phase 2: PSA Integration** ✓
   - API call tracking
   - Image downloading
   - Queue management
   - Duplicate checking

3. **Phase 3: Web Interface** (In Progress)
   - Basic dashboard
   - Import management
   - PSA processing controls
   - Set analytics port from TUI

4. **Phase 4: Automation**
   - Automatic PSA queue processing
   - Daily status reports
   - Error notifications
   - Backup management

5. **Phase 5: Analytics**
   - Enhanced set performance metrics
   - Price trend analysis
   - Inventory optimization
   - Sales forecasting

## Key Business Rules

1. **Data Integrity**
   - All imports are timestamped and archived
   - Validation before database updates
   - Duplicate detection for PSA certs

2. **PSA Processing**
   - Check for existing certs before API calls
   - Track partial and failed processing
   - Maintain detailed processing logs
   - Queue management for large submissions

3. **Inventory Management**
   - Track boxes at case and individual level
   - Monitor sealed vs opened status
   - Link sales to specific inventory items
   - Track shipping costs and profits

4. **Financial Tracking**
   - Separate revenue streams (packs vs slabs)
   - Include all associated costs
   - Track shipping profits/losses
   - Monitor set-level performance

This document serves as the primary reference for business logic and implementation details. It should be updated as new features are added or existing ones are modified.