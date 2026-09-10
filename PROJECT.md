# Project: KUET CampusShare Platform Revision & Production Login Fix

## Architecture
KUET CampusShare is a student-exclusive campus sharing economy platform designed specifically for Khulna University of Engineering & Technology (KUET).
- **Frontend Architecture**: Single Page Application built with React 18, Vite, Tailwind CSS, TanStack Query v5, and MapLibre GL JS with Turf.js. Deployed to Vercel (or Render Static Site).
- **Backend Architecture**: REST API built with Python FastAPI, Uvicorn ASGI server, SQLAlchemy 2.0 ORM, and Pydantic v2. Deployed to Render Web Service.
- **Database Layer**: Relational database with dual support for SQLite (local/container with persistent volume) and PostgreSQL (cloud e.g. Neon on Render).
- **Security & Identity**: Access strictly restricted to `@stud.kuet.ac.bd` emails. The 7-digit roll format `YYDDRRR` is decoded into Batch (`YY`), Department acronym (`DD` -> CSE, EEE, CE, ME, etc.), and Roll (`RRR`). JWT tokens (HS256) authenticate API requests.
- **Trust & Karma Protocol**: 100 Base Karma upon registration. Transactions award +10 to lender, +5 to on-time borrower, and penalize -30 for late returns.
- **Physical Handover**: 4-digit OTP exchange and QR code verification to securely confirm physical item transfer.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | KUET Email Domain Gatekeeper | Strict `@stud.kuet.ac.bd` domain restriction; non-KUET emails rejected with HTTP 400 | M1 | survey |
| 2 | 7-Digit Roll Decoder | Automatically extracts Batch (`YY`), Dept code (`DD`), and Roll (`RRR`) from student email local part | M1 | survey |
| 3 | Department Acronym Mapping | Maps all 31 KUET department codes and aliases (01-31) to official acronyms (CE, EEE, CSE, ME, etc.) | M1 | survey |
| 4 | Minimal Registration API | Registers student with name, email, password; auto-populates batch, dept, roll, karma | M1 | survey |
| 5 | Base Karma Award | Initializes newly registered students with 100 Base Karma and 100.0 trust score | M1 | survey |
| 6 | Student Authentication & JWT | Authenticates credentials and issues HS256 JWT access tokens; handles `/api/auth/me` | M1 | survey |
| 7 | DB Migration & Directory Auto-Creation | Automatically creates parent directories for SQLite and runs startup schema migrations | M1 | survey |
| 8 | Cloud DB Connection Resilience | Adds `pool_pre_ping=True` and connection error recovery for cloud PostgreSQL | M1 | survey |
| 9 | Render Deployment Configuration | Robust `render.yaml` with free tier compatibility, SECRET_KEY generation, and proper environment variables | M1 | survey |
| 10 | Vercel API Reverse Proxy Rewrite | Adds `/api/:path*` reverse proxy rule in `vercel.json` before SPA `/(.*)` catch-all to prevent HTML rewrite collision | M1 | survey |
| 11 | Item Listings & Demand Beacons API | CRUD endpoints for items (`type: 'lend'` and `type: 'borrow'`), specs, condition, and status | M2 | survey |
| 12 | Campus Landmarks & Coordinates | Geolocation coordinates for items within 700m KUET campus perimeter and 21 campus zones | M2 | survey |
| 13 | Item Save & Report APIs | Endpoints for bookmarking saved items and submitting community moderation reports | M2 | survey |
| 14 | Borrow Requests Lifecycle API | Request creation, duplicate prevention, self-borrowing guard, owner accept/decline, competing request auto-decline | M2 | survey |
| 15 | Physical Handover Verification | 4-digit OTP generation, QR code base64 generation, and OTP verification transitioning item to 'borrowed' | M2 | survey |
| 16 | Item Return & Karma Calculation | Return confirmation endpoint checking on-time return; applies +10 lender, +5 on-time borrower, -30 late borrower | M2 | survey |
| 17 | Messaging & Conversations API | Direct 1:1 chat endpoints and request-linked chat threads; unread message tracking | M2 | survey |
| 18 | In-App Notifications API | Automated notifications on borrow requests, status changes, and chat messages | M2 | survey |
| 19 | Peer Reviews & Ratings API | 1-5 star rating and feedback submission after transaction completion | M2 | survey |
| 20 | Frontend API Client Hardening | Axios client with 401 interceptor (auto-logout), cold-start timeout handling, and informative error toasts | M3 | survey |
| 21 | Purpose-Aligned Auth UI | Login and registration pages with live KUET roll/dept/batch preview, format hints, and error handling | M3 | survey |
| 22 | CampusShare Branding & Copy Alignment | Update hero section, titles, navigation, and badges to reflect official KUET CampusShare identity | M3 | survey |
| 23 | Item Detail Scroll & Clipping Fix | Add `h-full overflow-y-auto` to `ItemDetail.jsx` so action buttons are accessible on all screens | M3 | survey |
| 24 | Image URL Normalization Helper | Standardize image resolution in `ItemCard.jsx` and `ItemDetail.jsx` to handle relative, uploaded, and absolute URLs | M3 | survey |
| 25 | AllItems & Filter Responsiveness | Add department filter dropdown and make Type / Category filters accessible on mobile viewports | M4 | survey |
| 26 | Handover & Return Navigation in Requests | Keep `/transaction/:id` link visible when request status is `'borrowed'` with clear "Confirm Return" button | M4 | survey |
| 27 | Mobile Chat Master-Detail UI | Responsive stacked layout in `Chat.jsx` with mobile toggle and back button for viewports <768px | M4 | survey |
| 28 | Student Profile Enhancements | Profile tabs for "My Active Listings" and "Borrowed Items History", plus Karma Tier badges | M4 | survey |
| 29 | Comprehensive E2E Test Suite (Tiers 1-4) | Opaque-box requirement-driven test suite covering all features, boundaries, combinations, and workflows | M5 | survey |
| 30 | Adversarial Coverage Hardening (Tier 5) | White-box stress testing, edge cases, and robustness hardening verified by Challenger | M5 | survey |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Backend DB, Migrations, Deployment & Auth | Database resilience, directory auto-creation, `render.yaml`, `vercel.json` API proxy, `@stud.kuet.ac.bd` domain gate, roll decoder, and Auth APIs | none | DONE |
| 2 | Backend Core Services & Karma Engine | Item CRUD, Borrow Requests lifecycle, OTP/QR Handover, Return & Karma calculation, Chat & Notifications | M1 | DONE |
| 3 | Frontend Purpose Alignment, Auth & Base Fixes | API client 401 interceptor & timeouts, Purpose alignment & branding, Auth UI with live preview, ItemDetail scroll fix, Image URL helper | M1 | IN_PROGRESS |
| 4 | Frontend Core Features Revision & UI/UX Polish | Mobile chat master-detail, Requests return button fix, Mobile filters in AllItems, Profile Active Listings & History tabs | M2, M3 | PLANNED |
| 5 | Final E2E Test Suite Pass & Adversarial Hardening | Pass 100% of E2E test suite (Tiers 1-4), then execute Phase 2 Adversarial Coverage Hardening (Tier 5) | M4 | PLANNED |

