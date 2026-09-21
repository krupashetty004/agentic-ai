@echo off
setlocal
set "ROOT=%~dp0"

start "Agentic AI - Backend" powershell -NoExit -ExecutionPolicy Bypass -Command "if (Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue) { Write-Host 'Backend already running on port 8000.'; exit 0 }; Set-Location -LiteralPath '%ROOT%backend'; if (Test-Path '..\.venv\Scripts\Activate.ps1') { Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned; . '..\.venv\Scripts\Activate.ps1' }; python -m uvicorn app.main:app --reload --port 8000"

start "Agentic AI - Frontend" powershell -NoExit -ExecutionPolicy Bypass -Command "if (Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue) { Write-Host 'Frontend already running on port 3000.'; exit 0 }; Set-Location -LiteralPath '%ROOT%frontend'; npm run dev"

start "Agentic AI - MCP Tools" powershell -NoExit -ExecutionPolicy Bypass -Command "Set-Location -LiteralPath '%ROOT%backend'; if (Test-Path '..\.venv\Scripts\Activate.ps1') { Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned; . '..\.venv\Scripts\Activate.ps1' }; python mcp_server.py"

endlocal
