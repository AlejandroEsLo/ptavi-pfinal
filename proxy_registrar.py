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
    emisor = [0, 0]  # SIP y PUERTO del emisor

    def handle(self):
        """Manejador del servidor."""
        self.json2registered()  # Reestablecer los usuarios conectados

        Ip_client = str(self.client_address[0])
        Port_client = self.client_address[1]
        while 1:
            # Leyendo línea a línea lo que nos envía el cliente
            line = self.rfile.read()

            # Si no hay más líneas salimos del bucle infinito
            if not line:
                break

            mensaje_cliente = line.decode("utf-8").split(" ")

            # Escribe dirección y puerto del cliente (de tupla client_address)
            print("\nEl cliente nos manda ", ' '.join(mensaje_cliente))

            linea_coment = line.decode("utf-8").split("\r\n")
            metodo = mensaje_cliente[0]

            if metodo == "REGISTER":
                expires = int(mensaje_cliente[3].split("\r\n")[0])
                cliente_sip = mensaje_cliente[1].split(":")[1]
                cliente_puerto = int(mensaje_cliente[1].split(":")[-1])

                if len(mensaje_cliente) == 4:
                    # Register no autorizado, enviamos 401 Unauthorized
                    comentario = " ".join(linea_coment)
                    fich_log(log_path, "received", Ip_client, cliente_puerto,
                             comentario)
                    nonce = random.randint(0, 10**15)

                    if cliente_sip in clients_passw:
                        clients_passw["nonce"] = nonce
                        respuesta_serv = ("SIP/2.0 401 Unauthorized\r\n"
                                          + "WWW Authenticate: Digest nonce="
                                          + "\"" + str(nonce) + "\"" + "\r\n")
                        print("Respuesta enviada: \n" + respuesta_serv)

                    else:
                        respuesta_serv = ("SIP/2.0 404 User Not Found\r\n\r\n")
                        print("El cliente no esta en la lista de contraseñas")

                    self.wfile.write(bytes(respuesta_serv, "utf-8"))
                    comentario = respuesta_serv
                    fich_log(log_path, "sent_to", Ip_client, cliente_puerto,
                             comentario)

                else:
                    # Comprobamos la contraseña recibida
                    passw_hash = mensaje_cliente[-1].split("=")[-1]
                    passw_hash = passw_hash.split("\"")[1]

                    comentario = " ".join(linea_coment)
                    fich_log(log_path, "received", Ip_client, cliente_puerto,
                             comentario)
                    print("\r\ncontraseña recibida= " + str(passw_hash))
                    h = hashlib.md5()
                    if cliente_sip in clients_passw:
                        h.update(bytes(clients_passw[cliente_sip], 'utf-8'))
                        h.update(bytes(str(clients_passw["nonce"]), 'utf-8'))

                    nueva_contraseña = h.hexdigest()
                    print("contraseña creada para comparar= "
                          + nueva_contraseña + "\r\n")

                    if nueva_contraseña == passw_hash:
                        # Si coinciden las contraseñas , registramos el cliente
                        # Cogemos localtime para que sea nuestra hora local
                        time1 = time.localtime(int(time.time()))
                        time2 = time.localtime(int(time.time() + expires))
                        t_inicio = time.strftime("%Y-%m-%d %H:%M:%S", time1)
                        t_expires = time.strftime("%Y-%m-%d %H:%M:%S", time2)

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
                        archv_reg = self.register_clients
                        respuesta_serv = ("SIP/2.0 200 OK\r\n\r\n")
                        self.wfile.write(bytes(respuesta_serv, "utf-8"))
                        print("Usuario Registrado: {}".format(archv_reg))
                        comentario = respuesta_serv
                        fich_log(log_path, "sent_to", Ip_client,
                                 cliente_puerto, comentario)

                    else:
                        rand = 10**15
                        respuesta_serv = ("SIP/2.0 401 Unauthorized\r\n"
                                          + "WWW Authenticate: Digest nonce="
                                          + "\"" + str(random.randint(0, rand))
                                          + "\"" + "\r\n\r\n")

                        print("Respuesta enviada: \n" + respuesta_serv)
                        self.wfile.write(bytes(respuesta_serv, "utf-8"))
                        comentario = " ".join(respuesta_serv)
                        fich_log(log_path, "sent_to", Ip_client, Port_client,
                                 comentario)

            elif metodo == "INVITE":
                ip_destino = mensaje_cliente[1].split(":")[1]
                # Comprobamos si esta registrado en nuestra lista
                if ip_destino in self.register_clients:
                    # Si el cliente esta en nuestra lista....
                    archv_reg = self.register_clients
                    ip_destinatario = (archv_reg[ip_destino]["IP"])
                    puerto_destinatario = (archv_reg[ip_destino]["PUERTO"])
                    comentario = " ".join(linea_coment)

                    mensaje_emisor = line.decode("utf-8").split("\r\n")
                    mensaje_emisor = mensaje_emisor[4].split(" ")
                    cliente_emisor = mensaje_emisor[0].split("=")[1]

                    puerto_emisor = (archv_reg[cliente_emisor]["PUERTO"])

                    self.emisor[0] = cliente_emisor
                    self.emisor[1] = puerto_emisor

                    fich_log(log_path, "received", Ip_client,
                             puerto_emisor, comentario)
                    # Creamos el socket para conectarnos con el otro cliente
                    socket1 = socket.AF_INET
                    socket2 = socket.SOCK_DGRAM
                    with socket.socket(socket1, socket2) as my_socket:
                        my_socket.setsockopt(socket.SOL_SOCKET,
                                             socket.SO_REUSEADDR, 1)
                        my_socket.connect((ip_destinatario,
                                           int(puerto_destinatario)))
                        fich_log(log_path, "sent_to", ip_destinatario,
                                 puerto_destinatario, comentario)

                        try:
                            my_socket.send(line)
                            data = my_socket.recv(1024)

                            print('Recibido:')
                            print(data.decode('utf-8'))

                            mensaje = data.decode("utf-8").split("\r\n")
                            comentario = " ".join(mensaje)

                            fich_log(log_path, "received", ip_destinatario,
                                     puerto_destinatario, comentario)
                            self.wfile.write(data)

                            fich_log(log_path, "sent_to", Ip_client,
                                     puerto_emisor, comentario)

                        except ConnectionRefusedError:
                            comentario = ("No server listening at "
                                          + ip_destinatario + " port "
                                          + str(puerto_destinatario))
                            fich_log(log_path, "error", ip_destinatario,
                                     puerto_destinatario, comentario)
                            error = "Error: No server listening"
                            print(error)
                            self.wfile.write(bytes(error, "utf-8"))
                else:
                    # Si el cliente NO esta en nuestra lista....
                    respuesta_serv = "SIP/2.0 404 User Not Found"
                    print("Usuario NO registrado {}".format(ip_destino))
                    print("\r\nEnviando:\r\n" + respuesta_serv)
                    self.wfile.write(bytes(respuesta_serv, "utf-8"))
                    mensaje = respuesta_serv.split("\r\n")
                    comentario = " ".join(mensaje)
                    fich_log(log_path, "sent_to", Ip_client, Port_client,
                             comentario)

            elif metodo == "ACK":
                mensaje = line.decode("utf-8").split("\r\n")
                comentario = " ".join(mensaje)
                ip_destino = mensaje_cliente[1].split(":")[1]
                archv_reg = self.register_clients
                ip_destinatario = (archv_reg[ip_destino]["IP"])
                puerto_destinatario = (archv_reg[ip_destino]["PUERTO"])
                puerto_emisor = int(self.emisor[1])
                fich_log(log_path, "received", ip_destinatario,
                         puerto_emisor, comentario)

                socket1 = socket.AF_INET
                socket2 = socket.SOCK_DGRAM
                with socket.socket(socket1, socket2) as my_socket:
                    my_socket.setsockopt(socket.SOL_SOCKET,
                                         socket.SO_REUSEADDR, 1)
                    my_socket.connect((ip_destinatario,
                                       int(puerto_destinatario)))
                    my_socket.send(line)
                    print("\r\nEnviando:\r\n" + comentario)
                    mensaje = line.decode("utf-8").split("\r\n")
                    comentario = " ".join(mensaje)
                    fich_log(log_path, "sent_to", Ip_client,
                             puerto_destinatario, comentario)

            elif metodo == "BYE":
                mensaje = line.decode("utf-8").split("\r\n")
                comentario = " ".join(mensaje)
                ip_destino = mensaje_cliente[1].split(":")[1]
                puerto_emisor = int(self.emisor[1])

                if ip_destino in self.register_clients:
                    # Si el cliente esta en nuestra lista....
                    archv_reg = self.register_clients
                    ip_destinatario = (archv_reg[ip_destino]["IP"])
                    puerto_destinatario = (archv_reg[ip_destino]["PUERTO"])

                    fich_log(log_path, "received", ip_destinatario,
                             puerto_emisor, comentario)

                    socket1 = socket.AF_INET
                    socket2 = socket.SOCK_DGRAM
                    with socket.socket(socket1, socket2) as my_socket:
                        my_socket.setsockopt(socket.SOL_SOCKET,
                                             socket.SO_REUSEADDR, 1)
                        my_socket.connect((ip_destinatario,
                                           int(puerto_destinatario)))
                        my_socket.send(line)

                        print("\r\nEnviando:\r\n" + comentario)
                        mensaje = line.decode("utf-8").split("\r\n")
                        comentario = " ".join(mensaje)
                        fich_log(log_path, "sent_to", ip_destinatario,
                                 puerto_destinatario, comentario)

                        data = my_socket.recv(1024)
                        mensaje = data.decode("utf-8").split("\r\n")
                        comentario = " ".join(mensaje)
                        fich_log(log_path, "received", ip_destinatario,
                                 puerto_destinatario, comentario)
                        print("\r\nRecibido:\r\n" + comentario)
                        fich_log(log_path, "sent_to", ip_destinatario,
                                 puerto_emisor, comentario)
                        self.wfile.write(data)

                else:  # Si el cliente no esta registrado

                    print("Usuario " + ip_destino + " no registrado")
                    respuesta_serv = ("SIP/2.0 404 User Not Found")
                    self.wfile.write(bytes(respuesta_serv, "utf-8"))

                    print("\r\nEnviando:\r\n" + respuesta_serv)
                    self.wfile.write(bytes(respuesta_serv, "utf-8"))
                    mensaje = respuesta_serv.split("\r\n")
                    comentario = " ".join(mensaje)
                    fich_log(log_path, "sent_to", Ip_client, Port_client,
                             comentario)

            elif metodo != ["REGISTER", "INVITE", "ACK", "BYE"]:
                mensaje = data.decode("utf-8").split("\r\n")
                comentario = " ".join(mensaje)

                fich_log(log_path, "received", ip_destinatario,
                         puerto_destinatario, comentario)
                self.wfile.write(data)
                respuesta_serv = ("SIP/2.0 405 Method Not Allowed\r\n\r\n")
                print("\r\nEnviando:\r\n" + respuesta_serv)
                self.wfile.write(bytes(respuesta_serv, "utf-8"))
                mensaje = respuesta_serv.split("\r\n")
                comentario = " ".join(mensaje)
                fich_log(log_path, "sent_to", Ip_client, Port_client,
                         comentario)

            else:
                mensaje = data.decode("utf-8").split("\r\n")
                comentario = " ".join(mensaje)

                fich_log(log_path, "received", ip_destinatario,
                         puerto_destinatario, comentario)
                self.wfile.write(data)
                respuesta_serv = ("SIP/2.0 400 Bad Request\r\n\r\n")
                print("\r\nEnviando:\r\n" + respuesta_serv)
                self.wfile.write(bytes(respuesta_serv, "utf-8"))
                mensaje = respuesta_serv.split("\r\n")
                comentario = " ".join(mensaje)
                fich_log(log_path, "sent_to", Ip_client, Port_client,
                         comentario)


if __name__ == "__main__":

    try:
        CONFIG = sys.argv[1]

    except IndexError:
        sys.exit("Usage: python proxy_registrar.py config")

    # SACAMOS DATOS DEL XML PROXY
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

    # Sacamos datos del fichero passwords.json
    with open("passwords.json", "r") as fich_passw:
        clients_passw = {}
        fich_passw = json.loads(fich_passw.read())
        clients_passw = fich_passw

    # Creamos servidor de eco y escuchamos
    serv = socketserver.UDPServer((ip_serv, int(puerto_serv)), EchoHandler)
    print("Server " + serv_name + " listening at port " + puerto_serv + "...")
    # Empezamos a escribir fich_log
    fich_log(log_path, "starting", ip_serv, puerto_serv, "")

    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print("Finalizado servidor")
