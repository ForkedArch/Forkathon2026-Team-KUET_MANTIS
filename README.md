# CampusShare KUET

CampusShare KUET is a campus-only marketplace for sharing, borrowing, and
coordinating the handover of student supplies at Khulna University of
Engineering & Technology (KUET). Students can publish items they are willing
to lend, broadcast items they need, find listings on a God's Eye campus map,
and complete an exchange with a one-time OTP or QR code.

Built by **KUET_MANTIS** for the ForkedArch Freshers Hackathon 2026.

## Why CampusShare?

Students often need a calculator, charger, adapter, lab tool, book, or other
small item for only a few hours. Existing group chats make those exchanges
hard to search, difficult to coordinate, and impossible to track reliably.
CampusShare provides a structured KUET student network where:

- listings are searchable by category, type, zone, owner, and description;
- the map shows where items are available within a 700 m KUET perimeter;
- requests have clear pending, accepted, declined, borrowed, and completed
  states;
- owner and borrower identity is tied to a KUET student email;
- handovers are verified in person with a short-lived OTP/QR flow; and
- reliable lending and returning is rewarded through KUET Karma.

## Features

### Student identity and authentication

- Registration accepts only `@stud.kuet.ac.bd` addresses.
- The final seven digits of the email local part are decoded into batch,
  department, and roll (`BB DD RRR`).
- New accounts start with 100 Karma and receive a JWT access token after login.
- Passwords are stored as bcrypt hashes; tokens are sent as Bearer tokens.

### Campus listings

- Create lending listings or borrow-demand beacons.
- Add descriptions, specifications, condition, tags, image, zone, and map
  coordinates.
- Upload JPEG, PNG, or WEBP item images up to 5 MB.
- Search by title, description, specifications, owner name, or department.
- Filter by category, listing type, zone, and availability.
- Edit or delete items owned by the authenticated student.

### God's Eye map

- MapLibre GL map centered on KUET using OpenStreetMap raster tiles.
- Interactive 700 m campus perimeter ring.
- Emerald markers for lending listings and red pulsing markers for borrow
  beacons.
- Click-to-pin mode for assigning a precise location while adding an item.
- Campus landmarks and exchange zones are served by the backend.

### Borrowing workflow

1. A borrower opens an available listing and submits duration, purpose, pickup
   zone, and an optional message.
2. The owner accepts or declines the request. Accepting makes the item
   unavailable and automatically declines other pending requests for it.
3. The owner starts the handover and receives a four-digit OTP plus a QR code.
4. The borrower verifies the OTP in person. The transaction becomes
   `borrowed`.
5. The borrower confirms the return. The item becomes available again and the
   request becomes `completed`.

Accepted requests also unlock a request-specific chat between the owner and
borrower. The frontend polls for new messages every three seconds.

### KUET Karma protocol

| Event | Karma change |
| --- | ---: |
| Account registration | 100 base Karma |
| Completed lending transaction | Owner +10 |
| On-time return | Borrower +5 |
| Late return | Borrower -30 |

The profile view displays the current score, completed exchanges, and the
rules above.

## Architecture

```text
React 18 + Vite + Tailwind CSS
        |
        | Axios / JSON and multipart requests
        v
FastAPI REST API
        |
        +-- JWT authentication and bcrypt passwords
        +-- SQLAlchemy ORM
        +-- SQLite (default; configurable database URL)
        +-- Local image uploads
        +-- QR code generation
        |
        v
  Users, items, requests, transactions, messages
```

### Repository layout

```text
.
├── backend/
│   ├── app/
│   │   ├── data/kuet_landmarks.json
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── borrow_requests.py
│   │   │   ├── chat.py
│   │   │   ├── items.py
│   │   │   ├── landmarks.py
│   │   │   └── transactions.py
│   │   ├── utils/
│   │   │   ├── file_upload.py
│   │   │   └── qr_code.py
│   │   ├── auth.py
│   │   ├── database.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   └── seed.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── context/AuthContext.jsx
│   │   ├── pages/
│   │   ├── api/client.js
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   ├── capacitor.config.ts
│   ├── android/                 # Generated Capacitor Android project
│   └── .env.example
├── PROJECT.md
├── CONTRIBUTING.md
└── README.md
```

## Requirements

- Python 3.10 or newer
- Node.js 18 or newer and npm
- A modern browser with JavaScript enabled

The frontend loads MapLibre GL JS, Turf.js, and OpenStreetMap tiles from
external resources at runtime. An internet connection is therefore needed for
the full map experience.

## Local setup

### 1. Clone the repository

```bash
git clone https://github.com/ForkedArch/Forkathon2026-Team-KUET_MANTIS.git
cd Forkathon2026-Team-KUET_MANTIS
```

### 2. Configure and run the backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000`. FastAPI's interactive
documentation is available at `http://localhost:8000/docs`, and the health
check is `http://localhost:8000/health`.

The default development configuration uses SQLite at
`backend/campus_share.db`, creates the database tables at startup, and uses a
development JWT key. Before deploying, set `ENVIRONMENT` to a non-development
value and provide a strong `SECRET_KEY`.

### 3. Optionally seed demo data

With the backend virtual environment active and the working directory set to
`backend`:

```bash
python -m app.seed
```

The seed script adds sample KUET students and active listings from
`backend/app/data/kuet_landmarks.json`. Seed users use the default password
`kuet1234`; change or remove demo data before using a shared deployment.

### 4. Configure and run the frontend

In a second terminal:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open the URL printed by Vite, normally `http://localhost:5173`.

