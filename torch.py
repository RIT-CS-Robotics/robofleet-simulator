import math
import random
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import QByteArray, Qt, QTimer

class RobotFace:
    def __init__(self, label_widget: QLabel):
        self.label = label_widget
        
        # Global variables for colors
        self.bg_color = "#38bdf8"
        self.face_color = "#ffffff"
        
        self.emotion = "happy"
        self.breathing_step = 0.0
        self.scan_step = 0.0
        self.is_blinking = False
        self.blink_frame_counter = 0
        self.is_scanning = False
        self.scan_duration_frames = 0
        self.is_startled = False
        self.startle_step = 0.0
        self.startle_duration_frames = 0
        self.is_talking = False
        self.talk_frames_remaining = 0
        self.talk_cycle_step = 0.0
        self.talk_amplitude = 1.0
        
        self.is_excited = False
        self.excited_frame_counter = 0
        self.excited_y_offset = 0.0
        self.excited_jitter = 0.0
        self.excited_blink = False
        
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setScaledContents(True)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_animation)
        self.timer.start(33)
        self._render_current_frame()

    def change_emotion(self, emotion: str):
        if self.emotion != emotion:
            self.emotion = emotion
            self._render_current_frame()

    def talk(self, duration_ms: int):
        self.talk_frames_remaining = max(0, int(duration_ms / 33))
        self.is_talking = self.talk_frames_remaining > 0
        if self.is_talking:
            self.is_scanning = False
            self.is_startled = False
            self.is_excited = False
            self.startle_step = 0.0

    def _update_animation(self):
        self.breathing_step = (self.breathing_step + 0.05) % (2 * math.pi)
        
        if self.is_talking:
            self.talk_cycle_step += 0.45
            self.talk_frames_remaining -= 1
            if int(self.talk_cycle_step) % 3 == 0:
                self.talk_amplitude = random.uniform(0.4, 1.2)
            if self.talk_frames_remaining <= 0:
                self.is_talking = False
                self.talk_cycle_step = 0.0
                
        if self.is_blinking:
            self.blink_frame_counter += 1
            if self.blink_frame_counter >= 3:
                self.is_blinking = False
                self.blink_frame_counter = 0
        elif not self.is_startled and not self.is_excited and random.random() < 0.008:
            self.is_blinking = True
            self.blink_frame_counter = 0

        if self.is_excited:
            self.excited_frame_counter += 1
            if self.excited_frame_counter < 8:
                self.excited_y_offset = self.excited_frame_counter * 1.5
                self.excited_jitter = 0.0
                self.excited_blink = False
            elif self.excited_frame_counter < 50:
                bounce_cycle = (self.excited_frame_counter - 8) * 0.4
                self.excited_y_offset = -30.0 * abs(math.sin(bounce_cycle * 0.5)) - 5.0
                self.excited_jitter = random.choice([-3.0, 3.0])
                self.excited_blink = (18 <= self.excited_frame_counter <= 24) or (34 <= self.excited_frame_counter <= 40)
            elif self.excited_frame_counter < 65:
                progress = (65 - self.excited_frame_counter) / 15.0
                self.excited_y_offset = self.excited_y_offset * progress
                self.excited_jitter = 0.0
                self.excited_blink = False
            else:
                self.is_excited = False
                self.excited_frame_counter = 0
                self.excited_y_offset = 0.0
                self.excited_jitter = 0.0
                self.excited_blink = False
        elif not self.is_talking and not self.is_startled and not self.is_scanning:
            if self.emotion == "happy" and random.random() < 0.0015:
                self.is_excited = True
                self.excited_frame_counter = 0

        if self.is_scanning:
            self.scan_step += 0.07
            self.scan_duration_frames += 1
            if self.scan_duration_frames >= 90:
                self.is_scanning = False
                self.scan_step = 0.0
                self.scan_duration_frames = 0
        elif not self.is_startled and not self.is_talking and not self.is_excited and self.emotion != "surprised":
            if random.random() < 0.003:
                self.is_scanning = True
                self.scan_step = 0.0
                self.scan_duration_frames = 0

        if self.is_startled:
            self.startle_duration_frames += 1
            if self.startle_duration_frames < 10:
                self.startle_step += 0.1
            elif self.startle_duration_frames > 35:
                self.startle_step -= 0.1
            self.startle_step = max(0.0, min(1.0, self.startle_step))
            if self.startle_duration_frames >= 45:
                self.is_startled = False
                self.startle_step = 0.0
                self.startle_duration_frames = 0
        elif not self.is_talking and not self.is_excited and self.emotion != "surprised":
            if random.random() < 0.002:
                self.is_startled = True
                self.startle_step = 0.0
                self.startle_duration_frames = 0
                
        self._render_current_frame()

    def _generate_svg(self, y_offset: float, x_offset: float) -> str:
        svg_start = f'<svg width="400" height="400" viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg"><rect width="400" height="400" fill="{self.bg_color}"/>'
        svg_end = '</svg>'
        
        is_compressing = self.is_excited and self.excited_frame_counter < 8
        eye_width = 60
        base_eye_height = 80 if self.emotion == "surprised" else 60
        
        if is_compressing:
            eye_height = base_eye_height - 12
        else:
            eye_height = base_eye_height + (20 * self.startle_step)
            
        eye_x_left = 100 + x_offset + self.excited_jitter
        eye_x_right = 240 + x_offset - self.excited_jitter
        base_eye_y = 110 if self.emotion == "surprised" else (140 if self.emotion == "sad" else 130 if self.emotion == "neutral" else 120)
        eye_y = (base_eye_y - (10 * self.startle_step)) + y_offset + self.excited_y_offset
        mouth_y_offset = (y_offset * 0.5) + self.excited_y_offset

        if self.is_blinking or self.excited_blink:
            eye_y += (eye_height / 2) - 3
            eye_height = 6

        if self.is_talking:
            talk_modifier = abs(math.sin(self.talk_cycle_step)) * self.talk_amplitude
            rx_val = 20 + (25 * talk_modifier)
            ry_val = 8 + (22 * talk_modifier)
            mouth_y = 265 + mouth_y_offset
            shapes = f'<rect x="{eye_x_left}" y="{eye_y}" width="{eye_width}" height="{eye_height}" rx="4" fill="{self.face_color}" /><rect x="{eye_x_right}" y="{eye_y}" width="{eye_width}" height="{eye_height}" rx="4" fill="{self.face_color}" /><ellipse cx="200" cy="{mouth_y}" rx="{rx_val}" ry="{ry_val}" fill="{self.face_color}" />'
        elif self.startle_step > 0.1:
            circle_radius = 20 + (20 * self.startle_step)
            shapes = f'<rect x="{eye_x_left}" y="{eye_y}" width="{eye_width}" height="{eye_height}" rx="4" fill="{self.face_color}" /><rect x="{eye_x_right}" y="{eye_y}" width="{eye_width}" height="{eye_height}" rx="4" fill="{self.face_color}" /><circle cx="200" cy="{265 + mouth_y_offset}" r="{circle_radius}" fill="{self.face_color}" />'
        else:
            eyes_svg = f'<rect x="{eye_x_left}" y="{eye_y}" width="{eye_width}" height="{eye_height}" rx="4" fill="{self.face_color}" /><rect x="{eye_x_right}" y="{eye_y}" width="{eye_width}" height="{eye_height}" rx="4" fill="{self.face_color}" />'
            if self.emotion == "happy":
                mouth_stretch = 22 if (self.is_excited and not is_compressing) else 0
                shapes = eyes_svg + f'<path d="M 130 {225 + mouth_y_offset} A 70 {70 + mouth_stretch} 0 0 0 270 {225 + mouth_y_offset} Z" fill="{self.face_color}"/>'
            elif self.emotion == "sad":
                shapes = eyes_svg + f'<path d="M 140 {290 + mouth_y_offset} A 60 60 0 0 1 260 {290 + mouth_y_offset} Z" fill="{self.face_color}"/>'
            elif self.emotion == "neutral":
                shapes = eyes_svg + f'<rect x="130" y="{250 + mouth_y_offset}" width="140" height="20" rx="4" fill="{self.face_color}" />'
            elif self.emotion == "surprised":
                shapes = eyes_svg + f'<circle cx="200" cy="{265 + mouth_y_offset}" r="40" fill="{self.face_color}" />'
            else:
                shapes = eyes_svg
                
        return f"{svg_start}{shapes}{svg_end}"

    def _render_current_frame(self):
        y_offset = math.sin(self.breathing_step) * 4.0
        x_offset = math.sin(self.scan_step) * 10.0 if self.is_scanning else 0.0
        svg_text = self._generate_svg(y_offset, x_offset)
        
        svg_bytes = QByteArray(svg_text.encode('utf-8'))
        renderer = QSvgRenderer(svg_bytes)
        if renderer.isValid():
            image = QImage(400, 400, QImage.Format.Format_RGB32)
            image.fill(QColor(self.bg_color))
            painter = QPainter(image)
            renderer.render(painter)
            painter.end()
            self.label.setPixmap(QPixmap.fromImage(image))


