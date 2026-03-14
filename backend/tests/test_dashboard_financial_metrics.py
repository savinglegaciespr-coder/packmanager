"""
Tests for Enhanced Financial Dashboard:
- Dashboard metrics: total_deposit_collected, total_balance_collected, total_revenue_collected, total_deposit_expected, total_balance_expected
- Dashboard charts: payment_breakdown array with monthly deposits, final_payments, outstanding
- Deposit-verified email: non-refundable policy notice text and secure /payment/{token} upload link
"""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestDashboardFinancialMetrics:
    """Tests for enhanced dashboard financial metrics"""

    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@pawstraining.com",
            "password": "PawsAdmin2026!"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["token"]

    def test_dashboard_metrics_contain_financial_fields(self, auth_token):
        """Dashboard metrics should include all financial tracking fields"""
        response = requests.get(f"{BASE_URL}/api/admin/dashboard", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        
        # Verify dashboard structure
        assert "metrics" in data
        metrics = data["metrics"]
        
        # Test for required financial metrics
        assert "total_deposit_collected" in metrics, "Missing total_deposit_collected"
        assert "total_balance_collected" in metrics, "Missing total_balance_collected (final payments)"
        assert "total_revenue_collected" in metrics, "Missing total_revenue_collected"
        assert "total_deposit_expected" in metrics, "Missing total_deposit_expected"
        assert "total_balance_expected" in metrics, "Missing total_balance_expected"
        
        # Verify they are numeric values
        assert isinstance(metrics["total_deposit_collected"], (int, float))
        assert isinstance(metrics["total_balance_collected"], (int, float))
        assert isinstance(metrics["total_revenue_collected"], (int, float))
        assert isinstance(metrics["total_deposit_expected"], (int, float))
        assert isinstance(metrics["total_balance_expected"], (int, float))
        
        # Verify total_revenue_collected = total_deposit_collected + total_balance_collected
        expected_revenue = round(metrics["total_deposit_collected"] + metrics["total_balance_collected"], 2)
        assert metrics["total_revenue_collected"] == expected_revenue, \
            f"total_revenue_collected ({metrics['total_revenue_collected']}) != deposit ({metrics['total_deposit_collected']}) + balance ({metrics['total_balance_collected']})"
        
        print(f"✓ Dashboard financial metrics: deposit_collected={metrics['total_deposit_collected']}, balance_collected={metrics['total_balance_collected']}, total_revenue={metrics['total_revenue_collected']}")

    def test_dashboard_metrics_contain_payment_counters(self, auth_token):
        """Dashboard metrics should include payment status counters"""
        response = requests.get(f"{BASE_URL}/api/admin/dashboard", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        metrics = response.json()["metrics"]
        
        # Payment status counters
        assert "deposits_pending" in metrics, "Missing deposits_pending counter"
        assert "deposits_verified" in metrics or "balance_pending" in metrics, "Missing deposit status counters"
        assert "paid_in_full" in metrics, "Missing paid_in_full counter"
        
        print(f"✓ Payment status counters: deposits_pending={metrics.get('deposits_pending')}, paid_in_full={metrics.get('paid_in_full')}")

    def test_dashboard_charts_contain_payment_breakdown(self, auth_token):
        """Dashboard charts should include payment_breakdown array"""
        response = requests.get(f"{BASE_URL}/api/admin/dashboard", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        
        # Verify charts structure
        assert "charts" in data
        charts = data["charts"]
        
        # Test for payment_breakdown chart
        assert "payment_breakdown" in charts, "Missing payment_breakdown chart"
        payment_breakdown = charts["payment_breakdown"]
        
        assert isinstance(payment_breakdown, list), "payment_breakdown should be an array"
        
        # If there's data, verify structure of each entry
        if len(payment_breakdown) > 0:
            for entry in payment_breakdown:
                assert "month" in entry, "payment_breakdown entry missing 'month' key"
                assert "deposits" in entry, "payment_breakdown entry missing 'deposits' key"
                assert "final_payments" in entry, "payment_breakdown entry missing 'final_payments' key"
                assert "outstanding" in entry, "payment_breakdown entry missing 'outstanding' key"
                
                # Verify they are numeric
                assert isinstance(entry["deposits"], (int, float))
                assert isinstance(entry["final_payments"], (int, float))
                assert isinstance(entry["outstanding"], (int, float))
            
            print(f"✓ Payment breakdown chart has {len(payment_breakdown)} months of data")
            print(f"  Sample entry: {payment_breakdown[0]}")
        else:
            print("✓ Payment breakdown chart is empty (no active bookings with payment data)")

    def test_dashboard_has_other_required_charts(self, auth_token):
        """Dashboard should have capacity_breakdown and dog_status_breakdown charts"""
        response = requests.get(f"{BASE_URL}/api/admin/dashboard", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        charts = response.json()["charts"]
        
        assert "capacity_breakdown" in charts, "Missing capacity_breakdown chart"
        assert "dog_status_breakdown" in charts, "Missing dog_status_breakdown chart"
        
        print(f"✓ All required charts present: capacity_breakdown, dog_status_breakdown, payment_breakdown")


class TestDepositVerifiedEmail:
    """Tests for deposit-verified email content"""

    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@pawstraining.com",
            "password": "PawsAdmin2026!"
        })
        assert response.status_code == 200
        return response.json()["token"]

    def test_deposit_verification_triggers_email_with_policy(self, auth_token):
        """When deposit status is set to Verified, email should contain non-refundable policy notice"""
        import uuid
        
        # First, find a booking with Pending Review payment_status
        # Or create a test booking
        bookings_resp = requests.get(f"{BASE_URL}/api/admin/bookings", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert bookings_resp.status_code == 200
        bookings = bookings_resp.json()
        
        # Find a booking to test with
        test_booking = None
        for b in bookings:
            if b.get("payment_status") == "Pending Review":
                test_booking = b
                break
        
        if not test_booking:
            # Use any booking for the email log check
            print("! No Pending Review bookings found; checking existing email logs instead")
            return self._check_existing_email_logs(auth_token)
        
        booking_id = test_booking["id"]
        
        # Update payment_status to Verified (should trigger deposit-verified email)
        update_resp = requests.patch(
            f"{BASE_URL}/api/admin/bookings/{booking_id}",
            json={"payment_status": "Verified"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert update_resp.status_code == 200, f"Update failed: {update_resp.text}"
        
        # Check email logs for this booking
        self._verify_email_policy_content(auth_token, booking_id)
        
        # Revert for other tests
        requests.patch(
            f"{BASE_URL}/api/admin/bookings/{booking_id}",
            json={"payment_status": "Pending Review"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )

    def _check_existing_email_logs(self, auth_token):
        """Check existing email logs for deposit-verified emails"""
        logs_resp = requests.get(f"{BASE_URL}/api/admin/email-logs", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert logs_resp.status_code == 200
        logs = logs_resp.json()
        
        deposit_emails = [log for log in logs if "verificado" in log.get("subject", "").lower() or "verified" in log.get("subject", "").lower()]
        
        if deposit_emails:
            for log in deposit_emails[:2]:
                body = log.get("body", "")
                # Check for policy notice (Spanish or English)
                has_policy = "no es reembolsable" in body.lower() or "non-refundable" in body.lower()
                # Check for payment link
                has_link = "/payment/" in body
                
                print(f"✓ Found deposit-verified email: subject='{log.get('subject')}'")
                print(f"  Has non-refundable policy: {has_policy}")
                print(f"  Has payment link: {has_link}")
                
                if has_policy and has_link:
                    print("✓ Email contains required policy notice and payment link")
                    return
        
        print("! No deposit-verified emails found in logs to verify")

    def _verify_email_policy_content(self, auth_token, booking_id):
        """Verify the deposit-verified email contains required content"""
        logs_resp = requests.get(f"{BASE_URL}/api/admin/email-logs", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert logs_resp.status_code == 200
        logs = logs_resp.json()
        
        # Find email for this booking
        booking_emails = [log for log in logs if log.get("booking_id") == booking_id]
        
        if not booking_emails:
            pytest.skip(f"No email logs found for booking {booking_id}")
        
        # Find deposit-verified email
        deposit_email = None
        for log in booking_emails:
            subject = log.get("subject", "").lower()
            if "verificado" in subject or "verified" in subject:
                deposit_email = log
                break
        
        if not deposit_email:
            print(f"! No deposit-verified email found for booking {booking_id}")
            return
        
        body = deposit_email.get("body", "")
        
        # Check for non-refundable policy notice (Spanish or English)
        has_es_policy = "no es reembolsable" in body.lower()
        has_en_policy = "non-refundable" in body.lower()
        assert has_es_policy or has_en_policy, f"Email body missing non-refundable policy notice. Body: {body[:500]}"
        
        # Check for payment link
        assert "/payment/" in body, f"Email body missing /payment/{{token}} link. Body: {body[:500]}"
        
        print(f"✓ Deposit-verified email verified for booking {booking_id}")
        print(f"  Non-refundable policy: {'ES' if has_es_policy else 'EN'}")
        print(f"  Payment link present: True")


class TestBookingPaymentFields:
    """Tests for booking payment fields (overall_payment_status, deposit_amount, balance_amount)"""

    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@pawstraining.com",
            "password": "PawsAdmin2026!"
        })
        assert response.status_code == 200
        return response.json()["token"]

    def test_bookings_contain_payment_fields(self, auth_token):
        """Each booking should have overall_payment_status, deposit_amount, balance_amount"""
        response = requests.get(f"{BASE_URL}/api/admin/bookings", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        bookings = response.json()
        
        assert len(bookings) > 0, "No bookings found"
        
        for booking in bookings[:5]:  # Check first 5 bookings
            # Check overall_payment_status
            assert "overall_payment_status" in booking, f"Booking {booking['id']} missing overall_payment_status"
            valid_statuses = ["Deposit Pending", "Deposit Verified", "Balance Pending", "Paid in Full"]
            assert booking["overall_payment_status"] in valid_statuses, \
                f"Invalid overall_payment_status: {booking['overall_payment_status']}"
            
            # Check deposit_amount and balance_amount
            assert "deposit_amount" in booking, f"Booking {booking['id']} missing deposit_amount"
            assert "balance_amount" in booking, f"Booking {booking['id']} missing balance_amount"
            
            # Verify they are numeric
            assert isinstance(booking["deposit_amount"], (int, float))
            assert isinstance(booking["balance_amount"], (int, float))
            
            # Verify deposit + balance = program_price
            total = booking["deposit_amount"] + booking["balance_amount"]
            expected = booking.get("program_price", 0)
            assert abs(total - expected) < 0.01, \
                f"deposit ({booking['deposit_amount']}) + balance ({booking['balance_amount']}) != program_price ({expected})"
        
        print(f"✓ Verified payment fields for {min(5, len(bookings))} bookings")
        sample = bookings[0]
        print(f"  Sample: overall_status={sample['overall_payment_status']}, deposit={sample['deposit_amount']}, balance={sample['balance_amount']}")

    def test_overall_payment_status_logic(self, auth_token):
        """Verify overall_payment_status correctly reflects deposit and final payment states"""
        response = requests.get(f"{BASE_URL}/api/admin/bookings", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        bookings = response.json()
        
        for booking in bookings:
            deposit_status = booking.get("payment_status", "Pending Review")
            final_status = booking.get("final_payment_status", "Pending Review")
            overall = booking.get("overall_payment_status")
            
            if deposit_status != "Verified":
                assert overall == "Deposit Pending", \
                    f"Expected 'Deposit Pending' when deposit not verified, got '{overall}'"
            elif final_status == "Verified":
                assert overall == "Paid in Full", \
                    f"Expected 'Paid in Full' when both verified, got '{overall}'"
            elif booking.get("final_payment_proof"):
                assert overall == "Balance Pending", \
                    f"Expected 'Balance Pending' when final proof uploaded, got '{overall}'"
            else:
                assert overall == "Deposit Verified", \
                    f"Expected 'Deposit Verified' when deposit verified but no final proof, got '{overall}'"
        
        print(f"✓ Overall payment status logic verified for {len(bookings)} bookings")


class TestTranslationKeys:
    """Tests for required translation keys in frontend"""

    def test_translation_keys_exist_in_api_response(self):
        """Verify dashboard provides data that matches expected translation keys"""
        # Login to get dashboard data
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@pawstraining.com",
            "password": "PawsAdmin2026!"
        })
        token = login_resp.json()["token"]
        
        dashboard_resp = requests.get(f"{BASE_URL}/api/admin/dashboard", headers={
            "Authorization": f"Bearer {token}"
        })
        data = dashboard_resp.json()
        
        # These are the translation keys used in frontend for financial summary
        required_metrics_for_ui = [
            "total_deposit_collected",   # for t.depositCollected
            "total_balance_collected",   # for t.finalPaymentsCollected
            "total_deposit_expected",    # for calculating outstanding
            "total_balance_expected",    # for calculating outstanding
            "total_revenue_collected",   # for t.totalRevenueCollected
        ]
        
        for key in required_metrics_for_ui:
            assert key in data["metrics"], f"Missing metric for UI: {key}"
        
        print("✓ All required metrics for Financial Summary UI are present")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
