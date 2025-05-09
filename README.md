# Pokemon TCG Manager

A web-based inventory management system for Pokemon Trading Card Game products.

## Project Structure

```
pokemanager_web/
├── app.py                 # Main Flask application
├── config/               
│   ├── config.json       # Application configuration
│   └── config.py         # Configuration loader
├── data/                 
│   ├── inventory.json    # Main inventory database
│   ├── pokemon_sets.json # Sets reference data
│   └── psa_slab_info/   # PSA slab data and images
├── database/            
│   ├── inventory_manager.py  # Inventory management system
│   ├── booster_imports.py   # Booster box import handler
│   └── psa_imports.py       # PSA data import handler
├── psa/                 
│   ├── psa_api_tracker.py   # PSA API rate limiting
│   └── psa_processor.py     # PSA data processing
├── routes/              
│   └── inventory.py      # Web routes for inventory
├── static/              # Static assets
└── templates/           # HTML templates
    ├── base.html        # Base template
    ├── inventory.html   # Inventory management
    └── psa_status.html  # PSA grading status
```

## Features

- Inventory Management
  - Track booster boxes, packs, and cases
  - Monitor opened vs stashed inventory
  - Track PSA graded cards
  - Sequential set tracking

- PSA Integration
  - Automated PSA data retrieval
  - Image downloads
  - Population report tracking

- Data Import/Export
  - CSV import for purchases
  - eBay sales tracking
  - PSA submission tracking

## Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database:
```bash
python database/initialize_inventory.py
```

4. Run the application:
```bash
python app.py
```

## Configuration

The application uses JSON files for configuration and data storage:

- `config/config.json`: Application settings
- `data/pokemon_sets.json`: Pokemon TCG set definitions
- `data/inventory.json`: Main inventory database

## Data Management

### Inventory Structure

The inventory system uses a JSON-based structure:

1. Opened Inventory
   - Boxes (purchased/processed)
   - Packs (ripped/sold)
   - Slabs (imported/ready/listed/stashed)

2. Stashed Inventory
   - Cases
   - Loose boxes

3. Sequential Sets
   - Pokemon-based sequences
   - Set-based sequences

### PSA Integration

PSA data is managed through:
- Daily API quota tracking
- Automated image downloads
- Population report updates