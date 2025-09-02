# (tidak berubah besar, hanya komentar ekstra opsional)
from typing import List, Optional
from PyQt5.QtCore import QObject, pyqtSignal
from .models import CallEntry


class QueueManager(QObject):
    new_call = pyqtSignal(CallEntry)

    def __init__(self, start_number: int = 1, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._current_number = start_number - 1
        self._calls: List[CallEntry] = []

    def next_number(self, counter: str) -> CallEntry:
        self._current_number += 1
        entry = CallEntry(number=self._current_number, counter=counter)
        self._calls.append(entry)
        self.new_call.emit(entry)
        return entry

    def current(self) -> Optional[CallEntry]:
        return self._calls[-1] if self._calls else None

    def last_history(self, n: int) -> List[CallEntry]:
        if not self._calls:
            return []
        subset = self._calls[:-1]
        return subset[-n:] if len(subset) >= n else subset

    def reset(self):
        self._current_number = 0
        self._calls.clear()