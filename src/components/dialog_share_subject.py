from sympy.core import kind
import segno
import streamlit as st
import io 

@st.dialog("Share Class Link")
def share_subject_dialog(subject_name, subject_code):
    app_domain = "presence-main.streamlit.app"
    join_url = f"https://{app_domain}?join-code={subject_code}"

    qr = segno.make(join_url)

    out = io.BytesIO()

    qr.save(out, kind="png", scale=10, border=1)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Copy Link")
        st.space()
        st.code(join_url, language='text')
        st.space()
        st.code(subject_code, language='text')
        st.space()
        st.info('Copy this link to share on Whatsapp or Email')

    with col2:
        st.markdown('### Scan to Join')
        st.image(out.getvalue(), width=200, caption='QR code for Joining Class')