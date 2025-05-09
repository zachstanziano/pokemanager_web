# Pokemon TCG Manager Web

A web-based inventory management system for Pokemon Trading Card Game products.

## Features

- Track booster box inventory (business and personal collection)
- Import purchase data from CSV files
- Track PSA graded cards
- Monitor eBay sales
- Filter by series and show/hide empty sets

## Setup

1. Clone the repository:
```bash
git clone https://github.com/zachstanziano/poke-manager_web.git
cd poke-manager_web
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Initialize the database:
```bash
python app.py
```

4. Access the web interface:
Open http://localhost:5000 in your browser

## Data Import Format

### Booster Box Purchases
CSV format:
```
Source,Purchase Date,Boxes,Per Box USD,Total,Set,Packs Per Box,#of boxes stashed
Vendor,2025-02-07,2,$38.00,$76.00,Set Name,30,0
```

### PSA Submissions
CSV format (details to be added)

### eBay Sales
CSV format (details to be added)

## Configuration

Create a `config.json` file with your settings:
```json
{
    "psa_api_key": "your_api_key",
    "psa_cookie": "your_cookie"
}
```