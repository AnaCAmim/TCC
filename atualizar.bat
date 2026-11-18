@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
set "CONTAINER=pgtcc"
set "BANCO=websig"
set "WEBSIG_CONTAINER=%CONTAINER%"
set "WEBSIG_BANCO=%BANCO%"
echo === WebSIG: carga, indicadores, dados do painel e testes ===
echo.

rem --- Pré-requisitos ---
where python >nul 2>&1
if errorlevel 1 (
  echo Python nao encontrado. Instale o Python 3 e rode de novo.
  goto erro
)
docker version >nul 2>&1
if errorlevel 1 (
  echo O Docker nao esta respondendo. Abra o Docker Desktop e rode de novo.
  goto erro
)
docker inspect %CONTAINER% >nul 2>&1
if errorlevel 1 (
  echo Criando o banco PostGIS ^(a primeira vez baixa a imagem, pode demorar^)...
  docker run --name %CONTAINER% -e POSTGRES_PASSWORD=tcc -p 127.0.0.1:5432:5432 -v pgtcc_data:/var/lib/postgresql/data -d postgis/postgis:16-3.4 >nul
  if errorlevel 1 goto erro
) else (
  docker start %CONTAINER% >nul
)
echo Aguardando o banco ficar pronto...
:espera
docker exec %CONTAINER% pg_isready -h 127.0.0.1 -U postgres >nul 2>&1
if errorlevel 1 (
  ping -n 2 127.0.0.1 >nul
  goto espera
)
docker exec %CONTAINER% createdb -h 127.0.0.1 -U postgres %BANCO% >nul 2>&1

rem --- 1. Conferência dos dados brutos ---
echo.
echo [1/5] Conferindo os dados brutos...
python pipeline\conferir.py
if errorlevel 1 goto erro

rem --- 2. Carga no PostGIS: numa transação só (-1); se um total não bater, aborta e o banco anterior fica intacto ---
echo.
echo [2/5] Carregando no PostGIS...
docker exec %CONTAINER% sh -c "rm -rf /websig && mkdir -p /websig"
docker cp sql %CONTAINER%:/websig/ >nul
if errorlevel 1 goto erro
docker cp dados %CONTAINER%:/websig/ >nul
if errorlevel 1 goto erro
docker exec -w /websig %CONTAINER% psql -h 127.0.0.1 -U postgres -d %BANCO% -v ON_ERROR_STOP=1 -q -1 -f sql/01_schema.sql -f sql/02_carga.sql
if errorlevel 1 goto erro

rem --- 3. Views dos indicadores ---
echo.
echo [3/5] Criando as views dos indicadores...
docker exec -w /websig %CONTAINER% psql -h 127.0.0.1 -U postgres -d %BANCO% -v ON_ERROR_STOP=1 -q -1 -f sql/03_views_indicadores.sql
if errorlevel 1 goto erro

rem --- 4. Exportação para o painel ---
echo.
echo [4/5] Exportando web\dados.json e web\dados.js...
python pipeline\exportar.py
if errorlevel 1 goto erro

rem --- 5. Testes ---
echo.
echo [5/5] Testando os dados e o painel...
python testes\testar_dados.py
if errorlevel 1 goto erro
if not exist ".venv\Scripts\python.exe" (
  echo Preparando o ambiente do teste do painel ^(Playwright, so na primeira vez^)...
  python -m venv .venv
  if errorlevel 1 goto erro
  ".venv\Scripts\python.exe" -m pip install -q playwright
  if errorlevel 1 goto erro
)
".venv\Scripts\python.exe" testes\testar_front.py
if errorlevel 1 goto erro
".venv\Scripts\python.exe" testes\testar_usabilidade.py
if errorlevel 1 goto erro

echo.
echo Pronto. Tudo conferido: 223 municipios ^| 10.344 casos ^| 2.055.832 mulheres.
echo Abra web\index.html com duplo clique, ou publique a pasta web\ num servidor.
goto fim

:erro
echo.
echo ERRO: o processo foi interrompido na etapa acima. Nada foi publicado.
pause
exit /b 1

:fim
echo.
pause
exit /b 0
