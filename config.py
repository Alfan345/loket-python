"""
config.py (DITAMBAH beberapa opsi kiosk)
"""
from pathlib import Path

ASSETS_DIR = Path("assets")

LOGO_PATHS = [
    ASSETS_DIR / "logo1.png",
    ASSETS_DIR / "logo2.png",
]

VIDEO_PATH = ASSETS_DIR / "sample.mp4"
CHIME_PATH = ASSETS_DIR / "chime.wav"

ENABLE_TTS = True
ENABLE_CHIME = True
TTS_QUEUE_DELAY_MS = 300
LOOP_VIDEO = True

# Kiosk defaults (bisa dioverride via argument)
KIOSK_HIDE_CURSOR_DEFAULT = False

STYLE = {
    "BACKGROUND_PANEL": "background-color:#0F172A; border:2px solid #1E293B; border-radius:8px;",
    "CURRENT_NUMBER": "color:#FACC15; font-weight:900;",  # ukuran akan diatur dinamis
    "CURRENT_COUNTER": "color:#38BDF8; font-weight:bold;",  # ukuran dinamis
    "HISTORY_ITEM": "color:#E2E8F0; font-size:16px;",
    "LOGO_PLACEHOLDER": (
        "background-color:#10B981; color:white; font-weight:bold; font-size:16px;"
        "border-radius:6px; padding:10px;"
    ),
    "VIDEO_PLACEHOLDER": "background-color:#1E3A8A; color:white; font-size:26px;",
    "TELLER_PANEL": "background-color:#0F172A; border:1px solid #334155; border-radius:10px; padding:18px;",
    "TELLER_TITLE": "font-size:22px; font-weight:700; color:#F1F5F9;",
    "TELLER_LABEL": "font-size:14px; color:#94A3B8;",
    "TELLER_LAST": "font-size:18px; font-weight:600; color:#F8FAFC;",
    "TELLER_NEXT_BTN": (
        "font-size:26px; font-weight:700; background: qlineargradient("
        "x1:0 y1:0, x2:1 y2:1, stop:0 #2563EB, stop:1 #1D4ED8);"
        "color:white; padding:18px; border:none; border-radius:12px;"
    ),
    "TELLER_NEXT_BTN_HOVER": "background-color:#1E40AF;",
    "TELLER_COMBO": (
        "font-size:16px; padding:6px 10px; background-color:#1E293B; color:#E2E8F0;"
        "border:1px solid #334155; border-radius:6px;"
    ),
    "MARQUEE": "color:white; font-size:20px; background-color:#222; padding:8px;"
}