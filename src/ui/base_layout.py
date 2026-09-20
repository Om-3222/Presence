import streamlit as st

# Primary #171717
# Background #F5F1EA
# Accent #C96A3D
# Secondary #B9A58C
# Soft #E5DDD2
# White #FFFFFF


def style_background_home():
    st.markdown(
        """
        <style>
            .stApp {
                background-color: #F5F1EA;
            }
        </style>
        """
    , unsafe_allow_html=True)

def style_background_dashboard():
    st.markdown(
        """
        <style>
            .stApp {
                background-color: #F5F1EA;
            }
        </style>
        """
    , unsafe_allow_html=True)

def style_base_layout():
    with open("src/ui/style.css") as f:
        css = f.read()
    st.markdown(
        f"""
        <style>
            {css}
        </style>
        """
    , unsafe_allow_html=True)