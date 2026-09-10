# KUET CampusShare — Test Infrastructure Specification (TEST_INFRA.md)

## 1. Test Architecture & Design Philosophy

The KUET CampusShare testing infrastructure implements a comprehensive, opaque-box, requirement-driven test suite designed specifically for the Khulna University of Engineering & Technology (KUET) student-exclusive sharing economy platform.

### Core Testing Principles
1. **Opaque-Box Requirement-Driven**: Tests interact strictly via public HTTP contracts, request bodies, query parameters, and status codes as defined in `PROJECT.md` and `ORIGINAL_REQUEST.md`. Internal implementation details remain encapsulated.
2. **Zero-Socket In-Memory ASGI Execution**: Rather than relying on external networking, port binding, or brittle TCP sockets, the test runner utilizes an in-memory ASGI client (`tests/asgi_client.py`). This passes ASGI scopes directly to the FastAPI application, exercising the entire middleware, routing, Pydantic v2 validation, and dependency injection pipeline.
3. **Hermetic State Isolation**: Every single test case initializes an independent in-memory SQLite database using `StaticPool` (`sqlite:///:memory:`), completely isolated from the development database (`campus_share.db`). Upon teardown, schemas are dropped, engines disposed, and FastAPI dependency overrides cleared.
4. **Authoritative Expected Output Derivation**: Expected outputs (e.g. 100 Base Karma, 7-digit roll decoding, +10/-30 Karma engine deltas, 4-digit OTP format, 700m campus perimeter geofence) are derived directly from the project specification.

---

## 2. 4-Tier Test Taxonomy & Methodology

The test suite is structured into four progressive tiers providing exhaustive coverage across isolation, boundaries, integration, and real-world workflows:

| Tier | Category | Minimum Required | Implemented Tests | Focus Area |
|------|----------|------------------|-------------------|------------|
| **Tier 1** | Feature Coverage | >= 5 per feature | **55 tests** | Happy-path isolation tests for all 11 core functional modules |
| **Tier 2** | Boundary & Corner Cases | >= 5 per area | **55 tests** | Extreme inputs, invalid domains, malformed rolls, coordinates, permissions |
| **Tier 3** | Cross-Feature Combinations | Pairwise coverage | **7 tests** | Multi-step integration pipelines across requests, handover, chat, and reviews |
| **Tier 4** | Real-World Scenarios | Complete workflows | **5 tests** | Multi-student campus workflows (inter-department loans, overdue penalties) |
| **TOTAL** | **Full E2E Suite** | **>= 115 tests** | **122 tests** | **100% Pass Rate (Exit Code 0)** |

---

## 3. Directory Layout & Test Artifacts

```
tests/
├── __init__.py                  # Package initialization
├── asgi_client.py               # Zero-socket in-memory FastAPI ASGI test client
├── base.py                      # BaseE2ETestCase harness (DB isolation, auth/item helpers)
├── test_tier1_features.py       # Tier 1: 55 feature coverage tests
├── test_tier2_boundaries.py     # Tier 2: 55 boundary & corner case tests
├── test_tier3_combinations.py   # Tier 3: 7 cross-feature combination tests
├── test_tier4_scenarios.py      # Tier 4: 5 real-world multi-student scenarios
└── run_tests.py                 # Standalone test runner with rich summary metrics
```

---

## 4. Test Harness & Technical Implementation

### 4.1 In-Memory ASGI Test Client (`tests/asgi_client.py`)
- Emulates asynchronous ASGI HTTP requests (`GET`, `POST`, `PUT`, `DELETE`).
- Sets headers, parses JSON payloads, handles form encodings, and formats query strings.
- Captures status codes, response headers, raw content bytes, and decoded JSON objects.
- Eliminates external `httpx` or network socket dependencies while maintaining 100% fidelity with FastAPI and Starlette.

### 4.2 Isolated Database Lifecycle (`tests/base.py`)
```python
# Isolated in-memory database with shared static pool for concurrent thread safety
self.test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
models.Base.metadata.create_all(bind=self.test_engine)
self.TestSession = sessionmaker(autocommit=False, autoflush=False, bind=self.test_engine)

def override_get_db():
    db = self.TestSession()
    try:
        yield db
    finally:
        db.close()

self.app.dependency_overrides[database.get_db] = override_get_db
```

### 4.3 Reusable Student Action Helpers
- `register_user(...)`: Posts to `/api/auth/register`.
- `login_user(...)`: Posts to `/api/auth/login`.
- `register_and_login(...)`: Registers, retrieves Bearer JWT, and prepares Authorization headers.
- `create_item(...)`: Posts item listing with category, condition, specs, and GPS coordinates.
- `create_borrow_request(...)`: Submits formal request with duration and pickup location.

