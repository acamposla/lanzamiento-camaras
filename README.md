# Lanzamiento de cámaras: cuánto pedir y qué dice el consumidor

Una marca quiere lanzar cinco cámaras WiFi nuevas y tiene que decidir cuántas unidades pedir de
cada una antes de haber vendido ninguna. Este repo reproduce, sobre datos sintéticos, las dos
partes del estudio que respondía a eso:

1. **Demanda por segmento:** cuánto vende al mes el segmento de cada modelo (tienda física y
   online), qué cuota es razonable y qué pedido sale con el stock de seguridad que fija compras.
2. **Encuesta a consumidores:** cómo limpiar un panel online barato antes de contar nada, y cómo
   leer un test A/B de packaging sin creerse más de lo que dicen cien respuestas.

El caso contado:
[Cuántas unidades pedir de un producto que aún no se vende](https://alejandrocamposlamas.com/portfolio/cuantas-unidades-pedir/).
Sale del estudio de lanzamiento de cámaras IP que hice para Garza, la marca que dirigía en
Imprex, en 2026.

> **English summary.** Sizing a product launch before any sales exist, rebuilt on synthetic data.
> Demand is estimated top-down per segment: offline from a retail panel (same camera type and
> price band, refined by resolution and power where the panel has them, then scaled up for the
> stores the panel doesn't cover) plus online from marketplace best sellers in the same aisle and
> price band. Three share scenarios give monthly sales; models in the same segment split the
> share; the order is monthly sales times the safety-stock months. Each base scenario is checked
> against the reference competitor's sales. The survey half cleans a cheap online panel with five
> rules (duplicates, speeders, failed attention check, straight-liners, non-Spanish answers),
> each discard keeping its reason, and reads an A/B packaging test with Wilson confidence
> intervals by age group. All data is synthetic. Code and docs are in Spanish; charts export in
> English too.

## Los datos son sintéticos

Ninguna cifra, marca ni modelo de este repo es real. El estudio original usaba un panel de
ventas de tiendas físicas y datos de un marketplace, que son datos con licencia y no se publican.
`lanzamiento/datos.py` genera con semilla fija tres fuentes con la misma forma: un panel de tiendas
con tipo, precio, resolución y alimentación; los más vendidos de dos pasillos de un marketplace; y
270 respuestas de encuesta con la basura típica de un panel barato.

## La demanda

| Paso | Qué hace | Por qué |
|---|---|---|
| Segmento offline | Mismo tipo de cámara y rango de precio en el panel; se afina por resolución y alimentación | El panel tiene características técnicas; aprovecharlas acota el segmento al producto |
| Cobertura del panel | El offline se multiplica por un factor (2 por defecto) | El panel no ve todas las tiendas. Es el supuesto más débil, y por eso es un parámetro a la vista |
| Segmento online | Mismo pasillo y rango de precio en el marketplace | Aquí no hay características: no se puede afinar más |
| Cuota | Conservador 1 %, base 2 %, optimista 5 % del mercado del segmento | Una sola cifra esconde la incertidumbre |
| Segmento compartido | Dos modelos propios en el mismo segmento se reparten la cuota | Si no, la marca se cuenta dos veces el mismo mercado |
| Pedido | Ventas al mes del escenario por los meses de stock de seguridad | Lo que compras necesita para lanzar el pedido al proveedor |
| Contraste | Ventas del escenario base frente al competidor de referencia | Si el base pide vender más de la mitad que el líder del segmento, se revisa |

Con los datos sintéticos, el contraste marca dos modelos. En los dos, el competidor de referencia
vende muy poco para el tamaño de su segmento: o es un nicho que nadie ha ocupado todavía, o el
competidor elegido no es el que manda en ese segmento. En ninguno de los dos casos la cuota de
mercado es buena guía, y el pedido se decide con criterio y no con la fórmula.

## La encuesta

Cada respuesta pasa por cinco filtros y la que cae se queda con el primer motivo, para poder
auditar la limpieza: duplicada (misma huella), demasiado rápida (menos de un tercio de la mediana),
falla la pregunta de control, contesta la matriz en línea recta o escribe el texto libre en otro
idioma. De 270 respuestas sintéticas quedan 103.

El test A/B se lee con el intervalo de Wilson. En total, el frente A gana con claridad (72 %, del
63 % al 80 %). Entre los menores de 45, el 58 % no basta: el intervalo baja del 50 %, y con 31
respuestas no se puede decir que ganen.

## Ejecutarlo

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

pytest                                  # 21 comprobaciones, en menos de un segundo
python scripts/estudio.py figuras       # tablas por pantalla y gráficos en figuras/
python scripts/estudio.py figuras en    # los gráficos en inglés
```

Los tests comprueban los rangos de precio en sus bordes, que afinar nunca agranda el segmento,
cada filtro del segmento offline, que el mercado es offline corregido más online, el reparto de
cuota entre modelos del mismo segmento, el pedido, el orden de los escenarios, qué modelos marca el
contraste, la detección de idioma, cada filtro de la encuesta por separado, que la limpieza atrapa
toda la basura sintética y nada más, el intervalo de Wilson y que el A/B dice lo que el texto dice.

## Diferencias con el estudio real

- El estudio real cruzaba un panel de ventas de tiendas físicas y datos de un marketplace con
  licencia. Aquí son tablas sintéticas con la misma forma.
- El real incluía buyer personas a partir de fuentes secundarias, tratadas como hipótesis, y una
  matriz de persona por tipo de cámara para priorizar el surtido. Aquí no están: sin los datos
  reales no aportan método.
- La encuesta real se hizo con Typeform y su panel, y la limpieza se centraba en detectar las
  respuestas que no estaban en español. Aquí son cinco reglas, cada una separada y probada.

## Licencia

MIT. Ver `LICENSE`.
