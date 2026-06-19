import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# Vercel expects the app object to be named 'app'
# This is the entry point for Vercel serverless functions
