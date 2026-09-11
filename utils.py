import base64
import os
import time
import json
import requests
import streamlit as st
import pandas as pd
import numpy as np
from openai import OpenAI
import plotly.graph_objects as go
import streamlit.components.v1 as components

# Color Palette Mappings
color_map_sentiment = {
    'Positive': '#16a34a',
    'Neutral': '#237ece',
    'Negative': '#ea580c'
}


import base64
import streamlit as st

def load_custom_css():
    """CSS Global, background rasi bintang, dan penataan modebar Plotly."""
    
    # SVG Rasi Bintang halus
    svg_constellation = """<svg xmlns="http://www.w3.org/2000/svg" width="450" height="450" viewBox="0 0 450 450">
        <style>
            @keyframes driftA {
                0% { transform: translate(0px, 0px); }
                50% { transform: translate(25px, -18px); }
                100% { transform: translate(0px, 0px); }
            }
            @keyframes driftB {
                0% { transform: translate(0px, 0px); }
                50% { transform: translate(-22px, 20px); }
                100% { transform: translate(0px, 0px); }
            }
            @keyframes twinkle {
                0%, 100% { opacity: 0.12; r: 3px; }
                50% { opacity: 0.32; r: 4px; }
            }
            .const-group1 { animation: driftA 16s ease-in-out infinite; }
            .const-group2 { animation: driftB 20s ease-in-out infinite; }
            .star-node { fill: #237ece; animation: twinkle 4s ease-in-out infinite alternate; }
            .const-line { stroke: #237ece; stroke-width: 0.8; stroke-opacity: 0.10; stroke-dasharray: 4, 3; }
        </style>
        
        <!-- Rasi Bintang Cluster 1 -->
        <g class="const-group1">
            <line x1="60" y1="90" x2="160" y2="150" class="const-line" />
            <line x1="160" y1="150" x2="240" y2="70" class="const-line" />
            <line x1="240" y1="70" x2="340" y2="120" class="const-line" />
            <line x1="160" y1="150" x2="190" y2="220" class="const-line" />
            
            <circle cx="60" cy="90" r="3" class="star-node" />
            <circle cx="160" cy="150" r="3.8" class="star-node" style="animation-delay: 1s;" />
            <circle cx="240" cy="70" r="2.8" class="star-node" style="animation-delay: 2s;" />
            <circle cx="340" cy="120" r="3.5" class="star-node" style="animation-delay: 0.5s;" />
            <circle cx="190" cy="220" r="2.8" class="star-node" style="animation-delay: 1.5s;" />
        </g>

        <!-- Rasi Bintang Cluster 2 -->
        <g class="const-group2">
            <line x1="80" y1="320" x2="180" y2="270" class="const-line" />
            <line x1="180" y1="270" x2="270" y2="360" class="const-line" />
            <line x1="270" y1="360" x2="360" y2="300" class="const-line" />
            
            <circle cx="80" cy="320" r="3.5" class="star-node" style="animation-delay: 2.2s;" />
            <circle cx="180" cy="270" r="2.8" class="star-node" style="animation-delay: 0.8s;" />
            <circle cx="270" cy="360" r="3.8" class="star-node" style="animation-delay: 1.8s;" />
            <circle cx="360" cy="300" r="2.8" class="star-node" style="animation-delay: 2.7s;" />
        </g>
    </svg>"""

    svg_b64 = base64.b64encode(svg_constellation.encode('utf-8')).decode('utf-8')
    bg_data_url = f"data:image/svg+xml;base64,{svg_b64}"

    st.markdown(f"""
    <style>
        .stApp, [data-testid="stAppViewContainer"] {{
            min-height: 100vh !important;
            background-color: #f8fafc !important;
            background-image: url('{bg_data_url}') !important;
            background-repeat: repeat !important;
            background-attachment: scroll !important;
            background-size: 450px 450px !important;
        }}

        div.block-container {{
            padding-top: 1rem !important;
            padding-bottom: 2rem !important;
            max-width: 98% !important;
            position: relative !important;
            z-index: 2 !important;
        }}

        [data-testid="stHeader"] {{
            background: transparent !important;
            height: 1.5rem !important;
        }}

        .user-mgr-card,
        .admin-noborder-card,
        .metric-pill-card-noborder,
        div[data-testid="stForm"],
        div[data-testid="stDataFrame"],
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background-color: #ffffff !important;
            position: relative !important;
            z-index: 3 !important;
        }}

        div[data-testid="stMarkdownContainer"],
        p, span, label, h1, h2, h3, h4, h5, h6 {{
            background: transparent !important;
            background-color: transparent !important;
        }}

        /* Beri jarak tombol toolbar Plotly agar tidak menempel rapat pada chart */
        .js-plotly-plot .plotly .modebar-container {{
            top: -10px !important;
            right: 8px !important;
            padding: 2px 4px !important;
        }}

        .js-plotly-plot .plotly .modebar-btn {{
            padding: 2px 3px !important;
            margin-left: 2px !important;
        }}
    </style>
    """, unsafe_allow_html=True)

