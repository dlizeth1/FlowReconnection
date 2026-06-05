# -*- coding: utf-8 -*-
"""
config.py — Supuestos del modelo financiero de Flow Reconnection (centro de flotación).

FUENTE: Google Sheet 13v_c-IKpTtp25rWFLb47jb0oLEccQ7Fi (leído 2026-06-05).
Moneda: COP. Todas las cifras son editables: este archivo es la única fuente de verdad.

Notas de reconciliación (verificadas contra el Sheet):
  - CAPEX suma exactamente $344,441,600.
  - Costos fijos Medellín (estado estable) suman $47,484,523, consistentes con el P&L del Sheet.
"""

# ---------------------------------------------------------------------------
# 1. INVERSIÓN INICIAL (CAPEX)  — fuente: hoja "INVERSIÓN"
# ---------------------------------------------------------------------------
CAPEX = {
    "tanques_flotacion":      174_441_600,   # 4 tanques x $43,610,400 c/u (opción compra)
    "adecuaciones_y_muebles": 100_000_000,
    "capital_trabajo_6m":      60_000_000,   # capital de trabajo 6 meses (sin admin)
    "camaras_seguridad":        5_000_000,
    "pagina_web":               5_000_000,
}
CAPEX_TOTAL = sum(CAPEX.values())            # = 344,441,600

# Alternativas de base de inversión que aparecen en el Sheet (para el slider de capex).
CAPEX_ALTERNATIVAS = {
    "Base (compra tanques)":           344_441_600,
    "Tanques en RENTING":              261_662_400,
    "Acumulado intermedio (Sheet)":    516_102_527,
    "Acumulado máximo (Sheet)":        777_764_927,
}

# Costo unitario de un tanque y opción renting (referencia).
TANQUE_VALOR_UNITARIO = 43_610_400
TANQUE_RENTING_TOTAL  = 261_662_400
MARCA_BLANCA_USD      = 4_000              # x 4 meses, sin % sobre ventas

# Depreciación mensual (tanques) — fuente: hoja INVERSIÓN.
DEPRECIACION_MENSUAL = 2_907_360

# ---------------------------------------------------------------------------
# 2. CAPACIDAD INSTALADA  — fuente: hoja "PROY RAFAEL CAPACIDAD INSTALADA"
# ---------------------------------------------------------------------------
CAPACIDAD = {
    "horas_por_flote":        1.5,
    "horas_atencion_dia":     14,
    "sesiones_dia_por_tanque": 9,     # 14h / 1.5h ≈ 9 turnos
    "dias_abiertos_mes":      30,
}
N_TANQUES_BASE = 4

def capacidad_mensual(n_tanques=N_TANQUES_BASE):
    """Sesiones máximas por mes para n tanques (100% de ocupación)."""
    return CAPACIDAD["sesiones_dia_por_tanque"] * CAPACIDAD["dias_abiertos_mes"] * n_tanques
# 4 tanques -> 1,080 sesiones/mes

# ---------------------------------------------------------------------------
# 3. PRECIOS  — fuente: hojas "PROY RAFAEL" e "INGRESOS Franja horaria"
# ---------------------------------------------------------------------------
PRECIO_OPERATIVO_PLANO = 155_000   # precio usado en el P&L real Medellín/Barranquilla

PRECIOS_FRANJA = {
    "diurno":   {"precio": 150_000, "share": 0.57, "franja": "9am–5pm"},
    "nocturno": {"precio": 170_000, "share": 0.43, "franja": "5pm–11pm"},
}
def precio_blended():
    return sum(v["precio"] * v["share"] for v in PRECIOS_FRANJA.values())  # = 158,600

# ---------------------------------------------------------------------------
# 4. COSTOS VARIABLES  — fuente: hoja de costos (100% capacidad = 1,080 sesiones, 4 tanques)
# ---------------------------------------------------------------------------
COSTOS_VARIABLES_100 = {
    "sal_epsom":          2_615_200,   # 14 sacos x $46,700 x 4 tanques
    "tapaoidos":            726_000,
    "vaselina":             540_000,
    "panitos_humedos":      200_000,
    "quimicos_peroxido":    500_000,
    "productos_limpieza":   500_000,
}
COSTOS_VARIABLES_100_TOTAL = sum(COSTOS_VARIABLES_100.values())   # = 5,081,200

def costo_variable_por_sesion():
    """Costo variable por sesión = total al 100% / capacidad al 100% (4 tanques)."""
    return COSTOS_VARIABLES_100_TOTAL / capacidad_mensual(4)      # ≈ 4,705.74

