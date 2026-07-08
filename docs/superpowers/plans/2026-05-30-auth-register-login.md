# Auth: Register, Login, Token Refresh — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire up user registration, login (email or username), and JWT token refresh endpoints in the `authentication` app.

**Architecture:** Custom `User` model (already defined) registered as `AUTH_USER_MODEL`. Three open endpoints under `/api/auth/`. Login serializer tries email lookup first, then username. simplejwt handles token issuance and refresh.

**Tech Stack:** Django 5.2, DRF 3.16, djangorestframework-simplejwt 5.5, drf-spectacular

---

## File Map

| Action | File |
|---|---|
| Modify | `assetmanagement/assetmanagement/settings.py` |
| Modify | `assetmanagement/authentication/serializers.py` |
| Modify | `assetmanagement/authentication/views.py` |
| Modify | `assetmanagement/authentication/urls.py` |
| Modify | `assetmanagement/authentication/tests.py` |

---

## Task 1: Settings — Register the authentication app and custom User model

**Files:**
- Modify: `assetmanagement/assetmanagement/settings.py`

- [ ] **Step 1: Add `authentication` to INSTALLED_APPS and set AUTH_USER_MODEL**

Open `assetmanagement/assetmanagement/settings.py`. Make two changes:

Change `INSTALLED_APPS` from:
```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    ##
    "drf_spectacular",
    "rest_framework",
    "django_filters",
    ##
    "predictions",
]
```
To:
```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    ##
    "drf_spectacular",
    "rest_framework",
    "django_filters",
    ##
    "authentication",
    "predictions",
]
```

Then add this line anywhere before `MIDDLEWARE`:
```python
AUTH_USER_MODEL = "authentication.User"
```

- [ ] **Step 2: Create and apply migrations**

```bash
cd assetmanagement
python manage.py makemigrations authentication
python manage.py migrate
```

Expected output ends with: `Applying authentication.0001_initial... OK`

- [ ] **Step 3: Commit**

```bash
git add assetmanagement/assetmanagement/settings.py assetmanagement/authentication/migrations/
git commit -m "chore: register authentication app and custom User model"
```

---

## Task 2: Register endpoint — tests, view fix, URL

**Files:**
- Modify: `assetmanagement/authentication/tests.py`
- Modify: `assetmanagement/authentication/views.py`
- Modify: `assetmanagement/authentication/urls.py`

- [ ] **Step 1: Write failing tests for registration**

Replace the contents of `assetmanagement/authentication/tests.py` with:

```python
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()

REGISTER_URL = "/api/auth/register/"


class UserRegisterTests(APITestCase):
    def setUp(self):
        self.valid_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "StrongPass123",
            "confirm_password": "StrongPass123",
        }

    def test_register_success(self):
        response = self.client.post(REGISTER_URL, self.valid_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="test@example.com").exists())
        self.assertNotIn("password", response.data)

    def test_register_password_mismatch(self):
        data = {**self.valid_data, "confirm_password": "WrongPass123"}
        response = self.client.post(REGISTER_URL, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("confirm_password", response.data)

    def test_register_duplicate_email(self):
        self.client.post(REGISTER_URL, self.valid_data)
        data = {**self.valid_data, "username": "otheruser"}
        response = self.client.post(REGISTER_URL, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_username(self):
        self.client.post(REGISTER_URL, self.valid_data)
        data = {**self.valid_data, "email": "other@example.com"}
        response = self.client.post(REGISTER_URL, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd assetmanagement
python manage.py test authentication.tests.UserRegisterTests -v 2
```

Expected: all 4 tests FAIL (404 Not Found — no URLs wired yet)

- [ ] **Step 3: Update UserRegisterView to allow unauthenticated access**

Replace `assetmanagement/authentication/views.py` with:

```python
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView

from .models import User
from .serializers import UserRegisterSerializer


class UserRegisterView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]
```

- [ ] **Step 4: Wire the register URL**

Replace `assetmanagement/authentication/urls.py` with:

```python
from django.urls import path

from .views import UserRegisterView

urlpatterns = [
    path("register/", UserRegisterView.as_view(), name="user-register"),
]
```

- [ ] **Step 5: Run tests to confirm they pass**

```bash
cd assetmanagement
python manage.py test authentication.tests.UserRegisterTests -v 2
```

Expected: 4 tests PASS

- [ ] **Step 6: Commit**

```bash
git add assetmanagement/authentication/tests.py assetmanagement/authentication/views.py assetmanagement/authentication/urls.py
git commit -m "feat: add user registration endpoint"
```

---

## Task 3: Login endpoint — tests, serializer update, view, URL

**Files:**
- Modify: `assetmanagement/authentication/tests.py`
- Modify: `assetmanagement/authentication/serializers.py`
- Modify: `assetmanagement/authentication/views.py`
- Modify: `assetmanagement/authentication/urls.py`

