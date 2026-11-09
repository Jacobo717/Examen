import os
from typing import Any

import psycopg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="DataMart API", version="1.0.0")
DATABASE_URL = os.environ["DATABASE_URL"]

class ResultadoIn(BaseModel):
    clave: str = Field(min_length=1)
    ticket_promedio: float = Field(ge=0)
    registros: int = Field(ge=0)

def ensure_table() -> None:
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS resultados (clave TEXT PRIMARY KEY, ticket_promedio NUMERIC(14,2) NOT NULL, registros INTEGER NOT NULL)")
        conn.commit()

@app.on_event("startup")
def startup() -> None:
    ensure_table()

def serialize(row: tuple[Any, ...]) -> dict[str, Any]:
    return {"clave": row[0], "ticket_promedio": float(row[1]), "registros": row[2]}

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/resultados")
def resultados() -> list[dict[str, Any]]:
    with psycopg.connect(DATABASE_URL) as conn:
        rows = conn.execute("SELECT clave,ticket_promedio,registros FROM resultados ORDER BY clave").fetchall()
    return [serialize(row) for row in rows]

@app.get("/resultados/{clave}")
def resultado(clave: str) -> dict[str, Any]:
    with psycopg.connect(DATABASE_URL) as conn:
        row = conn.execute("SELECT clave,ticket_promedio,registros FROM resultados WHERE clave=%s", (clave,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Clave no encontrada")
    return serialize(row)

@app.post("/resultados", status_code=201)
def crear_resultado(payload: ResultadoIn) -> dict[str, Any]:
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute("INSERT INTO resultados (clave,ticket_promedio,registros) VALUES (%s,%s,%s) ON CONFLICT (clave) DO UPDATE SET ticket_promedio=EXCLUDED.ticket_promedio, registros=EXCLUDED.registros", (payload.clave, payload.ticket_promedio, payload.registros))
        conn.commit()
    return payload.model_dump()

@app.delete("/resultados/{clave}", status_code=204)
def eliminar_resultado(clave: str) -> None:
    with psycopg.connect(DATABASE_URL) as conn:
        result = conn.execute("DELETE FROM resultados WHERE clave=%s", (clave,))
        conn.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Clave no encontrada")

