# Vacation Rental PMS API ドキュメント

## 概要

一棟貸の貸別荘に特化したPMS（Property Management System）のREST APIです。

## APIドキュメントへのアクセス

### Swagger UI
- URL: http://localhost:8000/api/docs
- インタラクティブなAPIドキュメント
- 直接APIをテスト実行可能

### ReDoc
- URL: http://localhost:8000/api/redoc
- より詳細で読みやすいAPIドキュメント

### OpenAPI JSON
- URL: http://localhost:8000/api/openapi.json
- OpenAPI仕様のJSONファイル
- Postman等のツールでインポート可能

## エンドポイント一覧

### 予約管理 (/api/reservations)
| メソッド | パス | 説明 |
|---------|------|------|
| GET | / | 予約一覧の取得 |
| GET | /{reservation_id} | 予約詳細の取得 |
| POST | / | 新規予約の作成 |
| PUT | /{reservation_id} | 予約情報の更新 |
| DELETE | /{reservation_id} | 予約の削除 |

### 施設管理 (/api/properties)
| メソッド | パス | 説明 |
|---------|------|------|
| GET | / | 施設一覧の取得 |
| GET | /{facility_id} | 施設詳細の取得 |
| POST | / | 新規施設の登録 |
| PUT | /{facility_id} | 施設情報の更新 |

### 清掃管理 (/api/cleaning)
| メソッド | パス | 説明 |
|---------|------|------|
| **スタッフ管理** |
| GET | /staff | スタッフ一覧の取得 |
| GET | /staff/{staff_id} | スタッフ詳細の取得 |
| POST | /staff | スタッフの登録 |
| PUT | /staff/{staff_id} | スタッフ情報の更新 |
| DELETE | /staff/{staff_id} | スタッフの削除 |
| **タスク管理** |
| GET | /tasks | 清掃タスク一覧の取得 |
| GET | /tasks/{task_id} | タスク詳細の取得 |
| POST | /tasks | タスクの作成 |
| PUT | /tasks/{task_id} | タスクの更新 |
| POST | /tasks/{task_id}/assign | タスクの割当 |
| POST | /tasks/{task_id}/status | ステータスの更新 |
| POST | /tasks/{task_id}/revision | 修正依頼 |
| **自動処理** |
| POST | /tasks/auto-create | タスクの自動生成 |
| POST | /tasks/auto-assign | タスクの自動割当 |
| **統計** |
| GET | /dashboard | 清掃ダッシュボード |
| GET | /staff/{staff_id}/performance | スタッフ実績 |
| GET | /staff/{staff_id}/monthly-stats | 月次統計 |

### ダッシュボード (/api/dashboard)
| メソッド | パス | 説明 |
|---------|------|------|
| GET | /stats | 統計情報の取得 |
| GET | /monthly-stats | 月間統計の取得 |
| GET | /monthly-comparison | 月間比較データ |
| GET | /daily-stats | 日別統計の取得 |
| GET | /ota-breakdown | OTA別内訳 |

### データ同期 (/api/sync)
| メソッド | パス | 説明 |
|---------|------|------|
| POST | /upload | CSVファイルのアップロード |
| POST | /process-local | ローカルファイルの処理 |
| GET | /files | アップロード済みファイル一覧 |
| GET | /logs | 同期ログの取得 |
| GET | /status/{sync_id} | 同期状態の確認 |

### スタッフグループ (/api/staff-groups)
| メソッド | パス | 説明 |
|---------|------|------|
| GET | / | グループ一覧の取得 |
| GET | /{group_id} | グループ詳細の取得 |
| POST | / | グループの作成 |
| PUT | /{group_id} | グループの更新 |
| DELETE | /{group_id} | グループの削除 |
| POST | /{group_id}/members | メンバーの追加 |
| DELETE | /{group_id}/members/{staff_id} | メンバーの削除 |

## 認証

現在のバージョンでは認証は実装されていません。本番環境では以下の認証方式の実装を推奨します：

- JWT Bearer Token
- OAuth 2.0
- API Key

## エラーハンドリング

### HTTPステータスコード

| コード | 説明 |
|--------|------|
| 200 | 成功 |
| 201 | 作成成功 |
| 204 | 削除成功 |
| 400 | リクエストエラー |
| 401 | 認証エラー |
| 403 | 権限エラー |
| 404 | リソースが見つからない |
| 409 | 競合エラー |
| 422 | バリデーションエラー |
| 500 | サーバーエラー |

### エラーレスポンス形式

```json
{
  "detail": "エラーメッセージ"
}
```

バリデーションエラーの場合：
```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## データ形式

### 日付形式
- 日付: `YYYY-MM-DD` (例: 2024-01-15)
- 日時: `YYYY-MM-DDTHH:MM:SS` (例: 2024-01-15T10:30:00)

### 文字エンコーディング
- UTF-8

### Content-Type
- Request: `application/json`
- Response: `application/json; charset=utf-8`

## ページネーション

リスト取得エンドポイントでは以下のクエリパラメータでページネーションが可能：

- `skip`: スキップする件数（デフォルト: 0）
- `limit`: 取得する最大件数（デフォルト: 100、最大: 1000）

例：
```
GET /api/reservations?skip=20&limit=10
```

## フィルタリング

多くのリスト取得エンドポイントでは、クエリパラメータによるフィルタリングが可能：

例（予約一覧）：
```
GET /api/reservations?ota_name=Booking.com&check_in_date_from=2024-01-01&check_in_date_to=2024-01-31
```

## ソート

ソート可能なエンドポイントでは以下のパラメータを使用：

- `sort_by`: ソートキー（例: check_in_date, created_at）
- `sort_order`: ソート順序（asc: 昇順, desc: 降順）

例：
```
GET /api/reservations?sort_by=check_in_date&sort_order=desc
```

## レート制限

現在のバージョンではレート制限は実装されていません。本番環境では以下の制限の実装を推奨：

- 1分あたり60リクエスト
- 1時間あたり1000リクエスト

## 開発環境

### 必要な環境変数

```env
# データベース
DATABASE_URL=postgresql://user:password@localhost/dbname

# API設定
API_HOST=0.0.0.0
API_PORT=8000

# CSVファイル保存先
CSV_DIR=./data/csv

# CORS設定（フロントエンドURL）
FRONTEND_URL=http://localhost:3000
```

### サーバー起動

```bash
# 開発サーバー
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# 本番サーバー
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## テスト

### APIテストの実行

```bash
# 全テスト実行
pytest

# 特定のテストファイルを実行
pytest tests/test_api_reservations.py

# カバレッジレポート
pytest --cov=api --cov-report=html
```

### Postmanコレクション

`/api/openapi.json`をPostmanにインポートすることで、全エンドポイントのテストが可能です。

## セキュリティ考慮事項

1. **HTTPS通信**: 本番環境では必ずHTTPSを使用
2. **認証・認可**: JWT等による適切な認証機構の実装
3. **入力検証**: すべての入力データのバリデーション
4. **SQLインジェクション対策**: ORMの使用とパラメータ化クエリ
5. **CORS設定**: 許可するオリジンの制限
6. **レート制限**: DDoS攻撃対策
7. **ログ記録**: アクセスログと監査ログの記録
8. **データ暗号化**: 機密情報の暗号化

## サポート

- Issue報告: https://github.com/your-org/vacation-rental-pms/issues
- ドキュメント: http://localhost:8000/api/docs
- 問い合わせ: support@example.com