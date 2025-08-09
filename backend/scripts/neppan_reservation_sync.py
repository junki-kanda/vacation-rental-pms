# 新しいコードファイル（fixed_script.py）を作成
"""
neppan_reservation_sync.py
  1) ねっぱん! 予約 CSV を DL
  2) Google Drive フォルダへアップロード
"""

from __future__ import annotations
import os
import sys
import datetime
import pathlib
import time
import logging
import random
import json
from typing import List, Optional, Callable

from playwright.sync_api import sync_playwright, Page, Browser, ElementHandle
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload
from dotenv import load_dotenv

# ─── 1. ロギング設定 ────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('neppan-sync')

# ─── 2. 環境変数読み込み ──────────────────────────────────────────
# スクリプトのディレクトリからの相対パスで.envを探す
script_dir = pathlib.Path(__file__).parent
backend_dir = script_dir.parent
project_root = backend_dir.parent

# 本番環境用の環境変数ファイル
ENV_FILE = "/var/secrets/neppan-env"
if pathlib.Path(ENV_FILE).exists():
    load_dotenv(ENV_FILE)
    logger.info(f"環境変数を {ENV_FILE} から読み込みました")
else:
    # ローカル環境: backend/.env を読み込む
    local_env = backend_dir / ".env"
    if local_env.exists():
        load_dotenv(local_env)
        logger.info(f"環境変数を {local_env} から読み込みました")
    else:
        logger.warning(".envファイルが見つかりません。環境変数が設定されていることを確認してください。")

# 環境変数設定（オプションのデフォルト値も提供）
HEADLESS = os.environ.get("HEADLESS", "true").lower() == "true"
TIMEOUT_SECONDS = int(os.environ.get("TIMEOUT_SECONDS", "90"))
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "5"))
INITIAL_RETRY_DELAY = int(os.environ.get("INITIAL_RETRY_DELAY", "5"))
TAKE_SCREENSHOT = os.environ.get("TAKE_SCREENSHOT", "true").lower() == "true"
SAVE_HTML = os.environ.get("SAVE_HTML", "true").lower() == "true"

def env(key: str) -> str:
    """必須環境変数を取得。無ければ STDERR に出して終了。"""
    val = os.environ.get(key)
    if not val:
        logger.error(f"[FATAL] 環境変数 '{key}' が設定されていません")
        sys.exit(1)
    return val

# 必須環境変数
NEPPAN_CODE = env("NEPPAN_CODE")
NEPPAN_USER = env("NEPPAN_USER")
NEPPAN_PASS = env("NEPPAN_PASS")
DRIVE_FOLDER_ID = env("DRIVE_FOLDER_ID")
SA_PATH = env("SA_FILE")                     # drive-sa-key のパス
SCOPES = ["https://www.googleapis.com/auth/drive"]

# ─── 3. 定数 ────────────────────────────────────────────────────
NEPPAN_URL = "https://www41.neppan.net/login.php"
RESERVATION_URL = "https://www41.neppan.net/reservationView.php"

# Cloud Runのファイルシステム対応
# 一時ディレクトリのパスを環境に応じて調整
if os.environ.get("K_SERVICE") or os.environ.get("K_REVISION"):
    # Cloud Run環境
    DL_DIR = pathlib.Path("/tmp/neppan_dl")
    DATA_DIR = pathlib.Path("/tmp/data/csv")
    logger.info("Cloud Run環境を検出しました - /tmpを使用します")
else:
    # ローカル環境: backend/data/csv に保存（APIと連携）
    DL_DIR = backend_dir / "data" / "csv"
    DATA_DIR = backend_dir / "data" / "csv"
    logger.info(f"ローカル環境を検出しました - {DL_DIR} を使用します")

# 確実にディレクトリを作成（存在すれば何もしない）
DL_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
DEBUG_DIR = DL_DIR / "debug"
DEBUG_DIR.mkdir(exist_ok=True)

