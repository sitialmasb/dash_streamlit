import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re
import ast
import textwrap
import html


# =============================================================
# HELPER: HTML RENDERING
# =============================================================
def render_html(content):
    """
    Render custom HTML using Streamlit's HTML renderer.
    This prevents multiline HTML from appearing as code text.
    """
    content = textwrap.dedent(content).strip()
    st.html(content)


# =============================================================
# HELPER: SENTIMENT STANDARDIZATION
# =============================================================
def standardize_sentiment(value):
    value = str(value).strip().lower()

    if value in {
        "positive",
        "positif",
        "pos",
        "good",
        "baik",
        "1"
    }:
        return "Positive"

    if value in {
        "negative",
        "negatif",
        "neg",
        "bad",
        "buruk",
        "-1"
    }:
        return "Negative"

    if value in {
        "neutral",
        "netral",
        "neu",
        "0"
    }:
        return "Neutral"

    if "positive" in value or "positif" in value:
        return "Positive"

    if "negative" in value or "negatif" in value:
        return "Negative"

    return "Neutral"


# =============================================================
# HELPER: EXTRACT KEYWORDS
# =============================================================
def extract_keywords(series):
    """
    Extract keywords from KEYWORD column.

    Supported formats:

    Project
    Project, Growth, Investment
    Project; Growth; Investment
    Project | Growth | Investment
    Project
    Growth
    Investment

    ['Project', 'Growth', 'Investment']
    """

    keywords = []

    if series is None:
        return keywords

    for value in series.dropna():

        text = str(value).strip()

        if not text:
            continue

        # -----------------------------------------------------
        # Python list format
        # -----------------------------------------------------
        if text.startswith("[") and text.endswith("]"):

            try:
                parsed = ast.literal_eval(text)

                if isinstance(
                    parsed,
                    (list, tuple, set)
                ):

                    for item in parsed:

                        item = str(item).strip()

                        if (
                            item
                            and item.lower()
                            not in {
                                "nan",
                                "none",
                                "null",
                                "-"
                            }
                        ):
                            keywords.append(item)

                    continue

            except Exception:
                pass

        # -----------------------------------------------------
        # Multiple separator format
        # -----------------------------------------------------
        split_values = re.split(
            r"[,;|\n]+",
            text
        )

        for item in split_values:

            item = item.strip()

            if not item:
                continue

            if item.lower() in {
                "nan",
                "none",
                "null",
                "-"
            }:
                continue

            keywords.append(item)

    return keywords


# =============================================================
# HELPER: GET TOP KEYWORD
# =============================================================
def get_top_keyword(
    df,
    keyword_col,
    sentiment=None
):
    """
    Return the single most frequent keyword.

    If sentiment is provided, only articles with that
    sentiment are considered.
    """

    if (
        df is None
        or df.empty
        or not keyword_col
    ):
        return None, 0

    df_keyword = df.copy()

    # ---------------------------------------------------------
    # Filter sentiment
    # ---------------------------------------------------------
    if sentiment is not None:

        if "SENTIMENT" in df_keyword.columns:

            df_keyword = df_keyword[
                df_keyword[
                    "SENTIMENT"
                ]
                .astype(str)
                .str.strip()
                .str.lower()
                == sentiment.lower()
            ]

    if df_keyword.empty:
        return None, 0

    # ---------------------------------------------------------
    # Extract keywords
    # ---------------------------------------------------------
    raw_keywords = extract_keywords(
        df_keyword[keyword_col]
    )

    if not raw_keywords:
        return None, 0

    normalized_keywords = []
    display_lookup = {}

    for keyword in raw_keywords:

        clean_keyword = str(
            keyword
        ).strip()

        if not clean_keyword:
            continue

        normalized = (
            clean_keyword.lower()
        )

        if normalized in {
            "nan",
            "none",
            "null",
            "-"
        }:
            continue

        normalized_keywords.append(
            normalized
        )

        if normalized not in display_lookup:

            display_lookup[
                normalized
            ] = clean_keyword

    if not normalized_keywords:
        return None, 0

    counts = (
        pd.Series(
            normalized_keywords
        )
        .value_counts()
    )

    top_keyword = counts.index[0]
    top_count = int(
        counts.iloc[0]
    )

    return (
        display_lookup.get(
            top_keyword,
            top_keyword
        ),
        top_count
    )


# =============================================================
# HELPER: PERIOD CALLBACK
# =============================================================
def update_period_from_preset():
    """
    Update the calendar range when the preset period changes.
    """

    if (
        "sa_period" not in st.session_state
        or "sa_dataset_max_date"
        not in st.session_state
    ):
        return

    latest_date = pd.Timestamp(
        st.session_state[
            "sa_dataset_max_date"
        ]
    )

    selected_period = (
        st.session_state[
            "sa_period"
        ]
    )

    if selected_period == "1 Month":

        start_date = (
            latest_date
            - pd.DateOffset(
                months=1
            )
        ).date()

    elif selected_period == "3 Months":

        start_date = (
            latest_date
            - pd.DateOffset(
                months=3
            )
        ).date()

    elif selected_period == "1 Year":

        start_date = (
            latest_date
            - pd.DateOffset(
                years=1
            )
        ).date()

    else:

        return

    st.session_state[
        "sa_date_range"
    ] = (
        start_date,
        latest_date.date()
    )


