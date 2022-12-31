pyinstaller --noconfirm .\countdown.spec
Copy-Item scripts\install.ps1 .\dist\
Compress-Archive -Path .\dist\* -DestinationPath release\countdown-release-v0.1.zip -Force
