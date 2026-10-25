"""Khwezi Mining Monitoring App.

Run with: streamlit run app.py
This classroom project uses rule-based Python only. It does not use LLMs,
machine learning, external APIs or hidden automated decisions.
"""

from pathlib import Path
from datetime import datetime
import base64
import csv
import json
import hashlib
import hmac
import html
import random
import secrets
import time
import textwrap

import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from utils.logic import build_alerts, build_equipment_summary, risk_level, worker_risk


DATA_FOLDER = Path(__file__).parent / "data"
BACKGROUND_FOLDER = DATA_FOLDER / "home_backgrounds"
USERS_FILE = DATA_FOLDER / "users.csv"
HOME_SETTINGS_FILE = DATA_FOLDER / "home_settings.json"
USER_FIELDS = ["Worker_ID", "Username", "Password_Hash", "Full_Name", "Title", "Role"]

ROLE_PAGES = {
    "Administrator": ["Dashboard", "Worker Safety", "Safety Incidents", "Equipment", "Maintenance", "Risk Assessment", "Alerts"],
    "Safety Officer": ["Dashboard", "Worker Safety", "Safety Incidents", "Risk Assessment", "Alerts"],
    "Mining Engineer": ["Dashboard", "Worker Safety", "Safety Incidents", "Equipment", "Maintenance", "Risk Assessment", "Alerts"],
    "Maintenance Engineer": ["Dashboard", "Equipment", "Maintenance", "Alerts"],
    "Manager": ["Dashboard", "Worker Safety", "Safety Incidents", "Equipment", "Maintenance", "Risk Assessment", "Alerts"],
}


def password_hash(password, salt=None):
    """Return a salted password hash instead of saving a plain password."""
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 200_000).hex()
    return f"{salt}${digest}"


def password_matches(password, stored_hash):
    """Check one password against the saved password hash."""
    try:
        salt, saved_digest = stored_hash.split("$", 1)
    except ValueError:
        return False
    check_digest = password_hash(password, salt).split("$", 1)[1]
    return hmac.compare_digest(check_digest, saved_digest)


class UserStore:
    """Keep worker accounts in data/users.csv using functions and CSV files."""

    def __init__(self):
        if not USERS_FILE.exists():
            with USERS_FILE.open("w", newline="", encoding="utf-8") as file:
                csv.DictWriter(file, fieldnames=USER_FIELDS).writeheader()

    def read_users(self):
        # Ignore blank lines before the header (including the leading blank
        # line found in some Windows-edited copies of users.csv).
        with USERS_FILE.open(newline="", encoding="utf-8-sig") as file:
            reader = csv.reader(file)
            header = next((row for row in reader if any(cell.strip() for cell in row)), [])
            header = [cell.strip().lstrip("\ufeff") for cell in header]
            users = []
            for values in reader:
                if not any(cell.strip() for cell in values):
                    continue
                row = dict(zip(header, values))
                users.append({field: row.get(field, "").strip() for field in USER_FIELDS})
            return users

    def write_users(self, users):
        with USERS_FILE.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=USER_FIELDS)
            writer.writeheader()
            writer.writerows(users)

    def worker_exists(self, worker_id):
        with (DATA_FOLDER / "workers.csv").open(newline="", encoding="utf-8") as file:
            return any(row["Worker_ID"].strip().upper() == worker_id.strip().upper() for row in csv.DictReader(file))

    def create_user(self, worker_id, username, password, full_name, title, role):
        worker_id, username = worker_id.strip().upper(), username.strip().lower()
        users = self.read_users()
        if not all([worker_id, username, password, full_name.strip(), role]):
            return False, "Complete every required account field."
        if len(password) < 8:
            return False, "Use a password with at least 8 characters."
        if not self.worker_exists(worker_id):
            return False, "That Worker ID is not in the worker safety database."
        if any(row["Worker_ID"].upper() == worker_id for row in users):
            return False, "An account already exists for this Worker ID."
        if any(row["Username"].lower() == username for row in users):
            return False, "That username is already in use."
        users.append({"Worker_ID": worker_id, "Username": username, "Password_Hash": password_hash(password), "Full_Name": full_name.strip(), "Title": title.strip(), "Role": role})
        self.write_users(users)
        return True, "Account created. You can now sign in."

    def authenticate(self, username, worker_id, password):
        for row in self.read_users():
            if (row["Username"].lower() == username.strip().lower()
                    and row["Worker_ID"].upper() == worker_id.strip().upper()
                    and password_matches(password, row["Password_Hash"])):
                return {"username": row["Username"], "worker_id": row["Worker_ID"], "name": row["Full_Name"], "title": row["Title"], "role": row["Role"]}
        return None

    def update_password(self, worker_id, current_password, new_password):
        if len(new_password) < 8:
            return False, "Use a new password with at least 8 characters."
        users = self.read_users()
        for row in users:
            if row["Worker_ID"].upper() == worker_id.strip().upper():
                if not password_matches(current_password, row["Password_Hash"]):
                    return False, "Your current password is incorrect."
                row["Password_Hash"] = password_hash(new_password)
                self.write_users(users)
                return True, "Password updated successfully."
        return False, "Worker account not found."


USER_STORE = UserStore()


def login(username, worker_id, password):
    """Sign in only if the username, Worker ID and password match one record."""
    return USER_STORE.authenticate(username, worker_id, password)


def create_account(worker_id, username, password, full_name, title, role):
    """Create a worker account in users.csv."""
    return USER_STORE.create_user(worker_id, username, password, full_name, title, role)


def change_password(worker_id, current_password, new_password):
    """Update the signed-in worker's password in users.csv."""
    return USER_STORE.update_password(worker_id, current_password, new_password)


def pages_for_role(role):
    """Return the pages visible to each role."""
    return ROLE_PAGES.get(role, ["Dashboard"])


def available_roles():
    """Return role choices for the registration form."""
    return list(ROLE_PAGES)

MOTIVATIONAL_QUOTES = [
    "Safety is not a department. It is the way we work.",
    "Great operations are built one safe decision at a time.",
    "Every observation today can prevent an incident tomorrow.",
    "Reliable equipment starts with disciplined inspection.",
    "Strong teams speak up, check twice and protect one another.",
    "Data becomes valuable when it helps people go home safely.",
]

WORKSPACE_DETAILS = {
    "Dashboard": ("Operations overview", "Review the most important safety, incident and equipment indicators."),
    "Worker Safety": ("Worker safety", "Check PPE compliance, training, fatigue and safety observations."),
    "Safety Incidents": ("Safety incidents", "Record, filter and review incidents across the operation."),
    "Equipment": ("Equipment monitoring", "Inspect temperature, vibration and equipment condition."),
    "Maintenance": ("Maintenance planning", "Review availability, downtime and overdue maintenance."),
    "Risk Assessment": ("Risk assessment", "Calculate likelihood × consequence and select controls."),
    "Alerts": ("Risk alerts", "View the active conditions that require attention."),
}

