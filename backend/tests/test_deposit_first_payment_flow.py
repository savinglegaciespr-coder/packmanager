"""
Test suite for the deposit-first booking flow with token-based final payment upload.

Flow:
1. Client creates booking with deposit proof (public booking)
2. Admin verifies deposit (PATCH payment_status=Verified)
3. System sends deposit-verified email with /payment/{token} link
4. Client opens link → sees summary + upload form (GET /api/public/booking-payment/{token})
5. Client uploads final proof (POST /api/public/booking-payment/{token}/upload)
6. Admin gets notification email
"""

import io
import os
import pytest
import requests
import time

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
ADMIN_EMAIL = "admin@pawstraining.com"
ADMIN_PASSWORD = "PawsAdmin2026!"


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def admin_token(api_client):
    """Get admin authentication token"""
    response = api_client.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    return response.json()["token"]


@pytest.fixture(scope="module")
def test_booking_with_token(api_client, admin_token):
    """Create a test booking via public endpoint and return booking_id and token"""
    # Create a dummy PDF file for payment proof
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    
    # Use multipart form data
    files = {
        "payment_proof": ("deposit_proof.pdf", io.BytesIO(pdf_content), "application/pdf"),
        "vaccination_certificate": ("vaccination.pdf", io.BytesIO(pdf_content), "application/pdf"),
    }
    
    data = {
        "program_id": "basic-6-day",
        "start_week": "2026-06-01",
        "locale": "en",
        "owner_full_name": "TEST_DepositFlow_John Doe",
        "owner_email": "test.depositflow@example.com",
        "owner_phone": "+1234567890",
        "owner_address": "123 Test Street, Test City",
        "dog_name": "TEST_DepositFlow_Buddy",
        "breed": "Golden Retriever",
        "date_of_birth": "2023-01-15",
        "sex": "Male",
        "weight": "25",
        "vaccination_status": "Up to date",
        "allergies": "",
        "behavior_goals": "Basic obedience and socialization",
    }
    
    # Submit booking (no Content-Type header for multipart)
    session = requests.Session()
    response = session.post(f"{BASE_URL}/api/public/bookings", data=data, files=files)
    assert response.status_code == 200, f"Public booking creation failed: {response.text}"
    
    result = response.json()
    booking_id = result["booking_id"]
    
    # Get the booking to retrieve the final_payment_token
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = api_client.get(f"{BASE_URL}/api/admin/bookings/{booking_id}", headers=headers)
    assert response.status_code == 200, f"Failed to get booking: {response.text}"
    
    booking = response.json()
    token = booking.get("final_payment_token")
    
    return {
        "booking_id": booking_id,
        "final_payment_token": token,
        "owner_name": "TEST_DepositFlow_John Doe",
        "dog_name": "TEST_DepositFlow_Buddy",
    }


class TestPublicBookingCreatesToken:
    """Test that public booking creates a booking with final_payment_token field"""
    
    def test_public_booking_has_final_payment_token(self, api_client, admin_token, test_booking_with_token):
        """Verify that public booking creates a booking with final_payment_token"""
        booking_id = test_booking_with_token["booking_id"]
        token = test_booking_with_token["final_payment_token"]
        
        assert token is not None, "final_payment_token should be generated"
        assert len(token) > 20, "final_payment_token should be a secure token"
        print(f"✓ Public booking created with final_payment_token: {token[:10]}...")


