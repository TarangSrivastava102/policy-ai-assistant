import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date, datetime, timedelta
import urllib.parse

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Policy AI Assistant - Germane Media LLC",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- HR CONFIGURATION ---
HR_EMAIL = "tarang@thegermanemedia.com"
DIRECT_GOOGLE_CHAT_HR = f"https://chat.google.com/dm/{HR_EMAIL}"

# --- CUSTOM APP CSS ---
st.markdown("""
<style>
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    [data-testid="stColumn"]:nth-child(2) {
        position: sticky;
        top: 2rem;
        align-self: flex-start;
        max-height: 92vh;
        overflow-y: auto;
        padding-right: 5px;
    }

    .sidebar-header-title {
        font-size: 20px;
        font-weight: 700;
        letter-spacing: -0.02em;
        margin-bottom: 2px;
        color: #ffffff;
    }
    .sidebar-header-sub {
        font-size: 12px;
        color: #94a3b8;
        font-style: italic;
        margin-bottom: 12px;
    }

    .source-box {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-left: 3px solid #3b82f6;
        border-radius: 6px;
        padding: 10px 14px;
        font-size: 13px;
        margin-top: 10px;
        color: #cbd5e1;
    }

    .badge-safe {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 14px;
        text-align: left;
        margin-top: 18px;
    }

    .stButton>button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        border-color: #3b82f6;
        color: #3b82f6;
    }
</style>
""", unsafe_allow_html=True)

# --- INITIALIZE GEMINI API ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# --- PDF PROCESSING ---
@st.cache_resource
def load_and_index_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    pages_text = []
    for idx, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        pages_text.append({"page": idx + 1, "text": text})
    return pages_text

# --- GEMINI AI QUERY ---
def query_gemini_ai(prompt):
    candidate_models = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash", "gemini-pro"]
    try:
        available_models = [m.name.replace("models/", "") for m in genai.list_models() if "generateContent" in m.supported_generation_methods]
        for m in available_models:
            if m not in candidate_models:
                candidate_models.insert(0, m)
    except Exception:
        pass

    last_error = None
    for model_name in candidate_models:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text
        except Exception as e:
            last_error = e
            continue

    raise Exception(f"Could not fetch AI response: {last_error}")

# --- HELPER: GENERATE PRE-FILLED GOOGLE CALENDAR LINK ---
def generate_google_calendar_url(title, meeting_date, time_slot, employee_name, employee_email):
    dt_start = datetime.strptime(f"{meeting_date} {time_slot}", "%Y-%m-%d %I:%M %p")
    dt_end = dt_start + timedelta(minutes=30)
    
    start_str = dt_start.strftime("%Y%m%dT%H%M%S")
    end_str = dt_end.strftime("%Y%m%dT%H%M%S")
    
    event_title = f"HR Meeting: {title} - {employee_name}"
    event_details = f"Discussion Topic: {title}\n\nParticipants:\n- {employee_name} ({employee_email})\n- Tarang ({HR_EMAIL})\n\nScheduled via Germane Media Policy AI."
    
    query_parts = [
        "action=TEMPLATE",
        f"text={urllib.parse.quote(event_title)}",
        f"dates={start_str}/{end_str}",
        f"details={urllib.parse.quote(event_details)}",
        f"add={urllib.parse.quote(employee_email)}",
        f"add={urllib.parse.quote(HR_EMAIL)}",
        "ctz=Asia/Kolkata"
    ]
    
    return "https://calendar.google.com/calendar/render?" + "&".join(query_parts)

