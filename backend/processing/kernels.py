"""Kernel construction shared by spatial filtering, Sobel, and matrix display."""
from math import comb, isfinite
from typing import Literal

import numpy as np

KERNEL_SIZES = (3, 5, 7, 9, 11)
BOX_KERNEL_SIZES = (*KERNEL_SIZES, 21, 31)
SpatialOperation = Literal["blur", "sharpen", "emboss", "sobel"]


def validate_size(size: int, operation: str | None = None):
    supported = BOX_KERNEL_SIZES if operation in {"blur", "sharpen"} else KERNEL_SIZES
    if isinstance(size, (bool, np.bool_)) or not isinstance(size, (int, np.integer)) or size not in supported:
        raise ValueError(f"Kernel size for {operation or 'derivative filters'} must be one of {supported}.")


def validate_strength(name: str, value: float):
    if not isfinite(value) or not 0 <= value <= 2:
        raise ValueError(f"{name} must be finite and between 0 and 2.")


def box_kernel(size: int) -> np.ndarray:
    """Unit-sum N×N box: each coefficient is 1/N²."""
    validate_size(size, "blur")
    return np.ones((size, size), dtype=np.float64) / size**2


def sharpen_kernel(size: int, amount=1.0) -> np.ndarray:
    """Unit-sum unsharp mask: (1+a)δ - a*K_box. a=0 is identity."""
    validate_size(size, "sharpen")
    validate_strength("Sharpening amount", amount)
    kernel = -amount * box_kernel(size)
    kernel[size // 2, size // 2] += 1.0 + amount
    return kernel


def emboss_raw(size: int) -> np.ndarray:
    """Zero-sum directional ramp K[i,j]=i+j, i,j in [-m,m]."""
    validate_size(size)
    coordinates = np.arange(-(size // 2), size // 2 + 1, dtype=np.float64)
    return coordinates[:, None] + coordinates[None, :]


def emboss_kernel(size: int) -> np.ndarray:
    raw = emboss_raw(size)
    return raw / np.abs(raw).sum()


def sobel_raw(size: int) -> tuple[np.ndarray, np.ndarray]:
    """Generalized Sobel via binomial smoothing and an explicit 1-D convolution.

    S = binomial row of order N-1. D = [-1,0,1] convolved (full) with
    binomial row of order N-3. Kx=outer(S,D); Ky=outer(D,S).
    The larger kernels are constructed at their actual size, never resized.
    """
    validate_size(size)
    smoothing = np.array([comb(size - 1, i) for i in range(size)], dtype=np.float64)
    lower = [comb(size - 3, i) for i in range(size - 2)]
    derivative = np.zeros(size, dtype=np.float64)
    for i, coefficient in enumerate(lower):
        for j, difference in enumerate((-1, 0, 1)):
            derivative[i + j] += coefficient * difference
    return np.outer(smoothing, derivative), np.outer(derivative, smoothing)


def sobel_kernels(size: int) -> tuple[np.ndarray, np.ndarray]:
    kx, ky = sobel_raw(size)
    return kx / np.abs(kx).sum(), ky / np.abs(ky).sum()


def kernel_description(operation: SpatialOperation, size: int, amount=1.0) -> dict:
    """Raw/scaled coefficients and an exact divisor for readable matrix display.

    These are the unreversed kernels supplied to convolve(). Strength/reversal
    for emboss and thresholding for Sobel are output operations, not kernels.
    """
    validate_size(size, operation)
    if operation == "blur":
        entries = [("K_box", np.ones((size, size)), size**2)]
    elif operation == "sharpen":
        entries = [("K_sharp", sharpen_kernel(size, amount) * size**2, size**2)]
    elif operation == "emboss":
        raw = emboss_raw(size)
        entries = [("K_emboss", raw, float(np.abs(raw).sum()))]
    elif operation == "sobel":
        entries = [(name, raw, float(np.abs(raw).sum())) for name, raw in zip(("Kx", "Ky"), sobel_raw(size))]
    else:
        raise ValueError("Unknown spatial operation.")
    return {
        "operation": operation, "kernel_size": size,
        "kernels": [{"name": name, "coefficients": raw.tolist(), "divisor": divisor,
                     "normalized_sum": float((raw / divisor).sum())} for name, raw, divisor in entries],
        "convention": "Displayed coefficients divided by divisor give the kernel before true-convolution reversal.",
    }
