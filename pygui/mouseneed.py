import sys
import os
import json
import time
from typing import Dict

try:
    from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
    from PyQt6.QtGui import QColor
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
        QScrollArea, QFrame, QLineEdit, QDialog, QGraphicsDropShadowEffect,
        QCheckBox, QComboBox
    )
except Exception as e:
    print("PyQt6 required: pip install PyQt6")
    sys.exit(1)

import cv2
import numpy as np


class BorderedPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            BorderedPanel {
                background: #f5f7fa;
                border: 2px solid #d0dce8;
                border-radius: 8px;
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 60))
        self.setGraphicsEffect(shadow)


class GestureCardWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            GestureCardWidget {
                background: #ffffff;
                border: 1px solid #e0e6f0;
                border-radius: 6px;
            }
        """)


class DarkCameraPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            DarkCameraPanel {
                background: #0f1720;
                border: 2px solid #1a2332;
                border-radius: 8px;
                color: #cfcfcf;
            }
        """)


APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(APP_DIR, "gestures_config.json")
SETTINGS_PATH = os.path.join(APP_DIR, "settings.json")

GESTURE_NAMES = [
    "pointer", "2 fingers: Up", "2 fingers: Down", "Closed_Fist", "Open_Palm",
    "Pointing_Up", "Victory", "Thumbs_Down", "Thumbs_Up", "ILoveYou",
    "Thumb+Index", "Thumb+Middle", "Thumb+Ring", "Thumb+Pinky"
]

DEFAULT_GESTURES = {
    "Main": {gesture: "None" for gesture in GESTURE_NAMES},
    "Secondary": {gesture: "None" for gesture in GESTURE_NAMES}
}


def load_gestures() -> Dict:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    result = {}
                    for hand_data in data:
                        hand_name = hand_data.get("hand", "Main")
                        functions = hand_data.get("functions", [{}])[0]
                        result[hand_name] = functions
                    return result
                return data
        except Exception:
            pass
    return DEFAULT_GESTURES


def save_gestures(gestures: Dict):
    try:
        data = [
            {"hand": hand, "functions": [gestures.get(hand, {})]}
            for hand in ["Main", "Secondary"]
        ]
        with open(CONFIG_PATH, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def load_settings() -> Dict:
    defaults = {
        'sensitivity': 50,
        'show_fps': True,
        'show_grid': True,
        'enabled': True,
        'cursor_speed': 10,
        'default_cursor_speed': 10,
        'speed_boost_factor': 2,
        'main_hand': 'Left',
        'scroll_speed': 5,
        'default_scroll_speed': 5,
        'speed_boost_active': False,
        'camera_width_default': 1920,
        'camera_height_default': 1080,
        'camera_width_crop': 800,
        'camera_height_crop': 480,
        'camera_index': 0,
        'font_scale': 0.8,
        'thickness': 2,
        'debug_mode': False
    }
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return defaults


def save_settings(settings: Dict):
    try:
        with open(SETTINGS_PATH, 'w') as f:
            json.dump(settings, f, indent=2)
    except Exception:
        pass


class CameraThread(QThread):
    frame_ready = pyqtSignal(np.ndarray)
    error = pyqtSignal(str)

    def __init__(self, cam_index=0, parent=None):
        super().__init__(parent)
        self.cam_index = cam_index
        self.running = False
        self.cap = None

    def run(self):
        backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]
        for backend in backends:
            try:
                cap = cv2.VideoCapture(self.cam_index, backend)
                if cap and cap.isOpened():
                    self.cap = cap
                    break
            except:
                continue

        if not self.cap or not self.cap.isOpened():
            self.error.emit("Cannot open camera")
            return

        self.running = True
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                self.frame_ready.emit(frame)
            time.sleep(0.016)

        if self.cap:
            self.cap.release()

    def stop(self):
        self.running = False
        self.wait(1000)