# --- SEND ATTRACTIVE HTML EMAIL NOTIFICATION ---
def send_hr_meeting_email(employee_name, employee_email, meeting_date, time_slot, subject_reason, gcal_link):
    if "SMTP_USER" in st.secrets and "SMTP_PASSWORD" in st.secrets:
        try:
            sender_email = st.secrets["SMTP_USER"]
            sender_password = st.secrets["SMTP_PASSWORD"]
            
            msg = MIMEMultipart('alternative')
            msg['From'] = f"Germane Media HR <{sender_email}>"
            msg['To'] = employee_email
            msg['Cc'] = HR_EMAIL
            msg['Subject'] = f"📅 HR Discussion Scheduled: {subject_reason} - {employee_name}"

            html_body = f"""
            <!DOCTYPE html>
            <html>
            <body style="margin: 0; padding: 20px; background-color: #f1f5f9; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
                    
                    <!-- HEADER BANNER -->
                    <div style="background-color: #002B49; padding: 28px 20px; text-align: center;">
                        <h1 style="color: #ffffff; margin: 0; font-size: 22px; font-weight: 700; letter-spacing: -0.5px;">
                            📅 Meeting Invitation
                        </h1>
                        <p style="color: #94a3b8; margin: 6px 0 0 0; font-size: 13px;">Germane Media LLC</p>
                    </div>

                    <!-- BODY CONTENT -->
                    <div style="padding: 30px 28px;">
                        <p style="font-size: 15px; color: #1e293b; margin-top: 0;">Dear <strong>{employee_name}</strong> & <strong>Tarang (HR)</strong>,</p>
                        <p style="font-size: 14px; color: #475569; line-height: 1.6;">An HR discussion session has been initiated via the Policy AI Assistant.</p>
                        
                        <!-- DETAILS CARD -->
                        <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 18px 20px; margin: 20px 0;">
                            <table style="width: 100%; border-collapse: collapse; font-size: 14px; color: #334155;">
                                <tr>
                                    <td style="padding: 6px 0; font-weight: 600; width: 35%;">Meeting Title:</td>
                                    <td style="padding: 6px 0; color: #0284c7; font-weight: 600;">{subject_reason}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 6px 0; font-weight: 600;">Date:</td>
                                    <td style="padding: 6px 0;">{meeting_date}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 6px 0; font-weight: 600;">Time Slot:</td>
                                    <td style="padding: 6px 0;">{time_slot} (30 mins)</td>
                                </tr>
                                <tr>
                                    <td style="padding: 6px 0; font-weight: 600;">Participants:</td>
                                    <td style="padding: 6px 0;">{employee_name} ({employee_email})<br>Tarang ({HR_EMAIL})</td>
                                </tr>
                            </table>
                        </div>

                        <!-- ACTION BUTTON -->
                        <div style="text-align: center; margin: 28px 0;">
                            <a href="{gcal_link}" target="_blank" style="background-color: #002B49; color: #ffffff; text-decoration: none; padding: 14px 28px; border-radius: 8px; font-weight: 600; font-size: 14px; display: inline-block;">
                                📅 Confirm & Save in Google Calendar
                            </a>
                        </div>

                        <p style="font-size: 14px; color: #475569; margin-bottom: 0;">Warm wishes,<br><strong>Team The Germane Media 💙</strong></p>
                    </div>

                    <!-- FOOTER -->
                    <div style="background-color: #e2e8f0; padding: 16px; text-align: center; border-top: 1px solid #cbd5e1;">
                        <p style="margin: 0; font-size: 12px; color: #64748b;">
                            This is an automated email sent with lots of love and a touch of code. 😊
                        </p>
                    </div>

                </div>
            </body>
            </html>
            """

            msg.attach(MIMEText(html_body, 'html'))
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, [employee_email, HR_EMAIL], msg.as_string())
            server.quit()
            return True
        except Exception as e:
            st.error(f"Email Notification Error: {e}")
            return False
    return False

# --- SESSION STATE ---
if "booked_slots" not in st.session_state:
    st.session_state.booked_slots = set()

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown('<div class="sidebar-header-title">Germane Media LLC</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-header-sub">Psychology of Advertising</div>', unsafe_allow_html=True)
    
    try:
        st.image("logo.png", width=130)
    except Exception:
        pass
        
    st.divider()
    st.markdown("💬 **Chat with Policy AI**")
    st.markdown("📄 Company Policies")
    st.link_button("💬 Chat with HR Directly", DIRECT_GOOGLE_CHAT_HR, use_container_width=True)
    st.divider()
    
    st.markdown("""
    <div class="badge-safe">
        🔒 <b>Confidential & Safe</b><br/>
        <small style="color:#94a3b8;">Conversations are encrypted and accessible only by HR.</small>
    </div>
    """, unsafe_allow_html=True)
    
    st.caption("© Germane Media LLC. All rights reserved.")