def get_base64_image(image_path):
    """Membaca file gambar lokal dengan pencarian aman."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    possible_paths = [
        image_path,
        os.path.join(base_dir, image_path),
        os.path.join(base_dir, "..", image_path),
        os.path.join(base_dir, os.path.basename(image_path)),
    ]

    target_path = None
    for p in possible_paths:
        if os.path.exists(p) and os.path.isfile(p):
            target_path = p
            break

    if not target_path:
        return ""

    ext = os.path.splitext(target_path)[1].lower()
    mime_type = "image/jpeg" if ext in [".jpg", ".jpeg"] else "image/png"

    try:
        with open(target_path, "rb") as img_file:
            encoded = base64.b64encode(img_file.read()).decode()
            return f"data:{mime_type};base64,{encoded}"
    except Exception:
        return ""

def standardize_sentiment_en(val):
    """
    Menyeragamkan berbagai variasi sentiment menjadi:
    Positive, Negative, atau Neutral.
    """

    if pd.isna(val):
        return "Neutral"

    s = str(val).strip().lower()

    # Hilangkan spasi/karakter yang tidak diperlukan
    s = s.replace("_", " ").replace("-", " ").strip()

    # POSITIVE
    positive_values = {
        "positive",
        "positif",
        "pos",
        "good",
        "baik",
        "1",
        "+1",
        "1.0"
    }

    # NEGATIVE
    negative_values = {
        "negative",
        "negatif",
        "neg",
        "bad",
        "buruk",
        "-1",
        "-1.0"
    }

    # NEUTRAL
    neutral_values = {
        "neutral",
        "netral",
        "neu",
        "net",
        "0",
        "0.0"
    }

    if s in positive_values:
        return "Positive"

    if s in negative_values:
        return "Negative"

    if s in neutral_values:
        return "Neutral"

    # Fallback untuk tulisan yang mengandung keyword
    if "posit" in s or "positive" in s or "baik" in s:
        return "Positive"

    if "negat" in s or "negative" in s or "buruk" in s:
        return "Negative"

    if "neutral" in s or "netral" in s or "neu" in s:
        return "Neutral"

    # Jika tidak dikenali → Neutral
    return "Neutral"

def apply_clean_white_layout(fig, height=280):
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=25, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#334155", size=11, family="sans-serif"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig.update_xaxes(showgrid=True, gridcolor="#f1f5f9", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#f1f5f9", zeroline=False)
    return fig

def check_login():
    if not st.session_state.get("logged_in", False):
        user_param = st.query_params.get("user")
        role_param = st.query_params.get("role")
        if user_param and role_param:
            st.session_state.logged_in = True
            st.session_state.username = user_param
            st.session_state.user_role = role_param

    if "login_animating" not in st.session_state:
        st.session_state.login_animating = False

    if not st.session_state.get("logged_in", False):
        st.markdown("""
            <style>
                [data-testid="stSidebar"] { display: none !important; }
                header[data-testid="stHeader"] { display: none !important; }
                .block-container { padding: 2.5rem 3.5rem 2rem 3.5rem !important; max-width: 100% !important; }
                div[data-testid="stForm"] { border: none !important; padding: 0 !important; }
                button[kind="primaryFormSubmit"] {
                    background: #237ece !important; color: #ffffff !important; border-radius: 8px !important;
                    font-weight: 700 !important; font-size: 0.85rem !important; letter-spacing: 0.04em !important;
                    border: none !important; height: 42px !important; margin-top: 10px !important;
                }
                button[kind="primaryFormSubmit"]:hover { background: #1b63a5 !important; }
                .login-credit-footer { position: fixed; bottom: 20px; left: 3.5rem; color: #94a3b8; font-size: 0.8rem; font-weight: 600; pointer-events: none; }
            </style>
        """, unsafe_allow_html=True)

        logo_full_b64 = get_base64_image("assets/icons/logo_pertamina_full.png")
        if logo_full_b64:
            st.markdown(f"""
                <div style="display: flex; align-items: center; margin-bottom: 28px;">
                    <img src="{logo_full_b64}" alt="Pertamina Digital Hub" style="height: 38px; width: auto; object-fit: contain;" />
                </div>
            """, unsafe_allow_html=True)

        _, col_main, _ = st.columns([1, 2.6, 1])

        with col_main:
            st.markdown("""
                <h3 style="color: #0f172a; font-weight: 800; font-size: 1.2rem; letter-spacing: 0.02em; margin: 0 0 20px 0; text-transform: uppercase;">
                    LOGIN KE TKB NEWS SENTIMENT ANALYSIS
                </h3>
            """, unsafe_allow_html=True)

            is_anim = st.session_state.get("login_animating", False)
            col_l, col_r = st.columns([1, 1.2], gap="large")

            with col_l:
                if not is_anim:
                    st.markdown("""
                        <div style="height: 100%; min-height: 220px; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                            <div style="background: #f8fafc; border: 1.5px solid #e2e8f0; border-radius: 12px; padding: 22px; display: flex; align-items: center; justify-content: center;">
                                <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="#237ece" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                                    <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                                    <circle cx="12" cy="16" r="1.5" fill="#237ece"></circle>
                                </svg>
                            </div>
                            <span style="font-size: 0.72rem; font-weight: 700; color: #64748b; margin-top: 14px;">SECURE LOGIN ACCESS</span>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                        <div style="height: 100%; min-height: 220px; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                            <div style="background: #f0fdf4; border: 1.5px solid #bbf7d0; border-radius: 12px; padding: 22px; display: flex; align-items: center; justify-content: center;">
                                <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                                    <path d="M7 11V7a5 5 0 0 1 9.9-1"></path>
                                    <circle cx="12" cy="16" r="1.5" fill="#16a34a"></circle>
                                </svg>
                            </div>
                            <span style="font-size: 0.75rem; font-weight: 800; color: #16a34a; margin-top: 14px;">ACCESS GRANTED</span>
                        </div>
                    """, unsafe_allow_html=True)

            with col_r:
                with st.form("pertamina_login_form"):
                    st.markdown("<p style='font-size: 0.74rem; font-weight: 700; color: #475569; margin: 0 0 4px 0;'>USERNAME</p>", unsafe_allow_html=True)
                    username_input = st.text_input("Username", label_visibility="collapsed", placeholder="Ketik username...")
                    st.markdown("<p style='font-size: 0.74rem; font-weight: 700; color: #475569; margin: 10px 0 4px 0;'>PASSWORD</p>", unsafe_allow_html=True)
                    password_input = st.text_input("Password", type="password", label_visibility="collapsed", placeholder="Ketik password...")
                    st.write("")
                    submit_btn = st.form_submit_button("MASUK KE DASHBOARD", use_container_width=True)

            if submit_btn:
                if (username_input == "admin" and password_input == "admin123") or (username_input == "user" and password_input == "user123"):
                    st.session_state.login_animating = True
                    st.session_state.pending_user = "Admin" if username_input == "admin" else "Viewer"
                    st.session_state.pending_role = "admin" if username_input == "admin" else "viewer"
                    st.rerun()
                else:
                    st.error("Kredensial Salah: Periksa kembali username dan password Anda.")

            if is_anim:
                time.sleep(1.0)
                st.session_state.logged_in = True
                st.session_state.username = st.session_state.pending_user
                st.session_state.user_role = st.session_state.pending_role
                st.query_params["user"] = st.session_state.pending_user
                st.query_params["role"] = st.session_state.pending_role
                st.session_state.login_animating = False
                st.rerun()

        st.markdown("""<div class="login-credit-footer">© Pertamina Digital Hub</div>""", unsafe_allow_html=True)
        st.stop()

@st.cache_data
def load_local_dataset():
    """Memuat dataset lokal dan menyelaraskan kolom baru secara dinamis."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    candidate_files = [
        "tkb_news.xlsx",
        "data.xlsx",
        "dataset.xlsx",
        "data.csv",
        "dataset.csv"
    ]
    
    file_found = None
    for f in candidate_files:
        p = os.path.join(current_dir, f)
        if os.path.exists(p):
            file_found = p
            break
            
    if file_found:
        try:
            if file_found.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file_found)
            else:
                try:
                    df = pd.read_csv(file_found, low_memory=False)
                except Exception:
                    df = pd.read_csv(file_found, sep=';', low_memory=False)
            
            # Format seluruh nama kolom ke UPPERCASE
            df.columns = [str(c).strip().upper() for c in df.columns]
            
            # 1. Parsing Tanggal Berita
            if "NEWS_DATE" in df.columns:
                df["NEWS_DATE"] = pd.to_datetime(df["NEWS_DATE"], errors="coerce")
            
            # ============================================================
            # 2. STANDARDISASI TOPIC
            #    Sumber utama WAJIB: ISSUE_TOPIC
            # ============================================================

            if "ISSUE_TOPIC" in df.columns:
                df["ISSUE_TOPIC"] = (
                    df["ISSUE_TOPIC"]
                    .fillna("General")
                    .astype(str)
                    .str.strip()
                )
            else:
                # Jika kolom wajib tidak ada, buat agar dashboard tidak crash
                df["ISSUE_TOPIC"] = "General"


            # ============================================================
            # 3. STANDARDISASI SUBTOPIC
            #    Sumber utama WAJIB: ISSUE_SUBTOPIC
            # ============================================================

            if "ISSUE_SUBTOPIC" in df.columns:
                df["ISSUE_SUBTOPIC"] = (
                    df["ISSUE_SUBTOPIC"]
                    .fillna("General")
                    .astype(str)
                    .str.strip()
                )
            else:
                # Jika kolom tidak ada, buat default
                df["ISSUE_SUBTOPIC"] = "General"


            # ============================================================
            # 4. STANDARDISASI SENTIMENT
            # ============================================================

            if "SENTIMENT" in df.columns:
                df["SENTIMENT"] = df["SENTIMENT"].apply(standardize_sentiment_en)
            else:
                df["SENTIMENT"] = "Neutral"

            # 4. Standardisasi Sentimen
            if "SENTIMENT" in df.columns:
                df["SENTIMENT"] = df["SENTIMENT"].apply(standardize_sentiment_en)

            # 5. Standardisasi TIER
            if "TIER" in df.columns:
                df["TIER"] = df["TIER"].fillna(2).astype(str).apply(
                    lambda x: f"Tier {x}" if not str(x).lower().startswith("tier") else str(x)
                )

            # 6. Pembersihan Media / URL
            if "CLEAN_URL" in df.columns:
                df["CLEAN_URL"] = df["CLEAN_URL"].fillna("Media").astype(str).str.strip()
            elif "NEWS_URL" in df.columns:
                df["CLEAN_URL"] = df["NEWS_URL"].astype(str).str.replace(r'^https?://(www\.)?', '', regex=True).str.split('/').str[0]

            return df, os.path.basename(file_found)
        except Exception as e:
            st.error(f"Gagal membaca dataset {file_found}: {e}")
            return pd.DataFrame(), None

    return pd.DataFrame(), None

