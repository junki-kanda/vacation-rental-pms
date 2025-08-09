# ねっぱん予約同期スクリプト

## 概要
`neppan_reservation_sync.py` は、ねっぱんから予約データCSVを自動でダウンロードし、Google Driveにアップロードするスクリプトです。

## 機能
- ねっぱんへの自動ログイン
- 予約CSVファイルのダウンロード
- Google Driveへの自動アップロード（オプション）
- エラー時のスクリーンショット・HTML保存（デバッグ用）
- リトライ機能（ネットワークエラー対策）

## セットアップ

### 1. 環境変数の設定
`backend/.env` ファイルに以下の設定を追加：

```env
# ねっぱんログイン情報（必須）
NEPPAN_CODE=P01PI372
NEPPAN_USER=your_username
NEPPAN_PASS=your_password

# Google Drive設定（オプション）
DRIVE_FOLDER_ID=your_drive_folder_id
SA_FILE=C:\path\to\drive-sa.json

# クローラー設定
HEADLESS=true  # ブラウザを表示しない
TIMEOUT_SECONDS=90
MAX_RETRIES=5
```

### 2. Playwrightのインストール
```bash
# Playwrightブラウザのインストール
playwright install chromium
```

### 3. Google Drive連携の設定（オプション）
1. Google Cloud ConsoleでサービスアカウントKkeyを作成
2. `drive-sa.json` として保存
3. Google DriveフォルダをサービスアカウントEメールと共有

## 使用方法

### 基本的な実行
```bash
cd backend/scripts
python neppan_reservation_sync.py
```

### 定期実行（Windowsタスクスケジューラ）
1. `run_sync.bat` を作成：
```batch
@echo off
cd C:\Users\jkwrr\Documents\PMS\vacation-rental-pms\backend\scripts
python neppan_reservation_sync.py
```

2. タスクスケジューラで毎日実行に設定

### Dockerでの実行
```bash
cd vacation-rental-pms
docker-compose run --rm crawler python /app/scripts/neppan_reservation_sync.py
```

## ダウンロードしたCSVの場所
- ローカル: `backend/data/csv/` ディレクトリ
- Cloud Run: `/tmp/data/csv/`
- Google Drive: 設定したフォルダID

## トラブルシューティング

### ログインに失敗する場合
1. `HEADLESS=false` に設定して実際のブラウザ動作を確認
2. `backend/data/csv/debug/` のスクリーンショットを確認
3. ねっぱんのログイン情報を再確認

### CSVダウンロードに失敗する場合
1. タイムアウト値を増やす: `TIMEOUT_SECONDS=180`
2. ねっぱんのUIが変更されていないか確認
3. ネットワーク接続を確認

### Google Driveアップロードに失敗する場合
1. サービスアカウントの権限を確認
2. フォルダIDが正しいか確認
3. `drive-sa.json` のパスが正しいか確認

## ログファイル
スクリプトの実行ログはコンソールに出力されます。
ファイルに保存する場合：
```bash
python neppan_reservation_sync.py > sync.log 2>&1
```

## デバッグモード
詳細なデバッグ情報を見る場合：
```bash
# 環境変数で設定
HEADLESS=false TAKE_SCREENSHOT=true SAVE_HTML=true python neppan_reservation_sync.py
```

## APIとの連携
ダウンロードしたCSVファイルは自動的に `backend/data/csv/` に保存され、
FastAPI の `/api/sync/trigger` エンドポイントから処理できます。

```python
# APIから同期を実行
import requests

response = requests.post(
    "http://localhost:8000/api/sync/trigger",
    json={"file_path": "backend/data/csv/ReservationTotalList-20250807.csv"}
)
```

## 注意事項
- ねっぱんのUIが変更された場合、スクリプトの修正が必要
- 大量のデータをダウンロードする場合はタイムアウト値を調整
- 本番環境では適切なエラー通知を設定することを推奨