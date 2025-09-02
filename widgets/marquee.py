from typing import Optional
from PyQt5.QtWidgets import QLabel, QWidget
from PyQt5.QtCore import Qt, QTimer


class MarqueeLabel(QLabel):
    def __init__(self, text: str, interval_ms: int = 100, parent: Optional[QWidget] = None, stylesheet: str = ""):
        super().__init__(parent)
        self.original_text = f"   {text}   "
        self.display_text = self.original_text
        self.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        if stylesheet:
            self.setStyleSheet(stylesheet)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._scroll_text)
        self.timer.start(interval_ms)
        self.setText(self.display_text)

    def _scroll_text(self):
        if self.display_text:
            self.display_text = self.display_text[1:] + self.display_text[0]
            self.setText(self.display_text)

    def setMarqueeText(self, text: str):
        self.original_text = f"   {text}   "
        self.display_text = self.original_text
        self.setText(self.display_text)