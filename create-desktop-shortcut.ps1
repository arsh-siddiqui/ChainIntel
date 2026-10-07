$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Desktop)
$ShortcutPath = Join-Path $DesktopPath "ChainIntel Workstation.lnk"
$TargetScript = Join-Path $PSScriptRoot "start-app.bat"

$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $TargetScript
$Shortcut.WorkingDirectory = $PSScriptRoot
$Shortcut.Description = "ChainIntel Blockchain Forensics & OSINT Desktop Workstation"
$Shortcut.WindowStyle = 1
$Shortcut.Save()

Write-Host "Created Desktop Shortcut: $ShortcutPath" -ForegroundColor Green
