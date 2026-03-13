import sys
import json
import os
import ctypes
from ctypes import wintypes
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLineEdit, QPushButton, QComboBox,
                             QLabel, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal

try:
    from ui_settings import SettingsDialog
except ImportError:
    SettingsDialog = None
    print("Warning: ui_settings.py not found. Settings dialog will not open.")


class ScrcpyMainUI(QMainWindow):
    settings_saved = pyqtSignal()
    language_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.config_file = "config.json"

        self.is_dark_mode = False
        self.language = "EN"
        self.audio_enabled = False
        self.keyboard_uhid = True
        self.controller = False
        self.stay_awake = False
        self.program_logs = False
        self.hide_borders = False
        self.show_touches = False
        self.fullscreen = False
        self.always_on_top = False
        self.read_only = False
        self.turn_screen_off = False
        self.nav_bar_enabled = True
        self.perf_overlay = False
        self.nav_bar_position = "right"
        self.max_fps = ""
        self.boss_key = ""
        self.boss_key_mods = 0
        self.boss_key_vk = 0
        self.custom_scrcpy_path = "scrcpy"
        self.device_quality_map = {}

        self.default_quality = {"name": "Default Compatibility Mode", "codec": "h264", "resolution": "720",
                                "bitrate": "8M", "fps": "30"}
        self.quality_options = [
            self.default_quality,
            {"name": "HD mode: H264 1080P", "codec": "h264", "resolution": "1080", "bitrate": "16M", "fps": ""},
            {"name": "HD mode: H265 1080P", "codec": "h265", "resolution": "1080", "bitrate": "16M", "fps": ""},
            {"name": "HD mode: AV1 1080P", "codec": "av1", "resolution": "1080", "bitrate": "16M", "fps": ""}
        ]

        self.load_settings()

        self.texts = {
            "EN": {
                "window_title": "Pqscrcpy",
                "btn_theme": "🌗 Dark/Light Mode",
                "btn_lang": "🌐 English / 中文",
                "btn_settings": "⚙ Settings",
                "ip_placeholder": "Optional: Enter IP for Wi-Fi (e.g., 192.168.1.5)",
                "btn_connect": "▶ Start Mirroring",
                "lbl_quality": "Quality:",
                "btn_switch_wireless": "Switch to Wi-Fi",
                "no_devices": "No devices detected"
            },
            "ZH": {
                "window_title": "Pqscrcpy",
                "btn_theme": "🌗 深色/浅色模式",
                "btn_lang": "🌐 English / 中文",
                "btn_settings": "⚙ 设置",
                "ip_placeholder": "可选：输入设备IP进行无线连接",
                "btn_connect": "▶ 开始投屏",
                "lbl_quality": "画质选择:",
                "btn_switch_wireless": "切换至无线模式",
                "no_devices": "未检测到设备"
            }
        }

        self.init_ui()
        self.apply_theme()
        self.update_language()
        self.resize(600, 500)

    def load_settings(self):
        if not os.path.exists(self.config_file):
            self.save_settings()
            return

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.is_dark_mode = config.get("is_dark_mode", self.is_dark_mode)
                self.language = config.get("language", self.language)

                loaded_options = config.get("quality_options", self.quality_options)
                if loaded_options and "codec" in loaded_options[0]:
                    self.quality_options = loaded_options

                self.audio_enabled = config.get("audio_enabled", self.audio_enabled)
                self.keyboard_uhid = config.get("keyboard_uhid", self.keyboard_uhid)
                self.controller = config.get("controller", self.controller)
                self.stay_awake = config.get("stay_awake", self.stay_awake)
                self.program_logs = config.get("program_logs", self.program_logs)
                self.hide_borders = config.get("hide_borders", self.hide_borders)
                self.show_touches = config.get("show_touches", self.show_touches)
                self.fullscreen = config.get("fullscreen", self.fullscreen)
                self.always_on_top = config.get("always_on_top", self.always_on_top)
                self.read_only = config.get("read_only", self.read_only)
                self.turn_screen_off = config.get("turn_screen_off", self.turn_screen_off)
                self.nav_bar_enabled = config.get("nav_bar_enabled", self.nav_bar_enabled)
                self.perf_overlay = config.get("perf_overlay", self.perf_overlay)
                self.nav_bar_position = config.get("nav_bar_position", self.nav_bar_position)
                self.max_fps = config.get("max_fps", self.max_fps)
                self.boss_key = config.get("boss_key", self.boss_key)
                self.boss_key_mods = config.get("boss_key_mods", self.boss_key_mods)
                self.boss_key_vk = config.get("boss_key_vk", self.boss_key_vk)
                self.custom_scrcpy_path = config.get("CustomScrcpyPath", self.custom_scrcpy_path)
                self.device_quality_map = config.get("device_quality_map", self.device_quality_map)
        except Exception as e:
            print(f"Error loading config: {e}")

    def save_settings(self):
        config = {
            "is_dark_mode": self.is_dark_mode,
            "language": self.language,
            "quality_options": self.quality_options,
            "audio_enabled": self.audio_enabled,
            "keyboard_uhid": self.keyboard_uhid,
            "controller": self.controller,
            "stay_awake": self.stay_awake,
            "program_logs": self.program_logs,
            "hide_borders": self.hide_borders,
            "show_touches": self.show_touches,
            "fullscreen": self.fullscreen,
            "always_on_top": self.always_on_top,
            "read_only": self.read_only,
            "turn_screen_off": self.turn_screen_off,
            "nav_bar_enabled": self.nav_bar_enabled,
            "perf_overlay": self.perf_overlay,
            "nav_bar_position": self.nav_bar_position,
            "max_fps": self.max_fps,
            "boss_key": self.boss_key,
            "boss_key_mods": self.boss_key_mods,
            "boss_key_vk": self.boss_key_vk,
            "CustomScrcpyPath": self.custom_scrcpy_path,
            "device_quality_map": self.device_quality_map
        }
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        top_bar = QHBoxLayout()
        self.btn_theme = QPushButton()
        self.btn_theme.setCursor(Qt.PointingHandCursor)
        self.btn_theme.setFixedSize(170, 42)
        self.btn_theme.clicked.connect(self.toggle_theme)

        self.btn_lang = QPushButton()
        self.btn_lang.setCursor(Qt.PointingHandCursor)
        self.btn_lang.setFixedSize(170, 42)
        self.btn_lang.clicked.connect(self.toggle_language)

        self.btn_settings = QPushButton()
        self.btn_settings.setCursor(Qt.PointingHandCursor)
        self.btn_settings.setFixedSize(170, 42)
        self.btn_settings.clicked.connect(self.open_settings)

        top_bar.addWidget(self.btn_theme)
        top_bar.addWidget(self.btn_lang)
        top_bar.addStretch()
        top_bar.addWidget(self.btn_settings)
        main_layout.addLayout(top_bar)

        main_layout.addStretch(1)

        center_layout = QVBoxLayout()
        center_layout.setSpacing(20)
        center_layout.setAlignment(Qt.AlignCenter)

        self.btn_connect = QPushButton()
        self.btn_connect.setObjectName("btn_connect")
        self.btn_connect.setCursor(Qt.PointingHandCursor)
        self.btn_connect.setMinimumSize(320, 75)

        qual_layout = QHBoxLayout()
        self.lbl_quality = QLabel()
        self.combo_quality = QComboBox()
        self.combo_quality.setMinimumWidth(240)
        self.combo_quality.setMinimumHeight(40)
        self.populate_quality_options()
        qual_layout.addStretch()
        qual_layout.addWidget(self.lbl_quality)
        qual_layout.addWidget(self.combo_quality)
        qual_layout.addStretch()

        center_layout.addWidget(self.btn_connect, 0, Qt.AlignCenter)
        center_layout.addLayout(qual_layout)

        main_layout.addLayout(center_layout)

        main_layout.addStretch(1)

        self.bottom_card = QFrame()
        self.bottom_card.setObjectName("bottom_card")
        bottom_layout = QVBoxLayout(self.bottom_card)
        bottom_layout.setSpacing(15)
        bottom_layout.setContentsMargins(20, 20, 20, 20)

        dev_layout = QHBoxLayout()
        dev_layout.setSpacing(10)

        self.lbl_status_dot = QLabel()
        self.lbl_status_dot.setFixedSize(14, 14)
        self.lbl_status_dot.setStyleSheet("background-color: #f44336; border-radius: 7px;")

        self.combo_devices = QComboBox()
        self.combo_devices.setMinimumHeight(40)

        dev_layout.addWidget(self.lbl_status_dot)
        dev_layout.addWidget(self.combo_devices, 1)

        wireless_layout = QHBoxLayout()
        wireless_layout.setSpacing(10)

        self.ip_input = QLineEdit()
        self.ip_input.setMinimumHeight(45)

        self.btn_switch_wireless = QPushButton()
        self.btn_switch_wireless.setMinimumHeight(45)
        self.btn_switch_wireless.setCursor(Qt.PointingHandCursor)
        self.btn_switch_wireless.setEnabled(False)

        wireless_layout.addWidget(self.ip_input, 2)
        wireless_layout.addWidget(self.btn_switch_wireless, 1)

        bottom_layout.addLayout(dev_layout)
        bottom_layout.addLayout(wireless_layout)

        main_layout.addWidget(self.bottom_card)

    def populate_quality_options(self):
        self.combo_quality.blockSignals(True)
        self.combo_quality.clear()
        for opt in self.quality_options[:10]:
            self.combo_quality.addItem(opt["name"], userData=opt)
        self.combo_quality.blockSignals(False)

    def toggle_language(self):
        self.language = "ZH" if self.language == "EN" else "EN"
        self.update_language()
        self.save_settings()
        self.language_changed.emit()

    def update_language(self):
        t = self.texts[self.language]
        self.setWindowTitle(t["window_title"])
        self.btn_theme.setText(t["btn_theme"])
        self.btn_lang.setText(t["btn_lang"])
        self.btn_settings.setText(t["btn_settings"])
        self.ip_input.setPlaceholderText(t["ip_placeholder"])
        self.btn_connect.setText(t["btn_connect"])
        self.lbl_quality.setText(t["lbl_quality"])
        self.btn_switch_wireless.setText(t["btn_switch_wireless"])

        for opt in self.quality_options:
            if self.language == "ZH" and opt["name"] == "Default Compatibility Mode":
                opt["name"] = "默认兼容模式"
            elif self.language == "EN" and opt["name"] == "默认兼容模式":
                opt["name"] = "Default Compatibility Mode"
        self.populate_quality_options()

    def open_settings(self):
        if not SettingsDialog:
            return

        current_config = {
            "audio_enabled": self.audio_enabled,
            "keyboard_uhid": self.keyboard_uhid,
            "controller": self.controller,
            "stay_awake": self.stay_awake,
            "program_logs": self.program_logs,
            "hide_borders": self.hide_borders,
            "show_touches": self.show_touches,
            "fullscreen": self.fullscreen,
            "always_on_top": self.always_on_top,
            "read_only": self.read_only,
            "turn_screen_off": self.turn_screen_off,
            "nav_bar_enabled": self.nav_bar_enabled,
            "perf_overlay": self.perf_overlay,
            "nav_bar_position": self.nav_bar_position,
            "max_fps": self.max_fps,
            "boss_key": self.boss_key,
            "boss_key_mods": self.boss_key_mods,
            "boss_key_vk": self.boss_key_vk
        }

        dialog = SettingsDialog(self, current_options=self.quality_options, language=self.language,
                                current_config=current_config)
        if dialog.exec_():
            new_settings = dialog.get_settings()
            self.quality_options = new_settings.get("quality_options", self.quality_options)
            self.audio_enabled = new_settings.get("audio_enabled", self.audio_enabled)
            self.keyboard_uhid = new_settings.get("keyboard_uhid", self.keyboard_uhid)
            self.controller = new_settings.get("controller", self.controller)
            self.stay_awake = new_settings.get("stay_awake", self.stay_awake)
            self.program_logs = new_settings.get("program_logs", self.program_logs)
            self.hide_borders = new_settings.get("hide_borders", self.hide_borders)
            self.show_touches = new_settings.get("show_touches", self.show_touches)
            self.fullscreen = new_settings.get("fullscreen", self.fullscreen)
            self.always_on_top = new_settings.get("always_on_top", self.always_on_top)
            self.read_only = new_settings.get("read_only", self.read_only)
            self.turn_screen_off = new_settings.get("turn_screen_off", self.turn_screen_off)
            self.nav_bar_enabled = new_settings.get("nav_bar_enabled", self.nav_bar_enabled)
            self.perf_overlay = new_settings.get("perf_overlay", self.perf_overlay)
            self.nav_bar_position = new_settings.get("nav_bar_position", self.nav_bar_position)
            self.max_fps = new_settings.get("max_fps", self.max_fps)
            self.boss_key = new_settings.get("boss_key", self.boss_key)
            self.boss_key_mods = new_settings.get("boss_key_mods", self.boss_key_mods)
            self.boss_key_vk = new_settings.get("boss_key_vk", self.boss_key_vk)

            self.populate_quality_options()
            self.save_settings()
            self.settings_saved.emit()

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme()
        self.save_settings()

    def apply_theme(self):
        base_font = "'Segoe UI', 'Microsoft YaHei', 'PingFang SC', sans-serif"

        if self.is_dark_mode:
            qss = f"""
                QMainWindow, QDialog {{ background-color: #181818; }}
                QWidget {{ color: #e0e0e0; font-family: {base_font}; font-size: 15px; }}

                #bottom_card {{ background-color: #242424; border-radius: 12px; border: 1px solid #333333; }}

                #btn_connect {{ 
                    background-color: #4daafc; color: #121212; border-radius: 37px; 
                    font-size: 20px; font-weight: bold; padding: 10px; border: none; 
                }}
                #btn_connect:hover {{ background-color: #3b90df; }}
                #btn_connect:pressed {{ background-color: #297abf; }}

                QPushButton {{ background-color: #333333; border: 1px solid #444; border-radius: 8px; padding: 10px 16px; font-weight: bold; color: #e0e0e0; }}
                QPushButton:hover {{ background-color: #404040; border-color: #555; }}
                QPushButton:pressed {{ background-color: #2a2a2a; }}
                QPushButton:disabled {{ color: #666; background-color: #2d2d2d; border-color: #333; }}

                QLineEdit, QComboBox, QListWidget {{ background-color: #2d2d2d; border: 1px solid #444; border-radius: 8px; padding: 10px 12px; color: #e0e0e0; }}
                QLineEdit:focus, QComboBox:focus, QListWidget:focus {{ border: 1px solid #4daafc; }}

                QComboBox::drop-down {{ 
                    border-left: 1px solid #444; background-color: #4daafc; 
                    border-top-right-radius: 7px; border-bottom-right-radius: 7px; width: 26px; 
                }}
                QComboBox QAbstractItemView {{
                    background-color: #2d2d2d; color: #e0e0e0; selection-background-color: #4daafc; 
                    border: 1px solid #444; border-radius: 8px; 
                }}
                QGroupBox {{ 
                    border: 1px solid #3a3a3a; border-radius: 8px; margin-top: 2ex; font-weight: bold; padding: 15px; background-color: #252526;
                }}
                QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top center; padding: 0 8px; color: #4daafc; font-size: 16px; }}
            """
        else:
            qss = f"""
                QMainWindow, QDialog {{ background-color: #f0f2f5; }}
                QWidget {{ color: #202124; font-family: {base_font}; font-size: 15px; }}

                #bottom_card {{ background-color: #ffffff; border-radius: 12px; border: 1px solid #dadce0; }}

                #btn_connect {{ 
                    background-color: #1a73e8; color: white; border-radius: 37px; 
                    font-size: 20px; font-weight: bold; padding: 10px; border: none; 
                }}
                #btn_connect:hover {{ background-color: #1557b0; }}
                #btn_connect:pressed {{ background-color: #174ea6; }}

                QPushButton {{ background-color: #ffffff; border: 1px solid #dadce0; border-radius: 8px; padding: 10px 16px; color: #1a73e8; font-weight: bold;}}
                QPushButton:hover {{ background-color: #f8f9fa; border-color: #d2e3fc; }}
                QPushButton:pressed {{ background-color: #e8f0fe; }}
                QPushButton:disabled {{ color: #9aa0a6; background-color: #f1f3f4; border-color: #f1f3f4; }}

                QLineEdit, QComboBox, QListWidget {{ background-color: #ffffff; border: 1px solid #dadce0; border-radius: 8px; padding: 10px 12px; color: #202124; }}
                QLineEdit:focus, QComboBox:focus, QListWidget:focus {{ border: 2px solid #1a73e8; padding: 9px 11px; }}

                QComboBox::drop-down {{ 
                    border-left: 1px solid #dadce0; background-color: #1a73e8; 
                    border-top-right-radius: 7px; border-bottom-right-radius: 7px; width: 26px; 
                }}
                QComboBox QAbstractItemView {{
                    background-color: #ffffff; color: #202124; selection-background-color: #1a73e8; 
                    border: 1px solid #dadce0; border-radius: 8px; 
                }}
                QGroupBox {{ 
                    border: 1px solid #dadce0; border-radius: 8px; margin-top: 2ex; font-weight: bold; padding: 15px; background-color: #ffffff;
                }}
                QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top center; padding: 0 8px; color: #1a73e8; font-size: 16px; }}
            """
        self.setStyleSheet(qss)