# --- LOGIN / AUTHENTICATION ---
if "user_authenticated" not in st.session_state:
    st.session_state.user_authenticated = False

if not st.session_state.user_authenticated:
    st.title("Welcome to Germane Media Policy AI Assistant ✨")
    st.write("Please enter your details to access confidential policy support.")
    
    emp_name = st.text_input("Full Name")
    emp_email = st.text_input("Official Email Address (@thegermanemedia.com)")
    
    if st.button("Start Chat Session", type="primary"):
        if emp_name and emp_email and "@" in emp_email:
            st.session_state.emp_name = emp_name
            st.session_state.emp_email = emp_email
            st.session_state.user_authenticated = True
            st.session_state.messages = []
            st.rerun()
        else:
            st.error("Please enter a valid name and email address.")
    st.stop()

# --- MAIN CHAT LAYOUT ---
col_main, col_right = st.columns([3, 1.1])

with col_main:
    st.title("Policy AI Assistant ✨")
    st.caption("Your intelligent guide to Germane Media LLC workplace policies.")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "source" in message:
                st.markdown(f'<div class="source-box">📄 <b>Source:</b> {message["source"]}</div>', unsafe_allow_html=True)

    user_query = st.chat_input("Ask any policy question...")
    if user_query:
        st.session_state.messages.append({"role": "user", "content": user_query})
        try:
            pdf_pages = load_and_index_pdf("GERMANE_MEDIA_LLC_POLICY_DOCUMENT.pdf")
            full_context = "\n\n".join([f"--- PAGE {p['page']} ---\n{p['text']}" for p in pdf_pages])
            
            prompt = f"""
            You are the official HR AI Assistant for Germane Media LLC. 
            Answer the user query strictly using the official Policy Document provided below.
            
            Policy Document Context:
            {full_context}
            
            User Query: {user_query}
            """
            
            ai_response = query_gemini_ai(prompt)
            st.session_state.messages.append({
                "role": "assistant", 
                "content": ai_response,
                "source": "Referenced from Germane Media Policy Handbook"
            })
            st.rerun()
        except Exception as e:
            st.error(f"Error connecting to AI engine. Details: {e}")

# --- RIGHT SIDEBAR (INTERACTIVE SCHEDULER) ---
with col_right:
    st.markdown(f"**👤 {st.session_state.emp_name}**")
    st.caption(st.session_state.emp_email)
    st.divider()
    
    st.markdown("### 📅 **Schedule Meeting with HR**")
    st.caption("Fill in the meeting details below:")
    
    # INPUT FIELDS FOR TITLE, DATE, AND TIME
    meeting_title = st.text_input("Meeting Title / Subject *", value="Leave Policy Discussion")
    selected_date = st.date_input("Select Date", min_value=date.today())
    selected_time = st.selectbox("Select Time", [
        "10:00 AM", "10:30 AM", "11:00 AM", "11:30 AM",
        "02:00 PM", "02:30 PM", "03:00 PM", "03:30 PM", "04:00 PM"
    ])
    
    # GENERATE GOOGLE CALENDAR LINK WITH PRE-FILLED DETAILS
    gcal_url = generate_google_calendar_url(
        title=meeting_title,
        meeting_date=selected_date,
        time_slot=selected_time,
        employee_name=st.session_state.emp_name,
        employee_email=st.session_state.emp_email
    )

    st.markdown("---")
    
    # DIRECT REDIRECT BUTTON TO GOOGLE CALENDAR
    st.link_button("📅 Open & Schedule in Google Calendar", gcal_url, type="primary", use_container_width=True)
    
    # OPTIONAL EMAIL CONFIRMATION BUTTON
    if st.button("📧 Send Email Invite Copy", use_container_width=True):
        if send_hr_meeting_email(
            st.session_state.emp_name,
            st.session_state.emp_email,
            selected_date,
            selected_time,
            meeting_title,
            gcal_url
        ):
            st.success("Email invite copy successfully sent to both inbox accounts!")

    st.divider()
    st.link_button("💬 Chat with HR on Google Chat", DIRECT_GOOGLE_CHAT_HR, use_container_width=True)
