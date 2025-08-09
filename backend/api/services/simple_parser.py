"""シンプルなCSVパーサー（pandas不使用版）"""

import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from .encoding_detector import EncodingDetector

logger = logging.getLogger(__name__)

class SimpleCSVParser:
    """標準ライブラリのみを使用したCSVパーサー"""
    
    # OTAマッピング
    OTA_MAPPING = {
        "Booking.com": "booking",
        "ブッキングドットコム": "booking",
        "Expedia": "expedia",
        "エクスペディア": "expedia",
        "楽天トラベル": "rakuten",
        "じゃらん": "jalan",
        "じゃらんnet": "jalan",
        "一休.com": "ikyu",
        "一休": "ikyu",
        "Airbnb": "airbnb",
        "Hotels.com": "hotels",
        "Agoda": "agoda",
        "予約PRO": "yoyaku_pro",
        "直接予約": "direct"
    }
    
    def __init__(self, file_path: str, encoding: str = None):
        self.file_path = Path(file_path)
        self.encoding = encoding
        self.detected_encoding = None
        self.encoding_confidence = 0
        self.data = []
        self.errors = []
        self.headers = []
    
    def parse(self) -> Tuple[List[Dict], List[str]]:
        """CSVファイルをパースして予約データを返す"""
        # エンコーディングが指定されていない場合は自動検出
        if not self.encoding:
            try:
                detection_result = EncodingDetector.detect_encoding(str(self.file_path))
                self.detected_encoding = detection_result['encoding']
                self.encoding_confidence = detection_result['confidence']
                self.encoding = self.detected_encoding
                logger.info(f"Detected encoding: {self.encoding} (confidence: {self.encoding_confidence:.2f})")
                
                # 信頼度が低い場合は警告
                if self.encoding_confidence < 0.7:
                    self.errors.append(f"エンコーディング検出の信頼度が低いです: {self.encoding_confidence:.2f}")
                    
            except Exception as e:
                logger.error(f"Encoding detection failed: {str(e)}")
                self.encoding = 'utf-8'  # デフォルトに fallback
                self.errors.append(f"エンコーディング自動検出に失敗しました。UTF-8を使用します。")
        
        # CSVファイルを読み込む
        try:
            with open(self.file_path, 'r', encoding=self.encoding) as f:
                reader = csv.DictReader(f)
                self.headers = reader.fieldnames
                
                for row_num, row in enumerate(reader, start=2):
                    try:
                        processed_row = self._process_row(row)
                        if processed_row:
                            self.data.append(processed_row)
                    except Exception as e:
                        self.errors.append(f"Row {row_num}: {str(e)}")
                
            return self.data, self.errors
            
        except UnicodeDecodeError as e:
            logger.error(f"CSV parse error with encoding {self.encoding}: {str(e)}")
            # 代替エンコーディングを試す
            if self.detected_encoding:
                alternative_encodings = ['utf-8', 'shift_jis', 'cp932', 'euc-jp']
                for alt_encoding in alternative_encodings:
                    if alt_encoding != self.encoding:
                        try:
                            self.encoding = alt_encoding
                            self.data = []
                            self.errors = []
                            return self._retry_parse()
                        except:
                            continue
            
            self.errors.append(f"ファイル読み込みエラー: エンコーディング '{self.encoding}' で読み込めません")
            return [], self.errors
            
        except Exception as e:
            logger.error(f"CSV parse error: {str(e)}")
            self.errors.append(f"ファイル読み込みエラー: {str(e)}")
            return [], self.errors
    
    def _retry_parse(self) -> Tuple[List[Dict], List[str]]:
        """代替エンコーディングで再試行"""
        logger.info(f"Retrying with encoding: {self.encoding}")
        with open(self.file_path, 'r', encoding=self.encoding) as f:
            reader = csv.DictReader(f)
            self.headers = reader.fieldnames
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    processed_row = self._process_row(row)
                    if processed_row:
                        self.data.append(processed_row)
                except Exception as e:
                    self.errors.append(f"Row {row_num}: {str(e)}")
            
        return self.data, self.errors
    
    def _process_row(self, row: Dict) -> Optional[Dict]:
        """行データを処理（ねっぱんCSVフォーマット対応）"""
        # 空白を除去
        cleaned_row = {k.strip() if k else k: v.strip() if v else v for k, v in row.items()}
        
        # 予約IDがない行はスキップ
        if not cleaned_row.get("予約ID"):
            return None
        
        # OTA識別
        ota_name = cleaned_row.get("予約サイト名称", "")
        ota_type = self._identify_ota(ota_name)
        
        # 施設識別
        room_type = cleaned_row.get("部屋タイプ名称", "")
        facility_name = self._extract_facility(room_type)
        
        # 日付変換
        check_in_date = self._parse_date(cleaned_row.get("チェックイン日"))
        check_out_date = self._parse_date(cleaned_row.get("チェックアウト日"))
        reservation_date = self._parse_datetime(cleaned_row.get("申込日"))  # 申込日を使用
        
        # 数値変換（ねっぱんのカラム名に合わせる）
        num_adults = self._parse_number(cleaned_row.get("大人人数計", "1"))
        num_children = self._parse_number(cleaned_row.get("子供人数計", "0"))
        num_infants = self._parse_number(cleaned_row.get("幼児人数計", "0"))
        total_amount = self._parse_amount(cleaned_row.get("料金合計額"))
        
        # 料金詳細
        adult_rate = self._parse_amount(cleaned_row.get("大人単価"))
        child_rate = self._parse_amount(cleaned_row.get("子供単価"))
        infant_rate = self._parse_amount(cleaned_row.get("幼児単価"))
        adult_amount = self._parse_amount(cleaned_row.get("大人合計額"))
        child_amount = self._parse_amount(cleaned_row.get("子供合計額"))
        infant_amount = self._parse_amount(cleaned_row.get("幼児合計額"))
        
        # オプション・ポイント
        option_items = cleaned_row.get("その他明細")
        option_amount = self._parse_amount(cleaned_row.get("その他合計額"))
        point_amount = self._parse_amount(cleaned_row.get("ポイント額"))
        point_discount = self._parse_amount(cleaned_row.get("ポイント割引額"))
        
        # 備考の結合
        notes_parts = []
        if cleaned_row.get("備考1"):
            notes_parts.append(cleaned_row.get("備考1"))
        if cleaned_row.get("備考2"):
            notes_parts.append(cleaned_row.get("備考2"))
        if cleaned_row.get("メモ"):
            notes_parts.append(f"メモ: {cleaned_row.get('メモ')}")
        notes = "\n".join(notes_parts)
        
        return {
            "reservation_id": cleaned_row.get("予約ID"),
            "reservation_type": cleaned_row.get("予約区分", "予約"),
            "reservation_number": cleaned_row.get("予約番号"),
            "ota_name": ota_name,
            "ota_type": ota_type,
            "facility_name": facility_name,
            "room_type": room_type,
            "check_in_date": check_in_date,
            "check_out_date": check_out_date,
            "reservation_date": reservation_date,
            "guest_name": cleaned_row.get("宿泊者氏名", ""),  # カラム名修正
            "guest_name_kana": cleaned_row.get("宿泊者氏名カタカナ"),  # カラム名修正
            "guest_phone": cleaned_row.get("電話番号"),
            "guest_email": cleaned_row.get("メールアドレス"),
            "num_adults": num_adults,
            "num_children": num_children,  # 子供人数のみ
            "num_infants": num_infants,  # 幼児人数を別フィールドで保存
            "total_amount": total_amount,
            "commission": None,  # ねっぱんCSVには手数料カラムがない
            "net_amount": None,  # ねっぱんCSVには純売上カラムがない
            # 料金詳細
            "adult_rate": adult_rate,
            "child_rate": child_rate,
            "infant_rate": infant_rate,
            "adult_amount": adult_amount,
            "child_amount": child_amount,
            "infant_amount": infant_amount,
            # オプション・ポイント
            "option_items": option_items,
            "option_amount": option_amount,
            "point_amount": point_amount,
            "point_discount": point_discount,
            "notes": notes,
            "questions_answers": self._extract_questions(notes),
            "change_history": self._extract_changes(notes),
            # 追加フィールド
            "nights": self._parse_number(cleaned_row.get("泊数", "1")),
            "rooms": self._parse_number(cleaned_row.get("室数", "1")),
            "meal_plan": cleaned_row.get("食事"),
            "payment_method": cleaned_row.get("決済方法"),
            "booker_name": cleaned_row.get("予約者氏名"),
            "booker_name_kana": cleaned_row.get("予約者氏名カタカナ"),
            "plan_name": cleaned_row.get("商品プラン名称"),
            "plan_code": cleaned_row.get("商品プランコード"),
            "checkin_time": cleaned_row.get("チェックイン時刻"),
            "cancel_date": self._parse_date(cleaned_row.get("予約キャンセル日")),
            # 住所・連絡先情報
            "postal_code": cleaned_row.get("郵便番号"),
            "address": cleaned_row.get("住所1"),
            "member_number": cleaned_row.get("会員番号"),
            "company_info": cleaned_row.get("法人情報"),
            "reservation_route": cleaned_row.get("予約経路"),
            "memo": cleaned_row.get("メモ")
        }
    
    def _identify_ota(self, site_name: str) -> str:
        """OTAの識別"""
        if not site_name:
            return "unknown"
        
        for key, value in self.OTA_MAPPING.items():
            if key in site_name:
                return value
        return "other"
    
    def _extract_facility(self, room_type: str) -> str:
        """施設の識別"""
        if not room_type:
            return "未設定"
        
        # ハイフンや括弧で区切られている場合
        if " - " in room_type:
            return room_type.split(" - ")[0]
        elif "（" in room_type:
            return room_type.split("（")[0]
        elif "【" in room_type:
            return room_type.split("【")[0]
        else:
            return room_type
    
    def _extract_questions(self, note: str) -> str:
        """質問回答の抽出"""
        if not note:
            return ""
        
        if "質問" in note or "Q:" in note or "問い合わせ" in note:
            # 簡単な抽出ロジック
            lines = note.split('\n')
            questions = [line for line in lines if "質問" in line or "Q:" in line or "問い合わせ" in line]
            return '\n'.join(questions)
        return ""
    
    def _extract_changes(self, note: str) -> str:
        """変更履歴の抽出"""
        if not note:
            return ""
        
        if "変更" in note or "キャンセル" in note or "取消" in note:
            lines = note.split('\n')
            changes = [line for line in lines if "変更" in line or "キャンセル" in line or "取消" in line]
            return '\n'.join(changes)
        return ""
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """日付文字列を解析"""
        if not date_str:
            return None
        
        # YYYY/MM/DD or YYYY-MM-DD形式を想定
        for fmt in ["%Y/%m/%d", "%Y-%m-%d", "%Y年%m月%d日"]:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.date().isoformat()
            except ValueError:
                continue
        
        return None
    
    def _parse_datetime(self, datetime_str: str) -> Optional[str]:
        """日時文字列を解析"""
        if not datetime_str:
            return None
        
        for fmt in ["%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M"]:
            try:
                dt = datetime.strptime(datetime_str, fmt)
                return dt.isoformat()
            except ValueError:
                continue
        
        # 日付のみの場合
        date_only = self._parse_date(datetime_str)
        if date_only:
            return f"{date_only}T00:00:00"
        
        return None
    
    def _parse_number(self, num_str: str) -> int:
        """数値文字列を解析"""
        if not num_str:
            return 0
        
        try:
            # カンマや全角数字を処理
            num_str = num_str.replace(",", "").replace("，", "")
            return int(float(num_str))
        except (ValueError, TypeError):
            return 0
    
    def _parse_amount(self, amount_str: str) -> Optional[float]:
        """金額文字列を解析"""
        if not amount_str:
            return None
        
        try:
            # 円マークやカンマを除去
            amount_str = amount_str.replace("¥", "").replace(",", "").replace("円", "")
            return float(amount_str)
        except (ValueError, TypeError):
            return None
    
    def get_processed_data(self) -> List[Dict]:
        """処理済みデータを返す"""
        return self.data