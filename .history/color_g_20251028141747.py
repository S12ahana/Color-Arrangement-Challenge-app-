import streamlit as st
import cv2
import os
import pandas as pd
import time
import math
import random
from utils.color_detection import detect_colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as pdf_canvas
import numpy as np

COLORS = ["Red", "Blue", "Green", "Yellow", "Pink", "Violet"]

def generate_pdf_report(data):
    report_path = f"Color_Challenge_Report_{int(time.time())}.pdf"
    pdf = pdf_canvas.Canvas(report_path, pagesize=A4)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(100, 800, "🎨 Color Arrangement Challenge Report")
    y = 760
    pdf.setFont("Helvetica", 12)
    for key, value in data.items():
        text = f"{key}: {value}"
        if len(text) > 90:
            lines = [text[i:i + 90] for i in range(0, len(text), 90)]
            for line in lines:
                pdf.drawString(100, y, line)
                y -= 15
        else:
            pdf.drawString(100, y, text)
            y -= 20
    pdf.save()
    return report_path

st.set_page_config(page_title="🎨 Color Arrangement Challenge", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #f8e8ff 0%, #e3f2fd 100%);
        font-family: 'Poppins', sans-serif;
    }
    h1 {
        color: #5e35b1;
        text-align: center;
        padding: 10px 0;
        text-shadow: 1px 1px 2px #c7a4ff;
    }
    div.stButton > button {
        background: linear-gradient(90deg, #6a11cb 0%, #2575fc 100%);
        color: white;
        border-radius: 10px;
        padding: 0.6em 1.5em;
        border: none;
        font-weight: bold;
        transition: 0.3s;
    }
    div.stButton > button:hover {
        transform: scale(1.05);
        background: linear-gradient(90deg, #2575fc 0%, #6a11cb 100%);
    }
    .report-card {
        background-color: white;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-top: 25px;
    }
    img {
        border-radius: 12px;
        box-shadow: 0 3px 8px rgba(0,0,0,0.2);
        transition: 0.3s;
    }
    img:hover {
        transform: scale(1.02);
    }
    [data-testid="stMetricValue"] {
        color: #6a11cb;
        font-weight: bold;
    }
    div.stProgress > div > div {
        background-color: #6a11cb !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🎨 Color Arrangement Challenge (Web Version)")
arrangement_mode = st.radio("Choose Arrangement Mode", ["Linear", "Circular"])

if "current_order" not in st.session_state:
    st.session_state["current_order"] = COLORS

col1, col2 = st.columns([1, 3])
with col1:
    if st.button("🔀 Shuffle Colors"):
        st.session_state["current_order"] = random.sample(COLORS, len(COLORS))
with col2:
    st.markdown(f"### 🧩 Current Order: `{', '.join(st.session_state['current_order'])}`")

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

    if last_frame is None:
        st.error("❌ Could not read video frames.")
    else:
        detected_positions = detect_colors(last_frame)

        if arrangement_mode.lower() == "linear":
            colors_sorted = sorted(detected_positions.items(), key=lambda c: c[1][0] if c[1] else 9999)
        else:
            h, w, _ = last_frame.shape
            cx, cy = w // 2, h // 2
            def angle_from_top_clockwise(x, y):
                dx, dy = x - cx, cy - y
                angle = math.atan2(dx, -dy)
                return (360 - (math.degrees(angle) - 240)) % 360
            color_angles = [(angle_from_top_clockwise(pos[0], pos[1]), color)
                            for color, pos in detected_positions.items() if pos]
            color_angles.sort(key=lambda a: a[0])
            colors_sorted = [(c, detected_positions[c]) for _, c in color_angles]

        detected_order = [c[0] for c in colors_sorted if c[1] is not None]
        correct_colors = [color for i, color in enumerate(st.session_state["current_order"])
                          if i < len(detected_order) and detected_order[i] == color]
        correct_count = len(correct_colors)
        wrong_count = len(COLORS) - correct_count
        accuracy = round((correct_count / len(COLORS)) * 100, 2)

        result_data = {
            "Arrangement Mode": arrangement_mode.title(),
            "Generated Order": ", ".join(st.session_state["current_order"]),
            "Detected Order": ", ".join(detected_order),
            "Correctly Placed": correct_count,
            "Correct Colors": ", ".join(correct_colors) if correct_colors else "None",
            "Wrongly Placed": wrong_count,
            "Accuracy (%)": accuracy,
            "Result": "✅ Correct" if correct_count == len(COLORS) else "❌ Incorrect"
        }

        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        st.subheader("📊 Performance Summary")
        st.markdown(f"""
        <div style='font-size:18px; line-height:1.8'>
        ✅ <b>Arrangement Mode:</b> <span style='color:#1976D2;'>{result_data['Arrangement Mode']}</span><br>
        🎯 <b>Generated Order:</b> {result_data['Generated Order']}<br>
        🎥 <b>Detected Order:</b> {result_data['Detected Order']}<br>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("### 🎯 Accuracy Overview")
        st.progress(result_data["Accuracy (%)"] / 100)
        st.markdown(f"<h3 style='color:#4CAF50; text-align:center;'>Accuracy: {result_data['Accuracy (%)']}%</h3>", unsafe_allow_html=True)
        colA, colB = st.columns(2)
        with colA:
            st.metric("✅ Correctly Placed", f"{result_data['Correctly Placed']}")
            st.markdown(f"<b>✔ Correct Colors:</b> {result_data['Correct Colors']}", unsafe_allow_html=True)
        with colB:
            st.metric("❌ Wrongly Placed", f"{result_data['Wrongly Placed']}")
            st.markdown(f"<b>📋 Result:</b> {result_data['Result']}", unsafe_allow_html=True)
        if result_data["Accuracy (%)"] == 100:
            st.success("🏆 Excellent! Perfect arrangement achieved!")
        elif result_data["Accuracy (%)"] >= 70:
            st.info("💪 Great job! You're close to perfection.")
        elif result_data["Accuracy (%)"] >= 40:
            st.warning("🤔 Keep practicing! You’re improving.")
        else:
            st.error("😅 Needs improvement — try again with more focus!")
        st.markdown('</div>', unsafe_allow_html=True)

        os.makedirs("output", exist_ok=True)
        frame_copy = last_frame.copy()
        for color, pos in detected_positions.items():
            if pos:
                x, y = pos
                cv2.circle(frame_copy, (x, y), 40, (0, 255, 0) if color in correct_colors else (0, 0, 255), 3)
                cv2.putText(frame_copy, color, (x - 30, y - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        highlighted_path = os.path.join("output", "highlighted_correct_colors.jpg")
        cv2.imwrite(highlighted_path, frame_copy)
        st.image(cv2.cvtColor(frame_copy, cv2.COLOR_BGR2RGB), caption="✨ Highlighted Correct Colors")

        pdf_path = generate_pdf_report(result_data)
        with open(pdf_path, "rb") as f:
            st.download_button("⬇️ Download Report PDF", f, file_name=os.path.basename(pdf_path))
        st.success("✅ Analysis complete!")
