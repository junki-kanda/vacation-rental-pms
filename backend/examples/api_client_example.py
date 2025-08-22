"""
Vacation Rental PMS API クライアントサンプル
"""

import requests
import json
from datetime import datetime, date
from typing import Optional, List, Dict, Any

class VacationRentalPMSClient:
    """
    Vacation Rental PMS APIクライアント
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
    
    # ========== 予約管理 ==========
    
    def get_reservations(
        self,
        skip: int = 0,
        limit: int = 100,
        ota_name: Optional[str] = None,
        facility_id: Optional[int] = None,
        check_in_date_from: Optional[str] = None,
        check_in_date_to: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """予約一覧を取得"""
        params = {
            "skip": skip,
            "limit": limit
        }
        if ota_name:
            params["ota_name"] = ota_name
        if facility_id:
            params["facility_id"] = facility_id
        if check_in_date_from:
            params["check_in_date_from"] = check_in_date_from
        if check_in_date_to:
            params["check_in_date_to"] = check_in_date_to
        
        response = self.session.get(f"{self.base_url}/api/reservations", params=params)
        response.raise_for_status()
        return response.json()
    
    def create_reservation(self, reservation_data: Dict[str, Any]) -> Dict[str, Any]:
        """新規予約を作成"""
        response = self.session.post(
            f"{self.base_url}/api/reservations",
            json=reservation_data
        )
        response.raise_for_status()
        return response.json()
    
    # ========== 施設管理 ==========
    
    def get_facilities(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """施設一覧を取得"""
        params = {"skip": skip, "limit": limit}
        response = self.session.get(f"{self.base_url}/api/properties", params=params)
        response.raise_for_status()
        return response.json()
    
    def get_facility(self, facility_id: int) -> Dict[str, Any]:
        """施設詳細を取得"""
        response = self.session.get(f"{self.base_url}/api/properties/{facility_id}")
        response.raise_for_status()
        return response.json()
    
    # ========== 清掃管理 ==========
    
    def get_cleaning_staff(self, is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
        """清掃スタッフ一覧を取得"""
        params = {}
        if is_active is not None:
            params["is_active"] = is_active
        
        response = self.session.get(f"{self.base_url}/api/cleaning/staff", params=params)
        response.raise_for_status()
        return response.json()
    
    def create_cleaning_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """清掃タスクを作成"""
        response = self.session.post(
            f"{self.base_url}/api/cleaning/tasks",
            json=task_data
        )
        response.raise_for_status()
        return response.json()
    
    def auto_assign_tasks(self, date_str: str) -> Dict[str, Any]:
        """清掃タスクを自動割当"""
        response = self.session.post(
            f"{self.base_url}/api/cleaning/tasks/auto-assign",
            json={"date": date_str}
        )
        response.raise_for_status()
        return response.json()
    
    # ========== ダッシュボード ==========
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """ダッシュボード統計を取得"""
        response = self.session.get(f"{self.base_url}/api/dashboard/stats")
        response.raise_for_status()
        return response.json()
    
    def get_monthly_stats(self, year: int, month: int) -> Dict[str, Any]:
        """月間統計を取得"""
        params = {"year": year, "month": month}
        response = self.session.get(f"{self.base_url}/api/dashboard/monthly-stats", params=params)
        response.raise_for_status()
        return response.json()
    
    # ========== データ同期 ==========
    
    def upload_csv(self, file_path: str) -> Dict[str, Any]:
        """CSVファイルをアップロード"""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = self.session.post(
                f"{self.base_url}/api/sync/upload",
                files=files
            )
        response.raise_for_status()
        return response.json()
    
    def get_sync_status(self, sync_id: int) -> Dict[str, Any]:
        """同期状態を取得"""
        response = self.session.get(f"{self.base_url}/api/sync/status/{sync_id}")
        response.raise_for_status()
        return response.json()


def main():
    """
    使用例
    """
    # クライアントの初期化
    client = VacationRentalPMSClient()
    
    try:
        # 1. ダッシュボード統計の取得
        print("=== ダッシュボード統計 ===")
        stats = client.get_dashboard_stats()
        print(f"本日のチェックイン: {stats['today_checkins']}棟")
        print(f"本日のチェックアウト: {stats['today_checkouts']}棟")
        print(f"稼働率: {stats['occupancy_rate']}%")
        print()
        
        # 2. 施設一覧の取得
        print("=== 施設一覧 ===")
        facilities = client.get_facilities(limit=5)
        for facility in facilities:
            print(f"- {facility['name']} (ID: {facility['id']})")
        print()
        
        # 3. 予約一覧の取得（今月分）
        print("=== 今月の予約 ===")
        today = date.today()
        reservations = client.get_reservations(
            check_in_date_from=f"{today.year}-{today.month:02d}-01",
            check_in_date_to=f"{today.year}-{today.month:02d}-31"
        )
        for res in reservations[:5]:  # 最初の5件のみ表示
            print(f"- {res['guest_name']} ({res['check_in_date']} - {res['check_out_date']})")
        print()
        
        # 4. 清掃スタッフの取得
        print("=== アクティブな清掃スタッフ ===")
        staff_list = client.get_cleaning_staff(is_active=True)
        for staff in staff_list[:5]:  # 最初の5件のみ表示
            print(f"- {staff['name']} (ID: {staff['id']})")
        print()
        
        # 5. 清掃タスクの自動割当（例）
        # print("=== 清掃タスクの自動割当 ===")
        # tomorrow = (date.today() + timedelta(days=1)).isoformat()
        # result = client.auto_assign_tasks(tomorrow)
        # print(f"割当成功: {result['assigned_count']}件")
        # print(f"割当失敗: {result['failed_count']}件")
        
    except requests.exceptions.RequestException as e:
        print(f"APIエラー: {e}")
    except Exception as e:
        print(f"エラー: {e}")


if __name__ == "__main__":
    main()