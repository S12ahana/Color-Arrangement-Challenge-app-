import streamlit as st
import cv2, os, pandas as pd, time, math, random
from utils.color_detection import detect_colors
from reportlab.pdfgen import canvas as pdf_canvas

COLORS = ["Red", "Blue", "Green", "Yellow", "Pink", "Violet"]

st.title("🎨 Color Arrangement Challenge (Web Version)")

arrangement_mode = st.radio("Choose Arrangement Mode", ["Linear", "Circular"])
if st.button("🔀 Shuffle Colors"):
    current_order = random.sample(COLORS, len(COLORS))
    st.write("Generated Order:", ", ".join(current_order))
    st.session_state["current_order"] = current_order

uploaded_video = st.file_uploader("📂 Upload your video", type=["mp4"])
if uploaded_video and st.button("📊 Analyze Video"):
    video_path = f"temp_{time.time()}.mp4"
    with open(video_path, "wb") as f:
        f.write(uploaded_video.read())
    
    cap = cv2.VideoCapture(video_path)
    last_frame = None
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        last_frame = frame
    cap.release()
    
    detected_positions = detect_colors(last_frame)
    st.image(cv2.cvtColor(last_frame, cv2.COLOR_BGR2RGB), caption="Detected Frame")

    # Simple example result
    st.success("✅ Video analyzed successfully!")
