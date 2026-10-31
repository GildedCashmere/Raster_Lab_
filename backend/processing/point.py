"""Point operations on 8-bit images; floating-point work, one final rounding.

RGB weights (0.299, 0.587, 0.114) approximate intensity/luma in encoded
RGB, not physical luminance. Grayscale inputs expand to RGB; alpha is
copied unchanged. No function mutates its input.
"""
import math

import numpy as np


# Retain the local helper names while sharing channel/export policy with filters.
from .channels import (
    split_rgb_alpha as _components,
    export_uint8 as _export,
    rgb_intensity as _intensity,
)


def _finite_range(name: str, value: float, minimum: float, maximum: float) -> None:
    if not math.isfinite(value) or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be finite and between {minimum} and {maximum}.")


def validate_adjustments(gamma=1.0, red_gain=1.0, green_gain=1.0, blue_gain=1.0, saturation=1.0):
    _finite_range("gamma", gamma, 0.1, 3.0)
    for name, value in (("red_gain", red_gain), ("green_gain", green_gain),
                        ("blue_gain", blue_gain), ("saturation", saturation)):
        _finite_range(name, value, 0.0, 2.0)


def validate_bounds(black_point: float | None, white_point: float | None):
    """Omit both for auto-range; explicit bounds must satisfy 0 <= a < b <= 255."""
    if black_point is None and white_point is None:
        return
    if black_point is None or white_point is None:
        raise ValueError("Provide both black_point and white_point, or omit both for auto-range.")
    _finite_range("black_point", black_point, 0, 255)
    _finite_range("white_point", white_point, 0, 255)
    if black_point >= white_point:
        raise ValueError("Input black point must be less than input white point (a < b).")


def visible_range(image: np.ndarray) -> tuple[int | None, int | None]:
    """Global channel extrema of pixels with alpha > 0; None if none visible.

    Partially transparent pixels count without weighting. Shared RGB bounds
    preserve colour relationships; hidden RGB values do not set the range.
    """
    if image.ndim == 2:
        values = image
    else:
        channels = image.shape[-1]
        values = image[..., :1] if channels < 3 else image[..., :3]
        if channels in (2, 4):
            values = values[image[..., -1] > 0]
    if values.size == 0:
        return None, None
    return int(np.min(values)), int(np.max(values))


def grayscale(image: np.ndarray) -> np.ndarray:
    """Y=.299R+.587G+.114B; R'=G'=B'=Y, preserving alpha."""
    colour, alpha = _components(image)
    y = _intensity(colour.astype(np.float64))
    return _export(np.repeat(y, 3, axis=-1), alpha)


def inversion(image: np.ndarray) -> np.ndarray:
    """Invert only colour channels: C'=255-C; alpha is unchanged."""
    colour, alpha = _components(image)
    return _export(255.0 - colour.astype(np.float64), alpha)


def _adjust(colour: np.ndarray, gamma: float, red_gain: float, green_gain: float,
            blue_gain: float, saturation: float) -> np.ndarray:
    """Float gamma -> gains -> intensity from gained RGB -> saturation.

    No intermediate clipping after gamma or gains; the caller exports once.
    colour is a private float copy, so in-place arithmetic cannot affect input.
    """
    # Neutral controls are exact identities, avoiding unnecessary float drift.
    if gamma != 1.0:
        colour /= 255.0
        np.power(colour, gamma, out=colour)
        colour *= 255.0
    colour *= np.array([red_gain, green_gain, blue_gain])
    if saturation == 1.0:
        return colour
    y = _intensity(colour)
    return y + saturation * (colour - y)


def gamma_correction(image: np.ndarray, gamma=1.0, red_gain=1.0, green_gain=1.0,
                     blue_gain=1.0, saturation=1.0) -> np.ndarray:
    """Original -> 255*(C/255)^gamma -> gains -> saturation -> uint8."""
    validate_adjustments(gamma, red_gain, green_gain, blue_gain, saturation)
    colour, alpha = _components(image)
    result = _adjust(colour.astype(np.float64), gamma, red_gain, green_gain, blue_gain, saturation)
    return _export(result, alpha)


def contrast_stretch(image: np.ndarray, black_point=None, white_point=None,
                     gamma=1.0, red_gain=1.0, green_gain=1.0, blue_gain=1.0,
                     saturation=1.0) -> np.ndarray:
    """Original -> clipped stretch -> gamma -> gains -> saturation -> uint8.

    Auto bounds ignore fully transparent pixels. A constant/no-visible-pixel
    automatic range skips only the base stretch, avoiding division by zero.
    Later adjustments still apply. Explicit invalid/equal bounds are rejected.
    """
    validate_bounds(black_point, white_point)
    validate_adjustments(gamma, red_gain, green_gain, blue_gain, saturation)
    colour, alpha = _components(image)
    working = colour.astype(np.float64)
    if black_point is None:
        black_point, white_point = visible_range(image)
    if black_point is not None and white_point is not None and black_point < white_point:
        working -= black_point
        working *= 255.0
        working /= white_point - black_point
        np.clip(working, 0, 255, out=working)
    result = _adjust(working, gamma, red_gain, green_gain, blue_gain, saturation)
    return _export(result, alpha)
