import sys
import socket
import threading
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QLineEdit, QVBoxLayout, QWidget
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt

# Load pre-trained Haar Cascade for face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# Define a simple emotion classifier (you can replace this with a more advanced model)
emotion_dict = {0: "Happy", 1: "Sad", 2: "Neutral", 3: "Frustrated"}
def classify_emotion(face_image):
    # Dummy emotion classifier using pixel intensity mean (for demo purposes)
    mean_intensity = face_image.mean()
    if mean_intensity > 180:
        return "Happy"
    elif mean_intensity < 80:
        return "Sad"
    elif mean_intensity < 120:
        return "Frustrated"
    else:
        return "Neutral"

class AdminApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.is_receiving = False
        self.thread = None

    def init_ui(self):
        self.setWindowTitle("Admin Camera Monitoring")
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()

        self.ip_input = QLineEdit(self)
        self.ip_input.setPlaceholderText("Enter User IP")
        layout.addWidget(self.ip_input)

        self.add_btn = QPushButton("Add", self)
        self.add_btn.clicked.connect(self.start_monitoring)
        layout.addWidget(self.add_btn)

        self.screen_label = QLabel(self)
        self.screen_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.screen_label)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def start_monitoring(self):
        ip = self.ip_input.text().strip()
        if ip:
            self.is_receiving = True
            self.thread = threading.Thread(target=self.receive_camera, args=(ip,))
            self.thread.start()

    def receive_camera(self, ip):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect((ip, 5000))

                while self.is_receiving:
                    # Receive the frame size
                    size_data = client_socket.recv(4)
                    if not size_data:
                        break
                    size = int.from_bytes(size_data, 'big')

                    # Receive the frame
                    frame_data = b""
                    while len(frame_data) < size:
                        packet = client_socket.recv(size - len(frame_data))
                        if not packet:
                            break
                        frame_data += packet

                    # Decode the frame
                    np_frame = np.frombuffer(frame_data, dtype=np.uint8)
                    frame = cv2.imdecode(np_frame, cv2.IMREAD_COLOR)

                    # Face detection and emotion recognition
                    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

                    for (x, y, w, h) in faces:
                        face_roi = gray_frame[y:y+h, x:x+w]
                        emotion = classify_emotion(face_roi)
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                        cv2.putText(frame, emotion, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)

                    # Convert the frame to QImage and display it
                    height, width, channel = frame.shape
                    bytes_per_line = channel * width
                    q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()

                    pixmap = QPixmap.fromImage(q_image)
                    scaled_pixmap = pixmap.scaled(
                        self.screen_label.width(),
                        self.screen_label.height(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    self.screen_label.setPixmap(scaled_pixmap)
        except Exception as e:
            print(f"Error: {e}")

    def closeEvent(self, event):
        self.is_receiving = False
        if self.thread and self.thread.is_alive():
            self.thread.join()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    admin_app = AdminApp()
    admin_app.show()
    sys.exit(app.exec_())