# ---------------------------------------------------------------------------
# 5. COSTOS FIJOS MENSUALES (4 tanques, estado estable Medellín)
#    — fuente: P&L Medellín, meses estables (ene–mar).
# ---------------------------------------------------------------------------
COSTOS_FIJOS_4T = {
    "arriendo":            19_040_000,   # SLIDER (varía por ciudad/local)
    "servicios_publicos":   2_000_000,
    "servicios_generales":  6_317_265,   # 2 personas SMLV + 20% recargos
    "administracion":       2_334_540,
    "recepcion":            6_317_265,   # 2 personas ~$1.6M
    "contabilidad":           875_453,
    "software":               250_000,
    "seguridad_camaras":            0,
    "seguro":                 500_000,
    "pagina_web_mant":         50_000,
    "pauta_anuncios":       8_000_000,   # SLIDER (~2,000 usd)
    "mercadeo":             1_500_000,
    "mantenimiento":          300_000,
}
COSTOS_FIJOS_4T_TOTAL = sum(COSTOS_FIJOS_4T.values())   # = 47,484,523

# Buckets para escalar costos fijos según # de tanques en el modelo interactivo.
# (independientes del tamaño vs. los que escalan con la operación)
FIJOS_INDEPENDIENTES = ["contabilidad", "software", "seguro", "pagina_web_mant",
                        "mercadeo", "seguridad_camaras"]
FIJOS_ESCALAN_CON_TANQUES = ["servicios_publicos", "servicios_generales",
                             "administracion", "recepcion", "mantenimiento"]
FIJOS_SLIDERS = ["arriendo", "pauta_anuncios"]

# ---------------------------------------------------------------------------
# 6. CURVAS REALES DEL SHEET (para validación cruzada, no para el modelo limpio)
# ---------------------------------------------------------------------------
ESCENARIOS_REPORTADOS = {
    "Medellín (4 tanques)": {
        "meses":    ["Jul", "Ago", "Sep", "Oct", "Nov", "Dic", "Ene", "Feb", "Mar"],
        "sesiones": [162, 189, 216, 540, 648, 648, 432, 432, 432],
        "precio":   155_000,
        "ingresos_total":   573_345_000,
        "costos_total":     553_307_236,   # incluye capex del mes 1 dentro del opex
        "utilidad_marginal":  20_037_764,  # 3%
        "despues_depreciacion": -6_128_476,  # -1%
    },
    "Barranquilla (2–3 tanques)": {
        "meses":    ["Ago", "Sep", "Oct", "Nov", "Dic", "Ene", "Feb", "Mar", "Abr"],
        "sesiones": [162, 189, 324, 324, 324, 324, 324, 324, 324],
        "precio":   155_000,
        "ingresos_total":   405_945_000,
        "costos_total":     537_535_746,
        "utilidad_marginal": -131_590_746,  # -32%
        "despues_depreciacion": -157_756_986,  # -39%
    },
}

# Curva de ocupación objetivo (modelo limpio, 4 tanques) — ramp del Sheet.
OCUPACION_OBJETIVO = [0.30, 0.35, 0.40, 0.50, 0.60, 0.60, 0.40, 0.40, 0.40, 0.45, 0.45, 0.45]

# ---------------------------------------------------------------------------
# 7. IDEAS DE INGRESO ADICIONAL  — fuente: hoja "IDEAS INGRESOS"
# ---------------------------------------------------------------------------
IDEAS_INGRESO = [
    {"idea": "Membresía 'Fundadores' (100 cupos x $1.5M)", "potencial": 150_000_000},
    {"idea": "Anualidad socios 'Fundadores' (30 cupos x $7M)", "potencial": 210_000_000},
    {"idea": "Ceremonia de lanzamiento (30 cupos x $50K)", "potencial": 15_000_000},
    {"idea": "Tienda (sales, aceites, velas, journal, libros, té)", "potencial": None},
]

# ---------------------------------------------------------------------------
# 8. PARÁMETROS POR DEFECTO DEL MODELO INTERACTIVO
# ---------------------------------------------------------------------------
DEFAULTS = {
    "n_tanques":   4,
    "precio":      155_000,          # precio operativo plano del Sheet
    "ocupacion":   0.40,             # ocupación de estado estable
    "arriendo":    19_040_000,
    "pauta":       8_000_000,
    "capex":       344_441_600,
    "incluir_depreciacion_en_be": False,
}
