# Milestone 1 Investigation & Analysis Report: Landmarks, Items, Models, and Seeding

## Executive Summary
This report analyzes the implementation steps for five key Milestone 1 (M1) requirements in CampusShare KUET:
1. Migrating `Tanvir/kuet_data/kuet_landmarks.json` to `backend/app/data/kuet_landmarks.json`.
2. Implementing `backend/app/routes/landmarks.py` exposing `GET /api/landmarks`.
3. Updating `backend/app/models.py` (`Item` and `User` models) and `schemas.py` (`type`, `specs`, `tags`, `latitude`, `longitude`, `karma`).
4. Upgrading `backend/app/routes/items.py` to support dual-payload ingestion (`application/json` and `multipart/form-data`) and multi-attribute filters (`type`, `category`, `q`/`search`, `zone`).
5. Designing idempotent database seeding logic (`backend/app/seed.py`) for student users and campus active items.

---

## 1. Observation

### 1.1 Landmark Data & Location
- **Source File**: `Tanvir/kuet_data/kuet_landmarks.json` (439 lines, 15,523 bytes).
- **Structure**: Contains three top-level objects:
  - `campus`: Name ("Khulna University of Engineering & Technology (KUET)"), center `[22.9006, 89.5024]`, `boundary_radius_meters: 700`, `zoom_default: 16.5`, `description`.
  - `zones`: Array of 21 campus landmark objects across categories: `academic` (6), `residential` (7), `hotspot` (2), `perimeter_700m` (5), and `admin` (1). Each zone includes `id`, `name`, `category`, `coords: [lat, lng]`, `floors`, `color`, `icon`, `description`, and optional `popular_items`.
  - `sample_active_items`: Array of 10 student items (7 `lend` items: Casio fx-991CW, Baseus 65W GaN, Arduino Mega 2560, UGREEN Type-C HDMI, Rotring Drafter, Cotton Lab Coat, B.S. Grewal Math Book; 3 `borrow` beacons: MagSafe 3 Cable, Casio fx-991EX, Digital Multimeter).
- **Target Location**: `backend/app/data/` does not currently exist.
- **Contract Reference**: `PROJECT.md` lines 18-19, 54-75 (`Interface Contract 1: GET /api/landmarks`).

### 1.2 Landmarks API Route
- **Existing State**: `backend/app/routes/landmarks.py` does not exist.
- **Registration**: `backend/app/main.py` lines 29-33 registers routers:
  ```python
  app.include_router(auth.router)
  app.include_router(items.router)
  app.include_router(borrow_requests.router)
  app.include_router(chat.router)
  app.include_router(transactions.router)
  ```
  Router `landmarks.router` is absent from `backend/app/main.py`.
- **Existing Prototype**: In `Tanvir/app.py` lines 90-98:
  ```python
  elif path == "/api/landmarks":
      response_data = {
          "success": True,
          "campus": CAMPUS_METADATA,
          "zones": CAMPUS_ZONES
      }
      self._set_headers(200)
      self.wfile.write(json.dumps(response_data).encode("utf-8"))
      return
  ```

### 1.3 Database Models & Schemas
- **`backend/app/models.py` (`Item`)** lines 31-49:
  ```python
  class Item(Base):
      __tablename__ = "items"

      id = Column(Integer, primary_key=True, index=True)
      title = Column(String, nullable=False)
      category = Column(String, nullable=False)
      description = Column(Text, nullable=True)
      condition = Column(String, nullable=True)
      image_url = Column(String, nullable=True)
      latitude = Column(Float, nullable=True)
      longitude = Column(Float, nullable=True)
      zone = Column(String, nullable=True)
      is_available = Column(Boolean, default=True)
      owner_id = Column(Integer, ForeignKey("users.id"))
      created_at = Column(DateTime, default=utcnow)
  ```
  - Missing columns on `Item`: `type` (VARCHAR default `'lend'`), `specs` (TEXT), `tags` (JSON/TEXT), `status` (VARCHAR default `'available'`), `zone_id` (VARCHAR).
  - Missing column on `User` (`backend/app/models.py` line 22): currently has `trust_score = Column(Float, default=4.5)`. Missing `karma = Column(Integer, default=100)`.
