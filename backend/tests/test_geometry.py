"""Hand-calculated non-square fixtures distinguish direction and row/column order."""
import numpy as np
import pytest

from backend.processing.geometry import OPERATIONS, horizontal_flip, vertical_flip, rotate_90

SOURCE = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.uint8)
EXPECTED = {
    "horizontal_flip": [[3, 2, 1], [6, 5, 4]],
    "vertical_flip": [[4, 5, 6], [1, 2, 3]],
    "rotate_90": [[4, 1], [5, 2], [6, 3]],
    "rotate_180": [[6, 5, 4], [3, 2, 1]],
    "rotate_270": [[3, 6], [2, 5], [1, 4]],
}


@pytest.mark.parametrize("name", OPERATIONS)
@pytest.mark.parametrize("channels", [None, 2, 3, 4])
def test_expected_mapping_and_independent_result(name, channels):
    source = SOURCE.copy()
    expected = np.array(EXPECTED[name], dtype=np.uint8)
    if channels:
        # Alpha, like every colour channel, has distinct and exact values.
        source = np.stack([source + 20 * c for c in range(channels)], axis=-1)
        expected = np.stack([expected + 20 * c for c in range(channels)], axis=-1)
    before = source.copy()
    result = OPERATIONS[name](source)
    np.testing.assert_array_equal(result, expected)
    np.testing.assert_array_equal(source, before)
    assert result.dtype == source.dtype
    assert result.shape == expected.shape
    assert not np.shares_memory(result, source)
    result.flat[0] = 255
    np.testing.assert_array_equal(source, before)


@pytest.mark.parametrize("flip", [horizontal_flip, vertical_flip])
def test_double_flip(flip):
    np.testing.assert_array_equal(flip(flip(SOURCE)), SOURCE)


def test_four_quarter_turns():
    result = SOURCE.copy()
    for _ in range(4):
        result = rotate_90(result)
    np.testing.assert_array_equal(result, SOURCE)


@pytest.mark.parametrize("shape", [(1, 3), (3, 1), (1, 1)])
@pytest.mark.parametrize("operation", OPERATIONS.values())
def test_single_pixel_axes_preserve_values(shape, operation):
    source = np.arange(np.prod(shape), dtype=np.uint8).reshape(shape)
    np.testing.assert_array_equal(np.sort(operation(source).ravel()), source.ravel())
