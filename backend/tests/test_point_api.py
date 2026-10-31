from io import BytesIO

from fastapi.testclient import TestClient
import numpy as np
from PIL import Image
import pytest

from backend.main import create_app, Settings
from backend.tests.test_api import encoded, decoded


@pytest.fixture
def client():
    with TestClient(create_app(Settings())) as client:
        yield client


def submit(client, source, operation, **parameters):
    return client.post('/process', files={'file': ('image.png', encoded(Image.fromarray(source)), 'image/png')},
                       data={'operation': operation, **parameters})


@pytest.mark.parametrize("operation,parameters,expected", [
    ('grayscale', {}, [62, 62, 62, 128]),
    ('inversion', {}, [155, 205, 235, 128]),
    ('gamma', {'gamma': 1}, [100, 50, 20, 128]),
    ('gamma', {'gamma': 2}, [39, 10, 2, 128]),
    ('gamma', {'red_gain': 2, 'green_gain': .5, 'saturation': 0}, [77, 77, 77, 128]),
    ('contrast', {'black_point': 20, 'white_point': 100}, [255, 96, 0, 128]),
    ('contrast', {'black_point': 20, 'white_point': 100, 'gamma': 2}, [255, 36, 0, 128]),
    ('contrast', {}, [255, 96, 0, 128]),
])
def test_point_requests(client, operation, parameters, expected):
    source = np.array([[[100, 50, 20, 128]]], dtype=np.uint8)
    response = submit(client, source, operation, **parameters)
    np.testing.assert_array_equal(np.array(decoded(response)), [[expected]])
    assert response.headers['x-output-width'] == '1'
    assert response.headers['x-output-height'] == '1'


@pytest.mark.parametrize('parameter', ['gamma', 'red_gain', 'green_gain', 'blue_gain', 'saturation', 'black_point', 'white_point'])
@pytest.mark.parametrize('value', ['NaN', 'Infinity', '-Infinity', 'not-a-number'])
def test_non_finite_or_non_numeric_parameters(client, parameter, value):
    source = np.zeros((1, 1, 3), dtype=np.uint8)
    parameters = {'black_point': 0, 'white_point': 255, parameter: value}
    response = submit(client, source, 'contrast', **parameters)
    assert response.status_code == 422
    assert 'detail' in response.json()


@pytest.mark.parametrize('parameters', [
    {'gamma': .09}, {'gamma': 3.01}, {'red_gain': -0.01}, {'green_gain': 2.01},
    {'blue_gain': -1}, {'saturation': 2.01}, {'black_point': 100, 'white_point': 100},
    {'black_point': 200, 'white_point': 100}, {'black_point': 0}, {'white_point': 255},
    {'black_point': -1, 'white_point': 255}, {'black_point': 0, 'white_point': 256},
])
def test_invalid_parameter_ranges(client, parameters):
    assert submit(client, np.zeros((1, 1, 3), dtype=np.uint8), 'contrast', **parameters).status_code == 422


@pytest.mark.parametrize('operation,parameters', [('grayscale', {'gamma': 2}), ('inversion', {'saturation': 0}),
    ('rotate_90', {'red_gain': 2}), ('gamma', {'black_point': 0, 'white_point': 255})])
def test_inapplicable_adjustments_rejected(client, operation, parameters):
    assert submit(client, np.zeros((1, 1, 3), dtype=np.uint8), operation, **parameters).status_code == 422


@pytest.mark.parametrize('source,expected', [
    ([[[0, 255, 1, 0], [30, 60, 90, 1], [100, 140, 200, 255]]], (30, 200, 'ready')),
    ([[[128, 128, 128, 255]]], (128, 128, 'constant')),
    ([[[0, 255, 20, 0]]], (None, None, 'transparent')),
])
def test_inspect_and_degenerate_contrast(client, source, expected):
    source = np.array(source, dtype=np.uint8)
    response = client.post('/inspect', files={'file': ('image.png', encoded(Image.fromarray(source)))})
    assert response.status_code == 200
    assert response.headers['cache-control'] == 'no-store'
    a, b, state = expected
    assert response.json() == {'width': source.shape[1], 'height': source.shape[0], 'black_point': a, 'white_point': b, 'range_status': state}
    result = np.array(decoded(submit(client, source, 'contrast')))
    if state != 'ready':
        np.testing.assert_array_equal(result, source)


def test_inspect_orientation(client):
    exif = Image.Exif(); exif[274] = 6
    response = client.post('/inspect', files={'file': ('image.png', encoded(Image.new('RGB', (3, 2), (10, 20, 30)), exif=exif))})
    assert response.status_code == 200
    assert response.json() == {'width': 2, 'height': 3, 'black_point': 10, 'white_point': 30, 'range_status': 'ready'}


def test_inspect_preserves_upload_guards():
    data = encoded(Image.new('RGB', (3, 2)))
    with TestClient(create_app(Settings(max_pixels=5))) as client:
        assert client.post('/inspect', files={'file': ('x.png', data)}).status_code == 413
    with TestClient(create_app(Settings(max_upload_bytes=len(data) - 1))) as client:
        assert client.post('/inspect', files={'file': ('x.png', data)}).status_code == 413
    with TestClient(create_app(Settings())) as client:
        assert client.post('/inspect', files={'file': ('x.png', b'corrupt')}).status_code == 400
        assert client.post('/inspect', files={'file': ('x.gif', encoded(Image.new('L', (3, 2)), 'GIF'))}).status_code == 415


def test_api_grayscale_alpha_expands_and_preserves_alpha(client):
    source = np.array([[[10, 0], [20, 128], [30, 255]]], dtype=np.uint8)
    result = np.array(decoded(submit(client, source, 'gamma', red_gain=2)))
    np.testing.assert_array_equal(result, [[[20, 10, 10, 0], [40, 20, 20, 128], [60, 30, 30, 255]]])


def test_openapi_exposes_operations_and_parameters(client):
    schema = client.get('/openapi.json').json()
    assert '/inspect' in schema['paths']
    form_schema = schema['components']['schemas']['Body_process_process_post']
    assert {'grayscale', 'inversion', 'gamma', 'contrast'} <= set(form_schema['properties']['operation']['enum'])
    assert form_schema['properties']['gamma']['default'] == 1
    assert form_schema['properties']['gamma']['minimum'] == .1
    assert form_schema['properties']['gamma']['maximum'] == 3