def apply_page_filters(df, filter_state):
    """Menyaring DataFrame menggunakan kolom canonical dataset."""

    if not filter_state or df is None or df.empty:
        return df

    df_out = df.copy()

    d_range = filter_state.get("date_range")

    if (
        d_range
        and isinstance(d_range, (tuple, list))
        and len(d_range) == 2
    ):
        s_d, e_d = d_range

        if "NEWS_DATE" in df_out.columns and s_d and e_d:
            df_out = df_out[
                (df_out["NEWS_DATE"].dt.date >= s_d)
                & (df_out["NEWS_DATE"].dt.date <= e_d)
            ]

    mapping = [
        ("sentiment", "SENTIMENT"),
        ("tier", "TIER"),
        ("topic", "ISSUE_TOPIC"),
        ("subtopic", "ISSUE_SUBTOPIC"),
        ("domain", "CLEAN_URL")
    ]

    for key, col_name in mapping:
        vals = filter_state.get(key, [])

        if vals and col_name in df_out.columns:
            df_out = df_out[
                df_out[col_name].astype(str).isin(vals)
            ]

    return df_out

def analyze_negative_peak(df):
    if df.empty or "SENTIMENT" not in df.columns or "NEWS_DATE" not in df.columns:
        return None
    df_neg = df[(df["SENTIMENT"] == "Negative") & (df["NEWS_DATE"].notna())].copy()
    if df_neg.empty:
        return None
    df_neg_daily = df_neg.groupby(df_neg["NEWS_DATE"].dt.date).size().reset_index(name="count")
    df_neg_daily = df_neg_daily.sort_values(by="NEWS_DATE")
    peak_row = df_neg_daily.sort_values(by="count", ascending=False).iloc[0]
    peak_date = peak_row["NEWS_DATE"]
    peak_count = peak_row["count"]
    df_peak_news = df_neg[df_neg["NEWS_DATE"].dt.date == peak_date]
    
    top_cause_topic = df_peak_news["ISSUE_TOPIC"].mode()[0] if "ISSUE_TOPIC" in df_peak_news.columns and not df_peak_news["ISSUE_TOPIC"].empty else "-"
    top_cause_subtopic = df_peak_news["SUBCATEGORY"].mode()[0] if "SUBCATEGORY" in df_peak_news.columns and not df_peak_news["SUBCATEGORY"].empty else "-"
    
    return {
        "peak_date": peak_date.strftime('%d %B %Y'),
        "peak_date_raw": peak_date,
        "peak_count": peak_count,
        "cause_topic": top_cause_topic,
        "cause_subtopic": top_cause_subtopic,
        "peak_articles": df_peak_news,
        "daily_trend": df_neg_daily
    }

