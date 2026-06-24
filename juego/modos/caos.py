from juego.partida import Partida, ModoJuego, EstadoPartida, EventoCaos, EVENTOS_CAOS
from juego.cartas import Color
import random


class PartidaCaos(Partida):
    def __init__(self, max_jugadores=4):
        super().__init__(modo=ModoJuego.CAOS, max_jugadores=max_jugadores)

    def iniciar(self):
        result = super().iniciar()
        self.mazo_eventos = list(EVENTOS_CAOS) * 3
        random.shuffle(self.mazo_eventos)
        return result

    def jugar_carta(self, id_jugador, id_carta, color_elegido=None):
        evento = self.robar_evento_caos()
        self._aplicar_evento(evento, id_jugador)
        self.eventos_pendientes.append(evento)
        self.ultima_accion = ("EVENTO", evento)

        return super().jugar_carta(id_jugador, id_carta, color_elegido)

    def robar_carta(self, id_jugador):
        evento = self.robar_evento_caos()
        self._aplicar_evento(evento, id_jugador)
        self.eventos_pendientes.append(evento)
        return super().robar_carta(id_jugador)

    def _aplicar_evento(self, evento, id_actual):
        if evento == EventoCaos.TORBELLINO:
            manos = [list(j.mano) for j in self.jugadores]
            n = len(self.jugadores)
            for i in range(n):
                self.jugadores[(i - 1) % n].mano = manos[i]

        elif evento == EventoCaos.INTERCAMBIO:
            otros = [j for j in self.jugadores if j.id != id_actual]
            if otros:
                objetivo = random.choice(otros)
                self.jugadores[id_actual].mano, objetivo.mano = objetivo.mano, self.jugadores[id_actual].mano

        elif evento == EventoCaos.VISION:
            self.ultima_accion = ("VISION", id_actual)

        elif evento == EventoCaos.BOMBA:
            for _ in range(4):
                c = self.mazo.robar()
                if c:
                    self.jugadores[id_actual].mano.append(c)

        elif evento == EventoCaos.OSCURIDAD:
            for jug in self.jugadores:
                c = self.mazo.robar()
                if c:
                    jug.mano.append(c)

        elif evento == EventoCaos.DADO:
            resultado = random.randint(1, 6)
            jug = self.jugadores[id_actual]
            if resultado == 1:
                c = self.mazo.robar()
                if c: jug.mano.append(c)
            elif resultado == 2:
                pass
            elif resultado == 3:
                c = self.mazo.robar()
                if c: jug.mano.append(c)
                c = self.mazo.robar()
                if c: jug.mano.append(c)
                if jug.mano:
                    jug.mano.pop(0)
                    if jug.mano:
                        jug.mano.pop(0)
            elif resultado == 4:
                for _ in range(3):
                    c = self.mazo.robar()
                    if c: jug.mano.append(c)
            elif resultado == 5:
                max_jug = max(self.jugadores, key=lambda j: len(j.mano))
                c = max_jug.mano.pop(0)
                jug.mano.append(c)
            elif resultado == 6:
                pass

        elif evento == EventoCaos.SUERTE:
            max_jug = max(self.jugadores, key=lambda j: len(j.mano))
            c = max_jug.mano.pop(0)
            self.jugadores[id_actual].mano.append(c)

        elif evento == EventoCaos.MALDICION:
            for _ in range(2):
                c = self.mazo.robar()
                if c:
                    self.jugadores[id_actual].mano.append(c)

        elif evento == EventoCaos.ESTRELLA:
            jug = self.jugadores[id_actual]
            for _ in range(min(3, len(jug.mano))):
                if jug.mano:
                    jug.mano.pop(0)

        elif evento == EventoCaos.CAOS_TOTAL:
            todas = []
            for jug in self.jugadores:
                todas.extend(jug.mano)
                jug.mano = []
            random.shuffle(todas)
            n = len(todas)
            por_jug = n // len(self.jugadores)
            sobrante = n % len(self.jugadores)
            idx = 0
            for i, jug in enumerate(self.jugadores):
                extra = 1 if i < sobrante else 0
                jug.mano = todas[idx:idx + por_jug + extra]
                idx += por_jug + extra

    def get_estado_dict(self, para_jugador=None):
        d = super().get_estado_dict(para_jugador)
        d["eventos_pendientes"] = [e.value for e in self.eventos_pendientes]
        d["prox_eventos"] = len(self.mazo_eventos)
        return d
