import sys
import os
import subprocess
import ctypes
import re
from ctypes import wintypes
from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout, QApplication, QMessageBox, QWidget, QPushButton, QGridLayout, \
    QPlainTextEdit
from PyQt5.QtCore import QTimer, pyqtSignal, Qt, QThread, QAbstractNativeEventFilter
from PyQt5.QtGui import QIcon

from ui_main import ScrcpyMainUI
from adb_manager import AdbManager

# --- Explicitly define ctypes argtypes and restype to prevent 64-bit OverflowError ---
user32 = ctypes.windll.user32

user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowThreadProcessId.restype = wintypes.DWORD

user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
user32.GetWindowTextLengthW.restype = ctypes.c_int

user32.GetWindowTextW.argtypes = [wintypes.HWND, ctypes.c_wchar_p, ctypes.c_int]
user32.GetWindowTextW.restype = ctypes.c_int

user32.IsWindow.argtypes = [wintypes.HWND]
user32.IsWindow.restype = ctypes.c_bool

user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.ShowWindow.restype = ctypes.c_bool

user32.IsIconic.argtypes = [wintypes.HWND]
user32.IsIconic.restype = ctypes.c_bool

user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.IsWindowVisible.restype = ctypes.c_bool

user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.GetWindowRect.restype = ctypes.c_bool

EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
user32.EnumWindows.argtypes = [EnumWindowsProc, wintypes.LPARAM]
user32.EnumWindows.restype = ctypes.c_bool


# -------------------------------------------------------------------------------------

class HotkeyFilter(QAbstractNativeEventFilter):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def nativeEventFilter(self, eventType, message):
        if eventType == b"windows_generic_MSG":
            msg = wintypes.MSG.from_address(message.__int__())
            if msg.message == 0x0312:
                if msg.wParam == 1:
                    self.callback()
                    return True, 0
        return False, 0


class LogReaderThread(QThread):
    log_signal = pyqtSignal(str)

    def __init__(self, process):
        super().__init__()
        self.process = process
        self._is_running = True

    def run(self):
        for line in iter(self.process.stdout.readline, ''):
            if not self._is_running or not line:
                break
            self.log_signal.emit(line.strip())

    def stop(self):
        self._is_running = False


class LogWindow(QDialog):
    def __init__(self, parent=None, title="Pqscrcpy Logs"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(600, 400)
        layout = QVBoxLayout(self)
        self.text_area = QPlainTextEdit()
        self.text_area.setReadOnly(True)
        base_font = "'Segoe UI', 'Microsoft YaHei', 'PingFang SC', sans-serif"
        self.text_area.setStyleSheet(
            f"font-family: {base_font}; font-size: 13px; background-color: #1e1e1e; color: #d4d4d4; padding: 5px;")
        layout.addWidget(self.text_area)

    def append_log(self, text):
        self.text_area.appendPlainText(text)
        bar = self.text_area.verticalScrollBar()
        bar.setValue(bar.maximum())


class PerfWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowTransparentForInput)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        base_font = "'Segoe UI', 'Microsoft YaHei', 'PingFang SC', sans-serif"
        lbl_style = f"color: #00FF00; background-color: rgba(0, 0, 0, 160); font-weight: bold; font-family: {base_font}; font-size: 14px; padding: 4px 8px; border-radius: 4px;"

        self.lbl_fps = QLabel("FPS: --")
        self.lbl_bitrate = QLabel("Bitrate: --")

        self.lbl_fps.setStyleSheet(lbl_style)
        self.lbl_bitrate.setStyleSheet(lbl_style)

        layout.addWidget(self.lbl_fps)
        layout.addWidget(self.lbl_bitrate)

    def update_perf(self, fps=None, bitrate=None):
        if fps: self.lbl_fps.setText(f"FPS: {fps}")
        if bitrate: self.lbl_bitrate.setText(f"Bitrate: {bitrate}")
        self.adjustSize()


