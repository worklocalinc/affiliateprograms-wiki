@echo off
echo ========================================
echo AffiliatePrograms.wiki Deployment
echo ========================================
echo.

echo Step 1: Building production bundle...
call npm run build

if %errorlevel% neq 0 (
    echo Build failed! Please fix errors and try again.
    pause
    exit /b %errorlevel%
)

echo.
echo Step 2: Deploying to Firebase...
call firebase deploy

if %errorlevel% neq 0 (
    echo.
    echo Deployment failed!
    echo.
    echo If you see an authentication error, please run:
    echo   firebase login
    echo.
    echo Then run this script again.
    pause
    exit /b %errorlevel%
)

echo.
echo ========================================
echo Deployment successful!
echo Your site is live at:
echo https://afffiliate-wiki.web.app
echo ========================================
pause
