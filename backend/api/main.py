from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pathlib import Path
import logging
import os
import json

from .database import engine
from .models import Base
from .routers import reservations_router, properties_router, sync_router, dashboard_router, cleaning_router, staff_groups_router
from .docs_config import tags_metadata

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# データベーステーブルの作成
Base.metadata.create_all(bind=engine)

# FastAPIアプリケーション
app = FastAPI(
    title="Vacation Rental PMS API",
    description="""
## 一棟貸の貸別荘に特化したPMSシステム

### 主な機能:
- **予約管理**: 複数OTAからの予約データの統合管理
- **施設管理**: 施設情報、部屋タイプ、料金設定の管理
- **清掃管理**: 清掃タスクの自動生成、スタッフ割当、進捗管理
- **ダッシュボード**: リアルタイム統計、稼働率、売上分析
- **データ同期**: CSVファイルによるバッチ同期機能

### 認証:
現在のバージョンでは認証は実装されていません。本番環境では適切な認証機構を実装してください。

### レート制限:
現在のバージョンではレート制限は実装されていません。

### エラーレスポンス:
すべてのエンドポイントは標準的なHTTPステータスコードを返します。
- 200: 成功
- 201: 作成成功
- 400: リクエストエラー
- 404: リソースが見つからない
- 422: バリデーションエラー
- 500: サーバーエラー
    """,
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    openapi_tags=tags_metadata,
    default_response_class=JSONResponse
)

# CORS設定
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001", 
    "http://localhost:3002",
    "http://localhost:3003",
    "http://localhost:3004",
    "http://localhost:3005",
    "http://localhost:3006",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3005",
    "http://127.0.0.1:3006"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# UTF-8エンコーディングミドルウェア
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import json as json_module

class UTF8Middleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # JSONレスポンスの場合はcharset=utf-8を追加
        if response.headers.get("content-type", "").startswith("application/json"):
            response.headers["content-type"] = "application/json; charset=utf-8"
        
        return response

app.add_middleware(UTF8Middleware)

# ディレクトリの作成
CSV_DIR = os.getenv("CSV_DIR", "./backend/data/csv")
Path(CSV_DIR).mkdir(parents=True, exist_ok=True)

# ルーターの登録
app.include_router(reservations_router)
app.include_router(properties_router)
app.include_router(sync_router)
app.include_router(dashboard_router)
app.include_router(cleaning_router)
app.include_router(staff_groups_router)

# ルートエンドポイント
@app.get("/")
def read_root():
    return {
        "message": "Vacation Rental PMS API",
        "version": "1.0.0",
        "description": "一棟貸の貸別荘に特化したPMSシステム"
    }

# ヘルスチェック
@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host=os.getenv("API_HOST", "0.0.0.0"), 
        port=int(os.getenv("API_PORT", "8000"))
    )