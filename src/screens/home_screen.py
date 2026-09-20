import streamlit as st
from src.components.header import header_home
from src.ui.base_layout import style_base_layout, style_background_home, style_background_dashboard
from src.components.footer import footer_home

def home_screen():
    
    style_background_home()
    style_base_layout()
    
    header_home()
    col1, col2 = st.columns(2, gap="large")
    with col1:
        with st.container(key='teacher_container'):
            st.header("I'm a Teacher")
            st.image("https://res.cloudinary.com/mogsungf/image/upload/v1789292300/9e9d7a5a-6d19-471d-9919-2e2fffaba67d.png", width=150)
            if st.button("Teacher Portal", icon=":material/arrow_outward:", icon_position="right"):
                st.session_state['login_type'] = 'teacher'
                st.rerun() 
    with col2:
        with st.container(key='student_container'):
            st.header("I'm a Student")
            st.image("https://res.cloudinary.com/mogsungf/image/upload/v1789292051/b751f9d3-f6f6-449a-aeff-a677233ffad8.png", width=150)
            if st.button("Student Portal", icon=":material/arrow_outward:", icon_position="right"):
                st.session_state['login_type'] = 'student'
                st.rerun() 
    footer_home()