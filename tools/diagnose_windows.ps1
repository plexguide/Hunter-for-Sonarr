# Huntarr Windows Service Diagnostic Tool
# Run this script as Administrator to diagnose issues with the Huntarr service

Write-Host "Huntarr Windows Service Diagnostic Tool" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Huntarr service exists
Write-Host "Checking if Huntarr service is installed..." -ForegroundColor Yellow
$service = Get-Service -Name "Huntarr" -ErrorAction SilentlyContinue
if ($service -eq $null) {
    Write-Host "ERROR: Huntarr service is not installed!" -ForegroundColor Red
    Write-Host "Please make sure you've installed Huntarr and run the installer with the 'Install as Windows Service' option." -ForegroundColor Red
    exit 1
} else {
    Write-Host "Huntarr service is installed." -ForegroundColor Green
    Write-Host "Current status: $($service.Status)" -ForegroundColor Green
    
    if ($service.Status -ne "Running") {
        Write-Host "Attempting to start the service..." -ForegroundColor Yellow
        Start-Service -Name "Huntarr" -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
        $service = Get-Service -Name "Huntarr"
        Write-Host "Service status after start attempt: $($service.Status)" -ForegroundColor $(if ($service.Status -eq "Running") { "Green" } else { "Red" })
    }
}

# Check network connectivity
Write-Host ""
Write-Host "Checking network connectivity..." -ForegroundColor Yellow
$tcpConnection = Test-NetConnection -ComputerName localhost -Port 9705 -ErrorAction SilentlyContinue
if ($tcpConnection.TcpTestSucceeded) {
    Write-Host "Port 9705 is open and accessible." -ForegroundColor Green
} else {
    Write-Host "WARNING: Port 9705 is not accessible!" -ForegroundColor Red
    Write-Host "The service may not be running properly or may be blocked by a firewall." -ForegroundColor Red
}

# Check firewall settings
Write-Host ""
Write-Host "Checking Windows Firewall rules..." -ForegroundColor Yellow
$firewallRule = Get-NetFirewallRule -DisplayName "Huntarr Web UI" -ErrorAction SilentlyContinue
if ($firewallRule -eq $null) {
    Write-Host "No firewall rule found for Huntarr. Creating one..." -ForegroundColor Yellow
    try {
        New-NetFirewallRule -DisplayName "Huntarr Web UI" -Direction Inbound -Protocol TCP -LocalPort 9705 -Action Allow -ErrorAction Stop
        Write-Host "Created firewall rule to allow inbound connections to port 9705." -ForegroundColor Green
    } catch {
        Write-Host "ERROR: Failed to create firewall rule. You may need to manually allow port 9705 in your firewall settings." -ForegroundColor Red
    }
} else {
    Write-Host "Firewall rule for Huntarr found:" -ForegroundColor Green
    Write-Host "  Name: $($firewallRule.DisplayName)" -ForegroundColor Green
    Write-Host "  Enabled: $($firewallRule.Enabled)" -ForegroundColor Green
    Write-Host "  Action: $($firewallRule.Action)" -ForegroundColor Green
}

# Check installed location
Write-Host ""
Write-Host "Checking Huntarr installation..." -ForegroundColor Yellow
$installPaths = @(
    "C:\Program Files\Huntarr",
    "C:\Program Files (x86)\Huntarr"
)

$foundInstallation = $false
foreach ($path in $installPaths) {
    if (Test-Path $path) {
        $foundInstallation = $true
        Write-Host "Found Huntarr installation at: $path" -ForegroundColor Green
        
        # Check logs
        $logPath = Join-Path $path "config\logs"
        if (Test-Path $logPath) {
            Write-Host "Log directory exists at: $logPath" -ForegroundColor Green
            $logFiles = Get-ChildItem $logPath -Filter "*.log"
            if ($logFiles.Count -gt 0) {
                Write-Host "Found $($logFiles.Count) log files:" -ForegroundColor Green
                foreach ($log in $logFiles) {
                    Write-Host "  $($log.Name) - Last updated: $($log.LastWriteTime)" -ForegroundColor Green
                }
                
                # Check for errors in the service log
                $serviceLogPath = Join-Path $logPath "windows_service.log"
                if (Test-Path $serviceLogPath) {
                    Write-Host ""
                    Write-Host "Checking service log for errors..." -ForegroundColor Yellow
                    $errors = Select-String -Path $serviceLogPath -Pattern "ERROR|CRITICAL|EXCEPTION" -Context 0,1
                    if ($errors.Count -gt 0) {
                        Write-Host "Found $($errors.Count) error(s) in service log:" -ForegroundColor Red
                        foreach ($error in $errors) {
                            Write-Host "  $($error.LineNumber): $($error.Line)" -ForegroundColor Red
                        }
                    } else {
                        Write-Host "No obvious errors found in service log." -ForegroundColor Green
                    }
                }
            } else {
                Write-Host "No log files found in $logPath. This may indicate the service has never run successfully." -ForegroundColor Red
            }
        } else {
            Write-Host "WARNING: Log directory does not exist at: $logPath" -ForegroundColor Red
            Write-Host "This may indicate the service has never started properly." -ForegroundColor Red
        }
    }
}

if (-not $foundInstallation) {
    Write-Host "WARNING: Could not find Huntarr installation in standard locations!" -ForegroundColor Red
}

# Summary and recommendations
Write-Host ""
Write-Host "Diagnostic Summary and Recommendations:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($service -eq $null) {
    Write-Host "- Reinstall Huntarr using the Windows installer" -ForegroundColor Yellow
} elseif ($service.Status -ne "Running") {
    Write-Host "- The Huntarr service is not running. Try starting it manually in Windows Services" -ForegroundColor Yellow
}

if ($tcpConnection -eq $null -or -not $tcpConnection.TcpTestSucceeded) {
    Write-Host "- Port 9705 is not accessible. Check firewall settings and ensure the service is running" -ForegroundColor Yellow
    Write-Host "- You can try temporarily disabling your firewall to test if that's the issue" -ForegroundColor Yellow
}

Write-Host "- Make sure you're using the correct URL: http://localhost:9705 or http://127.0.0.1:9705" -ForegroundColor Yellow
Write-Host "- Review the log files in the config\logs directory for specific error messages" -ForegroundColor Yellow
Write-Host "- If the service starts but the web UI isn't accessible, check for IP binding issues" -ForegroundColor Yellow

Write-Host ""
Write-Host "Diagnostic complete. If issues persist, please share this output with the Huntarr community." -ForegroundColor Cyan 