---

## 5. Detailed Test Inventory by Tier

### Tier 1: Feature Coverage (55 Tests)
- **Auth & Identity (5 tests)**: Registration success, JWT issuance, `/api/auth/me`, `/api/auth/current` alias, public profile `/api/auth/user/{id}`.
- **Roll Decoding & Department Mapping (5 tests)**: CSE (`07`), EEE (`03`), CE (`01`), ME (`05`), Specialized departments (`09` ECE, `11` IEM, `15` BME, `25` MTE, `29` LE).
- **Item Listings & Demand Beacons (5 tests)**: Lend item creation, Borrow beacon creation, Item catalog listing, Detailed item specification query, Owner item update & deletion.
- **Search & Filtering Engine (5 tests)**: Title keyword search, Hardware specs search, Category filter (`Books`), Type filter (`lend`), Campus zone filter (`cse_bldg`).
- **Borrow Requests Lifecycle (5 tests)**: Request submission, User requests retrieval (`/api/requests/me`), Owner request acceptance, Owner request decline, Competing request auto-decline.
- **Physical Handover Verification (5 tests)**: 4-digit OTP generation, QR code base64 generation, OTP verification, `borrowed_at` timestamp setting, Sensitive OTP clearing upon handover.
- **Item Return & Karma Engine (5 tests)**: On-time return confirmation, Availability restoration, +10 Karma lender award, +5 Karma on-time borrower award, -30 Karma late return penalty.
- **Messaging & Conversations (5 tests)**: 1:1 direct chat dispatch, Conversation inbox listing, Unread counter increment, Read receipt upon thread open, Request-linked chat messages.
- **In-App Notifications (5 tests)**: Student notification feed, Direct message notification trigger, Peer review notification trigger, Single notification read receipt, Batch read-all mark.
- **Peer Reviews & Ratings (5 tests)**: 1-5 star peer review submission, User reviews list retrieval, Reviewer profile embedding, Rating boundary validation, Chronological ordering.
- **Campus Landmarks & Coordinates (5 tests)**: Landmarks API retrieval, Campus center coordinates `[22.9006, 89.5024]`, 700m perimeter definition, 21 campus zones coverage, Boundary coordinates validation (`22.88-22.92 N`, `89.48-89.52 E`).

### Tier 2: Boundary & Corner Cases (55 Tests)
- **Email Domain Rejections (5 tests)**: `@gmail.com` rejection, `@kuet.ac.bd` faculty domain rejection, `@buet.ac.bd` external institution rejection, `@evil.stud.kuet.ac.bd` subdomain spoof rejection, missing `@` symbol rejection.
- **Roll Decoding Corner Cases (5 tests)**: Missing 7-digit roll rejection, Alphanumeric roll suffix rejection, Short 6-digit roll rejection, Unrecognized department code rejection, Leading/trailing whitespace normalization.
- **Auth Security & Token Boundaries (5 tests)**: Incorrect password 401, Non-existent user 401, Missing Authorization header 403, Malformed JWT token 401, Tampered JWT signature 401.
- **Composite Roll & Email Collisions (5 tests)**: Duplicate email rejection 400, Duplicate roll in same batch/dept rejection 400, Same roll in different batch allowed, Same roll in different dept allowed, Case-insensitive email collision rejection 400.
- **Item Boundaries & Permissions (5 tests)**: Blank/whitespace title rejection 422, Invalid type rejection 422, Non-owner update rejection 403, Non-owner delete rejection 403, Non-existent item 404.
- **Campus Geofence Calculations (5 tests)**: CSE building coordinates inside 700m boundary, Teligati mess zone coordinates (~660m) inside 700m boundary, Coordinates >3km outside perimeter identification, Null coordinates handling, Non-existent zone query graceful handling.
- **Borrow Requests Boundaries & Guards (5 tests)**: Self-borrowing guard 400, Duplicate pending request guard 400, Request on unavailable item guard 400, Non-existent item request 404, Non-owner request status modification 403.
- **Handover & OTP Boundaries (5 tests)**: Invalid 4-digit OTP rejection 400, Handover on unaccepted request rejection 400, Handover start by non-owner rejection 403, Handover verification by non-borrower rejection 403, Re-verifying already borrowed transaction rejection 400.
- **Item Return Boundaries (5 tests)**: Return attempt by non-borrower rejection 403, Return on not-borrowed item rejection 400, Non-existent request return 404, Duplicate return attempt rejection 400, Return without prior transaction rejection 400.
- **Chat Boundaries & Input Validation (5 tests)**: Self-chat attempt rejection 400, Empty message body rejection 400, Direct message to non-existent user 404, Unauthorized request thread access 403, Non-existent request message 404.
- **Reviews & Reporting Boundaries (5 tests)**: Self-review rejection 400, Non-existent student review 404, Non-existent item report 404, Non-existent item save/bookmark 404, Save/unsave toggle state inversion.

