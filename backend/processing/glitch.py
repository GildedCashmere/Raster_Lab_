"""Still-image signal effects: wrapped RGB remapping, noise, then row modulation.

The local PCG64 streams are independently spawned for tearing and noise. Alpha
never enters the pipeline: it stays at its original coordinates, byte for byte.
"""
from math import ceil

import numpy as np

from backend.processing.channels import split_rgb_alpha

DEFAULT_SEED = 0
MAX_SEED = 2**32 - 1


def validate_glitch(shift=0, tear=0, noise=0, scanlines=0, seed=DEFAULT_SEED):
    """Require integer percentages and an unsigned 32-bit integer seed."""
    for name, value, maximum in (
        ("shift", shift, 100), ("tear", tear, 100), ("noise", noise, 100),
        ("scanlines", scanlines, 100), ("seed", seed, MAX_SEED),
    ):
        if (isinstance(value, (bool, np.bool_))
                or not isinstance(value, (int, np.integer))
                or not 0 <= value <= maximum):
            raise ValueError(f"{name} must be an integer between 0 and {maximum}.")


def tearing_bands(height: int, width: int, intensity: int,
                  rng: np.random.Generator) -> list[tuple[int, int, int]]:
    """Return (start, stop, displacement) strips; never cover every row at once.

    ceil(12*t) bands, heights about 0.5--4% of H, displacement up to 12%*t
    of W (at least one pixel when feasible). Bands may overlap; apply in order.
    A one-row or one-column image has no useful tearing and is left alone.
    """
    if intensity == 0 or height < 2 or width < 2:
        return []
    t = intensity / 100
    low = max(1, round(0.005 * height))
    high = min(height - 1, max(low, round(0.04 * height)))
    low = min(low, high)
    maximum = min(width - 1, max(1, round(0.12 * width * t)))
    bands = []
    for _ in range(ceil(12 * t)):
        band_height = int(rng.integers(low, high + 1))
        start = int(rng.integers(0, height - band_height + 1))
        distance = int(rng.integers(1, maximum + 1))
        distance *= -1 if rng.integers(0, 2) == 0 else 1
        bands.append((start, start + band_height, distance))
    return bands


def glitch_effect(image: np.ndarray, shift=0, tear=0, noise=0, scanlines=0,
                  seed=DEFAULT_SEED) -> np.ndarray:
    """Original -> RGB shift -> tearing -> monochrome noise -> scanlines -> export.

    R[y,x] samples x-d and B[y,x] samples x+d modulo W, with
    d=round(.03*W*shift/100), nearest ties to even. G stays put. Each tearing
    band rolls all RGB together. Add one uniform(-64*n,64*n) value per pixel
    to all channels. Odd rows multiply by 1-.85*s. Only the final result is
    rounded (nearest, ties to even) and clipped. Input is never modified.

    L/LA expand to RGB/RGBA like other colour tools. The all-zero path copies
    those decoded samples exactly, without float conversion. Nonzero effects
    use one float32 RGB workspace and bounded noise blocks, not float64 copies.
    """
    validate_glitch(shift, tear, noise, scanlines, seed)
    rgb, alpha = split_rgb_alpha(image)
    height, width = rgb.shape[:2]
    if height == 0 or width == 0:
        raise ValueError("Image dimensions must be positive.")
    if not any((shift, tear, noise, scanlines)):
        return rgb.copy() if alpha is None else np.concatenate((rgb, alpha), axis=-1)

    work = rgb.astype(np.float32)
    if shift:
        distance = round(0.03 * width * (shift / 100))
        work[..., 0] = np.roll(work[..., 0], distance, axis=1)
        work[..., 2] = np.roll(work[..., 2], -distance, axis=1)

    tear_stream, noise_stream = np.random.SeedSequence(int(seed)).spawn(2)
    tear_rng = np.random.Generator(np.random.PCG64(tear_stream))
    noise_rng = np.random.Generator(np.random.PCG64(noise_stream))
    for start, stop, distance in tearing_bands(height, width, tear, tear_rng):
        work[start:stop] = np.roll(work[start:stop], distance, axis=1)

    if noise:
        amplitude = np.float32(64 * noise / 100)
        for start in range(0, height, 128):
            block = work[start:start + 128]
            # One scalar per pixel, broadcast to RGB; reuse the noise allocation.
            eta = noise_rng.random(block.shape[:2], dtype=np.float32)
            eta *= 2 * amplitude
            eta -= amplitude
            block += eta[..., None]
    if scanlines:
        work[1::2] *= np.float32(1 - 0.85 * scanlines / 100)

    # Reuse the owned workspace for final conversion to bound peak memory.
    np.rint(work, out=work)
    np.clip(work, 0, 255, out=work)
    output = np.empty((height, width, 4 if alpha is not None else 3), dtype=np.uint8)
    output[..., :3] = work
    if alpha is not None:
        output[..., 3:] = alpha
    return output
