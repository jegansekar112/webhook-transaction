#!/usr/bin/env python3
"""
Entry point for running the Flask application.
This script ensures proper Python path setup before importing the app.
"""
import sys
import os
from app.main import app

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)


if __name__ == "__main__":
    # Run Flask server
    app.run(debug=True, host="0.0.0.0", port=8000)

