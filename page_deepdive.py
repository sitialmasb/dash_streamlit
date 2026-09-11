import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

def render_deepdive_page(df_raw: pd.DataFrame):
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
        "ISSUE_SUBTOPIC"
        if "ISSUE_SUBTOPIC" in df_clean.columns
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
    
    # Deteksi kolom provinsi / region
    prov_col = next((c for c in ["PROVINSI", "provinsi", "PROVINCE", "province", "REGION", "region", "WILAYAH", "wilayah"] if c in df_clean.columns), None)

    # Inisialisasi State Sub-page & AI Generator
    if "deepdive_selected_topic" not in st.session_state:
        st.session_state.deepdive_selected_topic = None
    if "ai_generated_dd" not in st.session_state:
        st.session_state.ai_generated_dd = False

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
                                    st.session_state.ai_generated_dd = False
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

        sub_left, sub_right = st.columns([2.1, 1.1], gap="medium")

        with sub_left:
            st.markdown('<span class="dd-label" style="margin-bottom: 8px;">SUBCATEGORY BREAKDOWN BY SENTIMENT</span>', unsafe_allow_html=True)

            if subtopic_col and sent_col and not df_sub_topic.empty:
                top_subs_pie = df_sub_topic[subtopic_col].dropna().value_counts().head(5).index.tolist()
                df_sub_break = df_sub_topic[df_sub_topic[subtopic_col].isin(top_subs_pie)].groupby([subtopic_col, sent_col]).size().unstack(fill_value=0).reset_index()
            else:
                df_sub_break = pd.DataFrame()

            fig_sb = go.Figure()
            if not df_sub_break.empty:
                for s_name, s_col in [("Positive", "#10b981"), ("Neutral", "#94a3b8"), ("Negative", "#ef4444")]:
                    found_col = next((c for c in df_sub_break.columns if s_name.lower() in str(c).lower()), None)
                    if found_col:
                        fig_sb.add_trace(go.Bar(
                            x=df_sub_break[subtopic_col], y=df_sub_break[found_col],
                            name=s_name, marker_color=s_col, width=0.18
                        ))
            else:
                fig_sb.add_trace(go.Bar(x=["Sub A", "Sub B", "Sub C"], y=[30, 50, 25], name="Positive", marker_color="#10b981", width=0.18))
                fig_sb.add_trace(go.Bar(x=["Sub A", "Sub B", "Sub C"], y=[45, 60, 35], name="Neutral", marker_color="#94a3b8", width=0.18))
                fig_sb.add_trace(go.Bar(x=["Sub A", "Sub B", "Sub C"], y=[90, 55, 80], name="Negative", marker_color="#ef4444", width=0.18))

            fig_sb.update_layout(
                barmode="stack", 
                height=170, 
                margin=dict(l=0, r=0, t=18, b=0),
                paper_bgcolor="#f8fafc", 
                plot_bgcolor="#f8fafc",
                xaxis=dict(showgrid=False, tickfont=dict(size=9, color="#94a3b8")),
                yaxis=dict(showgrid=True, gridcolor="rgba(226, 232, 240, 0.9)", tickfont=dict(size=9, color="#94a3b8")),
                showlegend=False
            )
            st.plotly_chart(
                fig_sb, 
                use_container_width=True, 
                config={
                    "displayModeBar": True,
                    "modeBarButtons": [["zoom2d", "pan2d", "resetScale2d"]],
                    "displaylogo": False
                }
            )

        with sub_right:
            st.markdown('<span class="dd-label" style="margin-bottom: 8px;">GENERATE AI CRITICAL ROOT CAUSE & MITIGATION</span>', unsafe_allow_html=True)

            if st.button("Generate AI Summary", key="btn_gen_ai_dd", type="primary", use_container_width=True):
                st.session_state.ai_generated_dd = True

            if st.session_state.ai_generated_dd:
                st.markdown(f"""
                    <div style="background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 12px; font-size: 0.72rem; color: #334155; line-height: 1.45; margin-top: 8px;">
                        <p style="color: #1d4ed8; font-weight: 700; margin-bottom: 4px;">Root Cause Summary</p>
                        <p style="margin-bottom: 8px;">Lonjakan isu pada <b>{sel_t['name']}</b> didorong oleh akumulasi pemberitaan terkait subtopik <b>SUBCATEGORY</b>.</p>
                        <p style="color: #1d4ed8; font-weight: 700; margin-bottom: 4px;">Suggested Mitigation</p>
                        <p style="margin-bottom: 2px;">→ Action 1: Klarifikasi proaktif melalui media kredibel Tier 1</p>
                        <p>→ Action 2: Monitor tren eskalasi berita secara berkala</p>
                    </div>
                """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        c_hdr_art, c_flt_art = st.columns([3.8, 1.0])
        with c_hdr_art:
            st.markdown(f'<span class="dd-label">NEWS ARTICLES (TOPIC: {sel_t["name"].upper()})</span>', unsafe_allow_html=True)
        with c_flt_art:
            art_sent_opts = ["All Sentiment", "Positive", "Neutral", "Negative"]
            sel_art_sent = st.selectbox("Sentiment Filter", options=art_sent_opts, index=0, label_visibility="collapsed", key="sel_art_sent_dd")

        df_art = df_sub_topic.dropna(subset=[title_col]).copy() if title_col and not df_sub_topic.empty else pd.DataFrame()
        if not df_art.empty and sel_art_sent != "All Sentiment" and sent_col:
            df_art = df_art[
            df_art[sent_col] == sel_art_sent
        ]

        if not df_art.empty:
            df_show = pd.DataFrame()
            df_show["Article"] = df_art[title_col].astype(str).str.replace(r'[\r\n]+', ' ', regex=True)
            
            if media_col:
                df_show["Media Source"] = (
                    df_art[media_col].astype(str)
                    .str.replace("https://", "", regex=False)
                    .str.replace("http://", "", regex=False)
                    .str.replace("www.", "", regex=False)
                    .str.split("/").str[0]
                )
            else:
                df_show["Media Source"] = "N/A"
                
            if "NEWS_DATE" in df_art.columns:
                df_show["Date"] = pd.to_datetime(df_art["NEWS_DATE"], errors="coerce").dt.strftime("%Y-%m-%d")
            else:
                df_show["Date"] = "-"
                
            df_show["Sentiment"] = df_art[sent_col]

            st.dataframe(
                df_show,
                use_container_width=True,
                height=420,
                hide_index=True,
                column_config={
                    "Article": st.column_config.TextColumn("Article", width="large"),
                    "Media Source": st.column_config.TextColumn("Media Source", width="medium"),
                    "Date": st.column_config.TextColumn("Date", width="small"),
                    "Sentiment": st.column_config.TextColumn("Sentiment", width="small"),
                }
            )
        else:
            st.info("Tidak ada artikel untuk filter sentimen ini.")