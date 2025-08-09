@echo off
echo ============================================
echo Installing backend dependencies...
echo ============================================

echo Updating pip...
python -m pip install --upgrade pip

echo.
echo Installing core dependencies...
pip install fastapi uvicorn[standard] python-multipart sqlalchemy alembic
pip install pydantic pydantic-settings python-dotenv

echo.
echo Fixing numpy and pandas compatibility...
pip uninstall numpy pandas -y
pip install numpy==1.24.3
pip install pandas==2.0.3

echo.
echo Installing other dependencies...
pip install openpyxl
pip install playwright
pip install google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2

echo.
echo Installing development tools...
pip install pytest pytest-asyncio

echo.
echo ============================================
echo Installation complete!
echo ============================================
pause