MINE_ICON_SVG = """<svg class='mine-mark' viewBox='0 0 128 67' aria-hidden='true'>
<g fill='none' stroke='#fb923c' stroke-width='2.8' stroke-linecap='round' stroke-linejoin='round'>
  <path d='M5 65 31 39 43 50 62 22 81 45 98 28 124 65'/>
</g>
<g stroke='#fbbf24' stroke-width='2' stroke-linecap='round'>
  <path d='M103 7v5m0 22v5m-16-16h5m22 0h5M91 9l4 4m16 16 4 4m0-24-4 4m-16 16-4 4'/>
</g>
<circle cx='103' cy='21' r='7' fill='#f97316' stroke='#fbbf24' stroke-width='1.5'/>
</svg>"""

st.set_page_config(page_title="Khwezi Mining App", page_icon="🌋", layout="wide")


def apply_custom_style():
    """Apply a consistent volcano-inspired visual theme to the Streamlit UI."""
    st.markdown(
        """
        <style>
        .stApp {
            background: linear-gradient(145deg, #f8fafc 0%, #fef3e6 48%, #fff7ed 100%);
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        h1, h2, h3 { font-family: 'Segoe UI', Arial, sans-serif; color: #172033; }
        h1 { letter-spacing: -0.8px; }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #172033 0%, #263854 100%);
        }
        [data-testid="stSidebar"] * { color: #f8fafc; }
        [data-testid="stSidebar"] .stRadio label { padding: 3px 0; }
        [data-testid="stSidebar"] .stButton button {
            background: transparent; border: 1px solid rgba(255,255,255,.28); color: #fff7ed;
            text-align: left; padding: 10px 12px;
        }
        [data-testid="stSidebar"] .stButton button:hover {
            background: #f97316; color: white; border-color: #f97316;
        }
        [data-testid="stMetric"] {
            background: rgba(255,255,255,0.92);
            border: 1px solid #e8edf3;
            border-radius: 16px;
            padding: 16px;
            box-shadow: 0 8px 22px rgba(23, 32, 51, 0.07);
        }
        [data-testid="stMetricLabel"] { color: #64748b; font-weight: 600; }
        [data-testid="stMetricValue"] { color: #172033; }
        .hero {
            background: radial-gradient(circle at top right, rgba(251,146,60,.95), transparent 37%),
                        linear-gradient(120deg, #172033 0%, #263854 100%);
            padding: 42px 44px; border-radius: 24px; color: white;
            box-shadow: 0 20px 35px rgba(23,32,51,.22); margin-bottom: 20px;
        }
        .hero h1 { color: white; margin: 0 0 8px 0; font-size: 2.8rem; }
        .hero .hero-title { display: flex; align-items: flex-end; gap: 14px; }
        .hero .hero-title span { order: 1; }
        .hero .hero-title .mine-mark { order: 2; transform: translateY(0); }
        .hero .hero-title span { line-height: 1; transform: translateY(14px); }
        .hero .mine-mark { width: 96px; height: auto; flex: 0 0 auto; }
        .sidebar-brand { display: flex; align-items: flex-end; gap: 10px; color: #fff; font-size: 1.2rem; font-weight: 800; margin-bottom: 4px; }
        .sidebar-brand span { line-height: 1; }
        .sidebar-brand .mine-mark { width: 52px; height: auto; flex: 0 0 auto; }
        .hero p { color: #e2e8f0; font-size: 1.1rem; margin: 0; max-width: 640px; }
        .eyebrow { color: #fdba74; text-transform: uppercase; letter-spacing: 2px; font-size: .76rem; font-weight: 700; }
        .section-intro { color: #64748b; margin-top: -10px; margin-bottom: 16px; }
        .feature-card {
            background: rgba(255,255,255,.9); border: 1px solid #e8edf3; border-radius: 16px;
            padding: 16px; min-height: 125px; box-shadow: 0 8px 18px rgba(23,32,51,.05);
        }
        .feature-card h4 { color: #172033; margin: 0 0 8px 0; font-size: 1rem; }
        .feature-card p { color: #64748b; font-size: .9rem; margin: 0; }
        .page-banner {
            background: white; border-left: 5px solid #f97316; padding: 14px 18px; border-radius: 12px;
            margin-bottom: 18px; box-shadow: 0 5px 15px rgba(23,32,51,.05);
        }
        .page-banner-home {
            background: linear-gradient(115deg, #172033 0%, #334155 72%, #9a4b1b 150%);
            border-left-color: #f97316;
        }
        .page-banner-home h2 { color: #fff !important; }
        .page-banner-home .section-intro { color: #e2e8f0 !important; }
        .page-banner-image h2 { color: #ffffff !important; text-shadow: 0 2px 8px rgba(0,0,0,.65); }
        .page-banner-image .section-intro { color: #f8fafc !important; text-shadow: 0 1px 5px rgba(0,0,0,.7); }
        .page-banner-image .page-alert-badge {
            background: rgba(23,32,51,.45); color: #fff; border: 1px solid rgba(255,255,255,.42);
            text-shadow: 0 1px 4px rgba(0,0,0,.55); backdrop-filter: blur(6px);
        }
        .page-banner-title { display: flex; align-items: center; gap: 12px; }
        .page-banner-title h2 { margin: 0; }
        .page-banner-title .mine-mark { display: block; width: 72px; height: auto; flex: 0 0 auto; }
        .status-chip { display: inline-block; border-radius: 999px; padding: 4px 10px; margin-right: 6px; font-size: .82rem; font-weight: 700; }
        .chip-critical { color: #991b1b; background: #fee2e2; }
        .chip-warning { color: #9a3412; background: #ffedd5; }
        .chip-normal { color: #166534; background: #dcfce7; }
        .page-alert-badge { display: inline-block; background: #fee2e2; color: #b91c1c; border-radius: 999px; padding: 8px 12px; font-weight: 700; text-align: center; white-space: nowrap; flex: 0 0 auto; }
        .stButton > button, .stFormSubmitButton > button {
            border-radius: 10px; background: #ea580c; color: white; border: 0; font-weight: 700;
        }
        .stButton > button:hover, .stFormSubmitButton > button:hover { background: #c2410c; color: white; }
        [data-testid="stDataFrame"] { border: 1px solid #e8edf3; border-radius: 12px; overflow: hidden; }
        .workspace-bar {
            display: flex; align-items: center; justify-content: space-between; gap: 16px;
            background: rgba(255,255,255,.82); border: 1px solid #e8edf3; border-radius: 14px;
            padding: 11px 16px; margin-bottom: 18px; box-shadow: 0 6px 16px rgba(23,32,51,.05);
        }
        .workspace-quote { color: #334155; font-weight: 600; font-size: .92rem; }
        .workspace-user { color: #ea580c; font-size: .78rem; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; }
        .quick-action {
            background: white; border: 1px solid #e8edf3; border-radius: 15px; padding: 14px;
            box-shadow: 0 6px 14px rgba(23,32,51,.05); min-height: 118px;
        }
        .quick-action h4 { margin: 0 0 5px 0; color: #172033; }
        .quick-action p { color: #64748b; margin: 0; font-size: .86rem; }
        .home-card {
            padding: 22px; background: linear-gradient(130deg,#172033,#304968); border-radius: 18px;
            color: white; min-height: 150px;
        }
        .home-card h3 { color: white; margin: 0 0 8px 0; }
        .home-card p { color: #e2e8f0; margin: 0; }
        .profile-card {
            padding: 15px 12px; border: 1px solid rgba(255,255,255,.18);
            background: rgba(255,255,255,.08); border-radius: 16px; margin: 6px 0 16px 0;
        }
        .profile-avatar {
            width: 48px; height: 48px; border-radius: 50%; display: inline-flex;
            align-items: center; justify-content: center; background: #f97316; color: white;
            font-weight: 800; font-size: 1rem; margin-bottom: 9px;
        }
        .profile-name { color: #ffffff; font-size: 1rem; font-weight: 750; }
        .profile-role { color: #cbd5e1; font-size: .82rem; margin-top: 3px; }
        .workspace-card {
            background: rgba(255,255,255,.94); border: 1px solid #e8edf3; border-radius: 16px;
            padding: 18px; min-height: 150px; box-shadow: 0 8px 18px rgba(23,32,51,.05);
        }
        .workspace-card h4 { color: #172033; margin: 0 0 8px 0; font-size: 1.02rem; }
        .workspace-card p { color: #64748b; font-size: .9rem; line-height: 1.45; margin: 0; }
        .workspace-kicker { color: #ea580c; font-size: .72rem; font-weight: 800; text-transform: uppercase; letter-spacing: 1.1px; margin-bottom: 7px; }
        .glass-panel {
            background: rgba(255, 255, 255, 0.66); border: 1px solid rgba(255, 255, 255, 0.70);
            backdrop-filter: blur(15px); -webkit-backdrop-filter: blur(15px);
            box-shadow: 0 18px 36px rgba(23,32,51,.14);
        }
        .home-background-card {
            padding: 28px; border-radius: 22px; min-height: 180px; background-size: cover;
            background-position: center; margin-bottom: 16px;
        }
        .home-background-card h3 { color: white; margin: 0 0 8px 0; }
        .home-background-card p { color: #f8fafc; margin: 0; max-width: 620px; }
        .home-background-date { display: inline-block; margin-top: 14px; padding: 7px 11px; border-radius: 999px; color: #fff; background: rgba(23,32,51,.62); font-size: .88rem; font-weight: 700; }
        .search-result { background: rgba(255,255,255,.72); border: 1px solid #e8edf3; border-radius: 12px; padding: 10px 14px; }
        [data-baseweb="tab-list"] {
            gap: 8px; background: rgba(255,255,255,.48); padding: 7px;
            border: 1px solid rgba(255,255,255,.72); border-radius: 14px;
            backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
        }
        [data-baseweb="tab"] {
            border-radius: 10px; color: #334155; font-weight: 700; padding: 8px 16px;
        }
        [aria-selected="true"][data-baseweb="tab"] {
            background: rgba(234,88,12,.14); color: #c2410c;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_heading(title, subtitle, background_image=None, icon_svg=None):
    """Display a visually consistent page heading."""
    if background_image is None:
        background_image = background_as_data_url(DATA_FOLDER / "login_background.jpg")
    alert_badge = ""
    banner_class = "page-banner"
    background_css = ""
    if title == "Home" and not background_image:
        banner_class += " page-banner-home"
    if background_image:
        banner_class += " page-banner-image"
        background_css = (
            "<style>.page-banner-image { background-image: "
            "linear-gradient(120deg, rgba(23,32,51,.48), rgba(48,73,104,.30)), "
            f"url('{background_image}') !important; background-position: center; background-size: cover; }}</style>"
        )
    if st.session_state.get("current_page", "Home") != "Home":
        alert_count = st.session_state.get("active_alert_count", 0)
        alert_badge = f"<span class='page-alert-badge'>🔔 {alert_count} active alerts</span>"
    title_html = f"<div class='page-banner-title'><h2>{title}</h2>{icon_svg}</div>" if icon_svg else f"<h2>{title}</h2>"
    st.markdown(
        f"{background_css}<div class='{banner_class}' style='display:flex;justify-content:space-between;align-items:center;gap:16px;'>"
        f"<div>{title_html}<div class='section-intro'>{subtitle}</div></div>{alert_badge}</div>",
        unsafe_allow_html=True,
    )


def choose_new_quote():
    """Choose a different motivational quote for the signed-in user."""
    current_quote = st.session_state.get("quote", "")
    choices = [quote for quote in MOTIVATIONAL_QUOTES if quote != current_quote]
    st.session_state.quote = random.choice(choices or MOTIVATIONAL_QUOTES)


def go_to_page(page):
    """Open a page and remember the previous page."""
    current_page = st.session_state.get("current_page", "Home")
    if current_page != page:
        st.session_state.setdefault("page_history", []).append(current_page)
        st.session_state.current_page = page


def go_back():
    """Return to the most recently opened page."""
    history = st.session_state.get("page_history", [])
    if history:
        st.session_state.current_page = history.pop()


def read_uploaded_table(uploaded_file):
    """Read a CSV or Excel file selected by the user."""
    if uploaded_file.name.lower().endswith(".csv"):
        return pd.read_csv(uploaded_file)
    return pd.read_excel(uploaded_file)


def show_data_importer(current_data, file_name, area_name):
    """Validate and safely replace one of the project's data tables."""
    with st.expander(f"Upload {area_name} data"):
        st.caption("Upload a CSV or Excel file with the same columns as the current table.")
        uploaded_file = st.file_uploader(
            "Choose a data file",
            type=["csv", "xlsx", "xls"],
            key=f"upload_{file_name}",
        )
        if uploaded_file is not None:
            try:
                uploaded_data = read_uploaded_table(uploaded_file)
                missing_columns = [column for column in current_data.columns if column not in uploaded_data.columns]
                if missing_columns:
                    st.error("Missing required columns: " + ", ".join(missing_columns))
                else:
                    st.success(f"File ready: {len(uploaded_data)} row(s) found.")
                    if st.button(f"Replace {area_name} data", key=f"save_{file_name}"):
                        save_data(uploaded_data[current_data.columns], file_name)
                        st.success(f"{area_name} data imported successfully.")
                        st.rerun()
            except Exception as error:
                st.error(f"The file could not be read: {error}")


def show_search_results(query, workers, incidents, equipment_summary, maintenance, alerts):
    """Search all project tables using normal pandas filtering."""
    if not query.strip():
        return
    data_sets = {
        "Worker safety": workers,
        "Safety incidents": incidents,
        "Equipment": pd.DataFrame(equipment_summary),
        "Maintenance": maintenance,
        "Alerts": pd.DataFrame(alerts),
    }
    with st.expander(f"Search results for: {query}", expanded=True):
        results_found = False
        for name, data_frame in data_sets.items():
            if data_frame.empty:
                continue
            matches = data_frame.astype(str).apply(
                lambda column: column.str.contains(query, case=False, na=False, regex=False)
            )
            filtered = data_frame[matches.any(axis=1)]
            if not filtered.empty:
                results_found = True
                st.markdown(f"<div class='search-result'><b>{name}</b> — {len(filtered)} matching record(s)</div>", unsafe_allow_html=True)
                st.dataframe(filtered, use_container_width=True, hide_index=True)
        if not results_found:
            st.info("No matching records were found.")


def show_top_navigation(workers, incidents, equipment_summary, maintenance, alerts):
    """Show top-left navigation and a system-wide search field."""
    current_page = st.session_state.get("current_page", "Home")
    history = st.session_state.get("page_history", [])
    back_column, home_column, search_column = st.columns([0.07, 0.12, 0.81])
    if history:
        if back_column.button("←", key="top_back", help="Go back", use_container_width=True):
            go_back()
            st.rerun()
    if current_page != "Home":
        if home_column.button("Home", key="top_home", use_container_width=True):
            # Keep the current page in history so Back returns here after Home.
            go_to_page("Home")
            st.rerun()
    with search_column:
        query = st.text_input(
            "Search the system",
            placeholder="Search workers, incidents, equipment, maintenance or alerts",
            label_visibility="collapsed",
            key="global_search",
        )
    show_search_results(query, workers, incidents, equipment_summary, maintenance, alerts)


def show_workspace_bar(user, alert_count):
    """Show the logged-in top bar using the quote chosen at sign-in."""
    if "quote" not in st.session_state:
        choose_new_quote()

    st.markdown(
        f"<div class='workspace-bar'><div><div class='workspace-user'>{user['role']} workspace</div>"
        f"<div class='workspace-quote'>“{st.session_state.quote}”</div></div>"
        f"<span class='status-chip chip-critical'>🔔 {alert_count} active alerts</span></div>",
        unsafe_allow_html=True,
    )


def background_as_data_url(image_path):
    """Convert one saved background image into a browser-ready data URL."""
    image_types = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
    image_type = image_types.get(image_path.suffix.lower(), "image/jpeg")
    encoded_image = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    return f"data:{image_type};base64,{encoded_image}"


def load_home_display_date():
    """Return the saved shared Home date, or today's date if none is saved."""
    try:
        saved_date = json.loads(HOME_SETTINGS_FILE.read_text(encoding="utf-8")).get("display_date")
        if saved_date:
            return datetime.strptime(saved_date, "%Y-%m-%d").date()
    except (FileNotFoundError, json.JSONDecodeError, TypeError, ValueError):
        pass
    return datetime.now().date()


def saved_backgrounds():
    """Return the permanently saved mine photos used on Home."""
    BACKGROUND_FOLDER.mkdir(parents=True, exist_ok=True)
    image_files = sorted(
        [
            path for path in BACKGROUND_FOLDER.iterdir()
            if path.name.startswith("mine_scene_") and path.suffix.lower() in [".png", ".jpg", ".jpeg"]
        ]
    )
    return [background_as_data_url(path) for path in image_files]


def show_home(workers, incidents, equipment_summary, alerts, user):
    """Show a personalised home page with role-based workspace cards."""
    background_path = DATA_FOLDER / "login_background.jpg"
    home_photos = saved_backgrounds()
    display_date = load_home_display_date()
    if home_photos:
        photo_number = st_autorefresh(interval=45000, key="home_photo_rotation")
        background_image = home_photos[photo_number % len(home_photos)]
        ready_card_image = home_photos[(photo_number + 1) % len(home_photos)]
    else:
        background_image = background_as_data_url(background_path)
        ready_card_image = background_image
    equipment_df = pd.DataFrame(equipment_summary)
    critical_equipment = int((equipment_df["Condition"] == "Critical").sum())
    open_incidents = int((incidents["Incident_Status"].astype(str).str.lower() != "closed").sum())
    critical_alerts = sum(1 for alert in alerts if alert["Level"] == "Critical")

    home_background_css = (
        "<style>.home-background-card { background-image: "
        "linear-gradient(120deg, rgba(23,32,51,.58), rgba(48,73,104,.38)), "
        f"url('{ready_card_image}') !important; background-position: center; background-size: cover; }}</style>"
    )

    overview_tab, workspace_tab, guide_tab = st.tabs(["Overview", "My workspaces", "How to use this app"])

    with overview_tab:
        page_heading("Home", f"Welcome back, {user['name']}. Choose a workspace to continue.", "", MINE_ICON_SVG)
        lead, score = st.columns([1.4, 1])
        with lead:
            st.markdown(
                "<div class='feature-card glass-panel'><h4>Mine monitoring is active</h4>"
                "<p>Critical items are surfaced first so the team can act quickly and make safer decisions.</p></div>",
                unsafe_allow_html=True,
            )
        with score:
            st.metric("Critical alerts needing attention", critical_alerts)
            st.caption("Open the Alerts page to see the exact rule that created each alert.")
        cols = st.columns(3)
        cols[0].metric("Workers on record", len(workers))
        cols[1].metric("Open incidents", open_incidents)
        cols[2].metric("Critical equipment", critical_equipment)

    with workspace_tab:
        st.markdown(
            f"{home_background_css}<div class='home-background-card glass-panel'>"
            "<h3>Ready for a safer shift</h3>"
            "<p>Monitor what matters, identify priorities and move quickly from insight to action.</p>"
            f"<div class='home-background-date'>{display_date.strftime('%d %b %Y')}</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        st.markdown("#### Your available workspaces")
        st.caption("Your role determines the pages shown here.")
        allowed_pages = pages_for_role(user["role"])
        for start in range(0, len(allowed_pages), 3):
            row_pages = allowed_pages[start:start + 3]
            row_columns = st.columns(3)
            for column, page in zip(row_columns, row_pages):
                title, description = WORKSPACE_DETAILS[page]
                with column:
                    st.markdown(
                        f"<div class='workspace-card'><div class='workspace-kicker'>Workspace</div>"
                        f"<h4>{title}</h4><p>{description}</p></div>",
                        unsafe_allow_html=True,
                    )
                    button_name = "Open alerts" if page == "Alerts" else f"Open {title.lower()}"
                    st.button(button_name, key=f"workspace_{page}", on_click=go_to_page, args=(page,), use_container_width=True)

    with guide_tab:
        st.markdown("#### A simple guide to using Khwezi Mine")
        st.markdown(
            """
            1. **Choose a workspace:** Open **My workspaces** and select the area you need, such as Worker Safety, Equipment or Alerts.
            2. **Review the overview:** Check the dashboard figures and alerts to see what needs attention.
            3. **Find the right records:** Use the filters on a workspace page to narrow the information. Press **Show** to view a data table and **Hide** when you are finished.
            4. **Move between pages:** Use the navigation buttons at the top. **Back** returns to the page you were using before.
            5. **Get help with your account:** Use **Change password** in the sidebar. Administrators can manage the shared Home and login background there too.

            Your available workspaces depend on your role. Only make changes when you have the right responsibility and current information.
            """
        )

def load_data(file_name):
    """Read one CSV file from the data folder."""
    return pd.read_csv(DATA_FOLDER / file_name)


def save_data(data_frame, file_name):
    """Save updated data to the same CSV file."""
    data_frame.to_csv(DATA_FOLDER / file_name, index=False)


def show_data_table(data_frame, label, key, hide_index=False):
    """Show a data table only after its show button is pressed."""
    state_key = f"show_table_{key}"
    is_visible = st.session_state.get(state_key, False)
    button_label = f"Hide {label}" if is_visible else f"Show {label}"
    if st.button(button_label, key=f"toggle_table_{key}"):
        st.session_state[state_key] = not is_visible
    if st.session_state.get(state_key, False):
        st.dataframe(data_frame, use_container_width=True, hide_index=hide_index)


def show_login():
    """Display the worker sign-in form without public account registration."""
    login_background = background_as_data_url(DATA_FOLDER / "login_background.jpg")
    st.markdown(
        f"""<style>
        .stApp {{
            background-image: linear-gradient(rgba(23, 32, 51, 0.43), rgba(23, 32, 51, 0.43)),
                              url('{login_background}');
            background-position: center;
            background-size: cover;
            background-attachment: fixed;
        }}
        [data-testid="stExpander"] {{
            background: rgba(255, 255, 255, 0.96) !important;
            border: 1px solid #ffffff !important;
            border-radius: 12px !important;
        }}
        [data-testid="stExpander"] summary,
        [data-testid="stExpander"] summary * {{
            color: #ffffff !important;
            font-weight: 700 !important;
        }}
        [data-testid="stExpander"] summary {{
            background: radial-gradient(circle at top right, rgba(251,146,60,.95), transparent 37%),
                        linear-gradient(120deg, #172033 0%, #263854 100%) !important;
            border-radius: 10px !important;
            padding: 11px 14px !important;
        }}
        [data-testid="stExpander"] summary svg {{ fill: #fdba74 !important; }}
        </style>""",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""<div class='hero'>
        <div class='eyebrow'>Mining operations centre</div>
        <h1 class='hero-title'><span>Khwezi Mine</span>{MINE_ICON_SVG}</h1>
        <p>One place to review safety, incidents, equipment condition and maintenance priorities.</p>
        </div>""",
        unsafe_allow_html=True,
    )
    with st.expander("Sign in", expanded=True):
        st.caption("Enter the username, Worker ID and password stored for your account.")
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="e.g. tabi.mtono")
            worker_id = st.text_input("Worker ID", placeholder="e.g. W001")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            submitted = st.form_submit_button("Enter monitoring centre", use_container_width=True)

        if submitted:
            user = login(username, worker_id, password)
            if user:
                st.session_state.user = user
                st.session_state.current_page = "Home"
                st.session_state.page_history = []
                st.session_state.show_workspace_loader = True
                st.session_state.welcome_until = time.time() + 15
                choose_new_quote()
                st.rerun()
            else:
                st.error("Your username, Worker ID or password is incorrect.")

        st.caption("Need access? Contact a Khwezi Mine Administrator. Only administrators can create worker accounts.")

    with st.expander("App information", expanded=False):
        st.markdown("<div class='eyebrow' style='color:#ea580c'>Built for safe decisions</div><p class='section-intro'>Monitor worker safety, incidents, equipment condition, and maintenance priorities across the mine.</p>", unsafe_allow_html=True)
        cards = st.columns(2)
        cards[0].markdown("<div class='feature-card'><h4>Worker safety</h4><p>Review PPE, training, fatigue, near misses and safety observations.</p></div>", unsafe_allow_html=True)
        cards[1].markdown("<div class='feature-card'><h4>Equipment</h4><p>Check temperature, vibration, availability and service requirements.</p></div>", unsafe_allow_html=True)
        cards[0].markdown("<div class='feature-card'><h4>Alerts</h4><p>See high-priority conditions without searching through spreadsheets.</p></div>", unsafe_allow_html=True)
        cards[1].markdown("<div class='feature-card'><h4>Risk control</h4><p>Use the transparent likelihood x consequence risk matrix.</p></div>", unsafe_allow_html=True)

def show_admin_account_form():
    """Show the account form directly beneath the Administrator profile card."""
    with st.sidebar.expander("Create worker account"):
        st.caption("Administrator-only access. The Worker ID must already exist in worker safety data.")
        with st.form("admin_create_account_form", clear_on_submit=True):
            worker_id = st.text_input("Worker ID", placeholder="W011")
            username = st.text_input("Username", placeholder="e.g. worker.name")
            full_name = st.text_input("Full name", placeholder="e.g. Worker Name")
            title = st.selectbox("Title", ["", "Mr.", "Ms.", "Mrs.", "Dr."])
            role = st.selectbox("Role", available_roles())
            password = st.text_input("Temporary password", type="password", help="Use at least 8 characters.")
            confirm_password = st.text_input("Confirm temporary password", type="password")
            submitted = st.form_submit_button("Create account", use_container_width=True)

        if submitted:
            if password != confirm_password:
                st.error("The two passwords do not match.")
            else:
                success, message = create_account(worker_id, username, password, full_name, title, role)
                if success:
                    st.success(message)
                else:
                    st.error(message)


def show_dashboard(workers, incidents, equipment_summary, alerts):
    """Display KPI cards and simple analytics."""
    page_heading("Operations dashboard", "A quick view of the current safety and equipment picture.")
    critical_alerts = sum(1 for alert in alerts if alert["Level"] == "Critical")
    workers_at_risk = 0
    for _, worker in workers.iterrows():
        _, level = worker_risk(worker["PPE_Compliance"], worker["Safety_Training_Status"], worker["Fatigue_Level"], worker["Safety_Observations"], worker["Near_Misses"], worker["Previous_Incidents"])
        if level == "High":
            workers_at_risk += 1

    equipment_df = pd.DataFrame(equipment_summary)
    open_incidents = incidents[incidents["Incident_Status"].astype(str).str.lower() != "closed"]
    cols = st.columns(5)
    cols[0].metric("Workers", len(workers))
    cols[1].metric("Open incidents", len(open_incidents))
    cols[2].metric("Workers at high risk", workers_at_risk)
    cols[3].metric("Critical equipment", int((equipment_df["Condition"] == "Critical").sum()))
    cols[4].metric("Critical alerts", critical_alerts)

    st.markdown("#### Current operational status")
    condition_counts = equipment_df["Condition"].value_counts().to_dict()
    st.markdown(
        f"<span class='status-chip chip-normal'>● Normal: {condition_counts.get('Normal', 0)}</span>"
        f"<span class='status-chip chip-warning'>● Warning: {condition_counts.get('Warning', 0)}</span>"
        f"<span class='status-chip chip-critical'>● Critical: {condition_counts.get('Critical', 0)}</span>",
        unsafe_allow_html=True,
    )

    incident_col, severity_bar_col = st.columns(2)
    with incident_col:
        incident_chart = px.pie(incidents, names="Severity", title="Incident severity", hole=0.55)
        st.plotly_chart(incident_chart, use_container_width=True)
    with severity_bar_col:
        severity_counts = incidents["Severity"].value_counts().rename_axis("Severity").reset_index(name="Incident count")
        severity_bar = px.bar(
            severity_counts, x="Severity", y="Incident count", color="Severity",
            title="Incidents by severity",
        )
        st.plotly_chart(severity_bar, use_container_width=True)

    chart = px.bar(
        equipment_df, x="Equipment ID", y="Temperature (°C)", color="Condition",
        color_discrete_map={"Normal": "green", "Warning": "orange", "Critical": "red"},
        title="Equipment temperature status",
    )
    st.plotly_chart(chart, use_container_width=True)
    st.caption("Temperature: normal below 80 °C; warning 80–100 °C; critical above 100 °C.")

def show_worker_safety(workers):
    """Show, filter and add worker safety data."""
    page_heading("Worker safety", "Track the practical conditions that affect the people on site.")
    show_data_importer(workers, "workers.csv", "worker safety")
    department = st.selectbox("Filter by department", ["All"] + sorted(workers["Department"].dropna().unique().tolist()))
    displayed = workers if department == "All" else workers[workers["Department"] == department]
    show_data_table(displayed, "worker safety data", "worker_safety")

    if "show_worker_observation_form" not in st.session_state:
        st.session_state.show_worker_observation_form = False
    if not st.session_state.show_worker_observation_form:
        if st.button("Add a worker safety observation", key="open_worker_observation_form"):
            st.session_state.show_worker_observation_form = True
            st.rerun()
    else:
        st.subheader("Add a worker safety observation")
        with st.form("worker_form", clear_on_submit=True):
            left, right = st.columns(2)
            worker_id = left.text_input("Worker ID", placeholder="W021")
            worker_department = left.text_input("Department")
            job_role = left.text_input("Job role")
            shift = left.selectbox("Shift", ["Day", "Night"])
            ppe = right.checkbox("PPE compliant", value=True)
            training = right.selectbox("Safety training", ["Current", "Expired", "Not completed"])
            fatigue = right.selectbox("Fatigue level", ["Low", "Medium", "High"])
            observations = right.number_input("Safety observations", min_value=0, step=1)
            near_misses = right.number_input("Near misses", min_value=0, step=1)
            previous_incidents = right.number_input("Previous incidents", min_value=0, step=1)
            save_worker = st.form_submit_button("Save worker record")
        if save_worker:
            if worker_id and worker_department and job_role:
                score, level = worker_risk(ppe, training, fatigue, observations, near_misses, previous_incidents)
                new_row = pd.DataFrame([[worker_id, worker_department, job_role, shift, ppe, training, fatigue, observations, near_misses, previous_incidents, level]], columns=workers.columns)
                save_data(pd.concat([workers, new_row], ignore_index=True), "workers.csv")
                st.session_state.show_worker_observation_form = False
                st.success(f"Worker record saved. Rule-based risk score: {score} ({level}).")
                st.rerun()
            else:
                st.warning("Enter Worker ID, Department and Job role.")


def show_incidents(incidents):
    """Show incident records and an entry form."""
    page_heading("Safety incidents", "Review, filter and record safety events in one place.")
    show_data_importer(incidents, "incidents.csv", "safety incident")
    severity_filter = st.multiselect("Filter by severity", sorted(incidents["Severity"].dropna().unique().tolist()))
    displayed = incidents if not severity_filter else incidents[incidents["Severity"].isin(severity_filter)]
    show_data_table(displayed, "incident data", "incidents")
    trend = incidents.groupby("Department").size().reset_index(name="Incident count")
    st.plotly_chart(px.bar(trend, x="Department", y="Incident count", title="Incidents by department"), use_container_width=True)

    st.subheader("Report a safety incident")
    with st.form("incident_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        incident_id = c1.text_input("Incident ID", placeholder="INC021")
        incident_date = c1.date_input("Date")
        incident_time = c1.time_input("Time")
        shift = c1.selectbox("Shift", ["Day", "Night"])
        location = c2.text_input("Location")
        department = c2.text_input("Department")
        incident_type = c2.text_input("Incident type")
        severity = c2.selectbox("Severity", ["Minor", "Moderate", "Major", "Fatal"])
        injury = c3.selectbox("Injury status", ["No Injury", "Injured"])
        lost_time = c3.checkbox("Lost-time injury")
        cause = c3.text_input("Cause")
        action = c3.text_input("Corrective action")
        status = c3.selectbox("Status", ["Open", "Under Investigation", "Closed"])
        save_incident = st.form_submit_button("Save incident")
    if save_incident:
        required = [incident_id, location, department, incident_type, cause, action]
        if all(required):
            values = [[incident_id, incident_date.isoformat(), incident_time.strftime("%H:%M"), shift, location, department, incident_type, severity, injury, lost_time, cause, action, status]]
            new_row = pd.DataFrame(values, columns=incidents.columns)
            save_data(pd.concat([incidents, new_row], ignore_index=True), "incidents.csv")
            st.success("Incident saved to data/incidents.csv.")
        else:
            st.warning("Complete every text field before saving.")


def show_equipment(equipment, equipment_summary):
    """Display equipment condition monitoring with one-machine feedback."""
    page_heading("Equipment Condition Monitoring", "Prioritise inspection using visible temperature and vibration limits.")
    show_data_importer(equipment, "equipment.csv", "equipment")
    eq = pd.DataFrame(equipment_summary).rename(columns={
        "Equipment ID": "equipment_id",
        "Temperature (°C)": "temperature",
        "Vibration (mm/s)": "vibration",
        "Availability (%)": "availability",
        "Condition": "status",
    })
    eq["status"] = eq["status"].astype(str).str.upper()
    show_data_table(eq, "equipment data", "equipment", hide_index=True)
    pick = st.selectbox("Check one machine", eq["equipment_id"])
    record = eq[eq["equipment_id"] == pick].iloc[0]
    if float(record["temperature"]) > 100 or float(record["vibration"]) > 8:
        level = "CRITICAL"
        message = "Temperature or vibration exceeds the critical threshold. Inspection required."
    elif float(record["temperature"]) >= 80 or float(record["vibration"]) >= 5:
        level = "WARNING"
        message = "Temperature or vibration is approaching a critical threshold."
    else:
        level = "NORMAL"
        message = "Equipment is operating within the defined monitoring limits."
    text = f"{level}: {message}"
    if level == "NORMAL":
        st.success(text)
    elif level == "WARNING":
        st.warning(text)
    else:
        st.error(text)
    st.plotly_chart(
        px.scatter(eq, x="temperature", y="vibration", color="status", hover_name="equipment_id", title="Temperature vs vibration"),
        use_container_width=True,
    )
    st.caption("Educational prototype thresholds only - not manufacturer or mine safety limits.")


def show_maintenance(maintenance, equipment_summary):
    """Display grouped equipment maintenance monitoring conditions."""
    from datetime import date

    page_heading("Equipment Maintenance Monitoring", "Keep service plans and equipment availability visible.")
    show_data_importer(maintenance, "maintenance.csv", "maintenance")
    HIGH_DOWNTIME = 12
    LOW_AVAIL = 85
    eq = pd.DataFrame(equipment_summary).rename(columns={
        "Equipment ID": "equipment_id",
        "Availability (%)": "availability",
    })
    eq["type"] = "Mining equipment"
    eq["maintenance_status"] = "Not Due"
    eq["alerts_count"] = 0

    for index, row in eq.iterrows():
        records = maintenance[maintenance["Equipment_ID"].astype(str) == str(row["equipment_id"])]
        if not records.empty:
            statuses = records["Status"].astype(str).str.lower()
            due_dates = pd.to_datetime(records["Next_Due_Date"], errors="coerce")
            eq.loc[index, "alerts_count"] = int(records["Alert_Count"].fillna(0).sum())
            if (statuses == "overdue").any() or (due_dates.dt.date < date.today()).any():
                eq.loc[index, "maintenance_status"] = "Overdue"
            elif (statuses == "under maintenance").any():
                eq.loc[index, "maintenance_status"] = "Under Maintenance"
            elif (statuses == "scheduled").any():
                eq.loc[index, "maintenance_status"] = "Due"

    groups = {
        "Due for maintenance": eq[eq["maintenance_status"] == "Due"],
        "Overdue": eq[eq["maintenance_status"] == "Overdue"],
        "Under maintenance": eq[eq["maintenance_status"] == "Under Maintenance"],
        "Excessive downtime": eq[eq["Downtime (hours)"] > HIGH_DOWNTIME],
        "Repeated alerts (3+)": eq[eq["alerts_count"] >= 4],
        f"Low availability (<{LOW_AVAIL}%)": eq[eq["availability"] < LOW_AVAIL],
    }
    for name, frame in groups.items():
        with st.expander(f"{name}: {len(frame)}"):
            st.dataframe(
                frame[["equipment_id", "type", "maintenance_status", "Downtime (hours)", "availability", "alerts_count"]],
                use_container_width=True,
                hide_index=True,
            )


def show_risk_assessment():
    """Let users calculate the project risk matrix result themselves."""
    page_heading("Risk assessment", "Calculate the risk score before deciding on controls.")
    st.write("Risk score = likelihood × consequence. Choose a value from 1 (low) to 5 (very high).")
    c1, c2 = st.columns(2)
    likelihood = c1.slider("Likelihood", 1, 5, 3)
    consequence = c2.slider("Consequence", 1, 5, 3)
    score, level = risk_level(likelihood, consequence)
    st.metric("Risk score", score)
    if level == "Critical":
        st.error("CRITICAL: Stop and escalate this risk before work continues.")
    elif level == "High":
        st.error("HIGH: Controls are required before work continues.")
    elif level == "Medium":
        st.warning("MEDIUM: Review and apply controls.")
    else:
        st.success("LOW: Continue monitoring this risk.")


def show_alerts(alerts):
    """Show every automatically-created rule-based alert."""
    page_heading("Alerts & notifications", "Rule-based alerts from the current worker, incident, equipment and maintenance data.")
    st.write("Alerts below are generated by the visible rules in `utils/logic.py`.")
    alert_df = pd.DataFrame(alerts)
    if alert_df.empty:
        st.success("No active alerts.")
        return
    show_data_table(alert_df, "alert data", "alerts")
    for _, alert in alert_df.iterrows():
        message = f"{alert['Area']} — {alert['Item']}: {alert['Message']}"
        if alert["Level"] == "Critical":
            st.error(message)
        elif alert["Level"] == "High":
            st.warning(message)
        else:
            st.info(message)


def main():
    """Run the login page or the application navigation."""
    apply_custom_style()
    if "user" not in st.session_state:
        show_login()
        return

    if st.session_state.get("show_workspace_loader", False):
        if time.time() < st.session_state.get("welcome_until", 0):
            welcome_name = html.escape(st.session_state.user["name"])
            welcome_quote = html.escape(st.session_state.get("quote", ""))
            welcome_background = background_as_data_url(DATA_FOLDER / "login_background.jpg")
            st.markdown(
                textwrap.dedent(f"""
                <style>
                .welcome-screen {{
                    box-sizing: border-box; width: 100%; min-height: calc(100vh - 2rem);
                    display: flex; align-items: center; justify-content: center; text-align: center;
                    padding: 36px; border-radius: 24px; color: #fff;
                    background: radial-gradient(circle at top right, rgba(251,146,60,.38), transparent 36%),
                                linear-gradient(rgba(23,32,51,.68), rgba(23,32,51,.72)),
                                url('{welcome_background}') center / cover no-repeat;
                }}
                .welcome-content {{ max-width: 760px; }}
                .welcome-mark {{ width: 112px; height: auto; margin: 0 auto 22px auto; display: block; }}
                .welcome-eyebrow {{ color: #fdba74; text-transform: uppercase; letter-spacing: 2px; font-weight: 800; font-size: .82rem; }}
                .welcome-title {{ color: #fff !important; font-size: clamp(2.2rem, 5vw, 3.4rem); margin: 12px 0; }}
                .welcome-copy {{ color: #e2e8f0; font-size: 1.12rem; margin: 0 auto 12px auto; }}
                .welcome-motivation-label {{ color: #fdba74; text-transform: uppercase; letter-spacing: 1.5px; font-size: .76rem; font-weight: 800; margin: 22px 0 7px; }}
                .welcome-quote {{ color: #fff7ed; font-size: 1.15rem; font-style: italic; font-weight: 600; margin: 0 auto 30px auto; }}
                .welcome-track {{ height: 8px; max-width: 460px; margin: 0 auto 14px auto; border-radius: 99px; background: rgba(255,255,255,.22); overflow: hidden; }}
                .welcome-track span {{ display: block; height: 100%; width: 0; border-radius: inherit; background: #f97316; animation: welcome-load 15s linear forwards; }}
                .welcome-status {{ color: #cbd5e1; font-size: .92rem; }}
                @keyframes welcome-load {{ to {{ width: 100%; }} }}
                </style>
                <div class='welcome-screen'><div class='welcome-content'>
                    {MINE_ICON_SVG.replace("mine-mark", "welcome-mark").replace("\n", "")}
                    <div class='welcome-eyebrow'>Mining operations centre</div>
                    <h1 class='welcome-title'>Welcome, {welcome_name}</h1>
                    <p class='welcome-copy'>Preparing your Khwezi Mine workspace</p>
                    <div class='welcome-motivation-label'>Motivational message</div>
                    <p class='welcome-quote'>“{welcome_quote}”</p>
                    <div class='welcome-track'><span></span></div>
                    <div class='welcome-status'>Loading your safety and operations overview…</div>
                </div></div>
                """),
                unsafe_allow_html=True,
            )
            st_autorefresh(interval=1000, key="welcome_notice_refresh")
            return
        st.session_state.show_workspace_loader = False
        st.session_state.pop("welcome_until", None)

    workers = load_data("workers.csv")
    incidents = load_data("incidents.csv")
    equipment = load_data("equipment.csv").fillna({"Engine_Temp (°C)": 0, "Vibration_Level (mm/s)": 0, "Hours_Since_Last_Service": 0})
    maintenance = load_data("maintenance.csv").fillna({"Downtime_Hours": 0, "Alert_Count": 0})
    equipment_summary = build_equipment_summary(equipment, maintenance)
    alerts = build_alerts(workers, incidents, equipment_summary, maintenance)
    st.session_state.active_alert_count = len(alerts)

    user = st.session_state.user
    initials = "".join(part[0] for part in user["name"].split()[:2]).upper()
    welcome_name = f"{user['title']} {user['name']}".strip()
    st.sidebar.markdown(
        f"<div class='sidebar-brand'>{MINE_ICON_SVG}<span>Khwezi Mining</span></div>",
        unsafe_allow_html=True,
    )
    st.sidebar.caption("OPERATIONS CENTRE")
    st.sidebar.markdown(
        f"<div class='profile-card'><div class='profile-avatar'>{initials}</div>"
        f"<div class='profile-name'>Welcome, {welcome_name}</div>"
        f"<div class='profile-role'>{user['role']} - Khwezi Mine</div>"
        f"<div class='profile-role'>Worker ID: {user['worker_id']}</div></div>",
        unsafe_allow_html=True,
    )

    if user["role"] == "Administrator":
        show_admin_account_form()
        with st.sidebar.expander("Personalise Home page"):
            st.caption("Set the fixed background for all staff. This updates both the login page and Home.")
            selected_home_date = st.date_input(
                "Date shown on the Home card",
                value=load_home_display_date(),
                key="shared_home_display_date",
            )
            if st.button("Save Home date", key="save_home_display_date", use_container_width=True):
                HOME_SETTINGS_FILE.write_text(
                    json.dumps({"display_date": selected_home_date.isoformat()}, indent=2),
                    encoding="utf-8",
                )
                st.success("The Home card date has been saved for all staff.")
                st.rerun()
            background_file = st.file_uploader(
                "Choose a replacement background image",
                type=["jpg", "jpeg"],
                key="shared_background_uploader",
            )
            if background_file and st.button("Save shared background", key="save_shared_background", use_container_width=True):
                (DATA_FOLDER / "login_background.jpg").write_bytes(background_file.getvalue())
                st.success("The shared login and Home background has been saved for all staff.")
                st.rerun()

    with st.sidebar.expander("Change password"):
        with st.form("change_password_form", clear_on_submit=True):
            current_password = st.text_input("Current password", type="password")
            new_password = st.text_input("New password", type="password", help="Use at least 8 characters.")
            confirm_new_password = st.text_input("Confirm new password", type="password")
            password_submitted = st.form_submit_button("Update password", use_container_width=True)
        if password_submitted:
            if new_password != confirm_new_password:
                st.error("The new passwords do not match.")
            else:
                success, message = change_password(user["worker_id"], current_password, new_password)
                if success:
                    st.success(message)
                else:
                    st.error(message)

    if st.sidebar.button("Sign out", use_container_width=True):
        del st.session_state.user
        st.session_state.pop("current_page", None)
        st.session_state.pop("quote", None)
        st.session_state.pop("page_history", None)
        st.rerun()

    available_pages = ["Home"] + pages_for_role(st.session_state.user["role"])
    if st.session_state.get("current_page") not in available_pages:
        st.session_state.current_page = "Home"
    page = st.session_state.current_page
    show_top_navigation(workers, incidents, equipment_summary, maintenance, alerts)
    if page == "Home":
        show_workspace_bar(user, len(alerts))
    if page == "Home":
        show_home(workers, incidents, equipment_summary, alerts, user)
    elif page == "Dashboard":
        show_dashboard(workers, incidents, equipment_summary, alerts)
    elif page == "Worker Safety":
        show_worker_safety(workers)
    elif page == "Safety Incidents":
        show_incidents(incidents)
    elif page == "Equipment":
        show_equipment(equipment, equipment_summary)
    elif page == "Maintenance":
        show_maintenance(maintenance, equipment_summary)
    elif page == "Risk Assessment":
        show_risk_assessment()
    elif page == "Alerts":
        show_alerts(alerts)


if __name__ == "__main__":
    main()
