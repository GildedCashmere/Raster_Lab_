"""Known coordinate/row fixtures, deterministic streams and colour invariants."""
import numpy as np
import pytest

from backend.processing.glitch import glitch_effect, tearing_bands, validate_glitch


@pytest.mark.parametrize("channels", [None, 1, 2, 3, 4])
def test_zero_exact_decoded_samples_and_independent_copy(channels):
    shape = (3, 7) if channels is None else (3, 7, channels)
    image = np.arange(np.prod(shape), dtype=np.uint8).reshape(shape)
    before = image.copy()
    expected = image if channels in (3, 4) else np.repeat(
        image[..., None] if channels is None else image[..., :1], 3, axis=-1)
    if channels == 2:
        expected = np.concatenate((expected, image[..., 1:]), axis=-1)
    actual = glitch_effect(image)
    np.testing.assert_array_equal(actual, expected)
    assert not np.shares_memory(actual, image)
    np.testing.assert_array_equal(image, before)


def test_known_rgb_shift_and_wrap():
    image = np.arange(300, dtype=np.uint16).reshape(1, 100, 3).astype(np.uint8)
    actual = glitch_effect(image, shift=100)  # d = 3, red right / blue left
    np.testing.assert_array_equal(actual[0, 0], [image[0, 97, 0], image[0, 0, 1], image[0, 3, 2]])
    np.testing.assert_array_equal(actual[0, 99], [image[0, 96, 0], image[0, 99, 1], image[0, 2, 2]])
    np.testing.assert_array_equal(actual[..., 1], image[..., 1])


@pytest.mark.parametrize("width,distance", [(1, 0), (50, 2), (150, 4)])
def test_shift_rounds_nearest_ties_even(width, distance):
    image = np.arange(width * 3, dtype=np.uint16).reshape(1, width, 3).astype(np.uint8)
    actual = glitch_effect(image, shift=100)
    for x in range(width):
        assert actual[0, x, 0] == image[0, (x - distance) % width, 0]
        assert actual[0, x, 2] == image[0, (x + distance) % width, 2]


@pytest.mark.parametrize("intensity,expected_odd", [(0, [100, 200, 240]), (50, [58, 115, 138]), (100, [15, 30, 36])])
def test_scanline_parity(intensity, expected_odd):
    image = np.tile(np.array([100, 200, 240], dtype=np.uint8), (5, 3, 1))
    actual = glitch_effect(image, scanlines=intensity)
    np.testing.assert_array_equal(actual[::2], image[::2])
    np.testing.assert_array_equal(actual[1::2], np.tile(expected_odd, (2, 3, 1)))


def test_known_seeded_tearing_strips():
    image = np.broadcast_to(np.arange(100, dtype=np.uint8)[None, :, None], (20, 100, 3)).copy()
    expected = image.copy()
    # Fixed seed 42 / stream zero; independently recorded strip coordinates.
    bands = [(9, 10, 4), (18, 19, 1), (6, 7, 2), (19, 20, -4)]
    for start, stop, distance in bands:
        for x in range(100):
            expected[start:stop, x] = image[start:stop, (x - distance) % 100]
    np.testing.assert_array_equal(glitch_effect(image, tear=30, seed=42), expected)
    assert np.count_nonzero(np.any(image != expected, axis=(1, 2))) == 4


def test_known_noise_is_shared_across_rgb():
    image = np.full((2, 3, 3), 128, dtype=np.uint8)
    expected = np.array([[74, 124, 87], [70, 148, 140]], dtype=np.uint8)
    actual = glitch_effect(image, noise=100, seed=42)
    for c in range(3):
        np.testing.assert_array_equal(actual[..., c], expected)


def test_noise_precedes_scanline_and_final_clipping():
    image = np.full((2, 3, 3), 250, dtype=np.uint8)
    # The second row includes noise pushing values above 255; don't clip first.
    expected = np.array([[196, 246, 209], [29, 40, 39]], dtype=np.uint8)
    actual = glitch_effect(image, noise=100, scanlines=100, seed=42)
    np.testing.assert_array_equal(actual[..., 0], expected)


