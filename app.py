import streamlit as st
from google import genai
from pypdf import PdfReader
import smtplib
from email.message import EmailMessage
from html import escape
import base64
from pathlib import Path
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

HR_BOOKING_URL = (
    "https://calendar.app.google/wjkBcfyeAgKqCRUVA"
)

DIRECT_GOOGLE_CHAT_HR = (
    "https://chat.google.com/dm/tarang@thegermanemedia.com"
)

POLICY_PDF = "GERMANE_MEDIA_LLC_POLICY_DOCUMENT.pdf"


# ============================================================
# BRAND ASSET
# ============================================================

def get_logo_data_uri():
    """Load the repository logo for the login page."""
    try:
        logo_path = Path("logo.png")
        if logo_path.exists():
            encoded = base64.b64encode(
                logo_path.read_bytes()
            ).decode("utf-8")
            return f"data:image/png;base64,{encoded}"
    except Exception:
        pass

    return ""


# ============================================================
# GLOBAL CSS
# ============================================================

st.markdown(
    textwrap.dedent("""
    <style>

    /* ========================================================
       GENERAL
       ======================================================== */

    @import url(
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
    );

    html, body, [class*="css"] {
        font-family: 'Inter',
        -apple-system,
        BlinkMacSystemFont,
        sans-serif;
    }

    .stApp {
        background: #f8f9ff;
    }

    /* Hide Streamlit default menu/footer */
    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header {
        background: transparent;
    }


    /* ========================================================
       LOGIN PAGE
       ======================================================== */

    .login-page {
        min-height: calc(100vh - 30px);
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 30px 24px 45px;
        background:
            radial-gradient(circle at 15% 20%, rgba(104, 80, 240, 0.10), transparent 34%),
            radial-gradient(circle at 85% 75%, rgba(126, 92, 255, 0.09), transparent 34%),
            #f8f9ff;
        box-sizing: border-box;
    }

    .login-wrapper {
        width: 100%;
        max-width: 1360px;
        display: grid;
        grid-template-columns: 1.03fr 0.97fr;
        gap: 52px;
        align-items: center;
    }

    /* LEFT BRAND SECTION */

    .brand-section {
        padding: 20px 22px;
    }

    .brand-header {
        display: flex;
        align-items: center;
        gap: 20px;
        margin-bottom: 22px;
    }

    .brand-logo-img {
        width: 92px;
        height: 92px;
        object-fit: contain;
        border-radius: 24px;
        filter: drop-shadow(0 14px 25px rgba(91, 75, 231, 0.18));
        flex: 0 0 auto;
    }

    .brand-logo-fallback {
        width: 92px;
        height: 92px;
        border-radius: 24px;
        background: linear-gradient(135deg, #5540df, #8b6cff);
        color: #fff;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 58px;
        font-weight: 800;
        box-shadow: 0 15px 35px rgba(91, 75, 231, 0.25);
    }

    .brand-company {
        font-size: clamp(30px, 3vw, 43px);
        font-weight: 800;
        color: #17213a;
        letter-spacing: -1.7px;
        line-height: 1.08;
    }

    .brand-product {
        margin-top: 9px;
        font-size: 18px;
        font-weight: 700;
        color: #6049e8;
    }

    .brand-line {
        width: 70px;
        height: 4px;
        border-radius: 10px;
        background: linear-gradient(90deg, #6049e8, #8b6cff);
        margin: 20px 0 42px;
    }

    .brand-heading {
        font-size: clamp(25px, 2.2vw, 32px);
        font-weight: 800;
        color: #17213a;
        margin-bottom: 15px;
        letter-spacing: -0.9px;
    }

    .brand-description {
        max-width: 650px;
        font-size: 17px;
        line-height: 1.75;
        color: #53617c;
        margin-bottom: 30px;
    }

    .features-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;
        max-width: 690px;
    }

    .feature-card {
        background: rgba(255,255,255,0.82);
        border: 1px solid #e6e3fb;
        border-radius: 18px;
        padding: 19px;
        display: flex;
        gap: 14px;
        box-shadow: 0 10px 30px rgba(76, 63, 145, 0.05);
        backdrop-filter: blur(8px);
    }

    .feature-icon {
        min-width: 50px;
        width: 50px;
        height: 50px;
        border-radius: 15px;
        background: #f0edff;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
    }

    .feature-title {
        font-size: 15px;
        font-weight: 800;
        color: #17213a;
        margin-bottom: 6px;
    }

    .feature-text {
        font-size: 13px;
        line-height: 1.55;
        color: #64718b;
    }

    .wave-decoration {
        margin-top: 32px;
        height: 65px;
        overflow: hidden;
        opacity: 0.38;
        position: relative;
    }

    .wave-decoration::before,
    .wave-decoration::after {
        content: "";
        position: absolute;
        left: -5%;
        width: 110%;
        height: 55px;
        border-top: 2px solid #8174e9;
        border-radius: 50%;
        transform: rotate(-3deg);
    }

    .wave-decoration::after {
        top: 17px;
        transform: rotate(3deg);
        opacity: 0.65;
    }

    /* RIGHT LOGIN CARD */

    /* Streamlit bordered container used for the login card */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255,255,255,0.97);
        border: 1px solid #e4e5f2 !important;
        border-radius: 28px !important;
        padding: 12px !important;
        box-shadow: 0 25px 70px rgba(34, 28, 88, 0.12);
    }


    .login-card {
        background: rgba(255,255,255,0.97);
        border: 1px solid #e4e5f2;
        border-radius: 28px;
        padding: 40px 42px 34px;
        box-shadow: 0 25px 70px rgba(34, 28, 88, 0.12);
    }

    .login-lock {
        width: 100px;
        height: 100px;
        border-radius: 50%;
        background: #f0edff;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 46px;
        margin: 0 auto 20px;
    }

    .welcome-title {
        text-align: center;
        font-size: 34px;
        font-weight: 800;
        color: #17213a;
        margin-bottom: 7px;
        letter-spacing: -0.8px;
    }

    .welcome-subtitle {
        text-align: center;
        color: #687591;
        font-size: 16px;
        margin-bottom: 27px;
    }

    .restricted-box {
        display: flex;
        gap: 14px;
        align-items: center;
        padding: 17px;
        border: 1px solid #e1ddfb;
        background: #faf9ff;
        border-radius: 14px;
        margin-bottom: 27px;
    }

    .restricted-icon {
        font-size: 25px;
    }

    .restricted-text {
        font-size: 14px;
        line-height: 1.5;
        font-weight: 700;
        color: #5741d9;
    }

    .signin-heading {
        text-align: center;
        color: #17213a;
        font-size: 17px;
        font-weight: 700;
        margin-bottom: 14px;
    }

    /* The actual Streamlit Google button is placed immediately
       below the card header. It is styled to match the design. */

    .login-button-area {
        margin: -3px 0 0;
    }

    .stButton > button[kind="primary"] {
        min-height: 56px !important;
        border-radius: 12px !important;
        border: 0 !important;
        background: linear-gradient(135deg, #6049e8, #7658f5) !important;
        color: white !important;
        font-size: 16px !important;
        font-weight: 800 !important;
        box-shadow: 0 12px 25px rgba(96, 73, 232, 0.22) !important;
    }

    .stButton > button[kind="primary"]:hover {
        filter: brightness(1.04);
        transform: translateY(-1px);
    }

    .google-note {
        margin-top: 22px;
        padding: 18px;
        border: 1px solid #e5e6f0;
        border-radius: 14px;
        background: #fafbff;
        color: #53617c;
        font-size: 13px;
        line-height: 1.65;
    }

    .google-note strong {
        color: #17213a;
    }

    .protected-text {
        text-align: center;
        margin-top: 20px;
        color: #73809a;
        font-size: 13px;
    }

    .login-footer {
        text-align: center;
        margin-top: 24px;
        color: #73809a;
        font-size: 12px;
    }


    /* ========================================================
       MAIN APPLICATION
       ======================================================== */

    .app-brand-title {
        font-size: 25px;
        font-weight: 800;
        color: #17213a;
    }

    .app-brand-sub {
        color: #687591;
        font-size: 14px;
        margin-top: 5px;
        margin-bottom: 18px;
    }

    .privacy-notice {
        background: #f4f2ff;
        border: 1px solid #ddd8ff;
        border-radius: 12px;
        padding: 14px 17px;
        color: #51458b;
        font-size: 13px;
        margin-bottom: 18px;
    }

    .escalation-box {
        background: #fff7f7;
        border: 1px solid #fecaca;
        border-radius: 12px;
        padding: 17px;
        margin-top: 10px;
        color: #991b1b;
        font-size: 13px;
    }


    /* ========================================================
       SIDEBAR
       ======================================================== */

    section[data-testid="stSidebar"] {
        background: #20212b;
    }

    section[data-testid="stSidebar"] * {
        color: #f8fafc;
    }


    /* ========================================================
       RESPONSIVE
       ======================================================== */

    @media (max-width: 900px) {

        .login-wrapper {
            grid-template-columns: 1fr;
        }

        .brand-section {
            padding: 10px;
        }

        .brand-company {
            font-size: 30px;
        }

        .brand-heading {
            font-size: 25px;
        }

        .features-grid {
            grid-template-columns: 1fr;
        }

        .login-card {
            padding: 28px;
        }
    }

    </style>

    """),
    unsafe_allow_html=True
)


