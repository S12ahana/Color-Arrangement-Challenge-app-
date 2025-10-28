import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import random, os, cv2, pandas as pd, time, math
from utils.color_detection import detect_colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as pdf_canvas
from PIL import Image, ImageTk  # <-- for displaying image

# --- Globals ---
current_order = []
uploaded_video = None
arrangement_mode = None  # "linear" or "circular"
last_result_data = {}
COLORS = ["Red", "Blue", "Green", "Yellow", "Pink", "Violet"]
COLOR_HEX = {
    "Red": "#FF4C4C",
    "Blue": "#4C6EFF",
    "Green": "#4CFF88",
    "Yellow": "#FFF44C",
    "Pink": "#FF7BF7",
    "Violet": "#A64CFF"
}

# --- Helper: Get video duration ---
def get_video_duration(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return 0
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    duration = frame_count / fps if fps > 0 else 0
    cap.release()
    return round(duration, 2)

# --- Mode Selection ---
def choose_mode():
    mode_win = tk.Toplevel(root)
    mode_win.title("Choose Arrangement Mode")
    mode_win.geometry("400x250")
    mode_win.configure(bg="#F5F5F5")

    tk.Label(mode_win, text="Select Color Arrangement Type:",
             font=("Poppins", 14, "bold"), bg="#F5F5F5").pack(pady=30)

    def set_mode(mode):
        global arrangement_mode
        arrangement_mode = mode
        mode_win.destroy()
        status_label.config(
            text=f"✅ {mode.title()} mode selected! Now click 'Shuffle Colors' to generate order."
        )

    linear_btn = tk.Button(mode_win, text="🟦 Linear Arrangement",
                           font=("Poppins", 13, "bold"), bg="#2196F3", fg="white",
                           relief="flat", cursor="hand2", command=lambda: set_mode("linear"))
    linear_btn.pack(pady=10, ipadx=10, ipady=5)

    circular_btn = tk.Button(mode_win, text="🔵 Circular Arrangement",
                             font=("Poppins", 13, "bold"), bg="#4CAF50", fg="white",
                             relief="flat", cursor="hand2", command=lambda: set_mode("circular"))
    circular_btn.pack(pady=10, ipadx=10, ipady=5)

# --- Shuffle Colors ---
def shuffle_order():
    global current_order
    if arrangement_mode is None:
        messagebox.showwarning("Select Mode", "Please choose Linear or Circular first!")
        return

    current_order = random.sample(COLORS, len(COLORS))
    draw_color_layout()
    status_label.config(text=f"🌀 {arrangement_mode.title()} color order generated!")

# --- Draw Color Layout ---
def draw_color_layout():
    for widget in order_frame.winfo_children():
        widget.destroy()

    if not current_order:
        messagebox.showwarning("No Colors", "Please shuffle colors first!")
        return

    if arrangement_mode == "linear":
        for color in current_order:
            lbl = tk.Label(order_frame, width=10, height=5, bg=COLOR_HEX[color],
                           relief="ridge", bd=3)
            lbl.pack(side="left", padx=25)

    elif arrangement_mode == "circular":
        canvas = tk.Canvas(order_frame, width=400, height=350, bg="white", highlightthickness=0)
        canvas.pack()
        cx, cy, r = 200, 175, 120
        angle_step = 2 * math.pi / len(current_order)

        for i, color in enumerate(current_order):
            angle = i * angle_step - math.pi / 2
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            canvas.create_oval(x - 35, y - 35, x + 35, y + 35, fill=COLOR_HEX[color], outline="")
            canvas.create_text(x, y, text=color, font=("Poppins", 10, "bold"))

# --- Upload Video ---
def upload_video():
    global uploaded_video
    uploaded_video = filedialog.askopenfilename(filetypes=[("MP4 files", "*.mp4")])
    if uploaded_video:
        video_label.config(text=os.path.basename(uploaded_video), fg="#00C851")
        status_label.config(text="🎥 Video uploaded successfully!")
    else:
        video_label.config(text="No video selected", fg="red")

# --- Get Last Frame ---
def get_last_frame(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None
    frame = None
    while True:
        ret, temp_frame = cap.read()
        if not ret:
            break
        frame = temp_frame
    cap.release()
    return frame

# --- Analyze Video ---
def analyze_video():
    global last_result_data
    if not uploaded_video:
        messagebox.showerror("Error", "Please upload a video first!")
        return
    if not current_order:
        messagebox.showerror("Error", "Please shuffle to generate a color order first!")
        return

    frame = get_last_frame(uploaded_video)
    if frame is None:
        messagebox.showerror("Error", "Could not read video frames.")
        return

    detected_positions = detect_colors(frame)

    # --- Determine detected order ---
    if arrangement_mode == "linear":
        colors_sorted = sorted(detected_positions.items(),
                               key=lambda c: c[1][0] if c[1] else 9999)
    else:
        h, w, _ = frame.shape
        cx, cy = w // 2, h // 2

        def angle_from_top_clockwise(x, y):
            dx, dy = x - cx, cy - y
            angle = math.atan2(dx, -dy)
            angle_deg = (360 - (math.degrees(angle) - 240)) % 360
            return angle_deg

        color_angles = []
        for color, pos in detected_positions.items():
            if pos:
                angle = angle_from_top_clockwise(pos[0], pos[1])
                color_angles.append((angle, color))
        color_angles.sort(key=lambda a: a[0])
        colors_sorted = [(c, detected_positions[c]) for _, c in color_angles]

    detected_order = [c[0] for c in colors_sorted if c[1] is not None]

    # --- Compare with generated order ---
    correct_colors = []
    for i, color in enumerate(current_order):
        if i < len(detected_order) and detected_order[i] == color:
            correct_colors.append(color)

    correct_count = len(correct_colors)
    wrong_count = len(COLORS) - correct_count
    accuracy = round((correct_count / len(COLORS)) * 100, 2)
    result = "✅ Correct" if correct_count == len(COLORS) else "❌ Incorrect"
    time_taken = get_video_duration(uploaded_video)

    # --- Save visualized frame ---
    os.makedirs("output", exist_ok=True)
    vis_frame_path = os.path.join("output", "last_frame_detected.jpg")
    cv2.imwrite(vis_frame_path, frame)

    # --- Prepare result data ---
    video_name = os.path.basename(uploaded_video)
    data = {
        "Arrangement Mode": [arrangement_mode.title()],
        "Video Name": [video_name],
        "Generated Order": [", ".join(current_order)],
        "Detected Order": [", ".join(detected_order)],
        "Correctly Placed": [correct_count],
        "Correct Colors": [", ".join(correct_colors) if correct_colors else "None"],
        "Wrongly Placed": [wrong_count],
        "Accuracy (%)": [accuracy],
        "Time Taken (s)": [time_taken],
        "Result": [result]
    }

    # --- Save to CSV ---
    results_csv = os.path.join("output", "results.csv")
    df = pd.DataFrame(data)
    if not os.path.exists(results_csv):
        df.to_csv(results_csv, index=False)
    else:
        df.to_csv(results_csv, mode="a", index=False, header=False)

    last_result_data = data
    show_result_window(data)
    status_label.config(text="📊 Analysis complete! Check output folder.")


# --- PDF Report ---
def download_report():
    if not last_result_data:
        messagebox.showwarning("No Data", "Please analyze a video first.")
        return
    report_name = f"output/Color_Challenge_Report_{int(time.time())}.pdf"
    pdf = pdf_canvas.Canvas(report_name, pagesize=A4)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(150, 800, "🎨 Color Arrangement Challenge Report")
    pdf.setFont("Helvetica", 12)
    y = 750
    for key, value in last_result_data.items():
        text = f"{key}: {value[0]}"
    # Wrap long lines (like color lists)
        if len(text) > 90:
            lines = [text[i:i+90] for i in range(0, len(text), 90)]
            for line in lines:
                pdf.drawString(100, y, line)
                y -= 18
        else:
            pdf.drawString(100, y, text)
            y -= 25

    pdf.drawString(100, y - 20, "✔ Report generated successfully!")
    pdf.save()
    messagebox.showinfo("Report Saved", f"PDF saved successfully at:\n{report_name}")

# --- Result Window ---
def show_result_window(data):
    result_window = tk.Toplevel(root)
    result_window.title("📊 Analysis Result")
    result_window.configure(bg="#F1FCFB")
    result_window.geometry("900x600")
    result_window.resizable(False, False)

    tk.Label(result_window, text="🎨 Game Performance Report",
             font=("Poppins", 20, "bold"), fg="#2F4F4F", bg="#F1FCFB").pack(pady=15)

    content_frame = tk.Frame(result_window, bg="#F1FCFB")
    content_frame.pack(fill="both", expand=True, padx=20, pady=10)

    style_frame = tk.Frame(content_frame, bg="white", relief="groove", bd=3)
    style_frame.pack(side="left", fill="both", expand=True, padx=(0, 15))

    for key, value in data.items():
        row = tk.Frame(style_frame, bg="white")
        row.pack(fill="x", pady=5)
        tk.Label(row, text=f"{key}:", font=("Poppins", 12, "bold"),
                 width=18, anchor="w", bg="white").pack(side="left", padx=10)
        tk.Label(row, text=f"{value[0]}", font=("Poppins", 12),
                 bg="white", fg="#333").pack(side="left")

    # ---- Right side: image preview ----
    vis_frame_path = os.path.join("output", "last_frame_detected.jpg")
    img_frame = tk.Frame(content_frame, bg="#FFFFFF", relief="ridge", bd=3)
    img_frame.pack(side="right", fill="y")

    tk.Label(img_frame, text="🖼 Detected Frame",
             font=("Poppins", 14, "bold"), bg="white").pack(pady=10)
    img_label = tk.Label(img_frame, bg="white")
    img_label.pack(padx=10, pady=5)

    def load_image(path):
        try:
            img = Image.open(path)
            img = img.resize((350, 300))
            photo = ImageTk.PhotoImage(img)
            img_label.config(image=photo)
            img_label.image = photo
        except Exception as e:
            img_label.config(text=f"⚠ Could not load image: {e}", fg="red", font=("Poppins", 11))

    load_image(vis_frame_path)

    # --- Highlight Button ---
    def highlight_correct_colors():
        frame = cv2.imread(os.path.join("output", "last_frame_detected.jpg"))
        detected_positions = detect_colors(frame)

    # Get correctly placed colors from last analysis data
        correct_colors_list = []
        if "Correct Colors" in last_result_data:
            correct_colors_list = [c.strip() for c in last_result_data["Correct Colors"][0].split(",") if c.strip() != "None"]

        if not correct_colors_list:
            messagebox.showinfo("No Correct Colors", "No correctly placed colors to highlight.")
            return

    # Draw green bounding boxes for correctly placed colors
        any_drawn = False
        for color, pos in detected_positions.items():
            if pos and color in correct_colors_list:
                x, y = pos
                box_size = 40
                cv2.rectangle(frame, (x - box_size, y - box_size),(x + box_size, y + box_size), (0, 255, 0), 3)
                cv2.putText(frame, f"{color}",(x - 30, y - box_size - 10),cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                any_drawn = True

        highlighted_path = os.path.join("output", "highlighted_correct_colors.jpg")
        cv2.imwrite(highlighted_path, frame)
        load_image(highlighted_path) 
       
    tk.Button(img_frame, text="✨ Highlight Correct Colors", bg="#4CAF50", fg="white", font=("Poppins", 12, "bold"), relief="flat", cursor="hand2", command=highlight_correct_colors).pack(pady=10, ipadx=10, ipady=5)

    # ---- Bottom Buttons ----
    ttk.Separator(result_window, orient="horizontal").pack(fill="x", pady=15)
    btn_frame = tk.Frame(result_window, bg="#F1FCFB")
    btn_frame.pack()

    tk.Button(btn_frame, text="⬇ Download Report (PDF)", bg="#007BFF", fg="white",
              font=("Poppins", 12, "bold"), relief="flat", cursor="hand2",
              command=download_report).pack(pady=10, ipadx=10, ipady=5)

    tk.Button(btn_frame, text="❌ Close", bg="#FF5C5C", fg="white",
              font=("Poppins", 12, "bold"), relief="flat", cursor="hand2",
              command=result_window.destroy).pack(pady=5, ipadx=10, ipady=5)

# --- GUI Design ---
root = tk.Tk()
root.title("🎨 Color Arrangement Challenge")
root.state("zoomed")
root.configure(bg="#78FBE3")

title_label = tk.Label(root, text="🎨 Color Arrangement Challenge",
                       font=("Poppins", 30, "bold"),
                       bg="#FFFFFF", fg="#2F4F4F", pady=20)
title_label.place(relx=0.5, rely=0.1, anchor="center")

main_frame = tk.Frame(root, bg="#A8E1F2", bd=5, relief="groove")
main_frame.place(relx=0.5, rely=0.55, anchor="center", relwidth=0.7, relheight=0.65)

order_container = tk.Frame(main_frame, bg="#FFFFFF", height=400)
order_container.pack(pady=20, fill="x")
order_container.pack_propagate(False)

order_frame = tk.Frame(order_container, bg="#FFFFFF")
order_frame.pack(expand=True)

def glow_button(btn, normal, hover):
    btn.configure(bg=normal, fg="white", font=("Poppins", 13, "bold"),
                  relief="flat", width=18, height=2, cursor="hand2", bd=0)
    btn.bind("<Enter>", lambda e: btn.config(bg=hover))
    btn.bind("<Leave>", lambda e: btn.config(bg=normal))

button_frame = tk.Frame(main_frame, bg="#A8E1F2")
button_frame.pack(pady=10)

mode_btn = tk.Button(button_frame, text="🎯 Choose Arrangement", command=choose_mode)
glow_button(mode_btn, "#673AB7", "#512DA8")
mode_btn.pack(side="left", padx=10)

shuffle_btn = tk.Button(button_frame, text="🔀 Shuffle Colors", command=shuffle_order)
glow_button(shuffle_btn, "#4CAF50", "#45A049")
shuffle_btn.pack(side="left", padx=10)

upload_btn = tk.Button(button_frame, text="📂 Upload Video", command=upload_video)
glow_button(upload_btn, "#2196F3", "#1976D2")
upload_btn.pack(side="left", padx=10)

analyze_btn = tk.Button(button_frame, text="📊 Analyze Video", command=analyze_video)
glow_button(analyze_btn, "#FF9800", "#F57C00")
analyze_btn.pack(side="left", padx=10)

video_label = tk.Label(main_frame, text="No video selected",
                       font=("Poppins", 12), fg="red", bg="#FFFFFF")
video_label.pack(pady=5)

status_label = tk.Label(root, text="✨ Welcome! Choose arrangement and shuffle to start your challenge.",
                        font=("Poppins", 12), bg="#2F4F4F", fg="white", anchor="w", padx=20)
status_label.pack(side="bottom", fill="x")

main_frame.pack_propagate(False)
root.mainloop()