def test_rgb_shift_before_known_tearing(monkeypatch):
    monkeypatch.setattr('backend.processing.glitch.tearing_bands', lambda *args: [(1, 2, -2)])
    image = np.arange(2 * 100 * 3, dtype=np.uint16).reshape(2, 100, 3).astype(np.uint8)
    actual = glitch_effect(image, shift=100, tear=1)
    for y, band_shift in [(0, 0), (1, -2)]:
        for x in range(100):
            for c, channel_shift in enumerate([3, 0, -3]):
                assert actual[y, x, c] == image[y, (x - band_shift - channel_shift) % 100, c]


def test_separate_noise_stream_not_consumed_by_tearing():
    image = np.full((20, 100, 3), 128, dtype=np.uint8)
    # Tearing a constant image is neutral, but consumes random numbers.
    np.testing.assert_array_equal(glitch_effect(image, tear=100, noise=50, seed=42),
                                  glitch_effect(image, tear=0, noise=50, seed=42))


def test_changing_noise_does_not_redraw_bands(monkeypatch):
    captured = []
    def record(height, width, intensity, rng):
        bands = tearing_bands(height, width, intensity, rng)
        captured.append(bands)
        return bands
    monkeypatch.setattr('backend.processing.glitch.tearing_bands', record)
    image = np.zeros((20, 100, 3), dtype=np.uint8)
    glitch_effect(image, tear=30, noise=0, seed=42)
    glitch_effect(image, tear=30, noise=100, seed=42)
    assert captured[0] == captured[1] == [(9, 10, 4), (18, 19, 1), (6, 7, 2), (19, 20, -4)]


@pytest.mark.parametrize("settings", [dict(tear=75), dict(noise=50), dict(shift=80, tear=70, noise=40, scanlines=65)])
def test_seed_repeatability_and_different_seed(settings):
    image = np.arange(20 * 100 * 3, dtype=np.uint16).reshape(20, 100, 3).astype(np.uint8)
    a = glitch_effect(image, seed=42, **settings)
    np.testing.assert_array_equal(a, glitch_effect(image, seed=42, **settings))
    assert not np.array_equal(a, glitch_effect(image, seed=43, **settings))


@pytest.mark.parametrize("shape", [(1, 1), (1, 7), (7, 1), (2, 3), (7, 13), (130, 5)])
@pytest.mark.parametrize("channels", [2, 3, 4])
def test_tiny_non_square_alpha_dimensions_and_immutability(shape, channels):
    image = np.arange(np.prod(shape) * channels, dtype=np.uint32).reshape(*shape, channels).astype(np.uint8)
    before = image.copy()
    actual = glitch_effect(image, shift=100, tear=100, noise=100, scanlines=100, seed=2**32-1)
    assert actual.shape == (*shape, 4 if channels in (2, 4) else 3)
    assert actual.dtype == np.uint8 and actual.min() >= 0 and actual.max() <= 255
    if channels in (2, 4):
        np.testing.assert_array_equal(actual[..., -1], image[..., -1])
    np.testing.assert_array_equal(image, before)


@pytest.mark.parametrize("name", ["shift", "tear", "noise", "scanlines", "seed"])
@pytest.mark.parametrize("value", [-1, 1.5, float('nan'), float('inf'), True, '1'])
def test_processing_rejects_non_integer_values(name, value):
    with pytest.raises(ValueError):
        validate_glitch(**{name: value})


@pytest.mark.parametrize("name,maximum", [("shift", 100), ("tear", 100), ("noise", 100), ("scanlines", 100), ("seed", 2**32-1)])
def test_processing_range(name, maximum):
    validate_glitch(**{name: maximum})
    with pytest.raises(ValueError):
        validate_glitch(**{name: maximum + 1})
