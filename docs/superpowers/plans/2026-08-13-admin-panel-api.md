# Admin Panel API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a robust DRF ModelViewSet API for the Admin Panel (`admin` app) accessible only by superusers, with full Asset CRUD operations and dashboard stats metrics.

**Architecture:** Custom `IsSuperUser` permission class in `admin/permissions.py`, `AdminAssetSerializer` and `AdminAssetStatsSerializer` in `admin/serializers.py`, `AdminAssetViewSet(viewsets.ModelViewSet)` in `admin/views.py` with `@action(detail=False)` for dashboard stats, routed via DRF DefaultRouter in `admin/urls.py`.

**Tech Stack:** Django 5.x, Django REST Framework, SimpleJWT, sqlite3/PostgreSQL.

## Global Constraints

- Authentication: SimpleJWT (`rest_framework_simplejwt.authentication.JWTAuthentication`)
- Access Control: Only `is_superuser=True` allowed
- Base URL prefix: `/api/admin/`

---

### Task 1: IsSuperUser Permission Class

**Files:**
- Create: `assetmanagement/admin/permissions.py`
- Modify: `assetmanagement/admin/tests.py`

**Interfaces:**
- Consumes: `rest_framework.permissions.BasePermission`
- Produces: `IsSuperUser` permission class in `admin.permissions`

- [ ] **Step 1: Write failing unit test for IsSuperUser permission**

Write test in `assetmanagement/admin/tests.py`:

```python
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from admin.permissions import IsSuperUser

User = get_user_model()


class IsSuperUserPermissionTestCase(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.permission = IsSuperUser()
        self.superuser = User.objects.create_superuser(
            username="super", email="super@example.com", password="password"
        )
        self.regular_user = User.objects.create_user(
            username="regular", email="regular@example.com", password="password"
        )

    def test_superuser_has_permission(self):
        request = self.factory.get("/")
        request.user = self.superuser
        self.assertTrue(self.permission.has_permission(request, None))

    def test_regular_user_denied_permission(self):
        request = self.factory.get("/")
        request.user = self.regular_user
        self.assertFalse(self.permission.has_permission(request, None))

    def test_anonymous_user_denied_permission(self):
        from django.contrib.auth.models import AnonymousUser
        request = self.factory.get("/")
        request.user = AnonymousUser()
        self.assertFalse(self.permission.has_permission(request, None))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `SECRET_KEY="testsecretkey" DB_ENGINE="django.db.backends.sqlite3" DB_NAME="testdb.sqlite3" /home/rejens/work/AssetManagement/.venv/bin/python manage.py test admin`
Expected: FAIL with `ModuleNotFoundError: No module named 'admin.permissions'`

- [ ] **Step 3: Write minimal implementation**

Create `assetmanagement/admin/permissions.py`:

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

- [ ] **Step 4: Run test to verify it passes**

Run: `SECRET_KEY="testsecretkey" DB_ENGINE="django.db.backends.sqlite3" DB_NAME="testdb.sqlite3" /home/rejens/work/AssetManagement/.venv/bin/python manage.py test admin`
Expected: PASS (Ran 3 tests in ... OK)

- [ ] **Step 5: Commit**

```bash
git add assetmanagement/admin/permissions.py assetmanagement/admin/tests.py
git commit -m "feat(admin): implement IsSuperUser permission class with tests"
```

---

### Task 2: Admin Serializers (`AdminAssetSerializer` & `AdminAssetStatsSerializer`)

**Files:**
- Create: `assetmanagement/admin/serializers.py`
- Modify: `assetmanagement/admin/tests.py`

**Interfaces:**
- Consumes: `assets.models.Asset`
- Produces: `AdminAssetSerializer`, `AdminAssetStatsSerializer` in `admin.serializers`

- [ ] **Step 1: Write failing unit test for serializers**

Add to `assetmanagement/admin/tests.py`:

```python
from assets.models import Asset
from admin.serializers import AdminAssetSerializer, AdminAssetStatsSerializer


