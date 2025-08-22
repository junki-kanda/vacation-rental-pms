"""
ねっぱんCSVダウンロードの定期実行スケジューラー
"""

import os
import time
import schedule
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# fetch_csv モジュールをインポート
from fetch_csv import main as fetch_csv_main

# 環境変数の読み込み
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./backend/logs/scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ログディレクトリの作成
Path('./backend/logs').mkdir(parents=True, exist_ok=True)


def scheduled_fetch():
    """スケジュール実行用の関数"""
    try:
        logger.info("=" * 50)
        logger.info("定期CSVダウンロードを開始します")
        
        # fetch_csv のメイン処理を実行
        result = fetch_csv_main(
            auto_sync=os.getenv("AUTO_SYNC_ENABLED", "true").lower() == "true",
            cleanup=os.getenv("AUTO_CLEANUP_ENABLED", "true").lower() == "true"
        )
        
        if result:
            logger.info(f"✅ 定期CSVダウンロード成功: {result}")
            
            # 成功通知（オプション）
            send_notification(
                subject="CSVダウンロード成功",
                message=f"ねっぱんからのCSVダウンロードが成功しました。\nファイル: {result}"
            )
        else:
            logger.error("❌ 定期CSVダウンロード失敗")
            
            # エラー通知（オプション）
            send_notification(
                subject="CSVダウンロード失敗",
                message="ねっぱんからのCSVダウンロードに失敗しました。ログを確認してください。",
                is_error=True
            )
            
    except Exception as e:
        logger.error(f"スケジュール実行エラー: {e}")
        
        # エラー通知
        send_notification(
            subject="スケジューラーエラー",
            message=f"スケジューラーでエラーが発生しました。\nエラー: {e}",
            is_error=True
        )


def send_notification(subject: str, message: str, is_error: bool = False):
    """
    メール通知を送信（オプション）
    
    Args:
        subject: 件名
        message: 本文
        is_error: エラー通知かどうか
    """
    # メール通知が設定されている場合のみ送信
    if not os.getenv("NOTIFICATION_EMAIL"):
        return
    
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        smtp_host = os.getenv("SMTP_HOST")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")
        to_email = os.getenv("NOTIFICATION_EMAIL")
        
        if not all([smtp_host, smtp_user, smtp_password, to_email]):
            logger.debug("メール通知設定が不完全です")
            return
        
        # メールメッセージの作成
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = to_email
        msg['Subject'] = f"[PMS] {subject}"
        
        # 本文
        body = f"""
        {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        {message}
        
        ---
        Vacation Rental PMS 自動通知
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # メール送信
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            
        logger.info(f"通知メール送信: {subject}")
        
    except Exception as e:
        logger.error(f"メール送信エラー: {e}")


def main():
    """メイン処理"""
    logger.info("スケジューラーを開始します")
    
    # スケジュール設定を環境変数から取得
    schedule_time = os.getenv("FETCH_CSV_SCHEDULE", "06:00")  # デフォルト: 朝6時
    
    # 毎日指定時刻に実行
    schedule.every().day.at(schedule_time).do(scheduled_fetch)
    
    logger.info(f"スケジュール設定: 毎日 {schedule_time} に実行")
    
    # 起動時に一度実行するかの設定
    if os.getenv("RUN_ON_STARTUP", "false").lower() == "true":
        logger.info("起動時実行を開始")
        scheduled_fetch()
    
    # スケジュールループ
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # 1分ごとにチェック
        except KeyboardInterrupt:
            logger.info("スケジューラーを停止します")
            break
        except Exception as e:
            logger.error(f"スケジューラーエラー: {e}")
            time.sleep(60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="CSVダウンロードスケジューラー")
    parser.add_argument("--once", action="store_true", help="一度だけ実行して終了")
    parser.add_argument("--test-notification", action="store_true", help="通知テストを実行")
    
    args = parser.parse_args()
    
    if args.test_notification:
        # 通知テスト
        send_notification(
            subject="テスト通知",
            message="これはテスト通知です。メール設定が正しく動作しています。"
        )
        print("✅ テスト通知を送信しました")
    elif args.once:
        # 一度だけ実行
        scheduled_fetch()
    else:
        # 通常のスケジュール実行
        main()