import numpy as np
from PIL import Image
from fastapi.testclient import TestClient
import pytest

from backend.main import create_app, Settings
from backend.processing.kernels import KERNEL_SIZES
from backend.tests.test_api import encoded, decoded
from backend.processing.spatial import box_blur, sharpen, emboss, sobel_edges


@pytest.fixture
def client():
    with TestClient(create_app(Settings())) as client:
        yield client


def source_image():
    source = np.zeros((13, 17, 4), dtype=np.uint8)
    source[..., 0] = np.arange(17) * 15
    source[..., 1] = np.arange(13)[:, None] * 20
    source[5:8, 7:10, 2] = 255
    source[..., 3] = np.arange(17) * 15
    return source


def submit(client, operation, **parameters):
    return client.post('/process', files={'file': ('source.png', encoded(Image.fromarray(source_image())), 'image/png')}, data={'operation': operation, **parameters})


@pytest.mark.parametrize('size', KERNEL_SIZES)
@pytest.mark.parametrize('operation,function', [('blur', box_blur), ('sharpen', sharpen), ('emboss', emboss), ('sobel', sobel_edges)])
def test_all_operations_all_sizes(client, size, operation, function):
    response = submit(client, operation, kernel_size=size)
    result = np.array(decoded(response))
    np.testing.assert_array_equal(result, function(source_image(), size))
    assert response.headers['x-output-width'] == '17'
    assert response.headers['x-output-height'] == '13'


@pytest.mark.parametrize('operation', ['blur', 'sharpen', 'emboss', 'sobel'])
def test_size_changes_actual_output(client, operation):
    small = np.array(decoded(submit(client, operation, kernel_size=3)))
    large = np.array(decoded(submit(client, operation, kernel_size=11)))
    assert not np.array_equal(small[..., :3], large[..., :3])


def test_filter_parameter_handling(client):
    np.testing.assert_array_equal(np.array(decoded(submit(client, 'sharpen', amount=0))), source_image())
    np.testing.assert_array_equal(np.array(decoded(submit(client, 'emboss', kernel_size=7, strength=1.5, reverse_relief='true'))), emboss(source_image(), 7, 1.5, True))
    binary = np.array(decoded(submit(client, 'sobel', kernel_size=9, binary_threshold='true', threshold=70)))
    np.testing.assert_array_equal(binary, sobel_edges(source_image(), 9, True, 70))
    assert set(np.unique(binary[..., :3])) <= {0, 255}


@pytest.mark.parametrize('size', [0, 2, 4, 6, 8, 10, 12, 3.1, 'NaN', 'Infinity', 'large'])
def test_invalid_sizes(client, size):
    assert submit(client, 'blur', kernel_size=size).status_code == 422


@pytest.mark.parametrize('operation,parameters', [
    ('sharpen', {'amount': -1}), ('sharpen', {'amount': 2.01}), ('sharpen', {'amount': 'NaN'}),
    ('emboss', {'strength': 'Infinity'}), ('emboss', {'strength': -1}), ('emboss', {'strength': 3}),
    ('emboss', {'reverse_relief': 'sometimes'}), ('sobel', {'binary_threshold': 'maybe'}),
    ('sobel', {'threshold': -1}), ('sobel', {'threshold': 256}), ('sobel', {'threshold': 'NaN'}),
    ('sobel', {'threshold': 'Infinity'}), ('blur', {'amount': .5}), ('sharpen', {'strength': 2}),
    ('blur', {'binary_threshold': True}), ('blur', {'reverse_relief': True}), ('blur', {'gamma': 2}),
    ('gamma', {'kernel_size': 5}), ('grayscale', {'amount': 2}), ('emboss', {'threshold': 10}),
])
def test_invalid_or_inapplicable_parameters(client, operation, parameters):
    assert submit(client, operation, **parameters).status_code == 422


@pytest.mark.parametrize('size', KERNEL_SIZES)
@pytest.mark.parametrize('operation,count', [('blur', 1), ('sharpen', 1), ('emboss', 1), ('sobel', 2)])
def test_kernel_metadata(client, size, operation, count):
    response = client.get('/kernels', params={'operation': operation, 'kernel_size': size, 'amount': .73})
    assert response.status_code == 200
    data = response.json()
    assert data['operation'] == operation and data['kernel_size'] == size
    assert len(data['kernels']) == count
    for matrix in data['kernels']:
        assert len(matrix['coefficients']) == size
        assert all(len(row) == size for row in matrix['coefficients'])
        assert matrix['divisor'] > 0


@pytest.mark.parametrize('parameters', [{'operation': 'inversion'}, {'operation': 'sobel', 'kernel_size': 4}, {'operation': 'sharpen', 'amount': 'NaN'}])
def test_invalid_metadata_parameters(client, parameters):
    assert client.get('/kernels', params=parameters).status_code == 422


def test_spatial_upload_guards():
    with TestClient(create_app(Settings(max_pixels=5))) as client:
        assert submit(client, 'sobel').status_code == 413
    with TestClient(create_app(Settings(max_upload_bytes=40))) as client:
        assert submit(client, 'blur').status_code == 413
