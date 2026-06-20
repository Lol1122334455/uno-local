class Jugador:
    def __init__(self, id, nombre):
        self.id = id
        self.nombre = nombre
        self.mano = []
        self.conectado = True
        self.puntos_acumulados = 0
        self.vida = 20
        self.infeccion = 0
        self.inmune_hasta = 0
        self.tiene_escudo = False
        self.veneno_restante = 0
        self.ha_gritado_uno = False

    def __repr__(self):
        return f"{self.nombre} ({len(self.mano)} cartas)"

    def to_dict(self, ocultar_mano=False):
        d = {
            "id": self.id,
            "nombre": self.nombre,
            "cantidad_cartas": len(self.mano),
            "conectado": self.conectado,
            "puntos": self.puntos_acumulados,
            "vida": self.vida,
        }
        if not ocultar_mano:
            d["mano"] = [c.to_dict() for c in self.mano]
        return d