# ============================================================
# GEMINI API
# ============================================================

if "GEMINI_API_KEY" not in st.secrets:

    st.error(
        "Gemini API key is not configured. "
        "Please contact the administrator."
    )

    st.stop()


try:

    gemini_client = genai.Client(
        api_key=st.secrets["GEMINI_API_KEY"]
    )

except Exception:

    st.error(
        "Unable to initialize the Gemini AI service. "
        "Please contact the administrator."
    )

    st.stop()


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

def query_policy_ai(prompt, conversation_history):

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

    pdf_pages = load_and_index_pdf(POLICY_PDF)

    full_context = "\n\n".join(
        [
            f"--- PAGE {p['page']} ---\n{p['text']}"
            for p in pdf_pages
        ]
    )

    system_prompt = f"""
You are the official GM Policy Assistant for
Germane Media LLC.

Your role is to assist employees with workplace
policy questions using ONLY the provided
Germane Media LLC Employee Policy Handbook.

CRITICAL RULES:

1. Answer strictly from the policy handbook.

2. Do NOT use internet information.

3. Do NOT use general HR knowledge.

4. Do NOT invent policy.

5. Do NOT assume information that is not present
   in the handbook.

6. If the question cannot be answered from the
   handbook, respond exactly:

"I couldn't find a specific provision covering this
in the Germane Media LLC Employee Policy Handbook.
I recommend contacting HR directly for clarification."

7. ALWAYS include exact page citations for relevant
   information.

Example:

[📄 Page 12]

8. If multiple pages support the answer, cite all
   relevant pages.

Example:

[📄 Pages 12, 14]

9. Maintain a professional, neutral and helpful
   corporate tone.

10. For appraisal, variable pay, probation,
    confirmation, extension or termination matters,
    explicitly mention management discretion whenever
    the handbook indicates it.

11. If the employee asks a follow-up question,
    use the conversation history to understand
    the context.

12. The policy handbook is the ONLY source of
    policy information.

POLICY HANDBOOK:

{full_context}

CONVERSATION HISTORY:

{history_context}

EMPLOYEE QUESTION:

{prompt}
"""

    try:

        response = gemini_client.models.generate_content(
            model="gemini-3.6-flash",
            contents=system_prompt
        )

        if response and response.text:

            return response.text

        raise Exception(
            "Gemini returned an empty response."
        )

    except Exception as e:

        raise Exception(
            "AI Assistant is currently unavailable. "
            "Please contact HR."
        )


