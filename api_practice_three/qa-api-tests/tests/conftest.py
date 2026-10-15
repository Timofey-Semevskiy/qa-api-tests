import time
import httpx
import pytest
from dotenv import load_dotenv
import os

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

@pytest.fixture
def http_client():
    with httpx.Client(base_url = BASE_URL) as client:
        yield client

@pytest.fixture
def test_email():
    return f"test{time.time()}@test.com"

@pytest.fixture
def test_password():
    return os.getenv("TEST_PASSWORD", "Password123")

@pytest.fixture
def created_user(http_client, test_email, test_password):
    """Создаёт реального юзера и возвращает (email, password) для логина."""
    resp = http_client.post("/api/v1/users", json={
        "email": test_email,
        "password": test_password,
        "firstName": "Tim",
        "lastName": "Sev",
        "middleName": "Test",
    })
    assert resp.status_code == 200
    return test_email, test_password
