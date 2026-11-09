"""Limpiar una encuesta de panel barato y leer un test A/B sin engañarse.

Un panel online barato trae mucha basura. Antes de contar nada, cada respuesta pasa por cinco
filtros, y la que cae se queda con el primer motivo para que se pueda auditar:

1. **Duplicado:** misma huella de dispositivo que una respuesta anterior.
2. **Demasiado rápida:** menos de un tercio de la duración mediana. Nadie lee las preguntas así.
3. **Falla el control:** una pregunta que dice qué contestar ("marque algo de acuerdo").
4. **En línea recta:** la misma nota en todos los ítems de la matriz.
5. **Otro idioma:** el texto libre no está en español. En un panel de España, suele ser un bot o
   alguien fuera del público.

Después, el test A/B: la proporción que elige cada frente, con su intervalo de confianza. Con
un centenar de respuestas válidas, un 72 % no es un 72 % exacto, y por segmentos de edad el
intervalo se abre aún más; el informe lo tiene que decir.
"""
from __future__ import annotations

import math
import re

import pandas as pd

PALABRAS_ES = {"el", "la", "los", "las", "de", "que", "y", "me", "se", "más", "para", "lo",
               "es", "por", "mejor", "con", "una", "un", "hace", "porque", "da"}
PALABRAS_OTRAS = {"the", "good", "nice", "very", "like", "best", "product", "price", "it", "i",
                  "ok", "design"}
CONTROL_CORRECTO = "algo de acuerdo"
MATRIZ = ["m1", "m2", "m3", "m4", "m5"]


def en_espanol(texto: str) -> bool:
    palabras = set(re.findall(r"[a-záéíóúñü]+", str(texto).lower()))
    return len(palabras & PALABRAS_ES) > len(palabras & PALABRAS_OTRAS)


def limpiar(respuestas: pd.DataFrame) -> pd.DataFrame:
    """Devuelve las respuestas con una columna `motivo_descarte` (None si la respuesta vale)."""
    r = respuestas.copy()
    mediana = r["duracion_seg"].median()
    reglas = [
        ("duplicado", r.duplicated("huella", keep="first")),
        ("demasiado rápida", r["duracion_seg"] < mediana / 3),
        ("falla el control", r["control"] != CONTROL_CORRECTO),
        ("en línea recta", r[MATRIZ].nunique(axis=1) == 1),
        ("otro idioma", ~r["por_que"].map(en_espanol)),
    ]
    motivo = pd.Series([None] * len(r), index=r.index, dtype=object)
    for nombre, mascara in reglas:
        motivo = motivo.where(motivo.notna() | ~mascara, nombre)
    r["motivo_descarte"] = motivo
    return r


def wilson(exitos: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    """Proporción e intervalo de confianza de Wilson (95 % por defecto)."""
    if n == 0:
        return 0.0, 0.0, 1.0
    p = exitos / n
    den = 1 + z * z / n
    centro = (p + z * z / (2 * n)) / den
    margen = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return p, max(0.0, centro - margen), min(1.0, centro + margen)


def test_ab(validas: pd.DataFrame, por: str | None = None, opcion: str = "A") -> pd.DataFrame:
    """Proporción que elige `opcion`, con intervalo, en total o por grupos."""
    grupos = [("Total", validas)] if por is None else list(validas.groupby(por))
    filas = []
    for nombre, g in grupos:
        k, n = int((g["frente"] == opcion).sum()), len(g)
        p, lo, hi = wilson(k, n)
        filas.append({"grupo": nombre, "n": n, "eligen": k, "proporcion": p, "ic_bajo": lo,
                      "ic_alto": hi})
    return pd.DataFrame(filas)
