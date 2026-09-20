
import streamlit as st
from google import genai
from pypdf import PdfReader
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from html import escape
from pathlib import Path
import base64
import textwrap
import calendar
import json
import ast
import uuid
from datetime import date, datetime

# Optional Google integrations
try:
    import gspread
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload
    GOOGLE_LIBS_AVAILABLE = True
except Exception:
    GOOGLE_LIBS_AVAILABLE = False

# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="GM Policy Assistant - Germane Media LLC",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# CONFIGURATION
# ============================================================
HR_EMAIL = "tarang@thegermanemedia.com"
COMPANY_DOMAIN = "thegermanemedia.com"
HR_BOOKING_URL = "https://calendar.app.google/wjkBcfyeAgKqCRUVA"
DIRECT_GOOGLE_CHAT_HR = "https://chat.google.com/dm/tarang@thegermanemedia.com"
POLICY_PDF = "GERMANE_MEDIA_LLC_POLICY_DOCUMENT.pdf"
GEMINI_MODEL = "gemini-3.6-flash"

REIMBURSEMENT_CUTOFF_DAY = 22
REIMBURSEMENT_CYCLE_MONTHS = 3

# Per the current portal design requested:
# Wi-Fi, Gym/Health and Course: 1 invoice per month, ₹1,000 cap.
# Other: multiple invoices, no ₹1,000 cap.
REIMBURSEMENT_TYPES = {
    "Wi-Fi / Internet": {"monthly_limit": 1000, "max_invoices": 1},
    "Gym / Health": {"monthly_limit": 1000, "max_invoices": 1},
    "Course": {"monthly_limit": 1000, "max_invoices": 1},
    "Other Reimbursement": {"monthly_limit": None, "max_invoices": None},
}

# Google Sheet / Drive settings
REIMBURSEMENT_SHEET_NAME = "Germane Media - Employee Reimbursements"
REIMBURSEMENT_DRIVE_FOLDER_NAME = "Germane Media - Reimbursement Bills"

# Google Shared Drive destination for reimbursement invoices.
# Service accounts do not have personal Drive storage, so invoices must be
# uploaded into a Shared Drive.
REIMBURSEMENT_SHARED_DRIVE_ID = "0ABjzNoo-x_RwUk9PVA"
REIMBURSEMENT_DRIVE_FOLDER_ID = "1Qrozesa14l5UPoCqU-zdVfR0GDNHRTum"

# Job Referral Portal settings
JOB_REFERRAL_SHEET_NAME = "Germane Media - Job Referrals"
JOB_REFERRAL_DRIVE_FOLDER_ID = "1CNwDzA4ujA2n2xV34vbtMjbqyHlYYnee"

# ============================================================
# UI
# ============================================================
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}
#MainMenu, footer, header { visibility: hidden; }
/* Main application background */
.stApp {
    background: #1e1f23 !important;
    color: #f3f4f6 !important;
}

/* Keep the reimbursement portal cards light */

/* AI chat messages */
div[data-testid="stChatMessage"] {
    background: #292b31 !important;
    border: 1px solid #3a3d45 !important;
    border-radius: 14px !important;
    padding: 16px 18px !important;
    margin: 12px 0 !important;
}

/* User messages */
div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background: #34363d !important;
}

/* Assistant messages */
div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    background: #25272c !important;
}

/* Text inside chat messages */
div[data-testid="stChatMessage"] p,
div[data-testid="stChatMessage"] li,
div[data-testid="stChatMessage"] span {
    color: #f1f3f5 !important;
}

/* Headings inside AI answers */
div[data-testid="stChatMessage"] h1,
div[data-testid="stChatMessage"] h2,
div[data-testid="stChatMessage"] h3,
div[data-testid="stChatMessage"] h4 {
    color: #ffffff !important;
}

/* Code blocks */
div[data-testid="stChatMessage"] pre {
    background: #17181c !important;
    border: 1px solid #3b3e46 !important;
    color: #f3f4f6 !important;
}

div[data-testid="stChatMessage"] code {
    background: #17181c !important;
    color: #e5e7eb !important;
}

/* Chat input */
div[data-testid="stChatInput"] {
    background: #25272c !important;
    border: 1px solid #454851 !important;
    border-radius: 14px !important;
}

div[data-testid="stChatInput"] textarea {
    background: #25272c !important;
    color: #ffffff !important;
}

div[data-testid="stChatInput"] textarea::placeholder {
    color: #9ca3af !important;
}

div[data-testid="stChatInput"]:focus-within {
    border-color: #6b4de6 !important;
    box-shadow: 0 0 0 1px #6b4de6 !important;
}

