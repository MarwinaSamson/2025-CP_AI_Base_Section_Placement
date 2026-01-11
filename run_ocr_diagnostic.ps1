#!/usr/bin/env powershell
# Run OCR diagnostic test with proper environment setup

# Function to find Django environment
function Find-DjangoEnv {
    $envs = @(
        'C:\Users\Marwina\.conda\envs\djangoenv',
        'C:\Users\Marwina\.conda\envs\cp_ai_section_env',
        'C:\Users\Marwina\.conda\envs\Student_Section_Placement_And_Risk_Prediction_env'
    )
    
    foreach ($env in $envs) {
        if (Test-Path "$env\Scripts\python.exe") {
            return "$env\Scripts\python.exe"
        }
    }
    
    # Check Anaconda2 venv
    if (Test-Path 'C:\Users\Marwina\Desktop\Anacondas\Anaconda-2\venv\Scripts\python.exe') {
        return 'C:\Users\Marwina\Desktop\Anacondas\Anaconda-2\venv\Scripts\python.exe'
    }
    
    return $null
}

Write-Host "🔍 OCR Diagnostic Test - PowerShell Launcher" -ForegroundColor Cyan
Write-Host "==========================================`n" -ForegroundColor Cyan

# Find Python with Django
$pythonExe = Find-DjangoEnv
if (-not $pythonExe) {
    Write-Host "❌ Could not find Django environment!" -ForegroundColor Red
    Write-Host "Tried environments:" -ForegroundColor Yellow
    Write-Host "  - djangoenv" -ForegroundColor Yellow
    Write-Host "  - cp_ai_section_env" -ForegroundColor Yellow
    Write-Host "  - Student_Section_Placement_And_Risk_Prediction_env" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Found Python: $pythonExe`n" -ForegroundColor Green

# Run the diagnostic test
Write-Host "Running OCR diagnostic with your image..." -ForegroundColor Cyan
Write-Host "============================================`n" -ForegroundColor Cyan

$args_to_pass = @('test_ocr_diagnostic.py', 'ADLFA_3.jpg', '90')

& $pythonExe @args_to_pass

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "Test complete!" -ForegroundColor Cyan
