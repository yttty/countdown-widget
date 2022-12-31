# Delete old version
$FileName = "$env:APPDATA\Countdown"
if (Test-Path $FileName) {
  Remove-Item -Recurse $FileName
}

# Copy to user's APPDATA
Copy-Item -Recurse "Countdown" "$env:APPDATA\"

# Create object
$WshShell = New-Object -comObject WScript.Shell

# Create shortcut in start menu
$Shortcut = $WshShell.CreateShortcut("$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Countdown.lnk")
$Shortcut.TargetPath = "$env:APPDATA\Countdown\countdown.exe"
$Shortcut.Save()

# Create shortcut in startup for auto startup
$Shortcut = $WshShell.CreateShortcut("$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\Countdown.lnk")
$Shortcut.TargetPath = "$env:APPDATA\Countdown\countdown.exe"
$Shortcut.Save()