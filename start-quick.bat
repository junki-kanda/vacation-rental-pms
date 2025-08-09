@echo off
echo ============================================
echo Vacation Rental PMS - Quick Start
echo ============================================
echo.

echo Starting Backend Server...
start cmd /k "cd backend && python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak > nul

echo Starting Frontend Server...
start cmd /k "cd frontend && npm run dev"

timeout /t 3 /nobreak > nul

echo Opening browser...
start http://localhost:3000

echo.
echo ============================================
echo Servers started!
echo.
echo Frontend: http://localhost:3000
echo Backend API: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo CSV file location: backend\data\csv\
echo Go to http://localhost:3000/sync to process CSV files
echo ============================================
pause