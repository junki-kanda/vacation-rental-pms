@echo off
echo Starting Vacation Rental PMS Development Environment...

echo.
echo Starting services with Docker Compose...
docker-compose up -d db redis

echo.
echo Waiting for database to be ready...
timeout /t 10 /nobreak

echo.
echo Running database migrations...
docker-compose run --rm backend alembic upgrade head

echo.
echo Starting backend API...
start cmd /k "cd backend && uvicorn api.main:app --reload --host 0.0.0.0 --port 8000"

echo.
echo Starting frontend development server...
start cmd /k "cd frontend && npm run dev"

echo.
echo Development environment is starting up!
echo.
echo Frontend: http://localhost:3000
echo Backend API: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Press any key to continue...
pause