@echo off
chcp 65001 >nul
rem Testa o painel tambem no Firefox e no WebKit (motor do Safari), alem do Chrome.
rem Requer: Docker Desktop aberto e ter rodado o atualizar.bat ao menos uma vez (cria .venv e o banco).
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Rode primeiro o atualizar.bat.
  pause
  exit /b 1
)
docker info >nul 2>&1
if errorlevel 1 (
  echo Abra o Docker Desktop e rode de novo.
  pause
  exit /b 1
)
docker start pgtcc >nul 2>&1
:espera
docker exec pgtcc pg_isready -h 127.0.0.1 -U postgres >nul 2>&1
if errorlevel 1 (
  ping -n 2 127.0.0.1 >nul
  goto espera
)
echo Preparando Firefox e WebKit do Playwright ^(so na primeira vez^)...
".venv\Scripts\python.exe" -m playwright install firefox webkit
if errorlevel 1 goto erro
for %%N in (firefox webkit) do (
  echo.
  echo === %%N ===
  ".venv\Scripts\python.exe" testes\testar_front.py --navegador %%N
  if errorlevel 1 goto erro
  ".venv\Scripts\python.exe" testes\testar_usabilidade.py --navegador %%N
  if errorlevel 1 goto erro
)
echo.
echo Pronto: painel conferido no Firefox e no WebKit.
pause
exit /b 0

:erro
echo.
echo ERRO: algum teste falhou no navegador acima.
pause
exit /b 1
