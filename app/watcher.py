import time

from PyQt6.QtCore import QThread, pyqtSignal
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class ProjectFolderWatcher(QThread):
    file_changed = pyqtSignal()

    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path
        self.event_handler = FileSystemEventHandler()
        self.event_handler.on_any_event = self.on_any_event
        self.observer = Observer()

    def on_any_event(self, event):
        self.file_changed.emit()

    def run(self):
        self.observer.schedule(self.event_handler,
                               self.folder_path,
                               recursive=True)
        self.observer.start()
        try:
            while not self.isInterruptionRequested():
                time.sleep(1)
        finally:
            self.observer.stop()
            self.observer.join()

    def stop(self):
        self.requestInterruption()
        self.wait()
