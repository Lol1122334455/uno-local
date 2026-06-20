from juego.partida import Partida, ModoJuego, EstadoPartida
from juego.cartas import Carta, Color, TipoCarta
import random


class PartidaZombie(Partida):
    def __init__(self, max_jugadores=4):
        super().__init__(modo=ModoJuego.ZOMBIE, max_jugadores=max_jugadores)
        self.id_zombie = None
        self.manos_visibles = {}

    def iniciar(self):
        result = super().iniciar()
        if not result:
            return False

        self.id_zombie = random.randint(0, len(self.jugadores) - 1)
        zombie = self.jugadores[self.id_zombie]
        zombie.mano = []
        zombie.infeccion = 0

        for _ in range(5):
            c = self._crear_carta_zombie()
            if c:
                zombie.mano.append(c)

        return True

    def _crear_carta_zombie(self):
        if not hasattr(self, '_zombie_mazo'):
            self._zombie_mazo = [
                ("INFECTAR", 5), ("MORDER", 4), ("HORDA", 3), ("PLAGA", 2), ("APOCALIPSIS", 1)
            ]
            self._zombie_cartas = []
            for tipo, cant in self._zombie_mazo:
                for _ in range(cant):
                    c = Carta(Color.SIN_COLOR, TipoCarta.COMODIN)
                    c.tipo_zombie = tipo
                    self._zombie_cartas.append(c)
            random.shuffle(self._zombie_cartas)

        if self._zombie_cartas:
            return self._zombie_cartas.pop(0)
        return None

    def jugar_carta(self, id_jugador, id_carta, color_elegido=None):
        jug = self.jugadores[id_jugador]
        carta = next((c for c in jug.mano if c.id == id_carta), None)
        if not carta:
            return False, "No tienes esa carta"

        if id_jugador == self.id_zombie:
            return self._jugar_carta_zombie(id_jugador, carta)
        else:
            return self._jugar_carta_humano(id_jugador, id_carta, color_elegido)

    def _jugar_carta_zombie(self, id_jugador, carta):
        tipo = getattr(carta, 'tipo_zombie', None)
        if not tipo:
            return False, "Carta zombie inválida"

        humanos = [j for j in self.jugadores if j.id != self.id_zombie and j.infeccion < 2]
        if not humanos:
            return False, "No hay humanos para atacar"

        if tipo == "INFECTAR":
            objetivo = random.choice(humanos)
            objetivo.infeccion += 1
            if objetivo.infeccion >= 2:
                self._convertir_zombie(objetivo.id)
            self.ultima_accion = ("ZOMBIE_INFECTAR", id_jugador, objetivo.id)

        elif tipo == "MORDER":
            objetivo = random.choice(humanos)
            for _ in range(2):
                c = self.mazo.robar()
                if c: objetivo.mano.append(c)
            objetivo.infeccion += 1
            if objetivo.infeccion >= 2:
                self._convertir_zombie(objetivo.id)
            self.ultima_accion = ("ZOMBIE_MORDER", id_jugador, objetivo.id)

        elif tipo == "HORDA":
            for h in humanos:
                c = self.mazo.robar()
                if c: h.mano.append(c)
            self.ultima_accion = ("ZOMBIE_HORDA", id_jugador)

        elif tipo == "PLAGA":
            for h in humanos:
                h.infeccion += 1
                if h.infeccion >= 2:
                    self._convertir_zombie(h.id)
            self.ultima_accion = ("ZOMBIE_PLAGA", id_jugador)

        elif tipo == "APOCALIPSIS":
            for h in humanos:
                if h.infeccion >= 2:
                    self._convertir_zombie(h.id)
            self.ultima_accion = ("ZOMBIE_APOCALIPSIS", id_jugador)

        jug.mano.remove(carta)
        if not hasattr(self, 'zombie_cartas_usadas'):
            self.zombie_cartas_usadas = []
        self.zombie_cartas_usadas.append(carta)

        if len(self._zombie_cartas) == 0 and len(self.zombie_cartas_usadas) > 0:
            self._zombie_cartas = list(self.zombie_cartas_usadas)
            random.shuffle(self._zombie_cartas)
            self.zombie_cartas_usadas = []

        for jug2 in self.jugadores:
            if jug2.id != self.id_zombie and jug2.infeccion >= 2:
                self._convertir_zombie(jug2.id)

        if not self._hay_humanos():
            self.estado = EstadoPartida.TERMINADA
            self.ganador = self.id_zombie

        return True, "OK"

    def _jugar_carta_humano(self, id_jugador, id_carta, color_elegido=None):
        jug = self.jugadores[id_jugador]
        carta = next((c for c in jug.mano if c.id == id_carta), None)
        if not carta:
            return False, "No tienes esa carta"

        if not carta.es_jugable(self.carta_activa, self.color_activo):
            if not carta.tipo.es_comodin():
                if not (carta.tipo == TipoCarta.ANTIDOTO):
                    return False, "La carta no es jugable"

        jug.mano.remove(carta)

        if carta.tipo.es_comodin() and color_elegido:
            self.color_activo = Color(color_elegido.upper())
        elif carta.tipo.es_de_color():
            self.color_activo = carta.color

        self.descarte.append(carta)
        self.carta_activa = carta
        self.ultima_accion = ("JUGAR", id_jugador, carta)

        if carta.tipo == TipoCarta.ANTIDOTO:
            sig = self._siguiente_turno()
            objetivo = self.jugadores[sig]
            objetivo.infeccion = max(0, objetivo.infeccion - 1)
            victoria_humano = all(j.infeccion == 0 for j in self.jugadores if j.id != self.id_zombie)
            if victoria_humano:
                pass

        if carta.tipo == TipoCarta.TRAMPA:
            pass

        if len(jug.mano) == 0:
            self.estado = EstadoPartida.TERMINADA
            self.ganador = id_jugador
            return True, "VICTORIA_HUMANO"

        self._avanzar_turno()
        return True, "OK"

    def _convertir_zombie(self, id_jugador):
        jug = self.jugadores[id_jugador]
        jug.infeccion = 2
        jug.mano = []
        for _ in range(3):
            c = self._crear_carta_zombie()
            if c:
                jug.mano.append(c)
        self.ultima_accion = ("CONVERTIDO", id_jugador)

    def _hay_humanos(self):
        return any(j.id != self.id_zombie and j.infeccion < 2 for j in self.jugadores)

    def _avanzar_turno(self):
        self.turno_actual = self._siguiente_turno()

    def get_estado_dict(self, para_jugador=None):
        d = super().get_estado_dict(para_jugador)
        d["id_zombie"] = self.id_zombie
        jugs = []
        for j in self.jugadores:
            info = {"id": j.id, "nombre": j.nombre, "infeccion": j.infeccion,
                    "conectado": j.conectado, "cantidad_cartas": len(j.mano)}
            if j.id == self.id_zombie or j.infeccion >= 2:
                info["es_zombie"] = True
            else:
                info["es_zombie"] = False
            jugs.append(info)
        d["jugadores"] = jugs
        if para_jugador is not None:
            d["tu_mano"] = [c.to_dict() for c in self.jugadores[para_jugador].mano]
        return d
