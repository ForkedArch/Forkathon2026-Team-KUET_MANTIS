from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .database import migrate_db
from .routes import auth, items, borrow_requests, chat, transactions, landmarks, notifications, reviews
import os

app = FastAPI(title="CampusShare KUET API")


@app.on_event("startup")
def on_startup():
    migrate_db()


# CORS
raw_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost",
).split(",")
allowed_origins = []
for o in raw_origins:
    cleaned = o.strip().rstrip("/")
    if cleaned:
        allowed_origins.append(cleaned)

allow_all = "*" in allowed_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=not allow_all,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for uploads
upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
os.makedirs(upload_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")

# Include routers
app.include_router(auth.router)
app.include_router(items.router)
app.include_router(borrow_requests.router)
app.include_router(chat.router)
app.include_router(transactions.router)
app.include_router(landmarks.router)
app.include_router(notifications.router)
app.include_router(reviews.router)

@app.get("/")
def root():
    return {"message": "CampusShare KUET API is running"}

@app.get("/health")
def health():
    return {"status": "ok"}
