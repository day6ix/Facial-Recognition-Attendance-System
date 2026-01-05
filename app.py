import os
import io
import threading
import sqlite3
import datetime
import json

import cv2
import numpy as np
import mediapipe as mp

from flask import Flask, render_template, request, jsonify, send_file
from model import (
    train_model_background,
    extract_embedding_for_image,
    load_model_if_exists,
    predict_with_model
)

# -------------------- Paths --------------------
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, "attendance.db")
DATASET_DIR = os.path.join(APP_DIR, "dataset")
TRAIN_STATUS_FILE = os.path.join(APP_DIR, "train_status.json")

os.makedirs(DATASET_DIR, exist_ok=True)

# -------------------- Flask --------------------
app = Flask(__name__, static_folder="static", template_folder="templates")

# -------------------- MediaPipe --------------------
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)

# -------------------- DB --------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            roll TEXT,
            class TEXT,
            section TEXT,
            reg_no TEXT,
            created_at TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            name TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# -------------------- Train Status --------------------
def write_train_status(data):
    with open(TRAIN_STATUS_FILE, "w") as f:
        json.dump(data, f)

def read_train_status():
    if not os.path.exists(TRAIN_STATUS_FILE):
        return {"running": False, "progress": 0, "message": "Not trained"}
    with open(TRAIN_STATUS_FILE) as f:
        return json.load(f)

write_train_status({"running": False, "progress": 0, "message": "No training yet"})

# -------------------- Routes --------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/add_student")
def add_student_page():
    return render_template("add_student.html")

@app.route("/mark_attendance")
def mark_attendance_page():
    return render_template("mark_attendance.html")

# -------------------- Add Student --------------------
@app.route("/add_student", methods=["POST"])
def add_student():
    data = request.form
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Name required"}), 400

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.datetime.utcnow().isoformat()
    c.execute("""
        INSERT INTO students (name, roll, class, section, reg_no, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        name,
        data.get("roll"),
        data.get("class"),
        data.get("sec"),
        data.get("reg_no"),
        now
    ))
    sid = c.lastrowid
    conn.commit()
    conn.close()

    os.makedirs(os.path.join(DATASET_DIR, str(sid)), exist_ok=True)
    return jsonify({"student_id": sid})

# -------------------- Upload Faces --------------------
@app.route("/upload_face", methods=["POST"])
def upload_face():
    student_id = request.form.get("student_id")
    files = request.files.getlist("images[]")
    folder = os.path.join(DATASET_DIR, student_id)
    os.makedirs(folder, exist_ok=True)

    saved = 0
    for f in files:
        f.save(os.path.join(folder, f"{datetime.datetime.utcnow().timestamp()}.jpg"))
        saved += 1

    return jsonify({"saved": saved})

# -------------------- Train Model --------------------
@app.route("/train_model")
def train_model_route():
    if read_train_status()["running"]:
        return jsonify({"status": "already_running"}), 202

    write_train_status({"running": True, "progress": 0, "message": "Training started"})
    t = threading.Thread(
        target=train_model_background,
        args=(DATASET_DIR, lambda p, m: write_train_status(
            {"running": True, "progress": p, "message": m}
        ))
    )
    t.daemon = True
    t.start()
    return jsonify({"status": "started"}), 202

@app.route("/train_status")
def train_status():
    return jsonify(read_train_status())

# -------------------- LIVENESS + RECOGNITION --------------------
@app.route("/recognize_face", methods=["POST"])
def recognize_face():
    if "image" not in request.files:
        return jsonify({"recognized": False, "blink": False, "yaw": 0})

    img_file = request.files["image"]

    # ---- Decode image
    img_bytes = np.frombuffer(img_file.read(), np.uint8)
    frame = cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)
    img_file.stream.seek(0)

    if frame is None:
        return jsonify({"recognized": False, "blink": False, "yaw": 0})

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)

    blink = False
    yaw = 0.0

    if results.multi_face_landmarks:
        lm = results.multi_face_landmarks[0].landmark

        left_eye = [lm[i] for i in [33, 160, 158, 133, 153, 144]]
        right_eye = [lm[i] for i in [362, 385, 387, 263, 373, 380]]

        def ear(eye):
            v1 = abs(eye[1].y - eye[5].y)
            v2 = abs(eye[2].y - eye[4].y)
            h = abs(eye[0].x - eye[3].x)
            return (v1 + v2) / (2.0 * h + 1e-6)

        blink = ((ear(left_eye) + ear(right_eye)) / 2) < 0.28
        yaw = (lm[1].x - lm[234].x) * 100

    # ---- Face recognition
    emb = extract_embedding_for_image(img_file.stream)
    if emb is None:
        return jsonify({"recognized": False, "blink": blink, "yaw": yaw})

    clf = load_model_if_exists()
    if clf is None:
        return jsonify({"recognized": False, "blink": blink, "yaw": yaw})

    pred_label, conf = predict_with_model(clf, emb)
    if conf < 0.5:
        return jsonify({"recognized": False, "blink": blink, "yaw": yaw})

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT name FROM students WHERE id=?", (int(pred_label),))
    row = c.fetchone()
    name = row[0] if row else "Unknown"

    ts = datetime.datetime.utcnow().isoformat()
    c.execute(
        "INSERT INTO attendance (student_id, name, timestamp) VALUES (?, ?, ?)",
        (int(pred_label), name, ts)
    )
    conn.commit()
    conn.close()

    return jsonify({
        "recognized": True,
        "student_id": int(pred_label),
        "name": name,
        "confidence": float(conf),
        "blink": blink,
        "yaw": yaw
    })

# -------------------- Records --------------------
@app.route("/attendance_record")
def attendance_record():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, student_id, name, timestamp FROM attendance ORDER BY timestamp DESC")
    rows = c.fetchall()
    conn.close()
    return render_template("attendance_record.html", records=rows)

@app.route("/download_csv")
def download_csv():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, student_id, name, timestamp FROM attendance")
    rows = c.fetchall()
    conn.close()

    output = io.StringIO()
    output.write("id,student_id,name,timestamp\n")
    for r in rows:
        output.write(f"{r[0]},{r[1]},{r[2]},{r[3]}\n")

    mem = io.BytesIO()
    mem.write(output.getvalue().encode())
    mem.seek(0)
    return send_file(mem, download_name="attendance.csv", as_attachment=True)

# -------------------- Run --------------------
if __name__ == "__main__":
    app.run(debug=True)
