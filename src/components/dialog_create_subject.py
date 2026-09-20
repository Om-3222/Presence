import streamlit as st
from src.database.db import create_subject 


@st.dialog("Create new Subject")
def create_subject_dialog(teacher_id):
    st.write("Enter the details of new Subject:")
    st.space()
    sub_code = st.text_input("Subject Code", placeholder='BCS401')
    st.space()
    sub_name = st.text_input("Subject Name", placeholder='Analysis and Design of Algorithms')
    st.space()
    sub_section = st.text_input("Subject Section", placeholder='A')
    st.space()
    

    if st.button("Create Subject Now", width='stretch'):
        if sub_code and sub_name and sub_section:
            try: 
                create_subject(teacher_id, sub_code, sub_name, sub_section)
                st.toast("Subject Created Successfully")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")
        else: 
            st.warning("All fields are required")