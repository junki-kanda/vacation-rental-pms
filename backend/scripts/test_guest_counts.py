"""人数データの表示テスト"""

# このモジュールは、SQLite データベース内の宿泊者数統計を表示する
# スクリプトとして作成されました。pytest からインポートされた際に
# 不要な副作用を生じさせないよう、実行処理は ``main`` 関数に
# まとめ、モジュールインポート時には何も実行しないようにする。

from __future__ import annotations

import sqlite3
import sys
import os


def main() -> None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    conn = sqlite3.connect('vacation_rental_pms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 予約テーブルが存在しない環境では早期終了する
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='reservations'"
    )
    if cursor.fetchone() is None:
        print("reservations table not found; skipping statistics")
        conn.close()
        return

    print("=" * 80)
    print("人数データ表示テスト")
    print("=" * 80)

    # 統計情報を取得
    cursor.execute(
        '''
    SELECT
        COUNT(*) as total_reservations,
        SUM(num_adults) as total_adults,
        SUM(num_children) as total_children,
        SUM(num_infants) as total_infants,
        SUM(num_adults + num_children + num_infants) as total_all_guests,
        AVG(num_adults + num_children + num_infants) as avg_guests_per_reservation
    FROM reservations
        '''
    )

    stats = cursor.fetchone()
    print("\n【全体統計】")
    print(f"総予約数: {stats['total_reservations']}件")
    print(f"大人合計: {stats['total_adults']}名")
    print(f"子供合計: {stats['total_children']}名")
    print(f"幼児合計: {stats['total_infants']}名")
    print(f"全宿泊者合計: {stats['total_all_guests']}名")
    print(f"1予約あたり平均人数: {stats['avg_guests_per_reservation']:.2f}名")

    # 人数パターン別の集計
    cursor.execute(
        '''
    SELECT
        CASE
            WHEN num_children > 0 AND num_infants > 0 THEN '大人+子供+幼児'
            WHEN num_children > 0 THEN '大人+子供'
            WHEN num_infants > 0 THEN '大人+幼児'
            ELSE '大人のみ'
        END as guest_pattern,
        COUNT(*) as count
    FROM reservations
    GROUP BY guest_pattern
    ORDER BY count DESC
        '''
    )

    print("\n【宿泊パターン別集計】")
    for row in cursor.fetchall():
        print(f"{row['guest_pattern']}: {row['count']}件")

    # 人数別TOP10
    cursor.execute(
        '''
    SELECT
        reservation_id,
        guest_name,
        num_adults,
        num_children,
        num_infants,
        (num_adults + num_children + num_infants) as total_guests,
        check_in_date
    FROM reservations
    ORDER BY total_guests DESC
    LIMIT 10
        '''
    )

    print("\n【宿泊人数TOP10】")
    print("-" * 80)
    print(
        f"{'予約ID':<10} {'宿泊者名':<15} {'大人':>6} {'子供':>6} {'幼児':>6} {'合計':>6} {'チェックイン'}"
    )
    print("-" * 80)
    for row in cursor.fetchall():
        print(
            f"{row['reservation_id']:<10} {row['guest_name'][:15]:<15} "
            f"{row['num_adults']:>6} {row['num_children']:>6} {row['num_infants']:>6} "
            f"{row['total_guests']:>6} {row['check_in_date']}"
        )

    conn.close()

    print("\n" + "=" * 80)
    print("テスト完了")
    print("=" * 80)


if __name__ == '__main__':  # pragma: no cover - 手動スクリプトのため
    main()