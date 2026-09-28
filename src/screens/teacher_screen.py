from src.components.dialog_voice_attendance import voice_attendance_dialog
from src.components.dialog_attendance_results import attendance_results_dialog
from datetime import datetime
from src.database.config import supabase
from src.pipelines.face_pipeline import predict_attendance
from src.components.dialog_add_photo import add_photos_dialog
from src.components.dialog_share_subject import share_subject_dialog
from src.components.subject_card import subject_card
from src.components.dialog_create_subject import create_subject_dialog
from src.components.footer import footer_home
import streamlit as st
import time
from src.ui.base_layout import style_background_dashboard, style_base_layout
from src.components.header import header_dashboard
import numpy as np
import pandas as pd
from src.database.db import check_teacher_exists, create_teacher, teacher_login, get_teacher_subjects, get_attendance_for_teacher

def teacher_screen():
    style_background_dashboard()
    style_base_layout()
    
    if 'teacher_data' in st.session_state:
        teacher_dashboard()
    elif 'teacher_login_type' not in st.session_state or st.session_state.teacher_login_type=="login":
        teacher_screen_login()
    elif st.session_state.teacher_login_type=="register":
        teacher_screen_register()
    
def teacher_dashboard():
    teacher_data = st.session_state.teacher_data
    c1, c2 = st.columns(2, vertical_alignment="bottom", gap="xxlarge")
    with c1:
        header_dashboard()
    with c2: 
        if st.button("Logout", key="loginbackbtn", icon=":material/logout:"):
            st.session_state['is_logged_in'] = False
            del st.session_state.teacher_data
            st.rerun()

    if "current_teacher_tab" not in st.session_state:
        st.session_state.current_teacher_tab = 'take_attendance'

    st.header(f"Welcome, {teacher_data['name']}", text_alignment='center')
    st.space()

    tab1, tab2, tab3 = st.columns(3)

    with tab1:
        type1 = "primary" if st.session_state.current_teacher_tab == 'take_attendance' else "tertiary"
        if st.button("Take Attendance", width='stretch', icon=':material/ar_on_you:', type=type1):
            st.session_state.current_teacher_tab = 'take_attendance'
            st.rerun()
    with tab2:
        type2 = "primary" if st.session_state.current_teacher_tab == 'manage_subjects' else "tertiary"
        if st.button("Manage Subjects", width='stretch', icon=':material/book_ribbon:', type=type2):
            st.session_state.current_teacher_tab = 'manage_subjects'
            st.rerun()
    with tab3:
        type3 = "primary" if st.session_state.current_teacher_tab == 'attendance_records' else "tertiary"
        if st.button("Attendance Records", width='stretch', icon=':material/cards_stack:', type=type3):
            st.session_state.current_teacher_tab = 'attendance_records'
            st.rerun()


    st.divider()

    if st.session_state.current_teacher_tab == 'take_attendance':
        teacher_tab_take_attendance()
    elif st.session_state.current_teacher_tab == 'manage_subjects':
        teacher_tab_manage_subjects()
    elif st.session_state.current_teacher_tab == 'attendance_records':
        teacher_tab_attendance_records()


    footer_home()


