"""
ねっぱんから予約データCSVをダウンロードするスクリプト
"""

import os
import datetime
import pathlib
import logging
import shutil
from typing import Optional
from playwright.sync_api import sync_playwright, TimeoutError
from dotenv import load_dotenv

# プロジェクトのルートディレクトリから.envを読み込む
env_path = pathlib.Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 設定
NEPPAN_URL = "https://www41.neppan.net/login.php"  # ねっぱんログインURL

# CSVファイルの保存先（プロジェクトの設定に合わせる）
CSV_DIR = pathlib.Path(os.getenv("CSV_DIR", "./backend/data/csv"))
CSV_DIR.mkdir(parents=True, exist_ok=True)

# 一時ダウンロードディレクトリ
TEMP_DL_DIR = pathlib.Path("./backend/temp_downloads")
TEMP_DL_DIR.mkdir(parents=True, exist_ok=True)

def fetch_csv(headless: bool = True) -> Optional[pathlib.Path]:
    """
    ねっぱんから予約データCSVをダウンロード
    
    Args:
        headless: ブラウザをヘッドレスモードで実行するか
    
    Returns:
        保存したCSVファイルのパス、失敗時はNone
    """
    browser = None
    try:
        # 環境変数のチェック
        client_code = os.getenv("NEPPAN_CODE")
        login_id = os.getenv("NEPPAN_USER")
        password = os.getenv("NEPPAN_PASS")
        
        if not all([client_code, login_id, password]):
            logger.error("ねっぱんのログイン情報が環境変数に設定されていません")
            logger.error("必要な環境変数: NEPPAN_CODE, NEPPAN_USER, NEPPAN_PASS")
            return None
        
        logger.info("ねっぱんからCSVダウンロードを開始します")
        
        with sync_playwright() as p:
            # ブラウザ起動
            browser = p.chromium.launch(
                headless=headless,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            context = browser.new_context(
                accept_downloads=True,
                viewport={'width': 1920, 'height': 1080}
            )
            page = context.new_page()
            
            # ログインページへアクセス
            logger.info(f"ログインページへアクセス: {NEPPAN_URL}")
            page.goto(NEPPAN_URL, timeout=60000)
            page.wait_for_load_state("networkidle")
            
            # ログイン処理
            logger.info("ログイン処理を実行")
            page.fill("#clientCode", client_code)
            page.fill("#loginId", login_id)
            page.fill("#password", password)
            page.click("#LoginBtn")
            page.wait_for_load_state("networkidle", timeout=30000)
            
            # 予約一覧画面へ遷移
            logger.info("予約一覧画面へ遷移")
            page.click("text=予約管理")
            page.wait_for_timeout(2000)  # 待機
            page.click("text=予約一覧")
            page.wait_for_load_state("networkidle", timeout=30000)
            
            # CSV出力ボタンが表示されるまで待機
            logger.info("CSV出力ボタンを待機")
            page.wait_for_selector("#CsvOut", timeout=15000)
            
            # ダイアログ処理の準備（confirm型の場合）
            page.once("dialog", lambda dialog: dialog.accept())
            
            # CSVダウンロード実行
            logger.info("CSVダウンロードを実行")
            with page.expect_download(timeout=30000) as dl_info:
                page.click("#CsvOut")
            download = dl_info.value
            
            # ファイル名を生成（日付_時刻_reservations.csv）
            now = datetime.datetime.now()
            filename = f"{now.strftime('%Y%m%d_%H%M%S')}_reservations.csv"
            temp_path = TEMP_DL_DIR / filename
            
            # 一時ディレクトリに保存
            download.save_as(temp_path)
            logger.info(f"CSVを一時保存: {temp_path}")
            
            # 最終的な保存先にコピー
            final_path = CSV_DIR / filename
            shutil.copy2(temp_path, final_path)
            logger.info(f"✅ CSV保存完了: {final_path}")
            
            # 一時ファイルを削除
            temp_path.unlink()
            
            browser.close()
            return final_path
            
    except TimeoutError as e:
        logger.error(f"タイムアウトエラー: {e}")
        return None
    except Exception as e:
        logger.error(f"予期しないエラー: {e}")
        return None
    finally:
        if browser:
            browser.close()

def process_csv_to_database(csv_path: pathlib.Path) -> bool:
    """
    ダウンロードしたCSVファイルをデータベースに同期
    
    Args:
        csv_path: CSVファイルのパス
    
    Returns:
        成功時True、失敗時False
    """
    try:
        # APIサービスを使用してCSVを処理
        from api.services.sync_service import SyncService
        from api.database import SessionLocal
        from api.crud.sync_log import create_sync_log
        from api.schemas.sync_log import SyncLogCreate
        
        logger.info(f"CSVファイルの処理を開始: {csv_path}")
        
        # データベースセッションを作成
        db = SessionLocal()
        
        try:
            # 同期ログを作成
            sync_log = create_sync_log(
                db,
                SyncLogCreate(
                    sync_type="reservations",
                    file_name=csv_path.name,
                    status="processing"
                )
            )
            
            # SyncServiceを使用してCSVを処理
            sync_service = SyncService()
            result = sync_service.process_csv(str(csv_path), sync_log.id)
            
            if result:
                logger.info(f"✅ CSVファイルの処理完了: {result}")
                return True
            else:
                logger.error("CSVファイルの処理に失敗しました")
                return False
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"データベース同期エラー: {e}")
        return False


def cleanup_old_csv_files(keep_days: int = 7):
    """
    古いCSVファイルを削除
    
    Args:
        keep_days: 保持する日数
    """
    try:
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=keep_days)
        
        for csv_file in CSV_DIR.glob("*.csv"):
            file_time = datetime.datetime.fromtimestamp(csv_file.stat().st_mtime)
            if file_time < cutoff_date:
                csv_file.unlink()
                logger.info(f"古いCSVファイルを削除: {csv_file.name}")
                
    except Exception as e:
        logger.error(f"CSVファイルのクリーンアップエラー: {e}")


def main(auto_sync: bool = True, cleanup: bool = True):
    """
    メイン処理
    
    Args:
        auto_sync: ダウンロード後に自動的にデータベースに同期するか
        cleanup: 古いCSVファイルを削除するか
    """
    # CSVダウンロード
    csv_path = fetch_csv(headless=True)
    
    if csv_path:
        logger.info(f"CSVダウンロード成功: {csv_path}")
        
        # データベースへの自動同期
        if auto_sync:
            success = process_csv_to_database(csv_path)
            if success:
                logger.info("データベース同期完了")
            else:
                logger.error("データベース同期に失敗しました")
        
        # 古いファイルのクリーンアップ
        if cleanup:
            cleanup_old_csv_files()
            
        return csv_path
    else:
        logger.error("CSVダウンロードに失敗しました")
        return None


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="ねっぱんから予約データCSVをダウンロード")
    parser.add_argument("--no-sync", action="store_true", help="データベース同期をスキップ")
    parser.add_argument("--no-cleanup", action="store_true", help="古いファイルの削除をスキップ")
    parser.add_argument("--debug", action="store_true", help="ブラウザを表示モードで実行")
    
    args = parser.parse_args()
    
    # デバッグモードの設定
    if args.debug:
        # ブラウザを表示モードで実行
        result = fetch_csv(headless=False)
        if result:
            print(f"✅ ダウンロード完了: {result}")
    else:
        # 通常実行
        result = main(
            auto_sync=not args.no_sync,
            cleanup=not args.no_cleanup
        )
        if result:
            print(f"✅ 処理完了: {result}")
