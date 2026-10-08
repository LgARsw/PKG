import os
from PyQt6.QtCore import QThread, pyqtSignal
from data_layer import ImageParser

class ScanWorker(QThread):
    """Слой бизнес-логики: многопоточный менеджер обхода папок."""
    
    # Сигналы для обновления UI
    progress_updated = pyqtSignal(int, int) # (текущий, всего)
    file_processed = pyqtSignal(dict)       # (словарь с данными)
    finished_scan = pyqtSignal()            # (завершение)

    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path
        self._is_running = True  # Приватный флаг для потокобезопасной остановки
        self.supported_extensions = ('.jpg', '.jpeg', '.gif', '.tif', '.tiff', '.bmp', '.png', '.pcx')

    def run(self):
        """Метод, который выполняется в отдельном потоке."""
        files_to_process = []
        
        # 1. Сбор файлов (проверяем флаг на каждой итерации)
        for root, _, files in os.walk(self.folder_path):
            if not self._is_running:
                self.finished_scan.emit()
                return  # Выходим из потока
                
            for file in files:
                if file.lower().endswith(self.supported_extensions):
                    files_to_process.append(os.path.join(root, file))
        
        total_files = len(files_to_process)
        if total_files == 0:
            self.finished_scan.emit()
            return

        # 2. Обработка файлов (проверяем флаг перед каждым файлом)
        for i, filepath in enumerate(files_to_process):
            if not self._is_running:
                break  # Выходим из цикла
                
            # Парсим файл через Data Layer
            info = ImageParser.get_image_info(filepath)
            
            # Отправляем результат в UI, только если поток еще активен
            if self._is_running:
                self.file_processed.emit(info)
                self.progress_updated.emit(i + 1, total_files)

        self.finished_scan.emit()

    def stop(self):
        """Потокобезопасная остановка."""
        self._is_running = False