"""
Gerenciador de Dispositivos (ADB)
---------------------------------
Responsável por detectar, conectar e operar dispositivos Android
(físicos, emulados ou "cloud phones") para fins de teste de QA.

Escopo: automação restrita ao app sob teste (definido em cada Flow).
Não implementa nem expõe primitivas de interação com apps de terceiros
fora do que o próprio usuário definir como alvo de teste.
"""
import subprocess
import shlex
from dataclasses import dataclass
from typing import List


@dataclass
class Device:
    serial: str
    model: str
    android_version: str
    state: str  # "device", "offline", "unauthorized"


class ADBError(RuntimeError):
    pass


def _run(cmd: str, timeout: int = 30) -> str:
    try:
        result = subprocess.run(
            shlex.split(cmd),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        raise ADBError("adb não encontrado no PATH. Instale o Android SDK Platform-Tools.")
    except subprocess.TimeoutExpired:
        raise ADBError(f"Comando expirou: {cmd}")
    if result.returncode != 0 and "error" in result.stderr.lower():
        raise ADBError(result.stderr.strip())
    return result.stdout.strip()


class DeviceManager:
    def list_devices(self) -> List[Device]:
        out = _run("adb devices -l")
        devices = []
        for line in out.splitlines()[1:]:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            serial = parts[0]
            state = parts[1] if len(parts) > 1 else "unknown"
            model = "desconhecido"
            for token in parts:
                if token.startswith("model:"):
                    model = token.split(":", 1)[1]
            android_version = self._get_prop(serial, "ro.build.version.release") if state == "device" else "?"
            devices.append(Device(serial=serial, model=model, android_version=android_version, state=state))
        return devices

    def _get_prop(self, serial: str, prop: str) -> str:
        try:
            return _run(f"adb -s {serial} shell getprop {prop}")
        except ADBError:
            return "?"

    def connect_network_device(self, host: str, port: int = 5555) -> str:
        return _run(f"adb connect {host}:{port}")

    def disconnect(self, serial: str) -> str:
        return _run(f"adb disconnect {serial}")

    def install_apk(self, serial: str, apk_path: str) -> str:
        return _run(f"adb -s {serial} install -r {apk_path}", timeout=120)

    def screenshot(self, serial: str, out_path: str) -> str:
        remote = "/sdcard/_qa_screen.png"
        _run(f"adb -s {serial} shell screencap -p {remote}")
        _run(f"adb -s {serial} pull {remote} {out_path}", timeout=60)
        return out_path

    def tap(self, serial: str, x: int, y: int) -> None:
        _run(f"adb -s {serial} shell input tap {x} {y}")

    def swipe(self, serial: str, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> None:
        _run(f"adb -s {serial} shell input swipe {x1} {y1} {x2} {y2} {duration_ms}")

    def input_text(self, serial: str, text: str) -> None:
        escaped = text.replace(" ", "%s")
        _run(f"adb -s {serial} shell input text {escaped}")

    def open_app(self, serial: str, package: str, activity: str = None) -> None:
        target = f"{package}/{activity}" if activity else package
        if activity:
            _run(f"adb -s {serial} shell am start -n {target}")
        else:
            _run(f"adb -s {serial} shell monkey -p {package} -c android.intent.category.LAUNCHER 1")

    def clear_app_cache(self, serial: str, package: str) -> None:
        _run(f"adb -s {serial} shell pm clear {package}")

    def reboot(self, serial: str) -> None:
        _run(f"adb -s {serial} reboot")
