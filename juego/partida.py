from juego.cartas import Carta, Mazo, Color, TipoCarta
from juego.jugador import Jugador
from enum import Enum
import random


class EstadoPartida(Enum):
    ESPERANDO = "ESPERANDO"
    JUGANDO = "JUGANDO"
    TERMINADA = "TERMINADA"


class ModoJuego(Enum):
    CLASICO = "CLASICO"
    RELAMPAGO = "RELAMPAGO"
    CAOS = "CAOS"
    DUELO = "DUELO"
    ZOMBIE = "ZOMBIE"


class EventoCaos(Enum):
    TORBELLINO = "TORBELLINO"
    INTERCAMBIO = "INTERCAMBIO"
    VISION = "VISION"
    BOMBA = "BOMBA"
    OSCURIDAD = "OSCURIDAD"
    DADO = "DADO"
    SUERTE = "SUERTE"
    MALDICION = "MALDICION"
    ESTRELLA = "ESTRELLA"
    CAOS_TOTAL = "CAOS_TOTAL"


EVENTOS_CAOS = list(EventoCaos)


class Partida:
    def __init__(self, modo=ModoJuego.CLASICO, max_jugadores=4):
        self.modo = modo
        self.max_jugadores = max_jugadores
        self.jugadores = []
        self.mazo = None
        self.descarte = []
        self.carta_activa = None
        self.color_activo = None
        self.turno_actual = 0
        self.sentido = 1
        self.estado = EstadoPartida.ESPERANDO
        self.ganador = None
        self.ultima_accion = None
        self.eventos_pendientes = []
        self.turnos_sin_jugar = {}
        self.penalizacion_actual = None

        self.mazo_eventos = []

    def agregar_jugador(self, nombre):
        if self.estado != EstadoPartida.ESPERANDO:
            return None
        if len(self.jugadores) >= self.max_jugadores:
            return None
        id_jug = len(self.jugadores)
        jug = Jugador(id_jug, nombre)
        self.jugadores.append(jug)
        return id_jug

    def iniciar(self):
        if len(self.jugadores) < 2:
            return False

        self.mazo = Mazo(incluir_nuevas=(self.modo != ModoJuego.CLASICO))
        self.mazo.reiniciar()
        self.descarte = []
        self.turno_actual = 0
        self.sentido = 1
        self.estado = EstadoPartida.JUGANDO
        self.ganador = None
        self.turnos_sin_jugar = {}

        for jug in self.jugadores:
            jug.mano = []
            jug.ha_gritado_uno = False
            jug.infeccion = 0
            jug.vida = 20
            jug.tiene_escudo = False
            jug.veneno_restante = 0
            for _ in range(7):
                c = self.mazo.robar()
                if c:
                    jug.mano.append(c)

        primera = self.mazo.robar()
        while primera and primera.tipo in (TipoCarta.COMODIN, TipoCarta.MAS4):
            self.mazo.cartas.append(primera)
            random.shuffle(self.mazo.cartas)
            primera = self.mazo.robar()

        self.carta_activa = primera
        self.descarte.append(primera)
        self.color_activo = primera.color

        if primera.tipo == TipoCarta.SALTO:
            self.turno_actual = self._siguiente_turno()
        elif primera.tipo == TipoCarta.REVERSA:
            self.sentido = -1 if len(self.jugadores) > 2 else 1
            if len(self.jugadores) == 2:
                self.turno_actual = self._siguiente_turno()
        elif primera.tipo == TipoCarta.MAS2:
            sig = self._siguiente_turno()
            for _ in range(2):
                c = self.mazo.robar()
                if c:
                    self.jugadores[sig].mano.append(c)
            self.turno_actual = self._siguiente_turno()

        return True

    def _siguiente_turno(self):
        return (self.turno_actual + self.sentido) % len(self.jugadores)

    def jugar_carta(self, id_jugador, id_carta, color_elegido=None):
        self.penalizacion_actual = None
        if self.estado != EstadoPartida.JUGANDO:
            return False, "La partida no está en juego"

        if self.jugadores[id_jugador].id != self.jugadores[self.turno_actual].id:
            return False, "No es tu turno"

        jug = self.jugadores[id_jugador]
        carta = next((c for c in jug.mano if c.id == id_carta), None)
        if not carta:
            return False, "No tienes esa carta"

        if not carta.es_jugable(self.carta_activa, self.color_activo):
            if carta.tipo == TipoCarta.MAS4:
                tiene_color = any(
                    c.color == self.color_activo for c in jug.mano if c.id != carta.id
                )
                if tiene_color and self.modo != ModoJuego.CAOS:
                    return False, "Tienes el color activo, no puedes jugar +4"
            elif not carta.tipo.es_comodin():
                return False, "La carta no es jugable"

        jug.mano.remove(carta)

        if carta.tipo.es_comodin() and color_elegido:
            self.color_activo = Color(color_elegido.upper())
        elif carta.tipo.es_de_color():
            self.color_activo = carta.color

        self.descarte.append(carta)
        self.carta_activa = carta
        self.ultima_accion = ("JUGAR", id_jugador, carta)

        if carta.tipo != TipoCarta.NUMERO and carta.tipo != TipoCarta.CURA:
            self._aplicar_efecto(carta, id_jugador)

        if len(jug.mano) == 1 and not jug.ha_gritado_uno:
            pass

        if len(jug.mano) == 0:
            self.estado = EstadoPartida.TERMINADA
            self.ganador = id_jugador
            return True, "VICTORIA"

        if carta.tipo not in (TipoCarta.SALTO, TipoCarta.MAS2, TipoCarta.MAS4,
                               TipoCarta.REVERSA, TipoCarta.CAMBIO):
            self._avanzar_turno()

        return True, "OK"

    def _aplicar_efecto(self, carta, id_jugador):
        if carta.tipo == TipoCarta.SALTO:
            self.turno_actual = self._siguiente_turno()
            self._avanzar_turno()

        elif carta.tipo == TipoCarta.REVERSA:
            if len(self.jugadores) > 2:
                self.sentido *= -1
            self._avanzar_turno()

        elif carta.tipo == TipoCarta.MAS2:
            sig = self._siguiente_turno()
            self._avanzar_turno()
            for _ in range(2):
                c = self.mazo.robar()
                if c:
                    self.jugadores[sig].mano.append(c)
            self.penalizacion_actual = (sig, 2)
            self._avanzar_turno()

        elif carta.tipo == TipoCarta.MAS4:
            sig = self._siguiente_turno()
            self._avanzar_turno()
            for _ in range(4):
                c = self.mazo.robar()
                if c:
                    self.jugadores[sig].mano.append(c)
            self.penalizacion_actual = (sig, 4)
            self._avanzar_turno()

        elif carta.tipo == TipoCarta.CAMBIO:
            sig = self._siguiente_turno()
            jug_actual = self.jugadores[id_jugador]
            jug_objetivo = self.jugadores[sig]
            jug_actual.mano, jug_objetivo.mano = jug_objetivo.mano, jug_actual.mano
            self._avanzar_turno()

        elif carta.tipo == TipoCarta.BLOQUEO:
            jug = self.jugadores[id_jugador]
            jug.tiene_escudo = True
            self._avanzar_turno()

        elif carta.tipo == TipoCarta.VISION:
            self._avanzar_turno()

        elif carta.tipo == TipoCarta.ESPADA:
            sig = self._siguiente_turno()
            for _ in range(3):
                c = self.mazo.robar()
                if c:
                    self.jugadores[sig].mano.append(c)
            self.penalizacion_actual = (sig, 3)
            self._avanzar_turno()

        elif carta.tipo == TipoCarta.VENENO:
            sig = self._siguiente_turno()
            self.jugadores[sig].veneno_restante = 3
            self._avanzar_turno()

        elif carta.tipo == TipoCarta.CURA:
            jug = self.jugadores[id_jugador]
            jug.vida = min(jug.vida + 3, 20)
            self._avanzar_turno()

        elif carta.tipo == TipoCarta.ANTIDOTO:
            sig = self._siguiente_turno()
            objetivo = self.jugadores[sig]
            objetivo.infeccion = max(0, objetivo.infeccion - 1)
            self._avanzar_turno()

        elif carta.tipo == TipoCarta.TRAMPA:
            sig = self._siguiente_turno()
            self.turnos_sin_jugar[sig] = self.turnos_sin_jugar.get(sig, 0) + 1
            self._avanzar_turno()

        elif carta.tipo == TipoCarta.CORTOCIRCUITO:
            min_jug = min(self.jugadores, key=lambda j: len(j.mano))
            for _ in range(3):
                c = self.mazo.robar()
                if c:
                    min_jug.mano.append(c)
            if carta.tipo.es_comodin():
                self._avanzar_turno()

        elif carta.tipo == TipoCarta.RELAMPAGO:
            for jug in self.jugadores:
                c = self.mazo.robar()
                if c:
                    jug.mano.append(c)
            self._avanzar_turno()

        elif carta.tipo == TipoCarta.ESCUDO:
            self.jugadores[id_jugador].tiene_escudo = True
            self._avanzar_turno()

    def _avanzar_turno(self):
        self.turno_actual = self._siguiente_turno()

    def robar_sin_avanzar(self, id_jugador):
        if self.estado != EstadoPartida.JUGANDO:
            return None, "La partida no está en juego"
        if self.jugadores[id_jugador].id != self.jugadores[self.turno_actual].id:
            return None, "No es tu turno"
        carta = self.mazo.robar()
        if not carta and self.descarte and len(self.descarte) > 1:
            for c in self.descarte[:-1]:
                self.mazo.cartas.append(c)
            self.descarte = [self.descarte[-1]]
            self.mazo.reiniciar()
            carta = self.mazo.robar()
        if carta:
            self.jugadores[id_jugador].mano.append(carta)
        return carta, "OK"

    def robar_carta(self, id_jugador):
        if self.estado != EstadoPartida.JUGANDO:
            return None, "La partida no está en juego"
        if self.jugadores[id_jugador].id != self.jugadores[self.turno_actual].id:
            return None, "No es tu turno"

        carta = self.mazo.robar()
        if not carta and self.descarte and len(self.descarte) > 1:
            for c in self.descarte[:-1]:
                self.mazo.cartas.append(c)
            self.descarte = [self.descarte[-1]]
            self.mazo.reiniciar()
            carta = self.mazo.robar()

        if carta:
            self.jugadores[id_jugador].mano.append(carta)

        self._avanzar_turno()
        self.ultima_accion = ("ROBAR", id_jugador, carta)
        return carta, "OK"

    def gritar_uno(self, id_jugador):
        self.jugadores[id_jugador].ha_gritado_uno = True
        return True

    def verificar_uno_olvidado(self, id_jugador):
        jug = self.jugadores[id_jugador]
        if len(jug.mano) == 1 and not jug.ha_gritado_uno:
            for _ in range(2):
                c = self.mazo.robar()
                if c:
                    jug.mano.append(c)
            return True
        return False

    def get_estado_dict(self, para_jugador=None):
        accion = None
        if self.ultima_accion:
            tipo, *resto = self.ultima_accion
            if tipo == "JUGAR":
                _, id_jug, carta = self.ultima_accion
                accion = {"tipo": "JUGAR", "id_jugador": id_jug,
                          "carta": carta.to_dict() if carta else None}
                if self.penalizacion_actual:
                    accion["penalizacion"] = {
                        "id_jugador": self.penalizacion_actual[0],
                        "cantidad": self.penalizacion_actual[1]
                    }
            elif tipo == "ROBAR":
                _, id_jug, carta = self.ultima_accion
                accion = {"tipo": "ROBAR", "id_jugador": id_jug}
            elif tipo == "EVENTO":
                _, evento = self.ultima_accion
                accion = {"tipo": "EVENTO", "evento": evento.value}
            elif tipo == "VISION":
                _, id_jug = self.ultima_accion
                accion = {"tipo": "VISION", "id_jugador": id_jug}
            elif tipo == "CONVERTIDO":
                _, id_jug = self.ultima_accion
                accion = {"tipo": "CONVERTIDO", "id_jugador": id_jug}
            elif tipo.startswith("ZOMBIE_"):
                accion = {"tipo": self.ultima_accion[0]}
            else:
                accion = {"tipo": str(tipo)}

        d = {
            "modo": self.modo.value,
            "estado": self.estado.value,
            "turno": self.turno_actual,
            "sentido": self.sentido,
            "color_activo": self.color_activo.value if self.color_activo else None,
            "carta_activa": self.carta_activa.to_dict() if self.carta_activa else None,
            "cantidades": [len(j.mano) for j in self.jugadores],
            "ultima_accion": accion,
            "jugadores": [{"id": j.id, "nombre": j.nombre, "conectado": j.conectado,
                           "cantidad_cartas": len(j.mano), "vida": j.vida}
                          for j in self.jugadores],
            "ganador": self.ganador,
        }
        if para_jugador is not None and para_jugador < len(self.jugadores):
            d["tu_mano"] = [c.to_dict() for c in self.jugadores[para_jugador].mano]
        return d

    def calcular_puntos_ronda(self):
        total = 0
        for jug in self.jugadores:
            for carta in jug.mano:
                if carta.tipo == TipoCarta.NUMERO:
                    total += carta.numero if carta.numero else 0
                elif carta.tipo in (TipoCarta.SALTO, TipoCarta.REVERSA, TipoCarta.MAS2):
                    total += 20
                elif carta.tipo in (TipoCarta.COMODIN, TipoCarta.MAS4):
                    total += 50
                else:
                    total += 20
        return total

    def robar_evento_caos(self):
        if not self.mazo_eventos:
            self.mazo_eventos = list(EVENTOS_CAOS) * 3
            random.shuffle(self.mazo_eventos)
        return self.mazo_eventos.pop(0)
