import streamlit as st
import time
import os
import pandas as pd
from datetime import datetime
from utils import get_base64_image

LOG_FILE = "login_history.csv"

def record_login_history(username: str, role: str):
    """Mencatat tanggal, waktu, nama pengguna, dan peran ke file CSV."""
    now = datetime.now()
    log_entry = {
        "Tanggal": now.strftime("%Y-%m-%d"),
        "Waktu": now.strftime("%H:%M:%S"),
        "Username": username,
        "Role": role.upper()
    }
    df_new = pd.DataFrame([log_entry])
    if not os.path.exists(LOG_FILE):
        df_new.to_csv(LOG_FILE, index=False)
    else:
        df_new.to_csv(LOG_FILE, mode="a", header=False, index=False)

def render_login_page():
    if not st.session_state.get("logged_in", False):
        user_param = st.query_params.get("user")
        role_param = st.query_params.get("role")
        if user_param and role_param:
            st.session_state.logged_in = True
            st.session_state.username = user_param
            st.session_state.user_role = role_param
            return

    if st.session_state.get("logged_in", False):
        return

    if "login_animating" not in st.session_state:
        st.session_state.login_animating = False

    st.markdown("""
        <style>
            /* Sembunyikan elemen bawaan Streamlit */
            [data-testid="stSidebar"],
            header[data-testid="stHeader"],
            #MainMenu,
            footer {
                display: none !important;
            }

            /* Background Blueprint Grid */
            .stApp {
                min-height: 100vh !important;
                background:
                    linear-gradient(rgba(226, 232, 240, 0.45) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(226, 232, 240, 0.45) 1px, transparent 1px),
                    #f8fafc !important;
                background-size: 42px 42px !important;
            }

            [data-testid="stAppViewContainer"] {
                min-height: 100vh !important;
                background: transparent !important;
            }

            .block-container {
                max-width: 100% !important;
                padding: 0 !important;
                margin: 0 !important;
            }

            /* Header Topbar */
            .login-topbar {
                height: 68px;
                width: 100%;
                box-sizing: border-box;
                background: rgba(255, 255, 255, 0.98);
                border-bottom: 1px solid #e2e8f0;
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 0 42px;
            }

            .login-brand {
                display: flex;
                align-items: center;
            }

            .login-brand img {
                height: 38px;
                width: auto;
                object-fit: contain;
            }

            .login-brand-fallback {
                color: #0f172a;
                font-size: 17px;
                line-height: 1.1;
                font-weight: 800;
            }

            .login-brand-fallback span {
                display: block;
                color: #64748b;
                font-size: 8px;
                letter-spacing: 1.5px;
            }

            .login-header-title {
                color: #64748b;
                font-size: 12px;
                font-weight: 700;
                letter-spacing: 1.5px;
                text-transform: uppercase;
            }

            /* Container Tengah */
            .login-center-wrapper {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding-top: 48px;
                padding-bottom: 24px;
            }

            .login-icon-box {
                width: 52px;
                height: 52px;
                margin: 0 auto 16px auto;
                border-radius: 14px;
                background: linear-gradient(145deg, #163c9f 0%, #2563eb 100%);
                box-shadow: 0 8px 18px rgba(37, 99, 235, 0.22);
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .login-icon-box svg {
                width: 24px;
                height: 24px;
            }

            .login-main-heading {
                margin: 0;
                color: #0f172a;
                font-size: 24px;
                line-height: 1.2;
                font-weight: 800;
                text-align: center;
            }

            .login-sub-heading {
                margin: 6px 0 20px 0;
                color: #64748b;
                font-size: 13.5px;
                text-align: center;
                font-weight: 500;
            }

            /* Kartu Form */
            div[data-testid="stForm"] {
                width: 420px !important;
                max-width: calc(100vw - 32px) !important;
                margin: 0 auto !important;
                padding: 28px 30px !important;
                background: #ffffff !important;
                border: 1px solid #e2e8f0 !important;
                border-radius: 16px !important;
                box-shadow: 0 12px 32px rgba(15, 23, 42, 0.07) !important;
            }

            .login-field-label {
                color: #475569;
                font-size: 11px;
                font-weight: 800;
                letter-spacing: 0.8px;
                margin: 0 0 6px 0;
                display: block;
                text-transform: uppercase;
            }

            /* ============================================================
               BORDER UTUH PADA KOTAK INPUT (GARIS BAWAH JELAS & RAPI)
               ============================================================ */
            div[data-testid="stTextInput"] {
                margin: 0 0 16px 0 !important;
            }

            div[data-testid="stTextInput"] label {
                display: none !important;
            }

            div[data-testid="stTextInput"] > div,
            div[data-testid="stTextInputRootElement"] {
                border: 1.5px solid #cbd5e1 !important;
                border-radius: 8px !important;
                background-color: #ffffff !important;
                box-shadow: none !important;
                transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
                overflow: visible !important;
                box-sizing: border-box !important;
            }

            div[data-testid="stTextInput"]:focus-within > div,
            div[data-testid="stTextInputRootElement"]:focus-within {
                border-color: #2563eb !important;
                box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.15) !important;
            }

            div[data-testid="stTextInput"] input {
                height: 42px !important;
                box-sizing: border-box !important;
                border: none !important;
                outline: none !important;
                background: transparent !important;
                color: #1e293b !important;
                font-size: 13.5px !important;
                padding: 0 14px !important;
                box-shadow: none !important;
            }

            /* Sembunyikan Tombol Show Password */
            div[data-testid="stTextInput"] button[aria-label="Show password"],
            div[data-testid="stTextInput"] button[aria-label="Hide password"],
            div[data-testid="stTextInput"] button:not([kind]) {
                display: none !important;
                visibility: hidden !important;
            }

            /* Tombol Biru Gradasi */
            div[data-testid="stFormSubmitButton"],
            div[data-testid="stFormSubmitButton"] > button,
            button[kind="primaryFormSubmit"],
            button[kind="secondaryFormSubmit"] {
                width: 100% !important;
                height: 48px !important;
                min-height: 48px !important;
                margin-top: 10px !important;
                border: none !important;
                border-radius: 10px !important;
                background: linear-gradient(90deg, #153c9e 0%, #1e52c8 48%, #2563eb 100%) !important;
                color: #ffffff !important;
                box-shadow: 0 8px 24px rgba(21, 60, 158, 0.38) !important;
                transition: transform 0.2s ease, box-shadow 0.2s ease !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                cursor: pointer !important;
            }

            div[data-testid="stFormSubmitButton"] > button p,
            div[data-testid="stFormSubmitButton"] > button span,
            button[kind="primaryFormSubmit"] * {
                color: #ffffff !important;
                font-size: 13.5px !important;
                font-weight: 800 !important;
                letter-spacing: 0.8px !important;
                text-transform: uppercase !important;
            }

            div[data-testid="stFormSubmitButton"] > button:hover,
            button[kind="primaryFormSubmit"]:hover {
                background: linear-gradient(90deg, #113286 0%, #1843a8 48%, #1d51c7 100%) !important;
                transform: translateY(-2px) !important;
                box-shadow: 0 12px 28px rgba(21, 60, 158, 0.5) !important;
            }

            div[data-testid="stFormSubmitButton"] > button:active,
            button[kind="primaryFormSubmit"]:active {
                transform: translateY(0px) !important;
                box-shadow: 0 6px 16px rgba(21, 60, 158, 0.35) !important;
            }

            .login-footer-text {
                position: fixed;
                left: 0;
                right: 0;
                bottom: 18px;
                text-align: center;
                color: #94a3b8;
                font-size: 12px;
                font-weight: 500;
                pointer-events: none;
            }
        </style>
    """, unsafe_allow_html=True)

    logo_full_b64 = get_base64_image("assets/icons/logo_pertamina_full.png")
    if logo_full_b64:
        logo_markup = f'<img src="{logo_full_b64}" alt="Pertamina Digital Hub" />'
    else:
        logo_markup = '<div class="login-brand-fallback">PERTAMINA<span>DIGITAL HUB</span></div>'

    st.markdown(f"""
        <div class="login-topbar">
            <div class="login-brand">{logo_markup}</div>
            <div class="login-header-title">TKB NEWS SENTIMENT ANALYSIS</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="login-center-wrapper">
            <div class="login-icon-box">
                <svg viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                    <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                    <circle cx="12" cy="16" r="1.5" fill="#ffffff"></circle>
                </svg>
            </div>
            <h1 class="login-main-heading">Masuk ke Dashboard</h1>
            <p class="login-sub-heading">Platform analisis sentimen berita Pertamina</p>
        </div>
    """, unsafe_allow_html=True)

    is_anim = st.session_state.get("login_animating", False)

    with st.form("pertamina_login_form"):
        st.markdown('<p class="login-field-label">USERNAME</p>', unsafe_allow_html=True)
        username_input = st.text_input("Username", label_visibility="collapsed", placeholder="Masukkan username")

        st.markdown('<p class="login-field-label">PASSWORD</p>', unsafe_allow_html=True)
        password_input = st.text_input("Password", type="password", label_visibility="collapsed", placeholder="Masukkan password")

        submit_btn = st.form_submit_button("MASUK KE DASHBOARD", use_container_width=True)

    if submit_btn:
        USERS_FILE = "users.csv"
        authenticated = False
        auth_user = ""
        auth_role = ""

        # 1. Cek akun default bawaan
        if username_input == "admin" and password_input == "admin123":
            authenticated = True
            auth_user = "Admin"
            auth_role = "admin"
        elif username_input == "user" and password_input == "user123":
            authenticated = True
            auth_user = "User"
            auth_role = "user"

        # 2. Cek ke file users.csv jika belum cocok
        elif os.path.exists(USERS_FILE):
            try:
                df_u = pd.read_csv(USERS_FILE)
                u_col = next((c for c in ["username", "USERNAME", "user", "USER"] if c in df_u.columns), "username")
                p_col = next((c for c in ["password", "PASSWORD"] if c in df_u.columns), "password")
                r_col = next((c for c in ["role", "ROLE"] if c in df_u.columns), "role")

                matched = df_u[(df_u[u_col].astype(str) == username_input) & (df_u[p_col].astype(str) == password_input)]
                if not matched.empty:
                    authenticated = True
                    auth_user = str(matched.iloc[0][u_col])
                    auth_role = str(matched.iloc[0][r_col]).lower()
            except Exception:
                pass

        if authenticated:
            record_login_history(auth_user, auth_role)
            st.session_state.login_animating = True
            st.session_state.pending_user = auth_user
            st.session_state.pending_role = auth_role
            st.rerun()
        else:
            st.error("Kredensial Salah: Periksa kembali username dan password Anda.")

    if is_anim:
        time.sleep(0.5)
        st.session_state.logged_in = True
        st.session_state.username = st.session_state.pending_user
        st.session_state.user_role = st.session_state.pending_role
        st.query_params["user"] = st.session_state.pending_user
        st.query_params["role"] = st.session_state.pending_role
        st.session_state.login_animating = False
        st.rerun()

    st.markdown('<div class="login-footer-text">© Pertamina Digital Hub</div>', unsafe_allow_html=True)
    st.stop()