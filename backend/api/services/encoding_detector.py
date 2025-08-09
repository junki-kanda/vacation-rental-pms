"""文字エンコーディング検出サービス"""

from pathlib import Path
from typing import Dict, Any
import logging

# ``chardet`` は任意依存関係。存在しない環境でもモジュールを
# インポートできるように、読み込み時に失敗を許容する。
try:  # pragma: no cover - 環境依存のため
    import chardet  # type: ignore
except ModuleNotFoundError:  # ライブラリが無い場合
    chardet = None  # type: ignore
    logging.getLogger(__name__).warning(
        "chardet library not installed. Falling back to naive encoding detection."
    )

logger = logging.getLogger(__name__)

class EncodingDetector:
    """CSVファイルのエンコーディングを自動検出するサービス"""
    
    # よく使われる日本語エンコーディング（優先順位順）
    JAPANESE_ENCODINGS = [
        'utf-8-sig',  # UTF-8 with BOM
        'utf-8',      # UTF-8
        'shift_jis',  # Shift-JIS
        'cp932',      # Windows-31J (Shift-JIS拡張)
        'euc-jp',     # EUC-JP
        'iso-2022-jp' # JIS
    ]
    
    @classmethod
    def detect_encoding(cls, file_path: str, sample_size: int = 65536) -> Dict[str, Any]:
        """
        ファイルのエンコーディングを検出
        
        Args:
            file_path: 検出対象のファイルパス
            sample_size: 検出に使用するバイト数（デフォルト64KB）
            
        Returns:
            検出結果の辞書
            {
                'encoding': 検出されたエンコーディング,
                'confidence': 信頼度（0.0-1.0）,
                'language': 言語,
                'alternative_encodings': 代替エンコーディングのリスト
            }
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        result = {
            'encoding': None,
            'confidence': 0,
            'language': 'unknown',
        }

        # chardet が利用可能な場合のみ自動検出を試みる
        if chardet is not None:
            with open(file_path, 'rb') as f:
                raw_data = f.read(sample_size)
                result = chardet.detect(raw_data)

        detected_encoding = result.get('encoding')
        confidence = result.get('confidence', 0)
        
        # 信頼度が低い場合は日本語エンコーディングを試す
        alternative_encodings = []
        if confidence < 0.8 or detected_encoding is None:
            valid_encodings = cls._test_japanese_encodings(file_path)
            if valid_encodings:
                # 最初の有効なエンコーディングを使用
                if not detected_encoding or confidence < 0.5:
                    detected_encoding = valid_encodings[0]
                    confidence = 0.9  # 手動検証の信頼度
                alternative_encodings = valid_encodings[1:] if len(valid_encodings) > 1 else []
        
        return {
            'encoding': detected_encoding or 'utf-8',  # デフォルトはUTF-8
            'confidence': confidence,
            'language': result.get('language', 'unknown'),
            'alternative_encodings': alternative_encodings
        }
    
    @classmethod
    def _test_japanese_encodings(cls, file_path: str) -> list:
        """
        日本語エンコーディングを順番に試して、有効なものを返す
        
        Args:
            file_path: テスト対象のファイルパス
            
        Returns:
            有効なエンコーディングのリスト
        """
        valid_encodings = []
        
        for encoding in cls.JAPANESE_ENCODINGS:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    # 最初の数行を読んでみる
                    lines = []
                    for i in range(10):
                        line = f.readline()
                        if not line:
                            break
                        lines.append(line)
                    
                    # 日本語文字が含まれているかチェック
                    text = ''.join(lines)
                    if cls._contains_japanese(text):
                        valid_encodings.append(encoding)
                        logger.info(f"Valid encoding found: {encoding}")
                        
            except (UnicodeDecodeError, UnicodeError):
                continue
            except Exception as e:
                logger.debug(f"Error testing encoding {encoding}: {e}")
                continue
                
        return valid_encodings
    
    @staticmethod
    def _contains_japanese(text: str) -> bool:
        """
        テキストに日本語文字が含まれているかチェック
        
        Args:
            text: チェック対象のテキスト
            
        Returns:
            日本語文字が含まれている場合True
        """
        if not text:
            return False
            
        # 日本語文字の範囲をチェック
        for char in text:
            code_point = ord(char)
            # ひらがな、カタカナ、漢字の範囲
            if (0x3040 <= code_point <= 0x309F or  # ひらがな
                0x30A0 <= code_point <= 0x30FF or  # カタカナ
                0x4E00 <= code_point <= 0x9FFF):   # 漢字
                return True
        return False
    
    @classmethod
    def read_with_detected_encoding(cls, file_path: str, lines: int = None) -> tuple:
        """
        エンコーディングを自動検出してファイルを読む
        
        Args:
            file_path: 読み込むファイルパス
            lines: 読み込む行数（Noneの場合は全行）
            
        Returns:
            (読み込んだテキスト, 使用したエンコーディング)
        """
        detection_result = cls.detect_encoding(file_path)
        encoding = detection_result['encoding']
        
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                if lines:
                    text = ''.join(f.readline() for _ in range(lines))
                else:
                    text = f.read()
            return text, encoding
        except UnicodeDecodeError:
            # 代替エンコーディングを試す
            for alt_encoding in detection_result.get('alternative_encodings', []):
                try:
                    with open(file_path, 'r', encoding=alt_encoding) as f:
                        if lines:
                            text = ''.join(f.readline() for _ in range(lines))
                        else:
                            text = f.read()
                    return text, alt_encoding
                except UnicodeDecodeError:
                    continue
                    
            raise ValueError(f"Failed to read file with any detected encoding")