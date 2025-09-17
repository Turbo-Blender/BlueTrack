from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from kafka import KafkaProducer, KafkaConsumer
from widgets import BlueTrackTile
from colors import *
import threading
import json
import sys
import os
from datetime import datetime, timezone
import uuid
from functools import partial
from dotenv import load_dotenv
load_dotenv()
# Switch mode:
# 0 - login, 1 - register


# Zookeeper is set to handle max 60 connections in config/zoo.cfg

# Base project path
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Define colors



def resource_path(*parts):
    return os.path.join(BASE_PATH, *parts)


class BlueTrackUI(QWidget):
    
    loginSignal = Signal(str, str, bool, str, str)  # topic, message, success, session_id
    songsSignal = Signal(str, list)  # topic, login_random_tracks

    def __init__(self):
        super().__init__()
        self.setObjectName("mainWindow")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setFixedSize(1500, 800)
        self.setStyleSheet(
            "#mainWindow { background-color: #121212; }"
            "#mainWindow QLabel, #mainWindow QLineEdit, #mainWindow QPushButton { color: #FFFFFF; }"
        )
        self.content = QWidget()
        self.content_layout = QVBoxLayout()
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
        self.login_consumer = KafkaConsumer(
            'register_user_response', 'login_user_response', 'session_auth_response',
            bootstrap_servers='localhost:9092',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            group_id='qt_client_login'
        )

        self.songs_consumer = KafkaConsumer(
            'songs_response','top_genres',
            bootstrap_servers='localhost:9092',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            group_id='qt_client_songs'
        )

        self.loginSignal.connect(self._handle_login_response)
        self.songsSignal.connect(self._handle_songs_response)

        threading.Thread(target=self._consume_login_responses, daemon=True).start()
        threading.Thread(target=self._consume_songs_responses, daemon=True).start()
        print("[CLIENT] songs_consumer thread started")

        #Tile and song control
        self.tiles = {}
        self.active_song = {}
        self.paused = True
        self.playing = False
        self.song_duration = 0
        self.time_left = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.song_index = None
        self.last_index = None
        # Drag support
        self.drag_pos = QPoint()
        
        #PySpark top 5 genres

        self.top5_genres = None


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
        self.content.setLayout(self.content_layout)

    def _consume_login_responses(self):

        for msg in self.login_consumer:
            topic = msg.topic
            data = msg.value
            success = data.get('success', False)
            user_id = data.get('user_id', None)
            text = data.get('message', '')
            session_id = data.get('session_id', None)
            print(f"[CLIENT] Received response from topic '{topic}': {text} (Success: {success})")
            self.loginSignal.emit(topic, text, success, session_id, user_id)

    def _consume_songs_responses(self):
        for msg in self.songs_consumer:
            topic = msg.topic
            songs_properties = msg.value
            print(f"[CLIENT] Received songs response from topic '{topic}'")
            self.songsSignal.emit(topic, songs_properties)

    def _handle_login_response(self, topic, text, success, session_id, user_id):
        color = SUCCESS_COLOR if success else ERROR_COLOR
        if topic == 'register_user_response':
            self.register_feedback.setText(text)
            self.register_feedback.setStyleSheet(f"color: {color};")
        elif topic == 'login_user_response':
            self.session_correct = success
            self.login_feedback.setText(text)
            self.login_feedback.setStyleSheet(f"color: {color};")
            self.session_id = session_id
            self.user_id = user_id
            print(f"[CLIENT] Login response: {self.user_id} (Success: {success})")
            if success:
                self.switch_mode(2)
                self.producer.send('songs_update', {})
                print(f"[CLIENT] Sending songs update request for user '{user_id}'")
                self.producer.flush()

        elif topic == 'session_auth_response':
            self.session_id = session_id
            if success:
                self.session_correct = True
            else:
                self.session_correct = False

    def _handle_songs_response(self, topic, songs_properties):
        print("[CLIENT] _handle_songs_response triggered")
        if topic == 'songs_response':
            self.genres_tiles(songs_properties)
        elif topic == 'top_genres':
            
            self.top5_genres = songs_properties
            print("\n", self.top5_genres)
            self.update_top5_genres_sidebar()

    
    def update_top5_genres_sidebar(self):
    
        if not hasattr(self, "sidebar"):
            return

        # Usuń stare widgety
        for i in reversed(range(self.sidebar_layout.count())):
            widget = self.sidebar_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        if not self.top5_genres:
            return

        # Nagłówek
        header = QLabel("Top Gatunki")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        header.setStyleSheet("color: #FFFFFF; padding: 8px;")
        self.sidebar_layout.addWidget(header)

    
        for genre_info in self.top5_genres[:5]:
            genre = genre_info["genre"]
            count = genre_info["count"]
            btn = QLabel(f"{genre} ({count})")
            btn.setStyleSheet(
                "QLabel {"
                "  background: #282828;"
                "  color: #FFFFFF;"
                "  padding: 6px 8px;"
                "  border-radius: 6px;"
                "}"
            )
            self.sidebar_layout.addWidget(btn)

        self.sidebar_layout.addStretch()
    def genres_tiles(self, songs_properties):
        outer_scroll_area = QScrollArea()
        outer_scroll_area.setWidgetResizable(True)
        outer_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        outer_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        outer_scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #121212;
                border: none;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 10px;
            }
            QScrollBar::handle:vertical {
                background: #535353;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #888;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        main_container = QWidget()
        main_layout = QVBoxLayout(main_container)
        main_layout.setSpacing(40)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_container.setStyleSheet("background-color: #121212;")

        outer_scroll_area.setWidget(main_container)

        self.login_random_tracks = songs_properties[0]
        self.genres_names = songs_properties[1]
        self.tiles = {}

        for genre, tracks in self.login_random_tracks.items():
            list_of_tiles = []
            for i in range(10):
                track_name = tracks["track_names"][i]
                artist = tracks["artists"][i]
                track_id = tracks["tracks_id"][i]
                duration_ms = tracks["duration_ms"][i]
                message = artist + " - " + track_name
                tile = BlueTrackTile(message, track_id, genre, duration_ms)
                tile.setFixedSize(200, 250)
                tile.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                list_of_tiles.append(tile)
                tile.tile_button.clicked.connect(partial(self.handle_tile_click, tile))

            self.tiles[genre] = list_of_tiles

        for genre, genre_tiles in self.tiles.items():
            section_widget = QWidget()
            section_layout = QVBoxLayout(section_widget)
            section_layout.setSpacing(10)
            section_layout.setContentsMargins(0, 0, 0, 0)

            genre_label = QLabel(genre)
            genre_label.setStyleSheet("""
                QLabel {
                    font-size: 22px;
                    font-weight: 700;
                    color: #FFFFFF;
                    padding-left: 5px;
                }
            """)
            section_layout.addWidget(genre_label)

            tracks_area = QScrollArea()
            tracks_area.setWidgetResizable(False)
            tracks_area.setFixedHeight(270)
            tracks_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            tracks_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            tracks_area.setStyleSheet("""
                QScrollArea {
                    border: none;
                    background-color: transparent;
                }
                QScrollBar:horizontal {
                    background: transparent;
                    height: 8px;
                    margin: 0px 20px 0px 20px;
                }
                QScrollBar::handle:horizontal {
                    background: #535353;
                    border-radius: 4px;
                }
                QScrollBar::handle:horizontal:hover {
                    background: #888;
                }
                QScrollBar::add-line:horizontal,
                QScrollBar::sub-line:horizontal {
                    width: 0px;
                }
            """)

            # Sztywne wymiary kontenera kafelków
            tile_width = 200
            tile_height = 250
            tile_spacing = 12
            horizontal_margins = 40
            vertical_margins = 20
            total_width = len(genre_tiles) * tile_width + (len(genre_tiles) - 1) * tile_spacing + horizontal_margins
            total_height = tile_height + vertical_margins

            inner_container = QWidget()
            inner_container.setFixedSize(total_width, total_height)
            inner_container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

            inner_layout = QHBoxLayout(inner_container)
            inner_layout.setSpacing(tile_spacing)
            inner_layout.setContentsMargins(10, 10, 10, 10)

            for tile in genre_tiles:
                tile.setFixedSize(tile_width, tile_height)
                tile.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                inner_layout.addWidget(tile)

            tracks_area.setWidget(inner_container)
            section_layout.addWidget(tracks_area)
            main_layout.addWidget(section_widget)
        

        self.content_layout.addWidget(outer_scroll_area)

        
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

        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(240)
        self.sidebar.setStyleSheet(
            "background-color: #181818;"
            "border-right: 2px solid #383838;"
        )
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(16, 16, 16, 16)
        self.sidebar_layout.setSpacing(16)
        middle_layout.addWidget(self.sidebar)


        self.content = QWidget()
        
        self.content.setStyleSheet(
            "background-color: #121212;"
            "border-left: 2px solid #383838;"
            "border-right: 2px solid #383838;"
        )
    
        self.content_layout = QHBoxLayout(self.content)
        self.content_layout.setContentsMargins(24, 24, 24, 24)
        self.content_layout.setSpacing(24)
        
        
        # TODO: Dodaj siatkę albumów/utworów
        middle_layout.addWidget(self.content)    
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

        middle_layout.addWidget(details)

        outer_layout.addWidget(middle)

        # Dolne sterowanie odtwarzaczem
        

        stop_button = QPushButton()
        start_button = QPushButton()
        next_button = QPushButton()
        previous_button = QPushButton()

        icon_size = QSize(30, 30)

        for btn, img in [
            (stop_button, "stop_button.png"),
            (start_button, "start_button.png"),
            (next_button, "next_button.png"),
            (previous_button, "previous_button.png"),
        ]:
            path = resource_path("img", img)
            btn.setIcon(QIcon(path))
            btn.setIconSize(icon_size)
            btn.setFixedSize(icon_size + QSize(12, 12))

            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #2E2E2E;
                    border: 2px solid #565656;
                    border-radius: 10px;
                }}
                QPushButton:hover {{
                    border-color: {PRIMARY_COLOR};
                }}
            """)

        stop_container = QWidget()
        stop_container.setStyleSheet("background: transparent; border: none;")
        stop_layout = QHBoxLayout(stop_container)
        stop_layout.setContentsMargins(0, 0, 0, 0)
        stop_layout.setSpacing(0)
        stop_layout.addWidget(stop_button, alignment=Qt.AlignCenter)

        start_container = QWidget()
        start_container.setStyleSheet("background: transparent; border: none;")
        start_layout = QHBoxLayout(start_container)
        start_layout.setContentsMargins(0, 0, 0, 0)
        start_layout.setSpacing(0)
        start_layout.addWidget(start_button, alignment=Qt.AlignCenter)

        self.play_stack = QStackedWidget()
        self.play_stack.setFrameShape(QFrame.NoFrame)
        self.play_stack.setStyleSheet("background: transparent; border: none;")
        self.play_stack.addWidget(start_container)
        self.play_stack.addWidget(stop_container)
        
        self.play_stack.setCurrentIndex(0)

        stack_size = stop_button.size()
        self.play_stack.setFixedSize(stack_size)

        controls = QWidget()
        controls.setFixedHeight(96)
        controls.setStyleSheet(
            "background-color: #181818;"
            "border-top: 2px solid #383838;"
        )
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(24, 0, 24, 0)
        controls_layout.setSpacing(0)

        # LEWA CZĘŚĆ - info o aktualnie wybranym kafelku
        left = QWidget()
        left.setStyleSheet("background: transparent;")
        left_layout = QHBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)
        left.setMinimumWidth(200)

        # Miniatura koloru
        self.song_color_preview = QLabel()
        self.song_color_preview.setFixedSize(48, 48)
        self.song_color_preview.setStyleSheet("background-color: transparent; border-radius: 4px;")

        # Tekst utworu
        self.song_title_label = QLabel("Wybierz utwór...")
        self.song_title_label.setStyleSheet("color: white; font-size: 14px;")
        self.song_title_label.setWordWrap(True)

        left_layout.addWidget(self.song_color_preview, alignment=Qt.AlignVCenter)
        left_layout.addWidget(self.song_title_label, alignment=Qt.AlignVCenter) 

        
        

        # ŚRODEK - przyciski (wycentrowane)
        center = QWidget()
        center.setStyleSheet("background: transparent;")
        center_layout = QHBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(8)

        # Dodajemy przyciski do centrum; wyrównujemy pionowo do środka
        center_layout.addWidget(previous_button, alignment=Qt.AlignVCenter)
        center_layout.addWidget(self.play_stack, alignment=Qt.AlignVCenter)
        center_layout.addWidget(next_button, alignment=Qt.AlignVCenter)
        center_layout.setAlignment(Qt.AlignCenter)

        # PRAWA CZĘŚĆ - placeholder (przezroczysty, rezerwacja miejsca)
        right = QWidget()
        right.setStyleSheet("background: transparent;")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        right.setMinimumWidth(200)

        
        right_layout.addStretch()

        # Label wyświetlający czas utworu
        self.time_label = QLabel("0:00 / 0:00")
        self.time_label.setStyleSheet("color: #AAAAAA; font-size: 12px;")
        self.time_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        right_layout.addWidget(self.time_label)

        controls_layout.addWidget(left, 1, Qt.AlignVCenter | Qt.AlignLeft)
        controls_layout.addWidget(center, 0, Qt.AlignCenter)
        controls_layout.addWidget(right, 1, Qt.AlignVCenter | Qt.AlignRight)

        outer_layout.addWidget(controls)

        stop_button.clicked.connect(lambda : self.stop_track(0))
        start_button.clicked.connect(lambda : self.play_track(1))
        next_button.clicked.connect(self.next_track)
        previous_button.clicked.connect(self.previous_track)

        
        btn_logout.clicked.connect(self.logout_user)
        btn_settings.clicked.connect(self._create_settings_page)

        return page



    def switch_mode(self, idx):
        for widget in [getattr(self, 'username_input', None), getattr(self, 'email_input', None), getattr(self, 'password_input', None),
                       getattr(self, 'login_username', None), getattr(self, 'login_password', None)]:
            if widget:
                widget.clear()
        for label in [getattr(self, 'register_feedback', None), getattr(self, 'login_feedback', None)]:
            if label:
                label.clear()
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
        print("\n", "Dane wysłane")
    def play_track(self, idx):
        if not self.active_song:
            print("Brak wybranego utworu!")
            return
        response = {
            "user_id": self.user_id,
            "track_id": self.active_song["track_id"],
            "operation_type": "start",
            "start_time": datetime.now(timezone.utc).isoformat(),
            "duration_ms": int(self.song_duration),
            "genre": self.active_song["genre"]
        }
        self.producer.send("songs_tracker",response)
        self.producer.flush()
        print("\n Wysłano do songs_tracker: \n", response)
        self.play_stack.setCurrentIndex(idx)
        if not self.timer.isActive():
            self.timer.start(1000)
            
    

    def stop_track(self, idx):
        self.play_stack.setCurrentIndex(idx)
        if self.timer.isActive():
            self.timer.stop()
    
    def next_track(self):
        if not self.active_song:
            print("Brak wybranego utworu!")
            return
        if self.song_index == 9:
            print("Jesteś poza zakresem")
            return
        
        self.song_index = self.song_index + 1
        tile = self.tiles[self.active_song["genre"]][self.song_index]
        self.active_song = {
            "genre": tile.genre,
            "track_id": tile.track_id,
            "title": tile.wrapped_title,
            "duration_ms": int(tile.duration_ms) // 1000
        }
        self.play_stack.setCurrentIndex(0)
        self.song_duration = self.active_song["duration_ms"]
        if self.timer.isActive():
            self.timer.stop()
        self.time_left = self.song_duration

        
        self.song_title_label.setText(f"{tile.wrapped_title}")
        self.song_color_preview.setStyleSheet( f"background-color: {tile.color}; border-radius: 4px;" )
        self.time_label.setText(f"0:00 / {self.format_time(self.song_duration)}")

    def previous_track(self):
        if not self.active_song:
            print("Brak wybranego utworu!")
            return
        if self.song_index == 0:
            print("Jesteś poza zakresem")
            return
        
        self.song_index = self.song_index - 1
        tile = self.tiles[self.active_song["genre"]][self.song_index]
        self.active_song = {
            "genre": tile.genre,
            "track_id": tile.track_id,
            "title": tile.wrapped_title,
            "duration_ms": int(tile.duration_ms) // 1000
        }
        self.play_stack.setCurrentIndex(0)
        self.song_duration = self.active_song["duration_ms"]

        if self.timer.isActive():
            self.timer.stop()
        self.time_left = self.song_duration

        
        self.song_title_label.setText(f"{tile.wrapped_title}")
        self.song_color_preview.setStyleSheet( f"background-color: {tile.color}; border-radius: 4px;" )
        self.time_label.setText(f"0:00 / {self.format_time(self.song_duration)}")
    
    def format_time(self, seconds: int) -> str:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}:{secs:02d}"
    
    def update_time(self):
        if self.time_left > 0:
            elapsed = self.song_duration - self.time_left
            self.time_left -= 1
            self.time_label.setText(
                f"{self.format_time(elapsed)} / {self.format_time(self.song_duration)}"
            )
        else:
            print("Utwór skończył się.")
            self.time_label.setText("0:00 / 0:00")
            self.active_song = {}
            self.song_color_preview.setStyleSheet("background-color: transparent; border-radius: 4px;")
            self.song_title_label.setStyleSheet("color: white; font-size: 14px;")
            self.song_title_label.setText("Wybierz utwór...")
            self.stop_track(0)

    def handle_tile_click(self, tile):
        
        if self.active_song and tile.track_id == list(self.active_song.values())[0][0]:
            print("Ten sam utwór już jest aktywny")
            return
        
        
        self.active_song = {
            "genre": tile.genre,
            "track_id": tile.track_id,
            "title": tile.wrapped_title,
            "duration_ms": int(tile.duration_ms) // 1000
        }
        self.song_duration = self.active_song["duration_ms"]
        if self.timer.isActive():
            self.timer.stop()
        self.time_left = self.song_duration

        
        self.song_title_label.setText(f"{tile.wrapped_title}")
        self.song_color_preview.setStyleSheet( f"background-color: {tile.color}; border-radius: 4px;" )
        self.time_label.setText(f"0:00 / {self.format_time(self.song_duration)}")
        self.play_stack.setCurrentIndex(0)
        genre_tiles = self.tiles[self.active_song["genre"]]
        self.song_index = next(
        (i for i, tile in enumerate(genre_tiles) if tile.track_id == self.active_song["track_id"]),
        None
        )
        self.last_index = len(self.tiles[self.active_song["genre"]]) - 1

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
