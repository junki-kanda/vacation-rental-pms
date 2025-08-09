@echo off
echo Starting Vacation Rental PMS Production Environment...

echo.
echo Building and starting all services...
docker-compose up -d --build

echo.
echo Waiting for services to be ready...
timeout /t 30 /nobreak

echo.
echo Running database migrations...
docker-compose exec backend alembic upgrade head

echo.
echo Production environment is running!
echo.
echo Frontend: http://localhost:3000
echo Backend API: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo To view logs: docker-compose logs -f
echo To stop: docker-compose down
echo.
pause