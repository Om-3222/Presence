import numpy as np
import streamlit as st
from insightface.app import FaceAnalysis
from src.database.db import get_all_students
import cv2

# Minimum cosine similarity for two faces to count as the same person.
# Separate values so login and class photos can be tuned independently.
LOGIN_THRESHOLD = 0.5
CLASS_THRESHOLD = 0.5


def _build_app(det_size, det_thresh):
    # buffalo_l bundles the detector (SCRFD) and the embedding model (ArcFace).
    # allowed_modules skips the unused models (gender/age, 3D landmarks) to save memory.
    app = FaceAnalysis(
        name="buffalo_l",
        providers=["CPUExecutionProvider"],
        allowed_modules=["detection", "recognition"],
    )
    # ctx_id=-1 -> CPU, det_size -> detector working size, det_thresh -> min face confidence
    app.prepare(ctx_id=-1, det_size=det_size, det_thresh=det_thresh)
    return app


@st.cache_resource  # load once, reuse across reruns
def load_login_model():
    # Small canvas + lenient threshold: best for one large selfie-style face
    return _build_app(det_size=(640, 640), det_thresh=0.35)


@st.cache_resource
def load_class_model():
    # Large canvas + stricter threshold: best for many small faces in a class photo
    return _build_app(det_size=(1280, 1280), det_thresh=0.5)


def _enhance(image_bgr):
    """Even out lighting using CLAHE on the brightness channel."""
    lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)  # separate brightness (L) from colour
    l, a, b = cv2.split(lab)
    l = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(l)
    return cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)


def _pad(image_bgr, ratio=0.4):
    """Add a border so very close faces fit inside the frame with margin."""
    h, w = image_bgr.shape[:2]
    ph, pw = int(h * ratio), int(w * ratio)
    return cv2.copyMakeBorder(image_bgr, ph, ph, pw, pw,
                              cv2.BORDER_CONSTANT, value=(0, 0, 0))


def _to_bgr(image_rgb):
    # InsightFace expects BGR; contiguous copy avoids OpenCV layout errors
    return np.ascontiguousarray(image_rgb[:, :, ::-1])


def _face_area(f):
    return (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1])


def get_face_embeddings(image_rgb):
    """LOGIN / REGISTRATION: embeddings for faces in a selfie, with retries. Largest face first."""
    app = load_login_model()
    bgr = _to_bgr(image_rgb)

    # Try the original image, then progressively more forgiving versions
    for img in [bgr, _enhance(bgr), _pad(bgr), _pad(_enhance(bgr))]:
        faces = app.get(img)
        if faces:
            faces = sorted(faces, key=_face_area, reverse=True)
            return [f.normed_embedding for f in faces]
    return []


def get_class_embeddings(image_rgb):
    """CLASS PHOTO: embeddings for every face found. Single pass, no retries."""
    app = load_class_model()
    faces = app.get(_to_bgr(image_rgb))  # no retries, so the face set stays consistent
    return [f.normed_embedding for f in faces]


@st.cache_resource  # cached so the database isn't read on every call
def get_gallery():
    """Load all enrolled students' embeddings into memory."""
    ids, embs = [], []
    for s in get_all_students():
        e = s.get("face_embedding")
        if e is not None:
            ids.append(int(s["student_id"]))
            embs.append(np.asarray(e, dtype=np.float32))
    if not embs:
        return None  # nobody enrolled yet
    return np.array(ids), np.vstack(embs)  # (N,) ids and (N, 512) embeddings


def refresh_gallery():
    """Reload the gallery after a new student registers."""
    get_gallery.clear()  # clears only this cache, not the loaded models
    return get_gallery() is not None


def predict_attendance(image_np, single_face=False):
    """
    Return (detected students, all enrolled ids, number of faces found).
    single_face=True  -> login mode (selfie, retries, lenient detection)
    single_face=False -> class photo mode (many faces, large detector)
    """
    if single_face:
        encodings = get_face_embeddings(image_np)
        threshold = LOGIN_THRESHOLD
    else:
        encodings = get_class_embeddings(image_np)
        threshold = CLASS_THRESHOLD

    gallery = get_gallery()
    if gallery is None:  # empty database -> nobody to match against
        return {}, [], len(encodings)

    ids, G = gallery
    best_scores = {}  # student_id -> best similarity seen in this image
    for enc in encodings:
        sims = G @ enc                # cosine similarity against every enrolled face
        best = int(np.argmax(sims))   # closest enrolled embedding
        score = float(sims[best])
        sid = int(ids[best])
        # Accept only if similar enough; if two faces match the same student, keep the higher score
        if score >= threshold and score > best_scores.get(sid, -1):
            best_scores[sid] = score

    detected = {sid: True for sid in best_scores}
    return detected, sorted(set(ids.tolist())), len(encodings)