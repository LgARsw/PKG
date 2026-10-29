import math
from buffer_wrapper import BufferWrapper
import numpy as np

class ImageAlgorithms:

    @staticmethod
    def linear_contrast(buffer: BufferWrapper) -> BufferWrapper:
        """Линейное контрастирование."""
        h, w, ch = buffer.height, buffer.width, buffer.channels
        out = np.zeros_like(buffer.data)
        
        if ch == 1:
            min_v, max_v = float('inf'), float('-inf')
            for i in range(h):
                for j in range(w):
                    val = buffer.data[i, j]
                    if val < min_v: min_v = val
                    if val > max_v: max_v = val
            diff = max_v - min_v if max_v != min_v else 1.0
            for i in range(h):
                for j in range(w):
                    out[i, j] = (buffer.data[i, j] - min_v) / diff * 255.0
        else:
            for c in range(ch):
                min_v, max_v = float('inf'), float('-inf')
                for i in range(h):
                    for j in range(w):
                        val = buffer.data[i, j, c]
                        if val < min_v: min_v = val
                        if val > max_v: max_v = val
                diff = max_v - min_v if max_v != min_v else 1.0
                for i in range(h):
                    for j in range(w):
                        out[i, j, c] = (buffer.data[i, j, c] - min_v) / diff * 255.0
        return BufferWrapper(out)

    @staticmethod
    def histogram_equalization(buffer: BufferWrapper) -> BufferWrapper:
        """Эквализация гистограммы."""
        u8 = buffer.to_uint8()
        h, w, ch = buffer.height, buffer.width, buffer.channels
        out = np.zeros_like(buffer.data)

        if ch == 1:
            hist = [0] * 256
            for i in range(h):
                for j in range(w):
                    hist[u8[i, j]] += 1
            
            cdf = [0] * 256
            cdf[0] = hist[0]
            for i in range(1, 256):
                cdf[i] = cdf[i-1] + hist[i]
                
            cdf_min = next((x for x in cdf if x > 0), 0)
            total = h * w
            lut = [0] * 256
            for i in range(256):
                if total - cdf_min > 0:
                    lut[i] = round((cdf[i] - cdf_min) / (total - cdf_min) * 255.0)
                else:
                    lut[i] = i
            
            for i in range(h):
                for j in range(w):
                    out[i, j] = lut[u8[i, j]]
        else:
            for c in range(ch):
                hist = [0] * 256
                for i in range(h):
                    for j in range(w):
                        hist[u8[i, j, c]] += 1
                cdf = [0] * 256
                cdf[0] = hist[0]
                for i in range(1, 256):
                    cdf[i] = cdf[i-1] + hist[i]
                cdf_min = next((x for x in cdf if x > 0), 0)
                total = h * w
                lut = [0] * 256
                for i in range(256):
                    if total - cdf_min > 0:
                        lut[i] = round((cdf[i] - cdf_min) / (total - cdf_min) * 255.0)
                    else:
                        lut[i] = i
                for i in range(h):
                    for j in range(w):
                        out[i, j, c] = lut[u8[i, j, c]]
        return BufferWrapper(out)

    @staticmethod
    def lowpass_gaussian(buffer: BufferWrapper, kernel_size: int = 5, sigma: float = 1.0) -> BufferWrapper:
        """Низкочастотный фильтр (Гаусс) через разделяемые свертки[cite: 3, 4]."""
        if kernel_size % 2 == 0: kernel_size += 1
        radius = kernel_size // 2
        
        # Генерация ядра 1D
        kernel_1d = [0.0] * kernel_size
        k_sum = 0.0
        for i in range(kernel_size):
            x = i - radius
            val = math.exp(-(x**2) / (2 * (sigma**2)))
            kernel_1d[i] = val
            k_sum += val
        for i in range(kernel_size):
            kernel_1d[i] /= k_sum

        padded = buffer.pad(radius, radius, mode='reflect')
        h, w, ch = buffer.height, buffer.width, buffer.channels
        
        if ch == 1:
            # Проход по строкам
            temp = np.zeros((h + 2*radius, w), dtype=np.float64)
            for i in range(h + 2*radius):
                for j in range(w):
                    s = 0.0
                    for k in range(kernel_size):
                        s += padded[i, j + radius + (k - radius)] * kernel_1d[k]
                    temp[i, j] = s
            # Проход по столбцам
            out = np.zeros((h, w), dtype=np.float64)
            for i in range(h):
                for j in range(w):
                    s = 0.0
                    for k in range(kernel_size):
                        s += temp[i + radius + (k - radius), j] * kernel_1d[k]
                    out[i, j] = s
            return BufferWrapper(out)
        else:
            out = np.zeros((h, w, ch), dtype=np.float64)
            for c in range(ch):
                chan_buf = BufferWrapper(buffer.data[:, :, c])
                res = ImageAlgorithms.lowpass_gaussian(chan_buf, kernel_size, sigma)
                out[:, :, c] = res.data
            return BufferWrapper(out)

    @staticmethod
    def global_otsu(buffer: BufferWrapper) -> BufferWrapper:
        """Глобальный метод Оцу[cite: 3]."""
        h, w, ch = buffer.height, buffer.width, buffer.channels
        if ch > 1:
            gray = 0.299 * buffer.data[:, :, 0] + 0.587 * buffer.data[:, :, 1] + 0.114 * buffer.data[:, :, 2]
        else:
            gray = buffer.data

        u8 = np.clip(gray, 0, 255).astype(np.uint8)
        hist = [0] * 256
        for i in range(h):
            for j in range(w):
                hist[u8[i, j]] += 1

        total = h * w
        sum_total = sum(i * hist[i] for i in range(256))
        sum_b = 0
        w_b = 0
        max_var = 0.0
        threshold = 0

        for t in range(256):
            w_b += hist[t]
            if w_b == 0: continue
            w_f = total - w_b
            if w_f == 0: break
            sum_b += t * hist[t]
            m_b = sum_b / w_b
            m_f = (sum_total - sum_b) / w_f
            var = w_b * w_f * ((m_b - m_f) ** 2)
            if var > max_var:
                max_var = var
                threshold = t

        out = np.zeros((h, w), dtype=np.float64)
        for i in range(h):
            for j in range(w):
                out[i, j] = 255.0 if gray[i, j] >= threshold else 0.0
        return BufferWrapper(out)

    @staticmethod
    def local_adaptive_threshold(buffer: BufferWrapper, window_size: int = 15, c_val: float = 2.0) -> BufferWrapper:
        """Локальная пороговая обработка с использованием интегрального изображения (SAT)[cite: 3]."""
        h, w, ch = buffer.height, buffer.width, buffer.channels
        if ch > 1:
            gray = 0.299 * buffer.data[:, :, 0] + 0.587 * buffer.data[:, :, 1] + 0.114 * buffer.data[:, :, 2]
        else:
            gray = buffer.data

        # Построение интегрального изображения
        integral = np.zeros((h + 1, w + 1), dtype=np.float64)
        for i in range(h):
            row_sum = 0.0
            for j in range(w):
                row_sum += gray[i, j]
                integral[i + 1, j + 1] = integral[i, j + 1] + row_sum

        radius = window_size // 2
        out = np.zeros((h, w), dtype=np.float64)

        for i in range(h):
            y1 = max(0, i - radius)
            y2 = min(h, i + radius + 1)
            for j in range(w):
                x1 = max(0, j - radius)
                x2 = min(w, j + radius + 1)
                
                count = (y2 - y1) * (x2 - x1)
                total_sum = integral[y2, x2] - integral[y1, x2] - integral[y2, x1] + integral[y1, x1]
                mean_val = total_sum / count

                out[i, j] = 255.0 if gray[i, j] >= (mean_val - c_val) else 0.0
        return BufferWrapper(out)

    @staticmethod
    def sobel_segmentation(buffer: BufferWrapper) -> BufferWrapper:
        """Сегментация оператором Собеля[cite: 3]."""
        h, w, ch = buffer.height, buffer.width, buffer.channels
        if ch > 1:
            gray = 0.299 * buffer.data[:, :, 0] + 0.587 * buffer.data[:, :, 1] + 0.114 * buffer.data[:, :, 2]
        else:
            gray = buffer.data

        padded = np.pad(gray, 1, mode='reflect')
        Kx = [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]
        Ky = [[-1, -2, -1], [0, 0, 0], [1, 2, 1]]
        
        out = np.zeros((h, w), dtype=np.float64)
        for i in range(h):
            for j in range(w):
                gx = 0.0
                gy = 0.0
                for ki in range(3):
                    for kj in range(3):
                        pixel = padded[i + ki, j + kj]
                        gx += pixel * Kx[ki][kj]
                        gy += pixel * Ky[ki][kj]
                mag = math.sqrt(gx**2 + gy**2)
                out[i, j] = min(mag, 255.0)
        return BufferWrapper(out)

    @staticmethod
    def morphology_dilation(buffer: BufferWrapper, kernel_size: int = 3) -> BufferWrapper:
        """Морфологическая дилатация."""
        h, w, ch = buffer.height, buffer.width, buffer.channels
        if ch > 1:
            gray = 0.299 * buffer.data[:, :, 0] + 0.587 * buffer.data[:, :, 1] + 0.114 * buffer.data[:, :, 2]
        else:
            gray = buffer.data

        binary = (gray > 127).astype(np.uint8)
        radius = kernel_size // 2
        padded = np.pad(binary, radius, mode='edge')
        out = np.zeros((h, w), dtype=np.float64)

        for i in range(h):
            for j in range(w):
                has_one = False
                for ki in range(kernel_size):
                    for kj in range(kernel_size):
                        if padded[i + ki, j + kj] == 1:
                            has_one = True
                            break
                    if has_one: break
                out[i, j] = 255.0 if has_one else 0.0
        return BufferWrapper(out)

    @staticmethod
    def morphology_erosion(buffer: BufferWrapper, kernel_size: int = 3) -> BufferWrapper:
        """Морфологическая эрозия."""
        h, w, ch = buffer.height, buffer.width, buffer.channels
        if ch > 1:
            gray = 0.299 * buffer.data[:, :, 0] + 0.587 * buffer.data[:, :, 1] + 0.114 * buffer.data[:, :, 2]
        else:
            gray = buffer.data

        binary = (gray > 127).astype(np.uint8)
        radius = kernel_size // 2
        padded = np.pad(binary, radius, mode='edge')
        out = np.zeros((h, w), dtype=np.float64)

        for i in range(h):
            for j in range(w):
                all_ones = True
                for ki in range(kernel_size):
                    for kj in range(kernel_size):
                        if padded[i + ki, j + kj] == 0:
                            all_ones = False
                            break
                    if not all_ones: break
                out[i, j] = 255.0 if all_ones else 0.0
        return BufferWrapper(out)