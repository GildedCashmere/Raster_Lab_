"""Hand calculations and an independent index-based reference convolution."""
import numpy as np
import pytest

from backend.processing.convolution import convolve
from backend.processing.kernels import (
    KERNEL_SIZES, box_kernel, sharpen_kernel, emboss_raw, emboss_kernel,
    sobel_raw, sobel_kernels, kernel_description,
)
from backend.processing.spatial import (
    box_blur, sharpen, emboss, sobel_edges, sobel_responses, normalized_magnitude,
)


def reflect_index(index, length):
    if length == 1:
        return 0
    period = 2 * (length - 1)
    folded = index % period
    return folded if folded < length else period - folded


def reference_convolution(source, kernel):
    # Independent scalar coordinate mapping; no np.pad or reversed-slice engine.
    out = np.zeros(source.shape, dtype=np.float64)
    radius = len(kernel) // 2
    for y in range(source.shape[0]):
        for x in range(source.shape[1]):
            for ky in range(len(kernel)):
                for kx in range(len(kernel)):
                    iy = reflect_index(y + radius - ky, source.shape[0])
                    ix = reflect_index(x + radius - kx, source.shape[1])
                    out[y, x] += float(kernel[ky, kx]) * source[iy, ix].astype(np.float64)
    return out


def test_true_convolution_asymmetric_hand_calculation():
    source = np.arange(1, 10, dtype=np.uint8).reshape(3, 3)
    kernel = np.array([[0, 0, 0], [0, 0, 1], [0, 0, 0]])
    # Convolution shifts source samples from the LEFT; correlation gives 6 at centre.
    np.testing.assert_array_equal(convolve(source, kernel), [[2, 1, 2], [5, 4, 5], [8, 7, 8]])


def test_known_blur_reflected_borders():
    source = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.uint8)
    expected = [[11 / 3, 4, 13 / 3], [8 / 3, 3, 10 / 3]]
    np.testing.assert_allclose(convolve(source, box_kernel(3)), expected)


@pytest.mark.parametrize('size', KERNEL_SIZES)
@pytest.mark.parametrize('shape', [(2, 3), (2, 3, 3), (1, 3), (3, 1), (1, 1)])
def test_convolution_reference_and_immutability(size, shape):
    source = np.arange(np.prod(shape), dtype=np.uint8).reshape(shape)
    # Asymmetric signed coefficients, including for pads larger than the image.
    kernel = np.arange(size**2, dtype=float).reshape(size, size) / size**2 - .5
    before = source.copy(); original_kernel = kernel.copy()
    result = convolve(source, kernel)
    np.testing.assert_allclose(result, reference_convolution(source, kernel), atol=1e-12)
    np.testing.assert_array_equal(source, before)
    np.testing.assert_array_equal(kernel, original_kernel)
    assert result.shape == source.shape
    assert result.dtype == np.float64
    assert not np.shares_memory(result, source)


def test_identity_and_signed_float_response():
    source = np.array([[0, 255, 0], [0, 255, 0]], dtype=np.uint8)
    np.testing.assert_array_equal(convolve(source, [[1]]), source)
    # Add an internal step to inspect signed values without reflected cancellation.
    response = convolve(np.array([[0, 0, 255, 255]], dtype=np.uint8), [[0, 0, 0], [-1, 0, 1], [0, 0, 0]])
    assert response[0, 1] == -255
    assert response.dtype.kind == 'f'


@pytest.mark.parametrize('size', [3, 11])
def test_row_block_boundary_matches_reference(size):
    source = np.arange(131 * 2 * 3, dtype=np.float64).reshape(131, 2, 3) / 10
    kernel = np.arange(size**2, dtype=float).reshape(size, size) / size**2 - .5
    np.testing.assert_allclose(convolve(source, kernel), reference_convolution(source, kernel), atol=1e-10)


