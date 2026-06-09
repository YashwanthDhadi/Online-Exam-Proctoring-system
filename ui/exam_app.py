"""
exam_app.py
Main UI for the AI-Based Online Exam Proctoring System.
Screens:
  1. Login    – Student ID + Exam ID
  2. Camera   – Permission check + face calibration
  3. Exam     – MCQ + short-answer questions + timer
  4. Results  – Violation summary + report generation
"""

import customtkinter as ctk
from tkinter import messagebox
import tkinter as tk
from PIL import Image, ImageTk
import cv2
import time
import threading
import os
from datetime import datetime

from core.camera          import Camera
from core.face_detector   import FaceDetector
from core.activity_tracker import ActivityTracker
from core.proctor_engine  import ProctorEngine
from core.window_tracker  import WindowTracker
from core.database        import init_db, save_exam_session, get_setting, set_setting
from core.ai_coach        import AICoach
from core.report_generator import generate_exam_report

# ─── Theme ───────────────────────────────────────────────────────
T = {
    "bg":      "#0d0d1a",
    "panel":   "#13132b",
    "card":    "#1a1a35",
    "accent":  "#6c63ff",
    "accent2": "#00d26a",
    "accent3": "#ff4757",
    "accent4": "#f5a623",
    "text":    "#e8e8ff",
    "subtext": "#8888aa",
    "border":  "#2a2a50",
}

# ─── Sample Exam Questions ────────────────────────────────────────
EXAM_QUESTIONS = [
    {
        "type":    "mcq",
        "text":    "What is Artificial Intelligence?",
        "options": [
            "A) Machine Learning algorithms only",
            "B) Computer systems that simulate human intelligence",
            "C) Human intelligence transferred to machines",
            "D) A branch of data science dealing with databases",
        ],
        "answer_key": "B",
    },
    {
        "type":    "mcq",
        "text":    "Which of the following is NOT a type of machine learning?",
        "options": [
            "A) Supervised Learning",
            "B) Unsupervised Learning",
            "C) Reinforcement Learning",
            "D) Directional Learning",
        ],
        "answer_key": "D",
    },
    {
        "type":    "mcq",
        "text":    "What does CNN stand for in the context of Deep Learning?",
        "options": [
            "A) Convolutional Neural Network",
            "B) Computed Numerical Network",
            "C) Central Node Network",
            "D) Connected Neural Node",
        ],
        "answer_key": "A",
    },
    {
        "type":    "short",
        "text":    "Briefly explain the difference between supervised and unsupervised learning.",
        "answer_key": "",
    },
    {
        "type":    "mcq",
        "text":    "Which algorithm is commonly used for classification tasks?",
        "options": [
            "A) K-Means Clustering",
            "B) Linear Regression",
            "C) Decision Tree",
            "D) Principal Component Analysis",
        ],
        "answer_key": "C",
    },
    {
        "type":    "short",
        "text":    "What is overfitting in machine learning? How can it be prevented?",
        "answer_key": "",
    },
    {
        "type":    "mcq",
        "text":    "What is the primary purpose of a validation dataset?",
        "options": [
            "A) To train the model on more data",
            "B) To tune hyperparameters and prevent overfitting",
            "C) To test the final model performance",
            "D) To clean and preprocess raw data",
        ],
        "answer_key": "B",
    },
    {
        "type":    "short",
        "text":    "Define 'neural network' in your own words and give one real-world application.",
        "answer_key": "",
    },
]

EXAM_DURATION_SECS = 60 * 30  # 30-minute exam


