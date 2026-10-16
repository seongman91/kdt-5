param([string]$StudentId = '', [int]$ApiPort = 0, [switch]$LocalOnly)
. (Join-Path $PSScriptRoot 'Lab-Common.ps1')
Set-Location -LiteralPath $PSScriptRoot
try {
    Assert-LabDocker
    $settings = Read-LabSettings
    if (-not $StudentId) { $StudentId = $settings['STUDENT_ID'] }
    if (-not $StudentId) { $StudentId = Read-Host 'Enter your student ID (S01-S20)' }
    $StudentId = $StudentId.Trim().ToUpperInvariant()
    if ($StudentId -notmatch '^S(0[1-9]|1[0-9]|20)$') { throw 'Use an assigned ID from S01 to S20.' }
    if ($settings['STUDENT_ID'] -and $settings['STUDENT_ID'] -ne $StudentId) {
        throw 'This folder already belongs to another student ID. Use a fresh extracted folder.'
    }
    if ($ApiPort -eq 0) { $ApiPort = if ($settings['API_PORT']) { [int]$settings['API_PORT'] } else { 8000 } }
    if ($ApiPort -lt 1024 -or $ApiPort -gt 65535) { throw 'Use a port between 1024 and 65535.' }
    Write-Host '[1/5] Building the API image. The first run downloads dependencies.'
    Invoke-LabDocker -DockerArguments @('build', '-t', 'wxo-student-api:local', '.')
    $settings['STUDENT_ID'] = $StudentId
    $settings['API_PORT'] = "$ApiPort"
    $settings['COMPOSE_PROJECT_NAME'] = "wxo-lab-$($StudentId.ToLowerInvariant())"
    # Generated files must not keep a stale public URL if this run cannot connect.
    $settings['PUBLIC_HOST'] = 'localhost'
    Save-LabSettings -Settings $settings
    $prepareArgs = @('run', '--rm', '--network', 'none', '--mount', "type=bind,source=$PSScriptRoot,target=/workspace", '--workdir', '/workspace', '--entrypoint', 'python', 'wxo-student-api:local', 'prepare_training.py', '--students', '20', '--tool-prefix', $StudentId.ToLowerInvariant())
    # Student launches always prepare a server without authentication, including upgrades.
    $prepareArgs += '--no-auth'
    Write-Host '[2/5] Preparing your student details and import files.'
    Invoke-LabDocker -DockerArguments $prepareArgs
    Invoke-LabCompose -ComposeArguments @('config', '--quiet')
    Write-Host '[3/5] Starting the API and checking localhost.'
    Invoke-LabCompose -ComposeArguments @('up', '-d', 'api')
    $ready = $false
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        try {
            $health = Get-LabJson -Url "http://localhost:$ApiPort/health"
            if ($health.status -eq 'ok') { $ready = $true; break }
        } catch { }
        Start-Sleep -Seconds 2
    }
    if (-not $ready) { throw 'Local API did not become ready. Run 02_Check.cmd and read the troubleshooting chapter.' }
    if ($LocalOnly) {
        Invoke-LabCompose -ComposeArguments @('stop', 'tunnel')
        Write-Host '[LOCAL ONLY] Public tunnel was not started.'
        Write-LabConnectionInfo
        exit 0
    }
    Write-Host '[4/5] Starting Cloudflare Tunnel and waiting for its HTTPS address.'
    # Recreate so a restarted tunnel cannot return an old URL from earlier logs.
    Invoke-LabCompose -ComposeArguments @('up', '-d', '--force-recreate', '--no-deps', 'tunnel')
    $container = @(Invoke-LabCompose -ComposeArguments @('ps', '-a', '-q', 'tunnel'))[-1]
    $publicUrl = $null
    for ($attempt = 0; $attempt -lt 45; $attempt++) {
        # docker logs uses stderr for normal log lines; capture without exposing API credentials.
        $previousPreference = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        $logs = (& docker logs --tail 200 $container 2>&1 | Out-String)
        $ErrorActionPreference = $previousPreference
        $urls = [regex]::Matches($logs, 'https://(?!api\.)[a-z0-9-]+\.trycloudflare\.com')
        if ($urls.Count -gt 0) { $publicUrl = $urls[$urls.Count - 1].Value; break }
        Start-Sleep -Seconds 2
    }
    if (-not $publicUrl) { throw 'No tunnel URL was found. Keep the API running and check tunnel logs with 02_Check.cmd.' }
    Write-Host '[5/5] Updating OpenAPI files with the tunnel URL.'
    Invoke-LabDocker -DockerArguments ($prepareArgs + @('--public-host', ([uri]$publicUrl).Host))
    Write-LabConnectionInfo
    try {
        $health = Get-LabJson -Url "$publicUrl/health"
        if ($health.status -ne 'ok') { throw 'Unexpected public health response.' }
        Write-Host '[OK] Public HTTPS health check passed. Next: 02_Check.cmd, then the Orchestrate chapter.'
    } catch {
        Write-Warning 'The URL is ready, but public HTTP could not be verified yet. Wait briefly, then run 02_Check.cmd.'
    }
    exit 0
} catch {
    Write-Host "[ERROR] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host 'See guide.html. Do not delete your data volume to fix a connection problem.'
    exit 1
}
