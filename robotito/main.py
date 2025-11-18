import network
import socket
from time import sleep
import machine
from machine import Pin, PWM

ssid = '2505000_AP_2.4_339F2D'
password = 'radioshack1234'

Motor_A_Adelante = Pin(18, Pin.OUT)
Motor_A_Atras = Pin(19, Pin.OUT)
Motor_B_Adelante = Pin(20, Pin.OUT)
Motor_B_Atras = Pin(21, Pin.OUT)

pwm = PWM(Pin(0))
pwm.freq(50)

color = ""
escri = True

def bajar_lpz():
    global color, escri
    if escri:
        return
    else:
        escri = True
        
    if(color == "verde"):
        verde()
    elif(color == "morado"):
        morado()
    elif(color == "celeste"):
        celeste()
    else:
        verde()
    
def verde():
    global color
    color = "verde"
    pwm.duty_u16(4500)
    sleep(2)
    pwm.duty_u16(3700)# verde
    sleep(2)
 
def morado():
    global color
    color = "morado"
    pwm.duty_u16(6800)
    sleep(2)
    pwm.duty_u16(6000)#morado
    sleep(2)
    
def celeste():
    global color
    color = "celeste"
    pwm.duty_u16(7850)
    sleep(2)
    pwm.duty_u16(7400)#celeste
    sleep(2)

def subirlapiz():
    global escri
    if escri:
        pwm.duty_u16(1500)
        escri = False
    else:
        pass

def adelante():
    Motor_A_Adelante.value(0)
    Motor_B_Adelante.value(1)
    Motor_A_Atras.value(1)
    Motor_B_Atras.value(0)
    

    
def atras():
    Motor_A_Adelante.value(1)
    Motor_B_Adelante.value(0)
    Motor_A_Atras.value(0)
    Motor_B_Atras.value(1)
    

def detener():
    Motor_A_Adelante.value(0)
    Motor_B_Adelante.value(0)
    Motor_A_Atras.value(0)
    Motor_B_Atras.value(0)

def izquierda():
    Motor_A_Adelante.value(1)
    Motor_B_Adelante.value(1)
    Motor_A_Atras.value(0)
    Motor_B_Atras.value(0)

def derecha():
    Motor_A_Adelante.value(0)
    Motor_B_Adelante.value(0)
    Motor_A_Atras.value(1)
    Motor_B_Atras.value(1)


detener()
    
def conectar():
    red = network.WLAN(network.STA_IF)
    red.active(True)
    red.connect(ssid, password)
    while red.isconnected() == False:
        print('Conectando ...')
        sleep(1)
    ip = red.ifconfig()[0]
    print(f'Conectado con IP: {ip}')
    return ip
    
def open_socket(ip):
    address = (ip, 80)
    connection = socket.socket()
    connection.bind(address)
    connection.listen(1)
    return connection

def pagina_web():
    html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        </head>
        <body>

        <!-- Barra lateral izquierda -->
        <div style="position: fixed; left: 10px; top: 50px;">
            <form action="./verde">
                <input type="submit" value="Verde" 
                style="background-color: #2ecc71; border-radius: 15px; height:70px; width:120px; border: none; color: white; padding: 10px; margin-bottom: 10px"/>
            </form>

            <form action="./morado">
                <input type="submit" value="Morado" 
                style="background-color: #9b59b6; border-radius: 15px; height:70px; width:120px; border: none; color: white; padding: 10px; margin-bottom: 10px"/>
            </form>

            <form action="./celeste">
                <input type="submit" value="Celeste" 
                style="background-color: #5dade2; border-radius: 15px; height:70px; width:120px; border: none; color: white; padding: 10px; margin-bottom: 10px"/>
            </form>

            <form action="./bajarlapiz">
                <input type="submit" value="Bajar Lápiz" 
                style="background-color: #34495e; border-radius: 15px; height:70px; width:120px; border: none; color: white; padding: 10px; margin-bottom: 10px"/>
            </form>

            <form action="./levantarlapiz">
                <input type="submit" value="Levantar Lápiz" 
                style="background-color: #7f8c8d; border-radius: 15px; height:70px; width:120px; border: none; color: white; padding: 10px"/>
            </form>
        </div>


        <center>
        <form action="./adelante">
        <input type="submit" value="Adelante" style="background-color: #04AA6D; border-radius: 15px; height:120px; width:120px; border: none; color: white; padding: 16px 24px; margin: 4px 2px"  />
        </form>

        <table><tr>
        <td><form action="./izquierda">
        <input type="submit" value="Izquierda" style="background-color: #04AA6D; border-radius: 15px; height:120px; width:120px; border: none; color: white; padding: 16px 24px; margin: 4px 2px"/>
        </form></td>

        <td><form action="./detener">
        <input type="submit" value="Detener" style="background-color: #FF0000; border-radius: 50px; height:120px; width:120px; border: none; color: white; padding: 16px 24px; margin: 4px 2px" />
        </form></td>

        <td><form action="./derecha">
        <input type="submit" value="Derecha" style="background-color: #04AA6D; border-radius: 15px; height:120px; width:120px; border: none; color: white; padding: 16px 24px; margin: 4px 2px"/>
        </form></td>
        </tr></table>

        <form action="./atras">
        <input type="submit" value="Atras" style="background-color: #04AA6D; border-radius: 15px; height:120px; width:120px; border: none; color: white; padding: 16px 24px; margin: 4px 2px"/>
        </form>
        </center>

        </body>
        </html>
        """

    return str(html)

def serve(connection):
    global color, escri
    while True:
        cliente = connection.accept()[0]
        peticion = cliente.recv(1024)
        peticion = str(peticion)
        try:
            peticion = peticion.split()[1]
        except IndexError:
            pass
        if peticion == '/adelante?':
            adelante()
        elif peticion =='/izquierda?':
            izquierda()
        elif peticion =='/detener?':
            detener()
        elif peticion =='/derecha?':
            derecha()
        elif peticion =='/atras?':
            atras()
        elif peticion =='/bajarlapiz':
            escri = True
            if color=='verde':
                verde()
            elif color == 'morado':
                morado()
            elif color == 'celeste':
                celeste()
            else:
                color = 'verde'
                verde()
        elif peticion == '/subirlapiz':
            subirlapiz()
        elif peticion == '/verde?':
            if escri:
                verde()
            else:
                color = 'verde'
        
        elif peticion == '/morado?':
            if escri:
                morado()
            else:
                color = 'morado'
                
        elif peticion == '/celeste?':
            if escri:
                celeste()
            else:
                color = 'celeste'

        html = pagina_web()
        cliente.send(html)
        cliente.close()

try:
    ip = conectar()
    connection = open_socket(ip)
    serve(connection)
except KeyboardInterrupt:
    machine.reset()
