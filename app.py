import streamlit as st
from google import genai
from pypdf import PdfReader
import smtplib
from email.message import EmailMessage
from html import escape


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
HR_BOOKING_URL = "https://calendar.app.google/wjkBcfyeAgKqCRUVA"

# Google Chat
DIRECT_GOOGLE_CHAT_HR = (
    "https://chat.google.com/dm/tarang@thegermanemedia.com"
)


# ============================================================
# CORPORATE UI
# ============================================================

st.markdown(
    """
    <style>

    /* ======================================================
       GLOBAL
       ====================================================== */

    @import url(
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
    );

    html,
    body,
    [class*="css"] {
        font-family: 'Inter',
        -apple-system,
        BlinkMacSystemFont,
        sans-serif;
    }

    .stApp {
        background:
            radial-gradient(
                circle at 10% 20%,
                rgba(99, 102, 241, 0.08),
                transparent 35%
            ),
            radial-gradient(
                circle at 90% 80%,
                rgba(124, 58, 237, 0.08),
                transparent 35%
            ),
            #f8f9ff;
    }


    /* ======================================================
       LOGIN PAGE
       ====================================================== */

    .login-wrapper {
        min-height: 88vh;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 35px 20px;
    }

    .login-container {
        width: 100%;
        max-width: 1280px;
        min-height: 700px;
        background: rgba(255,255,255,0.96);
        border: 1px solid #e7e8f5;
        border-radius: 28px;
        overflow: hidden;
        box-shadow:
            0 25px 70px rgba(40, 30, 90, 0.12);
        display: grid;
        grid-template-columns: 1.05fr 0.95fr;
    }


    /* ======================================================
       LEFT BRANDING PANEL
       ====================================================== */

    .brand-panel {
        position: relative;
        padding: 58px 58px 40px 58px;
        background:
            radial-gradient(
                circle at 20% 10%,
                rgba(124, 58, 237, 0.13),
                transparent 35%
            ),
            linear-gradient(
                145deg,
                #ffffff 0%,
                #fafaff 48%,
                #f2efff 100%
            );
        overflow: hidden;
    }

    .brand-header {
        display: flex;
        align-items: center;
        gap: 18px;
        margin-bottom: 48px;
    }

    .gm-logo {
        width: 86px;
        height: 86px;
        flex-shrink: 0;
    }

    .brand-company {
        font-size: 38px;
        line-height: 1.05;
        font-weight: 800;
        color: #17223b;
        letter-spacing: -1.5px;
    }

    .brand-product {
        margin-top: 10px;
        font-size: 20px;
        font-weight: 700;
        color: #6547e8;
    }

    .brand-heading {
        font-size: 29px;
        line-height: 1.25;
        font-weight: 800;
        color: #17223b;
        margin-bottom: 16px;
        max-width: 560px;
    }

    .brand-description {
        font-size: 17px;
        line-height: 1.75;
        color: #52617d;
        max-width: 600px;
        margin-bottom: 40px;
    }


    /* ======================================================
       FEATURE CARDS
       ====================================================== */

    .features-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 22px;
        max-width: 650px;
    }

    .feature-card {
        display: flex;
        gap: 15px;
        padding: 19px;
        border-radius: 16px;
        background: rgba(255,255,255,0.72);
        border: 1px solid rgba(124,58,237,0.08);
    }

    .feature-icon {
        width: 48px;
        height: 48px;
        min-width: 48px;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #f0ecff;
        color: #6246e8;
        font-size: 24px;
    }

    .feature-title {
        font-size: 16px;
        font-weight: 800;
        color: #17223b;
        margin-bottom: 6px;
    }

    .feature-text {
        font-size: 13px;
        line-height: 1.6;
        color: #64728d;
    }


    /* ======================================================
       DECORATIVE WAVE
       ====================================================== */

    .wave-decoration {
        position: absolute;
        left: -20px;
        right: -20px;
        bottom: -15px;
        height: 150px;
        opacity: 0.35;
        pointer-events: none;
    }


    /* ======================================================
       RIGHT LOGIN PANEL
       ====================================================== */

    .auth-panel {
        background: #ffffff;
        padding: 45px 55px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    .auth-icon {
        width: 82px;
        height: 82px;
        border-radius: 50%;
        background: #f0edff;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 40px;
        margin: 0 auto 22px auto;
    }

    .auth-title {
        text-align: center;
        font-size: 31px;
        font-weight: 800;
        color: #17223b;
        margin-bottom: 8px;
    }

    .auth-subtitle {
        text-align: center;
        font-size: 16px;
        color: #66738e;
        margin-bottom: 30px;
    }

    .restriction-box {
        display: flex;
        align-items: center;
        gap: 15px;
        padding: 18px 20px;
        border-radius: 13px;
        background: #f7f4ff;
        border: 1px solid #e6defe;
        margin-bottom: 30px;
    }

    .restriction-icon {
        font-size: 28px;
    }

    .restriction-text {
        color: #5941cf;
        font-size: 15px;
        line-height: 1.5;
        font-weight: 700;
    }

    .signin-label {
        text-align: center;
        font-size: 17px;
        font-weight: 700;
        color: #17223b;
        margin-bottom: 16px;
    }

    .security-box {
        display: flex;
        gap: 16px;
        padding: 22px;
        border-radius: 14px;
        background: #fafbff;
        border: 1px solid #e5e8f2;
        margin-top: 28px;
    }

    .security-icon {
        font-size: 27px;
    }

    .security-title {
        font-weight: 700;
        color: #26334f;
        font-size: 14px;
        margin-bottom: 7px;
    }

    .security-text {
        color: #64728d;
        font-size: 13px;
        line-height: 1.65;
    }

    .protected-text {
        text-align: center;
        margin-top: 28px;
        font-size: 13px;
        color: #71809d;
    }


    /* ======================================================
       LOGIN BUTTON
       ====================================================== */

    div.stButton > button[kind="primary"] {
        height: 56px;
        border-radius: 12px;
        border: none;
        background: linear-gradient(
            90deg,
            #5b3fd5,
            #7048e8
        );
        color: white;
        font-size: 16px;
        font-weight: 700;
        box-shadow:
            0 8px 20px rgba(98,70,232,0.22);
    }

    div.stButton > button[kind="primary"]:hover {
        background: linear-gradient(
            90deg,
            #5034c3,
            #633bd8
        );
        color: white;
    }


    /* ======================================================
       FOOTER
       ====================================================== */

    .login-footer {
        display: flex;
        justify-content: space-between;
        max-width: 1280px;
        margin: 18px auto 0 auto;
        padding: 0 8px;
        color: #74819a;
        font-size: 12px;
    }


    /* ======================================================
       APPLICATION UI
       ====================================================== */

    [data-testid="stColumn"]:nth-child(2) {
        position: sticky;
        top: 2rem;
        align-self: flex-start;
        max-height: 92vh;
        overflow-y: auto;
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
        padding: 10px 14px;
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

    /* ======================================================
       RESPONSIVE
       ====================================================== */

    @media (max-width: 900px) {

        .login-container {
            grid-template-columns: 1fr;
        }

        .brand-panel {
            padding: 40px 30px;
        }

        .auth-panel {
            padding: 40px 30px;
        }

        .brand-company {
            font-size: 30px;
        }

        .brand-product {
            font-size: 17px;
        }

        .features-grid {
            grid-template-columns: 1fr;
        }

        .login-footer {
            display: none;
        }
    }

    </style>
    """,
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

    for msg in conversation_history[-6:]:

        role = (
            "Employee"
            if msg["role"] == "user"
            else "Assistant"
        )

        history_context += (
            f"{role}: {msg['content']}\n"
        )

    pdf_pages = load_and_index_pdf(
        "GERMANE_MEDIA_LLC_POLICY_DOCUMENT.pdf"
    )

    full_context = "\n\n".join(
        [
            f"--- PAGE {p['page']} ---\n{p['text']}"
            for p in pdf_pages
        ]
    )

    system_prompt = f"""
You are the official GM Policy Assistant for Germane Media LLC.

Your role is to assist employees with workplace policies strictly
using the provided Germane Media LLC Employee Policy Handbook.

CRITICAL RULES:

1. ANSWER STRICTLY FROM THE POLICY TEXT BELOW.

2. IF THE QUESTION CANNOT BE ANSWERED FROM THE HANDBOOK,
DO NOT USE GENERAL KNOWLEDGE.

Respond exactly:

"I couldn't find a specific provision covering this in the Germane Media LLC Employee Policy Handbook. I recommend contacting HR directly for clarification."

3. ALWAYS APPEND EXACT PAGE CITATIONS at the end of relevant facts.

Example:

[📄 Page 12]

4. Maintain a professional, neutral and helpful corporate tone.

5. For appraisal, variable pay, or probation questions,
explicitly note management discretion where applicable.

6. Do not invent policy.

7. Do not assume information that is not contained in the handbook.

8. If the employee asks a follow-up question, use the conversation
history to understand the context.

9. The policy handbook is the only source of policy information.
Do not use internet information or general HR knowledge.

10. If multiple pages support the answer, cite all relevant pages.

POLICY HANDBOOK CONTEXT:

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
# SEND EMAIL TO HR
# ============================================================

def send_conversation_to_hr(messages, employee_name, employee_email):

    if (
        "SMTP_USER" not in st.secrets
        or "SMTP_PASSWORD" not in st.secrets
    ):
        raise Exception(
            "Email service is not configured. "
            "Please check SMTP_USER and SMTP_PASSWORD "
            "in Streamlit Secrets."
        )

    smtp_user = st.secrets["SMTP_USER"]
    smtp_password = st.secrets["SMTP_PASSWORD"]

    transcript = []

    for message in messages:

        role = (
            "EMPLOYEE"
            if message["role"] == "user"
            else "GM POLICY ASSISTANT"
        )

        transcript.append(
            f"{role}:\n{message['content']}\n"
        )

    transcript_text = "\n------------------------------\n".join(
        transcript
    )

    email = EmailMessage()

    email["Subject"] = (
        f"HR Assistance Request - {employee_name}"
    )

    email["From"] = smtp_user
    email["To"] = HR_EMAIL
    email["Reply-To"] = employee_email

    email.set_content(
        f"""
HR Assistance Request

Employee Name:
{employee_name}

Employee Email:
{employee_email}

The employee has requested HR assistance through
the GM Policy Assistant.

Conversation Transcript:

{transcript_text}

------------------------------

This email was automatically generated
by the Germane Media LLC GM Policy Assistant.
"""
    )

    with smtplib.SMTP_SSL(
        "smtp.gmail.com",
        465
    ) as server:

        server.login(
            smtp_user,
            smtp_password
        )

        server.send_message(email)


# ============================================================
# GOOGLE AUTHENTICATION
# ============================================================

if not st.user.is_logged_in:

    # --------------------------------------------------------
    # LOGIN / LANDING PAGE
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="login-wrapper">

            <div class="login-container">

                <!-- ================================
                     LEFT BRAND PANEL
                     ================================ -->

                <div class="brand-panel">

                    <div class="brand-header">

                        <!-- Inline GM Logo -->
                        <svg
                            class="gm-logo"
                            viewBox="0 0 100 100"
                            xmlns="http://www.w3.org/2000/svg"
                        >

                            <defs>

                                <linearGradient
                                    id="gmGradient"
                                    x1="0%"
                                    y1="0%"
                                    x2="100%"
                                    y2="100%"
                                >
                                    <stop
                                        offset="0%"
                                        stop-color="#4f46e5"
                                    />

                                    <stop
                                        offset="55%"
                                        stop-color="#6366f1"
                                    />

                                    <stop
                                        offset="100%"
                                        stop-color="#9333ea"
                                    />

                                </linearGradient>

                            </defs>

                            <path
                                d="M82 23
                                   C68 8 44 4 26 14
                                   C6 25 -2 49 7 68
                                   C16 88 39 98 59 91
                                   C73 87 83 77 88 65
                                   L67 65
                                   C62 74 51 79 40 76
                                   C25 72 17 58 20 43
                                   C23 28 37 19 51 21
                                   C61 22 68 27 73 34
                                   L60 47
                                   L88 47
                                   L88 19
                                   Z"
                                fill="url(#gmGradient)"
                            />

                            <path
                                d="M42 51
                                   H72
                                   V66
                                   H58
                                   V59
                                   H42
                                   Z"
                                fill="white"
                                opacity="0.95"
                            />

                        </svg>

                        <div>

                            <div class="brand-company">
                                Germane Media LLC
                            </div>

                            <div class="brand-product">
                                GM Policy Assistant • Internal HR Portal
                            </div>

                        </div>

                    </div>


                    <div class="brand-heading">
                        Your Intelligent HR Policy Companion
                    </div>

                    <div class="brand-description">
                        Get instant, accurate answers to your policy
                        questions, understand company guidelines,
                        and connect with HR for personalized support —
                        anytime, anywhere.
                    </div>


                    <div class="features-grid">

                        <div class="feature-card">

                            <div class="feature-icon">
                                📖
                            </div>

                            <div>

                                <div class="feature-title">
                                    Instant Policy Answers
                                </div>

                                <div class="feature-text">
                                    Accurate responses based on the
                                    Germane Media LLC Employee Policy
                                    Handbook.
                                </div>

                            </div>

                        </div>


                        <div class="feature-card">

                            <div class="feature-icon">
                                🔐
                            </div>

                            <div>

                                <div class="feature-title">
                                    Secure & Confidential
                                </div>

                                <div class="feature-text">
                                    Your conversations are associated
                                    with your authenticated company
                                    account.
                                </div>

                            </div>

                        </div>


                        <div class="feature-card">

                            <div class="feature-icon">
                                🎧
                            </div>

                            <div>

                                <div class="feature-title">
                                    Direct HR Support
                                </div>

                                <div class="feature-text">
                                    Escalate questions to HR or schedule
                                    a confidential 15-minute discussion.
                                </div>

                            </div>

                        </div>


                        <div class="feature-card">

                            <div class="feature-icon">
                                👥
                            </div>

                            <div>

                                <div class="feature-title">
                                    For Employees Only
                                </div>

                                <div class="feature-text">
                                    Restricted to active Germane Media
                                    LLC employees using company
                                    accounts.
                                </div>

                            </div>

                        </div>

                    </div>


                    <!-- Decorative wave -->

                    <svg
                        class="wave-decoration"
                        viewBox="0 0 1000 180"
                        preserveAspectRatio="none"
                    >

                        <path
                            d="M0 110
                               C130 40 180 150 300 100
                               S500 60 620 120
                               S820 150 1000 80"
                            fill="none"
                            stroke="#8b7cf6"
                            stroke-width="2"
                        />

                        <path
                            d="M0 130
                               C130 60 180 170 300 120
                               S500 80 620 140
                               S820 170 1000 100"
                            fill="none"
                            stroke="#a99cf8"
                            stroke-width="2"
                        />

                        <path
                            d="M0 150
                               C130 80 180 190 300 140
                               S500 100 620 160
                               S820 190 1000 120"
                            fill="none"
                            stroke="#c4bdfb"
                            stroke-width="2"
                        />

                    </svg>

                </div>


                <!-- ================================
                     RIGHT AUTH PANEL
                     ================================ -->

                <div class="auth-panel">

                    <div class="auth-icon">
                        🔒
                    </div>

                    <div class="auth-title">
                        Welcome Back!
                    </div>

                    <div class="auth-subtitle">
                        Sign in to access the GM Policy Assistant
                    </div>


                    <div class="restriction-box">

                        <div class="restriction-icon">
                            🔐
                        </div>

                        <div class="restriction-text">
                            This portal is restricted to active
                            Germane Media LLC employees.
                        </div>

                    </div>


                    <div class="signin-label">
                        Sign in with your company account
                    </div>

                """,
        unsafe_allow_html=True
    )


    # Google login button
    if st.button(
        "🔐  Sign in with Google",
        type="primary",
        width="stretch"
    ):

        st.login()


    st.markdown(
        """
                    <div class="security-box">

                        <div class="security-icon">
                            🏢
                        </div>

                        <div>

                            <div class="security-title">
                                Use your official company account
                            </div>

                            <div class="security-text">

                                Please use your official
                                <b>@thegermanemedia.com</b>
                                Google Workspace account.

                                <br><br>

                                Your policy conversations are associated
                                with your authenticated company account.

                            </div>

                        </div>

                    </div>


                    <div class="protected-text">
                        🛡️ Protected by Google Workspace Authentication
                    </div>

                </div>

            </div>

        </div>

        <div class="login-footer">

            <div>
                🛡️ Secure • Private • Trusted
            </div>

            <div>
                © 2026 Germane Media LLC • Internal Use Only
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.stop()


# ============================================================
# VERIFIED GOOGLE IDENTITY
# ============================================================

try:

    user_email = st.user.email.lower().strip()

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
            key=cat,
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

            if message["role"] == "assistant":

                col_res, col_unres, _ = st.columns(
                    [1, 1, 3]
                )

                with col_res:

                    if st.button(
                        "✅ Satisfied",
                        key=f"res_{idx}"
                    ):

                        st.toast(
                            "Thank you for your feedback!"
                        )

                with col_unres:

                    if st.button(
                        "❌ Not Satisfied",
                        key=f"unres_{idx}"
                    ):

                        st.session_state.unsatisfied_msg_idx = idx


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

                    col_email, col_calendar = st.columns(2)

                    with col_email:

                        if st.button(
                            "📧 Send to HR",
                            key=f"send_hr_{idx}",
                            width="stretch"
                        ):

                            try:

                                send_conversation_to_hr(
                                    st.session_state.messages,
                                    st.session_state.emp_name,
                                    st.session_state.emp_email
                                )

                                st.session_state.hr_notified = True

                                st.success(
                                    "Your conversation has been sent to HR successfully."
                                )

                                st.info(
                                    "✅ HR has been notified. "
                                    "Your conversation transcript has been sent to HR."
                                )

                            except Exception as e:

                                st.error(
                                    f"Unable to notify HR: {str(e)}"
                                )

                    with col_calendar:

                        st.link_button(
                            "📅 Schedule HR Call",
                            HR_BOOKING_URL,
                            width="stretch"
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
            key=q,
            width="stretch"
        ):

            st.session_state.messages.append(
                {
                    "role": "user",
                    "content": q
                }
            )

            st.rerun()
