@echo off
cd /d "%~dp0"
echo Stress Atlas: opening http://localhost:8000 (latest local files, browser caching off).
echo Keep this window open while presenting. Press Ctrl+C to stop.
start "" http://localhost:8000
python scripts\serve.py 8000
pause
