"""El estudio entero sobre los datos sintéticos: estimación de pedido, limpieza de la encuesta y
test A/B. Imprime las tablas y guarda los gráficos.

Uso: python scripts/estudio.py [carpeta_figuras] [es|en]
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from lanzamiento import datos as d
from lanzamiento import demanda as dm
from lanzamiento import encuesta as e
from lanzamiento import graficos as g


def main(salida: Path, idioma: str = "es") -> None:
    pd.set_option("display.width", 160)
    est = dm.estimar(d.MODELOS, d.panel_tiendas(), d.mercado_online(),
                     dm.pasillos_por_tipo(d.TIPOS))
    cols = ["modelo", "mercado_mes", "modelos_en_segmento", "ventas_mes_conservador",
            "ventas_mes_base", "ventas_mes_optimista", "pedido_base", "ventas_competidor_mes",
            "base_frente_competidor", "revisar"]
    print("Estimación por modelo (unidades al mes; pedido a", dm.MESES_STOCK, "meses de stock)")
    print(est[cols].round(1).to_string(index=False), "\n")

    limpias = e.limpiar(d.encuesta())
    print("Encuesta: motivos de descarte")
    print(limpias["motivo_descarte"].fillna("válida").value_counts().to_string(), "\n")
    validas = limpias[limpias["motivo_descarte"].isna()]
    ab = pd.concat([e.test_ab(validas), e.test_ab(validas, "edad")], ignore_index=True)
    orden = ["Total", "menos de 45", "45 a 64", "65 o más"]
    ab = ab.set_index("grupo").loc[orden].reset_index()
    print("Test A/B: eligen el frente A")
    print(ab.round(3).to_string(index=False))

    salida.mkdir(parents=True, exist_ok=True)
    g.pedido(est, idioma).savefig(salida / "pedido.png", dpi=110)
    g.embudo(limpias, idioma).savefig(salida / "embudo.png", dpi=110)
    g.test_ab(ab, idioma).savefig(salida / "test_ab.png", dpi=110)
    portada = g.test_ab(ab, idioma)
    portada.set_size_inches(12, 6.3)
    portada.savefig(salida / "portada.png", dpi=100)
    print(f"\nGráficos en {salida} ({idioma})")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("figuras"),
         sys.argv[2] if len(sys.argv) > 2 else "es")
