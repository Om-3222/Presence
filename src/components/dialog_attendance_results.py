from src.database.db import create_attendance
import streamlit as st


def show_attendance_results(df, logs):
    st.write('Please review attendance before confirming.')
    st.space()

    with st.container(border=True, width=1500, height='stretch'):
        st.dataframe(df, hide_index=True, width='stretch')

    st.space()
    col1, col2 = st.columns(2)

    with col1:
        if st.button('Discard', width='stretch', icon=':material/close:', type='tertiary'):
            if 'attendance_images' in st.session_state:
                st.session_state.attendance_images = []
            if 'voice_attendance_results' in st.session_state:
                st.session_state.voice_attendance_results = None
            st.rerun()

    with col2:
        if st.button('Confirm & Save', width='stretch', type='primary', icon=':material/save:'):
            try:
                create_attendance(logs)
                st.toast('Attendance Taken!', icon=':material/check_circle:')
                if 'attendance_images' in st.session_state:
                    st.session_state.attendance_images = []
                if 'voice_attendance_results' in st.session_state:
                    st.session_state.voice_attendance_results = None
                st.rerun()
            except Exception as e:
                st.error("Sync Failed!")


@st.dialog("Attendance Results")
def attendance_results_dialog(df, logs):
    show_attendance_results(df, logs)
    