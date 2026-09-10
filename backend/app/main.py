from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .database import migrate_db, SessionLocal
from .seed import seed_db
from .routes import auth, items, borrow_requests, chat, transactions, landmarks, notifications, reviews
import os

app = FastAPI(title="CampusShare KUET API")


@app.on_event("startup")
def on_startup():
    migrate_db()
    db = SessionLocal()
    try:
        seed_db(db)
    finally:
        db.close()


# Universal CORS Support: Supports localhost, Vercel deployments (*.vercel.app), Render, and custom domains
raw_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://localhost",
).split(",")
allowed_origins = [o.strip().rstrip("/") for o in raw_origins if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
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
