"""
Test suite for Document Viewer feature - Admin Document Preview API
Tests the GET /api/admin/documents/{booking_id}/{document_type} endpoint
- Image preview (JPEG, PNG)
- PDF preview
- Unsupported file type handling
- Authentication requirements
- Error handling for missing documents and invalid IDs
"""
import pytest
import requests
import os
from PIL import Image
from io import BytesIO

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
ADMIN_EMAIL = "admin@pawstraining.com"
ADMIN_PASSWORD = os.environ.get("TEST_ADMIN_PASSWORD", "")


class TestDocumentViewerAPI:
    """Tests for the admin document viewer endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def _create_test_image_bytes(self, color="blue", size=(200, 200)):
        """Create a test image in memory"""
        img = Image.new("RGB", size, color=color)
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=90)
        buf.seek(0)
        return buf.read()
    
    def _create_test_pdf_bytes(self):
        """Create a minimal valid PDF in memory"""
        pdf_content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj
xref
0 4
0000000000 65535 f 
0000000009 00000 n 
0000000052 00000 n 
0000000101 00000 n 
trailer<</Size 4/Root 1 0 R>>
startxref
178
%%EOF"""
        return pdf_content
    
    def _get_booking_with_documents(self):
        """Find a booking that has at least one document"""
        bookings = requests.get(f"{BASE_URL}/api/admin/bookings", headers=self.headers)
        assert bookings.status_code == 200
        
        for booking in bookings.json():
            if booking.get("payment_proof") or booking.get("vaccination_certificate") or booking.get("final_payment_proof"):
                return booking
        
        pytest.skip("No bookings with documents found for testing")
    
    def _get_booking_without_documents(self):
        """Find a booking that has no documents"""
        bookings = requests.get(f"{BASE_URL}/api/admin/bookings", headers=self.headers)
        assert bookings.status_code == 200
        
        for booking in bookings.json():
            if not booking.get("payment_proof") and not booking.get("vaccination_certificate") and not booking.get("final_payment_proof"):
                return booking
        
        pytest.skip("No bookings without documents found for testing")
    
    # Document type validation tests
    def test_valid_document_types(self):
        """Test that only valid document types are accepted"""
        booking = self._get_booking_with_documents()
        booking_id = booking["id"]
        
        valid_types = ["payment_proof", "vaccination_certificate", "final_payment_proof"]
        for doc_type in valid_types:
            response = requests.get(
                f"{BASE_URL}/api/admin/documents/{booking_id}/{doc_type}",
                headers=self.headers
            )
            # Should return 200 if document exists, 404 if document not uploaded
            assert response.status_code in [200, 404], f"Unexpected status for {doc_type}: {response.status_code}"
        print(f"✓ Valid document types accepted for booking {booking_id}")
    
    def test_invalid_document_type_returns_400(self):
        """Test that invalid document type returns 400 Bad Request"""
        booking = self._get_booking_with_documents()
        booking_id = booking["id"]
        
        invalid_types = ["invalid_type", "random", "payment", "vaccine", ""]
        for doc_type in invalid_types:
            response = requests.get(
                f"{BASE_URL}/api/admin/documents/{booking_id}/{doc_type}",
                headers=self.headers
            )
            # Empty string might return 404 (URL routing), others should be 400
            if doc_type:
                assert response.status_code == 400, f"Expected 400 for '{doc_type}', got: {response.status_code}"
        print("✓ Invalid document types correctly rejected with 400")
    
    # Authentication tests
    def test_requires_authentication(self):
        """Test that endpoint requires valid auth token"""
        booking = self._get_booking_with_documents()
        booking_id = booking["id"]
        
        # No auth header
        response = requests.get(f"{BASE_URL}/api/admin/documents/{booking_id}/payment_proof")
        assert response.status_code == 401, f"Expected 401 without auth, got: {response.status_code}"
        print("✓ Endpoint correctly requires authentication")
    
    def test_invalid_token_rejected(self):
        """Test that invalid tokens are rejected"""
        booking = self._get_booking_with_documents()
        booking_id = booking["id"]
        
        invalid_headers = {"Authorization": "Bearer invalid-token-12345"}
        response = requests.get(
            f"{BASE_URL}/api/admin/documents/{booking_id}/payment_proof",
            headers=invalid_headers
        )
        assert response.status_code == 401, f"Expected 401 for invalid token, got: {response.status_code}"
        print("✓ Invalid token correctly rejected with 401")
    
    # Booking validation tests
    def test_invalid_booking_id_returns_404(self):
        """Test that non-existent booking ID returns 404"""
        response = requests.get(
            f"{BASE_URL}/api/admin/documents/non-existent-booking-id-123/payment_proof",
            headers=self.headers
        )
        assert response.status_code == 404, f"Expected 404 for invalid booking, got: {response.status_code}"
        print("✓ Non-existent booking correctly returns 404")
    
    def test_missing_document_returns_404(self):
        """Test that requesting a document that wasn't uploaded returns 404"""
        # Find booking without a specific document
        bookings = requests.get(f"{BASE_URL}/api/admin/bookings", headers=self.headers)
        
        for booking in bookings.json():
            # Check for booking without payment_proof
            if not booking.get("payment_proof"):
                response = requests.get(
                    f"{BASE_URL}/api/admin/documents/{booking['id']}/payment_proof",
                    headers=self.headers
                )
                assert response.status_code == 404, f"Expected 404 for missing document, got: {response.status_code}"
                print(f"✓ Missing document correctly returns 404 for booking {booking['id']}")
                return
        
        pytest.skip("No booking found without payment_proof document")
    
    # Content-Type tests
    def test_jpeg_returns_correct_content_type(self):
        """Test that JPEG images return image/jpeg content-type"""
        # Find a booking with JPEG payment proof
        bookings = requests.get(f"{BASE_URL}/api/admin/bookings", headers=self.headers)
        
        for booking in bookings.json():
            payment_proof = booking.get("payment_proof", {})
            if payment_proof and payment_proof.get("content_type") == "image/jpeg":
                response = requests.get(
                    f"{BASE_URL}/api/admin/documents/{booking['id']}/payment_proof",
                    headers=self.headers
                )
                assert response.status_code == 200
                content_type = response.headers.get("content-type", "")
                assert "image/jpeg" in content_type.lower(), f"Expected image/jpeg, got: {content_type}"
                print(f"✓ JPEG document returns correct content-type: {content_type}")
                return
        
        pytest.skip("No JPEG documents found for testing")
    
    def test_pdf_returns_correct_content_type(self):
        """Test that PDFs return application/pdf content-type"""
        # Find a booking with PDF document
        bookings = requests.get(f"{BASE_URL}/api/admin/bookings", headers=self.headers)
        
        for booking in bookings.json():
            payment_proof = booking.get("payment_proof", {})
            if payment_proof and payment_proof.get("content_type") == "application/pdf":
                response = requests.get(
                    f"{BASE_URL}/api/admin/documents/{booking['id']}/payment_proof",
                    headers=self.headers
                )
                assert response.status_code == 200
                content_type = response.headers.get("content-type", "")
                assert "application/pdf" in content_type.lower(), f"Expected application/pdf, got: {content_type}"
                print(f"✓ PDF document returns correct content-type: {content_type}")
                return
        
        pytest.skip("No PDF documents found for testing")
    
    def test_png_returns_correct_content_type(self):
        """Test that PNG images return image/png content-type"""
        bookings = requests.get(f"{BASE_URL}/api/admin/bookings", headers=self.headers)
        
        for booking in bookings.json():
            for doc_field in ["payment_proof", "vaccination_certificate", "final_payment_proof"]:
                doc = booking.get(doc_field, {})
                if doc and doc.get("content_type") == "image/png":
                    response = requests.get(
                        f"{BASE_URL}/api/admin/documents/{booking['id']}/{doc_field}",
                        headers=self.headers
                    )
                    assert response.status_code == 200
                    content_type = response.headers.get("content-type", "")
                    assert "image/png" in content_type.lower(), f"Expected image/png, got: {content_type}"
                    print(f"✓ PNG document returns correct content-type: {content_type}")
                    return
        
        pytest.skip("No PNG documents found for testing")
    
    # Response structure tests
    def test_document_response_has_filename_header(self):
        """Test that document response includes filename in Content-Disposition"""
        booking = self._get_booking_with_documents()
        
        for doc_type in ["payment_proof", "vaccination_certificate", "final_payment_proof"]:
            if booking.get(doc_type):
                response = requests.get(
                    f"{BASE_URL}/api/admin/documents/{booking['id']}/{doc_type}",
                    headers=self.headers
                )
                if response.status_code == 200:
                    disposition = response.headers.get("content-disposition", "")
                    assert "filename" in disposition.lower(), f"Missing filename in Content-Disposition: {disposition}"
                    print(f"✓ Content-Disposition header includes filename for {doc_type}")
                    return
        
        pytest.skip("No accessible documents found for testing")
    
    def test_document_response_has_content(self):
        """Test that document response has actual content"""
        booking = self._get_booking_with_documents()
        
        for doc_type in ["payment_proof", "vaccination_certificate", "final_payment_proof"]:
            if booking.get(doc_type):
                response = requests.get(
                    f"{BASE_URL}/api/admin/documents/{booking['id']}/{doc_type}",
                    headers=self.headers
                )
                if response.status_code == 200:
                    content_length = len(response.content)
                    assert content_length > 0, "Document response has no content"
                    print(f"✓ Document response has content ({content_length} bytes)")
                    return
        
        pytest.skip("No accessible documents found for testing")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
