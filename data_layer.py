import os
from PIL import Image

class ImageParser:
    @staticmethod
    def get_image_info(filepath):
        info = {
            'filename': os.path.basename(filepath),
            'width': 'N/A',
            'height': 'N/A',
            'dpi': 'N/A',
            'color_depth': 'N/A',
            'compression': 'N/A',
            'format': 'N/A',
            'error': None
        }
        
        try:
            with Image.open(filepath) as img:
                info['format'] = img.format
                info['width'], info['height'] = img.size
                
                dpi_found = False
                dpi = img.info.get('dpi')
                if dpi and dpi[0] > 0:
                    info['dpi'] = f"{int(dpi[0])}x{int(dpi[1])}"
                    dpi_found = True
                
                if not dpi_found:
                    try:
                        exif = img.getexif()
                        if exif:
                            x_res = exif.get(282)
                            y_res = exif.get(283)
                            if x_res and y_res:
                                info['dpi'] = f"{int(x_res)}x{int(y_res)}"
                                dpi_found = True
                    except Exception:
                        pass
                
                if not dpi_found:
                    info['dpi'] = "72x72 (default)"

                modes = {
                    '1': '1 bit',
                    'L': '8 bit',
                    'P': '8 bit',
                    'RGB': '24 bit',
                    'RGBA': '32 bit',
                    'CMYK': '32 bit',
                    'I': '32 bit',
                    'F': '32 bit'
                }
                info['color_depth'] = modes.get(img.mode, f"{img.mode}")

                comp = img.info.get('compression')
                if comp:
                    info['compression'] = comp
                else:
                    if img.format == 'JPEG':
                        info['compression'] = 'Lossy (JPEG)'
                    elif img.format in ['PNG', 'BMP', 'GIF', 'TIFF', 'PCX']:
                        info['compression'] = 'Lossless / None'
                        
        except Exception as e:
            info['error'] = str(e)
            
        return info
