import streamlit as st
import cv2
import os
import time
import math
import numpy as np
import matplotlib.pyplot as plt
from utils.color_detection import detect_colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as pdf_canvas

COLORS = ["Red", "Blue", "Green", "Yellow", "Pink", "Violet"]

def generate_pdf_report(data):
    report_path = f"Color_Challenge_Report_{int(time.time())}.pdf"
    c = pdf_canvas.Canvas(report_path, pagesize=A4)
    c.setTitle("Color Challenge Report")
    c.setFont("Helvetica-Bold", 20)
    c.drawString(200, 800, "Color Challenge Report")
    c.setFont("Helvetica", 12)
    y = 750
    for key, value in data.items():
        c.drawString(100, y, f"{key}: {value}")
        y -= 20
    c.save()
    return report_path

def extract_frames(video_path, interval=30):
    frames = []
    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if frame_count % interval == 0:
            frames.append(frame)
        frame_count += 1
    cap.release()
    return frames

def calculate_accuracy(detected_order, reference_order):
    correct = sum(d1 == d2 for d1, d2 in zip(detected_order, reference_order))
    total = len(reference_order)
    accuracy = (correct / total) * 100
    return round(accuracy, 2), correct, total - correct

st.set_page_config(page_title="🎨 Color Order Analysis", layout="wide")
st.title("🎨 Color Arrangement Challenge")
arrangement_mode = st.selectbox("Choose Arrangement Type", ["Linear", "Circular"])
uploaded_video = st.file_uploader("📤 Upload Challenge Video", type=["mp4", "mov", "avi"])

if uploaded_video:
    video_path = f"uploaded_{int(time.time())}.mp4"
    with open(video_path, "wb") as f:
        f.write(uploaded_video.read())

    st.video(video_path)
    st.info("Extracting frames and analyzing color order...")
    frames = extract_frames(video_path, interval=30)
    detected_colors_per_frame = []
    for frame in frames:
        detected_colors = detect_colors(frame, COLORS)
        detected_colors_per_frame.append(detected_colors)
    last_frame = frames[-1]
    reference_order = COLORS.copy()
    detected_order = detected_colors_per_frame[-1]
    accuracy, correct_count, wrong_count = calculate_accuracy(detected_order, reference_order)
    detected_positions = {color: None for color in COLORS}
    correct_colors = [c for i, c in enumerate(reference_order) if i < len(detected_order) and c == detected_order[i]]
    result_data = {
        "Arrangement Mode": arrangement_mode,
        "Reference Order": ", ".join(reference_order),
        "Detected Order": ", ".join(detected_order),
        "Correctly Placed": correct_count,
        "Wrongly Placed": wrong_count,
        "Accuracy (%)": accuracy
    }

    st.markdown("### 🧾 Result Data")
    st.json(result_data)

    st.markdown("### 📊 Accuracy Visualization")
    col1, col2 = st.columns(2)
    with col1:
        fig, ax = plt.subplots()
        sizes = [correct_count, wrong_count]
        labels = ['Correct', 'Wrong']
        colors = ['#66BB6A', '#EF5350']
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90, textprops={'fontsize': 12})
        ax.axis('equal')
        st.pyplot(fig)

    with col2:
        os.makedirs("output", exist_ok=True)
        frame_copy = last_frame.copy()
        for color, pos in detected_positions.items():
            if pos:
                x, y = pos
                cv2.circle(frame_copy, (x, y), 40, (0, 255, 0) if color in correct_colors else (0, 0, 255), 3)
                cv2.putText(frame_copy, color, (x - 30, y - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        highlighted_path = os.path.join("output", "highlighted_correct_colors.jpg")
        cv2.imwrite(highlighted_path, frame_copy)
        st.image(cv2.cvtColor(frame_copy, cv2.COLOR_BGR2RGB), caption="🎨 Highlighted Color Positions")

    pdf_path = generate_pdf_report(result_data)
    with open(pdf_path, "rb") as pdf_file:
        st.download_button(label="📥 Download PDF Report", data=pdf_file, file_name=pdf_path, mime="application/pdf")
