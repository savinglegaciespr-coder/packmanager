"""
Test Configurable Deposit Settings Feature

Tests the new deposit_type and deposit_value fields in programs and the
computed deposit_amount/balance_amount in bookings. Also tests dashboard metrics
for total_deposit_expected, total_deposit_collected, total_balance_expected, total_balance_collected.
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

@pytest.fixture(scope="module")
def admin_token():
    """Get admin auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@pawstraining.com",
        "password": os.environ.get("TEST_ADMIN_PASSWORD", "")
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["token"]


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    """Return headers with auth token"""
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


class TestProgramDepositFields:
    """Test deposit_type and deposit_value fields on programs"""
    
    def test_public_programs_return_deposit_fields(self):
        """Programs endpoint returns deposit_type and deposit_value"""
        response = requests.get(f"{BASE_URL}/api/public/programs")
        assert response.status_code == 200
        programs = response.json()
        assert len(programs) > 0, "Expected at least one program"
        
        for program in programs:
            assert "deposit_type" in program, f"Program {program['id']} missing deposit_type"
            assert "deposit_value" in program, f"Program {program['id']} missing deposit_value"
            assert program["deposit_type"] in ["percentage", "fixed"], f"Invalid deposit_type: {program['deposit_type']}"
            assert isinstance(program["deposit_value"], (int, float)), f"deposit_value should be numeric"
            assert program["deposit_value"] >= 0, "deposit_value should be non-negative"
    
    def test_admin_programs_return_deposit_fields(self, auth_headers):
        """Admin programs endpoint returns deposit_type and deposit_value"""
        response = requests.get(f"{BASE_URL}/api/admin/programs", headers=auth_headers)
        assert response.status_code == 200
        programs = response.json()
        
        for program in programs:
            assert "deposit_type" in program
            assert "deposit_value" in program

    def test_update_program_percentage_deposit(self, auth_headers):
        """Update program to use percentage-based deposit"""
        # First get current state of basic-6-day program
        response = requests.get(f"{BASE_URL}/api/admin/programs", headers=auth_headers)
        assert response.status_code == 200
        programs = response.json()
        basic_program = next((p for p in programs if p["id"] == "basic-6-day"), None)
        assert basic_program is not None, "basic-6-day program not found"
        
        # Update to percentage deposit
        update_payload = {
            "name_es": basic_program["name_es"],
            "name_en": basic_program["name_en"],
            "description_es": basic_program["description_es"],
            "description_en": basic_program["description_en"],
            "duration_value": basic_program["duration_value"],
            "duration_unit": basic_program["duration_unit"],
            "price": basic_program["price"],
            "active": True,
            "deposit_type": "percentage",
            "deposit_value": 50.0
        }
        
        response = requests.put(
            f"{BASE_URL}/api/admin/programs/basic-6-day",
            json=update_payload,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Update failed: {response.text}"
        updated = response.json()
        
        assert updated["deposit_type"] == "percentage"
        assert updated["deposit_value"] == 50.0
        print(f"✓ Program updated to percentage deposit: {updated['deposit_type']} = {updated['deposit_value']}")

    def test_update_program_fixed_deposit(self, auth_headers):
        """Update program to use fixed-amount deposit"""
        # Get multi-week program
        response = requests.get(f"{BASE_URL}/api/admin/programs", headers=auth_headers)
        assert response.status_code == 200
        programs = response.json()
        multi_week = next((p for p in programs if p["id"] == "multi-week"), None)
        assert multi_week is not None, "multi-week program not found"
        
        # Update to fixed deposit
        update_payload = {
            "name_es": multi_week["name_es"],
            "name_en": multi_week["name_en"],
            "description_es": multi_week["description_es"],
            "description_en": multi_week["description_en"],
            "duration_value": multi_week["duration_value"],
            "duration_unit": multi_week["duration_unit"],
            "price": multi_week["price"],
            "active": True,
            "deposit_type": "fixed",
            "deposit_value": 200.0
        }
        
        response = requests.put(
            f"{BASE_URL}/api/admin/programs/multi-week",
            json=update_payload,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Update failed: {response.text}"
        updated = response.json()
        
        assert updated["deposit_type"] == "fixed"
        assert updated["deposit_value"] == 200.0
        print(f"✓ Program updated to fixed deposit: {updated['deposit_type']} = {updated['deposit_value']}")
        
        # Restore to percentage for other tests
        update_payload["deposit_type"] = "percentage"
        update_payload["deposit_value"] = 50.0
        requests.put(f"{BASE_URL}/api/admin/programs/multi-week", json=update_payload, headers=auth_headers)


class TestBookingDepositComputation:
    """Test that bookings compute and return deposit_amount and balance_amount"""
    
    def test_bookings_return_deposit_amounts(self, auth_headers):
        """Bookings endpoint returns computed deposit_amount and balance_amount"""
        response = requests.get(f"{BASE_URL}/api/admin/bookings", headers=auth_headers)
        assert response.status_code == 200
        bookings = response.json()
        assert len(bookings) > 0, "Expected at least one booking"
        
        for booking in bookings[:5]:  # Check first 5 bookings
            assert "deposit_amount" in booking, f"Booking {booking['id']} missing deposit_amount"
            assert "balance_amount" in booking, f"Booking {booking['id']} missing balance_amount"
            
            deposit = booking["deposit_amount"]
            balance = booking["balance_amount"]
            price = booking["program_price"]
            
            # Verify deposit + balance = price
            assert abs(deposit + balance - price) < 0.01, f"Deposit ({deposit}) + Balance ({balance}) != Price ({price})"
            print(f"✓ Booking {booking['id']}: Deposit={deposit}, Balance={balance}, Total={price}")
    
    def test_booking_detail_returns_deposit_amounts(self, auth_headers):
        """Individual booking detail returns deposit_amount and balance_amount"""
        # Get first booking
        response = requests.get(f"{BASE_URL}/api/admin/bookings", headers=auth_headers)
        assert response.status_code == 200
        bookings = response.json()
        booking_id = bookings[0]["id"]
        
        # Get detail
        response = requests.get(f"{BASE_URL}/api/admin/bookings/{booking_id}", headers=auth_headers)
        assert response.status_code == 200
        booking = response.json()
        
        assert "deposit_amount" in booking
        assert "balance_amount" in booking
        assert "program_snapshot" in booking, "Booking should have program_snapshot"
        
        snapshot = booking.get("program_snapshot") or {}
        print(f"✓ Booking detail: deposit_type in snapshot = {snapshot.get('deposit_type')}, deposit_value = {snapshot.get('deposit_value')}")
    
    def test_booking_snapshot_contains_deposit_config(self, auth_headers):
        """New bookings snapshot the program's deposit_type and deposit_value"""
        # Create a manual booking
        unique_id = str(uuid.uuid4())[:8]
        booking_payload = {
            "program_id": "basic-6-day",
            "start_week": "2026-04-13",
            "locale": "en",
            "owner_full_name": f"TEST_Deposit_Config_{unique_id}",
            "owner_email": f"test.deposit{unique_id}@example.com",
            "owner_phone": "+34 600 000 000",
            "owner_address": "Test Address",
            "dog_name": f"TEST_Dog_{unique_id}",
            "breed": "Labrador",
            "sex": "Male",
            "weight": "25",
            "date_of_birth": "2023-01-15",
            "vaccination_status": "Up to date",
            "behavior_goals": "Testing deposit config",
            "status": "Scheduled",
            "payment_status": "Verified",
            "vaccination_certificate_status": "Verified",
            "eligibility_status": "Eligible"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/bookings/manual",
            json=booking_payload,
            headers=auth_headers
        )
        assert response.status_code in [200, 201], f"Manual booking failed: {response.text}"
        booking = response.json()
        
        # Verify program_snapshot has deposit config
        snapshot = booking.get("program_snapshot") or {}
        assert "deposit_type" in snapshot, "program_snapshot should contain deposit_type"
        assert "deposit_value" in snapshot, "program_snapshot should contain deposit_value"
        
        # Verify computed amounts
        assert "deposit_amount" in booking
        assert "balance_amount" in booking
        
        # Verify calculation is correct
        price = booking["program_price"]
        dep_type = snapshot["deposit_type"]
        dep_val = snapshot["deposit_value"]
        
        if dep_type == "fixed":
            expected_deposit = min(dep_val, price)
        else:
            expected_deposit = round(price * dep_val / 100, 2)
        expected_balance = round(price - expected_deposit, 2)
        
        assert abs(booking["deposit_amount"] - expected_deposit) < 0.01, f"Expected deposit {expected_deposit}, got {booking['deposit_amount']}"
        assert abs(booking["balance_amount"] - expected_balance) < 0.01, f"Expected balance {expected_balance}, got {booking['balance_amount']}"
        
        print(f"✓ New booking snapshot has deposit_type={dep_type}, deposit_value={dep_val}")
        print(f"✓ Computed: deposit={booking['deposit_amount']}, balance={booking['balance_amount']}")


class TestDepositComputationLogic:
    """Test the deposit computation formulas"""
    
    def test_percentage_deposit_computation(self, auth_headers):
        """Percentage mode: deposit = price * value / 100"""
        # Ensure basic-6-day is at percentage 50%
        response = requests.get(f"{BASE_URL}/api/admin/programs", headers=auth_headers)
        programs = response.json()
        basic = next(p for p in programs if p["id"] == "basic-6-day")
        
        update_payload = {
            "name_es": basic["name_es"],
            "name_en": basic["name_en"],
            "description_es": basic["description_es"],
            "description_en": basic["description_en"],
            "duration_value": basic["duration_value"],
            "duration_unit": basic["duration_unit"],
            "price": 450,
            "active": True,
            "deposit_type": "percentage",
            "deposit_value": 30.0
        }
        
        requests.put(f"{BASE_URL}/api/admin/programs/basic-6-day", json=update_payload, headers=auth_headers)
        
        # Create booking
        unique_id = str(uuid.uuid4())[:8]
        booking_payload = {
            "program_id": "basic-6-day",
            "start_week": "2026-04-20",
            "locale": "en",
            "owner_full_name": f"TEST_Pct_{unique_id}",
            "owner_email": f"test.pct{unique_id}@example.com",
            "owner_phone": "+34 600 000 000",
            "owner_address": "Test",
            "dog_name": f"TEST_DogPct_{unique_id}",
            "breed": "Beagle",
            "sex": "Male",
            "weight": "15",
            "date_of_birth": "2022-06-01",
            "vaccination_status": "Up to date",
            "behavior_goals": "Test percentage",
            "status": "Scheduled",
            "payment_status": "Verified",
            "vaccination_certificate_status": "Verified",
            "eligibility_status": "Eligible"
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/bookings/manual", json=booking_payload, headers=auth_headers)
        assert response.status_code in [200, 201]
        booking = response.json()
        
        # Verify: 450 * 30% = 135 deposit, 315 balance
        assert abs(booking["deposit_amount"] - 135.0) < 0.01, f"Expected 135, got {booking['deposit_amount']}"
        assert abs(booking["balance_amount"] - 315.0) < 0.01, f"Expected 315, got {booking['balance_amount']}"
        print(f"✓ Percentage deposit: 450 * 30% = {booking['deposit_amount']} deposit, {booking['balance_amount']} balance")
        
        # Restore to 50%
        update_payload["deposit_value"] = 50.0
        requests.put(f"{BASE_URL}/api/admin/programs/basic-6-day", json=update_payload, headers=auth_headers)

    def test_fixed_deposit_computation(self, auth_headers):
        """Fixed mode: deposit = min(value, price)"""
        # Set multi-week to fixed $200
        response = requests.get(f"{BASE_URL}/api/admin/programs", headers=auth_headers)
        programs = response.json()
        multi = next(p for p in programs if p["id"] == "multi-week")
        
        update_payload = {
            "name_es": multi["name_es"],
            "name_en": multi["name_en"],
            "description_es": multi["description_es"],
            "description_en": multi["description_en"],
            "duration_value": multi["duration_value"],
            "duration_unit": multi["duration_unit"],
            "price": 799,
            "active": True,
            "deposit_type": "fixed",
            "deposit_value": 200.0
        }
        
        requests.put(f"{BASE_URL}/api/admin/programs/multi-week", json=update_payload, headers=auth_headers)
        
        # Create booking
        unique_id = str(uuid.uuid4())[:8]
        booking_payload = {
            "program_id": "multi-week",
            "start_week": "2026-04-27",
            "locale": "en",
            "owner_full_name": f"TEST_Fixed_{unique_id}",
            "owner_email": f"test.fixed{unique_id}@example.com",
            "owner_phone": "+34 600 000 000",
            "owner_address": "Test",
            "dog_name": f"TEST_DogFixed_{unique_id}",
            "breed": "Poodle",
            "sex": "Female",
            "weight": "10",
            "date_of_birth": "2021-03-01",
            "vaccination_status": "Up to date",
            "behavior_goals": "Test fixed deposit",
            "status": "Scheduled",
            "payment_status": "Verified",
            "vaccination_certificate_status": "Verified",
            "eligibility_status": "Eligible"
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/bookings/manual", json=booking_payload, headers=auth_headers)
        assert response.status_code in [200, 201]
        booking = response.json()
        
        # Verify: fixed $200 deposit, 799 - 200 = 599 balance
        assert abs(booking["deposit_amount"] - 200.0) < 0.01, f"Expected 200, got {booking['deposit_amount']}"
        assert abs(booking["balance_amount"] - 599.0) < 0.01, f"Expected 599, got {booking['balance_amount']}"
        print(f"✓ Fixed deposit: $200 deposit, ${booking['balance_amount']} balance")
        
        # Restore to percentage
        update_payload["deposit_type"] = "percentage"
        update_payload["deposit_value"] = 50.0
        requests.put(f"{BASE_URL}/api/admin/programs/multi-week", json=update_payload, headers=auth_headers)

    def test_fixed_deposit_capped_at_price(self, auth_headers):
        """Fixed deposit is capped at price when value > price"""
        response = requests.get(f"{BASE_URL}/api/admin/programs", headers=auth_headers)
        programs = response.json()
        basic = next(p for p in programs if p["id"] == "basic-6-day")
        
        # Set fixed deposit higher than price
        update_payload = {
            "name_es": basic["name_es"],
            "name_en": basic["name_en"],
            "description_es": basic["description_es"],
            "description_en": basic["description_en"],
            "duration_value": basic["duration_value"],
            "duration_unit": basic["duration_unit"],
            "price": 450,
            "active": True,
            "deposit_type": "fixed",
            "deposit_value": 1000.0  # Higher than price
        }
        
        requests.put(f"{BASE_URL}/api/admin/programs/basic-6-day", json=update_payload, headers=auth_headers)
        
        # Create booking
        unique_id = str(uuid.uuid4())[:8]
        booking_payload = {
            "program_id": "basic-6-day",
            "start_week": "2026-05-04",
            "locale": "en",
            "owner_full_name": f"TEST_Cap_{unique_id}",
            "owner_email": f"test.cap{unique_id}@example.com",
            "owner_phone": "+34 600 000 000",
            "owner_address": "Test",
            "dog_name": f"TEST_DogCap_{unique_id}",
            "breed": "Bulldog",
            "sex": "Male",
            "weight": "20",
            "date_of_birth": "2020-09-01",
            "vaccination_status": "Up to date",
            "behavior_goals": "Test capped deposit",
            "status": "Scheduled",
            "payment_status": "Verified",
            "vaccination_certificate_status": "Verified",
            "eligibility_status": "Eligible"
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/bookings/manual", json=booking_payload, headers=auth_headers)
        assert response.status_code in [200, 201]
        booking = response.json()
        
        # Deposit should be capped at price (450)
        assert abs(booking["deposit_amount"] - 450.0) < 0.01, f"Expected capped at 450, got {booking['deposit_amount']}"
        assert abs(booking["balance_amount"] - 0.0) < 0.01, f"Expected 0 balance, got {booking['balance_amount']}"
        print(f"✓ Fixed deposit capped: price=450, fixed=1000 → deposit={booking['deposit_amount']}, balance={booking['balance_amount']}")
        
        # Restore to percentage
        update_payload["deposit_type"] = "percentage"
        update_payload["deposit_value"] = 50.0
        requests.put(f"{BASE_URL}/api/admin/programs/basic-6-day", json=update_payload, headers=auth_headers)


class TestBackwardCompatibility:
    """Test backward compatibility for old bookings without deposit config in snapshot"""
    
    def test_old_bookings_default_to_full_deposit(self, auth_headers):
        """Old bookings without deposit config in snapshot default to 100% deposit"""
        # This is tested implicitly via seed bookings which may not have deposit config
        # The sanitize_booking function uses dep_val = snapshot.get("deposit_value", 100.0)
        response = requests.get(f"{BASE_URL}/api/admin/bookings", headers=auth_headers)
        assert response.status_code == 200
        bookings = response.json()
        
        # Check all bookings have deposit_amount and balance_amount
        for booking in bookings:
            assert "deposit_amount" in booking, f"Booking {booking['id']} missing deposit_amount"
            assert "balance_amount" in booking, f"Booking {booking['id']} missing balance_amount"
            
            # If no snapshot deposit config, should default appropriately
            snapshot = booking.get("program_snapshot") or {}
            if "deposit_type" not in snapshot:
                # Default is percentage with 100% (full price as deposit)
                assert booking["deposit_amount"] == booking["program_price"], \
                    f"Old booking should have full deposit. Got {booking['deposit_amount']} vs price {booking['program_price']}"
        
        print("✓ All bookings have deposit_amount and balance_amount fields")


class TestDashboardDepositMetrics:
    """Test dashboard metrics for deposit tracking"""
    
    def test_dashboard_returns_deposit_metrics(self, auth_headers):
        """Dashboard returns total_deposit_expected/collected and total_balance_expected/collected"""
        response = requests.get(f"{BASE_URL}/api/admin/dashboard", headers=auth_headers)
        assert response.status_code == 200
        dashboard = response.json()
        
        metrics = dashboard.get("metrics", {})
        
        # Check deposit/balance metrics exist
        assert "total_deposit_expected" in metrics, "Missing total_deposit_expected"
        assert "total_deposit_collected" in metrics, "Missing total_deposit_collected"
        assert "total_balance_expected" in metrics, "Missing total_balance_expected"
        assert "total_balance_collected" in metrics, "Missing total_balance_collected"
        
        # Verify they are numeric
        assert isinstance(metrics["total_deposit_expected"], (int, float))
        assert isinstance(metrics["total_deposit_collected"], (int, float))
        assert isinstance(metrics["total_balance_expected"], (int, float))
        assert isinstance(metrics["total_balance_collected"], (int, float))
        
        # Values should be non-negative
        assert metrics["total_deposit_expected"] >= 0
        assert metrics["total_deposit_collected"] >= 0
        assert metrics["total_balance_expected"] >= 0
        assert metrics["total_balance_collected"] >= 0
        
        # Collected should not exceed expected
        assert metrics["total_deposit_collected"] <= metrics["total_deposit_expected"], \
            f"Deposit collected ({metrics['total_deposit_collected']}) > expected ({metrics['total_deposit_expected']})"
        assert metrics["total_balance_collected"] <= metrics["total_balance_expected"], \
            f"Balance collected ({metrics['total_balance_collected']}) > expected ({metrics['total_balance_expected']})"
        
        print(f"✓ Dashboard deposit metrics:")
        print(f"  - Total deposit expected: {metrics['total_deposit_expected']}")
        print(f"  - Total deposit collected: {metrics['total_deposit_collected']}")
        print(f"  - Total balance expected: {metrics['total_balance_expected']}")
        print(f"  - Total balance collected: {metrics['total_balance_collected']}")


class TestCleanup:
    """Clean up test data"""
    
    def test_restore_programs_to_defaults(self, auth_headers):
        """Restore programs to default percentage 50% deposit"""
        for program_id in ["basic-6-day", "multi-week"]:
            response = requests.get(f"{BASE_URL}/api/admin/programs", headers=auth_headers)
            programs = response.json()
            program = next((p for p in programs if p["id"] == program_id), None)
            if program:
                update_payload = {
                    "name_es": program["name_es"],
                    "name_en": program["name_en"],
                    "description_es": program["description_es"],
                    "description_en": program["description_en"],
                    "duration_value": program["duration_value"],
                    "duration_unit": program["duration_unit"],
                    "price": program["price"],
                    "active": True,
                    "deposit_type": "percentage",
                    "deposit_value": 50.0
                }
                requests.put(f"{BASE_URL}/api/admin/programs/{program_id}", json=update_payload, headers=auth_headers)
        
        print("✓ Programs restored to percentage 50% deposit")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
