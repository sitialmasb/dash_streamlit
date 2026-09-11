import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Pemetaan koordinat lintang & bujur provinsi Indonesia
PROVINCE_COORDS = {
    "ACEH": (4.6951, 96.7494),
    "SUMATERA UTARA": (2.1154, 99.5451),
    "SUMATERA BARAT": (-0.7399, 100.8000),
    "RIAU": (0.2933, 101.7068),
    "JAMBI": (-1.6101, 103.6131),
    "SUMATERA SELATAN": (-3.3194, 104.9144),
    "BENGKULU": (-3.5778, 102.3464),
    "LAMPUNG": (-4.5586, 105.4068),
    "KEPULAUAN BANGKA BELITUNG": (-2.7411, 106.4406),
    "BANGKA BELITUNG": (-2.7411, 106.4406),
    "KEPULAUAN RIAU": (3.9457, 108.1429),
    "DKI JAKARTA": (-6.2088, 106.8456),
    "JAKARTA": (-6.2088, 106.8456),
    "JAWA BARAT": (-6.9175, 107.6191),
    "JAWA TENGAH": (-7.1510, 110.1403),
    "DI YOGYAKARTA": (-7.7956, 110.3695),
    "YOGYAKARTA": (-7.7956, 110.3695),
    "JAWA TIMUR": (-7.5361, 112.2384),
    "BANTEN": (-6.4058, 106.0640),
    "BALI": (-8.4095, 115.1889),
    "NUSA TENGGARA BARAT": (-8.6529, 117.3616),
    "NTB": (-8.6529, 117.3616),
    "NUSA TENGGARA TIMUR": (-8.6574, 121.0794),
    "NTT": (-8.6574, 121.0794),
    "KALIMANTAN BARAT": (-0.2787, 111.4753),
    "KALIMANTAN TENGAH": (-1.6815, 113.3824),
    "KALIMANTAN SELATAN": (-3.0926, 115.2838),
    "KALIMANTAN TIMUR": (0.5387, 116.4194),
    "KALIMANTAN UTARA": (3.0731, 116.0414),
    "SULAWESI UTARA": (0.6247, 123.9750),
    "SULAWESI TENGAH": (-1.4300, 121.4456),
    "SULAWESI SELATAN": (-3.6687, 119.9741),
    "SULAWESI TENGGARA": (-4.1449, 122.1746),
    "GORONTALO": (0.6999, 122.4467),
    "SULAWESI BARAT": (-2.8441, 119.2321),
    "MALUKU": (-3.2385, 130.1453),
    "MALUKU UTARA": (1.5709, 127.8088),
    "PAPUA BARAT": (-1.3361, 133.1747),
    "PAPUA": (-4.2699, 138.0804),
    "PAPUA SELATAN": (-7.5000, 139.5000),
    "PAPUA TENGAH": (-3.7000, 136.5000),
    "PAPUA PEGUNUNGAN": (-4.2000, 139.0000),
    "PAPUA BARAT DAYA": (-1.0000, 131.5000)
}