class TestGetBookingByPaymentToken:
    """Test GET /api/public/booking-payment/{token} endpoint"""
    
    def test_get_booking_summary_returns_correct_fields(self, api_client, test_booking_with_token):
        """Verify that public endpoint returns booking summary with correct fields"""
        token = test_booking_with_token["final_payment_token"]
        
        response = api_client.get(f"{BASE_URL}/api/public/booking-payment/{token}")
        assert response.status_code == 200, f"Failed to get booking by token: {response.text}"
        
        data = response.json()
        
        # Verify all required fields
        required_fields = [
            "booking_id", "owner_name", "dog_name", "program_name_es", "program_name_en",
            "program_price", "deposit_amount", "balance_amount", "start_week", "status",
            "payment_status", "final_payment_status", "overall_payment_status",
            "final_payment_proof_uploaded", "locale", "currency", "business_name"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Verify values
        assert data["owner_name"] == test_booking_with_token["owner_name"]
        assert data["dog_name"] == test_booking_with_token["dog_name"]
        assert data["final_payment_proof_uploaded"] == False
        assert data["payment_status"] == "Pending Review"  # Not yet verified
        assert data["overall_payment_status"] == "Deposit Pending"
        
        print(f"✓ GET /api/public/booking-payment/{token[:10]}... returns correct summary")
    
    def test_invalid_token_returns_404(self, api_client):
        """Verify that invalid token returns 404"""
        response = api_client.get(f"{BASE_URL}/api/public/booking-payment/invalid-token-12345")
        assert response.status_code == 404, f"Expected 404 for invalid token, got {response.status_code}"
        print("✓ Invalid token correctly returns 404")


class TestUploadFinalPaymentViaToken:
    """Test POST /api/public/booking-payment/{token}/upload endpoint"""
    
    def test_upload_blocked_if_deposit_not_verified(self, api_client, test_booking_with_token):
        """Verify that upload is blocked if deposit (payment_status) is not Verified"""
        token = test_booking_with_token["final_payment_token"]
        
        # Try to upload without deposit being verified
        pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
        files = {"file": ("final_payment.pdf", io.BytesIO(pdf_content), "application/pdf")}
        
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/public/booking-payment/{token}/upload", files=files)
        
        assert response.status_code == 400, f"Expected 400 when deposit not verified, got {response.status_code}"
        assert "Deposit must be verified" in response.json().get("detail", ""), "Should mention deposit verification"
        print("✓ Upload blocked correctly when deposit not verified")


class TestDepositVerificationTriggersEmail:
    """Test that verifying deposit triggers email with payment link"""
    
    def test_verify_deposit_triggers_email(self, api_client, admin_token, test_booking_with_token):
        """Verify that setting payment_status=Verified triggers deposit-verified email"""
        booking_id = test_booking_with_token["booking_id"]
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get email log count before
        response = api_client.get(f"{BASE_URL}/api/admin/email-logs", headers=headers)
        assert response.status_code == 200
        initial_logs = response.json()
        
        # Verify deposit
        response = api_client.patch(
            f"{BASE_URL}/api/admin/bookings/{booking_id}",
            json={"payment_status": "Verified"},
            headers=headers
        )
        assert response.status_code == 200, f"Failed to verify deposit: {response.text}"
        
        # Check booking status updated
        data = response.json()
        assert data["payment_status"] == "Verified"
        
        # Check email logs for deposit-verified email
        time.sleep(0.5)  # Give time for email to be logged
        response = api_client.get(f"{BASE_URL}/api/admin/email-logs", headers=headers)
        assert response.status_code == 200
        new_logs = response.json()
        
        # Find the deposit-verified email
        deposit_emails = [
            log for log in new_logs 
            if ("Deposit verified" in log.get("subject", "") or 
                "Depósito verificado" in log.get("subject", "") or
                "/payment/" in log.get("body", ""))
        ]
        
        assert len(deposit_emails) > 0, "Deposit-verified email should be sent"
        
        # Verify email body contains the payment link
        email_body = deposit_emails[0].get("body", "")
        token = test_booking_with_token["final_payment_token"]
        assert f"/payment/{token}" in email_body, "Email should contain /payment/{token} link"
        
        print(f"✓ Deposit verification triggers email with correct /payment/{token[:10]}... link")


class TestFinalPaymentUploadAfterVerification:
    """Test final payment upload after deposit verification"""
    
    def test_upload_final_payment_success(self, api_client, admin_token, test_booking_with_token):
        """Verify that upload succeeds after deposit verification"""
        token = test_booking_with_token["final_payment_token"]
        booking_id = test_booking_with_token["booking_id"]
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Ensure deposit is verified (may already be verified from previous test)
        response = api_client.patch(
            f"{BASE_URL}/api/admin/bookings/{booking_id}",
            json={"payment_status": "Verified"},
            headers=headers
        )
        # Don't assert here as it may already be verified
        
        # Now upload final payment
        pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
        files = {"file": ("final_payment.pdf", io.BytesIO(pdf_content), "application/pdf")}
        
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/public/booking-payment/{token}/upload", files=files)
        
        assert response.status_code == 200, f"Failed to upload final payment: {response.text}"
        data = response.json()
        assert data.get("message") == "Final payment proof uploaded successfully."
        assert data.get("overall_payment_status") == "Balance Pending"
        
        print("✓ Final payment upload succeeded after deposit verification")
    
    def test_re_upload_blocked(self, api_client, test_booking_with_token):
        """Verify that re-uploading final payment is blocked"""
        token = test_booking_with_token["final_payment_token"]
        
        pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
        files = {"file": ("final_payment_2.pdf", io.BytesIO(pdf_content), "application/pdf")}
        
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/public/booking-payment/{token}/upload", files=files)
        
        assert response.status_code == 400, f"Expected 400 on re-upload, got {response.status_code}"
        assert "already been uploaded" in response.json().get("detail", "")
        print("✓ Re-upload correctly blocked")


class TestOverallPaymentStatusTransitions:
    """Test overall_payment_status transitions correctly"""
    
    def test_payment_status_transitions(self, api_client, admin_token, test_booking_with_token):
        """Verify overall_payment_status transitions: Deposit Pending → Deposit Verified → Balance Pending → Paid in Full"""
        booking_id = test_booking_with_token["booking_id"]
        token = test_booking_with_token["final_payment_token"]
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Check current state (should be Balance Pending after upload)
        response = api_client.get(f"{BASE_URL}/api/public/booking-payment/{token}")
        assert response.status_code == 200
        data = response.json()
        
        # Should be Balance Pending after final payment upload
        assert data["overall_payment_status"] == "Balance Pending", f"Expected 'Balance Pending', got '{data['overall_payment_status']}'"
        print(f"✓ Status is 'Balance Pending' after final payment upload")
        
        # Now verify final payment to make it 'Paid in Full'
        response = api_client.patch(
            f"{BASE_URL}/api/admin/bookings/{booking_id}",
            json={"final_payment_status": "Verified"},
            headers=headers
        )
        assert response.status_code == 200, f"Failed to verify final payment: {response.text}"
        
        # Check status is now Paid in Full
        response = api_client.get(f"{BASE_URL}/api/public/booking-payment/{token}")
        assert response.status_code == 200
        data = response.json()
        
        assert data["overall_payment_status"] == "Paid in Full", f"Expected 'Paid in Full', got '{data['overall_payment_status']}'"
        print("✓ Status correctly transitions to 'Paid in Full' after final payment verification")


class TestAdminNotificationOnFinalUpload:
    """Test that admin notification email is sent after final payment upload"""
    
    def test_admin_notification_sent(self, api_client, admin_token):
        """Create a new booking, verify deposit, upload final, and check admin notification"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a new test booking
        pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
        
        files = {
            "payment_proof": ("deposit_proof.pdf", io.BytesIO(pdf_content), "application/pdf"),
            "vaccination_certificate": ("vaccination.pdf", io.BytesIO(pdf_content), "application/pdf"),
        }
        
        data = {
            "program_id": "basic-6-day",
            "start_week": "2026-06-08",
            "locale": "es",
            "owner_full_name": "TEST_AdminNotify_Maria Garcia",
            "owner_email": "test.adminnotify@example.com",
            "owner_phone": "+1234567890",
            "owner_address": "456 Test Avenue",
            "dog_name": "TEST_AdminNotify_Luna",
            "breed": "German Shepherd",
            "date_of_birth": "2022-06-15",
            "sex": "Female",
            "weight": "30",
            "vaccination_status": "Up to date",
            "allergies": "",
            "behavior_goals": "Aggression management",
        }
        
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/public/bookings", data=data, files=files)
        assert response.status_code == 200, f"Failed to create booking: {response.text}"
        booking_id = response.json()["booking_id"]
        
        # Get token
        client = requests.Session()
        client.headers.update({"Content-Type": "application/json"})
        response = client.get(f"{BASE_URL}/api/admin/bookings/{booking_id}", headers=headers)
        assert response.status_code == 200
        token = response.json().get("final_payment_token")
        
        # Verify deposit
        response = client.patch(
            f"{BASE_URL}/api/admin/bookings/{booking_id}",
            json={"payment_status": "Verified"},
            headers=headers
        )
        assert response.status_code == 200
        
        # Get email count before upload
        response = client.get(f"{BASE_URL}/api/admin/email-logs", headers=headers)
        logs_before = len(response.json())
        
        # Upload final payment
        files = {"file": ("final_payment.pdf", io.BytesIO(pdf_content), "application/pdf")}
        response = session.post(f"{BASE_URL}/api/public/booking-payment/{token}/upload", files=files)
        assert response.status_code == 200
        
        # Check for admin notification email
        time.sleep(0.5)
        response = client.get(f"{BASE_URL}/api/admin/email-logs", headers=headers)
        logs_after = response.json()
        
        # Find admin notification about final payment
        admin_notifications = [
            log for log in logs_after
            if log.get("audience") == "admin" and
               ("Pago final" in log.get("subject", "") or 
                "final payment" in log.get("subject", "").lower() or
                "TEST_AdminNotify_Luna" in log.get("body", ""))
        ]
        
        assert len(admin_notifications) > 0, "Admin notification email should be sent after final payment upload"
        print(f"✓ Admin notification email sent after final payment upload")


class TestEmailContainsCorrectPaymentLink:
    """Test that the deposit-verified email contains the correct payment link"""
    
    def test_email_payment_link_format(self, api_client, admin_token):
        """Verify that email body contains correctly formatted /payment/{token} link"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a test booking
        pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
        
        files = {
            "payment_proof": ("deposit_proof.pdf", io.BytesIO(pdf_content), "application/pdf"),
            "vaccination_certificate": ("vaccination.pdf", io.BytesIO(pdf_content), "application/pdf"),
        }
        
        data = {
            "program_id": "basic-6-day",
            "start_week": "2026-06-15",
            "locale": "en",
            "owner_full_name": "TEST_EmailLink_Bob Wilson",
            "owner_email": "test.emaillink@example.com",
            "owner_phone": "+1234567890",
            "owner_address": "789 Test Blvd",
            "dog_name": "TEST_EmailLink_Max",
            "breed": "Labrador",
            "date_of_birth": "2024-01-01",
            "sex": "Male",
            "weight": "20",
            "vaccination_status": "Up to date",
            "allergies": "",
            "behavior_goals": "Puppy training",
        }
        
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/public/bookings", data=data, files=files)
        assert response.status_code == 200
        booking_id = response.json()["booking_id"]
        
        # Get token
        client = requests.Session()
        client.headers.update({"Content-Type": "application/json"})
        response = client.get(f"{BASE_URL}/api/admin/bookings/{booking_id}", headers=headers)
        token = response.json().get("final_payment_token")
        
        # Verify deposit to trigger email
        response = client.patch(
            f"{BASE_URL}/api/admin/bookings/{booking_id}",
            json={"payment_status": "Verified"},
            headers=headers
        )
        assert response.status_code == 200
        
        time.sleep(0.5)
        
        # Check email logs
        response = client.get(f"{BASE_URL}/api/admin/email-logs", headers=headers)
        logs = response.json()
        
        # Find deposit-verified email for this booking
        deposit_emails = [
            log for log in logs
            if log.get("booking_id") == booking_id and
               ("Deposit verified" in log.get("subject", "") or 
                "Depósito verificado" in log.get("subject", ""))
        ]
        
        assert len(deposit_emails) > 0, "Deposit-verified email should exist"
        
        email_body = deposit_emails[0].get("body", "")
        
        # Verify email contains frontend URL with payment link
        frontend_url = os.environ.get("FRONTEND_URL", "https://dog-training-app-7.preview.emergentagent.com")
        expected_link = f"{frontend_url}/payment/{token}"
        
        assert expected_link in email_body or f"/payment/{token}" in email_body, \
            f"Email should contain payment link. Found body: {email_body[:200]}..."
        
        print(f"✓ Email contains correct payment link: /payment/{token[:10]}...")


# Cleanup fixture
@pytest.fixture(scope="module", autouse=True)
def cleanup_test_bookings(api_client, admin_token):
    """Cleanup test bookings after all tests"""
    yield
    
    # Cleanup is optional - test data with TEST_ prefix
    headers = {"Authorization": f"Bearer {admin_token}"}
    try:
        response = api_client.get(f"{BASE_URL}/api/admin/bookings", headers=headers)
        if response.status_code == 200:
            bookings = response.json()
            for booking in bookings:
                if "TEST_" in booking.get("owner", {}).get("full_name", "") or \
                   "TEST_" in booking.get("dog", {}).get("name", ""):
                    # Could delete here if needed
                    pass
    except Exception:
        pass