@pytest.mark.parametrize('size', KERNEL_SIZES)
def test_kernel_properties_and_constant_images(size):
    image = np.full((4, 7, 3), 113, dtype=np.uint8)
    assert box_kernel(size).shape == (size, size)
    assert box_kernel(size).sum() == pytest.approx(1)
    np.testing.assert_array_equal(box_blur(image, size), image)
    for amount in [0, 1, 2]:
        assert sharpen_kernel(size, amount).sum() == pytest.approx(1)
        np.testing.assert_array_equal(sharpen(image, size, amount), image)
    assert emboss_kernel(size).sum() == pytest.approx(0, abs=1e-14)
    assert np.abs(emboss_kernel(size)).sum() == pytest.approx(1)
    np.testing.assert_array_equal(emboss(image, size), np.full_like(image, 128))
    np.testing.assert_array_equal(sobel_edges(image, size), np.zeros_like(image))
    for kernel in sobel_kernels(size):
        assert kernel.shape == (size, size)
        assert kernel.sum() == pytest.approx(0, abs=1e-14)
        assert np.abs(kernel).sum() == pytest.approx(1)


@pytest.mark.parametrize('size', KERNEL_SIZES)
def test_sharpen_zero_and_equivalent_kernel(size):
    source = np.arange(4 * 7 * 3, dtype=np.uint8).reshape(4, 7, 3)
    np.testing.assert_array_equal(sharpen(source, size, 0), source)
    expected_float = source.astype(float) + .7 * (source - reference_convolution(source, box_kernel(size)))
    expected = np.clip(np.rint(expected_float), 0, 255).astype(np.uint8)
    np.testing.assert_array_equal(sharpen(source, size, .7), expected)


def test_sharpen_final_clipping():
    source = np.zeros((3, 3, 3), dtype=np.uint8); source[1, 1] = 255
    signed = convolve(source, sharpen_kernel(3, 2))
    assert signed.min() < 0 and signed.max() > 255
    np.testing.assert_array_equal(sharpen(source, 3, 2), np.clip(np.rint(signed), 0, 255).astype(np.uint8))


