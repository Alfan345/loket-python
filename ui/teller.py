from typing import List
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QHBoxLayout,
    QFrame,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QShortcut
from PyQt5.QtGui import QKeySequence

from ..queue_manager import QueueManager
from ..models import CallEntry
from ..config import STYLE


class TellerWindow(QWidget):
    """
    Teller UI lebih menarik:
    - Panel dengan styling
    - Tombol besar
    - Preview nomor berikutnya (estimasi)
    - Shortcut: Enter / Space -> Next
    """
    def __init__(self, queue_manager: QueueManager, counters: List[str]):
        super().__init__()
        self.queue_manager = queue_manager
        self.counters = counters
        self.setWindowTitle("Teller - Pemanggilan Antrian")
        self.setMinimumSize(420, 360)

        self.last_called_label: QLabel
        self.next_preview_label: QLabel

        self._init_ui()
        self.queue_manager.new_call.connect(self._on_new_call)
        self._update_next_preview()

        # Shortcuts
        QShortcut(QKeySequence(Qt.Key_Return), self, activated=self._handle_next)
        QShortcut(QKeySequence(Qt.Key_Enter), self, activated=self._handle_next)
        QShortcut(QKeySequence(Qt.Key_Space), self, activated=self._handle_next)

    def _init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 14, 14, 14)

        panel = QFrame()
        panel.setStyleSheet(STYLE["TELLER_PANEL"])
        panel_layout = QVBoxLayout(panel)
        panel_layout.setSpacing(14)

        title = QLabel("Panel Petugas Loket")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(STYLE["TELLER_TITLE"])
        panel_layout.addWidget(title)

        loc_label = QLabel("Pilih Loket:")
        loc_label.setStyleSheet(STYLE["TELLER_LABEL"])
        panel_layout.addWidget(loc_label)

        self.counter_combo = QComboBox()
        self.counter_combo.addItems(self.counters)
        self.counter_combo.setStyleSheet(STYLE["TELLER_COMBO"])
        panel_layout.addWidget(self.counter_combo)

        self.next_button = QPushButton("PANGGIL NEXT")
        self.next_button.setStyleSheet(STYLE["TELLER_NEXT_BTN"])
        self.next_button.setCursor(Qt.PointingHandCursor)
        self.next_button.clicked.connect(self._handle_next)
        self.next_button.setMinimumHeight(90)
        panel_layout.addWidget(self.next_button)

        self.last_called_label = QLabel("Nomor Terakhir: -")
        self.last_called_label.setAlignment(Qt.AlignCenter)
        self.last_called_label.setStyleSheet(STYLE["TELLER_LAST"])
        panel_layout.addWidget(self.last_called_label)

        self.next_preview_label = QLabel("Nomor Berikutnya: 1")
        self.next_preview_label.setAlignment(Qt.AlignCenter)
        self.next_preview_label.setStyleSheet("font-size:16px; color:#A5B4FC; font-weight:600;")
        panel_layout.addWidget(self.next_preview_label)

        hint = QLabel("Shortcut: ENTER / SPACE untuk Next")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("color:#64748B; font-size:12px;")
        panel_layout.addWidget(hint)

        outer.addWidget(panel)

    def _update_next_preview(self):
        current = self.queue_manager.current()
        next_number = (current.number + 1) if current else 1
        self.next_preview_label.setText(f"Nomor Berikutnya: {next_number}")

    def _handle_next(self):
        selected_counter = self.counter_combo.currentText()
        entry = self.queue_manager.next_number(selected_counter)
        self.last_called_label.setText(f"Nomor Terakhir: {entry.number} ({entry.counter})")
        QTimer.singleShot(50, self._update_next_preview)  # update preview setelah emit

    def _on_new_call(self, entry: CallEntry):
        self.last_called_label.setText(f"Nomor Terakhir: {entry.number} ({entry.counter})")
        self._update_next_preview()