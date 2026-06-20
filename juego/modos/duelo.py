from juego.partida import Partida, ModoJuego, EstadoPartida
from juego.cartas import TipoCarta, Color
import random


class PartidaDuelo(Partida):
    def __init__(self, max_jugadores=2):
        super().__init__(modo=ModoJuego.DUELO, max_jugadores=max_jugadores)

    def iniciar(self):
        result = super().iniciar()
        for jug in self.jugadores:
            jug.vida = 20
        return result

    def jugar_carta(self, id_jugador, id_carta, color_elegido=None):
        result, msg = super().jugar_carta(id_jugador, id_carta, color_elegido)

        if result:
            jug = self.jugadores[id_jugador]
            carta = next((c for c in self.descarte if c.id == id_carta), None)
            if carta:
                danio = self._calcular_danio(carta)
                if danio > 0:
                    for otro in self.jugadores:
                        if otro.id != id_jugador:
                            otro.vida -= danio
                            if otro.vida <= 0:
                                self.estado = EstadoPartida.TERMINADA
                                self.ganador = id_jugador

        return result, msg

    def _calcular_danio(self, carta):
        if carta.tipo == TipoCarta.NUMERO:
            return carta.numero if carta.numero else 0
        elif carta.tipo == TipoCarta.CURA:
            return 0
        elif carta.tipo in (TipoCarta.SALTO, TipoCarta.REVERSA, TipoCarta.MAS2,
                            TipoCarta.CAMBIO, TipoCarta.BLOQUEO, TipoCarta.VISION,
                            TipoCarta.ESPADA, TipoCarta.VENENO, TipoCarta.ANTIDOTO,
                            TipoCarta.TRAMPA):
            return 5
        elif carta.tipo == TipoCarta.COMODIN:
            return 10
        elif carta.tipo == TipoCarta.MAS4:
            return 15
        elif carta.tipo == TipoCarta.COMODIN_VAMPIRO:
            return 5
        elif carta.tipo in (TipoCarta.COMODIN_PROBABILIDAD, TipoCarta.COMODIN_ESPEJO,
                            TipoCarta.COMODIN_DOBLE, TipoCarta.COMODIN_PERDER_TURNO):
            return 8
        elif carta.tipo == TipoCarta.COMODIN_SANGUINEO:
            return 3
        elif carta.tipo == TipoCarta.COMODIN_REFUGIO:
            return 0
        return 0

    def _aplicar_efecto(self, carta, id_jugador):
        jug = self.jugadores[id_jugador]

        if carta.tipo == TipoCarta.CURA:
            jug.vida = min(jug.vida + 3, 20)
            self._avanzar_turno()
            return

        if carta.tipo == TipoCarta.COMODIN_VAMPIRO:
            for otro in self.jugadores:
                if otro.id != id_jugador:
                    otro.vida -= 5
                    jug.vida += 5
                    if otro.vida <= 0:
                        self.estado = EstadoPartida.TERMINADA
                        self.ganador = id_jugador
            self._avanzar_turno()
            return

        if carta.tipo == TipoCarta.COMODIN_SANGUINEO:
            color_contar = self.color_activo
            count = sum(1 for c in jug.mano if c.color == color_contar)
            cura = count * 2
            jug.vida = min(jug.vida + cura, 20)
            self._avanzar_turno()
            return

        if carta.tipo == TipoCarta.ESPADA:
            for otro in self.jugadores:
                if otro.id != id_jugador:
                    for _ in range(3):
                        c = self.mazo.robar()
                        if c: otro.mano.append(c)
            self._avanzar_turno()
            return

        if carta.tipo == TipoCarta.VENENO:
            for otro in self.jugadores:
                if otro.id != id_jugador:
                    otro.veneno_restante = 3
            self._avanzar_turno()
            return

        if carta.tipo == TipoCarta.REVERSA:
            self._avanzar_turno()
            return

        super()._aplicar_efecto(carta, id_jugador)
