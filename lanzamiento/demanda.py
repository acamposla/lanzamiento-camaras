"""Cuántas unidades pedir de cada modelo: demanda del segmento, cuota y stock de seguridad.

El método es de arriba abajo, por segmento y no por modelo:

1. **Segmento offline.** Del panel de tiendas, las ventas del mismo tipo de cámara y el mismo
   rango de precio; donde el panel tiene la característica, se afina por resolución y por
   alimentación. Se pasa a ventas al mes.
2. **Cobertura del panel.** El panel no ve todas las tiendas (en el caso real faltaban las grandes
   cadenas de bricolaje y las ferreterías), así que el offline se multiplica por un factor de
   cobertura. Es el supuesto más débil de la estimación y por eso va a la vista, como parámetro.
3. **Segmento online.** De los más vendidos del marketplace, el mismo pasillo y el mismo rango de
   precio. Aquí no hay características técnicas: no se puede afinar más.
4. **Cuota.** Tres escenarios sobre el mercado total del segmento (conservador, base y
   optimista). Si dos modelos propios caen en el mismo segmento, se reparten la cuota en vez de
   contarla dos veces.
5. **Pedido.** Ventas al mes del escenario por los meses de stock de seguridad que fija compras.
6. **Contraste.** Las ventas del escenario base frente a las del competidor de referencia en el
   marketplace: si el escenario pide vender mucho más que el líder de su segmento, algo está mal.
"""
from __future__ import annotations

import pandas as pd

CORTES = [0, 25, 35, 50, 75, 100, 5_000]
RANGOS = ["<25", "25-35", "35-50", "50-75", "75-100", "100+"]
ESCENARIOS = {"conservador": 0.01, "base": 0.02, "optimista": 0.05}
COBERTURA_PANEL = 2.0   # el offline real se estima en el doble de lo que ve el panel
MESES_STOCK = 8
# Si el escenario base pide vender más de la mitad que el competidor de referencia, hay que
# mirarlo: o el segmento es más grande que su líder (un nicho nuevo) o la cuota es optimista.
UMBRAL_CONTRASTE = 0.5


def rango_precio(precio: pd.Series) -> pd.Series:
    return pd.cut(precio, bins=CORTES, labels=RANGOS, right=True).astype(str)


def segmento_offline(panel: pd.DataFrame, modelo: pd.Series, *, afinar: bool = True) -> float:
    """Unidades al mes del segmento del modelo en el panel de tiendas."""
    p = panel.assign(rango=rango_precio(panel["precio"]))
    m = (p["tipo"] == modelo["tipo"]) & (p["rango"] == modelo["rango"])
    if afinar:
        m &= p["resolucion"].between(modelo["res_min"], modelo["res_max"])
        if isinstance(modelo["alimentacion"], str):
            m &= p["alimentacion"] == modelo["alimentacion"]
    return float(p.loc[m, "unidades_año"].sum() / 12)


def segmento_online(online: pd.DataFrame, modelo: pd.Series, pasillos: dict[str, str]) -> float:
    """Unidades al mes del mismo pasillo y rango de precio en el marketplace."""
    o = online.assign(rango=rango_precio(online["precio"]))
    m = (o["pasillo"] == pasillos[modelo["tipo"]]) & (o["rango"] == modelo["rango"])
    return float(o.loc[m, "ventas_mes"].sum())


def estimar(modelos: pd.DataFrame, panel: pd.DataFrame, online: pd.DataFrame,
            pasillos: dict[str, str], *, cobertura: float = COBERTURA_PANEL,
            meses_stock: int = MESES_STOCK,
            escenarios: dict[str, float] = ESCENARIOS) -> pd.DataFrame:
    """Una fila por modelo con el mercado de su segmento, las ventas y el pedido por escenario."""
    filas = []
    for _, mod in modelos.iterrows():
        off_amplio = segmento_offline(panel, mod, afinar=False)
        off = segmento_offline(panel, mod)
        on = segmento_online(online, mod, pasillos)
        filas.append({"modelo": mod["modelo"], "tipo": mod["tipo"], "rango": mod["rango"],
                      "offline_amplio_mes": off_amplio, "offline_panel_mes": off,
                      "offline_corregido_mes": off * cobertura, "online_mes": on,
                      "mercado_mes": off * cobertura + on,
                      "competidor": mod["competidor"],
                      "ventas_competidor_mes": mod["ventas_competidor_mes"]})
    out = pd.DataFrame(filas)

    # Modelos que comparten segmento se reparten la cuota, a partes iguales
    comparten = out.groupby(["tipo", "rango"])["modelo"].transform("count")
    out["modelos_en_segmento"] = comparten
    for nombre, cuota in escenarios.items():
        ventas = out["mercado_mes"] * cuota / comparten
        out[f"ventas_mes_{nombre}"] = ventas.round()
        out[f"pedido_{nombre}"] = (ventas * meses_stock).round()
    out["base_frente_competidor"] = (out["ventas_mes_base"]
                                     / out["ventas_competidor_mes"]).round(2)
    out["revisar"] = out["base_frente_competidor"] > UMBRAL_CONTRASTE
    return out


def pasillos_por_tipo(tipos: dict) -> dict[str, str]:
    """De la tabla de tipos de `datos`, a qué pasillo online corresponde cada tipo."""
    return {t: v[1] for t, v in tipos.items()}
