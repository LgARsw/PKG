import numpy as np

class BufferWrapper:
    """
    Обертка над массивом пикселей. Изолирует алгоритмы от UI 
    и предоставляет методы доступа к памяти.
    """
    def __init__(self, data: np.ndarray):
        self.data = data.astype(np.float64)
        if self.data.ndim == 2:
            self.height, self.width = self.data.shape
            self.channels = 1
        elif self.data.ndim == 3:
            self.height, self.width, self.channels = self.data.shape
        else:
            raise ValueError("Неподдерживаемая размерность изображения")

    def pad(self, pad_h: int, pad_w: int, mode: str = 'reflect') -> np.ndarray:
        """Реализация стратегий обработки краев (Clamp / Reflect) вручную."""
        h, w = self.height, self.width
        if self.channels == 1:
            padded = np.zeros((h + 2 * pad_h, w + 2 * pad_w), dtype=np.float64)
            padded[pad_h:pad_h+h, pad_w:pad_w+w] = self.data
            
            # Заполнение границ (Reflect / Clamp)
            for i in range(pad_h):
                for j in range(pad_w, pad_w + w):
                    if mode == 'reflect':
                        padded[pad_h - 1 - i, j] = self.data[i + 1, j - pad_w]
                        padded[pad_h + h + i, j] = self.data[h - 2 - i, j - pad_w]
                    else: # clamp
                        padded[pad_h - 1 - i, j] = self.data[0, j - pad_w]
                        padded[pad_h + h + i, j] = self.data[h - 1, j - pad_w]
            for i in range(pad_h + h):
                for j in range(pad_w):
                    if mode == 'reflect':
                        padded[i, pad_w - 1 - j] = self.data[i - pad_h if i - pad_h >= 0 else 0, j + 1]
                        padded[i, pad_w + w + j] = self.data[i - pad_h if i - pad_h < h else h - 1, w - 2 - j]
                    else:
                        padded[i, pad_w - 1 - j] = self.data[i - pad_h if i - pad_h >= 0 else 0, 0]
                        padded[i, pad_w + w + j] = self.data[i - pad_h if i - pad_h < h else h - 1, w - 1]
            return padded
        else:
            # Многоканальный вариант (возвращаем с падингом по каналам)
            out_channels = []
            for c in range(self.channels):
                single_buf = BufferWrapper(self.data[:, :, c])
                out_channels.append(single_buf.pad(pad_h, pad_w, mode))
            return np.stack(out_channels, axis=-1)

    def to_uint8(self) -> np.ndarray:
        return np.clip(self.data, 0, 255).astype(np.uint8)