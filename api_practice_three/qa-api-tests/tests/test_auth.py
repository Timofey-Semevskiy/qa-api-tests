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
    # пустой password  выдаст ошибку
    resp = httpx.post(f"{BASE_URL}/api/v1/authentication/login",
                      json={"email": "a@b.c", "password": ""})
    assert resp.status_code == 422


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
    # 1. Создаём
    payload = {
        "email": f"test{time.time()}@test.com",
        "password": "Password123",
        "firstName": "Tim",
        "lastName": "Sev",
        "middleName": "Test"
    }
    resp = httpx.post(f"{BASE_URL}/api/v1/users", json=payload)
    assert resp.status_code == 200

    # 2. Достаём id из ответа
    user_id = resp.json()["user"]["id"]

    # 3. Удаляем
    resp = httpx.delete(f"{BASE_URL}/api/v1/users/{user_id}")
    assert resp.status_code == 200

    # 4. Проверяем, что пользователя нету
    resp = httpx.get(f"{BASE_URL}/api/v1/users/{user_id}")
    assert resp.status_code == 404

