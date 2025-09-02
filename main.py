"""
main.py (DIPERBARUI)
Argumen baru:
  --mode (display|teller|both)
  --fullscreen
  --kiosk (frameless, no menu, no status bar, margin 0)
  --hide-cursor (hanya efektif di kiosk)
  --screen-index N (pilih monitor ke-N, mulai 0)
  --no-sample
  --start-number N
Contoh:
  python -m queue_app.main --mode display --kiosk --fullscreen --screen-index 1
"""

import sys
import argparse
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QGuiApplication
from .queue_manager import QueueManager
from .ui import MainDisplayWindow, TellerWindow
from .extensions import ExtensionHooks
from .config import KIOSK_HIDE_CURSOR_DEFAULT


def bootstrap_sample_data(queue_manager: QueueManager):
    queue_manager.next_number("Loket 1")
    queue_manager.next_number("Loket 3")
    queue_manager.next_number("Loket 4")
    queue_manager.next_number("Loket 4")


def parse_args():
    parser = argparse.ArgumentParser(description="Sistem Antrian Loket Modular")
    parser.add_argument("--mode", choices=["display", "teller", "both"], default="both", help="Jalankan komponen apa")
    parser.add_argument("--fullscreen", action="store_true", help="Mulai display dalam fullscreen")
    parser.add_argument("--kiosk", action="store_true", help="Kiosk mode (frameless, no menu/status bar, margin0)")
    parser.add_argument("--hide-cursor", action="store_true", help="Sembunyikan kursor (disarankan untuk kiosk)")
    parser.add_argument("--screen-index", type=int, default=0, help="Index monitor untuk display (0 = primary)")
    parser.add_argument("--no-sample", action="store_true", help="Tanpa data contoh")
    parser.add_argument("--start-number", type=int, default=1, help="Nomor awal antrian")
    return parser.parse_args()


def main():
    args = parse_args()
    app = QApplication(sys.argv)

    queue_manager = QueueManager(start_number=args.start_number)

    display = None
    teller = None

    screen_geo = None
    screens = QGuiApplication.screens()
    if 0 <= args.screen_index < len(screens):
        screen_geo = screens[args.screen_index].geometry()
    else:
        print(f"[WARN] screen-index {args.screen_index} tidak valid. Gunakan 0..{len(screens)-1}")

    if args.mode in ("display", "both"):
        display = MainDisplayWindow(
            queue_manager,
            start_fullscreen=args.fullscreen or args.kiosk,
            kiosk=args.kiosk,
            hide_cursor=args.hide_cursor or (args.kiosk and KIOSK_HIDE_CURSOR_DEFAULT),
            screen_geometry=screen_geo,
        )
        display.show()

    if args.mode in ("teller", "both"):
        teller = TellerWindow(queue_manager, counters=["Loket 1", "Loket 2", "Loket 3", "Loket 4"])
        teller.show()

    ExtensionHooks(queue_manager, enable_logging=True)

    if not args.no_sample:
        bootstrap_sample_data(queue_manager)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()