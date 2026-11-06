"""Adaptador Cohere. El PROMPT lo redacta el alumnado."""
import os
import requests

LLM_MODE = os.getenv("LLM_MODE", "mock").lower()
COHERE_MODEL = os.getenv("COHERE_MODEL", "command-r7b-12-2024")


def generar_itinerario(contexto: dict) -> tuple[str, str]:
    """Devuelve (texto_itinerario, prompt_usado)."""
    if LLM_MODE == "mock":
        return _simulador(contexto), "[SIMULADOR: sin llamada a modelo]"

    if LLM_MODE != "cohere":
        raise ValueError("LLM_MODE debe ser 'mock' o 'cohere'")

    api_key = os.getenv("COHERE_API_KEY", "")
    if not api_key:
        raise RuntimeError("Falta COHERE_API_KEY (pedirla al docente)")

    meteo = contexto["meteorologia"]
    lugares = "\n".join(
        f"- {l['nombre']} ({l['categoria']}, lat {l['lat']}, lon {l['lon']})"
        for l in contexto["lugares"]
    )

    prompt = f"""Eres un guía turístico local de {contexto['ciudad']}.

Datos del usuario:
- Tipo de turismo: {contexto['tipo_turismo']}
- Duración disponible: {contexto['duracion_horas']} horas
- Preferencias: {contexto.get('preferencias') or 'ninguna'}

Tiempo actual: {meteo.get('temperatura_c')} °C, precipitación {meteo.get('precipitacion_mm')} mm.

Lugares verificados (OpenStreetMap):
{lugares}

Tarea: propón una ruta de 3 a 5 paradas en orden, con un tiempo aproximado en cada una, que encaje en {contexto['duracion_horas']} horas.

Reglas:
1. Usa SOLO lugares de la lista anterior. No inventes ningún lugar.
2. No digas horarios de apertura, precios ni eventos: no están verificados.
3. Si llueve (precipitación > 0), prioriza sitios cubiertos y explica por qué.
4. Si hay menos de 3 lugares, dilo claramente en vez de completar la ruta.
5. Responde en castellano, de forma breve."""

    r = requests.post(
        "https://api.cohere.com/v2/chat",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"model": COHERE_MODEL, "messages": [{"role": "user", "content": prompt}]},
        timeout=30,
    )
    r.raise_for_status()

    contenido = r.json().get("message", {}).get("content") or []
    if not contenido or not contenido[0].get("text"):
        raise RuntimeError("Cohere ha devuelto una respuesta vacía")

    texto_itinerario = contenido[0]["text"]
    return texto_itinerario, prompt


def _simulador(contexto: dict) -> str:
    """Salida no generativa para pruebas y para cuando no hay credenciales."""
    lugares = contexto.get("lugares") or []
    ciudad = contexto.get("ciudad", "la ciudad")
    tipo = contexto.get("tipo_turismo", "libre")
    nombres = [x.get("nombre", "Lugar sin nombre") for x in lugares[:4]]
    visitas = "\n".join(f"{i}. {nombre}" for i, nombre in enumerate(nombres, 1))
    if not visitas:
        visitas = "No hay lugares verificados disponibles."
    return f"[MODO SIMULACIÓN - NO ES IA]\nPlan {tipo} en {ciudad}:\n{visitas}"
