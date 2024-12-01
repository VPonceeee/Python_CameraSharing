import sys
import socket
import cv2
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton


class UserApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.is_sharing = False
        self.thread = None
        self.cap = None

    def init_ui(self):
        self.setWindowTitle("User Camera Sharing")
        self.setGeometry(100, 100, 300, 200)

        self.start_btn = QPushButton("Start Sharing", self)
        self.start_btn.setGeometry(50, 50, 200, 50)
        self.start_btn.clicked.connect(self.start_sharing)

        self.stop_btn = QPushButton("Stop Sharing", self)
        self.stop_btn.setGeometry(50, 120, 200, 50)
        self.stop_btn.clicked.connect(self.stop_sharing)

    def start_sharing(self):
        if not self.is_sharing:
            self.is_sharing = True
            print("Starting camera sharing...")
            self.thread = threading.Thread(target=self.share_camera)
            self.thread.start()

    def stop_sharing(self):
        self.is_sharing = False
        print("Stopping camera sharing...")
        if self.thread and self.thread.is_alive():
            self.thread.join()
        if self.cap:
            self.cap.release()

    def share_camera(self):
        try:
            self.cap = cv2.VideoCapture(0)  # Open the default camera
            if not self.cap.isOpened():
                print("Error: Camera not found or could not be opened.")
                self.is_sharing = False
                return

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
                server_socket.bind(("0.0.0.0", 5000))
                server_socket.listen(1)
                print("Waiting for connection...")
                conn, addr = server_socket.accept()
                print(f"Connected to {addr}")

                while self.is_sharing and self.cap.isOpened():
                    ret, frame = self.cap.read()
                    if not ret:
                        print("Error: Failed to read frame from camera.")
                        break

                    # Encode the frame as JPEG
                    _, buffer = cv2.imencode('.jpg', frame)
                    data = buffer.tobytes()

                    # Send the size of the frame followed by the frame
                    conn.sendall(len(data).to_bytes(4, 'big') + data)

                conn.close()
        except Exception as e:
            print(f"Error: {e}")
        finally:
            if self.cap:
                self.cap.release()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    user_app = UserApp()
    user_app.show()
    sys.exit(app.exec_())
