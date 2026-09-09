from pathlib import Path
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

db_url = os.getenv("DATABASE_URL", "sqlite:///./campus_share.db")
if db_url.startswith("sqlite:///./") or db_url == "sqlite:///campus_share.db":
    backend_dir = Path(__file__).resolve().parent.parent
    db_file = backend_dir / "campus_share.db"
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_file}"
else:
    SQLALCHEMY_DATABASE_URL = db_url

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def migrate_db():
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        # 1. Users table migration
        user_cols = [r[1] for r in conn.exec_driver_sql("PRAGMA table_info(users)").fetchall()]
        if user_cols:
            if "karma" not in user_cols:
                conn.exec_driver_sql("ALTER TABLE users ADD COLUMN karma INTEGER DEFAULT 100")
                conn.commit()

            # Check if UNIQUE (roll) constraint exists in users table definition
            res = conn.exec_driver_sql("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'").fetchone()
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
                INSERT INTO users_migrated (id, email, name, dept, batch, roll, hashed_password, is_verified, karma, trust_score, total_lends, total_borrows, created_at)
                SELECT id, email, name, dept, batch, roll, hashed_password, is_verified, COALESCE(karma, 100), COALESCE(trust_score, 100.0), total_lends, total_borrows, created_at
                FROM users
                """)
                conn.exec_driver_sql("DROP TABLE users")
                conn.exec_driver_sql("ALTER TABLE users_migrated RENAME TO users")
                conn.exec_driver_sql("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email)")
                conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_users_id ON users (id)")
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
                conn.exec_driver_sql("ALTER TABLE items ADD COLUMN status VARCHAR DEFAULT 'available'")
            if "zone_id" not in item_cols:
                conn.exec_driver_sql("ALTER TABLE items ADD COLUMN zone_id VARCHAR")
            conn.commit()
