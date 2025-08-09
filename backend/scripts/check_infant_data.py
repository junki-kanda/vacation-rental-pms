"""CSVファイルの幼児データを確認"""
import csv
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

csv_file = 'data/csv/20250807_170756_20250807_164342_ReservationTotalList-20250807160705.csv'

# CSVファイルを読み込んで幼児データがあるか確認
with open(csv_file, 'r', encoding='shift_jis') as f:
    reader = csv.DictReader(f)
    
    count = 0
    for row in reader:
        infants = row.get('幼児人数計', '0')
        if infants and infants != '0' and infants != '':
            print(f'予約ID: {row["予約ID"]}, 大人: {row["大人人数計"]}, 子供: {row["子供人数計"]}, 幼児: {infants}')
            count += 1
            if count >= 5:
                break
    
    if count == 0:
        print('幼児データが含まれる予約は見つかりませんでした')
        print('\nサンプルデータ（最初の5件）:')
        # 最初から読み直し
        f.seek(0)
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= 5:
                break
            adults = row.get('大人人数計', '')
            children = row.get('子供人数計', '')
            infants = row.get('幼児人数計', '')
            print(f'予約ID: {row["予約ID"]}, 大人: {adults}, 子供: {children}, 幼児: {infants}')