import io

import numpy as np
from cv2 import IMREAD_COLOR, QRCodeDetector, imdecode


def scan_file(qreader: QRCodeDetector, file: io.BytesIO) -> str:
    file.seek(0)
    file_bytes = np.asarray(bytearray(file.read()), dtype=np.uint8)
    img = imdecode(file_bytes, IMREAD_COLOR)
    code, *_ = qreader.detectAndDecode(img)
    return code
