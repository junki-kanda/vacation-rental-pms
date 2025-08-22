"""
CSVパーサーの数値カラムマッピング - 改善提案テスト
現在の実装の改善点を特定し、将来の機能拡張をテスト
"""
import pytest
import pandas as pd
from api.services.parser import NeppanCSVParser
import tempfile
import os
import re


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


def enhanced_number_converter(value):
    """
    改善された数値変換関数の提案実装
    全角数字、日本の特殊フォーマットに対応
    """
    if pd.isna(value) or value == "":
        return None
    
    # 文字列に変換
    str_value = str(value).strip()
    
    # 全角数字を半角に変換
    str_value = str_value.translate(str.maketrans(
        '０１２３４５６７８９', '0123456789'
    ))
    
    # 通貨記号や単位を除去（拡張版）
    # 日本円関連
    str_value = re.sub(r'[¥￥円JPY]', '', str_value)
    # その他通貨
    str_value = re.sub(r'[$€£]', '', str_value) 
    # 単位
    str_value = re.sub(r'[人名様泊室件回]', '', str_value)
    # 括弧内の説明を除去
    str_value = re.sub(r'[（）()【】\[\]].*?[（）()【】\[\]]', '', str_value)
    str_value = re.sub(r'\(.*?\)', '', str_value)
    str_value = re.sub(r'（.*?）', '', str_value)
    
    # カンマを除去
    str_value = str_value.replace(',', '')
    
    # 複数のスペースを単一スペースに変換してから除去
    str_value = re.sub(r'\s+', '', str_value)
    
    # 空文字チェック
    if not str_value:
        return None
    
    # 数値変換を試行
    try:
        # 整数として試行
        if '.' not in str_value:
            return int(str_value)
        else:
            return float(str_value)
    except ValueError:
        return None


def test_improvement_full_width_numbers():
    """改善提案: 全角数字の対応テスト"""
    # 現在の実装では全角数字は変換されない
    test_cases = [
        ("２", 2),
        ("１０", 10),
        ("１２３", 123),
        ("１,２３４", 1234),
    ]
    
    for input_val, expected in test_cases:
        result = enhanced_number_converter(input_val)
        assert result == expected, f"Failed to convert {input_val} to {expected}, got {result}"


def test_improvement_japanese_units():
    """改善提案: 日本語単位の除去テスト"""
    test_cases = [
        ("2人", 2),
        ("15,000円", 15000),
        ("3名", 3),
        ("5泊", 5),
        ("10室", 10),
    ]
    
    for input_val, expected in test_cases:
        result = enhanced_number_converter(input_val)
        assert result == expected, f"Failed to convert {input_val} to {expected}, got {result}"


def test_improvement_parenthetical_removal():
    """改善提案: 括弧内説明の除去テスト"""
    test_cases = [
        ("15,000（税込）", 15000),
        ("2人（大人）", 2),
        ("10,000円(サービス料込み)", 10000),
        ("¥5,000【消費税別】", 5000),
    ]
    
    for input_val, expected in test_cases:
        result = enhanced_number_converter(input_val)
        assert result == expected, f"Failed to convert {input_val} to {expected}, got {result}"


def test_improvement_multiple_currency_symbols():
    """改善提案: 複数通貨記号の対応テスト"""
    test_cases = [
        ("$100", 100),
        ("€50", 50),
        ("£75", 75),
        ("￥10,000", 10000),
    ]
    
    for input_val, expected in test_cases:
        result = enhanced_number_converter(input_val)
        assert result == expected, f"Failed to convert {input_val} to {expected}, got {result}"


def test_improvement_complex_formatting():
    """改善提案: 複雑なフォーマットの処理テスト"""
    test_cases = [
        ("　２　人　", 2),  # 全角スペース
        ("１,２３４,５６７円（税込）", 1234567),
        ("￥ 10,000 JPY", 10000),
        ("2人（大人1名、子供1名）", 2),
    ]
    
    for input_val, expected in test_cases:
        result = enhanced_number_converter(input_val)
        assert result == expected, f"Failed to convert {input_val} to {expected}, got {result}"


