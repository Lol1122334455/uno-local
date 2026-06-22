import pygame
import socket
import threading
import json
import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from juego.protocolo import codificar, decodificar, crear_mensaje
from juego.partida_local import PartidaLocal
from juego.partida import EstadoPartida
from juego.sonido import GestorSonido
from ui.menu import Menu
from ui.sala_espera import SalaEspera
from ui.mesa import Mesa
from servidor import ServidorUNO

NEGRO = (0, 0, 0)
BLANCO = (255, 255, 255)
GRIS_CLARO = (140, 140, 140)
ROJO = (200, 40, 40)
VERDE = (40, 180, 40)
AMARILLO = (220, 200, 20)
COLOR_FONDO = (10, 10, 15)

VIRTUAL_W = 320
VIRTUAL_H = 240
SCALE = 3


class ClienteUNO:
    def __init__(self):
        self.socket = None
        self.conectado = False
        self.id_jugador = None
        self.es_host = False
        self.nombre = ""
        self.puerto = 5555
        self.estado_juego = None
        self.mi_mano = []
        self.pantalla_actual = "MENU"
        self.modo_actual = "CLASICO"
        self.jugadores_conectados = []
        self.mensajes_red = []
        self.corriendo = True
        self.buffer_red = ""
        self.lock = threading.Lock()
        self.partida_local = None
        self.es_local = False
        self.ultimo_turno_bot = -1
        self.tiempo_ultimo_bot = 0
        self.fullscreen = False
        self.sonido = GestorSonido()
        self.ultima_pantalla = None
        self.ultimo_ganador_visto = None
        self.servidor = None
        self.servidor_hilo = None
        self.version_actual = self._leer_version()
        self.verifico_actualizacion = False

    def conectar(self, ip, puerto, nombre):
        self.ultimo_error_red = None
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)
            self.socket.connect((ip, puerto))
            self.socket.settimeout(None)
            self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

            self.nombre = nombre
            self.puerto = puerto
            self._enviar(crear_mensaje("UNIRSE", nombre=nombre))

            hilo = threading.Thread(target=self._escuchar_red, daemon=True)
            hilo.start()
            self.es_local = False
            return True
        except Exception as e:
            self.ultimo_error_red = str(e)
            return False

    def _detener_servidor(self):
        if self.servidor:
            try: self.servidor.detener()
            except: pass
            self.servidor = None
            self.servidor_hilo = None

    def _leer_version(self):
        ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "VERSION")
        try:
            with open(ruta) as f:
                return f.read().strip()
        except:
            return "?"

    def _verificar_actualizacion(self):
        try:
            import urllib.request
            url = "https://raw.githubusercontent.com/Lol1122334455/uno-local/refs/heads/main/VERSION"
            req = urllib.request.Request(url, headers={"User-Agent": "UNO-Local/1.0"})
            with urllib.request.urlopen(req, timeout=5) as r:
                ultima = r.read().decode().strip()
            if ultima != self.version_actual:
                return ultima
        except:
            pass
        return None

    def iniciar_local(self, num_bots, modo):
        self.es_local = True
        self.partida_local = PartidaLocal(modo=modo, num_bots=num_bots,
                                          nombre_jugador=self.nombre)
        self.id_jugador = self.partida_local.id_humano
        self.modo_actual = modo
        self.pantalla_actual = "MESA"
        self.ultimo_turno_bot = -1

    def _enviar(self, mensaje):
        try:
            if self.socket:
                self.socket.sendall(codificar(mensaje))
        except:
            pass

    def _escuchar_red(self):
        buffer = ""
        while self.corriendo and self.socket:
            try:
                datos = self.socket.recv(4096)
                if not datos:
                    break
                buffer += datos.decode("utf-8")
                while "\n" in buffer:
                    linea, buffer = buffer.split("\n", 1)
                    if linea.strip():
                        with self.lock:
                            self.mensajes_red.append(linea.strip())
            except:
                break
        self.conectado = False

    def _procesar_mensajes(self):
        with self.lock:
            mensajes = list(self.mensajes_red)
            self.mensajes_red.clear()

        for msg_str in mensajes:
            try:
                msg = json.loads(msg_str)
            except:
                continue
            self._procesar_msg(msg)

    def _procesar_msg(self, msg):
        tipo = msg.get("tipo")

        if tipo == "ASIGNADO":
            self.id_jugador = msg["id"]
            self.es_host = msg.get("es_host", False)
            self.modo_actual = msg.get("modo", "CLASICO")
            self.pantalla_actual = "SALA"

        elif tipo == "JUGADOR_CONECTADO":
            self.jugadores_conectados = msg.get("jugadores", [])

        elif tipo == "JUGADOR_DESCONECTADO":
            pass

        elif tipo == "MODO_SELECCIONADO":
            self.modo_actual = msg.get("modo", self.modo_actual)

        elif tipo == "PARTIDA_INICIADA":
            pass

        elif tipo == "ESTADO_JUEGO" or "tu_mano" in msg:
            self.estado_juego = msg
            self.mi_mano = msg.get("tu_mano", [])
            self.pantalla_actual = "MESA"
            if msg.get("estado") == "TERMINADA":
                self.pantalla_actual = "VICTORIA"

        elif tipo == "TU_TURNO":
            pass

        elif tipo == "VICTORIA":
            self.estado_juego["estado"] = "TERMINADA"
            self.estado_juego["ganador"] = msg.get("id_ganador")

        elif tipo == "MENSAJE":
            print(f"[SERVIDOR] {msg.get('texto', '')}")

        elif tipo == "ERROR":
            print(f"[ERROR] {msg.get('mensaje', '')}")

    def _actualizar_local(self):
        if not self.partida_local:
            return

        if self.partida_local.esta_terminada():
            estado = self.partida_local.obtener_estado()
            self.estado_juego = estado
            self.mi_mano = estado.get("tu_mano", [])
            self.pantalla_actual = "VICTORIA"
            return

        if self.partida_local.esperando_humano():
            estado = self.partida_local.obtener_estado()
            self.estado_juego = estado
            self.mi_mano = estado.get("tu_mano", [])
            return

        if self.partida_local.partida.turno_actual != self.ultimo_turno_bot:
            self.ultimo_turno_bot = self.partida_local.partida.turno_actual
            self.tiempo_ultimo_bot = time.time()
            return

        if time.time() - self.tiempo_ultimo_bot < 0.5:
            return

        accion = self.partida_local.turno_bot()
        if accion:
            self.ultimo_turno_bot = self.partida_local.partida.turno_actual
            self.tiempo_ultimo_bot = time.time()

        estado = self.partida_local.obtener_estado()
        self.estado_juego = estado
        self.mi_mano = estado.get("tu_mano", [])

        if self.partida_local.esta_terminada():
            self.pantalla_actual = "VICTORIA"

    def _sincronizar_estado_local(self):
        if self.partida_local:
            estado = self.partida_local.obtener_estado()
            self.estado_juego = estado
            self.mi_mano = estado.get("tu_mano", [])

    def _toggle_fullscreen(self, ventana):
        self.fullscreen = not self.fullscreen
        flags = pygame.FULLSCREEN | pygame.SCALED if self.fullscreen else 0
        size = (VIRTUAL_W * SCALE, VIRTUAL_H * SCALE)
        return pygame.display.set_mode(size, flags=flags)

    def ejecutar(self):
        pygame.init()
        ventana = pygame.display.set_mode((VIRTUAL_W * SCALE, VIRTUAL_H * SCALE))
        pygame.display.set_caption("UNO - Pixel Retro  [F11 = pantalla completa]")
        reloj = pygame.time.Clock()

        canvas = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
        font_peq = pygame.font.SysFont("monospace", 8, bold=False)
        font_gde = pygame.font.SysFont("monospace", 28, bold=True)

        menu = Menu(canvas, font_peq, font_gde, scale=SCALE, sonido=self.sonido)
        sala = SalaEspera(canvas, font_peq, font_gde, scale=SCALE)
        mesa = Mesa(canvas, font_peq, font_gde, scale=SCALE, sonido=self.sonido)

        while self.corriendo:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    self.corriendo = False
                if evento.type == pygame.KEYDOWN and evento.key == pygame.K_F11:
                    ventana = self._toggle_fullscreen(ventana)

                if self.pantalla_actual == "MENU":
                    if not self.verifico_actualizacion:
                        self.verifico_actualizacion = True
                        ultima = self._verificar_actualizacion()
                        if ultima:
                            menu.hay_actualizacion = True
                            menu.mensaje = f"Actualizacion: v{self.version_actual} -> v{ultima}"
                        menu.version_actual = self.version_actual

                    accion = menu.manejar_evento(evento)
                    if accion == "ACTUALIZAR":
                        menu.actualizando = True
                        menu.mensaje = "Actualizando..."
                        try:
                            import subprocess
                            subprocess.run(["git", "pull", "origin", "main"],
                                          cwd=os.path.dirname(os.path.abspath(__file__)),
                                          timeout=30)
                            self.version_actual = self._leer_version()
                            menu.version_actual = self.version_actual
                            menu.hay_actualizacion = False
                            menu.mensaje = f"Actualizado a v{self.version_actual}!"
                        except Exception as e:
                            menu.mensaje = f"Error al actualizar: {e}"
                        menu.actualizando = False
                    elif accion == "CONECTAR":
                        self.sonido.play("click")
                        exito = self.conectar(menu.ip, int(menu.puerto), menu.nombre)
                        if not exito:
                            err = getattr(self, 'ultimo_error_red', '')
                            menu.mensaje = f"Error: {err}" if err else "No se pudo conectar!"
                            self.sonido.play("error")
                        else:
                            self.sonido.play("carta")
                    elif accion == "CREAR":
                        self.sonido.play("click")
                        try:
                            self.servidor = ServidorUNO(host="0.0.0.0",
                                                       puerto=int(menu.puerto),
                                                       max_jugadores=4)
                            self.servidor_hilo = threading.Thread(
                                target=self.servidor.iniciar, daemon=True)
                            self.servidor_hilo.start()
                            time.sleep(0.5)
                            exito = self.conectar("127.0.0.1", int(menu.puerto),
                                                  menu.nombre)
                            if exito:
                                self.es_host = True
                                self.sonido.play("carta")
                                self._enviar(crear_mensaje("INICIAR",
                                            auto_bots=True))
                            else:
                                self.servidor.detener()
                                self.servidor = None
                                err = getattr(self, 'ultimo_error_red', '')
                                menu.mensaje = f"Error: {err}" if err else "No se pudo conectar!"
                                self.sonido.play("error")
                        except Exception as e:
                            menu.mensaje = f"Error: {e}"
                            self.sonido.play("error")
                    elif accion and accion.startswith("UN_JUGADOR"):
                        self.sonido.play("click")
                        partes = accion.split(":")
                        num_bots = int(partes[1])
                        modo = partes[2]
                        self.nombre = menu.nombre
                        self.iniciar_local(num_bots, modo)

                elif self.pantalla_actual == "SALA":
                    accion = sala.manejar_evento(evento)
                    if accion == "INICIAR":
                        self._enviar(crear_mensaje("INICIAR"))
                    elif accion and accion.startswith("MODO:"):
                        modo = accion.split(":")[1]
                        self._enviar(crear_mensaje("SELECCIONAR_MODO", modo=modo))

                elif self.pantalla_actual == "MESA":
                    accion = mesa.manejar_evento(evento)
                    if accion:
                        partes = accion.split(":")
                        if partes[0] == "JUGAR":
                            id_carta = int(partes[1])
                            if self.es_local:
                                color = partes[2] if len(partes) > 2 else None
                                self.partida_local.jugar_humano(id_carta, color)
                                self._sincronizar_estado_local()
                            else:
                                if len(partes) > 2:
                                    color = partes[2]
                                    self._enviar(crear_mensaje("JUGAR", id_carta=id_carta,
                                                               color_elegido=color))
                                else:
                                    self._enviar(crear_mensaje("JUGAR", id_carta=id_carta))
                        elif partes[0] == "ROBAR":
                            if self.es_local:
                                self.partida_local.robar_humano()
                                self._sincronizar_estado_local()
                            else:
                                self._enviar(crear_mensaje("ROBAR"))
                        elif partes[0] == "UNO":
                            self.sonido.play("uno")
                            if self.es_local:
                                self.partida_local.gritar_uno_humano()
                            else:
                                self._enviar(crear_mensaje("GRITAR_UNO"))
                        elif partes[0] == "REANUDAR":
                            self.sonido.play("click")
                        elif partes[0] == "IR_MENU":
                            self.sonido.play("click")
                            self.pantalla_actual = "MENU"
                            self.es_local = False
                            self.partida_local = None
                            self.estado_juego = None
                            self.verifico_actualizacion = False
                            self._detener_servidor()
                            if self.socket:
                                try: self.socket.close()
                                except: pass
                                self.socket = None
                        elif partes[0] == "SALIR":
                            self.corriendo = False

                elif self.pantalla_actual == "VICTORIA":
                    if evento.type == pygame.KEYDOWN:
                        if evento.key == pygame.K_ESCAPE:
                            self.pantalla_actual = "MENU"
                            self.es_local = False
                            self.partida_local = None
                            self.estado_juego = None
                            self.verifico_actualizacion = False
                            self._detener_servidor()
                        elif evento.key == pygame.K_r:
                            self.sonido.play("click")
                            if self.es_local and self.partida_local:
                                modo = self.partida_local.modo_str
                                num_bots = len(self.partida_local.bots)
                                self.iniciar_local(num_bots, modo)

            if not self.es_local:
                self._procesar_mensajes()
            else:
                self._actualizar_local()

            if self.pantalla_actual == "VICTORIA" and self.pantalla_actual != self.ultima_pantalla:
                if self.estado_juego:
                    gid = self.estado_juego.get("ganador")
                    if gid == self.id_jugador:
                        self.sonido.play("victoria")
                    else:
                        self.sonido.play("derrota")
            if self.pantalla_actual == "MESA" and self.pantalla_actual != self.ultima_pantalla:
                self.sonido.play("carta")
            self.ultima_pantalla = self.pantalla_actual

            canvas.fill(COLOR_FONDO)

            if self.pantalla_actual == "MENU":
                menu.dibujar()
            elif self.pantalla_actual == "SALA":
                sala.actualizar(self.jugadores_conectados, self.es_host, self.modo_actual)
                sala.dibujar()
            elif self.pantalla_actual == "MESA":
                if self.estado_juego:
                    mesa.actualizar_estado(self.estado_juego, self.id_jugador)
                mesa.dibujar()
            elif self.pantalla_actual == "VICTORIA":
                canvas.fill(NEGRO)
                pygame.draw.rect(canvas, (36, 36, 48), (20, 40, 280, 160))
                pygame.draw.rect(canvas, GRIS_CLARO, (20, 40, 280, 160), 1)
                if self.estado_juego:
                    ganador_id = self.estado_juego.get("ganador")
                    jugadores = self.estado_juego.get("jugadores", [])
                    nom_gan = next((j["nombre"] for j in jugadores if j["id"] == ganador_id), "?")
                    if ganador_id == self.id_jugador:
                        txt = font_gde.render("GANASTE!", True, AMARILLO)
                        canvas.blit(txt, (VIRTUAL_W // 2 - txt.get_width() // 2, 55))
                        txt2 = font_peq.render(f"Eres el ganador!", True, BLANCO)
                    else:
                        txt = font_gde.render("PERDISTE!", True, ROJO)
                        canvas.blit(txt, (VIRTUAL_W // 2 - txt.get_width() // 2, 55))
                        txt2 = font_peq.render(f"Ganador: {nom_gan}", True, BLANCO)
                    canvas.blit(txt2, (VIRTUAL_W // 2 - txt2.get_width() // 2, 95))
                    txt3 = font_peq.render("R = Reiniciar    ESC = Menu", True, GRIS_CLARO)
                    canvas.blit(txt3, (VIRTUAL_W // 2 - txt3.get_width() // 2, 160))

            escalado = pygame.transform.scale(canvas, (VIRTUAL_W * SCALE, VIRTUAL_H * SCALE))
            ventana.blit(escalado, (0, 0))
            pygame.display.flip()
            reloj.tick(30)

        self._detener_servidor()
        pygame.quit()
        if self.socket:
            try:
                self.socket.close()
            except:
                pass


def main():
    import subprocess
    cliente = ClienteUNO()
    cliente.ejecutar()


if __name__ == "__main__":
    main()
