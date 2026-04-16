Set fso = CreateObject("Scripting.FileSystemObject")
Set WshShell = CreateObject("WScript.Shell")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
python  = scriptDir & "\.venv\Scripts\python.exe"
script  = scriptDir & "\main.py"

WshShell.Run """" & python & """ """ & script & """", 0, False
