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
    page_title="GM Policy Assistant - Germane Media LLC",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CONFIGURATION CONSTANTS ---
HR_EMAIL = "tarang@thegermanemedia.com"
COMPANY_DOMAIN = "thegermanemedia.com"
DIRECT_GOOGLE_CHAT_HR = f"https://chat.google.com/dm/{HR_EMAIL}"

# --- CUSTOM CORPORATE UI CSS (Inter Font, Minimalist Layout) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Column Sticky Positioning */
    [data-testid="stColumn"]:nth-child(2) {
        position: sticky;
        top: 2rem;
        align-self: flex-start;
        max-height: 92vh;
        overflow-y: auto;
    }

    /* Header Styling */
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

    /* Source Citation Card */
    .source-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #0284c7;
        border-radius: 6px;
        padding: 10px 14px;
        font-size: 13px;
        color: #334155;
        margin-top: 10px;
    }

    /* Privacy Banner */
    .privacy-notice {
        background-color: #f1f5f9;
        border-radius: 8px;
        padding: 10px 14px;
        font-size: 12px;
        color: #475569;
        border: 1px solid #e2e8f0;
        margin-bottom: 15px;
    }

    /* Escalation Box */
    .escalation-box {
        background-color: #fef2f2;
        border: 1px solid #fecaca;
        border-radius: 8px;
        padding: 14px;
        margin-top: 10px;
        color: #991b1b;
        font-size: 13px;
    }
</style>
""", unsafe_allow_html=True)

# --- INITIALIZE GEMINI API ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# --- PDF PROCESSING & CACHING ---
@st.cache_resource
def load_and_index_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    pages_text = []
    for idx, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        pages_text.append({"page": idx + 1, "text": text})
    return pages_text

# --- GEMINI QUERY WITH STRICT REFUSAL GUARDRAILS ---
def query_policy_ai(prompt, conversation_history):
    candidate_models = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash", "gemini-pro"]
    
    # Format conversation history context
    history_context = ""
    for msg in conversation_history[-6:]:  # Maintain rolling 6-message memory
        role = "Employee" if msg["role"] == "user" else "Assistant"
        history_context += f"{role}: {msg['content']}\n"

    pdf_pages = load_and_index_pdf("GERMANE_MEDIA_LLC_POLICY_DOCUMENT.pdf")
    full_context = "\n\n".join([f"--- PAGE {p['page']} ---\n{p['text']}" for p in pdf_pages])

    system_prompt = f"""
    You are the official GM Policy Assistant for Germane Media LLC. 
    Your role is to assist employees with workplace policies strictly using the provided Employee Policy Handbook.

    CRITICAL RULES:
    1. ANSWER STRICTLY FROM THE POLICY TEXT BELOW.
    2. IF THE QUESTION CANNOT BE ANSWERED FROM THE HANDBOOK, DO NOT USE GENERAL KNOWLEDGE. RESPOND EXACTLY:
       "I couldn't find a specific provision covering this in the Germane Media LLC Employee Policy Handbook. I recommend contacting HR directly for clarification."
    3. ALWAYS APPEND EXACT PAGE CITATIONS at the end of relevant facts (e.g., [📄 Page X]).
    4. Maintain a professional, neutral, and helpful corporate tone.
    5. For appraisal, variable pay, or probation questions, explicitly note management discretion where applicable.

    POLICY HANDBOOK CONTEXT:
    {full_context}

    CONVERSATION HISTORY:
    {history_context}

    EMPLOYEE QUESTION:
    {prompt}
    """

    for model_name in candidate_models:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(system_prompt)
            if response and response.text:
                return response.text
        except Exception:
            continue

    raise Exception("AI Assistant is currently unavailable. Please contact HR.")

# --- HELPER: GOOGLE CALENDAR LINK GENERATOR ---
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
if "messages" not in st.session_state:
    st.session_state.messages = []
if "unsatisfied_msg_idx" not in st.session_state:
    st.session_state.unsatisfied_msg_idx = None

# --- AUTHENTICATION & DOMAIN VALIDATION GATEWAY ---
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

# --- SIDEBAR NAVIGATION & HR DASHBOARD TOGGLE ---
with st.sidebar:
    st.markdown(f"**👤 {st.session_state.emp_name}**")
    st.caption(st.session_state.emp_email)
    
    if st.session_state.is_hr:
        st.success("🔑 HR Admin Mode Active")
        
    st.divider()
    
    st.markdown("📚 **Company Policy Categories**")
    categories = ["Leave Policy", "Attendance & Work Hours", "Appraisal & Revisions", "Reimbursement", "Probation & Confirmation", "Full & Final Settlement"]
    for cat in categories:
        if st.button(f"📄 {cat}", key=cat, use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": f"Summarize the key points of the {cat}."})
            st.rerun()
            
    st.divider()
    st.link_button("💬 Message HR on Google Chat", DIRECT_GOOGLE_CHAT_HR, use_container_width=True)
    
    if st.button("🚪 Sign Out", use_container_width=True):
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

    # RENDER CHAT HISTORY
    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # RESOLVED / ESCALATION WORKFLOW FOR ASSISTANT RESPONSES
            if message["role"] == "assistant":
                col_res, col_unres, _ = st.columns([1, 1, 3])
                with col_res:
                    if st.button("👍 Resolved", key=f"res_{idx}"):
                        st.toast("Glad this helped resolve your query!")
                with col_unres:
                    if st.button("👎 Need Help", key=f"unres_{idx}"):
                        st.session_state.unsatisfied_msg_idx = idx

                # SHOW ESCALATION PANEL IF MARKED "NEED HELP"
                if st.session_state.unsatisfied_msg_idx == idx:
                    st.markdown("""
                    <div class="escalation-box">
                        <b>I couldn't fully resolve your question.</b><br/>
                        Would you like to schedule a direct 1-on-1 call with HR or escalate this query?
                    </div>
                    """, unsafe_allow_html=True)

    # CHAT INPUT
    user_query = st.chat_input("Ask a policy question (e.g., 'How many leaves do I get per month?')...")
    
    if user_query:
        st.session_state.messages.append({"role": "user", "content": user_query})
        
        with st.spinner("Searching Germane Media Policy Handbook..."):
            try:
                response = query_policy_ai(user_query, st.session_state.messages)
                
                # Append Disclaimer
                full_response = response + "\n\n---\n*Notice: Answers are derived from the Germane Media LLC Policy Handbook. Employment Agreement terms prevail where applicable.*"
                
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                st.rerun()
            except Exception as e:
                st.error(str(e))

# --- RIGHT SIDEBAR: DIRECT HR SCHEDULER & QUICK ACTION CARDS ---
with col_right:
    st.markdown("### 📅 **Schedule HR Discussion**")
    st.caption("Select a time slot to meet with Tarang (HR):")
    
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
    
    st.link_button("📅 Open & Save in Google Calendar", gcal_url, type="primary", use_container_width=True)
    
    st.divider()
    
    st.markdown("💡 **Suggested Questions**")
    suggested = [
        "How many leaves accumulate during probation?",
        "When am I eligible for appraisal consideration?",
        "What is the timeline for FNF settlement?",
        "How do medical reimbursement requests work?"
    ]
    for q in suggested:
        if st.button(f"❓ {q}", key=q, use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": q})
            st.rerun()
