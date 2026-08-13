# React Admin Dashboard — API & Developer Guide

This document provides everything you need to build the React Admin Panel for the Asset Management system (ideal for vibe-coding with AI coding assistants).

---

## 1. Overview & Setup

- **Base URL:** `http://localhost:8000/api/admin/` (or your production API host)
- **Auth Strategy:** SimpleJWT (Bearer Token in `Authorization` header)
- **Permissions:** Strictly Superuser (`is_superuser=True`)

### Authentication Flow
1. User logs in at `/api/auth/login/` with email and password.
2. Store the returned `access` token in memory / `localStorage`.
3. Include header in all admin API requests:
   ```http
   Authorization: Bearer <access_token>
   ```

---

## 2. API Endpoints Reference

### 📊 1. Dashboard Metrics
- **Endpoint:** `GET /api/admin/assets/stats/`
- **Description:** Returns aggregate counts for dashboard metric cards.
- **Response Example (200 OK):**
  ```json
  {
    "total_assets": 42,
    "pending_count": 5,
    "correct_count": 35,
    "incorrect_count": 2,
    "maintenance_due_count": 8
  }
  ```

---

### 📦 2. Asset Management (CRUD)

| Method | URL Path | Description |
| :--- | :--- | :--- |
| `GET` | `/api/admin/assets/` | List assets (supports search, filter, sorting, pagination) |
| `POST` | `/api/admin/assets/` | Create a new asset record |
| `GET` | `/api/admin/assets/{id}/` | Get single asset details |
| `PUT / PATCH` | `/api/admin/assets/{id}/` | Update any field of an asset |
| `DELETE` | `/api/admin/assets/{id}/` | Delete an asset |

#### Query Parameters for `GET /api/admin/assets/`
- `search`: Search across `maker`, `model_no`, `notes` (e.g. `?search=Yamaha`)
- `status`: Filter by status (`PENDING`, `CORRECT`, `INCORRECT`)
- `year`: Filter by manufacturing year (e.g. `?year=2023`)
- `ordering`: Sort by field (e.g. `?ordering=-created_at`, `?ordering=next_maintenance_due`, `?ordering=-price_jpy`)

---

## 3. Data Schema & Types (TypeScript Ready)

```typescript
export type AssetStatus = 'PENDING' | 'CORRECT' | 'INCORRECT';

export interface Coordinates {
  lat: number;
  lng: number;
  [key: string]: any;
}

export interface Asset {
  id: number;
  status: AssetStatus;
  original_image: string | null;
  predicted_image: string | null;
  label: string | string[] | Record<string, any> | null;
  conf: number | number[] | Record<string, any> | null;
  maker: string | null;
  model_no: string | null;
  year: number | null;
  price_jpy: string | null;
  size: string | null;
  maintenance_cycle: number | null; // in days
  last_maintenance_date: string | null; // YYYY-MM-DD
  next_maintenance_due: string | null; // YYYY-MM-DD (auto-calculated)
  notes: string | null;
  created_at: string; // ISO DateTime
  coordinates: Coordinates;
}

export interface AssetStats {
  total_assets: number;
  pending_count: number;
  correct_count: number;
  incorrect_count: number;
  maintenance_due_count: number;
}
```

---

## 4. Example HTTP Request Snippets

### Fetch Dashboard Stats
```javascript
async function fetchAdminStats(token) {
  const res = await fetch('http://localhost:8000/api/admin/assets/stats/', {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  return await res.json();
}
```

### Update Asset Status & Maintenance Date
```javascript
async function updateAsset(token, assetId, updateData) {
  const res = await fetch(`http://localhost:8000/api/admin/assets/${assetId}/`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(updateData)
  });
  return await res.json();
}

// Example usage:
// updateAsset(token, 12, { status: "CORRECT", last_maintenance_date: "2026-08-13", maintenance_cycle: 30 })
```

---

## 5. Recommended React Admin UI Blueprint

### Layout Structure
- **Sidebar**:
  - Dashboard (Home)
  - Asset Inventory Table
  - Maintenance Schedule
- **Header**:
  - Current User / Role badge (`SUPERUSER`)
  - Logout Button
- **Main View 1: Dashboard Home**
  - 4 Stat Cards: `Total Assets`, `Pending Review`, `Correct Assets`, `Maintenance Due (< 30 days)`
  - Quick action table of recent pending assets.
- **Main View 2: Asset Inventory Grid / Table**
  - Search bar + Status Filter dropdown (`All`, `Pending`, `Correct`, `Incorrect`).
  - Table Columns: Image thumbnail, Label, Maker / Model, Status Badge, Price (JPY), Next Maintenance Due, Actions (Edit / Delete).
  - Edit Drawer / Modal for inline editing of asset maker, model, notes, and maintenance schedules.
