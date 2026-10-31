"""Linear-work box averaging, checked against the direct convolution reference."""
import numpy as np

from .kernels import validate_size


def box_filter(image: np.ndarray, kernel_size=3) -> np.ndarray:
    """Return a float64 box mean with the exact direct engine's reflect padding.

    Pad by m=(N-1)/2 on both axes using np.pad(mode='reflect'), excluding
    border samples and repeating reflection for small/singleton dimensions.
    Prefix-sum differences compute horizontal and then vertical window sums.
    Divide by N² only at the end. This is convolution with the symmetric
    unit-sum box kernel, with O(HW) work per channel rather than O(HWN²).

    RGB arrays are processed channel by channel. Storage is image-sized;
    no window tensor is made. No clipping, rounding, alpha handling, or input
    mutation occurs here. For arbitrary float inputs, accumulation order may
    differ from direct convolution at float64 roundoff level.
    """
    validate_size(kernel_size, "blur")
    source = np.asarray(image)
    if source.ndim not in (2, 3) or any(d == 0 for d in source.shape):
        raise ValueError("Expected a nonempty grayscale or colour array.")
    if source.dtype.kind not in "uif" or not np.isfinite(source).all():
        raise ValueError("Image values must be finite real numbers.")
    if source.ndim == 3:
        result = np.empty(source.shape, dtype=np.float64)
        for channel in range(source.shape[-1]):
            result[..., channel] = box_filter(source[..., channel], kernel_size)
        return result
    radius = kernel_size // 2
    padded = np.pad(source, ((radius, radius), (radius, radius)), mode="reflect")
    prefix = np.empty((padded.shape[0], padded.shape[1] + 1), dtype=np.float64)
    prefix[:, 0] = 0
    np.cumsum(padded, axis=1, dtype=np.float64, out=prefix[:, 1:])
    horizontal = prefix[:, kernel_size:] - prefix[:, :-kernel_size]
    del padded, prefix
    prefix = np.empty((horizontal.shape[0] + 1, horizontal.shape[1]), dtype=np.float64)
    prefix[0] = 0
    np.cumsum(horizontal, axis=0, dtype=np.float64, out=prefix[1:])
    del horizontal
    result = prefix[kernel_size:] - prefix[:-kernel_size]
    result /= kernel_size**2
    return result
