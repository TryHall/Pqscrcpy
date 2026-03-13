from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QCheckBox,
                             QPushButton, QLabel, QLineEdit, QListWidget,
                             QMessageBox, QFormLayout, QComboBox, QGridLayout,
                             QGroupBox, QScrollArea, QWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence


class ShortcutInput(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.mods = 0
        self.vk = 0

    def set_initial_key(self, text, mods, vk):
        self.setText(text)
        self.mods = mods
        self.vk = vk

    def keyPressEvent(self, event):
        key = event.key()
        if key in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta):
            return
        if key in (Qt.Key_Backspace, Qt.Key_Delete, Qt.Key_Escape):
            self.clear()
            self.mods = 0
            self.vk = 0
            self.setStyleSheet("")
            return

        self.vk = event.nativeVirtualKey()
        self.mods = 0
        if event.modifiers() & Qt.AltModifier: self.mods |= 0x0001
        if event.modifiers() & Qt.ControlModifier: self.mods |= 0x0002
        if event.modifiers() & Qt.ShiftModifier: self.mods |= 0x0004
        if event.modifiers() & Qt.MetaModifier: self.mods |= 0x0008

        import ctypes
        user32 = ctypes.windll.user32
        registered = user32.RegisterHotKey(None, 0xB055, self.mods, self.vk)
        if registered:
            user32.UnregisterHotKey(None, 0xB055)
            self.setStyleSheet("")
        else:
            self.setStyleSheet("background-color: #550000; border: 1px solid #ff0000; color: white;")

        mods_str = ""
        if self.mods & 0x0002: mods_str += "Ctrl+"
        if self.mods & 0x0001: mods_str += "Alt+"
        if self.mods & 0x0004: mods_str += "Shift+"
        if self.mods & 0x0008: mods_str += "Win+"

        key_seq = QKeySequence(key).toString()
        self.setText(mods_str + key_seq)


class ProfileDialog(QDialog):
    def __init__(self, parent, profile=None, texts=None):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.texts = texts
        self.setWindowTitle(self.texts["profile_title"])
        self.setMinimumWidth(450)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        group_box = QGroupBox(self.texts["profile_title"])
        layout = QFormLayout(group_box)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 25, 15, 15)

        self.name_input = QLineEdit()
        self.codec_combo = QComboBox()
        self.codec_combo.addItems(["av1", "h265", "h264"])

        self.res_combo = QComboBox()
        self.res_combo.setEditable(True)
        self.res_combo.addItems(["", "720", "1080", "1440", "2160"])

        self.bitrate_combo = QComboBox()
        self.bitrate_combo.setEditable(True)
        self.bitrate_combo.addItems(["", "2M", "4M", "8M", "16M", "32M", "64M"])

        self.fps_combo = QComboBox()
        self.fps_combo.setEditable(True)
        self.fps_combo.addItems(["", "30", "60", "90", "120", "144"])

        if profile:
            self.name_input.setText(profile.get("name", ""))
            self.codec_combo.setCurrentText(profile.get("codec", "h264"))
            self.res_combo.setCurrentText(profile.get("resolution", ""))
            self.bitrate_combo.setCurrentText(profile.get("bitrate", ""))
            self.fps_combo.setCurrentText(profile.get("fps", ""))

        layout.addRow("Profile Name:" if texts.get("btn_add") == "Add" else "配置名称:", self.name_input)
        layout.addRow(self.texts["lbl_codec"], self.codec_combo)
        layout.addRow(self.texts["lbl_res"], self.res_combo)
        layout.addRow(self.texts["lbl_bitrate"], self.bitrate_combo)
        layout.addRow(self.texts["lbl_pfps"], self.fps_combo)

        main_layout.addWidget(group_box)

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        save_btn = QPushButton("Save" if texts.get("btn_add") == "Add" else "保存")
        save_btn.setMinimumWidth(120)
        save_btn.clicked.connect(self.accept)
        btn_box.addWidget(save_btn)
        main_layout.addLayout(btn_box)

    def get_profile(self):
        return {
            "name": self.name_input.text().strip(),
            "codec": self.codec_combo.currentText(),
            "resolution": self.res_combo.currentText().strip(),
            "bitrate": self.bitrate_combo.currentText().strip(),
            "fps": self.fps_combo.currentText().strip()
        }


