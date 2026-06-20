from juego.partida import Partida, ModoJuego


class PartidaClasica(Partida):
    def __init__(self, max_jugadores=4):
        super().__init__(modo=ModoJuego.CLASICO, max_jugadores=max_jugadores)
