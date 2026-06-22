import pygame
import math
import array
import io
import struct
import wave
import random
import threading
import time

NOTAS = {
    'C2': 65.41, 'D2': 73.42, 'E2': 82.41, 'F2': 87.31, 'G2': 98.00, 'A2': 110.00, 'B2': 123.47,
    'C3': 130.81, 'D3': 146.83, 'E3': 164.81, 'F3': 174.61,
    'G3': 196.00, 'A3': 220.00, 'B3': 246.94,
    'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23,
    'G4': 392.00, 'A4': 440.00, 'B4': 493.88,
    'C5': 523.25, 'D5': 587.33, 'E5': 659.25, 'F5': 698.46,
    'G5': 783.99, 'A5': 880.00, 'B5': 987.77,
    'C6': 1046.50,
}


def _clip(v):
    return max(-32768, min(32767, int(v)))

def _mezclar_buffers(buffers, sr=22050):
    if not buffers:
        return array.array('h', [0])
    max_n = max(len(b) for b in buffers)
    out = array.array('h', [0]) * max_n
    for buf in buffers:
        for i in range(len(buf)):
            out[i] = _clip(out[i] + buf[i])
    return out


def _aplicar_eco(buf, sr=22050, delay=0.08, decay=0.3):
    n = len(buf)
    eco = array.array('h', [0]) * n
    offset = int(sr * delay)
    for i in range(offset, n):
        eco[i] = _clip(buf[i - offset] * decay)
    return _mezclar_buffers([buf, eco])


def _cuadrada(freq, duracion, sr=22050):
    n = int(sr * duracion)
    buf = array.array('h', [0]) * n
    for i in range(n):
        t = i / sr
        v = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
        buf[i] = _clip(32767 * v)
    return buf


def _diente_sierra(freq, duracion, sr=22050):
    n = int(sr * duracion)
    buf = array.array('h', [0]) * n
    for i in range(n):
        t = i / sr
        v = 2.0 * (freq * t - math.floor(freq * t + 0.5))
        buf[i] = _clip(32767 * v)
    return buf


def _triangular(freq, duracion, sr=22050):
    n = int(sr * duracion)
    buf = array.array('h', [0]) * n
    for i in range(n):
        t = i / sr
        phase = freq * t - math.floor(freq * t)
        v = 4.0 * abs(phase - 0.5) - 1.0
        buf[i] = _clip(32767 * v)
    return buf


def _ruido(duracion, sr=22050):
    n = int(sr * duracion)
    buf = array.array('h', [0]) * n
    for i in range(n):
        buf[i] = _clip(random.gauss(0, 12000))
    return buf


def _envolvente(buf, inicio=1.0, fin=0.0, curva=1.0):
    n = len(buf)
    for i in range(n):
        frac = i / n
        env = inicio + (fin - inicio) * (frac ** curva)
        buf[i] = _clip(buf[i] * env)
    return buf


def _pulsar(freqs, duracion_por_nota, sr=22050, eco=False):
    partes = []
    for f in freqs:
        b = _cuadrada(f, duracion_por_nota, sr)
        b = _envolvente(b, 1.0, 0.0, 2.0)
        partes.append(b)
    max_len = max(len(b) for b in partes) + int(0.015 * sr * len(partes))
    for i, b in enumerate(partes):
        offset = int(i * 0.015 * sr)
        b2 = array.array('h', [0]) * (max_len)
        for j in range(len(b)):
            b2[offset + j] = b[j]
        partes[i] = b2
    out = _mezclar_buffers(partes, sr)
    if eco:
        out = _aplicar_eco(out, sr, 0.06, 0.25)
    return out


