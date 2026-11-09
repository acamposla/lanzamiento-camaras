"""Datos sintéticos para dimensionar el lanzamiento de una gama de cámaras WiFi, con semilla fija.

Tres fuentes, con la forma de las que se usan de verdad y cifras inventadas:

- **Panel de tiendas físicas.** Ventas anuales por modelo del mercado, con tipo de cámara, precio,
  resolución y alimentación. Como los paneles reales, no cubre todas las tiendas: deja fuera
  cadenas de bricolaje y ferreterías, y por eso la estimación lleva un factor de cobertura.
- **Mercado online.** Ventas mensuales estimadas de los más vendidos de cada pasillo (cámaras
  domo, que giran, y cámaras bala, fijas), con precio. Sin características técnicas.
- **Encuesta a consumidores.** Respuestas de un panel online barato, con la basura que traen esos
  paneles: bots que contestan en segundos, respuestas en línea recta, texto en otro idioma,
  duplicados y quien falla la pregunta de control. Incluye un test A/B de dos frentes de caja.

Las marcas, los modelos y todas las cifras son inventados.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

SEMILLA = 360
MARCAS = ("Atalaya", "Centinela", "Faro", "Kiro", "Lumo", "Nido", "Ojo Claro", "Vigía")
# tipo: (motorizada, pasillo online, precio medio, peso en el mercado)
TIPOS = {
    "interior 360": (True, "domo", 32, 0.34),
    "interior fija": (False, "bala", 27, 0.22),
    "exterior fija": (False, "bala", 44, 0.20),
    "exterior 360": (True, "domo", 55, 0.14),
    "solar 4G": (False, "bala", 85, 0.10),
}

# Los modelos propios que se quieren lanzar, con el segmento al que pertenecen y el competidor
# de referencia en el mercado online. DUNA y ESTELA caen en el mismo segmento: se reparten cuota.
MODELOS = pd.DataFrame([
    ("ALBA", "interior fija", "<25", 1080, 1080, None, "Kiro F0", 1_500),
    ("BRUMA", "exterior 360", "50-75", 1440, 2160, None, "Atalaya P4", 40),
    ("CIMA", "interior 360", "35-50", 1440, 1600, None, "Lumo Q5", 420),
    ("DUNA", "solar 4G", "75-100", 1080, 2160, "solar", "Faro S1", 180),
    ("ESTELA", "solar 4G", "75-100", 1080, 1600, "solar", "Vigía Sol", 10),
], columns=["modelo", "tipo", "rango", "res_min", "res_max", "alimentacion", "competidor",
            "ventas_competidor_mes"])


def panel_tiendas(semilla: int = SEMILLA, n: int = 900) -> pd.DataFrame:
    rng = np.random.default_rng(semilla)
    tipos = list(TIPOS)
    pesos = np.array([TIPOS[t][3] for t in tipos])
    filas = []
    for i in range(n):
        tipo = rng.choice(tipos, p=pesos / pesos.sum())
        motorizada, _, precio_medio, _ = TIPOS[tipo]
        precio = float(np.round(rng.lognormal(np.log(precio_medio), 0.35), 2))
        res = int(rng.choice([1080, 1440, 1600, 2160], p=[0.45, 0.30, 0.15, 0.10]))
        if tipo == "solar 4G":
            alim = "solar"
        elif tipo.startswith("exterior"):
            alim = str(rng.choice(["red", "batería"], p=[0.6, 0.4]))
        else:
            alim = "red"
        unidades = int(rng.lognormal(4.0, 1.3))
        filas.append((f"P{i:04d}", str(rng.choice(MARCAS)), tipo, motorizada, precio, res, alim,
                      unidades))
    return pd.DataFrame(filas, columns=["modelo_mercado", "marca", "tipo", "motorizada",
                                        "precio", "resolucion", "alimentacion", "unidades_año"])


def mercado_online(semilla: int = SEMILLA, por_pasillo: int = 100) -> pd.DataFrame:
    rng = np.random.default_rng(semilla + 1)
    filas = []
    for pasillo, precio_medio in (("domo", 34), ("bala", 42)):
        for i in range(por_pasillo):
            precio = float(np.round(rng.lognormal(np.log(precio_medio), 0.35), 2))
            ventas = int(rng.pareto(1.3) * 40) + 5  # unos pocos venden muchísimo
            filas.append((f"{pasillo[0].upper()}{i:03d}", pasillo, precio, ventas))
    return pd.DataFrame(filas, columns=["anuncio", "pasillo", "precio", "ventas_mes"])


FRASES_ES = [
    "me gusta más porque se ve claro lo que hace",
    "la caja de la izquierda explica mejor para qué sirve",
    "parece más fácil de instalar y eso me importa",
    "se entiende que no hace falta app complicada",
    "me da más confianza para la casa del pueblo",
    "la foto de la persona mayor me hace pensar en mis padres",
    "los colores son más tranquilos y se lee mejor",
]
FRASES_OTRAS = ["good product nice", "very good", "i like it", "nice design good price",
                "best one", "ok"]


def encuesta(semilla: int = SEMILLA, n: int = 270) -> pd.DataFrame:
    """Una fila por respuesta. `ruido` dice qué tipo de basura es (o 'ninguno'): sirve para los
    tests, nunca para limpiar."""
    rng = np.random.default_rng(semilla + 2)
    filas = []
    huellas = [f"h{i:05d}" for i in range(n)]
    for i in range(n):
        ruido = rng.choice(["ninguno", "bot", "linea_recta", "idioma", "control", "duplicado"],
                           p=[0.45, 0.20, 0.10, 0.15, 0.06, 0.04])
        edad = str(rng.choice(["menos de 45", "45 a 64", "65 o más"], p=[0.35, 0.40, 0.25]))
        duracion = float(rng.lognormal(np.log(240), 0.35))
        matriz = list(rng.integers(1, 6, size=5))
        control = "algo de acuerdo"
        # El frente A gana, más entre los mayores; los bots eligen al azar
        p_a = {"menos de 45": 0.60, "45 a 64": 0.72, "65 o más": 0.80}[edad]
        frente = "A" if rng.random() < p_a else "B"
        texto = str(rng.choice(FRASES_ES))
        huella = huellas[i]
        if ruido == "bot":
            duracion = float(rng.uniform(15, 50))
            frente = str(rng.choice(["A", "B"]))
            texto = str(rng.choice(FRASES_OTRAS))
        elif ruido == "linea_recta":
            matriz = [int(rng.integers(1, 6))] * 5
            frente = str(rng.choice(["A", "B"]))
        elif ruido == "idioma":
            texto = str(rng.choice(FRASES_OTRAS))
            frente = str(rng.choice(["A", "B"]))
        elif ruido == "control":
            control = str(rng.choice(["muy de acuerdo", "nada de acuerdo"]))
        elif ruido == "duplicado" and i > 0:
            huella = huellas[int(rng.integers(0, i))]
        filas.append((f"R{i:04d}", huella, round(duracion, 1), edad, *matriz, control, frente,
                      texto, ruido))
    return pd.DataFrame(filas, columns=["respuesta", "huella", "duracion_seg", "edad",
                                        "m1", "m2", "m3", "m4", "m5", "control", "frente",
                                        "por_que", "ruido"])
