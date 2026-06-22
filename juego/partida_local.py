from juego.partida import Partida, ModoJuego, EstadoPartida
from juego.modos import MODOS
from juego.bot import Bot


class PartidaLocal:
    def __init__(self, modo="CLASICO", num_bots=3, nombre_jugador="Tu"):
        self.modo_str = modo
        modo_cls = MODOS.get(modo)
        self.partida = modo_cls(max_jugadores=num_bots + 1)

        self.id_humano = self.partida.agregar_jugador(nombre_jugador)
        self.bots = []
        nombres_bot = ["R2-D2", "C-3PO", "BB-8", "HAL", "Data", "Wall-E", "Johnny 5"]
        for i in range(num_bots):
            nombre = nombres_bot[i % len(nombres_bot)]
            dificultad = ["facil", "media", "dificil"][i % 3]
            id_bot = self.partida.agregar_jugador(nombre)
            self.bots.append(Bot(id_bot, nombre, dificultad))

        self.partida.iniciar()
        self.esperando_accion_humano = (self.partida.turno_actual == self.id_humano)

    def obtener_estado(self):
        d = self.partida.get_estado_dict(para_jugador=self.id_humano)
        d["es_tu_turno"] = (self.partida.turno_actual == self.id_humano)
        d["id_humano"] = self.id_humano
        d["modo"] = self.modo_str
        return d

    def jugar_humano(self, id_carta, color_elegido=None):
        if self.partida.turno_actual != self.id_humano:
            return False, "No es tu turno"

        resultado, mensaje = self.partida.jugar_carta(self.id_humano, id_carta, color_elegido)
        if resultado:
            self.esperando_accion_humano = False
        return resultado, mensaje

    def robar_humano(self):
        if self.partida.turno_actual != self.id_humano:
            return None, "No es tu turno"

        carta, mensaje = self.partida.robar_carta(self.id_humano)
        self.esperando_accion_humano = False
        return carta, mensaje

    def gritar_uno_humano(self):
        self.partida.gritar_uno(self.id_humano)

    def turno_bot(self):
        if self.partida.estado != EstadoPartida.JUGANDO:
            return None

        if self.partida.turno_actual == self.id_humano:
            return None

        id_bot = self.partida.turno_actual
        bot = next((b for b in self.bots if b.id == id_bot), None)
        if not bot:
            return None

        jug = self.partida.jugadores[id_bot]
        carta_activa = self.partida.carta_activa
        color_activo = self.partida.color_activo

        if bot.deberia_gritar_uno(jug.mano):
            self.partida.gritar_uno(id_bot)

        decision = bot.decidir_jugada(jug.mano, carta_activa, color_activo, self.partida)

        if decision:
            color_elegido = None
            if decision.tipo.es_comodin():
                color_elegido = bot.elegir_color(jug.mano)
            resultado, mensaje = self.partida.jugar_carta(id_bot, decision.id, color_elegido)
            if resultado:
                accion = f"jugó {decision}"
                if color_elegido:
                    accion += f" (color: {color_elegido})"
                return accion

        carta, mensaje = self.partida.robar_sin_avanzar(id_bot)
        if carta:
            if carta.es_jugable(carta_activa, color_activo):
                color_elegido = None
                if carta.tipo.es_comodin():
                    color_elegido = bot.elegir_color(jug.mano)
                ok, _ = self.partida.jugar_carta(id_bot, carta.id, color_elegido)
                if ok:
                    return f"robó y jugó {carta}"
            self.partida._avanzar_turno()
            return f"robó {carta} (no jugable)"
        self.partida._avanzar_turno()
        return "robó (mazo vacío)"

    def esta_terminada(self):
        return self.partida.estado == EstadoPartida.TERMINADA

    def esperando_humano(self):
        return (self.partida.estado == EstadoPartida.JUGANDO and
                self.partida.turno_actual == self.id_humano)

    def obtener_ganador(self):
        return self.partida.ganador
