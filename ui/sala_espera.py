import pygame
import math
import random

NEGRO = (0, 0, 0)
BLANCO = (255, 255, 255)
GRIS = (60, 60, 60)
GRIS_CLARO = (140, 140, 140)
ROJO = (200, 40, 40)
VERDE = (40, 180, 40)
AZUL = (40, 80, 200)
AMARILLO = (220, 200, 20)


class ParticulaFondo:
    def __init__(self):
        self.x = random.uniform(0, 320)
        self.y = random.uniform(0, 240)
        self.vx = random.uniform(-0.3, 0.3)
        self.vy = random.uniform(0.1, 0.4)
        self.tam = random.uniform(1, 3)
        self.alpha = random.uniform(20, 60)
        self.color = random.choice([ROJO, AZUL, VERDE, AMARILLO])

    def actualizar(self):
        self.x += self.vx
        self.y += self.vy
        self.alpha += random.uniform(-1, 1)
        self.alpha = max(10, min(80, self.alpha))
        if self.y > 250:
            self.y = -5
            self.x = random.uniform(0, 320)

    def dibujar(self, surface):
        c = tuple(min(255, int(v * (self.alpha / 80))) for v in self.color)
        pygame.draw.circle(surface, c, (int(self.x), int(self.y)), self.tam)


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
        self.auto_bots = True
        self.frame = 0
        self.particulas = [ParticulaFondo() for _ in range(20)]

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

            if self.es_host and 170 <= y <= 188 and 100 <= x <= 220:
                self.auto_bots = not self.auto_bots
                return None

            if 130 <= y <= 150:
                modos = ["CLASICO", "RELAMPAGO", "CAOS", "DUELO", "ZOMBIE"]
                idx = (x - 30) // 52
                if 0 <= idx < len(modos):
                    return f"MODO:{modos[idx]}"

        return None

    def dibujar(self):
        self.frame += 1
        vw, vh = self.surface.get_size()
        sx = vw / 320
        sy = vh / 240

        self.surface.fill(NEGRO)

        for p in self.particulas:
            p.actualizar()
            p.dibujar(self.surface)

        glow = abs(math.sin(self.frame * 0.03)) * 20 + 30
        c = tuple(min(255, int(v * 0.3 + glow)) for v in AZUL)
        pygame.draw.rect(self.surface, c, (0, 0, 320, 240), 1)

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
            pulse = abs(math.sin(self.frame * 0.08 + i)) * 3
            r = pygame.Rect(avatar_x - pulse, y - pulse, 10 + pulse * 2, 14 + pulse * 2)
            pygame.draw.rect(self.surface, color, r)
            pygame.draw.rect(self.surface, BLANCO, r, 1)
            txt = self.font_peq.render(nombre, True, BLANCO)
            self.surface.blit(txt, (65, y))

        if self.es_host:
            if self.mensaje:
                msg = self.font_peq.render(self.mensaje, True, ROJO)
                self.surface.blit(msg, (160 - msg.get_width() // 2, 110))

            r = 4
            pulse_i = abs(math.sin(self.frame * 0.05)) * 30
            c_btn = tuple(min(255, int(v + pulse_i)) for v in VERDE)
            pygame.draw.rect(self.surface, c_btn, (100, 80, 120, 22), border_radius=r)
            pygame.draw.rect(self.surface, BLANCO, (100, 80, 120, 22), 1, border_radius=r)
            iniciar_txt = self.font_peq.render("INICIAR", True, NEGRO)
            self.surface.blit(iniciar_txt, (130, 83))

            color_bots = VERDE if self.auto_bots else ROJO
            pygame.draw.rect(self.surface, color_bots, (100, 170, 30, 18), border_radius=3)
            pygame.draw.rect(self.surface, BLANCO, (100, 170, 30, 18), 1, border_radius=3)
            if self.auto_bots:
                pygame.draw.line(self.surface, BLANCO, (105, 178), (113, 185), 2)
                pygame.draw.line(self.surface, BLANCO, (113, 185), (125, 172), 2)
            bot_txt = self.font_peq.render("Bots", True, BLANCO)
            self.surface.blit(bot_txt, (135, 172))
        else:
            esperando = self.font_peq.render("Esperando al host...", True, GRIS_CLARO)
            self.surface.blit(esperando, (160 - esperando.get_width() // 2, 85))

        modos = ["CLASICO", "RELAMPAGO", "CAOS", "DUELO", "ZOMBIE"]
        for i, m in enumerate(modos):
            x = 30 + i * 52
            y = 130
            color = ROJO if m == self.modo else GRIS
            if m == self.modo:
                pulse_m = abs(math.sin(self.frame * 0.08)) * 20
                color = tuple(min(255, int(v + pulse_m)) for v in color)
            pygame.draw.rect(self.surface, color, (x, y, 50, 20), border_radius=3)
            pygame.draw.rect(self.surface, BLANCO, (x, y, 50, 20), 1, border_radius=3)
            txt = self.font_peq.render(m[:4], True, BLANCO)
            self.surface.blit(txt, (x + 2, y + 2))

        jug_count = self.font_peq.render(f"Jugadores: {len(self.jugadores)}", True, BLANCO)
        self.surface.blit(jug_count, (160 - jug_count.get_width() // 2, 200))
