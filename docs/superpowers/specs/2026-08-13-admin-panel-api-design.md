# Admin Panel API Design Document

> **Date:** 2026-08-13
> **Target:** Admin Panel REST API (`admin` app)
> **Goal:** Provide a secure, robust DRF ModelViewSet API for the React Admin Panel allowing superusers to manage assets and inspect dashboard metrics.

---

## 1. Overview & Security

- **Authentication:** SimpleJWT (Bearer token)
- **Permissions:** Custom `IsSuperUser` permission class.
  - Anonymous users -> `401 Unauthorized`
  - Authenticated regular users / non-superuser staff -> `403 Forbidden`
  - Authenticated superusers (`is_superuser=True`) -> `200 OK`

---

## 2. Component Architecture & Files

The API logic resides inside the `admin` app (`assetmanagement/admin/`):

- `admin/permissions.py`: Custom `IsSuperUser` permission class.
- `admin/serializers.py`: `AdminAssetSerializer` and `AdminAssetStatsSerializer`.
- `admin/views.py`: `AdminAssetViewSet(viewsets.ModelViewSet)` with `@action(detail=False)` for `stats`.
- `admin/urls.py`: DRF `DefaultRouter` routing `/api/admin/assets/`.
- `admin/tests.py`: Complete TDD unit test suite.

---

## 3. Detailed Specifications

### 3.1 Permissions (`admin/permissions.py`)
```python
from rest_framework.permissions import BasePermission

class IsSuperUser(BasePermission):
    """
    Allows access only to authenticated superusers.
    """
    def has_permission(self, request, view):
        return bool(
            request.user 
            and request.user.is_authenticated 
            and request.user.is_superuser
        )
```

---

### 3.2 Serializers (`admin/serializers.py`)

#### `AdminAssetSerializer`
ModelSerializer for `Asset` exposing all model fields:
- `id` (read-only)
- `status`
- `original_image`
- `predicted_image`
- `label`
- `conf`
- `maker`
- `model_no`
- `year`
- `price_jpy`
- `size`
- `maintenance_cycle`
- `last_maintenance_date`
- `next_maintenance_due`
- `notes`
- `created_at` (read-only)
- `coordinates`

#### `AdminAssetStatsSerializer`
Non-model serializer returning key dashboard metrics:
- `total_assets`: `int`
- `pending_count`: `int`
- `correct_count`: `int`
- `incorrect_count`: `int`
- `maintenance_due_count`: `int` (assets with `next_maintenance_due <= today + 30 days`)

---

### 3.3 ViewSet (`admin/views.py`)

`AdminAssetViewSet` inherits from `viewsets.ModelViewSet`:
- `permission_classes = [IsSuperUser]`
- `queryset = Asset.objects.all()`
- `serializer_class = AdminAssetSerializer`
- `filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]`
- `filterset_fields = ['status', 'year']`
- `search_fields = ['maker', 'model_no', 'notes']`
- `ordering_fields = ['created_at', 'last_maintenance_date', 'next_maintenance_due', 'price_jpy']`

#### Stats Action Endpoint
`GET /api/admin/assets/stats/`
Calculates:
- `total_assets = Asset.objects.count()`
- `pending_count = Asset.objects.filter(status='PENDING').count()`
- `correct_count = Asset.objects.filter(status='CORRECT').count()`
- `incorrect_count = Asset.objects.filter(status='INCORRECT').count()`
- `maintenance_due_count = Asset.objects.filter(next_maintenance_due__lte=timezone.now().date() + timedelta(days=30)).count()`

Returns HTTP 200 with dictionary of metrics.

---

### 3.4 Routing (`admin/urls.py`)

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AdminAssetViewSet

router = DefaultRouter()
router.register(r"assets", AdminAssetViewSet, basename="admin-asset")

urlpatterns = [
    path("", include(router.urls)),
]
```

Included in root `urls.py`:
```python
path("api/admin/", include("admin.urls")),
```

---

## 4. Endpoints Table

| HTTP Method | URL Path | Description |
| :--- | :--- | :--- |
| `GET` | `/api/admin/assets/` | List all assets (searchable, filterable, paginated) |
| `POST` | `/api/admin/assets/` | Create a new asset record |
| `GET` | `/api/admin/assets/{id}/` | Retrieve full details of single asset |
| `PUT / PATCH` | `/api/admin/assets/{id}/` | Update any fields of asset |
| `DELETE` | `/api/admin/assets/{id}/` | Delete an asset record |
| `GET` | `/api/admin/assets/stats/` | Retrieve admin dashboard metrics |

---

## 5. Testing Plan

Using Test-Driven Development (TDD):
1. **Permission tests:**
   - Anonymous request -> 401
   - Non-superuser request -> 403
   - Superuser request -> 200/201
2. **CRUD tests:**
   - Verify list, create, retrieve, update, delete operations on `/api/admin/assets/`.
3. **Stats tests:**
   - Seed database with test assets (different statuses and maintenance dates).
   - Verify `/api/admin/assets/stats/` returns accurate aggregate counts.