# ============================================================
# SEND TRANSCRIPT TO HR
# ============================================================

def send_transcript_to_hr():

    if (
        "SMTP_USER" not in st.secrets
        or "SMTP_PASSWORD" not in st.secrets
    ):

        return False, (
            "Email service is not configured. "
            "Please check SMTP_USER and SMTP_PASSWORD "
            "in Streamlit Secrets."
        )

    try:

        employee_name = st.session_state.get(
            "emp_name",
            "Employee"
        )

        employee_email = st.session_state.get(
            "emp_email",
            "Unknown"
        )

        messages = st.session_state.get(
            "messages",
            []
        )

        transcript_lines = []

        for message in messages:

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

        email = EmailMessage()

        email["Subject"] = (
            f"HR Assistance Request - {employee_name}"
        )

        email["From"] = st.secrets["SMTP_USER"]

        email["To"] = HR_EMAIL

        email["Reply-To"] = employee_email

        email.set_content(
            f"""
GM POLICY ASSISTANT
HR ASSISTANCE REQUEST

Employee Name:
{employee_name}

Employee Email:
{employee_email}

--------------------------------------------------
CONVERSATION TRANSCRIPT
--------------------------------------------------

{transcript}

--------------------------------------------------

This request was submitted through the
Germane Media LLC GM Policy Assistant.

Please follow up with the employee directly
if required.
"""
        )

        with smtplib.SMTP(
            "smtp.gmail.com",
            587,
            timeout=20
        ) as server:

            server.starttls()

            server.login(
                st.secrets["SMTP_USER"],
                st.secrets["SMTP_PASSWORD"]
            )

            server.send_message(email)

        return True, "HR has been notified successfully."

    except Exception:

        return False, (
            "Unable to notify HR at the moment. "
            "Please contact HR directly."
        )


