# ============================================================
# GOOGLE AUTHENTICATION / LOGIN PAGE
# ============================================================

if not st.user.is_logged_in:

    # -----------------------------
    # LOGIN PAGE CSS
    # -----------------------------

    st.markdown(
        """
        <style>

        /* Remove Streamlit default top spacing */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
            max-width: 1400px !important;
        }

        /* Main login background */
        .login-page {
            min-height: 88vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 30px;
            background:
                radial-gradient(
                    circle at 10% 20%,
                    rgba(99, 102, 241, 0.10),
                    transparent 35%
                ),
                radial-gradient(
                    circle at 90% 80%,
                    rgba(139, 92, 246, 0.10),
                    transparent 35%
                );
            border-radius: 24px;
        }

        /* Main two-column container */
        .login-container {
            width: 100%;
            max-width: 1250px;
            display: grid;
            grid-template-columns: 1.05fr 0.95fr;
            gap: 45px;
            align-items: center;
        }

        /* --------------------------------
           LEFT SIDE
        -------------------------------- */

        .brand-section {
            padding: 40px 25px;
        }

        .brand-header {
            display: flex;
            align-items: center;
            gap: 20px;
            margin-bottom: 35px;
        }

        .brand-logo {
            width: 82px;
            height: 82px;
            border-radius: 20px;
            background: linear-gradient(
                135deg,
                #4f46e5,
                #7c3aed
            );
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 48px;
            font-weight: 800;
            box-shadow:
                0 15px 35px rgba(79, 70, 229, 0.25);
        }

        .brand-company {
            font-size: 38px;
            font-weight: 800;
            color: #17213a;
            letter-spacing: -1.5px;
        }

        .brand-product {
            margin-top: 5px;
            font-size: 18px;
            font-weight: 700;
            color: #5b4ce1;
        }

        .brand-line {
            width: 70px;
            height: 4px;
            border-radius: 10px;
            background: linear-gradient(
                90deg,
                #4f46e5,
                #8b5cf6
            );
            margin-top: 22px;
        }

        .brand-heading {
            font-size: 30px;
            font-weight: 800;
            color: #17213a;
            margin-top: 35px;
            margin-bottom: 15px;
        }

        .brand-description {
            max-width: 650px;
            font-size: 17px;
            line-height: 1.75;
            color: #53617a;
        }

        /* Features */

        .features-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 18px;
            margin-top: 40px;
        }

        .feature-card {
            padding: 20px;
            border-radius: 18px;
            background: rgba(255,255,255,0.75);
            border: 1px solid rgba(99,102,241,0.10);
            box-shadow:
                0 10px 30px rgba(15,23,42,0.05);
        }

        .feature-icon {
            font-size: 27px;
            margin-bottom: 10px;
        }

        .feature-title {
            font-size: 16px;
            font-weight: 800;
            color: #17213a;
            margin-bottom: 6px;
        }

        .feature-text {
            font-size: 13px;
            line-height: 1.6;
            color: #64748b;
        }

        /* --------------------------------
           RIGHT SIDE
        -------------------------------- */

        .login-card {
            background: rgba(255,255,255,0.96);
            border: 1px solid #e2e8f0;
            border-radius: 25px;
            padding: 45px;
            box-shadow:
                0 25px 70px rgba(15,23,42,0.10);
        }

        .login-icon {
            width: 90px;
            height: 90px;
            margin: 0 auto 20px auto;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #f0edff;
            font-size: 42px;
        }

        .login-title {
            text-align: center;
            font-size: 34px;
            font-weight: 800;
            color: #17213a;
            margin-bottom: 8px;
        }

        .login-subtitle {
            text-align: center;
            color: #718096;
            font-size: 16px;
            margin-bottom: 30px;
        }

        .restricted-box {
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 18px;
            border-radius: 14px;
            background: #f7f5ff;
            border: 1px solid #e5e0ff;
            margin-bottom: 30px;
        }

        .restricted-icon {
            font-size: 28px;
        }

        .restricted-text {
            color: #5139c7;
            font-size: 14px;
            line-height: 1.5;
            font-weight: 700;
        }

        .login-label {
            text-align: center;
            color: #17213a;
            font-weight: 700;
            font-size: 17px;
            margin-bottom: 15px;
        }

        .security-box {
            margin-top: 25px;
            padding: 20px;
            border-radius: 14px;
            background: #fafbff;
            border: 1px solid #e5e7eb;
        }

        .security-title {
            font-size: 15px;
            font-weight: 700;
            color: #17213a;
            margin-bottom: 8px;
        }

        .security-text {
            font-size: 13px;
            line-height: 1.6;
            color: #64748b;
        }

        .protected-text {
            text-align: center;
            margin-top: 28px;
            color: #718096;
            font-size: 13px;
        }

        .footer-text {
            text-align: center;
            margin-top: 25px;
            color: #94a3b8;
            font-size: 12px;
        }

        /* Mobile */

        @media (max-width: 900px) {

            .login-container {
                grid-template-columns: 1fr;
                gap: 20px;
            }

            .brand-section {
                padding: 20px;
            }

            .brand-company {
                font-size: 30px;
            }

            .brand-heading {
                font-size: 25px;
            }

            .features-grid {
                grid-template-columns: 1fr;
            }

            .login-card {
                padding: 30px 20px;
            }

        }

        </style>
        """,
        unsafe_allow_html=True
    )

    # ========================================================
    # LOGIN PAGE HTML
    # ========================================================

    st.markdown(
        """
        <div class="login-page">

            <div class="login-container">

                <!-- =========================
                     LEFT BRANDING SECTION
                ========================== -->

                <div class="brand-section">

                    <div class="brand-header">

                        <div class="brand-logo">
                            G
                        </div>

                        <div>

                            <div class="brand-company">
                                Germane Media LLC
                            </div>

                            <div class="brand-product">
                                GM Policy Assistant • Internal HR Portal
                            </div>

                            <div class="brand-line"></div>

                        </div>

                    </div>


                    <div class="brand-heading">
                        Your Intelligent HR Policy Companion
                    </div>

                    <div class="brand-description">
                        Get instant, accurate answers to your policy
                        questions, understand company guidelines, and
                        connect with HR for personalized support —
                        anytime, anywhere.
                    </div>


                    <!-- FEATURES -->

                    <div class="features-grid">

                        <div class="feature-card">

                            <div class="feature-icon">
                                📖
                            </div>

                            <div class="feature-title">
                                Instant Policy Answers
                            </div>

                            <div class="feature-text">
                                Get accurate responses based on the
                                Germane Media LLC Employee Policy Handbook.
                            </div>

                        </div>


                        <div class="feature-card">

                            <div class="feature-icon">
                                🔐
                            </div>

                            <div class="feature-title">
                                Secure & Confidential
                            </div>

                            <div class="feature-text">
                                Your conversations are associated with
                                your authenticated company account.
                            </div>

                        </div>


                        <div class="feature-card">

                            <div class="feature-icon">
                                🎧
                            </div>

                            <div class="feature-title">
                                Direct HR Support
                            </div>

                            <div class="feature-text">
                                Escalate questions to HR or schedule a
                                confidential 15-minute discussion.
                            </div>

                        </div>


                        <div class="feature-card">

                            <div class="feature-icon">
                                👥
                            </div>

                            <div class="feature-title">
                                For Employees Only
                            </div>

                            <div class="feature-text">
                                This portal is restricted to active
                                Germane Media LLC employees.
                            </div>

                        </div>

                    </div>

                </div>


                <!-- =========================
                     RIGHT LOGIN CARD
                ========================== -->

                <div class="login-card">

                    <div class="login-icon">
                        🔒
                    </div>

                    <div class="login-title">
                        Welcome Back!
                    </div>

                    <div class="login-subtitle">
                        Sign in to access the GM Policy Assistant
                    </div>


                    <div class="restricted-box">

                        <div class="restricted-icon">
                            🔐
                        </div>

                        <div class="restricted-text">
                            This portal is restricted to active
                            Germane Media LLC employees.
                        </div>

                    </div>


                    <div class="login-label">
                        Sign in with your company account
                    </div>

                </div>

            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


    # ========================================================
    # GOOGLE LOGIN BUTTON
    #
    # This MUST remain outside the HTML above.
    # Streamlit buttons cannot be placed inside raw HTML.
    # ========================================================

    login_col_left, login_col, login_col_right = st.columns(
        [1, 2, 1]
    )

    with login_col:

        if st.button(
            "🔐  Sign in with Google",
            type="primary",
            width="stretch"
        ):

            st.login()


    # ========================================================
    # COMPANY ACCOUNT INFORMATION
    # ========================================================

    st.markdown(
        """
        <div class="login-container"
             style="display:block; max-width:760px; margin:0 auto;">

            <div class="security-box">

                <div class="security-title">
                    🏢 Use your official company account
                </div>

                <div class="security-text">

                    Please use your official
                    <strong>@thegermanemedia.com</strong>
                    Google Workspace account.

                    <br><br>

                    Your policy conversations are associated with
                    your authenticated company account.

                </div>

            </div>

            <div class="protected-text">
                🛡️ Protected by Google Workspace Authentication
            </div>

            <div class="footer-text">
                © Germane Media LLC • Internal Use Only
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.stop()
