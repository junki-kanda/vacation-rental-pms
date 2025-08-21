#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Simple runner for the backend server"""

import os
import sys
import io
from pathlib import Path

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Change to backend directory
os.chdir(backend_dir)

# Import and run the app
from api.main import app
import uvicorn

if __name__ == "__main__":
    print("Starting Vacation Rental PMS Backend...")
    print(f"Working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        reload=False
    )