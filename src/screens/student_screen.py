from src.pipelines.voice_pipeline import get_voice_embedding
from src.pipelines.face_pipeline import get_face_embeddings, train_classifier
from src.database.db import get_all_students, create_student
from src.pipelines.face_pipeline import predict_attendance
from src.components.footer import footer_home
from src.components.header import header_dashboard
from src.ui.base_layout import style_base_layout
from src.ui.base_layout import style_background_dashboard
import numpy as np
from PIL import Image
import streamlit as st
import time




def student_dashboard():
    st.header("STUDENT DASHBOARD")

def student_screen():
    show_registration_screen = False

    style_background_dashboard()
    style_base_layout()

    if "student_data" in st.session_state:
        student_dashboard()
        return

    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1: 
        header_dashboard()
    with c2: 
        if st.button("Go back to home", key='loginbackbtn'):
            st.session_state['login_type'] = None
            st.rerun()

    st.header("Login using FaceID", text_alignment='center')
    st.space()
    st.space()

    
    photo_source = st.camera_input("Position your face in the center")
    if photo_source:
        img = np.array(Image.open(photo_source))

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
                        img = np.array(Image.open(photo_source))
                        encodings = get_face_embeddings(img)
                        if encodings:
                            face_emb = encodings[0].tolist()
                            
                            voice_emb = None 

                            if audio_data: 
                                voice_emb = get_voice_embedding(audio_data.read())

                            response_data = create_student(new_name, face_embedding=face_emb, voice_embedding=voice_emb)
                            print(response_data)

                            if response_data:
                                train_classifier()
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