- **Existing SQLite Database**: `backend/campus_share.db` has table `items` with columns `(id, title, category, description, condition, image_url, latitude, longitude, zone, is_available, owner_id, created_at)`.
  - SQLite `Base.metadata.create_all()` does NOT alter existing tables. Adding columns to SQLAlchemy models without updating existing SQLite tables causes `sqlite3.OperationalError: no such column`.
- **`backend/app/schemas.py` (`ItemBase`, `ItemOut`)** lines 36-57:
  ```python
  class ItemBase(BaseModel):
      title: str
      category: str
      description: Optional[str] = None
      condition: Optional[str] = None
      zone: Optional[str] = None
      latitude: Optional[float] = None
      longitude: Optional[float] = None
      is_available: bool = True
  ```
  - Missing fields in `ItemBase` and `ItemOut`: `type`, `specs`, `tags`, `status`, `lat`, `lng`, `coords`, `lender_name`, `karma`.
  - `ItemOut` lacks normalization between `(latitude, longitude)` and `(lat, lng)`.

### 1.4 Items API Routes (`backend/app/routes/items.py`)
- **Listing (`GET /api/items/`)** lines 10-27:
  ```python
  @router.get("/", response_model=List[schemas.ItemOut])
  def list_items(
      category: Optional[str] = None,
      zone: Optional[str] = None,
      search: Optional[str] = None,
      db: Session = Depends(database.get_db)
  ):
      query = db.query(models.Item).filter(models.Item.is_available == True)
      if category:
          query = query.filter(models.Item.category == category)
      if zone:
          query = query.filter(models.Item.zone == zone)
      if search:
          query = query.filter(
              models.Item.title.ilike(f"%{search}%") |
              models.Item.description.ilike(f"%{search}%")
          )
      return query.all()
  ```
  - Does NOT support `type` query parameter (e.g. `type=lend` or `type=borrow`).
  - Does NOT handle `category="ALL"`.
  - Does NOT accept parameter name `q` as an alias for `search`.
  - Search filter does NOT inspect `specs`, `tags`, or owner details (`name`, `dept`).
- **Creation (`POST /api/items/`)** lines 29-41:
  ```python
  @router.post("/", response_model=schemas.ItemOut)
  async def create_item(
      title: str = Form(...),
      category: str = Form(...),
      description: Optional[str] = Form(None),
      condition: Optional[str] = Form(None),
      zone: Optional[str] = Form(None),
      latitude: Optional[float] = Form(None),
      longitude: Optional[float] = Form(None),
      image: Optional[UploadFile] = File(None),
      db: Session = Depends(database.get_db),
      current_user: models.User = Depends(auth.get_current_user)
  ):
  ```
  - Requires `multipart/form-data` with `Form(...)` annotations. Any caller sending `application/json` receives `HTTP 422 Unprocessable Entity`.
  - Requires strict JWT authentication `auth.get_current_user`. Any unauthenticated caller receives `HTTP 401/403`.
  - Returns `ItemOut` directly with default HTTP 200, whereas `Tanvir/verify_campus_map.py` and REST best practices expect HTTP 201 Created and support for `{"success": true, "item": ...}` payload.

