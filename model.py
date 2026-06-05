# -*- coding: utf-8 -*-
"""
model.py — Cálculos financieros de Flow Reconnection (puro stdlib, sin dependencias).

Consolida: capacidad/ingresos, punto de equilibrio, P&L, ROI/payback (capex separado
de opex) y flujo de caja. Incluye un reporte de validación cruzada que
reproduce las cifras del Google Sheet.

Uso:
    python model.py            # imprime KPIs base + validación vs Sheet
"""

import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import config as C


# ---------------------------------------------------------------------------
# Costos fijos según número de tanques (escalado de buckets)
# ---------------------------------------------------------------------------
def costos_fijos(n_tanques=4, arriendo=None, pauta=None):
    """
    Costos fijos mensuales. Los items 'independientes' no varían con el tamaño;
    los de operación escalan con n_tanques/4 (piso 40%); arriendo y pauta son
    parámetros (sliders).
    """
    arriendo = C.COSTOS_FIJOS_4T["arriendo"] if arriendo is None else arriendo
    pauta    = C.COSTOS_FIJOS_4T["pauta_anuncios"] if pauta is None else pauta

    factor = max(0.40, n_tanques / 4.0)
    total = 0.0
    for item, valor in C.COSTOS_FIJOS_4T.items():
        if item == "arriendo":
            total += arriendo
        elif item == "pauta_anuncios":
            total += pauta
        elif item in C.FIJOS_ESCALAN_CON_TANQUES:
            total += valor * factor
        else:  # independientes
            total += valor
    return total


# ---------------------------------------------------------------------------
# Punto de equilibrio
# ---------------------------------------------------------------------------
def contribucion_por_sesion(precio):
    return precio - C.costo_variable_por_sesion()


def punto_equilibrio(n_tanques=4, precio=155_000, arriendo=None, pauta=None,
                     incluir_depreciacion=False):
    fijos = costos_fijos(n_tanques, arriendo, pauta)
    if incluir_depreciacion:
        fijos += C.DEPRECIACION_MENSUAL
    contrib = contribucion_por_sesion(precio)
    cap = C.capacidad_mensual(n_tanques)
    sesiones_be = fijos / contrib if contrib > 0 else float("inf")
    return {
        "sesiones_be":   sesiones_be,
        "ocupacion_be":  sesiones_be / cap if cap else float("inf"),
        "ingreso_be":    sesiones_be * precio,
        "contribucion_por_sesion": contrib,
        "fijos":         fijos,
        "capacidad":     cap,
    }


# ---------------------------------------------------------------------------
# P&L mensual (modelo limpio: capex NO entra en opex)
# ---------------------------------------------------------------------------
def pyl_mensual(n_tanques=4, precio=155_000, ocupacion=0.40,
                arriendo=None, pauta=None):
    cap = C.capacidad_mensual(n_tanques)
    sesiones = cap * ocupacion
    ingresos = sesiones * precio
    var = sesiones * C.costo_variable_por_sesion()
    fijos = costos_fijos(n_tanques, arriendo, pauta)
    utilidad_operativa = ingresos - var - fijos          # EBITDA aprox
    utilidad_neta = utilidad_operativa - C.DEPRECIACION_MENSUAL
    return {
        "sesiones": sesiones,
        "ingresos": ingresos,
        "costos_variables": var,
        "costos_fijos": fijos,
        "depreciacion": C.DEPRECIACION_MENSUAL,
        "utilidad_operativa": utilidad_operativa,
        "utilidad_neta": utilidad_neta,
        "margen_operativo": utilidad_operativa / ingresos if ingresos else 0,
        "margen_neto": utilidad_neta / ingresos if ingresos else 0,
        "flujo_caja_mensual": utilidad_operativa,  # EBITDA ≈ caja (depreciación no es salida)
    }


# ---------------------------------------------------------------------------
# ROI / Payback (estado estable, capex como inversión one-time)
# ---------------------------------------------------------------------------
def roi_payback(n_tanques=4, precio=155_000, ocupacion=0.40,
                arriendo=None, pauta=None, capex=None):
    capex = C.CAPEX_TOTAL if capex is None else capex
    pyl = pyl_mensual(n_tanques, precio, ocupacion, arriendo, pauta)
    flujo_mes = pyl["flujo_caja_mensual"]            # caja operativa mensual
    utilidad_anual = pyl["utilidad_neta"] * 12
    return {
        "capex": capex,
        "flujo_caja_mensual": flujo_mes,
        "payback_meses": (capex / flujo_mes) if flujo_mes > 0 else float("inf"),
        "roi_anual": utilidad_anual / capex if capex else 0,
        "utilidad_neta_anual": utilidad_anual,
    }


