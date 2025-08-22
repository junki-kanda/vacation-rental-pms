"""
FastAPI ドキュメント設定
Swagger UI と ReDoc のカスタマイズ設定
"""

from typing import Dict, Any

# API タグの説明
tags_metadata = [
    {
        "name": "予約管理",
        "description": "予約情報の取得、作成、更新、削除を行うエンドポイント群。複数のOTAから取得した予約データを統合管理します。",
        "externalDocs": {
            "description": "予約管理の詳細",
            "url": "/api/docs#/予約管理",
        },
    },
    {
        "name": "施設管理",
        "description": "施設（物件）情報の管理を行うエンドポイント群。施設の基本情報、設備、料金設定などを管理します。",
    },
    {
        "name": "清掃管理",
        "description": "清掃タスクの管理、スタッフの管理、自動割当機能などを提供するエンドポイント群。",
        "externalDocs": {
            "description": "清掃管理の詳細",
            "url": "/api/docs#/清掃管理",
        },
    },
    {
        "name": "ダッシュボード",
        "description": "統計情報、KPI、分析データを提供するエンドポイント群。リアルタイムの稼働状況や売上情報を取得できます。",
    },
    {
        "name": "データ同期",
        "description": "外部システムとのデータ同期を行うエンドポイント群。CSVファイルのアップロードや処理状況の確認が可能です。",
    },
    {
        "name": "スタッフグループ",
        "description": "清掃スタッフのグループ管理機能。グループ単位での一括タスク割当などが可能です。",
    }
]

# OpenAPI スキーマのカスタマイズ
def custom_openapi_schema() -> Dict[str, Any]:
    """
    カスタムOpenAPIスキーマを生成
    """
    return {
        "info": {
            "x-logo": {
                "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png",
                "altText": "Vacation Rental PMS"
            }
        },
        "servers": [
            {
                "url": "http://localhost:8000",
                "description": "開発サーバー"
            },
            {
                "url": "https://api.example.com",
                "description": "本番サーバー"
            }
        ],
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "JWT認証トークン（将来実装予定）"
                }
            }
        }
    }

# APIレスポンス例
response_examples = {
    "reservation": {
        "example": {
            "id": 1,
            "reservation_id": "RES-2024-001",
            "guest_name": "山田太郎",
            "check_in_date": "2024-01-15",
            "check_out_date": "2024-01-17",
            "num_adults": 2,
            "num_children": 1,
            "num_infants": 0,
            "total_amount": 50000,
            "facility_id": 1,
            "room_type": "デラックスルーム",
            "reservation_type": "予約",
            "ota_name": "Booking.com",
            "created_at": "2024-01-01T10:00:00",
            "updated_at": "2024-01-01T10:00:00"
        }
    },
    "facility": {
        "example": {
            "id": 1,
            "name": "湖畔の別荘A棟",
            "facility_group": "湖畔リゾート",
            "address": "山梨県富士河口湖町1-2-3",
            "max_guests": 8,
            "total_rooms": 3,
            "is_active": True,
            "created_at": "2024-01-01T10:00:00",
            "updated_at": "2024-01-01T10:00:00"
        }
    },
    "cleaning_task": {
        "example": {
            "id": 1,
            "facility_id": 1,
            "reservation_id": 1,
            "task_date": "2024-01-17",
            "task_type": "checkout",
            "status": "pending",
            "priority": "high",
            "assigned_staff_id": 5,
            "assigned_group_id": None,
            "start_time": "10:00",
            "end_time": "14:00",
            "notes": "ペット同伴のお客様でした",
            "created_at": "2024-01-01T10:00:00",
            "updated_at": "2024-01-15T14:30:00"
        }
    },
    "staff": {
        "example": {
            "id": 1,
            "name": "田中花子",
            "name_kana": "タナカハナコ",
            "email": "tanaka@example.com",
            "phone": "090-1234-5678",
            "employee_code": "EMP001",
            "is_active": True,
            "skill_level": "senior",
            "can_work_alone": True,
            "can_handle_large_properties": True,
            "available_facilities": [1, 2, 3],
            "rate_per_property": 5000,
            "transportation_fee": 500,
            "created_at": "2024-01-01T10:00:00",
            "updated_at": "2024-01-01T10:00:00"
        }
    },
    "dashboard_stats": {
        "example": {
            "today_checkins": 5,
            "today_checkouts": 3,
            "total_guests_today": 24,
            "occupancy_rate": 75.5,
            "recent_reservations": [],
            "sync_status": {
                "id": 1,
                "sync_type": "reservations",
                "status": "completed",
                "started_at": "2024-01-15T09:00:00",
                "completed_at": "2024-01-15T09:01:30",
                "total_rows": 150,
                "processed_rows": 150,
                "new_reservations": 10,
                "updated_reservations": 5,
                "error_message": None
            }
        }
    }
}

# エラーレスポンスの例
error_responses = {
    400: {
        "description": "Bad Request",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Invalid request parameters"
                }
            }
        }
    },
    401: {
        "description": "Unauthorized",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Authentication required"
                }
            }
        }
    },
    403: {
        "description": "Forbidden",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Permission denied"
                }
            }
        }
    },
    404: {
        "description": "Not Found",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Resource not found"
                }
            }
        }
    },
    409: {
        "description": "Conflict",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Resource already exists"
                }
            }
        }
    },
    422: {
        "description": "Validation Error",
        "content": {
            "application/json": {
                "example": {
                    "detail": [
                        {
                            "loc": ["body", "field_name"],
                            "msg": "field required",
                            "type": "value_error.missing"
                        }
                    ]
                }
            }
        }
    },
    500: {
        "description": "Internal Server Error",
        "content": {
            "application/json": {
                "example": {
                    "detail": "An unexpected error occurred"
                }
            }
        }
    }
}