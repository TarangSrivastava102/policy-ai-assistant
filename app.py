import streamlit as st
from google import genai
from pypdf import PdfReader
import smtplib
from email.message import EmailMessage
from pathlib import Path
import base64
import textwrap
import calendar
from datetime import date, datetime


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

GEMINI_MODEL = "gemini-3.6-flash"


# ============================================================
# REIMBURSEMENT CONFIGURATION
# ============================================================

REIMBURSEMENT_CUTOFF_DAY = 22

REIMBURSEMENT_CYCLE_MONTHS = 3

REIMBURSEMENT_TYPES = {

    "Wi-Fi / Internet": {
        "monthly_limit": 1000,
        "max_invoices": 3,
    },

    "Gym / Health": {
        "monthly_limit": 1000,
        "max_invoices": 3,
    },

    "Course": {
        "monthly_limit": 1000,
        "max_invoices": 3,
    },

    "Other Reimbursement": {
        "monthly_limit": None,
        "max_invoices": None,
    },
}


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

        .reimbursement-header {
            background: linear-gradient(
                135deg,
                #f7f5ff,
                #ffffff
            );
            border: 1px solid #e5e0ff;
            border-radius: 16px;
            padding: 25px;
            margin-bottom: 22px;
        }

        .reimbursement-title {
            font-size: 28px;
            font-weight: 800;
            color: #17233c;
            margin-bottom: 7px;
        }

        .reimbursement-subtitle {
            font-size: 14px;
            color: #667085;
        }

        .rule-card {
            background: #fafafa;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 15px;
        }

        .summary-card {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 18px;
            margin-top: 15px;
        }

        .total-card {
            background: #f5f3ff;
            border: 1px solid #ddd6fe;
            border-radius: 12px;
            padding: 20px;
            margin-top: 20px;
        }

        .amount-big {
            font-size: 28px;
            font-weight: 800;
            color: #5b43d6;
        }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def add_months(year, month, months_to_add):

    total_months = (
        year * 12
        + (month - 1)
        + months_to_add
    )

    new_year = total_months // 12

    new_month = (
        total_months % 12
        + 1
    )

    return new_year, new_month


def month_label(year, month):

    return (
        f"{calendar.month_name[month]} {year}"
    )


def get_default_submission_month():

    today = date.today()

    if today.day > REIMBURSEMENT_CUTOFF_DAY:

        return add_months(
            today.year,
            today.month,
            1
        )

    return (
        today.year,
        today.month
    )


def get_eligible_months_for_demo():

    """
    STEP 1 ONLY

    Google Sheets will be connected in Step 2.

    Until then, the portal uses the current
    submission month to demonstrate the UI.

    Once Google Sheets is connected, this function
    will automatically use the employee's actual
    previous reimbursement date.
    """

    submission_year, submission_month = (
        get_default_submission_month()
    )

    months = []

    for i in range(2, -1, -1):

        year, month = add_months(
            submission_year,
            submission_month,
            -i
        )

        months.append(
            {
                "year": year,
                "month": month,
                "label": month_label(
                    year,
                    month
                )
            }
        )

    return months


def calculate_reimbursement(
    reimbursement_type,
    total_amount
):

    config = REIMBURSEMENT_TYPES[
        reimbursement_type
    ]

    limit = config["monthly_limit"]

    if limit is None:

        return total_amount

    return min(
        total_amount,
        limit
    )


# ============================================================
# INITIALIZE REIMBURSEMENT SESSION
# ============================================================

if "reimbursement_entries" not in st.session_state:

    st.session_state.reimbursement_entries = []


