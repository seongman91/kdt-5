$ErrorActionPreference = 'Stop'
$script:LabRoot = $PSScriptRoot
$script:ComposeFile = Join-Path $script:LabRoot 'compose.student.yaml'
$script:EnvFile = Join-Path $script:LabRoot '.env.training'

function Invoke-LabDocker {
    param([string[]]$DockerArguments)
    & docker @DockerArguments
    if ($LASTEXITCODE -ne 0) { throw "Docker failed (exit $LASTEXITCODE). See the message above and guide.html." }
}

function Invoke-LabCompose {
    param([string[]]$ComposeArguments)
    Invoke-LabDocker -DockerArguments (@('compose', '--env-file', $script:EnvFile, '-f', $script:ComposeFile) + $ComposeArguments)
}

function Read-LabSettings {
    $settings = [ordered]@{}
    if (Test-Path -LiteralPath $script:EnvFile) {
        foreach ($line in [IO.File]::ReadAllLines($script:EnvFile)) {
            if ($line -match '^([^#=]+)=(.*)$') { $settings[$Matches[1]] = $Matches[2] }
        }
    }
    return $settings
}

function Save-LabSettings {
    param($Settings)
    $lines = @($Settings.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" })
    [IO.File]::WriteAllText($script:EnvFile, ($lines -join "`n") + "`n", [Text.UTF8Encoding]::new($false))
}

function Assert-LabDocker {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw 'Docker command not found. Install Docker Desktop, then open a new terminal.'
    }
    $engine = & docker info --format '{{.OSType}}' 2>$null
    if ($LASTEXITCODE -ne 0) { throw 'Docker is not ready. Open Docker Desktop and wait for Engine running.' }
    if ("$engine".Trim() -ne 'linux') { throw 'Switch Docker Desktop to Linux containers.' }
    Invoke-LabDocker -DockerArguments @('compose', 'version')
}

function Get-LabJson {
    param([string]$Url, [hashtable]$Headers = @{}, [string]$Method = 'GET', [object]$Body = $null)
    $options = @{ Uri = $Url; Headers = $Headers; Method = $Method; TimeoutSec = 12; ErrorAction = 'Stop' }
    if ($null -ne $Body) {
        $options['ContentType'] = 'application/json; charset=utf-8'
        $options['Body'] = [Text.Encoding]::UTF8.GetBytes(($Body | ConvertTo-Json -Compress))
    }
    # Windows PowerShell 5.1 can decode JSON without a charset as a legacy encoding.
    $response = Invoke-WebRequest -UseBasicParsing @options
    $jsonText = [Text.Encoding]::UTF8.GetString($response.RawContentStream.ToArray())
    return ($jsonText | ConvertFrom-Json)
}

function Write-LabConnectionInfo {
    $settings = Read-LabSettings
    $generated = Join-Path $script:LabRoot 'generated'
    $roster = Get-Content -LiteralPath (Join-Path $generated 'roster.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $row = $roster | Where-Object { $_.student -eq $settings['STUDENT_ID'] } | Select-Object -First 1
    if ($null -eq $row) { throw 'Student ID was not found in the generated roster.' }
    $publicUrl = if ($settings['PUBLIC_HOST'] -eq 'localhost') { '(not connected)' } else { "https://$($settings['PUBLIC_HOST'])" }
    $text = @"
Student: $($row.student)
Local URL: http://localhost:$($settings['API_PORT'])
Public URL: $publicUrl
Authentication: NONE. Import the generated YAML with No authentication.

HR name: $($row.hr_name)
Source IBAN: $($row.source_iban)
Destination IBAN: $($row.destination_iban)
Initial time off: 15 days
Initial balances: source 5000 EUR / destination 1000 EUR
Initial overdraft: 0 EUR

Import files: hr_training.yaml and bank_training.yaml
Tool names contain: _$($row.student.ToLowerInvariant())_
Restart 01_Start.cmd to refresh a changed public URL.
Then update YOUR imported tools in Orchestrate.
"@
    [IO.File]::WriteAllText((Join-Path $generated 'my_lab.txt'), $text, [Text.UTF8Encoding]::new($true))
    Write-Host "[OK] Student: $($row.student)"
    Write-Host "[OK] Local docs: http://localhost:$($settings['API_PORT'])/docs"
    Write-Host "[OK] Public URL: $publicUrl"
    Write-Host '[NOTE] Anyone who knows the public URL can read and change the fictional training data.'
    Write-Host '[OK] Open generated\my_lab.txt for your connection and account details.'
}
