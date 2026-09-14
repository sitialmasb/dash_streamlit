import streamlit as st
import pandas as pd
import numpy as np
import re
import ast
import textwrap
import html
import plotly.graph_objects as go
from datetime import datetime

def render_deepdive_page(df_raw: pd.DataFrame):
    # Initialize navigation state before it is accessed.
    if "deepdive_selected_topic" not in st.session_state:
        st.session_state.deepdive_selected_topic = None

    if df_raw is None or df_raw.empty:
        st.info("Data tidak tersedia.")
        return

    df_clean = df_raw.copy()
    if "NEWS_DATE" in df_clean.columns:
        df_clean["NEWS_DATE"] = pd.to_datetime(df_clean["NEWS_DATE"], errors="coerce")
    elif "news_date" in df_clean.columns:
        df_clean["NEWS_DATE"] = pd.to_datetime(df_clean["news_date"], errors="coerce")

    # Standardisasi nama-nama kolom dataset
    # ============================================================
    # CANONICAL DATASET COLUMNS
    # ============================================================

    topic_col = (
        "ISSUE_TOPIC"
        if "ISSUE_TOPIC" in df_clean.columns
        else None
    )

    subtopic_col = (
        "SUBCATEGORY"
        if "SUBCATEGORY" in df_clean.columns
        else None
    )

    sent_col = (
        "SENTIMENT"
        if "SENTIMENT" in df_clean.columns
        else None
    )

    tier_col = (
        "TIER"
        if "TIER" in df_clean.columns
        else None
    )
    media_col = next((c for c in ["CLEAN_URL", "MEDIA", "media", "SOURCE", "source", "MEDIA_DOMAIN"] if c in df_clean.columns), None)
    title_col = next((c for c in ["NEWS", "NEWS_SUMMARY", "title", "headline"] if c in df_clean.columns), None)
    # Category and subcategory columns used by the NEWS ARTICLES section.
    category_col = "NEWS_CATEGORY" if "NEWS_CATEGORY" in df_clean.columns else None
    subcategory_col = "SUBCATEGORY" if "SUBCATEGORY" in df_clean.columns else None


    # Detail metadata for each article in Topic Deep Dive.
    location_col = next((
        c for c in [
            "LOCATION", "location", "LOCATIONS", "WILAYAH", "wilayah",
            "PROVINSI", "provinsi", "PROVINCE", "province",
            "REGION", "region"
        ] if c in df_clean.columns
    ), None)

    subsidiary_col = next((
        c for c in [
            "SUBSIDIARY", "subsidiary", "ANAK_PERUSAHAAN",
            "ANAK PERUSAHAAN", "anak_perusahaan", "COMPANY",
            "company", "PERUSAHAAN", "perusahaan"
        ] if c in df_clean.columns
    ), None)
    
    # NEWS_CATEGORY is the platform name from the dataset.
    platform_col = "NEWS_CATEGORY" if "NEWS_CATEGORY" in df_clean.columns else None

    # Deteksi kolom provinsi / region
    prov_col = next((c for c in ["PROVINSI", "provinsi", "PROVINCE", "province", "REGION", "region", "WILAYAH", "wilayah"] if c in df_clean.columns), None)


    # Scoped Clean Styling
    st.markdown("""
        <style>
            .dd-card {
                background: #ffffff;
                border-radius: 12px;
                padding: 16px 18px;
                box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04);
                border: 1px solid #eef2f6;
                margin-bottom: 14px;
            }
            .dd-label {
                font-size: 0.74rem;
                font-weight: 800;
                color: #475569;
                letter-spacing: 0.05em;
                text-transform: uppercase;
                margin-bottom: 3px;
                display: block;
            }
            .dd-sublabel {
                font-size: 0.68rem;
                color: #94a3b8;
                margin-bottom: 8px;
                display: block;
            }
            .kpi-pill-box {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px 16px;
                display: flex;
                flex-direction: column;
                min-width: 140px;
            }
            .dd-module-title {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
                font-size: 0.76rem !important;
                font-weight: 800 !important;
                color: #475569 !important;
                letter-spacing: 0.05em !important;
                text-transform: uppercase !important;
                margin-bottom: 8px !important;
            }
            div[data-testid="stVerticalBlockBorderWrapper"] {
                background: #ffffff !important;
                border-radius: 12px !important;
                border: 1px solid #e2e8f0 !important;
                box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04) !important;
                padding: 10px 4px !important;
            }

            /* PAKSA LATAR BELAKANG PLOTLY MENJADI ABU SOLID (#f8fafc) */
            div[data-testid="stPlotlyChart"],
            div[data-testid="stPlotlyChart"] > div,
            .js-plotly-plot,
            .plot-container {
                background-color: #f8fafc !important;
                border-radius: 8px !important;
            }
            .js-plotly-plot .main-svg:first-child,
            .js-plotly-plot .main-svg:first-child rect.bg {
                fill: #f8fafc !important;
            }

            div[data-testid="stColumn"] div.stButton > button {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
                font-size: 0.70rem !important;
                font-weight: 700 !important;
                letter-spacing: -0.01em !important;
                padding: 2px 0px !important;
                min-height: 28px !important;
                height: 28px !important;
                margin-top: 4px !important;
                background: #f8fafc !important;
                border: 1px solid #e2e8f0 !important;
                border-radius: 6px !important;
                color: #0f172a !important;
                white-space: nowrap !important;
                word-break: keep-all !important;
            }
            div[data-testid="stColumn"] div.stButton > button p {
                font-family: inherit !important;
                font-size: 0.70rem !important;
                font-weight: 700 !important;
                margin: 0 !important;
                padding: 0 !important;
                white-space: nowrap !important;
                word-break: keep-all !important;
                overflow: hidden !important;
                text-overflow: ellipsis !important;
            }
            div[data-testid="stColumn"] div.stButton > button:hover {
                background: #eff6ff !important;
                border-color: #3b82f6 !important;
            }
            div[data-testid="stColumn"] div.stButton > button:hover p {
                color: #1d4ed8 !important;
            }
            .dd-vol-text {
                font-family: "SFMono-Regular", Consolas, Menlo, monospace !important;
                font-size: 0.70rem !important;
                font-weight: 700 !important;
                margin-bottom: 2px !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # =========================================================================
    # KONDISI 1: MAIN PAGE (TOPIC DEEP DIVE)
    # =========================================================================
    if st.session_state.deepdive_selected_topic is None:
        c_title, c_f_date, c_f_tier, c_f_reg = st.columns([2.6, 1.4, 1.0, 1.2], gap="medium")
        with c_title:
            st.markdown("""
                <div style="display: flex; align-items: center; gap: 12px; height: 100%; min-height: 48px;">
                    <div style="width: 8px; height: 48px; background: linear-gradient(180deg, #38bdf8 0%, #237ece 100%); border-radius: 4px; flex-shrink: 0;"></div>
                    <div style="display: flex; flex-direction: column; justify-content: center;">
                        <h2 style="margin: 0 0 1px 0; padding: 0; font-size: 2rem; line-height: 1.25; color: #0f172a; font-weight: 800; letter-spacing: -0.01em;">
                            TOPIC DEEP <span style="color: #237ece; font-style: italic;">DIVE</span>
                        </h2>
                        <span style="margin: 0; padding: 0; font-size: 0.70rem; line-height: 1.1; letter-spacing: 0.08em; color: #64748b; font-weight: 700; text-transform: uppercase;">
                            SUBTOPIC TREND MONITORING & TOPIC EXPLORATION
                        </span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # Filter 1: Tanggal
        with c_f_date:
            if "NEWS_DATE" in df_clean.columns and not df_clean["NEWS_DATE"].dropna().empty:
                min_d = df_clean["NEWS_DATE"].min().date()
                max_d = df_clean["NEWS_DATE"].max().date()
            else:
                min_d, max_d = datetime(2023, 1, 1).date(), datetime.now().date()
            
            sel_date_range = st.date_input(
                "Filter Date Range",
                value=(min_d, max_d),
                min_value=min_d,
                max_value=max_d,
                label_visibility="collapsed",
                key="dd_filter_date_range"
            )

        # Filter 2: Media Tier
        with c_f_tier:
            tier_opts = ["All Media Tier"] + sorted(list(df_clean[tier_col].dropna().astype(str).unique())) if tier_col else ["All Media Tier"]
            sel_tier = st.selectbox("Tier", options=tier_opts, index=0, label_visibility="collapsed", key="dd_filter_tier")

        # Filter 3: Region
        with c_f_reg:
            if prov_col and not df_clean[prov_col].dropna().empty:
                prov_list = sorted([str(p).strip() for p in df_clean[prov_col].dropna().unique() if str(p).strip() != ""])
                reg_opts = ["All Region"] + prov_list
            else:
                reg_opts = ["All Region"]
            sel_reg = st.selectbox("Region", options=reg_opts, index=0, label_visibility="collapsed", key="dd_filter_reg")

        st.markdown("<div style='margin-bottom: 22px;'></div>", unsafe_allow_html=True)

        # Filter Data
        df_dd = df_clean.copy()

        if "NEWS_DATE" in df_dd.columns and isinstance(sel_date_range, (tuple, list)) and len(sel_date_range) == 2:
            start_d, end_d = sel_date_range
            df_dd = df_dd[(df_dd["NEWS_DATE"].dt.date >= start_d) & (df_dd["NEWS_DATE"].dt.date <= end_d)]
        elif "NEWS_DATE" in df_dd.columns and isinstance(sel_date_range, (tuple, list)) and len(sel_date_range) == 1:
            df_dd = df_dd[df_dd["NEWS_DATE"].dt.date >= sel_date_range[0]]

        if sel_tier != "All Media Tier" and tier_col:
            df_dd = df_dd[df_dd[tier_col].astype(str) == sel_tier]

        if sel_reg != "All Region" and prov_col:
            df_dd = df_dd[df_dd[prov_col].astype(str).str.strip() == sel_reg]

        col_charts, col_widgets = st.columns([1.60, 1.50], gap="medium")

        # ----------------- KIRI: GRAFIK TOPIC TREND OVER TIME -----------------
        with col_charts:
            # Teks spike detection telah dihapus
            st.markdown("""
                <div style="margin-bottom: 4px;">
                    <span class="dd-label">TOPIC TREND OVER TIME & ARTICLE VOLUME</span>
                    <span class="dd-sublabel">Tren Volume Berita untuk Seluruh Kategori (NEWS_CATEGORY)</span>
                </div>
            """, unsafe_allow_html=True)

            trend_df = pd.DataFrame()
            if "NEWS_DATE" in df_dd.columns and topic_col and not df_dd["NEWS_DATE"].dropna().empty:
                df_dd["MONTH_ABBR"] = df_dd["NEWS_DATE"].dt.strftime("%b")
                all_cats_trend = df_dd[topic_col].dropna().unique().tolist()
                df_top_t = df_dd[df_dd[topic_col].isin(all_cats_trend)]
                
                trend_df = df_top_t.groupby(["MONTH_ABBR", topic_col]).size().unstack(fill_value=0)
                
                order_m = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                idx_exist = [m for m in order_m if m in trend_df.index]
                if idx_exist:
                    trend_df = trend_df.reindex(idx_exist)

            if trend_df.empty:
                trend_df = pd.DataFrame({
                    "No Data": [0]
                }, index=["-"])

            color_pool = [
                "#f59e0b", "#10b981", "#ef4444", "#8b5cf6", "#06b6d4", 
                "#ec4899", "#3b82f6", "#14b8a6", "#f97316", "#84cc16", 
                "#6366f1", "#d946ef", "#64748b"
            ]

            fig_line = go.Figure()
            for idx, c_name in enumerate(trend_df.columns):
                c_hex = color_pool[idx % len(color_pool)]
                fig_line.add_trace(go.Scatter(
                    x=trend_df.index,
                    y=trend_df[c_name],
                    mode="lines",
                    name=str(c_name)[:20],
                    line=dict(color=c_hex, width=2.2, shape="spline"),
                    hovertemplate=f"<b>{c_name}</b><br>Bulan: %{{x}}<br>Volume: %{{y}}<extra></extra>"
                ))

            fig_line.update_layout(
                height=460,
                margin=dict(l=0, r=0, t=24, b=35),
                paper_bgcolor="#f8fafc",
                plot_bgcolor="#f8fafc",
                xaxis=dict(showgrid=False, tickfont=dict(size=9.5, color="#94a3b8")),
                yaxis=dict(showgrid=True, gridcolor="rgba(226, 232, 240, 0.9)", tickfont=dict(size=9, color="#94a3b8")),
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.12,
                    xanchor="center",
                    x=0.5,
                    font=dict(size=8.5)
                )
            )
            st.plotly_chart(
                fig_line, 
                use_container_width=True, 
                config={
                    "displayModeBar": True,
                    "modeBarButtons": [["zoom2d", "pan2d", "resetScale2d"]],
                    "displaylogo": False
                }
            )

        # ----------------- KANAN: TOPIC ANALYSIS MODULE -----------------
        with col_widgets:
            st.markdown('<div class="dd-module-title">TOPIC ANALYSIS MODULE</div>', unsafe_allow_html=True)

            topic_cards = []
            if topic_col and not df_dd[topic_col].dropna().empty:
                top_cats = df_dd[topic_col].dropna().value_counts().head(9)
                for idx, (cat_name, vol_cnt) in enumerate(top_cats.items()):
                    df_c = df_dd[df_dd[topic_col] == cat_name]
                    
                    p_c, neu_c, neg_c = 0, 0, 0
                    if sent_col and not df_c[sent_col].dropna().empty:
                        s_series = df_c[sent_col].astype(str).str.lower()
                        p_c = len(s_series[s_series.str.contains("pos")])
                        neg_c = len(s_series[s_series.str.contains("neg")])
                        neu_c = max(0, vol_cnt - (p_c + neg_c))

                        if p_c >= neg_c and p_c >= neu_c:
                            sent_label, c_hex, bg_hex = "Positive", "#15803d", "#dcfce7"
                        elif neg_c >= p_c and neg_c >= neu_c:
                            sent_label, c_hex, bg_hex = "Negative", "#dc2626", "#fee2e2"
                        else:
                            sent_label, c_hex, bg_hex = "Neutral", "#64748b", "#f1f5f9"
                    else:
                        sent_label, c_hex, bg_hex = "Neutral", "#64748b", "#f1f5f9"
                        neu_c = vol_cnt

                    vol_fmt = f"{vol_cnt/1000:.1f}K" if vol_cnt >= 1000 else str(vol_cnt)
                    topic_cards.append({
                        "id": f"top_{idx}",
                        "name": str(cat_name),
                        "vol": vol_fmt,
                        "vol_raw": vol_cnt,
                        "sent": sent_label,
                        "color": c_hex,
                        "bg": bg_hex,
                        "pos_cnt": p_c,
                        "neu_cnt": neu_c,
                        "neg_cnt": neg_c
                    })

            if not topic_cards:
                st.info("Tidak ada data topik yang sesuai dengan filter yang dipilih.")
            else:
                num_cards = len(topic_cards)
                for row_i in range(0, num_cards, 3):
                    row_items = topic_cards[row_i:row_i + 3]
                    cols = st.columns(3, gap="small")
                    for j, t in enumerate(row_items):
                        with cols[j]:
                            with st.container(border=True):
                                tot_v = max(1, t["pos_cnt"] + t["neu_cnt"] + t["neg_cnt"])
                                c_circum = 100.53
                                s_pos = ((t["pos_cnt"] / tot_v) * 100 / 100) * c_circum
                                s_neu = ((t["neu_cnt"] / tot_v) * 100 / 100) * c_circum
                                s_neg = ((t["neg_cnt"] / tot_v) * 100 / 100) * c_circum
                                o_neu = -s_pos
                                o_neg = -(s_pos + s_neu)

                                st.markdown(f"""
                                    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center;">
                                        <svg width="42" height="42" viewBox="0 0 38 38" style="transform: rotate(-90deg); margin-bottom: 4px;">
                                            <circle cx="19" cy="19" r="16" fill="none" stroke="#f1f5f9" stroke-width="4.2"></circle>
                                            <circle cx="19" cy="19" r="16" fill="none" stroke="#10b981" stroke-width="4.2" stroke-dasharray="{s_pos} {c_circum}" stroke-dashoffset="0"></circle>
                                            <circle cx="19" cy="19" r="16" fill="none" stroke="#94a3b8" stroke-width="4.2" stroke-dasharray="{s_neu} {c_circum}" stroke-dashoffset="{o_neu}"></circle>
                                            <circle cx="19" cy="19" r="16" fill="none" stroke="#ef4444" stroke-width="4.2" stroke-dasharray="{s_neg} {c_circum}" stroke-dashoffset="{o_neg}"></circle>
                                        </svg>
                                        <span class="dd-vol-text" style="color: {t['color']};">
                                            Vol {t['vol']}
                                        </span>
                                    </div>
                                """, unsafe_allow_html=True)

                                if st.button(t['name'], key=f"btn_nav_{t['id']}", help=t['name'], use_container_width=True):
                                    st.session_state.deepdive_selected_topic = t
                                    st.rerun()

                st.markdown("<p style='font-size:0.68rem; color:#94a3b8; text-align:center; margin-top:8px;'>Klik tombol topik untuk membuka detail subtopik</p>", unsafe_allow_html=True)

    # =========================================================================
    # KONDISI 2: SUB-PAGE (TOPIC WIDGET SUB-PAGE & DEEP DIVE MODULE)
    # =========================================================================
    else:
        sel_t = st.session_state.deepdive_selected_topic

        c_sub_title, c_back, c_sub_tier = st.columns([3.2, 0.9, 1.1], gap="medium")
        with c_sub_title:
            st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 12px; height: 100%; min-height: 48px;">
                    <div style="width: 8px; height: 48px; background: linear-gradient(180deg, {sel_t['color']}88 0%, {sel_t['color']} 100%); border-radius: 4px; flex-shrink: 0;"></div>
                    <div style="display: flex; flex-direction: column; justify-content: center;">
                        <h2 style="margin: 0 0 1px 0; padding: 0; font-size: 1.85rem; line-height: 1.25; color: #0f172a; font-weight: 800; letter-spacing: -0.01em;">
                            TOPIC INVESTIGATION: <span style="color: {sel_t['color']}; font-style: italic;">{sel_t['name'].upper()}</span>
                        </h2>
                        <span style="margin: 0; padding: 0; font-size: 0.70rem; line-height: 1.1; letter-spacing: 0.08em; color: #64748b; font-weight: 700; text-transform: uppercase;">
                            GRANULAR SUBCATEGORY BREAKDOWN, MEDIA DOMAIN & CRITICAL ISSUES
                        </span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with c_back:
            if st.button("← Back to Topics", key="btn_back_deepdive", use_container_width=True):
                st.session_state.deepdive_selected_topic = None
                st.rerun()
        with c_sub_tier:
            sub_tier_opts = ["All Media Tier"] + sorted(list(df_clean[tier_col].dropna().astype(str).unique())) if tier_col else ["All Media Tier"]
            sel_sub_tier = st.selectbox("Media Tier", options=sub_tier_opts, index=0, label_visibility="collapsed", key="sub_tier_sel")

        st.markdown("<div style='margin-bottom: 22px;'></div>", unsafe_allow_html=True)

        df_sub_topic = df_clean[df_clean[topic_col] == sel_t['name']].copy() if topic_col else df_clean.copy()
        if sel_sub_tier != "All Media Tier" and tier_col:
            df_sub_topic = df_sub_topic[df_sub_topic[tier_col].astype(str) == sel_sub_tier]

        tot_sub_news = max(1, len(df_sub_topic))

        p_c, neu_c, neg_c = 0, 0, 0
        if sent_col and not df_sub_topic[sent_col].dropna().empty:
            s_series = df_sub_topic[sent_col].astype(str).str.lower()
            p_c = len(s_series[s_series.str.contains("pos")])
            neg_c = len(s_series[s_series.str.contains("neg")])
            neu_c = max(0, len(df_sub_topic) - (p_c + neg_c))

        pos_pct = round((p_c / tot_sub_news) * 100, 1)
        neu_pct = round((neu_c / tot_sub_news) * 100, 1)
        neg_pct = round((neg_c / tot_sub_news) * 100, 1)

        if tier_col and not df_sub_topic[tier_col].dropna().empty:
            s_tier = df_sub_topic[tier_col].astype(str).str.extract(r'(\d+)')[0].fillna('0')
            t_counts = s_tier.value_counts()
        else:
            t_counts = pd.Series()

        t1_cnt = int(t_counts.get("1", 0))
        t2_cnt = int(t_counts.get("2", 0))
        t3_cnt = int(t_counts.get("3", 0))
        t4_cnt = int(t_counts.get("4", 0))
        t5_cnt = int(t_counts.get("5", 0))
        t0_cnt = int(t_counts.get("0", 0))

        def calc_pct(cnt):
            pct = (cnt / tot_sub_news) * 100
            if pct == 0:
                return 0, "0%"
            elif pct < 1:
                return round(pct, 1), f"{pct:.1f}%"
            else:
                return int(round(pct)), f"{int(round(pct))}%"

        t1_pct_val, t1_str = calc_pct(t1_cnt)
        t2_pct_val, t2_str = calc_pct(t2_cnt)
        t3_pct_val, t3_str = calc_pct(t3_cnt)
        t4_pct_val, t4_str = calc_pct(t4_cnt)
        t5_pct_val, t5_str = calc_pct(t5_cnt)
        t0_pct_val, t0_str = calc_pct(t0_cnt)

        domain_rows_html = []
        if media_col and not df_sub_topic[media_col].dropna().empty:
            s_domains = df_sub_topic[media_col].dropna().astype(str).str.strip()
            s_domains = s_domains.str.replace("https://", "", regex=False)\
                                 .str.replace("http://", "", regex=False)\
                                 .str.replace("www.", "", regex=False)\
                                 .str.split("/").str[0]
            
            top_domains = s_domains.value_counts().head(5)
            
            for d_name, d_cnt in top_domains.items():
                pct_val = (d_cnt / tot_sub_news) * 100
                d_str = f"{pct_val:.1f}%" if pct_val < 10 else f"{round(pct_val)}%"
                domain_rows_html.append(f'''<div style="display: flex; align-items: center; justify-content: space-between; font-size: 0.70rem; margin-bottom: 4px;">
<span style="color: #1e293b; font-weight: 600; max-width: 170px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="{d_name}">• {d_name}</span>
<span style="color: #64748b; font-family: monospace; font-weight: 700;">{d_cnt:,} <span style="color: #94a3b8; font-weight: 500;">({d_str})</span></span>
</div>''')
        
        if not domain_rows_html:
            domain_rows_html.append('<div style="font-size: 0.70rem; color: #94a3b8;">Tidak ada data domain.</div>')

        rendered_domains = "".join(domain_rows_html)

        header_card_html = f'''<div class="dd-card">
<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 14px;">
<div style="width: 4px; height: 18px; background: {sel_t['color']}; border-radius: 2px;"></div>
<span style="font-size: 0.82rem; font-weight: 800; color: #1e293b; text-transform: uppercase;">
SELECTED TOPIC: {sel_t['name']}
</span>
</div>
<div style="display: flex; gap: 20px; align-items: flex-start; flex-wrap: wrap;">
<div style="display: flex; flex-direction: column; gap: 8px; flex-shrink: 0; min-width: 280px;">
<div style="display: flex; gap: 10px;">
<div class="kpi-pill-box" style="flex: 1;">
<span style="font-size: 0.68rem; color: #64748b;">Total News Volume</span>
<span style="font-size: 1.15rem; font-weight: 800; color: #0f172a;">{len(df_sub_topic):,}</span>
</div>
<div class="kpi-pill-box" style="flex: 1; background: {sel_t['bg']}; border-color: {sel_t['color']}44;">
    <span style="font-size: 0.68rem; color: {sel_t['color']}; font-weight: 700;">Topic Sentiment</span>
    <span style="font-size: 1.15rem; font-weight: 800; color: {sel_t['color']};">{sel_t['sent']}</span>
</div>
</div>
<div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 6px 10px; display: flex; justify-content: space-between; align-items: center;">
<span style="font-size: 0.68rem; font-weight: 700; color: #10b981;">● Pos {pos_pct:.1f}%</span>
<span style="font-size: 0.68rem; font-weight: 700; color: #64748b;">● Neu {neu_pct:.1f}%</span>
<span style="font-size: 0.68rem; font-weight: 700; color: #ef4444;">● Neg {neg_pct:.1f}%</span>
</div>
</div>

<div style="flex: 1; min-width: 220px; padding: 0 10px; border-left: 1px solid #f1f5f9;">
<div style="display: flex; flex-direction: column; gap: 5px;">
<div style="display:flex; align-items:center; gap:6px; font-size:0.70rem;">
<span style="color:#475569; width:38px;">Tier 1</span>
<div style="flex:1; background:#e2e8f0; height:5px; border-radius:10px;"><div style="width:{t1_pct_val}%; background:#2563eb; height:100%; border-radius:10px;"></div></div>
<span style="color:#64748b; font-family:monospace;">{t1_str}</span>
</div>
<div style="display:flex; align-items:center; gap:6px; font-size:0.70rem;">
<span style="color:#475569; width:38px;">Tier 2</span>
<div style="flex:1; background:#e2e8f0; height:5px; border-radius:10px;"><div style="width:{t2_pct_val}%; background:#10b981; height:100%; border-radius:10px;"></div></div>
<span style="color:#64748b; font-family:monospace;">{t2_str}</span>
</div>
<div style="display:flex; align-items:center; gap:6px; font-size:0.70rem;">
<span style="color:#475569; width:38px;">Tier 3</span>
<div style="flex:1; background:#e2e8f0; height:5px; border-radius:10px;"><div style="width:{t3_pct_val}%; background:#8b5cf6; height:100%; border-radius:10px;"></div></div>
<span style="color:#64748b; font-family:monospace;">{t3_str}</span>
</div>
<div style="display:flex; align-items:center; gap:6px; font-size:0.70rem;">
<span style="color:#475569; width:38px;">Tier 4</span>
<div style="flex:1; background:#e2e8f0; height:5px; border-radius:10px;"><div style="width:{t4_pct_val}%; background:#06b6d4; height:100%; border-radius:10px;"></div></div>
<span style="color:#64748b; font-family:monospace;">{t4_str}</span>
</div>
<div style="display:flex; align-items:center; gap:6px; font-size:0.70rem;">
<span style="color:#475569; width:38px;">Tier 5</span>
<div style="flex:1; background:#e2e8f0; height:5px; border-radius:10px;"><div style="width:{t5_pct_val}%; background:#ec4899; height:100%; border-radius:10px;"></div></div>
<span style="color:#64748b; font-family:monospace;">{t5_str}</span>
</div>
<div style="display:flex; align-items:center; gap:6px; font-size:0.70rem;">
<span style="color:#475569; width:38px;">Tier 0</span>
<div style="flex:1; background:#e2e8f0; height:5px; border-radius:10px;"><div style="width:{t0_pct_val}%; background:#f59e0b; height:100%; border-radius:10px;"></div></div>
<span style="color:#64748b; font-family:monospace;">{t0_str}</span>
</div>
</div>
</div>

<div style="flex: 1; min-width: 200px; padding-left: 10px; border-left: 1px solid #f1f5f9;">
<div style="font-size: 0.72rem; font-weight: 700; color: #475569; margin-bottom: 6px;">Top Publishers (CLEAN_URL)</div>
{rendered_domains}
</div>
</div>
</div>'''

        st.markdown(header_card_html, unsafe_allow_html=True)

        sub_right = st.container()

        with sub_right:
            st.markdown(
                '<span class="dd-label" style="margin-bottom: 8px;">TOP KEYWORD</span>',
                unsafe_allow_html=True
            )

            # Always source the keyword from the dataset KEYWORD column.
            keyword_col = next(
                (c for c in ["KEYWORD", "keyword", "KEYWORDS", "keywords"]
                 if c in df_sub_topic.columns),
                None
            )

            top_keywords = []

            keyword_stopwords = {
                "a", "an", "the", "and", "or", "of", "to", "in", "on", "for",
                "with", "from", "by", "at", "is", "are", "as", "be", "this",
                "that", "it", "its", "was", "were", "has", "have", "had",
                "yang", "dan", "atau", "dari", "ke", "di", "untuk", "dengan",
                "pada", "dalam", "ini", "itu", "adalah", "akan", "telah",
                "sebagai", "oleh", "tidak", "juga", "lebih", "terhadap"
            }

            def _extract_keyword_items(value):
                if pd.isna(value):
                    return []

                raw = str(value).strip()
                if not raw or raw.lower() in {"nan", "none", "null"}:
                    return []

                parsed = None
                if raw.startswith("[") and raw.endswith("]"):
                    try:
                        parsed = ast.literal_eval(raw)
                    except (ValueError, SyntaxError):
                        parsed = None

                items = (
                    parsed
                    if isinstance(parsed, (list, tuple, set))
                    else re.split(r"[,;|\n]+", raw)
                )

                result = []
                for item in items:
                    kw = str(item).strip(" []'\"")
                    kw = re.sub(r"\s+", " ", kw).strip()

                    if (
                        not kw
                        or len(kw) < 2
                        or kw.isdigit()
                        or kw.casefold() in keyword_stopwords
                        or not re.search(r"[A-Za-zÀ-ÿ]", kw)
                    ):
                        continue

                    result.append(kw)

                return result

            if keyword_col and not df_sub_topic.empty:
                keyword_items = []

                for value in df_sub_topic[keyword_col].dropna():
                    keyword_items.extend(_extract_keyword_items(value))

                if keyword_items:
                    counts = {}
                    display_names = {}

                    for kw in keyword_items:
                        normalized = kw.casefold()
                        counts[normalized] = counts.get(normalized, 0) + 1
                        display_names.setdefault(normalized, kw)

                    ranked_keywords = sorted(
                        counts.items(), key=lambda item: (-item[1], display_names[item[0]].casefold())
                    )[:3]

                    top_keywords = [
                        (display_names[normalized], count)
                        for normalized, count in ranked_keywords
                    ]

            if not top_keywords:
                top_keywords = [("N/A", 0)]

            keyword_rows = "".join(
                f"""
                <div style="display:flex; align-items:center; gap:12px;
                            padding:11px 0; border-bottom:{'1px solid #e2e8f0' if idx < len(top_keywords)-1 else 'none'};">
                    <div style="min-width:26px; height:26px; border-radius:50%;
                                background:#e2e8f0; color:#475569; display:flex;
                                align-items:center; justify-content:center;
                                font-size:0.72rem; font-weight:800;">
                        {idx + 1}
                    </div>
                    <div style="flex:1; min-width:0; font-size:0.96rem;
                                color:#1e293b; font-weight:800; line-height:1.3;
                                word-break:break-word;">
                        {html.escape(str(keyword))}
                    </div>
                    <div style="font-size:0.67rem; color:#94a3b8; white-space:nowrap;">
                        {count:,} occurrence(s)
                    </div>
                </div>
                """
                for idx, (keyword, count) in enumerate(top_keywords)
            )

            st.html(
                textwrap.dedent(f"""
                    <div style="background:#f8fafc; border:1px solid #e2e8f0;
                                border-radius:10px; padding:12px 16px;">
                        <div style="font-size:0.68rem; color:#64748b;
                                    font-weight:800; text-transform:uppercase;
                                    margin-bottom:2px;">
                            Top 3 Keywords
                        </div>
                        {keyword_rows}
                    </div>
                """).strip()
            )

        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

        c_hdr_art, c_search_art, c_flt_art = st.columns([2.5, 2.3, 1.2], gap="medium")

        with c_hdr_art:
            st.markdown(
                f'<span class="dd-label">NEWS ARTICLES — {sel_t["name"].upper()}</span>',
                unsafe_allow_html=True
            )

        with c_search_art:
            art_search = st.text_input(
                "Search News Articles",
                placeholder="Search keyword or news summary...",
                label_visibility="collapsed",
                key="search_news_articles_dd"
            )

        with c_flt_art:
            art_sent_opts = ["All Sentiment", "Positive", "Neutral", "Negative"]
            sel_art_sent = st.selectbox(
                "Sentiment Filter",
                options=art_sent_opts,
                index=0,
                label_visibility="collapsed",
                key="sel_art_sent_dd"
            )

        # NEWS ARTICLES hanya membutuhkan data yang memiliki NEWS_SUMMARY atau KEYWORD.
        article_required_col = next(
            (c for c in ["NEWS_SUMMARY", "news_summary", "KEYWORD", "keyword"]
             if c in df_sub_topic.columns),
            None
        )
        df_art = (
            df_sub_topic.dropna(subset=[article_required_col]).copy()
            if article_required_col and not df_sub_topic.empty
            else pd.DataFrame()
        )

        if not df_art.empty and sel_art_sent != "All Sentiment" and sent_col:
            df_art = df_art[df_art[sent_col] == sel_art_sent]

        # Search articles by keyword or full news summary.
        if not df_art.empty and art_search.strip():
            search_term = art_search.strip().lower()

            search_cols = [
                c for c in ["KEYWORD", "NEWS_SUMMARY", "NEWS_CATEGORY",
                            "SUBCATEGORY", "LOCATION", "WILAYAH", "PROVINSI"]
                if c in df_art.columns
            ]

            if search_cols:
                search_mask = pd.Series(False, index=df_art.index)
                for col in search_cols:
                    search_mask = search_mask | df_art[col].fillna("").astype(str).str.lower().str.contains(
                        search_term, regex=False
                    )
                df_art = df_art[search_mask]

        if not df_art.empty:
            # Tampilkan hanya delapan berita pertama, diurutkan dari yang paling baru.
            if "NEWS_DATE" in df_art.columns:
                df_art = df_art.sort_values("NEWS_DATE", ascending=False)

            df_art = df_art.head(8)

            link_col = next(
                (
                    c for c in [
                        "URL", "url", "LINK", "link",
                        "NEWS_URL", "news_url", "CLEAN_URL"
                    ]
                    if c in df_art.columns
                ),
                None
            )

            # Satu berita horizontal/full-width per baris.
            for _, row in df_art.iterrows():
                sentiment_value = (
                    str(row.get(sent_col, "Neutral")).strip().capitalize()
                    if sent_col else "Neutral"
                )

                if sentiment_value == "Positive":
                    sentiment_color = "#15803d"
                    sentiment_bg = "#dcfce7"
                elif sentiment_value == "Negative":
                    sentiment_color = "#dc2626"
                    sentiment_bg = "#fee2e2"
                else:
                    sentiment_color = "#64748b"
                    sentiment_bg = "#f1f5f9"

                # KEYWORD menjadi judul utama kartu, bukan NEWS/NEWS_SUMMARY.
                article_keyword = ""
                if keyword_col:
                    raw_keyword = row.get(keyword_col, "")
                    if pd.notna(raw_keyword):
                        article_keyword = str(raw_keyword).strip()

                if not article_keyword or article_keyword.lower() in {"nan", "none", "null"}:
                    article_keyword = "News Article"

                # NEWS_SUMMARY menjadi isi/ringkasan berita.
                summary_col = next(
                    (
                        c for c in [
                            "NEWS_SUMMARY", "news_summary",
                            "SUMMARY", "summary"
                        ]
                        if c in df_art.columns
                    ),
                    None
                )

                article_summary = ""
                if summary_col:
                    raw_summary = row.get(summary_col, "")
                    if pd.notna(raw_summary):
                        article_summary = re.sub(
                            r"[\r\n]+", " ", str(raw_summary)
                        ).strip()

                if not article_summary:
                    article_summary = "No news summary available."

                # Media
                media_name = "Unknown Source"
                if media_col:
                    media_name = str(
                        row.get(media_col, "Unknown Source")
                    ).strip()
                    media_name = re.sub(
                        r"^https?://", "", media_name, flags=re.I
                    ).replace("www.", "").split("/")[0]

                # Date and time
                article_datetime = "-"
                if "NEWS_DATE" in df_art.columns:
                    parsed_date = pd.to_datetime(
                        row.get("NEWS_DATE"), errors="coerce"
                    )
                    if not pd.isna(parsed_date):
                        article_datetime = parsed_date.strftime(
                            "%d %B %Y • %H:%M"
                        )

                # Location
                location_name = "-"
                if location_col:
                    raw_location = row.get(location_col, "")
                    if pd.notna(raw_location):
                        location_name = str(raw_location).strip()
                    if not location_name or location_name.lower() in {
                        "nan", "none", "null"
                    }:
                        location_name = "-"

                # Tier
                tier_value = "-"
                if tier_col:
                    raw_tier = row.get(tier_col, "")
                    if pd.notna(raw_tier):
                        tier_value = str(raw_tier).strip()
                    if not tier_value or tier_value.lower() in {
                        "nan", "none", "null"
                    }:
                        tier_value = "-"

                # Anak perusahaan, jika ada.
                subsidiary_value = ""
                if subsidiary_col:
                    raw_subsidiary = row.get(subsidiary_col, "")
                    if pd.notna(raw_subsidiary):
                        subsidiary_value = str(raw_subsidiary).strip()
                    if subsidiary_value.lower() in {
                        "nan", "none", "null"
                    }:
                        subsidiary_value = ""

                # Category / subcategory langsung dari dataset.
                category_value = "-"
                if category_col:
                    raw_category = row.get(category_col, "")
                    if pd.notna(raw_category):
                        category_value = str(raw_category).strip()
                    if category_value.lower() in {"nan", "none", "null", ""}:
                        category_value = "-"

                subcategory_value = "-"
                if subcategory_col:
                    raw_subcategory = row.get(subcategory_col, "")
                    if pd.notna(raw_subcategory):
                        subcategory_value = str(raw_subcategory).strip()
                    if subcategory_value.lower() in {"nan", "none", "null", ""}:
                        subcategory_value = "-"

                # Article URL
                article_url = ""
                if link_col:
                    raw_url = str(row.get(link_col, "")).strip()
                    if raw_url.lower() not in {"nan", "none", ""}:
                        article_url = raw_url
                        if not article_url.startswith(("http://", "https://")):
                            article_url = "https://" + article_url

                safe_keyword = html.escape(article_keyword)
                safe_summary = html.escape(article_summary)
                platform_value = "-"
                if platform_col:
                    raw_platform = row.get(platform_col, "")
                    if pd.notna(raw_platform):
                        platform_value = str(raw_platform).strip()
                    if platform_value.lower() in {"nan", "none", "null", ""}:
                        platform_value = "-"

                safe_platform = html.escape(platform_value)
                safe_media = html.escape(media_name)
                safe_datetime = html.escape(article_datetime)
                safe_location = html.escape(location_name)
                safe_tier = html.escape(tier_value)
                safe_category = html.escape(category_value)
                safe_subcategory = html.escape(subcategory_value)

                subsidiary_html = ""
                if subsidiary_value:
                    subsidiary_html = f"""
                        <div style="display:flex; flex-direction:column; min-width:145px;">
                            <span style="font-size:0.60rem; color:#94a3b8; font-weight:800; text-transform:uppercase;">
                                Subsidiary
                            </span>
                            <span style="font-size:0.70rem; color:#334155; font-weight:650; margin-top:2px;">
                                {html.escape(subsidiary_value)}
                            </span>
                        </div>
                    """

                link_html = ""
                if article_url:
                    safe_url = html.escape(article_url, quote=True)
                    link_html = f"""
                        <a href="{safe_url}" target="_blank" rel="noopener noreferrer"
                           style="font-size:0.66rem; font-weight:700; color:#237ece; text-decoration:none; white-space:nowrap;">
                            Read Article ↗
                        </a>
                    """

                card_html = f"""
                    <div style="background:#ffffff; border:1px solid #e2e8f0;
                                border-radius:12px; padding:17px 19px; margin-bottom:13px;
                                box-shadow:0 1px 4px rgba(15,23,42,0.05);">

                        <div style="display:flex; align-items:center; justify-content:space-between;
                                    gap:14px; margin-bottom:9px;">
                            <span style="display:inline-block; background:{sentiment_bg};
                                         color:{sentiment_color}; border-radius:999px;
                                         padding:4px 10px; font-size:0.62rem; font-weight:800;">
                                {html.escape(sentiment_value)}
                            </span>

                            <span style="font-size:0.64rem; color:#94a3b8; font-weight:650;">
                                {safe_datetime}
                            </span>
                        </div>

                        <!-- KEYWORD as the article-style heading -->
                        <div style="font-size:1.00rem; line-height:1.38;
                                    font-weight:800; color:#1e3a8a;
                                    margin-bottom:8px;">
                            {safe_keyword}
                        </div>

                        <!-- NEWS_SUMMARY as the article content -->
                        <div style="font-size:0.82rem; line-height:1.62;
                                    font-weight:500; color:#475569;
                                    margin-bottom:13px;
                                    white-space:normal;
                                    display:-webkit-box;
                                    -webkit-box-orient:vertical;
                                    -webkit-line-clamp:12;
                                    overflow:hidden;
                                    max-height:calc(12 * 1.62em);
                                    height:auto;
                                    overflow-wrap:anywhere;
                                    word-break:normal;">
                            {safe_summary}
                        </div>

                        <div style="display:flex; align-items:flex-start; flex-wrap:wrap;
                                    gap:22px; padding-top:11px;
                                    border-top:1px solid #f1f5f9;">

                            <div style="display:flex; flex-direction:column; min-width:125px;">
                                <span style="font-size:0.60rem; color:#94a3b8; font-weight:800; text-transform:uppercase;">
                                    Category
                                </span>
                                <span style="font-size:0.70rem; color:#334155; font-weight:650; margin-top:2px;">
                                    {safe_category}
                                </span>
                            </div>

                            <div style="display:flex; flex-direction:column; min-width:125px;">
                                <span style="font-size:0.60rem; color:#94a3b8; font-weight:800; text-transform:uppercase;">
                                    Subcategory
                                </span>
                                <span style="font-size:0.70rem; color:#334155; font-weight:650; margin-top:2px;">
                                    {safe_subcategory}
                                </span>
                            </div>

                            <div style="display:flex; flex-direction:column; min-width:125px;">
                                <span style="font-size:0.60rem; color:#94a3b8; font-weight:800; text-transform:uppercase;">
                                    Platform
                                </span>
                                <span style="font-size:0.70rem; color:#334155; font-weight:650; margin-top:2px;">
                                    {safe_platform}
                                </span>
                            </div>

                            <div style="display:flex; flex-direction:column; min-width:125px;">
                                <span style="font-size:0.60rem; color:#94a3b8; font-weight:800; text-transform:uppercase;">
                                    Location
                                </span>
                                <span style="font-size:0.70rem; color:#334155; font-weight:650; margin-top:2px;">
                                    {safe_location}
                                </span>
                            </div>

                            <div style="display:flex; flex-direction:column; min-width:90px;">
                                <span style="font-size:0.60rem; color:#94a3b8; font-weight:800; text-transform:uppercase;">
                                    Tier
                                </span>
                                <span style="font-size:0.70rem; color:#334155; font-weight:650; margin-top:2px;">
                                    {safe_tier}
                                </span>
                            </div>

                            {subsidiary_html}

                            <div style="margin-left:auto; align-self:center;">
                                {link_html}
                            </div>
                        </div>
                    </div>
                """

                st.html(textwrap.dedent(card_html).strip())
        else:
            st.info("Tidak ada artikel untuk filter sentimen ini.")

