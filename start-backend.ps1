param(
  [switch]$Lite
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root "backend"
$wheel = Join-Path (Split-Path -Parent $root) "actian-vectorAI-db-beta\actian_vectorai-0.1.0b2-py3-none-any.whl"
$deps = Join-Path $backend ".deps"

Set-Location $backend

function Start-WithWorkspaceDeps {
  param([switch]$LiteMode)

  if (!(Test-Path $deps)) {
    New-Item -ItemType Directory -Force -Path $deps | Out-Null
  }

  if ($LiteMode) {
    python -m pip install --target $deps fastapi "uvicorn[standard]" python-multipart pydantic-settings pypdf pillow pytesseract numpy
    $env:MEMORYMESH_EMBEDDING_MODE = "hash"
  } else {
    python -m pip install --target $deps -r requirements.txt
  }

  if (Test-Path $wheel) {
    python -m pip install --target $deps $wheel
  } else {
    Write-Host "Actian beta wheel not found at $wheel. Backend will use fallback unless actian-vectorai is installed."
  }

  $env:PYTHONPATH = "$deps;$backend"
  python -m uvicorn app.main:app --reload --port 8000
}

try {
  if (!(Test-Path ".venv")) {
    python -m venv .venv
  }
} catch {
  Write-Host "Virtual environment creation failed. Falling back to workspace-local dependencies."
  Start-WithWorkspaceDeps -LiteMode:$Lite
  exit $LASTEXITCODE
}

if (!(Test-Path ".\.venv\Scripts\python.exe")) {
  Write-Host "Virtual environment is incomplete. Falling back to workspace-local dependencies."
  Start-WithWorkspaceDeps -LiteMode:$Lite
  exit $LASTEXITCODE
}

try {
  .\.venv\Scripts\python.exe -m pip --version | Out-Null
} catch {
  Write-Host "Virtual environment pip is unavailable. Falling back to workspace-local dependencies."
  Start-WithWorkspaceDeps -LiteMode:$Lite
  exit $LASTEXITCODE
}

.\.venv\Scripts\python.exe -m pip install --upgrade pip

if ($Lite) {
  .\.venv\Scripts\python.exe -m pip install fastapi "uvicorn[standard]" python-multipart pydantic-settings pypdf pillow pytesseract numpy
  $env:MEMORYMESH_EMBEDDING_MODE = "hash"
} else {
  .\.venv\Scripts\python.exe -m pip install -r requirements.txt
}

if (Test-Path $wheel) {
  .\.venv\Scripts\python.exe -m pip install $wheel
} else {
  Write-Host "Actian beta wheel not found at $wheel. Backend will use fallback unless actian-vectorai is installed."
}

.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
