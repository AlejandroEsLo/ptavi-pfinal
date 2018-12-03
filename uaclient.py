#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Programa cliente que abre un socket a un servidor."""

import socket
import sys
import time

def fich_log(fich,evento,ip,port,coment):
    # Cogemos localtime para que sea conformea nuestra hora local
    hora = time.strftime("%Y%m%d%H%M%S",time.localtime(int(time.time())))
    fich = open(fich,"a" )
    hora_inicio = fich.write(hora())
    fin = "\r\n" #¿?¿?¿?
#DUDA!!!!!!!!!!!!!!!!!
    #Añadir más contenido a un fichero de texto:
        #fichero = open(‘fichero.txt’,’a’) # modo append y el puntero se coloca al final

    #si abrimos un fichero ya existente con ese nombre y en modo escritura, se eliminará el contenido al ejecutar:
        #fichero = open(‘fichero.txt’,’w’)

    if evento == "sent_to":
        fich.write(" Sent to " + ip + ":" + str(port) + ": " + coment + fin)
    elif evento == "received":
        fich.write(" Received from " + ip + ":" + str(port) +
                    ": " + coment + fin)
    elif evento == "error":   
        fich.write(" Error: " + coment + fin)
    
    elif evento == "starting":   
        fich.write(" Starting... "+ fin)
    
    elif evento == "finishing":   
        fich.write(" Finishing... "+ fin)
        
    fich.close()
# Cliente UDP simple.
try:
    METODO = sys.argv[1]
    DIRECCION = sys.argv[2]
    LOGIN = DIRECCION.split("@")[0]
    IP_Y_PORT = DIRECCION.split("@")[1]
    IP_RECEPTOR = IP_Y_PORT.split(":")[0]  # 127.0.0.1
    PORT = int(sys.argv[2].split(":")[-1])

except IndexError:
    sys.exit("Usage: python3 client.py method receiver@IP:SIPport")

# Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.connect((IP_RECEPTOR, PORT))

    # Contenido que vamos a enviar
    mensaje = (METODO.upper() + " sip:" + LOGIN + "@" + IP_RECEPTOR
               + " SIP/2.0\r\n")

    print("\r\nEnviando: " + mensaje)
    my_socket.send(bytes(mensaje, 'utf-8') + b'\r\n')
    data = my_socket.recv(1024)

    respuesta_serv = data.decode('utf-8')
    # End para quitar espacio print
    print('Recibido:')
    print(data.decode('utf-8'))

    if respuesta_serv == ("SIP/2.0 100 Trying\r\n\r\n"
                          + "SIP/2.0 180 Ringing\r\n\r\n"
                          + "SIP/2.0 200 OK\r\n\r\n"):
        METODO = "ACK"
        mensaje = (METODO.upper() + " sip:" + LOGIN + "@" + IP_RECEPTOR
                   + " SIP/2.0\r\n")

        print("Enviando: " + mensaje)
        my_socket.send(bytes(mensaje, 'utf-8') + b'\r\n')
        data = my_socket.recv(1024)

    print("Terminando socket...")
my_socket.close()
print("Fin.")
