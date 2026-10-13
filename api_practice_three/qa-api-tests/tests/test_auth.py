import httpx
import pytest

BASE_URL = 'http://localhost:8000'

def test_login():
    resp = httpx.post(url=f'{BASE_URL}/api/v1/authentication/login',
                      json={"email": "a@b.c", "password": "123"},
                      )
    assert resp.status_code == 200
    assert "token" in resp.json()

@pytest.mark.parametrize("email, password, expected", [
    ("a@b.c", "123", 200),
    ("bad-email", "123", 422),
])
def test_login_data(email,password, expected):
    resp = httpx.post(url =f'{BASE_URL}/api/v1/authentication/login',
                      json = {"email": email, "password": password},)
    assert resp.status_code == expected

def test_unknown_route():
    resp = httpx.get(f'{BASE_URL}/api/v1/does-not-exist')
    assert resp.status_code == 404

def test_wrong_method_on_login():
    resp = httpx.get(f'{BASE_URL}/api/v1/authentication/login')
    assert resp.status_code == 405

def test_unknow_route():
    resp = httpx.get(f'{BASE_URL}/api/v1/fdsafads')
    assert resp.status_code == 404

def test_wrong_method():
    resp = httpx.get(f'{BASE_URL}/api/v1/authentication/login')
    assert resp.status_code == 405

def test_login_empty_password():
    resp = httpx.post(url =f'{BASE_URL}/api/v1/authentication/login',
                      json = {"email": '', "password": ""},)
    assert resp.status_code == 422

@pytest.mark.parametrize("method, url, expected", [
    ("GET", f"{BASE_URL}/api/v1/does-not-exist", 404),
    ("GET", f"{BASE_URL}/api/v1/authentication/login", 405),
    ("PUT", f"{BASE_URL}/api/v1/authentication/login", 405),
])
def test_bad_request(method , url , expected):
    resp = httpx.request(method , url)
    assert  resp.status_code == expected

def test_create_user():
    payload = {"email": "new@test.com",
        "password": "Password123",
        "firstName": "Tim",
        "lastName": "Sev",
        "middleName": "Test"}
    resp = httpx.post(f"{BASE_URL}/api/v1/users", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data['user']["email"] == "new@test.com"
    assert data['user']["firstName"] == "Tim"
    assert "id" in data['user']
