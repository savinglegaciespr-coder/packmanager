"""
RBAC Endpoint Restrictions Tests for PAWS TRAINING
Tests role-based access control for all admin endpoints:
- Superadmin: Full access to all endpoints
- Admin: Dashboard, bookings, email-logs, documents, manual booking (NO settings, programs CRUD, capacity update)
- Operator: Bookings list (financial stripped), booking detail (financial stripped), documents (NO dashboard, settings, programs, capacity, email-logs, manual booking)
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SUPERADMIN_EMAIL = "admin@pawstraining.com"
SUPERADMIN_PASSWORD = "PawsAdmin2026!"


@pytest.fixture(scope="module")
def superadmin_token():
    """Get superadmin token for authenticated tests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": SUPERADMIN_EMAIL,
        "password": SUPERADMIN_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip("Superadmin login failed")
    return response.json()["token"]


@pytest.fixture(scope="module")
def admin_user_and_token(superadmin_token):
    """Create an admin user and get their token"""
    admin_email = f"test_admin_rbac_{uuid.uuid4().hex[:8]}@test.com"
    create_response = requests.post(
        f"{BASE_URL}/api/admin/users",
        headers={"Authorization": f"Bearer {superadmin_token}"},
        json={
            "name": "Test Admin RBAC",
            "email": admin_email,
            "password": "testpass123",
            "role": "admin"
        }
    )
    if create_response.status_code != 200:
        pytest.skip(f"Failed to create admin user: {create_response.text}")
    
    admin_user = create_response.json()
    
    # Login as admin
    login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": admin_email,
        "password": "testpass123"
    })
    if login_response.status_code != 200:
        pytest.skip(f"Failed to login as admin: {login_response.text}")
    
    login_data = login_response.json()
    
    yield {"user": admin_user, "token": login_data["token"], "email": admin_email}
    
    # Cleanup
    requests.delete(
        f"{BASE_URL}/api/admin/users/{admin_user['id']}",
        headers={"Authorization": f"Bearer {superadmin_token}"}
    )


@pytest.fixture(scope="module")
def operator_user_and_token(superadmin_token):
    """Create an operator user and get their token"""
    op_email = f"test_operator_rbac_{uuid.uuid4().hex[:8]}@test.com"
    create_response = requests.post(
        f"{BASE_URL}/api/admin/users",
        headers={"Authorization": f"Bearer {superadmin_token}"},
        json={
            "name": "Test Operator RBAC",
            "email": op_email,
            "password": "testpass123",
            "role": "operator"
        }
    )
    if create_response.status_code != 200:
        pytest.skip(f"Failed to create operator user: {create_response.text}")
    
    op_user = create_response.json()
    
    # Login as operator
    login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": op_email,
        "password": "testpass123"
    })
    if login_response.status_code != 200:
        pytest.skip(f"Failed to login as operator: {login_response.text}")
    
    login_data = login_response.json()
    
    yield {"user": op_user, "token": login_data["token"], "email": op_email}
    
    # Cleanup
    requests.delete(
        f"{BASE_URL}/api/admin/users/{op_user['id']}",
        headers={"Authorization": f"Bearer {superadmin_token}"}
    )


class TestSuperadminEndpointAccess:
    """Test superadmin can access all endpoints"""
    
    def test_superadmin_can_access_dashboard(self, superadmin_token):
        """Superadmin can access dashboard (200)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/dashboard",
            headers={"Authorization": f"Bearer {superadmin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ Superadmin can access dashboard")
    
    def test_superadmin_can_access_bookings(self, superadmin_token):
        """Superadmin can access bookings (200)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/bookings",
            headers={"Authorization": f"Bearer {superadmin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ Superadmin can access bookings")
    
    def test_superadmin_can_access_settings(self, superadmin_token):
        """Superadmin can access settings (200)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/settings",
            headers={"Authorization": f"Bearer {superadmin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ Superadmin can access settings")
    
    def test_superadmin_can_access_programs(self, superadmin_token):
        """Superadmin can access programs (200)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/programs",
            headers={"Authorization": f"Bearer {superadmin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ Superadmin can access programs")
    
    def test_superadmin_can_access_capacity(self, superadmin_token):
        """Superadmin can access capacity (200)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/capacity",
            headers={"Authorization": f"Bearer {superadmin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ Superadmin can access capacity")
    
    def test_superadmin_can_access_email_logs(self, superadmin_token):
        """Superadmin can access email-logs (200)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/email-logs",
            headers={"Authorization": f"Bearer {superadmin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ Superadmin can access email-logs")


