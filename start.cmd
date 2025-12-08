@echo off

echo ===== UPgradeing setuptools... =====
python -m pip install --upgrade setuptools || echo 注意：setuptools升级失败，但将继续执行后续步骤

echo.
echo ===== install requirements.txt... =====
python -m pip install -r requirements.txt || echo 注意：部分依赖安装可能失败，但将继续尝试启动应用

echo.
echo ===== start app.py... =====
python app.py