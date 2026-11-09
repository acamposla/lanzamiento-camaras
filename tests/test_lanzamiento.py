import pandas as pd
import pytest

from lanzamiento import datos as d
from lanzamiento import demanda as dm
from lanzamiento import encuesta as e

PASILLOS = dm.pasillos_por_tipo(d.TIPOS)


@pytest.fixture(scope="module")
def estimacion():
    return dm.estimar(d.MODELOS, d.panel_tiendas(), d.mercado_online(), PASILLOS)


# ---------- Datos ----------

def test_datos_reproducibles():
    pd.testing.assert_frame_equal(d.panel_tiendas(), d.panel_tiendas())
    pd.testing.assert_frame_equal(d.mercado_online(), d.mercado_online())
    pd.testing.assert_frame_equal(d.encuesta(), d.encuesta())


# ---------- Demanda ----------

@pytest.mark.parametrize("precio, rango", [(24.99, "<25"), (25.0, "<25"), (25.01, "25-35"),
                                          (50.0, "35-50"), (120.0, "100+")])
def test_rangos_de_precio(precio, rango):
    assert dm.rango_precio(pd.Series([precio])).iloc[0] == rango


def test_afinar_nunca_agranda_el_segmento(estimacion):
    assert (estimacion["offline_panel_mes"] <= estimacion["offline_amplio_mes"]).all()


def test_segmento_offline_filtra_tipo_rango_resolucion_y_alimentacion():
    panel = pd.DataFrame([
        ("a", "exterior fija", 40.0, 1440, "red", 120),       # entra
        ("b", "exterior fija", 40.0, 1440, "batería", 120),   # otra alimentación
        ("c", "exterior fija", 40.0, 2160, "red", 120),       # otra resolución
        ("d", "exterior fija", 60.0, 1440, "red", 120),       # otro rango
        ("e", "interior fija", 40.0, 1440, "red", 120),       # otro tipo
    ], columns=["modelo_mercado", "tipo", "precio", "resolucion", "alimentacion",
                "unidades_año"])
    mod = pd.Series({"tipo": "exterior fija", "rango": "35-50", "res_min": 1080,
                     "res_max": 1600, "alimentacion": "red"})
    assert dm.segmento_offline(panel, mod) == 10.0
    assert dm.segmento_offline(panel, mod, afinar=False) == 30.0  # a, b y c: mismo tipo y rango


def test_mercado_es_offline_corregido_mas_online(estimacion):
    esperado = estimacion["offline_panel_mes"] * dm.COBERTURA_PANEL + estimacion["online_mes"]
    assert estimacion["mercado_mes"].tolist() == pytest.approx(esperado.tolist())


def test_modelos_del_mismo_segmento_se_reparten_la_cuota(estimacion):
    e2 = estimacion.set_index("modelo")
    assert e2.loc["DUNA", "modelos_en_segmento"] == 2
    esperado = e2.loc["DUNA", "mercado_mes"] * dm.ESCENARIOS["base"] / 2
    assert e2.loc["DUNA", "ventas_mes_base"] == pytest.approx(round(esperado))


def test_pedido_es_ventas_por_meses_de_stock(estimacion):
    for esc in dm.ESCENARIOS:
        diff = (estimacion[f"pedido_{esc}"] - estimacion[f"ventas_mes_{esc}"] * dm.MESES_STOCK)
        assert diff.abs().max() <= dm.MESES_STOCK  # solo redondeo


def test_escenarios_ordenados(estimacion):
    assert (estimacion["pedido_conservador"] <= estimacion["pedido_base"]).all()
    assert (estimacion["pedido_base"] <= estimacion["pedido_optimista"]).all()


def test_el_contraste_marca_los_nichos(estimacion):
    revisar = set(estimacion.loc[estimacion["revisar"], "modelo"])
    assert revisar == {"BRUMA", "ESTELA"}


# ---------- Encuesta ----------

@pytest.mark.parametrize("texto, es", [
    ("la caja de la izquierda explica mejor para qué sirve", True),
    ("good product nice", False), ("i like it", False), ("", False),
])
def test_idioma(texto, es):
    assert e.en_espanol(texto) == es


def test_cada_filtro_por_separado():
    base = {"huella": "x", "duracion_seg": 240.0, "edad": "45 a 64", "m1": 1, "m2": 2,
            "m3": 3, "m4": 4, "m5": 5, "control": "algo de acuerdo", "frente": "A",
            "por_que": "me gusta más porque se entiende"}
    filas = [
        {**base, "huella": "h1"},                                     # válida
        {**base, "huella": "h1"},                                     # duplicado
        {**base, "huella": "h2", "duracion_seg": 30.0},               # rápida
        {**base, "huella": "h3", "control": "muy de acuerdo"},        # control
        {**base, "huella": "h4", "m1": 3, "m2": 3, "m4": 3, "m5": 3},  # línea recta
        {**base, "huella": "h5", "por_que": "good product nice"},     # idioma
        {**base, "huella": "h6"}, {**base, "huella": "h7"},           # válidas
    ]
    motivos = e.limpiar(pd.DataFrame(filas))["motivo_descarte"].tolist()
    assert motivos == [None, "duplicado", "demasiado rápida", "falla el control",
                       "en línea recta", "otro idioma", None, None]


def test_la_limpieza_atrapa_la_basura_sintetica():
    r = e.limpiar(d.encuesta())
    validas = r["motivo_descarte"].isna()
    assert (r.loc[validas, "ruido"] == "ninguno").all()
    assert (r.loc[~validas, "ruido"] != "ninguno").all()


def test_wilson():
    p, lo, hi = e.wilson(80, 100)
    assert p == 0.8 and lo == pytest.approx(0.711, abs=1e-3) and hi == pytest.approx(0.867,
                                                                                     abs=1e-3)
    assert e.wilson(0, 0) == (0.0, 0.0, 1.0)


def test_el_frente_a_gana_pero_no_en_todos_los_segmentos_con_seguridad():
    r = e.limpiar(d.encuesta())
    v = r[r["motivo_descarte"].isna()]
    total = e.test_ab(v).iloc[0]
    assert total["ic_bajo"] > 0.5
    jovenes = e.test_ab(v, "edad").set_index("grupo").loc["menos de 45"]
    assert jovenes["ic_bajo"] < 0.5 < jovenes["proporcion"]
