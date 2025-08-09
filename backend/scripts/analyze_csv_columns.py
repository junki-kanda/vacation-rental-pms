"""CSVファイルのカラムと実データを詳細に分析"""
import csv
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

csv_file = 'data/csv/20250807_170756_20250807_164342_ReservationTotalList-20250807160705.csv'

with open(csv_file, 'r', encoding='shift_jis') as f:
    reader = csv.DictReader(f)
    headers = reader.fieldnames
    
    print("=" * 80)
    print("CSVヘッダー詳細分析")
    print("=" * 80)
    print(f"カラム数: {len(headers)}")
    print("\nヘッダー一覧:")
    print("-" * 80)
    
    # 重要なカラムをグループ化して表示
    groups = {
        "基本情報": ["予約ID", "予約区分", "予約番号", "泊目"],
        "日付情報": ["チェックイン日", "チェックアウト日", "申込日", "泊数", "チェックイン時刻", "予約キャンセル日"],
        "施設情報": ["予約サイト名称", "部屋タイプ名称", "商品プラン名称", "商品プランコード", "室数"],
        "宿泊者情報": ["宿泊者氏名", "宿泊者氏名カタカナ", "電話番号", "郵便番号", "住所1", "メールアドレス"],
        "予約者情報": ["予約者氏名", "予約者氏名カタカナ", "会員番号", "法人情報"],
        "人数情報": ["大人人数計", "子供人数計", "幼児人数計"],
        "料金情報": ["料金合計額", "大人単価", "子供単価", "幼児単価", "大人合計額", "子供合計額", "幼児合計額", "その他明細", "その他合計額"],
        "ポイント情報": ["ポイント額", "ポイント割引額", "ポイント1額", "ポイント1名称", "ポイント2額", "ポイント2名称", "ポイント3額", "ポイント3名称", "ポイント4額", "ポイント4名称", "ポイント5額", "ポイント5名称"],
        "その他": ["備考1", "備考2", "メモ", "食事", "決済方法", "予約経路"]
    }
    
    for group_name, columns in groups.items():
        print(f"\n【{group_name}】")
        for col in columns:
            if col in headers:
                index = headers.index(col) + 1
                print(f"  {index:3}. {col}")
    
    # サンプルデータを表示
    print("\n" + "=" * 80)
    print("サンプルデータ（最初の3件）")
    print("=" * 80)
    
    # ファイルを最初から読み直し
    f.seek(0)
    reader = csv.DictReader(f)
    
    for i, row in enumerate(reader):
        if i >= 3:
            break
        
        print(f"\n--- 予約 {i+1} ---")
        print(f"予約ID: {row['予約ID']}")
        print(f"宿泊者氏名: {row['宿泊者氏名']}")
        print(f"部屋タイプ名称: {row['部屋タイプ名称']}")
        print(f"商品プラン名称: {row['商品プラン名称']}")
        
        # オプション関連のデータ
        print("\n[オプション関連]")
        print(f"食事: {row['食事']}")
        print(f"その他明細: {row['その他明細']}")
        print(f"その他合計額: {row['その他合計額']}")
        
        # 備考データ
        print("\n[備考関連]")
        print(f"備考1: {row['備考1'][:50] if row['備考1'] else ''}")
        print(f"備考2: {row['備考2'][:50] if row['備考2'] else ''}")
        print(f"メモ: {row['メモ'][:50] if row['メモ'] else ''}")
        
        # ポイント関連
        print("\n[ポイント関連]")
        for j in range(1, 6):
            point_amount = row.get(f'ポイント{j}額', '')
            point_name = row.get(f'ポイント{j}名称', '')
            if point_amount and point_amount != '0':
                print(f"ポイント{j}: {point_name} = {point_amount}")
    
    # 全データで使用されているカラムを分析
    print("\n" + "=" * 80)
    print("カラム使用状況分析")
    print("=" * 80)
    
    f.seek(0)
    reader = csv.DictReader(f)
    
    column_usage = {header: 0 for header in headers}
    total_rows = 0
    
    for row in reader:
        total_rows += 1
        for header in headers:
            if row[header] and row[header].strip() and row[header] != '0':
                column_usage[header] += 1
    
    print(f"\n総レコード数: {total_rows}")
    print("\nデータが入っているカラム（使用率順）:")
    sorted_usage = sorted(column_usage.items(), key=lambda x: x[1], reverse=True)
    
    for column, count in sorted_usage[:30]:  # 上位30カラムを表示
        usage_rate = (count / total_rows) * 100
        if usage_rate > 0:
            print(f"  {column:30} : {usage_rate:6.2f}% ({count}/{total_rows})")