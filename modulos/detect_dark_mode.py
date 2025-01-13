import platform

def detect_dark_mode():
    system = platform.system()
    if system == "Windows":
        try:
            import winreg
            registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
            key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return value == 0
        except Exception:
            return False
    elif system == "Linux":
        try:
            import subprocess
            result = subprocess.run(['gsettings', 'get', 'org.gnome.desktop.interface', 'gtk-theme'], stdout=subprocess.PIPE)
            theme = result.stdout.decode().strip().strip("'")
            return "dark" in theme.lower()
        except Exception:
            return False
    else:
        return False