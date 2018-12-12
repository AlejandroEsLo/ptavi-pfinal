#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Clase (y programa principal) para un servidor de eco en UDP simple."""

import socketserver
import sys
import socket
import os
import json
import time
from xml.dom import minidom
from uaclient import fich_log


class EchoHandler(socketserver.DatagramRequestHandler):
    """Echo server class."""

    list_clients = {}
    
    def register2json(self):
        """Guardar los clientes en un fichero registro Json."""
        json.dump(self.list_clients, open("registered.json", "w"))

    def json2registered(self):
        """Cargar fichero Json si existe para utilizarlo en el servidor."""
        try:
            registered_json = open("registered.json", "r")
            self.list_clients = json.load(registered_json)

        except FileNotFoundError:
            pass


    # FALTA DEFINIR METODOS PARA PROXY Y CAMBIARLOS POR LOS QUE TENIAMOS EN LA P6
    def handle(self):
        """Manejador del servidor."""
        while 1:
            # Leyendo línea a línea lo que nos envía el cliente
            line = self.rfile.read()

            # Si no hay más líneas salimos del bucle infinito
            if not line:
                break
            
            """handle method of the server class."""
            self.json2registered()
            mensaje_cliente = line.decode("utf-8").split(" ")
            
            # Escribe dirección y puerto del cliente (de tupla client_address)
            print("El cliente nos manda ", ' '.join(mensaje_cliente))
    
            Ip = self.client_address[0]
            metodo = mensaje_cliente[0]
            
            if metodo == "REGISTER":
                expires = int(mensaje_cliente[3].split("\\")[0])
                # Cogemos localtime para que sea conformea nuestra hora local
                t_inicio = time.strftime("%Y-%m-%d %H:%M:%S",
                                        time.localtime(int(time.time())))
                t_expires = time.strftime("%Y-%m-%d %H:%M:%S",
                                      time.localtime(int(time.time() + expires)))

                self.list_serv = {}
                usuarios_expires = []
                self.list_serv["IP"] = Ip
                self.list_serv["EXPIRES"] = t_expires
               # self.list_clients[direccion] = self.list_serv
               # print(usuario, "REGISTRADO\n")
                # Eliminamos cliente si expires = 0
                # O si su tiempo es menor que la hora actual
                for clients in self.list_clients:
                    inf = self.list_clients[clients]
                    if inf["EXPIRES"] <= t_inicio:
                        usuarios_expires.append(clients)
    
                for usuario in usuarios_expires:
                    print(usuario.split(":")[-1], "EXPIRADO\n")
                    del self.list_clients[usuario]
    
                self.register2json()
                respuesta_serv = ("SIP/2.0 200 OK\r\n\r\n")
                self.wfile.write(bytes(respuesta_serv, "utf-8"))
        
                print("Lista clientes: {}".format(self.list_clients))
                print("Lista ELIMINADOS: {}\n".format(usuarios_expires))
           
        

            elif metodo == "INVITE":
                
                ip_destino = mensaje_cliente[1]
                respuesta_serv = ("SIP/2.0 100 Trying\r\n\r\n"
                                  + "SIP/2.0 180 Ringing\r\n\r\n"
                                  + "SIP/2.0 200 OK\r\n\r\n")
                 
                print("Ip Destino: {}".format(ip_destino))
                
                # Creamos el socket para conectarnos con el servidor
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
                    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                  #  my_socket.connect((ip_proxy, int(puerto_proxy)))
                    self.wfile.write(bytes(respuesta_serv, "utf-8"))

            elif metodo == "ACK":
                # aEjecutar es un string con lo que ejcutara en la shell
          #      aEjecutar = ("mp32rtp -i " + Ip + " -p 23032 < " + audio_path)
          #      print("Vamos a ejecutar", aEjecutar)
          #      os.system(aEjecutar)
                  print("ACK")

            elif metodo == "BYE":
                respuesta_serv = ("SIP/2.0 200 OK\r\n\r\n")
                self.wfile.write(bytes(respuesta_serv, "utf-8"))

            elif metodo != ["REGISTER","INVITE", "ACK", "BYE"]:
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
    print("Server " + serv_name + " listening at port " + puerto_serv + "...")
    # Empezamos a escribir fich_log
    fich_log(log_path,"starting",ip_serv,puerto_serv,"") 
            
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print("Finalizado servidor")
