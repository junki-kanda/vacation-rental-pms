# ねっぱんCSVダウンロード機能

## 概要

ねっぱんから予約データCSVを自動的にダウンロードし、データベースに同期する機能です。

## セットアップ

### 1. 必要なパッケージのインストール

```bash
# Pythonパッケージのインストール
pip install -r backend/requirements.txt

# Playwrightのブラウザをインストール
playwright install chromium
```

### 2. 環境変数の設定

`.env`ファイルに以下の環境変数を設定してください：

```env
# ねっぱんログイン情報（必須）
NEPPAN_CODE=クライアントコード
NEPPAN_USER=ログインID
NEPPAN_PASS=パスワード

# CSVファイル保存先（オプション）
CSV_DIR=./backend/data/csv

# 自動同期設定（オプション）
AUTO_SYNC_ENABLED=true
AUTO_CLEANUP_ENABLED=true
CSV_RETENTION_DAYS=7

# スケジュール設定（オプション）
FETCH_CSV_SCHEDULE=06:00  # 毎日6時に実行
```

## 使用方法

### 手動実行

#### 基本的な実行（ダウンロード + DB同期 + クリーンアップ）
```bash
python backend/fetch_csv.py
```

#### CSVダウンロードのみ（DB同期なし）
```bash
python backend/fetch_csv.py --no-sync
```

#### デバッグモード（ブラウザを表示）
```bash
python backend/fetch_csv.py --debug
```

#### クリーンアップをスキップ
```bash
python backend/fetch_csv.py --no-cleanup
```

### 定期実行（スケジューラー）

#### スケジューラーの起動
```bash
python backend/scheduler.py
```

#### 一度だけ実行
```bash
python backend/scheduler.py --once
```

#### メール通知のテスト
```bash
python backend/scheduler.py --test-notification
```

### APIエンドポイント経由での実行

既存のAPIエンドポイントを使用してCSVファイルを処理することも可能です：

```python
import requests

# CSVファイルのアップロード
with open('path/to/csv', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/sync/upload',
        files={'file': f}
    )
    print(response.json())
```

## ディレクトリ構成

```
backend/
├── fetch_csv.py           # CSVダウンロードスクリプト
├── scheduler.py           # 定期実行スケジューラー
├── data/
│   └── csv/              # CSVファイル保存先
├── temp_downloads/        # 一時ダウンロードディレクトリ
└── logs/
    └── scheduler.log      # スケジューラーログ
```

## 機能詳細

### 1. CSVダウンロード機能
- Playwrightを使用してねっぱんにログイン
- 予約一覧画面からCSVをダウンロード
- ファイル名に日時を付けて保存

### 2. データベース同期機能
- ダウンロードしたCSVを自動的にデータベースに同期
- 既存のSyncServiceを使用
- 同期ログの記録

### 3. クリーンアップ機能
- 指定日数（デフォルト7日）より古いCSVファイルを自動削除
- ディスク容量の節約

### 4. スケジュール実行
- 毎日指定時刻に自動実行
- エラー時のメール通知（オプション）
- 実行ログの記録

## トラブルシューティング

### ログインに失敗する場合
1. 環境変数が正しく設定されているか確認
2. ねっぱんのログイン情報が正しいか確認
3. `--debug`モードで実行して画面を確認

### CSVダウンロードに失敗する場合
1. ねっぱんのUIが変更されていないか確認
2. ネットワーク接続を確認
3. タイムアウト設定を調整

### データベース同期に失敗する場合
1. データベース接続設定を確認
2. CSVファイルの形式が正しいか確認
3. ログファイルでエラー詳細を確認

## ログファイル

### スケジューラーログ
```
backend/logs/scheduler.log
```

### アプリケーションログ
コンソール出力またはAPIサーバーのログを確認

## セキュリティ注意事項

1. **環境変数の管理**
   - `.env`ファイルをGitにコミットしない
   - 本番環境では環境変数を適切に管理

2. **ログイン情報の保護**
   - ねっぱんのログイン情報は暗号化して保存することを推奨
   - アクセス権限を適切に設定

3. **CSVファイルの取り扱い**
   - 個人情報を含むため、適切なアクセス制御を実施
   - 定期的なクリーンアップで不要なファイルを削除

## 更新履歴

- 2024-01-XX: 初版作成
- Google Drive連携を削除し、ローカル保存に変更
- データベース自動同期機能を追加
- スケジューラー機能を追加