class GestureCard(GestureCardWidget):
    edit_clicked = pyqtSignal(str)
    
    def __init__(self, gesture_name: str, function_name: str, parent=None):
        super().__init__(parent)
        self.gesture_name = gesture_name
        self.function_name = function_name
        self.setMinimumHeight(70)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        
        left_label = QLabel(gesture_name)
        left_label.setStyleSheet("font-weight: 600; color: #1a1a1a; font-size: 13px;")
        layout.addWidget(left_label)
        
        arrow = QLabel("→")
        arrow.setStyleSheet("color: #999; font-size: 16px;")
        layout.addWidget(arrow)
        
        func_label = QLabel(function_name if function_name != "None" else "Unassigned")
        func_label.setStyleSheet("color: #666; font-size: 12px;")
        func_label.setWordWrap(True)
        layout.addWidget(func_label, 1)
        
        edit_btn = QPushButton("Edit")
        edit_btn.setFixedSize(70, 32)
        edit_btn.setStyleSheet(
            "QPushButton { background-color: #007bff; color: white; border: none; "
            "border-radius: 4px; font-weight: 600; font-size: 12px; }"
            "QPushButton:hover { background-color: #0056b3; }"
        )
        edit_btn.clicked.connect(lambda: self.edit_clicked.emit(gesture_name))
        layout.addWidget(edit_btn)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MouseNoNeed")
        self.setMinimumSize(1200, 600)
        
        screen = QApplication.primaryScreen()
        screen_geom = screen.geometry()
        width = min(screen_geom.width() - 100, 1920)
        height = min(screen_geom.height() - 100, 1080)
        self.resize(int(width * 0.9), int(height * 0.9))
        
        self.setStyleSheet("QMainWindow { background: #ffffff; }")
        self.gestures = load_gestures()
        save_gestures(self.gestures)
        self.settings = load_settings()
        save_settings(self.settings)
        self.camera_thread = None
        self.setup_ui()

    def setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: #ffffff; }")
        
        central = QWidget()
        central.setStyleSheet("background: #ffffff;")
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        camera_panel = DarkCameraPanel()
        camera_panel.setMinimumSize(400, 300)
        camera_layout = QVBoxLayout(camera_panel)
        camera_layout.setContentsMargins(24, 24, 24, 24)
        camera_layout.setSpacing(12)

        camera_title = QLabel("Camera Placeholder")
        camera_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        camera_title.setStyleSheet("color: #cfcfcf; font-size: 18px; font-weight: 600; background: transparent; border: none;")
        camera_layout.addWidget(camera_title)

        camera_subtitle = QLabel("Click 'Start Camera' to enable")
        camera_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        camera_subtitle.setStyleSheet("color: #9ca3af; font-size: 12px; background: transparent; border: none;")
        camera_layout.addWidget(camera_subtitle)

        camera_layout.addStretch()

        start_cam_btn = QPushButton("Start Camera")
        start_cam_btn.setFixedHeight(44)
        start_cam_btn.setStyleSheet("""
            QPushButton {
                background: #2B8AF7;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 12px;
            }
            QPushButton:hover { background: #1e6fe0; }
            QPushButton:pressed { background: #1559c0; }
        """)
        start_cam_btn.clicked.connect(self.start_camera)
        camera_layout.addWidget(start_cam_btn)

        main_layout.addWidget(camera_panel, stretch=3)
        
        right_panel = QWidget()
        right_panel.setMinimumSize(300, 300)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)
        
        gestures_panel = BorderedPanel()
        gestures_layout = QVBoxLayout(gestures_panel)
        gestures_layout.setContentsMargins(12, 12, 12, 12)
        gestures_layout.setSpacing(8)
        
        title_layout = QHBoxLayout()
        gestures_title = QLabel("Gestures")
        gestures_title.setStyleSheet("font-weight: 600; font-size: 13px; color: #1a2332; background: transparent; border: none;")
        title_layout.addWidget(gestures_title)
        title_layout.addStretch()
        
        self.hand_main_btn = QPushButton("Main")
        self.hand_secondary_btn = QPushButton("Secondary")
        for btn in [self.hand_main_btn, self.hand_secondary_btn]:
            btn.setFixedSize(80, 28)
            btn.setStyleSheet("""
                QPushButton {
                    background: #e0e0e0;
                    border: 1px solid #d0d0d0;
                    border-radius: 4px;
                    font-size: 11px;
                    color: #666;
                }
                QPushButton:hover { background: #d0d0d0; }
            """)
        
        self.hand_main_btn.setStyleSheet("""
            QPushButton {
                background: #2B8AF7;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
            }
        """)
        self.current_hand = "Main"
        
        self.hand_main_btn.clicked.connect(lambda: self.switch_hand("Main"))
        self.hand_secondary_btn.clicked.connect(lambda: self.switch_hand("Secondary"))
        
        title_layout.addWidget(self.hand_main_btn)
        title_layout.addWidget(self.hand_secondary_btn)
        gestures_layout.addLayout(title_layout)

        self.gestures_scroll = QScrollArea()
        self.gestures_scroll.setWidgetResizable(True)
        self.gestures_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.gestures_container = QWidget()
        self.gestures_container.setStyleSheet("background: transparent;")
        self.gestures_v = QVBoxLayout(self.gestures_container)
        self.gestures_v.setContentsMargins(0, 0, 0, 0)
        self.gestures_v.setSpacing(8)
        self.refresh_gestures()
        self.gestures_scroll.setWidget(self.gestures_container)
        gestures_layout.addWidget(self.gestures_scroll)

        right_layout.addWidget(gestures_panel, stretch=1)
        
        settings_panel = BorderedPanel()
        settings_layout = QVBoxLayout(settings_panel)
        settings_layout.setContentsMargins(12, 12, 12, 12)
        settings_layout.setSpacing(8)
        
        settings_title = QLabel("Settings")
        settings_title.setStyleSheet("font-weight: 600; font-size: 13px; color: #1a2332; background: transparent; border: none;")
        settings_layout.addWidget(settings_title)
        
        self.settings_scroll = QScrollArea()
        self.settings_scroll.setWidgetResizable(True)
        self.settings_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.settings_container = QWidget()
        self.settings_container.setStyleSheet("background: transparent;")
        self.settings_v = QVBoxLayout(self.settings_container)
        self.settings_v.setContentsMargins(0, 0, 0, 0)
        self.settings_v.setSpacing(8)
        
        self.add_setting_field("cursor_speed", "Cursor Speed", 10)
        self.add_setting_field("default_cursor_speed", "Default Cursor Speed", 10)
        self.add_setting_field("speed_boost_factor", "Speed Boost Factor", 2)
        self.add_setting_dropdown("main_hand", "Main Hand", ["Left", "Right"], self.settings.get("main_hand", "Left"))
        
        self.add_setting_field("scroll_speed", "Scroll Speed", 5)
        self.add_setting_field("default_scroll_speed", "Default Scroll Speed", 5)
        self.add_setting_checkbox("speed_boost_active", "Speed Boost Active", self.settings.get("speed_boost_active", False))
        
        self.add_setting_field("camera_width_default", "Camera Width", 1920)
        self.add_setting_field("camera_height_default", "Camera Height", 1080)
        self.add_setting_field("camera_width_crop", "Width Crop", 800)
        self.add_setting_field("camera_height_crop", "Height Crop", 480)
        self.add_setting_field("camera_index", "Camera Index", 0)
        
        self.add_setting_field("font_scale", "Font Scale", 0.8)
        self.add_setting_field("thickness", "Thickness", 2)
        self.add_setting_checkbox("debug_mode", "Debug Mode", self.settings.get("debug_mode", False))

        self.settings_scroll.setWidget(self.settings_container)
        settings_layout.addWidget(self.settings_scroll)
        right_layout.addWidget(settings_panel, stretch=1)

        main_layout.addWidget(right_panel, stretch=2)

        status = QLabel("Camera: Disconnected | FPS: -")
        status.setStyleSheet("font-size: 10px; color: #666; background: transparent; border: none;")
        status_layout = QVBoxLayout()
        status_layout.addStretch()
        status_layout.addWidget(status)
        main_layout.addLayout(status_layout)

        central.setLayout(main_layout)
        scroll.setWidget(central)
        self.setCentralWidget(scroll)

    def switch_hand(self, hand: str):
        self.current_hand = hand
        
        if hand == "Main":
            self.hand_main_btn.setStyleSheet("""
                QPushButton {
                    background: #2B8AF7;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 11px;
                }
            """)
            self.hand_secondary_btn.setStyleSheet("""
                QPushButton {
                    background: #e0e0e0;
                    border: 1px solid #d0d0d0;
                    border-radius: 4px;
                    font-size: 11px;
                    color: #666;
                }
                QPushButton:hover { background: #d0d0d0; }
            """)
        else:
            self.hand_secondary_btn.setStyleSheet("""
                QPushButton {
                    background: #2B8AF7;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 11px;
                }
            """)
            self.hand_main_btn.setStyleSheet("""
                QPushButton {
                    background: #e0e0e0;
                    border: 1px solid #d0d0d0;
                    border-radius: 4px;
                    font-size: 11px;
                    color: #666;
                }
                QPushButton:hover { background: #d0d0d0; }
            """)
        
        self.refresh_gestures()

    def refresh_gestures(self):
        while self.gestures_v.count() > 0:
            widget = self.gestures_v.takeAt(0)
            if widget.widget():
                widget.widget().deleteLater()

        hand_gestures = self.gestures.get(self.current_hand, {})
        
        if not hand_gestures:
            empty = QLabel("No gestures configured.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet("color: #999; background: transparent; border: none; font-size: 11px;")
            self.gestures_v.addWidget(empty)
        else:
            for gesture_name, function_name in hand_gestures.items():
                card = GestureCard(gesture_name, function_name)
                card.edit_clicked.connect(self.edit_gesture_function)
                self.gestures_v.addWidget(card)

        self.gestures_v.addStretch()

    def edit_gesture_function(self, gesture_name: str):
        current_hand = self.current_hand
        current_function = self.gestures[current_hand].get(gesture_name, "None")
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit {gesture_name}")
        dialog.setFixedSize(350, 200)
        layout = QVBoxLayout(dialog)

        label = QLabel(f"Select function for '{gesture_name}':")
        label.setStyleSheet("background: transparent; border: none; font-weight: 500;")
        layout.addWidget(label)
        
        functions = [
            "None", "click_func", "double_click", "right_click",
            "apply_boost", "voice_assistant", "osk",
            "volume_up", "volume_down", "play_pause",
            "update_scrolling(1)", "update_scrolling(-1)"
        ]
        
        combo = QComboBox()
        combo.addItems(functions)
        combo.setCurrentText(current_function if current_function in functions else "None")
        combo.setStyleSheet("""
            QComboBox {
                background: #f0f4f8;
                border: 1px solid #d0dce8;
                border-radius: 4px;
                padding: 6px;
                font-size: 11px;
            }
        """)
        layout.addWidget(combo)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.setStyleSheet("background: #2B8AF7; color: white; border: none; border-radius: 4px; padding: 6px 12px;")
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background: #f0f0f0; border: none; border-radius: 4px; padding: 6px 12px;")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_function = combo.currentText()
            self.gestures[current_hand][gesture_name] = new_function
            save_gestures(self.gestures)
            self.refresh_gestures()

    def start_camera(self):
        if not self.camera_thread:
            self.camera_thread = CameraThread()
            self.camera_thread.start()

    def add_setting_field(self, key, label, default_value):
        field_layout = QHBoxLayout()
        field_label = QLabel(label)
        field_label.setStyleSheet("font-size: 10px; font-weight: 500; color: #1a2332; background: transparent; border: none;")
        field_label.setFixedWidth(120)
        
        field_input = QLineEdit()
        field_input.setText(str(self.settings.get(key, default_value)))
        field_input.setFixedHeight(24)
        field_input.setStyleSheet("""
            QLineEdit {
                background: #f0f4f8;
                border: none;
                border-radius: 4px;
                padding: 4px 6px;
                font-size: 10px;
            }
        """)
        field_input.editingFinished.connect(lambda: self.update_setting(key, field_input.text()))
        
        field_layout.addWidget(field_label)
        field_layout.addWidget(field_input)
        field_layout.addStretch()
        self.settings_v.addLayout(field_layout)

    def add_setting_checkbox(self, key, label, default_value):
        check = QCheckBox(label)
        check.setChecked(bool(self.settings.get(key, default_value)))
        check.setStyleSheet("QCheckBox { background: transparent; border: none; font-size: 10px; }")
        check.stateChanged.connect(lambda: self.update_setting(key, check.isChecked()))
        self.settings_v.addWidget(check)

    def add_setting_dropdown(self, key, label, options, default_value):
        field_layout = QHBoxLayout()
        field_label = QLabel(label)
        field_label.setStyleSheet("font-size: 10px; font-weight: 500; color: #1a2332; background: transparent; border: none;")
        field_label.setFixedWidth(120)
        
        combo = QComboBox()
        combo.addItems(options)
        combo.setCurrentText(str(default_value))
        combo.setFixedHeight(24)
        combo.setStyleSheet("""
            QComboBox {
                background: #f0f4f8;
                border: none;
                border-radius: 4px;
                padding: 4px;
                font-size: 10px;
            }
            QComboBox::drop-down { border: none; }
        """)
        combo.currentTextChanged.connect(lambda text: self.update_setting(key, text))
        
        field_layout.addWidget(field_label)
        field_layout.addWidget(combo)
        field_layout.addStretch()
        self.settings_v.addLayout(field_layout)

    def update_setting(self, key, value):
        self.settings[key] = value
        save_settings(self.settings)

    def closeEvent(self, event):
        if self.camera_thread:
            self.camera_thread.stop()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
