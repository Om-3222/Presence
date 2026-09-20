from resemblyzer import VoiceEncoder, preprocess_wav
import numpy as np
import io
import librosa
import streamlit as st 

# 1. loading the voice encoder and caching 
@st.cache_resource
def load_voice_encoder():
    return VoiceEncoder() 


def get_voice_embedding(audio_bytes):
    try:
        encoder = load_voice_encoder()
        
        # sr -> sample rate of the audio (think of it like video, more fps = more frames = more detailed video)
        # audio -> numpy array containing the audio waveform
        audio, sr = librosa.load(io.BytesIO(audio_bytes), sr=16000) # io.BytesIO creates a in memory file-like object from your audio bytes and pass it to librosa.load()
        wav = preprocess_wav(audio)     # prepares your audio so that Resemblyzer's neural network can process it

        embedding = encoder.embed_utterance(wav) # converts it in to voice embedding 

        return embedding.tolist()
    except Exception as e:
        st.error("Voice recognition error")
        return None 

# threshold in this case if lower limit (similarity, sid) should be >= threshold to get the match (best_sid, best_threshold)
def identify_speaker(new_embedding, candidates_dict, threshold = 0.65):
    if new_embedding is None or not candidates_dict:
        return None, 0.0
    
    best_sid = None 
    best_score = -1.0 

    for sid, stored_embedding in candidates_dict.items(): 
        if stored_embedding:
            similarity = np.dot(new_embedding, stored_embedding)    # dot product to check if the vectors are in same direction (cosine similarity)
            if similarity > best_score: 
                best_score = similarity
                best_sid = sid 

    if best_score >= threshold:
        return best_sid, best_score
    
    return None, best_score

def process_bulk_audio(audio_bytes, candidates_dict, threshold=0.65):
    try:
        encoder = load_voice_encoder()
        
        audio, sr = librosa.load(io.BytesIO(audio_bytes), sr=16000)
        segments = librosa.effects.split(audio, top_db=30)  # returns a NumPy array containing the start and end sample indices of detected non-silent intervals in the audio
        
        identified_results = {} 

        for start, end in segments:
            if(end - start) < sr * 0.5:
                continue
            segment_audio = audio[start:end]
            wav = preprocess_wav(segment_audio)

            embedding = encoder.embed_utterance(wav)

            sid, score = identify_speaker(embedding, candidates_dict, threshold)

            if sid: 
                if sid not in identified_results or score > identified_results[sid]:
                    identified_results[sid] = score

        return identified_results
    
    except Exception as e: 
        st.error("Bulk Process Error")
        return {} 