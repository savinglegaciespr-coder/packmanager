"""
Test suite for Email Notification System in PAWS Training App
Tests:
- Email sending on new booking submission (2 emails: admin + client)
- Email sending on booking approval (1 email to client)
- Email sending on booking rejection (1 email to client)
- Admin settings endpoint returns correct SMTP configuration
- Email logs have proper delivery_status values
"""

import os
import pytest
import requests
import time
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@pawstraining.com"
ADMIN_PASSWORD = os.environ.get("TEST_ADMIN_PASSWORD", "")

# Test data
TEST_CLIENT_EMAIL = "Pawstraningpr@gmail.com"  # Using same email for testing
TEST_PROGRAM_ID = "basic-6-day"
TEST_START_WEEK = "2026-05-04"  # Future Monday


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for admin user"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Authentication failed - skipping authenticated tests")


@pytest.fixture(scope="module")
def admin_client(auth_token):
    """Session with auth header"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


class TestHealthCheck:
    """Basic API health check - run first"""
    
    def test_api_root(self):
        """Test API root endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "PAWS TRAINING" in data["message"]
        print(f"✓ API root accessible: {data['message']}")


class TestAdminSettings:
    """Test admin settings endpoint for SMTP configuration"""
    
    def test_admin_settings_returns_smtp_config(self, admin_client):
        """GET /api/admin/settings should return SMTP configuration"""
        response = admin_client.get(f"{BASE_URL}/api/admin/settings")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        
        # Verify SMTP fields are present
        assert "smtp_host" in data, "smtp_host missing from settings"
        assert "smtp_port" in data, "smtp_port missing from settings"
        assert "smtp_username" in data, "smtp_username missing from settings"
        assert "smtp_password_configured" in data, "smtp_password_configured missing from settings"
        assert "email_mode" in data, "email_mode missing from settings"
        
        # Verify SMTP is properly configured
        assert data["smtp_host"] == "smtp.gmail.com", f"Expected smtp.gmail.com, got {data['smtp_host']}"
        assert data["smtp_port"] == 587, f"Expected port 587, got {data['smtp_port']}"
        assert data["smtp_password_configured"] == True, "SMTP password should be configured"
        assert data["email_mode"] == "smtp", f"Expected email_mode='smtp', got {data['email_mode']}"
        assert data["smtp_username"] == "Pawstraningpr@gmail.com", f"Unexpected username: {data['smtp_username']}"
        
        print(f"✓ Admin settings returned correct SMTP config: host={data['smtp_host']}, port={data['smtp_port']}, mode={data['email_mode']}")


class TestEmailLogsEndpoint:
    """Test email logs endpoint"""
    
    def test_email_logs_have_delivery_status(self, admin_client):
        """GET /api/admin/email-logs should not have entries with delivery_status=null"""
        response = admin_client.get(f"{BASE_URL}/api/admin/email-logs")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Email logs should be a list"
        
        # Check that no logs have delivery_status=null
        null_status_count = 0
        for log in data:
            if log.get("delivery_status") is None:
                null_status_count += 1
                print(f"  Found log with null delivery_status: {log.get('id')}")
        
        assert null_status_count == 0, f"Found {null_status_count} email logs with delivery_status=null"
        
        print(f"✓ Email logs endpoint returned {len(data)} logs, all have valid delivery_status")
        
        # Print recent logs for debugging
        for log in data[:5]:
            print(f"  - {log.get('recipient')}: {log.get('subject')} [status={log.get('delivery_status')}, mode={log.get('mode')}]")


