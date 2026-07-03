"""
PolicySight — Demo User Seed Script
Creates the demo user if it doesn't exist.
"""

import logging

from src.db.base import SessionLocal
from src.db.models import User, UserRole
from src.core.auth import hash_password

logger = logging.getLogger("policysight.seed")

DEMO_EMAIL = "demo@demo.com"
DEMO_PASSWORD = "demo123"


def seed_demo_user():
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == DEMO_EMAIL).first()
        if existing:
            logger.info(f"Demo user already exists (id={existing.id})")
            return existing

        user = User(
            email=DEMO_EMAIL,
            encrypted_password=hash_password(DEMO_PASSWORD),
            role=UserRole.USER,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"Created demo user: {DEMO_EMAIL} (id={user.id})")
        return user
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_demo_user()
