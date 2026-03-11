import io
import uuid

import pytest


# Public flow coverage: landing config/programs/weeks + multipart booking validation and creation
def test_public_endpoints_and_capacity_labels(api_client, base_url, public_config):
    assert public_config["operational_start"] == "2026-03-30"

    programs_response = api_client.get(f"{base_url}/api/public/programs", timeout=30)
    assert programs_response.status_code == 200
    programs = programs_response.json()
    assert isinstance(programs, list) and len(programs) >= 1
    assert programs[0]["id"]

    weeks_response = api_client.get(
        f"{base_url}/api/public/weeks",
        params={"program_id": programs[0]["id"]},
        timeout=30,
    )
    assert weeks_response.status_code == 200
    weeks_payload = weeks_response.json()
    assert weeks_payload["program_id"] == programs[0]["id"]
    assert len(weeks_payload["weeks"]) > 0
    first_week = weeks_payload["weeks"][0]
    assert first_week["availability_label"] in {"available", "almost_full", "full"}
    assert isinstance(first_week["capacity"], int)


def test_public_booking_requires_payment_and_vaccination_files(api_client, base_url):
    payload = {
        "program_id": "basic-6-day",
        "start_week": "2026-03-30",
        "locale": "es",
        "owner_full_name": "TEST Missing Docs",
        "owner_email": f"test-missing-{uuid.uuid4().hex[:6]}@example.com",
        "owner_phone": "+34 600 100 100",
        "owner_address": "Madrid",
        "dog_name": "SinDocs",
        "breed": "Mixed",
        "sex": "Male",
        "weight": "12kg",
        "date_of_birth": "2023-01-01",
        "vaccination_status": "Up to date",
        "behavior_goals": "Basic obedience",
    }
    response = api_client.post(f"{base_url}/api/public/bookings", data=payload, timeout=30)
    assert response.status_code == 422
    details = response.json().get("detail", [])
    missing_fields = {item.get("loc", [None, None])[-1] for item in details if isinstance(item, dict)}
    assert "payment_proof" in missing_fields and "vaccination_certificate" in missing_fields


@pytest.fixture(scope="module")
def created_public_booking(api_client, base_url):
    owner_email = f"test-public-{uuid.uuid4().hex[:8]}@example.com"
    data = {
        "program_id": "basic-6-day",
        "start_week": "2026-04-13",
        "locale": "es",
        "owner_full_name": "TEST Public Booker",
        "owner_email": owner_email,
        "owner_phone": "+34 600 222 222",
        "owner_address": "Madrid",
        "dog_name": "TEST-Nube",
        "breed": "Labrador",
        "age": "2",
        "sex": "Male",
        "weight": "18kg",
        "date_of_birth": "2024-01-01",
        "vaccination_status": "Up to date",
        "allergies": "",
        "behavior_goals": "Recall and leash behavior",
        "current_medication": "",
        "additional_notes": "Automated API test",
    }
    files = {
        "payment_proof": ("payment.pdf", io.BytesIO(b"fake payment proof"), "application/pdf"),
        "vaccination_certificate": ("vaccine.pdf", io.BytesIO(b"fake vaccine cert"), "application/pdf"),
    }
    response = api_client.post(f"{base_url}/api/public/bookings", data=data, files=files, timeout=30)
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "Pending Review"
    assert isinstance(payload["booking_id"], str) and payload["booking_id"]
    return payload


# Admin flow coverage: auth guard, dashboard, bookings detail/update, manual create, programs, capacity, settings
def test_protected_routes_block_unauthenticated(api_client, base_url):
    response = api_client.get(f"{base_url}/api/admin/dashboard", timeout=30)
    assert response.status_code == 401
    assert "detail" in response.json()


def test_admin_dashboard_loads_metrics_and_charts(api_client, base_url, auth_headers):
    response = api_client.get(f"{base_url}/api/admin/dashboard", headers=auth_headers, timeout=30)
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload["metrics"], dict)
    assert isinstance(payload["weekly_occupancy"], list)
    assert isinstance(payload["charts"]["capacity_breakdown"], list)