def test_current_implementation_limitations(base_csv_headers):
    """現在の実装の制限事項を明確化するテスト"""
    headers = base_csv_headers + ["大人人数計", "子供人数計", "合計金額"]
    
    # 現在の実装では変換できないケース
    problematic_cases = [
        ["R001", "予約", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "田中太郎",
         "２", "１", "１５,０００円"],  # 全角数字・円記号
        ["R002", "予約", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "山田花子",
         "2人", "0人", "10,000（税込）"],  # 単位・括弧
        ["R003", "予約", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "佐藤次郎",
         " 3 ", "1 ", " 20000 "],  # 前後スペース
    ]
    
    csv_file = create_test_csv(headers, problematic_cases)
    
    try:
        parser = NeppanCSVParser(csv_file, encoding="utf-8")
        df, errors = parser.parse()
        
        assert len(errors) == 0
        assert len(df) == 3
        
        # 現在の実装での結果を記録（改善前の状態を確認）
        print("Current implementation results:")
        for i in range(3):
            adults = df.loc[i, "num_adults"]
            children = df.loc[i, "num_children"] 
            amount = df.loc[i, "total_amount"]
            print(f"Row {i}: adults={adults}, children={children}, amount={amount}")
        
        # Row 0: 全角数字は変換されない（NaN）
        assert pd.isna(df.loc[0, "num_adults"])
        assert pd.isna(df.loc[0, "num_children"])
        assert pd.isna(df.loc[0, "total_amount"])
        
        # Row 1: 単位付きは変換されない（NaN）
        assert pd.isna(df.loc[1, "num_adults"])
        assert pd.isna(df.loc[1, "num_children"])
        assert pd.isna(df.loc[1, "total_amount"])
        
        # Row 2: 前後スペースは処理される（trim済み）
        assert df.loc[2, "num_adults"] == 3
        assert df.loc[2, "num_children"] == 1
        assert df.loc[2, "total_amount"] == 20000
        
    finally:
        os.unlink(csv_file)


def test_error_handling_improvements(base_csv_headers):
    """改善提案: エラーハンドリングの強化テスト"""
    headers = base_csv_headers + ["大人人数計", "合計金額"]
    
    # 現在は無効値はNaNになるが、警告やログが出ない
    problematic_cases = [
        ["R001", "予約", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "田中太郎",
         "abc", "xyz123"],  # 完全に無効な値
        ["R002", "予約", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "山田花子",
         "2.5.3", "1000.000.50"],  # 複数小数点
    ]
    
    csv_file = create_test_csv(headers, problematic_cases)
    
    try:
        parser = NeppanCSVParser(csv_file, encoding="utf-8")
        df, errors = parser.parse()
        
        # 現在はパースエラーにならないが、改善すべき点：
        # 1. 無効値の詳細ログ
        # 2. 警告メッセージ
        # 3. データ品質レポート
        
        assert len(errors) == 0  # 現在の動作
        assert pd.isna(df.loc[0, "num_adults"])
        assert pd.isna(df.loc[0, "total_amount"])
        
        # 改善提案: 無効値の統計情報を取得できるようにする
        invalid_adults = df["num_adults"].isna().sum()
        invalid_amounts = df["total_amount"].isna().sum()
        
        print(f"Invalid adults count: {invalid_adults}")
        print(f"Invalid amounts count: {invalid_amounts}")
        
    finally:
        os.unlink(csv_file)


