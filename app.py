import os
import re
import sqlite3
import uuid
from datetime import datetime

import pandas as pd
import streamlit as st
from PIL import Image
from streamlit_echarts import JsCode, st_echarts

from estilos import aplicar_estilos
from ui_extra import aplicar_mejoras, cargando

# ------------------------------------------------------------------ CONFIGURACIÓN
# set_page_config SIEMPRE antes de cualquier otro comando de Streamlit
st.set_page_config(page_title="Pagos de Terrenos", page_icon=":material/landscape:", layout="wide")
aplicar_estilos()
aplicar_mejoras(splash=True)  # splash=False para desactivar la pantalla de entrada

CARPETA_COMPROBANTES = "comprobantes"
DB_NAME = "pagos_terrenos.db"
AZUL, NARANJA = "#12239E", "#FF5100"
ESTATUS = ["Pendiente", "Recibido", "Verificado", "Rechazado"]
ESTATUS_ICONO = {
    "Pendiente": "🟡 Pendiente", "Recibido": "🟠 Recibido",
    "Verificado": "🟢 Verificado", "Rechazado": "🔴 Rechazado",
}
MOTIVOS = ["Mensualidad", "Enganche", "Anualidad", "Liquidación total", "Servicios / Mantenimiento", "Otro"]

os.makedirs(CARPETA_COMPROBANTES, exist_ok=True)


# ------------------------------------------------------------------ SANTANDER (PLACEHOLDER)
def _secret(nombre, defecto=""):
    """Lee de st.secrets (.streamlit/secrets.toml) o de variables de entorno."""
    try:
        if nombre in st.secrets:
            return st.secrets[nombre]
    except Exception:
        pass
    return os.getenv(nombre, defecto)


SANTANDER = {
    "activo": str(_secret("SANTANDER_ACTIVO", "false")).lower() == "true",  # ← cámbialo a true al integrar
    "base_url": _secret("SANTANDER_BASE_URL"),        # URL del ambiente (sandbox / producción)
    "client_id": _secret("SANTANDER_CLIENT_ID"),
    "client_secret": _secret("SANTANDER_CLIENT_SECRET"),
    "merchant_id": _secret("SANTANDER_MERCHANT_ID"),
    "url_retorno": _secret("SANTANDER_URL_RETORNO"),  # a dónde regresa el cliente tras pagar
    "url_webhook": _secret("SANTANDER_URL_WEBHOOK"),  # endpoint que recibe la confirmación
}


def crear_orden_santander(referencia: str, monto: float, cliente: str, concepto: str) -> dict:
    """Crea la orden de cobro en Santander y devuelve la URL de pago (checkout alojado).

    IMPORTANTE (PCI-DSS): NO captures ni guardes número de tarjeta/CVV en esta app.
    Usa el checkout alojado/redirección o la tokenización del SDK de Santander.

    Debe devolver: {"ok": bool, "url_pago": str | None, "id_externo": str | None, "error": str | None}
    """
    if not SANTANDER["activo"]:
        return {"ok": False, "url_pago": None, "id_externo": None,
                "error": "La integración con Santander aún no está activada."}

    # ---------------- TODO: integrar API de Santander ----------------
    # import requests
    # 1) Autenticación (OAuth2 / token según tu contrato):
    #    tok = requests.post(f"{SANTANDER['base_url']}/<endpoint_token>",
    #                        data={"client_id": SANTANDER["client_id"],
    #                              "client_secret": SANTANDER["client_secret"],
    #                              "grant_type": "client_credentials"}, timeout=20).json()["access_token"]
    # 2) Crear orden / liga de pago:
    #    r = requests.post(f"{SANTANDER['base_url']}/<endpoint_orden>",
    #                      headers={"Authorization": f"Bearer {tok}"},
    #                      json={"merchant_id": SANTANDER["merchant_id"], "reference": referencia,
    #                            "amount": round(monto, 2), "currency": "MXN", "description": concepto,
    #                            "customer": {"name": cliente},
    #                            "return_url": SANTANDER["url_retorno"],
    #                            "notification_url": SANTANDER["url_webhook"]}, timeout=20)
    #    r.raise_for_status(); d = r.json()
    #    return {"ok": True, "url_pago": d["<campo_url>"], "id_externo": d["<campo_id>"], "error": None}
    # -----------------------------------------------------------------
    return {"ok": False, "url_pago": None, "id_externo": None, "error": "Falta implementar crear_orden_santander()."}