# ============================================================
# LOGIN PAGE
# ============================================================

if not st.user.is_logged_in:

    logo_uri = get_logo_data_uri()

    if logo_uri:
        logo_html = f'<img class="brand-logo-img" src="{logo_uri}" alt="Germane Media LLC logo">'
    else:
        logo_html = '<div class="brand-logo-fallback">G</div>'

    left_col, right_col = st.columns(
        [1.03, 0.97],
        gap="large"
    )

    # --------------------------------------------------------
    # LEFT BRANDING
    # --------------------------------------------------------

    with left_col:

        st.markdown(
            textwrap.dedent(
                f"""
                <div class="brand-section">

                    <div class="brand-header">

                        {logo_html}

                        <div>
                            <div class="brand-company">
                                Germane Media LLC
                            </div>

                            <div class="brand-product">
                                GM Policy Assistant • Internal HR Portal
                            </div>
                        </div>

                    </div>

                    <div class="brand-line"></div>

                    <div class="brand-heading">
                        Your Intelligent HR Policy Companion
                    </div>

                    <div class="brand-description">
                        Get instant, accurate answers to your policy questions,
                        understand company guidelines, and connect with HR for
                        personalized support — anytime, anywhere.
                    </div>

                    <div class="features-grid">

                        <div class="feature-card">
                            <div class="feature-icon">📖</div>
                            <div>
                                <div class="feature-title">
                                    Instant Policy Answers
                                </div>
                                <div class="feature-text">
                                    Accurate responses based on the Germane Media LLC
                                    Employee Policy Handbook.
                                </div>
                            </div>
                        </div>

                        <div class="feature-card">
                            <div class="feature-icon">🔐</div>
                            <div>
                                <div class="feature-title">
                                    Secure & Confidential
                                </div>
                                <div class="feature-text">
                                    Conversations are associated with your
                                    authenticated company account.
                                </div>
                            </div>
                        </div>

                        <div class="feature-card">
                            <div class="feature-icon">🎧</div>
                            <div>
                                <div class="feature-title">
                                    Direct HR Support
                                </div>
                                <div class="feature-text">
                                    Escalate questions to HR or schedule a
                                    confidential 15-minute discussion.
                                </div>
                            </div>
                        </div>

                        <div class="feature-card">
                            <div class="feature-icon">👥</div>
                            <div>
                                <div class="feature-title">
                                    For Employees Only
                                </div>
                                <div class="feature-text">
                                    This portal is restricted to Germane Media LLC
                                    company accounts.
                                </div>
                            </div>
                        </div>

                    </div>

                    <div class="wave-decoration"></div>

                    <div class="login-footer login-footer-left">
                        🛡️ Secure • Private • Trusted
                    </div>

                </div>
                """
            ),
            unsafe_allow_html=True
        )

    # --------------------------------------------------------
    # RIGHT LOGIN CARD
    # --------------------------------------------------------

    with right_col:

        with st.container(border=True):

            st.markdown(
                textwrap.dedent(
                    """
                    <div class="login-lock">🔒</div>

                    <div class="welcome-title">
                        Welcome Back!
                    </div>

                    <div class="welcome-subtitle">
                        Sign in to access the GM Policy Assistant
                    </div>

                    <div class="restricted-box">
                        <div class="restricted-icon">🔐</div>
                        <div class="restricted-text">
                            This portal is restricted to active
                            Germane Media LLC employees.
                        </div>
                    </div>

                    <div class="signin-heading">
                        Sign in with your company account
                    </div>
                    """
                ),
                unsafe_allow_html=True
            )

            if st.button(
                "🔐  Sign in with Google",
                type="primary",
                width="stretch",
                key="google_login_button"
            ):
                st.login()

            st.markdown(
                textwrap.dedent(
                    """
                    <div class="google-note">
                        🏢 &nbsp;
                        Please use your official
                        <strong>@thegermanemedia.com</strong>
                        Google Workspace account.

                        <br><br>

                        Your policy conversations are associated
                        with your authenticated company account.
                    </div>

                    <div class="protected-text">
                        🛡️ Protected by Google Workspace Authentication
                    </div>

                    <div class="login-footer">
                        🔒 Secure • Private • Trusted
                        &nbsp;&nbsp; | &nbsp;&nbsp;
                        © 2026 Germane Media LLC
                        &nbsp;&nbsp; | &nbsp;&nbsp;
                        Internal Use Only
                    </div>
                    """
                ),
                unsafe_allow_html=True
            )

    st.stop()