The frontend reads the backend URL from `VITE_API_URL`:

```dotenv
VITE_API_URL=http://localhost:8000/api
```

For a production build:

```bash
npm run build
npm run preview
```

### 5. Run the Android app in parallel

The Android target reuses the same React/Vite frontend through Capacitor. The
browser workflow above remains unchanged.

#### Prerequisites

- Android Studio with an Android SDK and emulator, or a USB-debuggable Android
  device
- A Java/Android toolchain supported by the installed Capacitor version
- A backend URL reachable from the emulator or device

From `frontend/`, install dependencies and create/synchronize the native
project:

```bash
npm install
npm run android:sync
```

Open the project in Android Studio or run it on an available device:

```bash
npm run android:open
npm run android:run
```

`android:sync` runs the normal Vite production build first, then copies
`dist/` into the Android project. After changing frontend code, run it again
before testing the Android app.

For local API development, use the correct URL for the device:

```dotenv
# Android emulator
VITE_API_URL=http://10.0.2.2:8000/api

# Physical device on the same LAN (replace with the computer's LAN address)
VITE_API_URL=http://192.168.1.10:8000/api
```

When testing from a physical device, bind the development API to the LAN
interface (for example, `uvicorn app.main:app --host 0.0.0.0 --reload`) and
allow the port through the development machine's firewall. If Android blocks
cleartext HTTP on a particular device, use an HTTPS development tunnel; keep
HTTP disabled for production.

`localhost` inside an Android app refers to the Android device/emulator, not
the development computer. For a release build, use a deployed HTTPS API URL,
for example `https://api.example.com/api`, and include the web origin and
`http://localhost` in the backend `ALLOWED_ORIGINS` value. Do not ship a
development SQLite database, local upload directory, or backend secret in the
APK.

To create a debug APK, open the generated `frontend/android/` project in
Android Studio and use **Build > Build App Bundle(s) / APK(s) > Build APK(s)**.
Release APK/AAB builds must be signed with a keystore kept outside the
repository; configure signing only in the local/CI Android build environment.

## Configuration

### Backend environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `ENVIRONMENT` | `development` | Allows the development JWT fallback only in development |
| `SECRET_KEY` | development fallback | JWT signing key; required outside development |
| `ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access-token lifetime |
| `DATABASE_URL` | SQLite in `backend/campus_share.db` | SQLAlchemy database URL |
| `ALLOWED_ORIGINS` | `http://localhost:5173,http://localhost` | Comma-separated browser and Android CORS origins |
| `UPLOAD_DIR` | `./uploads` | Directory for uploaded item images |

Do not commit `.env` files, credentials, database files, uploads, or build
output. The repository's `.gitignore` already excludes these local artifacts.

## API overview

All application endpoints are prefixed with `/api`.

| Area | Endpoints | Authentication |
| --- | --- | --- |
| Auth | `POST /auth/register`, `POST /auth/login`, `GET /auth/me`, `GET /auth/current` | Register/login public; profile protected |
| Items | `GET /items`, `GET /items/{id}`, `POST /items`, `PUT /items/{id}`, `DELETE /items/{id}` | Read public; mutations protected where applicable |
| Landmarks | `GET /landmarks` | Public |
| Requests | `POST /requests`, `GET /requests/me`, `PUT /requests/{id}/status` | Protected |
| Transactions | `POST /transactions/start`, `POST /transactions/verify`, `POST /transactions/return/{id}` | Protected |
| Chat | `GET/POST /chat/{request_id}/messages` | Protected; request participants only |

`POST /items` accepts either JSON or `multipart/form-data`. Multipart requests
can include an image file. See the generated OpenAPI documentation at
`/docs` for request and response schemas.

## Frontend routes

| Route | View |
| --- | --- |
| `/login` | Student login |
| `/register` | KUET registration with live email decoder |
| `/` | God's Eye campus map |
| `/items` | Searchable listing grid |
| `/item/:id` | Listing details |
| `/add` | Add-item view |
| `/requests` | Incoming and outgoing requests |
| `/transaction/:requestId` | OTP/QR handover and return |
| `/chat/:requestId` | Request chat |
| `/profile` | Student identity and Karma record |

## Development notes

- The backend uses SQLAlchemy models and performs lightweight schema
  migrations in `app/database.py` on startup.
- The default database is local SQLite; use `DATABASE_URL` for another
  SQLAlchemy-supported database.
- Images are served from `/uploads` and are restricted to JPEG, PNG, and WEBP
  files with a 5 MB limit.
- The map uses `[89.5024, 22.9006]` as the KUET center in
  `[longitude, latitude]` order. Landmark data uses `[latitude, longitude]`
  coordinates, as defined in the source JSON.
- The project currently provides build scripts for the frontend and API
  documentation through FastAPI. Add automated tests alongside new behavior
  when extending the application.

## Contributing

Please read [CONTRIBUTING.md](./CONTRIBUTING.md) before opening a change.
Create a branch, keep changes focused, test the affected backend or frontend
surface, and use a clear commit message.

## Team

| Name | Roll | Department | GitHub |
| --- | --- | --- | --- |
| Anupoma Sharmin Anonya | 2K2507009 | CSE | [@anonya25-1](https://github.com/anonya25-1) |
| Mugdha Sarkar Anik | 2K2507030 | CSE | [@mugdha-sarkar81](https://github.com/mugdha-sarkar81) |
| Tanvir Siddique | 2K2507028 | CSE | [@siddiquetanvir](https://github.com/siddiquetanvir) |

## License

This project is released under the [MIT License](./LICENSE).
