@echo off
title GM-COMPONENTS EV2 - Consola de Agentes con EV1
set "ROOT=%~dp0"
set "AGENT_PYTHON=%ROOT%agente\.venv\Scripts\python.exe"
echo ==========================================
echo GM-COMPONENTS EV2 - Consola de Agentes
echo ==========================================
echo.
echo Este script levantara automaticamente:
echo - Backend EV1 groq-proxy en http://localhost:8787
echo - Servicio EV2/EV3 FastAPI en http://localhost:8790
echo - Consola EV2 de agentes usando agente\.venv
echo.
echo Al cerrar esta consola se intentaran detener groq-proxy y FastAPI.
echo.
if not exist "%AGENT_PYTHON%" (
  echo ERROR: No se encontro el Python del entorno virtual:
  echo %AGENT_PYTHON%
  echo.
  echo Ejecuta primero instalar_dependencias_ev2.bat
  pause
  exit /b 1
)
if not exist "%ROOT%groq-proxy\node_modules" (
  echo ERROR: No se encontro groq-proxy\node_modules.
  echo Ejecuta primero instalar_dependencias_ev2.bat
  pause
  exit /b 1
)
cd /d "%ROOT%"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$root=$env:ROOT; " ^
  "$agentPython=$env:AGENT_PYTHON; " ^
  "$proxyPath=Join-Path $root 'groq-proxy'; " ^
  "$agentePath=Join-Path $root 'agente'; " ^
  "Write-Host 'Iniciando Streamlit dashboard EV3...'; " ^
  "$streamlit=Start-Process -FilePath $agentPython -ArgumentList '-m','streamlit','run','dashboard.py','--server.port','8501' -WorkingDirectory (Join-Path $root 'ev3_observability') -PassThru -NoNewWindow; " ^
  "Start-Sleep -Seconds 2; " ^
  "Write-Host 'Streamlit EV3 en http://localhost:8501'; " ^
  "Write-Host ''; " ^
  "Write-Host 'Iniciando groq-proxy EV1...'; " ^
  "$proxy=Start-Process -FilePath 'node' -ArgumentList 'server.js' -WorkingDirectory $proxyPath -PassThru -NoNewWindow; " ^
  "Start-Sleep -Seconds 3; " ^
  "try { Invoke-RestMethod 'http://localhost:8787/api/health' | Out-Null; Write-Host 'groq-proxy activo en http://localhost:8787'; } catch { Write-Host 'Advertencia: no se pudo validar health de groq-proxy.'; } " ^
  "Write-Host ''; " ^
  "Write-Host 'Iniciando FastAPI EV2/EV3 en background...'; " ^
  "$fastapi=Start-Process -FilePath $agentPython -ArgumentList '-m','uvicorn','app:app','--port','8790' -WorkingDirectory $agentePath -PassThru -NoNewWindow; " ^
  "Start-Sleep -Seconds 3; " ^
  "try { Invoke-RestMethod 'http://localhost:8790/health' | Out-Null; Write-Host 'FastAPI EV2/EV3 activo en http://localhost:8790'; } catch { Write-Host 'Advertencia: no se pudo validar health de FastAPI.'; } " ^
  "Write-Host ''; " ^
  "Write-Host 'Iniciando consola de agentes EV2...'; " ^
  "Write-Host 'Comandos utiles:'; " ^
  "Write-Host '  /faq tienen stock de rtx 4060'; " ^
  "Write-Host '  /rec quiero una grafica'; " ^
  "Write-Host '  salir'; " ^
  "Write-Host ''; " ^
  "Write-Host 'EV3 disponible en esta sesion:'; " ^
  "Write-Host '  http://localhost:8790/ev3/health'; " ^
  "Write-Host '  http://localhost:8790/ev3/traces'; " ^
  "Write-Host '  http://localhost:8787/api/ev3/health'; " ^
  "Write-Host '  http://localhost:8501 (Streamlit Dashboard)'; " ^
  "Write-Host ''; " ^
  "try { Set-Location $agentePath; & $agentPython 'main.py'; } finally { Write-Host ''; Write-Host 'Deteniendo servicios...'; if ($proxy -and -not $proxy.HasExited) { Stop-Process -Id $proxy.Id -Force -ErrorAction SilentlyContinue; } if ($fastapi -and -not $fastapi.HasExited) { Stop-Process -Id $fastapi.Id -Force -ErrorAction SilentlyContinue; } if ($streamlit -and -not $streamlit.HasExited) { Stop-Process -Id $streamlit.Id -Force -ErrorAction SilentlyContinue; } }"
echo Consola finalizada.
pause