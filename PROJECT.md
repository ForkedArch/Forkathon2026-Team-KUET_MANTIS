# Project: CampusShare KUET

## Architecture
CampusShare KUET is an integrated campus-wide asset sharing and borrowing platform for Khulna University of Engineering & Technology (KUET).
- **Backend**: FastAPI (Python) with SQLAlchemy ORM, SQLite database (`campus_share.db`), JWT authentication, and REST APIs.
- **Frontend**: React 18 with Vite, Tailwind CSS, and MapLibre GL JS providing a God's Eye campus map with a 700m perimeter ring, dual markers (emerald lend pins, red radar beacons), and an enterprise dashboard layout.
- **Data Flow**:
  1. User registers with `@stud.kuet.ac.bd` email -> backend decodes Batch, Dept, Roll -> issues JWT.
  2. User browses items on MapLibre map or dashboard list/table -> clicks pin/card to view hover popover.
  3. User creates item -> manual click-to-pinpoint mode on campus map -> saved with coordinates.
  4. Borrower requests item -> owner accepts -> handover started with OTP/QR -> borrower verifies OTP -> status "borrowed".
  5. Return completed -> KUET Karma updated: Owner +10, Borrower +5 (on-time) or -30 (late).
  6. Evaluator / Judge script runs against backend and frontend to score system on 20-point rubric.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Port `kuet_landmarks.json` | Move 21 campus landmarks and metadata into `backend/app/data/` | M1 | R1 |
| 2 | Serve `/api/landmarks` | Expose campus metadata (700m radius) and 21 zones | M1 | R1 |
| 3 | Seed Active Items | Seed 10 active student items from Tanvir into backend DB | M1 | R1 |
| 4 | Support JSON & Form Items API | Update `POST /api/items/` to accept both JSON and multipart/form-data | M1 | Survey |
| 5 | Resolve Schema Discrepancies | Add `transaction` to `BorrowRequestOut` & accept body or query in status PUT | M1 | Survey |
| 6 | Remove Duplicate Router | Delete orphaned `backend/app/routes/requests.py` | M1 | Survey |
| 7 | KUET Email Validation | Reject non-`@stud.kuet.ac.bd` registration with HTTP 400 | M1 | R3 |
| 8 | Automated Roll Decoder | Parse Batch, Dept, Roll from email prefix via regex `(\d{2})(\d{2})(\d{3})$` | M1 | R3 |
| 9 | Minimal Registration Form | Registration accepts only Full Name, Password, Email | M1, M2 | R3 |
| 10 | KUET Karma Base Score | New users initialized with 100 Base Karma | M1 | R4 |
| 11 | KUET Karma On-Time Transaction | Owner +10 Karma, Borrower on-time +5 Karma | M1 | R4 |
| 12 | KUET Karma Late Return | Borrower returning late deducts -30 Karma | M1 | R4 |
| 13 | MapLibre GL Integration | React map component with OSM raster tiles, center [89.5024, 22.9006], zoom 16.2 | M2 | R1, R2 |
| 14 | 700m Campus Perimeter Ring | Visual GeoJSON circle polygon and dashed halo over KUET boundary | M2 | R1, R2 |
| 15 | Dual-Marker Visuals | Emerald gradient lend pins & red pulsing radar borrow beacons | M2 | R1, R2 |
| 16 | Manual Click-to-Pin Mode | Crosshair cursor and click-to-pinpoint coordinate picker for new items | M2 | R1, R2 |
| 17 | Hover Cards / Popovers | Interactive popovers showing item specs, mini-location, owner info | M2 | R2 |
| 18 | Dashboard Layout | Left sidebar (Map, Items, Requests, Profile) and top action bar | M2 | R2 |
| 19 | Clean Light Theme | Modern enterprise aesthetic with Inter font and clean card borders | M2 | R2 |
| 20 | Frontend Karma & Decoder UI | Display karma badges and live decoded batch/dept/roll on registration | M2 | R3, R4 |
| 21 | Complete `Tanvir/` Deletion | Delete root `Tanvir/` folder after full verification | M3 | R1 |
| 22 | End-to-End User Flow | Add Item -> View Map/List -> Request -> Accept -> Handover -> Return | M3 | R5 |
| 23 | 20-Point Judge Rubric | `judge_rubric.py` automated test suite evaluating all 5 sections | M4 | R5 |
| 24 | Evaluator Score >= 18/20 | Achieve score >= 18/20 on automated evaluation loop | M4 | R5 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Backend Core & Data Migration | Port landmarks/seed data, fix schemas, implement KUET Roll Decoder (R3) & KUET Karma Protocol (R4) | none | DONE |
| M2 | Frontend Dashboard & MapLibre | DashboardLayout (sidebar, action bar), MapLibre map component, popovers, click-to-pin, registration update | M1 (contracts) | PLANNED |
| M3 | End-to-End Integration & Cleanup | Verify full user flow in React/FastAPI, delete `Tanvir/` folder completely | M1, M2 | PLANNED |
| M4 | Automated Evaluation Loop & Judge | Implement `judge_rubric.py` (20-point rubric), run evaluation loop to achieve >= 18/20 | M3 | PLANNED |
| M5 | Final Victory Verification | Independent audit, integrity checks, and completion report | M4 | PLANNED |