def _generar_musica_loop(bpm=120, duracion=8, sr=22050):
    beats = int(duracion * bpm / 60)
    seg_por_beat = 60 / bpm
    n_total = int(sr * duracion)
    out = array.array('h', [0]) * n_total

    progresion = [
        [NOTAS['C3'], NOTAS['E4'], NOTAS['G4']],
        [NOTAS['A3'], NOTAS['C4'], NOTAS['E4']],
        [NOTAS['F3'], NOTAS['A4'], NOTAS['C5']],
        [NOTAS['G3'], NOTAS['B4'], NOTAS['D5']],
        [NOTAS['C3'], NOTAS['E4'], NOTAS['G4']],
        [NOTAS['A3'], NOTAS['C4'], NOTAS['E4']],
        [NOTAS['F3'], NOTAS['A4'], NOTAS['C5']],
        [NOTAS['G3'], NOTAS['B4'], NOTAS['D5']],
    ]

    for compas in range(min(len(progresion), 8)):
        inicio = int(compas * seg_por_beat * sr)
        for acorde in progresion[compas]:
            for sub in range(4):
                t_sub = inicio + int(sub * seg_por_beat / 4 * sr)
                if t_sub >= n_total:
                    break
                freq = acorde
                if sub == 1:
                    freq = acorde * 0.5
                elif sub == 3:
                    freq = acorde * 1.5
                n_nota = int(seg_por_beat / 4 * sr * 0.8)
                for i in range(n_nota):
                    idx = t_sub + i
                    if idx >= n_total:
                        break
                    t = i / sr
                    v = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
                    env = 1.0 - (i / n_nota) * 0.7
                    out[idx] = max(-32768, min(32767, out[idx] + int(6000 * env * v)))
        for i in range(int(seg_por_beat * sr)):
            idx = inicio + i
            if idx >= n_total:
                break
            t = i / sr
            v = 1.0 if math.sin(2 * math.pi * NOTAS['C2'] * t) >= 0 else -1.0
            env = 1.0 if (i % int(sr * 0.1)) < int(sr * 0.05) else 0.3
            out[idx] = max(-32768, min(32767, out[idx] + int(4000 * env * v)))

    return out


def _generar_musica_menu(duracion=12, sr=22050):
    n_total = int(sr * duracion)
    out = array.array('h', [0]) * n_total

    acordes = [
        [NOTAS['C4'], NOTAS['E4'], NOTAS['G4']],
        [NOTAS['A3'], NOTAS['C4'], NOTAS['E4']],
        [NOTAS['F3'], NOTAS['A3'], NOTAS['C4']],
        [NOTAS['G3'], NOTAS['B3'], NOTAS['D4']],
    ]

    seg_por_acorde = duracion / len(acordes)
    for idx_ac, acorde in enumerate(acordes):
        inicio = int(idx_ac * seg_por_acorde * sr)
        fin = int((idx_ac + 1) * seg_por_acorde * sr)
        for i in range(inicio, fin):
            if i >= n_total:
                break
            t = i / sr
            local_t = (i - inicio) / sr
            env = 1.0 - local_t / seg_por_acorde * 0.3
            v = 0.0
            for f in acorde:
                onda = 1.0 if math.sin(2 * math.pi * f * t) >= 0 else -1.0
                v += onda * 0.3
                onda2 = math.sin(2 * math.pi * f * 0.5 * t)
                v += onda2 * 0.15
            out[i] = max(-32768, min(32767, out[i] + int(5000 * env * v)))

    return out


def _buf_a_sound(buf, sr=22050):
    return pygame.sndarray.make_sound(buf)


