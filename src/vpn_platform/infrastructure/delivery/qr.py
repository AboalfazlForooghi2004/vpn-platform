from io import BytesIO

import qrcode


def config_qr_png(config_text: str) -> bytes:
    """Return a PNG QR. Both the input and result contain secret config material."""
    image = qrcode.make(config_text)
    output = BytesIO()
    image.save(output)
    return output.getvalue()
