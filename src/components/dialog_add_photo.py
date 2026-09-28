import streamlit as st
from PIL import Image 

@st.dialog('Capture or Upload Photo')
def add_photos_dialog():
    
    st.write('add classroom photos to scan for attendance')

    if 'photo_tab' not in st.session_state:
        st.session_state.photo_tab = 'camera'

    t1, t2 = st.columns(2)

    with t1:
        type_camera = "primary" if st.session_state.photo_tab == 'camera' else "tertiary"
        if st.button("Camera", icon=":material/photo:", type=type_camera, width='stretch'):
            st.session_state.photo_tab = 'camera'
    with t2:
        type_upload = "primary" if st.session_state.photo_tab == 'upload' else "tertiary"
        if st.button("Upload", icon=":material/upload:", type=type_upload, width='stretch'):
            st.session_state.photo_tab = 'upload'

    if st.session_state.photo_tab == 'camera':
        cam_photo = st.camera_input('Click photo of the classroom', key='dialog_cam_photo')
        if cam_photo:
            st.session_state.attendance_images.append(Image.open(cam_photo))
            st.toast('Photo Captured')
            st.rerun()

    if st.session_state.photo_tab == 'upload':
        uploaded_files = st.file_uploader('choose image files', type=['jpg', 'png', 'jpeg'], accept_multiple_files=True, max_upload_size=5)
        if uploaded_files:
            for file in uploaded_files:
                st.session_state.attendance_images.append(Image.open(file))
            st.success(f"{len(uploaded_files)} Photos Added")
            st.rerun()


    st.divider()
    if st.button("Done", width='stretch', type='primary'):
        st.rerun()