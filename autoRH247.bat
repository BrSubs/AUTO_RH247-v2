@echo off
setlocal EnableExtensions
cd /d "%~dp0"

:menu
cls
echo ========================================
echo              AutoRH247
echo ========================================
echo 1 - Buscar funcionario
echo 2 - Validar planilha
echo 3 - Processar planilha
echo 4 - Abrir interface grafica
echo 5 - Sair
echo.
choice /c 12345 /n /m "Escolha uma opcao: "

if errorlevel 5 goto fim
if errorlevel 4 goto gui
if errorlevel 3 goto processar
if errorlevel 2 goto validar
if errorlevel 1 goto buscar

:buscar
set "identificador="
set /p "identificador=Nome ou CPF: "
if not defined identificador goto menu
uv run autorh247 buscar "%identificador%"
pause
goto menu

:validar
uv run autorh247 validar
pause
goto menu

:processar
uv run autorh247 processar
pause
goto menu

:gui
start "AutoRH247" cmd /c "uv run pythonw -m autorh247.gui"
goto menu

:fim
endlocal
