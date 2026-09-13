import streamlit as st

def header_home():
    
    logo_url = "https://res.cloudinary.com/mogsungf/image/upload/v1789280116/logo.png"
        
    st.markdown(
        f"""
        
        <div class="header">
            <img src="{logo_url}" alt="Logo" class="logo">
            <h1 class="name">Presence</h1>
        </div>
        
        """, unsafe_allow_html=True
    )