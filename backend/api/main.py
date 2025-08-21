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

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# データベーステーブルの作成
Base.metadata.create_all(bind=engine)

# FastAPIアプリケーション
app = FastAPI(
    title="Vacation Rental PMS",
    description="一棟貸の貸別荘に特化したPMSシステム",
    version="1.0.0",
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