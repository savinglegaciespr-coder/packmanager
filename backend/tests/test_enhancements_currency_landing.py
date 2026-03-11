import io
import uuid

import pytest


# Enhancement coverage: currency + editable landing content + weekly operational data shape


@pytest.fixture(scope="module")
def settings_restore(api_client, base_url, admin_session):
    headers = {"Authorization": f"Bearer {admin_session['token']}"}
    current_response = api_client.get(f"{base_url}/api/admin/settings", headers=headers, timeout=30)
    assert current_response.status_code == 200
    original = current_response.json()
    yield {"headers": headers, "original": original}

    restore_payload = {
        "currency": original.get("currency", "USD"),
        "landing_content": original.get("landing_content", {}),
    }
    restore_response = api_client.put(
        f"{base_url}/api/admin/settings",
        json=restore_payload,
        headers=headers,
        timeout=30,
    )
    assert restore_response.status_code == 200


def test_admin_settings_exposes_currency_and_landing_content(settings_restore, api_client, base_url):
    headers = settings_restore["headers"]
    response = api_client.get(f"{base_url}/api/admin/settings", headers=headers, timeout=30)
    assert response.status_code == 200
    payload = response.json()

    assert payload["currency"] in {"USD", "EUR", "GBP"}
    assert isinstance(payload.get("landing_content"), dict)
    assert isinstance(payload["landing_content"].get("feature_cards"), list)
    assert len(payload["landing_content"]["feature_cards"]) == 3


def test_currency_and_landing_changes_reflect_in_public_config(settings_restore, api_client, base_url):
    headers = settings_restore["headers"]
    original_landing = settings_restore["original"]["landing_content"]

    updated_landing = {
        **original_landing,
        "hero_description_es": "TEST Hero ES",
        "reserve_button_label_es": "TEST Reservar",
    }
    save_response = api_client.put(
        f"{base_url}/api/admin/settings",
        json={"currency": "EUR", "landing_content": updated_landing},
        headers=headers,
        timeout=30,
    )
    assert save_response.status_code == 200
    saved = save_response.json()
    assert saved["currency"] == "EUR"
    assert saved["landing_content"]["hero_description_es"] == "TEST Hero ES"

    public_response = api_client.get(f"{base_url}/api/public/config", timeout=30)
    assert public_response.status_code == 200
    public_config = public_response.json()
    assert public_config["currency"] == "EUR"
    assert public_config["landing_content"]["hero_description_es"] == "TEST Hero ES"
    assert public_config["landing_content"]["reserve_button_label_es"] == "TEST Reservar"


def test_price_related_email_logs_use_configured_currency_symbol(settings_restore, api_client, base_url):
    headers = settings_restore["headers"]

    switch_response = api_client.put(
        f"{base_url}/api/admin/settings",
        json={"currency": "GBP"},
        headers=headers,
        timeout=30,
    )
    assert switch_response.status_code == 200
    assert switch_response.json()["currency"] == "GBP"

    weeks_response = api_client.get(
        f"{base_url}/api/public/weeks",
        params={"program_id": "basic-6-day"},
        timeout=30,
    )
    assert weeks_response.status_code == 200
    weeks = weeks_response.json()["weeks"]
    available_week = next((week for week in weeks if week["remaining"] > 0), None)
    assert available_week is not None

    owner_email = f"test-gbp-{uuid.uuid4().hex[:8]}@example.com"
    form_data = {
        "program_id": "basic-6-day",
        "start_week": available_week["week_start"],
        "locale": "es",
        "owner_full_name": "TEST Currency Owner",
        "owner_email": owner_email,
        "owner_phone": "+34 600 444 444",
        "owner_address": "Madrid",
        "dog_name": "TEST-MoneyDog",
        "breed": "Mixed",
        "age": "2",
        "sex": "Male",
        "weight": "16kg",
        "date_of_birth": "2024-01-01",
        "vaccination_status": "Up to date",
        "allergies": "",
        "behavior_goals": "Lead walking",
        "current_medication": "",
        "additional_notes": "Currency verification",
    }
    files = {
        "payment_proof": ("payment.pdf", io.BytesIO(b"proof"), "application/pdf"),
        "vaccination_certificate": ("vaccine.pdf", io.BytesIO(b"certificate"), "application/pdf"),
    }
    create_response = api_client.post(f"{base_url}/api/public/bookings", data=form_data, files=files, timeout=30)
    assert create_response.status_code == 200
    booking_id = create_response.json()["booking_id"]

    logs_response = api_client.get(f"{base_url}/api/admin/email-logs", headers=headers, timeout=30)
    assert logs_response.status_code == 200
    logs = logs_response.json()
    booking_logs = [entry for entry in logs if entry.get("booking_id") == booking_id]
    assert len(booking_logs) >= 2

    combined_body = "\n".join(entry.get("body", "") for entry in booking_logs)
    assert "£" in combined_body


def test_capacity_and_bookings_support_weekly_operational_view(api_client, base_url, auth_headers):
    capacity_response = api_client.get(f"{base_url}/api/admin/capacity", headers=auth_headers, timeout=30)
    assert capacity_response.status_code == 200
    weeks = capacity_response.json()
    assert isinstance(weeks, list) and len(weeks) > 0
    first_week = weeks[0]
    assert "week_start" in first_week and "capacity" in first_week

    bookings_response = api_client.get(f"{base_url}/api/admin/bookings", headers=auth_headers, timeout=30)
    assert bookings_response.status_code == 200
    bookings = bookings_response.json()
    assert isinstance(bookings, list) and len(bookings) > 0

    operational_statuses = {"Pending Review", "Approved", "Scheduled", "In Training", "Delivered"}
    linked_booking = next(
        (
            booking
            for booking in bookings
            if booking.get("status") in operational_statuses
            and isinstance(booking.get("week_starts"), list)
            and first_week["week_start"] in booking["week_starts"]
        ),
        None,
    )
    assert linked_booking is not None
    assert linked_booking["dog"]["name"]
    assert linked_booking["owner"]["full_name"]
    assert linked_booking["program_name_es"]
    assert linked_booking["payment_status"] in {"Pending Review", "Verified", "Invalid"}
    assert linked_booking["vaccination_certificate_status"] in {"Pending Review", "Verified", "Invalid"}
