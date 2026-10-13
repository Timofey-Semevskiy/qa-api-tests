import httpx
import pytest

BASE_URL = 'http://localhost:8000'

@pytest.fixture
def token():
    resp = httpx.post(f'{BASE_URL}/api/v1/authentication/login',
                      json={"email": "a@b.c", "password": "123"})
    assert resp.status_code == 200
    return resp.json()['token']['accessToken']
