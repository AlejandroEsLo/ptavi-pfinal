#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Programa cliente que abre un socket a un servidor."""

import socket
import sys
import time
from xml.dom import minidom
import hashlib

def fich_log(fich, evento, ip, port, coment):
    # Cogemos localtime para que sea conformea nuestra hora local
    hora = time.strftime("%Y%m%d%H%M%S",time.localtime(time.time()))
    fich = open(fich,"a" )
    fich.write(hora)

    if evento == "sent_to":
        fich.write(" Sent to " + ip + ":" + str(port) + ": " + coment + "\r\n")
    elif evento == "received":
        fich.write(" Received from " + ip + ":" + str(port) +
                    ": " + coment + "\r\n")
    elif evento == "error":
        fich.write(" Error: " + coment + "\r\n")
    elif evento == "starting":   
        fich.write(" Starting... "+ "\r\n")
    elif evento == "finishing":   
        fich.write(" Finishing... "+ "\r\n")
        
    fich.close()


if __name__ == "__main__":
    
    try:
        CONFIG = sys.argv[1]
        METODO = sys.argv[2]
        OPCION = sys.argv[3]
    except IndexError:
        sys.exit("Usage: python uaclient.py config method option")

        
    #SACAMOS DATOS DEL XML
    fich_xml = minidom.parse(CONFIG)
        
    account = fich_xml.getElementsByTagName("account")
    username = account[0].attributes["username"].value
    passwd = account[0].attributes["passwd"].value
        
    uaserver = fich_xml.getElementsByTagName("uaserver")
    ip = uaserver[0].attributes["ip"].value
    if not ip:
        ip = "127.0.0.1"
    
    puerto_serv = uaserver[0].attributes["puerto"].value
        
    rtpaudio = fich_xml.getElementsByTagName("rtpaudio")
    puerto_rtp = rtpaudio[0].attributes["puerto"].value
       
    regproxy = fich_xml.getElementsByTagName("regproxy")
    ip_proxy = regproxy[0].attributes["ip"].value
    puerto_proxy = regproxy[0].attributes["puerto"].value
        
    log = fich_xml.getElementsByTagName("log")
    log_path = log[0].attributes["path"].value
    
    audio = fich_xml.getElementsByTagName("audio")
    audio_path = audio[0].attributes["path"].value
        
    # Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        my_socket.connect((ip_proxy, int(puerto_proxy)))

        # Introducioms los METODOS
        if METODO == "register":
            # Empezamos a escribir fich_log
            fich_log(log_path,"starting",ip,puerto_serv,"") 
            # Contenido que vamos a enviar (sip:emisor:puerto SIP/2.0)
            mensaje = (METODO.upper() + " sip:" + username + ":" + puerto_serv 
                       + " SIP/2.0\r\n")
            cabecera = ("Expires: " + OPCION + "\r\n")
            mensaje += cabecera
            
        elif METODO == "invite":
            # Contenido que vamos a enviar (sip:receptor SIP/2.0)
            mensaje = (METODO.upper() + " sip:" + OPCION + " SIP/2.0\r\n")
            cabecera = ("Content-Type: application/sdp\r\n\r\n"
                        + "v=0\r\n"
                        + "o=" + username + " " + ip + "\r\n"
                        + "s=misesion" + "\r\n"
                        + "t=0" + "\r\n"
                        + "m=audio " + puerto_rtp + " RTP" + "\r\n")
            mensaje += cabecera
            
        elif METODO == "bye":
            # Contenido que vamos a enviar (sip:receptor SIP/2.0)
            mensaje = (METODO.upper() + " sip:" + OPCION + " SIP/2.0\r\n")
            
        else:
            sys.exit("Metodo no valido, utiliza : REGISTER,INVITE O BYE")
        
        print("\r\nEnviando:\r\n" + mensaje)
    
        # Escribimos lo que enviamos en fich_log    
        mensj = mensaje.split("\r\n")
        comentario = " ".join(mensj)
        fich_log(log_path, "sent_to", ip_proxy, puerto_proxy, comentario)    
        
        try:
            my_socket.send(bytes(mensaje, 'utf-8') + b'\r\n')
        
            data = my_socket.recv(1024)       
            recepcion = data.decode('utf-8').split("\r\n")
            #respuesta_serv = recepcion[0]
            # End para quitar espacio print
            
            print("Respuesta Recibida: \n" + data.decode('utf-8'))
                        
            
            if recepcion[0] == ("SIP/2.0 100 Trying\r\n\r\n"
                                    + "SIP/2.0 180 Ringing\r\n\r\n"
                                    + "SIP/2.0 200 OK\r\n\r\n"):
                METODO = "ACK"
                mensaje = (METODO.upper() + " sip:" + OPCION + " SIP/2.0\r\n")
        
                print("Enviando: \n" + mensaje)
                my_socket.send(bytes(mensaje, 'utf-8') + b'\r\n')
                data = my_socket.recv(1024)
                comentario = mensaje.split("\r\n")
                fich_log(log_path, "sent_to", ip_proxy, puerto_proxy, comentario)
            
            elif recepcion[0] == ("SIP/2.0 401 Unauthorized"):
                # Metemos cabecera autenticacion con la funcion HASH
                h = hashlib.md5()
                nonce = recepcion[1].split("=")[-1]
                nonce = nonce.split("\"")[1]
                h.update(bytes(passwd, 'utf-8'))
                h.update(bytes(nonce, 'utf-8'))
                
                mensaje = (METODO.upper() + " sip:" + username + ":" 
                        + puerto_serv + " SIP/2.0\r\n" + "Expires: " + OPCION 
                        + "\r\n" + "Authorization: Digest response=\"" 
                        + h.hexdigest() + "\"" + "\r\n")
        
                print("Enviando: \n" + mensaje)
                my_socket.send(bytes(mensaje, 'utf-8') + b'\r\n')
                comentario = mensaje.split("\r\n")
                comentario = " ".join(comentario)                
                fich_log(log_path, "sent_to", ip_proxy, puerto_proxy, comentario)
                data = my_socket.recv(1024)
                mensaje_recibido = data.decode('utf-8')
                
                print("Recibido: \n" + mensaje_recibido)
                comentario = mensaje_recibido.split("\r\n")
                comentario = " ".join(comentario)
                fich_log(log_path, "received", ip_proxy, puerto_proxy, comentario)
                
            print("Terminando socket...")
            my_socket.close()
            print("Fin.")
           
        except ConnectionRefusedError:
            comentario = ("No server listening at "+ ip_proxy + " port "
                          + puerto_proxy)
            fich_log(log_path, "error", ip_proxy, puerto_proxy, comentario)
            sys.exit("Error: No server listening")
