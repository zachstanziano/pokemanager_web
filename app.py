"""
Main Flask application entry point
"""

import os
import sys

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, redirect
from routes.inventory import inventory_bp

app = Flask(__name__)

# Register blueprints
app.register_blueprint(inventory_bp, url_prefix='/inventory')

# Redirect root to inventory
@app.route('/')
def index():
    return redirect('/inventory')

if __name__ == '__main__':
    app.run(debug=True)