def generate_peak_crisis_summary(df_peak_articles):
    if df_peak_articles.empty:
        return "Tidak ada data artikel yang cukup untuk diringkas."
    
    api_key = None
    try:
        if "OPENROUTER_API_KEY" in st.secrets:
            api_key = st.secrets["OPENROUTER_API_KEY"]
        elif "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
        
    if not api_key:
        api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("GOOGLE_API_KEY")
        
    if not api_key:
        sub_val = df_peak_articles["SUBCATEGORY"].mode()[0] if "SUBCATEGORY" in df_peak_articles.columns else "General"
        return f"<b>Akar Masalah:</b> Terjadi akumulasi isu negatif terkait subtopik <b>{sub_val}</b>.<br><br><b>Peringatan:</b> Diperlukan klarifikasi proaktif pada media Tier 1."
    
    try:
        client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
        summary_col = "NEWS_SUMMARY" if "NEWS_SUMMARY" in df_peak_articles.columns else ("NEWS" if "NEWS" in df_peak_articles.columns else "CLEAN_URL")
        combined_texts = " - ".join(df_peak_articles[summary_col].dropna().astype(str).tolist()[:8])
        prompt = (
            "Bertindaklah sebagai analis PR. Berdasarkan ringkasan berita negatif berikut, "
            "buatkan ringkasan super singkat dalam 2 paragraf terpisah tanpa nomor atau bullet point. "
            "Gunakan tag HTML <b>Akar Masalah:</b> di awal paragraf pertama dan <b>Peringatan:</b> di awal paragraf kedua:\n\n" + combined_texts
        )
        response = client.chat.completions.create(
            model="microsoft/phi-4",
            messages=[
                {"role": "system", "content": "Anda adalah asisten AI PR yang menghasilkan paragraf bersih bertag HTML <b>."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Gagal menghasilkan ringkasan AI: {str(e)}"