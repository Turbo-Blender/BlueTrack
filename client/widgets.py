from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from colors import *

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

        # etykieta tytułu
        self.label = QLabel(title, self)
        self.label.setObjectName("BlueTrackTileLabel")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setFixedHeight(50)

        layout.addWidget(self.color_frame)
        layout.addWidget(self.label)
        
        # Styl z wykorzystaniem globalnych kolorów
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
        QLabel#BlueTrackTileLabel {{
            color: #FFFFFF;
            padding: 8px;
            font-size: 14px;
        }}
        QWidget#BlueTrackTile:hover QWidget#BlueTrackTileColor {{
            background-color: {color.replace('#', '#80')};
        }}
        """)
