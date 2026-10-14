import httpx
import pytest
import time

BASE_URL = 'http://localhost:8000'


@pytest.mark.parametrize("email, password, expected", [
    ("a@b.c", "123", 200),        # валидные данные → 200
    ("bad-email", "123", 422),    # битый email → 422
])
def test_login_data(email, password, expected):
    resp = httpx.post(f"{BASE_URL}/api/v1/authentication/login",
                      json={"email": email, "password": password})
    assert resp.status_code == expected


def test_unknown_route():
    # несуществующий маршрут → 404
    resp = httpx.get(f"{BASE_URL}/api/v1/does-not-exist")
    assert resp.status_code == 404


def test_wrong_method_on_login():
    # GET на эндпоинт, где только POST → 405
    resp = httpx.get(f"{BASE_URL}/api/v1/authentication/login")
    assert resp.status_code == 405

def test_login_empty_password():
    # пустой password → не проходит авторизацию → 401
    resp = httpx.post(f"{BASE_URL}/api/v1/authentication/login",
                      json={"email": "a@b.c", "password": ""})
    assert resp.status_code == 401


@pytest.mark.parametrize("method, url, expected", [
    ("GET", f"{BASE_URL}/api/v1/does-not-exist", 404),
    ("GET", f"{BASE_URL}/api/v1/authentication/login", 405),
    ("PUT", f"{BASE_URL}/api/v1/authentication/login", 405),
])
def test_bad_requests(method, url, expected):
    # httpx.request принимает метод как строку
    resp = httpx.request(method, url)
    assert resp.status_code == expected



def test_create_user():
    payload = {
        "email": f"test{time.time()}@test.com",  # уникальный email
        "password": "Password123",
        "firstName": "Tim",
        "lastName": "Sev",
        "middleName": "Test"
    }
    resp = httpx.post(f"{BASE_URL}/api/v1/users", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    # поля лежат в обёртке user
    assert data["user"]["email"] == payload["email"]
    assert data["user"]["firstName"] == "Tim"
    assert "id" in data["user"]



def test_user_crud():
    payload = {
        "email": f"test{time.time()}@test.com",
        "password": "Password123",
        "firstName": "Tim",
        "lastName": "Sev",
        "middleName": "Test"
    }
    resp = httpx.post(f"{BASE_URL}/api/v1/users", json=payload)
    assert resp.status_code == 200


    user_id = resp.json()["user"]["id"]


    resp = httpx.delete(f"{BASE_URL}/api/v1/users/{user_id}")
    assert resp.status_code == 200

    resp = httpx.get(f"{BASE_URL}/api/v1/users/{user_id}")
    assert resp.status_code == 404

def get_token(email="a@b.c", password="123"):
    """Помощник: логинимся и возвращаем токен."""
    resp = httpx.post(f"{BASE_URL}/api/v1/authentication/login",
                      json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]

def test_protected_endpoint_with_token():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    resp = httpx.get(f"{BASE_URL}/api/v1/users/me", headers=headers)  # ← защищённый эндпоинт из Swagger
    assert resp.status_code == 200


def test_protected_endpoint_without_token():
    resp = httpx.get(f"{BASE_URL}/api/v1/users/me")
    assert resp.status_code == 401


def test_protected_endpoint_bad_token():
    headers = {"Authorization": "Bearer garbage_token_123"}
    resp = httpx.get(f"{BASE_URL}/api/v1/users/me", headers=headers)
    assert resp.status_code == 401


def test_print_login_response():
    resp = httpx.post(f"{BASE_URL}/api/v1/authentication/login",
                      json={"email": "a@b.c", "password": "123"})
    print(resp.json())
