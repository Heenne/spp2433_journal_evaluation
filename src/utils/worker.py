from PyQt6.QtCore import QThread, pyqtSignal

class WorkerThread(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self._is_cancelled = False
        
    def cancel(self):
        self._is_cancelled = True
        
    def is_cancelled(self):
        return self._is_cancelled
        
    def run(self):
        try:
            if self.kwargs.pop("inject_progress", False):
                self.kwargs["progress_callback"] = self.progress.emit
                
            if self.kwargs.pop("inject_cancelled", False):
                self.kwargs["is_cancelled_callback"] = self.is_cancelled
                
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error.emit(str(e))
