"""ui_extra.py — Entrada animada, loader, hovers y estilos del portal de pagos.
No modifica estilos.py: se carga DESPUÉS de aplicar_estilos() y solo sobreescribe/añade.
"""
from contextlib import contextmanager

import streamlit as st

_CSS_EXTRA = """
:root {
    --azul: #12239E; --azul-profundo: #0B1659; --azul-medio: #2B3FD6;
    --acento: #FF5100; --acento-oscuro: #CC4706;
    --ok: #1E9E6A; --warn: #F2A100; --bad: #D93A3A;
    --ease: cubic-bezier(.22,.61,.36,1);
}

/* ============ ENTRADA (SPLASH) ============ */
.splash {
    position: fixed; inset: 0; z-index: 999999;
    display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 18px;
    background: radial-gradient(circle at 30% 20%, #2B3FD6 0%, #12239E 45%, #0B1659 100%);
    color: #fff; pointer-events: none;
    animation: splashOut .7s ease 2.3s forwards;
}
.splash::before, .splash::after {
    content: ''; position: absolute; border-radius: 50%; filter: blur(2px);
    animation: float 6s ease-in-out infinite;
}
.splash::before { width: 340px; height: 340px; right: -90px; top: -90px; background: var(--acento); opacity: .9; }
.splash::after  { width: 240px; height: 240px; left: -70px; bottom: -80px; background: rgba(255,255,255,.12); animation-delay: -3s; }
.splash-logo {
    position: relative; z-index: 2; width: 92px; height: 92px; border-radius: 26px;
    background: rgba(255,255,255,.14); backdrop-filter: blur(6px);
    border: 1px solid rgba(255,255,255,.3);
    display: flex; align-items: center; justify-content: center;
    animation: pop .8s var(--ease) both, pulse 2s ease-in-out .8s infinite;
}
.splash-logo svg { width: 44px; height: 44px; stroke: #fff; fill: none; stroke-width: 1.7; stroke-linecap: round; stroke-linejoin: round; }
.splash h2 { position: relative; z-index: 2; margin: 0; color: #fff; font-size: 1.9rem; font-weight: 700;
    letter-spacing: -.02em; animation: up .8s var(--ease) .25s both; }
.splash p { position: relative; z-index: 2; margin: 0; opacity: .85; font-size: .98rem; animation: up .8s var(--ease) .4s both; }
.splash-bar { position: relative; z-index: 2; width: 220px; height: 5px; border-radius: 99px;
    background: rgba(255,255,255,.2); overflow: hidden; margin-top: 8px; }
.splash-bar i { display: block; height: 100%; width: 0; border-radius: 99px; background: #fff;
    animation: fill 2.1s ease .3s forwards; }
@keyframes splashOut { to { opacity: 0; visibility: hidden; transform: scale(1.04); } }
@keyframes fill { to { width: 100%; } }
@keyframes pop { from { opacity: 0; transform: scale(.6) rotate(-8deg); } to { opacity: 1; transform: none; } }
@keyframes pulse { 0%,100% { box-shadow: 0 0 0 0 rgba(255,255,255,.35); } 50% { box-shadow: 0 0 0 16px rgba(255,255,255,0); } }
@keyframes up { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: none; } }
@keyframes float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(18px); } }

/* ============ LOADER ============ */
/* Barra superior mientras Streamlit ejecuta */
.stApp[data-test-script-state="running"]::before {
    content: ''; position: fixed; top: 0; left: 0; height: 3px; width: 100%; z-index: 99999;
    background: linear-gradient(90deg, transparent, var(--acento), var(--azul-medio), transparent);
    background-size: 50% 100%; background-repeat: no-repeat;
    animation: barra 1.1s ease-in-out infinite;
}
@keyframes barra { from { background-position: -60% 0; } to { background-position: 160% 0; } }
[data-testid="stStatusWidget"] { opacity: .85; }

.loader {
    display: flex; align-items: center; gap: 14px; width: fit-content;
    padding: 12px 20px; margin: 10px 0; background: #fff;
    border: 1px solid #e3e6f6; border-radius: 14px; box-shadow: 0 6px 18px rgba(18,35,158,.08);
    color: var(--azul); font-weight: 600; font-size: .92rem;
}
.loader .ring { width: 22px; height: 22px; border-radius: 50%;
    border: 3px solid #e3e6f6; border-top-color: var(--acento); animation: spin .8s linear infinite; }
.loader .dots span { display: inline-block; width: 5px; height: 5px; margin-left: 3px; border-radius: 50%;
    background: var(--azul); animation: dot 1.2s infinite ease-in-out; }
.loader .dots span:nth-child(2) { animation-delay: .15s; }
.loader .dots span:nth-child(3) { animation-delay: .3s; }
@keyframes spin { to { transform: rotate(360deg); } }
@keyframes dot { 0%,80%,100% { opacity: .25; transform: translateY(0); } 40% { opacity: 1; transform: translateY(-4px); } }

.skeleton { border-radius: 14px; min-height: 90px;
    background: linear-gradient(100deg, #eef0fb 30%, #f9faff 50%, #eef0fb 70%);
    background-size: 200% 100%; animation: shimmer 1.3s linear infinite; }
@keyframes shimmer { to { background-position: -200% 0; } }

/* ============ BASE / ANIMACIÓN DE ENTRADA ============ */
html { scroll-behavior: smooth; }
.stApp { background: linear-gradient(180deg, #f3f5fd 0%, #ffffff 45%); }
.block-container { max-width: 1250px; padding-top: 1.6rem; }
#MainMenu, footer { visibility: hidden; }
.block-container > div > div[data-testid="stVerticalBlock"] > div { animation: up .6s var(--ease) both; }
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-thumb { background: #c9cff0; border-radius: 99px; }
::-webkit-scrollbar-thumb:hover { background: var(--azul); }
::selection { background: var(--acento); color: #fff; }

/* ============ HERO ============ */
.hero {
    position: relative; overflow: hidden; color: #fff; border-radius: 22px;
    padding: 36px 40px; margin-bottom: 22px; border-bottom: none;
    background: linear-gradient(120deg, var(--azul) 0%, var(--azul-medio) 60%, #4A5CE8 100%);
    box-shadow: 0 16px 36px rgba(18,35,158,.28);
    transition: transform .3s var(--ease), box-shadow .3s var(--ease);
}
.hero:hover { transform: translateY(-2px); box-shadow: 0 22px 44px rgba(18,35,158,.34); }
.hero::after { content: ''; position: absolute; right: -60px; top: -70px; width: 260px; height: 260px;
    border-radius: 50%; background: var(--acento); opacity: .92; animation: float 7s ease-in-out infinite; }
.hero::before { content: ''; position: absolute; right: 130px; bottom: -90px; width: 190px; height: 190px;
    border-radius: 50%; background: rgba(255,255,255,.1); animation: float 9s ease-in-out infinite reverse; }
.hero h1, .hero p { position: relative; z-index: 2; }
.hero h1 { font-size: 2rem; }
.hero p { max-width: 640px; }
.hero-chips { position: relative; z-index: 2; display: flex; gap: 8px; flex-wrap: wrap; margin-top: 16px; }
.hero-chips span { background: rgba(255,255,255,.16); border: 1px solid rgba(255,255,255,.28);
    padding: 4px 12px; border-radius: 99px; font-size: .78rem; font-weight: 500; backdrop-filter: blur(4px); }

/* ============ TÍTULOS / TARJETAS / KPI ============ */
.section-title { display: flex; align-items: center; gap: 10px; width: fit-content;
    border-bottom: 3px solid var(--acento); padding-bottom: 8px; margin: 26px 0 14px 0; }
.section-title svg { width: 22px; height: 22px; color: var(--acento); margin: 0; vertical-align: 0; }

.card { background: #fff; border: 1px solid #e3e6f6; border-top: 1px solid #e3e6f6; border-radius: 16px; padding: 20px;
    box-shadow: 0 6px 18px rgba(18,35,158,.07); height: 100%; position: relative; overflow: hidden;
    transition: transform .25s var(--ease), box-shadow .25s var(--ease), border-color .25s; }
.card::after { content: ''; position: absolute; left: 0; bottom: 0; height: 3px; width: 0;
    background: var(--acento); transition: width .35s var(--ease); }
.card:hover { transform: translateY(-5px); box-shadow: 0 16px 32px rgba(18,35,158,.16); border-color: #c9cff0; }
.card:hover::after { width: 100%; }
.card .ic { width: 46px; height: 46px; border-radius: 13px; background: #eef0fb; color: var(--azul);
    display: flex; align-items: center; justify-content: center; margin-bottom: 12px; transition: transform .3s var(--ease), background .25s, color .25s; }
.card:hover .ic { transform: rotate(-6deg) scale(1.08); background: var(--acento); color: #fff; }
.card.blue { background: linear-gradient(135deg, var(--azul), var(--azul-medio)); border: none; }
.card.blue .ic { background: rgba(255,255,255,.16); color: #fff; }
.card.blue .ct, .card.blue .cb { color: #fff; }
.card.blue:hover .ic { background: var(--acento); }

.kpi { background: #fff; border-radius: 16px; padding: 18px 20px; border: 1px solid #e3e6f6;
    border-left: 6px solid var(--acento); box-shadow: 0 6px 18px rgba(18,35,158,.07);
    transition: transform .25s var(--ease), box-shadow .25s var(--ease); }
.kpi:hover { transform: translateY(-4px) scale(1.01); box-shadow: 0 14px 28px rgba(18,35,158,.15); }
.kpi .l { color: #6b7090; font-size: .78rem; text-transform: uppercase; letter-spacing: .05em; }
.kpi .v { color: var(--azul); font-size: 1.85rem; font-weight: 700; }
.kpi.ok { border-left-color: var(--ok); } .kpi.warn { border-left-color: var(--warn); }

/* ============ BADGES / FICHA ============ */
.badge { display: inline-block; padding: 4px 14px; border-radius: 999px; font-size: .8rem; font-weight: 600; }
.badge.Recibido { background: #FFF1E0; color: #C25E00; }
.badge.Pendiente { background: #FFF8DB; color: #8A6A00; }
.badge.Verificado { background: #E2F6EC; color: #137A50; }
.badge.Rechazado { background: #FCE5E5; color: #B02A2A; }
.ficha { background: #fff; border: 1px solid #e3e6f6; border-radius: 16px; padding: 18px 22px; box-shadow: 0 6px 18px rgba(18,35,158,.07); }
.ficha .fila { display: flex; justify-content: space-between; gap: 16px; padding: 9px 0; border-bottom: 1px dashed #dfe2f3; font-size: .9rem; transition: background .2s, padding .2s; }
.ficha .fila:hover { background: #f6f7fe; padding-left: 8px; padding-right: 8px; border-radius: 8px; }
.ficha .fila:last-child { border-bottom: none; }
.ficha .k { color: #6b7090; } .ficha .val { color: #1f2340; font-weight: 600; text-align: right; }

/* ============ TABS ============ */
.stTabs [data-baseweb="tab-list"] { gap: 8px; background: #eef0fb; padding: 6px; border-radius: 14px; }
.stTabs [data-baseweb="tab"] { border-radius: 10px; padding: 8px 18px; font-weight: 500; color: var(--azul); height: auto; transition: background .2s, transform .2s; }
.stTabs [data-baseweb="tab"]:hover { background: rgba(18,35,158,.08); transform: translateY(-1px); }
.stTabs [aria-selected="true"] { background: var(--azul) !important; color: #fff !important; box-shadow: 0 6px 14px rgba(18,35,158,.3); }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none; }
.stTabs [data-baseweb="tab-panel"] { animation: up .45s var(--ease) both; }

/* ============ FORMULARIO / INPUTS / BOTONES ============ */
[data-testid="stForm"] { background: #fff; border: 1px solid #e3e6f6; border-radius: 18px; padding: 26px; box-shadow: 0 8px 24px rgba(18,35,158,.08); transition: box-shadow .3s; }
[data-testid="stForm"]:focus-within { box-shadow: 0 14px 34px rgba(18,35,158,.15); }
div[data-baseweb="select"] > div, div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input,
div[data-testid="stDateInput"] input, div[data-testid="stTextArea"] textarea { transition: border-color .2s, box-shadow .2s, transform .2s; }
div[data-baseweb="select"] > div:hover, div[data-testid="stTextInput"] input:hover { border-color: var(--azul) !important; }
div[data-testid="stTextInput"] input:focus, div[data-testid="stTextArea"] textarea:focus { transform: translateY(-1px); }
[data-testid="stFileUploader"] section { border: 2px dashed #c9cff0; border-radius: 14px; background: #fafbff; transition: all .25s; }
[data-testid="stFileUploader"] section:hover { border-color: var(--acento); background: #fff6f1; }

.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button, .stLinkButton > a {
    border-radius: 12px; font-weight: 600; border: 1.5px solid var(--azul); color: var(--azul);
    position: relative; overflow: hidden; transition: transform .2s var(--ease), box-shadow .2s, background .2s, color .2s; }
.stButton > button:hover, .stFormSubmitButton > button:hover, .stDownloadButton > button:hover, .stLinkButton > a:hover {
    transform: translateY(-2px); box-shadow: 0 8px 18px rgba(18,35,158,.22); background: var(--azul); color: #fff; border-color: var(--azul); }
.stButton > button:active, .stFormSubmitButton > button:active { transform: translateY(0) scale(.98); }
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--acento), #ff7a3d); border-color: var(--acento); color: #fff; padding: 10px 0; }
.stButton > button[kind="primary"]:hover, .stFormSubmitButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #e04800, var(--acento)); border-color: #e04800; box-shadow: 0 10px 22px rgba(255,81,0,.38); }

/* ============ TABLAS / MÉTRICAS ============ */
div[data-testid="stDataFrame"] { border: 1px solid #e3e6f6; border-radius: 14px; overflow: hidden; box-shadow: 0 6px 18px rgba(18,35,158,.05); transition: box-shadow .25s; }
div[data-testid="stDataFrame"]:hover { box-shadow: 0 12px 26px rgba(18,35,158,.12); }
[data-testid="stMetric"] { background: #fff; border-radius: 14px; padding: 12px; }
div[data-testid="stVerticalBlockBorderWrapper"] { transition: box-shadow .25s, transform .25s; }
div[data-testid="stVerticalBlockBorderWrapper"]:hover { box-shadow: 0 12px 26px rgba(18,35,158,.12); }

/* ============ PAGO CON TARJETA (SANTANDER) ============ */
.pay-wrap { display: grid; grid-template-columns: 1.1fr 1fr; gap: 20px; align-items: stretch; }
.pay-card { position: relative; overflow: hidden; border-radius: 20px; padding: 26px; color: #fff; min-height: 190px;
    background: linear-gradient(135deg, #EC0000 0%, #B20000 70%); box-shadow: 0 16px 34px rgba(178,0,0,.3);
    transition: transform .35s var(--ease), box-shadow .35s; }
.pay-card:hover { transform: translateY(-4px) rotateX(3deg); box-shadow: 0 24px 44px rgba(178,0,0,.38); }
.pay-card::after { content: ''; position: absolute; right: -50px; top: -50px; width: 190px; height: 190px; border-radius: 50%; background: rgba(255,255,255,.14); }
.pay-card .chip { width: 42px; height: 30px; border-radius: 7px; background: linear-gradient(135deg, #ffe08a, #d9a928); margin-bottom: 26px; }
.pay-card .num { font-size: 1.3rem; letter-spacing: .18em; font-weight: 600; }
.pay-card .meta { display: flex; justify-content: space-between; margin-top: 18px; font-size: .78rem; opacity: .9; }
.pay-info { background: #fff; border: 1px solid #e3e6f6; border-radius: 16px; padding: 20px 22px; box-shadow: 0 6px 18px rgba(18,35,158,.07); }
.pay-info li { margin: 6px 0; color: #4a4f6a; font-size: .9rem; }
.tag-soon { display: inline-block; background: #FFF1E0; color: #C25E00; border-radius: 99px; padding: 2px 12px; font-size: .75rem; font-weight: 700; }
.tag-live { display: inline-block; background: #E2F6EC; color: #137A50; border-radius: 99px; padding: 2px 12px; font-size: .75rem; font-weight: 700; }
@media (max-width: 800px) { .pay-wrap { grid-template-columns: 1fr; } .hero { padding: 24px 22px; } .hero h1 { font-size: 1.5rem; } }

/* ============ PIE ============ */
.pie { text-align: center; color: #8a8fae; font-size: .8rem; margin-top: 36px; padding-top: 14px; border-top: 1px solid #e3e6f6; }
"""

