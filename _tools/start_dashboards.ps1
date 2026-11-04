$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = (Get-Command python -ErrorAction Stop).Source

try {
    foreach ($dashboard in @(
        @{ Port = 5180; Script = 'pcb_dashboard\server.py' },
        @{ Port = 5181; Script = 'progress_dashboard\server.py' }
    )) {
        $port = $dashboard.Port
        $scriptPath = Join-Path $PSScriptRoot $dashboard.Script
        $listener = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
        if ($listener) {
            foreach ($connection in $listener) {
                $process = Get-CimInstance Win32_Process -Filter ("ProcessId = {0}" -f $connection.OwningProcess)
                $commandLine = [string]$process.CommandLine
                if (-not $commandLine -or $commandLine.IndexOf($scriptPath, [StringComparison]::OrdinalIgnoreCase) -lt 0) {
                    throw "Port $port is already used by a process other than this QFBMS dashboard. Close that process, then run this script again."
                }
                Stop-Process -Id $connection.OwningProcess -Force
            }
            for ($attempt = 0; $attempt -lt 20; $attempt++) {
                if (-not (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)) { break }
                Start-Sleep -Milliseconds 250
            }
            if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) {
                throw "The old QFBMS dashboard on port $port did not stop."
            }
        }
        if (-not (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)) {
            $logPrefix = Join-Path $env:TEMP "qfbms-dashboard-$port"
            Start-Process -FilePath $pythonPath -ArgumentList ('"{0}"' -f $scriptPath) -WorkingDirectory $repoRoot -WindowStyle Hidden -RedirectStandardOutput "$logPrefix.out.log" -RedirectStandardError "$logPrefix.err.log"
        }

        $ready = $false
        for ($attempt = 0; $attempt -lt 20; $attempt++) {
            $client = New-Object System.Net.Sockets.TcpClient
            try {
                $connection = $client.ConnectAsync('127.0.0.1', $port)
                if ($connection.Wait(500) -and $client.Connected) { $ready = $true; break }
            } catch {
                # Retry while the Python server starts.
            } finally { $client.Dispose() }
            Start-Sleep -Milliseconds 300
        }
        if (-not $ready) {
            throw "Dashboard on port $port did not start. See $env:TEMP\qfbms-dashboard-$port.err.log"
        }
    }

    Start-Process 'http://localhost:5180/'
    Write-Host 'PCB dashboard:      http://localhost:5180/'
    Write-Host 'Progress dashboard: http://localhost:5181/'
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
