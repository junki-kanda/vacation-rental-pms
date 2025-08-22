"""
CSVパーサーの数値カラムマッピング - エッジケーステスト
日本特有のフォーマットや特殊ケースのテスト
"""
import pytest
import pandas as pd
from api.services.parser import NeppanCSVParser
import tempfile
import os


def create_test_csv(headers, rows, encoding="utf-8"):
    """テスト用CSVファイルを作成"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding=encoding, suffix='.csv') as f:
        # ヘッダー行
        f.write(','.join(headers) + '\n')
        # データ行
        for row in rows:
            f.write(','.join(str(cell) for cell in row) + '\n')
        return f.name


@pytest.fixture
def base_csv_headers():
    """基本的なCSVヘッダー（必須カラム含む）"""
    return [
        "予約ID", "予約区分", "チェックイン日", "チェックアウト日", 
        "予約サイト名称", "部屋タイプ名称", "宿泊者氏名"
    ]


def test_japanese_full_width_numbers(base_csv_headers):
    """全角数字の処理テスト"""
    headers = base_csv_headers + ["大人人数計", "子供人数計", "合計金額"]
    rows = [
        ["R001", "予約", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "田中太郎",
         "２", "１", "１５０００"]  # 全角数字
    ]
    
    csv_file = create_test_csv(headers, rows)
    
    try:
        parser = NeppanCSVParser(csv_file, encoding="utf-8")
        df, errors = parser.parse()
        
        assert len(errors) == 0
        # 全角数字は現在のロジックでは変換されない（NaNになる）
        # これは改善の余地があるポイント
        assert pd.isna(df.loc[0, "num_adults"])
        assert pd.isna(df.loc[0, "num_children"])
        assert pd.isna(df.loc[0, "total_amount"])
        
    finally:
        os.unlink(csv_file)


def test_japanese_comma_separator(base_csv_headers):
    """日本の万単位カンマの処理テスト"""
    headers = base_csv_headers + ["合計金額", "手数料", "純売上"]
    rows = [
        ["R001", "予約", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "田中太郎",
         "1,234,567", "123,456", "1,111,111"]
    ]
    
    csv_file = create_test_csv(headers, rows)
    
    try:
        parser = NeppanCSVParser(csv_file, encoding="utf-8")
        df, errors = parser.parse()
        
        assert len(errors) == 0
        assert df.loc[0, "total_amount"] == 1234567
        assert df.loc[0, "commission"] == 123456
        assert df.loc[0, "net_amount"] == 1111111
        
    finally:
        os.unlink(csv_file)


def test_decimal_values(base_csv_headers):
    """小数点を含む値のテスト（料金の詳細計算等）"""
    headers = base_csv_headers + ["合計金額", "手数料", "純売上"]
    rows = [
        ["R001", "予約", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "田中太郎",
         "15000.50", "1500.05", "13500.45"]
    ]
    
    csv_file = create_test_csv(headers, rows)
    
    try:
        parser = NeppanCSVParser(csv_file, encoding="utf-8")
        df, errors = parser.parse()
        
        assert len(errors) == 0
        assert df.loc[0, "total_amount"] == 15000.50
        assert df.loc[0, "commission"] == 1500.05
        assert df.loc[0, "net_amount"] == 13500.45
        
    finally:
        os.unlink(csv_file)


def test_mixed_currency_formats(base_csv_headers):
    """混在する通貨フォーマットのテスト"""
    headers = base_csv_headers + ["合計金額", "手数料", "純売上"]
    rows = [
        ["R001", "予約", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "田中太郎",
         "￥15,000", "¥1,500円", "13500JPY"],
        ["R002", "予約", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "山田花子",
         "15000円", "1500YEN", "¥13,500"]
    ]
    
    csv_file = create_test_csv(headers, rows)
    
    try:
        parser = NeppanCSVParser(csv_file, encoding="utf-8")
        df, errors = parser.parse()
        
        assert len(errors) == 0
        assert len(df) == 2
        
        # 1行目
        assert df.loc[0, "total_amount"] == 15000
        assert df.loc[0, "commission"] == 1500
        # "JPY"は除去されないので、NaNになる可能性がある
        
        # 2行目  
        assert df.loc[1, "total_amount"] == 15000
        # "YEN"は除去されないので、NaNになる可能性がある
        assert df.loc[1, "net_amount"] == 13500
        
    finally:
        os.unlink(csv_file)


def test_scientific_notation(base_csv_headers):
    """科学的記法の数値テスト"""
    headers = base_csv_headers + ["合計金額"]
    rows = [
        ["R001", "予約", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "田中太郎",
         "1.5e4"]  # 15000
    ]
    
    csv_file = create_test_csv(headers, rows)
    
    try:
        parser = NeppanCSVParser(csv_file, encoding="utf-8")
        df, errors = parser.parse()
        
        assert len(errors) == 0
        assert df.loc[0, "total_amount"] == 15000.0
        
    finally:
        os.unlink(csv_file)


def test_percentage_values(base_csv_headers):
    """パーセンテージ記号を含む値のテスト"""
    headers = base_csv_headers + ["手数料"]
    rows = [
        ["R001", "予約", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "田中太郎",
         "15%"]
    ]
    
    csv_file = create_test_csv(headers, rows)
    
    try:
        parser = NeppanCSVParser(csv_file, encoding="utf-8")
        df, errors = parser.parse()
        
        assert len(errors) == 0
        # "%"記号は除去されないので、NaNになる
        assert pd.isna(df.loc[0, "commission"])
        
    finally:
        os.unlink(csv_file)


def test_very_large_numbers(base_csv_headers):
    """非常に大きな数値のテスト"""
    headers = base_csv_headers + ["合計金額"]
    rows = [
        ["R001", "予約", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "田中太郎",
         "999999999999"]  # 12桁
    ]
    
    csv_file = create_test_csv(headers, rows)
    
    try:
        parser = NeppanCSVParser(csv_file, encoding="utf-8")
        df, errors = parser.parse()
        
        assert len(errors) == 0
        assert df.loc[0, "total_amount"] == 999999999999
        
    finally:
        os.unlink(csv_file)


def test_special_characters_in_numbers(base_csv_headers):
    """数値に特殊文字が含まれる場合のテスト"""
    headers = base_csv_headers + ["大人人数計", "合計金額"]
    rows = [
        ["R001", "予約", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "田中太郎",
         "2人", "15,000円（税込）"]
    ]
    
    csv_file = create_test_csv(headers, rows)
    
    try:
        parser = NeppanCSVParser(csv_file, encoding="utf-8")
        df, errors = parser.parse()
        
        assert len(errors) == 0
        # "人"や"（税込）"は除去されないので、NaNになる
        assert pd.isna(df.loc[0, "num_adults"])
        assert pd.isna(df.loc[0, "total_amount"])
        
    finally:
        os.unlink(csv_file)


def test_null_and_empty_variations(base_csv_headers):
    """NULL値や空値のバリエーションテスト"""
    headers = base_csv_headers + ["大人人数計", "子供人数計", "合計金額"]
    rows = [
        ["R001", "予約", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "田中太郎",
         "", "null", "N/A"],
        ["R002", "予約", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "山田花子",
         "NULL", "na", "-"],
        ["R003", "予約", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "佐藤次郎",
         "   ", "0", "未定"]
    ]
    
    csv_file = create_test_csv(headers, rows)
    
    try:
        parser = NeppanCSVParser(csv_file, encoding="utf-8")
        df, errors = parser.parse()
        
        assert len(errors) == 0
        assert len(df) == 3
        
        # 全て無効値またはNULL値なので、NaNになるはず
        for i in range(3):
            assert pd.isna(df.loc[i, "num_adults"]) or df.loc[i, "num_adults"] == 0
            if not (i == 2 and df.loc[i, "num_children"] == 0):  # 0は有効値
                assert pd.isna(df.loc[i, "num_children"])
            assert pd.isna(df.loc[i, "total_amount"])
        
    finally:
        os.unlink(csv_file)


def test_leading_zeros(base_csv_headers):
    """先頭ゼロを含む数値のテスト"""
    headers = base_csv_headers + ["大人人数計", "合計金額"]
    rows = [
        ["R001", "予約", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "田中太郎",
         "02", "015000"]
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


def test_multiple_decimal_points(base_csv_headers):
    """複数の小数点を含む無効な数値のテスト"""
    headers = base_csv_headers + ["合計金額"]
    rows = [
        ["R001", "予約", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "田中太郎",
         "15.000.50"]
    ]
    
    csv_file = create_test_csv(headers, rows)
    
    try:
        parser = NeppanCSVParser(csv_file, encoding="utf-8")
        df, errors = parser.parse()
        
        assert len(errors) == 0
        # 無効な数値フォーマットなので、NaNになるはず
        assert pd.isna(df.loc[0, "total_amount"])
        
    finally:
        os.unlink(csv_file)


def test_numbers_with_spaces(base_csv_headers):
    """数値の間にスペースがある場合のテスト"""
    headers = base_csv_headers + ["合計金額"]
    rows = [
        ["R001", "予約", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "田中太郎",
         "15 000"]  # スペース区切り（欧州式）
    ]
    
    csv_file = create_test_csv(headers, rows)
    
    try:
        parser = NeppanCSVParser(csv_file, encoding="utf-8")
        df, errors = parser.parse()
        
        assert len(errors) == 0
        # スペースは除去されないので、NaNになる
        assert pd.isna(df.loc[0, "total_amount"])
        
    finally:
        os.unlink(csv_file)


def test_range_values(base_csv_headers):
    """範囲を示す値のテスト（"2-3人"等）"""
    headers = base_csv_headers + ["大人人数計"]
    rows = [
        ["R001", "予約", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "田中太郎",
         "2-3"]
    ]
    
    csv_file = create_test_csv(headers, rows)
    
    try:
        parser = NeppanCSVParser(csv_file, encoding="utf-8")
        df, errors = parser.parse()
        
        assert len(errors) == 0
        # ハイフンを含む値は無効なので、NaNになる
        assert pd.isna(df.loc[0, "num_adults"])
        
    finally:
        os.unlink(csv_file)


def test_calculation_expressions(base_csv_headers):
    """計算式が含まれる場合のテスト"""
    headers = base_csv_headers + ["合計金額"]
    rows = [
        ["R001", "予約", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "田中太郎",
         "10000+5000"]
    ]
    
    csv_file = create_test_csv(headers, rows)
    
    try:
        parser = NeppanCSVParser(csv_file, encoding="utf-8")
        df, errors = parser.parse()
        
        assert len(errors) == 0
        # 計算式は評価されずに無効値として扱われる
        assert pd.isna(df.loc[0, "total_amount"])
        
    finally:
        os.unlink(csv_file)