# GPS Proximity Asset Matching Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement 1-meter radius GPS proximity matching using Haversine distance calculation to prevent duplicate asset creation when uploading CT/asset images from virtually the same location.

**Architecture:** A pure Python Haversine calculation helper `haversine_distance` will compute distance in meters between coordinates. A service function `find_or_create_asset_within_radius` will query candidate assets by label and select any asset within 1.0 meter deviation before creating a new asset. `AssetCreateSerializer` will call this service function.

**Tech Stack:** Python 3.12, Django 5.2, Django REST Framework, Math library, Pytest/Django TestCase.

## Global Constraints
- Must maintain backward compatibility for API requests (`coordinates`: `{"lat": ..., "lng": ...}`).
- Default deviation radius is `1.0` meter.
- No new external C dependencies (e.g. PostGIS/GDAL/GEOS not required).

---

### Task 1: Add Haversine Distance Utility and Proximity Service Function

**Files:**
- Modify: `assetmanagement/assets/services.py`
- Modify: `assetmanagement/assets/tests.py`

**Interfaces:**
- Produces: `haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float`
- Produces: `find_or_create_asset_within_radius(coordinates: dict, label_val: str, defaults: dict, radius_meters: float = 1.0) -> tuple[Asset, bool]`

- [ ] **Step 1: Write failing unit test for `haversine_distance` and `find_or_create_asset_within_radius`**

In `assetmanagement/assets/tests.py`, add:

```python
from assets.services import haversine_distance, find_or_create_asset_within_radius
from assets.models import Asset

class ProximityServiceTest(TestCase):
    def test_haversine_distance_calculation(self):
        # 27.700769, 85.300140 to 27.700769, 85.300149 is ~0.9 meters
        dist = haversine_distance(27.700769, 85.300140, 27.700769, 85.300149)
        self.assertLess(dist, 1.0)
        self.assertGreater(dist, 0.5)

    def test_find_or_create_asset_within_radius_match(self):
        existing = Asset.objects.create(
            coordinates={"lat": 27.700769, "lng": 85.300140},
            label="transformer",
            status="PENDING"
        )
        # Nearby point (approx 0.8m away)
        nearby_coords = {"lat": 27.700769, "lng": 85.300148}
        asset, created = find_or_create_asset_within_radius(
            coordinates=nearby_coords,
            label_val="transformer",
            defaults={"status": "PENDING"},
            radius_meters=1.0
        )
        self.assertFalse(created)
        self.assertEqual(asset.id, existing.id)

    def test_find_or_create_asset_within_radius_no_match_farther(self):
        existing = Asset.objects.create(
            coordinates={"lat": 27.700769, "lng": 85.300140},
            label="transformer",
            status="PENDING"
        )
        # Point far away (> 100 meters)
        far_coords = {"lat": 27.701500, "lng": 85.301500}
        asset, created = find_or_create_asset_within_radius(
            coordinates=far_coords,
            label_val="transformer",
            defaults={"status": "PENDING"},
            radius_meters=1.0
        )
        self.assertTrue(created)
        self.assertNotEqual(asset.id, existing.id)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python assetmanagement/manage.py test assets.tests.ProximityServiceTest`
Expected: FAIL with ImportError / AttributeError (functions not yet defined in `services.py`).

- [ ] **Step 3: Implement `haversine_distance` and `find_or_create_asset_within_radius` in `services.py`**

In `assetmanagement/assets/services.py`, add math import and functions:

```python
import math
from .models import Asset

def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Returns distance in meters between two lat/lng coordinates.
    """
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return R * c


def find_or_create_asset_within_radius(coordinates: dict, label_val: str, defaults: dict, radius_meters: float = 1.0):
    """
    Looks for an existing asset with matching label within radius_meters of coordinates.
    Returns (asset, created_boolean).
    """
    try:
        target_lat = float(coordinates.get("lat"))
        target_lng = float(coordinates.get("lng"))
    except (TypeError, ValueError):
        # Fallback if coordinates missing/invalid
        target_lat, target_lng = None, None

    if target_lat is not None and target_lng is not None and label_val:
        candidates = Asset.objects.filter(label=label_val)
        closest_asset = None
        min_distance = float("inf")

        for candidate in candidates:
            cand_coords = candidate.coordinates or {}
            try:
                cand_lat = float(cand_coords.get("lat"))
                cand_lng = float(cand_coords.get("lng"))
                dist = haversine_distance(target_lat, target_lng, cand_lat, cand_lng)
                if dist <= radius_meters and dist < min_distance:
                    min_distance = dist
                    closest_asset = candidate
            except (TypeError, ValueError):
                continue

        if closest_asset:
            return closest_asset, False

    # Create new if no match within radius
    new_asset = Asset.objects.create(
        coordinates=coordinates,
        label=label_val,
        **defaults
    )
    return new_asset, True
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python assetmanagement/manage.py test assets.tests.ProximityServiceTest`
Expected: PASS (3 tests pass).

- [ ] **Step 5: Commit Task 1**

```bash
git add assetmanagement/assets/services.py assetmanagement/assets/tests.py
git commit -m "feat: add haversine distance and proximity asset lookup service"
```

---

### Task 2: Integrate Proximity Matching into AssetCreateSerializer

**Files:**
- Modify: `assetmanagement/assets/serializers.py:114-135`
- Modify: `assetmanagement/assets/tests.py`

**Interfaces:**
- Consumes: `find_or_create_asset_within_radius` from `assets.services`

- [ ] **Step 1: Write API Integration Test for Proximity Upload**

In `assetmanagement/assets/tests.py`, add API test case:

```python
class AssetCreateProximityAPITest(APITestCase):
    def test_upload_within_1m_returns_existing_asset_200(self):
        # Setup existing asset
        existing = Asset.objects.create(
            coordinates={"lat": 27.700769, "lng": 85.300140},
            label="pipe",
            status="PENDING"
        )
        # Mock YOLO service to return 'pipe'
        # Perform POST to /api/assets/ with coords 0.5m away
        # Verify status == 200 OK and id == existing.id
```

- [ ] **Step 2: Update `AssetCreateSerializer.create()` to call `find_or_create_asset_within_radius`**

In `assetmanagement/assets/serializers.py`:

```python
from .services import run_yolo_and_annotate, find_or_create_asset_within_radius

# Inside AssetCreateSerializer.create():
        if coordinates and label_val:
            asset, created = find_or_create_asset_within_radius(
                coordinates=coordinates,
                label_val=label_val,
                defaults={
                    "user": user,
                    "original_image": original_image,
                    "predicted_image": predicted_image,
                    "conf": conf_val,
                    "status": "PENDING",
                },
                radius_meters=1.0,
            )
        else:
            validated_data['predicted_image'] = predicted_image
            validated_data['label'] = label_val
            validated_data['conf'] = conf_val
            validated_data['status'] = "PENDING"
            asset = super().create(validated_data)
            created = True

        asset.is_newly_created = created
        return asset
```

- [ ] **Step 3: Run all asset tests to verify zero regressions**

Run: `python assetmanagement/manage.py test assets`
Expected: ALL PASS.

- [ ] **Step 4: Commit Task 2**

```bash
git add assetmanagement/assets/serializers.py assetmanagement/assets/tests.py
git commit -m "feat: integrate 1m proximity lookup in AssetCreateSerializer"
```
