r"""Run .\.venv\Scripts\python.exe -m backend.benchmark_spatial [--repeats 3]."""
import argparse
from io import BytesIO
from statistics import median
from time import perf_counter

from fastapi.testclient import TestClient
import numpy as np
from PIL import Image

from backend.main import Settings, create_app
from backend.processing.kernels import BOX_KERNEL_SIZES, KERNEL_SIZES


def main():
    parser = argparse.ArgumentParser(description="Full-resolution spatial API benchmark, without network latency")
    parser.add_argument('--repeats', type=int, default=3)
    parser.add_argument('--sizes', type=int, nargs='+', default=[3, 11], choices=BOX_KERNEL_SIZES)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error('--repeats must be positive')
    with TestClient(create_app(Settings())) as client:
        for width, height in [(1200, 800), (4000, 3000)]:
            image = np.empty((height, width, 4), dtype=np.uint8)
            image[..., 0] = np.arange(width, dtype=np.uint16) % 256
            image[..., 1] = np.arange(height, dtype=np.uint16)[:, None] % 256
            image[..., 2] = 150
            image[..., 3] = 200
            buffer = BytesIO(); Image.fromarray(image).save(buffer, format='PNG')
            data = buffer.getvalue()
            for size in args.sizes:
                for operation in ('blur', 'sharpen', 'emboss', 'sobel'):
                    if size not in (BOX_KERNEL_SIZES if operation in ('blur', 'sharpen') else KERNEL_SIZES):
                        continue
                    times = []
                    for _ in range(args.repeats):
                        start = perf_counter()
                        response = client.post('/process', files={'file': ('gradient.png', data, 'image/png')}, data={'operation': operation, 'kernel_size': size})
                        response.raise_for_status()
                        times.append((perf_counter() - start) * 1000)
                    print(f'{width}x{height} RGBA {operation} {size}x{size}: API={median(times):.1f} ms; upload={len(data):,} bytes (median of {args.repeats})', flush=True)


if __name__ == '__main__':
    main()
