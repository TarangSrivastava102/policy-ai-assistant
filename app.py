import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date, datetime, timedelta, timezone
import urllib.parse
from pypdf import PdfReader
from google import genai
from google.genai import types

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="GM Policy Assistant - Germane Media LLC",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CONFIGURATION CONSTANTS ---
HR_EMAIL = "tarang@thegermanemedia.com"
COMPANY_DOMAIN = "thegermanemedia.com"
DIRECT_GOOGLE_CHAT_HR = f"https://chat.google.com/dm/{HR_EMAIL}"

# --- CUSTOM CORPORATE UI CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
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
</style>
""", unsafe_allow_html=True)

# --- INITIALIZE GEMINI CLIENT (NEW google.genai SDK) ---
@st.cache_resource
def get_gemini_client():
    api_key = st.secrets.get("GEMINI_API_KEY", None)
    if api_key:
        return genai.Client(api_key=api_key)
    return None

# --- PDF PROCESSING & CACHING ---
@st.cache_resource
def load_and_index_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    pages_text = []
    for idx, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        pages_text.append({"page": idx + 1, "text": text})
    return pages_text

# --- GEMINI QUERY FUNCTION ---
def query_policy_ai(prompt, conversation_history):
    client = get_gemini_client()
    if not client:
        raise Exception("Gemini API key is not configured in Secrets.")

    pdf_pages = load_and_index_pdf("GERMANE_MEDIA_LLC_POLICY_DOCUMENT.pdf")
    full_context = "\n\n".join([f"--- PAGE {p['page']} ---\n{p['text']}" for p in pdf_pages])

    system_instruction = f"""
    You are the official GM Policy Assistant for Germane Media LLC. 
    Your role is to assist employees with workplace policies strictly using the provided Employee Policy Handbook.

    CRITICAL RULES:
    1. ANSWER STRICTLY FROM THE POLICY TEXT BELOW.
    2. IF THE QUESTION CANNOT BE ANSWERED FROM THE HANDBOOK, DO NOT USE GENERAL KNOWLEDGE. RESPOND EXACTLY:
       "I couldn't find a specific provision covering this in the Germane Media LLC Employee Policy Handbook. I recommend contacting HR directly for clarification."
    3. ALWAYS APPEND EXACT PAGE CITATIONS at the end of relevant facts (e.g., [📄 Page X]).
    4. Maintain a professional, neutral, and helpful corporate tone.

    POLICY HANDBOOK CONTEXT:
    {full_context}
    """

    # Build memory context
    messages_payload = []
    for msg in conversation_history[-6:]:
        role = "user" if msg["role"] == "user" else "model"
        messages_payload.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))
    
    messages_payload.append(types.Content(role="user", parts=[types.Part.from_text(text=prompt)]))

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=messages_payload,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.2
        )
    )
    return response.text

# --- GOOGLE CALENDAR URL GENERATOR ---
def generate_gcal_link(title, meeting_date, time_slot, employee_name, employee_email):
    dt_start = datetime.strptime(f"{meeting_date} {time_slot}", "%Y-%m-%d %I:%M %p")
    dt_end = dt_start + timedelta(minutes=30)
    
    start_str = dt_start.strftime("%Y%m%dT%H%M%S")
    end_str = dt_end.strftime("%Y%m%dT%H%M%S")
    
    event_title = f"HR Discussion: {title} - {employee_name}"
    event_details = f"Topic: {title}\n\nParticipants:\n- {employee_name} ({employee_email})\n- Tarang ({HR_EMAIL})\n\nScheduled via GM Policy Assistant."
    
    query = [
        "action=TEMPLATE",
        f"text={urllib.parse.quote(event_title)}",
        f"dates={start_str}/{end_str}",
        f"details={urllib.parse.quote(event_details)}",
        f"add={urllib.parse.quote(employee_email)}",
        f"add={urllib.parse.quote(HR_EMAIL)}",
        "ctz=Asia/Kolkata"
    ]
    return "https://calendar.google.com/calendar/render?" + "&".join(query)

# --- SESSION INITIALIZATION ---
if "user_authenticated" not in st.session_state:
    st.session_state.user_authenticated = False
if "is_hr" not in st.session_state:
    st.session_state.is_hr = False
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- AUTHENTICATION GATEWAY ---
if not st.session_state.user_authenticated:
    st.markdown('<div class="brand-title">Germane Media LLC</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-sub">GM Policy Assistant • Internal HR Portal</div>', unsafe_allow_html=True)
    
    st.info("🔒 Access restricted strictly to Germane Media LLC active employees.")
    
    emp_name = st.text_input("Full Name")
    emp_email = st.text_input("Official Company Email (@thegermanemedia.com)")
    
    if st.button("Access Policy Assistant", type="primary"):
        clean_email = emp_email.strip().lower()
        if clean_email.endswith(f"@{COMPANY_DOMAIN}") and len(emp_name.strip()) > 2:
            st.session_state.emp_name = emp_name.strip()
            st.session_state.emp_email = clean_email
            st.session_state.is_hr = (clean_email == HR_EMAIL)
            st.session_state.user_authenticated = True
            st.rerun()
        else:
            st.error(f"⚠️ Access Denied. Please provide a valid company email ending in @{COMPANY_DOMAIN}.")
    st.stop()

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown(f"**👤 {st.session_state.emp_name}**")
    st.caption(st.session_state.emp_email)
    
    if st.session_state.get("is_hr", False):
        st.success("🔑 HR Admin Mode Active")
        
    st.divider()
    
    st.markdown("📚 **Company Policy Categories**")
    categories = ["Leave Policy", "Attendance & Work Hours", "Appraisal & Revisions", "Reimbursement", "Probation & Confirmation", "Full & Final Settlement"]
    for cat in categories:
        if st.button(f"📄 {cat}", key=cat, width="stretch"):
            st.session_state.messages.append({"role": "user", "content": f"Summarize key points from {cat}."})
            st.rerun()
            
    st.divider()
    st.link_button("💬 Message HR on Google Chat", DIRECT_GOOGLE_CHAT_HR, width="stretch")
    
    if st.button("🚪 Sign Out", width="stretch"):
        st.session_state.clear()
        st.rerun()

# --- MAIN INTERFACE ---
col_main, col_right = st.columns([3, 1.2])

with col_main:
    st.markdown('<div class="brand-title">GM Policy Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-sub">Ask questions, verify rules, and schedule direct support.</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="privacy-notice">
        🔒 <b>Private HR Conversation:</b> Your chat session is confidential and isolated to your employee account. HR may access transcripts for support and policy administration.
    </div>
    """, unsafe_allow_html=True)

    # RENDER CHAT MESSAGES
    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # CHAT INPUT
    user_query = st.chat_input("Ask a policy question...")
    
    if user_query:
        st.session_state.messages.append({"role": "user", "content": user_query})
        
        with st.spinner("Searching Germane Media Policy Handbook..."):
            try:
                response = query_policy_ai(user_query, st.session_state.messages)
                full_response = response + "\n\n---\n*Notice: Answers are derived from the Germane Media LLC Policy Handbook.*"
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# --- RIGHT SIDEBAR SCHEDULER ---
with col_right:
    st.markdown("### 📅 **Schedule HR Discussion**")
    
    meeting_subject = st.text_input("Meeting Subject", value="Policy Discussion")
    selected_date = st.date_input("Date", min_value=date.today())
    selected_time = st.selectbox("Time Slot", [
        "10:00 AM", "10:30 AM", "11:00 AM", "11:30 AM",
        "02:00 PM", "02:30 PM", "03:00 PM", "03:30 PM", "04:00 PM"
    ])
    
    gcal_url = generate_gcal_link(
        title=meeting_subject,
        meeting_date=selected_date,
        time_slot=selected_time,
        employee_name=st.session_state.emp_name,
        employee_email=st.session_state.emp_email
    )
    
    st.link_button("📅 Open & Save in Google Calendar", gcal_url, type="primary", width="stretch")
