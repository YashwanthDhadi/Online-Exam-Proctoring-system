# AI-Based Online Exam Proctoring System

An intelligent desktop application that monitors students during online exams using real-time webcam analysis, system activity tracking, and automated integrity reports.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Technologies Used](#technologies-used)
- [How It Works](#how-it-works)
- [Risk Score Formula](#risk-score-formula)
- [Exam Details](#exam-details)
- [Installation](#installation)
- [How to Run](#how-to-run)
- [Application Screens](#application-screens)
- [Output Files](#output-files)

---

## Overview

This system is a Python-based AI proctoring tool designed to detect and report suspicious behavior during online exams. It uses computer vision to track the student's face and gaze, monitors keyboard and mouse activity, detects window switching, and automatically generates a detailed PDF integrity report at the end of the exam.

---

## Features

- 🎥 **Live Face Detection** — Detects if the student's face is present or missing during the exam
- 👁️ **Gaze Tracking** — Detects if the student is looking away from the screen
- 👥 **Multiple Face Detection** — Flags if more than one person is visible (possible impersonation)
- 🪟 **Window Switch Detection** — Detects if the student switches to another application or tab
- ⌨️ **Activity Monitoring** — Tracks keyboard and mouse activity; flags prolonged inactivity
- 📸 **Auto Evidence Capture** — Automatically screenshots the webcam frame on every violation
- 📊 **Real-Time Risk Score** — Continuously calculates a weighted risk score displayed as a live badge
- 📝 **Automated Integrity Summary** — Generates a rule-based written summary of all violations
- 📄 **PDF Report Generation** — Produces a detailed report with violation counts, risk level, and evidence images
- 🗄️ **Session Storage** — Saves all exam sessions to a local SQLite database

---

## Project Structure

```
AI_ExamProctor_Clean/
├── main.py                   ← Entry point — launches the exam application
├── requirements.txt          ← All required Python dependencies
├── README.md                 ← Project documentation
│
├── core/                     ← Backend logic modules
│   ├── camera.py             ← OpenCV webcam wrapper
│   ├── face_detector.py      ← MediaPipe FaceMesh — face presence, count, and gaze detection
│   ├── activity_tracker.py   ← pynput — keyboard and mouse activity tracking
│   ├── window_tracker.py     ← pygetwindow — active window monitoring
│   ├── proctor_engine.py     ← Main proctoring loop — violation tracking + evidence saving
│   ├── risk_engine.py        ← Weighted risk score calculation
│   ├── exam_questions.py     ← Question bank (MCQ + short answer)
│   ├── database.py           ← SQLite database handler for session storage
│   ├── ai_coach.py           ← Rule-based exam integrity summary generator
│   ├── report_generator.py   ← PDF report generation with evidence images
│   └── screenshot_capture.py ← Screen capture utility for violation evidence
│
├── ui/
│   └── exam_app.py           ← Full 4-screen exam UI built with CustomTkinter
│
├── data/
│   └── exam_proctor.db       ← SQLite database (auto-managed)
│
├── evidence/                 ← Violation screenshots saved here automatically
└── reports/                  ← Generated PDF reports saved here
```

---

## Technologies Used

| Technology    | Purpose                                      |
|---------------|----------------------------------------------|
| Python 3.11   | Core programming language                    |
| CustomTkinter | Modern desktop UI framework                  |
| OpenCV        | Webcam capture and image processing          |
| MediaPipe     | Real-time face detection and gaze tracking   |
| pynput        | Keyboard and mouse activity monitoring       |
| pygetwindow   | Active window detection                      |
| ReportLab     | PDF report generation                        |
| SQLite        | Local session data storage                   |
| Pillow        | Image handling for evidence thumbnails       |

---

## How It Works

1. The student logs in with their **Student ID** and **Exam ID**
2. The system performs a **camera check** — the exam cannot begin without a detected face
3. During the exam, the **ProctorEngine** runs in a background thread, continuously:
   - Analyzing the webcam frame using MediaPipe FaceMesh
   - Checking if the exam window is the active window
   - Monitoring keyboard and mouse activity
   - Calculating and updating the risk score in real time
4. Any violation triggers an **automatic screenshot** saved to the `evidence/` folder
5. After the exam, results are shown with a full violation breakdown and risk level
6. An **integrity summary** is auto-generated based on the violations detected
7. A **PDF report** is generated and saved to the `reports/` folder

---

## Risk Score Formula

Each violation type carries a weight. The total risk score determines the student's integrity level.

```
Risk Score = (face_missing × 10) + (window_switch × 5) + (looking_away × 3)
           + (multiple_faces × 15) + (inactivity × 2)
```

| Score Range | Risk Level  | Color    |
|-------------|-------------|----------|
| 0 – 19      | Low Risk    | 🟢 Green |
| 20 – 49     | Medium Risk | 🟡 Amber |
| 50+         | High Risk   | 🔴 Red   |

**Violation weights explained:**
- **Multiple Faces (×15)** — Highest weight; strongly indicates impersonation
- **Face Missing (×10)** — Student left the camera frame
- **Window Switch (×5)** — Student switched to another application
- **Looking Away (×3)** — Gaze detected off-screen
- **Inactivity (×2)** — No keyboard or mouse activity for 30+ seconds

---

## Exam Details

- **Total Questions:** 10
- **MCQ Questions:** 6 (2 marks each = 12 marks)
- **Short Answer Questions:** 4 (5–6 marks each = 21 marks)
- **Total Marks:** 33
- **Duration:** 30 minutes
- **Subject:** Artificial Intelligence and Machine Learning

---

## Installation

> ⚠️ **Requires Python 3.8 – 3.11** (MediaPipe does not support Python 3.12+)

```bash
pip install -r requirements.txt
```

**requirements.txt includes:**
```
customtkinter>=5.2.0
opencv-python>=4.8.0
mediapipe>=0.10.0
Pillow>=10.0.0
pynput>=1.7.6
pygetwindow>=0.0.9
reportlab>=4.0.4
```

---

## How to Run

```bash
python main.py
```

---

## Application Screens

### 1. Login Screen
Enter your **Student ID** and **Exam ID** to begin.

### 2. Camera Check Screen
Live webcam preview is shown. The exam will not start unless a face is clearly detected. This ensures the student is present and the camera is working before the exam begins.

### 3. Exam Interface
- Displays all 10 questions (MCQ and short answer)
- 30-minute countdown timer
- Live proctoring badge showing real-time risk level (Low / Medium / High)
- Violation events are silently captured in the background

### 4. Results Screen
- Full violation breakdown (face missing, multiple faces, looking away, window switch, inactivity)
- Final risk score and risk level
- Auto-generated integrity summary based on violations
- Evidence screenshot thumbnails
- Button to download the PDF report

---

## Output Files

**Evidence Screenshots** — saved automatically on every violation:
```
evidence/
  violation_face_missing_10_25_01.png
  violation_window_switch_10_31_15.png
  violation_multiple_faces_10_45_30.png
```

**PDF Reports** — saved after exam completion:
```
reports/
  exam_report_STU001_2026-03-08.pdf
```

---

