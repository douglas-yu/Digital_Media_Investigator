#!/usr/bin/env python3
"""
PixelForce Analyze — Launcher
Checks dependencies and launches the application.
"""
import sys
import subprocess


REQUIRED = {
    "PyQt5": "pyqt5",
    "cv2": "opencv-python",
    "PIL": "Pillow",
    "imagehash": "imagehash",
    "exifread": "exifread",
}


def check_and_install():
    missing = []
    for mod, pkg in REQUIRED.items():
        try:
            __import__(mod)
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"Installing missing packages: {', '.join(missing)}")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--break-system-packages", *missing
        ])


if __name__ == "__main__":
    check_and_install()
    import runpy
    import os
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    runpy.run_path(os.path.join(os.path.dirname(__file__), "main.py"), run_name="__main__")
