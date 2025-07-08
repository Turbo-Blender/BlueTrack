from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from kafka import KafkaProducer
import json
import sys

class RegisterApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("User Registration")

        # Kafka producer
        self.producer = KafkaProducer(
            bootstrap_servers='localhost:9092',
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )

        # UI
        layout = QVBoxLayout()
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        layout.addWidget(QLabel("Username:"))
        layout.addWidget(self.username_input)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(QLabel("Password:"))
        layout.addWidget(self.password_input)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        layout.addWidget(QLabel("Email:"))
        layout.addWidget(self.email_input)
        
        register_btn = QPushButton("Zarejestruj")
        register_btn.clicked.connect(self.register_user)
        layout.addWidget(register_btn)

        self.setLayout(layout)

    def register_user(self):
        user_data = {
            "username": self.username_input.text(),
            "password": self.password_input.text(),
            "email": self.email_input.text()
        }

        # Wysyłanie na topic
        self.producer.send('register_user', user_data)
        self.producer.flush()

        QMessageBox.information(self, "Rejestracja", "Dane zostały wysłane do serwera!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RegisterApp()
    window.show()
    sys.exit(app.exec())