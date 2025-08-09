@echo off
echo ============================================
echo Vacation Rental PMS - テスト起動
echo ============================================
echo.

echo [1/3] バックエンドサーバーを起動中...
cd backend
start cmd /k "echo Backend Server Starting... && python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 5 /nobreak > nul

echo [2/3] フロントエンドサーバーを起動中...
cd ..\frontend
start cmd /k "echo Frontend Server Starting... && npm run dev"

timeout /t 5 /nobreak > nul

echo [3/3] ブラウザを開いています...
start http://localhost:3000

echo.
echo ============================================
echo サーバーが起動しました！
echo.
echo Backend API: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo Frontend: http://localhost:3000
echo.
echo CSVファイルのアップロード:
echo 1. http://localhost:3000/sync にアクセス
echo 2. ReservationTotalList-20250807160705.csv をアップロード
echo.
echo または、backend\data\csv フォルダのCSVファイルを
echo 自動的に読み込むことも可能です。
echo ============================================
echo.
echo 終了するには全てのコマンドウィンドウを閉じてください。
pause