## Interface Contracts

### Frontend ↔ Backend Auth Contract
- `POST /api/auth/register`:
  - Request: `{ "name": "...", "email": "...@stud.kuet.ac.bd", "password": "..." }`
  - Response (200): `{ "id": int, "name": str, "email": str, "dept": str, "batch": str, "roll": str, "karma": 100, "trust_score": 100.0, "total_lends": 0, "total_borrows": 0, "created_at": str }`
  - Rejections (400): Non-KUET domain, invalid roll suffix, duplicate email, duplicate roll in same batch/dept.
- `POST /api/auth/login`:
  - Request: `{ "email": "...@stud.kuet.ac.bd", "password": "..." }`
  - Response (200): `{ "access_token": str, "token_type": "bearer", "user": UserOut }`
  - Rejections (401): `"Incorrect email or password"`
- `GET /api/auth/me`:
  - Header: `Authorization: Bearer <access_token>`
  - Response (200): `UserOut`

### Frontend ↔ Backend Items Contract
- `GET /api/items`:
  - Query params: `category`, `type` (`lend` | `borrow`), `zone`, `zone_id`, `search`, `available_only`
  - Response (200): `List[ItemOut]`
- `POST /api/items`:
  - Request: `ItemCreate` or FormData (title, category, type, description, specs, condition, zone, latitude, longitude, tags)
  - Response (201): `{ "success": true, "item": ItemOut }`

