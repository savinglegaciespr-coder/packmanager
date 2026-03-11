import uuid

import pytest


# Landing hero configuration regression: admin settings + public config propagation


@pytest.fixture(scope="module")
def hero_settings_restore(api_client, base_url, admin_session):
    headers = {"Authorization": f"Bearer {admin_session['token']}"}
    response = api_client.get(f"{base_url}/api/admin/settings", headers=headers, timeout=30)
    assert response.status_code == 200
    original = response.json()
    yield {"headers": headers, "original": original}

    restore_response = api_client.put(
        f"{base_url}/api/admin/settings",
        json={"landing_hero_image_url": original.get("landing_hero_image_url", "")},
        headers=headers,
        timeout=30,
    )
    assert restore_response.status_code == 200


def test_admin_settings_exposes_landing_hero_fields(api_client, base_url, hero_settings_restore):
    headers = hero_settings_restore["headers"]
    response = api_client.get(f"{base_url}/api/admin/settings", headers=headers, timeout=30)
    assert response.status_code == 200
    payload = response.json()

    assert "landing_hero_image_url" in payload
    assert "landing_hero_image_asset" in payload


def test_public_config_exposes_landing_hero_url(api_client, base_url):
    response = api_client.get(f"{base_url}/api/public/config", timeout=30)
    assert response.status_code == 200
    payload = response.json()
    assert "landing_hero_image_url" in payload
    assert isinstance(payload["landing_hero_image_url"], str)


def test_landing_hero_url_update_reflects_in_public_config(api_client, base_url, hero_settings_restore):
    headers = hero_settings_restore["headers"]
    marker = uuid.uuid4().hex[:8]
    hero_url = f"https://example.com/test-hero-{marker}.jpg"

    save_response = api_client.put(
        f"{base_url}/api/admin/settings",
        json={"landing_hero_image_url": hero_url},
        headers=headers,
        timeout=30,
    )
    assert save_response.status_code == 200
    assert save_response.json()["landing_hero_image_url"] == hero_url

    public_response = api_client.get(f"{base_url}/api/public/config", timeout=30)
    assert public_response.status_code == 200
    public_payload = public_response.json()
    assert public_payload["landing_hero_image_url"] == hero_url


def test_landing_hero_url_can_be_cleared(api_client, base_url, hero_settings_restore):
    headers = hero_settings_restore["headers"]
    clear_response = api_client.put(
        f"{base_url}/api/admin/settings",
        json={"landing_hero_image_url": ""},
        headers=headers,
        timeout=30,
    )
    assert clear_response.status_code == 200
    assert clear_response.json().get("landing_hero_image_url", "") == ""

    public_response = api_client.get(f"{base_url}/api/public/config", timeout=30)
    assert public_response.status_code == 200
    assert isinstance(public_response.json().get("landing_hero_image_url", ""), str)