# ------------------------------------------------------------------ HELPERS HTML
ICONOS = {
    "home": '<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>',
    "dollar": '<line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',
    "file": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>',
    "upload": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>',
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
    "bar": '<line x1="12" y1="20" x2="12" y2="10"/><line x1="18" y1="20" x2="18" y2="4"/><line x1="6" y1="20" x2="6" y2="16"/>',
    "image": '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/>',
    "list": '<line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/>',
    "card": '<rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/>',
}


def svg(nombre):
    cuerpo = ICONOS.get(nombre)
    if not cuerpo:
        return ""
    return ("<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8'"
            f" stroke-linecap='round' stroke-linejoin='round'>{cuerpo}</svg>")


def show(html):
    st.markdown(html, unsafe_allow_html=True)


def hero(titulo_texto, subtitulo, icono=None, chips=()):
    ch = "".join(f"<span>{c}</span>" for c in chips)
    show(f"<div class='hero'><h1>{svg(icono)}{titulo_texto}</h1><p>{subtitulo}</p>"
         f"{f'<div class=hero-chips>{ch}</div>' if ch else ''}</div>")


def titulo(texto, icono=None):
    show(f"<h3 class='section-title'>{svg(icono)}{texto}</h3>")


def card(icono, titulo_, cuerpo, azul=False):
    cls = "card blue" if azul else "card"
    return (f"<div class='{cls}'><div class='ic'>{svg(icono)}</div>"
            f"<div class='ct'>{titulo_}</div><div class='cb'>{cuerpo}</div></div>")


def kpi(label, valor, sub="", tono=""):
    return (f"<div class='kpi {tono}'><div class='l'>{label}</div>"
            f"<div class='v'>{valor}</div><div class='s'>{sub}</div></div>")


def badge(estatus):
    return f"<span class='badge {estatus}'>{estatus}</span>"


def ficha(filas):
    html = "".join(f"<div class='fila'><span class='k'>{k}</span><span class='val'>{v}</span></div>" for k, v in filas)
    return f"<div class='ficha'>{html}</div>"


# ------------------------------------------------------------------ ECHARTS
BASE = {"backgroundColor": "transparent", "animationDuration": 1100, "animationEasing": "cubicOut"}
GRID = {"left": 40, "right": 20, "top": 40, "bottom": 30, "containLabel": True}


def _grad(c1, c2):
    return JsCode("new echarts.graphic.LinearGradient(0,0,0,1,"
                  f"[{{offset:0,color:'{c1}'}},{{offset:1,color:'{c2}'}}])").js_code


def opcion_mensual(df):
    d = df.copy()
    d["mes"] = pd.to_datetime(d["fecha_pago"], errors="coerce").dt.strftime("%Y-%m")
    g = d.dropna(subset=["mes"]).groupby("mes")["monto"].sum().sort_index()
    eje_fmt = JsCode("function(v){return Math.abs(v)>=1000?(v/1000).toFixed(0)+'k':v;}").js_code
    tip_fmt = JsCode("function(p){return '<b>'+p[0].axisValue+'</b><br/>$'+Number(p[0].value)"
                     ".toLocaleString('es-MX',{minimumFractionDigits:2});}").js_code
    return {
        **BASE,
        "tooltip": {"trigger": "axis", "formatter": tip_fmt, "borderColor": NARANJA},
        "grid": GRID,
        "xAxis": {"type": "category", "data": g.index.tolist()},
        "yAxis": {"type": "value", "axisLabel": {"formatter": eje_fmt},
                  "splitLine": {"lineStyle": {"type": "dashed", "color": "#d9dcf0"}}},
        "series": [{
            "name": "Recaudado", "type": "bar", "barWidth": "50%",
            "emphasis": {"itemStyle": {"shadowBlur": 14, "shadowColor": "rgba(255,81,0,.45)"}},
            "data": [{"value": round(float(v), 2),
                      "itemStyle": {"color": _grad(NARANJA, "#ffb08a"), "borderRadius": [8, 8, 0, 0]}}
                     for v in g.values],
        }],
    }