logger.info(f"ダウンロードディレクトリ: {DL_DIR} (存在: {DL_DIR.exists()})")
logger.info(f"デバッグディレクトリ: {DEBUG_DIR} (存在: {DEBUG_DIR.exists()})")

# ─── 4. ヘルパー関数 ──────────────────────────────────────────
def retry_with_backoff(func: Callable, max_retries: int = MAX_RETRIES, initial_delay: int = INITIAL_RETRY_DELAY):
    """指数バックオフ付きの再試行ロジック（クラウド環境向け最適化）"""
    last_error = None
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            last_error = e
            logger.warning(f"試行 {attempt+1}/{max_retries} 失敗: {str(e)}")
            if attempt == max_retries - 1:
                break
            
            # より長い遅延と若干のランダム性を導入
            delay = initial_delay * (2 ** attempt) + random.uniform(0, 2)
            logger.info(f"{delay:.1f}秒後に再試行します")
            time.sleep(delay)
    
    # 全試行が失敗した場合
    logger.error(f"最大試行回数 {max_retries} に達しました。最後のエラー: {last_error}")
    raise last_error

def save_debug_artifacts(page: Page, error_name: str):
    """デバッグ用のスクリーンショットとHTMLを保存"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if TAKE_SCREENSHOT:
        screenshot_path = DEBUG_DIR / f"{timestamp}_{error_name}.png"
        try:
            page.screenshot(path=screenshot_path)
            logger.info(f"スクリーンショット保存: {screenshot_path}")
        except Exception as e:
            logger.warning(f"スクリーンショット保存中にエラー: {str(e)}")
    
    if SAVE_HTML:
        html_path = DEBUG_DIR / f"{timestamp}_{error_name}.html"
        try:
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(page.content())
            logger.info(f"HTML保存: {html_path}")
        except Exception as e:
            logger.warning(f"HTML保存中にエラー: {str(e)}")

def analyze_page_structure(page):
    """ページ構造を詳細に分析してログに記録"""
    try:
        structure = page.evaluate("""() => {
            // すべてのフォーム要素を取得
            const forms = Array.from(document.querySelectorAll('form')).map(f => ({
                id: f.id || '',
                action: f.action || '',
                method: f.method || '',
                inputs: Array.from(f.querySelectorAll('input')).length
            }));
            
            // ボタン要素の詳細
            const buttons = Array.from(document.querySelectorAll('input[type="button"], button')).map(b => ({
                tag: b.tagName,
                id: b.id || '',
                class: b.className || '',
                value: b.value || '',
                text: (b.textContent || '').trim(),
                isVisible: b.offsetParent !== null,
                boundingBox: {
                    x: b.getBoundingClientRect().x,
                    y: b.getBoundingClientRect().y,
                    width: b.getBoundingClientRect().width,
                    height: b.getBoundingClientRect().height
                }
            }));
            
            // iframe の有無
            const iframes = Array.from(document.querySelectorAll('iframe')).map(i => ({
                id: i.id || '',
                name: i.name || '',
                src: i.src || ''
            }));
            
            return { forms, buttons, iframes };
        }""")
        logger.info(f"ページ構造分析結果: {json.dumps(structure, indent=2)}")
        return structure
    except Exception as e:
        logger.warning(f"ページ構造分析中にエラー: {str(e)}")
        return None

def wait_for_selector_to_be_stable(page, selector, timeout=10000):
    """セレクタが安定して操作可能になるまで待機"""
    logger.info(f"セレクタ {selector} が安定するまで待機中...")
    try:
        if selector.startswith("//"):
            element = page.wait_for_selector(selector, timeout=timeout, state="visible")
        else:
            element = page.wait_for_selector(selector, timeout=timeout, state="visible")
        
        # 要素が動かなくなるまで少し待機
        time.sleep(1)
        return element
    except Exception as e:
        logger.warning(f"セレクタ {selector} の待機中にエラー: {str(e)}")
        return None

def launch_optimized_browser(playwright):
    """クラウド環境に最適化されたブラウザを起動"""
    browser_args = [
        "--no-sandbox",
        "--disable-dev-shm-usage",  # 共有メモリ不足対策
        "--disable-gpu",            # GPUハードウェア加速無効化
        "--disable-features=site-per-process",  # プロセス分離の無効化（メモリ削減）
        "--disable-extensions",     # 拡張機能無効化
        "--disable-setuid-sandbox", 
        "--single-process"          # シングルプロセスモードで実行
    ]
    return playwright.chromium.launch(
        headless=HEADLESS, 
        args=browser_args,
        timeout=TIMEOUT_SECONDS * 1000
    )

# ─── 5. CSV ダウンロード ──────────────────────────────────────
def fetch_csv() -> pathlib.Path:
    """複数セレクタ対応・エラーハンドリング強化済みのCSV取得処理"""
    logger.info("ねっぱん!からCSVをダウンロードします")
    
    with sync_playwright() as p:
        browser = launch_optimized_browser(p)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        # ブラウザログの収集
        page.on("console", lambda msg: logger.info(f"ブラウザコンソール [{msg.type}]: {msg.text}"))
        page.on("pageerror", lambda err: logger.error(f"ページエラー: {err}"))
        
        # ネットワークトラフィック監視
        page.on("request", lambda request: logger.debug(f"リクエスト: {request.method} {request.url}"))
        page.on("response", lambda response: logger.info(f"レスポンス: {response.status} {response.url}") if response.status >= 400 else None)
        page.on("requestfailed", lambda request: logger.warning(f"リクエスト失敗: {request.url}, {request.failure}"))
        
        try:
            # ログイン処理
            logger.info(f"ねっぱん!サイトにアクセス: {NEPPAN_URL}")
            page.goto(NEPPAN_URL, timeout=TIMEOUT_SECONDS * 1000)
            
            logger.info("ログイン情報を入力中...")
            page.fill("#clientCode", NEPPAN_CODE)
            page.fill("#loginId", NEPPAN_USER)
            page.fill("#password", NEPPAN_PASS)
            page.click("#LoginBtn")
            page.wait_for_load_state("networkidle")
            
            # ログイン成功の確認
            if page.url.find("login.php") != -1:
                logger.error("ログインに失敗した可能性があります")
                save_debug_artifacts(page, "login_failure")
                raise Exception("ログインに失敗しました。認証情報を確認してください")
            
            # 予約一覧ページへ直接遷移
            logger.info(f"予約一覧ページへ遷移: {RESERVATION_URL}")
            response = page.goto(RESERVATION_URL, timeout=TIMEOUT_SECONDS * 1000, wait_until="networkidle")
            if not response or response.status >= 400:
                logger.warning(f"ページ遷移に問題があります。ステータス: {response.status if response else 'None'}")
                save_debug_artifacts(page, "page_navigation_issue")
            
            # 追加の待機 - ページが完全にロードされたことを確認
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_load_state("networkidle")
            
            # コンテンツが完全にロードされたことを確認する追加チェック
            ready_check = page.evaluate("""() => {
                return document.readyState === 'complete' && 
                       !document.querySelector('.loading') &&
                       document.querySelectorAll('input[type="button"]').length > 0;
            }""")
            
            if not ready_check:
                logger.warning("ページが完全にロードされていない可能性があります")
                time.sleep(3)  # 追加の待機
            
            # ページ構造の詳細分析
            structure = analyze_page_structure(page)
            
            # 複数のCSVボタンセレクタを試行（優先順位順）
            csv_selectors = [
                "#CsvOut",                               # 元の実装
                "input[type='button'][value*='CSV']",    # value属性で「CSV」を含むボタン
                "input[onclick*='csv']",                 # onclickで「csv」を含むボタン
                "//input[contains(@value, 'CSV')]",      # XPathでのCSV文字列検索
                "//button[contains(., 'CSV')]",          # テキストでCSVを含むボタン
                "//input[contains(@onclick, 'csv')]",    # onclickでcsvを含む要素
                "input[type='button']"                   # 最後の手段：すべてのボタンを試行
            ]
            
            # ボタン検索ロジック
            csv_button = None
            found_element = None
            
            for selector in csv_selectors:
                logger.info(f"CSVボタンを探索中: {selector}")
                try:
                    # セレクタが操作可能になるまで待機
                    element = wait_for_selector_to_be_stable(page, selector)
                    if element:
                        # 要素の可視性と操作可能性を確認
                        is_visible = element.is_visible()
                        is_enabled = element.is_enabled()
                        logger.info(f"セレクタ {selector} の状態: 可視={is_visible}, 操作可能={is_enabled}")
                        
                        if is_visible and is_enabled:
                            csv_button = selector
                            found_element = element
                            break
                except Exception as e:
                    logger.warning(f"セレクタ {selector} の検証中にエラー: {str(e)}")
            
            if not found_element:
                # すべてのセレクタが失敗した場合、ページの状態を保存して詳細診断
                logger.error("CSVボタンが見つかりませんでした。ページ状態を保存します")
                save_debug_artifacts(page, "csv_button_not_found")
                
                # ページ上の全ボタン要素をログに記録（追加診断用）
                try:
                    buttons = page.evaluate("""() => {
                        const buttons = Array.from(document.querySelectorAll('input[type="button"], button'));
                        return buttons.map(b => ({
                            tag: b.tagName,
                            id: b.id || '',
                            class: b.className || '',
                            value: b.value || '',
                            text: (b.textContent || '').trim(),
                            onclick: b.getAttribute('onclick') || ''
                        }));
                    }""")
                    logger.info(f"ページ上のボタン要素: {json.dumps(buttons, indent=2)}")
                    
                    # ボタン要素が見つかった場合は最初のボタンを試す（最後の手段）
                    if buttons and len(buttons) > 0:
                        logger.info("最後の手段として最初のボタンを試行します")
                        # 最も可能性の高いボタンを特定（CSV関連のテキストや値を持つもの）
                        csv_candidates = [b for b in buttons if 'csv' in (b['value'] + b['text'] + b['onclick']).lower()]
                        if csv_candidates:
                            logger.info(f"CSV関連のボタンを発見: {csv_candidates[0]}")
                            target_button = csv_candidates[0]
                        else:
                            logger.info("CSV関連のボタンが見つからないため、最初のボタンを試行")
                            target_button = buttons[0]
                            
                        # IDがある場合はIDで、なければXPathで特定
                        if target_button['id']:
                            logger.info(f"ID '{target_button['id']}' でボタンを試行")
                            found_element = page.locator(f"#{target_button['id']}").first
                        else:
                            xpath = f"//input[@value='{target_button['value']}']" if target_button['value'] else "//input[@type='button'][1]"
                            logger.info(f"XPath '{xpath}' でボタンを試行")
                            found_element = page.locator(xpath).first
                    
                except Exception as e:
                    logger.warning(f"ボタン要素の列挙中にエラー: {str(e)}")
                
                if not found_element:
                    raise Exception("CSVボタンが見つかりません。セレクタの見直しが必要です")
            
            # CSVダウンロード処理
            logger.info(f"CSVボタン {csv_button if csv_button else '(最終手段)'} をクリック準備中...")
            # ダイアログ処理のセットアップ
            page.once("dialog", lambda d: d.accept())
            
            # スクロールして要素を確実に表示
            found_element.scroll_into_view_if_needed()
            time.sleep(1)  # スクロール完了を待機
            
            with page.expect_download(timeout=TIMEOUT_SECONDS * 1000) as dl:
                # 要素の中心をクリック
                found_element.click(force=True)
                logger.info("ダウンロードボタンをクリックしました")
            
            # ダウンロード完了を待機
            try:
                download = dl.value
                logger.info("ダウンロード開始を検出しました")
                
                # ディレクトリ確認
                logger.info(f"保存前のダウンロードディレクトリ確認: {DL_DIR} (存在: {DL_DIR.exists()})")
                
                # 念のためディレクトリを再作成
                if not DL_DIR.exists():
                    logger.warning("ダウンロードディレクトリが存在しないため再作成します")
                    DL_DIR.mkdir(parents=True, exist_ok=True)
                
                # ダウンロードファイルの保存
                csv_path = DL_DIR / f"ReservationTotalList-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
                
                # 絶対パスに変換
                csv_absolute_path = csv_path.absolute()
                logger.info(f"CSVの保存先絶対パス: {csv_absolute_path}")
                
                # ファイル保存
                download.save_as(csv_absolute_path)
                logger.info(f"CSVが保存されました: {csv_absolute_path} (存在: {csv_absolute_path.exists()})")
                
                # ファイルサイズの確認
                if csv_absolute_path.exists():
                    file_size = csv_absolute_path.stat().st_size
                    logger.info(f"CSVファイルサイズ: {file_size} バイト")
                else:
                    logger.error("CSVファイルが存在しません！")
                
                return csv_absolute_path
                
            except Exception as e:
                logger.error(f"ダウンロード処理中にエラー: {str(e)}")
                save_debug_artifacts(page, "download_error")
                raise Exception(f"CSVダウンロード中にエラーが発生しました: {str(e)}")
            
        except Exception as e:
            logger.error(f"CSV取得中にエラーが発生しました: {str(e)}")
            save_debug_artifacts(page, "csv_fetch_error")
            raise
        finally:
            browser.close()

# ─── 6. Drive アップロード ────────────────────────────────────
def upload_to_drive(fp: pathlib.Path):
    """Google Driveへのアップロード処理"""
    logger.info(f"Google Driveへのアップロードを開始: {fp.name}")
    
    try:
        # ファイルの存在確認
        if not fp.exists():
            raise FileNotFoundError(f"アップロード対象ファイルが存在しません: {fp}")
        
        logger.info(f"SA_PATH: {SA_PATH}")
        if not pathlib.Path(SA_PATH).exists():
            raise FileNotFoundError(f"サービスアカウントキーが存在しません: {SA_PATH}")
        
        # サービスアカウントキーのファイルサイズを確認
        sa_size = pathlib.Path(SA_PATH).stat().st_size
        logger.info(f"サービスアカウントキーファイルサイズ: {sa_size} バイト")
        
        # ファイル内容の最初の数バイトをログに表示（デバッグ用）
        with open(SA_PATH, 'r') as f:
            sa_content_preview = f.read(100)
            logger.info(f"SA_PATHの内容プレビュー: {sa_content_preview}...")
        
        # 認証情報の構築
        creds = service_account.Credentials.from_service_account_file(SA_PATH, scopes=SCOPES)
        drive = build("drive", "v3", credentials=creds, cache_discovery=False)
        
        logger.info(f"認証完了、アップロード中... DRIVE_FOLDER_ID: {DRIVE_FOLDER_ID}")
        
        # CSVファイルの内容確認（デバッグ用）
        with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
            csv_preview = f.read(100)
            logger.info(f"CSVファイル内容プレビュー: {csv_preview}...")
        
        media = MediaFileUpload(fp, mimetype="text/csv")
        file = drive.files().create(
            body={"name": fp.name, "parents": [DRIVE_FOLDER_ID]},
            media_body=media, 
            fields="id", 
            supportsAllDrives=True
        ).execute()
        
        logger.info(f"アップロード完了: {fp.name} (ID: {file.get('id')})")
        return file.get('id')
    except Exception as e:
        logger.error(f"Driveアップロード中にエラーが発生しました: {str(e)}")
        raise

# ─── 7. エントリポイント ──────────────────────────────────────
if __name__ == "__main__":
    try:
        logger.info("ねっぱん!同期プロセスを開始")
        # 再試行ロジックを組み込んだCSV取得
        csv_path = retry_with_backoff(fetch_csv)
        
        # Driveへアップロード
        file_id = upload_to_drive(csv_path)
        
        logger.info("同期プロセスが正常に完了しました")
        sys.exit(0)
    except Exception as e:
        logger.error(f"同期プロセス全体でエラーが発生しました: {str(e)}")
        sys.exit(1)
