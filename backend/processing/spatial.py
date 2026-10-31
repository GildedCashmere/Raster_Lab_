"""Spatial filtering with our shared true convolution; source alpha never filtered."""
from math import isfinite

import numpy as np

from .channels import export_uint8, rgb_intensity, split_rgb_alpha
from .convolution import convolve
from .box_filter import box_filter
from .kernels import emboss_kernel, sobel_kernels, validate_size, validate_strength


def box_blur(image: np.ndarray, kernel_size=3) -> np.ndarray:
    """Unit-sum box via prefix sums; export each channel to bound float memory."""
    validate_size(kernel_size, "blur")
    colour, alpha = split_rgb_alpha(image)
    result = np.empty_like(colour)
    for channel in range(3):
        result[..., channel] = export_uint8(box_filter(colour[..., channel], kernel_size), None)
    return result if alpha is None else np.concatenate((result, alpha), axis=-1)


def sharpen(image: np.ndarray, kernel_size=3, amount=1.0) -> np.ndarray:
    """I+a*(I-B), B=box_filter(I,N); equivalent to the unit-sum sharp kernel."""
    validate_size(kernel_size, "sharpen")
    validate_strength("Sharpening amount", amount)
    colour, alpha = split_rgb_alpha(image)
    result = np.empty_like(colour)
    for channel in range(3):
        original = colour[..., channel]
        if amount == 0:
            result[..., channel] = original
            continue
        working = box_filter(original, kernel_size)
        np.subtract(original, working, out=working)
        working *= amount
        working += original
        result[..., channel] = export_uint8(working, None)
    return result if alpha is None else np.concatenate((result, alpha), axis=-1)


def emboss(image: np.ndarray, kernel_size=3, strength=1.0, reverse_relief=False) -> np.ndarray:
    """Float grayscale -> signed directional convolution -> 128 +/- strength*E."""
    validate_strength("Emboss strength", strength)
    colour, alpha = split_rgb_alpha(image)
    intensity = rgb_intensity(colour.astype(np.float64))[..., 0]
    response = convolve(intensity, emboss_kernel(kernel_size))
    result = 128.0 + (-strength if reverse_relief else strength) * response
    return export_uint8(np.repeat(result[..., None], 3, axis=-1), alpha)


def sobel_responses(intensity: np.ndarray, kernel_size=3) -> tuple[np.ndarray, np.ndarray]:
    """Signed Gx/Gy, without clipping; useful for explaining and testing direction."""
    kx, ky = sobel_kernels(kernel_size)
    return convolve(intensity, kx), convolve(intensity, ky)


def normalized_magnitude(gx: np.ndarray, gy: np.ndarray) -> np.ndarray:
    """Display scaling to 0..255. A maximum <=1e-10 is numerical zero."""
    magnitude = np.sqrt(gx * gx + gy * gy)
    maximum = float(magnitude.max())
    if maximum <= 1e-10:
        return np.zeros_like(magnitude)
    magnitude /= maximum
    magnitude *= 255.0
    return magnitude


def sobel_edges(image: np.ndarray, kernel_size=3, binary_threshold=False, threshold=128.0) -> np.ndarray:
    """Grayscale -> signed Gx/Gy -> normalized magnitude -> optional >= threshold.

    Threshold the normalized float image before the one final export rounding.
    Thus threshold 0 makes all pixels white, including a flat image.
    """
    if not isfinite(threshold) or not 0 <= threshold <= 255:
        raise ValueError("Threshold must be finite and between 0 and 255.")
    colour, alpha = split_rgb_alpha(image)
    intensity = rgb_intensity(colour.astype(np.float64))[..., 0]
    gx, gy = sobel_responses(intensity, kernel_size)
    output = normalized_magnitude(gx, gy)
    if binary_threshold:
        output = np.where(output >= threshold, 255.0, 0.0)
    return export_uint8(np.repeat(output[..., None], 3, axis=-1), alpha)
