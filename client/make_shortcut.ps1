param([string]$Dir)
$desktop = [Environment]::GetFolderPath('Desktop')
$lnk = Join-Path $desktop 'QuizSolver.lnk'
$vbs = Join-Path $Dir 'QuizSolver.vbs'
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut($lnk)
$s.TargetPath = 'wscript.exe'
$s.Arguments = "`"$vbs`""
$s.WorkingDirectory = $Dir
$s.IconLocation = 'shell32.dll,22'
$s.Description = 'QuizSolver'
$s.Save()
Write-Host "[+] Shortcut: $lnk"
