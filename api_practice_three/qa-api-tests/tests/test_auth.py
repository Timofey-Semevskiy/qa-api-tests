import httpx
import pytest

def find_token(obj):
    if isinstance(obj, dict):
        for value in obj.values():
            found = find_token(value)
            if found:
                return found
    elif isinstance(obj, str) and obj.count(".") == 2:
        return obj
    return None

def get_token(http_client,email,password):
    resp = http_client.post("/api/v1/authentication/login",
                            json={"email": email, "password": password})
    assert resp.status_code == 200
    token = find_token(resp.json())
    # Если нету токена показываем весь ответ
    assert token is not None , f"Токен не найден в ответе: {resp.json()}"
    return token

@pytest.mark.parametrize("email, password, expected", [
    ("bad-email", "123", 422),  # битый формат email → 422
    ("a@b.c", "", 401),         # пустой пароль → 401
])
def test_login_bad_data(http_client, email, password, expected):
    resp = http_client.post("/api/v1/authentication/login",
                            json={"email": email, "password": password})
    assert resp.status_code == expected


def test_login_success(http_client, created_user):
    # логинимся юзером, которого только что создали
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
    assert resp.status_code == 401  # юзер есть, пароль нет → 401, не 422


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


# ---------- Создание юзера ----------

def test_create_user(http_client, test_email, test_password):
    payload = {
        "email": test_email,
        "password": test_password,
        "firstName": "Tim",
        "lastName": "Sev",
        "middleName": "Test",
    }
    resp = http_client.post("/api/v1/users", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    # поля лежат в обёртке user
    assert data["user"]["email"] == test_email
    assert data["user"]["firstName"] == "Tim"
    assert "id" in data["user"]


# ---------- CRUD ----------

def test_user_crud(http_client, test_email, test_password):
    # CREATE
    resp = http_client.post("/api/v1/users", json={
        "email": test_email,
        "password": test_password,
        "firstName": "Tim",
        "lastName": "Sev",
        "middleName": "Test",
    })
    assert resp.status_code == 200
    user_id = resp.json()["user"]["id"]

    # DELETE — защищён, нужен токен
    token = get_token(http_client, test_email, test_password)
    resp = http_client.delete(f"/api/v1/users/{user_id}",
                              headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

    # VERIFY: юзера больше нет
    resp = http_client.get(f"/api/v1/users/{user_id}",
                           headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404


# ---------- Защищённые эндпоинты ----------

def test_protected_endpoint_with_token(http_client, created_user):
    email, password = created_user
    token = get_token(http_client, email, password)
    resp = http_client.get("/api/v1/users/me",
                           headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_protected_endpoint_without_token(http_client):
    # без токена → 401 (тест ловит, если защиту отключат)
    resp = http_client.get("/api/v1/users/me")
    assert resp.status_code == 401


def test_protected_endpoint_bad_token(http_client):
    # мусорный токен → тоже 401 (тест ловит, если проверку токена сломают)
    resp = http_client.get("/api/v1/users/me",
                           headers={"Authorization": "Bearer garbage_token_123"})
    assert resp.status_code == 401


# ---------- Отладка ----------

def test_print_login_response(http_client, created_user):
    # дебаг: печатает всю структуру ответа login (запускать с -s)
    email, password = created_user
    resp = http_client.post("/api/v1/authentication/login",
                            json={"email": email, "password": password})
    print(resp.json())
