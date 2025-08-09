@echo off
echo ============================================
echo ねっぱん予約データ同期
echo ============================================
echo.

cd /d "%~dp0\backend\scripts"

echo [1/2] ねっぱんからCSVをダウンロード中...
python neppan_reservation_sync.py
if errorlevel 1 (
    echo.
    echo エラー: CSVのダウンロードに失敗しました
    pause
    exit /b 1
)

echo.
echo [2/2] CSVファイルをデータベースに取り込み中...
cd ..
python -c "import requests; print(requests.post('http://localhost:8000/api/sync/upload', files={'file': open('data/csv/latest.csv', 'rb')}).json())" 2>nul
if errorlevel 1 (
    echo.
    echo 注意: APIでの自動取り込みはスキップされました（手動で同期画面から実行してください）
)

echo.
echo ============================================
echo 同期処理が完了しました
echo ダウンロードしたCSVは backend\data\csv に保存されています
echo ============================================
echo.
pause