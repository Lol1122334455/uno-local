import socket
import threading
import json
import sys

from juego.modos import MODOS
from juego.protocolo import codificar, decodificar, crear_mensaje
from juego.partida import EstadoPartida


class ServidorUNO:
    def __init__(self, host="0.0.0.0", puerto=5555, max_jugadores=4):
        self.host = host
        self.puerto = puerto
        self.max_jugadores = max_jugadores
        self.socket_servidor = None
        self.clientes = {}
        self.direcciones = {}
        self.hilos = {}
        self.partida = None
        self.modo_actual = "CLASICO"
        self.id_host = None
        self.corriendo = True

    def iniciar(self):
        self.socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket_servidor.bind((self.host, self.puerto))
        self.socket_servidor.listen(10)
        print(f"Servidor UNO iniciado en {self.host}:{self.puerto}")
        print("Esperando jugadores...")

        while self.corriendo:
            try:
                cliente_socket, direccion = self.socket_servidor.accept()
                hilo = threading.Thread(target=self._manejar_cliente,
                                        args=(cliente_socket, direccion),
                                        daemon=True)
                hilo.start()
            except:
                break

        for hilo in self.hilos.values():
            hilo.join(timeout=1)
        self.socket_servidor.close()

    def _manejar_cliente(self, cliente_socket, direccion):
        buffer = ""
        try:
            while self.corriendo:
                datos = cliente_socket.recv(4096)
                if not datos:
                    break
                buffer += datos.decode("utf-8")
                while "\n" in buffer:
                    linea, buffer = buffer.split("\n", 1)
                    if linea.strip():
                        self._procesar_mensaje(cliente_socket, linea.strip())
        except:
            pass
        finally:
            self._desconectar_cliente(cliente_socket)

    def _procesar_mensaje(self, cliente_socket, mensaje_str):
        try:
            msg = json.loads(mensaje_str)
        except:
            return

        tipo = msg.get("tipo")

        if tipo == "UNIRSE":
            nombre = msg.get("nombre", "Desconocido")
            if self.partida and self.partida.estado != EstadoPartida.ESPERANDO:
                self._enviar(cliente_socket, crear_mensaje("ERROR", mensaje="Partida ya iniciada"))
                return

            if len(self.clientes) >= self.max_jugadores:
                self._enviar(cliente_socket, crear_mensaje("ERROR", mensaje="Sala llena"))
                return

            id_jug = len(self.clientes)
            if self.partida is None:
                from juego.modos import MODOS
                modo_cls = MODOS.get(self.modo_actual)
                if modo_cls:
                    self.partida = modo_cls(max_jugadores=self.max_jugadores)

            self.partida.agregar_jugador(nombre)
            self.clientes[cliente_socket] = id_jug
            self.direcciones[id_jug] = direccion = cliente_socket.getpeername()

            if self.id_host is None:
                self.id_host = id_jug

            self._enviar(cliente_socket, crear_mensaje("ASIGNADO", id=id_jug,
                         nombre=nombre, es_host=(id_jug == self.id_host),
                         modo=self.modo_actual))

            self._broadcast(crear_mensaje("JUGADOR_CONECTADO", id=id_jug,
                            nombre=nombre,
                            jugadores=[j.to_dict(ocultar_mano=True)
                                       for j in self.partida.jugadores]))

            print(f"{nombre} se conectó (ID: {id_jug})")

        elif tipo == "SELECCIONAR_MODO":
            modo = msg.get("modo", "CLASICO")
            if modo in MODOS and self.partida and self.partida.estado == EstadoPartida.ESPERANDO:
                self.modo_actual = modo
                modo_cls = MODOS[modo]
                jugadores_actuales = [j.nombre for j in self.partida.jugadores]
                self.partida = modo_cls(max_jugadores=self.max_jugadores)
                for nombre in jugadores_actuales:
                    self.partida.agregar_jugador(nombre)
                self._broadcast(crear_mensaje("MODO_SELECCIONADO", modo=modo))

        elif tipo == "INICIAR":
            id_jug = self.clientes.get(cliente_socket)
            if id_jug != self.id_host:
                self._enviar(cliente_socket, crear_mensaje("ERROR",
                            mensaje="Solo el host puede iniciar"))
                return

            if len(self.partida.jugadores) < 2:
                self._enviar(cliente_socket, crear_mensaje("ERROR",
                            mensaje="Se necesitan al menos 2 jugadores"))
                return

            if self.partida.iniciar():
                self._broadcast_partida_iniciada()
                self._enviar_turno()
            else:
                self._enviar(cliente_socket, crear_mensaje("ERROR",
                            mensaje="No se pudo iniciar la partida"))

        elif tipo == "JUGAR":
            if not self.partida or self.partida.estado != EstadoPartida.JUGANDO:
                return

            id_jug = self.clientes.get(cliente_socket)
            id_carta = msg.get("id_carta")
            color_elegido = msg.get("color_elegido")

            if id_jug is None:
                return

            if id_jug != self.partida.turno_actual:
                self._enviar(cliente_socket, crear_mensaje("ERROR", mensaje="No es tu turno"))
                return

            resultado, mensaje = self.partida.jugar_carta(id_jug, id_carta, color_elegido)

            if resultado:
                if mensaje == "VICTORIA":
                    self._broadcast(crear_mensaje("VICTORIA",
                                    id_ganador=id_jug,
                                    nombre=self.partida.jugadores[id_jug].nombre))
                elif mensaje == "VICTORIA_HUMANO":
                    self._broadcast(crear_mensaje("VICTORIA",
                                    id_ganador=id_jug,
                                    nombre=self.partida.jugadores[id_jug].nombre,
                                    tipo="humano"))
                else:
                    self._broadcast_estado()
                    self._enviar_turno()
            else:
                self._enviar(cliente_socket, crear_mensaje("ERROR", mensaje=mensaje))

        elif tipo == "ROBAR":
            if not self.partida or self.partida.estado != EstadoPartida.JUGANDO:
                return

            id_jug = self.clientes.get(cliente_socket)
            if id_jug is None:
                return

            if id_jug != self.partida.turno_actual:
                self._enviar(cliente_socket, crear_mensaje("ERROR", mensaje="No es tu turno"))
                return

            carta, mensaje = self.partida.robar_carta(id_jug)
            if carta:
                self._broadcast_estado()
                self._enviar_turno()
            else:
                self._enviar(cliente_socket, crear_mensaje("ERROR", mensaje=mensaje))

        elif tipo == "GRITAR_UNO":
            id_jug = self.clientes.get(cliente_socket)
            if id_jug is not None:
                self.partida.gritar_uno(id_jug)
                self._broadcast(crear_mensaje("MENSAJE", texto=f"{self.partida.jugadores[id_jug].nombre} gritó UNO!"))

        elif tipo == "DESAFIAR":
            id_jug = self.clientes.get(cliente_socket)
            if id_jug is not None:
                self._broadcast(crear_mensaje("MENSAJE",
                                texto=f"{self.partida.jugadores[id_jug].nombre} desafió!"))

    def _enviar_turno(self):
        if self.partida and self.partida.estado == EstadoPartida.JUGANDO:
            id_turno = self.partida.turno_actual
            for sock, id_jug in self.clientes.items():
                if id_jug == id_turno:
                    self._enviar(sock, crear_mensaje("TU_TURNO"))

    def _enviar(self, cliente_socket, mensaje_dict):
        try:
            cliente_socket.sendall(codificar(mensaje_dict))
        except:
            pass

    def _broadcast(self, mensaje_dict, excluir=None):
        datos = codificar(mensaje_dict)
        for sock in list(self.clientes.keys()):
            if sock != excluir:
                try:
                    sock.sendall(datos)
                except:
                    pass

    def _broadcast_estado(self):
        if not self.partida:
            return
        for sock, id_jug in self.clientes.items():
            estado = self.partida.get_estado_dict(para_jugador=id_jug)
            self._enviar(sock, estado)

    def _broadcast_partida_iniciada(self):
        for sock, id_jug in self.clientes.items():
            estado = self.partida.get_estado_dict(para_jugador=id_jug)
            self._enviar(sock, crear_mensaje("PARTIDA_INICIADA"))
            self._enviar(sock, estado)

    def _desconectar_cliente(self, cliente_socket):
        if cliente_socket in self.clientes:
            id_jug = self.clientes[cliente_socket]
            nombre = self.partida.jugadores[id_jug].nombre if self.partida else "?"
            del self.clientes[cliente_socket]
            print(f"{nombre} se desconectó")
            if self.partida:
                self.partida.jugadores[id_jug].conectado = False
                self._broadcast(crear_mensaje("JUGADOR_DESCONECTADO",
                                id=id_jug, nombre=nombre))
            if id_jug == self.id_host and self.clientes:
                nuevos_ids = list(self.clientes.values())
                if nuevos_ids:
                    self.id_host = nuevos_ids[0]
                    nuevas_socks = [s for s, i in self.clientes.items() if i == self.id_host]
                    if nuevas_socks:
                        self._enviar(nuevas_socks[0], crear_mensaje("ASIGNADO",
                                     id=self.id_host, es_host=True,
                                     nombre=self.partida.jugadores[self.id_host].nombre,
                                     modo=self.modo_actual))

        try:
            cliente_socket.close()
        except:
            pass

    def detener(self):
        self.corriendo = False
        if self.socket_servidor:
            try:
                self.socket_servidor.close()
            except:
                pass


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Servidor UNO Multijugador")
    parser.add_argument("--host", default="0.0.0.0", help="IP del servidor")
    parser.add_argument("--puerto", type=int, default=5555, help="Puerto")
    parser.add_argument("--max", type=int, default=4, help="Máximo de jugadores")
    args = parser.parse_args()

    servidor = ServidorUNO(host=args.host, puerto=args.puerto, max_jugadores=args.max)
    try:
        servidor.iniciar()
    except KeyboardInterrupt:
        print("\nServidor detenido")
        servidor.detener()


if __name__ == "__main__":
    main()
