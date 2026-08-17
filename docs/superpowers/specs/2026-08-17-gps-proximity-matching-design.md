# GPS Proximity Asset Lookup Design Specification

## Overview
This specification details the proximity-based asset lookup and duplicate prevention mechanism for the Asset Management platform. 
Currently, assets are matched using exact string matching on coordinates JSON (`{"lat": ..., "lng": ...}`). Because real-world GPS readings drift (even when captured from the exact same physical spot), we introduce a 1-meter radius Haversine distance proximity matching system.

## Key Requirements & Criteria
1. **1-Meter Proximity Deviation**: When an asset image and location are uploaded via `POST /api/assets/`, if an existing asset with the same detected YOLO `label` exists within a **1.0 meter radius** of the submitted coordinates, return the existing asset (`is_newly_created = False`, HTTP 200 OK).
2. **New Asset Creation**: If no existing asset with the same `label` is within the 1-meter radius, create a new asset (`is_newly_created = True`, HTTP 201 Created).
3. **No Heavy Geospatial Dependencies**: Pure Python Haversine calculation to avoid complex PostGIS / GDAL / GEOS dependencies for prototype and test environments.

## Component Architecture

### 1. Haversine Math Utility (`assets/utils.py`)
Add a clean, standalone function `haversine_distance(lat1, lng1, lat2, lng2)`:
- Input: Latitude and Longitude floats for two points.
- Output: Distance in meters (float).
- Uses Earth radius $R = 6,371,000$ meters and standard trigonometric formulas.

### 2. Proximity Matching Function (`assets/services.py` or `assets/serializers.py`)
Function `get_or_create_asset_by_proximity`:
- Input: `coordinates` dict `{"lat": float, "lng": float}`, `label_val` str, `defaults` dict, `radius_meters` float = 1.0.
- Filter candidates: `Asset.objects.filter(label=label_val)`.
- Compare distances: For each candidate, calculate `haversine_distance(target_lat, target_lng, cand_lat, cand_lng)`.
- Pick the closest candidate where `distance <= radius_meters`.
- If matched: return `(closest_asset, False)`.
- If none match: create new `Asset` with `Asset.objects.create(...)` and return `(new_asset, True)`.

### 3. Serializer Integration (`assets/serializers.py`)
Replace `Asset.objects.get_or_create(...)` in `AssetCreateSerializer.create()` with the proximity matching call.

### 4. Unit Testing (`assets/tests.py`)
Add tests verifying:
- Asset captured within 0.5m radius matches existing asset.
- Asset captured beyond 1.0m radius creates a new asset.
- Coordinate edge cases (missing lat/lng or invalid numbers) are handled gracefully.

## Failure Modes & Risk Mitigation
- **Empty or null coordinates**: Handled by existing serializer validation before lookup.
- **Multiple assets within 1m radius**: Selects the asset with the minimum distance to the input coordinates.
