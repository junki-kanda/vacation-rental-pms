"""OTA識別サービス - 予約サイトの自動識別と分類"""

from typing import Dict, Optional
import re

class OTADetectorService:
    """OTA（Online Travel Agency）の識別と分類を行うサービス"""
    
    # 主要OTAマッピング（より詳細な識別パターン）
    OTA_PATTERNS = {
        # Booking.com系
        "booking": {
            "keywords": ["booking", "ブッキング", "booking.com"],
            "regex_patterns": [r"booking\.com", r"ブッキング.*コム"],
            "display_name": "Booking.com"
        },
        
        # Expedia系
        "expedia": {
            "keywords": ["expedia", "エクスペディア", "hotels.com"],
            "regex_patterns": [r"expedia", r"エクスペディア", r"hotels\.com"],
            "display_name": "Expedia Group"
        },
        
        # 楽天系
        "rakuten": {
            "keywords": ["楽天", "rakuten"],
            "regex_patterns": [r"楽天.*トラベル", r"rakuten.*travel"],
            "display_name": "楽天トラベル"
        },
        
        # じゃらん
        "jalan": {
            "keywords": ["じゃらん", "jalan"],
            "regex_patterns": [r"じゃらん", r"jalan"],
            "display_name": "じゃらん"
        },
        
        # 一休
        "ikyu": {
            "keywords": ["一休", "ikyu"],
            "regex_patterns": [r"一休", r"ikyu"],
            "display_name": "一休.com"
        },
        
        # Airbnb
        "airbnb": {
            "keywords": ["airbnb", "エアビー"],
            "regex_patterns": [r"airbnb", r"エアビー.*ビー"],
            "display_name": "Airbnb"
        },
        
        # Agoda
        "agoda": {
            "keywords": ["agoda", "アゴダ"],
            "regex_patterns": [r"agoda", r"アゴダ"],
            "display_name": "Agoda"
        },
        
        # Trip.com系
        "trip": {
            "keywords": ["trip", "ctrip"],
            "regex_patterns": [r"trip\.com", r"ctrip"],
            "display_name": "Trip.com"
        }
    }
    
    def __init__(self):
        """OTA検出サービスの初期化"""
        self.detection_cache = {}
    
    def detect_ota(self, site_name: str, additional_info: Optional[str] = None) -> Dict[str, str]:
        """
        OTAを検出・分類する
        
        Args:
            site_name: 予約サイト名称
            additional_info: 追加情報（予約番号、備考など）
        
        Returns:
            Dict containing:
                - ota_type: OTAタイプ（booking, expedia, etc.）
                - display_name: 表示名
                - confidence: 信頼度（high/medium/low）
        """
        if not site_name:
            return self._create_result("unknown", "不明", "low")
        
        # キャッシュチェック
        cache_key = f"{site_name}_{additional_info or ''}"
        if cache_key in self.detection_cache:
            return self.detection_cache[cache_key]
        
        site_name_lower = site_name.lower().strip()
        result = self._detect_by_patterns(site_name_lower, additional_info)
        
        # キャッシュに保存
        self.detection_cache[cache_key] = result
        return result
    
    def _detect_by_patterns(self, site_name: str, additional_info: Optional[str] = None) -> Dict[str, str]:
        """パターンマッチングによるOTA検出"""
        
        # 完全一致または高精度マッチング
        for ota_type, patterns in self.OTA_PATTERNS.items():
            # キーワードマッチング
            for keyword in patterns["keywords"]:
                if keyword.lower() in site_name:
                    return self._create_result(ota_type, patterns["display_name"], "high")
            
            # 正規表現マッチング
            for pattern in patterns["regex_patterns"]:
                if re.search(pattern, site_name, re.IGNORECASE):
                    return self._create_result(ota_type, patterns["display_name"], "high")
        
        # 追加情報からの推測
        if additional_info:
            additional_result = self._detect_from_additional_info(additional_info)
            if additional_result["ota_type"] != "unknown":
                return additional_result
        
        # 部分マッチング（信頼度中）
        fuzzy_result = self._fuzzy_match(site_name)
        if fuzzy_result["ota_type"] != "unknown":
            return fuzzy_result
        
        return self._create_result("other", site_name, "low")
    
    def _detect_from_additional_info(self, additional_info: str) -> Dict[str, str]:
        """追加情報からOTAを推測"""
        additional_info_lower = additional_info.lower()
        
        # 予約番号のパターンでOTAを推測
        if re.search(r"bdc|booking", additional_info_lower):
            return self._create_result("booking", "Booking.com", "medium")
        elif re.search(r"exp|expedia", additional_info_lower):
            return self._create_result("expedia", "Expedia Group", "medium")
        elif re.search(r"rakuten|楽天", additional_info_lower):
            return self._create_result("rakuten", "楽天トラベル", "medium")
        elif re.search(r"air|airbnb", additional_info_lower):
            return self._create_result("airbnb", "Airbnb", "medium")
        
        return self._create_result("unknown", "不明", "low")
    
    def _fuzzy_match(self, site_name: str) -> Dict[str, str]:
        """あいまい検索によるマッチング"""
        # 部分文字列での検索
        if "book" in site_name:
            return self._create_result("booking", "Booking.com", "medium")
        elif "exp" in site_name or "hotel" in site_name:
            return self._create_result("expedia", "Expedia Group", "medium")
        elif "楽天" in site_name or "rakuten" in site_name:
            return self._create_result("rakuten", "楽天トラベル", "medium")
        elif "じゃら" in site_name:
            return self._create_result("jalan", "じゃらん", "medium")
        elif "一休" in site_name:
            return self._create_result("ikyu", "一休.com", "medium")
        elif "air" in site_name:
            return self._create_result("airbnb", "Airbnb", "medium")
        
        return self._create_result("unknown", "不明", "low")
    
    def _create_result(self, ota_type: str, display_name: str, confidence: str) -> Dict[str, str]:
        """結果オブジェクトを作成"""
        return {
            "ota_type": ota_type,
            "display_name": display_name,
            "confidence": confidence
        }
    
    def get_ota_statistics(self, reservations_data: list) -> Dict[str, int]:
        """予約データからOTA別統計を取得"""
        stats = {}
        for reservation in reservations_data:
            ota_type = reservation.get("ota_type", "unknown")
            stats[ota_type] = stats.get(ota_type, 0) + 1
        return stats
    
    def get_supported_otas(self) -> Dict[str, str]:
        """サポートされているOTAの一覧を取得"""
        return {
            ota_type: patterns["display_name"] 
            for ota_type, patterns in self.OTA_PATTERNS.items()
        }