if "reimbursement_submitted" not in st.session_state:

    st.session_state.reimbursement_submitted = False


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
        and str(
            st.secrets["SMTP_EMAIL"]
        ).strip() != ""
        and str(
            st.secrets["SMTP_PASSWORD"]
        ).strip() != ""
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

    transcript_lines = []

    for message in conversation:

        role = (
            "EMPLOYEE"
            if message["role"] == "user"
            else "GM POLICY ASSISTANT"
        )

        transcript_lines.append(
            f"{role}:\n"
            f"{message['content']}\n"
        )

    transcript = "\n".join(
        transcript_lines
    )

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

    for idx, page in enumerate(
        reader.pages
    ):

        text = (
            page.extract_text()
            or ""
        )

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
            f"{role}: "
            f"{msg['content']}\n"
        )

    pdf_pages = load_and_index_pdf(
        POLICY_PDF
    )

    full_context = "\n\n".join(
        [
            f"--- PAGE {p['page']} ---\n"
            f"{p['text']}"
            for p in pdf_pages
        ]
    )

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

7. Keep answers professional, concise and easy to understand.

8. Never claim something is policy unless it is supported
by the handbook.

9. If a policy has an exception, clearly mention it.

10. If the handbook gives a specific number, date, duration,
percentage, amount or entitlement, reproduce it accurately.

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

        response = (
            gemini_client
            .models
            .generate_content(
                model=GEMINI_MODEL,
                contents=system_prompt
            )
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
# REIMBURSEMENT PORTAL
# ============================================================

def reimbursement_portal():

    st.markdown(
        """
        <div class="reimbursement-header">

            <div class="reimbursement-title">
                💰 Employee Reimbursement Portal
            </div>

            <div class="reimbursement-subtitle">
                Submit your eligible reimbursement claims
                securely through the Germane Media employee portal.
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


    # --------------------------------------------------------
    # EMPLOYEE INFORMATION
    # --------------------------------------------------------

    st.markdown("### 👤 Employee Information")

    info_col1, info_col2 = st.columns(2)

    with info_col1:

        st.text_input(
            "Employee Name",
            value=st.session_state.emp_name,
            disabled=True
        )

    with info_col2:

        st.text_input(
            "Company Email",
            value=st.session_state.emp_email,
            disabled=True
        )


    st.divider()


    # --------------------------------------------------------
    # SUBMISSION DEADLINE
    # --------------------------------------------------------

    today = date.today()

    if today.day > REIMBURSEMENT_CUTOFF_DAY:

        next_year, next_month = add_months(
            today.year,
            today.month,
            1
        )

        deadline_message = (
            f"The submission deadline for "
            f"{calendar.month_name[today.month]} "
            f"{today.year} has passed. "
            f"You can submit your reimbursement in "
            f"{calendar.month_name[next_month]} "
            f"{next_year}, before the 22nd."
        )

        st.warning(
            f"⚠️ {deadline_message}"
        )

    else:

        st.success(
            f"✅ Reimbursement submissions are open "
            f"until the {REIMBURSEMENT_CUTOFF_DAY}th "
            f"of {calendar.month_name[today.month]} "
            f"{today.year}."
        )


    # --------------------------------------------------------
    # IMPORTANT RULES
    # --------------------------------------------------------

    with st.expander(
        "📋 Important Reimbursement Rules",
        expanded=True
    ):

        st.markdown(
            """
            **Eligibility**

            - Applicable to Full-Time Employees and Interns.
            - Consultants are not eligible unless specifically
              approved by management.

            **Submission**

            - Claims can cover a maximum of 3 months.
            - Claims must be submitted before the 22nd.
            - Supporting documents are mandatory.
            - Employees are responsible for submitting claims
              on time.

            **Monthly Limits**

            - Wi-Fi / Internet: ₹1,000 per month.
            - Gym / Health: ₹1,000 per month.
            - Course: ₹1,000 per month.
            - Other Reimbursement: No ₹1,000 cap.

            **Invoice Limits**

            - Wi-Fi / Internet: maximum 3 invoices per month.
            - Gym / Health: maximum 3 invoices per month.
            - Course: maximum 3 invoices per month.
            - Other Reimbursement: unlimited invoices.
            """
        )


    st.divider()


    # --------------------------------------------------------
    # ELIGIBLE MONTHS
    # --------------------------------------------------------

    st.markdown(
        "### 📅 Select Reimbursement Months"
    )

    st.caption(
        "You can select a maximum of 3 months."
    )

    eligible_months = (
        get_eligible_months_for_demo()
    )

    eligible_labels = [
        item["label"]
        for item in eligible_months
    ]


    selected_months = st.multiselect(
        "Select the months you want to claim",
        options=eligible_labels,
        max_selections=3,
        key="selected_reimbursement_months"
    )


    if not selected_months:

        st.info(
            "Please select at least one month "
            "to continue."
        )

        return


    st.divider()


    # --------------------------------------------------------
    # CLEAR PREVIOUS ENTRIES WHEN MONTH SELECTION CHANGES
    # --------------------------------------------------------

    if (
        "last_selected_months"
        not in st.session_state
    ):

        st.session_state.last_selected_months = []


    if (
        st.session_state.last_selected_months
        != selected_months
    ):

        st.session_state.reimbursement_entries = []

        st.session_state.last_selected_months = (
            selected_months
        )


    # --------------------------------------------------------
    # MONTHLY CLAIMS
    # --------------------------------------------------------

    st.markdown(
        "### 🧾 Reimbursement Details"
    )

    st.caption(
        "Add reimbursement claims for each selected month."
    )


    for month_index, selected_month in enumerate(
        selected_months
    ):

        st.markdown(
            f"## 📅 {selected_month}"
        )


        # ----------------------------------------------------
        # NUMBER OF CLAIMS
        # ----------------------------------------------------

        claim_count_key = (
            f"claim_count_{selected_month}"
        )

        if claim_count_key not in st.session_state:

            st.session_state[
                claim_count_key
            ] = 1


        st.write(
            "Add reimbursement type"
        )


        # ----------------------------------------------------
        # CLAIM TYPE
        # ----------------------------------------------------

        claim_type = st.selectbox(
            "Reimbursement Type",
            options=list(
                REIMBURSEMENT_TYPES.keys()
            ),
            key=f"type_{selected_month}"
        )


        config = REIMBURSEMENT_TYPES[
            claim_type
        ]


        # ----------------------------------------------------
        # INVOICE COUNT
        # ----------------------------------------------------

        if config["max_invoices"] is None:

            invoice_count = st.number_input(
                "Number of invoices",
                min_value=1,
                max_value=20,
                value=1,
                step=1,
                key=f"invoice_count_{selected_month}"
            )

            st.caption(
                "Other reimbursement allows multiple invoices."
            )

        else:

            invoice_count = st.number_input(
                "Number of invoices",
                min_value=1,
                max_value=config["max_invoices"],
                value=1,
                step=1,
                key=f"invoice_count_{selected_month}"
            )

            st.caption(
                f"Maximum {config['max_invoices']} "
                f"invoices for this reimbursement type."
            )


        st.markdown(
            "#### Upload invoices"
        )


        invoice_data = []

        total_amount = 0


        for invoice_index in range(
            int(invoice_count)
        ):

            st.markdown(
                f"**Invoice {invoice_index + 1}**"
            )


            amount = st.number_input(
                f"Amount - Invoice {invoice_index + 1} (₹)",
                min_value=0.0,
                step=100.0,
                value=0.0,
                key=(
                    f"amount_"
                    f"{selected_month}_"
                    f"{invoice_index}"
                )
            )


            uploaded_file = st.file_uploader(
                (
                    f"Supporting document - "
                    f"Invoice {invoice_index + 1}"
                ),
                type=[
                    "pdf",
                    "jpg",
                    "jpeg",
                    "png"
                ],
                key=(
                    f"file_"
                    f"{selected_month}_"
                    f"{invoice_index}"
                )
            )


            total_amount += amount


            invoice_data.append(
                {
                    "invoice_number":
                        invoice_index + 1,
                    "amount": amount,
                    "file": uploaded_file
                }
            )


        # ----------------------------------------------------
        # CALCULATE MONTHLY REIMBURSEMENT
        # ----------------------------------------------------

        eligible_amount = (
            calculate_reimbursement(
                claim_type,
                total_amount
            )
        )


        st.markdown(
            f"""
            <div class="summary-card">

            <b>{claim_type}</b>

            <br><br>

            Total invoice amount:
            <b>₹{total_amount:,.2f}</b>

            <br>

            Eligible reimbursement:
            <b>₹{eligible_amount:,.2f}</b>

            </div>
            """,
            unsafe_allow_html=True
        )


        if (
            config["monthly_limit"]
            is not None
            and total_amount > config["monthly_limit"]
        ):

            st.info(
                f"The total eligible amount for "
                f"{claim_type} is capped at "
                f"₹{config['monthly_limit']:,} "
                f"per month."
            )


        st.divider()


    # --------------------------------------------------------
    # REVIEW SECTION
    # --------------------------------------------------------

    st.markdown(
        "## 🔎 Review Your Reimbursement"
    )

    st.caption(
        "Please verify all amounts and documents "
        "before submitting."
    )


    grand_total_claimed = 0

    grand_total_reimbursable = 0


    for selected_month in selected_months:

        claim_type = st.session_state.get(
            f"type_{selected_month}",
            "Wi-Fi / Internet"
        )

        config = REIMBURSEMENT_TYPES[
            claim_type
        ]

        invoice_count = st.session_state.get(
            f"invoice_count_{selected_month}",
            1
        )

        month_total = 0

        invoice_files_present = True


        for invoice_index in range(
            int(invoice_count)
        ):

            amount = st.session_state.get(
                (
                    f"amount_"
                    f"{selected_month}_"
                    f"{invoice_index}"
                ),
                0.0
            )

            month_total += amount


            uploaded_file = st.session_state.get(
                (
                    f"file_"
                    f"{selected_month}_"
                    f"{invoice_index}"
                )
            )


            if uploaded_file is None:

                invoice_files_present = False


        month_reimbursable = (
            calculate_reimbursement(
                claim_type,
                month_total
            )
        )


        grand_total_claimed += month_total

        grand_total_reimbursable += (
            month_reimbursable
        )


        col1, col2, col3 = st.columns(
            [2, 1, 1]
        )


        with col1:

            st.write(
                f"**{selected_month}**"
            )

            st.caption(
                claim_type
            )


        with col2:

            st.write(
                f"Claimed: "
                f"₹{month_total:,.2f}"
            )


        with col3:

            st.write(
                f"Eligible: "
                f"₹{month_reimbursable:,.2f}"
            )


        if not invoice_files_present:

            st.warning(
                f"Please upload all supporting documents "
                f"for {selected_month}."
            )


    # --------------------------------------------------------
    # GRAND TOTAL
    # --------------------------------------------------------

    st.markdown(
        f"""
        <div class="total-card">

        <div>
            <b>Total Invoice Value</b>
        </div>

        <div class="amount-big">
            ₹{grand_total_claimed:,.2f}
        </div>

        <br>

        <div>
            <b>Total Reimbursement Amount</b>
        </div>

        <div class="amount-big">
            ₹{grand_total_reimbursable:,.2f}
        </div>

        </div>
        """,
        unsafe_allow_html=True
    )


    st.divider()


    # --------------------------------------------------------
    # DECLARATION
    # --------------------------------------------------------

    declaration = st.checkbox(
        "I confirm that the information submitted is "
        "correct and that all uploaded documents are "
        "genuine supporting documents."
    )


    # --------------------------------------------------------
    # SUBMIT
    # --------------------------------------------------------

    submit_button = st.button(
        "✅ Submit Reimbursement",
        type="primary",
        use_container_width=True
    )


    if submit_button:

        # ----------------------------------------------------
        # DEADLINE CHECK
        # ----------------------------------------------------

        today = date.today()

        if today.day > REIMBURSEMENT_CUTOFF_DAY:

            st.error(
                "The reimbursement submission deadline "
                "for this month has passed. "
                "Please submit your reimbursement "
                "in the next month before the 22nd."
            )

            return


        # ----------------------------------------------------
        # DECLARATION CHECK
        # ----------------------------------------------------

        if not declaration:

            st.error(
                "Please confirm the declaration before "
                "submitting your reimbursement."
            )

            return


        # ----------------------------------------------------
        # MONTH CHECK
        # ----------------------------------------------------

        if len(selected_months) == 0:

            st.error(
                "Please select at least one month."
            )

            return


        if len(selected_months) > 3:

            st.error(
                "You can claim reimbursement for "
                "a maximum of 3 months."
            )

            return


        # ----------------------------------------------------
        # AMOUNT & DOCUMENT CHECK
        # ----------------------------------------------------

        validation_failed = False


        for selected_month in selected_months:

            invoice_count = st.session_state.get(
                f"invoice_count_{selected_month}",
                1
            )


            for invoice_index in range(
                int(invoice_count)
            ):

                amount = st.session_state.get(
                    (
                        f"amount_"
                        f"{selected_month}_"
                        f"{invoice_index}"
                    ),
                    0.0
                )


                uploaded_file = st.session_state.get(
                    (
                        f"file_"
                        f"{selected_month}_"
                        f"{invoice_index}"
                    )
                )


                if amount <= 0:

                    st.error(
                        f"Please enter a valid amount "
                        f"for {selected_month}, "
                        f"Invoice {invoice_index + 1}."
                    )

                    validation_failed = True


                if uploaded_file is None:

                    st.error(
                        f"Please upload the supporting "
                        f"document for {selected_month}, "
                        f"Invoice {invoice_index + 1}."
                    )

                    validation_failed = True


        if validation_failed:

            return


        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        st.session_state.reimbursement_submitted = True


    # --------------------------------------------------------
    # SUCCESS MESSAGE
    # --------------------------------------------------------

    if st.session_state.reimbursement_submitted:

        st.success(
            "🎉 Your reimbursement has been "
            "submitted successfully."
        )

        st.info(
            f"""
            Employee: {st.session_state.emp_name}

            Email: {st.session_state.emp_email}

            Months:
            {", ".join(selected_months)}

            Total Invoice Value:
            ₹{grand_total_claimed:,.2f}

            Total Reimbursement Amount:
            ₹{grand_total_reimbursable:,.2f}

            Your reimbursement is currently marked
            as submitted.
            """
        )

        st.warning(
            "This is Step 1 of the reimbursement system. "
            "Google Sheets and Google Drive storage will "
            "be connected in the next step."
        )


# ============================================================
# LOGIN PAGE
# ============================================================

if not st.user.is_logged_in:

    logo_path = (
        Path(__file__).parent
        / "logo.png"
    )

    if logo_path.exists():

        logo_b64 = base64.b64encode(
            logo_path.read_bytes()
        ).decode("utf-8")

        logo_html = (
            f'<img class="brand-logo" '
            f'src="data:image/png;base64,{logo_b64}" '
            f'alt="Germane Media LLC logo">'
        )

    else:

        logo_html = (
            '<div class="brand-logo-fallback">G</div>'
        )


    st.markdown(
        """
        <style>

        #MainMenu,
        footer,
        header {
            visibility: hidden;
        }

        .stApp {
            background:
                radial-gradient(
                    circle at 12% 20%,
                    rgba(112, 72, 237, 0.06),
                    transparent 28%
                ),
                radial-gradient(
                    circle at 82% 55%,
                    rgba(112, 72, 237, 0.05),
                    transparent 30%
                ),
                #fbfbfe;
        }

        .block-container {
            max-width: 1400px !important;
            padding: 28px 38px 18px !important;
        }

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
            background: linear-gradient(
                135deg,
                #5d4bea,
                #7c4df0
            );
            color: white;
            font-size: 58px;
            font-weight: 800;
        }

        .brand-name {
            font-size: 31px;
            line-height: 1.1;
            font-weight: 800;
            color: #15213a;
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
            font-weight: 800;
            margin: 5px 0 8px;
        }

        .feature-text {
            color: #626b7c;
            font-size: 13px;
            line-height: 1.65;
        }

        .wave {
            margin-top: 40px;
            width: 100%;
            height: 95px;
            overflow: hidden;
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
            font-weight: 800;
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
            font-weight: 700;
        }

        .signin-label {
            text-align: center;
            color: #1d263b;
            font-size: 15px;
            font-weight: 800;
            margin-bottom: 12px;
        }

        div[data-testid="stButton"] {
            width: 100% !important;
        }

        div[data-testid="stButton"] button {
            width: 100% !important;
            min-height: 54px !important;
            border-radius: 8px !important;
            border: 1px solid #6547ed !important;
            background: linear-gradient(
                90deg,
                #6547ed,
                #7048ed
            ) !important;
            color: #ffffff !important;
            font-size: 16px !important;
            font-weight: 800 !important;
        }

        .divider {
            display: flex;
            align-items: center;
            gap: 15px;
            margin: 29px 0 24px;
            color: #9aa1ae;
            font-size: 13px;
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

        .protected {
            text-align: center;
            margin-top: 32px;
            color: #858d9c;
            font-size: 12px;
        }

        </style>
        """,
        unsafe_allow_html=True
    )


    left_col, right_col = st.columns(
        [1.03, 0.97],
        gap="large"
    )


    with left_col:

        left_html = textwrap.dedent(
            f"""
            <div class="left-panel">

                <div class="brand">

                    {logo_html}

                    <div>

                        <div class="brand-name">
                            Germane Media LLC
                        </div>

                        <div class="brand-subtitle">
                            GM Policy Assistant •
                            Internal HR Portal
                        </div>

                        <div class="brand-line"></div>

                    </div>

                </div>

                <div class="left-title">
                    Your Intelligent HR Policy Companion
                </div>

                <div class="left-description">
                    Get instant, accurate answers to your policy
                    questions, understand company guidelines,
                    submit reimbursements, and connect with HR
                    for personalized support.
                </div>

                <div class="features">

                    <div class="feature">

                        <div class="feature-icon">
                            ▢
                        </div>

                        <div>

                            <div class="feature-title">
                                Instant Policy Answers
                            </div>

                            <div class="feature-text">
                                Accurate responses based on
                                Germane Media LLC Employee
                                Policy Handbook.
                            </div>

                        </div>

                    </div>


                    <div class="feature">

                        <div class="feature-icon">
                            ♙
                        </div>

                        <div>

                            <div class="feature-title">
                                Secure & Confidential
                            </div>

                            <div class="feature-text">
                                Your conversations are private,
                                secure, and associated with
                                your company account.
                            </div>

                        </div>

                    </div>


                    <div class="feature">

                        <div class="feature-icon">
                            ♧
                        </div>

                        <div>

                            <div class="feature-title">
                                Direct HR Support
                            </div>

                            <div class="feature-text">
                                Escalate questions to HR or
                                schedule a confidential discussion.
                            </div>

                        </div>

                    </div>


                    <div class="feature">

                        <div class="feature-icon">
                            ♟
                        </div>

                        <div>

                            <div class="feature-title">
                                For Employees Only
                            </div>

                            <div class="feature-text">
                                This portal is restricted to
                                active Germane Media LLC employees.
                            </div>

                        </div>

                    </div>

                </div>

            </div>
            """
        )

        st.html(left_html)


    with right_col:

        with st.container(
            border=True
        ):

            card_html = textwrap.dedent(
                """
                <div>

                    <div class="lock-circle">
                        🔒
                    </div>

                    <div class="card-title">
                        Welcome Back!
                    </div>

                    <div class="card-subtitle">
                        Sign in to access the GM Policy Assistant
                    </div>

                    <div class="restricted">

                        🔒

                        <div>
                            This portal is restricted to active
                            Germane Media LLC employees.
                        </div>

                    </div>

                    <div class="signin-label">
                        Sign in with your company account
                    </div>

                </div>
                """
            )

            st.html(card_html)


            if st.button(
                "G   Sign in with Google",
                key="login_button",
                type="primary",
                use_container_width=True
            ):

                st.login()


            st.markdown(
                """
                <div class="divider">
                    OR
                </div>

                <div class="workspace-note">

                    ▦

                    <div>

                        Please use your official
                        <strong>
                        @thegermanemedia.com
                        Google Workspace account.
                        </strong>

                        <br>

                        Your policy conversations are associated
                        with your authenticated company account.

                    </div>

                </div>

                <div class="protected">

                    🛡 Protected by Google Workspace Authentication

                </div>
                """,
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
    user_email
    == HR_EMAIL.lower()
)


# ============================================================
# CHAT SESSION INITIALIZATION
# ============================================================

if "messages" not in st.session_state:

    st.session_state.messages = []


if "unsatisfied_msg_idx" not in st.session_state:

    st.session_state.unsatisfied_msg_idx = None


if "hr_email_sent" not in st.session_state:

    st.session_state.hr_email_sent = False


# ============================================================
# PAGE NAVIGATION
# ============================================================

if "current_page" not in st.session_state:

    st.session_state.current_page = "Policy Assistant"


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
        "### 🧭 Portal"
    )


    if st.button(
        "🤖 Policy Assistant",
        width="stretch"
    ):

        st.session_state.current_page = (
            "Policy Assistant"
        )

        st.rerun()


    if st.button(
        "💰 Reimbursement Portal",
        width="stretch"
    ):

        st.session_state.current_page = (
            "Reimbursement"
        )

        st.rerun()


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

            st.session_state.current_page = (
                "Policy Assistant"
            )

            st.session_state.messages.append(
                {
                    "role": "user",
                    "content":
                    f"Summarize the key points "
                    f"of the {cat}."
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
# REIMBURSEMENT PAGE
# ============================================================

if (
    st.session_state.current_page
    == "Reimbursement"
):

    reimbursement_portal()

    st.stop()


# ============================================================
# POLICY ASSISTANT PAGE
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


            if message["role"] == "assistant":

                col_sat, col_not_sat, col_space = (
                    st.columns(
                        [1, 1, 3]
                    )
                )


                with col_sat:

                    if st.button(
                        "✅ Satisfied",
                        key=f"satisfied_{idx}"
                    ):

                        st.toast(
                            "Thank you for your feedback!"
                        )


                with col_not_sat:

                    if st.button(
                        "❌ Not Satisfied",
                        key=f"not_satisfied_{idx}"
                    ):

                        st.session_state.unsatisfied_msg_idx = (
                            idx
                        )

                        st.session_state.hr_email_sent = (
                            False
                        )

                        st.rerun()


                if (
                    st.session_state.unsatisfied_msg_idx
                    == idx
                ):

                    st.markdown(
                        """
                        <div class="escalation-box">

                        <b>
                        We're sorry we couldn't fully
                        resolve your question.
                        </b>

                        <br><br>

                        You can contact HR directly or
                        schedule a confidential 15-minute
                        discussion.

                        </div>
                        """,
                        unsafe_allow_html=True
                    )


                    col_email, col_calendar = (
                        st.columns([1, 1])
                    )


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

                                st.session_state.hr_email_sent = (
                                    True
                                )

                                st.success(
                                    "Your conversation has "
                                    "been sent to HR successfully."
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


                    if st.session_state.hr_email_sent:

                        st.markdown(
                            """
                            <div class="success-box">

                            ✅ <b>HR has been notified.</b>

                            Your conversation transcript has
                            been sent to HR.

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
        "💡 **Need immediate help?**"
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
