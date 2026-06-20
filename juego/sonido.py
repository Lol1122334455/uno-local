import pygame
import math
import array


class GestorSonido:
    def __init__(self):
        self.habilitado = False
        self.volumen = 0.4
        self.sonidos = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            self._generar_sonidos()
            self.habilitado = True
        except Exception:
            pass

    def _cuadrada(self, freq, duracion, volumen=0.5):
        sr = 22050
        n = int(sr * duracion)
        buf = array.array('h', [0]) * n
        for i in range(n):
            t = i / sr
            env = 1.0 - (i / n) * 0.6
            v = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
            v = v * (1.0 - abs(math.sin(math.pi * t * freq * 0.5)) * 0.3)
            buf[i] = int(volumen * 0.7 * env * 32767 * v)
        s = pygame.sndarray.make_sound(buf)
        s.set_volume(self.volumen)
        return s

    def _descendente(self, freq_start, freq_end, duracion, volumen=0.5):
        sr = 22050
        n = int(sr * duracion)
        buf = array.array('h', [0]) * n
        for i in range(n):
            t = i / sr
            frac = i / n
            freq = freq_start + (freq_end - freq_start) * frac
            env = 1.0 - frac * 0.5
            v = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
            buf[i] = int(volumen * 0.7 * env * 32767 * v)
        s = pygame.sndarray.make_sound(buf)
        s.set_volume(self.volumen)
        return s

    def _bip_doble(self, f1, f2, duracion, volumen=0.5):
        sr = 22050
        half = int(sr * duracion / 2)
        n = half * 2
        buf = array.array('h', [0]) * n
        for i in range(n):
            t = i / sr
            freq = f1 if i < half else f2
            env = 1.0 - (i % half) / half * 0.5
            v = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
            buf[i] = int(volumen * 0.7 * env * 32767 * v)
        s = pygame.sndarray.make_sound(buf)
        s.set_volume(self.volumen)
        return s

    def _tres_notas(self, notas, duracion_total, volumen=0.5):
        sr = 22050
        seg_por_nota = duracion_total / len(notas)
        n = int(sr * duracion_total)
        buf = array.array('h', [0]) * n
        for i in range(n):
            t = i / sr
            idx = min(int(t / seg_por_nota), len(notas) - 1)
            freq = notas[idx]
            local_t = (t - idx * seg_por_nota) / seg_por_nota
            env = 1.0 - local_t * 0.4
            v = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
            buf[i] = int(volumen * 0.7 * env * 32767 * v)
        s = pygame.sndarray.make_sound(buf)
        s.set_volume(self.volumen)
        return s

    def _generar_sonidos(self):
        self.sonidos['carta'] = self._cuadrada(660, 0.08, 0.4)
        self.sonidos['carta_especial'] = self._bip_doble(440, 880, 0.15, 0.5)
        self.sonidos['robar'] = self._descendente(330, 220, 0.12, 0.35)
        self.sonidos['comodin'] = self._tres_notas([523, 659, 784], 0.2, 0.5)
        self.sonidos['uno'] = self._tres_notas([440, 554, 659], 0.25, 0.6)
        self.sonidos['victoria'] = self._tres_notas([523, 659, 784], 0.3, 0.6)
        self.sonidos['derrota'] = self._descendente(440, 110, 0.4, 0.4)
        self.sonidos['click'] = self._cuadrada(880, 0.03, 0.25)
        self.sonidos['error'] = self._cuadrada(150, 0.25, 0.3)
        self.sonidos['evento'] = self._descendente(600, 900, 0.2, 0.5)
        self.sonidos['zombie'] = self._descendente(600, 100, 0.35, 0.5)
        self.sonidos['cura'] = self._tres_notas([392, 523, 659], 0.2, 0.5)

    def play(self, nombre):
        if self.habilitado and nombre in self.sonidos:
            self.sonidos[nombre].play()
