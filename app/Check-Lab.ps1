. (Join-Path $PSScriptRoot 'Lab-Common.ps1')
Set-Location -LiteralPath $PSScriptRoot
try {
    Assert-LabDocker
    $settings = Read-LabSettings
    if ($settings['TRAINING_AUTH_MODE'] -ne 'none') { throw 'Run the latest 01_Start.cmd first to prepare this student kit.' }
    Invoke-LabCompose -ComposeArguments @('ps', '-a')
    $roster = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'generated/roster.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $row = $roster | Where-Object { $_.student -eq $settings['STUDENT_ID'] } | Select-Object -First 1
    $targets = @("http://localhost:$($settings['API_PORT'])")
    if ($settings['PUBLIC_HOST'] -and $settings['PUBLIC_HOST'] -ne 'localhost') {
        if ($settings['PUBLIC_HOST'] -notmatch '^[a-z0-9-]+\.trycloudflare\.com$') { throw 'Unexpected public hostname. Run 01_Start.cmd to refresh it.' }
        $targets += "https://$($settings['PUBLIC_HOST'])"
    }
    foreach ($base in $targets) {
        Write-Host "Checking $base"
        $health = Get-LabJson -Url "$base/health"
        if ($health.status -ne 'ok') { throw 'Health check returned an unexpected response.' }
        $headers = @{}
        $name = [uri]::EscapeDataString($row.hr_name)
        $profile = Get-LabJson -Url "$base/user_profile_details/$name" -Headers $headers
        if ($profile.name -ne $row.hr_name) { throw 'The HR response does not match this student.' }
        $balance = Get-LabJson -Url "$base/balance-inquiry" -Headers $headers -Method 'POST' -Body @{ iban = $row.source_iban }
        if ($balance.iban -ne $row.source_iban) { throw 'The account response does not match this student.' }
        Write-Host '[OK] Health, HR, and banking passed. No data was changed.'
    }
    if ($targets.Count -eq 1) { Write-Warning 'Only localhost was checked. Public tunnel and SaaS are not connected yet.' }
    exit 0
} catch {
    Write-Host "[ERROR] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host 'Recent container logs follow. See guide.html for the matching error.'
    if (Test-Path -LiteralPath $script:EnvFile) {
        $ErrorActionPreference = 'Continue'
        & docker compose --env-file $script:EnvFile -f $script:ComposeFile logs --tail 30
    }
    exit 1
}
