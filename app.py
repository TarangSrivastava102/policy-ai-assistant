
col_main, col_right = st.columns([3, 1.2])

with col_main:
    st.markdown('<div class="brand-title">GM Policy Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-sub">Ask questions, verify rules, and connect with HR.</div>', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="info-card">
            <b>🔒 Private HR Conversation</b><br>
            <span style="font-size:12px;color:#667085;">
            Your chat session is associated with your authenticated employee account.
            HR may access transcripts for support and policy administration.
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            if message["role"] == "assistant":
                c1, c2, _ = st.columns([1,1,4])
                with c1:
                    if st.button("✅ Satisfied", key=f"sat_{idx}"):
                        st.toast("Thank you for your feedback!")
                with c2:
                    if st.button("❌ Not Satisfied", key=f"notsat_{idx}"):
                        st.session_state.unsatisfied_msg_idx = idx
                        st.session_state.hr_email_sent = False
                        st.rerun()

                if st.session_state.unsatisfied_msg_idx == idx:
                    st.warning("We're sorry we couldn't fully resolve your question. You can contact HR or schedule a confidential 15-minute discussion.")
                    e1, e2 = st.columns(2)
                    with e1:
                        if st.button("📧 Send to HR", key=f"sendhr_{idx}", use_container_width=True):
                            try:
                                # Reuse the original transcript email function from this portal.
                                if not smtp_is_configured():
                                    raise RuntimeError("SMTP is not configured.")
                                smtp_email = str(get_secret("SMTP_EMAIL")).strip()
                                smtp_password = str(get_secret("SMTP_PASSWORD")).strip()
                                msg = EmailMessage()
                                msg["Subject"] = f"HR Assistance Required - {st.session_state.emp_name}"
                                msg["From"] = smtp_email
                                msg["To"] = HR_EMAIL
                                msg["Reply-To"] = st.session_state.emp_email
                                transcript = "\n\n".join(
                                    ("EMPLOYEE" if m["role"]=="user" else "GM POLICY ASSISTANT") + ":\n" + m["content"]
                                    for m in st.session_state.messages
                                )
                                msg.set_content(
                                    f"Employee: {st.session_state.emp_name}\n"
                                    f"Email: {st.session_state.emp_email}\n\n"
                                    f"Conversation:\n{transcript}"
                                )
                                with smtplib.SMTP(str(get_secret("SMTP_HOST","smtp.gmail.com")), int(get_secret("SMTP_PORT",587)), timeout=30) as server:
                                    server.starttls()
                                    server.login(smtp_email, smtp_password)
                                    server.send_message(msg)
                                st.session_state.hr_email_sent = True
                                st.success("Your conversation has been sent to HR.")
                            except Exception as e:
                                st.error(f"Unable to notify HR: {e}")
                    with e2:
                        st.link_button("📅 Schedule HR Call", HR_BOOKING_URL, use_container_width=True)

    user_query = st.chat_input("Ask a policy question...")
    if user_query:
        st.session_state.messages.append({"role":"user","content":user_query})
        st.session_state.unsatisfied_msg_idx = None
        try:
            with st.spinner("Searching Germane Media Policy Handbook..."):
                response = query_policy_ai(user_query, st.session_state.messages)
            st.session_state.messages.append({
                "role":"assistant",
                "content":response + "\n\n---\n*Notice: Answers are derived from the Germane Media LLC Policy Handbook. Employment Agreement terms prevail where applicable.*"
            })
            st.rerun()
        except Exception as e:
            st.error(str(e))

with col_right:
    st.markdown("### 📅 Schedule HR Discussion")
    st.caption("Need to speak directly with HR? Book a 15-minute confidential discussion.")
    st.link_button("📅 Schedule 15-Minute HR Discussion", HR_BOOKING_URL, type="primary", use_container_width=True)
    st.divider()
    st.markdown("💬 **Need immediate help?**")
    st.link_button("💬 Contact HR on Google Chat", DIRECT_GOOGLE_CHAT_HR, use_container_width=True)
    st.divider()
    st.markdown("💡 **Suggested Questions**")
    for q in [
        "How many leaves do I get per month?",
        "When am I eligible for appraisal consideration?",
        "What is the reimbursement process?",
        "What is the timeline for FNF settlement?",
    ]:
        if st.button(f"❓ {q}", key=f"suggested_{q}", use_container_width=True):
            st.session_state.messages.append({"role":"user","content":q})
            st.rerun()
