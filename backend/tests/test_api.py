from io import BytesIO
import struct
import zlib

from fastapi.testclient import TestClient
import numpy as np
from PIL import Image, ImageFile
import pytest

from backend.main import Settings, create_app
from backend.tests.test_geometry import EXPECTED, SOURCE


@pytest.fixture
def client():
    with TestClient(create_app(Settings())) as client:
        yield client


def encoded(image, format="PNG", **kwargs):
    buffer = BytesIO()
    image.save(buffer, format=format, **kwargs)
    return buffer.getvalue()


def submit(client, data, operation="rotate_90"):
    # Deliberately generic MIME and name: decoded content is authoritative.
    return client.post("/process", files={"file": ("image.bin", data, "application/octet-stream")}, data={"operation": operation})


def decoded(response):
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "image/png"
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["content-disposition"].endswith('.png"')
    image = Image.open(BytesIO(response.content))
    image.load()
    assert image.format == "PNG"
    return image


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


@pytest.mark.parametrize("operation", EXPECTED)
def test_all_operations(client, operation):
    response = submit(client, encoded(Image.fromarray(SOURCE)), operation)
    image = decoded(response)
    np.testing.assert_array_equal(np.array(image), EXPECTED[operation])
    assert response.headers["x-original-width"] == "3"
    assert response.headers["x-original-height"] == "2"
    assert int(response.headers["x-output-width"]) == image.width
    assert int(response.headers["x-output-height"]) == image.height


@pytest.mark.parametrize("mode", ["L", "LA", "RGB", "RGBA"])
def test_modes_and_alpha(client, mode):
    channels = len(mode)
    source = SOURCE if mode == "L" else np.stack([SOURCE + c * 25 for c in range(channels)], axis=-1)
    expected = np.array(EXPECTED["rotate_90"])
    if mode != "L":
        expected = np.stack([expected + c * 25 for c in range(channels)], axis=-1)
    result = decoded(submit(client, encoded(Image.fromarray(source))))
    assert result.mode == mode
    np.testing.assert_array_equal(np.array(result), expected)


@pytest.mark.parametrize("format", ["JPEG", "PNG", "WEBP"])
def test_input_formats(client, format):
    data = encoded(Image.fromarray(SOURCE).convert("RGB"), format)
    # JPEG/WebP can be lossy: compare the transformation to decoded input pixels.
    source = np.array(Image.open(BytesIO(data)))
    expected = np.array([[source[1, 0], source[0, 0]], [source[1, 1], source[0, 1]], [source[1, 2], source[0, 2]]])
    np.testing.assert_array_equal(np.array(decoded(submit(client, data))), expected)


def test_palette_transparency(client):
    image = Image.fromarray(SOURCE).convert("P")
    data = encoded(image, transparency=1)
    result = decoded(submit(client, data, "horizontal_flip"))
    assert result.mode == "RGBA"
    source = np.array(Image.open(BytesIO(data)).convert("RGBA"))
    np.testing.assert_array_equal(np.array(result), source[:, [2, 1, 0]])
    assert np.array(result)[0, 2, 3] == 0


def test_rgb_colour_key_transparency(client):
    image = Image.new("RGB", (3, 2), (10, 20, 30))
    result = decoded(submit(client, encoded(image, transparency=(10, 20, 30))))
    assert result.mode == "RGBA"
    assert (np.array(result)[:, :, 3] == 0).all()


def test_lossless_webp_alpha(client):
    source = np.stack([SOURCE + c * 25 for c in range(4)], axis=-1)
    data = encoded(Image.fromarray(source), "WEBP", lossless=True)
    result = decoded(submit(client, data, "rotate_270"))
    expected = np.array(EXPECTED["rotate_270"])
    np.testing.assert_array_equal(np.array(result), np.stack([expected + c * 25 for c in range(4)], axis=-1))


def test_exif_orientation_is_normalized_before_operation(client):
    exif = Image.Exif()
    exif[274] = 6  # Stored 3x2 image displays 2x3, clockwise 90 degrees.
    data = encoded(Image.fromarray(SOURCE), exif=exif)
    response = submit(client, data, "horizontal_flip")
    result = decoded(response)
    np.testing.assert_array_equal(np.array(result), [[1, 4], [2, 5], [3, 6]])
    assert response.headers["x-original-width"] == "2"
    assert response.headers["x-original-height"] == "3"
    assert 274 not in result.getexif()


@pytest.mark.parametrize("data", [b"", b"not an image", b"\x89PNG\r\n\x1a\ncorrupt"])
def test_invalid_image(client, data):
    response = submit(client, data)
    assert response.status_code == 400
    assert isinstance(response.json()["detail"], str)


def test_truncated_image(client):
    data = encoded(Image.new("RGB", (64, 64)), "JPEG")
    assert submit(client, data[:-30]).status_code == 400


@pytest.mark.parametrize("operation", ["invert", "rotate_45", "", "ROTATE_90"])
def test_unsupported_operation(client, operation):
    assert submit(client, encoded(Image.fromarray(SOURCE)), operation).status_code == 422


def test_missing_fields(client):
    assert client.post("/process").status_code == 422
    assert client.post("/process", data={"operation": "rotate_90"}).status_code == 422