- [ ] **Step 1: Add failing login tests**

Append to `assetmanagement/authentication/tests.py`:

```python

LOGIN_URL = "/api/auth/login/"


class UserLoginTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="StrongPass123",
        )

    def test_login_with_email(self):
        response = self.client.post(LOGIN_URL, {
            "identifier": "test@example.com",
            "password": "StrongPass123",
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_with_username(self):
        response = self.client.post(LOGIN_URL, {
            "identifier": "testuser",
            "password": "StrongPass123",
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_wrong_password(self):
        response = self.client.post(LOGIN_URL, {
            "identifier": "test@example.com",
            "password": "WrongPassword",
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_nonexistent_identifier(self):
        response = self.client.post(LOGIN_URL, {
            "identifier": "nobody@example.com",
            "password": "SomePass123",
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
```

- [ ] **Step 2: Run login tests to confirm they fail**

```bash
cd assetmanagement
python manage.py test authentication.tests.UserLoginTests -v 2
```

Expected: all 4 tests FAIL (404 — no login URL wired yet)

- [ ] **Step 3: Update UserLoginSerializer**

Replace the `UserLoginSerializer` class in `assetmanagement/authentication/serializers.py` with the version below. Keep `UserRegisterSerializer` unchanged.

Full file content:

```python
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password", "confirm_password", "email_verified")
        read_only_fields = ("id", "email_verified")

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": _("Passwords do not match.")})
        return attrs

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        return User.objects.create_user(**validated_data)


class UserLoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        identifier = attrs.get("identifier")
        password = attrs.get("password")

        user = None
        try:
            user = User.objects.get(email=identifier)
        except User.DoesNotExist:
            try:
                user = User.objects.get(username=identifier)
            except User.DoesNotExist:
                pass

        if user is None or not user.check_password(password):
            raise AuthenticationFailed(_("Invalid credentials."))

        refresh = RefreshToken.for_user(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }
```

- [ ] **Step 4: Add UserLoginView to views.py**

Replace `assetmanagement/authentication/views.py` with:

```python
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView

from .models import User
from .serializers import UserRegisterSerializer, UserLoginSerializer


class UserRegisterView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]


class UserLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)
```

- [ ] **Step 5: Add login URL**

Replace `assetmanagement/authentication/urls.py` with:

```python
from django.urls import path

from .views import UserRegisterView, UserLoginView

urlpatterns = [
    path("register/", UserRegisterView.as_view(), name="user-register"),
    path("login/", UserLoginView.as_view(), name="user-login"),
]
```

- [ ] **Step 6: Run login tests to confirm they pass**

```bash
cd assetmanagement
python manage.py test authentication.tests.UserLoginTests -v 2
```

Expected: 4 tests PASS

- [ ] **Step 7: Commit**

```bash
git add assetmanagement/authentication/serializers.py assetmanagement/authentication/views.py assetmanagement/authentication/urls.py assetmanagement/authentication/tests.py
git commit -m "feat: add user login endpoint (email or username)"
```

---

## Task 4: Token refresh endpoint — test and URL

**Files:**
- Modify: `assetmanagement/authentication/tests.py`
- Modify: `assetmanagement/authentication/urls.py`

- [ ] **Step 1: Add failing token refresh test**

Append to `assetmanagement/authentication/tests.py`:

```python

REFRESH_URL = "/api/auth/token/refresh/"


class TokenRefreshTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="StrongPass123",
        )
        login_response = self.client.post(LOGIN_URL, {
            "identifier": "test@example.com",
            "password": "StrongPass123",
        })
        self.refresh_token = login_response.data["refresh"]

    def test_refresh_success(self):
        response = self.client.post(REFRESH_URL, {"refresh": self.refresh_token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_refresh_invalid_token(self):
        response = self.client.post(REFRESH_URL, {"refresh": "not-a-real-token"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
```

- [ ] **Step 2: Run token refresh tests to confirm they fail**

```bash
cd assetmanagement
python manage.py test authentication.tests.TokenRefreshTests -v 2
```

Expected: both tests FAIL (404 — no refresh URL wired yet)

- [ ] **Step 3: Add token refresh URL**

Replace `assetmanagement/authentication/urls.py` with:

```python
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import UserRegisterView, UserLoginView

urlpatterns = [
    path("register/", UserRegisterView.as_view(), name="user-register"),
    path("login/", UserLoginView.as_view(), name="user-login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
]
```

- [ ] **Step 4: Run all authentication tests to confirm everything passes**

```bash
cd assetmanagement
python manage.py test authentication -v 2
```

Expected: 10 tests PASS

- [ ] **Step 5: Commit**

```bash
git add assetmanagement/authentication/tests.py assetmanagement/authentication/urls.py
git commit -m "feat: add token refresh endpoint"
```
