"""
CSVパーサーの数値カラムマッピング包括的テスト
"""
import pytest
import pandas as pd
from api.services.parser import NeppanCSVParser
import tempfile
import os


@pytest.fixture
def base_csv_headers():
    """基本的なCSVヘッダー（必須カラム含む）"""
    return [
        "予約ID", "予約区分", "チェックイン日", "チェックアウト日", 
        "予約サイト名称", "部屋タイプ名称", "宿泊者氏名"
    ]


@pytest.fixture
def number_columns():
    """数値カラムのマッピング"""
    return {
        "大人人数計": "num_adults",
        "子供人数計": "num_children", 
        "幼児人数計": "num_infants",
        "合計金額": "total_amount",
        "手数料": "commission",
        "純売上": "net_amount"
    }


def create_test_csv(headers, rows, encoding="utf-8"):
    """テスト用CSVファイルを作成"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding=encoding, suffix='.csv') as f:
        # ヘッダー行
        f.write(','.join(headers) + '\n')
        # データ行
        for row in rows:
            f.write(','.join(str(cell) for cell in row) + '\n')
        return f.name


def test_basic_number_conversion(base_csv_headers, number_columns):
    """基本的な数値変換テスト"""
    headers = base_csv_headers + list(number_columns.keys())
    rows = [
        ["R001", "予約", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "田中太郎", 
         "2", "1", "0", "15000", "1500", "13500"]
    ]
    
    csv_file = create_test_csv(headers, rows)
    
    try:
        parser = NeppanCSVParser(csv_file, encoding="utf-8")
        df, errors = parser.parse()
        
        assert len(errors) == 0, f"Unexpected errors: {errors}"
        assert len(df) == 1
        
        # 各数値カラムが正しく変換されているかチェック
        assert df.loc[0, "num_adults"] == 2
        assert df.loc[0, "num_children"] == 1
        assert df.loc[0, "num_infants"] == 0
        assert df.loc[0, "total_amount"] == 15000
        assert df.loc[0, "commission"] == 1500
        assert df.loc[0, "net_amount"] == 13500
        
        # データタイプの確認
        for col in number_columns.values():
            assert pd.api.types.is_numeric_dtype(df[col]), f"Column {col} is not numeric"
            
    finally:
        os.unlink(csv_file)


def test_number_conversion_with_commas(base_csv_headers):
    """カンマ区切りの数値変換テスト"""
    headers = base_csv_headers + ["合計金額", "手数料", "純売上"]
    rows = [
        ["R001", "予約", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "田中太郎",
         "1,200,000", "120,000", "1,080,000"]
    ]
    
    csv_file = create_test_csv(headers, rows)
    
    try:
        parser = NeppanCSVParser(csv_file, encoding="utf-8")
        df, errors = parser.parse()
        
        assert len(errors) == 0
        assert df.loc[0, "total_amount"] == 1200000
        assert df.loc[0, "commission"] == 120000
        assert df.loc[0, "net_amount"] == 1080000
        
    finally:
        os.unlink(csv_file)


def test_number_conversion_with_currency_symbols(base_csv_headers):
    """通貨記号付きの数値変換テスト"""
    headers = base_csv_headers + ["合計金額", "手数料", "純売上"]
    rows = [
        ["R001", "予約", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "田中太郎",
         "¥50,000", "¥5,000円", "45,000円"]
    ]
    
    csv_file = create_test_csv(headers, rows)
    
    try:
        parser = NeppanCSVParser(csv_file, encoding="utf-8")
        df, errors = parser.parse()
        
        assert len(errors) == 0
        assert df.loc[0, "total_amount"] == 50000
        assert df.loc[0, "commission"] == 5000
        assert df.loc[0, "net_amount"] == 45000
        
    finally:
        os.unlink(csv_file)


def test_invalid_number_values(base_csv_headers):
    """無効な数値の処理テスト"""
    headers = base_csv_headers + ["大人人数計", "子供人数計", "合計金額"]
    rows = [
        ["R001", "予約", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "田中太郎",
         "abc", "２", "無効"],  # 無効な値を含む
        ["R002", "予約", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "山田花子",
         "", "", ""],  # 空文字
        ["R003", "予約", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "佐藤次郎",
         "2.5", "1.0", "15000.50"]  # 小数点
    ]
    
    csv_file = create_test_csv(headers, rows)
    
    try:
        parser = NeppanCSVParser(csv_file, encoding="utf-8")
        df, errors = parser.parse()
        
        assert len(errors) == 0  # パースエラーではなく、無効値はNaNになるべき
        assert len(df) == 3
        
        # 無効な値はNaNになる
        assert pd.isna(df.loc[0, "num_adults"])  # "abc"
        assert pd.isna(df.loc[0, "num_children"])  # "２"（全角数字）
        assert pd.isna(df.loc[0, "total_amount"])  # "無効"
        
        # 空文字もNaNになる
        assert pd.isna(df.loc[1, "num_adults"])
        assert pd.isna(df.loc[1, "num_children"])
        assert pd.isna(df.loc[1, "total_amount"])
        
        # 小数点はそのまま変換される
        assert df.loc[2, "num_adults"] == 2.5
        assert df.loc[2, "num_children"] == 1.0
        assert df.loc[2, "total_amount"] == 15000.5
        
    finally:
        os.unlink(csv_file)


def test_zero_values(base_csv_headers):
    """ゼロ値の処理テスト"""
    headers = base_csv_headers + ["大人人数計", "子供人数計", "幼児人数計", "合計金額"]
    rows = [
        ["R001", "予約", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "田中太郎",
         "0", "0", "0", "0"]
    ]
    
    csv_file = create_test_csv(headers, rows)
    
    try:
        parser = NeppanCSVParser(csv_file, encoding="utf-8")
        df, errors = parser.parse()
        
        assert len(errors) == 0
        assert df.loc[0, "num_adults"] == 0
        assert df.loc[0, "num_children"] == 0
        assert df.loc[0, "num_infants"] == 0
        assert df.loc[0, "total_amount"] == 0
        
    finally:
        os.unlink(csv_file)


def test_negative_values(base_csv_headers):
    """負の値の処理テスト（キャンセル等）"""
    headers = base_csv_headers + ["合計金額", "手数料", "純売上"]
    rows = [
        ["R001", "キャンセル", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "田中太郎",
         "-50000", "-5000", "-45000"]
    ]
    
    csv_file = create_test_csv(headers, rows)
    
    try:
        parser = NeppanCSVParser(csv_file, encoding="utf-8")
        df, errors = parser.parse()
        
        assert len(errors) == 0
        assert df.loc[0, "total_amount"] == -50000
        assert df.loc[0, "commission"] == -5000
        assert df.loc[0, "net_amount"] == -45000
        
    finally:
        os.unlink(csv_file)


def test_large_numbers(base_csv_headers):
    """大きな数値の処理テスト"""
    headers = base_csv_headers + ["大人人数計", "合計金額"]
    rows = [
        ["R001", "予約", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "田中太郎",
         "99", "999999999"]
    ]
    
    csv_file = create_test_csv(headers, rows)
    
    try:
        parser = NeppanCSVParser(csv_file, encoding="utf-8")
        df, errors = parser.parse()
        
        assert len(errors) == 0
        assert df.loc[0, "num_adults"] == 99
        assert df.loc[0, "total_amount"] == 999999999
        
    finally:
        os.unlink(csv_file)


def test_missing_number_columns(base_csv_headers):
    """数値カラムが存在しない場合のテスト"""
    headers = base_csv_headers  # 数値カラムなし
    rows = [
        ["R001", "予約", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "田中太郎"]
    ]
    
    csv_file = create_test_csv(headers, rows)
    
    try:
        parser = NeppanCSVParser(csv_file, encoding="utf-8")
        df, errors = parser.parse()
        
        assert len(errors) == 0  # 数値カラムがなくてもエラーにならない
        # 数値カラムは存在しないはず
        assert "num_adults" not in df.columns
        assert "total_amount" not in df.columns
        
    finally:
        os.unlink(csv_file)


def test_partial_number_columns(base_csv_headers):
    """一部の数値カラムのみ存在する場合のテスト"""
    headers = base_csv_headers + ["大人人数計", "合計金額"]  # 一部のみ
    rows = [
        ["R001", "予約", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "田中太郎",
         "2", "15000"]
    ]
    
    csv_file = create_test_csv(headers, rows)
    
    try:
        parser = NeppanCSVParser(csv_file, encoding="utf-8")
        df, errors = parser.parse()
        
        assert len(errors) == 0
        assert df.loc[0, "num_adults"] == 2
        assert df.loc[0, "total_amount"] == 15000
        
        # 存在しないカラムは作られない
        assert "num_children" not in df.columns
        assert "commission" not in df.columns
        
    finally:
        os.unlink(csv_file)


def test_mixed_valid_invalid_numbers(base_csv_headers):
    """有効・無効な数値が混在する場合のテスト"""
    headers = base_csv_headers + ["大人人数計", "子供人数計", "合計金額"]
    rows = [
        ["R001", "予約", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "田中太郎",
         "2", "abc", "15000"],  # 中間に無効値
        ["R002", "予約", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "山田花子",
         "xyz", "1", "invalid"],  # 最初と最後に無効値
        ["R003", "予約", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "佐藤次郎",
         "3", "2", "25000"]  # 全て有効
    ]
    
    csv_file = create_test_csv(headers, rows)
    
    try:
        parser = NeppanCSVParser(csv_file, encoding="utf-8")
        df, errors = parser.parse()
        
        assert len(errors) == 0
        assert len(df) == 3
        
        # 行1: 有効、無効、有効
        assert df.loc[0, "num_adults"] == 2
        assert pd.isna(df.loc[0, "num_children"])
        assert df.loc[0, "total_amount"] == 15000
        
        # 行2: 無効、有効、無効
        assert pd.isna(df.loc[1, "num_adults"])
        assert df.loc[1, "num_children"] == 1
        assert pd.isna(df.loc[1, "total_amount"])
        
        # 行3: 全て有効
        assert df.loc[2, "num_adults"] == 3
        assert df.loc[2, "num_children"] == 2
        assert df.loc[2, "total_amount"] == 25000
        
    finally:
        os.unlink(csv_file)


def test_different_encodings(base_csv_headers):
    """異なる文字エンコーディングでの数値処理テスト"""
    headers = base_csv_headers + ["大人人数計", "合計金額"]
    rows = [
        ["R001", "予約", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "田中太郎",
         "2", "15000"]
    ]
    
    # Shift_JIS でテスト
    csv_file = create_test_csv(headers, rows, encoding="shift_jis")
    
    try:
        parser = NeppanCSVParser(csv_file, encoding="shift_jis")
        df, errors = parser.parse()
        
        assert len(errors) == 0
        assert df.loc[0, "num_adults"] == 2
        assert df.loc[0, "total_amount"] == 15000
        
    finally:
        os.unlink(csv_file)


def test_get_processed_data_number_columns(base_csv_headers):
    """get_processed_data()メソッドでの数値カラム確認"""
    headers = base_csv_headers + ["大人人数計", "子供人数計", "合計金額"]
    rows = [
        ["R001", "予約", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "田中太郎",
         "2", "1", "15000"]
    ]
    
    csv_file = create_test_csv(headers, rows)
    
    try:
        parser = NeppanCSVParser(csv_file, encoding="utf-8")
        df, errors = parser.parse()
        processed_data = parser.get_processed_data()
        
        assert len(processed_data) == 1
        record = processed_data[0]
        
        # 数値カラムが正しく含まれているかチェック
        assert record["num_adults"] == 2
        assert record["num_children"] == 1
        assert record["total_amount"] == 15000
        
        # 型の確認（JSONシリアライズ可能）
        assert isinstance(record["num_adults"], (int, float))
        assert isinstance(record["num_children"], (int, float))
        assert isinstance(record["total_amount"], (int, float))
        
    finally:
        os.unlink(csv_file)


def test_whitespace_in_number_values(base_csv_headers):
    """数値に空白が含まれる場合のテスト"""
    headers = base_csv_headers + ["大人人数計", "合計金額"]
    rows = [
        ["R001", "予約", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "田中太郎",
         " 2 ", "  15000  "]
    ]
    
    csv_file = create_test_csv(headers, rows)
    
    try:
        parser = NeppanCSVParser(csv_file, encoding="utf-8")
        df, errors = parser.parse()
        
        assert len(errors) == 0
        assert df.loc[0, "num_adults"] == 2
        assert df.loc[0, "total_amount"] == 15000
        
    finally:
        os.unlink(csv_file)