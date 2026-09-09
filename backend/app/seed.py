import json
from pathlib import Path
from sqlalchemy.orm import Session
from .database import SessionLocal, migrate_db
from . import models, auth

LANDMARKS_PATH = Path(__file__).resolve().parent / "data" / "kuet_landmarks.json"

STUDENTS_SEED = [
    {
        "name": "Siddique Ahmed",
        "email": "siddique2307010@stud.kuet.ac.bd",
        "batch": "23",
        "dept": "07",
        "roll": "010",
        "karma": 100,
        "trust_score": 100.0,
    },
    {
        "name": "Tanvir Rahman",
        "email": "tanvir2207001@stud.kuet.ac.bd",
        "batch": "22",
        "dept": "07",
        "roll": "001",
        "karma": 100,
        "trust_score": 100.0,
    },
    {
        "name": "Anik Sen",
        "email": "anik2103012@stud.kuet.ac.bd",
        "batch": "21",
        "dept": "03",
        "roll": "012",
        "karma": 100,
        "trust_score": 100.0,
    },
    {
        "name": "Anonnya Roy",
        "email": "anonnya2205013@stud.kuet.ac.bd",
        "batch": "22",
        "dept": "05",
        "roll": "013",
        "karma": 100,
        "trust_score": 100.0,
    },
    {
        "name": "Rafiul Islam",
        "email": "rafiul2305014@stud.kuet.ac.bd",
        "batch": "23",
        "dept": "05",
        "roll": "014",
        "karma": 100,
        "trust_score": 100.0,
    },
    {
        "name": "Mahir Faisal",
        "email": "mahir2315015@stud.kuet.ac.bd",
        "batch": "23",
        "dept": "15",
        "roll": "015",
        "karma": 100,
        "trust_score": 100.0,
    },
    {
        "name": "Sadia Afrin",
        "email": "sadia2201016@stud.kuet.ac.bd",
        "batch": "22",
        "dept": "01",
        "roll": "016",
        "karma": 100,
        "trust_score": 100.0,
    },
    {
        "name": "Farhan Kabir",
        "email": "farhan2407017@stud.kuet.ac.bd",
        "batch": "24",
        "dept": "07",
        "roll": "017",
        "karma": 100,
        "trust_score": 100.0,
    }
]


def seed_db(db: Session = None, force: bool = False):
    migrate_db()
    close_after = False
    if db is None:
        db = SessionLocal()
        close_after = True

    try:
        current_item_count = db.query(models.Item).count()
        if current_item_count > 0 and not force:
            print(f"[Seed] Database already contains {current_item_count} items. Skipping seed.")
            return

        # Precompute password hash once for performance
        default_hash = auth.get_password_hash("kuet1234")

        # 1. Seed students
        user_map = {}
        for s in STUDENTS_SEED:
            user = db.query(models.User).filter(models.User.email == s["email"]).first()
            if not user:
                user = models.User(
                    email=s["email"],
                    name=s["name"],
                    dept=s["dept"],
                    batch=s["batch"],
                    roll=s["roll"],
                    hashed_password=default_hash,
                    karma=s["karma"],
                    trust_score=s["trust_score"],
                    is_verified=True,
                )
                db.add(user)
                db.flush()
            user_map[s["name"]] = user

        # 2. Seed items from kuet_landmarks.json
        if LANDMARKS_PATH.exists():
            with open(LANDMARKS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            sample_items = data.get("sample_active_items", [])

            for item_data in sample_items:
                title = item_data.get("title")
                lender_name = item_data.get("lender_name")
                owner = user_map.get(lender_name) or db.query(models.User).first()

                existing = db.query(models.Item).filter(
                    models.Item.title == title,
                    models.Item.owner_id == owner.id
                ).first()

                if not existing:
                    new_item = models.Item(
                        title=title,
                        category=item_data.get("category", "Other"),
                        type=item_data.get("type", "lend"),
                        description=item_data.get("specs") or title,
                        specs=item_data.get("specs"),
                        condition=item_data.get("condition", "Good"),
                        zone=item_data.get("zone_id"),
                        zone_id=item_data.get("zone_id"),
                        latitude=item_data.get("lat"),
                        longitude=item_data.get("lng"),
                        image_url=item_data.get("image"),
                        tags=item_data.get("tags", []),
                        status=item_data.get("status", "available"),
                        is_available=True,
                        owner_id=owner.id
                    )
                    db.add(new_item)

        db.commit()
        print(f"[Seed] Successfully seeded {db.query(models.User).count()} users and {db.query(models.Item).count()} items.")
    finally:
        if close_after:
            db.close()


if __name__ == "__main__":
    seed_db(force=True)

