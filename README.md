# Flow Reconnection — Modelo financiero

Modelo financiero del centro de flotación **Flow Reconnection** (Medellín, 4 tanques; Barranquilla
como alterno). Consolida punto de equilibrio, ROI, payback, P&L y flujo de caja a
partir del Google Sheet del equipo, y genera un **HTML interactivo** que se abre en el navegador.

## Archivos

| Archivo | Qué es |
|---|---|
| `config.py` | Supuestos del modelo (capex, precios, costos, ocupación, ideas de ingreso). Respaldo estático: **el Sheet manda**. |
| `live_sheet.py` | Lee EN VIVO el `.xlsx` del Drive (por link público) y sobrescribe los supuestos de `config.py`. |
| `model.py` | Cálculos puros (stdlib) + reporte de validación cruzada contra el Sheet. |
| `build_html.py` | Genera el entregable HTML autónomo. |
| `flow_reconnection_modelo.html` | **Entregable**: dashboard interactivo (sliders + gráficos). Doble clic para abrir. |

## Uso

```bash
pip install -r requirements.txt   # requests + openpyxl (para la lectura en vivo)
python model.py        # imprime KPIs y valida el modelo vs el Sheet
python build_html.py   # regenera flow_reconnection_modelo.html
```
Por defecto los scripts descargan el Sheet en vivo y caen a los valores estáticos de `config.py`
si la descarga falla. Para forzar modo offline: `FLOW_LIVE=0`. El HTML usa Plotly.js vía CDN
(requiere internet al abrir).

> **Privacidad**: el cap table (hoja ABONOS del Sheet) **no** se extrae ni se publica:
> contiene datos personales que no deben llegar al HTML público.

## Cómo editar los supuestos

Edita el Google Sheet (el Sheet manda) o, en modo offline, los valores de `config.py`, y vuelve a
correr `python build_html.py`. El HTML también permite ajustar en vivo (sin reconstruir):
# tanques, precio, ocupación, arriendo, pauta y base de inversión.

## Hallazgos clave (caso base Medellín, 4 tanques, $155.000)

- **Punto de equilibrio: ~29% de ocupación** (≈316 sesiones/mes). Contribución $150.295/sesión.
- **ROI / payback** muy sensibles a la ocupación: 40% → ~20 meses (ROI ~51%); 60% → ~7 meses.
- La **curva de apertura planeada** (arranque 30–40%) **no recupera la inversión en 12 meses**
  (saldo ≈ −$54M): conviene acelerar ocupación o subir precio en los primeros meses.
- **Barranquilla** (2–3 tanques) da margen negativo en el Sheet (−32%); Medellín es la mejor base.

## Validación

`model.py` reproduce las cifras del Sheet (ingreso año Medellín $573.345.000 exacto, ingreso 100%/mes
≈$171.3M, total de capex cuadrado). Diferencia clave con el Sheet: aquí la capex se
trata como inversión one-time (fuera del opex), lo que permite ROI/payback limpios.

Fuente: Google Sheet `13v_c-IKpTtp25rWFLb47jb0oLEccQ7Fi`.