_SPLASH = (
    "<div class='splash'>"
    "<div class='splash-logo'><svg viewBox='0 0 24 24'>"
    "<path d='M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z'/><polyline points='9 22 9 12 15 12 15 22'/></svg></div>"
    "<h2>Portal de Pagos de Terrenos</h2>"
    "<p>Preparando tu espacio…</p>"
    "<div class='splash-bar'><i></i></div></div>"
)


def aplicar_mejoras(splash: bool = True) -> None:
    """Inyecta el CSS extra y, una sola vez por sesión, la pantalla de entrada."""
    st.markdown(f"<style>{_CSS_EXTRA}</style>", unsafe_allow_html=True)
    if splash and not st.session_state.get("_splash_visto"):
        st.session_state["_splash_visto"] = True
        st.markdown(_SPLASH, unsafe_allow_html=True)


@contextmanager
def cargando(texto: str = "Cargando"):
    """Loader animado:  with cargando('Consultando pagos'): ..."""
    ph = st.empty()
    ph.markdown(
        f"<div class='loader'><div class='ring'></div><div>{texto}"
        "<span class='dots'><span></span><span></span><span></span></span></div></div>",
        unsafe_allow_html=True,
    )
    try:
        yield
    finally:
        ph.empty()


def skeleton(n: int = 4, alto: int = 90) -> str:
    """HTML de n tarjetas 'esqueleto' (shimmer) para mostrar mientras llegan datos."""
    return "".join(f"<div class='skeleton' style='min-height:{alto}px;margin-bottom:10px'></div>" for _ in range(n))