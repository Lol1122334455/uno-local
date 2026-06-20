import random
import time


class Bot:
    def __init__(self, id_jugador, nombre, dificultad="media"):
        self.id = id_jugador
        self.nombre = nombre
        self.dificultad = dificultad
        self.tiempo_espera = {"facil": 1.5, "media": 0.8, "dificil": 0.3}

    def decidir_jugada(self, mano, carta_activa, color_activo, estado):
        if not mano:
            return None

        jugables = [c for c in mano if c.es_jugable(carta_activa, color_activo)]

        comodines = [c for c in jugables if c.tipo.es_comodin()]
        normales = [c for c in jugables if not c.tipo.es_comodin()]

        if self.dificultad == "facil":
            if normales:
                return random.choice(normales)
            elif comodines:
                return random.choice(comodines)
            return None

        elif self.dificultad == "dificil":
            if normales:
                carta = self._mejor_carta(normales, color_activo)
                return carta
            elif comodines:
                return self._peor_comodin(comodines)
            return None

        else:
            if normales:
                return random.choice(normales)
            elif comodines:
                return comodines[0]
            return None

    def _mejor_carta(self, cartas, color_activo):
        for c in cartas:
            if c.tipo in (c.tipo.MAS2, c.tipo.SALTO, c.tipo.REVERSA):
                return c
        for c in cartas:
            if c.tipo in (c.tipo.ESPADA, c.tipo.VENENO, c.tipo.CAMBIO):
                return c
        mismo_color = [c for c in cartas if c.color == color_activo]
        if mismo_color:
            return mismo_color[0]
        return cartas[0]

    def _peor_comodin(self, comodines):
        for c in comodines:
            if c.tipo == c.tipo.MAS4:
                return c
        for c in comodines:
            if c.tipo == c.tipo.COMODIN_PROBABILIDAD:
                return c
        return comodines[0]

    def elegir_color(self, mano):
        conteo = {}
        for c in mano:
            if c.color != c.color.SIN_COLOR:
                color_str = c.color.value
                conteo[color_str] = conteo.get(color_str, 0) + 1
        if conteo:
            max_color = max(conteo, key=conteo.get)
            return max_color
        return "ROJO"

    def deberia_gritar_uno(self, mano):
        return len(mano) == 1

    def get_tiempo_espera(self):
        return self.tiempo_espera.get(self.dificultad, 0.8)
