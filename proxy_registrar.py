#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Clase (y programa principal) para un servidor de eco en UDP simple."""

import socketserver
import sys
import os
from xml.dom import minidom
from uaclient import fich_log


class EchoHandler(socketserver.DatagramRequestHandler):
    """Echo server class."""


    # FALTA DEFINIR METODOS PARA PROXY Y CAMBIARLOS POR LOS QUE TENIAMOS EN LA P6
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

            if metodo == "INVITE":
                respuesta_serv = ("SIP/2.0 100 Trying\r\n\r\n"
                                  + "SIP/2.0 180 Ringing\r\n\r\n"
                                  + "SIP/2.0 200 OK\r\n\r\n")
                self.wfile.write(bytes(respuesta_serv, "utf-8"))

            elif metodo == "ACK":
                # aEjecutar es un string con lo que ejcutara en la shell
                aEjecutar = ("mp32rtp -i " + Ip + " -p 23032 < " + audio_path)
                print("Vamos a ejecutar", aEjecutar)
                os.system(aEjecutar)

            elif metodo == "BYE":
                respuesta_serv = ("SIP/2.0 200 OK\r\n\r\n")
                self.wfile.write(bytes(respuesta_serv, "utf-8"))

            elif metodo != ["INVITE", "ACK", "BYE"]:
                respuesta_serv = ("SIP/2.0 405 Method Not Allowed\r\n\r\n")
                self.wfile.write(bytes(respuesta_serv, "utf-8"))

            else:
                respuesta_serv = ("SIP/2.0 400 Bad Request\r\n\r\n")
                self.wfile.write(bytes(respuesta_serv, "utf-8"))


if __name__ == "__main__":
    
    try:
        CONFIG = sys.argv[1]
        
    except IndexError:
        sys.exit("Usage: python proxy_registrar.py config")
    
    #SACAMOS DATOS DEL XML PROXY
    fich_xml = minidom.parse(CONFIG)
        
    server = fich_xml.getElementsByTagName("server")
    serv_name = server[0].attributes["name"].value
    ip_serv = server[0].attributes["ip"].value
    if not ip_serv:
        ip_serv = "127.0.0.1"
    
    puerto_serv = server[0].attributes["puerto"].value
    
        
    database = fich_xml.getElementsByTagName("database")
    database_path = database[0].attributes["path"].value
    passwd_path = database[0].attributes["passwdpath"].value
       
    log = fich_xml.getElementsByTagName("log")
    log_path = log[0].attributes["path"].value
    
    # Creamos servidor de eco y escuchamos
    serv = socketserver.UDPServer((ip_serv, int(puerto_serv)), EchoHandler)
    print("Server MiServidorBigBang listening at port " + puerto_serv + "...")
    # Empezamos a escribir fich_log
    fich_log(log_path,"starting",ip_serv,puerto_serv,"") 
            
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print("Finalizado servidor")
