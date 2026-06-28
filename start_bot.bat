@echo off
title Student AI Bot
color 0A
echo Bot ishga tushirilmoqda...
echo.

:: Virtual muhitni ishga tushirish va botni yoqish
call venv\Scripts\activate.bat
python bot.py

echo.
echo Bot to'xtatildi yoki xatolik yuz berdi.
pause
