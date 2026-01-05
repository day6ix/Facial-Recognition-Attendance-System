📌 Facial Recognition Attendance System

A Digital Facial Recognition Attendance System built with Python, Flask, OpenCV, and Machine Learning to automate attendance tracking using live webcam input. This system captures face data, trains a recognition model, and logs attendance with timestamps, making it ideal for schools, offices, and labs. 
GitHub

🧠 Key Features

🖥️ Web-based attendance UI powered by Flask

📸 Live webcam face capture and dataset management

🤖 Face detection & recognition using OpenCV

🗃️ SQLite attendance logging

🔁 Trainable ML model for accuracy improvement

📊 Simple attendance record viewing and export

📂 Project Structure
Facial-Recognition-Attendance-System/
├── app.py                      # Main Flask application
├── database.py                 # Database initialization
├── model.py / model logic      # Face recognition & training
├── static/                    # Frontend CSS, JS, images
├── templates/                 # HTML UI templates
├── services/                  # Supplemental scripts (face engine, liveness, etc.)
├── dataset/                   # Captured face images per student
├── attendance.db (local)      # SQLite attendance database
├── requirements.txt           # Python dependencies
└── README.md                  # Project documentation
``` :contentReference[oaicite:1]{index=1}

---

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/day6ix/Facial-Recognition-Attendance-System.git
   cd Facial-Recognition-Attendance-System


Create & activate a virtual environment

python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate # Linux / macOS


Install dependencies

pip install -r requirements.txt

⚙️ Usage
1. Start the application
python app.py

2. Open in browser

Visit:

http://127.0.0.1:5000

3. Workflow

Add Student

Enter basic info and create a student record.

Capture Faces

Capture multiple face images via webcam for training.

Train Model

Train the recognition model on collected images.

Mark Attendance

Use webcam to detect and recognize faces and log attendance.

🧩 How It Works

The system uses OpenCV and MediaPipe/ML tools for face detection.

Face embeddings are extracted when a face is detected.

A classifier model is trained and stored to recognize faces.

Attendance logs are stored in a local SQLite database for retrieval and reporting. 
GitHub

🗃️ Database & Files
File	Purpose
attendance.db	Stores attendance records
dataset/	Stores captured face images
model.pkl	Trained classification model
requirements.txt	Python dependencies
⚠️ Notes

Designed for local deployment due to webcam and privacy requirements.

Ensure proper lighting and clear face captures for higher recognition accuracy. 
GitHub

👨‍💻 Contributing

Contributions are welcome!

Fork the project

Create a feature branch

Commit your changes

Open a pull request

📜 License

MIT License — feel free to use, modify, and distribute for educational or research purposes.

📌 Acknowledgements

This project serves as a practical implementation of facial recognition for attendance automation, combining computer vision and web development best practices.
