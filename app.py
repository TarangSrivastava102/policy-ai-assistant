import streamlit as st
from google import genai
from pypdf import PdfReader
import smtplib
from email.message import EmailMessage
from html import escape
from pathlib import Path


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
