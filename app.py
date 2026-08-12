import streamlit as st
from pathlib import Path
import base64
import textwrap

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="GM Policy Assistant",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# LOGIN PAGE
# ============================================================

if not st.user.is_logged_in:

    # Load logo.png from the same folder as app.py.
    # A text "G" fallback is used if the file is temporarily unavailable.
    logo_path = Path(__file__).parent / "logo.png"

    if logo_path.exists():
        logo_b64 = base64.b64encode(logo_path.read_bytes()).decode("utf-8")
        logo_html = (
            f'<img class="brand-logo" src="data:image/png;base64,{logo_b64}" '
            'alt="Germane Media LLC logo">'
        )
    else:
        logo_html = '<div class="brand-logo-fallback">G</div>'

    st.markdown(
        """
        <style>
        /* ---------- Streamlit chrome ---------- */
        #MainMenu, footer, header {
            visibility: hidden;
        }

        .stApp {
            background:
                radial-gradient(circle at 12% 20%, rgba(112, 72, 237, 0.06), transparent 28%),
                radial-gradient(circle at 82% 55%, rgba(112, 72, 237, 0.05), transparent 30%),
                #fbfbfe;
        }

        .block-container {
            max-width: 1400px !important;
            padding: 28px 38px 18px !important;
        }

        /* ---------- Main login layout ---------- */
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

        /* ---------- Brand ---------- */
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
            background: linear-gradient(135deg, #5d4bea, #7c4df0);
            color: white;
            font-size: 58px;
            font-weight: 800;
            box-shadow: 0 12px 28px rgba(91, 75, 234, .20);
        }

        .brand-name {
            font-size: 31px;
            line-height: 1.1;
            font-weight: 800;
            color: #15213a;
            letter-spacing: -0.7px;
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

        /* ---------- Left content ---------- */
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
            line-height: 1.25;
            font-weight: 800;
            margin: 5px 0 8px;
        }

        .feature-text {
            color: #626b7c;
            font-size: 13px;
            line-height: 1.65;
        }

        /* ---------- Decorative wave ---------- */
        .wave {
            margin-top: 40px;
            width: 100%;
            height: 95px;
            overflow: hidden;
            opacity: .75;
        }

        .wave svg {
            width: 100%;
            height: 100%;
        }

        /* ---------- Login card ----------
           The second Streamlit column is the card. The invisible
           anchor below lets us target that exact column with :has(). */
        div[data-testid="stColumn"]:has(.login-card-anchor) {
            background: rgba(255, 255, 255, .97);
            border: 1px solid #e8e8ef;
            border-radius: 20px;
            padding: 34px 38px 28px !important;
            box-shadow: 0 14px 40px rgba(32, 35, 58, .09);
            box-sizing: border-box;
            align-self: stretch;
        }

        .login-card {
            padding: 0;
        }

        .login-card-anchor {
            display: none;
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
            line-height: 1.15;
            font-weight: 800;
            letter-spacing: -.5px;
            margin-bottom: 9px;
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
            line-height: 1.55;
            font-weight: 700;
        }

        .restricted-icon {
            font-size: 22px;
            flex: 0 0 auto;
        }

        .signin-label {
            text-align: center;
            color: #1d263b;
            font-size: 15px;
            font-weight: 800;
            margin-bottom: 12px;
        }

        /* ---------- Real Streamlit login button ---------- */
        div[data-testid="stButton"] {
            width: 100% !important;
            display: flex;
            justify-content: center;
            margin: 0;
        }

        div[data-testid="stButton"] button {
            width: 100% !important;
            min-height: 54px !important;
            border-radius: 8px !important;
            border: 1px solid #6547ed !important;
            background: linear-gradient(90deg, #6547ed, #7048ed) !important;
            color: #ffffff !important;
            font-size: 16px !important;
            font-weight: 800 !important;
            box-shadow: none !important;
        }

        div[data-testid="stButton"] button:hover {
            border-color: #5538d8 !important;
            background: linear-gradient(90deg, #5b3fe1, #6840e6) !important;
        }

        .google-mark {
            display: inline-flex;
            width: 43px;
            height: 52px;
            align-items: center;
            justify-content: center;
            background: white;
            border-radius: 8px 0 0 8px;
            color: #4285f4;
            font-size: 20px;
            font-weight: 900;
            margin-right: 12px;
        }

        /* ---------- Divider / Workspace note ---------- */
        .divider {
            display: flex;
            align-items: center;
            gap: 15px;
            margin: 29px 0 24px;
            color: #9aa1ae;
            font-size: 13px;
        }

        .divider::before,
        .divider::after {
            content: "";
            height: 1px;
            background: #e7e7ed;
            flex: 1;
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

        .workspace-icon {
            width: 30px;
            flex: 0 0 30px;
            color: #6547ed;
            font-size: 25px;
            text-align: center;
        }

        .workspace-note strong {
            color: #252d40;
        }

        .protected {
            text-align: center;
            margin-top: 32px;
            color: #858d9c;
            font-size: 12px;
        }

        .protected-icon {
            color: #8a91a2;
        }

        /* ---------- Bottom footer ---------- */
        .page-footer {
            text-align: center;
            margin-top: 12px;
            color: #8a91a2;
            font-size: 12px;
        }

        /* ---------- Responsive ---------- */
        @media (max-width: 900px) {
            .block-container {
                padding: 20px 18px !important;
            }

            .login-page {
                display: block;
            }

            .left-panel,
            .right-panel {
                padding: 15px 8px;
            }

            .brand {
                margin-bottom: 34px;
            }

            .features {
                grid-template-columns: 1fr;
                gap: 20px;
            }

            div[data-testid="stColumn"]:has(.login-card-anchor) {
                padding: 24px 20px !important;
            }

            .login-card {
                min-height: auto;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Two-column page. The actual login button remains a Streamlit widget
    # so st.login() continues to work normally.
    left_col, right_col = st.columns([1.03, 0.97], gap="large")

    with left_col:
        left_html = textwrap.dedent(f"""
            <div class="left-panel">
                <div class="brand">
                    {logo_html}
                    <div>
                        <div class="brand-name">Germane Media LLC</div>
                        <div class="brand-subtitle">GM Policy Assistant • Internal HR Portal</div>
                        <div class="brand-line"></div>
                    </div>
                </div>

                <div class="left-title">Your Intelligent HR Policy Companion</div>

                <div class="left-description">
                    Get instant, accurate answers to your policy questions,
                    understand company guidelines, and connect with HR
                    for personalized support — anytime, anywhere.
                </div>

                <div class="features">
                    <div class="feature">
                        <div class="feature-icon">▢</div>
                        <div>
                            <div class="feature-title">Instant Policy Answers</div>
                            <div class="feature-text">
                                Accurate responses based on Germane Media LLC
                                Employee Policy Handbook.
                            </div>
                        </div>
                    </div>

                    <div class="feature">
                        <div class="feature-icon">♙</div>
                        <div>
                            <div class="feature-title">Secure &amp; Confidential</div>
                            <div class="feature-text">
                                Your conversations are private, secure, and
                                associated with your company account.
                            </div>
                        </div>
                    </div>

                    <div class="feature">
                        <div class="feature-icon">♧</div>
                        <div>
                            <div class="feature-title">Direct HR Support</div>
                            <div class="feature-text">
                                Escalate questions to HR or schedule a confidential
                                15-minute discussion.
                            </div>
                        </div>
                    </div>

                    <div class="feature">
                        <div class="feature-icon">♟</div>
                        <div>
                            <div class="feature-title">For Employees Only</div>
                            <div class="feature-text">
                                This portal is restricted to active Germane Media
                                LLC employees.
                            </div>
                        </div>
                    </div>
                </div>

                <div class="wave">
                    <svg viewBox="0 0 900 120" preserveAspectRatio="none">
                        <path d="M0,65 C120,115 180,10 300,65 S480,115 600,60 S780,10 900,65"
                              fill="none" stroke="#c9c0ff" stroke-width="2"/>
                        <path d="M0,80 C120,125 180,25 300,75 S480,125 600,70 S780,25 900,75"
                              fill="none" stroke="#ddd8ff" stroke-width="2"/>
                        <path d="M0,95 C120,135 180,40 300,85 S480,135 600,80 S780,40 900,85"
                              fill="none" stroke="#ebe8ff" stroke-width="2"/>
                    </svg>
                </div>
            </div>
        """)
        st.markdown(left_html, unsafe_allow_html=True)

    with right_col:
        # A real Streamlit container keeps the complete login card together,
        # while the HTML inside it is safely dedented so it is rendered as HTML.
        with st.container(border=True):
            card_html = textwrap.dedent("""
                <div class="login-card">
                    <div class="lock-circle">🔒</div>

                    <div class="card-title">Welcome Back!</div>
                    <div class="card-subtitle">
                        Sign in to access the GM Policy Assistant
                    </div>

                    <div class="restricted">
                        <div class="restricted-icon">🔒</div>
                        <div>
                            This portal is restricted to active
                            Germane Media LLC employees.
                        </div>
                    </div>

                    <div class="signin-label">Sign in with your company account</div>
                </div>
            """)
            st.markdown(card_html, unsafe_allow_html=True)

            if st.button(
                "G   Sign in with Google",
                key="login_button",
                type="primary",
                use_container_width=True,
            ):
                st.login()

            bottom_html = textwrap.dedent("""
                <div class="divider">OR</div>

                <div class="workspace-note">
                    <div class="workspace-icon">▦</div>
                    <div>
                        Please use your official
                        <strong>@thegermanemedia.com Google Workspace account.</strong><br>
                        Your policy conversations are associated with your
                        authenticated company account.
                    </div>
                </div>

                <div class="protected">
                    <span class="protected-icon">🛡</span>
                    Protected by Google Workspace Authentication
                </div>
            """)
            st.markdown(bottom_html, unsafe_allow_html=True)

    st.markdown(
        textwrap.dedent("""
            <div class="page-footer">
                🛡 Secure • Private • Trusted
                &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
                © 2026 Germane Media LLC. All rights reserved.
                &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
                Internal Use Only
            </div>
        """),
        unsafe_allow_html=True,
    )

    st.stop()


# ============================================================
# LOGGED-IN PAGE
# ============================================================

st.title("🔒 GM Policy Assistant")

st.write(f"Welcome, {st.user.name}!")
st.write("You are successfully logged in.")
st.write(f"Account: {st.user.email}")

if st.button("Log out"):
    st.logout()
