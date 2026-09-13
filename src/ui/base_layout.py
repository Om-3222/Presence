import streamlit as st

# background (deep navy) #0D3B66
# text (cream) #FAF0CA
# accent (orange) #EE964B
# secondary highlight (golden yellow) #F4D35E

with open("src/ui/style.css") as f:
    css = f.read()

def style_background_home():
    st.markdown(
        """
        <style>
            .stApp {
                background-color: #F4D35E;
            }
        </style>
        """
    , unsafe_allow_html=True)

def style_background_dashboard():
    st.markdown(
        """
        <style>
            .stApp {
                background-color: #F4D35E;
            }
        </style>
        """
    , unsafe_allow_html=True)

def style_base_layout():
    st.markdown(
        f"""
        <style>
            {css}
        </style>
        """
    , unsafe_allow_html=True)