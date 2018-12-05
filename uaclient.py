#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Programa cliente que abre un socket a un servidor."""

import socket
import sys
import time
from xml.dom import minidom

def fich_log(fich,evento,ip,port,coment):
    # Cogemos localtime para que sea conformea nuestra hora local
    hora = time.strftime("%Y%m%d%H%M%S",time.localtime(int(time.time())))
    fich = open(fich,"a" )
    fich.write(hora())
    fin = "\r\n"

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
    CONFIG = sys.argv[1]
    METODO = sys.argv[2]
    OPCION = sys.argv[3]
except IndexError:
    sys.exit("Usage: python3 client.py method receiver@IP:SIPport")


    #SACAMOS DATOS DEL XML
    fich_xml = minidom.parse(CONFIG)
    
    account = fich_xml.getElementsByTagName("account")
    username = account[0].attributes["username"].value
    passwd = account[0].attributes["passwd"].value
    
    uaserver = fich_xml.getElementsByTagName("uaserver")
    ip = uaserver[0].attributes["ip"].value
    puerto_serv = uaserver[0].attributes["puerto"].value
    
    rtpaudio = fich_xml.getElementsByTagName("rtpaudio")
    puerto_rtp = rtpaudio[0].attributes["puerto"].value
   
    regproxy = fich_xml.getElementsByTagName("regproxy")
    ip_proxy = regproxy[0].attributes["ip"].value
    puerto_proxy = regproxy[0].attributes["puerto"].value
    
    print("passwd: "+ puerto_proxy)
    
# Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.connect((ip_proxy, puerto_proxy))
    # Contenido que vamos a enviar
    mensaje = (METODO.upper() + " sip:" + username + "@" + ip +
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
