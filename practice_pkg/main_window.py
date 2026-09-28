import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QMessageBox
)
from PyQt5.QtCore import QTimer

from practice_pkg.turtle_node import TurtleControllerNode
from practice_pkg.db_helper import DB


class MainWindow(QMainWindow):
    def __init__(self, node: TurtleControllerNode, db: DB):
        super().__init__()
        self.node = node
        self.db = db

        # Manage session ID by fetching the latest ID from DB (MAX(id) + 1 at startup)
        max_id = self.db.get_max_session_id()
        self.current_id = max_id + 1 if max_id > 0 else 1

        # Memory buffer to hold pose records before batch insertion into DB upon exit [(id, x, y, theta), ...]
        self.pose_buffer = []

        self.init_ui()

        # Timer for periodic UI pose updates (every 0.1s)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_pose_label)
        self.timer.start(100)

    def init_ui(self):
        self.setWindowTitle('Turtlesim GUI Controller')
        self.resize(340, 450)

        # UI stylesheet configuration for button visual distinction
        self.setStyleSheet("""
            QWidget {
                font-family: Arial, sans-serif;
                font-size: 13px;
                background-color: #F8F9FA;
            }
            QLabel {
                color: #212529;
                padding: 3px;
            }
            QPushButton {
                background-color: #E9ECEF;
                border: 1px solid #CED4DA;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
                min-height: 28px;
            }
            QPushButton:hover {
                background-color: #DEE2E6;
            }
            QPushButton:pressed {
                background-color: #CED4DA;
            }
            QPushButton#btn_stop {
                background-color: #E63946;
                color: white;
            }
            QPushButton#btn_stop:hover {
                background-color: #D62828;
            }
            QPushButton#btn_reset {
                background-color: #FFB703;
                color: #000000;
            }
            QPushButton#btn_reset:hover {
                background-color: #FB8500;
            }
            QPushButton#btn_save {
                background-color: #2A9D8F;
                color: white;
            }
            QPushButton#btn_save:hover {
                background-color: #264653;
            }
            QPushButton#btn_quit {
                background-color: #457B9D;
                color: white;
            }
            QPushButton#btn_quit:hover {
                background-color: #1D3557;
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 1. Status labels
        self.label_session = QLabel(f"<b>Session ID:</b> {self.current_id}", self)
        self.label_pose = QLabel("<b>Pose:</b> X: 0.00 | Y: 0.00 | Theta: 0.00", self)
        self.label_buffer_count = QLabel("<b>Saved Records:</b> 0 count", self)

        main_layout.addWidget(self.label_session)
        main_layout.addWidget(self.label_pose)
        main_layout.addWidget(self.label_buffer_count)

        # 2. Directional control buttons
        btn_up = QPushButton("▲ UP", self)
        btn_down = QPushButton("▼ DOWN", self)
        btn_left = QPushButton("◀ LEFT", self)
        btn_right = QPushButton("▶ RIGHT", self)
        btn_stop = QPushButton("■ STOP", self)
        btn_stop.setObjectName("btn_stop")

        btn_up.clicked.connect(lambda: self.node.move_forward())
        btn_down.clicked.connect(lambda: self.node.move_backward())
        btn_left.clicked.connect(lambda: self.node.turn_left())
        btn_right.clicked.connect(lambda: self.node.turn_right())
        btn_stop.clicked.connect(lambda: self.node.stop())

        # Layout arrangement for directional buttons
        row1 = QHBoxLayout()
        row1.addWidget(btn_up)

        row2 = QHBoxLayout()
        row2.addWidget(btn_left)
        row2.addWidget(btn_stop)
        row2.addWidget(btn_right)

        row3 = QHBoxLayout()
        row3.addWidget(btn_down)

        main_layout.addLayout(row1)
        main_layout.addLayout(row2)
        main_layout.addLayout(row3)

        # 3. Action buttons
        btn_reset = QPushButton("Reset Position", self)
        btn_reset.setObjectName("btn_reset")

        btn_save = QPushButton("Save Current Pose", self)
        btn_save.setObjectName("btn_save")

        btn_quit = QPushButton("Quit & Save to DB", self)
        btn_quit.setObjectName("btn_quit")

        btn_reset.clicked.connect(self.on_reset_clicked)
        btn_save.clicked.connect(self.on_save_clicked)
        btn_quit.clicked.connect(self.close)

        main_layout.addWidget(btn_reset)
        main_layout.addWidget(btn_save)
        main_layout.addWidget(btn_quit)

    def update_pose_label(self):
        """Update real-time pose in GUI"""
        info = self.node.get_pose_info()
        self.label_pose.setText(f"<b>Pose:</b> X: {info['x']:.2f} | Y: {info['y']:.2f} | Theta: {info['theta']:.2f}")

    def on_reset_clicked(self):
        """Reset turtle pose to (5.44, 5.44) and increment session ID"""
        success = self.node.reset_pose(5.44, 5.44, 0.0)
        if success:
            self.current_id += 1
            self.label_session.setText(f"<b>Session ID:</b> {self.current_id}")

    def on_save_clicked(self):
        """Store current pose into memory buffer"""
        info = self.node.get_pose_info()
        data = (self.current_id, info['x'], info['y'], info['theta'])
        self.pose_buffer.append(data)
        self.label_buffer_count.setText(f"<b>Saved Records:</b> {len(self.pose_buffer)} count")

    def closeEvent(self, event):
        """Batch insert accumulated pose records into MySQL DB on window close"""
        if self.pose_buffer:
            success = self.db.insert_poses(self.pose_buffer)
            if success:
                QMessageBox.information(self, "Save Success", f"Total {len(self.pose_buffer)} records saved to DB.")
            else:
                QMessageBox.critical(self, "Save Failed", "Error occurred while saving to DB.")
        event.accept()