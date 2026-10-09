import os
from PyQt6.QtCore import QThread, pyqtSignal
from data_layer import ImageParser

class ScanWorker(QThread):
    progress_updated = pyqtSignal(int, int) 
    file_processed = pyqtSignal(dict)       
    finished_scan = pyqtSignal()        

    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path
        self._is_running = True  
        self.supported_extensions = ('.jpg', '.jpeg', '.gif', '.tif', '.tiff', '.bmp', '.png', '.pcx')

    def run(self):
        files_to_process = []
        
        for root, _, files in os.walk(self.folder_path):
            if not self._is_running:
                self.finished_scan.emit()
                return 
                
            for file in files:
                if file.lower().endswith(self.supported_extensions):
                    files_to_process.append(os.path.join(root, file))
        
        total_files = len(files_to_process)
        if total_files == 0:
            self.finished_scan.emit()
            return

        for i, filepath in enumerate(files_to_process):
            if not self._is_running:
                break 
                
            info = ImageParser.get_image_info(filepath)
            if self._is_running:
                self.file_processed.emit(info)
                self.progress_updated.emit(i + 1, total_files)

        self.finished_scan.emit()

    def stop(self):
        self._is_running = False
