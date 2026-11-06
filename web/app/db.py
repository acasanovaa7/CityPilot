"""Acceso a PostgreSQL. Conexión mínima dada; funciones de negocio pendientes."""
import os
from sqlalchemy import create_engine, text
import json

DATABASE_URL = os.environ.get("DATABASE_URL", "")
engine = create_engine(DATABASE_URL, pool_pre_ping=True) if DATABASE_URL else None


def ping_db():
    if engine is None:
        raise RuntimeError("Falta DATABASE_URL")
    with engine.connect() as conn:
        return conn.execute(text("SELECT 1")).scalar_one()


def guardar_solicitud(registro: dict) -> int:
    datos = dict(registro)
    datos["meteorologia"] = json.dumps(datos["meteorologia"], ensure_ascii=False)
    datos["lugares"] = json.dumps(datos["lugares"], ensure_ascii=False)
    sql = text("""
        INSERT INTO solicitudes (ciudad, pais, tipo_turismo, duracion_horas, preferencias,
            latitud, longitud, meteorologia, lugares, prompt_usado, itinerario,
            estado, duracion_ms, error_resumido, modo_demo, modo_modelo)
        VALUES (:ciudad, :pais, :tipo_turismo, :duracion_horas, :preferencias,
            :latitud, :longitud, CAST(:meteorologia AS jsonb), CAST(:lugares AS jsonb),
            :prompt_usado, :itinerario, :estado, :duracion_ms, :error_resumido,
            :modo_demo, :modo_modelo)
        RETURNING id
    """)
    with engine.begin() as conn:
        return conn.execute(sql, datos).scalar_one()


def obtener_estadisticas() -> dict:
    """TODO(ALUMNADO): total, agrupación por ciudad/tipo y nº errores."""
    raise NotImplementedError("Implementa SELECTs de analítica")


def obtener_ultimas_solicitudes(limite: int = 8) -> list[dict]:
    """TODO(ALUMNADO): últimas solicitudes sin mostrar claves ni secretos."""
    raise NotImplementedError("Implementa SELECT con ORDER BY fecha DESC LIMIT")
