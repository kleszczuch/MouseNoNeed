import sys
import os
import json
import time
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_tasks_python
from mediapipe.tasks.python import vision as mp_tasks_vision
from typing import Dict
import platform

if platform.system() == "Windows":
    import winreg

try:
    from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
    from PyQt6.QtGui import QColor, QImage, QPixmap, QPalette
    from PyQt6.QtMultimedia import QMediaDevices
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
        QScrollArea, QFrame, QLineEdit, QDialog, QGraphicsDropShadowEffect,
        QCheckBox, QComboBox, QMessageBox
    )
except ImportError:
    print("PyQt6 required: pip install PyQt6")
    sys.exit(1)

from configuration.configuration import cfg
from function_library.trigerable_functions import record_key_press
from camera_library.hand_croper import HandCropper
from hand_recognition.hand_processing import process_hands
import configuration.function_assigne.function_configuration as func_config
from camera_library.recognition_main_loop import create_gesture_recognizer, to_mp_image
from camera_library.camera_display import create_camera_capture

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(APP_DIR, "configuration", "configuration.json")
FUNC_FILE = os.path.join(APP_DIR, "configuration", "function_assigne", "function_assigne.json")
MODEL_PATH = os.path.join(APP_DIR, cfg.MODEL_FILENAME)

def detect_system_theme():
    system = platform.system()
    
    if system == "Windows":
        try:
            registry_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path)
            value, regtype = winreg.QueryValueEx(registry_key, "AppsUseLightTheme")
            winreg.CloseKey(registry_key)
            return "light" if value == 1 else "dark"
        except Exception:
            return "dark"
    
    elif system == "Darwin":
        try:
            import subprocess
            result = subprocess.run(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0 and "Dark" in result.stdout:
                return "dark"
            else:
                return "light"
        except Exception:
            return "dark"
    
    else:
        return "dark"

SYSTEM_THEME = detect_system_theme()
IS_DARK_MODE = SYSTEM_THEME == "dark"

THEMES = {
    "dark": {
        "bg_primary": "#1e1e1e",
        "bg_secondary": "#2b2b2b",
        "border": "#444444",
        "border_light": "#555555",
        "text_primary": "#ffffff",
        "text_secondary": "#cccccc",
        "text_placeholder": "#999999",
        "input_bg": "#333333",
        "input_border": "#555555",
        "button_bg": "#007bff",
        "button_hover": "#0056b3",
        "button_bg_success": "#28a745",
        "button_bg_danger": "#dc3545",
        "camera_bg": "#0f1720", 
        "camera_border": "#1a2332",
    },
    "light": {
        "bg_primary": "#ffffff",
        "bg_secondary": "#f5f7fa",
        "border": "#d0dce8",
        "border_light": "#e0e6f0",
        "text_primary": "#1a1a1a",
        "text_secondary": "#666666",
        "text_placeholder": "#999999",
        "input_bg": "#f0f4f8",
        "input_border": "#d0dce8",
        "button_bg": "#007bff",
        "button_hover": "#0056b3",
        "button_bg_success": "#28a745",
        "button_bg_danger": "#dc3545",
        "camera_bg": "#f5f7fa",
        "camera_border": "#d0dce8",
    }
}

THEME = THEMES[SYSTEM_THEME]

if platform.system() == "Darwin" and IS_DARK_MODE:
    THEME["bg_primary"] = "#2a2a2a"
    THEME["bg_secondary"] = "#3a3a3a"
    THEME["border_light"] = "#4a4a4a"
    THEME["camera_bg"] = "#1a1a1a"
    THEME["camera_border"] = "#2a2a2a"
    THEME["text_secondary"] = "#d0d0d0"

GESTURE_NAMES = [
    "pointer", "2 fingers: Up", "2 fingers: Down", "Closed_Fist", "Open_Palm",
    "Pointing_Up", "Victory", "Thumb_Down", "Thumb_Up", "ILoveYou",
    "Thumb+Index", "Thumb+Middle", "Thumb+Ring", "Thumb+Pinky"
]

class BorderedPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            BorderedPanel {{
                background: {THEME['bg_secondary']};
                border: 2px solid {THEME['border_light']};
                border-radius: 8px;
                color: {THEME['text_primary']};
            }}
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 60))
        self.setGraphicsEffect(shadow)


class DarkCameraPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            DarkCameraPanel {{
                background: {THEME['camera_bg']};
                border: 2px solid {THEME['camera_border']};
                border-radius: 8px;
                color: {THEME['text_primary']};
            }}
        """)


class CameraThread(QThread):
    frame_ready = pyqtSignal(QImage)
    error = pyqtSignal(str)

    def __init__(self, cam_index=0, parent=None):
        super().__init__(parent)
        self.cam_index = cam_index
        self.running = False

    def run(self):
        recognizer = create_gesture_recognizer()
        if not recognizer:
            self.error.emit("Failed to init recognizer")
            return

        cap = create_camera_capture()
        if not cap or not cap.isOpened():
            self.error.emit(f"Cannot open camera {self.cam_index}")
            return

        cropper = HandCropper(
            output_width=min(cfg.camera_width_crop, cfg.camera_width_default),
            output_height=min(cfg.camera_height_crop, cfg.camera_height_default),
            smoothing_factor=0.1,
        )

        self.running = True
        while self.running:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue

            try:
                mp_image = to_mp_image(frame)
                timestamp_ms = int(time.time() * 1000)
                recognition_result = recognizer.recognize_for_video(mp_image, timestamp_ms)
                
                frame = process_hands(frame, recognition_result)

                hand_landmarks_list = (
                    recognition_result.hand_landmarks
                    if recognition_result and recognition_result.hand_landmarks
                    else None
                )
                cropped_frame = cropper.crop(frame, hand_landmarks_list)
                
                h, w, ch = cropped_frame.shape
                bytes_per_line = ch * w
                rgb_frame = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2RGB)
                qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                
                self.frame_ready.emit(qt_image.copy())

            except Exception as e:
                print(f"Error in camera loop: {e}")
                
        cap.release()

    def stop(self):
        self.running = False
        self.wait(1000)


class GestureCard(QFrame):
    edit_clicked = pyqtSignal(str)
    
    def __init__(self, gesture_name: str, function_name: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            GestureCard {{
                background: {THEME['bg_primary']};
                border: 1px solid {THEME['border_light']};
                border-radius: 6px;
            }}
        """)
        self.setMinimumHeight(60)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        
        left_label = QLabel(gesture_name)
        left_label.setStyleSheet(f"font-weight: 600; color: {THEME['text_primary']};")
        layout.addWidget(left_label)
        
        layout.addStretch()
        
        func_label = QLabel(function_name if function_name and function_name != "None" else "Unassigned")
        func_label.setStyleSheet(f"color: {THEME['text_secondary']};")
        layout.addWidget(func_label)
        
        edit_btn = QPushButton("Edit")
        edit_btn.setFixedSize(60, 28)
        edit_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {THEME['button_bg']}; color: white; border-radius: 4px; }}
            QPushButton:hover {{ background-color: {THEME['button_hover']}; }}
        """)
        edit_btn.clicked.connect(lambda: self.edit_clicked.emit(gesture_name))
        layout.addWidget(edit_btn)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MouseNoNeed Config & Cam")
        self.resize(1100, 700)
        
        self.gestures_data = self.load_gestures()
        self.settings_data = self.load_settings()
        
        self.camera_thread = None
        self.current_hand = "Main"
        self.help_dialog = None
        
        self.setup_ui()
    
    def show_help(self):
        if self.help_dialog is None:
            self.help_dialog = QDialog(self)
            self.help_dialog.setWindowTitle("MouseNoNeed - Help & Guide")
            self.help_dialog.setGeometry(100, 100, 700, 700)
            
            layout = QVBoxLayout(self.help_dialog)
            
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            
            content_label = QLabel()
            content_label.setWordWrap(True)
            content_label.setAlignment(Qt.AlignmentFlag.AlignTop)
            content_label.setStyleSheet(f"""
                color: {THEME['text_primary']};
                padding: 15px;
                line-height: 1.6;
            """)
            
            readme_path = os.path.join(APP_DIR, "README.md")
            readme_content = "No README found"
            
            if os.path.exists(readme_path):
                try:
                    with open(readme_path, 'r', encoding='utf-8') as f:
                        readme_content = f.read()
                        readme_content = self.markdown_to_html(readme_content)
                except Exception as e:
                    readme_content = f"Error reading README: {str(e)}"
            
            content_label.setText(readme_content)
            scroll.setWidget(content_label)
            
            scroll.setStyleSheet(f"""
                QScrollArea {{
                    background: {THEME['bg_secondary']};
                    border: 1px solid {THEME['border_light']};
                    border-radius: 4px;
                }}
                QScrollBar {{
                    width: 8px;
                }}
                QScrollBar::handle {{
                    background: {THEME['border_light']};
                    border-radius: 4px;
                }}
            """)
            
            layout.addWidget(scroll, 1)
            
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(self.help_dialog.close)
            close_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {THEME['button_bg']};
                    color: white;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background: {THEME['button_hover']};
                }}
            """)
            layout.addWidget(close_btn)
            
            self.help_dialog.setStyleSheet(f"""
                QDialog {{
                    background: {THEME['bg_primary']};
                }}
            """)
        
        self.help_dialog.show()
        self.help_dialog.raise_()
        self.help_dialog.activateWindow()
    
    def markdown_to_html(self, markdown_text):
        lines = markdown_text.split('\n')
        html_lines = []
        
        for line in lines:
            if line.startswith('# '):
                html_lines.append(f"<h1>{line[2:]}</h1>")
            elif line.startswith('## '):
                html_lines.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith('### '):
                html_lines.append(f"<h3>{line[4:]}</h3>")
            elif '**' in line:
                line = line.replace('**', '<b>', 1).replace('**', '</b>', 1)
                html_lines.append(f"<p>{line}</p>")
            elif line.startswith('- '):
                html_lines.append(f"<li>{line[2:]}</li>")
            elif line.startswith('```'):
                continue
            elif not line.strip():
                html_lines.append("<br>")
            else:
                if line.strip():
                    html_lines.append(f"<p>{line}</p>")
        
        return ''.join(html_lines)

    def get_cameras(self):
        try:
            cameras = QMediaDevices.videoInputs()
            return [(i, cam.description()) for i, cam in enumerate(cameras)]
        except Exception as e:
            print(f"Error getting cameras: {e}")
            return [(i, f"Camera {i}") for i in range(5)]

    def load_gestures(self):
        if os.path.exists(FUNC_FILE):
            try:
                with open(FUNC_FILE, 'r') as f:
                    data = json.load(f)
                    res = {}
                    for item in data:
                        h = item.get("hand")
                        funcs = item.get("functions", [{}])[0]
                        res[h] = funcs
                    return res
            except Exception as e:
                print(f"Error loading gestures: {e}")
        return {"Main": {}, "Secondary": {}}

    def save_gestures(self):
        data = []
        for hand in ["Main", "Secondary"]:
            funcs = self.gestures_data.get(hand, {})
            data.append({"hand": hand, "functions": [funcs]})
        
        try:
            with open(FUNC_FILE, 'w') as f:
                json.dump(data, f, indent=4)
            func_config.assignments = func_config.load_func_assignments()
            print("Gestures saved & reloaded.")
        except Exception as e:
            print(f"Error saving gestures: {e}")

    def load_settings(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading settings: {e}")
        return {}

    def save_settings(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.settings_data, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def setup_ui(self):
        central = QWidget()
        main_layout = QHBoxLayout(central)
        
        cam_container = DarkCameraPanel()
        cam_layout = QVBoxLayout(cam_container)
        cam_layout.setContentsMargins(0, 0, 0, 0)
        cam_layout.setSpacing(0)
        
        # Camera header with help button
        cam_header = QWidget()
        cam_header_layout = QHBoxLayout(cam_header)
        cam_header_layout.setContentsMargins(12, 12, 12, 0)
        
        # Help button (circular/oval style)
        self.help_btn = QPushButton("?")
        self.help_btn.setMaximumSize(40, 40)
        self.help_btn.setMinimumSize(40, 40)
        self.help_btn.clicked.connect(self.show_help)
        self.help_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME['button_bg']};
                color: white;
                border: none;
                border-radius: 20px;
                font-size: 18px;
                font-weight: 700;
                padding: 0px;
            }}
            QPushButton:hover {{
                background: {THEME['button_hover']};
            }}
            QPushButton:pressed {{
                background: #004085;
            }}
        """)
        cam_header_layout.addWidget(self.help_btn, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        cam_header_layout.addStretch()
        
        cam_layout.addWidget(cam_header)
        
        self.cam_label = QLabel("Camera Output")
        self.cam_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cam_label.setStyleSheet(f"color: {THEME['text_primary']};")
        self.cam_label.setMinimumSize(640, 480)
        
        cam_layout.addWidget(self.cam_label, 1)
        
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Camera")
        self.start_btn.clicked.connect(self.toggle_camera)
        self.start_btn.setStyleSheet(f"background: {THEME['button_bg_success']}; color: white; padding: 8px; border-radius: 4px;")
        
        btn_layout.addWidget(self.start_btn)
        cam_layout.addLayout(btn_layout)
        
        main_layout.addWidget(cam_container, 2)
        
        # Right side container with equal-sized panels
        right_container = QWidget()
        right_main_layout = QVBoxLayout(right_container)
        right_main_layout.setContentsMargins(0, 0, 0, 0)
        right_main_layout.setSpacing(8)
        
        # GESTURES PANEL with internal scroll
        gest_panel = BorderedPanel()
        gest_layout = QVBoxLayout(gest_panel)
        gest_layout.setContentsMargins(12, 12, 12, 12)
        
        h_layout = QHBoxLayout()
        title_label = QLabel("<b>Gestures</b>")
        title_label.setStyleSheet(f"color: {THEME['text_primary']};")
        h_layout.addWidget(title_label)
        self.hand_btn = QPushButton(self.current_hand)
        self.hand_btn.clicked.connect(self.switch_hand)
        h_layout.addWidget(self.hand_btn)
        gest_layout.addLayout(h_layout)
        
        # Scroll area for gestures content
        gest_scroll = QScrollArea()
        gest_scroll.setWidgetResizable(True)
        gest_scroll.setStyleSheet(f"""
            QScrollArea {{ background: {THEME['bg_secondary']}; border: none; }}
            QScrollBar {{ width: 8px; }}
            QScrollBar::handle {{ background: {THEME['border_light']}; border-radius: 4px; }}
        """)
        
        gest_scroll_widget = QWidget()
        self.gestures_list_layout = QVBoxLayout(gest_scroll_widget)
        self.gestures_list_layout.setContentsMargins(0, 0, 0, 0)
        self.refresh_gestures_list()
        self.gestures_list_layout.addStretch()
        
        gest_scroll.setWidget(gest_scroll_widget)
        gest_layout.addWidget(gest_scroll, 1)
        
        right_main_layout.addWidget(gest_panel, 1)
        
        # SETTINGS PANEL with internal scroll
        sett_panel = BorderedPanel()
        sett_layout = QVBoxLayout(sett_panel)
        sett_layout.setContentsMargins(12, 12, 12, 12)
        
        settings_label = QLabel("<b>Settings</b>")
        settings_label.setStyleSheet(f"color: {THEME['text_primary']};")
        sett_layout.addWidget(settings_label)
        
        # Scroll area for settings content
        sett_scroll = QScrollArea()
        sett_scroll.setWidgetResizable(True)
        sett_scroll.setStyleSheet(f"""
            QScrollArea {{ background: {THEME['bg_secondary']}; border: none; }}
            QScrollBar {{ width: 8px; }}
            QScrollBar::handle {{ background: {THEME['border_light']}; border-radius: 4px; }}
        """)
        
        sett_scroll_widget = QWidget()
        sett_content_layout = QVBoxLayout(sett_scroll_widget)
        sett_content_layout.setContentsMargins(0, 0, 0, 0)
        
        self.add_setting_row(sett_content_layout, "Cursor Speed", "cursor_speed")
        self.add_setting_row(sett_content_layout, "Scroll Speed", "scroll_speed")
        self.add_setting_row(sett_content_layout, "Boost Factor", "speed_boost_factor")
        self.add_camera_selection_row(sett_content_layout, "Camera Source", "camera_index")
        self.add_setting_row(sett_content_layout, "Cam Width (Crop)", "camera_width_crop")
        self.add_setting_row(sett_content_layout, "Cam Height (Crop)", "camera_height_crop")
        self.add_setting_combo(sett_content_layout, "Main Hand", "main_hand", ["Left", "Right"])
        self.add_setting_bool(sett_content_layout, "Debug Mode", "debug_mode")
        
        sett_content_layout.addStretch()
        
        sett_scroll.setWidget(sett_scroll_widget)
        sett_layout.addWidget(sett_scroll, 1)
        
        # Add Save Settings button (stays at bottom of settings panel)
        save_btn_layout = QHBoxLayout()
        save_btn_layout.addStretch()
        save_btn = QPushButton("Save Settings")
        save_btn.setStyleSheet(f"background: {THEME['button_bg_success']}; color: white; padding: 8px 16px; border-radius: 4px; font-weight: 600;")
        save_btn.clicked.connect(self.save_settings)
        save_btn_layout.addWidget(save_btn)
        sett_layout.addLayout(save_btn_layout)
        
        right_main_layout.addWidget(sett_panel, 1)
        
        main_layout.addWidget(right_container, 1)
        
        self.setCentralWidget(central)

    def toggle_camera(self):
        if self.camera_thread and self.camera_thread.isRunning():
            self.camera_thread.stop()
            self.start_btn.setText("Start Camera")
            self.start_btn.setStyleSheet(f"background: {THEME['button_bg_success']}; color: white; padding: 8px; border-radius: 4px;")
        else:
            idx = self.settings_data.get("camera_index", 0)
            self.camera_thread = CameraThread(cam_index=idx)
            self.camera_thread.frame_ready.connect(self.update_frame)
            self.camera_thread.error.connect(lambda e: print(e))
            self.camera_thread.start()
            self.start_btn.setText("Stop Camera")
            self.start_btn.setStyleSheet(f"background: {THEME['button_bg_danger']}; color: white; padding: 8px; border-radius: 4px;")

    def update_frame(self, q_img):
        self.cam_label.setPixmap(QPixmap.fromImage(q_img).scaled(
            self.cam_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        ))

    def switch_hand(self):
        self.current_hand = "Secondary" if self.current_hand == "Main" else "Main"
        self.hand_btn.setText(self.current_hand)
        self.refresh_gestures_list()

    def refresh_gestures_list(self):
        while self.gestures_list_layout.count():
            item = self.gestures_list_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        funcs = self.gestures_data.get(self.current_hand, {})
        for name in GESTURE_NAMES:
            assigned = funcs.get(name, "None")
            card = GestureCard(name, assigned)
            card.edit_clicked.connect(self.edit_gesture)
            self.gestures_list_layout.addWidget(card)

    def edit_gesture(self, gesture_name):
        current_val = self.gestures_data.get(self.current_hand, {}).get(gesture_name, "None")
        
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Edit {gesture_name}")
        l = QVBoxLayout(dlg)
        
        combo = QComboBox()
        options = ["None", "click_func", "right_click_func", "apply_boost", "volume_up", "volume_down", "toggle_mute", 
                   "voice_assistant", "osk", "update_scrolling up", "update_scrolling down", "next_song", "previous_song", 
                   "play_pause_music", "double_click_func", "minimize_window", "maximize_window", "custom_hotkey"]
        combo.addItems(options)
        combo.setCurrentText(current_val if current_val in options else "None")
        l.addWidget(combo)
        
        btns = QHBoxLayout()
        ok = QPushButton("OK")
        ok.clicked.connect(dlg.accept)
        btns.addWidget(ok)
        l.addLayout(btns)
        
        if dlg.exec():
            new_val = combo.currentText()

            if new_val == "custom_hotkey":
                QMessageBox.information(self, "Custom Hotkey", "Click OK, then press the key you want to bind.")
                QApplication.processEvents()
                
                detected_key = record_key_press()
                
                if detected_key:
                    hotkey_name = detected_key
      
                    if "custom_hotkeys" not in self.settings_data:
                        self.settings_data["custom_hotkeys"] = {}
                    self.settings_data["custom_hotkeys"][hotkey_name] = detected_key
                    self.save_settings()

                    if hasattr(cfg, "custom_hotkeys"):
                        cfg.custom_hotkeys[hotkey_name] = detected_key
                        
                    new_val = f"custom_hotkey:{hotkey_name}"
                    QMessageBox.information(self, "Success", f"Custom hotkey '{hotkey_name}' saved.")
                else:
                    QMessageBox.warning(self, "Timeout", "No key press detected.")
                    return

            if self.current_hand not in self.gestures_data:
                self.gestures_data[self.current_hand] = {}
            self.gestures_data[self.current_hand][gesture_name] = new_val
            self.save_gestures()
            self.refresh_gestures_list()

    def add_setting_row(self, parent_layout, label_text, key):
        row = QHBoxLayout()
        lbl = QLabel(label_text)
        lbl.setStyleSheet(f"color: {THEME['text_primary']};")
        row.addWidget(lbl)
        val = self.settings_data.get(key, "")
        inp = QLineEdit(str(val))
        inp.setStyleSheet(f"background: {THEME['input_bg']}; color: {THEME['text_primary']}; border: 1px solid {THEME['input_border']}; border-radius: 3px; padding: 3px;")
        inp.editingFinished.connect(lambda: self.update_setting(key, inp.text()))
        row.addWidget(inp)
        parent_layout.addLayout(row)

    def add_setting_bool(self, parent_layout, label_text, key):
        chk = QCheckBox(label_text)
        chk.setStyleSheet(f"color: {THEME['text_primary']};")
        chk.setChecked(bool(self.settings_data.get(key, False)))
        chk.clicked.connect(lambda: self.update_setting(key, chk.isChecked()))
        parent_layout.addWidget(chk)

    def add_setting_combo(self, parent_layout, label_text, key, options):
        row = QHBoxLayout()
        lbl = QLabel(label_text)
        lbl.setStyleSheet(f"color: {THEME['text_primary']};")
        row.addWidget(lbl)
        combo = QComboBox()
        combo.addItems(options)
        combo.setCurrentText(str(self.settings_data.get(key, options[0])))
        combo.setStyleSheet(f"background: {THEME['input_bg']}; color: {THEME['text_primary']}; border: 1px solid {THEME['input_border']}; border-radius: 3px; padding: 3px;")
        combo.currentTextChanged.connect(lambda: self.update_setting(key, combo.currentText()))
        row.addWidget(combo)
        parent_layout.addLayout(row)

    def add_camera_selection_row(self, parent_layout, label_text, key):
        row = QHBoxLayout()
        lbl = QLabel(label_text)
        lbl.setStyleSheet(f"color: {THEME['text_primary']};")
        row.addWidget(lbl)
        
        cameras = self.get_cameras()
        if not cameras:
            cameras = [(0, "Default Camera")]
            
        combo = QComboBox()
        for i, name in cameras:
            combo.addItem(name, i) 
            
        current_idx = self.settings_data.get(key, 0)
        found = False
        for i in range(combo.count()):
            if combo.itemData(i) == current_idx:
                combo.setCurrentIndex(i)
                found = True
                break
        if not found and combo.count() > 0:
             combo.setCurrentIndex(0)

        combo.setStyleSheet(f"background: {THEME['input_bg']}; color: {THEME['text_primary']}; border: 1px solid {THEME['input_border']}; border-radius: 3px; padding: 3px;")
        
        def on_change(idx):
             cam_id = combo.itemData(idx)
             self.update_setting(key, cam_id)
             
        combo.currentIndexChanged.connect(on_change)
        
        row.addWidget(combo)
        parent_layout.addLayout(row)

    def update_setting(self, key, value):
            current_val = self.settings_data.get(key)
            if isinstance(current_val, bool):
                value = bool(value)
            elif isinstance(current_val, int):
                try: value = int(value)
                except: pass
            elif isinstance(current_val, float):
                try: value = float(value)
                except: pass
                
            self.settings_data[key] = value
            self.save_settings()
            
            if hasattr(cfg, key):
                setattr(cfg, key, value)

    def closeEvent(self, event):
        if self.camera_thread:
            self.camera_thread.stop()
        event.accept()


def runAPP():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


