"""Readable true convolution, with image-sized storage rather than window tensors."""
import numpy as np


def convolve(image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    """Return signed float64 convolution with reflect padding and original shape.

    Accept a nonempty H×W array or H×W×channels array and a finite, odd square
    kernel. Alpha separation belongs to the caller. Reflect excludes the edge
    sample (e.g. [a,b,c] padded by one becomes [b,a,b,c,b]); singleton axes
    repeat their only value. Padding can exceed the image size.

    Reverse BOTH kernel axes before neighbourhood multiplication: without that
    reversal this would be correlation. Accumulate by kernel offset, using
    vectorized row blocks to bound temporary products. No H×W×N×N allocation,
    clipping, rounding or mutation of the original image/kernel occurs here.
    """
    source = np.asarray(image)
    weights = np.asarray(kernel, dtype=np.float64)
    if source.ndim not in (2, 3) or any(d == 0 for d in source.shape):
        raise ValueError("Expected a nonempty grayscale or colour image array.")
    if source.dtype.kind not in "uif" or not np.isfinite(source).all():
        raise ValueError("Image values must be finite real numbers.")
    if (weights.ndim != 2 or weights.shape[0] != weights.shape[1]
            or weights.shape[0] < 1 or weights.shape[0] % 2 != 1
            or not np.isfinite(weights).all()):
        raise ValueError("Kernel must be a finite, nonempty odd square matrix.")
    radius = weights.shape[0] // 2
    padding = [(radius, radius), (radius, radius)] + ([(0, 0)] if source.ndim == 3 else [])
    # Cast before multiplication; padding itself only rearranges source values.
    padded = np.pad(source, padding, mode="reflect").astype(np.float64, copy=False)
    reversed_kernel = weights[::-1, ::-1]
    height, width = source.shape[:2]
    result = np.zeros(source.shape, dtype=np.float64)
    block_height = min(128, height)
    scratch = np.empty((block_height, *source.shape[1:]), dtype=np.float64)
    for row in range(weights.shape[0]):
        for column in range(weights.shape[1]):
            coefficient = reversed_kernel[row, column]
            if coefficient == 0:
                continue
            for start in range(0, height, block_height):
                stop = min(start + block_height, height)
                product = scratch[:stop - start]
                window = padded[start + row:stop + row, column:column + width, ...]
                np.multiply(window, coefficient, out=product)
                np.add(result[start:stop], product, out=result[start:stop])
    return result
