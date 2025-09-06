from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from colors import *

def wrap_text(text, max_chars=20):
    """
    Dzieli tekst na linie co max_chars znaków.
    Działa najlepiej przy spacji między słowami.
    """
    words = text.split(' ')
    lines = []
    current_line = ''
    for word in words:
        if len(current_line + ' ' + word) <= max_chars:
            if current_line:
                current_line += ' ' + word
            else:
                current_line = word
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return '\n'.join(lines)

class BlueTrackTile(QWidget):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        color = random_color()
        self.setObjectName("BlueTrackTile")
        self.setFixedSize(200, 250)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # kolorowy blok
        self.color_frame = QWidget(self)
        self.color_frame.setObjectName("BlueTrackTileColor")
        self.color_frame.setFixedSize(200, 200)
        self.color_frame.setAutoFillBackground(True)

        # przycisk
        wrapped_title = wrap_text(title, max_chars=20)
        self.button = QPushButton(wrapped_title, self)
        self.button.setObjectName("BlueTrackTileButton")
        self.button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.button.setMinimumHeight(0)
        self.button.setMaximumHeight(16777215)

        layout.addWidget(self.color_frame)
        layout.addWidget(self.button)

        # style
        self.setStyleSheet(f"""
        QWidget#BlueTrackTile {{
            background-color: #282828;
            border-radius: 8px;
        }}
        QWidget#BlueTrackTileColor {{
            background-color: {color};
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
        }}
        QPushButton#BlueTrackTileButton {{
            color: #FFFFFF;
            padding: 8px;
            font-size: 14px;
            background: transparent;
            border: none;
            text-align: center;
        }}
        QPushButton#BlueTrackTileButton:hover {{
            color: {PRIMARY_COLOR};
        }}
        QWidget#BlueTrackTile:hover QWidget#BlueTrackTileColor {{
            background-color: {color.replace('#', '#80')};
        }}
        """)
