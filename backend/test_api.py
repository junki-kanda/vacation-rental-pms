"""APIのテストスクリプト"""

import requests
import json

API_URL = "http://localhost:8000"

def test_list_csv():
    """CSVファイル一覧の取得をテスト"""
    print("1. Testing CSV list endpoint...")
    response = requests.get(f"{API_URL}/api/sync/list-csv")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Files found: {len(data.get('files', []))}")
        for file in data.get('files', []):
            print(f"   - {file['filename']} ({file['size']} bytes)")
        return data.get('files', [])
    else:
        print(f"   Error: {response.text}")
        return []

def test_process_csv(filename):
    """CSVファイルの処理をテスト"""
    print(f"\n2. Testing process-local endpoint with {filename}...")
    
    headers = {'Content-Type': 'application/json'}
    payload = {"filename": filename}
    
    print(f"   Payload: {json.dumps(payload)}")
    response = requests.post(
        f"{API_URL}/api/sync/process-local",
        json=payload,
        headers=headers
    )
    
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Response: {json.dumps(data, indent=2)}")
        return data.get('sync_id')
    else:
        print(f"   Error: {response.text}")
        return None

def test_sync_status(sync_id):
    """同期ステータスの確認"""
    print(f"\n3. Testing sync status for ID {sync_id}...")
    response = requests.get(f"{API_URL}/api/sync/status/{sync_id}")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Sync Status: {data.get('status')}")
        print(f"   Total Rows: {data.get('total_rows')}")
        print(f"   Processed: {data.get('processed_rows')}")
    else:
        print(f"   Error: {response.text}")

if __name__ == "__main__":
    print("=" * 50)
    print("Testing Vacation Rental PMS API")
    print("=" * 50)
    
    # CSVファイル一覧を取得
    files = test_list_csv()
    
    # ファイルがあれば最初のファイルを処理
    if files:
        first_file = files[0]['filename']
        sync_id = test_process_csv(first_file)
        
        if sync_id:
            import time
            time.sleep(2)  # 処理待ち
            test_sync_status(sync_id)
    else:
        print("\nNo CSV files found. Please run the crawler first.")
    
    print("\n" + "=" * 50)
    print("Test completed")