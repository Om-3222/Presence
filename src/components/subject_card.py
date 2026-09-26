import streamlit as st
def subject_card(name, code, section, stats=None, footer_callback=None):
    html = f"""
        <div class="subject-card-main">
        <h3 class='subject-card-h3'>{name}</h3>
        <div style="margin-left:20px;">
        <p style="color:#B9A58C; font-family: 'Montserrat', sans-serif; font-weight: 600; margin:10px 0;">Code : <span style="background:#F8F5EE; color:#171717; border: 1px solid #B9A58C; padding:2px 4px; border-radius:5px; margin-right:8px;">{code} </span> | Section : {section}</p>
        
        """
    
    if stats:
        html+= """
        <div style="display:flex; gap:8px; flex-wrap:wrap; font-family: 'Montserrat', sans-serif; margin-top: 15px;">
        """
        for label, value in stats:
            html+= f'<div style="background: #F8F5EE; color: #171717; border: 1px solid #E5DDD2; padding:5px 12px; border-radius:12px; font-size:0.9rem; font-weight: 600;"><b style="color: #C96A3D; font-family: \'Headland One\', sans-serif;">{value}</b> {label} </div>'
        
        html+= """
        </div>
        </div>
        """
    st.space()
    st.space()
    st.markdown(html, unsafe_allow_html=True)

    if footer_callback:
        footer_callback()