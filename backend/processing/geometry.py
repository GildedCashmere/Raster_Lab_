"""Exact pixel rearrangements. Coordinates are zero-based (row y, column x).

Inputs have shape (H, W) or (H, W, channels). Every function returns an
independent copy, preserving dtype and every channel, including alpha.
"""

import numpy as np


def horizontal_flip(image: np.ndarray) -> np.ndarray:
    """out[y, x] = image[y, W - 1 - x]: mirror left to right."""
    return image[:, ::-1, ...].copy()


def vertical_flip(image: np.ndarray) -> np.ndarray:
    """out[y, x] = image[H - 1 - y, x]: mirror top to bottom."""
    return image[::-1, :, ...].copy()


def rotate_90(image: np.ndarray) -> np.ndarray:
    """Clockwise: out[y, x] = image[H - 1 - x, y]; output shape (W, H)."""
    return image[::-1, :, ...].swapaxes(0, 1).copy()


def rotate_180(image: np.ndarray) -> np.ndarray:
    """out[y, x] = image[H - 1 - y, W - 1 - x]; shape unchanged."""
    return image[::-1, ::-1, ...].copy()


def rotate_270(image: np.ndarray) -> np.ndarray:
    """Clockwise: out[y, x] = image[x, W - 1 - y]; output shape (W, H)."""
    return image[:, ::-1, ...].swapaxes(0, 1).copy()


OPERATIONS = {
    "horizontal_flip": horizontal_flip,
    "vertical_flip": vertical_flip,
    "rotate_90": rotate_90,
    "rotate_180": rotate_180,
    "rotate_270": rotate_270,
}