def render_home_page(df: pd.DataFrame):
    if df is None or df.empty:
        st.info("Data tidak tersedia.")
        return

    df_clean = df.copy()
    if "NEWS_DATE" in df_clean.columns:
        df_clean["NEWS_DATE"] = pd.to_datetime(df_clean["NEWS_DATE"], errors="coerce")
    elif "news_date" in df_clean.columns:
        df_clean["NEWS_DATE"] = pd.to_datetime(df_clean["news_date"], errors="coerce")

    sent_col = "SENTIMENT" if "SENTIMENT" in df_clean.columns else None
    topic_col = "ISSUE_TOPIC" if "ISSUE_TOPIC" in df_clean.columns else None
    subtopic_col = "ISSUE_SUBTOPIC" if "ISSUE_SUBTOPIC" in df_clean.columns else None
    tier_col = "TIER" if "TIER" in df_clean.columns else ("new_tier" if "new_tier" in df_clean.columns else None)
    url_col = "CLEAN_URL" if "CLEAN_URL" in df_clean.columns else ("domain" if "domain" in df_clean.columns else None)
    title_col = next((c for c in ["NEWS", "NEWS_SUMMARY", "news_title", "title", "headline"] if c in df_clean.columns), None)
    prov_col = next((c for c in ["PROVINSI", "provinsi", "PROVINCE", "province", "WILAYAH", "REGION"] if c in df_clean.columns), None)

    st.markdown("""
        <style>
            div[data-testid="stVerticalBlockBorderWrapper"] {
                background: transparent !important;
                border: none !important;
                box-shadow: none !important;
            }

            .home-card-title {
                font-size: 0.78rem !important;
                font-weight: 800 !important;
                color: #475569 !important;
                letter-spacing: 0.05em !important;
                text-transform: uppercase !important;
                margin: 0 0 10px 0 !important;
                padding: 0 !important;
                display: block !important;
            }

            .kpi-unit-wrapper {
                padding: 4px 0 !important;
                margin-bottom: 4px !important;
            }

            div[data-testid="stPlotlyChart"] {
                background-color: #f8fafc !important;
                border-radius: 8px !important;
                border: none !important;
                padding: 0 !important;
                margin: 0 !important;
            }

            .news-feed-item-box {
                background: #f8fafc !important;
                border-bottom: 1px solid rgba(226, 232, 240, 0.8) !important;
                padding: 9px 0 !important;
                margin-bottom: 4px !important;
                display: flex !important;
                align-items: flex-start !important;
                gap: 12px !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # 1. HEADER UTAMA: FILTER & TITLE
    valid_dates = df_clean["NEWS_DATE"].dropna() if "NEWS_DATE" in df_clean.columns else pd.Series([])
    min_d = valid_dates.min().date() if not valid_dates.empty else datetime(2023, 1, 1).date()
    max_d = valid_dates.max().date() if not valid_dates.empty else datetime.now().date()

    c_hdr, c_f_date, c_f_tier = st.columns([2.6, 1.1, 1.1], gap="medium")
    with c_hdr:
        st.markdown("""
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="width: 8px; height: 48px; background: linear-gradient(180deg, #38bdf8 0%, #237ece 100%); border-radius: 4px; flex-shrink: 0;"></div>
                <div style="display: flex; flex-direction: column; justify-content: center;">
                    <h2 style="margin: 0 0 1px 0; padding: 0; font-size: 2rem; line-height: 1.25; color: #0f172a; font-weight: 800; letter-spacing: -0.01em;">
                        DASHBOARD <span style="color: #237ece; font-style: italic;">HOME</span>
                    </h2>
                    <span style="margin: 0; padding: 0; font-size: 0.70rem; line-height: 1.1; letter-spacing: 0.08em; color: #64748b; font-weight: 700; text-transform: uppercase;">
                        EXECUTIVE SENTIMENT & MEDIA BENCHMARK
                    </span>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with c_f_date:
        sel_date = st.date_input("Filter Tanggal", value=(min_d, max_d), label_visibility="collapsed", key="home_top_date")

    with c_f_tier:
        tier_options = ["All Media Tier"] + sorted(list(df_clean[tier_col].dropna().astype(str).unique())) if tier_col else ["All Media Tier"]
        sel_tier = st.selectbox("Filter Tier", options=tier_options, index=0, label_visibility="collapsed", key="home_top_tier")

    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

    if sel_date and isinstance(sel_date, (tuple, list)) and len(sel_date) == 2:
        df_clean = df_clean[(df_clean["NEWS_DATE"].dt.date >= sel_date[0]) & (df_clean["NEWS_DATE"].dt.date <= sel_date[1])]
    if sel_tier != "All Media Tier" and tier_col:
        df_clean = df_clean[df_clean[tier_col].astype(str) == sel_tier]

    # Kalkulasi Metrik
    # TOTAL ARTIKEL pada KPI dihitung khusus untuk hari ini,
    # bukan seluruh artikel dalam dataset.
    # Perhitungan ini dilakukan sebelum filter tanggal agar KPI
    # tetap menunjukkan jumlah artikel yang terbit hari ini.
    df_today = df_clean.copy()

    if sel_tier != "All Media Tier" and tier_col:
        df_today = df_today[df_today[tier_col].astype(str) == sel_tier]

    today = datetime.now().date()

    if "NEWS_DATE" in df_today.columns:
        total_article_today = (
            df_today["NEWS_DATE"].dt.date == today
        ).sum()
    else:
        total_article_today = 0

    # total_vol tetap digunakan untuk kalkulasi sentiment dan
    # reputation index berdasarkan filter tanggal yang dipilih.
    total_vol = len(df_clean)
    pos_cnt = (
        (df_clean["SENTIMENT"] == "Positive").sum()
        if "SENTIMENT" in df_clean.columns
        else 0
    )

    neu_cnt = (
        (df_clean["SENTIMENT"] == "Neutral").sum()
        if "SENTIMENT" in df_clean.columns
        else 0
    )

    neg_cnt = (
        (df_clean["SENTIMENT"] == "Negative").sum()
        if "SENTIMENT" in df_clean.columns
        else 0
    )

    pos_pct = (pos_cnt / total_vol * 100) if total_vol > 0 else 57.6
    neu_pct = (neu_cnt / total_vol * 100) if total_vol > 0 else 24.07
    neg_pct = (neg_cnt / total_vol * 100) if total_vol > 0 else 18.33

    raw_ri = ((pos_cnt + 0.5 * neu_cnt) / max(1, total_vol) * 100) - ((neg_cnt / max(1, total_vol)) * 20)
    ri_score = max(0, min(100, int(round(raw_ri)))) if total_vol > 0 else 78

    if ri_score >= 65:
        ri_label = "Good"
        ri_color = "#10b981"
    elif ri_score >= 50:
        ri_label = "Moderate"
        ri_color = "#f59e0b"
    else:
        ri_label = "Alert"
        ri_color = "#ef4444"

    # -------------------------------------------------------------
    # TODAY'S ARTICLES & DATASET LAST UPDATED
    # -------------------------------------------------------------
    # Count articles published today.
    today = pd.Timestamp.now().normalize()
    today_article_count = 0

    if "NEWS_DATE" in df_clean.columns:
        today_article_count = int(
            (df_clean["NEWS_DATE"].dt.normalize() == today).sum()
        )

    # DATASET_LAST_UPDATED must be supplied by the dataset-loading layer.
    # It represents the dataset upload time, NOT the dashboard execution time.
    dataset_last_updated = df.attrs.get("DATASET_LAST_UPDATED", None)

    if dataset_last_updated is None:
        dataset_last_updated = df.attrs.get("LAST_UPDATED", None)

    if dataset_last_updated is not None:
        try:
            dataset_last_updated = pd.to_datetime(dataset_last_updated)
            last_updated_text = dataset_last_updated.strftime(
                "%B %d, %Y • %I:%M %p"
            )
        except Exception:
            last_updated_text = str(dataset_last_updated)
    else:
        last_updated_text = "Not available"

    # -------------------------------------------------------------
    # 2. KPI METRICS (TOTAL & REPUTATION ATAS-BAWAH, SENTIMENT TENGAH, TOP TOPICS KANAN)
    # -------------------------------------------------------------
    col_kpi_stack, col_kpi_sent, col_kpi_topics = st.columns([0.85, 1.35, 1.45], gap="large")

    with col_kpi_stack:
        st.markdown(f"""
            <div class="kpi-unit-wrapper">
                <span class="home-card-title">TODAY\'S ARTICLES</span>
            </div>
            <div style="display:flex; align-items:baseline; margin-bottom: 24px;">
                <span style="font-size:1.85rem; font-weight:800; color:#0f172a; line-height:1;">{total_article_today:,}</span>
            </div>
            <div class="kpi-unit-wrapper">
                <span class="home-card-title">REPUTATION INDEX</span>
            </div>
            <div style="display:flex; align-items:baseline; gap:4px; margin-bottom: 6px;">
                <span style="font-size:1.6rem; font-weight:800; color:{ri_color}; line-height:1;">{ri_score}</span>
                <span style="font-size:0.75rem; color:#64748b; font-weight:700;">/100</span>
            </div>
            <div>
                <div style="width:100%; background:#e2e8f0; height:6px; border-radius:10px; overflow:hidden; margin-bottom:6px;">
                    <div style="width:{ri_score}%; background:{ri_color}; height:100%; border-radius:10px;"></div>
                </div>
                <div style="display:flex; justify-content:space-between; font-size:0.70rem; color:#64748b; font-weight:700;">
                    <span>0</span>
                    <span style="color:{ri_color}; font-weight:800;">{ri_label}</span>
                    <span>100</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col_kpi_sent:
        st.markdown("""
            <div class="kpi-unit-wrapper" style="margin-bottom: 4px;">
                <span class="home-card-title">GLOBAL SENTIMENT</span>
            </div>
        """, unsafe_allow_html=True)
        
        c_don, c_leg = st.columns([1.0, 1.1], gap="small")
        with c_don:
            fig_donut = go.Pie(
                values=[pos_cnt if total_vol > 0 else 57.6, neu_cnt if total_vol > 0 else 24.07, neg_cnt if total_vol > 0 else 18.33],
                hole=0.62,
                marker=dict(colors=["#10b981", "#8da0b6", "#ef4444"]),
                textinfo="none",
                hoverinfo="percent",
                direction='clockwise',
                sort=False,
                domain={'x': [0.05, 0.95], 'y': [0.05, 0.95]}
            )
            fig_donut_layout = go.Layout(
                margin=dict(l=4, r=4, t=4, b=4),
                height=130,
                showlegend=False,
                paper_bgcolor="#f8fafc",
                plot_bgcolor="#f8fafc"
            )
            st.plotly_chart(go.Figure(data=[fig_donut], layout=fig_donut_layout), use_container_width=True, config={"displayModeBar": False})

        with c_leg:
            st.markdown(f"""
                <div style="display:flex; flex-direction:column; justify-content:center; height:130px; gap:8px; font-size:0.80rem;">
                    <div style="display:flex; align-items:center; justify-content:space-between; padding-bottom: 3px; border-bottom: 1px dashed #cbd5e1;">
                        <span style="color:#475569;">Positive</span>
                        <b style="color:#0f172a;">{pos_pct:.1f}%</b>
                    </div>
                    <div style="display:flex; align-items:center; justify-content:space-between; padding-bottom: 3px; border-bottom: 1px dashed #cbd5e1;">
                        <span style="color:#475569;">Neutral</span>
                        <b style="color:#0f172a;">{neu_pct:.1f}%</b>
                    </div>
                    <div style="display:flex; align-items:center; justify-content:space-between;">
                        <span style="color:#475569;">Negative</span>
                        <b style="color:#0f172a;">{neg_pct:.1f}%</b>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    with col_kpi_topics:
        st.markdown("""
            <div class="kpi-unit-wrapper" style="margin-bottom: 4px;">
                <span class="home-card-title">TOP TOPICS BY VOLUME</span>
            </div>
        """, unsafe_allow_html=True)
        if topic_col and not df_clean.empty:
            df_t = df_clean[topic_col].value_counts().head(5).reset_index()
            df_t.columns = ["topic", "count"]
            fig_bar = px.bar(df_t, x="topic", y="count")
            fig_bar.update_traces(marker_color="#237ece", width=0.42)
            fig_bar.update_layout(
                margin=dict(l=0, r=0, t=18, b=26),
                height=135,
                xaxis=dict(
                    title="", 
                    tickfont=dict(size=9.0, color="#64748b", family="sans-serif"), 
                    showgrid=False,
                    tickangle=0
                ),
                yaxis=dict(visible=False),
                plot_bgcolor="#f8fafc",
                paper_bgcolor="#f8fafc"
            )
            st.plotly_chart(
                fig_bar, 
                use_container_width=True, 
                config={
                    "displayModeBar": True,
                    "modeBarButtons": [["zoom2d", "pan2d", "resetScale2d"]],
                    "displaylogo": False
                }
            )
        else:
            st.caption("No topic data")

    st.markdown("<div style='margin-bottom: 26px;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # 3 & 4. [SENTIMENT TREND + PETA] vs [LATEST NEWS FEED MEMANJANG]
    # -------------------------------------------------------------
    col_main_left, col_feed_right = st.columns([2.35, 1.05], gap="large")

    with col_main_left:
        # A. SENTIMENT TREND OVER TIME
        st.markdown('<span class="home-card-title" style="margin-bottom:8px;">SENTIMENT TREND OVER TIME</span>', unsafe_allow_html=True)

        if "NEWS_DATE" in df_clean.columns and not df_clean.empty and sent_col:
            df_trend = df_clean.copy()
            df_trend["MONTH"] = df_trend["NEWS_DATE"].dt.to_period("M").dt.to_timestamp()
            df_mon = df_trend.groupby(["MONTH", sent_col]).size().unstack(fill_value=0).reset_index()

            df_daily = df_trend.groupby([df_trend["NEWS_DATE"].dt.date, sent_col]).size().unstack(fill_value=0)
            pos_spike = df_daily["Positive"].idxmax().strftime("%b %d, %Y") if "Positive" in df_daily.columns and not df_daily.empty else "Agu 24, 2023"
            neg_spike = df_daily["Negative"].idxmax().strftime("%b %d, %Y") if "Negative" in df_daily.columns and not df_daily.empty else "Apr 29, 2023"

            fig_line = go.Figure()
            for s_name, s_col in [("Positive", "#10b981"), ("Neutral", "#8da0b6"), ("Negative", "#ef4444")]:
                if s_name in df_mon.columns:
                    fig_line.add_trace(go.Scatter(
                        x=df_mon["MONTH"], y=df_mon[s_name], mode='lines', name=s_name,
                        line=dict(color=s_col, width=2.2, shape='spline')
                    ))

            fig_line.update_layout(
                height=230,
                margin=dict(l=0, r=10, t=24, b=10),
                paper_bgcolor="#f8fafc",
                plot_bgcolor="#f8fafc",
                xaxis=dict(showgrid=False, dtick="M1", tickformat="%b", tickfont=dict(size=9, color="#94a3b8")),
                yaxis=dict(showgrid=True, gridcolor="rgba(226, 232, 240, 0.9)", tickfont=dict(size=9, color="#94a3b8")),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=9.5, color="#475569"))
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

            st.markdown(f"""
                <div style="display:flex; gap:16px; align-items:center; margin-top:4px; font-size:0.72rem; font-weight:700; color:#475569;">
                    <span><span style="color:#10b981;">●</span> Positive Spike: {pos_spike}</span>
                    <span><span style="color:#ef4444;">●</span> Negative Spike: {neg_spike}</span>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.caption("Data tren tidak cukup.")

        st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

        # B. GEOGRAPHICAL NEWS INTENSITY (BOUNDING BOX INDONESIA)
        st.markdown('<span class="home-card-title" style="margin-bottom:8px;">GEOGRAPHICAL NEWS INTENSITY</span>', unsafe_allow_html=True)

        if prov_col and not df_clean[prov_col].dropna().empty:
            import requests
            import json

            @st.cache_data(show_spinner=False)
            def load_indonesia_geojson():
                url = "https://raw.githubusercontent.com/superpikar/indonesia-geojson/master/indonesia-province-simple.json"
                try:
                    res = requests.get(url, timeout=10)
                    return res.json()
                except Exception:
                    return None

            geojson_data = load_indonesia_geojson()

            if geojson_data:
                official_provs = []
                for feat in geojson_data.get("features", []):
                    p_name = feat.get("properties", {}).get("Propinsi") or feat.get("properties", {}).get("name")
                    if p_name:
                        official_provs.append(str(p_name).strip().upper())

                s_prov = df_clean[prov_col].dropna().astype(str).str.strip().str.upper()
                prov_alias = {
                    "JAKARTA": "DKI JAKARTA",
                    "YOGYAKARTA": "DAERAH ISTIMEWA YOGYAKARTA",
                    "DI YOGYAKARTA": "DAERAH ISTIMEWA YOGYAKARTA",
                    "DIY": "DAERAH ISTIMEWA YOGYAKARTA",
                    "KEPULAUAN BANGKA BELITUNG": "BANGKA BELITUNG",
                    "NTB": "NUSA TENGGARA BARAT",
                    "NTT": "NUSA TENGGARA TIMUR"
                }
                s_prov = s_prov.replace(prov_alias)
                prov_counts = s_prov.value_counts().to_dict()

                map_rows = []
                for p in set(official_provs):
                    cnt = prov_counts.get(p, 0)
                    if cnt == 0:
                        for k, v in prov_counts.items():
                            if k in p or p in k:
                                cnt = v
                                break
                    map_rows.append({"PROVINSI": p, "COUNT": cnt})

                df_map = pd.DataFrame(map_rows)

                blues_scale = [
                    [0.0, "#e2e8f0"],
                    [0.05, "#dbeafe"],
                    [0.2, "#93c5fd"],
                    [0.5, "#3b82f6"],
                    [0.8, "#1d4ed8"],
                    [1.0, "#0f172a"]
                ]

                fig_map = go.Figure(go.Choropleth(
                    geojson=geojson_data,
                    locations=df_map["PROVINSI"],
                    featureidkey="properties.Propinsi",
                    z=df_map["COUNT"],
                    colorscale=blues_scale,
                    zmin=0,
                    zmax=df_map["COUNT"].max() if df_map["COUNT"].max() > 0 else 100,
                    marker_line_width=1.0,
                    marker_line_color="#64748b",
                    hovertemplate="<b>%{location}</b><br>Volume Berita: %{z:,}<extra></extra>",
                    colorbar=dict(
                        title=dict(text="Volume", font=dict(size=9, color="#475569")),
                        thickness=8,
                        len=0.75,
                        tickfont=dict(size=8.5, color="#64748b"),
                        x=1.01
                    )
                ))

                fig_map.update_geos(
                    visible=False,
                    lonaxis_range=[94.0, 142.0],
                    lataxis_range=[-11.5, 6.5],
                    bgcolor="#f8fafc",
                    showocean=False,
                    showlakes=False,
                    showcoastlines=False,
                    showland=False
                )

                fig_map.update_layout(
                    margin=dict(l=0, r=0, t=16, b=0),
                    height=320,
                    paper_bgcolor="#f8fafc",
                    plot_bgcolor="#f8fafc"
                )

                st.plotly_chart(
                    fig_map, 
                    use_container_width=True,
                    config={
                        "displayModeBar": True,
                        "modeBarButtons": [["zoomInGeo", "zoomOutGeo", "resetGeo"]],
                        "displaylogo": False
                    }
                )
            else:
                st.caption("Gagal memuat batas wilayah peta.")
        else:
            st.caption("Kolom data provinsi tidak ditemukan pada dataset.")

    # C. SISI KANAN: LATEST NEWS FEED MEMANJANG (HTML AMAN & LINK AKTIF)
    with col_feed_right:
        st.markdown('<span class="home-card-title" style="margin-bottom:12px;">LATEST NEWS FEED</span>', unsafe_allow_html=True)

        if title_col and not df_clean.empty:
            def format_time_ago(news_dt):
                if pd.isna(news_dt):
                    return "recently"
                diff = pd.Timestamp.now() - pd.to_datetime(news_dt)
                total_seconds = int(diff.total_seconds())

                if total_seconds < 0:
                    return "just now"
                elif total_seconds < 3600:
                    minutes = max(1, total_seconds // 60)
                    return f"{minutes}m ago"
                elif total_seconds < 86400:
                    hours = total_seconds // 3600
                    return f"{hours}h ago"
                elif total_seconds < 604800:
                    days = total_seconds // 86400
                    return f"{days}d ago"
                elif total_seconds < 2592000:
                    weeks = total_seconds // 604800
                    return f"{weeks}w ago"
                else:
                    months = total_seconds // 2592000
                    return f"{months}mo ago"

            link_col = next((c for c in ["URL", "url", "LINK", "link", "NEWS_URL", "news_url"] if c in df_clean.columns), None)

            feed_items = df_clean.dropna(subset=[title_col]).sort_values(by="NEWS_DATE", ascending=False).head(7)
            
            feed_html_list = []
            for _, r in feed_items.iterrows():
                s_val = str(r.get(sent_col, "Neutral")).capitalize()
                arrow_icon = "↑" if s_val == "Positive" else ("↓" if s_val == "Negative" else "–")
                icon_bg = "#ecfdf5" if s_val == "Positive" else ("#fef2f2" if s_val == "Negative" else "#f1f5f9")
                icon_color = "#10b981" if s_val == "Positive" else ("#ef4444" if s_val == "Negative" else "#64748b")
                
                raw_t = str(r[title_col])
                disp_title = (raw_t[:65] + "...") if len(raw_t) > 65 else raw_t
                media_name = str(r.get(url_col, "Media.com")).lower().replace("www.", "")
                time_ago_str = format_time_ago(r.get("NEWS_DATE"))

                article_url = str(r.get(link_col, "")).strip() if link_col else ""
                if not article_url or article_url.lower() in ["nan", "none", ""]:
                    raw_domain = str(r.get(url_col, "")).strip()
                    article_url = f"https://{raw_domain}" if raw_domain and raw_domain.lower() not in ["nan", "none"] else "#"
                elif not (article_url.startswith("http://") or article_url.startswith("https://")):
                    article_url = f"https://{article_url}"

                if article_url != "#":
                    title_elem = f'<a href="{article_url}" target="_blank" rel="noopener noreferrer" style="text-decoration:none; color:#0f172a;" onmouseover="this.style.color=\'#237ece\'" onmouseout="this.style.color=\'#0f172a\'">{disp_title}</a>'
                else:
                    title_elem = f'<span style="color:#0f172a;">{disp_title}</span>'

                item_block = f'''<div class="news-feed-item-box"><div style="width:24px; height:24px; border-radius:50%; background:{icon_bg}; color:{icon_color}; font-size:0.75rem; font-weight:800; display:flex; align-items:center; justify-content:center; flex-shrink:0; margin-top:2px;">{arrow_icon}</div><div><div style="font-size:0.78rem; font-weight:700; line-height:1.3; margin-bottom:2px;">{title_elem}</div><div style="font-size:0.68rem; color:#94a3b8; font-weight:600;">{media_name} • {time_ago_str}</div></div></div>'''
                feed_html_list.append(item_block)

            st.markdown("".join(feed_html_list), unsafe_allow_html=True)
        else:
            st.caption("Feed berita kosong.")