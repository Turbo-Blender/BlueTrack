from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QHBoxLayout,
    QStackedWidget
)
from PySide6.QtGui import QPixmap, QFont, QIcon
from PySide6.QtCore import Qt, QPoint, Signal
from kafka import KafkaProducer, KafkaConsumer
import threading
import json
import sys
import os

# Base project path
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Define colors
PRIMARY_COLOR = "#0072ff"
HOVER_COLOR   = "#2892ff"
SUCCESS_COLOR = "#4caf50"  # zielony
ERROR_COLOR   = "#f44336"  # czerwony


def resource_path(*parts):
    return os.path.join(BASE_PATH, *parts)


class RegisterLoginApp(QWidget):
    responseSignal = Signal(str, str, str)  # topic, message, color

    def __init__(self):
        super().__init__()
        self.setObjectName("mainWindow")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setFixedSize(1200, 800)
        self.setStyleSheet(
            "#mainWindow { background-color: #121212; }"
            "#mainWindow QLabel, #mainWindow QLineEdit, #mainWindow QPushButton { color: #FFFFFF; }"
        )

        # Window icon
        icon_path = resource_path("img", "main_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Kafka producer
        self.producer = KafkaProducer(
            bootstrap_servers='localhost:9092',
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        # Kafka consumer for both register and login responses
        self.consumer = KafkaConsumer(
            'register_user_response', 'login_user_response',
            bootstrap_servers='localhost:9092',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            group_id='qt_client'
        )
        self.responseSignal.connect(self._handle_response)
        threading.Thread(target=self._consume_responses, daemon=True).start()

        # Drag support
        self.drag_pos = QPoint()

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Title bar
        title_bar = QWidget(self)
        title_bar.setFixedHeight(40)
        title_bar.setStyleSheet("background-color: #1E1E1E;")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(15, 0, 15, 0)
        title_layout.setSpacing(5)
        # Small icon
        icon_lbl = QLabel(self)
        if os.path.exists(icon_path):
            icon_lbl.setPixmap(
                QPixmap(icon_path).scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        title_layout.addWidget(icon_lbl)
        # App name
        title_lbl = QLabel("BlueTrack", self)
        title_lbl.setFont(QFont("Arial", 14, QFont.Bold))
        title_lbl.setStyleSheet(f"color: {PRIMARY_COLOR};")
        title_layout.addWidget(title_lbl)
        title_layout.addStretch()
        # Minimize & close buttons
        for sym, slot, hov in [("–", self.showMinimized, HOVER_COLOR), ("×", self.close, '#FF5C5C')]:
            btn = QPushButton(sym, self)
            btn.setFixedSize(20, 20)
            btn.setStyleSheet(
                "QPushButton{background:transparent;border:none;color:#FFF;}"
                f"QPushButton:hover{{color:{hov};}}"
            )
            btn.clicked.connect(slot)
            title_layout.addWidget(btn)
        main_layout.addWidget(title_bar)

        # Body
        body = QWidget(self)
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setAlignment(Qt.AlignCenter)

        # Mode switch
        switch_layout = QHBoxLayout()
        self.btn_login = QPushButton("Logowanie")
        self.btn_register = QPushButton("Rejestracja")
        for btn in (self.btn_login, self.btn_register):
            btn.setCursor(Qt.PointingHandCursor)
            btn.setCheckable(True)
            btn.setStyleSheet(
                "QPushButton{background:transparent;border:2px solid #565656;border-radius:8px;padding:10px 20px;font-size:16px;}"
                f"QPushButton:checked{{color:{PRIMARY_COLOR};border-color:{PRIMARY_COLOR};font-weight:bold;}}"
                f"QPushButton:hover{{border-color:{HOVER_COLOR};}}"
            )
        self.btn_login.clicked.connect(lambda: self.switch_mode(0))
        self.btn_register.clicked.connect(lambda: self.switch_mode(1))
        switch_layout.addWidget(self.btn_login)
        switch_layout.addWidget(self.btn_register)
        body_layout.addLayout(switch_layout)

        # Stack for pages
        self.stack = QStackedWidget()
        self.stack.addWidget(self._create_login_page())
        self.stack.addWidget(self._create_register_page())
        body_layout.addWidget(self.stack)
        # Default to registration
        self.switch_mode(1)

        main_layout.addWidget(body)

    def _consume_responses(self):
        for msg in self.consumer:
            topic = msg.topic
            data = msg.value
            success = data.get('success', False)
            text = data.get('message', '')
            color = SUCCESS_COLOR if success else ERROR_COLOR
            self.responseSignal.emit(topic, text, color)

    def _create_login_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 20, 30, 30)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignTop)

        # Logo
        logo = QLabel()
        p = resource_path("img", "main_icon.png")
        if os.path.exists(p):
            logo.setPixmap(
                QPixmap(p).scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)

        # Header
        header = QLabel("Zaloguj się")
        header.setFont(QFont("Arial", 24, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # Inputs
        self.login_username = QLineEdit()
        self.login_username.setPlaceholderText("Nazwa użytkownika lub Email")
        layout.addWidget(self._styled_input(self.login_username))
        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("Hasło")
        self.login_password.setEchoMode(QLineEdit.Password)
        layout.addWidget(self._styled_input(self.login_password))

        # Feedback label
        self.login_feedback = QLabel("")
        self.login_feedback.setAlignment(Qt.AlignCenter)
        self.login_feedback.setFont(QFont("Arial", 12))
        layout.addWidget(self.login_feedback)

        # Button
        btn = QPushButton("Zaloguj")
        btn.setFixedHeight(45)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(
            f"QPushButton{{background-color:{PRIMARY_COLOR};border:none;border-radius:22px;font-size:16px;}}"
            f"QPushButton:hover{{background-color:{HOVER_COLOR};}}"
        )
        btn.clicked.connect(self.login_user)
        layout.addWidget(btn)
        return page

    def _create_register_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 20, 30, 30)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignTop)

        # Logo
        logo = QLabel()
        p = resource_path("img", "main_icon.png")
        if os.path.exists(p):
            logo.setPixmap(
                QPixmap(p).scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)

        # Header
        header = QLabel("Załóż konto")
        header.setFont(QFont("Arial", 24, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # Inputs
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Nazwa użytkownika")
        layout.addWidget(self._styled_input(self.username_input))
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        layout.addWidget(self._styled_input(self.email_input))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Hasło")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self._styled_input(self.password_input))

        # Feedback label
        self.register_feedback = QLabel("")
        self.register_feedback.setAlignment(Qt.AlignCenter)
        self.register_feedback.setFont(QFont("Arial", 12))
        layout.addWidget(self.register_feedback)

        # Button
        btn = QPushButton("Zarejestruj się")
        btn.setFixedHeight(45)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(
            f"QPushButton{{background-color:{PRIMARY_COLOR};border:none;border-radius:22px;font-size:16px;}}"
            f"QPushButton:hover{{background-color:{HOVER_COLOR};}}"
        )
        btn.clicked.connect(self.register_user)
        layout.addWidget(btn)
        return page

    def switch_mode(self, idx):
        # Clear all inputs and feedback labels
        for widget in [getattr(self, 'username_input', None), getattr(self, 'email_input', None), getattr(self, 'password_input', None),
                       getattr(self, 'login_username', None), getattr(self, 'login_password', None)]:
            if widget:
                widget.clear()
        for label in [getattr(self, 'register_feedback', None), getattr(self, 'login_feedback', None)]:
            if label:
                label.clear()
        # Switch the page
        self.stack.setCurrentIndex(idx)
        self.btn_login.setChecked(idx == 0)
        self.btn_register.setChecked(idx == 1)

    def register_user(self):
        u = self.username_input.text().strip()
        e = self.email_input.text().strip()
        p = self.password_input.text().strip()
        if not (u and e and p):
            self.register_feedback.setText("Wypełnij wszystkie pola!")
            self.register_feedback.setStyleSheet(f"color: {ERROR_COLOR};")
            return
        # Send to server
        self.producer.send('register_user', {"username": u, "email": e, "password": p})
        self.producer.flush()

    def login_user(self):
        u = self.login_username.text().strip()
        p = self.login_password.text().strip()
        if not (u and p):
            self.login_feedback.setText("Wypełnij wszystkie pola!")
            self.login_feedback.setStyleSheet(f"color: {ERROR_COLOR};")
            return
        # Send to server
        self.producer.send('login_user', {"username": u, "password": p})
        self.producer.flush()

    def _handle_response(self, topic, text, color):
        if topic == 'register_user_response':
            self.register_feedback.setText(text)
            self.register_feedback.setStyleSheet(f"color: {color};")
        elif topic == 'login_user_response':
            self.login_feedback.setText(text)
            self.login_feedback.setStyleSheet(f"color: {color};")

    def _styled_input(self, w):
        w.setFixedHeight(40)
        w.setStyleSheet(
            "QLineEdit{background-color:#282828;border:2px solid #282828;border-radius:20px;padding-left:15px;font-size:14px;}"
            + f"QLineEdit:focus{{border:2px solid {PRIMARY_COLOR};}}"
        )
        return w

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.drag_pos = e.globalPosition().toPoint()

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.LeftButton:
            self.move(
                self.pos() + e.globalPosition().toPoint() - self.drag_pos
            )
            self.drag_pos = e.globalPosition().toPoint()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RegisterLoginApp()
    window.show()
    sys.exit(app.exec())
