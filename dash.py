import streamlit as st
import pandas as pd
from utils import load_custom_css, load_local_dataset, get_base64_image
from page_login import render_login_page
from page_home import render_home_page
from page_sentiment_analysis import render_sentiment_analysis_page
from page_deepdive import render_deepdive_page
from page_admin import render_admin_page

st.set_page_config(
    page_title="TKB News Sentiment Analysis",
    page_icon="assets/icons/logo_pertamina_square.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 1. Autentikasi Pengguna
render_login_page()
load_custom_css()

if "active_page" not in st.session_state:
    st.session_state.active_page = "HOME"

df_raw, loaded_file_name = load_local_dataset()
user_role = st.session_state.get("user_role", "user")

# Guardrail: Cegah akses role non-admin ke halaman settings
if user_role != "admin" and st.session_state.active_page == "ADMIN_SETTINGS":
    st.session_state.active_page = "HOME"

def navigate_to(page_name):
    if st.session_state.active_page != page_name:
        for key in ["home_filters", "ov_filters", "deep_filters"]:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state.active_page = page_name
        st.rerun()

# -------------------------------------------------------------
# CSS: FULL-BLEED TOPBAR & SIDEBAR WITH TITLES
# -------------------------------------------------------------
st.markdown("""
<style>
    /* Sembunyikan header bawaan Streamlit agar tidak menimpa topbar kustom */
    header[data-testid="stHeader"] {
        display: none !important;
    }

    /* TOPBAR FULL DARI UJUNG KE UJUNG */
    .dashboard-topbar-fullbleed {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        height: 64px !important;
        background: #ffffff !important;
        border-bottom: 1.5px solid #e2e8f0 !important;
        z-index: 99999 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        padding: 0 32px !important;
        box-sizing: border-box !important;
        box-shadow: 0 1px 4px rgba(15, 23, 42, 0.04) !important;
    }

    .dashboard-brand {
        display: flex;
        align-items: center;
    }

    .dashboard-brand img {
        height: 36px;
        width: auto;
        object-fit: contain;
    }

    .dashboard-brand-fallback {
        color: #0f172a;
        font-size: 16px;
        line-height: 1.1;
        font-weight: 800;
    }

    .dashboard-brand-fallback span {
        display: block;
        color: #64748b;
        font-size: 8px;
        letter-spacing: 1.5px;
    }

    .dashboard-header-title {
        color: #64748b;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 1.5px;
        text-transform: uppercase;
    }

    /* Padding kompensasi agar konten tidak tertutup fixed topbar */
    .main .block-container {
        padding-top: 80px !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }

    /* SIDEBAR MELEBAR DENGAN TEKS JUDUL MENU */
    [data-testid="stSidebar"] {
        min-width: 240px !important;
        max-width: 240px !important;
        background-color: #ffffff !important;
        border-right: 1.5px solid #e2e8f0 !important;
        top: 64px !important;
        height: calc(100vh - 64px) !important;
        z-index: 9999 !important;
    }

    [data-testid="stSidebar"] > div:first-child {
        padding: 1.2rem 0.8rem !important;
    }

    [data-testid="stSidebarCollapseButton"] {
        display: none !important;
    }

    /* CONTAINER TOMBOL MENU */
    [data-testid="stSidebar"] div.stButton {
        width: 100% !important;
        margin-bottom: 6px !important;
    }

    /* DESAIN TOMBOL: RATA KIRI, ADA IKON & TEKS */
    [data-testid="stSidebar"] div.stButton > button {
        width: 100% !important;
        min-height: 42px !important;
        border-radius: 8px !important;
        border: 1.5px solid transparent !important;
        background-color: transparent !important;
        color: #475569 !important;
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        justify-content: flex-start !important;
        padding: 8px 12px !important;
        gap: 10px !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: none !important;
    }

    /* PAKSA TEKS DAN IKON DI DALAM TOMBOL RATA KIRI */
    [data-testid="stSidebar"] div.stButton > button > div,
    [data-testid="stSidebar"] div.stButton > button [data-testid="stMarkdownContainer"] {
        display: flex !important;
        justify-content: flex-start !important;
        align-items: center !important;
        width: 100% !important;
        text-align: left !important;
    }

    [data-testid="stSidebar"] div.stButton > button p {
        font-size: 0.84rem !important;
        font-weight: 600 !important;
        color: #475569 !important;
        text-align: left !important;
        margin: 0 !important;
    }

    /* HOVER EFFECT */
    [data-testid="stSidebar"] div.stButton > button:hover {
        background-color: #f8fafc !important;
        border-color: #e2e8f0 !important;
        color: #237ece !important;
    }

    [data-testid="stSidebar"] div.stButton > button:hover p {
        color: #237ece !important;
    }

    /* ACTIVE STATE (MENU TERPILIH) */
    [data-testid="stSidebar"] div.stButton > button[kind="primary"] {
        background-color: #f0f7ff !important;
        border-color: #bfdbfe !important;
        color: #237ece !important;
    }

    [data-testid="stSidebar"] div.stButton > button[kind="primary"] p {
        color: #237ece !important;
        font-weight: 700 !important;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# TOPBAR BRANDING (MEMBENTANG PENUH UJUNG KE UJUNG)
# -------------------------------------------------------------
logo_full_b64 = get_base64_image("assets/icons/logo_pertamina_full.png")
if logo_full_b64:
    logo_markup = f'<img src="{logo_full_b64}" alt="Pertamina Digital Hub" />'
else:
    logo_markup = '<div class="dashboard-brand-fallback">PERTAMINA<span>DIGITAL HUB</span></div>'

st.markdown(f"""
    <div class="dashboard-topbar-fullbleed">
        <div class="dashboard-brand">{logo_markup}</div>
        <div class="dashboard-header-title">TKB NEWS SENTIMENT ANALYSIS</div>
    </div>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# SIDEBAR NAVIGATION (IKON + TEKS JUDUL)
# -------------------------------------------------------------
with st.sidebar:
    # Profil Singkat Pengguna yang Login
    st.markdown(f"""
        <div style="margin-bottom: 16px; padding: 10px 12px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;">
            <div style="color: #64748b; font-size: 0.65rem; font-weight: 700; text-transform: uppercase;">Logged In As:</div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 2px;">
                <b style="color: #0f172a; font-size: 0.88rem;">{st.session_state.get('username', 'User')}</b>
                <span style="font-size: 0.65rem; background: #e0f2fe; color: #0369a1; padding: 2px 6px; border-radius: 4px; font-weight: 700;">
                    {user_role.upper()}
                </span>
            </div>
        </div>
        <p style="font-size: 0.68rem; font-weight: 800; color: #94a3b8; letter-spacing: 0.05em; margin-bottom: 8px; margin-left: 4px;">DASHBOARD MENU</p>
    """, unsafe_allow_html=True)

    # Menu 1: Home
    if st.button(":material/home: Dashboard Home", key="btn_nav_home", use_container_width=True, type="primary" if st.session_state.active_page == "HOME" else "secondary"):
        navigate_to("HOME")

    # Menu 2: Sentiment Analysis
    if st.button(":material/analytics: Sentiment Analysis", key="btn_nav_sentiment", use_container_width=True, type="primary" if st.session_state.active_page == "SENTIMENT_ANALYSIS" else "secondary"):
        navigate_to("SENTIMENT_ANALYSIS")

    # Menu 3: Deep Dive
    if st.button(":material/search: Topic Deep Dive", key="btn_nav_deepdive", use_container_width=True, type="primary" if st.session_state.active_page == "DEEP_DIVE" else "secondary"):
        navigate_to("DEEP_DIVE")

    # Menu 4: Admin Settings (Khusus Role Admin)
    if user_role == "admin":
        if st.button(":material/settings: Admin Settings", key="btn_nav_admin", use_container_width=True, type="primary" if st.session_state.active_page == "ADMIN_SETTINGS" else "secondary"):
            navigate_to("ADMIN_SETTINGS")

    st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)

    # Tombol Logout
    if st.button(":material/logout: Logout", key="btn_nav_logout", use_container_width=True):
        st.session_state.clear()
        st.query_params.clear()
        st.rerun()

# -------------------------------------------------------------
# PAGE ROUTER
# -------------------------------------------------------------
if st.session_state.active_page == "HOME":
    render_home_page(df_raw)
elif st.session_state.active_page == "SENTIMENT_ANALYSIS":
    render_sentiment_analysis_page(df_raw)
elif st.session_state.active_page == "DEEP_DIVE":
    render_deepdive_page(df_raw)
elif st.session_state.active_page == "ADMIN_SETTINGS" and user_role == "admin":
    render_admin_page(df_raw, loaded_file_name)