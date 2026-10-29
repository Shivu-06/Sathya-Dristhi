@echo off
title SatyaDrishti - BBMP Civic AI Platform
echo =========================================================================
echo       SatyaDrishti: Fake Complaint Detection Using Computer Vision
echo       Bruhat Bengaluru Mahanagara Palike (BBMP) Grievance Verification
echo =========================================================================
echo.
echo [1/3] Verifying Python and Node runtimes...
node -v
python --version
echo.
echo [2/3] Starting Python AI Multimodal Microservice on port 5001...
start "SatyaDrishti AI Service" cmd /k "cd /d %~dp0 && python ai_service\ai_engine.py"
echo.
echo [3/3] Starting Express Server on port 5000...
start "SatyaDrishti Web Server" cmd /k "cd /d %~dp0 && node server\server.js"
echo.
timeout /t 3 >nul
echo Opening SatyaDrishti Portal in browser...
start http://localhost:5000
echo.
echo SatyaDrishti is active!
echo Web Application: http://localhost:5000
echo AI Microservice: http://127.0.0.1:5001
echo =========================================================================
pause
