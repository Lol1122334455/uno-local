import pygame

NEGRO = (0, 0, 0)
BLANCO = (255, 255, 255)
GRIS = (60, 60, 60)
GRIS_CLARO = (140, 140, 140)
ROJO = (200, 40, 40)
VERDE = (40, 180, 40)
AMARILLO = (220, 200, 20)
AZUL = (40, 80, 200)


class Menu:
    def __init__(self, surface, font_peq, font_gde, scale=3, sonido=None):
        self.surface = surface
        self.font_peq = font_peq
        self.font_gde = font_gde
        self.scale = scale
        self.sonido = sonido
        self.ip = "127.0.0.1"
        self.nombre = "Jugador"
        self.puerto = "5555"
        self.input_activo = "nombre"
        self.mensaje = ""
        self.animacion_frame = 0
        self.num_bots = 2
        self.modo_single = "CLASICO"
        self.version_actual = ""
        self.hay_actualizacion = False
        self.actualizando = False

    def manejar_evento(self, evento):
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_TAB:
                if self.input_activo == "nombre":
                    self.input_activo = "ip"
                elif self.input_activo == "ip":
                    self.input_activo = "puerto"
                else:
                    self.input_activo = "nombre"
            elif evento.key == pygame.K_BACKSPACE:
                if self.input_activo == "nombre":
                    self.nombre = self.nombre[:-1]
                elif self.input_activo == "ip":
                    self.ip = self.ip[:-1]
                elif self.input_activo == "puerto":
                    self.puerto = self.puerto[:-1]
            elif evento.key == pygame.K_RETURN:
                return "CONECTAR"
            else:
                if self.input_activo == "nombre" and len(self.nombre) < 15:
                    if evento.unicode.isprintable():
                        self.nombre += evento.unicode
                elif self.input_activo == "ip" and len(self.ip) < 15:
                    if evento.unicode.isprintable():
                        self.ip += evento.unicode
                elif self.input_activo == "puerto" and len(self.puerto) < 5:
                    if evento.unicode.isdigit():
                        self.puerto += evento.unicode

        elif evento.type == pygame.MOUSEBUTTONDOWN:
            x = evento.pos[0] // self.scale
            y = evento.pos[1] // self.scale

            if 58 <= y <= 78:
                self.input_activo = "nombre"
                if self.sonido: self.sonido.play("click")
            elif 78 <= y <= 98:
                self.input_activo = "ip"
                self.mensaje = ""
                if self.sonido: self.sonido.play("click")
            elif 98 <= y <= 118:
                self.input_activo = "puerto"
                if self.sonido: self.sonido.play("click")

            if 170 <= y <= 190:
                if 60 <= x <= 140:
                    if self.sonido: self.sonido.play("click")
                    return "CONECTAR"
                elif 160 <= x <= 260:
                    if self.sonido: self.sonido.play("click")
                    return "CREAR"

            if 134 <= y <= 154:
                modos = ["CLASICO", "RELAMPAGO", "CAOS", "DUELO", "ZOMBIE"]
                idx = (x - 20) // 56
                if 0 <= idx < len(modos):
                    self.modo_single = modos[idx]
                    if self.sonido: self.sonido.play("click")

            if 194 <= y <= 222 and 56 <= x <= 264:
                if self.sonido: self.sonido.play("click")
                return f"UN_JUGADOR:{self.num_bots}:{self.modo_single}"

            if 196 <= y <= 220 and 244 <= x <= 266:
                self.num_bots = min(3, self.num_bots + 1)
                if self.sonido: self.sonido.play("click")
            elif 196 <= y <= 220 and 218 <= x <= 242:
                self.num_bots = max(1, self.num_bots - 1)
                if self.sonido: self.sonido.play("click")

            if self.hay_actualizacion and not self.actualizando:
                if 108 <= y <= 126 and 200 <= x <= 300:
                    if self.sonido: self.sonido.play("click")
                    return "ACTUALIZAR"

        return None

    def dibujar(self):
        vw, vh = self.surface.get_size()
        sx = vw / 320
        sy = vh / 240

        self.surface.fill(NEGRO)

        pygame.draw.rect(self.surface, (36, 36, 48), (4, 4, 312, 232))
        pygame.draw.rect(self.surface, GRIS_CLARO, (4, 4, 312, 232), 1)

        titulo = self.font_gde.render("UNO", True, BLANCO)
        sombra = self.font_gde.render("UNO", True, (80, 20, 20))
        self.surface.blit(sombra, (162 - sombra.get_width() // 2, 10))
        self.surface.blit(titulo, (160 - titulo.get_width() // 2, 8))

        subtitulo = self.font_peq.render("MULTIJUGADOR", True, GRIS_CLARO)
        self.surface.blit(subtitulo, (160 - subtitulo.get_width() // 2, 34))

        y_base = 58
        labels = [("Nombre:", self.nombre), ("IP:", self.ip), ("Puerto:", self.puerto)]
        entradas = ["nombre", "ip", "puerto"]

        for i, (label, valor) in enumerate(labels):
            y = y_base + i * 22
            lbl = self.font_peq.render(label, True, GRIS_CLARO)
            self.surface.blit(lbl, (20, y + 1))
            pygame.draw.rect(self.surface, (40, 40, 52), (70, y, 110, 16))
            color_borde = (255, 200, 40) if self.input_activo == entradas[i] else GRIS
            pygame.draw.rect(self.surface, color_borde, (70, y, 110, 16), 1)
            txt = self.font_peq.render(valor, True, BLANCO)
            self.surface.blit(txt, (73, y + 1))

        pygame.draw.rect(self.surface, (160, 32, 32), (58, 168, 84, 24))
        pygame.draw.rect(self.surface, BLANCO, (58, 168, 84, 24), 1)
        conectar_txt = self.font_peq.render("CONECTAR", True, BLANCO)
        self.surface.blit(conectar_txt, (100 - conectar_txt.get_width() // 2, 173))

        pygame.draw.rect(self.surface, (32, 140, 32), (178, 168, 84, 24))
        pygame.draw.rect(self.surface, BLANCO, (178, 168, 84, 24), 1)
        crear_txt = self.font_peq.render("CREAR", True, BLANCO)
        self.surface.blit(crear_txt, (220 - crear_txt.get_width() // 2, 173))

        pygame.draw.rect(self.surface, GRIS, (10, 128, 300, 1))

        pygame.draw.rect(self.surface, (180, 160, 16), (58, 196, 204, 24))
        pygame.draw.rect(self.surface, BLANCO, (58, 196, 204, 24), 1)
        unoj_txt = self.font_peq.render(f"1 JUGADOR ({self.num_bots} bots)", True, NEGRO)
        self.surface.blit(unoj_txt, (160 - unoj_txt.get_width() // 2, 201))

        modos = ["CLASICO", "RELAMPAGO", "CAOS", "DUELO", "ZOMBIE"]
        colores_modo = [(200, 40, 40), (200, 200, 40), (160, 40, 200), (40, 160, 40), (80, 60, 40)]
        for i, m in enumerate(modos):
            x = 20 + i * 56
            y = 136
            mc = colores_modo[i] if m == self.modo_single else GRIS
            pygame.draw.rect(self.surface, mc, (x, y, 54, 16))
            pygame.draw.rect(self.surface, BLANCO, (x, y, 54, 16), 1)
            txt = self.font_peq.render(m[:4], True, BLANCO)
            self.surface.blit(txt, (x + 27 - txt.get_width() // 2, y + 1))

        pygame.draw.rect(self.surface, GRIS, (220, 198, 20, 20))
        pygame.draw.rect(self.surface, BLANCO, (220, 198, 20, 20), 1)
        menos_txt = self.font_peq.render("-", True, BLANCO)
        self.surface.blit(menos_txt, (230 - menos_txt.get_width() // 2, 200))
        pygame.draw.rect(self.surface, GRIS, (244, 198, 20, 20))
        pygame.draw.rect(self.surface, BLANCO, (244, 198, 20, 20), 1)
        mas_txt = self.font_peq.render("+", True, BLANCO)
        self.surface.blit(mas_txt, (254 - mas_txt.get_width() // 2, 200))

        if self.mensaje:
            msg = self.font_peq.render(self.mensaje, True, ROJO)
            self.surface.blit(msg, (160 - msg.get_width() // 2, 225))

        ver = self.font_peq.render(f"v{self.version_actual}", True, GRIS_CLARO)
        self.surface.blit(ver, (4, 228))

        if self.actualizando:
            txt = self.font_peq.render("ACTUALIZANDO...", True, AMARILLO)
            self.surface.blit(txt, (160 - txt.get_width() // 2, 114))
        elif self.hay_actualizacion:
            pygame.draw.rect(self.surface, (32, 120, 200), (200, 108, 100, 18))
            txt = self.font_peq.render("ACTUALIZAR", True, BLANCO)
            self.surface.blit(txt, (250 - txt.get_width() // 2, 110))

        self.animacion_frame += 1
        for i in range(3):
            x = 60 + i * 100
            y = 225 + (self.animacion_frame % 24 > 12) * 2
            card_color = [(200, 40, 40), (40, 80, 200), (40, 180, 40)][i]
            pygame.draw.rect(self.surface, BLANCO, (x, y, 18, 14))
            pygame.draw.rect(self.surface, NEGRO, (x, y, 18, 14), 1)
            pygame.draw.rect(self.surface, card_color, (x + 2, y + 2, 14, 10))
            pygame.draw.rect(self.surface, NEGRO, (x, y, 20, 16), 1)
