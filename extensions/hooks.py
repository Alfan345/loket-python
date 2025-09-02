import threading
from typing import Optional
from PyQt5.QtCore import QTimer, QObject
from PyQt5.QtMultimedia import QSoundEffect
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QApplication

from ..queue_manager import QueueManager
from ..models import CallEntry
from ..config import ENABLE_TTS, ENABLE_CHIME, CHIME_PATH, TTS_QUEUE_DELAY_MS


class ExtensionHooks(QObject):
    """
    Menangani integrasi eksternal:
    - Logging
    - Chime
    - TTS (pyttsx3)
    Dijalankan non-blok agar UI tidak freeze.
    """
    def __init__(self, queue_manager: QueueManager, enable_logging: bool = True, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.queue_manager = queue_manager
        self.enable_logging = enable_logging

        # Audio chime
        self._chime_effect: Optional[QSoundEffect] = None
        if ENABLE_CHIME:
            self._prepare_chime()

        self.queue_manager.new_call.connect(self._handle_new_call)

    # ---------- SIGNAL HANDLER ----------
    def _handle_new_call(self, entry: CallEntry):
        if self.enable_logging:
            self._log_call(entry)
        if ENABLE_CHIME:
            self._play_chime()
        if ENABLE_TTS:
            # beri jeda agar chime selesai dulu
            QTimer.singleShot(TTS_QUEUE_DELAY_MS, lambda e=entry: self.speak_call(e))

    # ---------- LOG ----------
    def _log_call(self, entry: CallEntry):
        print(f"[LOG] Dipanggil: Nomor {entry.number} -> {entry.counter}")

    # ---------- CHIME ----------
    def _prepare_chime(self):
        if CHIME_PATH.is_file():
            self._chime_effect = QSoundEffect()
            self._chime_effect.setSource(QUrl.fromLocalFile(str(CHIME_PATH)))
            self._chime_effect.setVolume(0.9)
        else:
            self._chime_effect = None

    def _play_chime(self):
        if self._chime_effect:
            self._chime_effect.play()
        else:
            QApplication.beep()

    # ---------- TTS ----------
    def speak_call(self, entry: CallEntry):
        def _run():
            try:
                import pyttsx3
                engine = pyttsx3.init()
                # Atur suara / kecepatan (opsional)
                rate = engine.getProperty("rate")
                engine.setProperty("rate", rate - 20)
                engine.say(f"Nomor antrian {entry.number}, menuju {entry.counter}")
                engine.runAndWait()
                engine.stop()
            except Exception as e:
                print(f"[TTS ERROR] {e}")

        threading.Thread(target=_run, daemon=True).start()