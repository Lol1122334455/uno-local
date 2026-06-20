from enum import Enum
import random


class Color(Enum):
    ROJO = "ROJO"
    AZUL = "AZUL"
    VERDE = "VERDE"
    AMARILLO = "AMARILLO"
    SIN_COLOR = "SIN_COLOR"

    def __str__(self):
        return self.value


class TipoCarta(Enum):
    NUMERO = "NUMERO"
    SALTO = "SALTO"
    REVERSA = "REVERSA"
    MAS2 = "MAS2"
    COMODIN = "COMODIN"
    MAS4 = "MAS4"

    CAMBIO = "CAMBIO"
    BLOQUEO = "BLOQUEO"
    VISION = "VISION"
    ESPADA = "ESPADA"
    VENENO = "VENENO"
    CURA = "CURA"
    ANTIDOTO = "ANTIDOTO"
    TRAMPA = "TRAMPA"

    CORTOCIRCUITO = "CORTOCIRCUITO"
    RELAMPAGO = "RELAMPAGO"
    ESCUDO = "ESCUDO"
    COMODIN_PROBABILIDAD = "COMODIN_PROBABILIDAD"
    COMODIN_ESPEJO = "COMODIN_ESPEJO"
    COMODIN_DOBLE = "COMODIN_DOBLE"
    COMODIN_PERDER_TURNO = "COMODIN_PERDER_TURNO"
    COMODIN_SANGUINEO = "COMODIN_SANGUINEO"
    COMODIN_VAMPIRO = "COMODIN_VAMPIRO"
    COMODIN_REFUGIO = "COMODIN_REFUGIO"

    def es_comodin(self):
        return self in (TipoCarta.COMODIN, TipoCarta.MAS4, TipoCarta.COMODIN_PROBABILIDAD,
                        TipoCarta.COMODIN_ESPEJO, TipoCarta.COMODIN_DOBLE,
                        TipoCarta.COMODIN_PERDER_TURNO, TipoCarta.COMODIN_SANGUINEO,
                        TipoCarta.COMODIN_VAMPIRO, TipoCarta.COMODIN_REFUGIO)

    def es_de_color(self):
        return self in (TipoCarta.NUMERO, TipoCarta.SALTO, TipoCarta.REVERSA,
                        TipoCarta.MAS2, TipoCarta.CAMBIO, TipoCarta.BLOQUEO,
                        TipoCarta.VISION, TipoCarta.ESPADA, TipoCarta.VENENO,
                        TipoCarta.CURA, TipoCarta.ANTIDOTO, TipoCarta.TRAMPA)

    def es_accion(self):
        return self in (TipoCarta.SALTO, TipoCarta.REVERSA, TipoCarta.MAS2,
                        TipoCarta.MAS4, TipoCarta.CAMBIO, TipoCarta.BLOQUEO,
                        TipoCarta.VISION, TipoCarta.ESPADA, TipoCarta.VENENO,
                        TipoCarta.CURA, TipoCarta.ANTIDOTO, TipoCarta.TRAMPA,
                        TipoCarta.CORTOCIRCUITO, TipoCarta.RELAMPAGO, TipoCarta.ESCUDO)


class Carta:
    _id_counter = 0

    def __init__(self, color, tipo, numero=None):
        Carta._id_counter += 1
        self.id = Carta._id_counter
        self.color = color
        self.tipo = tipo
        self.numero = numero

    def __repr__(self):
        color_str = str(self.color)[:2]
        if self.tipo == TipoCarta.NUMERO:
            return f"{color_str}{self.numero}"
        simbolos = {
            TipoCarta.SALTO: "S", TipoCarta.REVERSA: "R", TipoCarta.MAS2: "+2",
            TipoCarta.COMODIN: "★", TipoCarta.MAS4: "+4",
            TipoCarta.CAMBIO: "↔", TipoCarta.BLOQUEO: "■",
            TipoCarta.VISION: "👁", TipoCarta.ESPADA: "⚔", TipoCarta.VENENO: "☠",
            TipoCarta.CURA: "❤", TipoCarta.ANTIDOTO: "💊", TipoCarta.TRAMPA: "🪤",
            TipoCarta.CORTOCIRCUITO: "⚡", TipoCarta.RELAMPAGO: "🌩", TipoCarta.ESCUDO: "🛡",
            TipoCarta.COMODIN_PROBABILIDAD: "🎲", TipoCarta.COMODIN_ESPEJO: "🪞",
            TipoCarta.COMODIN_DOBLE: "🃏2", TipoCarta.COMODIN_PERDER_TURNO: "⏳",
            TipoCarta.COMODIN_SANGUINEO: "🩸", TipoCarta.COMODIN_VAMPIRO: "🧛",
            TipoCarta.COMODIN_REFUGIO: "🏠"
        }
        sim = simbolos.get(self.tipo, "?")
        if self.tipo.es_comodin():
            return sim
        return f"{color_str}{sim}"

    def to_dict(self):
        d = {"id": self.id, "tipo": self.tipo.value, "color": self.color.value}
        if self.numero is not None:
            d["numero"] = self.numero
        return d

    @staticmethod
    def from_dict(d):
        c = Carta(Color(d["color"]), TipoCarta(d["tipo"]), d.get("numero"))
        c.id = d["id"]
        return c

    def es_jugable(self, carta_activa, color_activo=None):
        if self.tipo.es_comodin():
            if self.tipo == TipoCarta.MAS4:
                return True
            if self.tipo == TipoCarta.COMODIN_PROBABILIDAD:
                return True
            if self.tipo == TipoCarta.COMODIN_ESPEJO:
                return True
            if self.tipo == TipoCarta.COMODIN_DOBLE:
                return True
            if self.tipo == TipoCarta.COMODIN_PERDER_TURNO:
                return True
            if self.tipo == TipoCarta.COMODIN_SANGUINEO:
                return True
            if self.tipo == TipoCarta.COMODIN_VAMPIRO:
                return True
            if self.tipo == TipoCarta.COMODIN_REFUGIO:
                return True
            return self.tipo == TipoCarta.COMODIN or self.tipo == TipoCarta.MAS4

        color_valido = color_activo if color_activo else carta_activa.color
        if self.color == color_valido:
            return True
        if carta_activa.tipo == TipoCarta.NUMERO and self.tipo == TipoCarta.NUMERO:
            return self.numero == carta_activa.numero
        if carta_activa.tipo == TipoCarta.MAS2 and self.tipo == TipoCarta.MAS2:
            return True
        if carta_activa.tipo == TipoCarta.SALTO and self.tipo == TipoCarta.SALTO:
            return True
        if carta_activa.tipo == TipoCarta.REVERSA and self.tipo == TipoCarta.REVERSA:
            return True
        if carta_activa.tipo == TipoCarta.CAMBIO and self.tipo == TipoCarta.CAMBIO:
            return True
        if carta_activa.tipo == TipoCarta.BLOQUEO and self.tipo == TipoCarta.BLOQUEO:
            return True
        if carta_activa.tipo == TipoCarta.VISION and self.tipo == TipoCarta.VISION:
            return True
        if carta_activa.tipo == TipoCarta.ESPADA and self.tipo == TipoCarta.ESPADA:
            return True
        if carta_activa.tipo == TipoCarta.VENENO and self.tipo == TipoCarta.VENENO:
            return True
        if carta_activa.tipo == TipoCarta.CURA and self.tipo == TipoCarta.CURA:
            return True
        if carta_activa.tipo == TipoCarta.ANTIDOTO and self.tipo == TipoCarta.ANTIDOTO:
            return True
        if carta_activa.tipo == TipoCarta.TRAMPA and self.tipo == TipoCarta.TRAMPA:
            return True

        if self.tipo == TipoCarta.NUMERO and carta_activa.tipo == TipoCarta.NUMERO:
            return self.numero == carta_activa.numero

        if self.tipo == TipoCarta.CURA and carta_activa.tipo == TipoCarta.NUMERO:
            if self.numero is not None and carta_activa.numero is not None:
                return self.numero == carta_activa.numero

        return False


