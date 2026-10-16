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
    email, password = created_user
    resp = http_client.post("/api/v1/authentication/login",
                            json={"email": email, "password": password})
    assert resp.status_code == 200
 
    assert find_token(resp.json()) is not None


def test_login_wrong_password(http_client, created_user):
    email, _ = created_user
    resp = http_client.post("/api/v1/authentication/login",
                            json={"email": email, "password": "wrong_pass"})
    assert resp.status_code == 401  # юзер есть, пароль нет → 401, не 422




@pytest.mark.parametrize("method, path, expected", [
    ("GET", "/api/v1/does-not-exist", 404),
    ("GET", "/api/v1/authentication/login", 405),
    ("PUT", "/api/v1/authentication/login", 405),
])
def test_bad_requests(http_client, method, path, expected):

    resp = http_client.request(method, path)
    assert resp.status_code == expected



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
    resp = http_client.post("/api/v1/users", json={
        "email": test_email,
        "password": test_password,
        "firstName": "Tim",
        "lastName": "Sev",
        "middleName": "Test",
    })
    assert resp.status_code == 200
    user_id = resp.json()["user"]["id"]

    token = get_token(http_client, test_email, test_password)
    resp = http_client.delete(f"/api/v1/users/{user_id}",
                              headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

    resp = http_client.get(f"/api/v1/users/{user_id}",
                           headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404


def test_protected_endpoint_with_token(http_client, created_user):
    email, password = created_user
    token = get_token(http_client, email, password)
    resp = http_client.get("/api/v1/users/me",
                           headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_protected_endpoint_without_token(http_client):
    resp = http_client.get("/api/v1/users/me")
    assert resp.status_code == 401


def test_protected_endpoint_bad_token(http_client):
    resp = http_client.get("/api/v1/users/me",
                           headers={"Authorization": "Bearer garbage_token_123"})
    assert resp.status_code == 401




def test_print_login_response(http_client, created_user):

    email, password = created_user
    resp = http_client.post("/api/v1/authentication/login",
                            json={"email": email, "password": password})
    print(resp.json())


def test_login_unknown_user(http_client):
   
    resp = http_client.post(
        "/api/v1/authentication/login",
        json={"email": "ghost@test.com", "password": "Password123"}
    )
    assert resp.status_code == 401


def test_login_empty_body(http_client):

    resp = http_client.post("/api/v1/authentication/login")
    assert resp.status_code == 422


def test_double_login(http_client, created_user):

    email, password = created_user
    for _ in range(2):
        resp = http_client.post(
            "/api/v1/authentication/login",
            json={"email": email, "password": password}
        )
        assert resp.status_code == 200




def test_create_user_duplicate(http_client, test_email, test_password):
 
    payload = {
        "email": test_email,
        "password": test_password,
        "firstName": "Tim",
        "lastName": "Sev",
    }
    assert http_client.post("/api/v1/users", json=payload).status_code == 200
    resp = http_client.post("/api/v1/users", json=payload)
    assert resp.status_code == 409


def test_create_user_missing_first_name(http_client, test_email, test_password):
    resp = http_client.post("/api/v1/users", json={
        "email": test_email,
        "password": test_password,
        "lastName": "Sev",
    })
    assert resp.status_code == 422


def test_create_user_empty_email(http_client, test_password):
    resp = http_client.post("/api/v1/users", json={
        "email": "",
        "password": test_password,
        "firstName": "Tim",
        "lastName": "Sev",
    })
    assert resp.status_code == 422



def test_get_user_by_id_with_token(http_client, test_email, test_password):
    resp = http_client.post("/api/v1/users", json={
        "email": test_email,
        "password": test_password,
        "firstName": "Tim",
        "lastName": "Sev",
    })
    user_id = resp.json()["user"]["id"]
    token = get_token(http_client, test_email, test_password)
    resp = http_client.get(
        f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == test_email


def test_get_user_by_id_without_token(http_client, test_email, test_password):
    resp = http_client.post("/api/v1/users", json={
        "email": test_email,
        "password": test_password,
        "firstName": "Tim",
        "lastName": "Sev",
    })
    user_id = resp.json()["user"]["id"]
    resp = http_client.get(f"/api/v1/users/{user_id}")
    assert resp.status_code == 401


def test_get_nonexistent_user(http_client, created_user):
    email, password = created_user
    token = get_token(http_client, email, password)
    resp = http_client.get(
        "/api/v1/users/999999999",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 404




def test_me_returns_token_owner_data(http_client, test_email, test_password):
    # два разных юзера: токен второго → /me отдаёт данные ВТОРОГО, не первого
    second_email = f"second{time.time()}@test.com"
    payload = {
        "email": second_email,
        "password": test_password,
        "firstName": "Other",
        "lastName": "Person",
    }
    resp = http_client.post("/api/v1/users", json=payload)
    assert resp.status_code == 200
    token = get_token(http_client, second_email, test_password)
    resp = http_client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == second_email
