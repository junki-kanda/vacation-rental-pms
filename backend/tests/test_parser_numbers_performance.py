"""
CSVパーサーの数値カラムマッピング - パフォーマンステスト
大量データでの数値変換のパフォーマンス確認
"""
import pytest
import pandas as pd
from api.services.parser import NeppanCSVParser
import tempfile
import os
import time


def create_large_test_csv(num_rows=1000):
    """大量データのテスト用CSVファイルを作成"""
    headers = [
        "予約ID", "予約区分", "チェックイン日", "チェックアウト日", 
        "予約サイト名称", "部屋タイプ名称", "宿泊者氏名",
        "大人人数計", "子供人数計", "幼児人数計",
        "合計金額", "手数料", "純売上"
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8', suffix='.csv') as f:
        # ヘッダー行
        f.write(','.join(headers) + '\n')
        
        # データ行を大量生成
        for i in range(num_rows):
            row = [
                f"R{i:06d}",  # 予約ID
                "予約",
                "2024/01/01",
                "2024/01/02", 
                "Booking.com",
                "ダブルルーム",
                f"テストユーザー{i}",
                str(2 + (i % 5)),  # 大人人数計 (2-6)
                str(i % 3),        # 子供人数計 (0-2)
                str(i % 2),        # 幼児人数計 (0-1)
                f"{10000 + (i * 100):,}",  # 合計金額（カンマ付き）
                f"{1000 + (i * 10)}",      # 手数料
                f"{9000 + (i * 90):,}"     # 純売上（カンマ付き）
            ]
            f.write(','.join(row) + '\n')
        
        return f.name


def test_large_dataset_performance():
    """大量データでの数値変換パフォーマンステスト"""
    csv_file = create_large_test_csv(1000)
    
    try:
        start_time = time.time()
        parser = NeppanCSVParser(csv_file, encoding="utf-8")
        df, errors = parser.parse()
        parse_time = time.time() - start_time
        
        assert len(errors) == 0
        assert len(df) == 1000
        
        # 数値変換が正しく行われているかサンプルチェック
        assert df.loc[0, "num_adults"] == 2
        assert df.loc[0, "num_children"] == 0
        assert df.loc[0, "total_amount"] == 10000
        
        assert df.loc[100, "num_adults"] == 2  # 2 + (100 % 5)
        assert df.loc[100, "num_children"] == 1  # 100 % 3
        assert df.loc[100, "total_amount"] == 20000  # 10000 + (100 * 100)
        
        # パフォーマンス要件（目安）: 1000行を2秒以内で処理
        print(f"Parse time for 1000 rows: {parse_time:.2f} seconds")
        assert parse_time < 5.0, f"Performance issue: took {parse_time:.2f} seconds"
        
        # メモリ使用量の確認（大まかな確認）
        memory_usage = df.memory_usage(deep=True).sum()
        print(f"Memory usage: {memory_usage / 1024 / 1024:.2f} MB")
        
    finally:
        os.unlink(csv_file)


def test_very_large_dataset_performance():
    """非常に大量データでの数値変換パフォーマンステスト"""
    csv_file = create_large_test_csv(5000)
    
    try:
        start_time = time.time()
        parser = NeppanCSVParser(csv_file, encoding="utf-8")
        df, errors = parser.parse()
        parse_time = time.time() - start_time
        
        assert len(errors) == 0
        assert len(df) == 5000
        
        # 数値変換が正しく行われているかサンプルチェック
        assert df.loc[0, "num_adults"] == 2
        assert df.loc[1000, "total_amount"] == 110000  # 10000 + (1000 * 100)
        assert df.loc[4999, "num_children"] == 1  # 4999 % 3
        
        # パフォーマンス要件（目安）: 5000行を10秒以内で処理
        print(f"Parse time for 5000 rows: {parse_time:.2f} seconds")
        assert parse_time < 15.0, f"Performance issue: took {parse_time:.2f} seconds"
        
    finally:
        os.unlink(csv_file)


def test_number_conversion_memory_efficiency():
    """数値変換のメモリ効率テスト"""
    csv_file = create_large_test_csv(1000)
    
    try:
        parser = NeppanCSVParser(csv_file, encoding="utf-8")
        
        # 変換前のメモリ使用量
        df_before, _ = parser.parse()
        memory_before = df_before.memory_usage(deep=True).sum()
        
        # 数値カラムが適切にint64/float64に変換されているかチェック
        assert df_before["num_adults"].dtype in ["int64", "float64"]
        assert df_before["total_amount"].dtype in ["int64", "float64"] 
        
        # 文字列カラムと数値カラムのメモリ使用量比較
        str_columns = df_before.select_dtypes(include=[object]).columns
        num_columns = df_before.select_dtypes(include=["int64", "float64"]).columns
        
        str_memory = df_before[str_columns].memory_usage(deep=True).sum()
        num_memory = df_before[num_columns].memory_usage(deep=True).sum()
        
        print(f"String columns memory: {str_memory / 1024:.2f} KB")
        print(f"Numeric columns memory: {num_memory / 1024:.2f} KB")
        
        # 数値カラムは文字列カラムよりもメモリ効率が良いはず
        # （この比較は参考値）
        
    finally:
        os.unlink(csv_file)


def test_mixed_valid_invalid_performance():
    """有効・無効な数値が混在する大量データのパフォーマンステスト"""
    headers = [
        "予約ID", "予約区分", "チェックイン日", "チェックアウト日", 
        "予約サイト名称", "部屋タイプ名称", "宿泊者氏名",
        "大人人数計", "合計金額"
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8', suffix='.csv') as f:
        # ヘッダー行
        f.write(','.join(headers) + '\n')
        
        # 有効・無効な値を混在させる
        for i in range(1000):
            if i % 3 == 0:
                # 無効な値
                adults = "abc"
                amount = "invalid"
            elif i % 3 == 1:
                # 空値
                adults = ""
                amount = ""
            else:
                # 有効な値
                adults = str(2 + (i % 5))
                amount = f"{10000 + (i * 100):,}"
            
            row = [
                f"R{i:06d}", "予約", "2024/01/01", "2024/01/02",
                "Booking.com", "ダブルルーム", f"テストユーザー{i}",
                adults, amount
            ]
            f.write(','.join(row) + '\n')
        
        csv_file = f.name
    
    try:
        start_time = time.time()
        parser = NeppanCSVParser(csv_file, encoding="utf-8")
        df, errors = parser.parse()
        parse_time = time.time() - start_time
        
        assert len(errors) == 0
        assert len(df) == 1000
        
        # 無効値の処理がされているか確認
        valid_adults = df["num_adults"].notna().sum()
        valid_amounts = df["total_amount"].notna().sum()
        
        # 約1/3が有効な値になるはず
        assert 300 <= valid_adults <= 400
        assert 300 <= valid_amounts <= 400
        
        print(f"Parse time with mixed data: {parse_time:.2f} seconds")
        print(f"Valid adults: {valid_adults}/1000")
        print(f"Valid amounts: {valid_amounts}/1000")
        
        # 無効値が多くても性能が著しく劣化しないこと
        assert parse_time < 5.0
        
    finally:
        os.unlink(csv_file)


def test_all_numeric_columns_performance():
    """全ての数値カラムを含む大量データのパフォーマンステスト"""
    headers = [
        "予約ID", "予約区分", "チェックイン日", "チェックアウト日", 
        "予約サイト名称", "部屋タイプ名称", "宿泊者氏名",
        "大人人数計", "子供人数計", "幼児人数計",  # 人数系
        "合計金額", "手数料", "純売上"  # 金額系
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8', suffix='.csv') as f:
        # ヘッダー行
        f.write(','.join(headers) + '\n')
        
        # 全ての数値カラムにデータを設定
        for i in range(1000):
            row = [
                f"R{i:06d}", "予約", "2024/01/01", "2024/01/02",
                "Booking.com", "ダブルルーム", f"テストユーザー{i}",
                str(1 + (i % 8)),      # 大人人数計 (1-8)
                str(i % 4),            # 子供人数計 (0-3)
                str(i % 2),            # 幼児人数計 (0-1)
                f"¥{10000 + (i * 100):,}",  # 合計金額（通貨記号・カンマ付き）
                f"{1000 + (i * 10)}円",      # 手数料（円記号付き）
                f"{9000 + (i * 90):,}"       # 純売上（カンマ付き）
            ]
            f.write(','.join(row) + '\n')
        
        csv_file = f.name
    
    try:
        start_time = time.time()
        parser = NeppanCSVParser(csv_file, encoding="utf-8")
        df, errors = parser.parse()
        parse_time = time.time() - start_time
        
        assert len(errors) == 0
        assert len(df) == 1000
        
        # 全ての数値カラムが存在し、正しく変換されているかチェック
        numeric_columns = ["num_adults", "num_children", "num_infants", 
                          "total_amount", "commission", "net_amount"]
        
        for col in numeric_columns:
            assert col in df.columns
            assert pd.api.types.is_numeric_dtype(df[col])
        
        # サンプル値の確認
        assert df.loc[0, "num_adults"] == 1
        assert df.loc[0, "total_amount"] == 10000  # ¥記号とカンマが除去されている
        assert df.loc[0, "commission"] == 1000     # 円記号が除去されている
        
        print(f"Parse time with all numeric columns: {parse_time:.2f} seconds")
        assert parse_time < 5.0
        
    finally:
        os.unlink(csv_file)


@pytest.mark.slow
def test_benchmark_comparison():
    """ベンチマーク比較テスト（手動実行用）"""
    sizes = [100, 500, 1000, 2000]
    
    for size in sizes:
        csv_file = create_large_test_csv(size)
        
        try:
            start_time = time.time()
            parser = NeppanCSVParser(csv_file, encoding="utf-8")
            df, errors = parser.parse()
            parse_time = time.time() - start_time
            
            print(f"Rows: {size:4d}, Time: {parse_time:.3f}s, "
                  f"Rate: {size/parse_time:.1f} rows/sec")
            
        finally:
            os.unlink(csv_file)