def teacher_tab_take_attendance():
    teacher_id = st.session_state.teacher_data['teacher_id']
    st.header("Take Attendance")
    
    if 'attendance_images' not in st.session_state:
        st.session_state.attendance_images = []
    
    subjects = get_teacher_subjects(teacher_id)
    
    if not subjects:
        st.warning("You don't have any subjects, Please create one to take attendance")
        return
    
    subject_options = {
        f"{s['name']} - {s['subject_code']}": s['subject_id'] for s in subjects
    }

    col1, col2 = st.columns([3, 1], vertical_alignment='bottom')

    with col1: 
        selected_subject_label = st.selectbox('Select Subject', options = list(subject_options.keys()))

    with col2:
        if st.button('Add Photos', icon=':material/add_a_photo:', width='stretch'): 
            add_photos_dialog()

    selected_subject_id = subject_options[selected_subject_label]
    
    st.divider()

    if st.session_state.attendance_images:
        st.header("Added Photos")
        st.space()
        gallery_cols = st.columns(4)

        for idx, img in enumerate(st.session_state.attendance_images):
            with gallery_cols[idx % 4]:
                st.image(img, caption=f"Photo {idx+1}", use_container_width=True)

        st.space()
    has_photos = bool(st.session_state.attendance_images)
    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("Clear all Photos", icon=':material/clear:', type='tertiary', width="stretch", disabled=not has_photos):
            st.session_state.attendance_images = []
            st.rerun()
    with c2:
        if st.button('Run Face Analysis', icon=':material/face:', type='tertiary', width="stretch", disabled=not has_photos):
            with st.spinner("Scanning Classroom Images..."):
                all_detected_ids = {}

                for idx, img in enumerate(st.session_state.attendance_images):
                    img_np = np.array(img.convert('RGB'))
                    
                    detected, _, _ = predict_attendance(img_np)

                    if detected:
                        for sid in detected.keys():
                            student_id = int(sid)

                            all_detected_ids.setdefault(student_id, []).append(f'Photo {idx + 1}')

                enrolled_res = supabase.table("subject_students").select("*, students(*)").eq('subject_id', selected_subject_id).execute()
                enrolled_students = enrolled_res.data

                if not enrolled_students:
                    st.warning("No Student Enrolled in this course")
                else:
                    results, attendance_to_log = [], []

                    current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    for node in enrolled_students:
                        student = node['students']
                        sources = all_detected_ids.get(int(student['student_id']), [])
                        is_present = len(sources) > 0

                        results.append({
                            "Name": student['name'],
                            "ID": student['student_id'],
                            "Sources": ", ".join(sources) if is_present else "-",
                            "Status": "Present" if is_present else "Absent"
                        })

                        attendance_to_log.append({
                            'student_id': student['student_id'],
                            'subject_id': selected_subject_id,
                            'timestamp': current_timestamp,
                            'is_present': bool(is_present)
                        })
                attendance_results_dialog(pd.DataFrame(results), attendance_to_log)

    with c3:
        if st.button('Use Voice Attendance', type='tertiary', width='stretch', icon=":material/mic:"):
            voice_attendance_dialog(selected_subject_id)
                                
                        

        
        
def teacher_tab_manage_subjects():
    teacher_id = st.session_state.teacher_data['teacher_id']
    col1, col2 = st.columns(2, vertical_alignment="bottom")
    with col1:
        st.header("Manage Subjects")
    with col2:
        if st.button('Create new Subject', width='stretch', icon=':material/add:', type='tertiary'):
            create_subject_dialog(teacher_id)

    # List all Subjects
    subjects = get_teacher_subjects(teacher_id)
    if subjects:
        for sub in subjects:
            stats = [
                ("Students", sub['total_students']),
                ("Classes", sub['total_classes'])
            ]
            def share_btn():
                if st.button(f"Share Code: {sub['name']}", key=f"share_{sub['subject_code']}", icon=":material/share:", type='tertiary'):
                    share_subject_dialog(sub['name'], sub['subject_code'])
                st.space()

            subject_card(
                name=sub['name'],
                code=sub['subject_code'],
                section=sub['section'],
                stats=stats,
                footer_callback=share_btn
            )
    else:
        st.space()
        st.info("No subjects created yet, Create one above")
            


def teacher_tab_attendance_records():
    st.header("Attendance Records")
    st.space()
    teacher_id = st.session_state.teacher_data['teacher_id']

    records = get_attendance_for_teacher(teacher_id)

    if not records: 
        st.info("No records available")
        return

    data = []

    for r in records:
        ts = r.get('timestamp')

        data.append({
            "ts_group": ts.split('.')[0] if ts else None,
            "Time": datetime.fromisoformat(ts).strftime("%Y-%m-%d %I:%M %p") if ts else "N/A",
            "Subject": r['subjects']['name'],
            "Subject Code": r['subjects']['subject_code'],
            "is_present": bool(r['is_present'])
        })

    df = pd.DataFrame(data)

    summary = (
        df.groupby(['ts_group', "Time", "Subject", "Subject Code"]).agg(
            Present_Count = ('is_present', 'sum'),
            Total_Count = ('is_present', 'count')
        ).reset_index()
    )

    summary['Attendance Stats'] = (
        summary['Present_Count'].astype(str) + "/" + summary["Total_Count"].astype(str) + ' Students'
    )

    display_df = (summary.sort_values(by = 'ts_group', ascending=False)
        [['Time','Subject','Subject Code', 'Attendance Stats']]
        )

    st.dataframe(display_df, width='stretch', hide_index=True)
    



