import httpx
import pytest
import time
from models import MeResponse, UserResponse


def find_token(obj):
    if isinstance(obj, dict):
        for value in obj.values():
            found = find_token(value)
            if found:
                return found
    elif isinstance(obj, str) and obj.count(".") == 2:
        return obj
    return None


def get_token(http_client, email, password):
    resp = http_client.post("/api/v1/authentication/login",
                            json={"email": email, "password": password})
    assert resp.status_code == 200
    token = find_token(resp.json())
    # Если токена нет, показываем весь ответ
    assert token is not None, f"Токен не найден в ответе: {resp.json()}"
    return token


def make_user_payload(email, password):
    return {
        "email": email,
        "password": password,
        "firstName": "Tim",
        "lastName": "Sev",
        "middleName": "Test",
    }


@pytest.mark.parametrize("email, password, expected", [
    ("bad-email", "123", 422),  # битый формат email → 422
    ("a@b.c", "", 401),         # пустой пароль → 401
])
def test_login_bad_data(http_client, email, password, expected):
    resp = http_client.post("/api/v1/authentication/login",
                            json={"email": email, "password": password})
    assert resp.status_code == expected


def test_login_success(http_client, created_user):
    # логинимся пользователем, которого только что создали
    email, password = created_user
    resp = http_client.post("/api/v1/authentication/login",
                            json={"email": email, "password": password})
    assert resp.status_code == 200
    # в ответе должен быть JWT
    assert find_token(resp.json()) is not None


def test_login_wrong_password(http_client, created_user):
    email, _ = created_user
    resp = http_client.post("/api/v1/authentication/login",
                            json={"email": email, "password": "wrong_pass"})
    assert resp.status_code == 401  # пользователь есть, пароля нет → 401, не 422


# ---------- Ошибки запросов ----------

@pytest.mark.parametrize("method, path, expected", [
    ("GET", "/api/v1/does-not-exist", 404),
    ("GET", "/api/v1/authentication/login", 405),
    ("PUT", "/api/v1/authentication/login", 405),
])
def test_bad_requests(http_client, method, path, expected):
    # httpx.request принимает метод как строку
    resp = http_client.request(method, path)
    assert resp.status_code == expected


# ---------- Создание пользователя ----------

def test_create_user(http_client, test_email, test_password):
    resp = http_client.post("/api/v1/users",
                            json=make_user_payload(test_email, test_password))
    assert resp.status_code == 200
    data = UserResponse(**resp.json())
    assert data.email == test_email
    assert data.user.firstName == "Tim"


def test_me_returns_token_owner_data(http_client, created_user, test_password):
    email, password = created_user
    token = get_token(http_client, email, password)
    resp = http_client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200

    me = MeResponse(**resp.json())  # упадёт, если схема ответа изменилась
    assert me.email == email


# ---------- CRUD ----------

def test_user_crud(http_client, test_email, test_password):
    # CREATE
    resp = http_client.post("/api/v1/users",
                            json=make_user_payload(test_email, test_password))
    assert resp.status_code == 200
    user_id = resp.json()["user"]["id"]

    # DELETE: эндпоинт защищён, нужен токен
    token = get_token(http_client, test_email, test_password)
    resp = http_client.delete(f"/api/v1/users/{user_id}",
                              headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

    # VERIFY: пользователя больше нет.
    resp = http_client.get(f"/api/v1/users/{user_id}",
                           headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404


# ---------- Защищённые эндпоинты ----------

def test_protected_endpoint_without_token(http_client):
    # без токена 
    resp = http_client.get("/api/v1/users/me")
    assert resp.status_code == 401


def test_protected_endpoint_bad_token(http_client):
    # мусорный токен 
    resp = http_client.get("/api/v1/users/me",
                           headers={"Authorization": "Bearer garbage_token_123"})
    assert resp.status_code == 401
