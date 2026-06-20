TIPOS_MENSAJE = {
    "UNIRSE": "UNIRSE",
    "ASIGNADO": "ASIGNADO",
    "JUGADOR_CONECTADO": "JUGADOR_CONECTADO",
    "JUGADOR_DESCONECTADO": "JUGADOR_DESCONECTADO",
    "INICIAR": "INICIAR",
    "PARTIDA_INICIADA": "PARTIDA_INICIADA",
    "ESTADO_JUEGO": "ESTADO_JUEGO",
    "TU_MANO": "TU_MANO",
    "TU_TURNO": "TU_TURNO",
    "JUGAR": "JUGAR",
    "ROBAR": "ROBAR",
    "GRITAR_UNO": "GRITAR_UNO",
    "UNO_OLVIDADO": "UNO_OLVIDADO",
    "DESAFIAR": "DESAFIAR",
    "RESULTADO_DESAFIO": "RESULTADO_DESAFIO",
    "ERROR": "ERROR",
    "MENSAJE": "MENSAJE",
    "VICTORIA": "VICTORIA",
    "SELECCIONAR_MODO": "SELECCIONAR_MODO",
    "MODO_SELECCIONADO": "MODO_SELECCIONADO",
    "ACCION": "ACCION",
    "EVENTO": "EVENTO",
}


def crear_mensaje(tipo, **datos):
    msg = {"tipo": tipo}
    msg.update(datos)
    return msg


def codificar(mensaje_dict):
    import json
    return (json.dumps(mensaje_dict) + "\n").encode("utf-8")


def decodificar(datos):
    import json
    return json.loads(datos.decode("utf-8").strip())
