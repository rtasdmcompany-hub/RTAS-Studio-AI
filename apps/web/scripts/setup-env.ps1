# RTAS Studio AI — bootstrap apps/web/.env.local and apps/backend/.env
# Usage: powershell -ExecutionPolicy Bypass -File apps/web/scripts/setup-env.ps1

$ErrorActionPreference = "Stop"

$WebRoot = Split-Path $PSScriptRoot -Parent
$RepoRoot = Split-Path $WebRoot -Parent
$BackendRoot = Join-Path $RepoRoot "backend"

$WebEnvLocal = Join-Path $WebRoot ".env.local"
$BackendEnv = Join-Path $BackendRoot ".env"

function New-CryptographicSecret {
    $bytes = New-Object byte[] 32
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    return [Convert]::ToBase64String($bytes)
}

function Write-IfMissing {
    param(
        [string]$Path,
        [string]$Content,
        [string]$Label
    )
    if (Test-Path -LiteralPath $Path) {
        Write-Host "[skip] $Label already exists: $Path"
        return $false
    }
    $dir = Split-Path $Path -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    [System.IO.File]::WriteAllText($Path, $Content)
    Write-Host "[ok] Created $Label : $Path"
    return $true
}

$secret = New-CryptographicSecret
$timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")

$webEnvContent = @"
# =============================================================================
# RTAS Studio AI — local environment (auto-generated $timestamp)
# Do not commit this file. Regenerate: npm run setup:env
# =============================================================================

# --- NextAuth (required for /studio) ---
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=$secret

# --- Google OAuth (leave empty for email-only auth / simulation) ---
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
# UI flag; Google button only appears when credentials above are non-empty
NEXT_PUBLIC_GOOGLE_AUTH_ENABLED=true

# --- Cloud AI (optional — empty = demo / simulation playback) ---
# Replicate is consumed by the FastAPI backend; copy the same token to apps/backend/.env
REPLICATE_API_TOKEN=

# --- FastAPI backend ---
NEXT_PUBLIC_FASTAPI_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000

# --- Payments (optional) ---
NEXT_PUBLIC_PAYMENT_PROVIDER=paddle
PADDLE_WEBHOOK_SECRET=
NEXT_PUBLIC_PADDLE_CLIENT_TOKEN=
NEXT_PUBLIC_PADDLE_CHECKOUT_URL=
LEMONSQUEEZY_WEBHOOK_SECRET=
LEMONSQUEEZY_STORE_ID=
LEMONSQUEEZY_VARIANT_ID=
NEXT_PUBLIC_LEMONSQUEEZY_CHECKOUT_URL=

# --- Legacy Next.js demo keys (optional) ---
RUNWAY_API_KEY=
KLING_API_KEY=
FAL_KEY=
"@

$backendEnvContent = @"
# =============================================================================
# RTAS Studio AI — FastAPI backend (auto-generated $timestamp)
# =============================================================================

CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
PUBLIC_BASE_URL=http://localhost:8000

# auto | simulation | replicate | comfyui | diffusers
AI_PROVIDER_MODE=auto

# Leave empty for local simulation / placeholder video delivery
REPLICATE_API_TOKEN=

REPLICATE_CACHE_OUTPUTS_LOCALLY=true
LOCAL_UPLOAD_DIR=data/uploads
LOCAL_OUTPUT_DIR=data/outputs
"@

Write-IfMissing -Path $WebEnvLocal -Content $webEnvContent -Label "frontend .env.local"
Write-IfMissing -Path $BackendEnv -Content $backendEnvContent -Label "backend .env"

Write-Host ""
Write-Host "Done. Start stack:"
Write-Host "  npm run dev          # Next.js"
Write-Host "  npm run dev:api      # FastAPI"
Write-Host ""