# =============================================================
# MAIN PAGE
# =============================================================
def render_sentiment_analysis_page(
    df_raw: pd.DataFrame
):

    # =========================================================
    # 0. CHECK DATA
    # =========================================================
    if (
        df_raw is None
        or df_raw.empty
    ):

        st.info(
            "Data is not available."
        )

        return

    df_clean = df_raw.copy()

    # =========================================================
    # 1. STANDARDIZE DATE
    # =========================================================
    if "NEWS_DATE" in df_clean.columns:

        df_clean[
            "NEWS_DATE"
        ] = pd.to_datetime(
            df_clean[
                "NEWS_DATE"
            ],
            errors="coerce"
        )

    elif "news_date" in df_clean.columns:

        df_clean[
            "NEWS_DATE"
        ] = pd.to_datetime(
            df_clean[
                "news_date"
            ],
            errors="coerce"
        )

    # =========================================================
    # 2. DATASET COLUMNS
    # =========================================================
    sent_col = (
        "SENTIMENT"
        if "SENTIMENT"
        in df_clean.columns
        else None
    )

    topic_col = (
        "ISSUE_TOPIC"
        if "ISSUE_TOPIC"
        in df_clean.columns
        else None
    )

    subtopic_col = (
        "ISSUE_SUBTOPIC"
        if "ISSUE_SUBTOPIC"
        in df_clean.columns
        else None
    )

    tier_col = (
        "TIER"
        if "TIER"
        in df_clean.columns
        else None
    )

    keyword_col = (
        "KEYWORD"
        if "KEYWORD"
        in df_clean.columns
        else None
    )

    media_col = next(
        (
            c
            for c in [
                "CLEAN_URL",
                "clean_url",
                "MEDIA",
                "media",
                "SOURCE",
                "source",
                "MEDIA_DOMAIN"
            ]
            if c in df_clean.columns
        ),
        None
    )

    title_col = next(
        (
            c
            for c in [
                "NEWS",
                "NEWS_SUMMARY",
                "news_title",
                "title",
                "headline"
            ]
            if c in df_clean.columns
        ),
        None
    )

    # =========================================================
    # 3. STANDARDIZE SENTIMENT
    # =========================================================
    if sent_col:

        df_clean[
            sent_col
        ] = df_clean[
            sent_col
        ].apply(
            standardize_sentiment
        )

    # =========================================================
    # 4. CSS
    # =========================================================
    render_html(
        """
        <style>

        .sa-card-title {
            font-size: 0.78rem;
            font-weight: 800;
            color: #475569;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            margin-bottom: 12px;
        }

        .formula-pill-noborder {
            border-radius: 8px;
            padding: 8px 12px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-width: 72px;
            border: none;
        }

        .spike-metric-card {
            background: #ffffff;
            border: none;
            border-radius: 12px;
            padding: 14px 16px;
            box-shadow:
                0 4px 14px
                rgba(15, 23, 42, 0.03);
            min-height: 105px;
            box-sizing: border-box;
        }

        .keyword-card {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 12px 14px;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 10px;
            box-sizing: border-box;
        }

        .keyword-label {
            font-size: 0.68rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        .keyword-name {
            font-size: 1rem;
            font-weight: 800;
            color: #0f172a;
            flex: 1;
        }

        .keyword-count {
            font-size: 0.70rem;
            font-weight: 700;
            color: #64748b;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 4px 9px;
        }

        .period-info {
            font-size: 0.70rem;
            color: #64748b;
            margin-top: 4px;
        }

        </style>
        """
    )

    # =========================================================
    # 5. DATASET DATE LIMITS
    # =========================================================
    valid_dates = (
        df_clean[
            "NEWS_DATE"
        ]
        .dropna()
        if "NEWS_DATE"
        in df_clean.columns
        else pd.Series(
            dtype="datetime64[ns]"
        )
    )

    if valid_dates.empty:

        dataset_min_date = None
        dataset_max_date = None

    else:

        dataset_min_date = (
            valid_dates.min()
            .date()
        )

        dataset_max_date = (
            valid_dates.max()
            .date()
        )

        st.session_state[
            "sa_dataset_max_date"
        ] = dataset_max_date

    # =========================================================
    # 6. PERIOD OPTIONS
    # =========================================================
    period_options = [
        "1 Month",
        "3 Months",
        "1 Year"
    ]

    if (
        "sa_period"
        not in st.session_state
    ):

        st.session_state[
            "sa_period"
        ] = "1 Month"

    selected_period = (
        st.session_state[
            "sa_period"
        ]
    )

    # =========================================================
    # 7. INITIAL CALENDAR RANGE
    # =========================================================
    if (
        dataset_min_date is not None
        and dataset_max_date is not None
    ):

        if (
            "sa_date_range"
            not in st.session_state
        ):

            initial_start = (
                pd.Timestamp(
                    dataset_max_date
                )
                - pd.DateOffset(
                    months=1
                )
            ).date()

            initial_start = max(
                initial_start,
                dataset_min_date
            )

            st.session_state[
                "sa_date_range"
            ] = (
                initial_start,
                dataset_max_date
            )

    # =========================================================
    # 8. TIER OPTIONS
    # =========================================================
    if tier_col:

        tier_opts = [
            "All Media Tier"
        ] + sorted(
            df_clean[
                tier_col
            ]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

    else:

        tier_opts = [
            "All Media Tier"
        ]

    if (
        "sa_tier"
        not in st.session_state
    ):

        st.session_state[
            "sa_tier"
        ] = "All Media Tier"

    selected_tier = (
        st.session_state[
            "sa_tier"
        ]
    )

    # =========================================================
    # TOP SPACING
    # =========================================================
    # Add a little breathing room between the fixed top bar
    # and the Sentiment Analysis content.
    st.markdown(
        "<div style='height:18px;'></div>",
        unsafe_allow_html=True
    )

    # =========================================================
    # 9. HEADER
    # =========================================================
    c_hdr, c_period, c_tier = st.columns(
        [2.45, 1.2, 1.2],
        gap="medium"
    )

    # ---------------------------------------------------------
    # HEADER TITLE
    # ---------------------------------------------------------
    with c_hdr:

        # Determine accent from NSS later.
        render_html(
            """
            <div style="
                display:flex;
                align-items:center;
                gap:12px;
                min-height:48px;
            ">

                <div style="
                    width:8px;
                    height:48px;
                    background:
                        linear-gradient(
                            180deg,
                            #34d399 0%,
                            #16a34a 100%
                        );
                    border-radius:4px;
                    flex-shrink:0;
                "></div>

                <div style="
                    display:flex;
                    flex-direction:column;
                    justify-content:center;
                ">

                    <h2 style="
                        margin:0 0 1px 0;
                        padding:0;
                        font-size:2rem;
                        line-height:1.25;
                        color:#0f172a;
                        font-weight:800;
                        letter-spacing:-0.01em;
                    ">
                        SENTIMENT
                        <span style="
                            color:#16a34a;
                            font-style:italic;
                        ">
                            ANALYSIS
                        </span>
                    </h2>

                    <span style="
                        margin:0;
                        padding:0;
                        font-size:0.70rem;
                        line-height:1.1;
                        letter-spacing:0.08em;
                        color:#64748b;
                        font-weight:700;
                        text-transform:uppercase;
                    ">
                        SENTIMENT TRENDS
                        & SPIKE ANALYSIS
                    </span>

                </div>

            </div>
            """
        )

    # ---------------------------------------------------------
    # PERIOD PRESET
    # ---------------------------------------------------------
    with c_period:

        st.selectbox(
            "Period:",
            options=period_options,
            key="sa_period",
            label_visibility="collapsed",
            on_change=update_period_from_preset
        )

    # ---------------------------------------------------------
    # TIER
    # ---------------------------------------------------------
    with c_tier:

        tier_idx = (
            tier_opts.index(
                selected_tier
            )
            if selected_tier
            in tier_opts
            else 0
        )

        st.selectbox(
            "Tier:",
            options=tier_opts,
            index=tier_idx,
            key="sa_tier",
            label_visibility="collapsed"
        )

    # =========================================================
    # 10. CALENDAR FILTER
    # =========================================================
    if (
        dataset_min_date is not None
        and dataset_max_date is not None
    ):

        selected_range = st.date_input(
            "Select Period",
            value=st.session_state[
                "sa_date_range"
            ],
            min_value=dataset_min_date,
            max_value=dataset_max_date,
            key="sa_date_range"
        )

        if isinstance(
            selected_range,
            tuple
        ):

            if len(selected_range) == 2:

                period_start = pd.Timestamp(
                    selected_range[0]
                )

                period_end = (
                    pd.Timestamp(
                        selected_range[1]
                    )
                    + pd.Timedelta(
                        days=1
                    )
                    - pd.Timedelta(
                        microseconds=1
                    )
                )

            else:

                period_start = pd.Timestamp(
                    selected_range[0]
                )

                period_end = (
                    period_start
                    + pd.Timedelta(
                        days=1
                    )
                    - pd.Timedelta(
                        microseconds=1
                    )
                )

        else:

            period_start = pd.Timestamp(
                selected_range
            )

            period_end = (
                period_start
                + pd.Timedelta(
                    days=1
                )
                - pd.Timedelta(
                    microseconds=1
                )
            )

    else:

        period_start = None
        period_end = None

    # =========================================================
    # 11. APPLY PERIOD FILTER
    # =========================================================
    df_filtered = df_clean.copy()

    if (
        period_start is not None
        and period_end is not None
        and "NEWS_DATE"
        in df_filtered.columns
    ):

        df_filtered = df_filtered[
            (
                df_filtered[
                    "NEWS_DATE"
                ]
                >= period_start
            )
            &
            (
                df_filtered[
                    "NEWS_DATE"
                ]
                <= period_end
            )
        ].copy()

    # =========================================================
    # 12. APPLY TIER FILTER
    # =========================================================
    if (
        selected_tier
        != "All Media Tier"
        and tier_col
    ):

        df_filtered = df_filtered[
            df_filtered[
                tier_col
            ]
            .astype(str)
            == selected_tier
        ].copy()

    # =========================================================
    # 13. NSS
    # =========================================================
    total_news = len(
        df_filtered
    )

    if sent_col:

        sentiment_series = (
            df_filtered[
                sent_col
            ]
            .astype(str)
            .str.strip()
            .str.lower()
        )

        pos_count = int(
            (
                sentiment_series
                == "positive"
            ).sum()
        )

        neg_count = int(
            (
                sentiment_series
                == "negative"
            ).sum()
        )

    else:

        pos_count = 0
        neg_count = 0

    if total_news > 0:

        nss_score = int(
            round(
                (
                    (
                        pos_count
                        - neg_count
                    )
                    / total_news
                )
                * 100
            )
        )

    else:

        nss_score = 0

    # =========================================================
    # 14. NSS COLORS
    # =========================================================
    if nss_score < 0:

        bar_gradient = (
            "linear-gradient("
            "180deg, #f87171 0%, "
            "#dc2626 100%)"
        )

        accent_color = "#dc2626"

        nss_card_bg = "#fef2f2"
        nss_card_border = "#fca5a5"
        nss_title_color = "#991b1b"
        nss_text_color = "#dc2626"
        nss_badge_bg = "#fee2e2"

        nss_str = (
            f"{nss_score}%"
        )

    else:

        bar_gradient = (
            "linear-gradient("
            "180deg, #34d399 0%, "
            "#16a34a 100%)"
        )

        accent_color = "#16a34a"

        nss_card_bg = "#f0fdf4"
        nss_card_border = "#86efac"
        nss_title_color = "#166534"
        nss_text_color = "#15803d"
        nss_badge_bg = "#dcfce7"

        nss_str = (
            f"+{nss_score}%"
        )

    # =========================================================
    # 15. NSS BANNER
    # =========================================================
    c_score, c_formula, c_mini = st.columns(
        [1.15, 2.35, 1.1],
        gap="medium"
    )

    # ---------------------------------------------------------
    # SCORE
    # ---------------------------------------------------------
    with c_score:

        render_html(
            f"""
            <div style="
                background:{nss_card_bg};
                border:1.5px solid
                    {nss_card_border};
                border-radius:12px;
                padding:12px 16px;
                height:100px;
                display:flex;
                flex-direction:column;
                justify-content:space-between;
                box-sizing:border-box;
            ">

                <span style="
                    font-size:0.68rem;
                    font-weight:800;
                    color:{nss_title_color};
                    letter-spacing:0.04em;
                ">
                    NET SENTIMENT SCORE
                </span>

                <div style="
                    font-size:2.2rem;
                    font-weight:800;
                    color:{nss_text_color};
                    line-height:1;
                ">
                    {nss_str}
                </div>

                <div style="
                    font-size:0.68rem;
                    color:#64748b;
                ">
                    {selected_period}
                </div>

            </div>
            """
        )

    # ---------------------------------------------------------
    # FORMULA
    # ---------------------------------------------------------
    with c_formula:

        render_html(
            f"""
            <div style="
                display:flex;
                align-items:center;
                justify-content:center;
                height:100px;
                gap:8px;
            ">

                <div
                    class="formula-pill-noborder"
                    style="
                        background:#ecfdf5;
                    "
                >

                    <span style="
                        font-size:0.68rem;
                        font-weight:700;
                        color:#059669;
                    ">
                        Positive
                    </span>

                    <span style="
                        font-size:1.15rem;
                        font-weight:800;
                        color:#0f172a;
                    ">
                        {pos_count:,}
                    </span>

                </div>

                <span style="
                    font-size:1.3rem;
                    font-weight:800;
                    color:#94a3b8;
                ">
                    −
                </span>

                <div
                    class="formula-pill-noborder"
                    style="
                        background:#fef2f2;
                    "
                >

                    <span style="
                        font-size:0.68rem;
                        font-weight:700;
                        color:#dc2626;
                    ">
                        Negative
                    </span>

                    <span style="
                        font-size:1.15rem;
                        font-weight:800;
                        color:#0f172a;
                    ">
                        {neg_count:,}
                    </span>

                </div>

                <span style="
                    font-size:1.3rem;
                    font-weight:800;
                    color:#94a3b8;
                ">
                    ÷
                </span>

                <div
                    class="formula-pill-noborder"
                    style="
                        background:#eff6ff;
                    "
                >

                    <span style="
                        font-size:0.68rem;
                        font-weight:700;
                        color:#2563eb;
                    ">
                        Total
                    </span>

                    <span style="
                        font-size:1.15rem;
                        font-weight:800;
                        color:#0f172a;
                    ">
                        {total_news:,}
                    </span>

                </div>

                <span style="
                    font-size:1rem;
                    font-weight:800;
                    color:#94a3b8;
                ">
                    ×100
                </span>

                <div style="
                    background:{nss_badge_bg};
                    color:{nss_text_color};
                    border-radius:8px;
                    padding:10px 14px;
                    font-size:1.2rem;
                    font-weight:800;
                    white-space:nowrap;
                ">
                    = {nss_str}
                </div>

            </div>
            """
        )

    # ---------------------------------------------------------
    # MONTHLY NSS
    #
    # IMPORTANT:
    # Use YEAR + MONTH instead of only MONTH NUMBER.
    # This fixes the 1-Year bug where (for example) Sep 2025
    # and Sep 2026 were incorrectly combined.
    # ---------------------------------------------------------
    with c_mini:

        render_html(
            """
            <div style="
                text-align:right;
                margin-bottom:2px;
            ">
                <span style="
                    font-size:0.68rem;
                    font-weight:800;
                    color:#475569;
                    text-transform:uppercase;
                    letter-spacing:0.04em;
                ">
                    Monthly NSS
                </span>
            </div>
            """
        )

        month_labels = []
        month_scores = []
        month_colors = []

        if (
            "NEWS_DATE" in df_clean.columns
            and sent_col
            and not valid_dates.empty
            and period_start is not None
            and period_end is not None
        ):

            # -------------------------------------------------
            # Build actual calendar months inside the selected
            # period. This preserves the year information.
            # -------------------------------------------------
            first_month = (
                period_start
                .to_period("M")
            )

            last_month = (
                period_end
                .to_period("M")
            )

            month_periods = pd.period_range(
                start=first_month,
                end=last_month,
                freq="M"
            )

            df_month = (
                df_clean
                .dropna(
                    subset=["NEWS_DATE"]
                )
                .copy()
            )

            # -------------------------------------------------
            # Apply media tier only.
            # -------------------------------------------------
            if (
                selected_tier != "All Media Tier"
                and tier_col
            ):

                df_month = df_month[
                    df_month[
                        tier_col
                    ]
                    .astype(str)
                    == selected_tier
                ].copy()

            # -------------------------------------------------
            # Apply the same selected calendar period.
            # -------------------------------------------------
            df_month = df_month[
                (
                    df_month[
                        "NEWS_DATE"
                    ]
                    >= period_start
                )
                &
                (
                    df_month[
                        "NEWS_DATE"
                    ]
                    <= period_end
                )
            ].copy()

            if not df_month.empty:

                df_month[
                    "MONTH_PERIOD"
                ] = (
                    df_month[
                        "NEWS_DATE"
                    ].dt.to_period("M")
                )

            # -------------------------------------------------
            # Calculate NSS separately for every real month.
            # -------------------------------------------------
            for month_period in month_periods:

                label = (
                    month_period
                    .strftime("%b %Y")
                )

                month_labels.append(
                    label
                )

                if df_month.empty:

                    month_scores.append(
                        0
                    )

                    month_colors.append(
                        "#cbd5e1"
                    )

                    continue

                df_m = df_month[
                    df_month[
                        "MONTH_PERIOD"
                    ]
                    == month_period
                ]

                if df_m.empty:

                    month_scores.append(
                        0
                    )

                    month_colors.append(
                        "#cbd5e1"
                    )

                    continue

                total_m = len(
                    df_m
                )

                month_sent = (
                    df_m[
                        sent_col
                    ]
                    .astype(str)
                    .str.strip()
                    .str.lower()
                )

                pos_m = int(
                    (
                        month_sent
                        == "positive"
                    ).sum()
                )

                neg_m = int(
                    (
                        month_sent
                        == "negative"
                    ).sum()
                )

                score_m = int(
                    round(
                        (
                            (
                                pos_m
                                - neg_m
                            )
                            / total_m
                        )
                        * 100
                    )
                )

                month_scores.append(
                    score_m
                )

                month_colors.append(
                    (
                        "#dc2626"
                        if score_m < 0
                        else "#16a34a"
                    )
                )

        # -----------------------------------------------------
        # Fallback if there is no usable date range.
        # -----------------------------------------------------
        if not month_labels:

            month_labels = ["N/A"]
            month_scores = [0]
            month_colors = ["#cbd5e1"]

        fig_month = go.Figure(
            go.Bar(
                x=month_labels,
                y=month_scores,
                marker_color=month_colors,
                marker_line_width=0,
                hovertemplate=(
                    "<b>%{x}</b>"
                    "<br>NSS: %{y}%"
                    "<extra></extra>"
                )
            )
        )

        # -----------------------------------------------------
        # Keep the compact chart but make labels readable when
        # the selected period is 1 year.
        # -----------------------------------------------------
        if len(month_labels) <= 4:

            tick_font_size = 7.5

        elif len(month_labels) <= 8:

            tick_font_size = 6.8

        else:

            tick_font_size = 6

        fig_month.update_layout(
            height=70,
            margin=dict(
                l=0,
                r=0,
                t=14,
                b=0
            ),
            xaxis=dict(
                visible=True,
                tickfont=dict(
                    size=tick_font_size,
                    color="#94a3b8"
                ),
                showgrid=False,
                tickangle=0
            ),
            yaxis=dict(
                visible=False,
                zeroline=True,
                zerolinecolor=(
                    "rgba(148, 163, 184, 0.4)"
                )
            ),
            paper_bgcolor="#f8fafc",
            plot_bgcolor="#f8fafc"
        )

        st.plotly_chart(
            fig_month,
            use_container_width=True,
            config={
                "displayModeBar": False
            }
        )

    st.markdown(
        "<div style='margin-bottom:24px;'></div>",
        unsafe_allow_html=True
    )

    # =========================================================
    # 16. SENTIMENT SPIKES
    # =========================================================
    render_html(
        """
        <div class="sa-card-title">
            SENTIMENT SPIKES
        </div>
        """
    )

    # =========================================================
    # 17. DAILY SENTIMENT DATA
    # =========================================================
    if (
        "NEWS_DATE"
        in df_filtered.columns
        and sent_col
        and not df_filtered.empty
    ):

        df_daily_base = (
            df_filtered
            .dropna(
                subset=[
                    "NEWS_DATE"
                ]
            )
            .copy()
        )

        df_daily_base[
            "DATE_ONLY"
        ] = (
            df_daily_base[
                "NEWS_DATE"
            ].dt.date
        )

        df_daily = (
            df_daily_base
            .groupby(
                [
                    "DATE_ONLY",
                    sent_col
                ]
            )
            .size()
            .unstack(
                fill_value=0
            )
        )

    else:

        df_daily = pd.DataFrame()

    # =========================================================
    # 18. DEFAULT SPIKE VALUES
    # =========================================================
    pos_peak_date = "-"
    pos_peak_date_raw = None
    pos_peak_count = 0
    pos_peak_is_spike = False
    pos_topic = "-"

    neg_peak_date = "-"
    neg_peak_date_raw = None
    neg_peak_count = 0
    neg_peak_is_spike = False
    neg_topic = "-"

    pos_spikes = []
    neg_spikes = []

    # =========================================================
    # 19. SPIKE DETECTION
    # =========================================================
    if not df_daily.empty:

        df_reset = (
            df_daily
            .reset_index()
            .rename(
                columns={
                    "DATE_ONLY":
                    "date_val"
                }
            )
        )

        # -----------------------------------------------------
        # Adaptive threshold
        #
        # 200 is retained as an absolute upper floor.
        # -----------------------------------------------------
        MIN_ABSOLUTE_SPIKE = 200

        # =====================================================
        # POSITIVE
        # =====================================================
        if (
            "Positive"
            in df_reset.columns
        ):

            pos_series = (
                df_reset[
                    "Positive"
                ]
                .astype(float)
            )

            pos_max = float(
                pos_series.max()
            )

            pos_mean = float(
                pos_series.mean()
            )

            pos_std = float(
                pos_series.std()
                if len(pos_series) > 1
                else 0
            )

            pos_peak_idx = (
                pos_series.idxmax()
            )

            pos_peak_date_raw = (
                df_reset.loc[
                    pos_peak_idx,
                    "date_val"
                ]
            )

            pos_peak_count = int(
                pos_max
            )

            pos_peak_date = (
                pos_peak_date_raw
                .strftime(
                    "%d %B %Y"
                )
            )

            # -------------------------------------------------
            # Topic at highest positive volume
            # -------------------------------------------------
            if topic_col:

                df_pos_peak = (
                    df_filtered[
                        (
                            df_filtered[
                                "NEWS_DATE"
                            ].dt.date
                            == pos_peak_date_raw
                        )
                        &
                        (
                            df_filtered[
                                sent_col
                            ]
                            == "Positive"
                        )
                    ]
                )

                if not df_pos_peak.empty:

                    mode_topic = (
                        df_pos_peak[
                            topic_col
                        ]
                        .dropna()
                        .astype(str)
                        .mode()
                    )

                    if not mode_topic.empty:

                        pos_topic = (
                            mode_topic.iloc[0]
                        )

            # -------------------------------------------------
            # Positive threshold
            # -------------------------------------------------
            pos_threshold = max(
                pos_mean
                + 3 * pos_std,
                pos_max * 0.65,
                MIN_ABSOLUTE_SPIKE
            )

            for i in range(
                len(df_reset)
            ):

                value = float(
                    pos_series.iloc[i]
                )

                if value >= pos_threshold:

                    previous_value = (
                        float(
                            pos_series.iloc[
                                i - 1
                            ]
                        )
                        if i > 0
                        else 0
                    )

                    next_value = (
                        float(
                            pos_series.iloc[
                                i + 1
                            ]
                        )
                        if i <
                        len(df_reset) - 1
                        else 0
                    )

                    if (
                        value >= previous_value
                        and value >= next_value
                    ):

                        pos_spikes.append(
                            (
                                df_reset.loc[
                                    i,
                                    "date_val"
                                ],
                                value
                            )
                        )

            pos_peak_is_spike = any(
                date == pos_peak_date_raw
                for date, _
                in pos_spikes
            )

        # =====================================================
        # NEGATIVE
        # =====================================================
        if (
            "Negative"
            in df_reset.columns
        ):

            neg_series = (
                df_reset[
                    "Negative"
                ]
                .astype(float)
            )

            neg_max = float(
                neg_series.max()
            )

            neg_mean = float(
                neg_series.mean()
            )

            neg_std = float(
                neg_series.std()
                if len(neg_series) > 1
                else 0
            )

            neg_peak_idx = (
                neg_series.idxmax()
            )

            neg_peak_date_raw = (
                df_reset.loc[
                    neg_peak_idx,
                    "date_val"
                ]
            )

            neg_peak_count = int(
                neg_max
            )

            neg_peak_date = (
                neg_peak_date_raw
                .strftime(
                    "%d %B %Y"
                )
            )

            # -------------------------------------------------
            # Topic at highest negative volume
            # -------------------------------------------------
            if topic_col:

                df_neg_peak = (
                    df_filtered[
                        (
                            df_filtered[
                                "NEWS_DATE"
                            ].dt.date
                            == neg_peak_date_raw
                        )
                        &
                        (
                            df_filtered[
                                sent_col
                            ]
                            == "Negative"
                        )
                    ]
                )

                if not df_neg_peak.empty:

                    mode_topic = (
                        df_neg_peak[
                            topic_col
                        ]
                        .dropna()
                        .astype(str)
                        .mode()
                    )

                    if not mode_topic.empty:

                        neg_topic = (
                            mode_topic.iloc[0]
                        )

            # -------------------------------------------------
            # Negative threshold
            # -------------------------------------------------
            neg_threshold = max(
                neg_mean
                + 3 * neg_std,
                neg_max * 0.60,
                MIN_ABSOLUTE_SPIKE
            )

            for i in range(
                len(df_reset)
            ):

                value = float(
                    neg_series.iloc[i]
                )

                if value >= neg_threshold:

                    previous_value = (
                        float(
                            neg_series.iloc[
                                i - 1
                            ]
                        )
                        if i > 0
                        else 0
                    )

                    next_value = (
                        float(
                            neg_series.iloc[
                                i + 1
                            ]
                        )
                        if i <
                        len(df_reset) - 1
                        else 0
                    )

                    if (
                        value >= previous_value
                        and value >= next_value
                    ):

                        neg_spikes.append(
                            (
                                df_reset.loc[
                                    i,
                                    "date_val"
                                ],
                                value
                            )
                        )

            neg_peak_is_spike = any(
                date == neg_peak_date_raw
                for date, _
                in neg_spikes
            )

    # =========================================================
    # 20. SPIKE SUMMARY CARDS
    # =========================================================
    sp1, sp2, sp3 = st.columns(
        3,
        gap="medium"
    )

    # ---------------------------------------------------------
    # POSITIVE CARD
    # ---------------------------------------------------------
    with sp1:

        positive_card_title = (
            "HIGHEST POSITIVE SPIKE"
            if pos_peak_is_spike
            else "HIGHEST POSITIVE VOLUME"
        )

        render_html(
            f"""
            <div
                class="spike-metric-card"
                style="
                    border-left:
                    4px solid #16a34a;
                "
            >

                <div style="
                    font-size:0.68rem;
                    font-weight:800;
                    color:#16a34a;
                ">
                    {positive_card_title}
                </div>

                <div style="
                    font-size:1.4rem;
                    font-weight:800;
                    color:#0f172a;
                    margin:4px 0;
                ">
                    {pos_peak_count:,}
                    Articles
                </div>

                <div style="
                    font-size:0.72rem;
                    color:#64748b;
                ">
                    {pos_peak_date}
                    • <b>{html.escape(str(pos_topic))}</b>
                </div>

            </div>
            """
        )

    # ---------------------------------------------------------
    # NEGATIVE CARD
    # ---------------------------------------------------------
    with sp2:

        negative_card_title = (
            "HIGHEST NEGATIVE SPIKE"
            if neg_peak_is_spike
            else "HIGHEST NEGATIVE VOLUME"
        )

        render_html(
            f"""
            <div
                class="spike-metric-card"
                style="
                    border-left:
                    4px solid #dc2626;
                "
            >

                <div style="
                    font-size:0.68rem;
                    font-weight:800;
                    color:#dc2626;
                ">
                    {negative_card_title}
                </div>

                <div style="
                    font-size:1.4rem;
                    font-weight:800;
                    color:#0f172a;
                    margin:4px 0;
                ">
                    {neg_peak_count:,}
                    Articles
                </div>

                <div style="
                    font-size:0.72rem;
                    color:#64748b;
                ">
                    {neg_peak_date}
                    • <b>{html.escape(str(neg_topic))}</b>
                </div>

            </div>
            """
        )

    # ---------------------------------------------------------
    # MITIGATION CARD
    # ---------------------------------------------------------
    with sp3:

        mitigation_title = (
            "CRISIS MITIGATION NEEDED"
            if neg_peak_is_spike
            else "MITIGATION NEEDED"
        )

        negative_percentage = (
            neg_count
            / max(
                1,
                total_news
            )
            * 100
        )

        render_html(
            f"""
            <div
                class="spike-metric-card"
                style="
                    border-left:
                    4px solid #dc2626;
                "
            >

                <div style="
                    font-size:0.68rem;
                    font-weight:800;
                    color:#dc2626;
                ">
                    {mitigation_title}
                </div>

                <div style="
                    font-size:1.4rem;
                    font-weight:800;
                    color:#dc2626;
                    margin:4px 0;
                ">
                    {neg_count:,}
                    Total
                </div>

                <div style="
                    font-size:0.72rem;
                    color:#64748b;
                ">
                    {negative_percentage:.1f}%
                    Negative Coverage
                </div>

            </div>
            """
        )

    st.markdown(
        "<div style='margin-bottom:24px;'></div>",
        unsafe_allow_html=True
    )

    # =========================================================
    # 21. DAILY SENTIMENT SPIKE CHART
    # =========================================================
    if not df_daily.empty:

        fig_spike = go.Figure()

        df_reset = (
            df_daily
            .reset_index()
            .rename(
                columns={
                    "DATE_ONLY":
                    "date_val"
                }
            )
        )

        # -----------------------------------------------------
        # Positive
        # -----------------------------------------------------
        if "Positive" in df_reset.columns:

            fig_spike.add_trace(
                go.Scatter(
                    x=df_reset[
                        "date_val"
                    ],
                    y=df_reset[
                        "Positive"
                    ],
                    mode="lines",
                    name="Positive",
                    line=dict(
                        color="#16a34a",
                        width=2.2,
                        shape="spline"
                    )
                )
            )

        # -----------------------------------------------------
        # Neutral
        # -----------------------------------------------------
        if "Neutral" in df_reset.columns:

            fig_spike.add_trace(
                go.Scatter(
                    x=df_reset[
                        "date_val"
                    ],
                    y=df_reset[
                        "Neutral"
                    ],
                    mode="lines",
                    name="Neutral",
                    line=dict(
                        color="#94a3b8",
                        width=2.0,
                        shape="spline"
                    )
                )
            )

        # -----------------------------------------------------
        # Negative
        # -----------------------------------------------------
        if "Negative" in df_reset.columns:

            fig_spike.add_trace(
                go.Scatter(
                    x=df_reset[
                        "date_val"
                    ],
                    y=df_reset[
                        "Negative"
                    ],
                    mode="lines",
                    name="Negative",
                    line=dict(
                        color="#dc2626",
                        width=2.2,
                        shape="spline"
                    )
                )
            )

        # -----------------------------------------------------
        # Positive spike markers
        # -----------------------------------------------------
        if pos_spikes:

            fig_spike.add_trace(
                go.Scatter(
                    x=[
                        item[0]
                        for item
                        in pos_spikes
                    ],
                    y=[
                        item[1]
                        for item
                        in pos_spikes
                    ],
                    mode="markers",
                    name="Positive Spike",
                    marker=dict(
                        size=9,
                        color="#16a34a",
                        line=dict(
                            color="#ffffff",
                            width=2
                        )
                    ),
                    hovertemplate=(
                        "<b>Positive Spike</b>"
                        "<br>Date: %{x}"
                        "<br>Volume: %{y}"
                        "<extra></extra>"
                    )
                )
            )

        # -----------------------------------------------------
        # Negative spike markers
        # -----------------------------------------------------
        if neg_spikes:

            fig_spike.add_trace(
                go.Scatter(
                    x=[
                        item[0]
                        for item
                        in neg_spikes
                    ],
                    y=[
                        item[1]
                        for item
                        in neg_spikes
                    ],
                    mode="markers",
                    name="Negative Spike",
                    marker=dict(
                        size=10,
                        color="#dc2626",
                        line=dict(
                            color="#ffffff",
                            width=2
                        )
                    ),
                    hovertemplate=(
                        "<b>Negative Spike</b>"
                        "<br>Date: %{x}"
                        "<br>Volume: %{y}"
                        "<extra></extra>"
                    )
                )
            )

        # -----------------------------------------------------
        # Mark spike dates
        # -----------------------------------------------------
        spike_dates = sorted(
            list(
                set(
                    [
                        item[0]
                        for item
                        in pos_spikes
                    ]
                    +
                    [
                        item[0]
                        for item
                        in neg_spikes
                    ]
                )
            )
        )

        for spike_date in spike_dates:

            fig_spike.add_vline(
                x=pd.Timestamp(
                    spike_date
                ),
                line_width=1,
                line_dash="dot",
                line_color="#cbd5e1"
            )

        fig_spike.update_layout(
            height=240,
            margin=dict(
                l=0,
                r=0,
                t=26,
                b=0
            ),
            paper_bgcolor="#f8fafc",
            plot_bgcolor="#f8fafc",
            hovermode="x unified",
            xaxis=dict(
                showgrid=False,
                tickfont=dict(
                    size=9.5,
                    color="#64748b"
                )
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor=(
                    "rgba(226, 232, 240, 0.9)"
                ),
                tickfont=dict(
                    size=9,
                    color="#94a3b8"
                ),
                rangemode="tozero"
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="left",
                x=0,
                font=dict(
                    size=9.5
                )
            )
        )

        st.plotly_chart(
            fig_spike,
            use_container_width=True,
            config={
                "displayModeBar": True,
                "modeBarButtons": [
                    [
                        "zoom2d",
                        "pan2d",
                        "resetScale2d"
                    ]
                ],
                "displaylogo": False
            }
        )

    st.markdown(
        "<div style='margin-bottom:24px;'></div>",
        unsafe_allow_html=True
    )

    # =========================================================
    # 22. SENTIMENT DISTRIBUTION + TOP KEYWORDS
    # =========================================================
    c_dist, c_keywords = st.columns(
        [1, 1],
        gap="large"
    )

    # =========================================================
    # 23. SENTIMENT DISTRIBUTION BY TOPIC
    # =========================================================
    with c_dist:

        render_html(
            """
            <div class="sa-card-title">
                SENTIMENT DISTRIBUTION BY TOPIC
            </div>
            """
        )

        if (
            topic_col
            and sent_col
            and not df_filtered.empty
        ):

            top_topics = (
                df_filtered[
                    topic_col
                ]
                .value_counts()
                .head(5)
                .index
                .tolist()
            )

            df_topic = (
                df_filtered[
                    df_filtered[
                        topic_col
                    ].isin(
                        top_topics
                    )
                ]
                .groupby(
                    [
                        topic_col,
                        sent_col
                    ]
                )
                .size()
                .unstack(
                    fill_value=0
                )
                .reset_index()
            )

            fig_topic = go.Figure()

            for (
                sentiment_name,
                sentiment_color
            ) in [
                ("Positive", "#10b981"),
                ("Neutral", "#94a3b8"),
                ("Negative", "#ef4444")
            ]:

                if (
                    sentiment_name
                    in df_topic.columns
                ):

                    fig_topic.add_trace(
                        go.Bar(
                            x=df_topic[
                                topic_col
                            ],
                            y=df_topic[
                                sentiment_name
                            ],
                            name=sentiment_name,
                            marker_color=(
                                sentiment_color
                            )
                        )
                    )

            fig_topic.update_layout(
                barmode="stack",
                height=210,
                margin=dict(
                    l=0,
                    r=0,
                    t=20,
                    b=0
                ),
                paper_bgcolor="#f8fafc",
                plot_bgcolor="#f8fafc",
                xaxis=dict(
                    showgrid=False,
                    tickfont=dict(
                        size=9.5
                    )
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor=(
                        "rgba(226, 232, 240, 0.9)"
                    )
                ),
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.2,
                    xanchor="center",
                    x=0.5,
                    font=dict(
                        size=9.5
                    )
                )
            )

            st.plotly_chart(
                fig_topic,
                use_container_width=True,
                config={
                    "displayModeBar": False
                }
            )

        else:

            st.info(
                "Topic sentiment data "
                "is not available."
            )

    # =========================================================
    # 24. TOP KEYWORDS
    # =========================================================
    with c_keywords:

        render_html(
            """
            <div class="sa-card-title">
                TOP KEYWORDS
            </div>
            """
        )

        if (
            keyword_col
            and not df_filtered.empty
        ):

            positive_keyword, positive_count = (
                get_top_keyword(
                    df_filtered,
                    keyword_col,
                    sentiment="Positive"
                )
            )

            negative_keyword, negative_count = (
                get_top_keyword(
                    df_filtered,
                    keyword_col,
                    sentiment="Negative"
                )
            )

            # -------------------------------------------------
            # Positive keyword
            # -------------------------------------------------
            if positive_keyword:

                safe_positive = html.escape(
                    str(
                        positive_keyword
                    )
                )

                render_html(
                    f"""
                    <div class="keyword-card">

                        <span
                            class="keyword-label"
                            style="
                                color:#059669;
                            "
                        >
                            Positive
                        </span>

                        <span class="keyword-name">
                            {safe_positive}
                        </span>

                        <span class="keyword-count">
                            {positive_count:,}
                        </span>

                    </div>
                    """
                )

            else:

                render_html(
                    """
                    <div class="keyword-card">

                        <span
                            class="keyword-label"
                            style="
                                color:#059669;
                            "
                        >
                            Positive
                        </span>

                        <span
                            class="keyword-name"
                            style="
                                color:#94a3b8;
                            "
                        >
                            No keyword available
                        </span>

                    </div>
                    """
                )

            # -------------------------------------------------
            # Negative keyword
            # -------------------------------------------------
            if negative_keyword:

                safe_negative = html.escape(
                    str(
                        negative_keyword
                    )
                )

                render_html(
                    f"""
                    <div class="keyword-card">

                        <span
                            class="keyword-label"
                            style="
                                color:#dc2626;
                            "
                        >
                            Negative
                        </span>

                        <span class="keyword-name">
                            {safe_negative}
                        </span>

                        <span class="keyword-count">
                            {negative_count:,}
                        </span>

                    </div>
                    """
                )

            else:

                render_html(
                    """
                    <div class="keyword-card">

                        <span
                            class="keyword-label"
                            style="
                                color:#dc2626;
                            "
                        >
                            Negative
                        </span>

                        <span
                            class="keyword-name"
                            style="
                                color:#94a3b8;
                            "
                        >
                            No keyword available
                        </span>

                    </div>
                    """
                )

        elif not keyword_col:

            render_html(
                """
                <div class="keyword-card">

                    <span
                        class="keyword-name"
                        style="
                            color:#94a3b8;
                        "
                    >
                        KEYWORD column is not
                        available in the dataset.
                    </span>

                </div>
                """
            )

        else:

            render_html(
                """
                <div class="keyword-card">

                    <span
                        class="keyword-name"
                        style="
                            color:#94a3b8;
                        "
                    >
                        No keyword available.
                    </span>

                </div>
                """
            )

    st.markdown(
        "<div style='margin-bottom:26px;'></div>",
        unsafe_allow_html=True
    )

    # =========================================================
    # 25. PEAK DATE ARTICLES TIMELINE
    # The hourly timeline is integrated into PEAK DATE ARTICLES below.
    st.markdown(
        "<div style='height:18px;'></div>",
        unsafe_allow_html=True
    )

    # 26. PEAK DATE ARTICLES
    #
    # The selected peak date controls one hourly publication timeline.
    # The sentiment filter below affects ONLY the article list.
    # =========================================================

    positive_spike_dates = [
        item[0]
        for item in pos_spikes
    ]

    negative_spike_dates = [
        item[0]
        for item in neg_spikes
    ]

    all_spike_dates = sorted(
        list(
            set(
                positive_spike_dates
                + negative_spike_dates
            )
        ),
        reverse=True
    )

    render_html(
        """
        <div class="sa-card-title">
            PEAK DATE ARTICLES
        </div>
        """
    )

    # =========================================================
    # FILTERS
    # =========================================================
    filter_date_col, filter_sent_col = st.columns(
        [1.6, 1.4],
        gap="medium"
    )

    # ---------------------------------------------------------
    # Peak Date
    # Default = latest spike date
    # ---------------------------------------------------------
    with filter_date_col:

        if all_spike_dates:

            article_date_options = [
                "All Peak Dates"
            ] + [
                date.strftime(
                    "%d %B %Y"
                )
                for date
                in all_spike_dates
            ]

            selected_article_date = st.selectbox(
                "Peak Date:",
                options=article_date_options,
                index=0,
                key="sa_article_date"
            )

            if selected_article_date == "All Peak Dates":
                selected_date_raw = None
            else:
                selected_date_raw = all_spike_dates[
                    article_date_options.index(
                        selected_article_date
                    ) - 1
                ]

        else:

            selected_article_date = None
            selected_date_raw = None

            st.selectbox(
                "Peak Date:",
                options=[
                    "No spike date available"
                ],
                disabled=True,
                key="sa_article_date_empty"
            )

    # ---------------------------------------------------------
    # Sentiment filter
    # ONLY affects article list
    # ---------------------------------------------------------
    with filter_sent_col:

        # -----------------------------------------------------
        # Once a Peak Date is selected, its sentiment is already
        # determined by the spike detection. Therefore the
        # sentiment filter is automatically locked to that
        # spike sentiment.
        # -----------------------------------------------------
        if selected_date_raw is not None:

            date_is_positive = (
                selected_date_raw
                in positive_spike_dates
            )

            date_is_negative = (
                selected_date_raw
                in negative_spike_dates
            )

            if date_is_positive and not date_is_negative:

                locked_sentiment = "Positive"

            elif date_is_negative and not date_is_positive:

                locked_sentiment = "Negative"

            elif date_is_positive and date_is_negative:

                # Both sentiments are spike types on the same date.
                # Keep "All Sentiments" as the locked state so both
                # spike lines/articles remain available.
                locked_sentiment = "All Sentiments"

            else:

                locked_sentiment = "All Sentiments"

            selected_article_sentiment = st.selectbox(
                "Filter Sentiment:",
                options=[
                    locked_sentiment
                ],
                index=0,
                disabled=True,
                key="sa_article_sentiment"
            )

        else:

            selected_article_sentiment = st.selectbox(
                "Filter Sentiment:",
                options=[
                    "All Sentiments",
                    "Positive",
                    "Negative"
                ],
                index=0,
                key="sa_article_sentiment"
            )

    # =========================================================
    # HOURLY PUBLICATION TIMELINE
    # =========================================================
    if (
        selected_date_raw is not None
        and "NEWS_DATE" in df_filtered.columns
        and sent_col
    ):

        selected_is_positive = (
            selected_date_raw
            in positive_spike_dates
        )

        selected_is_negative = (
            selected_date_raw
            in negative_spike_dates
        )

        chart_sentiments = []

        if selected_is_positive:
            chart_sentiments.append("Positive")

        if selected_is_negative:
            chart_sentiments.append("Negative")

        day_start = pd.Timestamp(
            selected_date_raw
        )

        day_end = (
            day_start
            + pd.Timedelta(days=1)
        )

        # Only the sentiment(s) responsible for the spike
        # are included in this chart.
        df_day = df_filtered[
            (
                df_filtered["NEWS_DATE"]
                >= day_start
            )
            &
            (
                df_filtered["NEWS_DATE"]
                < day_end
            )
            &
            (
                df_filtered[sent_col]
                .isin(chart_sentiments)
            )
        ].copy()

        hourly_index = pd.date_range(
            start=day_start,
            periods=24,
            freq="h"
        )

        # -----------------------------------------------------
        # Determine header accent
        # -----------------------------------------------------
        if (
            selected_is_positive
            and not selected_is_negative
        ):

            chart_accent = "#16a34a"

        elif (
            selected_is_negative
            and not selected_is_positive
        ):

            chart_accent = "#dc2626"

        else:

            chart_accent = "#475569"

        render_html(
            f"""
            <div style="
                margin-top:18px;
                margin-bottom:8px;
                display:flex;
                justify-content:space-between;
                align-items:end;
            ">

                <div>
                    <div style="
                        font-size:0.72rem;
                        font-weight:800;
                        color:#334155;
                        text-transform:uppercase;
                        letter-spacing:0.05em;
                    ">
                        HOURLY PUBLICATION TIMELINE
                    </div>

                    <div style="
                        font-size:0.68rem;
                        color:#64748b;
                        margin-top:3px;
                    ">
                        {selected_article_date}
                        • Spike sentiment only
                    </div>
                </div>

                <div style="
                    font-size:0.68rem;
                    font-weight:800;
                    color:{chart_accent};
                ">
                    {", ".join(chart_sentiments)}
                </div>

            </div>
            """
        )

        fig_peak_timeline = go.Figure()

        for sentiment_name in chart_sentiments:

            df_sent_day = df_day[
                df_day[sent_col]
                == sentiment_name
            ].copy()

            if df_sent_day.empty:

                hourly_counts = pd.Series(
                    0,
                    index=hourly_index,
                    dtype="int64"
                )

            else:

                hourly_counts = (
                    df_sent_day
                    .set_index("NEWS_DATE")
                    .resample("h")
                    .size()
                    .reindex(
                        hourly_index,
                        fill_value=0
                    )
                )

            sentiment_color = (
                "#16a34a"
                if sentiment_name == "Positive"
                else "#dc2626"
            )

            fig_peak_timeline.add_trace(
                go.Scatter(
                    x=hourly_counts.index,
                    y=hourly_counts.values,
                    mode="lines+markers",
                    name=sentiment_name,
                    line=dict(
                        color=sentiment_color,
                        width=2.5,
                        shape="linear"
                    ),
                    marker=dict(
                        size=5,
                        color=sentiment_color
                    ),
                    hovertemplate=(
                        f"<b>{sentiment_name}</b>"
                        "<br>%{x|%H:%M}"
                        "<br>Articles: %{y}"
                        "<extra></extra>"
                    )
                )
            )

        fig_peak_timeline.update_layout(
            height=250,
            margin=dict(
                l=0,
                r=0,
                t=8,
                b=8
            ),
            paper_bgcolor="#f8fafc",
            plot_bgcolor="#f8fafc",
            hovermode="x unified",
            showlegend=(
                len(chart_sentiments) > 1
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="left",
                x=0,
                font=dict(size=9)
            ),
            xaxis=dict(
                title=None,
                range=[
                    day_start,
                    day_end
                ],
                showgrid=False,
                tickmode="array",
                tickvals=[
                    day_start
                    + pd.Timedelta(
                        hours=h
                    )
                    for h in range(
                        0,
                        24,
                        3
                    )
                ],
                ticktext=[
                    f"{h:02d}:00"
                    for h in range(
                        0,
                        24,
                        3
                    )
                ],
                tickfont=dict(
                    size=8,
                    color="#64748b"
                )
            ),
            yaxis=dict(
                title="Articles",
                showgrid=True,
                gridcolor=(
                    "rgba(226, 232, 240, 0.9)"
                ),
                tickfont=dict(
                    size=8,
                    color="#94a3b8"
                ),
                rangemode="tozero"
            )
        )

        st.plotly_chart(
            fig_peak_timeline,
            use_container_width=True,
            config={
                "displayModeBar": True,
                "modeBarButtons": [
                    [
                        "zoom2d",
                        "pan2d",
                        "resetScale2d"
                    ]
                ],
                "displaylogo": False
            }
        )

    elif not all_spike_dates:

        st.info(
            "No positive or negative spike was detected "
            "within the selected period."
        )

    # =========================================================
    # ARTICLE LIST
    # =========================================================
    if (
        "NEWS_DATE" in df_filtered.columns
        and selected_date_raw is not None
    ):

        df_articles = (
            df_filtered[
                df_filtered[
                    "NEWS_DATE"
                ].dt.date
                == selected_date_raw
            ]
            .copy()
        )

    elif (
        "NEWS_DATE" in df_filtered.columns
        and selected_article_date == "All Peak Dates"
        and all_spike_dates
    ):

        # All Peak Dates: keep the article list visible and show
        # articles from every detected spike date.
        df_articles = (
            df_filtered[
                df_filtered[
                    "NEWS_DATE"
                ].dt.date
                .isin(all_spike_dates)
            ]
            .copy()
        )

    else:

        df_articles = pd.DataFrame()

    # Sentiment filter affects ONLY the article list.
    if (
        not df_articles.empty
        and sent_col
        and selected_article_sentiment
        != "All Sentiments"
    ):

        df_articles = df_articles[
            df_articles[
                sent_col
            ]
            .astype(str)
            .str.lower()
            == selected_article_sentiment.lower()
        ]

    # =========================================================
    # ARTICLE TABLE
    # =========================================================
    if (
        title_col
        and not df_articles.empty
    ):

        df_articles = (
            df_articles
            .sort_values(
                by="NEWS_DATE",
                ascending=False
            )
        )

        df_show = pd.DataFrame()

        df_show["Article"] = (
            df_articles[
                title_col
            ]
            .astype(str)
            .str.replace(
                r"[\r\n]+",
                " ",
                regex=True
            )
        )

        if media_col:

            df_show["Media Source"] = (
                df_articles[
                    media_col
                ]
                .astype(str)
                .str.replace(
                    "https://",
                    "",
                    regex=False
                )
                .str.replace(
                    "http://",
                    "",
                    regex=False
                )
                .str.replace(
                    "www.",
                    "",
                    regex=False
                )
                .str.split("/")
                .str[0]
            )

        else:

            df_show["Media Source"] = "N/A"

        df_show["Date"] = (
            pd.to_datetime(
                df_articles[
                    "NEWS_DATE"
                ],
                errors="coerce"
            )
            .dt.strftime(
                "%Y-%m-%d %H:%M"
            )
        )

        if sent_col:

            df_show["Sentiment"] = (
                df_articles[
                    sent_col
                ]
                .astype(str)
            )

        else:

            df_show["Sentiment"] = "N/A"

        st.dataframe(
            df_show,
            use_container_width=True,
            height=420,
            hide_index=True,
            column_config={

                "Article":
                    st.column_config.TextColumn(
                        "Article",
                        width="large"
                    ),

                "Media Source":
                    st.column_config.TextColumn(
                        "Media Source",
                        width="medium"
                    ),

                "Date":
                    st.column_config.TextColumn(
                        "Date",
                        width="medium"
                    ),

                "Sentiment":
                    st.column_config.TextColumn(
                        "Sentiment",
                        width="small"
                    )
            }
        )

    else:

        st.info(
            "No articles match the selected "
            "peak date or sentiment filter."
        )

