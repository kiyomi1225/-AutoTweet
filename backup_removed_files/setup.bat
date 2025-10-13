
@echo off
chcp 65001 > nul
echo ===============================================
echo Twitter自動運用システム - 初期セットアップ
echo ===============================================

cd /d "C:\Users\shiki\AutoTweet"

echo.
echo [1/4] ディレクトリ構造を作成中...
mkdir modules 2>nul
mkdir config 2>nul
mkdir config\ovpn 2>nul
mkdir data 2>nul
mkdir images 2>nul
mkdir logs 2>nul
mkdir chrome_profiles 2>nul

echo [2/4] Pythonファイルを作成中...
echo # -*- coding: utf-8 -*- > modules\__init__.py

echo [3/4] 必要なPythonパッケージをインストール中...
pip install pandas openpyxl selenium pyautogui psutil schedule requests opencv-python pillow

echo [4/4] logger_setup.pyのテストを実行中...
python modules\logger_setup.py