import pygame
import math
import array
import random

NOTAS = {
    'C2': 65.41, 'D2': 73.42, 'E2': 82.41, 'F2': 87.31, 'G2': 98.00, 'A2': 110.00, 'B2': 123.47,
    'C3': 130.81, 'D3': 146.83, 'E3': 164.81, 'F3': 174.61,
    'G3': 196.00, 'A3': 220.00, 'B3': 246.94,
    'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23,
    'G4': 392.00, 'A4': 440.00, 'B4': 493.88,
    'C5': 523.25, 'D5': 587.33, 'E5': 659.25, 'F5': 698.46,
    'G5': 783.99, 'A5': 880.00, 'B5': 987.77,
    'C6': 1046.50, 'C7': 2093.00,
}


def _clip(v):
    return max(-32768, min(32767, int(v)))


def _sine(freq, duracion, sr=22050):
    n = int(sr * duracion)
    buf = array.array('h', [0]) * n
    for i in range(n):
        t = i / sr
        v = math.sin(2 * math.pi * freq * t)
        buf[i] = _clip(28000 * v)
    return buf


def _sierra(freq, duracion, sr=22050):
    n = int(sr * duracion)
    buf = array.array('h', [0]) * n
    for i in range(n):
        t = i / sr
        v = 2.0 * (freq * t - math.floor(freq * t + 0.5))
        buf[i] = _clip(18000 * v)
    return buf


def _fm(freq, duracion, mod_freq=5, mod_depth=0.3, sr=22050):
    n = int(sr * duracion)
    buf = array.array('h', [0]) * n
    for i in range(n):
        t = i / sr
        v = math.sin(2 * math.pi * freq * t + mod_depth * math.sin(2 * math.pi * mod_freq * t))
        buf[i] = _clip(25000 * v)
    return buf


def _ruido(duracion, sr=22050):
    n = int(sr * duracion)
    buf = array.array('h', [0]) * n
    for i in range(n):
        buf[i] = _clip(random.gauss(0, 10000))
    return buf


def _envolvente(buf, ataque=0.01, caida=0.1, sostenido=0.7, liberacion=0.1, sr=22050):
    n = len(buf)
    n_ataque = int(sr * ataque)
    n_caida = int(sr * caida)
    n_liberacion = int(sr * liberacion)
    out = array.array('h', buf)
    for i in range(n):
        if i < n_ataque:
            env = i / n_ataque
        elif i < n_ataque + n_caida:
            env = 1.0 - (1.0 - sostenido) * (i - n_ataque) / n_caida
        elif i < n - n_liberacion:
            env = sostenido
        else:
            env = sostenido * (1.0 - (i - (n - n_liberacion)) / n_liberacion)
        out[i] = _clip(out[i] * env)
    return out


def _reverberar(buf, sr=22050, decay=0.25, taps=4):
    n = len(buf)
    out = array.array('h', buf)
    for t in range(1, taps + 1):
        delay = int(sr * 0.04 * t)
        gain = decay ** t
        for i in range(delay, n):
            out[i] = _clip(out[i] + buf[i - delay] * gain)
    return out


def _mezclar_buffers(buffers):
    if not buffers:
        return array.array('h', [0])
    max_n = max(len(b) for b in buffers)
    out = array.array('h', [0]) * max_n
    for buf in buffers:
        for i in range(len(buf)):
            out[i] = _clip(out[i] + buf[i])
    return out


def _hacer_nota(freq, duracion, eco=False, sr=22050):
    b = _sine(freq, duracion, sr)
    b2 = _sine(freq * 2, duracion, sr)
    for i in range(len(b2)):
        b2[i] = _clip(b2[i] * 0.3)
    b = _mezclar_buffers([b, b2])
    b = _envolvente(b, 0.005, 0.05, 0.6, 0.15, sr)
    if eco:
        b = _reverberar(b, sr, 0.2, 3)
    b = _envolvente(b, 0.005, 0.05, 0.6, 0.15, sr)
    return b


def _secuencia(frecuencias, duracion_por_nota, eco=False, sr=22050):
    total_n = 0
    partes = []
    for i, f in enumerate(frecuencias):
        b = _hacer_nota(f, duracion_por_nota, False, sr)
        offset = int(i * duracion_por_nota * 0.85 * sr)
        b2 = array.array('h', [0]) * (offset + len(b))
        for j in range(len(b)):
            b2[offset + j] = b[j]
        partes.append(b2)
        total_n = max(total_n, len(b2))
    out = _mezclar_buffers(partes)
    if eco:
        out = _reverberar(out, sr, 0.15, 3)
    return out