class GestorSonido:
    def __init__(self):
        self.habilitado = False
        self.volumen = 0.6
        self.volumen_musica = 0.3
        self.sonidos = {}
        self.musica_actual = None
        self.musica_canal = None
        self._lock = threading.Lock()
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=1024)
            self.musica_canal = pygame.mixer.Channel(0)
            self._generar_sonidos()
            self.habilitado = True
        except Exception:
            pass

    def _hacer_sonido(self, buf, volumen=1.0, eco=False):
        if eco:
            buf = _aplicar_eco(buf)
        buf = _envolvente(buf, 1.0, 0.0, 1.5)
        s = _buf_a_sound(buf)
        s.set_volume(self.volumen * volumen)
        return s

    def _generar_sonidos(self):
        sr = 22050

        b = _cuadrada(880, 0.06, sr)
        b = _envolvente(b, 1.0, 0.0, 3.0)
        self.sonidos['click'] = self._hacer_sonido(b, 0.3)

        b = _cuadrada(660, 0.1, sr)
        b = _envolvente(b, 1.0, 0.0, 2.0)
        self.sonidos['carta'] = self._hacer_sonido(b, 0.5)

        b1 = _cuadrada(440, 0.08, sr)
        b2 = _cuadrada(880, 0.08, sr)
        b1 = _envolvente(b1, 1.0, 0.0, 2.0)
        b2 = _envolvente(b2, 1.0, 0.0, 2.0)
        self.sonidos['carta_especial'] = self._hacer_sonido(_mezclar_buffers([b1, b2]), 0.5)

        b = _diente_sierra(330, 0.15, sr)
        b = _envolvente(b, 1.0, 0.0, 0.8)
        self.sonidos['robar'] = self._hacer_sonido(b, 0.5, eco=True)

        b = _pulsar([523, 659, 784], 0.06, sr, eco=True)
        self.sonidos['comodin'] = self._hacer_sonido(b, 0.6)

        b = _pulsar([440, 554, 659, 880], 0.07, sr, eco=True)
        self.sonidos['uno'] = self._hacer_sonido(b, 0.7)

        melodia = [523, 659, 784, 1047, 784, 1047]
        b = _pulsar(melodia, 0.08, sr, eco=True)
        b = _envolvente(b, 1.0, 0.0, 1.2)
        self.sonidos['victoria'] = self._hacer_sonido(b, 0.8, eco=True)

        b = _diente_sierra(440, 0.5, sr)
        b = _envolvente(b, 1.0, 0.0, 0.5)
        self.sonidos['derrota'] = self._hacer_sonido(b, 0.5, eco=True)

        b = _ruido(0.05, sr)
        b = _envolvente(b, 1.0, 0.0, 1.0)
        self.sonidos['error'] = self._hacer_sonido(b, 0.4)

        b1 = _diente_sierra(600, 0.12, sr)
        b2 = _diente_sierra(900, 0.12, sr)
        b1 = _envolvente(b1, 1.0, 0.0, 1.0)
        b2 = _envolvente(b2, 1.0, 0.0, 1.0)
        self.sonidos['evento'] = self._hacer_sonido(_mezclar_buffers([b1, b2]), 0.6)

        b = _diente_sierra(600, 0.4, sr)
        for i in range(len(b)):
            t = i / sr
            b[i] = int(b[i] * (0.5 + 0.5 * math.sin(2 * math.pi * 8 * t)))
        b = _envolvente(b, 1.0, 0.0, 0.3)
        self.sonidos['zombie'] = self._hacer_sonido(b, 0.6, eco=True)

        b = _pulsar([392, 523, 659, 784], 0.06, sr, eco=True)
        self.sonidos['cura'] = self._hacer_sonido(b, 0.6)

        b = _diente_sierra(200, 0.15, sr)
        b = _envolvente(b, 1.0, 0.0, 0.5)
        self.sonidos['shuffle'] = self._hacer_sonido(b, 0.3)

        b = _cuadrada(440, 0.3, sr)
        b = _envolvente(b, 0.0, 0.0, 1.0)
        for i in range(len(b)):
            t = i / sr
            mod = 1.0 + 3.0 * (t % 0.05) / 0.05 if (t % 0.05) < 0.01 else 1.0
            b[i] = int(b[i] * 0.25 * math.sin(2 * math.pi * 5 * t))
        self.sonidos['countdown'] = self._hacer_sonido(b, 0.4)

        b_musica_game = _generar_musica_loop(120, 8, sr)
        self.musica_juego = _buf_a_sound(b_musica_game)
        self.musica_juego.set_volume(self.volumen_musica)

        b_musica_menu = _generar_musica_menu(12, sr)
        self.musica_menu = _buf_a_sound(b_musica_menu)
        self.musica_menu.set_volume(self.volumen_musica)

    def play(self, nombre):
        if self.habilitado and nombre in self.sonidos:
            self.sonidos[nombre].play()

    def play_musica(self, tipo):
        if not self.habilitado:
            return
        self.stop_musica()
        if tipo == "menu" and hasattr(self, 'musica_menu'):
            self.musica_menu.play(loops=-1)
        elif tipo == "juego" and hasattr(self, 'musica_juego'):
            self.musica_juego.play(loops=-1)

    def stop_musica(self):
        if hasattr(self, 'musica_menu'):
            self.musica_menu.stop()
        if hasattr(self, 'musica_juego'):
            self.musica_juego.stop()