## Interface Contracts

### 1. `GET /api/landmarks`
- **Request**: No parameters
- **Response**:
  ```json
  {
    "success": true,
    "campus": {
      "name": "Khulna University of Engineering & Technology (KUET)",
      "center": [22.9006, 89.5024],
      "boundary_radius_meters": 700,
      "zoom_default": 16.5
    },
    "zones": [
      {
        "id": "cse_bldg",
        "name": "CSE Building",
        "category": "Academic",
        "coords": [22.9006, 89.5024]
      }
    ]
  }
  ```

### 2. `POST /api/auth/register`
- **Request Body**:
  ```json
  {
    "name": "Siddique Ahmed",
    "email": "siddique52507028@stud.kuet.ac.bd",
    "password": "secretpassword"
  }
  ```
- **Validation**: Email must end with `@stud.kuet.ac.bd`. Trailing 7 digits decoded into `batch="25"`, `dept="07"`, `roll="028"`.
- **Response**: User object with `batch`, `dept`, `roll`, and `karma: 100`.

### 3. `POST /api/transactions/return/{request_id}`
- **Response**:
  ```json
  {
    "message": "Item returned successfully",
    "karma_updated": {
      "owner_gain": 10,
      "borrower_change": 5,
      "is_on_time": true
    }
  }
  ```

### 4. `MapItemPin` (Frontend Contract)
- `id`: string/number
- `title`: string
- `type`: `"lend"` | `"borrow"`
- `category`: string
- `coords`: `[lng, lat]`
- `owner`: `{ name: string, roll: string, karma: number }`
- `condition`: string

## Code Layout
```
/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/
├── backend/
│   ├── app/
│   │   ├── data/
│   │   │   └── kuet_landmarks.json
│   │   ├── routes/
│   │   │   ├── auth.py          (Roll decoder, JWT, 100 base karma)
│   │   │   ├── items.py         (Item listing, filters, JSON & form support)
│   │   │   ├── borrow_requests.py (Status update bug fix, request handling)
│   │   │   ├── transactions.py  (Handover OTP/QR, Karma +10/+5/-30 calculation)
│   │   │   ├── landmarks.py     (Landmarks API)
│   │   │   └── chat.py
│   │   ├── models.py            (User with karma, Item with type/specs)
│   │   ├── schemas.py           (BorrowRequestOut with transaction, UserRegister)
│   │   ├── database.py
│   │   └── main.py
├── frontend/
│   ├── index.html               (MapLibre GL JS & CSS CDN tags)
│   ├── src/
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   └── DashboardLayout.jsx (Sidebar, Top bar, user footer)
│   │   │   ├── map/
│   │   │   │   └── GodsEyeMap.jsx      (MapLibre canvas, 700m ring, markers, HUD)
│   │   │   ├── items/
│   │   │   │   ├── ItemHoverCard.jsx   (Popovers with specs & mini-map)
│   │   │   │   └── AddItemModal.jsx    (Click-to-pinpoint modal)
│   │   │   └── requests/
│   │   ├── pages/
│   │   │   ├── Home.jsx         (Dashboard main view)
│   │   │   ├── Requests.jsx
│   │   │   ├── Profile.jsx      (Karma display)
│   │   │   └── Transaction.jsx  (Handover QR/OTP, return button)
│   │   ├── context/AuthContext.jsx
│   │   ├── api/client.js
│   │   └── App.jsx
├── DEPLOYMENT.md
└── PROJECT.md
```