def test_raw_emboss_and_sobel_3():
    np.testing.assert_array_equal(emboss_raw(3), [[-2, -1, 0], [-1, 0, 1], [0, 1, 2]])
    kx, ky = sobel_raw(3)
    np.testing.assert_array_equal(kx, [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
    np.testing.assert_array_equal(ky, [[-1, -2, -1], [0, 0, 0], [1, 2, 1]])
    np.testing.assert_array_equal(sobel_kernels(3)[0], kx / 8)


def test_generalized_sobel_known_5_and_7_vectors():
    kx, ky = sobel_raw(5)
    smoothing = np.array([1, 4, 6, 4, 1])
    derivative = np.array([-1, -2, 0, 2, 1])
    np.testing.assert_array_equal(kx, smoothing[:, None] * derivative[None, :])
    np.testing.assert_array_equal(ky, derivative[:, None] * smoothing[None, :])
    np.testing.assert_array_equal(sobel_raw(7)[0][0], [-1, -4, -5, 0, 5, 4, 1])


@pytest.mark.parametrize('size', KERNEL_SIZES)
def test_directional_step_responses(size):
    vertical = np.zeros((25, 31)); vertical[:, 15:] = 255
    gx, gy = sobel_responses(vertical, size)
    assert np.max(np.abs(gx)) > 100
    assert np.max(np.abs(gy)) < 1e-10
    assert gx[12, 14] < 0  # True convolution has the opposite sign to correlation.
    gx, gy = sobel_responses(vertical.T, size)
    assert np.max(np.abs(gy)) > 100
    assert np.max(np.abs(gx)) < 1e-10


@pytest.mark.parametrize('size', KERNEL_SIZES)
def test_emboss_reverse_relief_and_strength(size):
    ramp = np.arange(12, dtype=np.uint8).reshape(3, 4) * 15
    image = np.stack([ramp] * 3, axis=-1)
    expected_response = reference_convolution(ramp, emboss_kernel(size))
    # Avoid exact half-integers here: independent floating-point summation orders
    # can land on opposite sides of a rounding tie despite equivalent responses.
    expected = np.clip(np.rint(128 - 1.31 * expected_response), 0, 255).astype(np.uint8)
    np.testing.assert_array_equal(emboss(image, size, 1.31, True), np.stack([expected] * 3, axis=-1))
    np.testing.assert_array_equal(emboss(image, size, 0), np.full_like(image, 128))


def test_magnitude_display_normalization():
    gx = np.array([[0, 1e-6, 2e-6]]); gy = np.zeros_like(gx)
    np.testing.assert_array_equal(normalized_magnitude(gx, gy), [[0, 127.5, 255]])
    np.testing.assert_array_equal(normalized_magnitude(gx * 1e-6, gy), np.zeros_like(gx))
    # Combining both signed directions, without clipping negative responses first.
    np.testing.assert_array_equal(normalized_magnitude(np.array([[-3., 0]]), np.array([[-4., 0]])), [[255, 0]])


def test_threshold_uses_float_magnitude_before_rounding():
    # Gx magnitudes are [0,1,2,1,0], giving display values [0,127.5,255,127.5,0].
    # If rounded before comparing to 128, the two half-height edges turn white.
    image = np.array([[0, 0, 2, 4, 4]], dtype=np.uint8)
    expected = np.array([[0, 0, 255, 0, 0]], dtype=np.uint8)
    np.testing.assert_array_equal(sobel_edges(image, 3, True, 128), np.stack([expected] * 3, axis=-1))


@pytest.mark.parametrize('size', KERNEL_SIZES)
@pytest.mark.parametrize('operation', [box_blur, sharpen, emboss, sobel_edges])
@pytest.mark.parametrize('mode', ['L', 'LA', 'RGB', 'RGBA'])
def test_layout_alpha_ranges_and_input_unchanged(size, operation, mode):
    rgb = np.arange(3 * 4 * 3, dtype=np.uint8).reshape(3, 4, 3) * 7
    alpha = np.array([[0, 1, 20, 255], [60, 128, 180, 200], [255, 100, 0, 7]], dtype=np.uint8)
    source = rgb[..., 0] if mode == 'L' else np.stack((rgb[..., 0], alpha), axis=-1) if mode == 'LA' else rgb if mode == 'RGB' else np.concatenate((rgb, alpha[..., None]), axis=-1)
    before = source.copy()
    result = operation(source, size)
    assert result.shape == (3, 4, 4 if mode in ('LA', 'RGBA') else 3)
    assert result.dtype == np.uint8 and result.min() >= 0 and result.max() <= 255
    np.testing.assert_array_equal(source, before)
    assert not np.shares_memory(result, source)
    if mode in ('LA', 'RGBA'):
        np.testing.assert_array_equal(result[..., 3], alpha)
    if operation in (emboss, sobel_edges):
        np.testing.assert_array_equal(result[..., 0], result[..., 1])
        np.testing.assert_array_equal(result[..., 1], result[..., 2])


@pytest.mark.parametrize('size', KERNEL_SIZES)
def test_sobel_binary_threshold(size):
    source = np.zeros((15, 21, 3), dtype=np.uint8); source[:, 10:] = 255
    result = sobel_edges(source, size, True, 255)
    assert set(np.unique(result)) == {0, 255}
    assert (result[:, 9] == 255).all()
    np.testing.assert_array_equal(sobel_edges(np.zeros_like(source), size, True, 0), np.full_like(source, 255))


@pytest.mark.parametrize('operation', ['blur', 'sharpen', 'emboss', 'sobel'])
@pytest.mark.parametrize('size', KERNEL_SIZES)
def test_display_coefficients_match_processing(operation, size):
    metadata = kernel_description(operation, size, .73)
    expected = [box_kernel(size)] if operation == 'blur' else [sharpen_kernel(size, .73)] if operation == 'sharpen' else [emboss_kernel(size)] if operation == 'emboss' else sobel_kernels(size)
    for item, kernel in zip(metadata['kernels'], expected):
        np.testing.assert_allclose(np.array(item['coefficients']) / item['divisor'], kernel, atol=1e-15)


@pytest.mark.parametrize('kernel', [np.zeros((2, 2)), np.zeros((3, 5)), [], [[float('nan')]], [[float('inf')]]])
def test_invalid_convolution_kernel(kernel):
    with pytest.raises(ValueError):
        convolve(np.ones((2, 3)), kernel)


@pytest.mark.parametrize('function', [box_kernel, sharpen_kernel, emboss_kernel, sobel_kernels])
@pytest.mark.parametrize('size', [1, 4, 12, 3.0, True])
def test_invalid_filter_size(function, size):
    with pytest.raises(ValueError):
        function(size)
