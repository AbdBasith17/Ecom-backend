
from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class AuthTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@perfaura.com",
            password="testpass123",
            name="Test User",
            is_active=True
        )

    # --- Login tests ---
    def test_login_success(self):
        res = self.client.post("/api/auth/login/", {
            "email": "test@perfaura.com",
            "password": "testpass123"
        }, content_type="application/json")
        self.assertEqual(res.status_code, 200)
        self.assertIn("user", res.json())

    def test_login_wrong_password(self):
        res = self.client.post("/api/auth/login/", {
            "email": "test@perfaura.com",
            "password": "wrongpassword"
        }, content_type="application/json")
        self.assertEqual(res.status_code, 401)

    def test_login_missing_fields(self):
        res = self.client.post("/api/auth/login/", {
            "email": "test@perfaura.com"
        }, content_type="application/json")
        self.assertEqual(res.status_code, 400)

    # --- Me endpoint tests ---
    def test_me_without_auth_returns_401(self):
        res = self.client.get("/api/auth/me/")
        self.assertEqual(res.status_code, 401)

    # --- Register tests ---
    def test_register_missing_fields(self):
        res = self.client.post("/api/auth/register/", {
            "email": "new@perfaura.com"
        }, content_type="application/json")
        self.assertEqual(res.status_code, 400)

    # --- Logout tests ---
    def test_logout_succeeds(self):
        res = self.client.post("/api/auth/logout/")
        self.assertEqual(res.status_code, 200)