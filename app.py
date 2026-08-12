import streamlit as st
from google import genai
from pypdf import PdfReader
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape
from datetime import datetime


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

# Google Chat HR
DIRECT_GOOGLE_CHAT_HR = (
    "https://chat.google.com/dm/tarang@thegermanemedia.com"
)


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
# GEMINI API
# ============================================================

if "GEMINI_API_KEY" not in st.secrets:

    st.error(
        "Gemini API key is not configured. Please contact the administrator."
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

11. Keep answers reasonably concise and directly answer the question.

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
            f"AI Assistant is currently unavailable. "
            f"Please contact HR. Technical details: {str(e)}"
        )


# ============================================================
# EMAIL TRANSCRIPT FUNCTION
# ============================================================

def send_transcript_email(employee_email, employee_name, messages):

    # These must be stored in Streamlit Secrets.
    smtp_email = st.secrets.get("SMTP_EMAIL")
    smtp_password = st.secrets.get("SMTP_PASSWORD")

    if not smtp_email or not smtp_password:

        raise Exception(
            "Email service is not configured yet. "
            "Please contact the administrator."
        )

    if not messages:

        raise Exception(
            "There is no conversation to email."
        )

    timestamp = datetime.now().strftime(
        "%d %B %Y, %I:%M %p"
    )

    subject = (
        f"GM Policy Assistant Conversation - "
        f"{employee_name}"
    )

    # --------------------------------------------------------
    # Build readable HTML transcript
    # --------------------------------------------------------

    transcript_html = ""

    for message in messages:

        role = message.get("role", "")
        content = message.get("content", "")

        if role == "user":

            transcript_html += f"""
            <div style="
                margin-bottom:20px;
                padding:14px;
                background:#f8fafc;
                border-radius:8px;
                border-left:4px solid #64748b;
            ">
                <strong>Employee</strong><br><br>
                {escape(content).replace(chr(10), "<br>")}
            </div>
            """

        elif role == "assistant":

            transcript_html += f"""
            <div style="
                margin-bottom:20px;
                padding:14px;
                background:#eff6ff;
                border-radius:8px;
                border-left:4px solid #0284c7;
            ">
                <strong>GM Policy Assistant</strong><br><br>
                {escape(content).replace(chr(10), "<br>")}
            </div>
            """

    html_body = f"""
    <html>
    <body style="
        font-family:Arial,sans-serif;
        color:#1e293b;
        line-height:1.5;
    ">

        <h2>GM Policy Assistant - Conversation Transcript</h2>

        <p>
            <strong>Employee:</strong> {escape(employee_name)}
        </p>

        <p>
            <strong>Email:</strong> {escape(employee_email)}
        </p>

        <p>
            <strong>Date:</strong> {escape(timestamp)}
        </p>

        <hr>

        {transcript_html}

        <hr>

        <p style="font-size:12px;color:#64748b;">
            This transcript was generated by the Germane Media LLC
            Policy Assistant.
        </p>

    </body>
    </html>
    """

    # --------------------------------------------------------
    # Create email
    # --------------------------------------------------------

    msg = MIMEMultipart("alternative")

    msg["Subject"] = subject
    msg["From"] = smtp_email
    msg["To"] = employee_email
    msg["Cc"] = HR_EMAIL

    msg.attach(
        MIMEText(
            html_body,
            "html"
        )
    )

    # --------------------------------------------------------
    # Send using Gmail SMTP
    # --------------------------------------------------------

    with smtplib.SMTP(
        "smtp.gmail.com",
        587
    ) as server:

        server.starttls()

        server.login(
            smtp_email,
            smtp_password
        )

        server.send_message(msg)


# ============================================================
# GOOGLE AUTHENTICATION
# ============================================================

if not st.user.is_logged_in:

    st.markdown(
        '<div class="login-card">',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="login-title">'
        'Germane Media LLC'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="login-subtitle">'
        'GM Policy Assistant • Internal HR Portal'
        '</div>',
        unsafe_allow_html=True
    )

    st.info(
        "🔒 This portal is restricted to active "
        "Germane Media LLC employees."
    )

    st.markdown(
        "### Sign in with your company account"
    )

    if st.button(
        "🔐 Sign in with Google",
        type="primary",
        width="stretch"
    ):

        st.login()

    st.markdown(
        """
        <div class="security-note">
        Please use your official
        <b>@thegermanemedia.com</b>
        Google Workspace account.
        <br><br>
        Your policy conversations are associated with
        your authenticated company account.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        "</div>",
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


if "transcript_sent" not in st.session_state:

    st.session_state.transcript_sent = False


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


    # ========================================================
    # EMAIL TRANSCRIPT SECTION
    # ========================================================

    if st.session_state.messages:

        st.divider()

        st.markdown(
            "### 📧 Conversation Transcript"
        )

        st.caption(
            "When you're finished, you can email a copy of "
            "this conversation to yourself and HR."
        )

        if st.button(
            "📧 Email Conversation Transcript",
            type="secondary",
            width="stretch"
        ):

            with st.spinner(
                "Sending conversation transcript..."
            ):

                try:

                    send_transcript_email(
                        st.session_state.emp_email,
                        st.session_state.emp_name,
                        st.session_state.messages
                    )

                    st.session_state.transcript_sent = True

                    st.success(
                        "✅ Transcript sent successfully to "
                        f"{st.session_state.emp_email} and HR."
                    )

                except Exception as e:

                    st.error(
                        f"Unable to send the transcript. {str(e)}"
                    )


        if st.session_state.transcript_sent:

            st.info(
                "A copy of this conversation has been sent "
                "to your company email and HR."
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
