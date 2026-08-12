# ============================================================
# GOOGLE AUTHENTICATION
# ============================================================

if not st.user.is_logged_in:

    # --------------------------------------------------------
    # LOGIN PAGE CSS
    # --------------------------------------------------------

    st.markdown(
        """
        <style>

        .stApp {
            background: #f7f8ff;
        }

        .block-container {
            max-width: 1450px !important;
            padding-top: 0rem !important;
            padding-bottom: 0rem !important;
            padding-left: 3rem !important;
            padding-right: 3rem !important;
        }

        div[data-testid="stVerticalBlock"] {
            gap: 0.5rem;
        }

        /* ====================================================
           TOP BAR
           ==================================================== */

        .top-bar {
            height: 68px;
            background: #101116;
            margin-left: -3rem;
            margin-right: -3rem;
            margin-top: -1rem;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            padding: 0 40px;
            color: white;
            font-family: Arial, sans-serif;
        }

        .top-bar-text {
            font-size: 15px;
            font-weight: 600;
            margin-right: 28px;
        }

        .github-icon {
            font-size: 20px;
        }

        /* ====================================================
           MAIN LOGIN AREA
           ==================================================== */

        .login-wrapper {
            min-height: calc(100vh - 68px);
            padding-top: 78px;
            padding-bottom: 40px;
        }

        /* ====================================================
           LEFT SIDE
           ==================================================== */

        .left-section {
            padding: 35px 45px 30px 25px;
            position: relative;
            min-height: 680px;
        }

        .brand-header {
            display: flex;
            align-items: center;
            gap: 18px;
            margin-bottom: 28px;
        }

        .gm-logo {
            width: 58px;
            height: 58px;
            background: linear-gradient(135deg, #6448ee, #8b5cf6);
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 30px;
            font-weight: 800;
            box-shadow: 0 10px 25px rgba(99, 72, 238, 0.25);
        }

        .brand-name {
            font-size: 22px;
            font-weight: 800;
            color: #121827;
            margin-bottom: 4px;
        }

        .brand-tagline {
            font-size: 14px;
            color: #697386;
        }

        .purple-line {
            width: 75px;
            height: 4px;
            border-radius: 5px;
            background: #6948ef;
            margin-bottom: 30px;
        }

        .hero-title {
            font-size: 38px;
            line-height: 1.15;
            font-weight: 800;
            color: #14213d;
            max-width: 600px;
            margin-bottom: 20px;
        }

        .hero-description {
            font-size: 17px;
            line-height: 1.7;
            color: #667085;
            max-width: 600px;
            margin-bottom: 35px;
        }

        /* ====================================================
           FEATURES
           ==================================================== */

        .feature-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 18px;
            max-width: 700px;
        }

        .feature-card {
            background: white;
            border: 1px solid #e7e9f2;
            border-radius: 15px;
            padding: 20px;
            display: flex;
            gap: 15px;
            box-shadow: 0 5px 20px rgba(25, 30, 50, 0.035);
        }

        .feature-icon {
            width: 42px;
            height: 42px;
            min-width: 42px;
            border-radius: 11px;
            background: #f0edff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
        }

        .feature-content h4 {
            margin: 0 0 7px 0;
            font-size: 15px;
            font-weight: 750;
            color: #18233b;
        }

        .feature-content p {
            margin: 0;
            font-size: 13px;
            line-height: 1.55;
            color: #747b8b;
        }

        /* ====================================================
           RIGHT LOGIN PANEL
           ==================================================== */

        .right-section {
            display: flex;
            justify-content: center;
            align-items: flex-start;
        }

        .login-card {
            width: 100%;
            max-width: 610px;
            background: transparent;
            padding: 20px 25px 30px 25px;
            text-align: center;
        }

        .lock-circle {
            width: 115px;
            height: 115px;
            border-radius: 50%;
            background: #f0edff;
            margin: 0 auto 30px auto;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 42px;
            box-shadow: inset 0 0 0 1px #ebe6ff;
        }

        .welcome-title {
            font-size: 36px;
            font-weight: 800;
            color: #14213d;
            margin-bottom: 10px;
        }

        .welcome-subtitle {
            font-size: 17px;
            color: #718096;
            margin-bottom: 35px;
        }

        /* ====================================================
           RESTRICTED BOX
           ==================================================== */

        .restricted-box {
            width: 100%;
            box-sizing: border-box;
            border: 1px solid #ddd6fe;
            background: #fbfaff;
            border-radius: 15px;
            padding: 21px 25px;
            display: flex;
            align-items: center;
            text-align: left;
            gap: 16px;
            color: #4938a8;
            font-size: 14px;
            font-weight: 700;
            margin-bottom: 35px;
        }

        .restricted-icon {
            font-size: 23px;
        }

        .signin-heading {
            font-size: 17px;
            font-weight: 750;
            color: #172033;
            margin-bottom: 18px;
        }

        /* ====================================================
           GOOGLE LOGIN BUTTON
           ==================================================== */

        div[data-testid="stButton"] {
            width: 100%;
        }

        div[data-testid="stButton"] button {
            width: 100% !important;
            min-height: 64px !important;
            border-radius: 13px !important;
            border: none !important;
            background: linear-gradient(90deg, #6547ed, #7048ed) !important;
            color: white !important;
            font-size: 17px !important;
            font-weight: 700 !important;
            box-shadow: 0 12px 25px rgba(100, 72, 237, 0.20) !important;
            transition: all 0.2s ease !important;
        }

        div[data-testid="stButton"] button:hover {
            transform: translateY(-2px);
            box-shadow: 0 15px 30px rgba(100, 72, 237, 0.28) !important;
        }

        /* ====================================================
           SECURITY NOTE
           ==================================================== */

        .security-note {
            width: 100%;
            box-sizing: border-box;
            margin-top: 25px;
            padding: 20px 22px;
            background: white;
            border: 1px solid #e5e7ef;
            border-radius: 14px;
            text-align: left;
            color: #667085;
            font-size: 14px;
            line-height: 1.6;
        }

        .security-note strong {
            color: #475467;
        }

        .security-footer {
            margin-top: 25px;
            color: #8a91a2;
            font-size: 13px;
        }

        /* ====================================================
           BOTTOM FOOTER
           ==================================================== */

        .landing-footer {
            border-top: 1px solid #e5e7ef;
            margin-top: 20px;
            padding-top: 20px;
            display: flex;
            justify-content: space-between;
            color: #8a91a2;
            font-size: 12px;
        }

        /* ====================================================
           MOBILE
           ==================================================== */

        @media (max-width: 900px) {

            .block-container {
                padding-left: 1.2rem !important;
                padding-right: 1.2rem !important;
            }

            .left-section {
                padding: 20px 10px;
            }

            .hero-title {
                font-size: 30px;
            }

            .feature-grid {
                grid-template-columns: 1fr;
            }

            .login-card {
                padding: 20px 10px;
            }

            .landing-footer {
                flex-direction: column;
                gap: 8px;
                text-align: center;
            }
        }

        </style>
        """,
        unsafe_allow_html=True
    )


    # ========================================================
    # TOP NAVIGATION BAR
    # ========================================================

    st.markdown(
        """
        <div class="top-bar">

            <div class="top-bar-text">
                Fork
            </div>

            <div class="github-icon">
                ◉
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


    # ========================================================
    # MAIN TWO COLUMN LAYOUT
    # ========================================================

    st.markdown(
        '<div class="login-wrapper">',
        unsafe_allow_html=True
    )

    left_col, right_col = st.columns(
        [1.05, 0.95],
        gap="large"
    )


    # ========================================================
    # LEFT SIDE
    # ========================================================

    with left_col:

        st.markdown(
            """
            <div class="left-section">

                <div class="brand-header">

                    <div class="gm-logo">
                        G
                    </div>

                    <div>

                        <div class="brand-name">
                            Germane Media LLC
                        </div>

                        <div class="brand-tagline">
                            GM Policy Assistant • Internal HR Portal
                        </div>

                    </div>

                </div>

                <div class="purple-line"></div>

                <div class="hero-title">
                    Your Intelligent HR Policy Companion
                </div>

                <div class="hero-description">
                    Get instant, accurate answers to your policy questions,
                    understand company guidelines, and connect with HR
                    for personalized support — anytime, anywhere.
                </div>

                <div class="feature-grid">

                    <div class="feature-card">

                        <div class="feature-icon">
                            📖
                        </div>

                        <div class="feature-content">

                            <h4>
                                Instant Policy Answers
                            </h4>

                            <p>
                                Accurate responses based on the
                                Germane Media LLC Employee Policy
                                Handbook.
                            </p>

                        </div>

                    </div>

                    <div class="feature-card">

                        <div class="feature-icon">
                            🔒
                        </div>

                        <div class="feature-content">

                            <h4>
                                Secure & Confidential
                            </h4>

                            <p>
                                Your conversations are private,
                                secure, and associated with your
                                company account.
                            </p>

                        </div>

                    </div>

                    <div class="feature-card">

                        <div class="feature-icon">
                            🎧
                        </div>

                        <div class="feature-content">

                            <h4>
                                Direct HR Support
                            </h4>

                            <p>
                                Escalate questions to HR or schedule
                                a confidential 15-minute discussion.
                            </p>

                        </div>

                    </div>

                    <div class="feature-card">

                        <div class="feature-icon">
                            👥
                        </div>

                        <div class="feature-content">

                            <h4>
                                For Employees Only
                            </h4>

                            <p>
                                This portal is restricted to active
                                Germane Media LLC employees.
                            </p>

                        </div>

                    </div>

                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


    # ========================================================
    # RIGHT SIDE
    # ========================================================

    with right_col:

        st.markdown(
            """
            <div class="right-section">

                <div class="login-card">

                    <div class="lock-circle">
                        🔒
                    </div>

                    <div class="welcome-title">
                        Welcome Back!
                    </div>

                    <div class="welcome-subtitle">
                        Sign in to access the GM Policy Assistant
                    </div>

                    <div class="restricted-box">

                        <div class="restricted-icon">
                            🔐
                        </div>

                        <div>
                            This portal is restricted to active
                            Germane Media LLC employees.
                        </div>

                    </div>

                    <div class="signin-heading">
                        Sign in with your company account
                    </div>

                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


        # ====================================================
        # GOOGLE LOGIN BUTTON
        # ====================================================

        login_button = st.button(
            "🔐  Sign in with Google",
            type="primary",
            width="stretch",
            key="google_login_button"
        )

        if login_button:
            st.login("google")


        # ====================================================
        # SECURITY INFORMATION
        # ====================================================

        st.markdown(
            """
            <div class="security-note">

                🏢 &nbsp;
                Please use your official
                <strong>@thegermanemedia.com</strong>
                Google Workspace account.

                <br><br>

                Your policy conversations are associated
                with your authenticated company account.

            </div>

            <div class="security-footer">

                🛡️ &nbsp;
                Protected by Google Workspace Authentication

            </div>
            """,
            unsafe_allow_html=True
        )


    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )


    # ========================================================
    # FOOTER
    # ========================================================

    st.markdown(
        """
        <div class="landing-footer">

            <div>
                🛡️ &nbsp; Secure • Private • Trusted
            </div>

            <div>
                © 2026 Germane Media LLC.
                All rights reserved.
                &nbsp; | &nbsp;
                Internal Use Only
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


    # ========================================================
    # STOP EXECUTION UNTIL LOGIN
    # ========================================================

    st.stop()