@pytest.mark.parametrize("format", ["GIF", "BMP", "TIFF"])
def test_unsupported_decoded_format(client, format):
    assert submit(client, encoded(Image.fromarray(SOURCE), format)).status_code == 415


def test_unsupported_mode(client):
    assert submit(client, encoded(Image.new("CMYK", (3, 2)), "JPEG")).status_code == 415
    assert submit(client, encoded(Image.new("I;16", (3, 2)))).status_code == 415


@pytest.mark.parametrize("colour_type,channels", [(2, 3), (6, 4)])
def test_high_depth_colour_png_rejected_instead_of_silent_truncation(client, colour_type, channels):
    # Build a real 16-bit PNG: Pillow otherwise decodes these as 8-bit RGB/RGBA.
    def chunk(kind, payload):
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload))
    pixels = np.arange(2 * 3 * channels, dtype=">u2").reshape(2, 3, channels)
    raw = b"".join(b"\x00" + row.tobytes() for row in pixels)
    data = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 3, 2, 16, colour_type, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")
    assert Image.open(BytesIO(data)).mode in {"RGB", "RGBA"}
    response = submit(client, data)
    assert response.status_code == 415
    assert "16-bit" in response.json()["detail"]


def test_animated_image(client):
    image = Image.new("RGBA", (3, 2), "red")
    data = encoded(image, save_all=True, append_images=[Image.new("RGBA", (3, 2), "blue")], duration=100)
    assert submit(client, data).status_code == 415


def test_exact_upload_limit_and_over_limit():
    data = encoded(Image.fromarray(SOURCE))
    with TestClient(create_app(Settings(max_upload_bytes=len(data)))) as client:
        assert submit(client, data).status_code == 200
        assert submit(client, data + b"x").status_code == 413


def test_pixel_limit():
    data = encoded(Image.fromarray(SOURCE))
    with TestClient(create_app(Settings(max_pixels=5))) as client:
        assert submit(client, data).status_code == 413
    with TestClient(create_app(Settings(max_pixels=6))) as client:
        assert submit(client, data).status_code == 200


def test_pixel_limit_checked_before_decoding(monkeypatch):
    data = encoded(Image.fromarray(SOURCE))
    def unexpected_decode(*args, **kwargs):
        pytest.fail("An oversized image must be rejected before pixel decoding")
    monkeypatch.setattr(ImageFile.ImageFile, "load", unexpected_decode)
    with TestClient(create_app(Settings(max_pixels=5))) as client:
        assert submit(client, data).status_code == 413


@pytest.mark.parametrize("case", ["success", "invalid_operation", "invalid_image", "too_large"])
def test_upload_resources_closed(monkeypatch, case):
    import starlette.formparsers as parsers
    original_factory = parsers.SpooledTemporaryFile
    uploads = []
    def tracking_factory(*args, **kwargs):
        upload = original_factory(*args, **kwargs)
        uploads.append(upload)
        return upload
    monkeypatch.setattr(parsers, "SpooledTemporaryFile", tracking_factory)
    data = encoded(Image.fromarray(SOURCE))
    settings = Settings(max_upload_bytes=50) if case == "too_large" else Settings()
    with TestClient(create_app(settings)) as client:
        response = submit(client, b"broken" if case == "invalid_image" else data,
                          "unsupported" if case == "invalid_operation" else "rotate_90")
        assert response.status_code == {"success": 200, "invalid_operation": 422, "invalid_image": 400, "too_large": 413}[case]
    assert uploads
    assert all(upload.closed for upload in uploads)


def test_streamed_request_body_limit():
    # No Content-Length: the ASGI receive wrapper must enforce the limit.
    with TestClient(create_app(Settings(max_upload_bytes=50))) as client:
        def chunks():
            yield b'--boundary\r\nContent-Disposition: form-data; name="file"; filename="x.png"\r\n\r\n'
            yield b"x" * 70_000
            yield b"\r\n--boundary--\r\n"
        response = client.post("/process", content=chunks(), headers={"Content-Type": "multipart/form-data; boundary=boundary"})
        assert response.status_code == 413


def test_cors(client):
    for origin in ["http://localhost:4321", "http://127.0.0.1:4321"]:
        response = client.get("/health", headers={"Origin": origin})
        assert response.headers["access-control-allow-origin"] == origin
    assert "access-control-allow-origin" not in client.get("/health", headers={"Origin": "https://untrusted.example"}).headers
    response = client.options("/process", headers={"Origin": "http://localhost:4321", "Access-Control-Request-Method": "POST"})
    assert response.status_code == 200


def test_environment_settings(monkeypatch):
    monkeypatch.setenv("MAX_UPLOAD_BYTES", "2048")
    monkeypatch.setenv("MAX_IMAGE_PIXELS", "100")
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://images.example, https://lab.example")
    assert Settings.from_env() == Settings(2048, 100, ("https://images.example", "https://lab.example"))


@pytest.mark.parametrize("values", [{"max_upload_bytes": 0}, {"max_pixels": -1}])
def test_invalid_settings(values):
    with pytest.raises(ValueError):
        Settings(**values)