class AdminSerializersTestCase(TestCase):
    def setUp(self):
        self.asset = Asset.objects.create(
            status="PENDING",
            coordinates={"lat": 27.7, "lng": 85.3},
            maker="TestMaker",
            model_no="M123",
        )

    def test_admin_asset_serializer_contains_all_fields(self):
        serializer = AdminAssetSerializer(self.asset)
        data = serializer.data
        self.assertEqual(data["id"], self.asset.id)
        self.assertEqual(data["status"], "PENDING")
        self.assertEqual(data["maker"], "TestMaker")
        self.assertIn("coordinates", data)

    def test_admin_asset_stats_serializer(self):
        stats_data = {
            "total_assets": 10,
            "pending_count": 4,
            "correct_count": 5,
            "incorrect_count": 1,
            "maintenance_due_count": 2,
        }
        serializer = AdminAssetStatsSerializer(data=stats_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["total_assets"], 10)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `SECRET_KEY="testsecretkey" DB_ENGINE="django.db.backends.sqlite3" DB_NAME="testdb.sqlite3" /home/rejens/work/AssetManagement/.venv/bin/python manage.py test admin`
Expected: FAIL with `ModuleNotFoundError: No module named 'admin.serializers'`

- [ ] **Step 3: Write minimal implementation**

Create `assetmanagement/admin/serializers.py`:

