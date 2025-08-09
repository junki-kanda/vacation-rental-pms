"""
データベースをクリーンアップして再インポートするスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api.models import Base, Reservation, Facility, SyncLog
from api.services.sync_service import SyncService
from api.services.simple_parser import SimpleCSVParser
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clear_database():
    """データベースをクリア"""
    db_path = Path("vacation_rental_pms.db")
    if db_path.exists():
        # セッションを作成
        engine = create_engine(f"sqlite:///{db_path}")
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # 予約データを全て削除
            deleted_count = session.query(Reservation).delete()
            session.commit()
            logger.info(f"削除した予約データ: {deleted_count}件")
            
            # 施設データも削除（オプション）
            # deleted_facilities = session.query(Facility).delete()
            # session.commit()
            # logger.info(f"削除した施設データ: {deleted_facilities}件")
            
            return True
        except Exception as e:
            logger.error(f"データベースクリアエラー: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    else:
        logger.warning("データベースファイルが見つかりません")
        return False

def find_latest_csv():
    """最新のCSVファイルを探す"""
    csv_dir = Path("../data/csv")
    if csv_dir.exists():
        csv_files = list(csv_dir.glob("*.csv"))
        if csv_files:
            # 最新のファイルを取得
            latest_file = max(csv_files, key=lambda f: f.stat().st_mtime)
            return latest_file
    
    # backend/data/csv ディレクトリも確認
    csv_dir = Path("data/csv")
    if csv_dir.exists():
        csv_files = list(csv_dir.glob("*.csv"))
        if csv_files:
            latest_file = max(csv_files, key=lambda f: f.stat().st_mtime)
            return latest_file
    
    return None

def reimport_with_correct_encoding(csv_path: Path):
    """正しいエンコーディングで再インポート"""
    logger.info(f"CSVファイルを再インポート: {csv_path}")
    
    # データベースセッション作成
    engine = create_engine("sqlite:///vacation_rental_pms.db")
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # 同期サービスを使用
    sync_service = SyncService()
    
    # 同期ログ作成
    sync_log = SyncLog(
        sync_type="reimport",
        file_name=csv_path.name,
        status="processing"
    )
    session.add(sync_log)
    session.commit()
    
    try:
        # 自動エンコーディング検出で同期処理
        result = sync_service.process_csv_sync(
            str(csv_path),
            sync_log.id,
            session,
            encoding=None  # 自動検出を使用
        )
        
        if result["success"]:
            logger.info(f"インポート成功:")
            logger.info(f"  - 検出エンコーディング: {result.get('detected_encoding', '不明')}")
            logger.info(f"  - 信頼度: {result.get('encoding_confidence', 0):.2%}")
            logger.info(f"  - 新規: {result['new_count']}件")
            logger.info(f"  - 更新: {result['updated_count']}件")
            logger.info(f"  - エラー: {result['error_count']}件")
            
            # サンプルデータを表示
            sample_reservations = session.query(Reservation).limit(5).all()
            print("\nインポート後のサンプルデータ:")
            for res in sample_reservations:
                print(f"  ID: {res.reservation_id}, 名前: {res.guest_name}, OTA: {res.ota_name}")
            
            return True
        else:
            logger.error(f"インポート失敗: {result.get('errors', [])}")
            return False
            
    except Exception as e:
        logger.error(f"再インポートエラー: {e}")
        return False
    finally:
        session.close()

def main():
    """メイン処理"""
    print("="*50)
    print("データベース再インポートツール")
    print("="*50)
    
    # 最新のCSVファイルを探す
    csv_file = find_latest_csv()
    if not csv_file:
        print("CSVファイルが見つかりません")
        return
    
    print(f"\n使用するCSVファイル: {csv_file.name}")
    print(f"ファイルサイズ: {csv_file.stat().st_size / 1024:.2f} KB")
    
    # エンコーディングをプレビュー
    parser = SimpleCSVParser(str(csv_file), encoding=None)
    data, errors = parser.parse()
    
    print(f"\n検出されたエンコーディング: {parser.detected_encoding}")
    print(f"信頼度: {parser.encoding_confidence:.2%}")
    print(f"データ行数: {len(data)}")
    
    # ユーザー確認
    response = input("\nデータベースをクリアして再インポートしますか？ (y/n): ")
    if response.lower() != 'y':
        print("キャンセルしました")
        return
    
    # データベースクリア
    print("\nデータベースをクリアしています...")
    if clear_database():
        print("データベースクリア完了")
    else:
        print("データベースクリア失敗")
        return
    
    # 再インポート
    print("\n正しいエンコーディングで再インポートしています...")
    if reimport_with_correct_encoding(csv_file):
        print("\n再インポート完了！")
    else:
        print("\n再インポート失敗")

if __name__ == "__main__":
    main()