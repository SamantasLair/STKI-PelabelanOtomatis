@echo off
echo ===================================================
echo [RESTARTING FLASK SERVER]
echo ===================================================

echo [1/3] Menutup server lama yang berjalan pada port 5000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5000" ^| findstr "LISTENING"') do (
    echo Menutup PID %%a...
    taskkill /f /pid %%a >nul 2>&1
)

echo [2/3] Memulai server Flask baru...
start "" cmd /k "python TKI/app_web.py"

echo [3/3] Menunggu server siap...
timeout /t 3 /nobreak >nul

echo Membuka aplikasi di browser...
start http://127.0.0.1:5000

echo Done!
