import cv2
import numpy as np

class FaceEngine:
    def __init__(self):
        self.detector = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()

    def detect(self, gray):
        return self.detector.detectMultiScale(gray, 1.3, 5)

    def train(self, faces, labels):
        self.recognizer.train(faces, np.array(labels))

    def predict(self, face):
        return self.recognizer.predict(face)
