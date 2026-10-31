"""Small hand-calculated fixtures and an independent scalar reference."""
import math

import numpy as np
import pytest

from backend.processing.point import (
    grayscale, inversion, gamma_correction, contrast_stretch, visible_range,
)


def test_known_grayscale():
    source = np.array([[[255, 0, 0], [0, 255, 0], [0, 0, 255]],
                       [[255, 255, 255], [0, 0, 0], [12, 34, 56]]], dtype=np.uint8)
    expected = np.array([[76, 150, 29], [255, 0, 30]], dtype=np.uint8)
    np.testing.assert_array_equal(grayscale(source), np.stack([expected] * 3, axis=-1))


def test_known_inversion_and_double_inversion():
    source = np.array([[[0, 128, 255], [12, 34, 56]]], dtype=np.uint8)
    np.testing.assert_array_equal(inversion(source), [[[255, 127, 0], [243, 221, 199]]])
    np.testing.assert_array_equal(inversion(inversion(source)), source)


@pytest.mark.parametrize("gamma,source,expected", [
    (1, [0, 128, 255], [0, 128, 255]),
    (0.5, [0, 64, 255], [0, 128, 255]),
    (2, [64, 128, 192], [16, 64, 145]),
])
def test_known_gamma(gamma, source, expected):
    result = gamma_correction(np.array([[source]], dtype=np.uint8), gamma)
    np.testing.assert_array_equal(result, [[expected]])


def test_gamma_one_exhaustive_channel_values():
    source = np.arange(256, dtype=np.uint8).reshape(16, 16)
    expected = np.stack([source] * 3, axis=-1)
    np.testing.assert_array_equal(gamma_correction(expected, 1), expected)


def test_contrast_endpoints_intermediates_and_base_clipping():
    source = np.array([[[0, 50, 75], [100, 125, 150], [175, 200, 255]]], dtype=np.uint8)
    np.testing.assert_array_equal(contrast_stretch(source, 50, 150), [[[0, 0, 64], [128, 191, 255], [255, 255, 255]]])


def scalar_reference(pixel, gamma, gains, saturation, bounds=None):
    # Python scalar arithmetic/math.pow, independently of NumPy implementation.
    base = [float(value) for value in pixel]
    if bounds is not None:
        a, b = bounds
        base = [max(0, min(255, 255 * (value - a) / (b - a))) for value in base]
    gained = [255 * math.pow(value / 255, gamma) * gain for value, gain in zip(base, gains)]
    y = .299 * gained[0] + .587 * gained[1] + .114 * gained[2]
    return [max(0, min(255, round(y + saturation * (value - y)))) for value in gained]


@pytest.mark.parametrize("bounds", [None, (30, 180)])
def test_processing_order_and_float_precision(bounds):
    source = np.array([[[9, 81, 160], [128, 64, 32], [20, 200, 80]]], dtype=np.uint8)
    expected = [[scalar_reference(pixel, .5, (.73, 1.19, .42), .57, bounds) for pixel in source[0]]]
    kwargs = dict(gamma=.5, red_gain=.73, green_gain=1.19, blue_gain=.42, saturation=.57)
    result = gamma_correction(source, **kwargs) if bounds is None else contrast_stretch(source, *bounds, **kwargs)
    np.testing.assert_array_equal(result, expected)


def test_no_clipping_between_gains_and_saturation():
    source = np.array([[[200, 10, 20]]], dtype=np.uint8)
    # Gains give (400,10,20); Y=127.75; s=.5 gives (263.875,68.875,73.875).
    np.testing.assert_array_equal(gamma_correction(source, red_gain=2, saturation=.5), [[[255, 69, 74]]])


def test_saturation_zero_uses_intensity_after_gains():
    source = np.array([[[100, 50, 20]]], dtype=np.uint8)
    # Gained RGB=(200,25,20), intensity=76.755 -> 77.
    np.testing.assert_array_equal(gamma_correction(source, red_gain=2, green_gain=.5, saturation=0), [[[77, 77, 77]]])


