@echo off
REM StockSageAI Quick Deployment Script (Windows)
REM Usage: deploy.bat [platform] [app-name]
REM Platforms: docker, heroku, local

setlocal enabledelayedexpansion

set PLATFORM=%1
set APP_NAME=%2

if "%PLATFORM%"=="" set PLATFORM=docker
if "%APP_NAME%"=="" set APP_NAME=stocksageai

echo ===================================
echo StockSageAI Deployment Script
echo ===================================
echo Platform: %PLATFORM%
echo App Name: %APP_NAME%
echo.

if /i "%PLATFORM%"=="docker" (
    echo Building Docker image...
    docker build -t %APP_NAME%:latest .
    
    echo Starting Docker container...
    docker run -d -p 8501:8501 ^
      --name %APP_NAME% ^
      --restart unless-stopped ^
      %APP_NAME%:latest
    
    echo.
    echo Docker deployment complete!
    echo Access your app at: http://localhost:8501
    goto end
)

if /i "%PLATFORM%"=="heroku" (
    echo Logging into Heroku...
    call heroku login
    
    echo Creating Heroku app...
    call heroku create %APP_NAME%
    
    echo Deploying to Heroku...
    call git push heroku main
    
    echo.
    echo Heroku deployment complete!
    echo Access your app at: https://%APP_NAME%.herokuapp.com
    goto end
)

if /i "%PLATFORM%"=="local" (
    echo Running locally with Streamlit...
    call streamlit run StockSageAI/app.py
    goto end
)

echo Unknown platform: %PLATFORM%
echo.
echo Supported platforms:
echo   - docker   : Deploy using Docker
echo   - heroku   : Deploy to Heroku
echo   - local    : Run locally
echo.
echo Usage: %0 [platform] [app-name]

:end
echo.
echo ===================================
echo Deployment Guide:
echo See DEPLOYMENT.md for detailed instructions
echo See DEPLOYMENT_ALTERNATIVES.md for platform comparison
echo ===================================