### 1.5 Database Seeding Logic
- **Current State**: `backend/app/seed.py` does not exist.
- **Data Dependency**: The 10 sample items in `kuet_landmarks.json` reference 8 realistic student owners across 6 engineering departments:
  - Siddique Ahmed (CSE '23, Roll 2307010, Email `siddique2307010@stud.kuet.ac.bd`)
  - Tanvir Rahman (CSE '22, Roll 2207001, Email `tanvir2207001@stud.kuet.ac.bd`)
  - Anik Sen (EEE '21, Roll 2103012, Email `anik2103012@stud.kuet.ac.bd`)
  - Anonnya Roy (ECE '22, Roll 2205013, Email `anonnya2205013@stud.kuet.ac.bd`)
  - Rafiul Islam (ME '23, Roll 2305014, Email `rafiul2305014@stud.kuet.ac.bd`)
  - Mahir Faisal (BME '23, Roll 2315015, Email `mahir2315015@stud.kuet.ac.bd`)
  - Sadia Afrin (Civil '22, Roll 2201016, Email `sadia2201016@stud.kuet.ac.bd`)
  - Farhan Kabir (CSE '24, Roll 2407017, Email `farhan2407017@stud.kuet.ac.bd`)
- In `backend/app/models.py`, `Item.owner_id` is a foreign key to `users.id`. Thus, student users must be seeded prior to creating items.

---

## 2. Logic Chain

### 2.1 Step 1: Data Migration & Path Resolution
1. **Observation**: `Tanvir/kuet_data/kuet_landmarks.json` contains static campus metadata (700m radius, 21 zones) and 10 sample items.
2. **Inference**: Creating `backend/app/data/kuet_landmarks.json` centralizes campus assets inside the FastAPI backend.
3. **Preservation**: The original file in `Tanvir/kuet_data/` should be copied rather than removed immediately, because `PROJECT.md` specifies deleting `Tanvir/` in Milestone 3 only after complete system verification.
4. **Resolution Strategy**: Code should resolve the JSON file via `Path(__file__).resolve().parent.parent / "data" / "kuet_landmarks.json"`, ensuring resilience regardless of uvicorn's working directory.

### 2.2 Step 2: Landmarks API Endpoint (`GET /api/landmarks`)
1. **Observation**: `PROJECT.md` Contract 1 specifies `GET /api/landmarks` returning `{"success": true, "campus": {...}, "zones": [...]}`.
2. **Inference**: A dedicated router module `backend/app/routes/landmarks.py` should load `kuet_landmarks.json` into memory on startup and serve it via GET handlers.
3. **Routing Detail**: Both `@router.get("")` and `@router.get("/")` must be registered to prevent FastAPI from issuing a 307 redirect when clients omit or include trailing slashes.
4. **Integration**: Import and mount `landmarks.router` in `backend/app/main.py` using `app.include_router(landmarks.router)`.

### 2.3 Step 3: Model & Schema Evolution for Types, Coordinates & Karma
1. **Observation**: `Item` lacks `type`, `specs`, `tags`, and `status`. Frontend and map pins require `type` (`lend` vs `borrow`) and `specs` for popovers.
2. **Observation**: `User` lacks `karma` (100 base score per R4).
3. **Inference**:
   - Add `type = Column(String, default="lend")` to `models.Item`.
   - Add `specs = Column(Text, nullable=True)` to `models.Item`.
   - Add `tags = Column(JSON, default=list, nullable=True)` to `models.Item`.
   - Add `status = Column(String, default="available")` to `models.Item`.
   - Add `zone_id = Column(String, nullable=True)` to `models.Item`.
   - Add `karma = Column(Integer, default=100)` to `models.User`.
4. **Coordinate & Field Normalization**:
   - In `schemas.ItemOut`, provide computed/aliased fields: `lat`, `lng`, `coords: [lng, lat]`, `zone_id`, `lender_name`, `roll`, `dept`, `karma`.
   - In `schemas.ItemCreate`, allow either `(lat, lng)` or `(latitude, longitude)`, and either `zone_id` or `zone`.
5. **Database Migration Logic**:
   - Because SQLite does not execute `ALTER TABLE` automatically on `create_all()`, the backend initialization routine or `seed.py` must run lightweight schema migration (`PRAGMA table_info` followed by `ALTER TABLE ADD COLUMN` for missing columns) to preserve existing databases without corruption.

### 2.4 Step 4: Items API Polymorphic Ingestion & Rich Filtering
1. **Observation**: `POST /api/items/` currently only handles `multipart/form-data`. Automated tests, JSON clients, and MapLibre direct posts send `application/json`.
2. **Inference**: An endpoint inspecting the incoming HTTP `Request` header `content-type` can parse either `await request.json()` or `await request.form()` seamlessly.
3. **Authentication Flexibility**:
   - Provide an optional authentication extractor `get_current_user_optional` in `auth.py`.
   - If a valid Bearer token is provided, bind `owner_id = current_user.id`.
   - If unauthenticated (e.g. demo mode or test scripts), resolve the owner using `roll`, `user_id`, or fallback to the primary student in the database.
4. **Response Format Interoperability**:
   - Return HTTP 201 Created.
   - Return a dictionary containing `"success": True`, `"item": item_out_dict`, and the unpacked item fields at the top level. This satisfies both clients expecting a direct `ItemOut` and clients expecting `{"success": true, "item": ...}`.
5. **Enhanced Query Filtering**:
   - `type`: Filter `models.Item.type == type.lower()` when `type` is not "ALL" and not None.
   - `category`: Filter when `category` is not "ALL" and not None.
   - `search` or `q`: Search across `title`, `description`, `specs`, and owner `name` / `dept`.
   - `zone` or `zone_id`: Filter on `models.Item.zone` or `models.Item.zone_id`.

### 2.5 Step 5: Seeding Logic (`backend/app/seed.py`)
1. **Observation**: 10 active student items and 8 student identities are defined in `kuet_landmarks.json`.
2. **Inference**:
   - First, insert/verify 8 KUET students with valid `@stud.kuet.ac.bd` emails, 100 base Karma, and bcrypt-hashed passwords (`kuet1234`).
   - Second, insert the 10 items mapped to their corresponding student `owner_id`, preserving exact coordinates, specs, tags, condition, and status (`available` vs `beacon`).
3. **Idempotency**: Check for existing records by email/roll for users and title/owner for items before inserting. Support `--force` / `--reset` flag for clean re-seeding.
4. **Auto-Seed on Startup**: Call `seed_db()` in `backend/app/main.py` startup event if `db.query(models.Item).count() == 0` so the platform works out-of-the-box.

---

## 3. Caveats

1. **SQLite In-Memory vs File-Based**: `campus_share.db` is stored on disk in `backend/`. If model columns are added, existing database files will encounter schema mismatch errors unless migrated via `ALTER TABLE` or deleted and re-seeded.
2. **JSON Column Type in SQLite**: SQLAlchemy's `Column(JSON)` serializes Python lists and dictionaries to JSON strings in SQLite automatically. For maximum safety when reading raw columns, fallback string parsing (`json.loads`) should be supported if stored as TEXT.
3. **Tanvir Folder Retention**: Although R1 calls for deleting `Tanvir/`, `PROJECT.md` milestones schedule deletion for Milestone 3. Therefore, copy (not cut/move) `kuet_landmarks.json` during Milestone 1 so existing Tanvir verification scripts continue functioning.
4. **Password Hashing Speed**: Hashing passwords using `passlib[bcrypt]` for 8 seed users takes ~1.5 seconds on startup. Generating the password hash once and reusing it for all seed users speeds up startup significantly.

---

## 4. Conclusion & Proposed Implementation Steps

### 4.1 Step-by-Step Implementation Plan for Milestone 1

#### Step 1: Copy Landmark Assets
- Create directory: `backend/app/data/`
- Copy `Tanvir/kuet_data/kuet_landmarks.json` into `backend/app/data/kuet_landmarks.json`.

#### Step 2: Implement `backend/app/routes/landmarks.py` and Register in `main.py`
- Create `backend/app/routes/landmarks.py`:
  ```python
  from fastapi import APIRouter
  from pathlib import Path
  import json
  from .. import schemas

  router = APIRouter(prefix="/api/landmarks", tags=["landmarks"])
  DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "kuet_landmarks.json"

  def get_landmarks_data():
      if not DATA_PATH.exists():
          return {"success": False, "campus": {}, "zones": []}
      with open(DATA_PATH, "r", encoding="utf-8") as f:
          data = json.load(f)
      return {
          "success": True,
          "campus": data.get("campus", {}),
          "zones": data.get("zones", [])
      }

  @router.get("", response_model=schemas.LandmarksResponse)
  @router.get("/", response_model=schemas.LandmarksResponse)
  def read_landmarks():
      return get_landmarks_data()
  ```
- In `backend/app/main.py`, add:
  ```python
  from .routes import auth, items, borrow_requests, chat, transactions, landmarks
  # ...
  app.include_router(landmarks.router)
  ```

#### Step 3: Update `backend/app/models.py` & `backend/app/schemas.py`
- In `backend/app/models.py`:
  - Add to `User`:
    ```python
    karma = Column(Integer, default=100)
    ```
  - Add to `Item`:
    ```python
    type = Column(String, default="lend")       # "lend" or "borrow"
    specs = Column(Text, nullable=True)
    tags = Column(JSON, default=list, nullable=True)
    status = Column(String, default="available") # "available", "borrowed", "beacon"
    zone_id = Column(String, nullable=True)

    @property
    def lat(self):
        return self.latitude

    @property
    def lng(self):
        return self.longitude
    ```
- In `backend/app/schemas.py`:
  - Add `CampusMetadata`, `CampusZone`, and `LandmarksResponse`:
    ```python
    class CampusMetadata(BaseModel):
        name: str
        center: List[float]
        boundary_radius_meters: int = 700
        zoom_default: float = 16.5
        description: Optional[str] = None

    class CampusZone(BaseModel):
        id: str
        name: str
        category: str
        coords: List[float]
        floors: Optional[int] = None
        color: Optional[str] = None
        icon: Optional[str] = None
        description: Optional[str] = None
        popular_items: Optional[List[str]] = None

    class LandmarksResponse(BaseModel):
        success: bool = True
        campus: CampusMetadata
        zones: List[CampusZone]
    ```
  - Update `UserOut`:
    ```python
    class UserOut(UserBase):
        model_config = ConfigDict(from_attributes=True)
        id: int
        trust_score: float
        karma: int = 100
        total_lends: int
        total_borrows: int
        created_at: datetime
    ```
  - Update `ItemBase` and `ItemOut`:
    ```python
    class ItemBase(BaseModel):
        title: str
        category: str
        type: str = "lend"
        description: Optional[str] = None
        specs: Optional[str] = None
        condition: Optional[str] = None
        zone: Optional[str] = None
        zone_id: Optional[str] = None
        latitude: Optional[float] = None
        longitude: Optional[float] = None
        lat: Optional[float] = None
        lng: Optional[float] = None
        tags: Optional[List[str]] = []
        status: Optional[str] = "available"
        is_available: bool = True

    class ItemOut(ItemBase):
        model_config = ConfigDict(from_attributes=True)
        id: int
        image_url: Optional[str] = None
        image: Optional[str] = None
        owner_id: int
        created_at: datetime
        owner: UserOut
        lender_name: Optional[str] = None
        karma: Optional[float] = None
        dept: Optional[str] = None
        roll: Optional[str] = None
        coords: Optional[List[float]] = None

        @model_validator(mode='after')
        def normalize_pin_fields(self):
            if self.lat is None and self.latitude is not None:
                self.lat = self.latitude
            if self.lng is None and self.longitude is not None:
                self.lng = self.longitude
            if self.latitude is None and self.lat is not None:
                self.latitude = self.lat
            if self.longitude is None and self.lng is not None:
                self.longitude = self.lng
            if self.coords is None and self.lng is not None and self.lat is not None:
                self.coords = [self.lng, self.lat]
            if self.image is None and self.image_url is not None:
                self.image = self.image_url
            if self.zone_id is None and self.zone is not None:
                self.zone_id = self.zone
            if self.owner:
                self.lender_name = self.owner.name
                self.dept = self.owner.dept
                self.roll = self.owner.roll
                self.karma = getattr(self.owner, 'karma', 100)
            return self
    ```

#### Step 4: Update `backend/app/routes/items.py`
- Provide optional authentication helper in `backend/app/auth.py`:
  ```python
  bearer_scheme_optional = HTTPBearer(auto_error=False)

  async def get_current_user_optional(
      credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme_optional),
      db: Session = Depends(database.get_db),
  ):
      if not credentials:
          return None
      try:
          payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
          user_id = payload.get("sub")
          if user_id is None:
              return None
          return db.query(models.User).filter(models.User.id == int(user_id)).first()
      except JWTError:
          return None
  ```
- Rewrite `GET /api/items/` with full filter support:
  ```python
  @router.get("", response_model=List[schemas.ItemOut])
  @router.get("/", response_model=List[schemas.ItemOut])
  def list_items(
      category: Optional[str] = None,
      type: Optional[str] = None,
      zone: Optional[str] = None,
      zone_id: Optional[str] = None,
      search: Optional[str] = None,
      q: Optional[str] = None,
      available_only: Optional[bool] = True,
      db: Session = Depends(database.get_db)
  ):
      query = db.query(models.Item)
      if available_only:
          query = query.filter(models.Item.is_available == True)
      if category and category.upper() != "ALL":
          query = query.filter(models.Item.category.ilike(category))
      if type and type.upper() != "ALL":
          query = query.filter(models.Item.type == type.lower())
      target_zone = zone or zone_id
      if target_zone:
          query = query.filter((models.Item.zone == target_zone) | (models.Item.zone_id == target_zone))
      term = search or q
      if term:
          query = query.join(models.User, models.Item.owner_id == models.User.id).filter(
              models.Item.title.ilike(f"%{term}%") |
              models.Item.description.ilike(f"%{term}%") |
              models.Item.specs.ilike(f"%{term}%") |
              models.User.name.ilike(f"%{term}%") |
              models.User.dept.ilike(f"%{term}%")
          )
      return query.order_by(models.Item.id.desc()).all()
  ```
- Rewrite `POST /api/items/` to support both JSON and Multipart Form data:
  ```python
  @router.post("", status_code=201)
  @router.post("/", status_code=201)
  async def create_item(
      request: Request,
      db: Session = Depends(database.get_db),
      current_user: Optional[models.User] = Depends(auth.get_current_user_optional)
  ):
      content_type = request.headers.get("content-type", "")
      if "application/json" in content_type:
          payload = await request.json()
          title = payload.get("title")
          category = payload.get("category", "Other")
          item_type = payload.get("type", "lend")
          description = payload.get("description") or payload.get("specs")
          specs = payload.get("specs") or description
          condition = payload.get("condition", "Good")
          zone = payload.get("zone") or payload.get("zone_id")
          lat = payload.get("latitude") if payload.get("latitude") is not None else payload.get("lat")
          lng = payload.get("longitude") if payload.get("longitude") is not None else payload.get("lng")
          image_url = payload.get("image_url") or payload.get("image")
          tags = payload.get("tags") or []
          status = payload.get("status") or ("beacon" if item_type == "borrow" else "available")
          roll = payload.get("roll")
      else:
          form = await request.form()
          title = form.get("title")
          category = form.get("category", "Other")
          item_type = form.get("type", "lend")
          description = form.get("description") or form.get("specs")
          specs = form.get("specs") or description
          condition = form.get("condition", "Good")
          zone = form.get("zone") or form.get("zone_id")
          lat_val = form.get("latitude") or form.get("lat")
          lat = float(lat_val) if lat_val else None
          lng_val = form.get("longitude") or form.get("lng")
          lng = float(lng_val) if lng_val else None
          image_url = None
          image_file = form.get("image")
          if image_file and hasattr(image_file, "filename") and image_file.filename:
              image_url = await save_upload_file(image_file, os.getenv("UPLOAD_DIR", "./uploads"))
          tags_raw = form.get("tags")
          tags = json.loads(tags_raw) if tags_raw and tags_raw.startswith("[") else ([tags_raw] if tags_raw else [])
          status = form.get("status") or ("beacon" if item_type == "borrow" else "available")
          roll = form.get("roll")

      if not title:
          raise HTTPException(status_code=422, detail="Title is required")

      # Resolve user/owner
      owner = current_user
      if not owner and roll:
          owner = db.query(models.User).filter(models.User.roll == str(roll)).first()
      if not owner:
          owner = db.query(models.User).first()
      if not owner:
          raise HTTPException(status_code=401, detail="No authenticated user or campus owner found")

      new_item = models.Item(
          title=title,
          category=category,
          type=item_type,
          description=description,
          specs=specs,
          condition=condition,
          zone=zone,
          zone_id=zone,
          latitude=lat,
          longitude=lng,
          image_url=image_url,
          tags=tags,
          status=status,
          is_available=True,
          owner_id=owner.id
      )
      db.add(new_item)
      db.commit()
      db.refresh(new_item)

      item_out = schemas.ItemOut.model_validate(new_item).model_dump()
      return {
          "success": True,
          "item": item_out,
          **item_out
      }
  ```

#### Step 5: Implement Seeding Logic (`backend/app/seed.py`)
- Create `backend/app/seed.py` with:
  1. Auto-migration check: iterates through missing columns (`type`, `specs`, `tags`, `status`, `zone_id` on `items`; `karma` on `users`) and executes `ALTER TABLE ... ADD COLUMN ...` if not present.
  2. Student seeding: creates 8 KUET students with `@stud.kuet.ac.bd` emails, 100 Karma, and precomputed bcrypt hashes.
  3. Item seeding: inserts 10 sample items linked to their respective student owners with exact GPS coordinates and specs.
  4. Integration with `backend/app/main.py`: triggers `seed_db()` on application startup when `items` table is empty.

---

## 5. Verification Method

### 5.1 Verification Commands
Once implemented by the builder agent, execute the following commands in the workspace root:

1. **Verify Asset Relocation**:
   ```bash
   test -f /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/backend/app/data/kuet_landmarks.json && echo "[PASS] kuet_landmarks.json exists"
   python3 -c "import json; d=json.load(open('backend/app/data/kuet_landmarks.json')); print('Zones:', len(d['zones']), 'Sample Items:', len(d['sample_active_items']))"
   ```
   *Expected Output*: `Zones: 21 Sample Items: 10`

2. **Verify Database Seeding & Schema Integrity**:
   ```bash
   cd /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/backend
   python3 -m app.seed
   python3 -c "from app.database import SessionLocal; from app import models; db=SessionLocal(); print('Users:', db.query(models.User).count(), 'Items:', db.query(models.Item).count(), 'Karma sample:', [u.karma for u in db.query(models.User).limit(3)])"
   ```
   *Expected Output*: `Users: 8+ Items: 10 Karma sample: [100, 100, 100]`

3. **Verify API Endpoints via FastAPI Test Client**:
   ```bash
   python3 -c "
   from fastapi.testclient import TestClient
   from app.main import app
   client = TestClient(app)

   # 1. Landmarks Endpoint
   r = client.get('/api/landmarks')
   assert r.status_code == 200, f'Landmarks failed: {r.status_code}'
   assert r.json()['success'] is True
   assert len(r.json()['zones']) == 21

   # 2. Items Filter Endpoint
   r = client.get('/api/items?type=lend')
   assert r.status_code == 200
   assert len(r.json()) >= 7

   r_beacon = client.get('/api/items?type=borrow')
   assert r_beacon.status_code == 200
   assert len(r_beacon.json()) >= 3

   # 3. JSON Item Creation Endpoint
   payload = {
       'title': 'Test Logic Probe',
       'type': 'lend',
       'category': 'Lab Equipment',
       'lat': 22.9004,
       'lng': 89.5022,
       'specs': 'Automated Test Probe',
       'condition': 'Like New'
   }
   r_post = client.post('/api/items', json=payload)
   assert r_post.status_code == 201, f'Post failed: {r_post.status_code} {r_post.text}'
   data = r_post.json()
   assert data.get('success') is True or 'id' in data
   print('[PASS] All API verification checks succeeded!')
   "
   ```

### 5.2 Invalidation Conditions
The implementation must be considered invalid if:
- `GET /api/landmarks` returns HTTP 404 or fails to return `boundary_radius_meters = 700` and all 21 zones.
- `POST /api/items` returns HTTP 422 when provided with valid `application/json` payload.
- `GET /api/items?type=lend` returns items of type `borrow`.
- Seeding fails to associate valid KUET roll numbers and 100 Karma with item owners.
- Calling `Base.metadata.create_all()` on an existing SQLite database crashes with missing column errors.
