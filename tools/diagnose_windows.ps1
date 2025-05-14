# Huntarr Windows Service Diagnostic Tool
# Run this script as Administrator to diagnose issues with the Huntarr service

# Ensure we're running as admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "This script needs to be run as Administrator. Please restart with admin privileges." -ForegroundColor Red
    Write-Host "Right-click on PowerShell and select 'Run as Administrator', then run this script again." -ForegroundColor Red
    exit 1
}

Write-Host "Huntarr Windows Service Diagnostic Tool" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Define common installation paths
$installPaths = @(
    "C:\Program Files\Huntarr",
    "C:\Program Files (x86)\Huntarr"
)

# Find the actual install path
$installedPath = $null
foreach ($path in $installPaths) {
    if (Test-Path $path) {
        $installedPath = $path
        break
    }
}

if ($installedPath -eq $null) {
    Write-Host "ERROR: Cannot find Huntarr installation directory!" -ForegroundColor Red
    Write-Host "Please make sure you have installed Huntarr using the Windows installer." -ForegroundColor Red
    exit 1
}

Write-Host "Found Huntarr installation at: $installedPath" -ForegroundColor Green

# Check if Huntarr service exists
Write-Host ""
Write-Host "Checking if Huntarr service is installed..." -ForegroundColor Yellow
$service = Get-Service -Name "Huntarr" -ErrorAction SilentlyContinue
if ($service -eq $null) {
    Write-Host "ERROR: Huntarr service is not installed!" -ForegroundColor Red
    
    # Try to install the service
    Write-Host "Attempting to install the service..." -ForegroundColor Yellow
    $exePath = Join-Path $installedPath "Huntarr.exe"
    if (Test-Path $exePath) {
        try {
            Start-Process -FilePath $exePath -ArgumentList "--install-service" -Wait -NoNewWindow
            Start-Sleep -Seconds 3
            $service = Get-Service -Name "Huntarr" -ErrorAction SilentlyContinue
            if ($service -ne $null) {
                Write-Host "Service installed successfully!" -ForegroundColor Green
            } else {
                Write-Host "Failed to install service. You may need to manually install it." -ForegroundColor Red
            }
        } catch {
            Write-Host "Error installing service: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "Cannot find Huntarr.exe at $exePath" -ForegroundColor Red
    }
} else {
    Write-Host "Huntarr service is installed." -ForegroundColor Green
    Write-Host "Current status: $($service.Status)" -ForegroundColor Green
    
    if ($service.Status -ne "Running") {
        Write-Host "Attempting to start the service..." -ForegroundColor Yellow
        try {
            Start-Service -Name "Huntarr" -ErrorAction Stop
            Start-Sleep -Seconds 2
            $service = Get-Service -Name "Huntarr"
            Write-Host "Service status after start attempt: $($service.Status)" -ForegroundColor $(if ($service.Status -eq "Running") { "Green" } else { "Red" })
        } catch {
            Write-Host "Failed to start service: $_" -ForegroundColor Red
            Write-Host "Attempting to repair service..." -ForegroundColor Yellow
            
            # Try to remove and reinstall the service
            $exePath = Join-Path $installedPath "Huntarr.exe"
            if (Test-Path $exePath) {
                try {
                    # Stop and remove existing service
                    Start-Process -FilePath $exePath -ArgumentList "--remove-service" -Wait -NoNewWindow
                    Start-Sleep -Seconds 3
                    
                    # Reinstall the service
                    Start-Process -FilePath $exePath -ArgumentList "--install-service" -Wait -NoNewWindow
                    Start-Sleep -Seconds 3
                    
                    # Try to start the service again
                    $service = Get-Service -Name "Huntarr" -ErrorAction SilentlyContinue
                    if ($service -ne $null) {
                        Start-Service -Name "Huntarr" -ErrorAction SilentlyContinue
                        Start-Sleep -Seconds 2
                        $service = Get-Service -Name "Huntarr"
                        Write-Host "Service status after repair: $($service.Status)" -ForegroundColor $(if ($service.Status -eq "Running") { "Green" } else { "Red" })
                    }
                } catch {
                    Write-Host "Failed to repair service: $_" -ForegroundColor Red
                }
            }
        }
    }
}

# Check config directory permissions
Write-Host ""
Write-Host "Checking configuration directory permissions..." -ForegroundColor Yellow
$configPath = Join-Path $installedPath "config"
if (Test-Path $configPath) {
    Write-Host "Config directory exists at: $configPath" -ForegroundColor Green
    
    # Check if directory is writable
    $testFile = Join-Path $configPath "permission_test.tmp"
    try {
        [io.file]::WriteAllText($testFile, "test")
        Remove-Item $testFile -Force
        Write-Host "Config directory is writable." -ForegroundColor Green
    } catch {
        Write-Host "WARNING: Config directory is not writable!" -ForegroundColor Red
        Write-Host "Fixing permissions on config directory..." -ForegroundColor Yellow
        try {
            $acl = Get-Acl $configPath
            $rule = New-Object System.Security.AccessControl.FileSystemAccessRule("Everyone", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow")
            $acl.SetAccessRule($rule)
            Set-Acl $configPath $acl
            
            # Test again
            try {
                [io.file]::WriteAllText($testFile, "test")
                Remove-Item $testFile -Force
                Write-Host "Successfully fixed permissions on config directory." -ForegroundColor Green
            } catch {
                Write-Host "Failed to fix permissions. You may need to manually set permissions." -ForegroundColor Red
            }
        } catch {
            Write-Host "Error setting permissions: $_" -ForegroundColor Red
        }
    }
    
    # Ensure logs directory exists and is writable
    $logsPath = Join-Path $configPath "logs"
    if (-not (Test-Path $logsPath)) {
        Write-Host "Creating missing logs directory..." -ForegroundColor Yellow
        try {
            New-Item -Path $logsPath -ItemType Directory -Force | Out-Null
            Write-Host "Created logs directory." -ForegroundColor Green
        } catch {
            Write-Host "Failed to create logs directory: $_" -ForegroundColor Red
        }
    }
} else {
    Write-Host "ERROR: Config directory does not exist!" -ForegroundColor Red
    Write-Host "Creating config structure..." -ForegroundColor Yellow
    try {
        New-Item -Path $configPath -ItemType Directory -Force | Out-Null
        New-Item -Path (Join-Path $configPath "logs") -ItemType Directory -Force | Out-Null
        New-Item -Path (Join-Path $configPath "stateful") -ItemType Directory -Force | Out-Null
        New-Item -Path (Join-Path $configPath "user") -ItemType Directory -Force | Out-Null
        
        # Set permissions
        $acl = Get-Acl $configPath
        $rule = New-Object System.Security.AccessControl.FileSystemAccessRule("Everyone", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow")
        $acl.SetAccessRule($rule)
        Set-Acl $configPath $acl
        
        Write-Host "Created config directory structure with proper permissions." -ForegroundColor Green
    } catch {
        Write-Host "Failed to create config directory: $_" -ForegroundColor Red
    }
}

# Check network connectivity
Write-Host ""
Write-Host "Checking network connectivity..." -ForegroundColor Yellow
$tcpConnection = Test-NetConnection -ComputerName localhost -Port 9705 -InformationLevel Quiet -ErrorAction SilentlyContinue -WarningAction SilentlyContinue
if ($tcpConnection) {
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
        Write-Host "ERROR: Failed to create firewall rule: $_" -ForegroundColor Red
        Write-Host "You may need to manually allow port 9705 in your firewall settings." -ForegroundColor Red
    }
} else {
    Write-Host "Firewall rule for Huntarr found:" -ForegroundColor Green
    Write-Host "  Name: $($firewallRule.DisplayName)" -ForegroundColor Green
    Write-Host "  Enabled: $($firewallRule.Enabled)" -ForegroundColor Green
    Write-Host "  Action: $($firewallRule.Action)" -ForegroundColor Green
}

# Check log files
Write-Host ""
Write-Host "Checking log files..." -ForegroundColor Yellow
$logsPath = Join-Path $installedPath "config\logs"
if (Test-Path $logsPath) {
    $logFiles = Get-ChildItem $logsPath -Filter "*.log"
    if ($logFiles.Count -gt 0) {
        Write-Host "Found $($logFiles.Count) log files:" -ForegroundColor Green
        foreach ($log in $logFiles) {
            Write-Host "  $($log.Name) - Last updated: $($log.LastWriteTime)" -ForegroundColor Green
        }
        
        # Check for errors in service logs
        $serviceLogPath = Join-Path $logsPath "windows_service.log"
        if (Test-Path $serviceLogPath) {
            Write-Host ""
            Write-Host "Checking service log for errors..." -ForegroundColor Yellow
            try {
                $errors = Select-String -Path $serviceLogPath -Pattern "ERROR|CRITICAL|EXCEPTION" -Context 0,1 -ErrorAction SilentlyContinue
                if ($errors -ne $null -and $errors.Count -gt 0) {
                    Write-Host "Found $($errors.Count) error(s) in service log:" -ForegroundColor Red
                    foreach ($error in $errors) {
                        Write-Host "  $($error.LineNumber): $($error.Line)" -ForegroundColor Red
                    }
                } else {
                    Write-Host "No obvious errors found in service log." -ForegroundColor Green
                }
            } catch {
                Write-Host "Error reading log file: $_" -ForegroundColor Red
            }
        }
        
        # Check startup log
        $startupLogPath = Join-Path $installedPath "huntarr_service_startup.log"
        if (Test-Path $startupLogPath) {
            Write-Host ""
            Write-Host "Checking startup log..." -ForegroundColor Yellow
            try {
                $startupContent = Get-Content -Path $startupLogPath -ErrorAction SilentlyContinue
                if ($startupContent -ne $null) {
                    Write-Host "Startup log found with $($startupContent.Count) lines." -ForegroundColor Green
                }
                
                $startupErrors = Select-String -Path $startupLogPath -Pattern "ERROR|CRITICAL|EXCEPTION" -Context 0,1 -ErrorAction SilentlyContinue
                if ($startupErrors -ne $null -and $startupErrors.Count -gt 0) {
                    Write-Host "Found $($startupErrors.Count) error(s) in startup log:" -ForegroundColor Red
                    foreach ($error in $startupErrors) {
                        Write-Host "  $($error.LineNumber): $($error.Line)" -ForegroundColor Red
                    }
                }
            } catch {
                Write-Host "Error reading startup log: $_" -ForegroundColor Red
            }
        }
    } else {
        Write-Host "No log files found in $logsPath." -ForegroundColor Red
        Write-Host "This may indicate the service has never run successfully." -ForegroundColor Red
    }
} else {
    Write-Host "Log directory not found at: $logsPath" -ForegroundColor Red
}

# Summary and recommendations
Write-Host ""
Write-Host "Diagnostic Summary and Recommendations:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$fixCommands = @()

if ($service -eq $null) {
    Write-Host "- The Huntarr service is not installed. Try running the installer again" -ForegroundColor Yellow
    $fixCommands += "$installedPath\Huntarr.exe --install-service"
} elseif ($service.Status -ne "Running") {
    Write-Host "- The Huntarr service is not running. Try restarting it" -ForegroundColor Yellow
    $fixCommands += "Restart-Service -Name Huntarr -Force"
}

if (-not (Test-Path "$configPath\logs")) {
    Write-Host "- Missing logs directory in the config folder" -ForegroundColor Yellow
    $fixCommands += "New-Item -Path '$configPath\logs' -ItemType Directory -Force"
}

if (-not $tcpConnection) {
    Write-Host "- Port 9705 is not accessible. Check firewall settings and ensure the service is running" -ForegroundColor Yellow
    $fixCommands += "New-NetFirewallRule -DisplayName 'Huntarr Web UI' -Direction Inbound -Protocol TCP -LocalPort 9705 -Action Allow -ErrorAction SilentlyContinue"
}

Write-Host "- Make sure you're using the correct URL: http://localhost:9705 or http://127.0.0.1:9705" -ForegroundColor Yellow
Write-Host "- Review the log files in the config\logs directory for specific error messages" -ForegroundColor Yellow

# Offer to fix common issues
if ($fixCommands.Count -gt 0) {
    Write-Host ""
    Write-Host "Would you like to attempt to automatically fix the detected issues? (Y/N)" -ForegroundColor Cyan
    $response = Read-Host
    if ($response -eq "Y" -or $response -eq "y") {
        Write-Host "Attempting fixes..." -ForegroundColor Yellow
        foreach ($cmd in $fixCommands) {
            Write-Host "Running: $cmd" -ForegroundColor Yellow
            try {
                Invoke-Expression $cmd
                Write-Host "Command executed successfully." -ForegroundColor Green
            } catch {
                Write-Host "Error executing command: $_" -ForegroundColor Red
            }
        }
        
        # Final step - restart service if it exists
        if ($service -ne $null) {
            Write-Host "Restarting Huntarr service..." -ForegroundColor Yellow
            try {
                Restart-Service -Name Huntarr -Force -ErrorAction SilentlyContinue
                Start-Sleep -Seconds 3
                $service = Get-Service -Name "Huntarr"
                Write-Host "Service status after restart: $($service.Status)" -ForegroundColor $(if ($service.Status -eq "Running") { "Green" } else { "Red" })
            } catch {
                Write-Host "Failed to restart service: $_" -ForegroundColor Red
            }
        }
    }
}

Write-Host ""
Write-Host "Diagnostic complete. If issues persist, please share this output with the Huntarr community." -ForegroundColor Cyan 