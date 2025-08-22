"""同期サービスの日付フィルタリング機能のテスト"""

import pytest
from datetime import datetime, timedelta, date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from api.database import Base, get_db
from api.main import app
from api.models.sync_log import SyncLog
from api.services.sync_service import SyncService

# テスト用データベース設定
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_sync_filtering.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def setup_database():
    """テスト用データベースのセットアップ"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    """各テスト用のデータベースセッション"""
    session = TestingSessionLocal()
    yield session
    # テストごとにデータをクリア
    session.query(SyncLog).delete()
    session.commit()
    session.close()

@pytest.fixture
def client():
    """テスト用HTTPクライアント"""
    return TestClient(app)

@pytest.fixture
def sync_service():
    """同期サービスのインスタンス"""
    return SyncService()

def create_test_sync_logs(db_session, count=10):
    """テスト用同期ログを作成"""
    sync_logs = []
    base_date = datetime.utcnow()
    
    for i in range(count):
        # 過去60日間に分散させる
        days_ago = i * 6
        started_at = base_date - timedelta(days=days_ago)
        completed_at = started_at + timedelta(minutes=30)
        
        # ステータスをローテーション
        if i % 3 == 0:
            status = "completed"
        elif i % 3 == 1:
            status = "failed"
        else:
            status = "processing"
        
        sync_log = SyncLog(
            sync_type="manual",
            file_name=f"test_{i}.csv",
            file_path=f"/data/csv/test_{i}.csv",
            status=status,
            total_rows=100 + i * 10,
            processed_rows=90 + i * 8 if status == "completed" else 0,
            new_reservations=5 + i if status == "completed" else 0,
            updated_reservations=10 + i * 2 if status == "completed" else 0,
            error_rows=i if status == "failed" else 0,
            started_at=started_at,
            completed_at=completed_at if status != "processing" else None
        )
        db_session.add(sync_log)
        sync_logs.append(sync_log)
    
    db_session.commit()
    return sync_logs

def test_get_sync_statistics_with_days_filter(setup_database, db_session, sync_service):
    """日数フィルタを使った統計取得のテスト"""
    # テストデータ作成
    create_test_sync_logs(db_session, 10)
    
    # 30日間の統計を取得
    stats_30 = sync_service.get_sync_statistics(db_session, days=30)
    
    assert stats_30["period_days"] == 30
    assert stats_30["total_syncs"] >= 5  # 30日以内のログ
    assert "period_start" in stats_30
    assert "period_end" in stats_30
    assert "daily_breakdown" in stats_30
    assert "latest_sync" in stats_30
    
    # 7日間の統計を取得
    stats_7 = sync_service.get_sync_statistics(db_session, days=7)
    
    assert stats_7["period_days"] == 7
    assert stats_7["total_syncs"] <= stats_30["total_syncs"]
    assert stats_7["total_syncs"] >= 1  # 7日以内のログ

def test_get_sync_logs_by_date_range(setup_database, db_session, sync_service):
    """日付範囲によるログ取得のテスト"""
    # テストデータ作成
    create_test_sync_logs(db_session, 10)
    
    # 過去14日間のログを取得
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=14)
    
    logs = sync_service.get_sync_logs_by_date_range(
        db_session,
        start_date=start_date,
        end_date=end_date
    )
    
    assert len(logs) >= 2  # 14日以内のログ
    
    # 各ログの日付が範囲内であることを確認
    for log in logs:
        if log["started_at"]:
            log_date = datetime.fromisoformat(log["started_at"])
            assert start_date <= log_date <= end_date

def test_get_sync_logs_with_status_filter(setup_database, db_session, sync_service):
    """ステータスフィルタによるログ取得のテスト"""
    # テストデータ作成
    create_test_sync_logs(db_session, 10)
    
    # 成功したログのみ取得
    completed_logs = sync_service.get_sync_logs_by_date_range(
        db_session,
        status="completed"
    )
    
    for log in completed_logs:
        assert log["status"] == "completed"
    
    # 失敗したログのみ取得
    failed_logs = sync_service.get_sync_logs_by_date_range(
        db_session,
        status="failed"
    )
    
    for log in failed_logs:
        assert log["status"] == "failed"

def test_get_sync_summary_by_month(setup_database, db_session, sync_service):
    """月別サマリー取得のテスト"""
    # 現在の年月でテストデータ作成
    now = datetime.utcnow()
    year = now.year
    month = now.month
    
    # 今月のデータを作成
    for i in range(5):
        sync_log = SyncLog(
            sync_type="auto",
            file_name=f"monthly_test_{i}.csv",
            status="completed" if i % 2 == 0 else "failed",
            total_rows=100,
            processed_rows=90 if i % 2 == 0 else 0,
            new_reservations=10 if i % 2 == 0 else 0,
            updated_reservations=20 if i % 2 == 0 else 0,
            started_at=datetime(year, month, i + 1, 10, 0, 0),
            completed_at=datetime(year, month, i + 1, 10, 30, 0)
        )
        db_session.add(sync_log)
    
    db_session.commit()
    
    # 月別サマリーを取得
    summary = sync_service.get_sync_summary_by_month(db_session, year, month)
    
    assert summary["year"] == year
    assert summary["month"] == month
    assert summary["total_syncs"] == 5
    assert summary["successful_syncs"] == 3
    assert summary["failed_syncs"] == 2
    assert summary["success_rate"] == 60.0
    assert "weekly_breakdown" in summary

def test_daily_breakdown_calculation(setup_database, db_session, sync_service):
    """日別統計計算のテスト"""
    # 3日分のデータを作成
    base_date = datetime.utcnow()
    for day_offset in range(3):
        for i in range(2):
            sync_log = SyncLog(
                sync_type="manual",
                file_name=f"daily_{day_offset}_{i}.csv",
                status="completed",
                total_rows=100,
                processed_rows=90,
                new_reservations=5,
                updated_reservations=10,
                started_at=base_date - timedelta(days=day_offset),
                completed_at=base_date - timedelta(days=day_offset, hours=-1)
            )
            db_session.add(sync_log)
    
    db_session.commit()
    
    # 統計を取得
    stats = sync_service.get_sync_statistics(db_session, days=7)
    
    assert "daily_breakdown" in stats
    daily_breakdown = stats["daily_breakdown"]
    
    # 3日分のデータがあることを確認
    assert len(daily_breakdown) == 3
    
    # 各日のデータを確認
    for daily_stat in daily_breakdown:
        assert daily_stat["total_syncs"] == 2
        assert daily_stat["successful_syncs"] == 2
        assert daily_stat["processed_rows"] == 180

def test_api_endpoint_statistics(setup_database, db_session, client):
    """統計APIエンドポイントのテスト"""
    # テストデータ作成
    create_test_sync_logs(db_session, 5)
    
    # APIを呼び出し
    response = client.get("/api/sync/statistics?days=30")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["period_days"] == 30
    assert "total_syncs" in data
    assert "success_rate" in data
    assert "daily_breakdown" in data

def test_api_endpoint_logs(setup_database, db_session, client):
    """ログ取得APIエンドポイントのテスト"""
    # テストデータ作成
    create_test_sync_logs(db_session, 5)
    
    # APIを呼び出し（日付範囲指定）
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=10)
    
    response = client.get(
        f"/api/sync/logs?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}&limit=10"
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "logs" in data
    assert "count" in data
    assert data["count"] >= 1

def test_api_endpoint_monthly_summary(setup_database, db_session, client):
    """月別サマリーAPIエンドポイントのテスト"""
    # 現在の年月でテストデータ作成
    now = datetime.utcnow()
    year = now.year
    month = now.month
    
    sync_log = SyncLog(
        sync_type="auto",
        file_name="api_test.csv",
        status="completed",
        total_rows=100,
        processed_rows=90,
        started_at=datetime(year, month, 15, 10, 0, 0),
        completed_at=datetime(year, month, 15, 10, 30, 0)
    )
    db_session.add(sync_log)
    db_session.commit()
    
    # APIを呼び出し
    response = client.get(f"/api/sync/monthly-summary/{year}/{month}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["year"] == year
    assert data["month"] == month
    assert data["total_syncs"] >= 1
    assert "weekly_breakdown" in data

if __name__ == "__main__":
    pytest.main([__file__, "-v"])