def login_teacher(teacher_username, teacher_password):
    if not teacher_username.strip() or not teacher_password.strip():
        st.error("Please enter your username and password")
        return False
    teacher = teacher_login(teacher_username, teacher_password)
    if teacher: 
        st.session_state['teacher_data'] = teacher
        st.session_state['user_role'] = 'teacher'
        st.session_state['is_logged_in'] = True
        return True
    return False
    

def teacher_screen_login(): 
    c1, c2 = st.columns(2, vertical_alignment="bottom")
    with c1:
        header_dashboard()
    with c2: 
        if st.button("Go back to Home", key="loginbackbtn"):
            st.session_state['login_type'] = None
            st.rerun()
    st.space()
    st.space()
    st.header("Login using Password")
    st.space()
    st.space()
    
    teacher_username = st.text_input("Enter username:", placeholder="Enter your Name")
    st.space()
    teacher_password = st.text_input("Enter password:", type='password', placeholder='Enter your Password')
    
    st.divider()

    btnc1, btnc2 = st.columns(2)

    with btnc1: 
        if st.button('Login', icon=':material/passkey:', icon_position='right', width='stretch'):
            if login_teacher(teacher_username, teacher_password):
                st.toast("Welcome Back!")
                time.sleep(1)
                st.rerun()
            else: 
                st.error("Invalid Username and password Combination")
    with btnc2:
        if st.button('Register Instead', icon=':material/add_moderator:', icon_position='right', width='stretch'):
            st.session_state['teacher_login_type'] = 'register'
            st.rerun()
        
        
def register_teacher(teacher_username, teacher_name, teacher_password, teacher_password_confirm):
    if not teacher_username or not teacher_name or not teacher_password or not teacher_password_confirm:
        return False, "All fields are required!!!"
    if check_teacher_exists(teacher_username):
        return False, "Username already taken!!!"
    if teacher_password != teacher_password_confirm:
        return False, "Passwords do not match!!!"
    
    try: 
        create_teacher(teacher_username, teacher_password, teacher_name)
        return True, "Registration successful, Login Now"
    except Exception as e:
        return False, "Unexpected Error!"
    
def teacher_screen_register():

    c1, c2 = st.columns(2, vertical_alignment="bottom")
    with c1:
        header_dashboard()
    with c2: 
        if st.button("Go back to Home", key="registerbackbtn"):
            st.session_state['teacher_login_type'] = None
            st.rerun()
    
    st.space()
    st.space()
    st.header("Register Your Teacher Profile")
    st.space()
    st.space()
    
    teacher_username = st.text_input("Enter username:", placeholder="Enter your username")
    st.space()
    teacher_name = st.text_input("Enter your Name:", placeholder="Enter your Name")
    st.space()
    teacher_password = st.text_input("Enter password:", type='password', placeholder='Enter your Password')
    st.space()
    teacher_password_confirm = st.text_input("Confirm your password:", type='password', placeholder='Confirm your Password')
    st.space()
    
    
    st.divider()

    btnc1, btnc2 = st.columns(2)

    with btnc1: 
        if st.button('Register Now', icon=':material/add_moderator:', icon_position='right', width='stretch'):
            success, message = register_teacher(teacher_username, teacher_name, teacher_password, teacher_password_confirm)
            if success: 
                st.success(message)
                time.sleep(2)
                st.session_state.teacher_login_type = 'login'
                st.rerun()
            else:
                st.error(message)
    with btnc2:
        if st.button('Login Instead', icon=':material/passkey:', icon_position='right', width='stretch'):
            st.session_state['teacher_login_type'] = 'login'
            st.rerun()



