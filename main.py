import sys
import argparse
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QGuiApplication

from .queue_manager import QueueManager
from .ui import MainDisplayWindow, TellerWindow
from .extensions import ExtensionHooks


def bootstrap_sample_data(qm: QueueManager):
    qm.next_number("Loket 1")
    qm.next_number("Loket 3")
    qm.next_number("Loket 4")
    qm.next_number("Loket 4")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["display", "teller", "both"], default="both")
    p.add_argument("--start-number", type=int, default=1)
    p.add_argument("--no-sample", action="store_true")
    p.add_argument("--screen-index", type=int, default=0)
    p.add_argument("--no-full", action="store_true", help="Jalankan tanpa paksa fullscreen")
    p.add_argument("--no-kiosk", action="store_true", help="Jalankan tidak kiosk (menyisakan frame)")
    p.add_argument("--hide-cursor", action="store_true")
    return p.parse_args()


def main():
    args = parse_args()
    app = QApplication(sys.argv)

    qm = QueueManager(start_number=args.start_number)

    screen_geo = None
    screens = QGuiApplication.screens()
    if 0 <= args.screen_index < len(screens):
        screen_geo = screens[args.screen_index].geometry()
    else:
        print(f"[WARN] screen-index {args.screen_index} invalid, gunakan 0..{len(screens)-1}")

    display = None
    teller = None

    if args.mode in ("display", "both"):
        display = MainDisplayWindow(
            qm,
            force_fullscreen=not args.no_full,
            kiosk=not args.no_kiosk,
            hide_cursor=args.hide_cursor,
            screen_geometry=screen_geo,
        )

    if args.mode in ("teller", "both"):
        teller = TellerWindow(qm, counters=["Loket 1", "Loket 2", "Loket 3", "Loket 4"])
        teller.show()

    ExtensionHooks(qm, enable_logging=True)

    if not args.no_sample:
        bootstrap_sample_data(qm)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()