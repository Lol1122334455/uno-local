from juego.partida import Partida, ModoJuego, EstadoPartida
from juego.cartas import TipoCarta, Color
import random


class PartidaRelampago(Partida):
    def __init__(self, max_jugadores=4):
        super().__init__(modo=ModoJuego.RELAMPAGO, max_jugadores=max_jugadores)

    def jugar_carta(self, id_jugador, id_carta, color_elegido=None):
        if self.estado != EstadoPartida.JUGANDO:
            return False, "La partida no está en juego"

        jug = self.jugadores[id_jugador]
        carta = next((c for c in jug.mano if c.id == id_carta), None)
        if not carta:
            return False, "No tienes esa carta"

        if not carta.es_jugable(self.carta_activa, self.color_activo):
            if not carta.tipo.es_comodin():
                return False, "La carta no es jugable"

        jug.mano.remove(carta)

        if carta.tipo.es_comodin() and color_elegido:
            self.color_activo = Color(color_elegido.upper())
        elif carta.tipo.es_de_color():
            self.color_activo = carta.color

        self.descarte.append(carta)
        self.carta_activa = carta
        self.ultima_accion = ("JUGAR", id_jugador, carta)

        if carta.tipo in (TipoCarta.MAS2, TipoCarta.MAS4):
            for jug2 in self.jugadores:
                if jug2.id != id_jugador:
                    n = 2 if carta.tipo == TipoCarta.MAS2 else 4
                    for _ in range(n):
                        c = self.mazo.robar()
                        if c:
                            jug2.mano.append(c)
        elif carta.tipo == TipoCarta.CORTOCIRCUITO:
            min_jug = min(self.jugadores, key=lambda j: len(j.mano))
            for _ in range(3):
                c = self.mazo.robar()
                if c:
                    min_jug.mano.append(c)
        elif carta.tipo == TipoCarta.RELAMPAGO:
            for jug2 in self.jugadores:
                if jug2.id != id_jugador:
                    c = self.mazo.robar()
                    if c:
                        jug2.mano.append(c)
        elif carta.tipo == TipoCarta.ESCUDO:
            jug.tiene_escudo = True
        elif carta.tipo == TipoCarta.CAMBIO:
            otros = [j for j in self.jugadores if j.id != id_jugador]
            if otros:
                objetivo = random.choice(otros)
                jug.mano, objetivo.mano = objetivo.mano, jug.mano

        if len(jug.mano) == 0:
            self.estado = EstadoPartida.TERMINADA
            self.ganador = id_jugador
            return True, "VICTORIA"

        return True, "OK"

    def robar_carta(self, id_jugador):
        if self.estado != EstadoPartida.JUGANDO:
            return None, "La partida no está en juego"
        carta = self.mazo.robar()
        if carta:
            self.jugadores[id_jugador].mano.append(carta)
        return carta, "OK"
