import httpx

BASE_URL = 'http://localhost:8000'

def test_login():
    resp = httpx.post(url=f'{BASE_URL}/api/v1/authentication/login',
                      json={"email": "a@b.c", "password": "123"},
                      )
    assert resp.status_code == 200
    assert "token" in resp.json()

def test_get_users(token):
    resp = httpx.get(
        f"{BASE_URL}/api/v1/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 405