def test_column_mapping_flexibility(base_csv_headers):
    """改善提案: カラムマッピングの柔軟性向上テスト"""
    # 現在のマッピングは固定だが、設定可能にする提案
    
    # バリエーション1: 英語カラム名
    headers_en = [
        "ReservationID", "ReservationType", "CheckIn", "CheckOut", 
        "OTA", "RoomType", "GuestName", "Adults", "Children", "TotalAmount"
    ]
    
    # バリエーション2: 略称
    headers_short = [
        "予約ID", "予約区分", "チェックイン日", "チェックアウト日", 
        "予約サイト名称", "部屋タイプ名称", "宿泊者氏名", "大人数", "子供数", "金額"
    ]
    
    rows = [
        ["R001", "予約", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "田中太郎",
         "2", "1", "15000"]
    ]
    
    # 現在の実装では固定マッピングのため、これらは認識されない
    for headers_variant in [headers_en, headers_short]:
        csv_file = create_test_csv(headers_variant[:7], [row[:7] for row in rows])  # 必須カラムのみ
        
        try:
            parser = NeppanCSVParser(csv_file, encoding="utf-8")
            
            # 英語カラム名の場合は必須カラムエラーになる
            if headers_variant == headers_en:
                with pytest.raises(Exception):  # カラム不足エラー
                    df, errors = parser.parse()
            else:
                df, errors = parser.parse()
                # 数値カラムが存在しないので変換されない
                assert "num_adults" not in df.columns
                
        finally:
            os.unlink(csv_file)


def test_validation_improvements(base_csv_headers):
    """改善提案: バリデーション機能の強化テスト"""
    headers = base_csv_headers + ["大人人数計", "子供人数計", "合計金額"]
    
    # ビジネスロジック的に疑わしい値
    suspicious_cases = [
        ["R001", "予約", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "田中太郎",
         "0", "0", "0"],  # 人数0は疑わしい
        ["R002", "予約", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "山田花子", 
         "50", "20", "5"],  # 大人50人、金額5円は疑わしい
        ["R003", "予約", "2024/01/01", "2024/01/02", "Booking.com", "ダブルルーム", "佐藤次郎",
         "2", "1", "-1000"],  # 負の金額（キャンセル以外で）
    ]
    
    csv_file = create_test_csv(headers, suspicious_cases)
    
    try:
        parser = NeppanCSVParser(csv_file, encoding="utf-8")
        df, errors = parser.parse()
        
        assert len(errors) == 0  # 現在は技術的エラーのみ
        
        # 改善提案: ビジネスルールバリデーション
        # 1. 人数の妥当性チェック（0人、異常に多い人数）
        # 2. 金額の妥当性チェック（負の値、異常に高い/低い金額）
        # 3. 人数と金額の関係性チェック（人数に対して金額が少なすぎる等）
        
        # 現在の実装では全て有効値として処理される
        assert df.loc[0, "num_adults"] == 0
        assert df.loc[1, "num_adults"] == 50
        assert df.loc[2, "total_amount"] == -1000
        
        print("Business validation suggestions:")
        print("- Check for zero guests")
        print("- Check for unusually high guest counts")
        print("- Check for negative amounts (except cancellations)")
        print("- Check guest count vs amount relationship")
        
    finally:
        os.unlink(csv_file)


def test_performance_optimization_suggestions():
    """改善提案: パフォーマンス最適化のテスト"""
    # 現在の実装の最適化ポイント
    
    # 1. 数値変換の最適化
    # - pd.to_numeric()の前処理を最適化
    # - 正規表現の使用を最小限に
    # - vectorized操作の活用
    
    # 2. メモリ効率の改善
    # - 適切なデータ型の選択（int32 vs int64）
    # - 不要なカラムの早期削除
    
    test_data = [str(i) for i in range(1000)]
    
    # 現在の方式
    import time
    start_time = time.time()
    result1 = pd.Series(test_data).str.replace(",", "").str.replace("¥", "").str.replace("円", "").apply(pd.to_numeric, errors="coerce")
    time1 = time.time() - start_time
    
    # 最適化提案: 一括前処理
    start_time = time.time()
    series = pd.Series(test_data)
    series = series.str.replace(",", "", regex=False)
    series = series.str.replace("¥", "", regex=False) 
    series = series.str.replace("円", "", regex=False)
    result2 = pd.to_numeric(series, errors="coerce")
    time2 = time.time() - start_time
    
    print(f"Current method: {time1:.4f}s")
    print(f"Optimized method: {time2:.4f}s")
    print(f"Performance improvement: {(time1-time2)/time1*100:.1f}%")
    
    # 結果の同一性確認
    pd.testing.assert_series_equal(result1, result2)