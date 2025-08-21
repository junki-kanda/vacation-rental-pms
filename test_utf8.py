#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test UTF-8 group creation"""

import requests
import json
import sys
import io

# Set UTF-8 for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

url = "http://localhost:8000/api/staff-groups"
data = {
    "name": "テストグループ",
    "description": "日本語のテスト",
    "rate_per_property": 8000,
    "rate_per_property_with_option": 9000,
    "transportation_fee": 0,
    "max_properties_per_day": 1,
    "can_handle_large_properties": True,
    "can_handle_multiple_properties": True,
    "is_active": True,
    "member_ids": []
}

headers = {
    "Content-Type": "application/json; charset=utf-8",
    "Accept": "application/json"
}

try:
    response = requests.post(url, json=data, headers=headers)
    print(f"Status Code: {response.status_code}")
    
    # Check if response encoding is properly set
    print(f"Response encoding: {response.encoding}")
    response.encoding = 'utf-8'
    
    print(f"Response text: {response.text}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Created group name: {result['name']}")
        print(f"Description: {result.get('description', '')}")
        
        # Let's also check the raw bytes
        print(f"Name bytes: {result['name'].encode('utf-8')}")
except Exception as e:
    print(f"Error: {e}")