@pytest.fixture(scope="module")
def manual_booking_id(api_client, base_url, admin_session):
    headers = {"Authorization": f"Bearer {admin_session['token']}"}
    owner_email = f"test-manual-{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "program_id": "basic-6-day",
        "start_week": "2026-04-20",
        "locale": "es",
        "owner_full_name": "TEST Manual Booker",
        "owner_email": owner_email,
        "owner_phone": "+34 600 333 333",
        "owner_address": "Madrid",
        "dog_name": "TEST-ManualDog",
        "breed": "Beagle",
        "age": "3",
        "sex": "Male",
        "weight": "14kg",
        "date_of_birth": "2023-02-01",
        "vaccination_status": "Up to date",
        "behavior_goals": "Calm behavior",
        "status": "Scheduled",
        "payment_status": "Verified",
        "vaccination_certificate_status": "Verified",
        "eligibility_status": "Eligible",
    }
    response = api_client.post(f"{base_url}/api/admin/bookings/manual", json=payload, headers=headers, timeout=30)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "Scheduled"
    return body["id"]


def test_admin_bookings_lists_seeded_and_manual(api_client, base_url, auth_headers, manual_booking_id):
    response = api_client.get(f"{base_url}/api/admin/bookings", headers=auth_headers, timeout=30)
    assert response.status_code == 200
    bookings = response.json()
    assert len(bookings) >= 12
    booking_ids = {booking["id"] for booking in bookings}
    assert "seed-1" in booking_ids and manual_booking_id in booking_ids


def test_admin_booking_detail_and_status_update(api_client, base_url, auth_headers, created_public_booking):
    booking_id = created_public_booking["booking_id"]
    detail_response = api_client.get(f"{base_url}/api/admin/bookings/{booking_id}", headers=auth_headers, timeout=30)
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["status"] == "Pending Review"

    patch_payload = {
        "payment_status": "Verified",
        "vaccination_certificate_status": "Verified",
        "eligibility_status": "Eligible",
        "status": "Approved",
        "internal_notes": "TEST approved from API regression",
    }
    patch_response = api_client.patch(
        f"{base_url}/api/admin/bookings/{booking_id}",
        json=patch_payload,
        headers=auth_headers,
        timeout=30,
    )
    assert patch_response.status_code == 200
    updated = patch_response.json()
    assert updated["status"] == "Approved"

    verify_response = api_client.get(f"{base_url}/api/admin/bookings/{booking_id}", headers=auth_headers, timeout=30)
    assert verify_response.status_code == 200
    verify = verify_response.json()
    assert verify["payment_status"] == "Verified"


def test_admin_programs_create_and_edit(api_client, base_url, auth_headers):
    create_payload = {
        "name_es": f"TEST Programa {uuid.uuid4().hex[:6]}",
        "name_en": "TEST Program",
        "description_es": "Programa de prueba",
        "description_en": "Program test",
        "duration_value": 2,
        "duration_unit": "weeks",
        "price": 999,
        "active": True,
    }
    create_response = api_client.post(f"{base_url}/api/admin/programs", json=create_payload, headers=auth_headers, timeout=30)
    assert create_response.status_code == 200
    created = create_response.json()
    assert created["name_es"] == create_payload["name_es"]

    update_payload = {**create_payload, "price": 1111, "active": False}
    update_response = api_client.put(
        f"{base_url}/api/admin/programs/{created['id']}",
        json=update_payload,
        headers=auth_headers,
        timeout=30,
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["price"] == 1111


def test_admin_capacity_load_and_save(api_client, base_url, auth_headers):
    get_response = api_client.get(f"{base_url}/api/admin/capacity", headers=auth_headers, timeout=30)
    assert get_response.status_code == 200
    weeks = get_response.json()
    target = weeks[0]
    new_capacity = int(target["capacity"]) + 1

    save_response = api_client.put(
        f"{base_url}/api/admin/capacity/{target['week_start']}",
        json={"capacity": new_capacity},
        headers=auth_headers,
        timeout=30,
    )
    assert save_response.status_code == 200
    saved = save_response.json()
    assert saved["capacity"] == new_capacity


def test_admin_settings_load_and_save(api_client, base_url, auth_headers):
    current_response = api_client.get(f"{base_url}/api/admin/settings", headers=auth_headers, timeout=30)
    assert current_response.status_code == 200
    current = current_response.json()
    original_slogan = current.get("slogan", "")

    changed_slogan = f"{original_slogan} TEST".strip()
    save_response = api_client.put(
        f"{base_url}/api/admin/settings",
        json={"slogan": changed_slogan},
        headers=auth_headers,
        timeout=30,
    )
    assert save_response.status_code == 200
    updated = save_response.json()
    assert updated["slogan"] == changed_slogan

    restore_response = api_client.put(
        f"{base_url}/api/admin/settings",
        json={"slogan": original_slogan},
        headers=auth_headers,
        timeout=30,
    )
    assert restore_response.status_code == 200