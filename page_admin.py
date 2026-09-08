import streamlit as st
import pandas as pd
import os
from utils import load_custom_css, get_base64_image

def render_admin_page(df_current: pd.DataFrame, loaded_file_name: str):
    load_custom_css()

    icon_admin_b64 = get_base64_image("assets/icons/icon_admin.png")
    icon_markup = f'<img src="{icon_admin_b64}" width="20" height="20" style="object-fit: contain;" />' if icon_admin_b64 else ''

    # Scoped CSS: Admin Content Only (Sidebar Isolated)
    st.markdown("""
        <style>
            div[data-testid="stVerticalBlockBorderWrapper"] {
                border: none !important;
                box-shadow: none !important;
                background: transparent !important;
            }

            /* Table Header */
            .mgr-table-header {
                background: #237ece !important;
                color: #ffffff !important;
                border-radius: 8px !important;
                padding: 12px 16px !important;
                font-size: 0.74rem !important;
                font-weight: 800 !important;
                letter-spacing: 0.05em !important;
                text-transform: uppercase !important;
                display: flex !important;
                align-items: center !important;
            }

            .mgr-table-row {
                padding: 12px 16px !important;
                border-bottom: 1px solid #f1f5f9 !important;
                font-size: 0.78rem !important;
                color: #334155 !important;
                display: flex !important;
                align-items: center !important;
            }

            .mgr-table-row:hover {
                background-color: #f8fafc !important;
            }

            /* Status Badges */
            .badge-active {
                background: #ecfdf5 !important;
                color: #059669 !important;
                font-size: 0.70rem !important;
                font-weight: 700 !important;
                padding: 3px 8px !important;
                border-radius: 6px !important;
            }

            .badge-inactive {
                background: #fef2f2 !important;
                color: #dc2626 !important;
                font-size: 0.70rem !important;
                font-weight: 700 !important;
                padding: 3px 8px !important;
                border-radius: 6px !important;
            }

            /* Navigation Tabs di Konten Admin (Berlaku untuk Local & Cloud) */
            div[data-testid="stTabs"] [data-baseweb="tab-list"],
            div[data-testid="stTabs"] div[role="tablist"] {
                gap: 8px !important;
                background-color: #f1f5f9 !important;
                padding: 6px 8px !important;
                border-radius: 12px !important;
                border-bottom: none !important;
                width: fit-content !important;
                margin-bottom: 22px !important;
            }

            /* Hilangkan garis highlight bawaan browser/BaseWeb */
            div[data-testid="stTabs"] [data-baseweb="tab-highlight"],
            div[data-testid="stTabs"] div[role="tablist"] + div {
                display: none !important;
                height: 0px !important;
            }

            /* Tombol tab default */
            div[data-testid="stTabs"] [data-baseweb="tab"],
            div[data-testid="stTabs"] button[role="tab"] {
                height: 38px !important;
                padding: 0 18px !important;
                background-color: transparent !important;
                border-radius: 8px !important;
                border: none !important;
                color: #64748b !important;
                font-size: 0.80rem !important;
                font-weight: 700 !important;
                letter-spacing: 0.01em !important;
            }

            /* Tombol tab aktif (Biru & Rounded Pill) */
            div[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"],
            div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
                background-color: #237ece !important;
                color: #ffffff !important;
                border-radius: 8px !important;
                box-shadow: 0 2px 8px rgba(35, 126, 206, 0.28) !important;
            }

            div[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] p,
            div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] p {
                color: #ffffff !important;
            }

            /* =========================================================
               STYLING TOMBOL: HANYA DI DALAM KONTEN UTAMA (SECTION STMAIN)
               ========================================================= */
            section[data-testid="stMain"] div.stButton > button,
            section[data-testid="stMain"] button[kind="secondary"] {
                background-color: transparent !important;
                border: 1.5px solid #237ece !important;
                color: #237ece !important;
                font-weight: 700 !important;
                transition: all 0.2s ease-in-out !important;
            }

            section[data-testid="stMain"] div.stButton > button p,
            section[data-testid="stMain"] button[kind="secondary"] p {
                color: #237ece !important;
                font-weight: 700 !important;
            }

            section[data-testid="stMain"] div.stButton > button:hover,
            section[data-testid="stMain"] div.stButton > button:active,
            section[data-testid="stMain"] div.stButton > button:focus,
            section[data-testid="stMain"] button[kind="secondary"]:hover,
            section[data-testid="stMain"] button[kind="secondary"]:active,
            section[data-testid="stMain"] button[kind="secondary"]:focus,
            section[data-testid="stMain"] button[kind="primary"]:hover,
            section[data-testid="stMain"] button[kind="primary"]:active,
            section[data-testid="stMain"] button[kind="primary"]:focus,
            section[data-testid="stMain"] button[kind="primaryFormSubmit"]:hover,
            section[data-testid="stMain"] button[kind="primaryFormSubmit"]:active,
            section[data-testid="stMain"] button[kind="primaryFormSubmit"]:focus {
                background-color: #237ece !important;
                border-color: #237ece !important;
                color: #ffffff !important;
                box-shadow: 0 4px 14px rgba(35, 126, 206, 0.35) !important;
            }

            section[data-testid="stMain"] div.stButton > button:hover p,
            section[data-testid="stMain"] div.stButton > button:active p,
            section[data-testid="stMain"] div.stButton > button:focus p,
            section[data-testid="stMain"] button[kind="secondary"]:hover p,
            section[data-testid="stMain"] button[kind="secondary"]:active p,
            section[data-testid="stMain"] button[kind="secondary"]:focus p,
            section[data-testid="stMain"] button[kind="primary"]:hover p,
            section[data-testid="stMain"] button[kind="primary"]:active p,
            section[data-testid="stMain"] button[kind="primary"]:focus p {
                color: #ffffff !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # -------------------------------------------------------------
    # 1. PAGE HEADER
    # -------------------------------------------------------------
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px;">
            <div style="width: 8px; height: 48px; background: linear-gradient(180deg, #38bdf8 0%, #237ece 100%); border-radius: 4px; flex-shrink: 0;"></div>
            <div style="display: flex; flex-direction: column; justify-content: center;">
                <h2 style="margin: 0 0 1px 0; padding: 0; font-size: 2rem; line-height: 1.25; color: #0f172a; font-weight: 800; letter-spacing: -0.01em;">
                    ADMIN <span style="color: #237ece; font-style: italic;">SETTINGS</span>
                </h2>
                <span style="margin: 0; padding: 0; font-size: 0.70rem; line-height: 1.1; letter-spacing: 0.08em; color: #64748b; font-weight: 700; text-transform: uppercase;">
                    SYSTEM CONFIGURATION & DATASET MANAGEMENT
                </span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    tab_dataset, tab_history, tab_maintenance = st.tabs([
        "Dataset Manager", 
        "User Management & Login History",  # Judul submenu dikembalikan
        "System Maintenance"
    ])

    # -------------------------------------------------------------
    # TAB 1: DATASET MANAGER
    # -------------------------------------------------------------
    with tab_dataset:
        st.markdown("<p style='font-weight:700; font-size:0.92rem; margin-bottom:4px; color:#1e293b;'>Upload New Dataset (tkb_news.xlsx)</p>", unsafe_allow_html=True)
        st.caption("Upload an Excel file (.xlsx) to update the dashboard dataset.")

        uploaded_file = st.file_uploader(
            "Select Excel file:",
            type=["xlsx", "xls"],
            key="admin_file_uploader",
            label_visibility="collapsed"
        )

        if uploaded_file is not None:
            try:
                df_upload = pd.read_excel(uploaded_file)
                df_upload.columns = [str(c).strip().upper() for c in df_upload.columns]

                st.success(f"File processed successfully: {len(df_upload):,} rows and {len(df_upload.columns)} columns detected.")
                st.dataframe(df_upload.head(3), use_container_width=True)

                if st.button("Save as tkb_news.xlsx & Activate", type="primary"):
                    save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tkb_news.xlsx")
                    df_upload.to_excel(save_path, index=False)
                    st.cache_data.clear()
                    for key in ["home_filters", "ov_filters", "deep_filters"]:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.success("File successfully saved and dashboard dataset updated.")
                    st.rerun()
            except Exception as e:
                st.error(f"An error occurred while processing the file: {e}")

        st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
        st.markdown("<p style='font-weight:700; font-size:0.92rem; margin-bottom:8px; color:#1e293b;'>Active Dataset Status</p>", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3, gap="medium")
        with c1:
            st.markdown(f"""
                <div style="background:#fff; border:1px solid #f1f5f9; border-radius:12px; padding:14px 16px; box-shadow:0 4px 14px rgba(15,23,42,0.03);">
                    <div style="font-size:0.72rem; font-weight:800; color:#64748b; text-transform:uppercase;">ACTIVE FILE NAME</div>
                    <div style="font-size:1.2rem; font-weight:800; color:#0f172a; margin-top:4px;">{loaded_file_name if loaded_file_name else "Sample Data"}</div>
                </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
                <div style="background:#fff; border:1px solid #f1f5f9; border-radius:12px; padding:14px 16px; box-shadow:0 4px 14px rgba(15,23,42,0.03);">
                    <div style="font-size:0.72rem; font-weight:800; color:#64748b; text-transform:uppercase;">TOTAL ROWS</div>
                    <div style="font-size:1.2rem; font-weight:800; color:#237ece; margin-top:4px;">{len(df_current):,} Rows</div>
                </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
                <div style="background:#fff; border:1px solid #f1f5f9; border-radius:12px; padding:14px 16px; box-shadow:0 4px 14px rgba(15,23,42,0.03);">
                    <div style="font-size:0.72rem; font-weight:800; color:#64748b; text-transform:uppercase;">TOTAL COLUMNS</div>
                    <div style="font-size:1.2rem; font-weight:800; color:#16a34a; margin-top:4px;">{len(df_current.columns)} Columns</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
        st.markdown("<p style='font-weight:700; font-size:0.92rem; margin-bottom:4px; color:#1e293b;'>Column Structure & Missing Data Analysis</p>", unsafe_allow_html=True)

        tot_rows = len(df_current)
        cols_summary = []
        for col in df_current.columns:
            null_count = int(df_current[col].isnull().sum())
            null_pct = (null_count / tot_rows * 100) if tot_rows > 0 else 0
            cols_summary.append({
                "Column Name": col,
                "Data Type": str(df_current[col].dtype),
                "Missing Values": null_count,
                "Missing Percentage": f"{null_pct:.1f}%",
                "Status": "Missing Detected" if null_count > 0 else "Complete"
            })

        df_cols_summary = pd.DataFrame(cols_summary)
        st.dataframe(df_cols_summary, use_container_width=True, height=280, hide_index=True)

    # -------------------------------------------------------------
    # TAB 2: USERNAME MANAGEMENT & LOGIN HISTORY (TABLE VIEW)
    # -------------------------------------------------------------
    with tab_history:
        st.markdown("<p style='font-weight:700; font-size:0.92rem; margin-bottom:4px; color:#1e293b;'>User Management</p>", unsafe_allow_html=True)
        st.caption("Manage username access credentials and assigned roles. Default password format: username123.")

        users_csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.csv")
        if not os.path.exists(users_csv_path):
            users_csv_path = "users.csv"

        # Schema kolom
        base_columns = ["username", "password", "role", "status"]
        if os.path.exists(users_csv_path):
            try:
                df_users = pd.read_csv(users_csv_path)
            except Exception:
                df_users = pd.DataFrame(columns=base_columns)
        else:
            df_users = pd.DataFrame(columns=base_columns)

        for c in base_columns:
            if c not in df_users.columns:
                if c == "status":
                    df_users[c] = "Active"
                elif c == "role":
                    df_users[c] = "User"
                else:
                    df_users[c] = ""

        # Dialog Modal: Add Username
        @st.dialog("Add New Username")
        def add_user_modal():
            with st.form("form_modal_add"):
                n_user = st.text_input("Username:", placeholder="e.g. johan_pertamina").strip()
                n_role = st.selectbox("Role:", ["User", "Admin"])
                submit_modal = st.form_submit_button("Save Username", type="primary", use_container_width=True)

                if submit_modal:
                    if not n_user:
                        st.error("Username cannot be empty.")
                    elif not df_users.empty and n_user.lower() in df_users["username"].astype(str).str.lower().values:
                        st.warning(f"Username '{n_user}' is already registered.")
                    else:
                        new_entry = {
                            "username": n_user,
                            "password": f"{n_user}123",
                            "role": n_role.capitalize(),
                            "status": "Active"
                        }
                        df_updated = pd.concat([df_users, pd.DataFrame([new_entry])], ignore_index=True)
                        df_updated.to_csv(users_csv_path, index=False)
                        st.success(f"Username '{n_user}' has been created.")
                        st.rerun()

        # Dialog Modal: Edit Username
        @st.dialog("Edit Username")
        def edit_user_modal(u_name):
            matched_user = df_users[df_users["username"].astype(str).str.lower() == str(u_name).lower()]
            if matched_user.empty:
                st.error("Username not found.")
                return
            row = matched_user.iloc[0]
            curr_role_cap = str(row["role"]).capitalize()

            with st.form("form_modal_edit"):
                st.text_input("Username (Read-only):", value=str(row["username"]).capitalize(), disabled=True)
                e_role = st.selectbox(
                    "Role:", ["User", "Admin"],
                    index=["User", "Admin"].index(curr_role_cap) if curr_role_cap in ["User", "Admin"] else 0
                )
                e_status = st.selectbox(
                    "Status:", ["Active", "Inactive"],
                    index=0 if str(row["status"]).lower() == "active" else 1
                )
                e_password = st.text_input("Password:", value=str(row["password"]))

                submit_edit = st.form_submit_button("Save Changes", type="primary", use_container_width=True)
                if submit_edit:
                    idx = matched_user.index[0]
                    df_users.at[idx, "role"] = e_role.capitalize()
                    df_users.at[idx, "status"] = e_status
                    df_users.at[idx, "password"] = e_password
                    df_users.to_csv(users_csv_path, index=False)
                    st.success("Username credentials updated successfully.")
                    st.rerun()

        # Filter Data Berdasarkan Search
        c_search, c_spc, c_act_add, c_act_edt, c_act_del = st.columns([3.0, 0.2, 1.4, 0.9, 0.9], gap="small")

        with c_search:
            search_query = st.text_input("Search username", placeholder="Search username...", label_visibility="collapsed", key="search_user_input").strip()

        df_filtered_users = df_users.copy()
        if search_query:
            df_filtered_users = df_filtered_users[df_filtered_users["username"].astype(str).str.lower().str.contains(search_query.lower())]

        df_filtered_users = df_filtered_users.reset_index(drop=True)

        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
        
        display_df = df_filtered_users[["username", "role", "status"]].copy()

        # Format teks pada kolom Username & Role: Huruf depan kapital (Admin, User, Hira)
        display_df["username"] = display_df["username"].astype(str).str.capitalize()
        display_df["role"] = display_df["role"].astype(str).str.capitalize()
        display_df["status"] = display_df["status"].astype(str).str.capitalize()

        event = st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            selection_mode="single-row",
            on_select="rerun",
            key="user_table_select",
            column_config={
                "username": st.column_config.TextColumn("Username", width="large"),
                "role": st.column_config.TextColumn("Role", width="medium"),
                "status": st.column_config.TextColumn("Status", width="medium"),
            }
        )

        # Ambil username asli yang dipilih dari baris tabel
        selected_rows = event.selection.rows if event and hasattr(event, "selection") else []
        selected_user = df_filtered_users.iloc[selected_rows[0]]["username"] if len(selected_rows) > 0 else None
        selected_user_display = str(selected_user).capitalize() if selected_user else None

        # Tombol-tombol Aksi di Atas
        with c_act_add:
            if st.button("+ ADD USERNAME", type="secondary", use_container_width=True):
                add_user_modal()

        with c_act_edt:
            if st.button("EDIT", type="secondary", disabled=(selected_user is None), use_container_width=True):
                if selected_user:
                    edit_user_modal(selected_user)

        with c_act_del:
            if st.button("DELETE", type="secondary", disabled=(selected_user is None), use_container_width=True):
                if selected_user:
                    if str(selected_user).lower() == "admin":
                        st.error("The primary 'Admin' account cannot be deleted.")
                    else:
                        df_users = df_users[df_users["username"].astype(str).str.lower() != str(selected_user).lower()]
                        df_users.to_csv(users_csv_path, index=False)
                        st.success(f"Username '{selected_user_display}' deleted.")
                        st.rerun()

        st.markdown(f"<div style='margin-top: 10px; font-size: 0.74rem; color: #64748b;'>Total usernames: <b>{len(df_filtered_users)}</b> {f'| Selected: <b>{selected_user_display}</b>' if selected_user else '(Click a row to edit/delete)'}</div>", unsafe_allow_html=True)

        # Login History Section
        st.markdown("<div style='margin-top: 36px;'></div>", unsafe_allow_html=True)
        st.markdown("<p style='font-weight:700; font-size:0.92rem; margin-bottom:4px; color:#1e293b;'>Login History</p>", unsafe_allow_html=True)
        st.caption("Latest recorded user sign-in sessions from login_history.csv.")

        csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "login_history.csv")
        if not os.path.exists(csv_path):
            csv_path = "login_history.csv"

        if os.path.exists(csv_path):
            try:
                df_login = pd.read_csv(csv_path)
                if not df_login.empty:
                    time_col = next((c for c in ["TIMESTAMP", "timestamp", "LOGIN_TIME", "login_time", "DATE", "date", "WAKTU", "waktu"] if c in df_login.columns), None)
                    if time_col:
                        df_login[time_col] = pd.to_datetime(df_login[time_col], errors="coerce")
                        df_login = df_login.sort_values(by=time_col, ascending=False)
                    else:
                        df_login = df_login.iloc[::-1].reset_index(drop=True)

                    # Format nilai kolom Role pada tabel Login History agar Title Case (Admin, User)
                    role_col_h = next((c for c in ["Role", "role", "ROLE"] if c in df_login.columns), None)
                    if role_col_h:
                        df_login[role_col_h] = df_login[role_col_h].astype(str).str.capitalize()

                    # Format kolom Username pada Login History agar Title Case
                    user_col_h = next((c for c in ["Username", "username", "User", "user"] if c in df_login.columns), None)
                    if user_col_h:
                        df_login[user_col_h] = df_login[user_col_h].astype(str).str.capitalize()

                    st.dataframe(df_login, use_container_width=True, height=320, hide_index=True)
                else:
                    st.info("The login_history.csv file is empty.")
            except Exception as e:
                st.error(f"Failed to read login_history.csv: {e}")
        else:
            st.warning("The login_history.csv file was not found.")

    # -------------------------------------------------------------
    # TAB 3: SYSTEM MAINTENANCE
    # -------------------------------------------------------------
    with tab_maintenance:
        st.markdown("<p style='font-weight:700; font-size:0.92rem; margin-bottom:4px; color:#1e293b;'>System Cache Maintenance</p>", unsafe_allow_html=True)
        st.write("Click the button below to clear cached session state and force-resynchronize local datasets.")
        if st.button("Clear Cache & Reload Dataset", type="secondary"):
            st.cache_data.clear()
            st.rerun()