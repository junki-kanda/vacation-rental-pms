"""API endpoint tests using FastAPI TestClient."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


@pytest.fixture(scope="module")
def sample_csv():
    """Create a temporary CSV file for testing."""
    csv_dir = Path("./data/csv")
    csv_dir.mkdir(parents=True, exist_ok=True)
    file = csv_dir / "sample.csv"
    file.write_text("id,name\n1,Alice\n")
    yield file.name
    if file.exists():
        file.unlink()


def test_list_csv_files(sample_csv):
    """CSVファイル一覧の取得をテスト"""
    response = client.get("/api/sync/list-csv")
    assert response.status_code == 200
    data = response.json()
    assert any(f["filename"] == sample_csv for f in data["files"])


def test_process_local(sample_csv):
    """CSVファイルの処理をテスト"""
    response = client.post("/api/sync/process-local", json={"filename": sample_csv})
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == sample_csv
    assert isinstance(data["sync_id"], int)


def test_sync_status(sample_csv):
    """同期ステータスの確認"""
    process_resp = client.post("/api/sync/process-local", json={"filename": sample_csv})
    sync_id = process_resp.json()["sync_id"]

    response = client.get(f"/api/sync/status/{sync_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sync_id
    assert data["file_name"] == sample_csv

