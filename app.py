import streamlit as st

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="GM Policy Assistant",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# LOGIN PAGE
# ============================================================

if not st.user.is_logged_in:

    st.markdown(
        """
        <style>

        .stApp {
            background: #f7f8ff;
        }

        .block-container {
            max-width: 1200px;
            padding-top: 60px;
        }

        .login-container {
            max-width: 850px;
            margin: 80px auto;
            text-align: center;
        }

        .logo {
            width: 100px;
            height: 100px;
            border-radius: 22px;
            background: linear-gradient(135deg, #6547ed, #8b5cf6);
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 25px auto;
            color: white;
            font-size: 52px;
            font-weight: 800;
            box-shadow: 0 12px 30px rgba(100,72,237,0.25);
        }

        .company {
            font-size: 30px;
            font-weight: 800;
            color: #172033;
            margin-bottom: 8px;
        }

        .subtitle {
            font-size: 16px;
            color: #667085;
            margin-bottom: 45px;
        }

        .title {
            font-size: 42px;
            font-weight: 800;
            color: #14213d;
            margin-bottom: 15px;
        }

        .description {
            font-size: 17px;
            line-height: 1.6;
            color: #667085;
            max-width: 650px;
            margin: 0 auto 35px auto;
        }

        .restricted {
            max-width: 600px;
            margin: 0 auto 30px auto;
            padding: 18px 22px;
            border: 1px solid #ddd6fe;
            background: #fbfaff;
            border-radius: 14px;
            color: #4938a8;
            font-size: 14px;
            font-weight: 600;
        }

        div[data-testid="stButton"] {
            display: flex;
            justify-content: center;
        }

        div[data-testid="stButton"] button {
            width: 420px !important;
            height: 58px !important;
            border-radius: 12px !important;
            border: none !important;
            background: linear-gradient(90deg, #6547ed, #7048ed) !important;
            color: white !important;
            font-size: 17px !important;
            font-weight: 700 !important;
        }

        .footer {
            margin-top: 50px;
            color: #8a91a2;
            font-size: 13px;
        }

        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="login-container">

            <div class="logo">
                G
            </div>

            <div class="company">
                Germane Media LLC
            </div>

            <div class="subtitle">
                GM Policy Assistant • Internal HR Portal
            </div>

            <div class="title">
                Welcome Back!
            </div>

            <div class="description">
                Your intelligent HR policy companion.
                Get instant answers to questions about
                company policies, leaves, compensation,
                probation, appraisal and more.
            </div>

            <div class="restricted">
                🔒 This portal is restricted to active
                Germane Media LLC employees.
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button(
        "🔐  Sign in with Google",
        key="login_button"
    ):
        st.login()

    st.markdown(
        """
        <div class="footer">
            Secure • Private • Internal Use Only
            <br><br>
            © 2026 Germane Media LLC
        </div>
        """,
        unsafe_allow_html=True
    )

    st.stop()


# ============================================================
# LOGGED-IN PAGE
# ============================================================

st.title("🔒 GM Policy Assistant")

st.write(
    f"Welcome, {st.user.name}!"
)

st.write(
    "You are successfully logged in."
)

st.write(
    f"Account: {st.user.email}"
)

if st.button("Log out"):
    st.logout()
