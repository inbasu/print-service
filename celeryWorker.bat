@echo off
cd /d "C:\webpub\backend"
start cmd /c ".venv\Scripts\celery.exe -A core worker -P eventlet -l INFO --concurrency=10"