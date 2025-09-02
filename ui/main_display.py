from typing import List, Optional
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QSizePolicy,
    QSpacerItem,
)
from PyQt5.QtCore import Qt, QUrl, QTimer, QSize
from PyQt5.QtGui import QPixmap, QCursor
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget

from ..queue_manager import QueueManager
from ..models import CallEntry
from ..widgets.marquee import MarqueeLabel
from ..config import STYLE, LOGO_PATHS, VIDEO_PATH, LOOP_VIDEO


class MainDisplayWindow(QMainWindow):
    """
    Display utama dengan dukungan:
      - Fullscreen / Kiosk (frameless, no menu, no status bar)
      - Dinamis scaling font berdasarkan tinggi layar
      - ESC & F11 handling
    """
    def __init__(
        self,
        queue_manager: QueueManager,
        start_fullscreen: bool = False,
        kiosk: bool = False,
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
        self._scale_factor = 1.0
        self._screen_geometry = screen_geometry  # QScreen.geometry()

        self._prepare_window_flags()
        self._init_ui()
        self.queue_manager.new_call.connect(self.update_display)

        if self.hide_cursor:
            self.setCursor(QCursor(Qt.BlankCursor))

        # Atur posisi/dimensi ke layar target (kiosk)
        if self._screen_geometry:
            geo = self._screen_geometry
            self.setGeometry(geo)
        if start_fullscreen:
            self.showFullScreen()
        elif kiosk:
            # Jika kiosk tanpa fullscreen arg, tetap maximized
            self.showMaximized()

    # ---------- WINDOW FLAGS ----------
    def _prepare_window_flags(self):
        if self.kiosk:
            # Hilangkan frame & judul
            self.setWindowFlag(Qt.FramelessWindowHint, True)
            # Pastikan di atas (opsional)
            self.setWindowFlag(Qt.WindowStaysOnTopHint, False)
        self.setWindowTitle("Display Antrian Loket")

    # ---------- UI ----------
    def _init_ui(self):
        # Hitung scale factor berdasarkan tinggi layar (relative ke 1080)
        if self._screen_geometry:
            h = self._screen_geometry.height()
        else:
            # fallback
            h = self.screen().size().height() if self.screen() else 1080
        self._scale_factor = max(0.6, min(1.6, h / 1080.0))

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout()
        # Kiosk: hilangkan margin & spacing
        if self.kiosk:
            root_layout.setContentsMargins(0, 0, 0, 0)
            root_layout.setSpacing(0)
        else:
            root_layout.setContentsMargins(8, 8, 8, 8)
            root_layout.setSpacing(10)
        central.setLayout(root_layout)

        # TOP
        top_layout = QHBoxLayout()
        if self.kiosk:
            top_layout.setContentsMargins(0, 0, 0, 0)
            top_layout.setSpacing(0)
        logos_container = self._build_logos_section()
        marquee = MarqueeLabel(
            "Selamat datang di Loket Antrian",
            interval_ms=70,
            stylesheet=STYLE["MARQUEE"],
        )
        marquee.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        top_layout.addLayout(logos_container, 1)
        top_layout.addWidget(marquee, 4)

        # MIDDLE
        middle_layout = QHBoxLayout()
        if self.kiosk:
            middle_layout.setContentsMargins(0, 0, 0, 0)
            middle_layout.setSpacing(0)
        video_area = self._build_video_area()
        info_panel = self._build_info_panel()
        middle_layout.addWidget(video_area, 3)
        middle_layout.addWidget(info_panel, 2)

        root_layout.addLayout(top_layout, 1)
        root_layout.addLayout(middle_layout, 7)

        if not self.kiosk:
            # Status bar hanya jika bukan kiosk
            self.statusBar().showMessage("Sistem Antrian Siap")
        else:
            # Sembunyikan menu bar & status bar
            if self.menuBar():
                self.menuBar().hide()

    def _build_logos_section(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(8 if not self.kiosk else 4, 8 if not self.kiosk else 4, 8 if not self.kiosk else 4, 8)
        layout.setSpacing(8 if not self.kiosk else 6)
        for idx in range(2):
            if idx < len(LOGO_PATHS) and LOGO_PATHS[idx].is_file():
                lbl = QLabel()
                pix = QPixmap(str(LOGO_PATHS[idx]))
                if not pix.isNull():
                    target_w = int(220 * self._scale_factor)
                    target_h = int(90 * self._scale_factor)
                    lbl.setPixmap(pix.scaled(target_w, target_h, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                else:
                    lbl.setText("LOGO ERR")
                    lbl.setAlignment(Qt.AlignCenter)
                lbl.setStyleSheet("background-color:#0C4A3F; border-radius:6px;")
            else:
                lbl = self._create_logo_placeholder(f"LOGO {idx+1}")
            layout.addWidget(lbl)
        layout.addStretch()
        return layout

    def _create_logo_placeholder(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignCenter)
        base_style = STYLE["LOGO_PLACEHOLDER"]
        # Sesuaikan font-size relatif
        lbl.setStyleSheet(base_style.replace("font-size:16px", f"font-size:{int(16*self._scale_factor)}px"))
        lbl.setMinimumHeight(int(80 * self._scale_factor))
        return lbl

    def _build_video_area(self) -> QWidget:
        if VIDEO_PATH.is_file():
            container = QFrame()
            v_layout = QVBoxLayout(container)
            v_layout.setContentsMargins(0, 0, 0, 0)
            self._video_widget = QVideoWidget()
            self._video_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
            self._video_player.setVideoOutput(self._video_widget)
            self._video_player.setMedia(QMediaContent(QUrl.fromLocalFile(str(VIDEO_PATH))))
            self._video_player.play()
            if LOOP_VIDEO:
                self._video_player.mediaStatusChanged.connect(self._loop_video)
            v_layout.addWidget(self._video_widget)
            return container
        else:
            lbl = QLabel("AREA VIDEO")
            lbl.setAlignment(Qt.AlignCenter)
            style = STYLE["VIDEO_PLACEHOLDER"]
            lbl.setStyleSheet(style.replace("font-size:26px", f"font-size:{int(26*self._scale_factor)}px"))
            lbl.setMinimumSize(int(500 * self._scale_factor), int(350 * self._scale_factor))
            lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            return lbl

    def _loop_video(self, status):
        if status == QMediaPlayer.EndOfMedia and self._video_player:
            self._video_player.setPosition(0)
            self._video_player.play()

    def _build_info_panel(self) -> QWidget:
        container = QFrame()
        container.setFrameShape(QFrame.StyledPanel)
        container.setStyleSheet(STYLE["BACKGROUND_PANEL"])
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10 if not self.kiosk else 6, 10 if not self.kiosk else 6, 10 if not self.kiosk else 6, 10)
        layout.setSpacing(6 if not self.kiosk else 4)

        title = QLabel("INFORMASI ANTRIAN")
        title.setAlignment(Qt.AlignCenter)
        title_font_size = int(22 * self._scale_factor)
        title.setStyleSheet(f"color:#F8FAFC; font-size:{title_font_size}px; font-weight:800; letter-spacing:2px;")
        layout.addWidget(title)

        history_title = QLabel("3 Nomor Terakhir")
        hist_font = int(15 * self._scale_factor)
        history_title.setStyleSheet(f"color:#CBD5E1; font-size:{hist_font}px; font-weight:bold; margin-top:4px;")
        layout.addWidget(history_title)

        for _ in range(3):
            h_lbl = QLabel("-")
            base_hist_style = STYLE["HISTORY_ITEM"]
            # Ganti font-size di style
            h_lbl.setStyleSheet(base_hist_style.replace("font-size:16px", f"font-size:{int(16*self._scale_factor)}px"))
            self.history_labels.append(h_lbl)
            layout.addWidget(h_lbl)

        layout.addItem(QSpacerItem(10, 15, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.current_number_label = QLabel("--")
        self.current_number_label.setAlignment(Qt.AlignCenter)
        num_font = int(90 * self._scale_factor)
        self.current_number_label.setStyleSheet(STYLE["CURRENT_NUMBER"] + f" font-size:{num_font}px;")
        self.current_number_label.setMinimumHeight(int(160 * self._scale_factor))
        layout.addWidget(self.current_number_label)

        self.current_counter_label = QLabel("Ke Loket -")
        self.current_counter_label.setAlignment(Qt.AlignCenter)
        counter_font = int(32 * self._scale_factor)
        self.current_counter_label.setStyleSheet(STYLE["CURRENT_COUNTER"] + f" font-size:{counter_font}px;")
        layout.addWidget(self.current_counter_label)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color:#1E293B;")
        layout.addWidget(sep)

        footer = QLabel("© Sistem Antrian Modular")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet(f"color:#64748B; font-size:{int(12*self._scale_factor)}px;")
        layout.addWidget(footer)

        return container

    # ---------- UPDATE ----------
    def update_display(self, entry: CallEntry):
        self.current_number_label.setText(str(entry.number))
        self.current_counter_label.setText(f"Ke {entry.counter}")
        history = self.queue_manager.last_history(3)
        for idx, lbl in enumerate(self.history_labels):
            if idx < len(history):
                h = history[idx]
                lbl.setText(f"Nomor {h.number} {h.counter}")
            else:
                lbl.setText("-")

    # ---------- INPUT ----------
    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_F11:
            self._toggle_fullscreen()
            return
        if key == Qt.Key_Escape:
            # Shift+ESC langsung tutup
            if event.modifiers() & Qt.ShiftModifier:
                self.close()
                return
            if self.isFullScreen():
                # Keluar fullscreen tapi tetap terbuka
                self.showNormal()
            else:
                self.close()
            return
        super().keyPressEvent(event)

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()