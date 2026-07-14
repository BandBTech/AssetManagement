# API Documentation: Asset Management

This documentation outlines the updated Asset API schema and application workflow for the React frontend developer. 

## Overview
The "Predictions" application has been entirely refactored and renamed to "Assets". 
The core functionality involves uploading an image, running it through a YOLO object detection pipeline, and intelligently determining whether the asset is brand new or already exists based on geographical coordinates and detected objects.

## Base URL
`/api/assets/`

---

## 1. List / Create Asset
**Endpoint:** `GET` / `POST` `/api/assets/`

### GET (List)
Fetches all assets in the database, ordered by newest first.

### POST (Create / Detect)
Used to upload an image and coordinates. The backend runs YOLO detection and checks if this asset already exists in the database using the combination of `coordinates` + `detected_objects`.

**Request Body (`multipart/form-data`)**
- `image` (File, Required): The captured image of the asset.
- `coordinates` (JSON String, Optional): e.g. `{"lat": 12.34, "lng": 56.78}`

**Response Logic:**
- **If it already exists:** Returns the existing asset from the database. `is_newly_created` will be `false`.
- **If it does not exist:** Creates a new asset and returns it. `is_newly_created` will be `true`. The metadata fields (`brand`, `asset_model`, etc.) will default to `null`.

**Sample Response (`201 Created` or `200 OK`):**
```json
{
    "id": 1,
    "original_image": "http://localhost:8000/media/uploads/originals/image.jpg",
    "predicted_image": "http://localhost:8000/media/uploads/predicted/image.jpg",
    "detected_objects": ["laptop"],
    "status": "PENDING",
    "created_at": "2026-07-13T10:00:00Z",
    "coordinates": {"lat": 12.34, "lng": 56.78},
    "brand": null,
    "asset_model": null,
    "purchase_price": null,
    "depreciation_rate": null,
    "maintenance_period": null,
    "is_newly_created": true
}
```

**Frontend React Flow:**
1. Send the `POST` request with the photo and location.
2. Check `response.data.is_newly_created`.
3. If `true`, prompt the user via a form to input the missing asset details (brand, model, price, etc.). Then send a `PATCH` request to `/api/assets/<id>/` to save these details.
4. If `false`, simply display the existing asset details to the user without prompting for new data.

---

## 2. Retrieve / Update Asset Details
**Endpoint:** `GET` / `PUT` / `PATCH` `/api/assets/<id>/`

Used to retrieve a specific asset or update its details (such as filling out the form for a newly created asset). 

**Editable Fields for PATCH (JSON):**
- `brand` (String, max 255)
- `asset_model` (String, max 255)
- `purchase_price` (Decimal/Float, max 12 digits, 2 decimal places)
- `depreciation_rate` (Decimal/Float, max 5 digits, 2 decimal places)
- `maintenance_period` (Integer, representing days)
- `coordinates` (JSON Object)

*Note: The `image` cannot be updated here, only textual metadata.*

---

## 3. Submit Prediction Feedback
**Endpoint:** `PUT` / `PATCH` `/api/assets/<id>/feedback/`

Used exclusively to update the `status` of an asset's automated prediction.

**Request Body (JSON)**
- `status` (String, Required): Must be exactly `"correct"` or `"incorrect"`. The backend handles converting this safely to the required database enum format.

**Sample Request:**
```json
{
    "status": "correct"
}
```
