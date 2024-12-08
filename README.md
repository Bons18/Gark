## Herramienta de Ataque de Red

**¡Úsalo responsablemente!**

## Descripción

Esta herramienta permite realizar ataques de red utilizando diferentes tipos de métodos como:

- **UDP Flood**: Envía una gran cantidad de paquetes UDP al objetivo.
- **SYN Flood**: Envía una gran cantidad de solicitudes de conexión TCP (SYN) sin completar el handshake.
- **ICMP Flood**: Envía una gran cantidad de pings (ICMP Echo Request) al objetivo.
- **HTTP Flood**: Envía una gran cantidad de solicitudes HTTP al objetivo.

Está diseñada para fines educativos y de prueba en entornos controlados.

## Requisitos

- Python 3.x
- `colorama` para la coloración de la salida en consola
- Permisos de root para ejecutar el script debido al uso de sockets raw

## Instalación

Para instalar las dependencias, ejecuta el siguiente comando:

\`\`\`bash
pip install colorama
\`\`\`

## Uso

Para ejecutar el script de ataque, usa el siguiente comando:

\`\`\`bash
python Gark.py
\`\`\`

### Parámetros de configuración:

- **IP de destino**: La dirección IP del objetivo del ataque.
- **Puerto de destino**: El puerto al que se enviarán los paquetes (0 para ICMP).
- **Tipo de ataque**: El tipo de ataque que se realizará (\`UDP\`, \`SYN\`, \`ICMP\`, \`HTTP\`).
- **Tamaño de payload**: Tamaño en bytes del paquete enviado en el ataque.
- **Hilos de ataque**: Número de hilos que se utilizarán para enviar los paquetes.
- **Duración del ataque**: El tiempo en segundos que durará el ataque.

## Ejemplo de salida

\`\`\`bash
Introduce la IP objetivo: 192.168.1.100
Introduce el puerto objetivo (0 para ICMP): 80
Tipos de ataque disponibles:
  - udp: UDP Flood - Envía una gran cantidad de paquetes UDP al objetivo.
  - syn: SYN Flood - Envía una gran cantidad de solicitudes de conexión TCP (SYN).
  - icmp: ICMP Flood - Envía una gran cantidad de pings (ICMP Echo Request) al objetivo.
  - http: HTTP Flood - Envía una gran cantidad de solicitudes HTTP al objetivo.
Introduce el tipo de ataque: udp
Introduce el tamaño del payload (bytes): 1024
Introduce el número de hilos de ataque: 50
Introduce la duración del ataque (segundos): 60
Ataque en progreso...
Enviados 1000 paquetes a 192.168.1.100:80 (Spoofed IP: 10.0.0.1)
\`\`\`

## Importante

**Esta herramienta debe ser utilizada solo en entornos controlados y con permisos explícitos para realizar pruebas de penetración o de resistencia a ataques. El uso indebido puede tener consecuencias legales graves.**

## Licencia

Este proyecto está licenciado bajo la **Licencia MIT**, lo que te permite modificar y distribuir el código bajo los términos de esta licencia." > README.md