class NavBarWindow(QWidget):
    drag_started = pyqtSignal()
    drag_ended = pyqtSignal(object)
    closed = pyqtSignal()

    def __init__(self, send_cmd_func):
        super().__init__()
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(5, 5, 5, 5)
        self.grid.setSpacing(5)

        base_font = "'Segoe UI', 'Microsoft YaHei', 'PingFang SC', sans-serif"
        btn_style = f"""
            QPushButton {{ background-color: #333333; color: white; border: 1px solid #555; border-radius: 4px; padding: 10px; font-weight: bold; font-family: {base_font}; }}
            QPushButton:hover {{ background-color: #505050; }}
            QPushButton:pressed {{ background-color: #202020; }}
        """
        close_style = f"""
            QPushButton {{ background-color: #880000; color: white; border: 1px solid #555; border-radius: 4px; padding: 10px; font-weight: bold; font-family: {base_font}; }}
            QPushButton:hover {{ background-color: #aa0000; }}
            QPushButton:pressed {{ background-color: #550000; }}
        """

        self.btn_back = QPushButton("◁")
        self.btn_home = QPushButton("〇")
        self.btn_recent = QPushButton("□")
        self.btn_close = QPushButton("×")

        self.btn_back.setStyleSheet(btn_style)
        self.btn_home.setStyleSheet(btn_style)
        self.btn_recent.setStyleSheet(btn_style)
        self.btn_close.setStyleSheet(close_style)

        self.btn_back.clicked.connect(lambda: send_cmd_func(4))
        self.btn_home.clicked.connect(lambda: send_cmd_func(3))
        self.btn_recent.clicked.connect(lambda: send_cmd_func(187))
        self.btn_close.clicked.connect(self.closed.emit)

        self.current_orientation = None
        self.set_orientation("right")

        self._is_dragging = False
        self._drag_start_pos = None

    def set_orientation(self, pos):
        is_horizontal = pos in ["top", "bottom", "tl_h", "tr_h", "bl_h", "br_h"]
        new_orientation = "h" if is_horizontal else "v"

        if self.current_orientation == new_orientation:
            return

        self.current_orientation = new_orientation

        self.grid.removeWidget(self.btn_back)
        self.grid.removeWidget(self.btn_home)
        self.grid.removeWidget(self.btn_recent)
        self.grid.removeWidget(self.btn_close)

        if is_horizontal:
            self.grid.addWidget(self.btn_back, 0, 0)
            self.grid.addWidget(self.btn_home, 0, 1)
            self.grid.addWidget(self.btn_recent, 0, 2)
            self.grid.addWidget(self.btn_close, 0, 3)
            self.setFixedSize(185, 45)
        else:
            self.grid.addWidget(self.btn_back, 0, 0)
            self.grid.addWidget(self.btn_home, 1, 0)
            self.grid.addWidget(self.btn_recent, 2, 0)
            self.grid.addWidget(self.btn_close, 3, 0)
            self.setFixedSize(45, 185)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_dragging = True
            self._drag_start_pos = event.globalPos() - self.frameGeometry().topLeft()
            self.drag_started.emit()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._is_dragging:
            self.move(event.globalPos() - self._drag_start_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._is_dragging:
            self._is_dragging = False
            self.drag_ended.emit(self.pos())
            event.accept()


class MainApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setWindowIcon(QIcon("icon.ico"))

        self.hotkey_filter = HotkeyFilter(self.toggle_visibility)
        self.app.installNativeEventFilter(self.hotkey_filter)

        self.ui = ScrcpyMainUI()
        self.adb = AdbManager()

        self.current_devices = []
        self.scrcpy_process = None
        self.log_thread = None
        self.log_window = None

        self.is_hidden = False

        self.nav_bar = None
        self.perf_window = None
        self.is_dragging_nav = False

        self.tracking_timer = QTimer()
        self.tracking_timer.timeout.connect(self.update_overlays_position)

        self.bind_events()
        self.update_device_ui()
        self.start_device_polling()
        self.register_boss_key()

    def bind_events(self):
        self.ui.btn_connect.clicked.connect(self.launch_scrcpy)
        self.ui.btn_switch_wireless.clicked.connect(self.handle_switch_wireless)
        self.ui.settings_saved.connect(self.on_settings_saved)
        self.ui.language_changed.connect(self.update_device_ui)
        self.ui.combo_devices.currentIndexChanged.connect(self.on_device_selected)
        self.ui.combo_quality.currentIndexChanged.connect(self.on_quality_changed)

    def on_settings_saved(self):
        self.register_boss_key()
        self.update_device_ui()

    def on_device_selected(self, index):
        if index < 0 or not self.current_devices:
            return
        device = self.ui.combo_devices.currentText()
        saved_quality = self.ui.device_quality_map.get(device)
        if saved_quality:
            idx = self.ui.combo_quality.findText(saved_quality, Qt.MatchContains)
            if idx >= 0:
                self.ui.combo_quality.blockSignals(True)
                self.ui.combo_quality.setCurrentIndex(idx)
                self.ui.combo_quality.blockSignals(False)

    def on_quality_changed(self, index):
        if index < 0 or not self.current_devices:
            return
        device = self.ui.combo_devices.currentText()
        if device and device in self.current_devices:
            quality_name = self.ui.combo_quality.currentText().split('|')[0].strip()
            self.ui.device_quality_map[device] = quality_name
            self.ui.save_settings()

    def handle_nav_drag_started(self):
        self.is_dragging_nav = True

    def handle_nav_drag_ended(self, drop_pos):
        self.is_dragging_nav = False
        hwnd = self.get_scrcpy_hwnd()
        if not hwnd or not self.nav_bar:
            return

        rect = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))

        w = rect.right - rect.left
        h = rect.bottom - rect.top

        horiz_w, horiz_h = 185, 45
        vert_w, vert_h = 45, 185

        positions = {
            "top": (rect.left + (w // 2) - (horiz_w // 2), rect.top - horiz_h),
            "bottom": (rect.left + (w // 2) - (horiz_w // 2), rect.bottom),
            "left": (rect.left - vert_w, rect.top + (h // 2) - (vert_h // 2)),
            "right": (rect.right, rect.top + (h // 2) - (vert_h // 2)),

            "tl_v": (rect.left - vert_w, rect.top),
            "tl_h": (rect.left, rect.top - horiz_h),

            "tr_v": (rect.right, rect.top),
            "tr_h": (rect.right - horiz_w, rect.top - horiz_h),

            "bl_v": (rect.left - vert_w, rect.bottom - vert_h),
            "bl_h": (rect.left, rect.bottom),

            "br_v": (rect.right, rect.bottom - vert_h),
            "br_h": (rect.right - horiz_w, rect.bottom)
        }

        closest_pos = "right"
        min_dist = float('inf')
        for name, (tx, ty) in positions.items():
            dist = (drop_pos.x() - tx) ** 2 + (drop_pos.y() - ty) ** 2
            if dist < min_dist:
                min_dist = dist
                closest_pos = name

        self.ui.nav_bar_position = closest_pos
        self.ui.save_settings()
        self.update_overlays_position()

    def handle_nav_closed(self):
        self.ui.nav_bar_enabled = False
        self.ui.save_settings()
        if self.nav_bar:
            self.nav_bar.hide()

    def handle_log_line(self, line):
        if self.log_window and self.log_window.isVisible():
            self.log_window.append_log(line)

        if self.ui.perf_overlay and self.perf_window:
            fps_match = re.search(r'(\d+)\s*fps', line)
            if fps_match:
                self.perf_window.update_perf(fps=fps_match.group(1))

    def send_navigation_command(self, keycode):
        target_ip = self.ui.ip_input.text().strip()
        device = self.ui.combo_devices.currentText()
        if not device and not target_ip:
            device = self.current_devices[0] if self.current_devices else None

        if device or target_ip:
            self.adb.send_keyevent(target_ip if target_ip else device, keycode)
        else:
            msg = "No active device found to send commands." if self.ui.language == "EN" else "未找到活动设备以发送命令。"
            QMessageBox.warning(self.ui, "Warning" if self.ui.language == "EN" else "警告", msg)

    def register_boss_key(self):
        hwnd = int(self.ui.winId())
        user32.UnregisterHotKey(hwnd, 1)

        mods = self.ui.boss_key_mods
        vk = self.ui.boss_key_vk

        if vk and mods is not None:
            if not user32.RegisterHotKey(hwnd, 1, mods, vk):
                msg = "Boss Key conflict! Please choose another combination." if self.ui.language == "EN" else "老板键被其他程序占用，请选择其他快捷键。"
                QMessageBox.warning(self.ui, "Shortcut Error" if self.ui.language == "EN" else "快捷键错误", msg)

    def toggle_visibility(self):
        self.is_hidden = not self.is_hidden
        if self.is_hidden:
            self.ui.hide()
            if self.nav_bar: self.nav_bar.hide()
            if self.perf_window: self.perf_window.hide()
            self.hide_scrcpy(True)
        else:
            self.ui.show()
            self.hide_scrcpy(False)

    def hide_scrcpy(self, hide):
        hwnd = self.get_scrcpy_hwnd()
        if hwnd:
            user32.ShowWindow(hwnd, 0 if hide else 5)

    def get_scrcpy_hwnd(self):
        if not self.scrcpy_process or self.scrcpy_process.poll() is not None:
            self._cached_scrcpy_hwnd = None
            return None

        # Validate cache: ensure window is still valid.
        # DO NOT require IsWindowVisible here, as the boss key intentionally hides it.
        if hasattr(self, '_cached_scrcpy_hwnd') and self._cached_scrcpy_hwnd:
            if user32.IsWindow(self._cached_scrcpy_hwnd):
                return self._cached_scrcpy_hwnd
            else:
                self._cached_scrcpy_hwnd = None  # Invalidate cache only if destroyed

        target_pid = self.scrcpy_process.pid
        found_hwnd = None

        def callback(hwnd, lParam):
            nonlocal found_hwnd
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value == target_pid:
                if user32.IsWindowVisible(hwnd):  # Only lock onto initially visible windows
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        # Extract title to filter out generic system windows
                        title_buf = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(hwnd, title_buf, length + 1)
                        title = title_buf.value
                        if "IME" not in title and "Default" not in title:
                            found_hwnd = hwnd
                            return False  # Stop enumerating
            return True

        # Assign EnumWindowsProc to a variable to prevent Python from garbage collecting the callback
        enum_func = EnumWindowsProc(callback)
        user32.EnumWindows(enum_func, 0)

        if found_hwnd:
            self._cached_scrcpy_hwnd = found_hwnd

        return found_hwnd

    def update_overlays_position(self):
        if (not self.ui.nav_bar_enabled and not self.ui.perf_overlay) or self.is_hidden:
            if self.nav_bar: self.nav_bar.hide()
            if self.perf_window: self.perf_window.hide()
            return

        hwnd = self.get_scrcpy_hwnd()
        if not hwnd or user32.IsIconic(hwnd) or not user32.IsWindowVisible(hwnd):
            if self.nav_bar: self.nav_bar.hide()
            if self.perf_window: self.perf_window.hide()
            return

        rect = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        w = rect.right - rect.left
        h = rect.bottom - rect.top

        if self.ui.perf_overlay and self.perf_window:
            y_offset = 35 if not self.ui.hide_borders else 5
            tx = rect.left + 10
            ty = rect.top + y_offset
            self.perf_window.move(tx, ty)
            if not self.perf_window.isVisible():
                self.perf_window.show()

        if self.ui.nav_bar_enabled and self.nav_bar and not self.is_dragging_nav:
            pos = self.ui.nav_bar_position
            self.nav_bar.set_orientation(pos)
            nav_w = self.nav_bar.width()
            nav_h = self.nav_bar.height()

            if pos == "top":
                tx, ty = rect.left + (w // 2) - (nav_w // 2), rect.top - nav_h
            elif pos == "bottom":
                tx, ty = rect.left + (w // 2) - (nav_w // 2), rect.bottom
            elif pos == "left":
                tx, ty = rect.left - nav_w, rect.top + (h // 2) - (nav_h // 2)
            elif pos == "right":
                tx, ty = rect.right, rect.top + (h // 2) - (nav_h // 2)

            elif pos == "tl_v":
                tx, ty = rect.left - nav_w, rect.top
            elif pos == "tl_h":
                tx, ty = rect.left, rect.top - nav_h

            elif pos == "tr_v":
                tx, ty = rect.right, rect.top
            elif pos == "tr_h":
                tx, ty = rect.right - nav_w, rect.top - nav_h

            elif pos == "bl_v":
                tx, ty = rect.left - nav_w, rect.bottom - nav_h
            elif pos == "bl_h":
                tx, ty = rect.left, rect.bottom

            elif pos == "br_v":
                tx, ty = rect.right, rect.bottom - nav_h
            elif pos == "br_h":
                tx, ty = rect.right - nav_w, rect.bottom
            else:
                tx, ty = rect.right, rect.top + (h // 2) - (nav_h // 2)

            self.nav_bar.move(tx, ty)
            if not self.nav_bar.isVisible():
                self.nav_bar.show()

    def start_device_polling(self):
        self.poll_timer = QTimer()
        self.poll_timer.timeout.connect(self.check_devices)
        self.poll_timer.start(2000)

    def check_devices(self):
        devices = self.adb.get_connected_devices()

        if devices != self.current_devices:
            self.current_devices = devices
            self.update_device_ui()

    def update_device_ui(self):
        current_sel = self.ui.combo_devices.currentText()
        self.ui.combo_devices.blockSignals(True)
        self.ui.combo_devices.clear()

        if not self.current_devices:
            msg = self.ui.texts[self.ui.language]["no_devices"]
            self.ui.combo_devices.addItem(msg)
            self.ui.lbl_status_dot.setStyleSheet("background-color: #f44336; border-radius: 7px;")
            self.ui.btn_switch_wireless.setEnabled(False)
        else:
            self.ui.combo_devices.addItems(self.current_devices)
            self.ui.lbl_status_dot.setStyleSheet("background-color: #4CAF50; border-radius: 7px;")

            if current_sel in self.current_devices:
                self.ui.combo_devices.setCurrentText(current_sel)
            else:
                current_sel = self.current_devices[0]

            is_usb = ":" not in current_sel
            self.ui.btn_switch_wireless.setEnabled(is_usb)

            if not is_usb and not self.ui.ip_input.text():
                self.ui.ip_input.setText(current_sel)

        self.ui.combo_devices.blockSignals(False)
        self.on_device_selected(self.ui.combo_devices.currentIndex())

    def handle_switch_wireless(self):
        if not self.current_devices:
            return

        target_device = self.ui.combo_devices.currentText()
        if not target_device or target_device not in self.current_devices:
            target_device = self.current_devices[0]

        self.ui.btn_switch_wireless.setEnabled(False)

        wireless_ip = self.adb.switch_to_wireless(target_device)

        if wireless_ip:
            self.ui.ip_input.setText(wireless_ip)
            self.check_devices()
        else:
            msg = "Failed to extract device IP or switch to TCP mode." if self.ui.language == "EN" else "无法提取设备 IP 或切换到 TCP 模式。"
            QMessageBox.warning(self.ui, "Error" if self.ui.language == "EN" else "错误", msg)
            self.check_devices()

    def launch_scrcpy(self):
        target_ip = self.ui.ip_input.text().strip()
        device_sel = self.ui.combo_devices.currentText()

        if not target_ip and (not self.current_devices or device_sel not in self.current_devices):
            msg = "No device IP entered and no USB device detected." if self.ui.language == "EN" else "未输入设备 IP，也未检测到 USB 设备。"
            QMessageBox.warning(self.ui, "Error" if self.ui.language == "EN" else "错误", msg)
            return

        quality_opt = self.ui.combo_quality.currentData()
        if not quality_opt:
            quality_opt = self.ui.default_quality

        scrcpy_dir = self.ui.custom_scrcpy_path
        if not scrcpy_dir:
            scrcpy_dir = "scrcpy"

        scrcpy_exe = os.path.join(scrcpy_dir, "scrcpy.exe")
        cmd = [scrcpy_exe]

        if target_ip:
            cmd.extend(["-s", target_ip])
        elif device_sel in self.current_devices:
            cmd.extend(["-s", device_sel])

        if quality_opt.get("bitrate"):
            cmd.extend(["--video-bit-rate", quality_opt["bitrate"]])
        if quality_opt.get("resolution"):
            cmd.extend(["--max-size", quality_opt["resolution"]])
        if quality_opt.get("codec"):
            cmd.extend([f"--video-codec={quality_opt['codec']}"])

        fps_to_use = self.ui.max_fps if (self.ui.max_fps and self.ui.max_fps.isdigit()) else quality_opt.get("fps")
        if fps_to_use and str(fps_to_use).isdigit():
            cmd.extend(["--max-fps", str(fps_to_use)])

        if not self.ui.audio_enabled:
            cmd.append("--no-audio")
        if self.ui.keyboard_uhid:
            cmd.append("--keyboard=uhid")
        if self.ui.controller:
            cmd.append("--gamepad=uhid")
        if self.ui.stay_awake:
            cmd.append("--stay-awake")
        if self.ui.hide_borders:
            cmd.append("--window-borderless")
        if self.ui.show_touches:
            cmd.append("--show-touches")
        if self.ui.fullscreen:
            cmd.append("--fullscreen")
        if self.ui.always_on_top:
            cmd.append("--always-on-top")
        if self.ui.read_only:
            cmd.append("--no-control")
        if self.ui.turn_screen_off:
            cmd.append("--turn-screen-off")

        if self.ui.perf_overlay:
            cmd.append("--print-fps")

        kwargs = {'stdout': subprocess.PIPE, 'stderr': subprocess.STDOUT, 'text': True, 'bufsize': 1}
        if os.name == 'nt' and not self.ui.program_logs:
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

        if self.log_thread and self.log_thread.isRunning():
            self.log_thread.stop()
            self.log_thread.wait()

        if self.nav_bar:
            self.nav_bar.hide()
            self.nav_bar.deleteLater()
            self.nav_bar = None

        if self.perf_window:
            self.perf_window.hide()
            self.perf_window.deleteLater()
            self.perf_window = None

        if self.ui.nav_bar_enabled:
            self.nav_bar = NavBarWindow(self.send_navigation_command)
            self.nav_bar.drag_started.connect(self.handle_nav_drag_started)
            self.nav_bar.drag_ended.connect(self.handle_nav_drag_ended)
            self.nav_bar.closed.connect(self.handle_nav_closed)

        if self.ui.perf_overlay:
            self.perf_window = PerfWindow()
            self.perf_window.update_perf(bitrate=quality_opt.get("bitrate", "Auto"))

        if self.ui.program_logs:
            title = "Pqscrcpy Logs" if self.ui.language == "EN" else "Pqscrcpy 运行日志"
            self.log_window = LogWindow(title=title)
            self.log_window.show()

        try:
            self.scrcpy_process = subprocess.Popen(cmd, **kwargs)

            self.log_thread = LogReaderThread(self.scrcpy_process)
            self.log_thread.log_signal.connect(self.handle_log_line)
            self.log_thread.start()

            if self.ui.nav_bar_enabled or self.ui.perf_overlay:
                if self.ui.nav_bar_enabled:
                    self.nav_bar.set_orientation(self.ui.nav_bar_position)
                self.tracking_timer.start(30)

        except FileNotFoundError:
            err_en = f"scrcpy executable not found in {scrcpy_dir} directory."
            err_zh = f"在 {scrcpy_dir} 目录中未找到 scrcpy 可执行文件。"
            msg = err_en if self.ui.language == "EN" else err_zh
            QMessageBox.critical(self.ui, "Execution Error" if self.ui.language == "EN" else "执行错误", msg)
        except Exception as e:
            msg = f"Failed to launch Pqscrcpy: {str(e)}" if self.ui.language == "EN" else f"启动 Pqscrcpy 失败: {str(e)}"
            QMessageBox.critical(self.ui, "Execution Error" if self.ui.language == "EN" else "执行错误", msg)

    def run(self):
        self.ui.show()
        return self.app.exec_()


if __name__ == "__main__":
    app = MainApp()
    sys.exit(app.run())