r"""Run from the repository root: .\.venv\Scripts\python.exe -m backend.benchmark."""
from io import BytesIO
from statistics import median
from time import perf_counter

from fastapi.testclient import TestClient
import numpy as np
from PIL import Image

from backend.main import Settings, create_app
from backend.processing.geometry import rotate_90
from backend.processing.point import gamma_correction, contrast_stretch


def main():
    rng = np.random.default_rng(42)
    with TestClient(create_app(Settings())) as client:
        for width, height in [(1200, 800), (4000, 3000)]:
            # A compressible gradient stays inside the 8 MiB upload limit.
            row = np.arange(width, dtype=np.uint16) % 256
            pixels = np.empty((height, width, 4), dtype=np.uint8)
            pixels[..., 0] = row
            pixels[..., 1] = np.arange(height, dtype=np.uint16)[:, None] % 256
            pixels[..., 2] = rng.integers(0, 256, size=(height, 1), dtype=np.uint8)
            pixels[..., 3] = 220
            buffer = BytesIO()
            Image.fromarray(pixels).save(buffer, format="PNG")
            data = buffer.getvalue()
            cases = [
                ("rotate_90", rotate_90, {}),
                ("gamma", gamma_correction, dict(gamma=.7, red_gain=1.1, saturation=1.2)),
                ("contrast", contrast_stretch, dict(gamma=1.1, saturation=.8)),
            ]
            for operation, function, parameters in cases:
                algorithm, requests = [], []
                for _ in range(3):
                    start = perf_counter()
                    function(pixels, **parameters)
                    algorithm.append((perf_counter() - start) * 1000)
                    start = perf_counter()
                    response = client.post(
                        "/process", files={"file": ("gradient.png", data, "image/png")},
                        data={"operation": operation, **parameters},
                    )
                    response.raise_for_status()
                    requests.append((perf_counter() - start) * 1000)
                print(f"{width}x{height} RGBA {operation}: upload={len(data):,} bytes; "
                      f"NumPy={median(algorithm):.1f} ms; API={median(requests):.1f} ms (median of 3)", flush=True)



if __name__ == "__main__":
    main()