### Tier 3: Cross-Feature Combinations (7 Tests)
- **Combination 1 (Full Lifecycle)**: Borrow Request -> Acceptance -> Handover OTP -> Return -> Karma Protocol (+10/+5) -> Profile & Request History Audit.
- **Combination 2 (Discovery to Request)**: Item Post -> Hardware Spec Search -> Bookmark/Wishlist -> Direct 1:1 Chat -> Borrow Request.
- **Combination 3 (Concurrency & Cascade)**: Competing Requests Resolution -> Owner accepts Student B -> Auto-declines Student C -> Sets item unavailable -> Blocks Student D.
- **Combination 4 (Chat & Alert Loop)**: Direct message sent -> Notification generated -> Recipient reads notification -> Opens chat thread -> Unread counter resets to 0.
- **Combination 5 (Transaction & Evaluation)**: Handover completed -> Return executed -> Borrower reviews Lender 5 stars -> Review appears on Lender's profile -> Notification delivered.
- **Combination 6 (Wishlist & Mutations)**: Item posted -> Student bookmarks item -> Owner modifies title & specs -> Student's wishlist reflects updates -> Student removes bookmark.
- **Combination 7 (Negative Karma Cascade)**: Item borrowed with 2h duration -> Simulated elapsed time (6h) -> Return processed -> Borrower penalized -30 Karma (trust score 70.0) -> Lender awarded +10 Karma (trust score 110.0).

### Tier 4: Real-World Scenarios (5 Tests)
- **Scenario 1 (Inter-Department Lab Sharing)**: Tanvir (CSE Batch 21) lends Fluke Multimeter to Anik (EEE Batch 22) for Circuits II Lab Final; meeting at CSE building lobby; OTP verification; on-time return; 5-star review.
- **Scenario 2 (Overdue Coursebook Loan)**: Mehedi (ME Batch 20) lends Fluid Mechanics textbook to Sakib (CE Batch 22); return occurs past deadline; -30 Karma penalty applied to Sakib; +10 Karma to Mehedi.
- **Scenario 3 (High-Demand Beacon Resolution)**: Farhan (BME Batch 23) lists ECG sensor; Rifat (CSE) and Nabil (ECE) request concurrently; Farhan accepts Rifat; Nabil's request auto-declined; item unavailable.
- **Scenario 4 (End-to-End Discovery Journey)**: Sophomore discovers development board at CSE Building via landmarks and search; checks 700m perimeter; chats with senior owner; submits borrow request; completes OTP handover.
- **Scenario 5 (Defective Item Moderation Audit)**: Hazardous power supply reported with reason "Defective or Broken Item" and electric shock details; verified in database moderation records.

---

## 6. Execution Instructions

### Running via the Test Runner
```bash
# Execute full 4-tier suite (all 122 tests) with summary table
backend/.venv/bin/python tests/run_tests.py

# Execute specific tier
backend/.venv/bin/python tests/run_tests.py --tier 1
backend/.venv/bin/python tests/run_tests.py --tier 2
backend/.venv/bin/python tests/run_tests.py --tier 3
backend/.venv/bin/python tests/run_tests.py --tier 4

# Run with verbose output per test
backend/.venv/bin/python tests/run_tests.py -v
```

### Running via Standard Python `unittest`
```bash
# Discover and run all test suites
backend/.venv/bin/python -m unittest discover -s tests -p "test_*.py"

# Run individual test files
backend/.venv/bin/python -m unittest tests/test_tier1_features.py
backend/.venv/bin/python -m unittest tests/test_tier2_boundaries.py
backend/.venv/bin/python -m unittest tests/test_tier3_combinations.py
backend/.venv/bin/python -m unittest tests/test_tier4_scenarios.py
```

---

## 7. Verification & CI/CD Readiness
The test runner terminates with strict UNIX exit codes:
- **Exit Code 0**: All tests passed successfully.
- **Exit Code 1**: One or more test failures or unhandled exceptions occurred.
