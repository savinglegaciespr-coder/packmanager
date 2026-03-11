import os

import pytest
import requests


@pytest.fixture(scope="session")
def base_url() -> str:
    """Base URL from environment (external preview URL)."""
    value = os.environ.get("REACT_APP_BACKEND_URL")
    if not value:
        pytest.skip("REACT_APP_BACKEND_URL is not set; skipping API tests.")
    return value.rstrip("/")


@pytest.fixture(scope="session")
def api_client() -> requests.Session:
    """Shared HTTP session for API tests."""
    session = requests.Session()
    session.headers.update({"Accept": "application/json"})
    return session


@pytest.fixture(scope="session")
def public_config(api_client: requests.Session, base_url: str) -> dict:
    response = api_client.get(f"{base_url}/api/public/config", timeout=30)
    assert response.status_code == 200
    payload = response.json()
    assert payload["business_name"]
    assert payload["demo_admin"]["email"]
    return payload


@pytest.fixture(scope="session")
def admin_session(api_client: requests.Session, base_url: str, public_config: dict) -> dict:
    """Authenticated admin token + profile from demo credentials."""
    credentials = {
        "email": public_config["demo_admin"]["email"],
        "password": public_config["demo_admin"]["password"],
    }
    response = api_client.post(f"{base_url}/api/auth/login", json=credentials, timeout=30)
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload["token"], str) and payload["token"]
    assert payload["admin"]["email"] == credentials["email"]
    return payload


@pytest.fixture
def auth_headers(admin_session: dict) -> dict:
    return {"Authorization": f"Bearer {admin_session['token']}"}