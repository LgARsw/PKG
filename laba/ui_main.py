import sys
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QFileDialog, QComboBox, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap

from buffer_wrapper import BufferWrapper
from algorithms import ImageAlgorithms

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораторная 3 (Чистый Python + PyQt5)")
        self.resize(1100, 700)
        
        self.original_buffer = None
        self.current_buffer = None
        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        
        control_layout = QVBoxLayout()
        self.btn_load = QPushButton("Загрузить изображение")
        self.btn_load.clicked.connect(self.load_image)
        control_layout.addWidget(self.btn_load)
        
        self.combo_algo = QComboBox()
        self.combo_algo.addItems([
            "Линейное контрастирование",
            "Эквализация гистограммы",
            "Низкочастотный фильтр (Гаусс)",
            "Глобальный порог Оцу",
            "Локальный адаптивный порог (SAT)",
            "Сегментация Собеля",
            "Морфология: Дилатация",
            "Морфология: Эрозия"
        ])
        control_layout.addWidget(QLabel("Метод обработки:"))
        control_layout.addWidget(self.combo_algo)
        
        self.btn_process = QPushButton("Применить")
        self.btn_process.clicked.connect(self.process_image)
        control_layout.addWidget(self.btn_process)
        
        self.btn_reset = QPushButton("Сбросить")
        self.btn_reset.clicked.connect(self.reset_image)
        control_layout.addWidget(self.btn_reset)
        
        control_layout.addStretch()
        main_layout.addLayout(control_layout, 1)
        
        images_layout = QHBoxLayout()
        self.lbl_orig = QLabel("Исходное")
        self.lbl_orig.setAlignment(Qt.AlignCenter)
        self.lbl_orig.setStyleSheet("border: 1px solid gray; background: #eee;")
        images_layout.addWidget(self.lbl_orig)
        
        self.lbl_processed = QLabel("Результат")
        self.lbl_processed.setAlignment(Qt.AlignCenter)
        self.lbl_processed.setStyleSheet("border: 1px solid gray; background: #eee;")
        images_layout.addWidget(self.lbl_processed)
        
        main_layout.addLayout(images_layout, 3)
        self.setCentralWidget(main_widget)

    def load_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Открыть", "", "Изображения (*.png *.jpg *.bmp)")
        if file_name:
            img = QImage(file_name).convertToFormat(QImage.Format_RGB888)
            w, h = img.width(), img.height()
            ptr = img.bits()
            ptr.setsize(img.byteCount())
            arr = np.array(ptr, copy=True).reshape((h, w, 3))
            
            self.original_buffer = BufferWrapper(arr)
            self.current_buffer = BufferWrapper(arr.copy())
            
            self.show_image(self.original_buffer, self.lbl_orig)
            self.show_image(self.current_buffer, self.lbl_processed)

    def show_image(self, buffer: BufferWrapper, label: QLabel):
        u8 = buffer.to_uint8()
        h, w = u8.shape[:2]
        if u8.ndim == 2:
            q_img = QImage(u8.data, w, h, w, QImage.Format_Grayscale8)
        else:
            q_img = QImage(u8.data.tobytes(), w, h, w * 3, QImage.Format_RGB888)
        label.setPixmap(QPixmap.fromImage(q_img).scaled(label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def process_image(self):
        if not self.original_buffer: return
        idx = self.combo_algo.currentIndex()
        
        if idx == 0: self.current_buffer = ImageAlgorithms.linear_contrast(self.original_buffer)
        elif idx == 1: self.current_buffer = ImageAlgorithms.histogram_equalization(self.original_buffer)
        elif idx == 2: self.current_buffer = ImageAlgorithms.lowpass_gaussian(self.original_buffer, 5, 1.0)
        elif idx == 3: self.current_buffer = ImageAlgorithms.global_otsu(self.original_buffer)
        elif idx == 4: self.current_buffer = ImageAlgorithms.local_adaptive_threshold(self.original_buffer, 15, 2.0)
        elif idx == 5: self.current_buffer = ImageAlgorithms.sobel_segmentation(self.original_buffer)
        elif idx == 6: self.current_buffer = ImageAlgorithms.morphology_dilation(self.original_buffer, 3)
        elif idx == 7: self.current_buffer = ImageAlgorithms.morphology_erosion(self.original_buffer, 3)
        
        self.show_image(self.current_buffer, self.lbl_processed)

    def reset_image(self):
        if self.original_buffer:
            self.current_buffer = BufferWrapper(self.original_buffer.data.copy())
            self.show_image(self.current_buffer, self.lbl_processed)