import streamlit as st
import cv2, os, pandas as pd, time, math, random
import numpy as np
from reportlab.pdfgen import canvas as pdf_canvas
from utils.color_detection import detect_colors  # ensure this returns a dict or list of detected colors

COLORS = ["Red", "Blue", "Green", "Yellow", "Pink", "Violet"]

st.set_page_config(page_title="Color Arrangement Challenge", layout="wide")
st.title("🎨 Color Arrangement Challenge (Web Version)")

# --- Arrangement selection ---
arrangement_mode = st.radio("Choose Arrangement Mode", ["Linear", "Circular"])

# --- Shuffle color order ---
if "current_order" not in st.session_state:
    st.session_state["current_order"] = COLORS

if st.button("🔀 Shuffle Colors"):
    current_order = random.sample(COLORS, len(COLORS))
    st.session_state["current_order"] = current_order
    st.success(f"Generated Order: {', '.join(current_order)}")

st.write(f"**Current Order:** {', '.join(st.session_state['current_order'])}")

# --- Video upload ---
uploaded_video = st.file_uploader("📂 Upload your video", type=["mp4"])

# --- Analyze video button ---
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

    st.subheader("🖼️ Last Frame Detected")
    st.image(cv2.cvtColor(last_frame, cv2.COLOR_BGR2RGB), caption="Extracted from video")

    # --- Detect colors ---
    st.info("🔍 Detecting colors... Please wait")
    detected_positions = detect_colors(last_frame)  # expected to return something like {"Red": (x, y), "Blue": (x, y), ...}

    if detected_positions:
        # --- Draw highlights on image ---
        frame_copy = last_frame.copy()
        for color, (x, y) in detected_positions.items():
            cv2.circle(frame_copy, (int(x), int(y)), 25, (0, 255, 0), 3)
            cv2.putText(frame_copy, color, (int(x) - 30, int(y) - 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        st.subheader("✨ Highlighted Detected Colors")
        st.image(cv2.cvtColor(frame_copy, cv2.COLOR_BGR2RGB))

        # --- Generate a simple analysis report ---
        report_df = pd.DataFrame([
            {"Color": c, 
             "Detected": "✅" if c in detected_positions else "❌", 
             "Position": str(detected_positions.get(c, "Not Found"))}
            for c in st.session_state["current_order"]
        ])
        st.subheader("📊 Analysis Report")
        st.dataframe(report_df, use_container_width=True)

        accuracy = (sum(c in detected_positions for c in st.session_state["current_order"]) /
                    len(st.session_state["current_order"])) * 100
        st.success(f"🎯 Accuracy: {accuracy:.2f}%")

        # --- Optional: Download report as CSV ---
        csv_data = report_df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download Report as CSV", csv_data, "color_analysis_report.csv", "text/csv")

    else:
        st.error("No colors detected. Please upload a clearer video.")
