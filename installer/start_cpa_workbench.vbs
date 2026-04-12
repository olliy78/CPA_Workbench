Option Explicit

Dim shell, fso, projectDir, scriptPath, pythonExe
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

projectDir = fso.GetParentFolderName(WScript.ScriptFullName)
scriptPath = fso.BuildPath(projectDir, "cpa_workbench.py")
pythonExe = FindPythonExecutable()

If pythonExe = "" Then
    MsgBox "Python 3.8+ wurde nicht gefunden." & vbCrLf & _
           "Bitte installieren Sie Python, z.B. mit:" & vbCrLf & _
           "winget install --id Python.Python.3.12 -e --scope user", _
           vbExclamation, "CPA Workbench"
    WScript.Quit 1
End If

shell.CurrentDirectory = projectDir
shell.Run Quote(pythonExe) & " " & Quote(scriptPath), 0, False

Function FindPythonExecutable()
    Dim localPythonRoot, folder, candidate

    candidate = shell.ExpandEnvironmentStrings("%LocalAppData%\Programs\Python")
    If fso.FolderExists(candidate) Then
        localPythonRoot = candidate
        For Each folder In fso.GetFolder(localPythonRoot).SubFolders
            If LCase(Left(fso.GetFileName(folder.Path), 7)) = "python3" Then
                candidate = fso.BuildPath(folder.Path, "pythonw.exe")
                If fso.FileExists(candidate) Then
                    FindPythonExecutable = candidate
                End If
            End If
        Next
        If FindPythonExecutable <> "" Then Exit Function
    End If

    candidate = FindFromWhere("pythonw.exe")
    If candidate <> "" Then
        FindPythonExecutable = candidate
        Exit Function
    End If

    candidate = FindFromWhere("python.exe")
    If candidate <> "" Then
        FindPythonExecutable = candidate
        Exit Function
    End If

    FindPythonExecutable = ""
End Function

Function FindFromWhere(exeName)
    Dim execObj, line
    On Error Resume Next
    Set execObj = shell.Exec("cmd /c where " & exeName)
    If Err.Number <> 0 Then
        Err.Clear
        FindFromWhere = ""
        Exit Function
    End If
    On Error GoTo 0

    Do While Not execObj.StdOut.AtEndOfStream
        line = Trim(execObj.StdOut.ReadLine())
        If line <> "" And fso.FileExists(line) Then
            FindFromWhere = line
            Exit Function
        End If
    Loop

    FindFromWhere = ""
End Function

Function Quote(text)
    Quote = Chr(34) & text & Chr(34)
End Function