# ─────────────────────────────────────────────────────────────────
def run_app():
    init_db()
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    # ── Shared state ─────────────────────────────────────────────
    student_id   = [None]
    exam_id      = [None]
    started_at   = [None]

    cam          = Camera()
    detector     = FaceDetector()
    activity     = ActivityTracker()
    engine       = ProctorEngine()
    win_tracker  = WindowTracker()
    ai_coach     = AICoach(get_setting('gemini_api_key') or '')

    monitoring_active = [False]
    after_id          = [None]
    cam_after_id      = [None]
    exam_start_time   = [0]
    current_q         = [0]
    answers           = {}    # q_index -> answer string

    # ─────────────────────────────────────────────────────────────
    root = ctk.CTk()
    root.title("AI-Based Online Exam Proctoring System")
    root.geometry("1100x750")
    root.minsize(900, 650)
    root.configure(fg_color=T["bg"])

    # ── Container that holds all screens ─────────────────────────
    container = ctk.CTkFrame(root, fg_color=T["bg"])
    container.pack(fill="both", expand=True)

    def show_frame(frame):
        frame.tkraise()

    # ═════════════════════════════════════════════════════════════
    # SCREEN 1 — Login
    # ═════════════════════════════════════════════════════════════
    login_frame = ctk.CTkFrame(container, fg_color=T["bg"])
    login_frame.place(relwidth=1, relheight=1)

    ctk.CTkLabel(login_frame, text="🎓", font=("Helvetica", 60)).pack(pady=(80, 5))
    ctk.CTkLabel(login_frame,
                 text="AI-Based Online Exam Proctoring System",
                 font=("Helvetica", 22, "bold"),
                 text_color=T["text"]).pack()
    ctk.CTkLabel(login_frame,
                 text="Please enter your credentials to begin",
                 font=("Helvetica", 13),
                 text_color=T["subtext"]).pack(pady=(4, 30))

    card = ctk.CTkFrame(login_frame, fg_color=T["card"],
                        corner_radius=16, width=420)
    card.pack()

    ctk.CTkLabel(card, text="Student ID", font=("Helvetica", 13, "bold"),
                 text_color=T["subtext"]).pack(anchor="w", padx=30, pady=(25, 4))
    stu_entry = ctk.CTkEntry(card, placeholder_text="e.g.  23CAM1014",
                              width=360, height=42,
                              font=("Helvetica", 14),
                              fg_color=T["panel"], border_color=T["border"])
    stu_entry.pack(padx=30, pady=(0, 15))

    ctk.CTkLabel(card, text="Exam ID", font=("Helvetica", 13, "bold"),
                 text_color=T["subtext"]).pack(anchor="w", padx=30, pady=(0, 4))
    exam_entry = ctk.CTkEntry(card, placeholder_text="e.g.  EXAM-AI-2026",
                               width=360, height=42,
                               font=("Helvetica", 14),
                               fg_color=T["panel"], border_color=T["border"])
    exam_entry.pack(padx=30, pady=(0, 25))

    login_err = ctk.CTkLabel(card, text="", font=("Helvetica", 11),
                              text_color=T["accent3"])
    login_err.pack(pady=(0, 10))

    def on_login():
        sid  = stu_entry.get().strip()
        eid  = exam_entry.get().strip()
        if not sid or not eid:
            login_err.configure(text="Both fields are required.")
            return
        student_id[0] = sid
        exam_id[0]    = eid
        show_frame(camera_frame)
        start_camera_preview()

    ctk.CTkButton(card, text="Proceed to start Exam →",
                  width=360, height=46,
                  font=("Helvetica", 14, "bold"),
                  fg_color=T["accent"],
                  command=on_login).pack(padx=30, pady=(0, 30))

    # ═════════════════════════════════════════════════════════════
    # SCREEN 2 — Camera Calibration
    # ═════════════════════════════════════════════════════════════
    camera_frame = ctk.CTkFrame(container, fg_color=T["bg"])
    camera_frame.place(relwidth=1, relheight=1)

    ctk.CTkLabel(camera_frame,
                 text="Camera Permission & Calibration",
                 font=("Helvetica", 20, "bold"),
                 text_color=T["text"]).pack(pady=(30, 5))
    ctk.CTkLabel(camera_frame,
                 text="Ensure your face is clearly visible before starting the exam.",
                 font=("Helvetica", 12),
                 text_color=T["subtext"]).pack()

    cam_preview_label = ctk.CTkLabel(camera_frame, text="")
    cam_preview_label.pack(pady=15)

    cam_status_lbl = ctk.CTkLabel(camera_frame, text="⏳  Initialising camera…",
                                   font=("Helvetica", 13),
                                   text_color=T["accent4"])
    cam_status_lbl.pack(pady=5)

    cam_start_btn = ctk.CTkButton(camera_frame, text="Start Exam →",
                                   width=280, height=46,
                                   font=("Helvetica", 14, "bold"),
                                   fg_color=T["accent"],
                                   state="disabled",
                                   command=lambda: begin_exam())
    cam_start_btn.pack(pady=15)

    ctk.CTkButton(camera_frame, text="← Back",
                  width=160, height=36,
                  font=("Helvetica", 12),
                  fg_color=T["panel"],
                  command=lambda: (stop_camera_preview(), show_frame(login_frame))
                  ).pack()

    cam_calibrated = [False]

    def start_camera_preview():
        cam_calibrated[0] = False
        cam_start_btn.configure(state="disabled")
        cam_status_lbl.configure(text="⏳  Initialising camera…", text_color=T["accent4"])
        if not cam.available:
            cam.enable()
        _update_cam_preview()

    def _update_cam_preview():
        if cam_after_id[0] is not None:
            try:
                camera_frame.after_cancel(cam_after_id[0])
            except Exception:
                pass
        if not cam.available:
            cam_status_lbl.configure(text="❌  Camera not detected. Cannot start exam.",
                                      text_color=T["accent3"])
            return
        frame = cam.get_frame()
        if frame is not None:
            result = detector.detect(frame)
            face_present = result[0]
            face_count   = result[1] 

            # Try to calibrate once face is seen
            if face_present and not cam_calibrated[0]:
                if detector.calibrate(frame):
                    cam_calibrated[0] = True

            # Status message
            if not face_present:
                cam_status_lbl.configure(
                    text="❌  No face detected. Position yourself in front of the camera.",
                    text_color=T["accent3"])
                cam_start_btn.configure(state="disabled")
            elif face_count > 1:
                cam_status_lbl.configure(
                    text="⚠️  Multiple faces detected. Only one person may take the exam.",
                    text_color=T["accent4"])
                cam_start_btn.configure(state="disabled")
            else:
                cam_status_lbl.configure(
                    text="✅  Face detected. You may start the exam.",
                    text_color=T["accent2"])
                cam_start_btn.configure(state="normal")

            # Draw overlay on preview
            display = cv2.resize(frame, (400, 300))
            color_bgr = (0, 210, 106) if (face_present and face_count == 1) else (255, 71, 87)
            cv2.rectangle(display, (5, 5), (395, 295), color_bgr, 2)
            img_rgb  = cv2.cvtColor(display, cv2.COLOR_BGR2RGB)
            pil_img  = Image.fromarray(img_rgb)
            ctk_img  = ctk.CTkImage(pil_img, size=(400, 300))
            cam_preview_label.configure(image=ctk_img)
            cam_preview_label._image = ctk_img
        else:
            cam_status_lbl.configure(text="⏳  Waiting for camera feed…",
                                      text_color=T["accent4"])

        cam_after_id[0] = camera_frame.after(100, _update_cam_preview)

    def stop_camera_preview():
        if cam_after_id[0]:
            try:
                camera_frame.after_cancel(cam_after_id[0])
            except Exception:
                pass
        cam_after_id[0] = None

    # ═════════════════════════════════════════════════════════════
    # SCREEN 3 — Exam Interface
    # ═════════════════════════════════════════════════════════════
    exam_frame = ctk.CTkFrame(container, fg_color=T["bg"])
    exam_frame.place(relwidth=1, relheight=1)

    # Top bar
    exam_topbar = ctk.CTkFrame(exam_frame, fg_color=T["panel"],
                                corner_radius=0, height=56)
    exam_topbar.pack(fill="x")
    exam_topbar.pack_propagate(False)

    ctk.CTkLabel(exam_topbar, text="🔒  EXAM IN PROGRESS — PROCTORING ACTIVE",
                 font=("Helvetica", 13, "bold"),
                 text_color=T["accent"]).pack(side="left", padx=20)

    timer_lbl = ctk.CTkLabel(exam_topbar, text="⏱  30:00",
                              font=("Helvetica", 14, "bold"),
                              text_color=T["accent2"])
    timer_lbl.pack(side="right", padx=20)

    risk_badge = ctk.CTkLabel(exam_topbar, text="● Low Risk",
                               font=("Helvetica", 12, "bold"),
                               text_color=T["accent2"])
    risk_badge.pack(side="right", padx=10)

    # Live camera thumbnail
    cam_thumb_lbl = ctk.CTkLabel(exam_topbar, text="")
    cam_thumb_lbl.pack(side="right", padx=10)

    # Main content
    exam_body = ctk.CTkFrame(exam_frame, fg_color=T["bg"])
    exam_body.pack(fill="both", expand=True, padx=30, pady=20)

    # Progress label
    q_progress = ctk.CTkLabel(exam_body,
                               text="Question 1 of 8",
                               font=("Helvetica", 12),
                               text_color=T["subtext"])
    q_progress.pack(anchor="w")

    # Question card
    q_card = ctk.CTkFrame(exam_body, fg_color=T["card"],
                           corner_radius=14)
    q_card.pack(fill="x", pady=(8, 0))

    q_text_lbl = ctk.CTkLabel(q_card,
                               text="",
                               font=("Helvetica", 15, "bold"),
                               text_color=T["text"],
                               wraplength=780,
                               justify="left")
    q_text_lbl.pack(anchor="w", padx=24, pady=(20, 12))

    # MCQ options
    mcq_frame     = ctk.CTkFrame(q_card, fg_color="transparent")
    mcq_var       = tk.StringVar(value="")
    mcq_radios    = []
    for i in range(4):
        rb = ctk.CTkRadioButton(mcq_frame,
                                 text="",
                                 variable=mcq_var,
                                 value=str(i),
                                 font=("Helvetica", 13),
                                 text_color=T["text"],
                                 fg_color=T["accent"])
        rb.pack(anchor="w", pady=4, padx=10)
        mcq_radios.append(rb)

    # Short answer
    short_frame   = ctk.CTkFrame(q_card, fg_color="transparent")
    short_textbox = ctk.CTkTextbox(short_frame,
                                    width=780, height=140,
                                    font=("Helvetica", 13),
                                    fg_color=T["panel"],
                                    text_color=T["text"])
    short_textbox.pack(padx=10, pady=10)

    # Nav buttons
    nav_frame = ctk.CTkFrame(exam_body, fg_color="transparent")
    nav_frame.pack(fill="x", pady=16)

    prev_btn = ctk.CTkButton(nav_frame, text="← Previous",
                              width=140, height=40,
                              font=("Helvetica", 13),
                              fg_color=T["panel"],
                              command=lambda: navigate_question(-1))
    prev_btn.pack(side="left")

    next_btn = ctk.CTkButton(nav_frame, text="Next →",
                              width=140, height=40,
                              font=("Helvetica", 13),
                              fg_color=T["accent"],
                              command=lambda: navigate_question(1))
    next_btn.pack(side="left", padx=10)

    submit_btn = ctk.CTkButton(nav_frame, text="✔ Submit Exam",
                                width=160, height=40,
                                font=("Helvetica", 13, "bold"),
                                fg_color=T["accent2"],
                                text_color="#000000",
                                command=lambda: confirm_submit())
    submit_btn.pack(side="right")

    # Question dots (navigator)
    dots_frame = ctk.CTkFrame(exam_body, fg_color="transparent")
    dots_frame.pack(fill="x")
    q_dots = []
    for i in range(len(EXAM_QUESTIONS)):
        dot = ctk.CTkButton(dots_frame, text=str(i+1),
                             width=34, height=34,
                             font=("Helvetica", 11),
                             fg_color=T["panel"],
                             command=lambda idx=i: jump_to_question(idx))
        dot.pack(side="left", padx=3)
        q_dots.append(dot)

    def render_question(idx):
        q = EXAM_QUESTIONS[idx]
        q_progress.configure(text=f"Question {idx+1} of {len(EXAM_QUESTIONS)}")
        q_text_lbl.configure(text=f"Q{idx+1}.  {q['text']}")

        # Update dots
        for i, dot in enumerate(q_dots):
            if i == idx:
                dot.configure(fg_color=T["accent"])
            elif str(i) in answers:
                dot.configure(fg_color=T["accent2"])
            else:
                dot.configure(fg_color=T["panel"])

        # Show correct input type
        if q["type"] == "mcq":
            short_frame.pack_forget()
            mcq_frame.pack(anchor="w", padx=14, pady=(0, 16))
            opts = q["options"]
            mcq_var.set(answers.get(str(idx), ""))
            for i, rb in enumerate(mcq_radios):
                rb.configure(text=opts[i] if i < len(opts) else "")
        else:
            mcq_frame.pack_forget()
            short_frame.pack(anchor="w", padx=14, pady=(0, 16))
            short_textbox.delete("1.0", "end")
            short_textbox.insert("1.0", answers.get(str(idx), ""))

        prev_btn.configure(state="normal" if idx > 0 else "disabled")
        next_btn.configure(
            state="normal" if idx < len(EXAM_QUESTIONS) - 1 else "disabled")

    def save_current_answer():
        idx = current_q[0]
        q   = EXAM_QUESTIONS[idx]
        if q["type"] == "mcq":
            val = mcq_var.get()
            if val != "":
                answers[str(idx)] = val
        else:
            val = short_textbox.get("1.0", "end").strip()
            if val:
                answers[str(idx)] = val

    def navigate_question(delta):
        save_current_answer()
        new_idx = current_q[0] + delta
        if 0 <= new_idx < len(EXAM_QUESTIONS):
            current_q[0] = new_idx
            render_question(new_idx)

    def jump_to_question(idx):
        save_current_answer()
        current_q[0] = idx
        render_question(idx)

    def confirm_submit():
        save_current_answer()
        answered = len(answers)
        total    = len(EXAM_QUESTIONS)
        if answered < total:
            if not messagebox.askyesno(
                "Unanswered Questions",
                f"You have answered {answered}/{total} questions.\n"
                "Are you sure you want to submit?"
            ):
                return
        finish_exam()

    # ─── Timer & monitoring loop ──────────────────────────────
    def _monitoring_tick():
        if not monitoring_active[0]:
            return

        # Camera frame
        frame = cam.get_frame()

        # Face detection
        if frame is not None:
            result = detector.detect(frame)
            face_present   = result[0]
            face_count = result[1]
            looking_center = result[2] 
        else:
            face_present   = False
            looking_center = False
            face_count     = 0

        activity_active = activity.is_active()
        window_active   = win_tracker.is_study_window_active()

        # Evaluate proctoring
        result_dict = engine.evaluate(
            face_present   = face_present,
            face_count     = face_count,
            looking_center = looking_center,
            window_active  = window_active,
            activity_active= activity_active,
            frame          = frame,
        )

        # Update risk badge
        risk_badge.configure(
            text  = f"● {result_dict['status']}",
            text_color = result_dict['color'])

        # Update thumbnail
        if frame is not None:
            thumb = cv2.resize(frame, (100, 75))
            img_rgb = cv2.cvtColor(thumb, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(img_rgb)
            ctk_img = ctk.CTkImage(pil_img, size=(100, 75))
            cam_thumb_lbl.configure(image=ctk_img)
            cam_thumb_lbl._image = ctk_img

        # Timer
        elapsed   = int(time.time() - exam_start_time[0])
        remaining = max(0, EXAM_DURATION_SECS - elapsed)
        mins, secs = divmod(remaining, 60)
        timer_lbl.configure(text=f"⏱  {mins:02d}:{secs:02d}")
        if remaining <= 300:
            timer_lbl.configure(text_color=T["accent3"])
        if remaining == 0:
            finish_exam()
            return

        after_id[0] = exam_frame.after(500, _monitoring_tick)

    # ─── Exam start / end ─────────────────────────────────────
    def begin_exam():
        stop_camera_preview()
        engine.reset()
        current_q[0]     = 0
        answers.clear()
        exam_start_time[0] = time.time()
        started_at[0]    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        monitoring_active[0] = True
        show_frame(exam_frame)
        render_question(0)
        _monitoring_tick()

    def finish_exam():
        monitoring_active[0] = False
        if after_id[0]:
            try:
                exam_frame.after_cancel(after_id[0])
            except Exception:
                pass

        duration_secs = int(time.time() - exam_start_time[0])
        violations    = engine.violations
        risk_score    = engine.get_risk_score()
        risk_level    = engine.get_risk_level()
        evidence      = engine.get_evidence_files()
        ended_at      = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # AI summary (threaded)
        ai_summary_holder = [""]

        def _gen_summary():
            ai_summary_holder[0] = ai_coach.generate_exam_summary(
                student_id[0], exam_id[0],
                max(1, duration_secs // 60),
                violations, risk_level
            )

        t = threading.Thread(target=_gen_summary, daemon=True)
        t.start()
        t.join(timeout=10)

        ai_summary = ai_summary_holder[0]

        # Save to DB
        save_exam_session(
            student_id[0], exam_id[0],
            started_at[0], ended_at,
            duration_secs, risk_score, risk_level,
            violations, answers, ai_summary, evidence
        )

        # Generate PDF
        report_path = generate_exam_report(
            student_id[0], exam_id[0],
            started_at[0], duration_secs,
            violations, risk_score, risk_level,
            ai_summary, evidence
        )

        # Show results screen
        show_results(duration_secs, violations, risk_score,
                      risk_level, ai_summary, report_path, evidence)

    # ═════════════════════════════════════════════════════════════
    # SCREEN 4 — Results
    # ═════════════════════════════════════════════════════════════
    results_frame = ctk.CTkFrame(container, fg_color=T["bg"])
    results_frame.place(relwidth=1, relheight=1)

    def show_results(duration_secs, violations, risk_score,
                     risk_level, ai_summary, report_path, evidence):
        # Clear previous widgets
        for w in results_frame.winfo_children():
            w.destroy()

        activity.stop()

        scroll = ctk.CTkScrollableFrame(results_frame, fg_color=T["bg"])
        scroll.pack(fill="both", expand=True, padx=0, pady=0)

        # Header
        risk_color = (T["accent2"] if risk_level == "Low" else
                      T["accent4"] if risk_level == "Medium" else T["accent3"])

        ctk.CTkLabel(scroll,
                     text="Exam Completed",
                     font=("Helvetica", 26, "bold"),
                     text_color=T["text"]).pack(pady=(30, 4))
        ctk.CTkLabel(scroll,
                     text=f"Student: {student_id[0]}   |   Exam: {exam_id[0]}",
                     font=("Helvetica", 13),
                     text_color=T["subtext"]).pack()

        # Risk badge
        ctk.CTkLabel(scroll,
                     text=f"Risk Level: {risk_level}  (Score: {risk_score})",
                     font=("Helvetica", 18, "bold"),
                     text_color=risk_color).pack(pady=10)

        # Stats cards row
        cards_row = ctk.CTkFrame(scroll, fg_color="transparent")
        cards_row.pack(pady=5)

        mins, secs = divmod(duration_secs, 60)
        for label, value, color in [
            ("Duration",      f"{mins}m {secs}s", T["accent"]),
            ("Risk Score",    str(risk_score),    risk_color),
            ("Total Violations",
             str(sum(violations.values())),        T["accent4"]),
            ("Evidence Files", str(len(evidence)), T["subtext"]),
        ]:
            c = ctk.CTkFrame(cards_row, fg_color=T["card"],
                              corner_radius=12, width=160, height=90)
            c.pack(side="left", padx=8)
            c.pack_propagate(False)
            ctk.CTkLabel(c, text=value,
                         font=("Helvetica", 22, "bold"),
                         text_color=color).pack(pady=(16, 2))
            ctk.CTkLabel(c, text=label,
                         font=("Helvetica", 11),
                         text_color=T["subtext"]).pack()

        # Violation breakdown
        vio_card = ctk.CTkFrame(scroll, fg_color=T["card"],
                                 corner_radius=14)
        vio_card.pack(fill="x", padx=40, pady=15)
        ctk.CTkLabel(vio_card, text="Violations Detected",
                     font=("Helvetica", 15, "bold"),
                     text_color=T["text"]).pack(anchor="w", padx=20, pady=(15, 8))

        vio_labels = {
            'face_missing':   ('Face Missing',    T["accent3"]),
            'multiple_faces': ('Multiple Faces',  T["accent3"]),
            'looking_away':   ('Looking Away',    T["accent4"]),
            'window_switch':  ('Window Switch',   T["accent4"]),
            'inactivity':     ('Long Inactivity', T["subtext"]),
        }
        for key, (label, clr) in vio_labels.items():
            row = ctk.CTkFrame(vio_card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=2)
            ctk.CTkLabel(row, text=label,
                         font=("Helvetica", 13),
                         text_color=T["text"],
                         width=200, anchor="w").pack(side="left")
            count = violations.get(key, 0)
            ctk.CTkLabel(row, text=str(count),
                         font=("Helvetica", 13, "bold"),
                         text_color=clr if count > 0 else T["accent2"]).pack(side="left")
        ctk.CTkFrame(vio_card, fg_color="transparent", height=12).pack()

        # AI Summary
        if ai_summary:
            ai_card = ctk.CTkFrame(scroll, fg_color=T["card"],
                                    corner_radius=14)
            ai_card.pack(fill="x", padx=40, pady=10)
            ctk.CTkLabel(ai_card, text="🤖  AI Integrity Analysis",
                         font=("Helvetica", 15, "bold"),
                         text_color=T["accent"]).pack(anchor="w", padx=20, pady=(15, 6))
            ctk.CTkLabel(ai_card, text=ai_summary,
                         font=("Helvetica", 12),
                         text_color=T["text"],
                         wraplength=700, justify="left").pack(padx=20, pady=(0, 15))

        # Report path
        if report_path:
            ctk.CTkLabel(scroll,
                         text=f"📄  Report saved: {os.path.basename(report_path)}",
                         font=("Helvetica", 12),
                         text_color=T["subtext"]).pack(pady=5)

        # Evidence preview (first 3)
        if evidence:
            ctk.CTkLabel(scroll, text="Evidence Screenshots",
                         font=("Helvetica", 14, "bold"),
                         text_color=T["text"]).pack(pady=(10, 5))
            ev_row = ctk.CTkFrame(scroll, fg_color="transparent")
            ev_row.pack()
            for ev_path in evidence[:3]:
                if os.path.isfile(ev_path):
                    try:
                        img = Image.open(ev_path).resize((220, 165))
                        ctk_img = ctk.CTkImage(img, size=(220, 165))
                        ev_lbl = ctk.CTkLabel(ev_row, image=ctk_img, text="")
                        ev_lbl._image = ctk_img
                        ev_lbl.pack(side="left", padx=8)
                    except Exception:
                        pass

        # Buttons
        btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_row.pack(pady=20)
        ctk.CTkButton(btn_row, text="New Exam",
                       width=160, height=44,
                       font=("Helvetica", 13, "bold"),
                       fg_color=T["accent"],
                       command=new_exam).pack(side="left", padx=8)
        ctk.CTkButton(btn_row, text="Exit",
                       width=120, height=44,
                       font=("Helvetica", 13),
                       fg_color=T["panel"],
                       command=root.destroy).pack(side="left", padx=8)

        show_frame(results_frame)

    def new_exam():
        engine.reset()
        stu_entry.delete(0, "end")
        exam_entry.delete(0, "end")
        show_frame(login_frame)

    # ── Initial screen ────────────────────────────────────────────
    show_frame(login_frame)

    def on_close():
        monitoring_active[0] = False
        try:
            activity.stop()
        except Exception:
            pass
        try:
            cam.release()
        except Exception:
            pass
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()
