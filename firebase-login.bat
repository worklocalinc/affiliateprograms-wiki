@echo off
echo ========================================
echo Firebase Login
echo ========================================
echo.
echo This will open your browser to sign in to Firebase.
echo Please complete the authentication in your browser.
echo.
pause

firebase login

echo.
if %errorlevel% equ 0 (
    echo ========================================
    echo Login successful!
    echo You can now run deploy.bat to deploy your site.
    echo ========================================
) else (
    echo Login failed. Please try again.
)
echo.
pause