def _generar_musica_loop(duracion=8, sr=22050):
    n_total = int(sr * duracion)
    out = array.array('h', [0]) * n_total

    progresion = [
        [NOTAS['C3'], NOTAS['E4'], NOTAS['G4']],
        [NOTAS['A3'], NOTAS['C4'], NOTAS['E4']],
        [NOTAS['F3'], NOTAS['A4'], NOTAS['C5']],
        [NOTAS['G3'], NOTAS['B4'], NOTAS['D5']],
    ]

    seg_por_compas = duracion / len(progresion)
    for ci, acorde in enumerate(progresion):
        inicio = int(ci * seg_por_compas * sr)
        fin = int((ci + 1) * seg_por_compas * sr)
        for i in range(inicio, fin):
            if i >= n_total:
                break
            t = i / sr
            local_t = (i - inicio) / sr
            env = 0.3 + 0.7 * (1.0 - local_t / seg_por_compas)
            v = 0.0
            for f in acorde:
                onda = math.sin(2 * math.pi * f * t)
                v += onda * 0.25
                sub = math.sin(2 * math.pi * f * 0.5 * t) * 0.12
                v += sub
            out[i] = _clip(out[i] + 5000 * env * v)

        for i in range(inicio, min(inicio + int(0.1 * sr), n_total)):
            t = (i - inicio) / sr
            v = math.sin(2 * math.pi * NOTAS['C2'] * t)
            out[i] = _clip(out[i] + 4000 * (1.0 - t / 0.1) * v)

    return _envolvente(out, 0.01, 0.02, 0.9, 0.1, sr)


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
            env = 0.5 + 0.5 * (1.0 - local_t / seg_por_acorde)
            v = 0.0
            for f in acorde:
                v += math.sin(2 * math.pi * f * t) * 0.3
                v += math.sin(2 * math.pi * f * 0.5 * t) * 0.15
            out[i] = _clip(out[i] + 3500 * env * v)

    return _envolvente(out, 0.05, 0.05, 0.9, 0.1, sr)


class GestorSonido:
    def __init__(self):
        self.habilitado = False
        self.volumen = 0.5
        self.volumen_musica = 0.25
        self.sonidos = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=1024)
            self._generar_sonidos()
            self.habilitado = True
        except Exception:
            pass

    def _hacer_sonido(self, buf, volumen=1.0):
        s = pygame.sndarray.make_sound(buf)
        s.set_volume(self.volumen * volumen)
        return s

    def _generar_sonidos(self):
        sr = 22050

        b = _hacer_nota(880, 0.04, False, sr)
        self.sonidos['click'] = self._hacer_sonido(b, 0.3)

        b1 = _hacer_nota(660, 0.06, False, sr)
        b2 = _hacer_nota(990, 0.06, False, sr)
        b = _mezclar_buffers([b1, b2])
        b = _envolvente(b, 0.002, 0.02, 0.5, 0.1, sr)
        self.sonidos['carta'] = self._hacer_sonido(b, 0.5)

        b = _hacer_nota(440, 0.12, True, sr)
        b2 = _hacer_nota(880, 0.12, True, sr)
        b = _mezclar_buffers([b, b2])
        b = _envolvente(b, 0.005, 0.05, 0.4, 0.2, sr)
        self.sonidos['carta_especial'] = self._hacer_sonido(b, 0.5)

        b = _fm(330, 0.18, 3, 0.5, sr)
        b = _envolvente(b, 0.01, 0.05, 0.5, 0.2, sr)
        b = _reverberar(b, sr, 0.15, 3)
        self.sonidos['robar'] = self._hacer_sonido(b, 0.5)

        b = _secuencia([523, 659, 784], 0.05, True, sr)
        self.sonidos['comodin'] = self._hacer_sonido(b, 0.6)

        b = _secuencia([440, 554, 659, 880], 0.06, True, sr)
        self.sonidos['uno'] = self._hacer_sonido(b, 0.7)

        b = _secuencia([523, 659, 784, 1047, 784, 1047], 0.08, True, sr)
        b = _envolvente(b, 0.01, 0.02, 0.8, 0.3, sr)
        self.sonidos['victoria'] = self._hacer_sonido(b, 0.8)

        b = _sierra(220, 0.5, sr)
        b = _envolvente(b, 0.01, 0.1, 0.4, 0.4, sr)
        b = _reverberar(b, sr, 0.3, 5)
        self.sonidos['derrota'] = self._hacer_sonido(b, 0.5)

        b = _ruido(0.06, sr)
        b = _envolvente(b, 0.001, 0.01, 0.3, 0.05, sr)
        self.sonidos['error'] = self._hacer_sonido(b, 0.4)

        b1 = _fm(600, 0.15, 8, 0.4, sr)
        b2 = _fm(900, 0.15, 6, 0.3, sr)
        b = _mezclar_buffers([b1, b2])
        b = _envolvente(b, 0.005, 0.03, 0.5, 0.15, sr)
        b = _reverberar(b, sr, 0.12, 3)
        self.sonidos['evento'] = self._hacer_sonido(b, 0.6)

        b = _fm(150, 0.5, 2, 0.6, sr)
        b = _envolvente(b, 0.02, 0.1, 0.3, 0.3, sr)
        b = _reverberar(b, sr, 0.25, 4)
        self.sonidos['zombie'] = self._hacer_sonido(b, 0.6)

        b = _secuencia([392, 523, 659, 784], 0.05, True, sr)
        self.sonidos['cura'] = self._hacer_sonido(b, 0.6)

        b = _fm(200, 0.12, 15, 0.5, sr)
        b = _envolvente(b, 0.005, 0.03, 0.3, 0.1, sr)
        self.sonidos['shuffle'] = self._hacer_sonido(b, 0.3)

        b_musica_juego = _generar_musica_loop(8, sr)
        self.musica_juego = self._hacer_sonido(b_musica_juego, 0.5)

        b_musica_menu = _generar_musica_menu(12, sr)
        self.musica_menu = self._hacer_sonido(b_musica_menu, 0.5)

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
