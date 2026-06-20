import pygame

NEGRO = (0, 0, 0)
BLANCO = (255, 255, 255)
GRIS = (60, 60, 60)
GRIS_CLARO = (140, 140, 140)
ROJO = (200, 40, 40)
VERDE = (40, 180, 40)
AZUL = (40, 80, 200)


class SalaEspera:
    def __init__(self, surface, font_peq, font_gde, scale=3):
        self.surface = surface
        self.font_peq = font_peq
        self.font_gde = font_gde
        self.scale = scale
        self.jugadores = []
        self.es_host = False
        self.modo = "CLASICO"
        self.mensaje = ""

    def actualizar(self, jugadores, es_host, modo):
        self.jugadores = jugadores
        self.es_host = es_host
        self.modo = modo

    def manejar_evento(self, evento):
        if evento.type == pygame.MOUSEBUTTONDOWN:
            x = evento.pos[0] // self.scale
            y = evento.pos[1] // self.scale

            if self.es_host and 80 <= y <= 102 and 100 <= x <= 220:
                return "INICIAR"

            if 130 <= y <= 150:
                modos = ["CLASICO", "RELAMPAGO", "CAOS", "DUELO", "ZOMBIE"]
                idx = (x - 30) // 52
                if 0 <= idx < len(modos):
                    return f"MODO:{modos[idx]}"

        return None

    def dibujar(self):
        vw, vh = self.surface.get_size()
        sx = vw / 320
        sy = vh / 240

        self.surface.fill(NEGRO)

        titulo = self.font_gde.render("SALA DE ESPERA", True, BLANCO)
        self.surface.blit(titulo, (160 - titulo.get_width() // 2, 10))

        modo_txt = self.font_peq.render(f"Modo: {self.modo}", True, GRIS_CLARO)
        self.surface.blit(modo_txt, (160 - modo_txt.get_width() // 2, 35))

        nombres = [j["nombre"] for j in self.jugadores]
        for i, nombre in enumerate(nombres):
            y = 50 + i * 20
            conectado = self.jugadores[i].get("conectado", True)
            color = VERDE if conectado else GRIS
            avatar_x = 50
            pygame.draw.rect(self.surface, color, (avatar_x, y, 10, 14))
            txt = self.font_peq.render(nombre, True, BLANCO)
            self.surface.blit(txt, (65, y))

        if self.es_host:
            if self.mensaje:
                msg = self.font_peq.render(self.mensaje, True, ROJO)
                self.surface.blit(msg, (160 - msg.get_width() // 2, 110))

            pygame.draw.rect(self.surface, VERDE, (100, 80, 120, 22))
            iniciar_txt = self.font_peq.render("INICIAR", True, NEGRO)
            self.surface.blit(iniciar_txt, (130, 83))
        else:
            esperando = self.font_peq.render("Esperando al host...", True, GRIS_CLARO)
            self.surface.blit(esperando, (160 - esperando.get_width() // 2, 85))

        modos = ["CLASICO", "RELAMPAGO", "CAOS", "DUELO", "ZOMBIE"]
        for i, m in enumerate(modos):
            x = 30 + i * 52
            y = 130
            color = ROJO if m == self.modo else GRIS
            pygame.draw.rect(self.surface, color, (x, y, 50, 20))
            txt = self.font_peq.render(m[:4], True, BLANCO)
            self.surface.blit(txt, (x + 1, y + 1))

        jug_count = self.font_peq.render(f"Jugadores: {len(self.jugadores)}", True, BLANCO)
        self.surface.blit(jug_count, (160 - jug_count.get_width() // 2, 160))
