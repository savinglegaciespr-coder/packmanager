"""
Test Two-Stage Payment System for PAWS TRAINING
Tests: final_payment_status, final_payment_proof, overall_payment_status computation
"""
import os
import pytest
import requests
import tempfile
import uuid
from io import BytesIO

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
ADMIN_EMAIL = "admin@pawstraining.com"
ADMIN_PASSWORD = os.environ.get("TEST_ADMIN_PASSWORD", "")


@pytest.fixture(scope="module")
def auth_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["token"]


@pytest.fixture
def auth_headers(auth_token):
    """Auth headers for API requests"""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def test_pdf_file():
    """Create a simple test PDF file"""
    # Minimal valid PDF content
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
endobj
xref
0 4
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
trailer
<< /Size 4 /Root 1 0 R >>
startxref
196
%%EOF"""
    return pdf_content


class TestTwoStagePaymentBackend:
    """Backend API tests for two-stage payment system"""

    # Test 1: GET /api/admin/bookings returns bookings with new payment fields
    def test_get_bookings_has_payment_fields(self, auth_headers):
        """Verify GET /api/admin/bookings returns final_payment_status, final_payment_proof, overall_payment_status"""
        response = requests.get(f"{BASE_URL}/api/admin/bookings", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get bookings: {response.text}"
        
        bookings = response.json()
        assert isinstance(bookings, list), "Bookings should be a list"
        assert len(bookings) > 0, "Should have at least one booking"
        
        # Check first booking has required fields
        booking = bookings[0]
        assert "final_payment_status" in booking, "Booking should have final_payment_status"
        assert "final_payment_proof" in booking, "Booking should have final_payment_proof field (can be null)"
        assert "overall_payment_status" in booking, "Booking should have overall_payment_status"
        
        # Validate overall_payment_status values
        valid_overall_statuses = ["Deposit Pending", "Deposit Verified", "Balance Pending", "Paid in Full"]
        assert booking["overall_payment_status"] in valid_overall_statuses, \
            f"overall_payment_status should be one of {valid_overall_statuses}, got {booking['overall_payment_status']}"
        
        print(f"✓ Booking has all required payment fields")
        print(f"  - final_payment_status: {booking['final_payment_status']}")
        print(f"  - final_payment_proof: {booking['final_payment_proof']}")
        print(f"  - overall_payment_status: {booking['overall_payment_status']}")

    # Test 2: PATCH /api/admin/bookings/{id} accepts final_payment_status
    def test_update_booking_final_payment_status(self, auth_headers):
        """Test PATCH /api/admin/bookings/{id} accepts and updates final_payment_status"""
        # Get a booking to update
        response = requests.get(f"{BASE_URL}/api/admin/bookings", headers=auth_headers)
        bookings = response.json()
        test_booking = None
        for b in bookings:
            if b.get("payment_status") == "Verified":
                test_booking = b
                break
        
        if not test_booking:
            # Use first booking
            test_booking = bookings[0]
        
        booking_id = test_booking["id"]
        original_final_status = test_booking.get("final_payment_status", "Pending Review")
        
        # Test setting final_payment_status to each valid value
        for status in ["Pending Review", "Verified", "Invalid"]:
            update_response = requests.patch(
                f"{BASE_URL}/api/admin/bookings/{booking_id}",
                json={"final_payment_status": status},
                headers=auth_headers
            )
            assert update_response.status_code == 200, f"Failed to update final_payment_status to {status}: {update_response.text}"
            
            updated = update_response.json()
            assert updated["final_payment_status"] == status, \
                f"final_payment_status should be {status}, got {updated['final_payment_status']}"
            print(f"✓ Updated final_payment_status to '{status}'")
        
        # Restore original status
        requests.patch(
            f"{BASE_URL}/api/admin/bookings/{booking_id}",
            json={"final_payment_status": original_final_status},
            headers=auth_headers
        )
        print("✓ Restored original final_payment_status")

    # Test 3: Invalid final_payment_status is rejected
    def test_update_booking_invalid_final_payment_status(self, auth_headers):
        """Test PATCH rejects invalid final_payment_status values"""
        response = requests.get(f"{BASE_URL}/api/admin/bookings", headers=auth_headers)
        booking_id = response.json()[0]["id"]
        
        invalid_response = requests.patch(
            f"{BASE_URL}/api/admin/bookings/{booking_id}",
            json={"final_payment_status": "InvalidStatus"},
            headers=auth_headers
        )
        assert invalid_response.status_code == 400, "Should reject invalid final_payment_status"
        print("✓ Invalid final_payment_status correctly rejected")


class TestOverallPaymentStatusComputation:
    """Tests for overall_payment_status computation logic"""
    
    # Test 4: Deposit Pending - when payment_status is not Verified
    def test_overall_deposit_pending(self, auth_headers):
        """deposit Pending Review + no final proof = 'Deposit Pending'"""
        response = requests.get(f"{BASE_URL}/api/admin/bookings", headers=auth_headers)
        bookings = response.json()
        
        for booking in bookings:
            if booking["payment_status"] != "Verified":
                assert booking["overall_payment_status"] == "Deposit Pending", \
                    f"Expected 'Deposit Pending' when payment_status={booking['payment_status']}, got {booking['overall_payment_status']}"
                print(f"✓ Booking {booking['id'][:8]}... has overall_payment_status='Deposit Pending' (deposit not verified)")
                return
        
        print("⚠ No booking found with payment_status != Verified to test Deposit Pending state")

    # Test 5: Deposit Verified - deposit verified, no final proof
    def test_overall_deposit_verified(self, auth_headers):
        """deposit Verified + no final proof = 'Deposit Verified'"""
        response = requests.get(f"{BASE_URL}/api/admin/bookings", headers=auth_headers)
        bookings = response.json()
        
        for booking in bookings:
            if (booking["payment_status"] == "Verified" and 
                booking.get("final_payment_proof") is None and 
                booking.get("final_payment_status") != "Verified"):
                assert booking["overall_payment_status"] == "Deposit Verified", \
                    f"Expected 'Deposit Verified', got {booking['overall_payment_status']}"
                print(f"✓ Booking {booking['id'][:8]}... has overall_payment_status='Deposit Verified'")
                return
        
        print("⚠ No booking matching Deposit Verified criteria found")

    # Test 6: Paid in Full - both verified
    def test_overall_paid_in_full(self, auth_headers):
        """both Verified = 'Paid in Full'"""
        response = requests.get(f"{BASE_URL}/api/admin/bookings", headers=auth_headers)
        bookings = response.json()
        
        for booking in bookings:
            if booking["payment_status"] == "Verified" and booking.get("final_payment_status") == "Verified":
                assert booking["overall_payment_status"] == "Paid in Full", \
                    f"Expected 'Paid in Full', got {booking['overall_payment_status']}"
                print(f"✓ Booking {booking['id'][:8]}... has overall_payment_status='Paid in Full'")
                return
        
        print("⚠ No booking with both statuses Verified found - will be tested via update")


class TestFinalPaymentProofUpload:
    """Tests for final payment proof upload endpoint"""

    # Test 7: Upload final payment proof
    def test_upload_final_payment_proof(self, auth_headers, test_pdf_file):
        """POST /api/admin/bookings/{id}/final-payment-proof uploads a file"""
        # Get a booking
        response = requests.get(f"{BASE_URL}/api/admin/bookings", headers=auth_headers)
        bookings = response.json()
        
        # Find a booking with Verified deposit that doesn't have final payment proof
        test_booking = None
        for b in bookings:
            if b.get("payment_status") == "Verified" and b.get("final_payment_proof") is None:
                test_booking = b
                break
        
        if not test_booking:
            test_booking = bookings[0]
        
        booking_id = test_booking["id"]
        
        # Upload final payment proof
        files = {"file": ("test_final_payment.pdf", test_pdf_file, "application/pdf")}
        upload_response = requests.post(
            f"{BASE_URL}/api/admin/bookings/{booking_id}/final-payment-proof",
            headers=auth_headers,
            files=files
        )
        
        assert upload_response.status_code == 200, f"Failed to upload final payment proof: {upload_response.text}"
        
        result = upload_response.json()
        assert result["final_payment_proof"] is not None, "final_payment_proof should be set after upload"
        assert "original_name" in result["final_payment_proof"], "Should have original_name"
        assert "stored_name" in result["final_payment_proof"], "Should have stored_name"
        
        print(f"✓ Successfully uploaded final payment proof to booking {booking_id[:8]}...")
        print(f"  - original_name: {result['final_payment_proof']['original_name']}")
        print(f"  - stored_name: {result['final_payment_proof']['stored_name']}")
        
        return booking_id

    # Test 8: Verify Balance Pending status after upload
    def test_balance_pending_after_upload(self, auth_headers, test_pdf_file):
        """deposit Verified + final proof uploaded + final Pending Review = 'Balance Pending'"""
        # Get a booking with verified deposit and no final payment proof
        response = requests.get(f"{BASE_URL}/api/admin/bookings", headers=auth_headers)
        bookings = response.json()
        
        test_booking = None
        for b in bookings:
            if b.get("payment_status") == "Verified" and b.get("final_payment_proof") is None:
                test_booking = b
                break
        
        if not test_booking:
            pytest.skip("No suitable booking found for Balance Pending test")
        
        booking_id = test_booking["id"]
        
        # First ensure final_payment_status is Pending Review
        requests.patch(
            f"{BASE_URL}/api/admin/bookings/{booking_id}",
            json={"final_payment_status": "Pending Review"},
            headers=auth_headers
        )
        
        # Upload final payment proof
        files = {"file": ("test_balance.pdf", test_pdf_file, "application/pdf")}
        upload_response = requests.post(
            f"{BASE_URL}/api/admin/bookings/{booking_id}/final-payment-proof",
            headers=auth_headers,
            files=files
        )
        assert upload_response.status_code == 200
        
        result = upload_response.json()
        assert result["overall_payment_status"] == "Balance Pending", \
            f"Expected 'Balance Pending' after uploading final proof, got {result['overall_payment_status']}"
        
        print(f"✓ overall_payment_status correctly shows 'Balance Pending' after final proof upload")

    # Test 9: Verify Paid in Full after final payment verification
    def test_paid_in_full_after_verification(self, auth_headers, test_pdf_file):
        """Test full flow: deposit verified → final proof uploaded → final verified = Paid in Full"""
        # Get a booking
        response = requests.get(f"{BASE_URL}/api/admin/bookings", headers=auth_headers)
        bookings = response.json()
        
        # Find or use first booking with verified deposit
        test_booking = None
        for b in bookings:
            if b.get("payment_status") == "Verified":
                test_booking = b
                break
        
        if not test_booking:
            test_booking = bookings[0]
            # Set deposit as verified
            requests.patch(
                f"{BASE_URL}/api/admin/bookings/{test_booking['id']}",
                json={"payment_status": "Verified"},
                headers=auth_headers
            )
        
        booking_id = test_booking["id"]
        
        # Upload final payment proof if not present
        if test_booking.get("final_payment_proof") is None:
            files = {"file": ("test_full.pdf", test_pdf_file, "application/pdf")}
            requests.post(
                f"{BASE_URL}/api/admin/bookings/{booking_id}/final-payment-proof",
                headers=auth_headers,
                files=files
            )
        
        # Set final_payment_status to Verified
        update_response = requests.patch(
            f"{BASE_URL}/api/admin/bookings/{booking_id}",
            json={"final_payment_status": "Verified"},
            headers=auth_headers
        )
        
        assert update_response.status_code == 200
        result = update_response.json()
        
        assert result["overall_payment_status"] == "Paid in Full", \
            f"Expected 'Paid in Full' after verifying final payment, got {result['overall_payment_status']}"
        
        print(f"✓ overall_payment_status correctly shows 'Paid in Full' after final payment verification")


class TestFinalPaymentProofRetrieval:
    """Tests for final payment proof document retrieval"""

    # Test 10: GET final payment proof document
    def test_get_final_payment_proof_document(self, auth_headers, test_pdf_file):
        """GET /api/admin/documents/{id}/final_payment_proof returns the uploaded file"""
        # First find a booking with final_payment_proof
        response = requests.get(f"{BASE_URL}/api/admin/bookings", headers=auth_headers)
        bookings = response.json()
        
        booking_with_proof = None
        for b in bookings:
            if b.get("final_payment_proof") is not None:
                booking_with_proof = b
                break
        
        if not booking_with_proof:
            # Upload one first
            booking_id = bookings[0]["id"]
            files = {"file": ("test_retrieve.pdf", test_pdf_file, "application/pdf")}
            requests.post(
                f"{BASE_URL}/api/admin/bookings/{booking_id}/final-payment-proof",
                headers=auth_headers,
                files=files
            )
            booking_with_proof = requests.get(
                f"{BASE_URL}/api/admin/bookings/{booking_id}",
                headers=auth_headers
            ).json()
        
        booking_id = booking_with_proof["id"]
        
        # Try to get the document
        doc_response = requests.get(
            f"{BASE_URL}/api/admin/documents/{booking_id}/final_payment_proof",
            headers=auth_headers
        )
        
        assert doc_response.status_code == 200, f"Failed to get final payment proof: {doc_response.text}"
        assert len(doc_response.content) > 0, "Document content should not be empty"
        
        print(f"✓ Successfully retrieved final_payment_proof document for booking {booking_id[:8]}...")
        print(f"  - Content length: {len(doc_response.content)} bytes")


class TestDashboardPaymentMetrics:
    """Tests for dashboard payment metrics"""

    # Test 11: Dashboard returns new payment metrics
    def test_dashboard_has_payment_metrics(self, auth_headers):
        """GET /api/admin/dashboard returns deposits_pending, deposits_verified, balance_pending, paid_in_full"""
        response = requests.get(f"{BASE_URL}/api/admin/dashboard", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get dashboard: {response.text}"
        
        data = response.json()
        assert "metrics" in data, "Dashboard should have metrics"
        
        metrics = data["metrics"]
        
        # Check all required payment metrics exist
        required_metrics = ["deposits_pending", "deposits_verified", "balance_pending", "paid_in_full"]
        for metric in required_metrics:
            assert metric in metrics, f"Dashboard metrics should include {metric}"
            assert isinstance(metrics[metric], int), f"{metric} should be an integer"
            assert metrics[metric] >= 0, f"{metric} should be non-negative"
        
        print("✓ Dashboard has all required payment metrics:")
        print(f"  - deposits_pending: {metrics['deposits_pending']}")
        print(f"  - deposits_verified: {metrics['deposits_verified']}")
        print(f"  - balance_pending: {metrics['balance_pending']}")
        print(f"  - paid_in_full: {metrics['paid_in_full']}")
        
        # Verify total count makes sense
        total_payment_states = (
            metrics['deposits_pending'] + 
            metrics['deposits_verified'] + 
            metrics['balance_pending'] + 
            metrics['paid_in_full']
        )
        
        # Get total bookings to compare
        bookings_response = requests.get(f"{BASE_URL}/api/admin/bookings", headers=auth_headers)
        total_bookings = len(bookings_response.json())
        
        assert total_payment_states == total_bookings, \
            f"Sum of payment states ({total_payment_states}) should equal total bookings ({total_bookings})"
        
        print(f"✓ Payment metrics sum ({total_payment_states}) matches total bookings ({total_bookings})")


class TestManualBookingWithFinalPayment:
    """Test manual booking creation with final_payment_status"""

    # Test 12: Manual booking accepts final_payment_status
    def test_create_manual_booking_with_final_payment_status(self, auth_headers):
        """POST /api/admin/bookings/manual creates booking with final_payment_status"""
        unique_id = uuid.uuid4().hex[:8]
        payload = {
            "program_id": "basic-6-day",
            "start_week": "2026-04-13",
            "locale": "en",
            "owner_full_name": f"TEST_TwoStage_{unique_id}",
            "owner_email": f"test_twostage_{unique_id}@example.com",
            "owner_phone": "+1234567890",
            "owner_address": "Test Address",
            "dog_name": f"TestDog_{unique_id}",
            "breed": "Test Breed",
            "sex": "Male",
            "weight": "25",
            "date_of_birth": "2023-01-01",
            "vaccination_status": "Up to date",
            "behavior_goals": "Basic training",
            "status": "Scheduled",
            "payment_status": "Verified",
            "final_payment_status": "Pending Review",
            "vaccination_certificate_status": "Verified",
            "eligibility_status": "Eligible"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/bookings/manual",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Failed to create manual booking: {response.text}"
        
        booking = response.json()
        assert booking["final_payment_status"] == "Pending Review", \
            f"final_payment_status should be 'Pending Review', got {booking['final_payment_status']}"
        assert booking["overall_payment_status"] == "Deposit Verified", \
            f"With deposit verified and no final proof, should be 'Deposit Verified', got {booking['overall_payment_status']}"
        
        print(f"✓ Created manual booking {booking['id'][:8]}... with correct payment fields")
        print(f"  - final_payment_status: {booking['final_payment_status']}")
        print(f"  - overall_payment_status: {booking['overall_payment_status']}")
        
        return booking["id"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
