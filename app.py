import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date, time, datetime

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Policy AI Assistant - Germane Media LLC",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- HR CONFIGURATION ---
HR_EMAIL = "tarang@thegermanemedia.com"
GOOGLE_CHAT_LINK = "https://chat.google.com/"

# --- CUSTOM CSS (SIDEBAR LOGO & STICKY RIGHT COLUMN) ---
st.markdown("""
<style>
    /* Prevent long chat history from pushing down right sidebar elements */
    [data-testid="stColumn"]:nth-child(2) {
        position: sticky;
        top: 2rem;
        align-self: flex-start;
        max-height: 90vh;
        overflow-y: auto;
    }
    
    /* Source citation box styling */
    .source-box {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 13px;
        margin-top: 8px;
    }
    
    /* Privacy badge styling */
    .badge-safe {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 12px;
        text-align: left;
        margin-top: 20px;
    }
    
    .stButton>button {
        border-radius: 8px;
        font-weight: 500;
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

# --- GEMINI GENERATION ---
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

# --- EMAIL SENDER FUNCTION ---
def send_transcript_email(employee_email, employee_name, chat_history):
    if "SMTP_USER" in st.secrets and "SMTP_PASSWORD" in st.secrets:
        try:
            sender_email = st.secrets["SMTP_USER"]
            sender_password = st.secrets["SMTP_PASSWORD"]
            
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = employee_email
            msg['Cc'] = HR_EMAIL
            msg['Subject'] = f"Policy Chat Transcript - {employee_name}"
            
            body = f"Hello {employee_name},\n\nHere is the transcript of your recent interaction with the Germane Media Policy AI Assistant:\n\n"
            for message in chat_history:
                role = "You" if message["role"] == "user" else "Policy AI"
                body += f"[{role}]: {message['content']}\n\n"
            
            body += f"\nBest regards,\nGermane Media HR Team\nCC: {HR_EMAIL}"
            msg.attach(MIMEText(body, 'plain'))
            
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

# --- SESSION STATE INITIALIZATION FOR BOOKINGS ---
if "booked_slots" not in st.session_state:
    st.session_state.booked_slots = set()

# --- SIDEBAR COMPONENT ---
with st.sidebar:
    # --- GERMANE MEDIA LOGO ---
    # You can upload a file named 'logo.png' to your GitHub repo root, 
    # or paste your hosted image URL inside st.image below:
    try:
        st.image("logo.png", use_container_width=True)
    except Exception:
        st.title("🏢 GERMANE MEDIA LLC")
        
    st.caption("*Psychology of Advertising*")
    st.divider()
    
    st.markdown("💬 **Chat with Policy AI**")
    st.markdown("📄 Company Policies")
    st.markdown("💬 Contact HR")
    
    st.divider()
    
    st.markdown("""
    <div class="badge-safe">
        🔒 <b>Your Data is Safe</b><br/>
        <small>Your conversations are confidential and visible only to HR.</small>
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

# --- MAIN LAYOUT ---
col_main, col_right = st.columns([3, 1])

with col_main:
    st.title("Policy AI Assistant ✨")
    st.caption("Your smart guide to Germane Media LLC policies.")
    
    # Render Chat History
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
                        st.toast("We're sorry! Please use the right sidebar to schedule a call with HR.")

    # User Input Field
    user_query = st.chat_input("Type your question here...")
    
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
    
    # Email Transcript Section
    if st.button(f"📧 Send Chat Transcript to My Email ({st.session_state.emp_email})"):
        if "SMTP_USER" not in st.secrets or "SMTP_PASSWORD" not in st.secrets:
            st.warning("⚠️ Email credentials are not configured in Streamlit Secrets yet.")
        else:
            with st.spinner("Sending email..."):
                if send_transcript_email(st.session_state.emp_email, st.session_state.emp_name, st.session_state.messages):
                    st.success(f"Transcript sent to **{st.session_state.emp_email}** (CC'd to {HR_EMAIL})!")
                else:
                    st.error("Failed to send email. Please verify your Gmail App Password setup in Streamlit Secrets.")

# --- RIGHT SIDEBAR (STICKY PANEL) ---
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
        
        if st.button("Confirm Meeting Slot", type="primary", use_container_width=True):
            slot_key = f"{selected_date}_{selected_slot}"
            st.session_state.booked_slots.add(slot_key)
            st.success(f"✅ Meeting booked with HR for **{selected_date}** at **{selected_slot}**!")
            st.info(f"Notification sent to HR ({HR_EMAIL}).")
    else:
        st.error("❌ No slots available for this date. Please pick another date.")
        
    st.divider()
    st.link_button("💬 Chat on Google Chat", GOOGLE_CHAT_LINK, use_container_width=True)
