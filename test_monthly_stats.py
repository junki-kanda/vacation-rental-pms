#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test monthly stats API"""

import requests
from datetime import datetime
import sys
import io

# Set UTF-8 for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

url = "http://localhost:8000/api/cleaning/dashboard/staff-monthly-stats"
current_date = datetime.now()

params = {
    "year": current_date.year,
    "month": current_date.month
}

try:
    response = requests.get(url, params=params)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data)} staff records for {current_date.year}/{current_date.month}")
        
        for staff in data[:3]:  # Show first 3 records
            print(f"  - {staff['staff_name']}: {staff['working_days']}日出勤, {staff['total_tasks']}棟担当")
    else:
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")