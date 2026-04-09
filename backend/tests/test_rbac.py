"""
RBAC (Role-Based Access Control) Tests for PAWS TRAINING
Tests the 3-role system: superadmin, admin, operator
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SUPERADMIN_EMAIL = "admin@pawstraining.com"
SUPERADMIN_PASSWORD = "PawsAdmin2026!"

# Test user data
TEST_OPERATOR_EMAIL = f"test_operator_{uuid.uuid4().hex[:8]}@test.com"
TEST_ADMIN_EMAIL = f"test_admin_{uuid.uuid4().hex[:8]}@test.com"
TEST_OPERATOR_BY_ADMIN_EMAIL = f"test_op_by_admin_{uuid.uuid4().hex[:8]}@test.com"


class TestSuperadminLogin:
    """Test superadmin login and role verification"""
    
    def test_superadmin_login_success(self):
        """Verify superadmin can login and response includes role: superadmin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPERADMIN_EMAIL,
            "password": SUPERADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "token" in data, "Token missing from login response"
        assert "admin" in data, "Admin object missing from login response"
        assert data["admin"]["role"] == "superadmin", f"Expected role 'superadmin', got '{data['admin'].get('role')}'"
        assert data["admin"]["email"] == SUPERADMIN_EMAIL
        print(f"✓ Superadmin login successful, role: {data['admin']['role']}")
    
    def test_superadmin_login_invalid_credentials(self):
        """Verify invalid credentials return 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPERADMIN_EMAIL,
            "password": "wrongpassword"
        })
        assert response.status_code == 401


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
def created_test_users(superadmin_token):
    """Create test users and clean up after tests"""
    created_ids = []
    yield created_ids
    # Cleanup: delete all created test users
    for user_id in created_ids:
        try:
            requests.delete(
                f"{BASE_URL}/api/admin/users/{user_id}",
                headers={"Authorization": f"Bearer {superadmin_token}"}
            )
        except Exception:
            pass


class TestSuperadminUserManagement:
    """Test superadmin user management capabilities"""
    
    def test_superadmin_can_list_users(self, superadmin_token):
        """Superadmin can list all users"""
        response = requests.get(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {superadmin_token}"}
        )
        assert response.status_code == 200, f"Failed to list users: {response.text}"
        users = response.json()
        assert isinstance(users, list), "Expected list of users"
        # Should at least have the superadmin
        assert len(users) >= 1, "Expected at least 1 user (superadmin)"
        print(f"✓ Superadmin can list users, found {len(users)} users")
    
    def test_superadmin_can_create_operator(self, superadmin_token, created_test_users):
        """Superadmin can create an operator user"""
        response = requests.post(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {superadmin_token}"},
            json={
                "name": "Test Operator",
                "email": TEST_OPERATOR_EMAIL,
                "password": "testpass123",
                "role": "operator"
            }
        )
        assert response.status_code == 200, f"Failed to create operator: {response.text}"
        
        user = response.json()
        assert user["email"] == TEST_OPERATOR_EMAIL
        assert user["role"] == "operator"
        assert "id" in user
        created_test_users.append(user["id"])
        print(f"✓ Superadmin created operator: {user['email']}")
        return user
    
    def test_superadmin_can_create_admin(self, superadmin_token, created_test_users):
        """Superadmin can create an admin user"""
        response = requests.post(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {superadmin_token}"},
            json={
                "name": "Test Admin",
                "email": TEST_ADMIN_EMAIL,
                "password": "testpass123",
                "role": "admin"
            }
        )
        assert response.status_code == 200, f"Failed to create admin: {response.text}"
        
        user = response.json()
        assert user["email"] == TEST_ADMIN_EMAIL
        assert user["role"] == "admin"
        created_test_users.append(user["id"])
        print(f"✓ Superadmin created admin: {user['email']}")
        return user
    
    def test_superadmin_can_access_settings(self, superadmin_token):
        """Superadmin can access settings endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/settings",
            headers={"Authorization": f"Bearer {superadmin_token}"}
        )
        assert response.status_code == 200, f"Failed to access settings: {response.text}"
        settings = response.json()
        assert "business_name" in settings
        print(f"✓ Superadmin can access settings")


