from typing import List, Optional
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QFrame, QSizePolicy, QSpacerItem
)
from PyQt5.QtCore import Qt, QUrl, QTimer
from PyQt5.QtGui import QPixmap, QCursor
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget

from ..queue_manager import QueueManager
from ..models import CallEntry
from ..widgets.marquee import MarqueeLabel
from ..config import STYLE, LOGO_PATHS, VIDEO_PATH, LOOP_VIDEO

# (Opsional) aktifkan kalau mau paksa topmost via Win32 (install: pip install pywin32)
ENABLE_FORCE_TOPMOST = False
try:
    import win32gui, win32con  # type: ignore
except Exception:
    ENABLE_FORCE_TOPMOST = False


class MainDisplayWindow(QMainWindow):
    """
    Display utama Fullscreen / Kiosk.
    - Frameless
    - Zero margin
    - ESC pertama -> keluar fullscreen (jika mau), ESC kedua -> exit (atau Shift+ESC langsung exit)
    - F11 toggle
    - Re-apply fullscreen beberapa kali untuk mengatasi taskbar bandel.
    """
    def __init__(
        self,
        queue_manager: QueueManager,
        force_fullscreen: bool = True,
        kiosk: bool = True,
        hide_cursor: bool = False,
        screen_geometry=None,
    ):
        super().__init__()
        self.queue_manager = queue_manager
        self.kiosk = kiosk
        self.hide_cursor = hide_cursor
        self.history_labels: List[QLabel] = []
        self.current_number_label: QLabel
        self.current_counter_label: QLabel
        self._video_player: Optional[QMediaPlayer] = None
        self._video_widget: Optional[QVideoWidget] = None
        self._screen_geometry = screen_geometry

        self._apply_window_flags()
        self._build_ui()

        self.queue_manager.new_call.connect(self.update_display)

        if self.hide_cursor:
            self.setCursor(QCursor(Qt.BlankCursor))

        # Atur posisi di layar target
        if self._screen_geometry:
            self.setGeometry(self._screen_geometry)

        if force_fullscreen:
            # Lakukan beberapa kali agar taskbar lenyap
            self._enter_fullscreen_reliably()
        else:
            self.show()

    # ---------------- WINDOW FLAGS ----------------
    def _apply_window_flags(self):
        # Hilangkan frame & title
        self.setWindowFlag(Qt.FramelessWindowHint, True)
        # (Opsional) topmost
        # self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.setAttribute(Qt.WA_NoSystemBackground, False)
        self.setAttribute(Qt.WA_TranslucentBackground, False)

    def _enter_fullscreen_reliably(self):
        # 1) showFullScreen awal
        self.showFullScreen()
        # 2) Pastikan raise
        self.raise_()
        self.activateWindow()

        # 3) Re-apply setelah event loop mulai
        QTimer.singleShot(0, self._reassert_fullscreen)
        # 4) Re-apply lagi setelah 200ms (beberapa kasus Windows 11)
        QTimer.singleShot(200, self._reassert_fullscreen)
        # 5) (Opsional) Paksa topmost
        if ENABLE_FORCE_TOPMOST:
            QTimer.singleShot(250, self._force_topmost)

    def _reassert_fullscreen(self):
        if not self.isFullScreen():
            self.showFullScreen()
        self.raise_()
        self.activateWindow()

    def _force_topmost(self):
        try:
            hwnd = int(self.winId())
            win32gui.SetWindowPos(
                hwnd,
                win32con.HWND_TOPMOST,
                0, 0, 0, 0,
                win32con.SWP_NOMOVE
                | win32con.SWP_NOSIZE
                | win32con.SWP_NOACTIVATE
                | win32con.SWP_SHOWWINDOW
            )
        except Exception:
            pass

    # ---------------- BUILD UI ----------------
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        # Zero margin untuk benar-benar penuh
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(0)

        logos_container = self._build_logos()
        marquee = MarqueeLabel("Selamat datang di Loket Antrian", interval_ms=70, stylesheet=STYLE["MARQUEE"])
        marquee.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        top_layout.addLayout(logos_container, 1)
        top_layout.addWidget(marquee, 4)

        middle_layout = QHBoxLayout()
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.setSpacing(0)
        video_area = self._build_video()
        info_panel = self._build_info_panel()
        middle_layout.addWidget(video_area, 3)
        middle_layout.addWidget(info_panel, 2)

        root.addLayout(top_layout, 1)
        root.addLayout(middle_layout, 8)

        # Jangan tampilkan menu / status bar sama sekali (kiosk)
        if self.menuBar():
            self.menuBar().hide()
        if self.statusBar():
            self.statusBar().hide()

    def _build_logos(self):
        lay = QVBoxLayout()
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(8)
        for i in range(2):
            if i < len(LOGO_PATHS) and LOGO_PATHS[i].is_file():
                lbl = QLabel()
                pix = QPixmap(str(LOGO_PATHS[i]))
                if not pix.isNull():
                    lbl.setPixmap(pix.scaled(220, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                else:
                    lbl.setText("LOGO ERR")
                    lbl.setAlignment(Qt.AlignCenter)
                lbl.setStyleSheet("background-color:#0C4A3F; border-radius:6px;")
            else:
                lbl = QLabel(f"LOGO {i+1}")
                lbl.setAlignment(Qt.AlignCenter)
                lbl.setStyleSheet(STYLE["LOGO_PLACEHOLDER"])
                lbl.setMinimumHeight(80)
            lay.addWidget(lbl)
        lay.addStretch()
        return lay

    def _build_video(self):
        if VIDEO_PATH.is_file():
            container = QFrame()
            v = QVBoxLayout(container)
            v.setContentsMargins(0, 0, 0, 0)
            self._video_widget = QVideoWidget()
            self._video_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
            self._video_player.setVideoOutput(self._video_widget)
            self._video_player.setMedia(QMediaContent(QUrl.fromLocalFile(str(VIDEO_PATH))))
            self._video_player.play()
            if LOOP_VIDEO:
                self._video_player.mediaStatusChanged.connect(self._loop_video)
            v.addWidget(self._video_widget)
            return container
        else:
            lbl = QLabel("AREA VIDEO")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(STYLE["VIDEO_PLACEHOLDER"])
            lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            return lbl

    def _loop_video(self, status):
        if status == QMediaPlayer.EndOfMedia and self._video_player:
            self._video_player.setPosition(0)
            self._video_player.play()

    def _build_info_panel(self):
        container = QFrame()
        container.setStyleSheet(STYLE["BACKGROUND_PANEL"])
        lay = QVBoxLayout(container)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(6)

        title = QLabel("INFORMASI ANTRIAN")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color:#F8FAFC; font-size:28px; font-weight:800; letter-spacing:2px;")
        lay.addWidget(title)

        hist_title = QLabel("3 Nomor Terakhir")
        hist_title.setStyleSheet("color:#CBD5E1; font-size:16px; font-weight:bold;")
        lay.addWidget(hist_title)

        for _ in range(3):
            h = QLabel("-")
            h.setStyleSheet(STYLE["HISTORY_ITEM"])
            self.history_labels.append(h)
            lay.addWidget(h)

        lay.addItem(QSpacerItem(10, 15, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.current_number_label = QLabel("--")
        self.current_number_label.setAlignment(Qt.AlignCenter)
        self.current_number_label.setStyleSheet(STYLE["CURRENT_NUMBER"] + "font-size:130px;")
        self.current_number_label.setMinimumHeight(200)
        lay.addWidget(self.current_number_label)

        self.current_counter_label = QLabel("Ke Loket -")
        self.current_counter_label.setAlignment(Qt.AlignCenter)
        self.current_counter_label.setStyleSheet(STYLE["CURRENT_COUNTER"] + "font-size:48px;")
        lay.addWidget(self.current_counter_label)

        foot = QLabel("© Sistem Antrian Modular")
        foot.setAlignment(Qt.AlignCenter)
        foot.setStyleSheet("color:#64748B; font-size:14px;")
        lay.addWidget(foot)

        return container

    # ---------------- UPDATE ----------------
    def update_display(self, entry: CallEntry):
        self.current_number_label.setText(str(entry.number))
        self.current_counter_label.setText(f"Ke {entry.counter}")
        history = self.queue_manager.last_history(3)
        for i, lbl in enumerate(self.history_labels):
            if i < len(history):
                h = history[i]
                lbl.setText(f"Nomor {h.number} {h.counter}")
            else:
                lbl.setText("-")

    # ---------------- KEYS ----------------
    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            # ESC pertama keluar fullscreen (kalau mau tetap running), ESC kedua tutup
            if self.isFullScreen():
                self.showNormal()
            else:
                self.close()
            return
        if e.key() == Qt.Key_F11:
            if self.isFullScreen():
                self.showNormal()
            else:
                self._enter_fullscreen_reliably()
            return
        super().keyPressEvent(e)