class TestBookingEmailNotifications:
    """Test email notifications for booking lifecycle"""
    
    @pytest.fixture
    def create_test_pdf(self, tmp_path):
        """Create a dummy PDF file for testing"""
        pdf_content = b"%PDF-1.4\n%test dummy pdf content\n"
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(pdf_content)
        return str(pdf_path)
    
    def test_new_booking_sends_two_emails(self, admin_client, tmp_path):
        """POST /api/public/bookings should trigger 2 email logs (admin + client)"""
        
        # Get initial email log count
        initial_logs_response = admin_client.get(f"{BASE_URL}/api/admin/email-logs")
        initial_logs = initial_logs_response.json()
        initial_count = len(initial_logs)
        
        # Create dummy PDF files
        pdf_content = b"%PDF-1.4\n%test dummy pdf content for testing\n"
        payment_pdf = tmp_path / "payment_proof.pdf"
        vaccination_pdf = tmp_path / "vaccination_cert.pdf"
        payment_pdf.write_bytes(pdf_content)
        vaccination_pdf.write_bytes(pdf_content)
        
        # Create a unique test booking
        unique_id = uuid.uuid4().hex[:8]
        
        # Submit booking using multipart form data
        with open(payment_pdf, 'rb') as payment_file, open(vaccination_pdf, 'rb') as vac_file:
            files = {
                'payment_proof': ('payment_proof.pdf', payment_file, 'application/pdf'),
                'vaccination_certificate': ('vaccination_cert.pdf', vac_file, 'application/pdf')
            }
            form_data = {
                'program_id': TEST_PROGRAM_ID,
                'start_week': TEST_START_WEEK,
                'locale': 'es',
                'owner_full_name': f'TEST_EmailTest_{unique_id}',
                'owner_email': TEST_CLIENT_EMAIL,
                'owner_phone': '+34 600 111 222',
                'owner_address': 'Test Address, Madrid',
                'dog_name': f'TestDog_{unique_id}',
                'breed': 'Labrador',
                'age': '2 years',
                'sex': 'Male',
                'weight': '25 kg',
                'date_of_birth': '2024-01-15',
                'vaccination_status': 'Up to date',
                'allergies': 'None',
                'behavior_goals': 'Basic obedience training'
            }
            
            # Use requests without json content-type for multipart
            response = requests.post(
                f"{BASE_URL}/api/public/bookings",
                data=form_data,
                files=files
            )
        
        assert response.status_code == 200, f"Booking creation failed: {response.text}"
        booking_data = response.json()
        booking_id = booking_data.get("booking_id")
        assert booking_id, "No booking_id returned"
        
        print(f"✓ Created test booking: {booking_id}")
        
        # Wait for async email operations
        time.sleep(3)
        
        # Get updated email logs
        updated_logs_response = admin_client.get(f"{BASE_URL}/api/admin/email-logs")
        updated_logs = updated_logs_response.json()
        new_count = len(updated_logs)
        
        # Find emails for this booking
        booking_emails = [log for log in updated_logs if log.get("booking_id") == booking_id]
        
        assert len(booking_emails) >= 2, f"Expected at least 2 emails for new booking, got {len(booking_emails)}"
        
        # Verify we have both admin and client emails
        audiences = [log.get("audience") for log in booking_emails]
        assert "admin" in audiences, "Missing admin notification email"
        assert "client" in audiences, "Missing client notification email"
        
        # Verify emails have mode='smtp' and delivery_status='sent'
        for email in booking_emails:
            assert email.get("mode") == "smtp", f"Expected mode='smtp', got {email.get('mode')}"
            assert email.get("delivery_status") == "sent", f"Expected delivery_status='sent', got {email.get('delivery_status')}"
            print(f"  ✓ Email to {email.get('audience')}: {email.get('subject')} [status={email.get('delivery_status')}]")
        
        print(f"✓ New booking triggered {len(booking_emails)} emails (admin + client) with SMTP delivery")
        
        return booking_id
    
    def test_booking_approval_sends_email(self, admin_client, tmp_path):
        """PATCH /api/admin/bookings/{id} with status=Approved should trigger 1 email"""
        
        # First create a booking to approve
        pdf_content = b"%PDF-1.4\n%test dummy pdf content\n"
        payment_pdf = tmp_path / "payment_proof.pdf"
        vaccination_pdf = tmp_path / "vaccination_cert.pdf"
        payment_pdf.write_bytes(pdf_content)
        vaccination_pdf.write_bytes(pdf_content)
        
        unique_id = uuid.uuid4().hex[:8]
        
        with open(payment_pdf, 'rb') as payment_file, open(vaccination_pdf, 'rb') as vac_file:
            files = {
                'payment_proof': ('payment_proof.pdf', payment_file, 'application/pdf'),
                'vaccination_certificate': ('vaccination_cert.pdf', vac_file, 'application/pdf')
            }
            form_data = {
                'program_id': TEST_PROGRAM_ID,
                'start_week': TEST_START_WEEK,
                'locale': 'en',  # English locale for approval test
                'owner_full_name': f'TEST_ApprovalTest_{unique_id}',
                'owner_email': TEST_CLIENT_EMAIL,
                'owner_phone': '+34 600 333 444',
                'owner_address': 'Test Address, Barcelona',
                'dog_name': f'ApprovalDog_{unique_id}',
                'breed': 'Golden Retriever',
                'sex': 'Female',
                'weight': '30 kg',
                'date_of_birth': '2023-06-15',
                'vaccination_status': 'Up to date',
                'allergies': '',
                'behavior_goals': 'Advanced obedience'
            }
            
            response = requests.post(
                f"{BASE_URL}/api/public/bookings",
                data=form_data,
                files=files
            )
        
        assert response.status_code == 200, f"Booking creation failed: {response.text}"
        booking_id = response.json().get("booking_id")
        
        # Wait for initial emails
        time.sleep(2)
        
        # Get email count before approval
        logs_before = admin_client.get(f"{BASE_URL}/api/admin/email-logs").json()
        booking_emails_before = [log for log in logs_before if log.get("booking_id") == booking_id]
        
        # First verify document statuses and eligibility before approving
        # Step 1: Verify payment
        response = admin_client.patch(
            f"{BASE_URL}/api/admin/bookings/{booking_id}",
            json={"payment_status": "Verified"}
        )
        assert response.status_code == 200, f"Payment verification failed: {response.text}"
        
        # Step 2: Verify vaccination certificate
        response = admin_client.patch(
            f"{BASE_URL}/api/admin/bookings/{booking_id}",
            json={"vaccination_certificate_status": "Verified"}
        )
        assert response.status_code == 200, f"Vaccination verification failed: {response.text}"
        
        # Step 3: Set eligibility
        response = admin_client.patch(
            f"{BASE_URL}/api/admin/bookings/{booking_id}",
            json={"eligibility_status": "Eligible"}
        )
        assert response.status_code == 200, f"Eligibility update failed: {response.text}"
        
        # Step 4: Approve booking
        response = admin_client.patch(
            f"{BASE_URL}/api/admin/bookings/{booking_id}",
            json={"status": "Approved"}
        )
        assert response.status_code == 200, f"Booking approval failed: {response.text}"
        
        # Wait for approval email
        time.sleep(3)
        
        # Get email logs after approval
        logs_after = admin_client.get(f"{BASE_URL}/api/admin/email-logs").json()
        booking_emails_after = [log for log in logs_after if log.get("booking_id") == booking_id]
        
        # Should have at least 3 emails now (2 submission + 1 approval)
        new_email_count = len(booking_emails_after) - len(booking_emails_before)
        
        assert new_email_count >= 1, f"Expected at least 1 new email after approval, got {new_email_count}"
        
        # Find the approval email
        approval_emails = [
            log for log in booking_emails_after 
            if "approved" in log.get("subject", "").lower() or "aprobada" in log.get("subject", "").lower()
        ]
        
        assert len(approval_emails) >= 1, "Approval email not found"
        
        approval_email = approval_emails[0]
        assert approval_email.get("mode") == "smtp", f"Expected mode='smtp', got {approval_email.get('mode')}"
        assert approval_email.get("delivery_status") == "sent", f"Expected delivery_status='sent', got {approval_email.get('delivery_status')}"
        assert approval_email.get("audience") == "client", f"Approval email should be to client"
        
        print(f"✓ Booking approval triggered email: {approval_email.get('subject')} [status={approval_email.get('delivery_status')}]")
    
    def test_booking_rejection_sends_email(self, admin_client, tmp_path):
        """PATCH /api/admin/bookings/{id} with status=Rejected should trigger 1 email"""
        
        # First create a booking to reject
        pdf_content = b"%PDF-1.4\n%test dummy pdf content\n"
        payment_pdf = tmp_path / "payment_proof.pdf"
        vaccination_pdf = tmp_path / "vaccination_cert.pdf"
        payment_pdf.write_bytes(pdf_content)
        vaccination_pdf.write_bytes(pdf_content)
        
        unique_id = uuid.uuid4().hex[:8]
        
        with open(payment_pdf, 'rb') as payment_file, open(vaccination_pdf, 'rb') as vac_file:
            files = {
                'payment_proof': ('payment_proof.pdf', payment_file, 'application/pdf'),
                'vaccination_certificate': ('vaccination_cert.pdf', vac_file, 'application/pdf')
            }
            form_data = {
                'program_id': TEST_PROGRAM_ID,
                'start_week': TEST_START_WEEK,
                'locale': 'es',
                'owner_full_name': f'TEST_RejectionTest_{unique_id}',
                'owner_email': TEST_CLIENT_EMAIL,
                'owner_phone': '+34 600 555 666',
                'owner_address': 'Test Address, Valencia',
                'dog_name': f'RejectDog_{unique_id}',
                'breed': 'Beagle',
                'sex': 'Male',
                'weight': '15 kg',
                'date_of_birth': '2022-03-20',
                'vaccination_status': 'Up to date',
                'allergies': '',
                'behavior_goals': 'Behavioral correction'
            }
            
            response = requests.post(
                f"{BASE_URL}/api/public/bookings",
                data=form_data,
                files=files
            )
        
        assert response.status_code == 200, f"Booking creation failed: {response.text}"
        booking_id = response.json().get("booking_id")
        
        # Wait for initial emails
        time.sleep(2)
        
        # Get email count before rejection
        logs_before = admin_client.get(f"{BASE_URL}/api/admin/email-logs").json()
        booking_emails_before = [log for log in logs_before if log.get("booking_id") == booking_id]
        
        # Reject the booking with a reason
        response = admin_client.patch(
            f"{BASE_URL}/api/admin/bookings/{booking_id}",
            json={
                "status": "Rejected",
                "rejection_reason": "Documentación incompleta para el test automatizado."
            }
        )
        assert response.status_code == 200, f"Booking rejection failed: {response.text}"
        
        # Wait for rejection email
        time.sleep(3)
        
        # Get email logs after rejection
        logs_after = admin_client.get(f"{BASE_URL}/api/admin/email-logs").json()
        booking_emails_after = [log for log in logs_after if log.get("booking_id") == booking_id]
        
        # Should have at least 3 emails now (2 submission + 1 rejection)
        new_email_count = len(booking_emails_after) - len(booking_emails_before)
        
        assert new_email_count >= 1, f"Expected at least 1 new email after rejection, got {new_email_count}"
        
        # Find the rejection email
        rejection_emails = [
            log for log in booking_emails_after 
            if "update" in log.get("subject", "").lower() or "actualización" in log.get("subject", "").lower()
        ]
        
        assert len(rejection_emails) >= 1, "Rejection email not found"
        
        rejection_email = rejection_emails[0]
        assert rejection_email.get("mode") == "smtp", f"Expected mode='smtp', got {rejection_email.get('mode')}"
        assert rejection_email.get("delivery_status") == "sent", f"Expected delivery_status='sent', got {rejection_email.get('delivery_status')}"
        assert rejection_email.get("audience") == "client", f"Rejection email should be to client"
        
        print(f"✓ Booking rejection triggered email: {rejection_email.get('subject')} [status={rejection_email.get('delivery_status')}]")


