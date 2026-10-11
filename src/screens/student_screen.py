from src.pipelines.face_pipeline import refresh_gallery
from src.components.subject_card import subject_card
from src.database.db import get_student_subjects, get_student_attendance, get_all_students, create_student, unenroll_student_to_subject
from src.pipelines.voice_pipeline import get_voice_embedding
from src.pipelines.face_pipeline import get_face_embeddings
from src.pipelines.face_pipeline import predict_attendance
from src.components.footer import footer_home
from src.components.header import header_dashboard
from src.ui.base_layout import style_base_layout
from src.ui.base_layout import style_background_dashboard
import numpy as np
from PIL import Image
import streamlit as st
import time
from src.components.dialog_enroll import enroll_dialog




def student_dashboard():
    student_data = st.session_state.student_data
    student_id = student_data['student_id']

    c1, c2 = st.columns(2, vertical_alignment='bottom', gap='xxlarge')
    with c1:
        header_dashboard()
    with c2:
        if st.button("Logout", key='loginbackbtn', icon=":material/logout:"):
            st.session_state['is_logged_in'] = False
            del st.session_state.student_data
            st.rerun()
    
    st.header(f"Welcome, {student_data['name']}!", text_alignment="center")
    st.divider()

    c1, c2 = st.columns(2, vertical_alignment='bottom')
    with c1:
        st.header("Your Enrolled Subjects")
    with c2:
        if st.button("Enroll in a Subject", type='tertiary', width='stretch'):
            enroll_dialog()

    with st.spinner('Loading your subjects...'):
        subjects = get_student_subjects(student_id)
        logs = get_student_attendance(student_id)

    stats_map = {}

    for log in logs: 
        sub_id = log['subject_id']

        if sub_id not in stats_map:
            stats_map[sub_id] = {'total': 0, 'attended': 0}
        
        stats_map[sub_id]['total'] += 1
        if log['is_present']:
            stats_map[sub_id]['attended'] += 1

    cols = st.columns(2)
    for i, sub_node in enumerate(subjects):
        sub = sub_node['subjects']
        sub_id = sub['subject_id']
        
        stats = stats_map.get(sub_id, {'total': 0, 'attended': 0})

        def unenroll_btn():
            if st.button('Unenroll from the course', type='tertiary', width='stretch', icon=':material/delete_forever:'):
                unenroll_student_to_subject(student_id, sub_id)
                st.toast('Unenrolled Successfully!')
                time.sleep(1)
                st.rerun()


        with cols[i % 2]:
            subject_card(
                name = sub['name'], 
                code = sub['subject_code'],
                section = sub['section'], 
                stats = [
                    ('Total', stats['total']),
                    ('Attended', stats['attended'])
                ],
                footer_callback=unenroll_btn
            )
        

    footer_home()
    

def student_screen():
    show_registration_screen = False

    style_background_dashboard()
    style_base_layout()

    if "student_data" in st.session_state:
        student_dashboard()
        return

    c1, c2 = st.columns(2, vertical_alignment='bottom', gap='xxlarge')
    with c1: 
        header_dashboard()
    with c2: 
        if st.button("Go back to home", key='loginbackbtn'):
            st.query_params.clear()
            st.session_state['login_type'] = None
            st.rerun()

    st.header("Login using FaceID", text_alignment='center')
    st.space()
    st.space()

    
    photo_source = st.camera_input("Position your face in the center")
    if photo_source:
        img = np.array(Image.open(photo_source).convert('RGB'))

        with st.spinner("AI is scanning..."):
            detected, all_ids, num_faces = predict_attendance(img)

            if num_faces == 0:
                st.warning("Face is not found!")
            elif num_faces > 1: 
                st.warning("Multiple faces Detected.")
            else: 
                if detected:
                    student_id = list(detected.keys())[0]
                    all_students = get_all_students()
                    student = next((s for s in all_students if s['student_id'] == student_id), None)

                    if student: 
                        st.session_state.is_logged_in = True
                        st.session_state.user_role = 'student'
                        st.session_state.student_data = student
                        st.toast("Welcome Back! ")
                        time.sleep(1)
                        st.rerun()
                    
                else: 
                    st.info('Face not Recognized! You might be a new Student!')
                    show_registration_screen = True
    if show_registration_screen:
        with st.container(border=True):
            st.header("Register new Profile")
            new_name = st.text_input("Enter your name", placeholder="Peter Parker")

            st.header('Optional: Voice Enrollment')
            st.space()
            st.info("Enroll for voice only attendance")
            st.space()

            audio_data = None

            try:
                audio_data = st.audio_input("Record a short phrase like: I am present and my name is Peter")
                st.space()
            except Exception:
                st.error("Audio Data failed!")

            if st.button('Create Account'):
                if new_name:
                    with st.spinner("Creating Profile..."):
                        img = np.array(Image.open(photo_source).convert('RGB'))
                        encodings = get_face_embeddings(img)
                        if encodings:
                            face_emb = encodings[0].tolist()
                            
                            voice_emb = None 

                            if audio_data: 
                                voice_emb = get_voice_embedding(audio_data.read())

                            response_data = create_student(new_name, face_embedding=face_emb, voice_embedding=voice_emb)

                            if response_data:
                                refresh_gallery()
                                st.session_state.is_logged_in = True
                                st.session_state.user_role = 'student'
                                st.session_state.student_data = response_data[0]
                                st.toast("Profile Created Successfully! ")
                                time.sleep(1)
                                st.rerun()
                        else:
                            st.error("Couldn't capture your facial features for registration")
                else:
                    st.warning("Please Enter Your Name!")

    
    footer_home()