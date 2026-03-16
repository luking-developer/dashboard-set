import base64
import io

import qrcode


def generar_qr_base64(data):
    qr = qrcode.make(data)
    buffered = io.BytesIO()
    qr.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()