class Mazo:
    def __init__(self, incluir_nuevas=False):
        self.cartas = []
        Carta._id_counter = 0

        colores = [Color.ROJO, Color.AZUL, Color.VERDE, Color.AMARILLO]

        for color in colores:
            self.cartas.append(Carta(color, TipoCarta.NUMERO, 0))
            for num in range(1, 10):
                self.cartas.append(Carta(color, TipoCarta.NUMERO, num))
                self.cartas.append(Carta(color, TipoCarta.NUMERO, num))

        for color in colores:
            self.cartas.append(Carta(color, TipoCarta.SALTO))
            self.cartas.append(Carta(color, TipoCarta.SALTO))
            self.cartas.append(Carta(color, TipoCarta.REVERSA))
            self.cartas.append(Carta(color, TipoCarta.REVERSA))
            self.cartas.append(Carta(color, TipoCarta.MAS2))
            self.cartas.append(Carta(color, TipoCarta.MAS2))

        for _ in range(4):
            self.cartas.append(Carta(Color.SIN_COLOR, TipoCarta.COMODIN))
            self.cartas.append(Carta(Color.SIN_COLOR, TipoCarta.MAS4))

        if incluir_nuevas:
            for color in colores:
                self.cartas.append(Carta(color, TipoCarta.CAMBIO))
                self.cartas.append(Carta(color, TipoCarta.BLOQUEO))
                self.cartas.append(Carta(color, TipoCarta.VISION))
                self.cartas.append(Carta(color, TipoCarta.ESPADA))
                self.cartas.append(Carta(color, TipoCarta.VENENO))
                self.cartas.append(Carta(color, TipoCarta.CURA, 0))
                self.cartas.append(Carta(color, TipoCarta.ANTIDOTO))
                self.cartas.append(Carta(color, TipoCarta.TRAMPA))

            self.cartas.append(Carta(Color.SIN_COLOR, TipoCarta.CORTOCIRCUITO))
            self.cartas.append(Carta(Color.SIN_COLOR, TipoCarta.RELAMPAGO))
            self.cartas.append(Carta(Color.SIN_COLOR, TipoCarta.ESCUDO))

            self.cartas.append(Carta(Color.SIN_COLOR, TipoCarta.COMODIN_PROBABILIDAD))
            self.cartas.append(Carta(Color.SIN_COLOR, TipoCarta.COMODIN_ESPEJO))
            self.cartas.append(Carta(Color.SIN_COLOR, TipoCarta.COMODIN_DOBLE))
            self.cartas.append(Carta(Color.SIN_COLOR, TipoCarta.COMODIN_PERDER_TURNO))
            self.cartas.append(Carta(Color.SIN_COLOR, TipoCarta.COMODIN_SANGUINEO))
            self.cartas.append(Carta(Color.SIN_COLOR, TipoCarta.COMODIN_VAMPIRO))
            self.cartas.append(Carta(Color.SIN_COLOR, TipoCarta.COMODIN_REFUGIO))

        self.reiniciar()

    def reiniciar(self):
        random.shuffle(self.cartas)

    def robar(self, n=1):
        if len(self.cartas) < n:
            return None
        if n == 1:
            return self.cartas.pop(0)
        return [self.cartas.pop(0) for _ in range(n)]

    def __len__(self):
        return len(self.cartas)
