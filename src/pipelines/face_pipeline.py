import numpy as np
import streamlit as st
from insightface.app import FaceAnalysis
from src.database.db import get_all_students

SIM_THRESHOLD = 0.5  # cosine similarity; tune on your own data

@st.cache_resource
def load_model():
    app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
    app.prepare(ctx_id=-1, det_size=(1280, 1280))  # large size helps with class photos
    return app

def get_face_embeddings(image_rgb):
    app = load_model()
    image_bgr = np.ascontiguousarray(image_rgb[:, :, ::-1] )         # InsightFace expects BGR
    faces = app.get(image_bgr)
    return [f.normed_embedding for f in faces] # already L2-normalised, 512-D

@st.cache_resource
def get_gallery():
    ids, embs = [], []
    for s in get_all_students():
        e = s.get("face_embedding")
        if e is not None:
            ids.append(int(s["student_id"]))
            embs.append(np.asarray(e, dtype=np.float32))
    if not embs:
        return None
    return np.array(ids), np.vstack(embs)

def refresh_gallery():
    get_gallery.clear()          # clears only this cache, not the models
    return get_gallery() is not None

def predict_attendance(class_image_np):
    encodings = get_face_embeddings(class_image_np)
    gallery = get_gallery()
    if gallery is None:
        return {}, [], len(encodings)

    ids, G = gallery
    detected = {}
    for enc in encodings:
        sims = G @ enc                       # cosine similarity (vectors are normalised)
        best = int(np.argmax(sims))
        if sims[best] >= SIM_THRESHOLD:
            detected[int(ids[best])] = True
    return detected, sorted(set(ids.tolist())), len(encodings)