### Frontend ↔ Backend Borrow & Handover Lifecycle Contract
- `POST /api/requests`:
  - Header: Bearer token (borrower)
  - Request: `{ "item_id": int, "duration_hours": int, "purpose": str, "pickup_zone": str, "message": str }`
  - Response (200): `BorrowRequestOut` (`status: "pending"`)
- `PUT /api/requests/{id}/status`:
  - Header: Bearer token (owner)
  - Request: `{ "status": "accepted" | "declined" }`
  - Side effect on accepted: Sets `item.is_available = false`, declines competing pending requests for item.
- `POST /api/transactions/start`:
  - Header: Bearer token (owner)
  - Request: `{ "request_id": int }`
  - Response (200): `{ "otp": "XXXX", "qr_code": "data:image/png;base64,...", "transaction_id": int }`
- `POST /api/transactions/verify`:
  - Header: Bearer token (borrower)
  - Request: `{ "request_id": int, "otp": "XXXX" }`
  - Side effect: Marks transaction `borrowed`, sets `borrowed_at = now`, clears OTP.
- `POST /api/transactions/return/{request_id}`:
  - Header: Bearer token (borrower)
  - Side effect: Marks transaction `returned`, restores `item.is_available = true`, computes karma delta (+10 lender, +5 or -30 borrower).

### Frontend ↔ Backend Chat Contract
- `GET /api/chat/conversations`:
  - Header: Bearer token
  - Response (200): `List[ConversationOut]`
- `GET /api/chat/direct/{other_user_id}`:
  - Header: Bearer token
  - Response (200): `List[MessageOut]` (marks incoming messages `is_read = true`)
- `POST /api/chat/direct/{other_user_id}`:
  - Header: Bearer token
  - Request: `{ "content": str, "item_id": Optional[int] }`
  - Response (200): `MessageOut`

## Code Layout
```
/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI app, CORS, static mount, lifespan hooks
│   │   ├── database.py                 # SQLAlchemy engine, session generator, migrations
│   │   ├── models.py                   # 9 relational models (User, Item, Request, Transaction, Chat, etc.)
│   │   ├── schemas.py                  # Pydantic v2 models for request/response serialization
│   │   ├── auth.py                     # Password hashing, JWT creation/decoding, get_current_user
│   │   ├── seed.py                     # Seed data for campus items and demo student profiles
│   │   └── routes/
│   │       ├── auth.py                 # Register, login, me, KUET roll decoder
│   │       ├── items.py                # Item listing, search, save, report
│   │       ├── borrow_requests.py      # Borrow requests lifecycle management
│   │       ├── transactions.py         # OTP/QR handover, return confirmation, Karma logic
│   │       ├── chat.py                 # Direct and request-linked chat messages
│   │       ├── notifications.py        # In-app notifications
│   │       ├── reviews.py              # Peer ratings and reviews
│   │       └── landmarks.py            # KUET campus zones and perimeter coordinates
│   ├── requirements.txt
│   ├── Dockerfile
│   └── campus_share.db
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── vercel.json                     # Vercel SPA routing and /api reverse proxy
│   └── src/
│       ├── main.jsx
│       ├── App.jsx                     # Root router, Auth views, PrivateRoute
│       ├── api/client.js               # Axios instance, baseURL resolution, 401 interceptor
│       ├── context/AuthContext.jsx     # User authentication state
│       ├── utils/dept.js               # KUET 31 department definitions and formatters
│       ├── components/
│       │   ├── layout/                 # DashboardLayout, Sidebar, TopActionBar
│       │   ├── map/                    # GodsEyeMap, campus perimeter ring
│       │   ├── items/                  # ItemCard, ItemHoverCard, AddItemModal
│       │   └── requests/               # RequestModal
│       └── pages/
│           ├── Home.jsx                # Landing page, God's Eye Map, How it works
│           ├── AllItems.jsx            # Browse listings and demand beacons
│           ├── AddItem.jsx             # Post new item or beacon
│           ├── ItemDetail.jsx          # Item details, borrow action, report
│           ├── Requests.jsx            # Incoming and outgoing requests management
│           ├── Transaction.jsx         # OTP/QR verification, return confirmation
│           ├── Chat.jsx                # Student-to-student messaging
│           └── Profile.jsx             # Student profile, karma score, listings, history
├── render.yaml                         # Blueprint for backend web service & frontend static site
├── vercel.json                         # Root Vercel configuration
├── checklist_judge.py                  # Automated 20-criteria validation judge
└── tests/                              # E2E test suite (Dual Track)
```