class TestAdminDashboard:
    """Test admin dashboard loads correctly"""
    
    def test_admin_dashboard_loads(self, admin_client):
        """GET /api/admin/dashboard should return dashboard data"""
        response = admin_client.get(f"{BASE_URL}/api/admin/dashboard")
        assert response.status_code == 200, f"Dashboard failed: {response.text}"
        
        data = response.json()
        
        # Verify dashboard structure
        assert "metrics" in data, "Missing metrics in dashboard"
        assert "weekly_occupancy" in data, "Missing weekly_occupancy in dashboard"
        assert "charts" in data, "Missing charts in dashboard"
        assert "recent_email_logs" in data, "Missing recent_email_logs in dashboard"
        
        # Verify metrics structure
        metrics = data["metrics"]
        expected_metric_keys = [
            "nearly_full_weeks", "full_weeks", "dogs_pending_intake", 
            "dogs_in_training", "dogs_delivered", "pending_payments",
            "confirmed_payments", "confirmed_revenue", "pending_revenue"
        ]
        for key in expected_metric_keys:
            assert key in metrics, f"Missing metric: {key}"
        
        print(f"✓ Admin dashboard loaded successfully with {len(data['weekly_occupancy'])} weeks")
        print(f"  Metrics: {metrics['dogs_in_training']} in training, {metrics['pending_payments']} pending payments")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
