# Face Image 
# Face Detector (dlib) 
# shape predictor (sp) -> landmarks
# ResNet (facerec) -> embedding (128 D)
# SVM classifier
# Student ID

import dlib 
import numpy as np
import face_recognition_models
from sklearn.svm import SVC 
from sklearn.calibration import CalibratedClassifierCV
import streamlit as st 

from src.database.db import get_all_students 


@st.cache_resource
def load_dlib_models(): 
    
    # detector the face (rectangular box / bounding box)
    # get_frontal_face_detector: it will load the dlib detector model from the dlib library
    # this model is used to detect the face in the image
    # no of faces, location of the faces in the images etc 
    detector = dlib.get_frontal_face_detector()


    # shape predictor to detect landmarks in the face (eyes, nose, mouth)
    sp = dlib.shape_predictor(
        face_recognition_models.pose_predictor_model_location()
    )


    # face recognition model (ResNet) -> embedding vector (128D)
    facerec = dlib.face_recognition_model_v1(
        face_recognition_models.face_recognition_model_location()
    )

    return detector, sp, facerec

# 1. Detect Faces in Image 
# 2. for each face get landmarks 
# 3. for those landmarks get embeddings 
# 4. all the encodings are stores in encodings []
def get_face_embeddings(image_np):
    detector, sp, facerec = load_dlib_models() 

    # Try detection with increasing upsample factors
    faces = detector(image_np, 1)
    # print(f"[face_pipeline] upsample=1 → faces detected: {len(faces)}")
    
    if len(faces) == 0:
        faces = detector(image_np, 2)
        # print(f"[face_pipeline] upsample=2 → faces detected: {len(faces)}")
    
    if len(faces) == 0:
        # Try grayscale as a last resort
        gray = np.mean(image_np, axis=2).astype(np.uint8) if image_np.ndim == 3 else image_np
        faces = detector(gray, 2)
        # print(f"[face_pipeline] grayscale upsample=2 → faces detected: {len(faces)}")
        if len(faces) > 0:
            image_np = image_np  # keep original RGB for embedding extraction

    encodings = [] 

    for face in faces:
        shape = sp(image_np, face) # landmarks (left eye, right eye, nose, corners of mouth etc.) --> 68 points
        face_descriptor = facerec.compute_face_descriptor(image_np, shape, 1) # embedding of the face (128D vector)

        encodings.append(np.array(face_descriptor))

    return encodings

# 1. get all the students from the DB 
# 2. for each student add their embedding (x) and student ID (y) to X and y 
# 3. train svc classifier
@st.cache_resource
def get_trained_model():
    X = []
    y = []

    student_db = get_all_students()

    if not student_db:
        return None

    for student in student_db:
        embedding = student.get('face_embedding')
        if embedding:
            X.append(np.array(embedding))
            y.append(student.get('student_id'))

    if len(X) == 0:
        return None

    clf = CalibratedClassifierCV(SVC(), ensemble=False)

    try:
        clf.fit(X, y)
    except ValueError:
        pass

    return {'clf': clf, 'X': X, 'y': y}
    

# 1. clear old model from cache
# 2. Train a new model in case of a new face(new student)
def train_classifier():
    st.cache_resource.clear()
    model_data = get_trained_model()
    return bool(model_data)


# 1. get embeddings for all the faces in the image
# 2. get trained model
# 3. for each encoding, using the model predict the student id and convert from numpy.int64 to int
# 4. if predicted value is < resemblence threshold then add to detected students dict
def predict_attendance(class_image_np):
    encodings = get_face_embeddings(class_image_np)
    # print("encodings", encodings)
    detected_students = {}

    model_data = get_trained_model()

    if not model_data:
        return detected_students, [], len(encodings) if bool(encodings) else 0

    clf = model_data['clf']
    X_train = model_data['X']
    y_train = model_data['y']
    
    all_students = sorted(list(set(y_train)))

    for encoding in encodings: 
        if len(all_students) >= 2:
            predicted_id = int(clf.predict([encoding])[0])
        else: 
            predicted_id = int(all_students[0])

        student_embedding = X_train[y_train.index(predicted_id)]

        best_match_score = np.linalg.norm(student_embedding - encoding)

        resemblance_threshold = 0.6 # this is the upper limit of the distance between the embeddings

        if best_match_score <= resemblance_threshold:
            detected_students[predicted_id] = True

    return detected_students, all_students, len(encodings)