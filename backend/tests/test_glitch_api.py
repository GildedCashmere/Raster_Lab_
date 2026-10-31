import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.main import create_app, Settings
from backend.processing.glitch import glitch_effect
from backend.tests.test_api import encoded, decoded


@pytest.fixture
def client():
    with TestClient(create_app(Settings())) as client:
        yield client


SOURCE = np.arange(20 * 100 * 4, dtype=np.uint16).reshape(20, 100, 4).astype(np.uint8)


def submit(client, **settings):
    return client.post('/process', files={'file': ('original.png', encoded(Image.fromarray(SOURCE)), 'image/png')},
                       data={'operation': 'glitch', **settings})


@pytest.mark.parametrize('settings', [{}, {'shift': 100}, {'tear': 70, 'seed': 42}, {'noise': 60},
                                     {'scanlines': 75}, {'shift': 80, 'tear': 60, 'noise': 30, 'scanlines': 45, 'seed': 2**32-1}])
def test_api_dispatch_parameters_png_and_repeatability(client, settings):
    response = submit(client, **settings)
    actual = np.array(decoded(response))
    np.testing.assert_array_equal(actual, glitch_effect(SOURCE, **settings))
    np.testing.assert_array_equal(actual[..., 3], SOURCE[..., 3])
    assert response.headers['x-output-width'] == '100'
    assert response.headers['x-output-height'] == '20'
    assert response.content == submit(client, **settings).content


@pytest.mark.parametrize('name', ['shift', 'tear', 'noise', 'scanlines', 'seed'])
@pytest.mark.parametrize('value', ['-1', '1.5', 'NaN', 'Infinity', '-Infinity', 'no', '4294967296'])
def test_api_rejects_invalid_values(client, name, value):
    response = submit(client, **{name: value})
    assert response.status_code == 422
    assert 'detail' in response.json()


@pytest.mark.parametrize('name', ['shift', 'tear', 'noise', 'scanlines'])
def test_api_rejects_intensity_over_100(client, name):
    assert submit(client, **{name: 101}).status_code == 422


@pytest.mark.parametrize('settings', [{'gamma': .5}, {'kernel_size': 5}, {'amount': 2}, {'black_point': 0, 'white_point': 255}])
def test_inapplicable_settings_rejected(client, settings):
    assert submit(client, **settings).status_code == 422


@pytest.mark.parametrize('name', ['shift', 'tear', 'noise', 'scanlines', 'seed'])
def test_glitch_settings_do_not_leak_into_other_operations(client, name):
    assert submit(client, operation='grayscale', **{name: 1}).status_code == 422


def test_existing_validation_reused():
    with TestClient(create_app(Settings(max_pixels=1))) as client:
        assert submit(client).status_code == 413
    with TestClient(create_app(Settings(max_upload_bytes=10))) as client:
        assert submit(client).status_code == 413
    with TestClient(create_app()) as client:
        for data, status in [(b'', 400), (b'not an image', 400), (encoded(Image.new('RGB', (2, 2)), format='GIF'), 415)]:
            response = client.post('/process', files={'file': ('image.png', data)}, data={'operation': 'glitch'})
            assert response.status_code == status
