from juego.modos.clasico import PartidaClasica
from juego.modos.relampago import PartidaRelampago
from juego.modos.caos import PartidaCaos
from juego.modos.duelo import PartidaDuelo
from juego.modos.zombie import PartidaZombie

MODOS = {
    "CLASICO": PartidaClasica,
    "RELAMPAGO": PartidaRelampago,
    "CAOS": PartidaCaos,
    "DUELO": PartidaDuelo,
    "ZOMBIE": PartidaZombie,
}