/* Policy Assistant text */
.brand-title { color: #ffffff !important; }
.brand-sub { color: #aeb4c0 !important; }

/* Private HR conversation card */
.info-card {
    background: #292b31 !important;
    border-color: #3a3d45 !important;
}
.info-card b { color: #ffffff !important; }
.info-card span { color: #b7bdc8 !important; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #18191d !important;
}

/* General text in dark areas */
.stMarkdown, div[data-testid="stCaptionContainer"] {
    color: #f3f4f6;
}

/* Dividers */
/* Login page only - restored light landing-page design */
.gm-login-marker { display:none; }
.stApp:has(.gm-login-marker) {
    background: #f8f9fd !important;
    color: #17233c !important;
}
.stApp:has(.gm-login-marker) section[data-testid="stSidebar"] { display:none !important; }
.stApp:has(.gm-login-marker) .main .block-container {
    max-width: 1280px !important;
    padding-top: 52px !important;
    padding-bottom: 40px !important;
}
.gm-login-shell {
    max-width: 1280px;
    margin: 0 auto;
    display: grid;
    grid-template-columns: 1.05fr 0.95fr;
    gap: 62px;
    align-items: center;
}
.gm-login-brand { display:flex; align-items:center; gap:18px; }
.gm-login-brand .brand-logo { width:90px !important; height:90px !important; object-fit:contain; }
.gm-login-brand .brand-logo-fallback { width:90px; height:90px; border-radius:20px; background:#6547ed; color:#fff; display:flex; align-items:center; justify-content:center; font-size:50px; font-weight:800; }
.gm-login-brand-title { font-size:30px; font-weight:800; color:#17233c; }
.gm-login-brand-sub { color:#5c4bb5; font-size:18px; font-weight:700; margin-top:7px; }
.gm-login-brand-line { width:70px; height:3px; background:#6547ed; margin-top:17px; border-radius:3px; }
.gm-login-heading { font-size:29px; line-height:1.25; color:#17233c; margin:57px 0 13px; }
.gm-login-description { font-size:16px; line-height:1.7; color:#667085; max-width:650px; margin:0; }
.gm-login-features { display:grid; grid-template-columns:1fr 1fr; gap:31px 42px; margin-top:43px; }
.gm-login-feature { display:flex; gap:16px; align-items:flex-start; }
.gm-login-feature-icon {
    width:58px; height:58px; min-width:58px; border-radius:18px;
    background:#f0efff; color:#5c4bb5; display:flex; align-items:center; justify-content:center;
    font-size:25px; font-weight:700;
}
.gm-login-feature-title { font-size:16px; font-weight:800; color:#17233c; margin:2px 0 8px; }
.gm-login-feature-text { font-size:14px; line-height:1.55; color:#737b8c; }
.gm-login-right { min-width:0; }
.gm-login-card {
    background:#fff; border:1px solid #e4e7ef; border-radius:22px;
    box-shadow:0 14px 40px rgba(32,35,58,.08); overflow:hidden;
}
.gm-login-lock {
    width:76px; height:76px; margin:26px auto 12px; border-radius:50%;
    background:#f0efff; display:flex; align-items:center; justify-content:center; font-size:35px;
}
.gm-login-card-title { text-align:center; font-size:30px; font-weight:800; color:#17233c; }
.gm-login-card-sub { text-align:center; color:#747d8e; font-size:15px; margin:9px 20px 27px; }
.gm-login-divider { height:1px; background:#e8eaf0; }
.gm-login-company-line { padding:24px 28px; color:#5c4bb5; font-weight:700; font-size:15px; }
.gm-login-button-wrap { margin-top:18px; }
.stApp:has(.gm-login-marker) div[data-testid="stButton"] {
    width: calc(47% - 12px) !important;
    margin-left: auto !important;
    margin-right: 0 !important;
    margin-top: -76px !important;
    position: relative !important;
    z-index: 5 !important;
}
.stApp:has(.gm-login-marker) div[data-testid="stButton"] > button[kind="primary"] {
    height:58px !important; border-radius:12px !important;
    background:#6547ed !important; border:1px solid #6547ed !important;
    color:#fff !important; font-weight:700 !important; font-size:15px !important;
    box-shadow:none !important;
}
.stApp:has(.gm-login-marker) div[data-testid="stButton"] > button[kind="primary"]:hover {
    background:#5839dc !important; border-color:#5839dc !important;
}
@media (max-width: 900px) {
    .gm-login-shell { grid-template-columns:1fr; gap:35px; }
    .gm-login-features { gap:24px; }
}


hr { border-color: #3a3d45 !important; }

/* ========================================================
   REIMBURSEMENT PORTAL - HIGH CONTRAST ON DARK BACKGROUND
   ======================================================== */
.portal-hero {
    background: linear-gradient(135deg,#ffffff 0%,#f6f3ff 100%) !important;
}
.portal-kicker { color:#6b4de6 !important; }
.portal-title { color:#17233c !important; }
.portal-subtitle { color:#52627a !important; }

/* Top employee/company/deadline cards */
.info-card {
    background:#292b31 !important;
    border:1px solid #3a3d45 !important;
}
.info-label { color:#aeb7c8 !important; }
.info-value { color:#ffffff !important; }

/* Green/blue Streamlit alerts remain readable */
div[data-testid="stAlert"] p,
div[data-testid="stAlert"] span {
    color:#ffffff !important;
}

/* Cycle explanation */
.rule-strip {
    background:#ffffff !important;
    border:1px solid #e3e6ee !important;
}
.rule-strip strong { color:#17233c !important; }
.rule-strip span { color:#52627a !important; }

/* Section headings on the dark page */
.section-title { color:#ffffff !important; }
.section-caption { color:#aeb7c8 !important; }

/* Month cards */
.month-card {
    background:#292b31 !important;
    border:1px solid #3a3d45 !important;
    box-shadow:none !important;
}
.month-heading { color:#ffffff !important; }
.month-caption { color:#aeb7c8 !important; }

/* Reimbursement type cards */
.type-card {
    background:#23252a !important;
    border:1px solid #3a3d45 !important;
}
.type-title { color:#ffffff !important; }
.type-subtitle { color:#aeb7c8 !important; }

/* Eligible amount */
.eligible-box {
    background:#302a4a !important;
    border-color:#51458a !important;
}
.eligible-label { color:#c7bcff !important; }
.eligible-value { color:#ffffff !important; }

/* Review area */
.review-card {
    background:#292b31 !important;
    border-color:#3a3d45 !important;
}
.review-row { border-bottom-color:#3a3d45 !important; }
.review-month { color:#ffffff !important; }
.review-type { color:#aeb7c8 !important; }
.review-amount { color:#ffffff !important; }

/* Native Streamlit controls used by reimbursement portal */
div[data-testid="stMultiSelect"] label,
div[data-testid="stNumberInput"] label,
div[data-testid="stFileUploader"] label {
    color:#f3f4f6 !important;
}
div[data-testid="stMultiSelect"] [data-baseweb="select"],
div[data-testid="stNumberInput"] input,
div[data-testid="stFileUploaderDropzone"] {
    background:#292b31 !important;
    color:#ffffff !important;
    border-color:#454851 !important;
}
div[data-testid="stMultiSelect"] [data-baseweb="select"] *,
div[data-testid="stNumberInput"] input {
    color:#ffffff !important;
}
div[data-testid="stMultiSelect"] input::placeholder,
div[data-testid="stNumberInput"] input::placeholder {
    color:#aeb7c8 !important;
}

/* Captions and helper text throughout reimbursement portal */
div[data-testid="stCaptionContainer"] p,
div[data-testid="stCaptionContainer"] span {
    color:#aeb7c8 !important;
}

/* Expander text */
div[data-testid="stExpander"] {
    border-color:#454851 !important;
}
div[data-testid="stExpander"] summary,
div[data-testid="stExpander"] summary span {
    color:#ffffff !important;
}

.block-container { max-width: 1440px !important; padding: 28px 42px 40px !important; }

.brand-title { font-size: 24px; font-weight: 800; color:#17233c; letter-spacing:-.4px; }
.brand-sub { font-size:13px; color:#6b7280; margin-bottom:18px; }

.portal-hero {
    background: linear-gradient(135deg,#ffffff 0%,#f6f3ff 100%);
    border:1px solid #e7e2fb; border-radius:22px;
    padding:30px 32px; margin-bottom:22px;
    box-shadow:0 8px 30px rgba(31,35,55,.05);
}
.portal-kicker { color:#6b4de6; font-size:12px; font-weight:800; text-transform:uppercase; letter-spacing:1px; }
.portal-title { color:#17233c; font-size:31px; font-weight:800; margin-top:5px; }
.portal-subtitle { color:#667085; font-size:14px; margin-top:7px; }

.info-card {
    background:#fff; border:1px solid #e6e8ef; border-radius:16px;
    padding:18px 20px; box-shadow:0 5px 20px rgba(31,35,55,.035);
}
.info-label { color:#7b8496; font-size:11px; text-transform:uppercase; letter-spacing:.8px; font-weight:700; }
.info-value { color:#1d263b; font-size:15px; font-weight:700; margin-top:4px; }

.rule-strip {
    background:#fff; border:1px solid #e7e8ee; border-radius:14px;
    padding:14px 16px; margin:12px 0 22px;
}
.rule-strip strong { color:#1f2937; }
.rule-strip span { color:#667085; font-size:13px; }

.section-head { margin:28px 0 10px; }
.section-title { font-size:20px; font-weight:800; color:#18233a; }
.section-caption { font-size:12px; color:#7b8496; margin-top:3px; }

.month-card {
    background:#fff; border:1px solid #e4e6ee; border-radius:20px;
    padding:22px 22px 18px; margin:20px 0;
    box-shadow:0 8px 26px rgba(31,35,55,.045);
}
.month-heading { font-size:22px; font-weight:800; color:#17233c; }
.month-caption { font-size:12px; color:#7b8496; margin-top:3px; margin-bottom:14px; }

.type-card {
    background:#fbfbfd; border:1px solid #e6e7ee; border-radius:15px;
    padding:18px; margin:14px 0;
}
.type-title { font-size:16px; font-weight:800; color:#252d40; }
.type-subtitle { font-size:11px; color:#7b8496; margin-top:2px; margin-bottom:12px; }

.eligible-box {
    background:#f5f2ff; border:1px solid #ded6ff; border-radius:12px;
    padding:12px 14px; margin-top:12px;
}
.eligible-label { color:#6b5aa8; font-size:11px; text-transform:uppercase; font-weight:800; letter-spacing:.6px; }
.eligible-value { color:#5c43d4; font-size:21px; font-weight:800; margin-top:2px; }

.review-card {
    background:#fff; border:1px solid #e3e6ee; border-radius:18px;
    padding:20px; margin-top:18px;
}
.review-row { padding:11px 0; border-bottom:1px solid #eef0f4; }
.review-row:last-child { border-bottom:0; }
.review-month { font-weight:800; color:#20283a; }
.review-type { color:#6b7280; font-size:12px; }
.review-amount { text-align:right; font-weight:700; color:#374151; }

.total-card {
    background:linear-gradient(135deg,#1f2a44,#40316f);
    color:white; border-radius:20px; padding:24px 26px; margin-top:20px;
    box-shadow:0 12px 35px rgba(43,36,91,.20);
}
.total-label { font-size:11px; text-transform:uppercase; letter-spacing:1px; opacity:.75; font-weight:700; }
.total-value { font-size:30px; font-weight:800; margin-top:3px; }
.total-note { font-size:12px; opacity:.78; margin-top:5px; }

.success-card {
    background:#ecfdf5; border:1px solid #b7efd4; border-radius:18px;
    padding:22px; margin-top:18px;
}
.success-title { color:#047857; font-size:20px; font-weight:800; }
.success-text { color:#166534; font-size:13px; line-height:1.6; margin-top:5px; }

.email-preview {
    background:#fff; border:1px solid #e5e7eb; border-radius:16px;
    padding:18px; margin-top:12px;
}

div[data-testid="stButton"] button, div[data-testid="stLinkButton"] a {
    border-radius:10px !important;
    font-weight:700 !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# ============================================================
# HELPERS
# ============================================================
def add_months(year, month, months_to_add):
    total = year * 12 + (month - 1) + months_to_add
    return total // 12, total % 12 + 1

def month_key(year, month):
    return f"{year:04d}-{month:02d}"

def month_label(year, month):
    return f"{calendar.month_name[month]} {year}"

def month_index(year, month):
    return year * 12 + month - 1

def parse_month_key(value):
    y, m = value.split("-")
    return int(y), int(m)

def current_submission_month():
    today = date.today()
    if today.day > REIMBURSEMENT_CUTOFF_DAY:
        return add_months(today.year, today.month, 1)
    return today.year, today.month

def calculate_eligible(reimbursement_type, amount):
    limit = REIMBURSEMENT_TYPES[reimbursement_type]["monthly_limit"]
    return amount if limit is None else min(amount, limit)

def get_secret(name, default=None):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default

# ============================================================
# GOOGLE SHEETS / DRIVE
# ============================================================
@st.cache_resource(show_spinner=False)
def google_clients():
    if not GOOGLE_LIBS_AVAILABLE:
        raise RuntimeError(
            "Google integration libraries are not installed. "
            "Add gspread, google-auth and google-api-python-client to requirements.txt."
        )

    raw = get_secret("google_service_account")
    if not raw:
        raise RuntimeError(
            "google_service_account is missing from Streamlit Secrets."
        )

    if isinstance(raw, dict):
        info = dict(raw)
    elif isinstance(raw, str):
        # Handle both a JSON string and a Python-dict-style string.
        try:
            info = json.loads(raw)
        except json.JSONDecodeError:
            try:
                info = ast.literal_eval(raw)
            except (ValueError, SyntaxError) as exc:
                raise RuntimeError(
                    "google_service_account secret could not be parsed. "
                    "Please check the [google_service_account] section in Streamlit Secrets."
                ) from exc
        if not isinstance(info, dict):
            raise RuntimeError(
                "google_service_account secret must contain service-account fields."
            )
    else:
        info = dict(raw)

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    creds = Credentials.from_service_account_info(
        info,
        scopes=scopes
    )

    gc = gspread.authorize(creds)

    drive = build(
        "drive",
        "v3",
        credentials=creds,
        cache_discovery=False
    )

    return gc, drive

def get_or_create_spreadsheet():
    gc, _ = google_clients()
    try:
        sh = gc.open(REIMBURSEMENT_SHEET_NAME)
    except gspread.SpreadsheetNotFound:
        sh = gc.create(REIMBURSEMENT_SHEET_NAME)

        # Share with HR so the HR account can access it.
        try:
            sh.share(HR_EMAIL, perm_type="user", role="writer", notify=False)
        except Exception:
            pass

    try:
        ws = sh.worksheet("Reimbursements")
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title="Reimbursements", rows=2000, cols=20)

    headers = [
        "Submission ID", "Submission Date", "Employee Name", "Employee Email",
        "Submission Month", "Claim Month", "Reimbursement Type",
        "Invoice No.", "Invoice Amount", "Eligible Amount",
        "Document Name", "Drive File URL", "Status"
    ]

    current = ws.row_values(1)
    if current != headers:
        ws.update("A1:M1", [headers])
        try:
            ws.freeze(rows=1)
        except Exception:
            pass

    return sh, ws

def get_employee_submissions(employee_email):
    try:
        _, ws = get_or_create_spreadsheet()
        rows = ws.get_all_records()
    except Exception:
        return []

    email = employee_email.strip().lower()
    return [r for r in rows if str(r.get("Employee Email", "")).strip().lower() == email]

def latest_claimed_month_index(employee_email):
    rows = get_employee_submissions(employee_email)
    indices = []
    for r in rows:
        val = str(r.get("Claim Month", "")).strip()
        if not val:
            continue
        try:
            y, m = parse_month_key(val)
            indices.append(month_index(y, m))
        except Exception:
            continue
    return max(indices) if indices else None

def get_eligible_month_options(employee_email):
    submission_y, submission_m = current_submission_month()
    end_idx = month_index(submission_y, submission_m)

    last_idx = latest_claimed_month_index(employee_email)
    earliest_idx = end_idx - 2

    if last_idx is not None:
        earliest_idx = max(earliest_idx, last_idx + 1)

    # If the employee has no remaining months after a very recent claim,
    # show the next 3-month window.
    if earliest_idx > end_idx:
        return []

    options = []
    for idx in range(earliest_idx, end_idx + 1):
        y = idx // 12
        m = idx % 12 + 1
        options.append((month_key(y, m), month_label(y, m)))
    return options

def get_or_create_drive_folder():
    # The reimbursement folder already exists inside the Shared Drive.
    # Return its ID directly instead of trying to create a folder in My Drive.
    return REIMBURSEMENT_DRIVE_FOLDER_ID

def upload_to_drive(uploaded_file, employee_name, claim_month, reimbursement_type, invoice_no):
    _, drive = google_clients()
    folder_id = get_or_create_drive_folder()

    safe_employee = "".join(c if c.isalnum() or c in " _-" else "_" for c in employee_name).strip()
    safe_type = "".join(c if c.isalnum() or c in " _-" else "_" for c in reimbursement_type).strip()
    original = uploaded_file.name
    suffix = Path(original).suffix.lower()
    filename = f"{safe_employee}_{claim_month}_{safe_type}_Invoice_{invoice_no}_{uuid.uuid4().hex[:8]}{suffix}"

    metadata = {
        "name": filename,
        "parents": [folder_id],
        "description": f"Reimbursement bill submitted by {employee_name} for {claim_month}.",
    }

    file_bytes = uploaded_file.getvalue()
    import io
    media = MediaIoBaseUpload(
        io.BytesIO(file_bytes),
        mimetype=uploaded_file.type or "application/octet-stream",
        resumable=False,
    )
    created = drive.files().create(
        body=metadata,
        media_body=media,
        fields="id,name,webViewLink",
        supportsAllDrives=True,
    ).execute()

    return created.get("id"), created.get("name"), created.get("webViewLink")

def save_reimbursement_to_google(submission):
    sh, ws = get_or_create_spreadsheet()

    for item in submission["items"]:
        ws.append_row(
            [
                submission["submission_id"],
                submission["submission_date"],
                submission["employee_name"],
                submission["employee_email"],
                submission["submission_month"],
                item["claim_month"],
                item["reimbursement_type"],
                item["invoice_no"],
                item["invoice_amount"],
                item["eligible_amount"],
                item["document_name"],
                item["drive_url"],
                "Submitted",
            ],
            value_input_option="USER_ENTERED",
        )
    return sh.url

# ============================================================
# EMAIL
# ============================================================
def smtp_is_configured():
    return bool(get_secret("SMTP_EMAIL")) and bool(get_secret("SMTP_PASSWORD"))

def send_reimbursement_hr_email(submission):
    if not smtp_is_configured():
        raise RuntimeError("SMTP_EMAIL / SMTP_PASSWORD is not configured.")

    smtp_email = str(get_secret("SMTP_EMAIL")).strip()
    smtp_password = str(get_secret("SMTP_PASSWORD")).strip()
    smtp_host = str(get_secret("SMTP_HOST", "smtp.gmail.com")).strip()
    smtp_port = int(get_secret("SMTP_PORT", 587))

    by_month = {}
    for item in submission["items"]:
        by_month.setdefault(item["claim_month"], []).append(item)

    month_blocks = []
    for mkey in sorted(by_month.keys()):
        items = by_month[mkey]
        my, mm = parse_month_key(mkey)
        rows = ""
        month_claimed = 0
        month_eligible = 0
        for item in items:
            month_claimed += item["invoice_amount"]
            month_eligible += item["eligible_amount"]
            rows += f"""
            <tr>
                <td style="padding:10px;border-bottom:1px solid #eee;">{escape(item["reimbursement_type"])}</td>
                <td style="padding:10px;border-bottom:1px solid #eee;">Invoice {item["invoice_no"]}</td>
                <td style="padding:10px;border-bottom:1px solid #eee;text-align:right;">₹{item["invoice_amount"]:,.2f}</td>
                <td style="padding:10px;border-bottom:1px solid #eee;text-align:right;font-weight:700;">₹{item["eligible_amount"]:,.2f}</td>
            </tr>
            """
        month_blocks.append(f"""
        <div style="margin:22px 0 10px;font-size:16px;font-weight:700;color:#17233c;">
            {escape(month_label(my, mm))}
        </div>
        <table style="width:100%;border-collapse:collapse;font-size:13px;">
            <thead>
                <tr style="background:#f7f5ff;">
                    <th style="padding:10px;text-align:left;">Type</th>
                    <th style="padding:10px;text-align:left;">Invoice</th>
                    <th style="padding:10px;text-align:right;">Claimed</th>
                    <th style="padding:10px;text-align:right;">Eligible</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
        <div style="margin-top:8px;text-align:right;font-size:13px;color:#667085;">
            Month claimed: <b>₹{month_claimed:,.2f}</b>
            &nbsp;&nbsp; | &nbsp;&nbsp;
            Month eligible: <b style="color:#5c43d4;">₹{month_eligible:,.2f}</b>
        </div>
        """)

    html = f"""
    <div style="margin:0;padding:0;background:#f5f6fa;font-family:Arial,Helvetica,sans-serif;">
      <div style="max-width:760px;margin:0 auto;padding:28px 12px;">
        <div style="background:#173f70;border-radius:16px 16px 0 0;padding:24px 28px;color:#fff;">
          <div style="font-size:12px;letter-spacing:1px;text-transform:uppercase;opacity:.8;">Germane Media LLC</div>
          <div style="font-size:25px;font-weight:700;margin-top:6px;">New Reimbursement Submission</div>
          <div style="font-size:13px;opacity:.82;margin-top:5px;">Employee reimbursement request received</div>
        </div>

        <div style="background:#fff;padding:26px 28px;border:1px solid #e6e8ee;border-top:0;border-radius:0 0 16px 16px;">
          <div style="display:flex;justify-content:space-between;gap:20px;flex-wrap:wrap;">
            <div>
              <div style="font-size:11px;color:#8a93a5;text-transform:uppercase;">Employee</div>
              <div style="font-size:16px;font-weight:700;color:#17233c;margin-top:3px;">{escape(submission["employee_name"])}</div>
              <div style="font-size:13px;color:#667085;margin-top:2px;">{escape(submission["employee_email"])}</div>
            </div>
            <div style="text-align:right;">
              <div style="font-size:11px;color:#8a93a5;text-transform:uppercase;">Submission ID</div>
              <div style="font-size:13px;font-weight:700;color:#17233c;margin-top:3px;">{escape(submission["submission_id"])}</div>
              <div style="font-size:13px;color:#667085;margin-top:2px;">{escape(submission["submission_date"])}</div>
            </div>
          </div>

          {''.join(month_blocks)}

          <div style="margin-top:26px;padding:18px;border-radius:13px;background:#f6f3ff;border:1px solid #e1d9ff;">
            <div style="font-size:11px;color:#6b5aa8;text-transform:uppercase;font-weight:700;">Total reimbursement requested</div>
            <div style="font-size:28px;font-weight:800;color:#5c43d4;margin-top:3px;">₹{submission["total_eligible"]:,.2f}</div>
            <div style="font-size:12px;color:#667085;margin-top:3px;">Total invoice value: ₹{submission["total_claimed"]:,.2f}</div>
          </div>

          <div style="margin-top:22px;font-size:12px;color:#7b8496;line-height:1.6;">
            Please verify the supporting documents and process the reimbursement as per company policy.
          </div>
        </div>
      </div>
    </div>
    """

    msg = EmailMessage()
    msg["Subject"] = f"Reimbursement Submission | {submission['employee_name']} | {submission['submission_id']}"
    msg["From"] = formataddr(("Germane Media Reimbursement Portal", smtp_email))
    msg["To"] = HR_EMAIL
    msg["Reply-To"] = submission["employee_email"]
    msg.set_content(
        f"New reimbursement submission from {submission['employee_name']}.\n"
        f"Total claimed: ₹{submission['total_claimed']:,.2f}\n"
        f"Total eligible: ₹{submission['total_eligible']:,.2f}\n"
    )
    msg.add_alternative(html, subtype="html")

    with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(smtp_email, smtp_password)
        server.send_message(msg)


# ============================================================
# JOB REFERRAL PORTAL
# ============================================================
def get_or_create_job_referral_spreadsheet():
    gc, _ = google_clients()

    try:
        sh = gc.open(JOB_REFERRAL_SHEET_NAME)
    except gspread.SpreadsheetNotFound:
        sh = gc.create(JOB_REFERRAL_SHEET_NAME)

    # Make sure HR can open and manage the sheet.
    try:
        sh.share(HR_EMAIL, perm_type="user", role="writer", notify=False)
    except Exception:
        pass

    try:
        jobs_ws = sh.worksheet("Job Openings")
    except gspread.WorksheetNotFound:
        jobs_ws = sh.add_worksheet(title="Job Openings", rows=500, cols=5)

    job_headers = ["Job Title", "JD Link"]
    if jobs_ws.row_values(1) != job_headers:
        jobs_ws.update("A1:B1", [job_headers])
        try:
            jobs_ws.freeze(rows=1)
        except Exception:
            pass

    try:
        referrals_ws = sh.worksheet("Referrals")
    except gspread.WorksheetNotFound:
        referrals_ws = sh.add_worksheet(title="Referrals", rows=5000, cols=20)

    referral_headers = [
        "Referral ID",
        "Date",
        "Job Title",
        "JD Link",
        "Referring Employee",
        "Employee Email",
        "Candidate Name",
        "Candidate Phone",
        "Candidate Email",
        "Resume Name",
        "Resume URL",
        "Status",
    ]
    if referrals_ws.row_values(1) != referral_headers:
        referrals_ws.update("A1:L1", [referral_headers])
        try:
            referrals_ws.freeze(rows=1)
        except Exception:
            pass

    return sh, jobs_ws, referrals_ws


def get_job_openings():
    try:
        _, jobs_ws, _ = get_or_create_job_referral_spreadsheet()
        rows = jobs_ws.get_all_records()
    except Exception:
        return []

    jobs = []
    for row in rows:
        title = str(row.get("Job Title", "")).strip()
        jd_link = str(row.get("JD Link", "")).strip()
        if title:
            jobs.append({
                "job_title": title,
                "jd_link": jd_link,
            })
    return jobs


def referral_already_exists(candidate_email, job_title):
    try:
        _, _, referrals_ws = get_or_create_job_referral_spreadsheet()
        rows = referrals_ws.get_all_records()
    except Exception:
        return False

    candidate_email = candidate_email.strip().lower()
    job_title = job_title.strip().lower()

    for row in rows:
        existing_email = str(row.get("Candidate Email", "")).strip().lower()
        existing_job = str(row.get("Job Title", "")).strip().lower()
        if existing_email == candidate_email and existing_job == job_title:
            return True

    return False


def upload_referral_resume(uploaded_file, candidate_name, job_title, referral_id):
    _, drive = google_clients()

    safe_candidate = "".join(
        c if c.isalnum() or c in " _-" else "_"
        for c in candidate_name
    ).strip()

    safe_job = "".join(
        c if c.isalnum() or c in " _-" else "_"
        for c in job_title
    ).strip()

    original_name = uploaded_file.name
    suffix = Path(original_name).suffix.lower()
    filename = f"{referral_id}_{safe_candidate}_{safe_job}{suffix}"

    metadata = {
        "name": filename,
        "parents": [JOB_REFERRAL_DRIVE_FOLDER_ID],
        "description": (
            f"Employee referral resume for {job_title}. "
            f"Referral ID: {referral_id}."
        ),
    }

    import io

    file_bytes = uploaded_file.getvalue()
    media = MediaIoBaseUpload(
        io.BytesIO(file_bytes),
        mimetype=uploaded_file.type or "application/octet-stream",
        resumable=False,
    )

    created = drive.files().create(
        body=metadata,
        media_body=media,
        fields="id,name,webViewLink",
        supportsAllDrives=True,
    ).execute()

    file_id = created.get("id")
    file_url = created.get("webViewLink") or f"https://drive.google.com/file/d/{file_id}/view"

    return file_id, created.get("name"), file_url


def save_job_referral(referral):
    sh, _, referrals_ws = get_or_create_job_referral_spreadsheet()

    referrals_ws.append_row(
        [
            referral["referral_id"],
            referral["date"],
            referral["job_title"],
            referral["jd_link"],
            referral["employee_name"],
            referral["employee_email"],
            referral["candidate_name"],
            referral["candidate_phone"],
            referral["candidate_email"],
            referral["resume_name"],
            referral["resume_url"],
            "Submitted",
        ],
        value_input_option="USER_ENTERED",
    )

    return sh.url


def send_job_referral_emails(referral):
    if not smtp_is_configured():
        raise RuntimeError("SMTP_EMAIL / SMTP_PASSWORD is not configured.")

    smtp_email = str(get_secret("SMTP_EMAIL")).strip()
    smtp_password = str(get_secret("SMTP_PASSWORD")).strip()
    smtp_host = str(get_secret("SMTP_HOST", "smtp.gmail.com")).strip()
    smtp_port = int(get_secret("SMTP_PORT", 587))

    # 1. Confirmation email to the employee who made the referral.
    employee_msg = EmailMessage()
    employee_msg["Subject"] = (
        f"Referral Submitted | {referral['job_title']} | {referral['referral_id']}"
    )
    employee_msg["From"] = formataddr(("Germane Media Job Referral Portal", smtp_email))
    employee_msg["To"] = referral["employee_email"]

    employee_msg.set_content(
        f"Hi {referral['employee_name']},\n\n"
        f"Your employee referral has been submitted successfully.\n\n"
        f"Referral ID: {referral['referral_id']}\n"
        f"Position: {referral['job_title']}\n"
        f"Candidate: {referral['candidate_name']}\n\n"
        f"HR has been notified and will review the referral.\n\n"
        f"Regards,\n"
        f"Germane Media LLC HR"
    )

    # 2. Notification email to the candidate.
    candidate_msg = EmailMessage()
    candidate_msg["Subject"] = (
        f"You have been referred for {referral['job_title']} | Germane Media LLC"
    )
    candidate_msg["From"] = formataddr(("Germane Media LLC", smtp_email))
    candidate_msg["To"] = referral["candidate_email"]

    candidate_msg.set_content(
        f"Hi {referral['candidate_name']},\n\n"
        f"You have been referred by {referral['employee_name']} "
        f"for the position of {referral['job_title']} at Germane Media LLC.\n\n"
        f"Our HR team will review your referral and contact you if your profile "
        f"is shortlisted for the next stage.\n\n"
        f"Regards,\n"
        f"Germane Media LLC HR"
    )

    # 3. Notification to HR, with the resume attached.
    hr_msg = EmailMessage()
    hr_msg["Subject"] = (
        f"New Employee Referral | {referral['job_title']} | {referral['referral_id']}"
    )
    hr_msg["From"] = formataddr(("Germane Media Job Referral Portal", smtp_email))
    hr_msg["To"] = HR_EMAIL
    hr_msg["Reply-To"] = referral["employee_email"]

    hr_msg.set_content(
        f"New employee referral received.\n\n"
        f"Referral ID: {referral['referral_id']}\n"
        f"Date: {referral['date']}\n\n"
        f"Position: {referral['job_title']}\n"
        f"JD: {referral['jd_link']}\n\n"
        f"Referring Employee: {referral['employee_name']}\n"
        f"Employee Email: {referral['employee_email']}\n\n"
        f"Candidate Name: {referral['candidate_name']}\n"
        f"Candidate Phone: {referral['candidate_phone']}\n"
        f"Candidate Email: {referral['candidate_email']}\n\n"
        f"Resume: {referral['resume_url']}\n"
    )

    resume_bytes = referral.get("resume_bytes")
    resume_type = referral.get("resume_type") or "application/octet-stream"
    resume_name = referral.get("resume_original_name") or referral["resume_name"]

    if resume_bytes:
        maintype, subtype = (
            resume_type.split("/", 1)
            if "/" in resume_type
            else ("application", "octet-stream")
        )
        hr_msg.add_attachment(
            resume_bytes,
            maintype=maintype,
            subtype=subtype,
            filename=resume_name,
        )

    with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(smtp_email, smtp_password)
        server.send_message(employee_msg)
        server.send_message(candidate_msg)
        server.send_message(hr_msg)


def job_referral_portal():
    st.markdown(
        """
        <div class="portal-hero">
            <div class="portal-kicker">Employee Referral Program</div>
            <div class="portal-title">Job Referral Portal</div>
            <div class="portal-subtitle">
                Refer suitable candidates for current Germane Media LLC job openings.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    try:
        jobs = get_job_openings()
    except Exception as e:
        st.error(f"Unable to load current job openings. Technical details: {e}")
        return

    if not jobs:
        st.info(
            "There are currently no active job openings available for referral. "
            "Please check again later."
        )
        if st.session_state.is_hr:
            try:
                sh, _, _ = get_or_create_job_referral_spreadsheet()
                st.link_button(
                    "Open Job Referral Google Sheet",
                    sh.url,
                    use_container_width=False,
                )
            except Exception as e:
                st.warning(f"Unable to open the Job Referral Google Sheet: {e}")
        return

    if st.session_state.is_hr:
        try:
            sh, _, _ = get_or_create_job_referral_spreadsheet()
            st.link_button(
                "Open Job Referral Google Sheet",
                sh.url,
                use_container_width=False,
            )
        except Exception:
            pass

    selected_job = st.session_state.get("selected_referral_job")

    if selected_job:
        st.markdown(
            '<div class="section-head"><div class="section-title">Refer a Candidate</div>'
            '<div class="section-caption">Complete the candidate details below.</div></div>',
            unsafe_allow_html=True,
        )

        st.info(f"Position: {selected_job['job_title']}")

        if st.button("← Back to Job Openings", key="back_to_referral_jobs"):
            st.session_state.selected_referral_job = None
            st.rerun()

        with st.form("job_referral_form", clear_on_submit=False):
            candidate_name = st.text_input("Candidate Name *")
            candidate_phone = st.text_input("Candidate Phone *")
            candidate_email = st.text_input("Candidate Email *")
            resume = st.file_uploader(
                "Upload Resume *",
                accept_multiple_files=False,
                help="PDF, DOC, DOCX or another resume file format is accepted.",
            )

            consent = st.checkbox(
                "I confirm that I have the candidate's permission to share their "
                "contact details and resume with Germane Media LLC for this job opportunity."
            )

            submit_referral = st.form_submit_button(
                "Submit Referral",
                type="primary",
                use_container_width=True,
            )

        if submit_referral:
            errors = []

            candidate_name = candidate_name.strip()
            candidate_phone = candidate_phone.strip()
            candidate_email = candidate_email.strip().lower()

            if not candidate_name:
                errors.append("Please enter the candidate's name.")

            if not candidate_phone:
                errors.append("Please enter the candidate's phone number.")

            if not candidate_email or "@" not in candidate_email:
                errors.append("Please enter a valid candidate email address.")

            if resume is None:
                errors.append("Please upload the candidate's resume.")

            if not consent:
                errors.append(
                    "Please confirm that you have the candidate's permission to share their information."
                )

            if not errors and referral_already_exists(
                candidate_email,
                selected_job["job_title"],
            ):
                errors.append(
                    "This candidate has already been referred for this position."
                )

            if errors:
                for error in errors:
                    st.error(error)
                return

            referral_id = (
                f"REF-{datetime.now().strftime('%Y%m%d')}-"
                f"{uuid.uuid4().hex[:6].upper()}"
            )
            referral_date = datetime.now().strftime("%d %b %Y, %I:%M %p")

            referral = {
                "referral_id": referral_id,
                "date": referral_date,
                "job_title": selected_job["job_title"],
                "jd_link": selected_job["jd_link"],
                "employee_name": st.session_state.emp_name,
                "employee_email": st.session_state.emp_email,
                "candidate_name": candidate_name,
                "candidate_phone": candidate_phone,
                "candidate_email": candidate_email,
                "resume_original_name": resume.name,
                "resume_type": resume.type,
                "resume_bytes": resume.getvalue(),
            }

            with st.spinner("Submitting referral..."):
                try:
                    _, resume_name, resume_url = upload_referral_resume(
                        resume,
                        candidate_name,
                        selected_job["job_title"],
                        referral_id,
                    )

                    referral["resume_name"] = resume_name
                    referral["resume_url"] = resume_url

                    sheet_url = save_job_referral(referral)
                    send_job_referral_emails(referral)

                    st.session_state.referral_success = {
                        "referral_id": referral_id,
                        "job_title": selected_job["job_title"],
                        "candidate_name": candidate_name,
                        "sheet_url": sheet_url,
                    }
                    st.session_state.selected_referral_job = None
                    st.rerun()

                except Exception as e:
                    st.error(
                        "The referral could not be submitted. "
                        "Please check the Google Drive, Google Sheet and email configuration. "
                        f"Technical details: {e}"
                    )
                    return

    else:
        st.markdown(
            '<div class="section-head"><div class="section-title">Current Job Openings</div>'
            '<div class="section-caption">Select a position and refer a suitable candidate.</div></div>',
            unsafe_allow_html=True,
        )

        for index, job in enumerate(jobs):
            c1, c2, c3 = st.columns([3.8, 2.2, 1.2])

            with c1:
                st.markdown(f"**{escape(job['job_title'])}**")

            with c2:
                if job["jd_link"]:
                    # Open the JD as a true external link. If the sheet contains
                    # a URL without a protocol, add https:// automatically.
                    jd_url = str(job["jd_link"]).strip()
                    if not jd_url.lower().startswith(("http://", "https://")):
                        jd_url = "https://" + jd_url.lstrip("/")

                    st.markdown(
                        f'''<a href="{escape(jd_url)}" target="_blank" rel="noopener noreferrer" style="display:block; text-align:center; padding:0.55rem 0.75rem; border:1px solid rgba(250,250,250,0.2); border-radius:0.5rem; background:#11141b; color:white; text-decoration:none; font-weight:500;">View Job Opening / JD</a>''',
                        unsafe_allow_html=True,
                    )
                else:
                    st.caption("JD link not available")

            with c3:
                if st.button(
                    "Refer",
                    key=f"refer_job_{index}",
                    use_container_width=True,
                ):
                    st.session_state.selected_referral_job = job
                    st.rerun()

            st.divider()

    if st.session_state.get("referral_success"):
        success = st.session_state.referral_success
        st.success(
            f"Referral submitted successfully. Referral ID: {success['referral_id']}"
        )
        st.write(
            f"Candidate **{success['candidate_name']}** has been referred for "
            f"**{success['job_title']}**."
        )
        st.caption(
            "A confirmation email has been sent to you, the candidate has been "
            "notified, and HR has received the referral with the resume."
        )
        if st.session_state.is_hr:
            st.link_button("Open Job Referral Google Sheet", success["sheet_url"])

        if st.button("Submit Another Referral", key="another_referral"):
            st.session_state.referral_success = None
            st.rerun()


# ============================================================
# POLICY ASSISTANT
# ============================================================
@st.cache_resource
def load_and_index_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    return [{"page": i + 1, "text": p.extract_text() or ""} for i, p in enumerate(reader.pages)]

def query_policy_ai(prompt, conversation_history):
    history_context = ""
    for msg in conversation_history[-8:]:
        role = "Employee" if msg["role"] == "user" else "Assistant"
        history_context += f"{role}: {msg['content']}\n"

    pdf_pages = load_and_index_pdf(POLICY_PDF)
    full_context = "\n\n".join(
        f"--- PAGE {p['page']} ---\n{p['text']}" for p in pdf_pages
    )

    system_prompt = f"""
You are the official GM Policy Assistant for Germane Media LLC.

Your ONLY source of policy information is the Germane Media LLC Employee Policy Handbook below.
Do not use general HR knowledge, internet information, assumptions, or outside sources.

1. Answer strictly from the handbook.
2. Do not invent policy.
3. If the question cannot be answered from the handbook, respond exactly:
"I couldn't find a specific provision covering this in the Germane Media LLC Employee Policy Handbook. I recommend contacting HR directly for clarification."
4. ALWAYS provide page citations.
5. If multiple pages support the answer, cite all relevant pages.
6. Keep answers professional, concise and easy to understand.
7. Reproduce policy numbers, dates and amounts accurately.

POLICY HANDBOOK
{full_context}

CONVERSATION HISTORY
{history_context}

EMPLOYEE QUESTION
{prompt}

ANSWER
"""
    try:
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=system_prompt
        )
        if response and response.text:
            return response.text.strip()
        raise RuntimeError("Gemini returned an empty response.")
    except Exception as e:
        raise RuntimeError(f"AI Assistant is currently unavailable. Please contact HR. Technical details: {e}")

# ============================================================
# REIMBURSEMENT UI
# ============================================================
def reimbursement_portal():
    st.markdown(
        """
        <div class="portal-hero">
            <div class="portal-kicker">Employee Benefits</div>
            <div class="portal-title">Reimbursement Portal</div>
            <div class="portal-subtitle">
                Submit eligible claims, upload supporting bills and review your reimbursement before sending it to HR.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="info-card"><div class="info-label">Employee</div><div class="info-value">{escape(st.session_state.emp_name)}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="info-card"><div class="info-label">Company Email</div><div class="info-value">{escape(st.session_state.emp_email)}</div></div>', unsafe_allow_html=True)
    with c3:
        today = date.today()
        deadline = "Next month" if today.day > REIMBURSEMENT_CUTOFF_DAY else f"{calendar.month_name[today.month]} {REIMBURSEMENT_CUTOFF_DAY}"
        st.markdown(f'<div class="info-card"><div class="info-label">Submission Deadline</div><div class="info-value">Before the 22nd • {deadline}</div></div>', unsafe_allow_html=True)

    if today.day > REIMBURSEMENT_CUTOFF_DAY:
        ny, nm = add_months(today.year, today.month, 1)
        st.warning(
            f"The {calendar.month_name[today.month]} {today.year} submission window has closed. "
            f"Please submit in {calendar.month_name[nm]} {ny}, before the 22nd."
        )
    else:
        st.success(f"Reimbursement submissions are open until {calendar.month_name[today.month]} {REIMBURSEMENT_CUTOFF_DAY}.")

    st.markdown(
        """
        <div class="rule-strip">
            <strong>How the cycle works:</strong>
            <span>
            You may claim a maximum of 3 months in one submission.
            After a submission, the next reimbursement window opens after 3 months.
            If you miss a month, the oldest month eventually falls outside the 3-month window.
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("View reimbursement rules", expanded=False):
        st.markdown("""
        **Eligibility**
        - Full-Time Employees and Interns are eligible.
        - Consultants require specific management approval.

        **Submission**
        - Claims can cover a maximum of 3 months.
        - Claims must be submitted before the 22nd.
        - Supporting documents are mandatory.
        - Employees are responsible for timely submission.

        **Monthly limits**
        - Wi-Fi / Internet: ₹1,000 per month.
        - Gym / Health: ₹1,000 per month.
        - Course: ₹1,000 per month.
        - Other Reimbursement: no ₹1,000 cap.

        **Current portal invoice limits**
        - Wi-Fi / Internet: 1 invoice per month.
        - Gym / Health: 1 invoice per month.
        - Course: 1 invoice per month.
        - Other Reimbursement: multiple invoices.
        """)

    options = get_eligible_month_options(st.session_state.emp_email)
    if not options:
        st.info("No reimbursement months are currently available. Please check your previous reimbursement submission cycle.")
        return

    option_labels = [label for _, label in options]
    label_to_key = {label: key for key, label in options}

    st.markdown('<div class="section-head"><div class="section-title">1. Select reimbursement months</div><div class="section-caption">Select up to 3 eligible months.</div></div>', unsafe_allow_html=True)

    selected_labels = st.multiselect(
        "Months",
        options=option_labels,
        max_selections=3,
        key="reimbursement_selected_months",
        label_visibility="collapsed",
    )

    if not selected_labels:
        st.info("Select at least one month to continue.")
        return

    selected_keys = [label_to_key[x] for x in selected_labels]

    # Keep order chronological
    selected_keys = sorted(selected_keys)

    # Initialize claim type selection state per month
    for mkey in selected_keys:
        if f"types_{mkey}" not in st.session_state:
            st.session_state[f"types_{mkey}"] = []

    all_items = []

    st.markdown('<div class="section-head"><div class="section-title">2. Add reimbursement details</div><div class="section-caption">You can claim multiple reimbursement types for the same month.</div></div>', unsafe_allow_html=True)

    for mkey in selected_keys:
        y, m = parse_month_key(mkey)
        label = month_label(y, m)

        st.markdown(
            f"""
            <div class="month-card">
                <div class="month-heading">{escape(label)}</div>
                <div class="month-caption">Choose one or more reimbursement types for this month.</div>
            """,
            unsafe_allow_html=True,
        )

        selected_types = st.multiselect(
            "Reimbursement types",
            options=list(REIMBURSEMENT_TYPES.keys()),
            key=f"types_{mkey}",
            label_visibility="collapsed",
        )

        if not selected_types:
            st.caption("No reimbursement type selected for this month.")
        else:
            for rtype in selected_types:
                config = REIMBURSEMENT_TYPES[rtype]
                type_key = rtype.lower().replace(" ", "_").replace("/", "_")

                st.markdown(
                    f"""
                    <div class="type-card">
                        <div class="type-title">{escape(rtype)}</div>
                        <div class="type-subtitle">
                            {'₹1,000 monthly cap • 1 invoice' if config['monthly_limit'] else 'No monthly cap • multiple invoices allowed'}
                        </div>
                    """,
                    unsafe_allow_html=True,
                )

                if config["max_invoices"] == 1:
                    amount = st.number_input(
                        "Amount (₹)",
                        min_value=0.0,
                        step=100.0,
                        value=0.0,
                        key=f"amount_{mkey}_{type_key}",
                    )
                    uploaded = st.file_uploader(
                        "Invoice / supporting document",
                        type=["pdf", "jpg", "jpeg", "png"],
                        accept_multiple_files=False,
                        key=f"file_{mkey}_{type_key}",
                    )

                    eligible = calculate_eligible(rtype, amount)

                    if amount > 0 and eligible < amount:
                        st.caption("Eligible amount is capped at ₹1,000 for this reimbursement type and month.")

                    st.markdown(
                        f"""
                        <div class="eligible-box">
                            <div class="eligible-label">Amount eligible for reimbursement</div>
                            <div class="eligible-value">₹{eligible:,.2f}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    all_items.append({
                        "claim_month": mkey,
                        "reimbursement_type": rtype,
                        "invoice_no": 1,
                        "invoice_amount": float(amount),
                        "eligible_amount": float(eligible),
                        "file": uploaded,
                    })

                else:
                    uploaded_files = st.file_uploader(
                        "Invoices / supporting documents",
                        type=["pdf", "jpg", "jpeg", "png"],
                        accept_multiple_files=True,
                        key=f"files_{mkey}_{type_key}",
                        help="Upload as many supporting documents as required.",
                    )

                    other_total = 0.0
                    other_entries = []

                    for idx, uploaded in enumerate(uploaded_files, start=1):
                        amount = st.number_input(
                            f"Amount - Invoice {idx} (₹)",
                            min_value=0.0,
                            step=100.0,
                            value=0.0,
                            key=f"other_amount_{mkey}_{idx}",
                        )
                        other_total += amount
                        other_entries.append({
                            "claim_month": mkey,
                            "reimbursement_type": rtype,
                            "invoice_no": idx,
                            "invoice_amount": float(amount),
                            "eligible_amount": float(amount),
                            "file": uploaded,
                        })

                    st.markdown(
                        f"""
                        <div class="eligible-box">
                            <div class="eligible-label">Amount eligible for reimbursement</div>
                            <div class="eligible-value">₹{other_total:,.2f}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    all_items.extend(other_entries)

                st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # REVIEW
    # --------------------------------------------------------
    valid_items = [x for x in all_items if x["invoice_amount"] > 0 or x["file"] is not None]
    total_claimed = sum(x["invoice_amount"] for x in all_items)
    total_eligible = sum(x["eligible_amount"] for x in all_items)

    st.markdown('<div class="section-head"><div class="section-title">3. Review your submission</div><div class="section-caption">The final summary will be sent to HR after submission.</div></div>', unsafe_allow_html=True)

    if all_items:
        review_html = '<div class="review-card">'
        for item in all_items:
            y, m = parse_month_key(item["claim_month"])
            review_html += f"""
            <div class="review-row">
                <div style="display:flex;justify-content:space-between;gap:20px;">
                    <div>
                        <div class="review-month">{escape(month_label(y,m))}</div>
                        <div class="review-type">{escape(item["reimbursement_type"])} • Invoice {item["invoice_no"]}</div>
                    </div>
                    <div class="review-amount">
                        ₹{item["invoice_amount"]:,.2f}
                        <div style="font-size:11px;color:#5c43d4;">Eligible ₹{item["eligible_amount"]:,.2f}</div>
                    </div>
                </div>
            </div>
            """
        review_html += "</div>"
        st.html(review_html)

    st.markdown(
        f"""
        <div class="total-card">
            <div class="total-label">Total invoice value</div>
            <div class="total-value">₹{total_claimed:,.2f}</div>
            <div class="total-label" style="margin-top:15px;">Total reimbursement requested</div>
            <div class="total-value">₹{total_eligible:,.2f}</div>
            <div class="total-note">Subject to HR verification and approval.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    declaration = st.checkbox(
        "I confirm that the information submitted is correct and the uploaded documents are genuine supporting documents.",
        key="reimbursement_declaration",
    )

    submit = st.button(
        "Submit Reimbursement",
        type="primary",
        use_container_width=True,
        key="submit_reimbursement",
    )

    if submit:
        errors = []

        today = date.today()
        if today.day > REIMBURSEMENT_CUTOFF_DAY:
            ny, nm = add_months(today.year, today.month, 1)
            errors.append(
                f"The current submission window has closed. Please submit in {calendar.month_name[nm]} {ny}, before the 22nd."
            )

        if not declaration:
            errors.append("Please confirm the declaration before submitting.")

        if not selected_keys:
            errors.append("Please select at least one reimbursement month.")

        if len(selected_keys) > 3:
            errors.append("You can claim a maximum of 3 months.")

        # Must select at least one type and complete every selected type.
        for mkey in selected_keys:
            types = st.session_state.get(f"types_{mkey}", [])
            if not types:
                y, m = parse_month_key(mkey)
                errors.append(f"Please select at least one reimbursement type for {month_label(y,m)}.")

        for item in all_items:
            y, m = parse_month_key(item["claim_month"])
            label = month_label(y, m)
            if item["invoice_amount"] <= 0:
                errors.append(f"Please enter a valid amount for {label} → {item['reimbursement_type']} → Invoice {item['invoice_no']}.")
            if item["file"] is None:
                errors.append(f"Please upload the supporting document for {label} → {item['reimbursement_type']} → Invoice {item['invoice_no']}.")

        if errors:
            for err in errors:
                st.error(err)
            return

        # Prevent duplicate month claims against Google Sheet.
        existing = get_employee_submissions(st.session_state.emp_email)
        existing_months = set(str(r.get("Claim Month", "")).strip() for r in existing)
        duplicate_months = [m for m in selected_keys if m in existing_months]
        if duplicate_months:
            errors.append(
                "The following month(s) have already been submitted: "
                + ", ".join(month_label(*parse_month_key(x)) for x in duplicate_months)
            )
            for err in errors:
                st.error(err)
            return

        submission_id = f"RMB-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        submission_date = datetime.now().strftime("%d %b %Y, %I:%M %p")
        sy, sm = current_submission_month()
        submission_month = month_key(sy, sm)

        prepared_items = []
        with st.spinner("Uploading bills and saving your reimbursement..."):
            try:
                for item in all_items:
                    file_id, file_name, drive_url = upload_to_drive(
                        item["file"],
                        st.session_state.emp_name,
                        item["claim_month"],
                        item["reimbursement_type"],
                        item["invoice_no"],
                    )
                    prepared = dict(item)
                    prepared["document_name"] = file_name
                    prepared["drive_url"] = drive_url or f"https://drive.google.com/file/d/{file_id}/view"
                    prepared_items.append(prepared)

                submission = {
                    "submission_id": submission_id,
                    "submission_date": submission_date,
                    "employee_name": st.session_state.emp_name,
                    "employee_email": st.session_state.emp_email,
                    "submission_month": submission_month,
                    "items": prepared_items,
                    "total_claimed": total_claimed,
                    "total_eligible": total_eligible,
                }

                sheet_url = save_reimbursement_to_google(submission)
                send_reimbursement_hr_email(submission)

                st.session_state.reimbursement_success = submission
                st.session_state.reimbursement_sheet_url = sheet_url
                st.rerun()

            except Exception as e:
                st.error(
                    "The reimbursement could not be submitted. "
                    "Please check the Google Drive/Sheet and email configuration. "
                    f"Technical details: {e}"
                )
                return

    if st.session_state.get("reimbursement_success"):
        submission = st.session_state.reimbursement_success
        st.markdown(
            f"""
            <div class="success-card">
                <div class="success-title">Reimbursement submitted successfully</div>
                <div class="success-text">
                    Your reimbursement request <b>{escape(submission["submission_id"])}</b> has been recorded.
                    HR has been notified by email and the supporting documents have been stored in Google Drive.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("### Submission summary")
        for mkey in sorted(set(x["claim_month"] for x in submission["items"])):
            y, m = parse_month_key(mkey)
            month_items = [x for x in submission["items"] if x["claim_month"] == mkey]
            month_claimed = sum(x["invoice_amount"] for x in month_items)
            month_eligible = sum(x["eligible_amount"] for x in month_items)
            st.write(f"**{month_label(y,m)}** — Claimed ₹{month_claimed:,.2f} • Eligible ₹{month_eligible:,.2f}")
        st.success(f"Total reimbursement requested: ₹{submission['total_eligible']:,.2f}")

# ============================================================
# LOGIN
# ============================================================
if not st.user.is_logged_in:
    logo_path = Path(__file__).parent / "logo.png"
    if logo_path.exists():
        logo_b64 = base64.b64encode(logo_path.read_bytes()).decode("utf-8")
        logo_html = f'<img class="brand-logo" src="data:image/png;base64,{logo_b64}" alt="Germane Media LLC logo">'
    else:
        logo_html = '<div class="brand-logo-fallback">G</div>'

    st.markdown('<div class="gm-login-marker"></div>', unsafe_allow_html=True)

    # IMPORTANT: keep the HTML unindented. Streamlit otherwise interprets
    # indented multi-line HTML as a Markdown code block.
    login_html = (
        '<div class="gm-login-shell">'
        '<div class="gm-login-left">'
        '<div class="gm-login-brand">' + logo_html + '<div>'
        '<div class="gm-login-brand-title">Germane Media LLC</div>'
        '<div class="gm-login-brand-sub">GM Policy Assistant • Internal HR Portal</div>'
        '<div class="gm-login-brand-line"></div>'
        '</div></div>'
        '<h1 class="gm-login-heading">Your Intelligent HR Policy Companion</h1>'
        '<p class="gm-login-description">Get instant, accurate answers to your policy questions, understand company guidelines, and connect with HR for personalized support — anytime, anywhere.</p>'
        '<div class="gm-login-features">'
        '<div class="gm-login-feature"><div class="gm-login-feature-icon">□</div><div><div class="gm-login-feature-title">Instant Policy Answers</div><div class="gm-login-feature-text">Accurate responses based on Germane Media LLC Employee Policy Handbook.</div></div></div>'
        '<div class="gm-login-feature"><div class="gm-login-feature-icon">♟</div><div><div class="gm-login-feature-title">Secure &amp; Confidential</div><div class="gm-login-feature-text">Your conversations are private, secure, and associated with your company account.</div></div></div>'
        '<div class="gm-login-feature"><div class="gm-login-feature-icon">♧</div><div><div class="gm-login-feature-title">Direct HR Support</div><div class="gm-login-feature-text">Escalate questions to HR or schedule a confidential 15-minute discussion.</div></div></div>'
        '<div class="gm-login-feature"><div class="gm-login-feature-icon">♟</div><div><div class="gm-login-feature-title">For Employees Only</div><div class="gm-login-feature-text">This portal is restricted to active Germane Media LLC employees.</div></div></div>'
        '</div></div>'
        '<div class="gm-login-right">'
        '<div class="gm-login-card">'
        '<div class="gm-login-lock">🔒</div>'
        '<div class="gm-login-card-title">Welcome Back!</div>'
        '<div class="gm-login-card-sub">Sign in to access the GM Policy Assistant</div>'
        '<div class="gm-login-divider"></div>'
        '<div class="gm-login-company-line">🔒 &nbsp; <span>Sign in with your company account</span></div>'
        '</div>'
        '<div class="gm-login-button-wrap"></div>'
        '</div></div>'
    )
    st.markdown(login_html, unsafe_allow_html=True)

    if st.button("G  Sign in with Google", type="primary", use_container_width=True, key="login_button"):
        st.login()

    st.stop()

# ============================================================
# AUTHENTICATED USER
# ============================================================
try:
    user_email = st.user.email.lower().strip()
except Exception:
    st.error("Unable to identify your Google account.")
    st.stop()

user_name = getattr(st.user, "name", None) or user_email.split("@")[0]

if not user_email.endswith(f"@{COMPANY_DOMAIN}"):
    st.error("Access denied. This application is restricted to Germane Media LLC employees.")
    if st.button("Sign Out"):
        st.logout()
    st.stop()

st.session_state.emp_name = user_name
st.session_state.emp_email = user_email
st.session_state.is_hr = user_email == HR_EMAIL.lower()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "unsatisfied_msg_idx" not in st.session_state:
    st.session_state.unsatisfied_msg_idx = None
if "hr_email_sent" not in st.session_state:
    st.session_state.hr_email_sent = False
if "current_page" not in st.session_state:
    st.session_state.current_page = "Policy Assistant"

# ============================================================
# GEMINI INITIALIZATION
# ============================================================
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Gemini API key is not configured.")
    st.stop()

try:
    gemini_client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error(f"Unable to initialize Gemini: {e}")
    st.stop()

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown(f"**👤 {st.session_state.emp_name}**")
    st.caption(st.session_state.emp_email)
    if st.session_state.is_hr:
        st.success("🔑 HR Admin Mode Active")

    st.divider()
    st.markdown("### 🧭 Portal")

    if st.button("🤖 Policy Assistant", use_container_width=True):
        st.session_state.current_page = "Policy Assistant"
        st.rerun()

    if st.button("💰 Reimbursement Portal", use_container_width=True):
        st.session_state.current_page = "Reimbursement"
        st.rerun()

    if st.button("👥 Job Referral Portal", use_container_width=True):
        st.session_state.current_page = "Job Referral"
        st.rerun()

    st.divider()
    st.markdown("📚 **Company Policy Categories**")

    categories = [
        "Leave Policy",
        "Attendance & Work Hours",
        "Appraisal & Revisions",
        "Reimbursement",
        "Probation & Confirmation",
        "Full & Final Settlement",
    ]
    for cat in categories:
        if st.button(f"📄 {cat}", key=f"category_{cat}", use_container_width=True):
            st.session_state.current_page = "Policy Assistant"
            st.session_state.messages.append({"role":"user","content":f"Summarize the key points of the {cat}."})
            st.rerun()

    st.divider()
    st.link_button("💬 Message HR on Google Chat", DIRECT_GOOGLE_CHAT_HR, use_container_width=True)
    st.divider()

    if st.button("🚪 Sign Out", use_container_width=True):
        st.session_state.clear()
        st.logout()

# ============================================================
# REIMBURSEMENT PAGE
# ============================================================
if st.session_state.current_page == "Reimbursement":
    reimbursement_portal()
    st.stop()

# ============================================================
# JOB REFERRAL PAGE
# ============================================================
if st.session_state.current_page == "Job Referral":
    job_referral_portal()
    st.stop()

# ============================================================
# POLICY PAGE
# ============================================================
if not Path(POLICY_PDF).exists():
    st.error(f"Policy PDF not found: {POLICY_PDF}")
    st.info("Upload GERMANE_MEDIA_LLC_POLICY_DOCUMENT.pdf in the same directory as app.py.")
    st.stop()

col_main, col_right = st.columns([3, 1.2])

with col_main:
    st.markdown('<div class="brand-title">GM Policy Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-sub">Ask questions, verify rules, and connect with HR.</div>', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="info-card">
            <b>🔒 Private HR Conversation</b><br>
            <span style="font-size:12px;color:#667085;">
            Your chat session is associated with your authenticated employee account.
            HR may access transcripts for support and policy administration.
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            if message["role"] == "assistant":
                c1, c2, _ = st.columns([1,1,4])
                with c1:
                    if st.button("✅ Satisfied", key=f"sat_{idx}"):
                        st.toast("Thank you for your feedback!")
                with c2:
                    if st.button("❌ Not Satisfied", key=f"notsat_{idx}"):
                        st.session_state.unsatisfied_msg_idx = idx
                        st.session_state.hr_email_sent = False
                        st.rerun()

                if st.session_state.unsatisfied_msg_idx == idx:
                    st.warning("We're sorry we couldn't fully resolve your question. You can contact HR or schedule a confidential 15-minute discussion.")
                    e1, e2 = st.columns(2)
                    with e1:
                        if st.button("📧 Send to HR", key=f"sendhr_{idx}", use_container_width=True):
                            try:
                                # Reuse the original transcript email function from this portal.
                                if not smtp_is_configured():
                                    raise RuntimeError("SMTP is not configured.")
                                smtp_email = str(get_secret("SMTP_EMAIL")).strip()
                                smtp_password = str(get_secret("SMTP_PASSWORD")).strip()
                                msg = EmailMessage()
                                msg["Subject"] = f"HR Assistance Required - {st.session_state.emp_name}"
                                msg["From"] = smtp_email
                                msg["To"] = HR_EMAIL
                                msg["Reply-To"] = st.session_state.emp_email
                                transcript = "\n\n".join(
                                    ("EMPLOYEE" if m["role"]=="user" else "GM POLICY ASSISTANT") + ":\n" + m["content"]
                                    for m in st.session_state.messages
                                )
                                msg.set_content(
                                    f"Employee: {st.session_state.emp_name}\n"
                                    f"Email: {st.session_state.emp_email}\n\n"
                                    f"Conversation:\n{transcript}"
                                )
                                with smtplib.SMTP(str(get_secret("SMTP_HOST","smtp.gmail.com")), int(get_secret("SMTP_PORT",587)), timeout=30) as server:
                                    server.starttls()
                                    server.login(smtp_email, smtp_password)
                                    server.send_message(msg)
                                st.session_state.hr_email_sent = True
                                st.success("Your conversation has been sent to HR.")
                            except Exception as e:
                                st.error(f"Unable to notify HR: {e}")
                    with e2:
                        st.link_button("📅 Schedule HR Call", HR_BOOKING_URL, use_container_width=True)

    user_query = st.chat_input("Ask a policy question...")
    if user_query:
        st.session_state.messages.append({"role":"user","content":user_query})
        st.session_state.unsatisfied_msg_idx = None
        try:
            with st.spinner("Searching Germane Media Policy Handbook..."):
                response = query_policy_ai(user_query, st.session_state.messages)
            st.session_state.messages.append({
                "role":"assistant",
                "content":response + "\n\n---\n*Notice: Answers are derived from the Germane Media LLC Policy Handbook. Employment Agreement terms prevail where applicable.*"
            })
            st.rerun()
        except Exception as e:
            st.error(str(e))

with col_right:
    st.markdown("### 📅 Schedule HR Discussion")
    st.caption("Need to speak directly with HR? Book a 15-minute confidential discussion.")
    st.link_button("📅 Schedule 15-Minute HR Discussion", HR_BOOKING_URL, type="primary", use_container_width=True)
    st.divider()
    st.markdown("💬 **Need immediate help?**")
    st.link_button("💬 Contact HR on Google Chat", DIRECT_GOOGLE_CHAT_HR, use_container_width=True)
    st.divider()
    st.markdown("💡 **Suggested Questions**")
    for q in [
        "How many leaves do I get per month?",
        "When am I eligible for appraisal consideration?",
        "What is the reimbursement process?",
        "What is the timeline for FNF settlement?",
    ]:
        if st.button(f"❓ {q}", key=f"suggested_{q}", use_container_width=True):
            st.session_state.messages.append({"role":"user","content":q})
            st.rerun()