# ============================================================
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
    getattr(st.user, "name", None)
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

    if st.button("🚪 Sign Out"):

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


if "hr_notified" not in st.session_state:

    st.session_state.hr_notified = False


# ============================================================
# PROCESS QUESTION
# ============================================================

def process_question(question):

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question
        }
    )

    try:

        response = query_policy_ai(
            question,
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

    except Exception as e:

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": str(e)
            }
        )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        f"### 👤 {st.session_state.emp_name}"
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
        "### 📚 Company Policy Categories"
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

            question = (
                f"Summarize the key points of the "
                f"{cat}."
            )

            with st.spinner(
                "Searching Policy Handbook..."
            ):

                process_question(question)

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
# MAIN COLUMNS
# ============================================================

col_main, col_right = st.columns(
    [3, 1.2]
)


# ============================================================
# MAIN CHAT
# ============================================================

with col_main:

    st.markdown(
        textwrap.dedent("""
        <div class="app-brand-title">
            GM Policy Assistant
        </div>

        <div class="app-brand-sub">
            Ask questions, verify rules, and connect
            with HR when you need additional support.
        </div>

        """),
        unsafe_allow_html=True
    )


    st.markdown(
        textwrap.dedent("""
        <div class="privacy-notice">

            🔒 <strong>Private HR Conversation:</strong>

            Your chat session is associated with your
            authenticated employee account.

            HR may access transcripts for support and
            policy administration.

        </div>

        """),
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

            if message["role"] == "assistant":

                col_res, col_unres, _ = st.columns(
                    [1, 1, 3]
                )

                with col_res:

                    if st.button(
                        "👍 Resolved",
                        key=f"resolved_{idx}"
                    ):

                        st.toast(
                            "Glad this helped resolve your query!"
                        )

                with col_unres:

                    if st.button(
                        "👎 Need Help",
                        key=f"need_help_{idx}"
                    ):

                        st.session_state.unsatisfied_msg_idx = idx

                        st.rerun()


                if (
                    st.session_state.unsatisfied_msg_idx
                    == idx
                ):

                    st.markdown(
                        textwrap.dedent("""
                        <div class="escalation-box">

                            <strong>
                                We're sorry we couldn't fully
                                resolve your question.
                            </strong>

                            <br><br>

                            You can contact HR directly or
                            schedule a confidential
                            15-minute discussion.

                        </div>

                        """),
                        unsafe_allow_html=True
                    )

                    col_email, col_calendar = st.columns(
                        [1, 1]
                    )

                    with col_email:

                        if st.button(
                            "📧 Send to HR",
                            key=f"send_hr_{idx}",
                            width="stretch"
                        ):

                            success, message = (
                                send_transcript_to_hr()
                            )

                            if success:

                                st.session_state.hr_notified = True

                                st.success(
                                    "Your conversation has been "
                                    "sent to HR successfully."
                                )

                            else:

                                st.error(message)


                    with col_calendar:

                        st.link_button(
                            "📅 Schedule HR Call",
                            HR_BOOKING_URL,
                            width="stretch"
                        )


    # ========================================================
    # HR NOTIFICATION
    # ========================================================

    if st.session_state.hr_notified:

        st.success(
            "✅ HR has been notified.\n\n"
            "Your conversation transcript has been "
            "sent to HR. You can also schedule a "
            "confidential discussion if required."
        )


    # ========================================================
    # CHAT INPUT
    # ========================================================

    user_query = st.chat_input(
        "Ask a policy question "
        "(e.g., 'How many leaves do I get per month?')..."
    )


    if user_query:

        with st.spinner(
            "Searching Germane Media Policy Handbook..."
        ):

            process_question(user_query)

        st.rerun()


# ============================================================
# RIGHT PANEL
# ============================================================

with col_right:

    st.markdown(
        "### 📅 Schedule HR Discussion"
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
        "Google Calendar will show only available "
        "appointment slots. A Google Meet link will "
        "be provided after booking."
    )


    st.divider()


    st.markdown(
        "### 💬 Need immediate help?"
    )


    st.link_button(
        "💬 Contact HR on Google Chat",
        DIRECT_GOOGLE_CHAT_HR,
        width="stretch"
    )


    st.divider()


    st.markdown(
        "### 💡 Suggested Questions"
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

            with st.spinner(
                "Searching Policy Handbook..."
            ):

                process_question(q)

            st.rerun()
