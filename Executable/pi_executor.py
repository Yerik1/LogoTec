# Executable/pi_executor.py
"""
Executor para enviar comandos a Raspberry Pi por TCP en MicroPython.
Traduce comandos internos a instrucciones que entiende robotito/main.py.
"""
import socket
import threading
from typing import Optional, Callable

class PiExecutor:
    """Ejecuta comandos en la Raspberry Pi por TCP sin bloquear la UI."""
    
    def __init__(self, pi_ip: str, pi_port: int = 5000, 
                 on_message: Optional[Callable[[str], None]] = None,
                 on_error: Optional[Callable[[str], None]] = None):
        """
        Args:
            pi_ip: IP de la Raspberry Pi (ej: "192.168.x.y")
            pi_port: Puerto TCP en la Pi (default: 5000)
            on_message: Callback para mensajes (log)
            on_error: Callback para errores
        """
        self.pi_ip = pi_ip
        self.pi_port = pi_port
        self.on_message = on_message or (lambda m: print(f"[PiExecutor] {m}"))
        self.on_error = on_error or (lambda e: print(f"[PiExecutor ERROR] {e}"))
        self.socket = None
        self.connected = False
    
    def connect(self) -> bool:
        """Conecta a la Pi. Retorna True si logra conectar."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)
            self.socket.connect((self.pi_ip, self.pi_port))
            self.connected = True
            self.on_message(f"Conectado a {self.pi_ip}:{self.pi_port}")
            return True
        except Exception as e:
            self.on_error(f"No se pudo conectar a {self.pi_ip}:{self.pi_port}: {e}")
            self.connected = False
            return False
    
    def send_command(self, cmd: str) -> bool:
        """Envía un comando a la Pi. Retorna True si se envió."""
        if not self.connected:
            self.on_error("No conectado a la Pi. Conecta primero.")
            return False
        try:
            # Asegúrate que el comando termina con \n
            if not cmd.endswith('\n'):
                cmd += '\n'
            self.socket.sendall(cmd.encode('utf-8'))
            self.on_message(f"Enviado: {cmd.strip()}")
            return True
        except Exception as e:
            self.on_error(f"Error al enviar comando: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Desconecta de la Pi."""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.connected = False
        self.on_message("Desconectado de la Pi")
    
    def execute_commands_async(self, commands: list, done_callback: Optional[Callable[[], None]] = None):
        """
        Ejecuta una lista de comandos de forma asincrónica (en thread) sin bloquear la UI.
        
        Args:
            commands: Lista de strings (comandos)
            done_callback: Se llama cuando termina la ejecución
        """
        def worker():
            try:
                for cmd in commands:
                    if not self.send_command(cmd):
                        self.on_error(f"Falló al enviar: {cmd}")
                        break
                self.on_message("Ejecución completada")
            except Exception as e:
                self.on_error(f"Error durante ejecución: {e}")
            finally:
                if done_callback:
                    done_callback()
        
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()


# Mapeo de primitivas de tu IR a comandos de la Pi
IR_TO_PI_COMMANDS = {
    # Movimiento
    "move_forward": lambda args: f"ADELANTE",
    "move_backward": lambda args: f"ATRAS",
    "turn_right": lambda args: f"DERECHA",
    "turn_left": lambda args: f"IZQUIERDA",
    
    # Lápiz
    "pen_up": lambda args: f"LEVANTAR_LAPIZ",
    "pen_down": lambda args: f"BAJAR_LAPIZ",
    
    # Colores
    "set_color": lambda args: _color_cmd(args[0] if args else 0),
    
    # Control
    "delay_ms": lambda args: f"ESPERA {args[0] if args else 100}",
    
    # Otros (pueden ignorarse o adaptarse según necesidad)
    "hide_turtle": lambda args: "# hide_turtle (no soportado en Pi)",
    "center_turtle": lambda args: "# center_turtle (no soportado en Pi)",
}

def _color_cmd(color_id: int) -> str:
    """Mapea IDs de color a comandos de la Pi."""
    color_map = {
        0: "VERDE",      # negro -> verde (por default)
        1: "# rojo",     # rojo (ajusta según tu Pi)
        2: "CELESTE",    # azul -> celeste
        3: "MORADO",     # verde -> morado
    }
    return color_map.get(color_id, "VERDE")

def translate_runtime_to_pi(runtime_cmd: str) -> Optional[str]:
    """
    Traduce comandos del runtime (ej: 'FORWARD 50') a comandos para la Pi.
    Retorna el comando para la Pi o None si no se puede traducir.
    """
    parts = runtime_cmd.strip().split()
    if not parts:
        return None
    
    cmd_name = parts[0].lower()
    args = parts[1:] if len(parts) > 1 else []
    
    # Mapeo rápido de comandos
    if cmd_name == "forward":
        return "ADELANTE"
    elif cmd_name == "back":
        return "ATRAS"
    elif cmd_name == "right":
        return "DERECHA"
    elif cmd_name == "left":
        return "IZQUIERDA"
    elif cmd_name == "penup":
        return "LEVANTAR_LAPIZ"
    elif cmd_name == "pendown":
        return "BAJAR_LAPIZ"
    elif cmd_name == "color":
        color_id = int(args[0]) if args else 0
        return _color_cmd(color_id)
    elif cmd_name == "delay":
        delay_ms = int(args[0]) if args else 100
        return f"ESPERA {delay_ms}"
    else:
        # Comando desconocido, ignora
        return None
