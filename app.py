import streamlit as st
from google import genai
from pypdf import PdfReader
import smtplib
from email.message import EmailMessage
from html import escape
from pathlib import Path
import base64
import textwrap


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="GM Policy Assistant - Germane Media LLC",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CONFIGURATION
# ============================================================

HR_EMAIL = "tarang@thegermanemedia.com"
COMPANY_DOMAIN = "thegermanemedia.com"

# Google Calendar Appointment Schedule
HR_BOOKING_URL = (
    "https://calendar.app.google/wjkBcfyeAgKqCRUVA"
)

# Direct Google Chat with HR
DIRECT_GOOGLE_CHAT_HR = (
    "https://chat.google.com/dm/tarang@thegermanemedia.com"
)

# Policy PDF
POLICY_PDF = "GERMANE_MEDIA_LLC_POLICY_DOCUMENT.pdf"

# Gemini model
GEMINI_MODEL = "gemini-3.6-flash"


# ============================================================
# CORPORATE UI
# ============================================================

st.markdown(
    """
    <style>

        @import url(
            'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap'
        );

        html, body, [class*="css"] {
            font-family: 'Inter',
            -apple-system,
            BlinkMacSystemFont,
            sans-serif;
        }

        [data-testid="stColumn"] {
            border-radius: 10px;
        }

        .brand-title {
            font-size: 22px;
            font-weight: 700;
            color: #0f172a;
            letter-spacing: -0.02em;
        }

        .brand-sub {
            font-size: 13px;
            color: #64748b;
            margin-bottom: 16px;
        }

        .privacy-notice {
            background-color: #f1f5f9;
            border-radius: 8px;
            padding: 12px 14px;
            font-size: 12px;
            color: #475569;
            border: 1px solid #e2e8f0;
            margin-bottom: 15px;
        }

        .escalation-box {
            background-color: #fef2f2;
            border: 1px solid #fecaca;
            border-radius: 8px;
            padding: 14px;
            margin-top: 10px;
            color: #991b1b;
            font-size: 13px;
        }

        .success-box {
            background-color: #ecfdf5;
            border: 1px solid #a7f3d0;
            border-radius: 8px;
            padding: 14px;
            margin-top: 10px;
            color: #065f46;
            font-size: 13px;
        }

        .login-card {
            max-width: 560px;
            margin: 80px auto;
            padding: 40px;
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            background: white;
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
        }

        .login-title {
            font-size: 30px;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 8px;
        }

        .login-subtitle {
            color: #64748b;
            font-size: 15px;
            margin-bottom: 24px;
        }

        .security-note {
            margin-top: 20px;
            padding: 12px 14px;
            border-radius: 8px;
            background: #f8fafc;
            color: #475569;
            font-size: 12px;
            border: 1px solid #e2e8f0;
        }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# CHECK POLICY PDF
# ============================================================

if not Path(POLICY_PDF).exists():

    st.error(
        f"Policy PDF not found: {POLICY_PDF}"
    )

    st.info(
        "Make sure the PDF is uploaded in the same directory "
        "as app.py."
    )

    st.stop()


# ============================================================
# GEMINI API
# ============================================================

if "GEMINI_API_KEY" not in st.secrets:

    st.error(
        "Gemini API key is not configured."
    )

    st.info(
        "Please add GEMINI_API_KEY to Streamlit Secrets."
    )

    st.stop()


try:

    gemini_client = genai.Client(
        api_key=st.secrets["GEMINI_API_KEY"]
    )

except Exception as e:

    st.error(
        "Unable to initialize the Gemini AI service."
    )

    st.error(str(e))

    st.stop()


# ============================================================
# SMTP CONFIGURATION
# ============================================================

def smtp_is_configured():

    return (
        "SMTP_EMAIL" in st.secrets
        and "SMTP_PASSWORD" in st.secrets
        and str(st.secrets["SMTP_EMAIL"]).strip() != ""
        and str(st.secrets["SMTP_PASSWORD"]).strip() != ""
    )


# ============================================================
# SEND EMAIL TO HR
# ============================================================

def send_hr_email(
    employee_name,
    employee_email,
    conversation
):

    if not smtp_is_configured():

        raise Exception(
            "Email service is not configured. "
            "Please check SMTP_EMAIL and SMTP_PASSWORD "
            "in Streamlit Secrets."
        )

    smtp_email = str(
        st.secrets["SMTP_EMAIL"]
    ).strip()

    smtp_password = str(
        st.secrets["SMTP_PASSWORD"]
    ).strip()

    smtp_host = str(
        st.secrets.get(
            "SMTP_HOST",
            "smtp.gmail.com"
        )
    ).strip()

    smtp_port = int(
        st.secrets.get(
            "SMTP_PORT",
            587
        )
    )

    # --------------------------------------------------------
    # Build conversation transcript
    # --------------------------------------------------------

    transcript_lines = []

    for message in conversation:

        role = (
            "EMPLOYEE"
            if message["role"] == "user"
            else "GM POLICY ASSISTANT"
        )

        transcript_lines.append(
            f"{role}:\n{message['content']}\n"
        )

    transcript = "\n".join(
        transcript_lines
    )

    # --------------------------------------------------------
    # Email
    # --------------------------------------------------------

    msg = EmailMessage()

    msg["Subject"] = (
        f"HR Assistance Required - "
        f"{employee_name}"
    )

    msg["From"] = smtp_email
    msg["To"] = HR_EMAIL
    msg["Reply-To"] = employee_email

    msg.set_content(
        f"""
HR Assistance Request
=====================

Employee Name:
{employee_name}

Employee Email:
{employee_email}

The employee marked a policy conversation as:

NOT SATISFIED

Conversation Transcript
======================

{transcript}

======================

Please follow up with the employee directly.

Google Chat:
{DIRECT_GOOGLE_CHAT_HR}

HR Booking Page:
{HR_BOOKING_URL}
"""
    )

    # --------------------------------------------------------
    # SMTP connection
    # --------------------------------------------------------

    with smtplib.SMTP(
        smtp_host,
        smtp_port,
        timeout=30
    ) as server:

        server.ehlo()

        server.starttls()

        server.ehlo()

        server.login(
            smtp_email,
            smtp_password
        )

        server.send_message(msg)


# ============================================================
# PDF PROCESSING
# ============================================================

@st.cache_resource
def load_and_index_pdf(pdf_path):

    reader = PdfReader(pdf_path)

    pages_text = []

    for idx, page in enumerate(reader.pages):

        text = page.extract_text() or ""

        pages_text.append(
            {
                "page": idx + 1,
                "text": text
            }
        )

    return pages_text


# ============================================================
# GEMINI POLICY QUERY
# ============================================================

def query_policy_ai(
    prompt,
    conversation_history
):

    history_context = ""

    for msg in conversation_history[-8:]:

        role = (
            "Employee"
            if msg["role"] == "user"
            else "Assistant"
        )

        history_context += (
            f"{role}: {msg['content']}\n"
        )

    # --------------------------------------------------------
    # Load policy
    # --------------------------------------------------------

    pdf_pages = load_and_index_pdf(
        POLICY_PDF
    )

    full_context = "\n\n".join(
        [
            f"--- PAGE {p['page']} ---\n{p['text']}"
            for p in pdf_pages
        ]
    )

    # --------------------------------------------------------
    # System prompt
    # --------------------------------------------------------

    system_prompt = f"""
You are the official GM Policy Assistant
for Germane Media LLC.

Your ONLY source of policy information is the
Germane Media LLC Employee Policy Handbook
provided below.

You are NOT allowed to use general HR knowledge,
internet information, assumptions, or outside sources.

============================================================
IMPORTANT RULES
============================================================

1. ANSWER STRICTLY FROM THE POLICY HANDBOOK.

2. DO NOT INVENT POLICY.

3. DO NOT ASSUME INFORMATION THAT IS NOT WRITTEN
   IN THE HANDBOOK.

4. If the question cannot be answered from the handbook,
   respond exactly:

"I couldn't find a specific provision covering this in the
Germane Media LLC Employee Policy Handbook. I recommend
contacting HR directly for clarification."

5. ALWAYS provide page citations.

Example:

[📄 Page 12]

6. If multiple pages support the answer, cite all relevant
   pages.

Example:

[📄 Page 2, Page 18, Page 24]

7. For appraisal, compensation, variable pay, probation,
   confirmation, extension, termination or similar matters,
   explicitly mention management discretion where the
   handbook provides for it.

8. If the employee asks a follow-up question, use the
   previous conversation to understand what they mean.

9. Keep answers professional, concise and easy to understand.

10. Never claim something is policy unless it is supported
    by the handbook.

11. If a policy has an exception, clearly mention it.

12. If the handbook gives a specific number, date, duration,
    percentage, amount or entitlement, reproduce it accurately.

13. The Employment Agreement may prevail where applicable,
    but do not invent Employment Agreement terms.

============================================================
POLICY HANDBOOK
============================================================

{full_context}

============================================================
CONVERSATION HISTORY
============================================================

{history_context}

============================================================
EMPLOYEE QUESTION
============================================================

{prompt}

============================================================
ANSWER
============================================================
"""

    try:

        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=system_prompt
        )

        if response and response.text:

            return response.text.strip()

        raise Exception(
            "Gemini returned an empty response."
        )

    except Exception as e:

        raise Exception(
            "AI Assistant is currently unavailable. "
            "Please contact HR. "
            f"Technical details: {str(e)}"
        )


# ============================================================


# LOGIN PAGE
# ============================================================

if not st.user.is_logged_in:

    # Load logo.png from the same folder as app.py.
    # A text "G" fallback is used if the file is temporarily unavailable.
    logo_path = Path(__file__).parent / "logo.png"

    if logo_path.exists():
        logo_b64 = base64.b64encode(logo_path.read_bytes()).decode("utf-8")
        logo_html = (
            f'<img class="brand-logo" src="data:image/png;base64,{logo_b64}" '
            'alt="Germane Media LLC logo">'
        )
    else:
        logo_html = '<div class="brand-logo-fallback">G</div>'

    st.markdown(
        """
        <style>
        /* ---------- Streamlit chrome ---------- */
        #MainMenu, footer, header {
            visibility: hidden;
        }

        .stApp {
            background:
                radial-gradient(circle at 12% 20%, rgba(112, 72, 237, 0.06), transparent 28%),
                radial-gradient(circle at 82% 55%, rgba(112, 72, 237, 0.05), transparent 30%),
                #fbfbfe;
        }

        .block-container {
            max-width: 1400px !important;
            padding: 28px 38px 18px !important;
        }

        /* ---------- Main login layout ---------- */
        .login-page {
            min-height: calc(100vh - 90px);
            display: flex;
            align-items: center;
        }

        .left-panel {
            padding: 28px 34px 10px 18px;
        }

        .right-panel {
            padding: 0 8px 0 24px;
        }

        /* ---------- Brand ---------- */
        .brand {
            display: flex;
            align-items: center;
            gap: 22px;
            margin-bottom: 54px;
        }

        .brand-logo,
        .brand-logo-fallback {
            width: 102px;
            height: 102px;
            object-fit: contain;
            flex: 0 0 102px;
        }

        .brand-logo-fallback {
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 24px;
            background: linear-gradient(135deg, #5d4bea, #7c4df0);
            color: white;
            font-size: 58px;
            font-weight: 800;
            box-shadow: 0 12px 28px rgba(91, 75, 234, .20);
        }

        .brand-name {
            font-size: 31px;
            line-height: 1.1;
            font-weight: 800;
            color: #15213a;
            letter-spacing: -0.7px;
        }

        .brand-subtitle {
            margin-top: 10px;
            font-size: 17px;
            font-weight: 600;
            color: #5b48c9;
        }

        .brand-line {
            width: 60px;
            height: 3px;
            margin-top: 25px;
            border-radius: 10px;
            background: #6547ed;
        }

        /* ---------- Left content ---------- */
        .left-title {
            font-size: 23px;
            line-height: 1.25;
            font-weight: 800;
            color: #17233c;
            margin-bottom: 15px;
        }

        .left-description {
            max-width: 610px;
            font-size: 16px;
            line-height: 1.65;
            color: #596274;
            margin-bottom: 38px;
        }

        .features {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 28px 38px;
            max-width: 650px;
        }

        .feature {
            display: flex;
            gap: 15px;
            align-items: flex-start;
        }

        .feature-icon {
            width: 62px;
            height: 62px;
            flex: 0 0 62px;
            border-radius: 17px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #f0edff;
            color: #6049dc;
            font-size: 29px;
        }

        .feature-title {
            color: #18233a;
            font-size: 14px;
            line-height: 1.25;
            font-weight: 800;
            margin: 5px 0 8px;
        }

        .feature-text {
            color: #626b7c;
            font-size: 13px;
            line-height: 1.65;
        }

        /* ---------- Decorative wave ---------- */
        .wave {
            margin-top: 40px;
            width: 100%;
            height: 95px;
            overflow: hidden;
            opacity: .75;
        }

        .wave svg {
            width: 100%;
            height: 100%;
        }

        /* ---------- Login card ----------
           The second Streamlit column is the card. The invisible
           anchor below lets us target that exact column with :has(). */
        div[data-testid="stColumn"]:has(.login-card-anchor) {
            background: rgba(255, 255, 255, .97);
            border: 1px solid #e8e8ef;
            border-radius: 20px;
            padding: 34px 38px 28px !important;
            box-shadow: 0 14px 40px rgba(32, 35, 58, .09);
            box-sizing: border-box;
            align-self: stretch;
        }

        .login-card {
            padding: 0;
        }

        .login-card-anchor {
            display: none;
        }

        .lock-circle {
            width: 94px;
            height: 94px;
            margin: 0 auto 18px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #f0edff;
            color: #5e46d8;
            font-size: 42px;
        }

        .card-title {
            text-align: center;
            color: #17233c;
            font-size: 31px;
            line-height: 1.15;
            font-weight: 800;
            letter-spacing: -.5px;
            margin-bottom: 9px;
        }

        .card-subtitle {
            text-align: center;
            color: #747d8e;
            font-size: 15px;
            margin-bottom: 28px;
        }

        .restricted {
            display: flex;
            align-items: center;
            gap: 14px;
            padding: 17px 18px;
            margin-bottom: 34px;
            border: 1px solid #e3ddff;
            background: #faf9ff;
            border-radius: 11px;
            color: #5a43c9;
            font-size: 14px;
            line-height: 1.55;
            font-weight: 700;
        }

        .restricted-icon {
            font-size: 22px;
            flex: 0 0 auto;
        }

        .signin-label {
            text-align: center;
            color: #1d263b;
            font-size: 15px;
            font-weight: 800;
            margin-bottom: 12px;
        }

        /* ---------- Real Streamlit login button ---------- */
        div[data-testid="stButton"] {
            width: 100% !important;
            display: flex;
            justify-content: center;
            margin: 0;
        }

        div[data-testid="stButton"] button {
            width: 100% !important;
            min-height: 54px !important;
            border-radius: 8px !important;
            border: 1px solid #6547ed !important;
            background: linear-gradient(90deg, #6547ed, #7048ed) !important;
            color: #ffffff !important;
            font-size: 16px !important;
            font-weight: 800 !important;
            box-shadow: none !important;
        }

        div[data-testid="stButton"] button:hover {
            border-color: #5538d8 !important;
            background: linear-gradient(90deg, #5b3fe1, #6840e6) !important;
        }

        .google-mark {
            display: inline-flex;
            width: 43px;
            height: 52px;
            align-items: center;
            justify-content: center;
            background: white;
            border-radius: 8px 0 0 8px;
            color: #4285f4;
            font-size: 20px;
            font-weight: 900;
            margin-right: 12px;
        }

        /* ---------- Divider / Workspace note ---------- */
        .divider {
            display: flex;
            align-items: center;
            gap: 15px;
            margin: 29px 0 24px;
            color: #9aa1ae;
            font-size: 13px;
        }

        .divider::before,
        .divider::after {
            content: "";
            height: 1px;
            background: #e7e7ed;
            flex: 1;
        }

        .workspace-note {
            display: flex;
            gap: 15px;
            padding: 18px 17px;
            border: 1px solid #e6e6ee;
            background: #fff;
            border-radius: 11px;
            color: #667083;
            font-size: 13px;
            line-height: 1.65;
        }

        .workspace-icon {
            width: 30px;
            flex: 0 0 30px;
            color: #6547ed;
            font-size: 25px;
            text-align: center;
        }

        .workspace-note strong {
            color: #252d40;
        }

        .protected {
            text-align: center;
            margin-top: 32px;
            color: #858d9c;
            font-size: 12px;
        }

        .protected-icon {
            color: #8a91a2;
        }

        /* ---------- Bottom footer ---------- */
        .page-footer {
            text-align: center;
            margin-top: 12px;
            color: #8a91a2;
            font-size: 12px;
        }

        /* ---------- Responsive ---------- */
        @media (max-width: 900px) {
            .block-container {
                padding: 20px 18px !important;
            }

            .login-page {
                display: block;
            }

            .left-panel,
            .right-panel {
                padding: 15px 8px;
            }

            .brand {
                margin-bottom: 34px;
            }

            .features {
                grid-template-columns: 1fr;
                gap: 20px;
            }

            div[data-testid="stColumn"]:has(.login-card-anchor) {
                padding: 24px 20px !important;
            }

            .login-card {
                min-height: auto;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Two-column page. The actual login button remains a Streamlit widget
    # so st.login() continues to work normally.
    left_col, right_col = st.columns([1.03, 0.97], gap="large")

    with left_col:
        left_html = textwrap.dedent(f"""
            <div class="left-panel">
                <div class="brand">
                    {logo_html}
                    <div>
                        <div class="brand-name">Germane Media LLC</div>
                        <div class="brand-subtitle">GM Policy Assistant • Internal HR Portal</div>
                        <div class="brand-line"></div>
                    </div>
                </div>

                <div class="left-title">Your Intelligent HR Policy Companion</div>

                <div class="left-description">
                    Get instant, accurate answers to your policy questions,
                    understand company guidelines, and connect with HR
                    for personalized support — anytime, anywhere.
                </div>

                <div class="features">
                    <div class="feature">
                        <div class="feature-icon">▢</div>
                        <div>
                            <div class="feature-title">Instant Policy Answers</div>
                            <div class="feature-text">
                                Accurate responses based on Germane Media LLC
                                Employee Policy Handbook.
                            </div>
                        </div>
                    </div>

                    <div class="feature">
                        <div class="feature-icon">♙</div>
                        <div>
                            <div class="feature-title">Secure &amp; Confidential</div>
                            <div class="feature-text">
                                Your conversations are private, secure, and
                                associated with your company account.
                            </div>
                        </div>
                    </div>

                    <div class="feature">
                        <div class="feature-icon">♧</div>
                        <div>
                            <div class="feature-title">Direct HR Support</div>
                            <div class="feature-text">
                                Escalate questions to HR or schedule a confidential
                                15-minute discussion.
                            </div>
                        </div>
                    </div>

                    <div class="feature">
                        <div class="feature-icon">♟</div>
                        <div>
                            <div class="feature-title">For Employees Only</div>
                            <div class="feature-text">
                                This portal is restricted to active Germane Media
                                LLC employees.
                            </div>
                        </div>
                    </div>
                </div>

                <div class="wave">
                    <svg viewBox="0 0 900 120" preserveAspectRatio="none">
                        <path d="M0,65 C120,115 180,10 300,65 S480,115 600,60 S780,10 900,65"
                              fill="none" stroke="#c9c0ff" stroke-width="2"/>
                        <path d="M0,80 C120,125 180,25 300,75 S480,125 600,70 S780,25 900,75"
                              fill="none" stroke="#ddd8ff" stroke-width="2"/>
                        <path d="M0,95 C120,135 180,40 300,85 S480,135 600,80 S780,40 900,85"
                              fill="none" stroke="#ebe8ff" stroke-width="2"/>
                    </svg>
                </div>
            </div>
        """)
        st.html(left_html)

    with right_col:
        # A real Streamlit container keeps the complete login card together,
        # while the HTML inside it is safely dedented so it is rendered as HTML.
        with st.container(border=True):
            card_html = textwrap.dedent("""
                <div class="login-card">
                    <div class="lock-circle">🔒</div>

                    <div class="card-title">Welcome Back!</div>
                    <div class="card-subtitle">
                        Sign in to access the GM Policy Assistant
                    </div>

                    <div class="restricted">
                        <div class="restricted-icon">🔒</div>
                        <div>
                            This portal is restricted to active
                            Germane Media LLC employees.
                        </div>
                    </div>

                    <div class="signin-label">Sign in with your company account</div>
                </div>
            """)
            st.html(card_html)

            if st.button(
                "G   Sign in with Google",
                key="login_button",
                type="primary",
                use_container_width=True,
            ):
                st.login()

            bottom_html = textwrap.dedent("""
                <div class="divider">OR</div>

                <div class="workspace-note">
                    <div class="workspace-icon">▦</div>
                    <div>
                        Please use your official
                        <strong>@thegermanemedia.com Google Workspace account.</strong><br>
                        Your policy conversations are associated with your
                        authenticated company account.
                    </div>
                </div>

                <div class="protected">
                    <span class="protected-icon">🛡</span>
                    Protected by Google Workspace Authentication
                </div>
            """)
            st.html(bottom_html)

    st.html(
        textwrap.dedent("""
            <div class="page-footer">
                🛡 Secure • Private • Trusted
                &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
                © 2026 Germane Media LLC. All rights reserved.
                &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
                Internal Use Only
            </div>
        """)
    )

    st.stop()


# VERIFIED GOOGLE IDENTITY
# ============================================================

try:

    user_email = (
        st.user.email
        .lower()
        .strip()
    )

except Exception:

    st.error(
        "Unable to identify your Google account."
    )

    st.stop()


user_name = (
    getattr(
        st.user,
        "name",
        None
    )
    or user_email.split("@")[0]
)


# ============================================================
# COMPANY DOMAIN SECURITY
# ============================================================

if not user_email.endswith(
    f"@{COMPANY_DOMAIN}"
):

    st.error(
        "Access denied. This application is restricted "
        "to Germane Media LLC employees."
    )

    st.warning(
        "Please sign in using your "
        "@thegermanemedia.com Google Workspace account."
    )

    if st.button(
        "🚪 Sign Out"
    ):

        st.logout()

    st.stop()


# ============================================================
# EMPLOYEE SESSION
# ============================================================

st.session_state.emp_name = user_name
st.session_state.emp_email = user_email

st.session_state.is_hr = (
    user_email == HR_EMAIL.lower()
)


# ============================================================
# SESSION INITIALIZATION
# ============================================================

if "messages" not in st.session_state:

    st.session_state.messages = []


if "unsatisfied_msg_idx" not in st.session_state:

    st.session_state.unsatisfied_msg_idx = None


if "hr_email_sent" not in st.session_state:

    st.session_state.hr_email_sent = False


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        f"**👤 {st.session_state.emp_name}**"
    )

    st.caption(
        st.session_state.emp_email
    )

    if st.session_state.is_hr:

        st.success(
            "🔑 HR Admin Mode Active"
        )

    st.divider()

    st.markdown(
        "📚 **Company Policy Categories**"
    )

    categories = [
        "Leave Policy",
        "Attendance & Work Hours",
        "Appraisal & Revisions",
        "Reimbursement",
        "Probation & Confirmation",
        "Full & Final Settlement"
    ]

    for cat in categories:

        if st.button(
            f"📄 {cat}",
            key=f"category_{cat}",
            width="stretch"
        ):

            st.session_state.messages.append(
                {
                    "role": "user",
                    "content":
                    f"Summarize the key points of the {cat}."
                }
            )

            st.rerun()

    st.divider()

    st.link_button(
        "💬 Message HR on Google Chat",
        DIRECT_GOOGLE_CHAT_HR,
        width="stretch"
    )

    st.divider()

    if st.button(
        "🚪 Sign Out",
        width="stretch"
    ):

        st.session_state.clear()

        st.logout()


# ============================================================
# MAIN INTERFACE
# ============================================================

col_main, col_right = st.columns(
    [3, 1.2]
)


# ============================================================
# CHAT AREA
# ============================================================

with col_main:

    st.markdown(
        '<div class="brand-title">'
        'GM Policy Assistant'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="brand-sub">'
        'Ask questions, verify rules, and schedule direct support.'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="privacy-notice">

        🔒 <b>Private HR Conversation:</b>

        Your chat session is associated with your
        authenticated employee account.

        <br><br>

        HR may access transcripts for support and
        policy administration.

        </div>
        """,
        unsafe_allow_html=True
    )


    # ========================================================
    # CHAT HISTORY
    # ========================================================

    for idx, message in enumerate(
        st.session_state.messages
    ):

        with st.chat_message(
            message["role"]
        ):

            st.markdown(
                message["content"]
            )

            # ------------------------------------------------
            # Feedback buttons for assistant responses
            # ------------------------------------------------

            if message["role"] == "assistant":

                col_sat, col_not_sat, col_space = st.columns(
                    [1, 1, 3]
                )

                # --------------------------------------------
                # SATISFIED
                # --------------------------------------------

                with col_sat:

                    if st.button(
                        "✅ Satisfied",
                        key=f"satisfied_{idx}"
                    ):

                        st.toast(
                            "Thank you for your feedback!"
                        )

                # --------------------------------------------
                # NOT SATISFIED
                # --------------------------------------------

                with col_not_sat:

                    if st.button(
                        "❌ Not Satisfied",
                        key=f"not_satisfied_{idx}"
                    ):

                        st.session_state.unsatisfied_msg_idx = idx

                        # Reset email state for this request
                        st.session_state.hr_email_sent = False

                        st.rerun()


                # ------------------------------------------------
                # HR ESCALATION AREA
                # ------------------------------------------------

                if (
                    st.session_state.unsatisfied_msg_idx
                    == idx
                ):

                    st.markdown(
                        """
                        <div class="escalation-box">

                        <b>We're sorry we couldn't fully resolve your question.</b>

                        <br><br>

                        You can contact HR directly or schedule
                        a confidential 15-minute discussion.

                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    col_email, col_calendar = st.columns(
                        [1, 1]
                    )

                    # --------------------------------------------
                    # SEND TO HR
                    # --------------------------------------------

                    with col_email:

                        if st.button(
                            "📧 Send to HR",
                            key=f"send_hr_{idx}",
                            width="stretch"
                        ):

                            try:

                                send_hr_email(
                                    employee_name=(
                                        st.session_state.emp_name
                                    ),
                                    employee_email=(
                                        st.session_state.emp_email
                                    ),
                                    conversation=(
                                        st.session_state.messages
                                    )
                                )

                                st.session_state.hr_email_sent = True

                                st.success(
                                    "Your conversation has been "
                                    "sent to HR successfully."
                                )

                            except Exception as e:

                                st.error(
                                    f"Unable to notify HR: {str(e)}"
                                )

                    # --------------------------------------------
                    # SCHEDULE HR CALL
                    # --------------------------------------------

                    with col_calendar:

                        st.link_button(
                            "📅 Schedule HR Call",
                            HR_BOOKING_URL,
                            width="stretch"
                        )

                    # --------------------------------------------
                    # EMAIL SENT MESSAGE
                    # --------------------------------------------

                    if st.session_state.hr_email_sent:

                        st.markdown(
                            """
                            <div class="success-box">

                            ✅ <b>HR has been notified.</b>

                            Your conversation transcript has been
                            sent to HR. You can also schedule a
                            confidential discussion if required.

                            </div>
                            """,
                            unsafe_allow_html=True
                        )


    # ========================================================
    # CHAT INPUT
    # ========================================================

    user_query = st.chat_input(
        "Ask a policy question "
        "(e.g., 'How many leaves do I get per month?')..."
    )


    if user_query:

        st.session_state.messages.append(
            {
                "role": "user",
                "content": user_query
            }
        )

        # Reset previous escalation state
        st.session_state.unsatisfied_msg_idx = None
        st.session_state.hr_email_sent = False

        with st.spinner(
            "Searching Germane Media Policy Handbook..."
        ):

            try:

                response = query_policy_ai(
                    user_query,
                    st.session_state.messages
                )

                full_response = (
                    response
                    + "\n\n---\n"
                    + "*Notice: Answers are derived from "
                    "the Germane Media LLC Policy Handbook. "
                    "Employment Agreement terms prevail "
                    "where applicable.*"
                )

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": full_response
                    }
                )

                st.rerun()

            except Exception as e:

                st.error(
                    str(e)
                )


# ============================================================
# RIGHT SIDEBAR
# ============================================================

with col_right:

    st.markdown(
        "### 📅 **Schedule HR Discussion**"
    )

    st.caption(
        "Need to speak directly with HR? "
        "Book a 15-minute confidential discussion."
    )

    st.link_button(
        "📅 Schedule 15-Minute HR Discussion",
        HR_BOOKING_URL,
        type="primary",
        width="stretch"
    )

    st.caption(
        "Google Calendar will show only the available "
        "appointment slots. A Google Meet link will be "
        "provided after booking."
    )

    st.divider()

    st.markdown(
        "💬 **Need immediate help?**"
    )

    st.link_button(
        "💬 Contact HR on Google Chat",
        DIRECT_GOOGLE_CHAT_HR,
        width="stretch"
    )

    st.divider()

    st.markdown(
        "💡 **Suggested Questions**"
    )

    suggested = [
        "How many leaves accumulate during probation?",
        "When am I eligible for appraisal consideration?",
        "What is the timeline for FNF settlement?",
        "How do medical reimbursement requests work?"
    ]

    for q in suggested:

        if st.button(
            f"❓ {q}",
            key=f"suggested_{q}",
            width="stretch"
        ):

            st.session_state.messages.append(
                {
                    "role": "user",
                    "content": q
                }
            )

            st.rerun()