@pytest.mark.parametrize("operation", [grayscale, inversion, gamma_correction, contrast_stretch])
@pytest.mark.parametrize("channels", [3, 4])
def test_alpha_dimensions_immutability(operation, channels):
    source = np.array([[[10, 20, 30, 0], [60, 80, 90, 128], [200, 210, 220, 255]],
                       [[15, 25, 35, 1], [65, 85, 95, 200], [205, 215, 225, 100]]], dtype=np.uint8)[..., :channels]
    before = source.copy()
    result = operation(source)
    assert result.shape == source.shape
    assert result.dtype == np.uint8
    assert not np.shares_memory(source, result)
    np.testing.assert_array_equal(source, before)
    if channels == 4:
        np.testing.assert_array_equal(result[..., 3], source[..., 3])


@pytest.mark.parametrize("operation", [grayscale, inversion, gamma_correction, contrast_stretch])
@pytest.mark.parametrize("alpha", [False, True])
def test_grayscale_inputs_expand_with_alpha_preserved(operation, alpha):
    source = np.array([[0, 64, 128], [160, 192, 255]], dtype=np.uint8)
    if alpha:
        source = np.stack([source, np.array([[0, 1, 128], [200, 254, 255]], dtype=np.uint8)], axis=-1)
    result = operation(source)
    assert result.shape == (2, 3, 4 if alpha else 3)
    np.testing.assert_array_equal(result[..., 0], result[..., 1])
    np.testing.assert_array_equal(result[..., 1], result[..., 2])
    if alpha:
        np.testing.assert_array_equal(result[..., 3], source[..., 1])


def test_range_ignores_hidden_pixels_and_uses_shared_channels():
    source = np.array([[[0, 255, 1, 0], [40, 60, 80, 1], [100, 140, 200, 255]]], dtype=np.uint8)
    assert visible_range(source) == (40, 200)
    expected = [[[0, 255, 0, 0], [0, 32, 64, 1], [96, 159, 255, 255]]]
    np.testing.assert_array_equal(contrast_stretch(source), expected)


@pytest.mark.parametrize("value", [0, 128, 255])
def test_constant_auto_range_unchanged(value):
    source = np.full((2, 3, 3), value, dtype=np.uint8)
    assert visible_range(source) == (value, value)
    np.testing.assert_array_equal(contrast_stretch(source), source)


def test_fully_transparent_auto_range_unchanged():
    source = np.array([[[1, 230, 55, 0], [0, 22, 255, 0]]], dtype=np.uint8)
    assert visible_range(source) == (None, None)
    np.testing.assert_array_equal(contrast_stretch(source), source)


def test_constant_base_still_allows_later_adjustments_and_manual_bounds():
    source = np.full((1, 1, 3), 100, dtype=np.uint8)
    np.testing.assert_array_equal(contrast_stretch(source, gamma=2), [[[39, 39, 39]]])
    np.testing.assert_array_equal(contrast_stretch(source, 50, 150), [[[128, 128, 128]]])


@pytest.mark.parametrize("operation", [gamma_correction, contrast_stretch])
@pytest.mark.parametrize("parameter,value", [("gamma", 0), ("gamma", 3.1), ("gamma", float('nan')), ("gamma", float('inf')),
    ("red_gain", -1), ("green_gain", 2.1), ("blue_gain", float('-inf')), ("saturation", float('nan')), ("saturation", 3)])
def test_invalid_adjustments(operation, parameter, value):
    with pytest.raises(ValueError):
        operation(np.zeros((1, 1, 3), dtype=np.uint8), **{parameter: value})


@pytest.mark.parametrize("bounds", [(0, 0), (255, 255), (50, 40), (-1, 100), (0, 256), (float('nan'), 255), (0, float('inf')), (None, 255), (0, None)])
def test_invalid_bounds(bounds):
    with pytest.raises(ValueError):
        contrast_stretch(np.zeros((1, 1, 3), dtype=np.uint8), *bounds)
