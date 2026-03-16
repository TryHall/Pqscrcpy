import subprocess
import os


class AdbManager:
    def __init__(self):
        # 确保使用绝对路径或正确的相对路径指向提取后的 adb.exe
        self.adb_path = os.path.join(os.getcwd(), "scrcpy", "adb.exe")

    def _run_adb_cmd(self, cmd_list):
        """统一封装的底层命令行执行方法，彻底解决黑框和阻塞乱象"""
        kwargs = {
            'stdout': subprocess.PIPE,
            'stderr': subprocess.PIPE,
            'text': True
        }

        # 核心修复：针对 Windows 系统隐藏控制台黑框
        if os.name == 'nt':
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

        try:
            # 增加 timeout 防止死锁阻塞 GUI 线程
            result = subprocess.run([self.adb_path] + cmd_list, timeout=3, **kwargs)
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            return ""
        except Exception as e:
            print(f"ADB Error: {e}")
            return ""

    def get_connected_devices(self):
        output = self._run_adb_cmd(["devices"])
        devices = []
        if output:
            lines = output.split('\n')
            for line in lines[1:]:
                if '\tdevice' in line:
                    devices.append(line.split('\t')[0])
        return devices

    # 其他 adb 命令（如发送按键、切换无线等）也必须全部通过 _run_adb_cmd 调用