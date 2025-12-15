"""
Vercel serverless function entry point for Flask app.
This file wraps the Flask app for Vercel's serverless environment.
Note: Backend folder is the repo root, so app is directly accessible.
"""
# Import Flask app directly (no backend/ prefix needed)
from app.main import app

# Export app directly for Vercel
# Vercel automatically detects Flask apps when exported as 'app'
handler = app

