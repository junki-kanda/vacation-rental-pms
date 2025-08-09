"""インポートされたオプションデータを確認"""
import sqlite3
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

conn = sqlite3.connect('vacation_rental_pms.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=" * 80)
print("オプション情報の確認")
print("=" * 80)

# オプション情報があるデータを確認
cursor.execute("""
    SELECT 
        reservation_id, guest_name, 
        option_items, option_amount,
        point_amount, point_discount,
        adult_rate, child_rate, infant_rate,
        adult_amount, child_amount, infant_amount,
        postal_code, address, member_number
    FROM reservations 
    WHERE option_amount > 0 OR point_amount > 0 OR adult_rate > 0
    LIMIT 10
""")

rows = cursor.fetchall()
count = 0
for row in rows:
    count += 1
    print(f"\n【予約 {count}】")
    print(f"予約ID: {row['reservation_id']}, 宿泊者: {row['guest_name']}")
    
    # オプション情報
    if row['option_items']:
        print(f"オプション項目: {row['option_items']}")
    if row['option_amount'] and row['option_amount'] > 0:
        print(f"オプション料金: {row['option_amount']:,.0f}円")
    
    # ポイント情報
    if row['point_amount'] and row['point_amount'] > 0:
        print(f"ポイント利用: {row['point_amount']:,.0f}円")
    if row['point_discount'] and row['point_discount'] > 0:
        print(f"ポイント割引: {row['point_discount']:,.0f}円")
    
    # 料金詳細
    if row['adult_rate'] and row['adult_rate'] > 0:
        print(f"料金内訳:")
        print(f"  大人単価: {row['adult_rate']:,.0f}円 → 合計: {row['adult_amount']:,.0f}円")
    if row['child_rate'] and row['child_rate'] > 0:
        print(f"  子供単価: {row['child_rate']:,.0f}円 → 合計: {row['child_amount']:,.0f}円")
    if row['infant_rate'] and row['infant_rate'] > 0:
        print(f"  幼児単価: {row['infant_rate']:,.0f}円 → 合計: {row['infant_amount']:,.0f}円")
    
    # 住所情報
    if row['postal_code']:
        print(f"郵便番号: {row['postal_code']}")
    if row['address']:
        print(f"住所: {row['address'][:30]}...")
    if row['member_number']:
        print(f"会員番号: {row['member_number']}")

# 統計情報
print("\n" + "=" * 80)
print("データ統計")
print("=" * 80)

cursor.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN option_amount > 0 THEN 1 END) as with_options,
        COUNT(CASE WHEN point_amount > 0 THEN 1 END) as with_points,
        COUNT(CASE WHEN adult_rate > 0 THEN 1 END) as with_rate_detail,
        COUNT(CASE WHEN postal_code IS NOT NULL AND postal_code != '' THEN 1 END) as with_postal,
        COUNT(CASE WHEN address IS NOT NULL AND address != '' THEN 1 END) as with_address,
        COUNT(CASE WHEN member_number IS NOT NULL AND member_number != '' THEN 1 END) as with_member,
        SUM(option_amount) as total_option_amount,
        SUM(point_amount) as total_point_amount
    FROM reservations
""")

stats = cursor.fetchone()
print(f"総予約数: {stats['total']}件")
print(f"オプション付き: {stats['with_options']}件 ({stats['with_options']/stats['total']*100:.1f}%)")
print(f"ポイント利用: {stats['with_points']}件 ({stats['with_points']/stats['total']*100:.1f}%)")
print(f"料金詳細あり: {stats['with_rate_detail']}件 ({stats['with_rate_detail']/stats['total']*100:.1f}%)")
print(f"郵便番号あり: {stats['with_postal']}件 ({stats['with_postal']/stats['total']*100:.1f}%)")
print(f"住所あり: {stats['with_address']}件 ({stats['with_address']/stats['total']*100:.1f}%)")
print(f"会員番号あり: {stats['with_member']}件 ({stats['with_member']/stats['total']*100:.1f}%)")
if stats['total_option_amount']:
    print(f"\nオプション料金合計: {stats['total_option_amount']:,.0f}円")
if stats['total_point_amount']:
    print(f"ポイント利用合計: {stats['total_point_amount']:,.0f}円")

conn.close()