```python
from rest_framework import serializers
from assets.models import Asset
from assets.serializers import CustomImageField


class AdminAssetSerializer(serializers.ModelSerializer):
    original_image = CustomImageField(required=False, allow_null=True)
    predicted_image = CustomImageField(required=False, allow_null=True)

    class Meta:
        model = Asset
        fields = [
            "id",
            "status",
            "original_image",
            "predicted_image",
            "label",
            "conf",
            "maker",
            "model_no",
            "year",
            "price_jpy",
            "size",
            "maintenance_cycle",
            "last_maintenance_date",
            "next_maintenance_due",
            "notes",
            "created_at",
            "coordinates",
        ]
        read_only_fields = ["id", "created_at"]


class AdminAssetStatsSerializer(serializers.Serializer):
    total_assets = serializers.IntegerField()
    pending_count = serializers.IntegerField()
    correct_count = serializers.IntegerField()
    incorrect_count = serializers.IntegerField()
    maintenance_due_count = serializers.IntegerField()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `SECRET_KEY="testsecretkey" DB_ENGINE="django.db.backends.sqlite3" DB_NAME="testdb.sqlite3" /home/rejens/work/AssetManagement/.venv/bin/python manage.py test admin`
Expected: PASS (Ran 5 tests in ... OK)

- [ ] **Step 5: Commit**

```bash
git add assetmanagement/admin/serializers.py assetmanagement/admin/tests.py
git commit -m "feat(admin): implement AdminAssetSerializer and AdminAssetStatsSerializer"
```

---

### Task 3: AdminAssetViewSet, URL Routing & API Endpoint Integration Tests

**Files:**
- Modify: `assetmanagement/admin/views.py`
- Modify: `assetmanagement/admin/urls.py`
- Modify: `assetmanagement/admin/tests.py`

**Interfaces:**
- Consumes: `admin.permissions.IsSuperUser`, `admin.serializers.AdminAssetSerializer`, `admin.serializers.AdminAssetStatsSerializer`
- Produces: `/api/admin/assets/` CRUD and `/api/admin/assets/stats/` endpoints

- [ ] **Step 1: Write failing API integration tests**

Add `AdminAssetAPITestCase` to `assetmanagement/admin/tests.py`:

```python
from datetime import date, timedelta
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class AdminAssetAPITestCase(APITestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="adminuser", email="admin@example.com", password="password123"
        )
        self.regular_user = User.objects.create_user(
            username="normie", email="normie@example.com", password="password123"
        )
        self.asset1 = Asset.objects.create(
            status="PENDING",
            coordinates={"lat": 27.7, "lng": 85.3},
            maker="BrandA",
            model_no="M1",
            last_maintenance_date=date.today(),
            maintenance_cycle=10,
        )
        self.asset2 = Asset.objects.create(
            status="CORRECT",
            coordinates={"lat": 27.8, "lng": 85.4},
            maker="BrandB",
            model_no="M2",
        )
        self.list_url = reverse("admin-asset-list")
        self.stats_url = reverse("admin-asset-stats")

    def test_anonymous_access_denied(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_user_access_forbidden(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_superuser_can_list_assets(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_superuser_can_update_asset(self):
        self.client.force_authenticate(user=self.superuser)
        detail_url = reverse("admin-asset-detail", kwargs={"pk": self.asset1.pk})
        payload = {
            "status": "CORRECT",
            "maker": "BrandA_Updated",
            "coordinates": {"lat": 27.7, "lng": 85.3},
        }
        response = self.client.patch(detail_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.asset1.refresh_from_db()
        self.assertEqual(self.asset1.maker, "BrandA_Updated")
        self.assertEqual(self.asset1.status, "CORRECT")

    def test_superuser_can_delete_asset(self):
        self.client.force_authenticate(user=self.superuser)
        detail_url = reverse("admin-asset-detail", kwargs={"pk": self.asset1.pk})
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Asset.objects.filter(pk=self.asset1.pk).exists())

    def test_superuser_can_get_dashboard_stats(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(self.stats_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_assets"], 2)
        self.assertEqual(response.data["pending_count"], 1)
        self.assertEqual(response.data["correct_count"], 1)
        self.assertEqual(response.data["incorrect_count"], 0)
        self.assertEqual(response.data["maintenance_due_count"], 1)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `SECRET_KEY="testsecretkey" DB_ENGINE="django.db.backends.sqlite3" DB_NAME="testdb.sqlite3" /home/rejens/work/AssetManagement/.venv/bin/python manage.py test admin`
Expected: FAIL with `NoReverseMatch: Could not resolve "admin-asset-list"`

- [ ] **Step 3: Write minimal implementation**

Update `assetmanagement/admin/views.py`:

```python
from datetime import timedelta
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from assets.models import Asset
from .permissions import IsSuperUser
from .serializers import AdminAssetSerializer, AdminAssetStatsSerializer


class AdminAssetViewSet(viewsets.ModelViewSet):
    queryset = Asset.objects.all()
    serializer_class = AdminAssetSerializer
    permission_classes = [IsSuperUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "year"]
    search_fields = ["maker", "model_no", "notes"]
    ordering_fields = [
        "created_at",
        "last_maintenance_date",
        "next_maintenance_due",
        "price_jpy",
    ]

    @action(detail=False, methods=["get"], url_path="stats")
    def stats(self, request):
        today = timezone.now().date()
        upcoming_threshold = today + timedelta(days=30)

        total_assets = Asset.objects.count()
        pending_count = Asset.objects.filter(status="PENDING").count()
        correct_count = Asset.objects.filter(status="CORRECT").count()
        incorrect_count = Asset.objects.filter(status="INCORRECT").count()
        maintenance_due_count = Asset.objects.filter(
            next_maintenance_due__lte=upcoming_threshold
        ).count()

        stats_data = {
            "total_assets": total_assets,
            "pending_count": pending_count,
            "correct_count": correct_count,
            "incorrect_count": incorrect_count,
            "maintenance_due_count": maintenance_due_count,
        }

        serializer = AdminAssetStatsSerializer(stats_data)
        return Response(serializer.data, status=status.HTTP_200_OK)
```

Update `assetmanagement/admin/urls.py`:

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

- [ ] **Step 4: Run test to verify it passes**

Run: `SECRET_KEY="testsecretkey" DB_ENGINE="django.db.backends.sqlite3" DB_NAME="testdb.sqlite3" /home/rejens/work/AssetManagement/.venv/bin/python manage.py test admin`
Expected: PASS (Ran 11 tests in ... OK)

- [ ] **Step 5: Commit**

```bash
git add assetmanagement/admin/views.py assetmanagement/admin/urls.py assetmanagement/admin/tests.py
git commit -m "feat(admin): implement AdminAssetViewSet and router endpoints with test suite"
```
