import pygame
import math
import random

NEGRO = (16, 16, 24)
BLANCO = (232, 232, 240)
GRIS = (64, 64, 72)
GRIS_CLARO = (144, 144, 152)
ROJO = (216, 40, 40)
VERDE = (40, 176, 40)
AZUL = (40, 72, 216)
AMARILLO = (224, 200, 24)
NARANJA = (224, 128, 16)
VIOLETA = (168, 48, 200)
FONDO_MESA = (12, 64, 28)
BORDE_CARTA = (20, 16, 28)
MESA_OSCURO = (8, 48, 20)
MESA_BORDE = (6, 38, 14)

COLORES_MAP = {
    "ROJO": ROJO, "AZUL": AZUL, "VERDE": VERDE, "AMARILLO": AMARILLO, "SIN_COLOR": GRIS
}

ANCHO_CARTA = 24
ALTO_CARTA = 36
CENTRO_X = 148
CENTRO_Y = 82
MAZO_X = 240
MAZO_Y = 56

# Seats for 2, 3, 4 players. Index 0 = always the human (bottom)
SEATS = {
    2: [(160, 188), (160, 24)],
    3: [(160, 188), (268, 100), (160, 24)],
    4: [(160, 188), (268, 100), (160, 24), (52, 100)],
}


class Animacion:
    def __init__(self, tipo, carta, origen, destino, duracion=25, dorso=False, retraso=0):
        self.tipo = tipo
        self.carta = carta
        self.origen = origen
        self.destino = destino
        self.duracion = duracion
        self.dorso = dorso
        self.retraso = retraso
        self.progreso = 0.0
        self.activo = True

    def actualizar(self):
        if not self.activo:
            return
        if self.retraso > 0:
            self.retraso -= 1
            return
        self.progreso += 1.0 / max(1, self.duracion)
        if self.progreso >= 1.0:
            self.progreso = 1.0
            self.activo = False
            return True
        return False

    def posicion_actual(self):
        t = self.progreso
        t_suave = t * t * (3 - 2 * t)
        if t > 0.85:
            rebote = math.sin((t - 0.85) / 0.15 * math.pi) * 4
        else:
            rebote = 0
        x = self.origen[0] + (self.destino[0] - self.origen[0]) * t_suave
        y = self.origen[1] + (self.destino[1] - self.origen[1]) * t_suave + rebote
        return (int(x), int(y))

    def escala_actual(self):
        if self.progreso < 0.2:
            return 0.6 + 0.4 * (self.progreso / 0.2)
        if self.progreso > 0.85:
            return 1.0 + 0.15 * math.sin((self.progreso - 0.85) / 0.15 * math.pi)
        return 1.0