def opcion_metodos(df):
    g = df.groupby("metodo_pago")["monto"].sum().sort_values(ascending=False)
    return {
        **BASE,
        "color": [AZUL, NARANJA, "#7C89E0", "#FFB08A"],
        "tooltip": {"trigger": "item", "formatter": "{b}<br/>${c} ({d}%)"},
        "legend": {"bottom": 0, "textStyle": {"fontSize": 11}},
        "series": [{
            "type": "pie", "radius": ["48%", "72%"], "center": ["50%", "45%"],
            "itemStyle": {"borderRadius": 8, "borderColor": "#fff", "borderWidth": 3},
            "label": {"show": False},
            "emphasis": {"scaleSize": 8, "label": {"show": True, "fontWeight": "bold"}},
            "data": [{"name": k, "value": round(float(v), 2)} for k, v in g.items()],
        }],
    }


# ------------------------------------------------------------------ BASE DE DATOS
def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pagos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_registro TEXT, fecha_pago TEXT, cliente TEXT, lote_manzana TEXT, motivo TEXT,
            cantidad_mensualidades INTEGER, monto REAL, metodo_pago TEXT, ruta_comprobante TEXT, estatus TEXT
        )""")
    # Migración: columnas nuevas para pagos con tarjeta (no rompe la BD existente)
    cols = {r[1] for r in conn.execute("PRAGMA table_info(pagos)")}
    for col in ("referencia_pago", "id_externo"):
        if col not in cols:
            conn.execute(f"ALTER TABLE pagos ADD COLUMN {col} TEXT")
    conn.commit()
    conn.close()


def guardar_pago(fecha_pago, cliente, lote, motivo, cantidad, monto, metodo, ruta_img,
                 estatus="Recibido", referencia=None, id_externo=None):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("""
        INSERT INTO pagos (fecha_registro, fecha_pago, cliente, lote_manzana, motivo, cantidad_mensualidades,
            monto, metodo_pago, ruta_comprobante, estatus, referencia_pago, id_externo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), str(fecha_pago), cliente, lote, motivo, cantidad,
         monto, metodo, ruta_img, estatus, referencia, id_externo))
    conn.commit()
    conn.close()


def cargar_pagos():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM pagos ORDER BY id DESC", conn)
    conn.close()
    return df


def actualizar_estatus(id_pago, nuevo_estatus):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("UPDATE pagos SET estatus = ? WHERE id = ?", (nuevo_estatus, id_pago))
    conn.commit()
    conn.close()


