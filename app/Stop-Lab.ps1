. (Join-Path $PSScriptRoot 'Lab-Common.ps1')
try {
    if (-not (Test-Path -LiteralPath $script:EnvFile)) { throw 'No lab configuration exists yet.' }
    Invoke-LabCompose -ComposeArguments @('stop')
    Write-Host '[OK] API and tunnel stopped. Your training data is preserved.'
    Write-Host 'Next time, run 01_Start.cmd and update the changed URL in Orchestrate.'
    exit 0
} catch { Write-Host "[ERROR] $($_.Exception.Message)" -ForegroundColor Red; exit 1 }
