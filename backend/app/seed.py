"""
CampusShare KUET — Database Seeding Module
Populates the database with 4 demo student users, 4 rich campus items (2 lend, 2 borrow),
and starter chat data if the database is uninitialized.
"""

from sqlalchemy.orm import Session
from . import models, auth
from datetime import datetime


def seed_db(db: Session):
    """Seed demo students and items if items table is empty."""
    item_count = db.query(models.Item).count()
    if item_count > 0:
        return

    # 1. Create or fetch demo student users
    demo_users_data = [
        {
            "email": "tanvir.rahman@stud.kuet.ac.bd",
            "name": "Tanvir Rahman",
            "dept": "CSE",
            "batch": "22",
            "roll": "015",
            "karma": 125,
            "trust_score": 100.0,
            "total_lends": 5,
            "total_borrows": 2,
        },
        {
            "email": "anik.sen@stud.kuet.ac.bd",
            "name": "Anik Sen",
            "dept": "EEE",
            "batch": "21",
            "roll": "042",
            "karma": 140,
            "trust_score": 100.0,
            "total_lends": 8,
            "total_borrows": 1,
        },
        {
            "email": "farhan.kabir@stud.kuet.ac.bd",
            "name": "Farhan Kabir",
            "dept": "CSE",
            "batch": "24",
            "roll": "089",
            "karma": 95,
            "trust_score": 100.0,
            "total_lends": 1,
            "total_borrows": 3,
        },
        {
            "email": "sadia.afrin@stud.kuet.ac.bd",
            "name": "Sadia Afrin",
            "dept": "CE",
            "batch": "22",
            "roll": "064",
            "karma": 110,
            "trust_score": 100.0,
            "total_lends": 3,
            "total_borrows": 2,
        },
    ]

    users = []
    default_password_hash = auth.get_password_hash("password123")

    for u_data in demo_users_data:
        existing = db.query(models.User).filter(models.User.email == u_data["email"]).first()
        if not existing:
            user = models.User(
                email=u_data["email"],
                name=u_data["name"],
                dept=u_data["dept"],
                batch=u_data["batch"],
                roll=u_data["roll"],
                hashed_password=default_password_hash,
                karma=u_data["karma"],
                trust_score=u_data["trust_score"],
                total_lends=u_data["total_lends"],
                total_borrows=u_data["total_borrows"],
                is_verified=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            users.append(user)
        else:
            users.append(existing)

    user_map = {u.email: u for u in users}

    # 2. Insert exactly 4 detailed dummy items (2 lending, 2 borrowing)
    tanvir = user_map.get("tanvir.rahman@stud.kuet.ac.bd") or users[0]
    anik = user_map.get("anik.sen@stud.kuet.ac.bd") or users[1]
    farhan = user_map.get("farhan.kabir@stud.kuet.ac.bd") or users[2]
    sadia = user_map.get("sadia.afrin@stud.kuet.ac.bd") or users[3]

    items_data = [
        # Lend 1
        models.Item(
            title="Casio fx-991CW ClassWiz Scientific Calculator (Exam Approved)",
            category="Calculators",
            type="lend",
            condition="Like New",
            specs="High-resolution 4-tone natural textbook display with QR code visualization. Authentic Casio hologram, approved for all KUET semester finals and math sessionals. Solar + LR44 dual power backup.",
            description="Clean exam-ready condition with hard sliding protective cover. Available for short-term midterm loans or final exam weeks.",
            zone="Ekushey Hall",
            zone_id="ekushey_hall",
            latitude=22.9015,
            longitude=89.5036,
            image_url="https://images.unsplash.com/photo-1594980596870-8aa52a78d8cd?w=600",
            tags=["#ExamReady", "#Casio991CW", "#CSE", "#Calculators"],
            status="available",
            is_available=True,
            owner_id=tanvir.id,
        ),
        # Lend 2
        models.Item(
            title="Arduino Mega 2560 R3 Microcontroller Kit + Sensor Bundle",
            category="Lab Equipment",
            type="lend",
            condition="Good",
            specs="ATmega2560 running at 16MHz with 54 digital I/O pins, 16 analog inputs, 4 UARTs. Includes USB programming cable, full-size breadboard, 40-pin Dupont jumper wires, ultrasonic HC-SR04, DHT22 sensor, and dual-channel 5V relay module.",
            description="Complete embedded systems lab package for EEE/CSE/ECE students working on hardware interfacing or term projects.",
            zone="EEE Building",
            zone_id="eee_bldg",
            latitude=22.8998,
            longitude=89.5031,
            image_url="https://images.unsplash.com/photo-1553406830-ef2513450d76?w=600",
            tags=["#Arduino", "#LabKit", "#Robotics", "#EEE"],
            status="available",
            is_available=True,
            owner_id=anik.id,
        ),
        # Borrow 1 (Demand Beacon)
        models.Item(
            title="URGENT BEACON: MacBook 67W / 140W USB-C Power Adapter (2 Hours)",
            category="Electronics & Power",
            type="borrow",
            condition="N/A",
            specs="🚨 EMERGENCY BORROW BEACON: Need USB-C Power Delivery charger (67W or higher, MagSafe 3 / Type-C) for 2 hours during software lab defense. Currently at 5% battery.",
            description="Urgent demand beacon for afternoon lab evaluation session. Can meet at Central Cafeteria or CSE Department lobby.",
            zone="Central Cafeteria",
            zone_id="central_cafeteria",
            latitude=22.8992,
            longitude=89.5015,
            image_url="https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=600",
            tags=["#Urgent", "#PowerAdapter", "#MacBook", "#DemandBeacon"],
            status="beacon",
            is_available=True,
            owner_id=farhan.id,
        ),
        # Borrow 2 (Demand Beacon)
        models.Item(
            title="DEMAND BEACON: Rotring Engineering Mini Drafter with Table Clamp",
            category="Stationery & Drawing",
            type="borrow",
            condition="N/A",
            specs="🚨 URGENT Sessional Requirement: Rotring or Omron mini drafter with steel scale arms and 360-degree protractor head. Needed for Civil/Mechanical engineering drawing final plate submission.",
            description="Borrowing for today's 4-hour drawing studio in ME building. Will return immediately afterwards in mint condition.",
            zone="ME Building",
            zone_id="me_bldg",
            latitude=22.8990,
            longitude=89.5032,
            image_url="https://images.unsplash.com/photo-1581092160607-ee22621dd758?w=600",
            tags=["#EngineeringDrawing", "#MiniDrafter", "#Civil", "#DemandBeacon"],
            status="beacon",
            is_available=True,
            owner_id=sadia.id,
        ),
    ]

    for item in items_data:
        db.add(item)
    db.commit()

    # 3. Seed starter 1:1 chat conversation between Farhan and Tanvir
    first_item = db.query(models.Item).filter(models.Item.owner_id == tanvir.id).first()
    item_id = first_item.id if first_item else None

    msg1 = models.Message(
        sender_id=farhan.id,
        recipient_id=tanvir.id,
        item_id=item_id,
        content="Assalamu Alaikum brother, is the Casio 991CW available for tomorrow's midterm exam?",
        is_read=True,
    )
    msg2 = models.Message(
        sender_id=tanvir.id,
        recipient_id=farhan.id,
        item_id=item_id,
        content="Wa Alaikum Assalam! Yes, it's available. You can collect it from Ekushey Hall room 312 after 8 PM.",
        is_read=True,
    )
    db.add(msg1)
    db.add(msg2)
    db.commit()

