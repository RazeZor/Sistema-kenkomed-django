@echo off
echo =======================================
echo Iniciando instalacion del entorno...
echo =======================================

echo.
echo 1. Creando entorno virtual (carpeta 'env')...
python -m venv env

echo.
echo 2. Activando el entorno virtual...
call env\Scripts\activate.bat

echo.
echo 3. Instalando librerias desde requirements.txt...
pip install -r requirements.txt

echo.
echo =======================================
echo Instalacion completada con exito!
echo =======================================
echo.
echo Para empezar a trabajar, recuerda activar tu entorno ejecutando:
echo env\Scripts\activate
echo.
pause
