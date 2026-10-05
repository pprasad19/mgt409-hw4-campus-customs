# Start the Campus Customs API with auto-reload that actually works.
#
# `uvicorn --reload` detects file changes on this machine but never finishes
# restarting - it logs "Reloading..." and then keeps serving the old code. This
# script uses watchfiles to restart the whole uvicorn process instead, which
# applies edits in about two seconds.
#
# Run it from anywhere:  .\backend\dev.ps1
# Or double-click it in Explorer.
#
# The plain command from the assignment still works if you prefer it; you just
# have to restart it by hand after each edit:
#     cd backend
#     uvicorn main:app --reload --port 8000

$ErrorActionPreference = 'Stop'

$BackendDir = $PSScriptRoot
$Python = Join-Path $BackendDir '..\.venv\Scripts\python.exe'

if (-not (Test-Path $Python)) {
    throw "Virtual environment not found at $Python. Create it with: python -m venv .venv"
}

# Signing key for session tokens. Without a fixed value a fresh random key is
# generated on every start, which logs you out each time the server restarts -
# painful when it restarts on every save. This is a development-only value;
# set CAMPUS_CUSTOMS_SECRET yourself for anything real.
if (-not $env:CAMPUS_CUSTOMS_SECRET) {
    $env:CAMPUS_CUSTOMS_SECRET = 'dev-only-campus-customs-secret'
}

# Skip the pydantic-ai startup banner.
$env:PYDANTIC_AI_NO_BANNER = '1'

Set-Location $BackendDir

Write-Host 'Campus Customs API  ->  http://127.0.0.1:8000' -ForegroundColor Cyan
Write-Host 'Watching backend/ for changes. Ctrl+C to stop.' -ForegroundColor DarkGray
Write-Host ''

# --filter python restarts only for .py edits.
#
# Without it, any file in backend/ triggers a restart - including
# prompts/prompt.md. That caused spurious restarts: OneDrive re-touches a file
# roughly half a minute after it is saved, which fired a reload long after the
# edit and killed an in-flight request. prompt.md is re-read on every message
# anyway, so restarting for it was never necessary.
#
# The inner command uses a path relative to backend/ on purpose: the absolute
# path contains spaces, which watchfiles would split into separate arguments.
& $Python -m watchfiles --filter python '../.venv/Scripts/python.exe -m uvicorn main:app --port 8000' .
