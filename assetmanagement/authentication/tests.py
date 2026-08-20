from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class UserRegisterSerializerTestCase(APITestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="admin_test", email="admin@test.com", password="Password123!"
        )

    def test_valid_registration(self):
        payload = {
            "username": "new_user",
            "email": "new_user@example.com",
            "password": "SecurePassword123",
            "confirm_password": "SecurePassword123",
        }
        self.client.force_authenticate(user=self.superuser)
        url = reverse("user-register")
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="new_user").exists())

    def test_password_mismatch_fails(self):
        payload = {
            "username": "new_user",
            "email": "new_user@example.com",
            "password": "SecurePassword123",
            "confirm_password": "DifferentPassword123",
        }
        self.client.force_authenticate(user=self.superuser)
        url = reverse("user-register")
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])

    def test_duplicate_email_fails(self):
        User.objects.create_user(
            username="existing_user1",
            email="duplicate@example.com",
            password="Password123",
        )
        payload = {
            "username": "another_user",
            "email": "duplicate@example.com",
            "password": "SecurePassword123",
            "confirm_password": "SecurePassword123",
        }
        self.client.force_authenticate(user=self.superuser)
        url = reverse("user-register")
        # In a robust API, this must return 400 Bad Request instead of throwing unhandled 500 DB error
        try:
            response = self.client.post(url, payload, format="json")
            self.assertEqual(
                response.status_code,
                status.HTTP_400_BAD_REQUEST,
                f"AUDIT BUG: Registration with duplicate email returned status {response.status_code} instead of 400!",
            )
        except Exception as e:
            self.fail(
                f"AUDIT BUG: Duplicate email registration crashed with unhandled database exception: {e}"
            )

    def test_duplicate_username_fails(self):
        User.objects.create_user(
            username="existing_user2",
            email="existing2@example.com",
            password="Password123",
        )
        payload = {
            "username": "existing_user2",
            "email": "different2@example.com",
            "password": "SecurePassword123",
            "confirm_password": "SecurePassword123",
        }
        self.client.force_authenticate(user=self.superuser)
        url = reverse("user-register")
        # In a robust API, this must return 400 Bad Request instead of throwing unhandled 500 DB error
        try:
            response = self.client.post(url, payload, format="json")
            self.assertEqual(
                response.status_code,
                status.HTTP_400_BAD_REQUEST,
                f"AUDIT BUG: Registration with duplicate username returned status {response.status_code} instead of 400!",
            )
        except Exception as e:
            self.fail(
                f"AUDIT BUG: Duplicate username registration crashed with unhandled database exception: {e}"
            )

    def test_short_password_fails(self):
        payload = {
            "username": "short_pw_user",
            "email": "short@example.com",
            "password": "short",
            "confirm_password": "short",
        }
        self.client.force_authenticate(user=self.superuser)
        url = reverse("user-register")
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserLoginSecurityTestCase(APITestCase):
    def setUp(self):
        self.active_user = User.objects.create_user(
            username="active_user",
            email="active@example.com",
            password="SecurePassword123",
            is_active=True,
        )
        self.inactive_user = User.objects.create_user(
            username="inactive_user",
            email="inactive@example.com",
            password="SecurePassword123",
            is_active=False,
        )
        self.login_url = reverse("user-login")

    def test_active_user_login_with_username(self):
        payload = {"identifier": "active_user", "password": "SecurePassword123"}
        response = self.client.post(self.login_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_active_user_login_with_email(self):
        payload = {"identifier": "active@example.com", "password": "SecurePassword123"}
        response = self.client.post(self.login_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_inactive_user_login_attempt(self):
        """
        SECURITY AUDIT TEST:
        Checks if inactive/deactivated user accounts can log in.
        Inactive accounts SHOULD NOT be allowed to obtain JWT tokens.
        """
        payload = {"identifier": "inactive_user", "password": "SecurePassword123"}
        response = self.client.post(self.login_url, payload, format="json")
        # In a secure production API, inactive users must be denied login (400 or 401).
        self.assertIn(
            response.status_code,
            [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED],
            f"SECURITY VULNERABILITY: Inactive user was able to authenticate! Status code: {response.status_code}",
        )

    def test_invalid_password_login_fails(self):
        payload = {"identifier": "active_user", "password": "WrongPassword"}
        response = self.client.post(self.login_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_nonexistent_user_login_fails(self):
        payload = {"identifier": "ghost_user", "password": "SecurePassword123"}
        response = self.client.post(self.login_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticationPermissionsTestCase(APITestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="admin_user", email="admin@example.com", password="Password123"
        )
        self.regular_user = User.objects.create_user(
            username="regular_user", email="regular@example.com", password="Password123"
        )
        self.register_url = reverse("user-register")

    def test_anonymous_cannot_access_register(self):
        payload = {
            "username": "hacker",
            "email": "hacker@example.com",
            "password": "Password123",
            "confirm_password": "Password123",
        }
        response = self.client.post(self.register_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_user_cannot_access_register(self):
        self.client.force_authenticate(user=self.regular_user)
        payload = {
            "username": "hacker2",
            "email": "hacker2@example.com",
            "password": "Password123",
            "confirm_password": "Password123",
        }
        response = self.client.post(self.register_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_superuser_can_access_register(self):
        self.client.force_authenticate(user=self.superuser)
        payload = {
            "username": "authorized_user",
            "email": "auth@example.com",
            "password": "Password123",
            "confirm_password": "Password123",
        }
        response = self.client.post(self.register_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class TokenRefreshTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="token_user", email="token@example.com", password="Password123"
        )
        self.refresh_token = str(RefreshToken.for_user(self.user))
        self.refresh_url = reverse("token_refresh")

    def test_valid_token_refresh(self):
        payload = {"refresh": self.refresh_token}
        response = self.client.post(self.refresh_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_invalid_token_refresh_fails(self):
        payload = {"refresh": "invalid_refresh_token_string"}
        response = self.client.post(self.refresh_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
