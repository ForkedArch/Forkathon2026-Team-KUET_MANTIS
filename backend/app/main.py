from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .database import engine, Base
from .routes import auth, items, borrow_requests, chat, transactions
import os

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="CampusShare KUET API")

# CORS
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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

@app.get("/")
def root():
    return {"message": "CampusShare KUET API is running"}

@app.get("/health")
def health():
    return {"status": "ok"}
