#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Clase (y programa principal) para un servidor de eco en UDP simple."""

import socketserver
import sys
import os
import socket
from xml.dom import minidom
from uaclient import fich_log


class EchoHandler(socketserver.DatagramRequestHandler):
    """Echo server class."""

    def handle(self):
        """Manejador del servidor."""
            
        while 1:
            # Leyendo línea a línea lo que nos envía el cliente
            line = self.rfile.read()

            # Si no hay más líneas salimos del bucle infinito
            if not line:
                break

            # Escribe dirección y puerto del cliente (de tupla client_address)
            print("El cliente nos manda " + line.decode('utf-8'))
            
            mensaje_cliente = line.decode("utf-8").split(" ")
            metodo = mensaje_cliente[0]
            Ip = self.client_address[0]
            Puerto = int(self.client_address[1])
            
            mensaje = line.decode("utf-8").split("\r\n")   
            comentario = " ".join(mensaje)
            # Escribimos lo que vamos recibiendo
            fich_log(log_path,"received",Ip,Puerto,comentario) 
        

            if metodo == "INVITE":
                respuesta_serv = ("SIP/2.0 100 Trying\r\n\r\n"
                                  + "SIP/2.0 180 Ringing\r\n\r\n"
                                  + "SIP/2.0 200 OK\r\n\r\n")
                cabecera = ("Content-Type: application/sdp\r\n\r\n"
                        + "v=0\r\n"
                        + "o=" + username + " " + ip + "\r\n"
                        + "s=misesion" + "\r\n"
                        + "t=0" + "\r\n"
                        + "m=audio " + puerto_rtp + " RTP" + "\r\n")
                
                respuesta_serv += cabecera

                print("Respuesta Enviada: " + respuesta_serv)

                self.wfile.write(bytes(respuesta_serv, "utf-8"))
                respuesta_serv = respuesta_serv.split("\r\n")
                comentario = " ".join(respuesta_serv)
                fich_log(log_path,"sent_to",Ip,Puerto,comentario) 
            
            # FALTAA METODO ACK !!!!!!!!!!!!!!!!
            elif metodo == "ACK":
                # aEjecutar es un string con lo que ejcutara en la shell
                aEjecutar = ("mp32rtp -i " + Ip + " -p 23032 < " + audio_path)
                print("Vamos a ejecutar", aEjecutar)
                os.system(aEjecutar)

            elif metodo == "BYE":
                respuesta_serv = ("SIP/2.0 200 OK\r\n\r\n")
                print("Respuesta Enviada: " + respuesta_serv)
                self.wfile.write(bytes(respuesta_serv, "utf-8"))
                respuesta_serv = respuesta_serv.split("\r\n")
                comentario = " ".join(respuesta_serv)
                fich_log(log_path,"sent_to",Ip,Puerto,comentario) 
                fich_log(log_path,"finishing",Ip,Puerto,"") 
        
            elif metodo != ["INVITE", "ACK", "BYE"]:
                respuesta_serv = ("SIP/2.0 405 Method Not Allowed\r\n\r\n")
                self.wfile.write(bytes(respuesta_serv, "utf-8"))
                respuesta_serv = respuesta_serv.split("\r\n")
                comentario = " ".join(respuesta_serv)
                fich_log(log_path,"sent_to",Ip,Puerto,comentario) 
                
            else:
                respuesta_serv = ("SIP/2.0 400 Bad Request\r\n\r\n")
                self.wfile.write(bytes(respuesta_serv, "utf-8"))
                respuesta_serv = respuesta_serv.split("\r\n")
                comentario = " ".join(respuesta_serv)
                fich_log(log_path,"sent_to",Ip,Puerto,comentario) 
                

if __name__ == "__main__":
    
    try:
        CONFIG = sys.argv[1]
        
    except IndexError:
        sys.exit("Usage: python uaserver.py config")
        
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
    
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        my_socket.connect((ip_proxy, int(puerto_proxy)))
    
        # Creamos servidor de eco y escuchamos
        serv = socketserver.UDPServer((ip, int(puerto_serv)), EchoHandler)
        print("Listening...")
        # Empezamos a escribir fich_log
        fich_log(log_path,"starting",ip,puerto_serv,"") 
        
        try:
            serv.serve_forever()
        except KeyboardInterrupt:
            print("Finalizado servidor")
