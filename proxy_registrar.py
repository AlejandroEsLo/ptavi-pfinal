#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Clase (y programa principal) para un servidor de eco en UDP simple."""

import socketserver
import sys
import socket
import json
import time
import random
import hashlib
from xml.dom import minidom
from uaclient import fich_log


class EchoHandler(socketserver.DatagramRequestHandler):
    """Echo server class."""

    register_clients = {}
    
    def register2json(self):
        """Guardar los clientes en un fichero registro Json."""
        json.dump(self.register_clients, open("registered.json", "w"))

    def json2registered(self):
        """Cargar fichero Json si existe para utilizarlo en el servidor."""
        try:
            registered_json = open("registered.json", "r")
            self.register_clients = json.load(registered_json)

        except FileNotFoundError:
            pass

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
            print("\nEl cliente nos manda ", ' '.join(mensaje_cliente))
            
            linea_coment = line.decode("utf-8").split("\r\n")
            Ip_client = str(self.client_address[0])
            Port_client = self.client_address[1]
            metodo = mensaje_cliente[0]

            # FALTA DEFINIR METODO REGISTER PARA PROXY !!!!!!!               
            if metodo == "REGISTER":
                expires = int(mensaje_cliente[3].split("\r\n")[0])
                cliente_sip = mensaje_cliente[1].split(":")[1]
                cliente_puerto = int(mensaje_cliente[1].split(":")[-1])

                if len(mensaje_cliente) == 4:
                # Register no autorizado, enviamos 401 Unauthorized
                    comentario = " ".join(linea_coment)
                    fich_log(log_path,"received",Ip_client,Port_client,comentario)
                    nonce = random.randint(0, 10**15)
                    
                    if cliente_sip in clients_passw:
                        clients_passw["nonce"] = nonce
                        respuesta_serv = ("SIP/2.0 401 Unauthorized\r\n"
                                        + "WWW Authenticate: Digest nonce="
                                        + "\"" + str(nonce) + "\"" + "\r\n")
                        print("Respuesta enviada: \n"+ respuesta_serv)
                        
                    else:
                        respuesta_serv = ("SIP/2.0 404 User Not Found\r\n\r\n")
                        print("El cliente no esta en la lista de contraseñas")
                    
                    self.wfile.write(bytes(respuesta_serv, "utf-8"))
                    comentario = respuesta_serv
                    fich_log(log_path,"sent_to",Ip_client,Port_client,comentario)
                       
                else:                
                    # Comprobamos la contraseña recibida para ver si es correcta
                    passw_hash = mensaje_cliente[-1].split("=")[-1]
                    passw_hash = passw_hash.split("\"")[1]
                    
                    comentario = " ".join(linea_coment)
                    fich_log(log_path,"received",Ip_client,Port_client,comentario)
                    print("\r\ncontraseña recibida= " + str(passw_hash))
                    h = hashlib.md5()
                    if cliente_sip in clients_passw:
                        h.update(bytes(clients_passw[cliente_sip], 'utf-8'))
                        h.update(bytes(str(clients_passw["nonce"]), 'utf-8'))
                    
                    nueva_contraseña = h.hexdigest()
                    print("contraseña creada para comparar= " +nueva_contraseña+ "\r\n")    
                    
                    if nueva_contraseña == passw_hash:
                        # Si coinciden las contraseñas , registramos el cliente
                        # Cogemos localtime para que sea conforme a nuestra hora local
                        t_inicio = time.strftime("%Y-%m-%d %H:%M:%S",
                                                time.localtime(int(time.time())))
                        t_expires = time.strftime("%Y-%m-%d %H:%M:%S",
                                              time.localtime(int(time.time() + expires)))
                        
                        self.list_serv = {}
                        usuarios_expires = []
                        self.list_serv["IP"] = Ip_client
                        self.list_serv["PUERTO"] = cliente_puerto              
                        self.list_serv["EXPIRES"] = t_expires
                        self.register_clients[cliente_sip] = self.list_serv
                        print(cliente_sip, "REGISTRADO\n")
                        # Eliminamos cliente si expires = 0
                        # O si su tiempo es menor que la hora actual
                        for clients in self.register_clients:
                            inf = self.register_clients[clients]
                            if inf["EXPIRES"] <= t_inicio:
                                usuarios_expires.append(clients)
                                
                        for usuario in usuarios_expires:
                            print(usuario.split(":")[-1], "EXPIRADO\n")
                            del self.register_clients[usuario]
                        
                        self.register2json()
                        
                        respuesta_serv = ("SIP/2.0 200 OK\r\n\r\n")
                        self.wfile.write(bytes(respuesta_serv, "utf-8"))
                        print("Usuario Registrado: {}".format(self.register_clients))
                        comentario = respuesta_serv
                        fich_log(log_path,"sent_to",Ip_client,Port_client,comentario)
                       
                    else:                        
                        respuesta_serv = ("SIP/2.0 401 Unauthorized\r\n"
                                        + "WWW Authenticate: Digest nonce="
                                        + "\"" + str(random.randint(0,10**15)) 
                                        + "\"" + "\r\n\r\n")
                        
                        print("Respuesta enviada: \n" + respuesta_serv)
                        self.wfile.write(bytes(respuesta_serv, "utf-8"))
                        comentario = " ".join(respuesta_serv)
                        fich_log(log_path,"sent_to",Ip_client,Port_client,comentario)   
                        
            elif metodo == "INVITE":
                comentario = " ".join(linea_coment)
                fich_log(log_path,"received",Ip_client,Port_client,comentario)                
                ip_destino = mensaje_cliente[1].split(":")[1]
                # Comprobamos si esta registrado el destinatario del mensaje en nuestra lista
                if ip_destino in self.register_clients:
                    #Si el cliente esta en nuestra lista....
                    ip_destinatario = (self.register_clients[ip_destino]["IP"])
                    puerto_destinatario =(self.register_clients[ip_destino]["PUERTO"])
                    
                    # Creamos el socket para conectarnos con el otro cliente
                    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
                        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        my_socket.connect((ip_destinatario, int(puerto_destinatario)))
                        fich_log(log_path,"sent_to",ip_destinatario,puerto_destinatario,comentario)                
                        
                        try: 
                            my_socket.send(line)
                            data = my_socket.recv(1024)

                            print('Recibido:')
                            print(data.decode('utf-8'))
                            
                            mensaje = data.decode("utf-8").split("\r\n")   
                            comentario = " ".join(mensaje)
            
                            fich_log(log_path,"received",ip_destinatario,puerto_destinatario,comentario)                
                            self.wfile.write(data)
                        
                        except ConnectionRefusedError:
                            comentario = ("No server listening at "+ ip_destinatario + " port "
                                            + str(puerto_destinatario))
                            fich_log(log_path, "error", ip_destinatario, puerto_destinatario, comentario)
                            print("Error: No server listening")
                            self.wfile.write(bytes("Error: No server listening", "utf-8"))
                else:
                    #Si el cliente NO esta en nuestra lista....
                    respuesta_serv = "SIP/2.0 404 User Not Found"
                    print("Usuario NO registrado {}".format(ip_destino))
                    print("\r\nEnviando:\r\n" + respuesta_serv)
                    self.wfile.write(bytes(respuesta_serv, "utf-8"))
                    mensaje = respuesta_serv.split("\r\n")
                    comentario = " ".join(mensaje)
                    fich_log(log_path,"sent_to",Ip_client,Port_client,comentario)
            # FALTA ACK Y BYE CORRECTO!!!!!!!!!!!
            elif metodo == "ACK":
                # aEjecutar es un string con lo que ejcutara en la shell
          #      aEjecutar = ("mp32rtp -i " + Ip + " -p 23032 < " + audio_path)
          #      print("Vamos a ejecutar", aEjecutar)
          #      os.system(aEjecutar)
                  print("ACK PROXY")

            elif metodo == "BYE":
                respuesta_serv = ("SIP/2.0 200 OK\r\n\r\n")
                self.wfile.write(bytes(respuesta_serv, "utf-8"))
                print("\r\nEnviando:\r\n" + respuesta_serv)
                self.wfile.write(bytes(respuesta_serv, "utf-8"))
                mensaje = respuesta_serv.split("\r\n")
                comentario = " ".join(mensaje)
                fich_log(log_path,"sent_to",Ip_client,Port_client,comentario)
                
            elif metodo != ["REGISTER","INVITE", "ACK", "BYE"]:
                respuesta_serv = ("SIP/2.0 405 Method Not Allowed\r\n\r\n")
                print("\r\nEnviando:\r\n" + respuesta_serv)
                self.wfile.write(bytes(respuesta_serv, "utf-8"))
                mensaje = respuesta_serv.split("\r\n")
                comentario = " ".join(mensaje)
                fich_log(log_path,"sent_to",Ip_client,Port_client,comentario)

            else:
                respuesta_serv = ("SIP/2.0 400 Bad Request\r\n\r\n")
                print("\r\nEnviando:\r\n" + respuesta_serv)
                self.wfile.write(bytes(respuesta_serv, "utf-8"))
                mensaje = respuesta_serv.split("\r\n")
                comentario = " ".join(mensaje)
                fich_log(log_path,"sent_to",Ip_client,Port_client,comentario)


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
    
    
    #Sacamos datos del fichero passwords.json
    with open("passwords.json","r") as fich_passw:
        clients_passw = {}
        fich_passw = json.loads(fich_passw.read())
        clients_passw = fich_passw
        
    
    # Creamos servidor de eco y escuchamos
    serv = socketserver.UDPServer((ip_serv, int(puerto_serv)), EchoHandler)
    print("Server " + serv_name + " listening at port " + puerto_serv + "...")
    # Empezamos a escribir fich_log
    fich_log(log_path,"starting",ip_serv,puerto_serv,"") 
            
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print("Finalizado servidor")
    
