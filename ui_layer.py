import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QProgressBar, 
                             QTableWidget, QTableWidgetItem, QFileDialog,
                             QMessageBox, QHeaderView)
from PyQt6.QtCore import Qt, QTimer
from core_layer import ScanWorker

class ImageAnalyzerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Metadata Analyzer (Lab 2 - PyQt)")
        self.resize(1200, 600)
        
        self.worker = None
        self._setup_ui()

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Верхняя панель ---
        top_layout = QHBoxLayout()
        self.btn_select = QPushButton("Выбрать папку")
        self.btn_select.clicked.connect(self.select_folder)
        
        self.lbl_path = QLabel("Папка не выбрана")
        self.lbl_path.setStyleSheet("color: gray;")
        
        self.btn_help = QPushButton("Справка")
        self.btn_help.clicked.connect(self.show_help)
        
        self.btn_stop = QPushButton("Стоп")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_scan)

        top_layout.addWidget(self.btn_select)
        top_layout.addWidget(self.lbl_path, stretch=1)
        top_layout.addWidget(self.btn_help)
        top_layout.addWidget(self.btn_stop)
        main_layout.addLayout(top_layout)

        # --- Прогресс-бар ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        # --- Таблица ---
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Имя файла", "Формат", "Размер (px)", "Разрешение (DPI)", "Глубина цвета", "Сжатие"
        ])
        
        # --- СТАТИЧЕСКАЯ НАСТРОЙКА ШИРИНЫ КОЛОНОК ---
        header = self.table.horizontalHeader()
        
        # 1. "Имя файла" — растягивается на свободное место (но не бесконечно)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        
        # 2. Остальные колонки — фиксированная ширина
        fixed_widths = {
            1: 90,   # Формат (JPEG, PNG, BMP)
            2: 120,  # Размер (например, 1920x1080)
            3: 150,  # DPI (например, 72x72 (default))
            4: 210,  # Глубина цвета (32 bit (True Color + Alpha))
            5: 170,  # Сжатие (Lossless / None)
        }
        
        for col, width in fixed_widths.items():
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)
            self.table.setColumnWidth(col, width)
        
        # 3. Задаем минимальную ширину для "Имя файла", чтобы не сжималась слишком сильно
        self.table.setColumnWidth(0, 350)
        
        # 4. Отключаем растягивание последней колонки
        header.setStretchLastSection(False)
        
        # 5. Запрет редактирования и чередование цветов
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        
        main_layout.addWidget(self.table)

    def show_help(self):
        help_text = (
            "<h2>Image Metadata Analyzer</h2>"
            "<p><b>Версия:</b> 1.0 (Лабораторная работа №2)</p>"
            "<p>Приложение предназначено для быстрого извлечения метаданных "
            "из графических файлов без загрузки самих пикселей в память.</p>"
            
            "<h3>Поддерживаемые форматы:</h3>"
            "<ul>"
            "<li>JPEG (.jpg, .jpeg)</li>"
            "<li>PNG (.png)</li>"
            "<li>BMP (.bmp)</li>"
            "<li>GIF (.gif)</li>"
            "<li>TIFF (.tif, .tiff)</li>"
            "<li>PCX (.pcx)</li>"
            "</ul>"
            
            "<h3>Отображаемые характеристики:</h3>"
            "<ul>"
            "<li><b>Имя файла</b> — название файла без полного пути.</li>"
            "<li><b>Формат</b> — формат растрового изображения.</li>"
            "<li><b>Размер (px)</b> — ширина и высота изображения в пикселях.</li>"
            "<li><b>Разрешение (DPI)</b> — количество точек на дюйм. "
            "Если в файле не задано, отображается стандарт 72x72.</li>"
            "<li><b>Глубина цвета</b> — количество бит, отведённых на один пиксель.</li>"
            "<li><b>Сжатие</b> — тип сжатия: "
            "Lossy (с потерями, напр. JPEG) или Lossless (без потерь, напр. PNG/BMP).</li>"
            "</ul>"
            
            "<h3>Как пользоваться:</h3>"
            "<ol>"
            "<li>Нажмите <b>«Выбрать папку»</b> и укажите директорию с изображениями.</li>"
            "<li>Дождитесь окончания сканирования (прогресс-бар покажет статус).</li>"
            "<li>Для прерывания процесса нажмите <b>«Стоп»</b>.</li>"
            "</ol>"
            
            "<p><i>Приложение использует многопоточную обработку (QThread) "
            "и библиотеку Pillow для парсинга заголовков файлов.</i></p>"
        )
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Справка")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(help_text)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку с изображениями")
        if not folder:
            return
            
        self.lbl_path.setText(folder)
        self.lbl_path.setStyleSheet("color: black;")
        self.table.setRowCount(0)
        self.progress_bar.setValue(0)
        
        self.btn_select.setEnabled(False)
        self.btn_stop.setEnabled(True)
        
        self.worker = ScanWorker(folder)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.file_processed.connect(self.add_row)
        self.worker.finished_scan.connect(self.scan_finished)
        self.worker.start()

    def stop_scan(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.btn_stop.setEnabled(False)
            QTimer.singleShot(100, self._check_worker_stopped)

    def _check_worker_stopped(self):
        if self.worker and self.worker.isRunning():
            QTimer.singleShot(100, self._check_worker_stopped)
        else:
            self.scan_finished()

    def update_progress(self, current, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)

    def add_row(self, info):
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        if info['error']:
            self.table.setItem(row, 0, QTableWidgetItem(info['filename']))
            self.table.setItem(row, 1, QTableWidgetItem("ERROR"))
            self.table.setItem(row, 5, QTableWidgetItem(info['error']))
        else:
            size_str = f"{info['width']}x{info['height']}"
            self.table.setItem(row, 0, QTableWidgetItem(info['filename']))
            self.table.setItem(row, 1, QTableWidgetItem(info['format']))
            self.table.setItem(row, 2, QTableWidgetItem(size_str))
            self.table.setItem(row, 3, QTableWidgetItem(info['dpi']))
            self.table.setItem(row, 4, QTableWidgetItem(info['color_depth']))
            self.table.setItem(row, 5, QTableWidgetItem(info['compression']))

    def scan_finished(self):
        self.btn_select.setEnabled(True)
        self.btn_stop.setEnabled(False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageAnalyzerApp()
    window.show()
    sys.exit(app.exec())