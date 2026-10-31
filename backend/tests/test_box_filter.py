"""Prefix-sum optimization equivalence, including reflected borders and large pads."""
import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.main import Settings, create_app
from backend.processing.box_filter import box_filter
from backend.processing.convolution import convolve
from backend.processing.kernels import BOX_KERNEL_SIZES, box_kernel, sharpen_kernel
from backend.processing.spatial import box_blur, sharpen
from backend.tests.test_api import encoded, decoded


@pytest.mark.parametrize('size', BOX_KERNEL_SIZES)
@pytest.mark.parametrize('shape', [(2, 3), (1, 1), (1, 5), (6, 1), (5, 9), (4, 7, 3)])
@pytest.mark.parametrize('kind', ['uint8', 'float64'])
def test_prefix_sums_match_direct(size, shape, kind):
    rng = np.random.default_rng(514)
    image = rng.integers(0, 256, size=shape, dtype=np.uint8) if kind == 'uint8' else rng.uniform(-100, 300, size=shape)
    original = image.copy()
    actual = box_filter(image, size)
    np.testing.assert_allclose(actual, convolve(image, box_kernel(size)), rtol=1e-12, atol=1e-10)
    assert actual.shape == shape and actual.dtype == np.float64
    np.testing.assert_array_equal(image, original)
    assert not np.shares_memory(image, actual)


@pytest.mark.parametrize('size', BOX_KERNEL_SIZES)
def test_constants_sums_alpha_and_sharpen_zero(size):
    image = np.full((3, 7, 4), (80, 120, 180, 128), dtype=np.uint8)
    assert box_kernel(size).sum() == pytest.approx(1)
    assert sharpen_kernel(size, 1.6).sum() == pytest.approx(1)
    np.testing.assert_array_equal(box_blur(image, size), image)
    np.testing.assert_array_equal(sharpen(image, size, 1.6), image)
    image[..., 0] = np.arange(21).reshape(3, 7) * 11
    image[..., 3] = np.arange(21).reshape(3, 7) * 12
    original = image.copy()
    np.testing.assert_array_equal(sharpen(image, size, 0), original)
    for function in (box_blur, sharpen):
        result = function(image, size)
        np.testing.assert_array_equal(result[..., 3], original[..., 3])
        np.testing.assert_array_equal(image, original)


@pytest.mark.parametrize('size', [21, 31])
def test_large_api_size_policy_and_coefficients(size):
    image = np.arange(3 * 7 * 3, dtype=np.uint8).reshape(3, 7, 3)
    with TestClient(create_app(Settings())) as client:
        for operation in ('blur', 'sharpen', 'emboss', 'sobel'):
            response = client.post('/process', files={'file': ('x.png', encoded(Image.fromarray(image)))}, data={'operation': operation, 'kernel_size': size})
            metadata = client.get('/kernels', params={'operation': operation, 'kernel_size': size})
            if operation in ('emboss', 'sobel'):
                assert response.status_code == metadata.status_code == 422
            else:
                result = decoded(response)
                assert result.size == (7, 3)
                assert metadata.status_code == 200
                assert len(metadata.json()['kernels'][0]['coefficients']) == size


@pytest.mark.parametrize('size', [12, 13, 20, 22, 30, 32, 33])
def test_no_intermediate_or_larger_sizes(size):
    with pytest.raises(ValueError): box_kernel(size)