def confirmar_pago_por_referencia(referencia, estatus="Verificado"):
    """Para el webhook/retorno de Santander: marca el pago como pagado usando su referencia."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute("UPDATE pagos SET estatus = ? WHERE referencia_pago = ?", (estatus, referencia))
    conn.commit()
    conn.close()


def limpio(texto):
    return re.sub(r"[^A-Za-z0-9_-]", "", texto.strip().replace(" ", "_"))


init_db()


# ------------------------------------------------------------------ PESTAÑA 1: REGISTRO (transferencia / depósito)
def vista_registro():
    hero("Registro de pagos de terrenos",
         "Sube tu comprobante de transferencia o depósito y registra tu abono en menos de un minuto.",
         icono="home", chips=["⚡ Rápido", "🔒 Seguro", "📄 Con comprobante"])

    c1, c2, c3 = st.columns(3)
    c1.markdown(card("file", "1 · Llena los datos", "Nombre, lote, motivo y monto del abono.", azul=True), unsafe_allow_html=True)
    c2.markdown(card("upload", "2 · Adjunta tu comprobante", "Foto, captura o PDF de la operación."), unsafe_allow_html=True)
    c3.markdown(card("shield", "3 · Recibe validación", "Revisamos tu pago y lo marcamos como verificado.", azul=True), unsafe_allow_html=True)

    titulo("Datos del abono", "dollar")
    with st.form("form_pagos", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            cliente = st.text_input("Nombre completo de quien paga *", placeholder="Ej. Juan Pérez López")
            lote = st.text_input("Lote y manzana *", placeholder="Ej. Manzana 4, Lote 12")
            motivo = st.selectbox("Motivo del pago *", MOTIVOS)
            cantidad = st.number_input("Mensualidades o unidades pagadas", min_value=1, value=1, step=1)
        with col2:
            fecha_pago = st.date_input("Fecha en que se realizó el pago *", value=datetime.today())
            monto = st.number_input("Monto total pagado (MXN) *", min_value=0.0, format="%.2f", step=500.0)
            metodo = st.selectbox("Método de pago", ["Transferencia SPEI", "Depósito en ventanilla / OXXO", "Efectivo"])
            comprobante = st.file_uploader("Foto o captura del comprobante *", type=["png", "jpg", "jpeg", "pdf"])

        notas_extra = st.text_area("Observaciones (opcional)", placeholder="Ej. Pago de los meses de noviembre y diciembre.")
        enviado = st.form_submit_button("Registrar pago", use_container_width=True, type="primary", icon=":material/task_alt:")

        if enviado:
            if not cliente or not lote or monto <= 0 or comprobante is None:
                st.error("Completa los campos obligatorios (*) y adjunta el comprobante.")
            else:
                with cargando("Guardando tu pago"):
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    ext = comprobante.name.split(".")[-1].lower()
                    ruta = os.path.join(CARPETA_COMPROBANTES, f"{ts}_{limpio(cliente)}_{limpio(lote)}.{ext}")
                    with open(ruta, "wb") as f:
                        f.write(comprobante.getbuffer())
                    motivo_completo = f"{motivo} ({notas_extra})" if notas_extra else motivo
                    guardar_pago(fecha_pago, cliente, lote, motivo_completo, cantidad, monto, metodo, ruta)
                st.success(f"Pago de **${monto:,.2f}** registrado a nombre de **{cliente}**.")
                st.balloons()


# ------------------------------------------------------------------ PESTAÑA 2: PAGO CON TARJETA (SANTANDER)
def vista_tarjeta():
    live = SANTANDER["activo"]
    estado = "<span class='tag-live'>Activo</span>" if live else "<span class='tag-soon'>Próximamente</span>"
    hero("Paga con tarjeta",
         "Pago en línea seguro con Santander. Serás redirigido a su página de pago protegida.",
         icono="card", chips=["💳 Crédito y débito", "🔐 Pago cifrado", "✅ Confirmación automática"])

    show(
        "<div class='pay-wrap'>"
        "<div class='pay-card'><div class='chip'></div><div class='num'>•••• •••• •••• ••••</div>"
        f"<div class='meta'><span>SANTANDER</span><span>{estado}</span></div></div>"
        "<div class='pay-info'><b>¿Cómo funciona?</b><ul>"
        "<li>Capturas los datos del abono.</li>"
        "<li>Te llevamos al checkout seguro de Santander.</li>"
        "<li>Al pagar, tu abono se marca como <b>Verificado</b> automáticamente.</li>"
        "<li>Nunca guardamos los datos de tu tarjeta.</li></ul></div></div>"
    )

    titulo("Datos del pago", "dollar")
    with st.form("form_tarjeta", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            cliente = st.text_input("Nombre completo de quien paga *", key="t_cliente")
            lote = st.text_input("Lote y manzana *", key="t_lote")
        with col2:
            motivo = st.selectbox("Motivo del pago *", MOTIVOS, key="t_motivo")
            monto = st.number_input("Monto a pagar (MXN) *", min_value=0.0, format="%.2f", step=500.0, key="t_monto")
        pagar = st.form_submit_button("Pagar con tarjeta", use_container_width=True, type="primary", icon=":material/lock:")

    if pagar:
        if not cliente or not lote or monto <= 0:
            st.error("Completa los campos obligatorios (*).")
            return
        referencia = f"TER-{datetime.now():%Y%m%d%H%M%S}-{uuid.uuid4().hex[:6].upper()}"
        with cargando("Conectando con Santander"):
            res = crear_orden_santander(referencia, monto, cliente, f"{motivo} - {lote}")
        if res["ok"]:
            guardar_pago(datetime.today().date(), cliente, lote, motivo, 1, monto, "Pago con tarjeta (Santander)",
                         "", estatus="Pendiente", referencia=referencia, id_externo=res["id_externo"])
            st.success("Orden creada. Continúa en la página segura de Santander.")
            st.link_button("Ir a pagar", res["url_pago"], type="primary", icon=":material/open_in_new:")
        else:
            st.warning(res["error"], icon=":material/construction:")
            with st.expander("Checklist para activar la integración"):
                st.markdown(
                    "- Definir en `.streamlit/secrets.toml`: `SANTANDER_ACTIVO`, `SANTANDER_BASE_URL`, "
                    "`SANTANDER_CLIENT_ID`, `SANTANDER_CLIENT_SECRET`, `SANTANDER_MERCHANT_ID`, "
                    "`SANTANDER_URL_RETORNO`, `SANTANDER_URL_WEBHOOK`.\n"
                    "- Implementar `crear_orden_santander()` (hay un esqueleto comentado en el código).\n"
                    "- Crear un endpoint (p. ej. FastAPI) que reciba el webhook y llame a "
                    "`confirmar_pago_por_referencia(referencia)`; Streamlit no puede recibir webhooks.\n"
                    "- No capturar número de tarjeta ni CVV en esta app (PCI-DSS): usa checkout alojado."
                )


# ------------------------------------------------------------------ PESTAÑA 3: ADMINISTRACIÓN
def vista_admin():
    hero("Panel de administración",
         "Revisa pagos, valida comprobantes y da seguimiento a la cobranza de cada lote.", icono="bar")

    with cargando("Consultando pagos"):
        df = cargar_pagos()
    if df.empty:
        st.info("Aún no hay pagos registrados. Cuando un cliente registre uno, aparecerá aquí.")
        return

    total = df["monto"].sum()
    n_rec = int(df["estatus"].isin(["Recibido", "Pendiente"]).sum())
    n_ver = int((df["estatus"] == "Verificado").sum())

    k = st.columns(4)
    k[0].markdown(kpi("Total recaudado", f"${total:,.2f}", "todos los estatus"), unsafe_allow_html=True)
    k[1].markdown(kpi("Pagos registrados", f"{len(df)}", f"ticket promedio ${df['monto'].mean():,.0f}"), unsafe_allow_html=True)
    k[2].markdown(kpi("Por verificar", f"{n_rec}", "pendientes de revisión", "warn"), unsafe_allow_html=True)
    k[3].markdown(kpi("Verificados", f"{n_ver}", "validados", "ok"), unsafe_allow_html=True)

    titulo("Resumen de cobranza", "bar")
    g1, g2 = st.columns([1.7, 1])
    with g1:
        st.caption("Monto recibido por mes de pago")
        st_echarts(opcion_mensual(df), height="300px", key="eco_mensual")
    with g2:
        st.caption("Monto por método de pago")
        st_echarts(opcion_metodos(df), height="300px", key="eco_metodos")

    titulo("Pagos registrados", "list")
    f1, f2 = st.columns([2, 1])
    filtro = f1.text_input("Buscar por nombre o lote", placeholder="Escribe un nombre o lote", key="f_texto")
    filtro_est = f2.selectbox("Estatus", ["Todos"] + ESTATUS, key="f_estatus")

    dff = df.copy()
    if filtro:
        dff = dff[dff["cliente"].str.contains(filtro, case=False, na=False)
                  | dff["lote_manzana"].str.contains(filtro, case=False, na=False)]
    if filtro_est != "Todos":
        dff = dff[dff["estatus"] == filtro_est]

    tabla = dff[["id", "fecha_pago", "cliente", "lote_manzana", "motivo",
                 "cantidad_mensualidades", "monto", "metodo_pago", "estatus"]].copy()
    tabla["estatus"] = tabla["estatus"].map(ESTATUS_ICONO).fillna(tabla["estatus"])
    st.dataframe(
        tabla, use_container_width=True, hide_index=True,
        column_config={
            "id": "ID", "fecha_pago": "Fecha de pago", "cliente": "Cliente", "lote_manzana": "Lote / manzana",
            "motivo": "Motivo", "cantidad_mensualidades": "Cant.",
            "monto": st.column_config.NumberColumn("Monto", format="$%.2f"),
            "metodo_pago": "Método", "estatus": "Estatus",
        },
    )
    st.download_button("Descargar reporte CSV", data=dff.to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"reporte_pagos_terrenos_{datetime.today():%Y-%m-%d}.csv",
                       mime="text/csv", icon=":material/download:")

    titulo("Visor y validación de comprobantes", "image")
    if dff.empty:
        st.info("No hay pagos con esos filtros.")
        return

    nombres = {r.id: f"ID #{r.id} · {r.cliente} · ${r.monto:,.2f}" for r in dff.itertuples()}
    id_sel = st.selectbox("Selecciona un pago", dff["id"].tolist(), format_func=lambda x: nombres[x])
    reg = dff[dff["id"] == id_sel].iloc[0]

    col_img, col_det = st.columns(2)
    with col_img:
        ruta = reg["ruta_comprobante"]
        with st.container(border=True):
            if not ruta:
                st.info("Pago con tarjeta: no requiere comprobante. Se confirma con la respuesta de Santander.")
            elif os.path.exists(ruta):
                if ruta.lower().endswith(".pdf"):
                    st.warning("El comprobante es un archivo PDF.")
                    with open(ruta, "rb") as pdf:
                        st.download_button("Abrir / descargar PDF", pdf, file_name=os.path.basename(ruta))
                else:
                    st.image(Image.open(ruta), caption=os.path.basename(ruta), use_container_width=True)
            else:
                st.error("No se encontró el archivo del comprobante en el servidor.")

    with col_det:
        filas = [("Cliente", reg["cliente"]), ("Lote / manzana", reg["lote_manzana"]),
                 ("Fecha de pago", reg["fecha_pago"]), ("Motivo", reg["motivo"]),
                 ("Cantidad", reg["cantidad_mensualidades"]), ("Método", reg["metodo_pago"]),
                 ("Monto", f"${reg['monto']:,.2f}")]
        if reg.get("referencia_pago"):
            filas.append(("Referencia", reg["referencia_pago"]))
        filas.append(("Estatus", badge(reg["estatus"])))
        show(ficha(filas))
        st.write("")
        nuevo = st.selectbox("Cambiar estatus", ESTATUS, index=ESTATUS.index(reg["estatus"]))
        if st.button("Actualizar estatus", type="primary", use_container_width=True, icon=":material/sync:"):
            actualizar_estatus(int(id_sel), nuevo)
            st.success("Estatus actualizado.")
            st.rerun()


# ------------------------------------------------------------------ NAVEGACIÓN
t1, t2, t3 = st.tabs([
    ":material/edit_note: Registrar pago",
    ":material/credit_card: Pagar con tarjeta",
    ":material/dashboard: Administración",
])
with t1:
    vista_registro()
with t2:
    vista_tarjeta()
with t3:
    vista_admin()

show("<div class='pie'>Portal de pagos de terrenos · Los comprobantes se resguardan en el servidor</div>")