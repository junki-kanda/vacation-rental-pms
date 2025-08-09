# 貸別荘PMS（Property Management System）

## 🎯 プロジェクト概要

一棟貸の貸別荘に特化したPMSシステム。ねっぱんから各OTA（一休、楽天トラベル、Booking.com、Airbnb）の予約データを自動取得し、統合管理を実現します。

### ✨ 主要機能
- 📥 **自動データ取得**: ねっぱんから予約CSVを自動ダウンロード
- 🏨 **OTA統合管理**: 複数OTAの予約を一元管理
- 📊 **ダッシュボード**: リアルタイムで予約状況を可視化
- 📅 **カレンダービュー**: 施設別の予約状況を直感的に表示
- ☁️ **Google Drive連携**: 予約データの自動バックアップ

## 📁 プロジェクト構成

```
vacation-rental-pms/
├── backend/                    # FastAPI バックエンド
│   ├── api/                   # API関連ファイル
│   │   ├── routers/          # APIルーター
│   │   │   ├── reservations.py   # 予約管理API
│   │   │   ├── properties.py     # 施設管理API
│   │   │   ├── sync.py           # 同期管理API
│   │   │   └── dashboard.py      # ダッシュボードAPI
│   │   ├── models/           # データモデル
│   │   │   ├── reservation.py    # 予約データモデル
│   │   │   ├── property.py       # 施設データモデル
│   │   │   └── sync_log.py       # 同期ログモデル
│   │   ├── schemas/          # Pydanticスキーマ
│   │   │   ├── reservation.py    # 予約スキーマ
│   │   │   ├── property.py       # 施設スキーマ
│   │   │   ├── sync_log.py       # 同期ログスキーマ
│   │   │   └── dashboard.py      # ダッシュボードスキーマ
│   │   ├── services/         # ビジネスロジック
│   │   │   ├── parser.py         # CSVパーサー
│   │   │   ├── ota_detector.py   # OTA識別サービス
│   │   │   └── sync_service.py   # 同期サービス
│   │   ├── crud/             # データベース操作
│   │   │   ├── reservation.py    # 予約CRUD
│   │   │   ├── property.py       # 施設CRUD
│   │   │   ├── sync_log.py       # 同期ログCRUD
│   │   │   └── dashboard.py      # ダッシュボードCRUD
│   │   ├── database.py       # DB接続設定
│   │   └── main.py          # FastAPIメインアプリ
│   ├── scripts/              # スクリプト
│   │   └── neppan_reservation_sync.py  # ねっぱんクローラー
│   ├── data/                # データファイル
│   │   └── csv/            # CSVファイル格納
│   ├── tests/              # テストファイル
│   ├── .env.example        # 環境変数サンプル
│   ├── requirements.txt    # Python依存関係
│   ├── alembic.ini        # DBマイグレーション設定
│   └── Dockerfile         # Dockerイメージ設定
├── frontend/               # Next.js フロントエンド
│   ├── app/               # アプリケーション
│   │   ├── dashboard/     # ダッシュボード
│   │   ├── reservations/  # 予約管理
│   │   ├── properties/    # 施設管理
│   │   └── sync/         # 同期管理
│   ├── components/        # UIコンポーネント
│   │   ├── ui/           # 基本UIコンポーネント
│   │   └── features/     # 機能別コンポーネント
│   ├── lib/              # ユーティリティ
│   │   ├── api.ts       # API通信
│   │   └── utils.ts     # ヘルパー関数
│   ├── package.json
│   ├── tsconfig.json
│   └── Dockerfile       # Dockerイメージ設定
├── docker-compose.yml     # Docker設定
├── PROJECT_SETUP.md      # 設計仕様書
└── README.md            # このファイル
```

## 🛠 技術スタック

### Backend
- **言語**: Python 3.11+
- **フレームワーク**: FastAPI
- **ORM**: SQLAlchemy
- **DB**: PostgreSQL
- **タスクキュー**: Celery + Redis
- **クローリング**: Playwright
- **データ処理**: Pandas

### Frontend
- **フレームワーク**: Next.js 15 (App Router)
- **言語**: TypeScript
- **スタイリング**: Tailwind CSS
- **状態管理**: React Query
- **データ可視化**: Recharts

### インフラ
- **コンテナ化**: Docker, Docker Compose
- **データベース**: PostgreSQL 15
- **キャッシュ**: Redis 7

## 🚀 セットアップ手順

### 1. プロジェクトクローン

```bash
cd C:\Users\jkwrr\Documents\PMS
cd vacation-rental-pms
```

### 2. 環境変数設定

```bash
# バックエンド環境変数
cp backend/.env.example backend/.env

# Google Drive連携を使用する場合（オプション）
# drive-sa.json をbackendディレクトリに配置
```

**backend/.env** を編集して必要な値を設定:

