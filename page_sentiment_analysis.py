import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

def render_sentiment_analysis_page(df_raw: pd.DataFrame):
    if df_raw is None or df_raw.empty:
        st.info("Data is not available.")
        return

    df_clean = df_raw.copy()
    if "NEWS_DATE" in df_clean.columns:
        df_clean["NEWS_DATE"] = pd.to_datetime(df_clean["NEWS_DATE"], errors="coerce")
    elif "news_date" in df_clean.columns:
        df_clean["NEWS_DATE"] = pd.to_datetime(df_clean["news_date"], errors="coerce")

    # Standardize dataset columns

    sent_col = (
        "SENTIMENT"
        if "SENTIMENT" in df_clean.columns
        else None
    )

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

    tier_col = (
        "TIER"
        if "TIER" in df_clean.columns
        else None
    )
    media_col = next((c for c in ["CLEAN_URL", "clean_url", "MEDIA", "media", "SOURCE", "source", "MEDIA_DOMAIN"] if c in df_clean.columns), None)
    title_col = next((c for c in ["NEWS", "NEWS_SUMMARY", "news_title", "title", "headline"] if c in df_clean.columns), None)

    # Scoped CSS
    st.markdown("""
        <style>
            div[data-testid="stVerticalBlockBorderWrapper"],
            .ov-transparent-section {
                border: none !important;
                box-shadow: none !important;
                background: transparent !important;
                background-color: transparent !important;
            }
            .ov-card-title {
                font-size: 0.78rem !important;
                font-weight: 800 !important;
                color: #475569 !important;
                letter-spacing: 0.05em !important;
                text-transform: uppercase !important;
                margin-bottom: 12px !important;
                display: block !important;
            }
            .formula-pill-noborder {
                border-radius: 8px !important;
                padding: 8px 12px !important;
                display: flex !important;
                flex-direction: column !important;
                align-items: center !important;
                justify-content: center !important;
                min-width: 72px !important;
                border: none !important;
            }
            .spike-metric-card {
                background: #ffffff !important;
                border: none !important;
                border-radius: 12px !important;
                padding: 14px 16px !important;
                box-shadow: 0 4px 14px rgba(15, 23, 42, 0.03) !important;
            }
            .badge-pos {
                background: #ecfdf5 !important;
                color: #059669 !important;
                border: 1px solid #a7f3d0 !important;
                padding: 4px 12px !important;
                border-radius: 20px !important;
                font-weight: 700 !important;
                display: inline-block !important;
                margin: 3px !important;
            }
            .badge-neg {
                background: #fef2f2 !important;
                color: #dc2626 !important;
                border: 1px solid #fecaca !important;
                padding: 4px 12px !important;
                border-radius: 20px !important;
                font-weight: 700 !important;
                display: inline-block !important;
                margin: 3px !important;
            }
            div[data-testid="stPlotlyChart"] {
                background-color: #f8fafc !important;
                border-radius: 8px !important;
                border: none !important;
                padding: 0 !important;
                margin: 0 !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # -------------------------------------------------------------
    # 1. TOP FILTERS PREPARATION
    # -------------------------------------------------------------
    month_options = ["All Months"]
    if "NEWS_DATE" in df_clean.columns and not df_clean["NEWS_DATE"].dropna().empty:
        df_clean["YEAR_MONTH"] = df_clean["NEWS_DATE"].dt.to_period("M")
        sorted_periods = sorted(df_clean["YEAR_MONTH"].dropna().unique(), reverse=True)
        month_options.extend([p.strftime("%B %Y") for p in sorted_periods])

    tier_opts = ["All Media Tier"] + sorted(list(df_clean[tier_col].dropna().astype(str).unique())) if tier_col else ["All Media Tier"]

    selected_month = st.session_state.get("sa_month", "All Months")
    selected_tier = st.session_state.get("sa_tier", "All Media Tier")

    df_filtered = df_clean.copy()
    if selected_month != "All Months" and "NEWS_DATE" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["NEWS_DATE"].dt.strftime("%B %Y") == selected_month]
    if selected_tier != "All Media Tier" and tier_col:
        df_filtered = df_filtered[df_filtered[tier_col].astype(str) == selected_tier]

    # -------------------------------------------------------------
    # 2. NSS CALCULATION
    # -------------------------------------------------------------
    total_news = len(df_filtered)
    pos_count = len(df_filtered[df_filtered[sent_col].astype(str).str.lower().str.contains("pos")]) if sent_col else 0
    neg_count = len(df_filtered[df_filtered[sent_col].astype(str).str.lower().str.contains("neg")]) if sent_col else 0
    nss_score = int(round(((pos_count - neg_count) / total_news) * 100)) if total_news > 0 else 0

    if nss_score < 0:
        bar_gradient = "linear-gradient(180deg, #f87171 0%, #dc2626 100%)"
        accent_color = "#dc2626"
        nss_card_bg, nss_card_border, nss_title_color, nss_text_color = "#fef2f2", "#fca5a5", "#991b1b", "#dc2626"
        nss_spark_color, nss_badge_bg = "#ef4444", "#fee2e2"
        nss_str = f"{nss_score}%"
    else:
        bar_gradient = "linear-gradient(180deg, #34d399 0%, #16a34a 100%)"
        accent_color = "#16a34a"
        nss_card_bg, nss_card_border, nss_title_color, nss_text_color = "#f0fdf4", "#86efac", "#166534", "#15803d"
        nss_spark_color, nss_badge_bg = "#16a34a", "#dcfce7"
        nss_str = f"+{nss_score}%"

    # -------------------------------------------------------------
    # 3. PAGE HEADER
    # -------------------------------------------------------------
    c_hdr, c_f_month, c_f_tier = st.columns([2.6, 1.15, 1.15], gap="medium")
    with c_hdr:
        st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 12px; height: 100%; min-height: 48px;">
                <div style="width: 8px; height: 48px; background: {bar_gradient}; border-radius: 4px; flex-shrink: 0;"></div>
                <div style="display: flex; flex-direction: column; justify-content: center;">
                    <h2 style="margin: 0 0 1px 0; padding: 0; font-size: 2rem; line-height: 1.25; color: #0f172a; font-weight: 800; letter-spacing: -0.01em;">
                        SENTIMENT <span style="color: {accent_color}; font-style: italic;">ANALYSIS</span>
                    </h2>
                    <span style="margin: 0; padding: 0; font-size: 0.70rem; line-height: 1.1; letter-spacing: 0.08em; color: #64748b; font-weight: 700; text-transform: uppercase;">
                        COMPREHENSIVE SENTIMENT INTELLIGENCE & SPIKE INVESTIGATION
                    </span>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with c_f_month:
        month_idx = month_options.index(selected_month) if selected_month in month_options else 0
        new_month = st.selectbox("Month:", options=month_options, index=month_idx, label_visibility="collapsed", key="sa_month")
        if new_month != selected_month:
            st.rerun()

    with c_f_tier:
        tier_idx = tier_opts.index(selected_tier) if selected_tier in tier_opts else 0
        new_tier = st.selectbox("Tier:", options=tier_opts, index=tier_idx, label_visibility="collapsed", key="sa_tier")
        if new_tier != selected_tier:
            st.rerun()

    st.markdown("<div style='margin-bottom: 22px;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # 4. TOP BANNER: NSS SCORE + FORMULA + MONTHLY NSS
    # -------------------------------------------------------------
    c_score, c_formula, c_mini = st.columns([1.15, 2.35, 1.1], gap="medium")

    with c_score:
        st.markdown(f"""
            <div style="background: {nss_card_bg}; border: 1.5px solid {nss_card_border}; border-radius: 12px; padding: 12px 16px; height: 100px; display: flex; flex-direction: column; justify-content: space-between; box-sizing: border-box;">
                <span style="font-size: 0.68rem; font-weight: 800; color: {nss_title_color}; letter-spacing: 0.04em;">NET SENTIMENT SCORE</span>
                <div style="font-size: 2.2rem; font-weight: 800; color: {nss_text_color}; line-height: 1;">
                    {nss_str}
                </div>
                <div style="font-size: 0.68rem; font-weight: 700; color: {nss_title_color};">
                    Period: {selected_month if selected_month != "All Months" else "All Time"}
                </div>
            </div>
        """, unsafe_allow_html=True)

    with c_formula:
        st.markdown(f"""
            <div style="display: flex; align-items: center; justify-content: center; height: 100px; gap: 8px;">
                <div class="formula-pill-noborder" style="background: #ecfdf5;">
                    <span style="font-size: 0.68rem; font-weight: 700; color: #059669;">Positive</span>
                    <span style="font-size: 1.15rem; font-weight: 800; color: #0f172a;">{pos_count:,}</span>
                </div>
                <span style="font-size: 1.3rem; font-weight: 800; color: #94a3b8;">−</span>
                <div class="formula-pill-noborder" style="background: #fef2f2;">
                    <span style="font-size: 0.68rem; font-weight: 700; color: #dc2626;">Negative</span>
                    <span style="font-size: 1.15rem; font-weight: 800; color: #0f172a;">{neg_count:,}</span>
                </div>
                <span style="font-size: 1.3rem; font-weight: 800; color: #94a3b8;">÷</span>
                <div class="formula-pill-noborder" style="background: #eff6ff;">
                    <span style="font-size: 0.68rem; font-weight: 700; color: #2563eb;">Total</span>
                    <span style="font-size: 1.15rem; font-weight: 800; color: #0f172a;">{total_news:,}</span>
                </div>
                <span style="font-size: 1rem; font-weight: 800; color: #94a3b8;">×100</span>
                <div style="background: {nss_badge_bg}; color: {nss_text_color}; border-radius: 8px; padding: 10px 14px; font-size: 1.2rem; font-weight: 800; white-space: nowrap;">
                    = {nss_str}
                </div>
            </div>
        """, unsafe_allow_html=True)

    with c_mini:
        st.markdown("""
            <div style="text-align: right; margin-bottom: 2px;">
                <span style="font-size: 0.68rem; font-weight: 800; color: #475569; text-transform: uppercase; letter-spacing: 0.04em;">
                    Monthly NSS
                </span>
            </div>
        """, unsafe_allow_html=True)
        
        months_abbr = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        monthly_nss_vals = [0] * 12
        monthly_bar_colors = ["#cbd5e1"] * 12

        if "NEWS_DATE" in df_clean.columns and sent_col and not df_clean["NEWS_DATE"].dropna().empty:
            df_m_calc = df_clean.dropna(subset=["NEWS_DATE"]).copy()
            target_year = int(selected_month.split()[-1]) if selected_month != "All Months" else df_m_calc["NEWS_DATE"].dt.year.max()

            df_year = df_m_calc[df_m_calc["NEWS_DATE"].dt.year == target_year]
            if selected_tier != "All Media Tier" and tier_col:
                df_year = df_year[df_year[tier_col].astype(str) == selected_tier]

            df_year["MONTH_NUM"] = df_year["NEWS_DATE"].dt.month
            for m_idx in range(1, 13):
                sub_df = df_year[df_year["MONTH_NUM"] == m_idx]
                tot_m = len(sub_df)
                if tot_m > 0:
                    pos_m = len(sub_df[sub_df[sent_col].astype(str).str.lower().str.contains("pos")])
                    neg_m = len(sub_df[sub_df[sent_col].astype(str).str.lower().str.contains("neg")])
                    score_m = int(round(((pos_m - neg_m) / tot_m) * 100))
                    monthly_nss_vals[m_idx - 1] = score_m
                    monthly_bar_colors[m_idx - 1] = "#dc2626" if score_m < 0 else "#16a34a"
                else:
                    monthly_nss_vals[m_idx - 1] = 0
                    monthly_bar_colors[m_idx - 1] = "#cbd5e1"

        fig_mini = go.Figure(go.Bar(
            x=months_abbr,
            y=monthly_nss_vals,
            marker_color=monthly_bar_colors,
            marker_line_width=0,
            hovertemplate="<b>%{x}</b><br>NSS: %{y}%<extra></extra>"
        ))
        fig_mini.update_layout(
            margin=dict(l=0, r=0, t=14, b=0),
            height=65,
            xaxis=dict(visible=True, tickfont=dict(size=7.5, color="#94a3b8"), showgrid=False),
            yaxis=dict(visible=False, zeroline=True, zerolinecolor="rgba(148, 163, 184, 0.4)", zerolinewidth=1),
            paper_bgcolor="#f8fafc",
            plot_bgcolor="#f8fafc"
        )
        st.plotly_chart(
            fig_mini, 
            use_container_width=True, 
            config={"displayModeBar": False}
        )

    st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # 5. SPIKE DYNAMICS & PEAK DATE DETECTION
    # -------------------------------------------------------------
    st.markdown('<div class="ov-card-title">SPIKE DYNAMICS: POSITIVE VS NEGATIVE ANOMALY INVESTIGATION</div>', unsafe_allow_html=True)

    df_daily = df_filtered.groupby([df_filtered["NEWS_DATE"].dt.date, sent_col]).size().unstack(fill_value=0) if ("NEWS_DATE" in df_filtered.columns and sent_col) else pd.DataFrame()
    
    pos_peak_date, pos_peak_count, pos_topic = "-", 0, "-"
    neg_peak_date, neg_peak_count, neg_topic = "-", 0, "-"
    pos_spikes = []
    neg_spikes = []

    if not df_daily.empty:
        df_reset = df_daily.reset_index().rename(columns={"NEWS_DATE": "date_val"})
        MIN_ABSOLUTE_SPIKE = 200

        if "Positive" in df_reset.columns:
            pos_series = df_reset["Positive"]
            pos_max = pos_series.max()
            pos_mean = pos_series.mean()
            pos_std = pos_series.std() if len(pos_series) > 1 else 0

            pos_peak_idx = pos_series.idxmax()
            pos_peak_date_raw = df_reset.loc[pos_peak_idx, "date_val"]
            pos_peak_count = int(pos_max)
            pos_peak_date = pos_peak_date_raw.strftime("%d %B %Y")
            df_pos_peak = df_filtered[(df_filtered["NEWS_DATE"].dt.date == pos_peak_date_raw) & (df_filtered[sent_col] == "Positive")]
            pos_topic = df_pos_peak[topic_col].mode()[0] if topic_col and not df_pos_peak.empty else "General"

            thresh_pos = max(pos_mean + 3 * pos_std, pos_max * 0.65, MIN_ABSOLUTE_SPIKE)
            for i in range(len(df_reset)):
                val = pos_series.iloc[i]
                if val >= thresh_pos:
                    prev_v = pos_series.iloc[i - 1] if i > 0 else 0
                    next_v = pos_series.iloc[i + 1] if i < len(df_reset) - 1 else 0
                    if val >= prev_v and val >= next_v:
                        pos_spikes.append((df_reset.loc[i, "date_val"], val))

        if "Negative" in df_reset.columns:
            neg_series = df_reset["Negative"]
            neg_max = neg_series.max()
            neg_mean = neg_series.mean()
            neg_std = neg_series.std() if len(neg_series) > 1 else 0

            neg_peak_idx = neg_series.idxmax()
            neg_peak_date_raw = df_reset.loc[neg_peak_idx, "date_val"]
            neg_peak_count = int(neg_max)
            neg_peak_date = neg_peak_date_raw.strftime("%d %B %Y")
            df_neg_peak = df_filtered[(df_filtered["NEWS_DATE"].dt.date == neg_peak_date_raw) & (df_filtered[sent_col] == "Negative")]
            neg_topic = df_neg_peak[topic_col].mode()[0] if topic_col and not df_neg_peak.empty else "General"

            thresh_neg = max(neg_mean + 3 * neg_std, neg_max * 0.60, MIN_ABSOLUTE_SPIKE)
            for i in range(len(df_reset)):
                val = neg_series.iloc[i]
                if val >= thresh_neg:
                    prev_v = neg_series.iloc[i - 1] if i > 0 else 0
                    next_v = neg_series.iloc[i + 1] if i < len(df_reset) - 1 else 0
                    if val >= prev_v and val >= next_v:
                        neg_spikes.append((df_reset.loc[i, "date_val"], val))

    sp1, sp2, sp3, sp4 = st.columns(4, gap="medium")
    with sp1:
        st.markdown(f"""
            <div class="spike-metric-card" style="border-left: 4px solid #16a34a !important;">
                <div style="font-size: 0.68rem; font-weight: 800; color: #16a34a;">HIGHEST POSITIVE SPIKE</div>
                <div style="font-size: 1.4rem; font-weight: 800; color: #0f172a; margin: 4px 0;">{pos_peak_count} Articles</div>
                <div style="font-size: 0.72rem; color: #64748b;">{pos_peak_date} • <b>{pos_topic}</b></div>
            </div>
        """, unsafe_allow_html=True)
    with sp2:
        st.markdown(f"""
            <div class="spike-metric-card" style="border-left: 4px solid #16a34a !important;">
                <div style="font-size: 0.68rem; font-weight: 800; color: #16a34a;">POSITIVE MOMENTUM</div>
                <div style="font-size: 1.4rem; font-weight: 800; color: #16a34a; margin: 4px 0;">{pos_count:,} Total</div>
                <div style="font-size: 0.72rem; color: #64748b;">{(pos_count/max(1, total_news)*100):.1f}% Positive Exposure</div>
            </div>
        """, unsafe_allow_html=True)
    with sp3:
        st.markdown(f"""
            <div class="spike-metric-card" style="border-left: 4px solid #dc2626 !important;">
                <div style="font-size: 0.68rem; font-weight: 800; color: #dc2626;">HIGHEST NEGATIVE SPIKE</div>
                <div style="font-size: 1.4rem; font-weight: 800; color: #0f172a; margin: 4px 0;">{neg_peak_count} Articles</div>
                <div style="font-size: 0.72rem; color: #64748b;">{neg_peak_date} • <b>{neg_topic}</b></div>
            </div>
        """, unsafe_allow_html=True)
    with sp4:
        st.markdown(f"""
            <div class="spike-metric-card" style="border-left: 4px solid #dc2626 !important;">
                <div style="font-size: 0.68rem; font-weight: 800; color: #dc2626;">CRISIS MITIGATION NEEDED</div>
                <div style="font-size: 1.4rem; font-weight: 800; color: #dc2626; margin: 4px 0;">{neg_count:,} Total</div>
                <div style="font-size: 0.72rem; color: #64748b;">{(neg_count/max(1, total_news)*100):.1f}% Issues Requiring Response</div>
            </div>
        """, unsafe_allow_html=True)
    st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)
    if not df_daily.empty:
        fig_spike = go.Figure()
        df_reset = df_daily.reset_index().rename(columns={"NEWS_DATE": "date_val"})
        for s_name, s_col in [("Positive", "#16a34a"), ("Neutral", "#94a3b8"), ("Negative", "#dc2626")]:
            if s_name in df_reset.columns:
                fig_spike.add_trace(go.Scatter(
                    x=df_reset["date_val"], y=df_reset[s_name], mode='lines', name=s_name,
                    line=dict(color=s_col, width=2.2, shape='spline')
                ))

        if pos_spikes:
            fig_spike.add_trace(go.Scatter(
                x=[d[0] for d in pos_spikes], y=[d[1] for d in pos_spikes],
                mode='markers', name='Pos Spike',
                marker=dict(size=9, color='#16a34a', symbol='circle', line=dict(color='#ffffff', width=2)),
                hovertemplate="<b>Positive Spike</b><br>Date: %{x}<br>Volume: %{y}<extra></extra>"
            ))

        if neg_spikes:
            fig_spike.add_trace(go.Scatter(
                x=[d[0] for d in neg_spikes], y=[d[1] for d in neg_spikes],
                mode='markers', name='Neg Spike (Crisis)',
                marker=dict(size=10, color='#dc2626', symbol='circle', line=dict(color='#ffffff', width=2)),
                hovertemplate="<b>Negative Crisis Spike</b><br>Date: %{x}<br>Volume: %{y}<extra></extra>"
            ))

        fig_spike.update_layout(
            height=240, margin=dict(l=0, r=0, t=26, b=0),
            paper_bgcolor="#f8fafc", plot_bgcolor="#f8fafc",
            xaxis=dict(showgrid=False, tickfont=dict(size=9.5, color="#64748b")),
            yaxis=dict(showgrid=True, gridcolor="rgba(226, 232, 240, 0.9)", tickfont=dict(size=9, color="#94a3b8")),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=9.5))
        )
        st.plotly_chart(
            fig_spike, 
            use_container_width=True, 
            config={
                "displayModeBar": True,
                "modeBarButtons": [["zoom2d", "pan2d", "resetScale2d"]],
                "displaylogo": False
            }
        )

    st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # 6. SENTIMENT DISTRIBUTION BY TOPIC & KEYWORD CLOUDS
    # -------------------------------------------------------------
    c_dist, c_cloud = st.columns([1, 1], gap="large")
    with c_dist:
        st.markdown('<div class="ov-card-title">SENTIMENT DISTRIBUTION BY TOPIC</div>', unsafe_allow_html=True)
        if topic_col and sent_col and not df_filtered.empty:
            top_t = df_filtered[topic_col].value_counts().head(5).index.tolist()
            df_g = df_filtered[df_filtered[topic_col].isin(top_t)].groupby([topic_col, sent_col]).size().unstack(fill_value=0).reset_index()
            fig_b = go.Figure()
            for s_name, s_color in [("Positive", "#10b981"), ("Neutral", "#94a3b8"), ("Negative", "#ef4444")]:
                if s_name in df_g.columns:
                    fig_b.add_trace(go.Bar(x=df_g[topic_col], y=df_g[s_name], name=s_name.lower(), marker_color=s_color, width=0.22))
            fig_b.update_layout(
                barmode='stack', height=210, margin=dict(l=0, r=0, t=20, b=0),
                paper_bgcolor="#f8fafc", plot_bgcolor="#f8fafc",
                xaxis=dict(showgrid=False, tickfont=dict(size=9.5)),
                yaxis=dict(showgrid=True, gridcolor="rgba(226, 232, 240, 0.9)"),
                legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5, font=dict(size=9.5))
            )
            st.plotly_chart(
                fig_b, 
                use_container_width=True, 
                config={
                    "displayModeBar": True,
                    "modeBarButtons": [["zoom2d", "pan2d", "resetScale2d"]],
                    "displaylogo": False
                }
            )

    with c_cloud:
        st.markdown('<div class="ov-card-title">POSITIVE & NEGATIVE KEYWORD CLOUDS</div>', unsafe_allow_html=True)
        k1, k2 = st.columns(2)
        with k1:
            st.markdown("<span style='font-size: 0.75rem; font-weight: 800; color: #059669;'>Positive Drivers</span>", unsafe_allow_html=True)
            st.markdown("""
                <div style="margin-top: 6px;">
                    <span class="badge-pos">Project</span> <span class="badge-pos">Success</span>
                    <span class="badge-pos">Innovation</span> <span class="badge-pos">Growth</span>
                    <span class="badge-pos">Profit</span> <span class="badge-pos">Achievement</span>
                </div>
            """, unsafe_allow_html=True)
        with k2:
            st.markdown("<span style='font-size: 0.75rem; font-weight: 800; color: #dc2626;'>Negative Triggers</span>", unsafe_allow_html=True)
            st.markdown("""
                <div style="margin-top: 6px;">
                    <span class="badge-neg">Delay</span> <span class="badge-neg">Cost</span>
                    <span class="badge-neg">Problem</span> <span class="badge-neg">Issue</span>
                    <span class="badge-neg">Decline</span> <span class="badge-neg">Risk</span>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom: 26px;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # 7. PEAK DATE ARTICLES INVESTIGATION
    # -------------------------------------------------------------
    st.markdown('<div class="ov-card-title">PEAK DATE ARTICLES INVESTIGATION: TIME DISTRIBUTION & ARTICLE BREAKDOWN</div>', unsafe_allow_html=True)

    # 1. Pilihan Sentimen ditaruh lebih awal untuk menentukan tanggal peak yang relevan
    f_tbl_col1, f_tbl_col2, _ = st.columns([1.6, 1.4, 2.2], gap="medium")

    with f_tbl_col2:
        sel_sentiment = st.selectbox(
            "Filter Sentiment:", 
            options=["All Sentiments", "Positive", "Negative"], 
            index=0, 
            key="tbl_sel_sent"
        )

    # 2. Saring tanggal peak berdasarkan sentimen yang dipilih
    pos_dates_only = [d[0] for d in pos_spikes]
    neg_dates_only = [d[0] for d in neg_spikes]

    if sel_sentiment == "Positive":
        active_spike_dates = sorted(list(set(pos_dates_only)))
    elif sel_sentiment == "Negative":
        active_spike_dates = sorted(list(set(neg_dates_only)))
    else:
        # All Sentiments / Neutral: gabungan tanggal peak
        active_spike_dates = sorted(list(set(pos_dates_only + neg_dates_only)))

    # 3. Dropdown pilihan tanggal peak dinamis
    with f_tbl_col1:
        date_options = ["All Peak Dates"] + [d.strftime("%d %B %Y") for d in active_spike_dates]
        sel_peak_date = st.selectbox(
            "Filter Peak Date:", 
            options=date_options, 
            index=0, 
            key="tbl_sel_peak_date"
        )

    # 4. Filter artikel hanya dari tanggal peak aktif
    if active_spike_dates and "NEWS_DATE" in df_filtered.columns:
        df_spike_articles = df_filtered[df_filtered["NEWS_DATE"].dt.date.isin(active_spike_dates)].copy()
    else:
        df_spike_articles = pd.DataFrame()

    df_table = df_spike_articles.copy()
    if not df_table.empty and "NEWS_DATE" in df_table.columns:
        if sel_peak_date != "All Peak Dates":
            df_table = df_table[df_table["NEWS_DATE"].dt.strftime("%d %B %Y") == sel_peak_date]

        if sel_sentiment != "All Sentiments" and sent_col:
            df_table = df_table[df_table[sent_col].astype(str).str.lower().str.contains(sel_sentiment.lower()[:3])]

    # 5. Visualisasi Distribusi Waktu
    if not df_table.empty and "NEWS_DATE" in df_table.columns:
        all_sent_configs = [("Positive", "#16a34a"), ("Neutral", "#94a3b8"), ("Negative", "#dc2626")]
        if sel_sentiment != "All Sentiments":
            active_sent_configs = [item for item in all_sent_configs if item[0].lower() == sel_sentiment.lower()]
        else:
            active_sent_configs = all_sent_configs

        if sel_peak_date != "All Peak Dates":
            df_table["HOUR"] = df_table["NEWS_DATE"].dt.hour
            hourly_counts = df_table.groupby(["HOUR", sent_col]).size().unstack(fill_value=0).reset_index()
            
            full_hours = pd.DataFrame({"HOUR": list(range(24))})
            hourly_df = pd.merge(full_hours, hourly_counts, on="HOUR", how="left").fillna(0)
            hourly_df["HOUR_LABEL"] = hourly_df["HOUR"].apply(lambda h: f"{h:02d}:00")

            sum_series = df_table.groupby("HOUR").size()
            peak_h = sum_series.idxmax() if not sum_series.empty else 0
            peak_h_cnt = sum_series.max() if not sum_series.empty else 0

            st.markdown(f"""
                <div style="font-size: 0.72rem; color: #475569; margin-bottom: 6px; font-weight: 600;">
                    Peak Publication Hour on <b>{sel_peak_date}</b>: <b style="color:#2563eb;">{peak_h:02d}:00 - {peak_h:02d}:59</b> ({peak_h_cnt} articles)
                </div>
            """, unsafe_allow_html=True)

            fig_time = go.Figure()
            for s_name, s_color in active_sent_configs:
                if s_name in hourly_df.columns:
                    fig_time.add_trace(go.Bar(
                        x=hourly_df["HOUR_LABEL"], 
                        y=hourly_df[s_name], 
                        name=s_name, 
                        marker_color=s_color
                    ))

            fig_time.update_layout(
                barmode="stack", 
                height=180, 
                margin=dict(l=0, r=0, t=10, b=0),
                paper_bgcolor="#f8fafc", 
                plot_bgcolor="#f8fafc",
                xaxis=dict(showgrid=False, tickfont=dict(size=8.5, color="#64748b")),
                yaxis=dict(showgrid=True, gridcolor="rgba(226, 232, 240, 0.9)", tickfont=dict(size=8.5, color="#94a3b8")),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=9))
            )
            st.plotly_chart(
                fig_time, 
                use_container_width=True, 
                config={"displayModeBar": False}
            )

        else:
            date_bar_counts = df_table.groupby([df_table["NEWS_DATE"].dt.strftime("%d %b %Y"), sent_col]).size().unstack(fill_value=0).reset_index()
            date_bar_counts.rename(columns={"NEWS_DATE": "DATE_LABEL"}, inplace=True)

            fig_time = go.Figure()
            for s_name, s_color in active_sent_configs:
                if s_name in date_bar_counts.columns:
                    fig_time.add_trace(go.Bar(
                        x=date_bar_counts["DATE_LABEL"], 
                        y=date_bar_counts[s_name], 
                        name=s_name, 
                        marker_color=s_color
                    ))

            fig_time.update_layout(
                barmode="stack", 
                height=180, 
                margin=dict(l=0, r=0, t=10, b=0),
                paper_bgcolor="#f8fafc", 
                plot_bgcolor="#f8fafc",
                xaxis=dict(showgrid=False, tickfont=dict(size=8.5, color="#64748b")),
                yaxis=dict(showgrid=True, gridcolor="rgba(226, 232, 240, 0.9)", tickfont=dict(size=8.5, color="#94a3b8")),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=9))
            )
            st.plotly_chart(
                fig_time, 
                use_container_width=True, 
                config={"displayModeBar": False}
            )

    st.markdown("<div style='margin-bottom: 14px;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # 8. ARTICLE BREAKDOWN TABLE
    # -------------------------------------------------------------
    if title_col and not df_table.empty:
        if "NEWS_DATE" in df_table.columns:
            df_table = df_table.sort_values(by="NEWS_DATE", ascending=False)

        df_show = pd.DataFrame()
        df_show["Article"] = df_table[title_col].astype(str).str.replace(r'[\r\n]+', ' ', regex=True)

        if media_col:
            df_show["Media Source"] = (
                df_table[media_col].astype(str)
                .str.replace("https://", "", regex=False)
                .str.replace("http://", "", regex=False)
                .str.replace("www.", "", regex=False)
                .str.split("/").str[0]
            )
        else:
            df_show["Media Source"] = "N/A"

        if "NEWS_DATE" in df_table.columns:
            df_show["Date"] = pd.to_datetime(df_table["NEWS_DATE"], errors="coerce").dt.strftime("%Y-%m-%d")
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
        st.info("No articles match the selected peak date or sentiment filter.")