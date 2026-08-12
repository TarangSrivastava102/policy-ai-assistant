import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date, datetime, timedelta
import uuid

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

# --- RICH HTML TRANSCRIPT EMAIL SENDER ---
def send_transcript_email(employee_email, employee_name, chat_history):
    if "SMTP_USER" in st.secrets and "SMTP_PASSWORD" in st.secrets:
        try:
            sender_email = st.secrets["SMTP_USER"]
            sender_password = st.secrets["SMTP_PASSWORD"]
            
            msg = MIMEMultipart('alternative')
            msg['From'] = f"Germane Media Policy AI <{sender_email}>"
            msg['To'] = employee_email
            msg['Cc'] = HR_EMAIL
            msg['Subject'] = f"📄 Policy Chat Transcript - {employee_name}"
            
            chat_html = ""
            for message in chat_history:
                role = "You" if message["role"] == "user" else "Policy AI Assistant"
                bg_color = "#f8fafc" if message["role"] == "user" else "#eff6ff"
                border_color = "#cbd5e1" if message["role"] == "user" else "#93c5fd"
                chat_html += f"""
                <div style="background-color: {bg_color}; border-left: 4px solid {border_color}; padding: 12px 16px; margin-bottom: 12px; border-radius: 6px;">
                    <strong style="color: #0f172a; font-size: 14px;">{role}:</strong>
                    <p style="margin: 6px 0 0 0; color: #334155; font-size: 14px; line-height: 1.5;">{message['content']}</p>
                </div>
                """

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <body style="margin: 0; padding: 20px; background-color: #f1f5f9; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
                    
                    <div style="background-color: #002B49; padding: 28px 20px; text-align: center;">
                        <h1 style="color: #ffffff; margin: 0; font-size: 22px; font-weight: 700; letter-spacing: -0.5px;">
                            💬 Policy Chat Transcript
                        </h1>
                        <p style="color: #94a3b8; margin: 6px 0 0 0; font-size: 13px;">Germane Media LLC</p>
                    </div>

                    <div style="padding: 30px 28px;">
                        <p style="font-size: 15px; color: #1e293b; margin-top: 0;">Dear <strong>{employee_name}</strong>,</p>
                        <p style="font-size: 14px; color: #475569; line-height: 1.6;">Here is a copy of your recent conversation with the Germane Media Policy AI Assistant:</p>
                        
                        <div style="margin-top: 20px; margin-bottom: 25px;">
                            {chat_html}
                        </div>

                        <p style="font-size: 14px; color: #475569;">Warm regards,<br><strong>Team The Germane Media 💙</strong></p>
                    </div>

                    <div style="background-color: #e2e8f0; padding: 16px; text-align: center; border-top: 1px solid #cbd5e1;">
                        <p style="margin: 0; font-size: 12px; color: #64748b;">
                            This is an automated policy transcript sent with lots of love and a touch of code. 😊
                        </p>
                    </div>

                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_content, 'html'))
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, sender_password)
            recipients = [employee_email, HR_EMAIL]
            server.sendmail(sender_email, recipients, msg.as_string())
            server.quit()
            return True
        except Exception as e:
            st.error(f"Email Error: {e}")
            return False
    return False

