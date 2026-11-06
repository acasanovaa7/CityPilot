"""Clientes HTTP de datos públicos. Se entregan los contratos, NO la solución."""
import json
import os
from pathlib import Path
import requests

GEO_URL = os.getenv("OPEN_METEO_GEO_URL", "https://geocoding-api.open-meteo.com/v1/search")
METEO_URL = os.getenv("OPEN_METEO_WEATHER_URL", "https://api.open-meteo.com/v1/forecast")
OVERPASS_URL = os.getenv("OVERPASS_URL", "https://overpass-api.de/api/interpreter")


def geocodificar(ciudad: str) -> dict:
    parametros = {"name": ciudad, "count": 1, "language": "es", "countryCode": "ES"}
    r = requests.get(GEO_URL, params=parametros, timeout=8)
    r.raise_for_status()
    contenido = r.json()
 
    resultados = contenido.get("results")
    if not resultados:
        raise ValueError(f"No se ha encontrado la ciudad '{ciudad}'")
 
    primero = resultados[0]
    return {
        "ciudad": primero["name"],
        "pais": primero.get("country", ""),
        "lat": primero["latitude"],
        "lon": primero["longitude"],
    }


def obtener_meteorologia(lat: float, lon: float) -> dict:
    parametros = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,precipitation,weather_code",
        "timezone": "auto",
    }
    r = requests.get(METEO_URL, params=parametros, timeout=8)
    r.raise_for_status()
    actual = r.json()["current"]
 
    return {
        "temperatura_c": actual.get("temperature_2m"),
        "precipitacion_mm": actual.get("precipitation"),
        "codigo_tiempo": actual.get("weather_code"),
        "instante": actual.get("time"),
    }


def obtener_lugares(lat: float, lon: float, tipo: str) -> list[dict]:
    # Filtros fijos por tipo: el usuario nunca escribe nada dentro de la consulta
    if tipo == "cultural":
        filtros = ['["tourism"~"museum|gallery|attraction"]', '["historic"~"monument|castle|memorial"]']
    elif tipo == "gastronomica":
        filtros = ['["amenity"~"restaurant|cafe|food_court"]']
    elif tipo == "naturaleza":
        filtros = ['["leisure"~"park|garden"]']
    elif tipo == "familiar":
        filtros = ['["tourism"~"attraction|zoo"]', '["leisure"~"park|playground"]']
    else:
        raise ValueError(f"Tipo de turismo no válido: {tipo}")
 
    lineas = ""
    for filtro in filtros:
        lineas += f'nwr{filtro}["name"](around:2500,{float(lat)},{float(lon)});\n'
    consulta = f"[out:json][timeout:20];\n(\n{lineas});\nout center 40;"
 
    r = requests.post(OVERPASS_URL, data={"data": consulta}, timeout=25)
    r.raise_for_status()
    elementos = r.json().get("elements", [])
 
    lugares = []
    nombres_vistos = set()
    for elemento in elementos:
        tags = elemento.get("tags", {})
        nombre = tags.get("name")
        if not nombre or nombre in nombres_vistos:
            continue
 
        if elemento["type"] == "node":
            lat_lugar, lon_lugar = elemento.get("lat"), elemento.get("lon")
        else:  # way o relation: usamos el centro que da "out center"
            centro = elemento.get("center", {})
            lat_lugar, lon_lugar = centro.get("lat"), centro.get("lon")
        if lat_lugar is None or lon_lugar is None:
            continue
 
        categoria = tags.get("tourism") or tags.get("historic") or tags.get("amenity") or tags.get("leisure")
        lugares.append({
            "nombre": nombre,
            "categoria": categoria,
            "lat": lat_lugar,
            "lon": lon_lugar,
            "fuente": "OpenStreetMap",
            "demo": False,
        })
        nombres_vistos.add(nombre)
        if len(lugares) == 12:
            break
 
    return lugares


def cargar_fixture_lugares() -> list[dict]:
    """Utilidad entregada para simular Overpass durante pruebas sin Internet.

    Los lugares son FICTICIOS y deben identificarse como DEMO en la UI.
    """
    file_path = Path("/fixtures/puntos_demo.json")
    if not file_path.exists():
        file_path = Path(__file__).resolve().parents[2] / "fixtures/puntos_demo.json"
    return json.loads(file_path.read_text(encoding="utf-8"))["lugares"]
