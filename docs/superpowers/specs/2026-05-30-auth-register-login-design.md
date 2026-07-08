# Auth: Register, Login, Token Refresh — Design Spec

**Date:** 2026-05-30  
**Status:** Approved

---

## Overview

Add user registration, login (email or username), and JWT token refresh endpoints to the `authentication` app. The stack is Django 5.2 + DRF + simplejwt. Newly registered users can log in immediately — no email verification gate.

---

## Architecture

All auth logic lives in the `authentication` Django app. Three endpoints are exposed under `/api/auth/`. The custom `User` model (already defined) is registered as `AUTH_USER_MODEL`. No new models are needed.

---

## Settings Changes

Two additions to `assetmanagement/settings.py`:

- Add `"authentication"` to `INSTALLED_APPS`
- Add `AUTH_USER_MODEL = "authentication.User"`

---

## Model

`authentication/models.py` — **no changes needed**.

```python
class User(AbstractUser):
    email = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=False)
```

The `email_verified` field remains on the model but is not checked during login.

---

## Serializers (`authentication/serializers.py`)

### UserRegisterSerializer — no changes needed
- Fields: `id`, `username`, `email`, `password`, `confirm_password`
- Validates passwords match
- Calls `User.objects.create_user()` (hashes password automatically)
- `email_verified` is read-only (defaults False)

### UserLoginSerializer — update existing
- Fields: `identifier` (CharField, accepts email or username), `password` (write-only)
- Lookup: try `User.objects.get(email=identifier)` first; if not found, try `User.objects.get(username=identifier)`
- If neither matches or password is wrong: raise `AuthenticationFailed("Invalid credentials.")`
- Remove `email_verified` check entirely
- On success: return `{"access": "...", "refresh": "..."}`

### TokenRefreshSerializer
- Not needed — simplejwt's `TokenRefreshView` handles this internally.

---

## Views (`authentication/views.py`)

### UserRegisterView — minor update
- Already a `CreateAPIView` with `UserRegisterSerializer`
- Add `permission_classes = [AllowAny]`

### UserLoginView — new
- `APIView` with `permission_classes = [AllowAny]`
- `POST`: instantiate `UserLoginSerializer(data=request.data)`, call `.is_valid(raise_exception=True)`, return `Response(serializer.validated_data)`

---

## URLs (`authentication/urls.py`)

```
POST /api/auth/register/       → UserRegisterView
POST /api/auth/login/          → UserLoginView
POST /api/auth/token/refresh/  → simplejwt TokenRefreshView
```

Root `urls.py` already includes `authentication.urls` at `api/auth/` — no change needed there.

---

## Error Handling

| Scenario | Response |
|---|---|
| Email/username not found | 401 `{"detail": "Invalid credentials."}` |
| Wrong password | 401 `{"detail": "Invalid credentials."}` |
| Passwords don't match (register) | 400 `{"confirm_password": ["Passwords do not match."]}` |
| Invalid/expired refresh token | 401 (handled by simplejwt) |

---

## Testing

- Register with valid data → 201, user created, password hashed
- Register with mismatched passwords → 400
- Login with email → 200, tokens returned
- Login with username → 200, tokens returned
- Login with wrong password → 401
- Refresh with valid token → 200, new access token
- Refresh with invalid token → 401