class SettingsDialog(QDialog):
    def __init__(self, parent=None, current_options=None, language="EN", current_config=None):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.resize(600, 560)
        self.language = language
        self.quality_options = current_options if current_options else []
        self.current_config = current_config or {}

        self.texts = {
            "EN": {
                "title": "Pqscrcpy Settings",
                "features": "Pqscrcpy Features",
                "chk_audio": "Enable Audio",
                "chk_keyboard": "Enable UHID Keyboard",
                "lbl_fps": "Global MAXfps:",
                "fps_placeholder": "e.g., 60 (leave blank)",
                "lbl_boss_key": "Boss Key:",
                "boss_key_placeholder": "Press keys (e.g., Ctrl+Alt+B)",
                "lbl_quality": "Connection Quality Profiles (Max 10)",
                "btn_add": "Add",
                "btn_modify": "Modify",
                "btn_del": "Delete",
                "btn_up": "Move Up",
                "btn_down": "Move Down",
                "btn_save": "Save Settings",
                "err_limit": "Limit Reached: Maximum 10 connection quality options.",
                "chk_stay_awake": "Keep screen on during wake",
                "chk_logs": "Program logs",
                "chk_hide_borders": "Hide borders",
                "chk_show_touches": "Show touch",
                "chk_fullscreen": "Full-screen window",
                "chk_always_on_top": "Window always on top",
                "chk_read_only": "Read-only mode",
                "chk_turn_screen_off": "Turn screen off",
                "chk_controller": "Enable controller",
                "chk_nav_bar": "Enable floating navigation bar",
                "chk_perf": "Real-time performance overlay",
                "lbl_nav_pos": "Nav Bar Position:",
                "pos_top": "Top Center", "pos_bottom": "Bottom Center",
                "pos_left": "Left Center", "pos_right": "Right Center",
                "pos_tl_v": "Top-Left (Vertical)", "pos_tl_h": "Top-Left (Horizontal)",
                "pos_tr_v": "Top-Right (Vertical)", "pos_tr_h": "Top-Right (Horizontal)",
                "pos_bl_v": "Bottom-Left (Vertical)", "pos_bl_h": "Bottom-Left (Horizontal)",
                "pos_br_v": "Bottom-Right (Vertical)", "pos_br_h": "Bottom-Right (Horizontal)",
                "profile_title": "Profile Settings",
                "lbl_codec": "Encoding (av1/h265/h264):",
                "lbl_res": "Resolution:",
                "lbl_bitrate": "Bitrate:",
                "lbl_pfps": "Frame Rate:",
                "about": "<a href='https://github.com/TryHall/Pqscrcpy' style='color: #4daafc; text-decoration: none;'>Pqscrcpy v1.0.0</a> | <a href='https://github.com/Genymobile/scrcpy' style='color: #4daafc; text-decoration: none;'>Powered by scrcpy</a>"
            },
            "ZH": {
                "title": "Pqscrcpy 设置",
                "features": "Pqscrcpy 运行参数",
                "chk_audio": "启用音频传输",
                "chk_keyboard": "启用 UHID 键盘",
                "lbl_fps": "全局最大帧率:",
                "fps_placeholder": "例如 60 (留空)",
                "lbl_boss_key": "老板键快捷键:",
                "boss_key_placeholder": "按下按键 (例如: Ctrl+Alt+B)",
                "lbl_quality": "连接质量配置 (最多 10 个)",
                "btn_add": "添加",
                "btn_modify": "修改",
                "btn_del": "删除",
                "btn_up": "上移",
                "btn_down": "下移",
                "btn_save": "保存设置",
                "err_limit": "已达上限: 最多只能有 10 个连接质量选项。",
                "chk_stay_awake": "唤醒时保持屏幕常亮",
                "chk_logs": "程序日志",
                "chk_hide_borders": "隐藏无边框",
                "chk_show_touches": "显示触摸轨迹",
                "chk_fullscreen": "全屏窗口",
                "chk_always_on_top": "窗口置顶",
                "chk_read_only": "只读模式",
                "chk_turn_screen_off": "关闭设备屏幕",
                "chk_controller": "启用手柄控制",
                "chk_nav_bar": "启用悬浮导航栏",
                "chk_perf": "实时性能监测 (覆盖在画面上)",
                "lbl_nav_pos": "导航栏位置:",
                "pos_top": "顶部居中 (横向)", "pos_bottom": "底部居中 (横向)",
                "pos_left": "左侧居中 (竖向)", "pos_right": "右侧居中 (竖向)",
                "pos_tl_v": "左上角 (竖向)", "pos_tl_h": "左上角 (横向)",
                "pos_tr_v": "右上角 (竖向)", "pos_tr_h": "右上角 (横向)",
                "pos_bl_v": "左下角 (竖向)", "pos_bl_h": "左下角 (横向)",
                "pos_br_v": "右下角 (竖向)", "pos_br_h": "右下角 (横向)",
                "profile_title": "配置设置",
                "lbl_codec": "编码格式 (av1/h265/h264):",
                "lbl_res": "分辨率:",
                "lbl_bitrate": "比特率:",
                "lbl_pfps": "帧率:",
                "about": "<a href='https://github.com/TryHall/Pqscrcpy' style='color: #4daafc; text-decoration: none;'>Pqscrcpy v1.0.0</a> | <a href='https://github.com/Genymobile/scrcpy' style='color: #4daafc; text-decoration: none;'>由 scrcpy 驱动</a>"
            }
        }

        self.init_ui()
        self.apply_language()

    def init_ui(self):
        base_layout = QVBoxLayout(self)
        base_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        content_widget = QWidget()
        main_layout = QVBoxLayout(content_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(25, 25, 25, 25)

        t = self.texts[self.language]

        self.features_group = QGroupBox(t["features"])
        features_layout = QVBoxLayout(self.features_group)
        features_layout.setSpacing(15)
        features_layout.setContentsMargins(20, 25, 20, 20)

        features_grid = QGridLayout()
        features_grid.setVerticalSpacing(15)
        features_grid.setHorizontalSpacing(30)

        self.chk_keyboard = QCheckBox()
        self.chk_controller = QCheckBox()
        self.chk_nav_bar = QCheckBox()
        self.chk_perf = QCheckBox()
        self.chk_audio = QCheckBox()
        self.chk_read_only = QCheckBox()
        self.chk_turn_screen_off = QCheckBox()
        self.chk_logs = QCheckBox()

        self.chk_fullscreen = QCheckBox()
        self.chk_hide_borders = QCheckBox()
        self.chk_always_on_top = QCheckBox()
        self.chk_show_touches = QCheckBox()
        self.chk_stay_awake = QCheckBox()

        self.chk_audio.setChecked(self.current_config.get("audio_enabled", False))
        self.chk_keyboard.setChecked(self.current_config.get("keyboard_uhid", True))
        self.chk_controller.setChecked(self.current_config.get("controller", False))
        self.chk_stay_awake.setChecked(self.current_config.get("stay_awake", False))
        self.chk_hide_borders.setChecked(self.current_config.get("hide_borders", False))
        self.chk_show_touches.setChecked(self.current_config.get("show_touches", False))
        self.chk_fullscreen.setChecked(self.current_config.get("fullscreen", False))
        self.chk_always_on_top.setChecked(self.current_config.get("always_on_top", False))
        self.chk_read_only.setChecked(self.current_config.get("read_only", False))
        self.chk_turn_screen_off.setChecked(self.current_config.get("turn_screen_off", False))
        self.chk_logs.setChecked(self.current_config.get("program_logs", False))
        self.chk_nav_bar.setChecked(self.current_config.get("nav_bar_enabled", True))
        self.chk_perf.setChecked(self.current_config.get("perf_overlay", False))

        features_grid.addWidget(self.chk_keyboard, 0, 0)
        features_grid.addWidget(self.chk_nav_bar, 1, 0)
        features_grid.addWidget(self.chk_perf, 2, 0)
        features_grid.addWidget(self.chk_controller, 3, 0)
        features_grid.addWidget(self.chk_audio, 4, 0)
        features_grid.addWidget(self.chk_read_only, 5, 0)
        features_grid.addWidget(self.chk_turn_screen_off, 6, 0)

        features_grid.addWidget(self.chk_always_on_top, 0, 1)
        features_grid.addWidget(self.chk_show_touches, 1, 1)
        features_grid.addWidget(self.chk_hide_borders, 2, 1)
        features_grid.addWidget(self.chk_fullscreen, 3, 1)
        features_grid.addWidget(self.chk_stay_awake, 4, 1)
        features_grid.addWidget(self.chk_logs, 5, 1)

        features_layout.addLayout(features_grid)

        nav_layout = QHBoxLayout()
        self.lbl_nav_pos = QLabel()
        self.combo_nav_pos = QComboBox()

        nav_layout.addWidget(self.lbl_nav_pos)
        nav_layout.addWidget(self.combo_nav_pos)
        nav_layout.addStretch()
        features_layout.addLayout(nav_layout)

        misc_layout = QHBoxLayout()
        misc_layout.setSpacing(10)
        self.lbl_fps = QLabel()
        self.input_fps = QLineEdit()
        self.input_fps.setText(str(self.current_config.get("max_fps", "")))

        self.lbl_boss_key = QLabel()
        self.boss_key_input = ShortcutInput(self)
        self.boss_key_input.set_initial_key(
            self.current_config.get("boss_key", ""),
            self.current_config.get("boss_key_mods", 0),
            self.current_config.get("boss_key_vk", 0)
        )

        misc_layout.addWidget(self.lbl_fps)
        misc_layout.addWidget(self.input_fps)
        misc_layout.addWidget(self.lbl_boss_key)
        misc_layout.addWidget(self.boss_key_input)

        features_layout.addLayout(misc_layout)
        main_layout.addWidget(self.features_group)

        self.profiles_group = QGroupBox(t["lbl_quality"])
        profiles_layout = QVBoxLayout(self.profiles_group)
        profiles_layout.setSpacing(15)
        profiles_layout.setContentsMargins(15, 25, 15, 15)

        self.list_quality = QListWidget()
        self.refresh_list()
        profiles_layout.addWidget(self.list_quality)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        self.btn_add_quality = QPushButton()
        self.btn_modify_quality = QPushButton()
        self.btn_del_quality = QPushButton()
        self.btn_up_quality = QPushButton()
        self.btn_down_quality = QPushButton()

        self.btn_add_quality.clicked.connect(self.add_quality)
        self.btn_modify_quality.clicked.connect(self.modify_quality)
        self.btn_del_quality.clicked.connect(self.delete_quality)
        self.btn_up_quality.clicked.connect(self.move_up)
        self.btn_down_quality.clicked.connect(self.move_down)

        btn_layout.addWidget(self.btn_add_quality)
        btn_layout.addWidget(self.btn_modify_quality)
        btn_layout.addWidget(self.btn_del_quality)
        btn_layout.addWidget(self.btn_up_quality)
        btn_layout.addWidget(self.btn_down_quality)
        profiles_layout.addLayout(btn_layout)

        main_layout.addWidget(self.profiles_group)

        self.btn_save = QPushButton()
        self.btn_save.setMinimumHeight(45)
        self.btn_save.clicked.connect(self.accept)
        main_layout.addWidget(self.btn_save)

        self.lbl_about = QLabel()
        self.lbl_about.setAlignment(Qt.AlignCenter)
        self.lbl_about.setOpenExternalLinks(True)
        self.lbl_about.setStyleSheet("color: #888888; font-size: 13px;")
        main_layout.addWidget(self.lbl_about)

        scroll.setWidget(content_widget)
        base_layout.addWidget(scroll)

    def apply_language(self):
        t = self.texts[self.language]
        self.setWindowTitle(t["title"])
        self.features_group.setTitle(t["features"])
        self.chk_audio.setText(t["chk_audio"])
        self.chk_keyboard.setText(t["chk_keyboard"])
        self.chk_controller.setText(t["chk_controller"])
        self.chk_stay_awake.setText(t["chk_stay_awake"])
        self.chk_hide_borders.setText(t["chk_hide_borders"])
        self.chk_show_touches.setText(t["chk_show_touches"])
        self.chk_fullscreen.setText(t["chk_fullscreen"])
        self.chk_always_on_top.setText(t["chk_always_on_top"])
        self.chk_read_only.setText(t["chk_read_only"])
        self.chk_turn_screen_off.setText(t["chk_turn_screen_off"])
        self.chk_logs.setText(t["chk_logs"])
        self.chk_nav_bar.setText(t["chk_nav_bar"])
        self.chk_perf.setText(t["chk_perf"])
        self.lbl_nav_pos.setText(t["lbl_nav_pos"])

        self.combo_nav_pos.blockSignals(True)
        self.combo_nav_pos.clear()
        self.combo_nav_pos.addItem(t["pos_top"], userData="top")
        self.combo_nav_pos.addItem(t["pos_bottom"], userData="bottom")
        self.combo_nav_pos.addItem(t["pos_left"], userData="left")
        self.combo_nav_pos.addItem(t["pos_right"], userData="right")
        self.combo_nav_pos.addItem(t["pos_tl_v"], userData="tl_v")
        self.combo_nav_pos.addItem(t["pos_tl_h"], userData="tl_h")
        self.combo_nav_pos.addItem(t["pos_tr_v"], userData="tr_v")
        self.combo_nav_pos.addItem(t["pos_tr_h"], userData="tr_h")
        self.combo_nav_pos.addItem(t["pos_bl_v"], userData="bl_v")
        self.combo_nav_pos.addItem(t["pos_bl_h"], userData="bl_h")
        self.combo_nav_pos.addItem(t["pos_br_v"], userData="br_v")
        self.combo_nav_pos.addItem(t["pos_br_h"], userData="br_h")

        current_pos = self.current_config.get("nav_bar_position", "right")
        index = self.combo_nav_pos.findData(current_pos)
        if index >= 0:
            self.combo_nav_pos.setCurrentIndex(index)
        self.combo_nav_pos.blockSignals(False)

        self.lbl_fps.setText(t["lbl_fps"])
        self.input_fps.setPlaceholderText(t["fps_placeholder"])
        self.lbl_boss_key.setText(t["lbl_boss_key"])
        self.boss_key_input.setPlaceholderText(t["boss_key_placeholder"])
        self.profiles_group.setTitle(t["lbl_quality"])
        self.btn_add_quality.setText(t["btn_add"])
        self.btn_modify_quality.setText(t["btn_modify"])
        self.btn_del_quality.setText(t["btn_del"])
        self.btn_up_quality.setText(t["btn_up"])
        self.btn_down_quality.setText(t["btn_down"])
        self.btn_save.setText(t["btn_save"])
        self.lbl_about.setText(t["about"])

    def refresh_list(self):
        self.list_quality.clear()
        for opt in self.quality_options:
            details = f"[{opt.get('codec', 'N/A')}] {opt.get('resolution', 'Auto')}p | {opt.get('bitrate', 'Auto')} | {opt.get('fps', 'Auto')} FPS"
            self.list_quality.addItem(f"{opt['name']} | {details}")

    def add_quality(self):
        t = self.texts[self.language]
        if len(self.quality_options) >= 10:
            QMessageBox.warning(self, "Warning", t["err_limit"])
            return

        dialog = ProfileDialog(self, texts=t)
        if dialog.exec_():
            new_profile = dialog.get_profile()
            if new_profile["name"]:
                self.quality_options.append(new_profile)
                self.refresh_list()

    def modify_quality(self):
        t = self.texts[self.language]
        current_row = self.list_quality.currentRow()
        if current_row < 0:
            return

        profile = self.quality_options[current_row]
        dialog = ProfileDialog(self, profile=profile, texts=t)
        if dialog.exec_():
            updated_profile = dialog.get_profile()
            if updated_profile["name"]:
                self.quality_options[current_row] = updated_profile
                self.refresh_list()

    def delete_quality(self):
        current_row = self.list_quality.currentRow()
        if current_row < 0:
            return

        del self.quality_options[current_row]
        self.refresh_list()

    def move_up(self):
        row = self.list_quality.currentRow()
        if row > 0:
            self.quality_options[row - 1], self.quality_options[row] = self.quality_options[row], self.quality_options[
                row - 1]
            self.refresh_list()
            self.list_quality.setCurrentRow(row - 1)

    def move_down(self):
        row = self.list_quality.currentRow()
        if row >= 0 and row < len(self.quality_options) - 1:
            self.quality_options[row + 1], self.quality_options[row] = self.quality_options[row], self.quality_options[
                row + 1]
            self.refresh_list()
            self.list_quality.setCurrentRow(row + 1)

    def accept(self):
        if len(self.quality_options) == 0:
            default_name = "默认兼容模式" if self.language == "ZH" else "Default Compatibility Mode"
            self.quality_options.append({
                "name": default_name,
                "codec": "h264",
                "resolution": "720",
                "bitrate": "8M",
                "fps": "30"
            })
        super().accept()

    def get_settings(self):
        return {
            "audio_enabled": self.chk_audio.isChecked(),
            "keyboard_uhid": self.chk_keyboard.isChecked(),
            "controller": self.chk_controller.isChecked(),
            "stay_awake": self.chk_stay_awake.isChecked(),
            "hide_borders": self.chk_hide_borders.isChecked(),
            "show_touches": self.chk_show_touches.isChecked(),
            "fullscreen": self.chk_fullscreen.isChecked(),
            "always_on_top": self.chk_always_on_top.isChecked(),
            "read_only": self.chk_read_only.isChecked(),
            "turn_screen_off": self.chk_turn_screen_off.isChecked(),
            "nav_bar_enabled": self.chk_nav_bar.isChecked(),
            "perf_overlay": self.chk_perf.isChecked(),
            "nav_bar_position": self.combo_nav_pos.currentData(),
            "program_logs": self.chk_logs.isChecked(),
            "max_fps": self.input_fps.text().strip(),
            "boss_key": self.boss_key_input.text().strip(),
            "boss_key_mods": self.boss_key_input.mods,
            "boss_key_vk": self.boss_key_input.vk,
            "quality_options": self.quality_options
        }