class Particula:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-1.5, 1.5)
        self.vy = random.uniform(-2.0, -0.5)
        self.color = color
        self.vida = random.randint(15, 25)
        self.max_vida = self.vida

    def actualizar(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.15
        self.vida -= 1
        return self.vida > 0

    def dibujar(self, surface):
        alpha = self.vida / self.max_vida
        size = max(1, int(3 * alpha))
        c = tuple(int(v * alpha * 0.6 + 64 * (1 - alpha)) for v in self.color)
        pygame.draw.rect(surface, c, (int(self.x), int(self.y), size, size))


class Mesa:
    def __init__(self, surface, font_peq, font_gde, scale=3, sonido=None):
        self.surface = surface
        self.font_peq = font_peq
        self.font_gde = font_gde
        self.scale = scale
        self.sonido = sonido
        self.estado = None
        self.mi_id = None
        self.mi_mano = []
        self.carta_seleccionada = None
        self.carta_hover = None
        self.mostrando_color = False
        self.animaciones = []
        self.particulas = []
        self.frame = 0
        self.ultimo_id_carta_activa = None
        self.ultima_accion_vista = None
        self.cantidades_previas = []
        self.texto_notificacion = None
        self.texto_notif_timer = 0
        self.turno_pulso = 0
        self.en_pausa = False
        self.carta_activa_pulso = 0

    def _num_jugadores(self):
        if not self.estado:
            return 0
        return len(self.estado.get("jugadores", []))

    def _posicion_asiento(self, id_jugador):
        n = self._num_jugadores()
        if n < 2:
            return (160, 100)
        asiento = (id_jugador - self.mi_id) % n
        seats = SEATS.get(n, SEATS[2])
        if asiento < len(seats):
            return seats[asiento]
        return (160, 100)

    def actualizar_estado(self, estado, mi_id):
        cant_prev = self.estado.get("cantidades", []) if self.estado else []
        self.estado = estado
        self.mi_id = mi_id
        if "tu_mano" in estado:
            self.mi_mano = estado["tu_mano"]

        accion = estado.get("ultima_accion")
        if accion and accion != self.ultima_accion_vista:
            self._procesar_accion(accion)
            self.ultima_accion_vista = accion

        if "carta_activa" in estado:
            ca = estado["carta_activa"]
            if ca:
                nuevo_id = ca.get("id")
                if nuevo_id != self.ultimo_id_carta_activa:
                    self.ultimo_id_carta_activa = nuevo_id

        self.cantidades_previas = cant_prev

    def _procesar_accion(self, accion):
        tipo = accion.get("tipo")

        if tipo == "JUGAR":
            id_jug = accion.get("id_jugador")
            carta = accion.get("carta")
            if not carta:
                return

            if id_jug == self.mi_id:
                orig = self._origen_carta_humano()
            else:
                orig = self._posicion_asiento(id_jug)

            anim = Animacion("JUGAR", carta, orig, (CENTRO_X, CENTRO_Y), duracion=22)
            self.animaciones.append(anim)

            tipo_carta = carta.get("tipo", "")
            es_especial = tipo_carta != "NUMERO" and tipo_carta != "CURA"
            if self.sonido:
                self.sonido.play("carta_especial" if es_especial else "carta")
            if tipo_carta in ("COMODIN", "MAS4", "COMODIN_PROBABILIDAD", "COMODIN_ESPEJO",
                             "COMODIN_DOBLE", "COMODIN_PERDER_TURNO", "COMODIN_SANGUINEO",
                             "COMODIN_VAMPIRO", "COMODIN_REFUGIO"):
                if self.sonido:
                    self.sonido.play("comodin")

            jugadores = self.estado.get("jugadores", [])
            nombre = next((j["nombre"] for j in jugadores if j["id"] == id_jug), "Alguien")
            self._mostrar_notificacion(f"{nombre} jug\u00f3")
            self._generar_particulas(CENTRO_X + ANCHO_CARTA // 2, CENTRO_Y + ALTO_CARTA // 2)

            pen = accion.get("penalizacion")
            if pen:
                id_pen = pen["id_jugador"]
                cantidad = pen["cantidad"]
                dest = self._posicion_asiento(id_pen)
                if id_pen == self.mi_id:
                    dest = (160, 200)
                for i in range(cantidad):
                    a = Animacion("PENALIZACION", None, (MAZO_X, MAZO_Y), dest,
                                  duracion=20, dorso=True, retraso=i * 4)
                    self.animaciones.append(a)
                nom_pen = next((j["nombre"] for j in jugadores if j["id"] == id_pen), "Alguien")
                self._mostrar_notificacion(f"+{cantidad} para {nom_pen}!")

        elif tipo == "ROBAR":
            id_jug = accion.get("id_jugador")
            dest = self._posicion_asiento(id_jug)
            if id_jug == self.mi_id:
                dest = (160, 200)
            anim = Animacion("ROBAR", None, (MAZO_X, MAZO_Y), dest, duracion=18, dorso=True)
            self.animaciones.append(anim)
            if self.sonido:
                self.sonido.play("robar")

        elif tipo == "EVENTO":
            self._mostrar_notificacion(f"Evento: {accion.get('evento','')}")
            if self.sonido:
                self.sonido.play("evento")
        elif tipo == "CONVERTIDO":
            self._mostrar_notificacion("Alguien se convirtio!")
            if self.sonido:
                self.sonido.play("zombie")
        elif tipo.startswith("ZOMBIE_"):
            self._mostrar_notificacion("Zombie ataca!")
            if self.sonido:
                self.sonido.play("zombie")

    def _origen_carta_humano(self):
        n = self._num_jugadores()
        if n == 0:
            return (160, 188)
        old_count = len(self.mi_mano) + 1
        espacio = min(ANCHO_CARTA + 2, (280 - ANCHO_CARTA) // max(1, old_count - 1))
        inicio_x = (320 - max(0, old_count - 1) * espacio - ANCHO_CARTA) // 2
        idx = self.carta_seleccionada or 0
        return (inicio_x + min(old_count - 1, idx) * espacio, 190)

    def _generar_particulas(self, x, y):
        colores = [ROJO, AZUL, VERDE, AMARILLO, BLANCO]
        for _ in range(12):
            self.particulas.append(Particula(x, y, random.choice(colores)))

    def _mostrar_notificacion(self, texto):
        self.texto_notificacion = texto
        self.texto_notif_timer = 75

    def manejar_evento(self, evento):
        if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
            if not self.mostrando_color:
                self.en_pausa = not self.en_pausa
            return None

        if self.en_pausa:
            if evento.type == pygame.MOUSEBUTTONDOWN:
                x = evento.pos[0] // self.scale
                y = evento.pos[1] // self.scale
                if 100 <= x <= 220:
                    if 78 <= y <= 98:
                        self.en_pausa = False
                        return "REANUDAR"
                    if 104 <= y <= 124:
                        self.en_pausa = False
                        return "IR_MENU"
                    if 130 <= y <= 150:
                        return "SALIR"
            return None

        if self.mostrando_color:
            return self._manejar_color(evento)

        if evento.type == pygame.MOUSEBUTTONDOWN:
            x = evento.pos[0] // self.scale
            y = evento.pos[1] // self.scale
            if self._rect_robar().collidepoint(x, y):
                self.carta_seleccionada = None
                return "ROBAR"
            if self._rect_uno().collidepoint(x, y):
                return "UNO"
            if self.carta_seleccionada is not None and self._rect_jugar().collidepoint(x, y):
                carta = self.mi_mano[self.carta_seleccionada]
                return f"JUGAR:{carta['id']}"
            idx = self._carta_en_pos(x, y)
            if idx is not None and idx < len(self.mi_mano):
                if idx == self.carta_seleccionada:
                    carta = self.mi_mano[idx]
                    if not self._es_comodin(carta):
                        self.carta_seleccionada = None
                        return f"JUGAR:{carta['id']}"
                self.carta_seleccionada = idx
                carta = self.mi_mano[idx]
                if self._es_comodin(carta):
                    self.mostrando_color = True
            else:
                self.carta_seleccionada = None

        elif evento.type == pygame.MOUSEMOTION:
            x = evento.pos[0] // self.scale
            y = evento.pos[1] // self.scale
            self.carta_hover = self._carta_en_pos(x, y)
        return None

    def _es_comodin(self, carta):
        tipo = carta["tipo"]
        return tipo in ("COMODIN", "MAS4", "COMODIN_PROBABILIDAD", "COMODIN_ESPEJO",
                        "COMODIN_DOBLE", "COMODIN_PERDER_TURNO", "COMODIN_SANGUINEO",
                        "COMODIN_VAMPIRO", "COMODIN_REFUGIO")

    def _carta_en_pos(self, x, y):
        n = len(self.mi_mano)
        if n == 0:
            return None
        espacio = min(ANCHO_CARTA + 2, (280 - ANCHO_CARTA) // max(1, n - 1))
        inicio_x = (320 - max(0, n - 1) * espacio - ANCHO_CARTA) // 2
        y_mano = 188
        for i in range(n):
            cx = inicio_x + i * espacio
            if cx <= x <= cx + ANCHO_CARTA and y_mano <= y <= y_mano + ALTO_CARTA:
                return i
        return None

    def _rect_robar(self):
        return pygame.Rect(238, 148, 52, 20)

    def _rect_uno(self):
        return pygame.Rect(10, 148, 50, 16)

    def _rect_jugar(self):
        return pygame.Rect(120, 163, 60, 18)

    def _manejar_color(self, evento):
        if evento.type == pygame.MOUSEBUTTONDOWN:
            x = evento.pos[0] // self.scale
            y = evento.pos[1] // self.scale
            colores = [("ROJO", 94), ("AZUL", 124), ("VERDE", 154), ("AMARILLO", 184)]
            for nombre, cx in colores:
                if cx <= x <= cx + 28 and 78 <= y <= 106:
                    self.mostrando_color = False
                    if self.carta_seleccionada is not None and self.carta_seleccionada < len(self.mi_mano):
                        id_carta = self.mi_mano[self.carta_seleccionada]["id"]
                        return f"JUGAR:{id_carta}:{nombre}"
        return None

    def _dibujar_mesa(self):
        pygame.draw.ellipse(self.surface, MESA_OSCURO, (40, 28, 240, 155))
        pygame.draw.ellipse(self.surface, MESA_BORDE, (40, 28, 240, 155), 2)
        pygame.draw.ellipse(self.surface, (10, 56, 24), (58, 40, 204, 130), 1)

    def _dibujar_carta(self, x, y, carta, seleccionada=False, hover=False, escala=1.0):
        cw = int(ANCHO_CARTA * escala)
        ch = int(ALTO_CARTA * escala)
        if seleccionada:
            y -= 12
        bx = x
        by = y

        pygame.draw.rect(self.surface, BORDE_CARTA, (bx - 1, by - 1, cw + 2, ch + 2))
        col_fondo = (248, 244, 240) if escala >= 0.9 else (220, 216, 212)
        pygame.draw.rect(self.surface, col_fondo, (bx, by, cw, ch))

        if hover or seleccionada:
            brillo = NARANJA if hover else (255, 240, 80)
            pygame.draw.rect(self.surface, brillo, (bx - 2, by - 2, cw + 4, ch + 4), 2)
        else:
            pygame.draw.rect(self.surface, BORDE_CARTA, (bx, by, cw, ch), 1)

        color_str = carta.get("color", "SIN_COLOR")
        color_rgb = COLORES_MAP.get(color_str, GRIS)
        tipo = carta.get("tipo", "")
        cx = bx + cw // 2
        cy = by + ch // 2

        if color_str != "SIN_COLOR":
            pygame.draw.rect(self.surface, color_rgb, (bx + 2, by + 2, cw - 4, ch - 4))
            pygame.draw.rect(self.surface, (255, 255, 255, 80), (bx + 2, by + 2, cw - 4, 4))
            if tipo == "NUMERO" and carta.get("numero") is not None:
                num = str(carta["numero"])
                txt = self.font_peq.render(num, True, BLANCO)
                self.surface.blit(txt, (cx - txt.get_width() // 2, cy - txt.get_height() // 2))
                txt_peq = self.font_peq.render(num, True, BORDE_CARTA)
                self.surface.blit(txt_peq, (bx + 2, by + 2))
            else:
                sim = self._simbolo_carta(carta)
                txt = self.font_peq.render(sim, True, BLANCO)
                self.surface.blit(txt, (cx - txt.get_width() // 2, cy - txt.get_height() // 2))
        else:
            centro_color = color_rgb if color_rgb != GRIS else (180, 180, 200)
            pygame.draw.rect(self.surface, centro_color, (bx + 3, by + 3, cw - 6, ch - 6))
            pygame.draw.rect(self.surface, (255, 255, 255, 60), (bx + 3, by + 3, cw - 6, 4))
            sim = self._simbolo_carta(carta)
            txt = self.font_peq.render(sim, True, BLANCO)
            self.surface.blit(txt, (cx - txt.get_width() // 2, cy - txt.get_height() // 2))

    def _dibujar_carta_dorso(self, x, y, escala=1.0):
        cw = int(ANCHO_CARTA * escala)
        ch = int(ALTO_CARTA * escala)
        pygame.draw.rect(self.surface, BORDE_CARTA, (x - 1, y - 1, cw + 2, ch + 2))
        pygame.draw.rect(self.surface, (40, 36, 72), (x, y, cw, ch))
        pygame.draw.rect(self.surface, (56, 52, 96), (x + 2, y + 2, cw - 4, ch - 4))
        pygame.draw.rect(self.surface, (72, 68, 120), (x + 4, y + 4, cw - 8, ch - 8))
        txt = self.font_peq.render("U", True, (100, 100, 180))
        self.surface.blit(txt, (x + cw // 2 - txt.get_width() // 2,
                                y + ch // 2 - txt.get_height() // 2))

    def _simbolo_carta(self, carta):
        tipo = carta.get("tipo", "")
        s = {
            "SALTO": "S", "REVERSA": "R", "MAS2": "+2", "COMODIN": "\u2605",
            "MAS4": "+4", "CAMBIO": "~", "BLOQUEO": "B", "VISION": "V",
            "ESPADA": "Sd", "VENENO": "Vn", "CURA": "+0", "ANTIDOTO": "A",
            "TRAMPA": "T", "CORTOCIRCUITO": "CC", "RELAMPAGO": "RL",
            "ESCUDO": "Es", "COMODIN_PROBABILIDAD": "??",
            "COMODIN_ESPEJO": "><", "COMODIN_DOBLE": "2x",
            "COMODIN_PERDER_TURNO": "XX", "COMODIN_SANGUINEO": "Sa",
            "COMODIN_VAMPIRO": "Vm", "COMODIN_REFUGIO": "Rf"
        }
        return s.get(tipo, "?")

    def _dibujar_carta_activa(self, x, y, carta):
        if not carta:
            return
        pulso = abs(math.sin(self.frame * 0.06)) * 3
        glow_color = COLORES_MAP.get(carta.get("color", "SIN_COLOR"), GRIS_CLARO)
        for r in range(6, 0, -1):
            alpha = 40 - r * 6
            if alpha > 0:
                gc = tuple(min(255, c + 60) for c in glow_color)
                pygame.draw.rect(self.surface, gc + (alpha,),
                                 (x - r - 1, y - r - 1, ANCHO_CARTA + r * 2 + 2, ALTO_CARTA + r * 2 + 2), 1)
        self._dibujar_carta(x, y, carta)

    def _dibujar_mazo(self, x, y):
        for i in range(3):
            dx = x + i * 2
            dy = y + i * 2
            self._dibujar_carta_dorso(dx, dy)
        pygame.draw.rect(self.surface, BORDE_CARTA, (x - 1, y - 1, ANCHO_CARTA + 2, ALTO_CARTA + 2), 1)

    def _dibujar_jugadores(self):
        if not self.estado:
            return
        jugadores = self.estado.get("jugadores", [])
        cantidades = self.estado.get("cantidades", [])
        turno = self.estado.get("turno")

        for j in jugadores:
            jid = j["id"]
            nombre = j["nombre"][:10]

            if jid == self.mi_id:
                ncartas = len(self.mi_mano)
                txt = self.font_peq.render(f"{nombre}: {ncartas}", True, (220, 220, 120))
                self.surface.blit(txt, (4, 216))
                if turno == jid:
                    self.turno_pulso = (self.turno_pulso + 1) % 50
                    p = abs(self.turno_pulso - 25) / 25
                    b = int(180 + 75 * p)
                    ind = self.font_peq.render("<<< TU TURNO >>>", True, (b, b, 40))
                    self.surface.blit(ind, (160 - ind.get_width() // 2, 140))
                continue

            pos = self._posicion_asiento(jid)
            ncartas = cantidades[jid] if jid < len(cantidades) else j.get("cantidad_cartas", 0)
            es_turno = (turno == jid)

            vida = j.get("vida")
            infeccion = j.get("infeccion", 0)
            linea_nombre = nombre
            if vida is not None:
                linea_nombre += f" H{vida}"
            if infeccion:
                linea_nombre += " Z" * infeccion

            txt = self.font_peq.render(linea_nombre, True, BLANCO)
            self.surface.blit(txt, (pos[0] - txt.get_width() // 2, pos[1] - 28))

            mostrar = min(ncartas, 5)
            for i in range(mostrar):
                dx = pos[0] - 10 + i * 2
                dy = pos[1] - 14 + i * 1
                self._dibujar_carta_dorso(dx, dy, escala=0.65)

            ctxt = self.font_peq.render(str(ncartas), True, (255, 255, 200))
            self.surface.blit(ctxt, (pos[0] - ctxt.get_width() // 2, pos[1] + 8))

            if es_turno:
                pulso = abs(math.sin(self.frame * 0.08)) * 0.5 + 0.5
                col = (int(200 * pulso + 55), int(200 * pulso + 55), 40)
                tri = self.font_peq.render(">", True, col)
                self.surface.blit(tri, (pos[0] - tri.get_width() // 2, pos[1] + 18))

    def _dibujar_selector_color(self):
        s = pygame.Surface((320, 240), pygame.SRCALPHA)
        s.fill((0, 0, 0, 200))
        self.surface.blit(s, (0, 0))
        pygame.draw.rect(self.surface, BORDE_CARTA, (86, 68, 148, 50))
        txt = self.font_peq.render("ELEGIR COLOR", True, BLANCO)
        self.surface.blit(txt, (160 - txt.get_width() // 2, 72))
        colores = [("ROJO", ROJO, 94), ("AZUL", AZUL, 124), ("VERDE", VERDE, 154), ("AMARILLO", AMARILLO, 184)]
        for nombre, color, cx in colores:
            pygame.draw.rect(self.surface, BORDE_CARTA, (cx - 1, 88 - 1, 30, 30))
            pygame.draw.rect(self.surface, color, (cx, 88, 28, 28))
            pygame.draw.rect(self.surface, (255, 255, 255, 40), (cx, 88, 28, 4))

    def _dibujar_animaciones(self):
        for anim in self.animaciones[:]:
            anim.actualizar()
            pos = anim.posicion_actual()
            esc = anim.escala_actual()
            if anim.carta:
                self._dibujar_carta(pos[0], pos[1], anim.carta, escala=esc)
            elif anim.dorso:
                self._dibujar_carta_dorso(pos[0], pos[1], escala=esc * 0.8)
            if not anim.activo:
                self.animaciones.remove(anim)

    def _dibujar_particulas(self):
        for p in self.particulas[:]:
            if not p.actualizar():
                self.particulas.remove(p)
                continue
            p.dibujar(self.surface)

    def _dibujar_notificacion(self):
        if self.texto_notificacion and self.texto_notif_timer > 0:
            self.texto_notif_timer -= 1
            txt = self.font_peq.render(self.texto_notificacion, True, (255, 255, 200))
            x = 160 - txt.get_width() // 2
            y = 118
            f = pygame.Surface((txt.get_width() + 6, txt.get_height() + 4))
            f.fill(NEGRO)
            f.set_alpha(min(180, self.texto_notif_timer * 5))
            self.surface.blit(f, (x - 3, y - 2))
            txt.set_alpha(min(255, self.texto_notif_timer * 8))
            self.surface.blit(txt, (x, y))

    def dibujar(self):
        self.frame += 1
        self.surface.fill(FONDO_MESA)

        if not self.estado:
            txt = self.font_gde.render("UNO", True, BLANCO)
            self.surface.blit(txt, (160 - txt.get_width() // 2, 80))
            txt = self.font_peq.render("Esperando partida...", True, GRIS_CLARO)
            self.surface.blit(txt, (160 - txt.get_width() // 2, 110))
            return

        self._dibujar_mesa()

        self._dibujar_jugadores()

        sent = self.estado.get("sentido", 1)
        stxt = self.font_peq.render("->" if sent == 1 else "<-", True, GRIS_CLARO)
        self.surface.blit(stxt, (160 - stxt.get_width() // 2, 52))

        self.carta_activa_pulso = abs(math.sin(self.frame * 0.04))

        carta_activa = self.estado.get("carta_activa")
        if carta_activa:
            self._dibujar_carta_activa(CENTRO_X, CENTRO_Y, carta_activa)

        self._dibujar_mazo(MAZO_X, MAZO_Y)

        pygame.draw.rect(self.surface, BORDE_CARTA, (236, 146, 56, 24))
        pygame.draw.rect(self.surface, (48, 160, 48), (238, 148, 52, 20))
        robar_txt = self.font_peq.render("ROBAR", True, BLANCO)
        self.surface.blit(robar_txt, (250 - robar_txt.get_width() // 2, 152))

        pulso_uno = abs(math.sin(self.frame * 0.12))
        cu = (int(200 + 55 * pulso_uno), int(180 + 40 * pulso_uno), int(20 + 10 * pulso_uno))
        pygame.draw.rect(self.surface, BORDE_CARTA, (8, 146, 54, 20))
        pygame.draw.rect(self.surface, cu, (10, 148, 50, 16))
        uno_txt = self.font_peq.render("UNO!", True, NEGRO)
        self.surface.blit(uno_txt, (35 - uno_txt.get_width() // 2, 150))

        if self.carta_seleccionada is not None and self.carta_seleccionada < len(self.mi_mano):
            pygame.draw.rect(self.surface, BORDE_CARTA, (118, 161, 64, 22))
            pygame.draw.rect(self.surface, NARANJA, (120, 163, 60, 18))
            jugar_txt = self.font_peq.render("JUGAR", True, BLANCO)
            self.surface.blit(jugar_txt, (150 - jugar_txt.get_width() // 2, 165))

        n = len(self.mi_mano)
        if n > 0:
            espacio = min(ANCHO_CARTA + 2, (280 - ANCHO_CARTA) // max(1, n - 1))
            inicio_x = (320 - max(0, n - 1) * espacio - ANCHO_CARTA) // 2
            y_mano = 188
            for i, cd in enumerate(self.mi_mano):
                cx = inicio_x + i * espacio
                sel = (i == self.carta_seleccionada)
                hover = (i == self.carta_hover)
                self._dibujar_carta(cx, y_mano, cd, seleccionada=sel, hover=hover)

        if self.mostrando_color:
            self._dibujar_selector_color()

        self._dibujar_animaciones()
        self._dibujar_particulas()
        self._dibujar_notificacion()

        if self.en_pausa:
            s = pygame.Surface((320, 240), pygame.SRCALPHA)
            s.fill((0, 0, 0, 210))
            self.surface.blit(s, (0, 0))
            pygame.draw.rect(self.surface, BORDE_CARTA, (88, 58, 144, 100))
            txt = self.font_gde.render("PAUSA", True, BLANCO)
            self.surface.blit(txt, (160 - txt.get_width() // 2, 62))
            for i, (texto, y) in enumerate([("REANUDAR", 80), ("MENU", 106), ("SALIR", 132)]):
                pygame.draw.rect(self.surface, (48, 48, 56), (100, y, 120, 22))
                pygame.draw.rect(self.surface, BLANCO, (100, y, 120, 22), 1)
                t = self.font_peq.render(texto, True, BLANCO)
                self.surface.blit(t, (160 - t.get_width() // 2, y + 4))
