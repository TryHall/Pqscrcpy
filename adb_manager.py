import subprocess
import re
import os


class AdbManager:
    def __init__(self):
        self.adb_path = os.path.join("scrcpy", "adb.exe")

    def run_cmd(self, cmd):
        try:
            result = subprocess.run([self.adb_path] + cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return None

    def get_connected_devices(self):
        output = self.run_cmd(["devices"])
        if not output: return []
        devices = []
        for line in output.split('\n')[1:]:
            if '\t' in line:
                serial, state = line.split('\t')
                if state == 'device':
                    devices.append(serial)
        return devices

    def switch_to_wireless(self, serial):
        if re.match(r"^\d{1,3}(\.\d{1,3}){3}:\d+$", serial):
            return serial

        self.run_cmd(["-s", serial, "tcpip", "5555"])

        ip_output = self.run_cmd(["-s", serial, "shell", "ip", "route"])
        if ip_output:
            match = re.search(r"src (\d{1,3}(?:\.\d{1,3}){3})", ip_output)
            if match:
                ip = match.group(1)
                self.run_cmd(["connect", f"{ip}:5555"])
                return f"{ip}:5555"
        return None

    def send_keyevent(self, serial, keycode):
        self.run_cmd(["-s", serial, "shell", "input", "keyevent", str(keycode)])