from pathlib import Path
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

db_url = os.getenv("DATABASE_URL", "sqlite:///./campus_share.db")

# Some hosts give postgres:// — SQLAlchemy needs postgresql://
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

if db_url.startswith("sqlite:///./") or db_url == "sqlite:///campus_share.db":
    backend_dir = Path(__file__).resolve().parent.parent
    db_file = backend_dir / "campus_share.db"
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_file}"
else:
    SQLALCHEMY_DATABASE_URL = db_url

# check_same_thread is SQLite-only. Postgres crashes if this is always set.
connect_args = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def migrate_db():
    """Create tables. Support both SQLite and PostgreSQL (Neon/Render)."""
    Base.metadata.create_all(bind=engine)

    # PostgreSQL (Neon Database on Render) migrations using ADD COLUMN IF NOT EXISTS
    if not SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
        with engine.connect() as conn:
            postgres_alters = [
                # Messages table
                "ALTER TABLE messages ADD COLUMN IF NOT EXISTS recipient_id INTEGER",
                "ALTER TABLE messages ADD COLUMN IF NOT EXISTS item_id INTEGER",
                "ALTER TABLE messages ADD COLUMN IF NOT EXISTS is_read BOOLEAN DEFAULT FALSE",
                # Users table
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS karma INTEGER DEFAULT 100",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS trust_score FLOAT DEFAULT 100.0",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS total_lends INTEGER DEFAULT 0",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS total_borrows INTEGER DEFAULT 0",
                # Items table
                "ALTER TABLE items ADD COLUMN IF NOT EXISTS type VARCHAR DEFAULT 'lend'",
                "ALTER TABLE items ADD COLUMN IF NOT EXISTS specs TEXT",
                "ALTER TABLE items ADD COLUMN IF NOT EXISTS tags JSON DEFAULT '[]'",
                "ALTER TABLE items ADD COLUMN IF NOT EXISTS status VARCHAR DEFAULT 'available'",
                "ALTER TABLE items ADD COLUMN IF NOT EXISTS zone_id VARCHAR",
                # Borrow requests & Transactions
                "ALTER TABLE borrow_requests ADD COLUMN IF NOT EXISTS pickup_zone VARCHAR",
                "ALTER TABLE borrow_requests ADD COLUMN IF NOT EXISTS purpose VARCHAR",
                "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS otp VARCHAR",
                "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS qr_code TEXT",
            ]
            for stmt in postgres_alters:
                try:
                    conn.exec_driver_sql(stmt)
                except Exception as e:
                    print(f"Postgres migration notice for '{stmt}': {e}")
            conn.commit()
        return

    with engine.connect() as conn:
        # 1. Users table migration
        user_cols = [r[1] for r in conn.exec_driver_sql("PRAGMA table_info(users)").fetchall()]
        if user_cols:
            if "karma" not in user_cols:
                conn.exec_driver_sql("ALTER TABLE users ADD COLUMN karma INTEGER DEFAULT 100")
                conn.commit()

            res = conn.exec_driver_sql(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='users'"
            ).fetchone()
            if res and "UNIQUE (roll)" in res[0]:
                conn.exec_driver_sql("PRAGMA foreign_keys=off")
                conn.exec_driver_sql("""
                CREATE TABLE users_migrated (
                    id INTEGER NOT NULL PRIMARY KEY,
                    email VARCHAR NOT NULL UNIQUE,
                    name VARCHAR NOT NULL,
                    dept VARCHAR NOT NULL,
                    batch VARCHAR NOT NULL,
                    roll VARCHAR NOT NULL,
                    hashed_password VARCHAR NOT NULL,
                    is_verified BOOLEAN DEFAULT 1,
                    karma INTEGER DEFAULT 100,
                    trust_score FLOAT DEFAULT 100.0,
                    total_lends INTEGER DEFAULT 0,
                    total_borrows INTEGER DEFAULT 0,
                    created_at DATETIME,
                    UNIQUE (batch, dept, roll)
                )
                """)
                conn.exec_driver_sql("""
                INSERT INTO users_migrated (
                    id, email, name, dept, batch, roll, hashed_password, is_verified,
                    karma, trust_score, total_lends, total_borrows, created_at
                )
                SELECT id, email, name, dept, batch, roll, hashed_password, is_verified,
                       COALESCE(karma, 100), COALESCE(trust_score, 100.0),
                       total_lends, total_borrows, created_at
                FROM users
                """)
                conn.exec_driver_sql("DROP TABLE users")
                conn.exec_driver_sql("ALTER TABLE users_migrated RENAME TO users")
                conn.exec_driver_sql(
                    "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email)"
                )
                conn.exec_driver_sql(
                    "CREATE INDEX IF NOT EXISTS ix_users_id ON users (id)"
                )
                conn.exec_driver_sql("PRAGMA foreign_keys=on")
                conn.commit()

        # 2. Items table migration
        item_cols = [r[1] for r in conn.exec_driver_sql("PRAGMA table_info(items)").fetchall()]
        if item_cols:
            if "type" not in item_cols:
                conn.exec_driver_sql("ALTER TABLE items ADD COLUMN type VARCHAR DEFAULT 'lend'")
            if "specs" not in item_cols:
                conn.exec_driver_sql("ALTER TABLE items ADD COLUMN specs TEXT")
            if "tags" not in item_cols:
                conn.exec_driver_sql("ALTER TABLE items ADD COLUMN tags JSON DEFAULT '[]'")
            if "status" not in item_cols:
                conn.exec_driver_sql(
                    "ALTER TABLE items ADD COLUMN status VARCHAR DEFAULT 'available'"
                )
            if "zone_id" not in item_cols:
                conn.exec_driver_sql("ALTER TABLE items ADD COLUMN zone_id VARCHAR")
            conn.commit()

        # 3. Messages table migration
        msg_cols = [r[1] for r in conn.exec_driver_sql("PRAGMA table_info(messages)").fetchall()]
        if msg_cols:
            if "recipient_id" not in msg_cols:
                conn.exec_driver_sql("ALTER TABLE messages ADD COLUMN recipient_id INTEGER")
            if "item_id" not in msg_cols:
                conn.exec_driver_sql("ALTER TABLE messages ADD COLUMN item_id INTEGER")
            if "is_read" not in msg_cols:
                conn.exec_driver_sql("ALTER TABLE messages ADD COLUMN is_read BOOLEAN DEFAULT 0")
            conn.commit()

        # 4. Migrate existing numeric department codes to official acronyms (e.g. 07 -> CSE, 03 -> EEE)
        if user_cols and "dept" in user_cols:
            dept_map = {
                "01": "CE", "02": "EEE", "03": "EEE", "04": "ME", "05": "ME",
                "06": "ECE", "07": "CSE", "08": "BME", "09": "ECE", "10": "TE",
                "11": "IEM", "12": "ESE", "13": "ESE", "14": "ChE", "15": "BME",
                "16": "Arch", "17": "URP", "18": "URP", "19": "BECM", "20": "BECM",
                "21": "MSE", "22": "MSE", "23": "ChE", "24": "ChE", "25": "MTE",
                "26": "MTE", "27": "Arch", "28": "Arch", "29": "LE", "31": "TE"
            }
            for code, name in dept_map.items():
                conn.exec_driver_sql(
                    "UPDATE users SET dept = ? WHERE dept = ? OR dept = ?",
                    (name, code, str(int(code)))
                )
            conn.commit()

