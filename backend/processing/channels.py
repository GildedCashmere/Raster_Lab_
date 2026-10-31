"""Shared NumPy channel layout, weighted intensity, and final uint8 export."""
import numpy as np


def split_rgb_alpha(image: np.ndarray) -> tuple[np.ndarray, np.ndarray | None]:
    """Expand L/LA to RGB/RGBA; return colour and a separate unchanged alpha."""
    if image.dtype != np.uint8 or image.ndim not in (2, 3):
        raise ValueError("Expected a uint8 grayscale, RGB, or RGBA image.")
    if image.ndim == 2:
        return np.repeat(image[..., None], 3, axis=-1), None
    if image.shape[-1] not in (1, 2, 3, 4):
        raise ValueError("Expected one to four image channels.")
    channels = image.shape[-1]
    colour = image[..., :1] if channels < 3 else image[..., :3]
    if channels < 3:
        colour = np.repeat(colour, 3, axis=-1)
    alpha = image[..., -1:] if channels in (2, 4) else None
    return colour, alpha


def export_uint8(colour: np.ndarray, alpha: np.ndarray | None) -> np.ndarray:
    """One final round (nearest, ties to even), clip, and cast; copy alpha."""
    rgb = np.clip(np.rint(colour), 0, 255).astype(np.uint8)
    return rgb if alpha is None else np.concatenate((rgb, alpha), axis=-1)


def rgb_intensity(rgb: np.ndarray) -> np.ndarray:
    """Float RGB intensity/luma approximation; not physical luminance."""
    return 0.299 * rgb[..., 0:1] + 0.587 * rgb[..., 1:2] + 0.114 * rgb[..., 2:3]
