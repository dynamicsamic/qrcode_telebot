import io

import numpy as np
from cv2 import COLOR_BGR2RGB, IMREAD_COLOR, QRCodeDetector, cvtColor, imdecode
from qreader import QReader

new_reader = QReader()

def decode_file(file: io.BytesIO)-> str:
    file.seek(0)
    file_bytes = np.asarray(bytearray(file.read()), dtype=np.uint8)
    img = imdecode(file_bytes, IMREAD_COLOR)    
    decoded = new_reader.detect_and_decode(img)
    return None if not decoded else decoded[0]


def _decode_file(file: io.BytesIO) -> str:
    """A less powerfrul qr code decoder."""
    qreader = QRCodeDetector()
    file.seek(0)
    file_bytes = np.asarray(bytearray(file.read()), dtype=np.uint8)
    img = cvtColor(imdecode(file_bytes, IMREAD_COLOR),  COLOR_BGR2RGB)
    code, *_ = qreader.detectAndDecode(img)
    return code



