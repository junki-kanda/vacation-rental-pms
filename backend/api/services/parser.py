import pandas as pd
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class NeppanCSVParser:
    """ねっぱんCSVフォーマットのパーサー"""
    
    # OTAマッピング
    OTA_MAPPING = {
        "Booking.com": "booking",
        "ブッキングドットコム": "booking",
        "Expedia": "expedia",
        "エクスペディア": "expedia",
        "楽天トラベル": "rakuten",
        "じゃらん": "jalan",
        "一休.com": "ikyu",
        "Airbnb": "airbnb",
        "Hotels.com": "hotels",
        "Agoda": "agoda"
    }
    
    # 必須カラム（宿泊者氏名など）
    REQUIRED_COLUMNS = [
        "予約ID", "予約区分", "チェックイン日", "チェックアウト日",
        "予約サイト名称", "部屋タイプ名称", "宿泊者氏名"
    ]
    
    def __init__(self, file_path: str, encoding: str = "shift_jis"):
        self.file_path = Path(file_path)
        self.encoding = encoding
        self.df = None
        self.errors = []
    
    def parse(self) -> Tuple[pd.DataFrame, List[str]]:
        """CSVファイルをパースして予約データを返す"""
        try:
            # CSVを読み込み
            self.df = pd.read_csv(
                self.file_path,
                encoding=self.encoding,
                dtype=str,  # 全て文字列として読み込み
                na_values=["", "NA", "N/A", "null", "NULL"]
            )
            
            # カラム名の正規化（空白除去）
            self.df.columns = self.df.columns.str.strip()
            
            # 必須カラムチェック
            self._validate_columns()
            
            # データクレンジング
            self._clean_data()
            
            # OTA識別
            self._identify_ota()
            
            # 施設識別
            self._identify_facility()
            
            # 備考欄のパース
            self._parse_notes()
            
            # 日付の変換
            self._convert_dates()
            
            # 数値の変換
            self._convert_numbers()
            
            return self.df, self.errors
            
        except Exception as e:
            logger.error(f"CSV parse error: {str(e)}")
            self.errors.append(f"ファイル読み込みエラー: {str(e)}")
            return pd.DataFrame(), self.errors
    
    def _validate_columns(self):
        """必須カラムの存在確認"""
        missing_columns = []
        for col in self.REQUIRED_COLUMNS:
            if col not in self.df.columns:
                missing_columns.append(col)
        
        if missing_columns:
            error_msg = f"必須カラムが不足: {', '.join(missing_columns)}"
            self.errors.append(error_msg)
            raise ValueError(error_msg)
    
    def _clean_data(self):
        """データクレンジング"""
        # 空白行を削除
        self.df = self.df.dropna(subset=["予約ID"])
        
        # 文字列カラムの前後空白を除去
        str_columns = self.df.select_dtypes(include=[object]).columns
        for col in str_columns:
            self.df[col] = self.df[col].str.strip() if self.df[col].dtype == object else self.df[col]
    
    def _identify_ota(self):
        """OTAの識別"""
        def map_ota(site_name):
            if pd.isna(site_name):
                return "unknown"
            
            for key, value in self.OTA_MAPPING.items():
                if key in str(site_name):
                    return value
            return "other"
        
        self.df["ota_type"] = self.df["予約サイト名称"].apply(map_ota)
    
    def _identify_facility(self):
        """施設の識別（部屋タイプ名称から推定）"""
        # 部屋タイプ名称から施設名を抽出するロジック
        # 例: "ゲストハウスA - ツインルーム" -> "ゲストハウスA"
        def extract_facility(room_type):
            if pd.isna(room_type):
                return "未設定"
            
            # ハイフンや括弧で区切られている場合
            if " - " in str(room_type):
                return str(room_type).split(" - ")[0]
            elif "（" in str(room_type):
                return str(room_type).split("（")[0]
            elif "【" in str(room_type):
                return str(room_type).split("【")[0]
            else:
                # 区切り文字がない場合は全体を施設名とする
                return str(room_type)
        
        self.df["facility_name"] = self.df["部屋タイプ名称"].apply(extract_facility)
    
    def _parse_notes(self):
        """備考欄のパース（質問回答、変更履歴など）"""
        def parse_note(note):
            if pd.isna(note):
                return {"questions": "", "changes": "", "other": ""}
            
            note_str = str(note)
            result = {"questions": "", "changes": "", "other": ""}
            
            # 質問回答の抽出
            if "質問" in note_str or "Q:" in note_str:
                # 質問部分を抽出
                q_pattern = r"(質問.*?(?=変更|$))"
                q_match = re.search(q_pattern, note_str, re.DOTALL)
                if q_match:
                    result["questions"] = q_match.group(1).strip()
            
            # 変更履歴の抽出
            if "変更" in note_str or "キャンセル" in note_str:
                c_pattern = r"(変更.*?$|キャンセル.*?$)"
                c_match = re.search(c_pattern, note_str, re.DOTALL)
                if c_match:
                    result["changes"] = c_match.group(1).strip()
            
            # その他
            result["other"] = note_str
            
            return result
        
        notes_parsed = self.df["備考"].apply(parse_note) if "備考" in self.df.columns else pd.Series([{"questions": "", "changes": "", "other": ""}] * len(self.df))
        self.df["questions_answers"] = notes_parsed.apply(lambda x: x["questions"])
        self.df["change_history"] = notes_parsed.apply(lambda x: x["changes"])
        self.df["notes_other"] = notes_parsed.apply(lambda x: x["other"])
    
    def _convert_dates(self):
        """日付カラムの変換"""
        date_columns = {
            "チェックイン日": "check_in_date",
            "チェックアウト日": "check_out_date",
            "予約日": "reservation_date"
        }
        
        for jp_col, en_col in date_columns.items():
            if jp_col in self.df.columns:
                try:
                    self.df[en_col] = pd.to_datetime(
                        self.df[jp_col],
                        format="%Y/%m/%d",
                        errors="coerce"
                    )
                except:
                    try:
                        self.df[en_col] = pd.to_datetime(
                            self.df[jp_col],
                            format="%Y-%m-%d",
                            errors="coerce"
                        )
                    except:
                        self.df[en_col] = pd.NaT
    
    def _convert_numbers(self):
        """数値カラムの変換"""
        number_columns = {
            "大人数": "num_adults",
            "子供数": "num_children",
            "合計金額": "total_amount",
            "手数料": "commission",
            "純売上": "net_amount"
        }
        
        for jp_col, en_col in number_columns.items():
            if jp_col in self.df.columns:
                # カンマを除去して数値に変換
                self.df[en_col] = (
                    self.df[jp_col]
                    .str.replace(",", "")
                    .str.replace("¥", "")
                    .str.replace("円", "")
                    .apply(pd.to_numeric, errors="coerce")
                )
    
    def get_processed_data(self) -> List[Dict]:
        """処理済みデータを辞書のリストとして返す"""
        if self.df is None:
            return []
        
        # 英語カラムマッピング
        column_mapping = {
            "予約ID": "reservation_id",
            "予約区分": "reservation_type",
            "予約番号": "reservation_number",
            "予約サイト名称": "ota_name",
            "部屋タイプ名称": "room_type",
            "宿泊者氏名": "guest_name",
            "宿泊者名カナ": "guest_name_kana",
            "電話番号": "guest_phone",
            "メールアドレス": "guest_email"
        }
        
        # カラム名を英語に変換
        df_renamed = self.df.rename(columns=column_mapping)
        
        # 必要なカラムのみ選択
        required_cols = [
            "reservation_id", "reservation_type", "reservation_number",
            "ota_name", "ota_type", "facility_name", "room_type",
            "check_in_date", "check_out_date", "reservation_date",
            "guest_name", "guest_name_kana", "guest_phone", "guest_email",
            "num_adults", "num_children",
            "total_amount", "commission", "net_amount",
            "questions_answers", "change_history", "notes_other"
        ]
        
        # 存在するカラムのみ選択
        existing_cols = [col for col in required_cols if col in df_renamed.columns]
        df_final = df_renamed[existing_cols]
        
        # NaNをNoneに変換してJSONシリアライズ可能にする
        df_final = df_final.where(pd.notnull(df_final), None)
        
        return df_final.to_dict("records")