# ---------------------------------------------------------------------------
# Flujo de caja acumulado (ramp con curva de ocupación)
# ---------------------------------------------------------------------------
def flujo_caja_acumulado(n_tanques=4, precio=155_000, arriendo=None, pauta=None,
                         capex=None, ocupacion_curva=None):
    capex = C.CAPEX_TOTAL if capex is None else capex
    curva = ocupacion_curva or C.OCUPACION_OBJETIVO
    saldo = -capex
    filas = [{"mes": 0, "flujo": -capex, "acumulado": saldo, "ocupacion": None}]
    for i, occ in enumerate(curva, start=1):
        pyl = pyl_mensual(n_tanques, precio, occ, arriendo, pauta)
        flujo = pyl["flujo_caja_mensual"]
        saldo += flujo
        filas.append({"mes": i, "flujo": flujo, "acumulado": saldo, "ocupacion": occ})
    return filas


def payback_desde_curva(filas):
    for f in filas:
        if f["mes"] > 0 and f["acumulado"] >= 0:
            return f["mes"]
    return None


# ---------------------------------------------------------------------------
# Reporte de validación cruzada vs Sheet
# ---------------------------------------------------------------------------
def _fmt(x):
    return f"${x:,.0f}"


def validar():
    print("=" * 72)
    print("FLOW RECONNECTION — Validación del modelo vs Google Sheet")
    print("=" * 72)

    # --- Totales y consistencia interna ---
    fuente = "EN VIVO (Google Sheet)" if getattr(C, "LIVE_DATA", False) else "estático (config.py)"
    print(f"\n[1] Totales (fuente: {fuente}):")
    fij_ok = C.COSTOS_FIJOS_4T_TOTAL == sum(C.COSTOS_FIJOS_4T.values())
    print(f"  CAPEX total            : {_fmt(C.CAPEX_TOTAL)}")
    print(f"  Costos fijos 4T total  : {_fmt(C.COSTOS_FIJOS_4T_TOTAL)}  "
          f"(suma de items {'OK' if fij_ok else 'DIF'})")

    # --- Capacidad e ingreso 100% ---
    print("\n[2] Capacidad e ingreso (4 tanques):")
    cap = C.capacidad_mensual(4)
    ing100_blended = cap * C.precio_blended()
    print(f"  Capacidad/mes          : {cap:,.0f} sesiones  (esperado 1,080)")
    print(f"  Precio blended         : {_fmt(C.precio_blended())}  (esperado $158,600)")
    print(f"  Ingreso 100% (blended) : {_fmt(ing100_blended)}  (Sheet ≈ $171,280,000)")

    # --- Punto de equilibrio ---
    print("\n[3] Punto de equilibrio (4 tanques, $155,000):")
    be = punto_equilibrio(4, 155_000)
    print(f"  Contribución/sesión    : {_fmt(be['contribucion_por_sesion'])}")
    print(f"  Costos fijos/mes        : {_fmt(be['fijos'])}")
    print(f"  Sesiones equilibrio    : {be['sesiones_be']:,.0f}/mes")
    print(f"  Ocupación equilibrio   : {be['ocupacion_be']*100:,.1f}%")
    print(f"  Ingreso equilibrio     : {_fmt(be['ingreso_be'])}/mes")

    # --- Validación de P&L Medellín reportado ---
    print("\n[4] Validación curva Medellín reportada (precio $155,000):")
    esc = C.ESCENARIOS_REPORTADOS["Medellín (4 tanques)"]
    ing_model = sum(esc["sesiones"]) * esc["precio"]
    print(f"  Sesiones año           : {sum(esc['sesiones']):,.0f}")
    print(f"  Ingreso año (modelo)   : {_fmt(ing_model)}  (Sheet {_fmt(esc['ingresos_total'])})  "
          f"{'OK' if ing_model == esc['ingresos_total'] else 'DIF'}")
    _ing = esc["ingresos_total"] or 1
    print(f"  Utilidad marginal Sheet: {_fmt(esc['utilidad_marginal'])} "
          f"({esc['utilidad_marginal']/_ing*100:.0f}%)")
    print(f"  Después de deprec Sheet: {_fmt(esc['despues_depreciacion'])} "
          f"({esc['despues_depreciacion']/_ing*100:.0f}%)")

    # --- ROI / Payback estado estable ---
    print(f"\n[5] ROI / Payback (estado estable, capex {_fmt(C.CAPEX_TOTAL)}):")
    for occ in (0.30, 0.40, 0.50, 0.60):
        rp = roi_payback(4, 155_000, occ)
        pm = rp["payback_meses"]
        pm_txt = f"{pm:,.1f} meses" if pm != float("inf") else "no recupera"
        print(f"  Ocup {occ*100:>3.0f}% -> flujo/mes {_fmt(rp['flujo_caja_mensual']):>16} | "
              f"ROI anual {rp['roi_anual']*100:>6.1f}% | payback {pm_txt}")

    # --- Flujo de caja con ramp ---
    print("\n[6] Flujo de caja acumulado (curva de ocupación objetivo):")
    filas = flujo_caja_acumulado(4, 155_000)
    pb = payback_desde_curva(filas)
    print(f"  Mes de payback         : {pb if pb else 'no en el horizonte'}")
    print(f"  Saldo fin de horizonte : {_fmt(filas[-1]['acumulado'])}")
    print("=" * 72)


if __name__ == "__main__":
    validar()