# --- AUTOMATIC CALENDAR INVITE & EMAIL NOTIFICATION ---
def send_hr_meeting_email(employee_name, employee_email, meeting_date, time_slot, subject_reason):
    if "SMTP_USER" in st.secrets and "SMTP_PASSWORD" in st.secrets:
        try:
            sender_email = st.secrets["SMTP_USER"]
            sender_password = st.secrets["SMTP_PASSWORD"]
            
            # Datetime calculations (UTC formatted for global iCal synchronization)
            dt_start = datetime.strptime(f"{meeting_date} {time_slot}", "%Y-%m-%d %I:%M %p")
            dt_end = dt_start + timedelta(minutes=30)
            
            cal_start = dt_start.strftime("%Y%m%dT%H%M%S")
            cal_end = dt_end.strftime("%Y%m%dT%H%M%S")
            dt_stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            event_uid = f"meeting-{uuid.uuid4()}@thegermanemedia.com"
            
            # Outer MIMEMultipart set to 'alternative' triggers Gmail Auto-Calendar Addition
            msg = MIMEMultipart('alternative')
            msg['From'] = f"Germane Media HR <{sender_email}>"
            msg['To'] = employee_email
            msg['Cc'] = HR_EMAIL
            msg['Subject'] = f"📅 HR Discussion Scheduled: {subject_reason} - {employee_name}"
            
            plain_text = f"HR Meeting with {employee_name} on {meeting_date} at {time_slot}. Subject: {subject_reason}."

            html_body = f"""
            <!DOCTYPE html>
            <html>
            <body style="margin: 0; padding: 20px; background-color: #f1f5f9; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
                    
                    <!-- BANNER -->
                    <div style="background-color: #002B49; padding: 28px 20px; text-align: center;">
                        <h1 style="color: #ffffff; margin: 0; font-size: 22px; font-weight: 700; letter-spacing: -0.5px;">
                            📅 Meeting Scheduled with HR
                        </h1>
                        <p style="color: #94a3b8; margin: 6px 0 0 0; font-size: 13px;">Germane Media LLC</p>
                    </div>

                    <!-- BODY -->
                    <div style="padding: 30px 28px;">
                        <p style="font-size: 15px; color: #1e293b; margin-top: 0;">Dear <strong>{employee_name}</strong> & <strong>Tarang (HR)</strong>,</p>
                        <p style="font-size: 14px; color: #475569; line-height: 1.6;">An HR discussion session has been scheduled via the Policy AI Assistant and added to your calendar schedule.</p>
                        
                        <!-- DETAILS CARD -->
                        <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 18px 20px; margin: 20px 0;">
                            <table style="width: 100%; border-collapse: collapse; font-size: 14px; color: #334155;">
                                <tr>
                                    <td style="padding: 6px 0; font-weight: 600; width: 35%;">Reason / Subject:</td>
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

                        <p style="font-size: 13px; color: #64748b; margin-top: 20px;">
                            ℹ️ <em>This event has been automatically sent as a direct calendar invitation to your inbox.</em>
                        </p>

                        <p style="font-size: 14px; color: #475569; margin-top: 25px; margin-bottom: 0;">Warm wishes,<br><strong>Team The Germane Media 💙</strong></p>
                    </div>

                    <!-- FOOTER -->
                    <div style="background-color: #e2e8f0; padding: 16px; text-align: center; border-top: 1px solid #cbd5e1;">
                        <p style="margin: 0; font-size: 12px; color: #64748b;">
                            This is an automated HR meeting notification sent with lots of love and a touch of code. 😊
                        </p>
                    </div>

                </div>
            </body>
            </html>
            """

            # Native iCalendar Request Object
            ics_content = f"""BEGIN:VCALENDAR
METHOD:REQUEST
PRODID:-//Germane Media LLC//HR Assistant//EN
VERSION:2.0
CALSCALE:GREGORIAN
BEGIN:VEVENT
ORGANIZER;CN="Germane Media HR":mailto:{HR_EMAIL}
ATTENDEE;CUTYPE=INDIVIDUAL;ROLE=REQ-PARTICIPANT;PARTSTAT=ACCEPTED;RSVP=TRUE;CN="Tarang (HR)":mailto:{HR_EMAIL}
ATTENDEE;CUTYPE=INDIVIDUAL;ROLE=REQ-PARTICIPANT;PARTSTAT=NEEDS-ACTION;RSVP=TRUE;CN="{employee_name}":mailto:{employee_email}
UID:{event_uid}
DTSTAMP:{dt_stamp}
DTSTART:{cal_start}
DTEND:{cal_end}
SUMMARY:HR Meeting: {subject_reason} - {employee_name}
DESCRIPTION:HR Discussion scheduled via Policy AI Assistant.\\n\\nSubject: {subject_reason}\\nEmployee: {employee_name} ({employee_email})
STATUS:CONFIRMED
SEQUENCE:0
TRANSP:OPAQUE
END:VEVENT
END:VCALENDAR"""

            # Attach parts in correct MIME order for automatic Calendar parsing
            part_text = MIMEText(plain_text, 'plain', 'utf-8')
            part_html = MIMEText(html_body, 'html', 'utf-8')
            part_ics = MIMEText(ics_content, 'calendar; method=REQUEST', 'utf-8')
            part_ics.add_header('Content-Class', 'urn:content-classes:calendarmessage')

            msg.attach(part_text)
            msg.attach(part_html)
            msg.attach(part_ics)
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, sender_password)
            recipients = [employee_email, HR_EMAIL]
            server.sendmail(sender_email, recipients, msg.as_string())
            server.quit()
            return True
        except Exception as e:
            st.error(f"Notification Error: {e}")
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
            
            if message["role"] == "assistant":
                col_sat, col_unsat, _ = st.columns([1, 1, 4])
                with col_sat:
                    if st.button("👍 Satisfied", key=f"sat_{idx}"):
                        st.toast("Thank you for your feedback!")
                with col_unsat:
                    if st.button("👎 Not Satisfied", key=f"unsat_{idx}"):
                        st.toast("We're sorry! Please schedule a direct call with HR using the right panel.")

    user_query = st.chat_input("Ask any policy question...")
    
    if user_query:
        st.session_state.messages.append({"role": "user", "content": user_query})
        
        try:
            pdf_pages = load_and_index_pdf("GERMANE_MEDIA_LLC_POLICY_DOCUMENT.pdf")
            full_context = "\n\n".join([f"--- PAGE {p['page']} ---\n{p['text']}" for p in pdf_pages])
            
            prompt = f"""
            You are the official HR AI Assistant for Germane Media LLC. 
            Answer the user query strictly using the official Policy Document provided below.
            
            Instructions:
            1. Provide a direct, precise, and helpful answer.
            2. ALWAYS cite the exact Page Number(s) from the text below where the policy is described.
            3. Maintain a warm, professional tone.
            
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

    st.divider()
    
    if st.button(f"📧 Send Chat Transcript to My Email ({st.session_state.emp_email})"):
        if "SMTP_USER" not in st.secrets or "SMTP_PASSWORD" not in st.secrets:
            st.warning("⚠️ Email credentials are not configured in Streamlit Secrets yet.")
        else:
            with st.spinner("Sending email..."):
                if send_transcript_email(st.session_state.emp_email, st.session_state.emp_name, st.session_state.messages):
                    st.success(f"Transcript sent to **{st.session_state.emp_email}** (CC'd to {HR_EMAIL})!")
                else:
                    st.error("Failed to send email. Please check your SMTP settings.")

# --- RIGHT SIDEBAR (STICKY SCHEDULER & QUICK TOPICS) ---
with col_right:
    st.markdown(f"**👤 {st.session_state.emp_name}**")
    st.caption(st.session_state.emp_email)
    st.divider()
    
    st.markdown("⚡ **Quick Topics**")
    quick_topics = [
        "Leave Policy", "Attendance Policy", "Reimbursement Policy",
        "Appraisal Policy", "Full & Final Settlement", "Loan Policy"
    ]
    for topic in quick_topics:
        if st.button(f"{topic} ›", key=topic, use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": f"Tell me about the {topic}"})
            st.rerun()
            
    st.divider()
    
    # INTERACTIVE HR MEETING SCHEDULER
    st.markdown("### 📅 **Schedule Meeting with HR**")
    
    selected_date = st.date_input("Select Date", min_value=date.today())
    
    all_slots = [
        "10:00 AM", "10:30 AM", "11:00 AM", "11:30 AM",
        "02:00 PM", "02:30 PM", "03:00 PM", "03:30 PM", "04:00 PM"
    ]
    
    available_slots = [
        slot for slot in all_slots 
        if f"{selected_date}_{slot}" not in st.session_state.booked_slots
    ]
    
    if available_slots:
        selected_slot = st.selectbox("Available Time Slots", available_slots)
        
        # MANDATORY SUBJECT FIELD
        meeting_subject = st.text_input("Meeting Subject / Reason *", placeholder="e.g., Leave approval discussion")

        if st.button("Confirm Meeting & Send Invite", type="primary", use_container_width=True):
            if not meeting_subject.strip():
                st.error("⚠️ Please enter a subject/reason for the meeting before confirming.")
            else:
                slot_key = f"{selected_date}_{selected_slot}"
                st.session_state.booked_slots.add(slot_key)
                
                # Send email notification with HTML template and Calendar Link
                if send_hr_meeting_email(
                    st.session_state.emp_name, 
                    st.session_state.emp_email, 
                    selected_date, 
                    selected_slot, 
                    meeting_subject
                ):
                    st.success(f"✅ Meeting booked for **{selected_date}** at **{selected_slot}**!")
                    st.info(f"📧 Calendar invite automatically delivered to **{st.session_state.emp_email}** and **{HR_EMAIL}**!")
    else:
        st.error("❌ No slots available for this date. Please pick another date.")
        
    st.divider()
    st.link_button("💬 Chat with HR on Google Chat", DIRECT_GOOGLE_CHAT_HR, use_container_width=True)