# --- ENTRY POINT TO RUN THE WINDOW ---
def main():
    app = QApplication(sys.argv)

    main_window = QMainWindow()
    main_window.setWindowTitle("Robot Face")
    main_window.setFixedSize(450, 520)

    # Layout setup
    central_widget = QWidget()
    main_layout = QVBoxLayout()
    
    # Label to render the face
    face_label = QLabel()
    face_label.setFixedSize(400, 400)
    
    # Initialize the Robot Face class
    robot = RobotFace(face_label)

    # Buttons layout to test emotions
    btn_layout = QHBoxLayout()
    
    btn_happy = QPushButton("Happy")
    btn_happy.clicked.connect(lambda: robot.change_emotion("happy"))
    
    btn_sad = QPushButton("Sad")
    btn_sad.clicked.connect(lambda: robot.change_emotion("sad"))
    
    btn_neutral = QPushButton("Neutral")
    btn_neutral.clicked.connect(lambda: robot.change_emotion("neutral"))
    
    btn_surprised = QPushButton("Surprised")
    btn_surprised.clicked.connect(lambda: robot.change_emotion("surprised"))
    
    btn_talk = QPushButton("Talk")
    btn_talk.clicked.connect(lambda: robot.talk(3000)) # Talks for 3 seconds

    btn_layout.addWidget(btn_happy)
    btn_layout.addWidget(btn_sad)
    btn_layout.addWidget(btn_neutral)
    btn_layout.addWidget(btn_surprised)
    btn_layout.addWidget(btn_talk)

    main_layout.addWidget(face_label, alignment=Qt.AlignmentFlag.AlignCenter)
    main_layout.addLayout(btn_layout)
    central_widget.setLayout(main_layout)
    
    main_window.setCentralWidget(central_widget)
    main_window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()