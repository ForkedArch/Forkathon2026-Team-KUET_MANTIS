from fastapi import APIRouter
from pathlib import Path
import json

router = APIRouter(prefix="/api/landmarks", tags=["landmarks"])

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "kuet_landmarks.json"


def load_landmarks():
    if not DATA_PATH.exists():
        return {
            "success": False,
            "campus": {},
            "zones": []
        }
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {
        "success": True,
        "campus": data.get("campus", {}),
        "zones": data.get("zones", [])
    }


@router.get("")
@router.get("/")
def get_landmarks():
    return load_landmarks()

