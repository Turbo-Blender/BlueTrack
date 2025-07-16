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
import uuid
import bcrypt
# Switch mode:
# 0 - login, 1 - register




# Base project path
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Define colors
PRIMARY_COLOR = "#0072ff"
HOVER_COLOR   = "#2892ff"
SUCCESS_COLOR = "#4caf50"  # zielony
ERROR_COLOR   = "#f44336"  # czerwony


def resource_path(*parts):
    return os.path.join(BASE_PATH, *parts)


class BlueTrackUI(QWidget):
    responseSignal = Signal(str, str, bool, str)  # topic, message, success, session_id

    def __init__(self):
        super().__init__()
        self.setObjectName("mainWindow")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setFixedSize(1500, 1000)
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
            'register_user_response', 'login_user_response', 'session_auth_response',
            bootstrap_servers='localhost:9092',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            group_id=f'qt_client_{uuid.uuid4()}'
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

        # Stack for pages
        self.stack = QStackedWidget()
        self.stack.addWidget(self._create_login_page())
        self.stack.addWidget(self._create_register_page())
        self.stack.addWidget(self._create_main_page())
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
            session_id = data.get('session_id', None)
            print(f"[CLIENT] Received response from topic '{topic}': {text} (Success: {success})")
            self.responseSignal.emit(topic, text, success, session_id)
            

    def _create_login_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 20, 30, 30)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignTop)

        
        self.btn_login = QPushButton("Logowanie")
        self.btn_register = QPushButton("Rejestracja")

        for btn in [self.btn_login, self.btn_register]:
            btn.setCursor(Qt.PointingHandCursor)
            btn.setCheckable(True)

        self.btn_login.setStyleSheet(
            "QPushButton {"
            f"  background: transparent;"
            f"  border: 2px solid #565656;"
            f"  border-radius: 8px;"
            f"  padding: 10px 20px;"
            f"  font-size: 16px;"
            f"  color: {PRIMARY_COLOR};"           
            f"  border-color: {PRIMARY_COLOR};"    
            f"  font-weight: bold;"                 
            "}"
            f"QPushButton:hover {{"
            f"  border-color: {HOVER_COLOR};"
            f"}}"
        )

        self.btn_register.setStyleSheet(
            "QPushButton {"
            f"  background: transparent;"
            f"  border: 2px solid #565656;"
            f"  border-radius: 8px;"
            f"  padding: 10px 20px;"
            f"  font-size: 16px;"       
            "}"
            f"QPushButton:hover {{"
            f"  border-color: {HOVER_COLOR};"
            f"}}"
        )
        
        self.btn_register.clicked.connect(lambda: self.switch_mode(1))
        
        switch_layout = QHBoxLayout()
        switch_layout.addWidget(self.btn_login)
        switch_layout.addWidget(self.btn_register)
        layout.addLayout(switch_layout)
        


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
        self.login_username.setFixedWidth(400)
        layout.addWidget(self._styled_input(self.login_username), alignment=Qt.AlignHCenter)
        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("Hasło")
        self.login_password.setFixedWidth(400)
        self.login_password.setEchoMode(QLineEdit.Password)
        layout.addWidget(self._styled_input(self.login_password), alignment=Qt.AlignHCenter)

        # Feedback label
        self.login_feedback = QLabel("")
        self.login_feedback.setAlignment(Qt.AlignCenter)
        self.login_feedback.setFont(QFont("Arial", 12))
        layout.addWidget(self.login_feedback)

        # Button
        btn = QPushButton("Zaloguj")
        btn.setFixedHeight(45)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedWidth(500)
        btn.setStyleSheet(
            f"QPushButton{{background-color:{PRIMARY_COLOR};border:none;border-radius:22px;font-size:16px;}}"
            f"QPushButton:hover{{background-color:{HOVER_COLOR};}}"
        )

        btn.clicked.connect(lambda: self.login_user())
        # btn.clicked.connect(lambda: self.switch_mode(2))
        layout.addWidget(btn, alignment=Qt.AlignHCenter)
        return page

    def _create_register_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 20, 30, 30)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignTop)

        self.btn_login = QPushButton("Logowanie")
        self.btn_register = QPushButton("Rejestracja")
        
        
        for btn in [self.btn_login, self.btn_register]:
            btn.setCursor(Qt.PointingHandCursor)
            btn.setCheckable(True)
        
        
        self.btn_register.setStyleSheet(
            "QPushButton {"
            f"  background: transparent;"
            f"  border: 2px solid #565656;"
            f"  border-radius: 8px;"
            f"  padding: 10px 20px;"
            f"  font-size: 16px;"
            f"  color: {PRIMARY_COLOR};"           
            f"  border-color: {PRIMARY_COLOR};"    
            f"  font-weight: bold;"                 
            "}"
            f"QPushButton:hover {{"
            f"  border-color: {HOVER_COLOR};"
            f"}}"
        )

        self.btn_login.setStyleSheet(
            "QPushButton {"
            f"  background: transparent;"
            f"  border: 2px solid #565656;"
            f"  border-radius: 8px;"
            f"  padding: 10px 20px;"
            f"  font-size: 16px;"       
            "}"
            f"QPushButton:hover {{"
            f"  border-color: {HOVER_COLOR};"
            f"}}"
        )

        self.btn_login.clicked.connect(lambda: self.switch_mode(0))
        switch_layout = QHBoxLayout()
        switch_layout.addWidget(self.btn_login)
        switch_layout.addWidget(self.btn_register)
        layout.addLayout(switch_layout)

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
        self.username_input.setFixedWidth(400)
        layout.addWidget(self._styled_input(self.username_input), alignment=Qt.AlignHCenter)
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        self.email_input.setFixedWidth(400)
        layout.addWidget(self._styled_input(self.email_input), alignment=Qt.AlignHCenter)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Hasło")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedWidth(400)
        layout.addWidget(self._styled_input(self.password_input), alignment=Qt.AlignHCenter)

        # Feedback label
        self.register_feedback = QLabel("")
        self.register_feedback.setAlignment(Qt.AlignCenter)
        self.register_feedback.setFont(QFont("Arial", 12))
        layout.addWidget(self.register_feedback)

        # Button
        btn = QPushButton("Zarejestruj się")
        btn.setFixedHeight(45)
        btn.setFixedWidth(500)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(
            f"QPushButton{{background-color:{PRIMARY_COLOR};border:none;border-radius:22px;font-size:16px;}}"
            f"QPushButton:hover{{background-color:{HOVER_COLOR};}}"
        )
        btn.clicked.connect(self.register_user)
        layout.addWidget(btn, alignment=Qt.AlignHCenter)
        return page

    def _create_main_page(self):
        page = QWidget()
        # Główne tło w stylu Spotify
        page.setStyleSheet("background-color: #121212;")
        outer_layout = QVBoxLayout(page)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # Środkowy obszar: sidebar + content + details
        middle = QWidget()
        middle_layout = QHBoxLayout(middle)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.setSpacing(0)

        # Lewy sidebar (lista playlist)
        sidebar = QWidget()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet(
            "background-color: #181818;"
            "border-right: 2px solid #383838;"
        )
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(16, 16, 16, 16)
        sidebar_layout.setSpacing(16)
        # TODO: Dodaj widgety playlist
        middle_layout.addWidget(sidebar)

        # Główna przestrzeń treści
        content = QWidget()
        content.setStyleSheet(
            "background-color: #121212;"
            "border-left: 2px solid #383838;"
            "border-right: 2px solid #383838;"
        )
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(24)
        # TODO: Dodaj siatkę albumów/utworów
        middle_layout.addWidget(content, 1)

        # Prawy panel szczegółów/kolejki
        details = QWidget()
        details.setFixedWidth(280)
        details.setStyleSheet(
            "background-color: #181818;"
            "border-left: 2px solid #383838;"
        )
        details_layout = QHBoxLayout(details)
        details_layout.setContentsMargins(16, 16, 16, 16)
        details_layout.setSpacing(16)
        # Przyciski po prawej: Ustawienia i Wyloguj
        btn_settings = QPushButton("Ustawienia")
        btn_logout = QPushButton("Wyloguj")

        details_layout.setAlignment(Qt.AlignTop)

        for btn in (btn_settings, btn_logout):
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(48)
            btn.setStyleSheet(
                "QPushButton {"
                "  background: transparent;"
                "  border: 2px solid #565656;"
                "  border-radius: 8px;"
                "  padding: 10px 20px;"
                "  font-size: 16px;"
                "}"
                f"QPushButton:hover {{border-color: {HOVER_COLOR};}}"
            )
            details_layout.addWidget(btn)

        # TODO: Dodaj szczegóły utworu i kolejkę
        middle_layout.addWidget(details)

        outer_layout.addWidget(middle)

        # Dolne sterowanie odtwarzaczem
        controls = QWidget()
        controls.setFixedHeight(96)
        controls.setStyleSheet(
            "background-color: #181818;"
            "border-top: 2px solid #383838;"
        )
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(24, 12, 24, 12)
        controls_layout.setSpacing(32)
        # TODO: Dodaj przyciski play/pause, prev/next, suwaki (użyj PRIMARY_COLOR jako accent)
        middle_layout.setStretchFactor(content, 1)
        outer_layout.addWidget(controls)
        btn_logout.clicked.connect(self.logout_user)
        btn_settings.clicked.connect(self._create_settings_page)

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

    def logout_user(self):
        self.session_auth()
        if self.session_correct:
            self.session_id = None
        self.switch_mode(0)
    
    def _create_settings_page(self):
        self.session_auth()
        if self.session_correct:
            print("Session authenticated successfully.")
        else:
            print("Session authentication failed.")

    def session_auth(self):
        self.producer.send('session_auth', {"session_id": self.session_id})
        self.producer.flush()
    
    def _handle_response(self, topic, text, success, session_id):
        color = SUCCESS_COLOR if success else ERROR_COLOR
        if topic == 'register_user_response':
            self.register_feedback.setText(text)
            self.register_feedback.setStyleSheet(f"color: {color};")
        elif topic == 'login_user_response':
            self.session_correct = success
            self.login_feedback.setText(text)
            self.login_feedback.setStyleSheet(f"color: {color};")
            self.session_id = session_id
            success and self.switch_mode(2)
        elif topic == 'session_auth_response':
            self.session_id = session_id
            if success:
                self.session_correct = True
            else:
                self.session_correct = False

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
    window = BlueTrackUI()
    window.show()
    sys.exit(app.exec())