class TestAdminEndpointAccess:
    """Test admin role endpoint access - can access dashboard, bookings, email-logs, documents"""
    
    def test_admin_can_access_dashboard(self, admin_user_and_token):
        """Admin can access dashboard (200)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/dashboard",
            headers={"Authorization": f"Bearer {admin_user_and_token['token']}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ Admin can access dashboard")
    
    def test_admin_can_access_bookings(self, admin_user_and_token):
        """Admin can access bookings (200)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/bookings",
            headers={"Authorization": f"Bearer {admin_user_and_token['token']}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ Admin can access bookings")
    
    def test_admin_can_access_email_logs(self, admin_user_and_token):
        """Admin can access email-logs (200)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/email-logs",
            headers={"Authorization": f"Bearer {admin_user_and_token['token']}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ Admin can access email-logs")
    
    def test_admin_can_access_programs_read(self, admin_user_and_token):
        """Admin can read programs (200) - read-only access"""
        response = requests.get(
            f"{BASE_URL}/api/admin/programs",
            headers={"Authorization": f"Bearer {admin_user_and_token['token']}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ Admin can read programs (GET)")
    
    def test_admin_can_access_capacity_read(self, admin_user_and_token):
        """Admin can read capacity (200) - read-only access"""
        response = requests.get(
            f"{BASE_URL}/api/admin/capacity",
            headers={"Authorization": f"Bearer {admin_user_and_token['token']}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ Admin can read capacity (GET)")


class TestAdminEndpointRestrictions:
    """Test admin role endpoint restrictions - CANNOT access settings, programs POST/PUT, capacity PUT"""
    
    def test_admin_cannot_access_settings(self, admin_user_and_token):
        """Admin CANNOT access settings (403)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/settings",
            headers={"Authorization": f"Bearer {admin_user_and_token['token']}"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print("✓ Admin correctly blocked from settings")
    
    def test_admin_cannot_create_program(self, admin_user_and_token):
        """Admin CANNOT create programs (403)"""
        response = requests.post(
            f"{BASE_URL}/api/admin/programs",
            headers={"Authorization": f"Bearer {admin_user_and_token['token']}"},
            json={
                "name_es": "Test Program",
                "name_en": "Test Program",
                "description_es": "Test",
                "description_en": "Test",
                "duration_value": 2,
                "duration_unit": "weeks",
                "price": 100.0
            }
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print("✓ Admin correctly blocked from creating programs")
    
    def test_admin_cannot_update_program(self, admin_user_and_token, superadmin_token):
        """Admin CANNOT update programs (403)"""
        # First get a program ID
        programs_response = requests.get(
            f"{BASE_URL}/api/admin/programs",
            headers={"Authorization": f"Bearer {superadmin_token}"}
        )
        programs = programs_response.json()
        if not programs:
            pytest.skip("No programs available to test update")
        
        program_id = programs[0]["id"]
        
        response = requests.put(
            f"{BASE_URL}/api/admin/programs/{program_id}",
            headers={"Authorization": f"Bearer {admin_user_and_token['token']}"},
            json={
                "name_es": "Updated Program",
                "name_en": "Updated Program",
                "description_es": "Updated",
                "description_en": "Updated",
                "duration_value": 2,
                "duration_unit": "weeks",
                "price": 150.0
            }
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print("✓ Admin correctly blocked from updating programs")
    
    def test_admin_cannot_update_capacity(self, admin_user_and_token):
        """Admin CANNOT update capacity (403)"""
        response = requests.put(
            f"{BASE_URL}/api/admin/capacity/2026-04-06",
            headers={"Authorization": f"Bearer {admin_user_and_token['token']}"},
            json={"capacity": 10}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print("✓ Admin correctly blocked from updating capacity")


class TestOperatorEndpointAccess:
    """Test operator role endpoint access - can access bookings list, booking detail, documents"""
    
    def test_operator_can_access_bookings(self, operator_user_and_token):
        """Operator can access bookings list (200)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/bookings",
            headers={"Authorization": f"Bearer {operator_user_and_token['token']}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ Operator can access bookings list")
    
    def test_operator_can_access_programs_read(self, operator_user_and_token):
        """Operator can read programs (200) - read-only access"""
        response = requests.get(
            f"{BASE_URL}/api/admin/programs",
            headers={"Authorization": f"Bearer {operator_user_and_token['token']}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ Operator can read programs (GET)")
    
    def test_operator_can_access_capacity_read(self, operator_user_and_token):
        """Operator can read capacity (200) - read-only access"""
        response = requests.get(
            f"{BASE_URL}/api/admin/capacity",
            headers={"Authorization": f"Bearer {operator_user_and_token['token']}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ Operator can read capacity (GET)")


class TestOperatorEndpointRestrictions:
    """Test operator role endpoint restrictions - CANNOT access dashboard, settings, programs POST, capacity PUT, email-logs, manual booking"""
    
    def test_operator_cannot_access_dashboard(self, operator_user_and_token):
        """Operator CANNOT access dashboard (403)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/dashboard",
            headers={"Authorization": f"Bearer {operator_user_and_token['token']}"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print("✓ Operator correctly blocked from dashboard")
    
    def test_operator_cannot_access_settings(self, operator_user_and_token):
        """Operator CANNOT access settings (403)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/settings",
            headers={"Authorization": f"Bearer {operator_user_and_token['token']}"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print("✓ Operator correctly blocked from settings")
    
    def test_operator_cannot_create_program(self, operator_user_and_token):
        """Operator CANNOT create programs (403)"""
        response = requests.post(
            f"{BASE_URL}/api/admin/programs",
            headers={"Authorization": f"Bearer {operator_user_and_token['token']}"},
            json={
                "name_es": "Test Program",
                "name_en": "Test Program",
                "description_es": "Test",
                "description_en": "Test",
                "duration_value": 2,
                "duration_unit": "weeks",
                "price": 100.0
            }
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print("✓ Operator correctly blocked from creating programs")
    
    def test_operator_cannot_update_capacity(self, operator_user_and_token):
        """Operator CANNOT update capacity (403)"""
        response = requests.put(
            f"{BASE_URL}/api/admin/capacity/2026-04-06",
            headers={"Authorization": f"Bearer {operator_user_and_token['token']}"},
            json={"capacity": 10}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print("✓ Operator correctly blocked from updating capacity")
    
    def test_operator_cannot_access_email_logs(self, operator_user_and_token):
        """Operator CANNOT access email-logs (403)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/email-logs",
            headers={"Authorization": f"Bearer {operator_user_and_token['token']}"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print("✓ Operator correctly blocked from email-logs")
    
    def test_operator_cannot_create_manual_booking(self, operator_user_and_token, superadmin_token):
        """Operator CANNOT create manual booking (403)"""
        # Get a program ID first
        programs_response = requests.get(
            f"{BASE_URL}/api/admin/programs",
            headers={"Authorization": f"Bearer {superadmin_token}"}
        )
        programs = programs_response.json()
        if not programs:
            pytest.skip("No programs available to test manual booking")
        
        program_id = programs[0]["id"]
        
        response = requests.post(
            f"{BASE_URL}/api/admin/bookings/manual",
            headers={"Authorization": f"Bearer {operator_user_and_token['token']}"},
            json={
                "program_id": program_id,
                "start_week": "2026-04-06",
                "locale": "es",
                "owner_full_name": "Test Owner",
                "owner_email": "test@test.com",
                "owner_phone": "+34600123456",
                "owner_address": "Test Address",
                "dog_name": "Test Dog",
                "breed": "Test Breed",
                "sex": "male",
                "weight": "10kg",
                "date_of_birth": "2024-01-01",
                "vaccination_status": "up_to_date",
                "behavior_goals": "Test goals"
            }
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print("✓ Operator correctly blocked from creating manual booking")


class TestOperatorFinancialDataStripping:
    """Test that operator bookings list does NOT contain financial fields"""
    
    def test_operator_bookings_no_financial_fields(self, operator_user_and_token):
        """Operator bookings list should NOT contain: program_price, deposit_amount, balance_amount, overall_payment_status, program_snapshot"""
        response = requests.get(
            f"{BASE_URL}/api/admin/bookings",
            headers={"Authorization": f"Bearer {operator_user_and_token['token']}"}
        )
        assert response.status_code == 200
        bookings = response.json()
        
        financial_fields = {"program_price", "deposit_amount", "balance_amount", "overall_payment_status", "program_snapshot"}
        
        for booking in bookings:
            for field in financial_fields:
                assert field not in booking, f"Financial field '{field}' should NOT be in operator booking response"
        
        print(f"✓ Operator bookings list correctly strips financial fields ({len(bookings)} bookings checked)")
    
    def test_operator_bookings_payment_status_simplified(self, operator_user_and_token):
        """Operator bookings list payment_status should show only 'Paid' or 'Pending'"""
        response = requests.get(
            f"{BASE_URL}/api/admin/bookings",
            headers={"Authorization": f"Bearer {operator_user_and_token['token']}"}
        )
        assert response.status_code == 200
        bookings = response.json()
        
        valid_payment_statuses = {"Paid", "Pending"}
        
        for booking in bookings:
            if "payment_status" in booking:
                assert booking["payment_status"] in valid_payment_statuses, f"payment_status should be 'Paid' or 'Pending', got '{booking['payment_status']}'"
            if "final_payment_status" in booking:
                assert booking["final_payment_status"] in valid_payment_statuses, f"final_payment_status should be 'Paid' or 'Pending', got '{booking['final_payment_status']}'"
        
        print(f"✓ Operator bookings payment_status correctly simplified ({len(bookings)} bookings checked)")
    
    def test_operator_booking_detail_no_financial_fields(self, operator_user_and_token, superadmin_token):
        """Operator booking detail should NOT contain financial fields"""
        # Get a booking ID first
        bookings_response = requests.get(
            f"{BASE_URL}/api/admin/bookings",
            headers={"Authorization": f"Bearer {superadmin_token}"}
        )
        bookings = bookings_response.json()
        if not bookings:
            pytest.skip("No bookings available to test detail")
        
        booking_id = bookings[0]["id"]
        
        response = requests.get(
            f"{BASE_URL}/api/admin/bookings/{booking_id}",
            headers={"Authorization": f"Bearer {operator_user_and_token['token']}"}
        )
        assert response.status_code == 200
        booking = response.json()
        
        financial_fields = {"program_price", "deposit_amount", "balance_amount", "overall_payment_status", "program_snapshot"}
        
        for field in financial_fields:
            assert field not in booking, f"Financial field '{field}' should NOT be in operator booking detail"
        
        print(f"✓ Operator booking detail correctly strips financial fields")


class TestOperatorBookingUpdateRestrictions:
    """Test operator PATCH booking restrictions - can only update status field"""
    
    def test_operator_can_update_status_only(self, operator_user_and_token, superadmin_token):
        """Operator PATCH booking with status field only succeeds (200)"""
        # Get a booking ID first
        bookings_response = requests.get(
            f"{BASE_URL}/api/admin/bookings",
            headers={"Authorization": f"Bearer {superadmin_token}"}
        )
        bookings = bookings_response.json()
        if not bookings:
            pytest.skip("No bookings available to test update")
        
        # Find a booking that can be updated
        booking = bookings[0]
        booking_id = booking["id"]
        original_status = booking["status"]
        
        # Try to update status only
        new_status = "In Training" if original_status != "In Training" else "Scheduled"
        
        response = requests.patch(
            f"{BASE_URL}/api/admin/bookings/{booking_id}",
            headers={"Authorization": f"Bearer {operator_user_and_token['token']}"},
            json={"status": new_status}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Restore original status
        requests.patch(
            f"{BASE_URL}/api/admin/bookings/{booking_id}",
            headers={"Authorization": f"Bearer {superadmin_token}"},
            json={"status": original_status}
        )
        
        print(f"✓ Operator can update booking status")
    
    def test_operator_cannot_update_payment_status(self, operator_user_and_token, superadmin_token):
        """Operator PATCH booking with payment_status returns 403"""
        # Get a booking ID first
        bookings_response = requests.get(
            f"{BASE_URL}/api/admin/bookings",
            headers={"Authorization": f"Bearer {superadmin_token}"}
        )
        bookings = bookings_response.json()
        if not bookings:
            pytest.skip("No bookings available to test update")
        
        booking_id = bookings[0]["id"]
        
        response = requests.patch(
            f"{BASE_URL}/api/admin/bookings/{booking_id}",
            headers={"Authorization": f"Bearer {operator_user_and_token['token']}"},
            json={"payment_status": "Verified"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print(f"✓ Operator correctly blocked from updating payment_status")
    
    def test_operator_cannot_update_internal_notes(self, operator_user_and_token, superadmin_token):
        """Operator PATCH booking with internal_notes returns 403"""
        # Get a booking ID first
        bookings_response = requests.get(
            f"{BASE_URL}/api/admin/bookings",
            headers={"Authorization": f"Bearer {superadmin_token}"}
        )
        bookings = bookings_response.json()
        if not bookings:
            pytest.skip("No bookings available to test update")
        
        booking_id = bookings[0]["id"]
        
        response = requests.patch(
            f"{BASE_URL}/api/admin/bookings/{booking_id}",
            headers={"Authorization": f"Bearer {operator_user_and_token['token']}"},
            json={"internal_notes": "Test notes"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print(f"✓ Operator correctly blocked from updating internal_notes")
    
    def test_operator_cannot_update_eligibility_status(self, operator_user_and_token, superadmin_token):
        """Operator PATCH booking with eligibility_status returns 403"""
        # Get a booking ID first
        bookings_response = requests.get(
            f"{BASE_URL}/api/admin/bookings",
            headers={"Authorization": f"Bearer {superadmin_token}"}
        )
        bookings = bookings_response.json()
        if not bookings:
            pytest.skip("No bookings available to test update")
        
        booking_id = bookings[0]["id"]
        
        response = requests.patch(
            f"{BASE_URL}/api/admin/bookings/{booking_id}",
            headers={"Authorization": f"Bearer {operator_user_and_token['token']}"},
            json={"eligibility_status": "Eligible"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print(f"✓ Operator correctly blocked from updating eligibility_status")


class TestSuperadminVsAdminBookingsComparison:
    """Compare superadmin and admin bookings response to verify admin gets full financial data"""
    
    def test_admin_bookings_has_financial_fields(self, admin_user_and_token):
        """Admin bookings list SHOULD contain financial fields (unlike operator)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/bookings",
            headers={"Authorization": f"Bearer {admin_user_and_token['token']}"}
        )
        assert response.status_code == 200
        bookings = response.json()
        
        if not bookings:
            pytest.skip("No bookings available to verify financial fields")
        
        # Admin should see financial fields
        booking = bookings[0]
        financial_fields = {"program_price", "deposit_amount", "balance_amount", "overall_payment_status"}
        
        for field in financial_fields:
            assert field in booking, f"Admin should see financial field '{field}' in booking response"
        
        print(f"✓ Admin bookings list correctly includes financial fields")


class TestPublicEndpointsNoRegression:
    """Test that public endpoints still work (no regression)"""
    
    def test_public_config_accessible(self):
        """Public config endpoint works without auth"""
        response = requests.get(f"{BASE_URL}/api/public/config")
        assert response.status_code == 200, f"Public config failed: {response.text}"
        data = response.json()
        assert "business_name" in data
        print(f"✓ Public config endpoint works")
    
    def test_public_programs_accessible(self):
        """Public programs endpoint works without auth"""
        response = requests.get(f"{BASE_URL}/api/public/programs")
        assert response.status_code == 200, f"Public programs failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Public programs endpoint works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
