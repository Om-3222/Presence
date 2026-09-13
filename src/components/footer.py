import streamlit as st 

def footer_home(): 
    st.markdown(
        """
        <div class="footer">
            <p class="footer-text">An AI Powered Attendance App.</p>
        </div>
        """, unsafe_allow_html=True
    )