class TestAdminRole:
    """Test admin role capabilities and restrictions"""
    
    @pytest.fixture(scope="class")
    def admin_user_and_token(self, superadmin_token, created_test_users):
        """Create an admin user and get their token"""
        # Create admin user
        admin_email = f"test_admin_role_{uuid.uuid4().hex[:8]}@test.com"
        create_response = requests.post(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {superadmin_token}"},
            json={
                "name": "Test Admin Role",
                "email": admin_email,
                "password": "testpass123",
                "role": "admin"
            }
        )
        if create_response.status_code != 200:
            pytest.skip(f"Failed to create admin user: {create_response.text}")
        
        admin_user = create_response.json()
        created_test_users.append(admin_user["id"])
        
        # Login as admin
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": admin_email,
            "password": "testpass123"
        })
        if login_response.status_code != 200:
            pytest.skip(f"Failed to login as admin: {login_response.text}")
        
        login_data = login_response.json()
        assert login_data["admin"]["role"] == "admin", f"Expected role 'admin', got '{login_data['admin'].get('role')}'"
        
        return {"user": admin_user, "token": login_data["token"], "email": admin_email}
    
    def test_admin_login_returns_admin_role(self, admin_user_and_token):
        """Verify admin login response includes role: admin"""
        # Already verified in fixture, but let's be explicit
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": admin_user_and_token["email"],
            "password": "testpass123"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["admin"]["role"] == "admin"
        print(f"✓ Admin login returns role: admin")
    
    def test_admin_can_list_users(self, admin_user_and_token):
        """Admin can list users (only their created operators)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {admin_user_and_token['token']}"}
        )
        assert response.status_code == 200, f"Admin failed to list users: {response.text}"
        users = response.json()
        # Admin should see empty list initially (no operators created yet)
        assert isinstance(users, list)
        print(f"✓ Admin can list users, found {len(users)} users")
    
    def test_admin_can_create_operator(self, admin_user_and_token, created_test_users):
        """Admin can create an operator user"""
        op_email = f"admin_created_op_{uuid.uuid4().hex[:8]}@test.com"
        response = requests.post(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {admin_user_and_token['token']}"},
            json={
                "name": "Admin Created Operator",
                "email": op_email,
                "password": "testpass123",
                "role": "operator"
            }
        )
        assert response.status_code == 200, f"Admin failed to create operator: {response.text}"
        
        user = response.json()
        assert user["role"] == "operator"
        created_test_users.append(user["id"])
        print(f"✓ Admin created operator: {user['email']}")
    
    def test_admin_cannot_create_admin(self, admin_user_and_token):
        """Admin cannot create another admin user"""
        response = requests.post(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {admin_user_and_token['token']}"},
            json={
                "name": "Attempted Admin",
                "email": f"attempted_admin_{uuid.uuid4().hex[:8]}@test.com",
                "password": "testpass123",
                "role": "admin"
            }
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print(f"✓ Admin correctly blocked from creating admin user")
    
    def test_admin_cannot_access_settings(self, admin_user_and_token):
        """Admin cannot access settings endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/settings",
            headers={"Authorization": f"Bearer {admin_user_and_token['token']}"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print(f"✓ Admin correctly blocked from accessing settings")


class TestOperatorRole:
    """Test operator role restrictions"""
    
    @pytest.fixture(scope="class")
    def operator_user_and_token(self, superadmin_token, created_test_users):
        """Create an operator user and get their token"""
        # Create operator user
        op_email = f"test_operator_role_{uuid.uuid4().hex[:8]}@test.com"
        create_response = requests.post(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {superadmin_token}"},
            json={
                "name": "Test Operator Role",
                "email": op_email,
                "password": "testpass123",
                "role": "operator"
            }
        )
        if create_response.status_code != 200:
            pytest.skip(f"Failed to create operator user: {create_response.text}")
        
        op_user = create_response.json()
        created_test_users.append(op_user["id"])
        
        # Login as operator
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": op_email,
            "password": "testpass123"
        })
        if login_response.status_code != 200:
            pytest.skip(f"Failed to login as operator: {login_response.text}")
        
        login_data = login_response.json()
        assert login_data["admin"]["role"] == "operator", f"Expected role 'operator', got '{login_data['admin'].get('role')}'"
        
        return {"user": op_user, "token": login_data["token"], "email": op_email}
    
    def test_operator_login_returns_operator_role(self, operator_user_and_token):
        """Verify operator login response includes role: operator"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": operator_user_and_token["email"],
            "password": "testpass123"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["admin"]["role"] == "operator"
        print(f"✓ Operator login returns role: operator")
    
    def test_operator_cannot_list_users(self, operator_user_and_token):
        """Operator cannot access user list endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {operator_user_and_token['token']}"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print(f"✓ Operator correctly blocked from listing users")
    
    def test_operator_cannot_create_users(self, operator_user_and_token):
        """Operator cannot create users"""
        response = requests.post(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {operator_user_and_token['token']}"},
            json={
                "name": "Attempted User",
                "email": f"attempted_{uuid.uuid4().hex[:8]}@test.com",
                "password": "testpass123",
                "role": "operator"
            }
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print(f"✓ Operator correctly blocked from creating users")
    
    def test_operator_cannot_access_settings(self, operator_user_and_token):
        """Operator cannot access settings endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/settings",
            headers={"Authorization": f"Bearer {operator_user_and_token['token']}"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print(f"✓ Operator correctly blocked from accessing settings")
    
    def test_operator_can_access_dashboard(self, operator_user_and_token):
        """Operator can access dashboard endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/dashboard",
            headers={"Authorization": f"Bearer {operator_user_and_token['token']}"}
        )
        assert response.status_code == 200, f"Operator failed to access dashboard: {response.text}"
        print(f"✓ Operator can access dashboard")
    
    def test_operator_can_access_bookings(self, operator_user_and_token):
        """Operator can access bookings endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/bookings",
            headers={"Authorization": f"Bearer {operator_user_and_token['token']}"}
        )
        assert response.status_code == 200, f"Operator failed to access bookings: {response.text}"
        print(f"✓ Operator can access bookings")


class TestUserDeletion:
    """Test user deletion permissions"""
    
    def test_superadmin_can_delete_operator(self, superadmin_token, created_test_users):
        """Superadmin can delete an operator"""
        # First create an operator to delete
        op_email = f"delete_test_op_{uuid.uuid4().hex[:8]}@test.com"
        create_response = requests.post(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {superadmin_token}"},
            json={
                "name": "To Delete Operator",
                "email": op_email,
                "password": "testpass123",
                "role": "operator"
            }
        )
        assert create_response.status_code == 200
        user_id = create_response.json()["id"]
        
        # Delete the operator
        delete_response = requests.delete(
            f"{BASE_URL}/api/admin/users/{user_id}",
            headers={"Authorization": f"Bearer {superadmin_token}"}
        )
        assert delete_response.status_code == 200, f"Failed to delete operator: {delete_response.text}"
        
        # Verify user is deleted
        list_response = requests.get(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {superadmin_token}"}
        )
        users = list_response.json()
        user_ids = [u["id"] for u in users]
        assert user_id not in user_ids, "Deleted user still appears in list"
        print(f"✓ Superadmin successfully deleted operator")
    
    def test_superadmin_can_delete_admin(self, superadmin_token, created_test_users):
        """Superadmin can delete an admin"""
        # First create an admin to delete
        admin_email = f"delete_test_admin_{uuid.uuid4().hex[:8]}@test.com"
        create_response = requests.post(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {superadmin_token}"},
            json={
                "name": "To Delete Admin",
                "email": admin_email,
                "password": "testpass123",
                "role": "admin"
            }
        )
        assert create_response.status_code == 200
        user_id = create_response.json()["id"]
        
        # Delete the admin
        delete_response = requests.delete(
            f"{BASE_URL}/api/admin/users/{user_id}",
            headers={"Authorization": f"Bearer {superadmin_token}"}
        )
        assert delete_response.status_code == 200, f"Failed to delete admin: {delete_response.text}"
        print(f"✓ Superadmin successfully deleted admin")


class TestPublicEndpoints:
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
