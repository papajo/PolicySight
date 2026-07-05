from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from src.config.settings import get_settings

settings = get_settings()

# SQLAlchemy 2.0+ requires 'postgresql://', not 'postgres://'
db_url = settings.database_url
if db_url.startswith("postgres://"):
    db_url = "postgresql://" + db_url[len("postgres://"):]

engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()