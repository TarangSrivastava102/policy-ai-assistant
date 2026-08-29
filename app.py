
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
.stApp { background: #f7f8fc; }
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

def reimbursement_today():
    """
    Date used by the reimbursement portal.
    Normally this is today's date.

    Optional testing secret:
        REIMBURSEMENT_TEST_DATE = "2026-09-15"

    Remove the secret after testing.
    """
    test_date = get_secret("REIMBURSEMENT_TEST_DATE")
    if test_date:
        try:
            return datetime.strptime(str(test_date).strip(), "%Y-%m-%d").date()
        except Exception:
            pass
    return date.today()

def current_submission_month():
    today = reimbursement_today()
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

    # Your Streamlit Secrets store the service account as a TOML section:
    # [google_service_account]
    # Therefore we read that section directly instead of looking for
    # a single GOOGLE_SERVICE_ACCOUNT_JSON secret.
    if "google_service_account" not in st.secrets:
        raise RuntimeError(
            "google_service_account is missing from Streamlit Secrets."
        )

    try:
        info = dict(st.secrets["google_service_account"])
    except Exception as e:
        raise RuntimeError(
            f"Unable to read google_service_account from Streamlit Secrets: {e}"
        )

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    gc = gspread.authorize(creds)
    drive = build("drive", "v3", credentials=creds, cache_discovery=False)
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
    _, drive = google_clients()
    q = (
        "mimeType='application/vnd.google-apps.folder' "
        "and name='Germane Media - Reimbursement Bills' "
        "and trashed=false"
    )
    result = drive.files().list(
        q=q,
        spaces="drive",
        fields="files(id,name,webViewLink)",
        pageSize=10
    ).execute()
    files = result.get("files", [])
    if files:
        return files[0]["id"]

    metadata = {
        "name": REIMBURSEMENT_DRIVE_FOLDER_NAME,
        "mimeType": "application/vnd.google-apps.folder",
    }
    folder = drive.files().create(
        body=metadata,
        fields="id,webViewLink"
    ).execute()
    return folder["id"]

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
        today = reimbursement_today()
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
        # Native Streamlit components are used for the review so raw HTML
        # can never appear as text in the employee-facing portal.
        grouped_review = {}
        for item in all_items:
            grouped_review.setdefault(item["claim_month"], []).append(item)

        for claim_month in sorted(grouped_review.keys()):
            y, m = parse_month_key(claim_month)
            st.markdown(f"### {month_label(y, m)}")

            for item in grouped_review[claim_month]:
                with st.container(border=True):
                    left, right = st.columns([3, 1])

                    with left:
                        st.markdown(
                            f"**{item['reimbursement_type']}**  \n"
                            f"Invoice {item['invoice_no']}"
                        )

                    with right:
                        st.markdown(
                            f"**₹{item['invoice_amount']:,.2f}**  \n"
                            f"<span style='font-size:12px;color:#5c43d4;'>"
                            f"Eligible ₹{item['eligible_amount']:,.2f}"
                            f"</span>",
                            unsafe_allow_html=True,
                        )

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

        today = reimbursement_today()
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
        logo_html = '<div style="width:90px;height:90px;border-radius:20px;background:#6547ed;color:#fff;display:flex;align-items:center;justify-content:center;font-size:50px;font-weight:800;">G</div>'

    st.markdown(
        f"""
        <div style="max-width:1050px;margin:80px auto;display:grid;grid-template-columns:1.1fr .9fr;gap:45px;align-items:center;">
            <div>
                <div style="display:flex;align-items:center;gap:18px;">
                    {logo_html}
                    <div>
                        <div style="font-size:30px;font-weight:800;color:#17233c;">Germane Media LLC</div>
                        <div style="color:#6547ed;font-weight:700;margin-top:5px;">Internal HR Portal</div>
                    </div>
                </div>
                <h1 style="font-size:32px;color:#17233c;margin-top:48px;">Your Intelligent HR Policy Companion</h1>
                <p style="font-size:16px;line-height:1.7;color:#667085;max-width:600px;">
                    Get accurate policy answers, submit employee reimbursements and connect directly with HR.
                </p>
            </div>
            <div style="background:#fff;border:1px solid #e3e6ee;border-radius:22px;padding:38px;box-shadow:0 14px 40px rgba(32,35,58,.08);">
                <div style="text-align:center;font-size:46px;">🔒</div>
                <div style="text-align:center;font-size:30px;font-weight:800;color:#17233c;margin-top:12px;">Welcome Back!</div>
                <div style="text-align:center;color:#747d8e;margin:8px 0 25px;">Sign in with your company Google Workspace account.</div>
            """,
        unsafe_allow_html=True,
    )
    if st.button("G   Sign in with Google", type="primary", use_container_width=True, key="login_button"):
        st.login()
    st.markdown(
        f"""
                <div style="margin-top:20px;padding:15px;border-radius:11px;background:#faf9ff;border:1px solid #e3ddff;color:#5a43c9;font-size:13px;">
                    This portal is restricted to active <b>@{COMPANY_DOMAIN}</b> employees.
                </div>
                </div>
        """,
        unsafe_allow_html=True,
    )
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
