import streamlit as st
import cv2
import os
import time
import math
import random
import numpy as np
import matplotlib.pyplot as plt
from utils.color_detection import detect_colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.utils import ImageReader

COLORS = ["Red", "Blue", "Green", "Yellow", "Pink", "Violet"]

def generate_pdf_report(data, chart_path):
    report_path = f"Color_Challenge_Report_{int(time.time())}.pdf"
    pdf = pdf_canvas.Canvas(report_path, pagesize=A4)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(100, 800, "Color Arrangement Challenge Report")
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
    if os.path.exists(chart_path):
        y -= 200
        pdf.drawImage(ImageReader(chart_path), 160, y, width=250, height=250)
    pdf.save()
    return report_path

st.set_page_config(page_title="🎮 Color Arrangement Challenge", layout="wide")

st.markdown("""
    <style>
    .stApp {background: linear-gradient(135deg, #f6f9fc 0%, #e8f0ff 100%);
    font-family: 'Poppins', sans-serif; color: #1a1a1a;}
    h1 {color: #5A00FF; text-align: center;
    text-shadow: 0 0 15px #b48eff, 0 0 25px #b48eff;}
    div.stButton > button {
        background: linear-gradient(90deg, #5A00FF 0%, #FF00FF 100%);
        color: white; border-radius: 10px; padding: 0.7em 1.6em;
        font-weight: 700; border: none; transition: 0.3s ease-in-out;
    }
    div.stButton > button:hover {transform: scale(1.1); box-shadow: 0 0 20px #b48eff;}
    .report-card {
        background: rgba(255, 255, 255, 0.7);
        padding: 25px; border-radius: 15px;
        box-shadow: 0 0 20px rgba(0,0,0,0.1);
        margin-top: 25px; backdrop-filter: blur(10px);
    }
    img {border-radius: 15px;
    box-shadow: 0 0 15px rgba(90,0,255,0.3); transition: 0.3s;}
    img:hover {transform: scale(1.05);}
    .stDownloadButton button {
        background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%) !important;
        color: black !important; font-weight: 600 !important;
        border-radius: 8px !important; padding: 10px 20px !important;
        border: none !important; transition: 0.3s ease;
    }
    .stDownloadButton button:hover {
        transform: scale(1.05);
        box-shadow: 0 0 20px #92FE9D;
    }
    </style>
""", unsafe_allow_html=True)
st.markdown("<h1>🎨 COLOR PUZZLE ANALYSIS PORTAL 🎮</h1>", unsafe_allow_html=True)
st.markdown("<h1>🎨 COLOR PUZZLE ANALYSIS PORTAL 🎮</h1>", unsafe_allow_html=True)

arrangement_mode = st.radio("🎮 Choose Arrangement Mode", ["Linear", "Circular"])
if "current_order" not in st.session_state:
    st.session_state["current_order"] = COLORS

col1, col2 = st.columns([1, 3])
with col1:
    if st.button("🔀 Shuffle Colors"):
        st.session_state["current_order"] = random.sample(COLORS, len(COLORS))
with col2:
    st.markdown(f"<h3 style='color:dark blue;'>🧩 Current Order: {', '.join(st.session_state['current_order'])}</h3>", unsafe_allow_html=True)

uploaded_video = st.file_uploader("🎥 Upload your challenge video", type=["mp4"])

if uploaded_video and st.button("⚡ Analyze Video"):
    video_path = f"temp_{time.time()}.mp4"
    with open(video_path, "wb") as f:
        f.write(uploaded_video.read())

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps if fps > 0 else 0
    minutes = int(duration // 60)
    seconds = int(duration % 60)
    video_duration = f"{minutes} min {seconds} sec"

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
            "Challenge Duration": video_duration,
            "Result": "Correct" if correct_count == len(COLORS) else "Incorrect"
        }

        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        st.subheader("🧠 Performance Summary")
        st.markdown(f"""
        <div style='font-size:17px; line-height:1.8'>
        <b>Arrangement Mode:</b> <span style='color:#FF00FF;'>{result_data['Arrangement Mode']}</span><br>
        <b>Challenge Duration:</b> ⏱ {video_duration}<br>
        <b>Generated Order:</b> {result_data['Generated Order']}<br>
        <b>Detected Order:</b> {result_data['Detected Order']}<br>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### ⚙️ Accuracy Overview")
        col_graph, col_frame = st.columns([1, 1.5])

        with col_graph:
            st.markdown(f"<h3 style='text-align:center;color:#FF00FF;'>🎯 Accuracy: {accuracy}%</h3>", unsafe_allow_html=True)
            fig, ax = plt.subplots(figsize=(4, 4))
            ax.pie(
                [correct_count, wrong_count],
                labels=["Correct", "Wrong"],
                autopct="%1.1f%%",
                startangle=90,
                colors=["#7CFC00", "#FF6F61"],
                textprops={"fontsize": 12, "color": "black"}
            )
            ax.axis("equal")
            chart_path = f"accuracy_chart_{int(time.time())}.png"
            plt.savefig(chart_path, bbox_inches="tight")
            st.pyplot(fig)

        with col_frame:
            os.makedirs("output", exist_ok=True)
            frame_copy = last_frame.copy()
            for color, pos in detected_positions.items():
                if pos:
                    x, y = pos
                    cv2.circle(frame_copy, (x, y), 40,
                               (0, 255, 0) if color in correct_colors else (0, 0, 255), 3)
                    cv2.putText(frame_copy, color, (x - 30, y - 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            highlighted_path = os.path.join("output", "highlighted_correct_colors.jpg")
            cv2.imwrite(highlighted_path, frame_copy)
            st.image(cv2.cvtColor(frame_copy, cv2.COLOR_BGR2RGB),
                     caption="🎨 Highlighted Color Positions")

        if accuracy >= 90:
            st.success("🏆 Excellent! You're a Color Master!")
        elif accuracy >= 70:
            st.info("🎯 Great job! Keep it up!")
        else:
            st.warning("⚡ Try again to improve your score!")

        pdf_path = generate_pdf_report(result_data, chart_path)
        with open(pdf_path, "rb") as f:
            st.download_button("📄 Download Report PDF", f, file_name=os.path.basename(pdf_path))
        st.balloons()
        st.success("✅ Analysis Completed!")