```env
# データベース
DATABASE_URL=postgresql://pmsuser:pmspassword@localhost:5432/vacation_rental_pms

# Redis
REDIS_URL=redis://localhost:6379

# API設定
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000

# ねっぱんクローラー設定（同期機能に必要）
NEPPAN_CODE=your_neppan_code
NEPPAN_USER=your_neppan_user  
NEPPAN_PASS=your_neppan_password

# Google Drive設定（オプション）
DRIVE_FOLDER_ID=your_drive_folder_id
SA_FILE=./path/to/service-account-key.json
```

### 3. Docker Composeで起動

```bash
# 全サービス起動
docker-compose up -d

# ログ確認
docker-compose logs -f
```

### 4. データベース初期化

```bash
# マイグレーション実行
docker-compose exec backend alembic upgrade head
```

### 5. アクセス確認

- **フロントエンド**: http://localhost:3000
- **バックエンドAPI**: http://localhost:8000
- **API ドキュメント**: http://localhost:8000/docs

## 🔧 開発モード

### バックエンド開発

```bash
cd backend

# 仮想環境作成（Windows）
python -m venv venv
venv\Scripts\activate

# 依存関係インストール
pip install -r requirements.txt

# Playwrightブラウザのインストール（ねっぱんクローラー用）
playwright install chromium

# 開発サーバー起動
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### フロントエンド開発

```bash
cd frontend

# 依存関係インストール
npm install

# 開発サーバー起動
npm run dev
```

## 📊 主要機能

### 🔄 予約データ同期
- ねっぱんからのCSV自動取得
- 複数OTAの予約データ統合
- リアルタイム同期ステータス監視

#### ねっぱんクローラーの実行
```bash
# 手動実行
run-sync.bat

# または直接スクリプト実行
cd backend/scripts
python neppan_reservation_sync.py
```

**自動実行設定（Windowsタスクスケジューラ）**:
1. `run-sync.bat` をタスクスケジューラに登録
2. 毎日指定時刻に自動実行

### 📅 予約管理
- 予約一覧表示・検索・フィルタリング
- 予約詳細表示・編集
- カレンダー表示

### 🏠 施設管理
- 施設情報管理
- 部屋タイプ別管理
- 稼働率分析

### 📈 ダッシュボード
- 本日のチェックイン・チェックアウト
- 稼働率表示
- 最近の予約表示
- 同期ステータス表示

## 🔍 API エンドポイント

### 予約管理
- `GET /api/reservations` - 予約一覧取得
- `GET /api/reservations/{id}` - 予約詳細取得  
- `POST /api/reservations` - 予約作成
- `PUT /api/reservations/{id}` - 予約更新

### 施設管理
- `GET /api/properties` - 施設一覧取得
- `GET /api/properties/{id}` - 施設詳細取得
- `POST /api/properties` - 施設作成

### 同期管理
- `POST /api/sync/upload` - CSVアップロード
- `POST /api/sync/trigger` - 同期実行
- `GET /api/sync/status/{id}` - 同期ステータス取得

### ダッシュボード
- `GET /api/dashboard/stats` - 統計情報取得
- `GET /api/dashboard/calendar/reservations` - カレンダー用予約取得

## 🧪 テスト実行

```bash
# バックエンドテスト
cd backend
pytest

# フロントエンドテスト
cd frontend  
npm test
```

## 📝 データフロー

```mermaid
graph LR
    A[ねっぱん] -->|クローリング| B[CSV取得]
    B --> C[CSVパーサー]
    C --> D[OTA識別]
    D --> E[データ正規化]
    E --> F[PostgreSQL]
    F --> G[FastAPI]
    G --> H[Next.js]
    H --> I[ユーザー]
```

## 🔧 トラブルシューティング

### よくある問題

1. **データベース接続エラー**
   ```bash
   docker-compose restart db
   ```

2. **ポート競合エラー**
   - `docker-compose.yml` のポート番号を変更

3. **ねっぱんクローラーエラー**
   - `.env` ファイルの認証情報を確認
   - ねっぱんサイトの仕様変更の可能性

### ログ確認

```bash
# 全サービスのログ
docker-compose logs

# 特定サービスのログ
docker-compose logs backend
docker-compose logs frontend
```

## 🚢 本番デプロイ

### 環境変数の設定

本番環境では以下の環境変数を適切に設定:

- `DATABASE_URL`: 本番データベースURL
- `REDIS_URL`: 本番RedisURL  
- `CORS_ORIGINS`: 本番フロントエンドURL
- セキュリティ関連の設定

### SSL/HTTPS設定

- リバースプロキシ（nginx等）でSSL終端
- 証明書の設定

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 🤝 コントリビューション

1. フォークしてください
2. フィーチャーブランチを作成してください (`git checkout -b feature/new-feature`)
3. 変更をコミットしてください (`git commit -am 'Add some feature'`)
4. ブランチにプッシュしてください (`git push origin feature/new-feature`)
5. プルリクエストを作成してください

## 📞 サポート

質問や問題がある場合は、GitHubのIssuesまでお気軽にお寄せください。