"""Punto ÚNICO de integración para web y API JSON. Pendiente del alumnado."""
from app import api_clients, db, llm
import time
import requests

TIPOS_VALIDOS = {"cultural", "gastronomica", "naturaleza", "familiar"}
DURACIONES_VALIDAS = {2, 4, 6}


def procesar_solicitud(ciudad: str, tipo_turismo: str, duracion_horas: int, preferencias: str = "") -> dict:
    inicio = time.time()

    # 1) Validación
    ciudad = (ciudad or "").strip()
    preferencias = (preferencias or "").strip()
    duracion_horas = int(duracion_horas)
    if not ciudad or len(ciudad) > 80:
        raise ValueError("La ciudad es obligatoria (máximo 80 caracteres)")
    if tipo_turismo not in TIPOS_VALIDOS:
        raise ValueError("Tipo de turismo no válido")
    if duracion_horas not in DURACIONES_VALIDAS:
        raise ValueError("La duración debe ser 2, 4 o 6 horas")
    if len(preferencias) > 200:
        raise ValueError("Las preferencias no pueden superar 200 caracteres")

   # 2) Coordenadas y clima
    g = api_clients.geocodificar(ciudad)
    meteo = api_clients.obtener_meteorologia(g["lat"], g["lon"])

    # 3) Lugares reales
    lugares = api_clients.obtener_lugares(g["lat"], g["lon"], tipo_turismo)

    # 4) Contexto y modelo
    contexto = {
        "ciudad": g["ciudad"], "tipo_turismo": tipo_turismo,
        "duracion_horas": duracion_horas, "preferencias": preferencias,
        "meteorologia": meteo, "lugares": lugares,
    }
    itinerario, prompt = llm.generar_itinerario(contexto)
    # 5) Guardar en PostgreSQL
    duracion_ms = int((time.time() - inicio) * 1000)
    solicitud_id = db.guardar_solicitud({
        "ciudad": g["ciudad"], "pais": g["pais"], "tipo_turismo": tipo_turismo,
        "duracion_horas": duracion_horas, "preferencias": preferencias,
        "latitud": g["lat"], "longitud": g["lon"],
        "meteorologia": meteo, "lugares": lugares,
        "prompt_usado": prompt, "itinerario": itinerario,
        "estado": "ok", "duracion_ms": duracion_ms, "error_resumido": None,
        "modo_demo": False, "modo_modelo": llm.LLM_MODE,
    })

    # 6) Mismo diccionario para HTML y JSON
    return {
        "solicitud_id": solicitud_id, "ciudad": g["ciudad"],
        "tipo_turismo": tipo_turismo, "duracion_horas": duracion_horas,
        "meteorologia": meteo, "lugares": lugares,
        "itinerario": itinerario, "modo_demo": False,
    }
