import json
import os
from typing import Any

from pydantic_core import to_jsonable_python
from sqlalchemy import create_engine
from sqlalchemy import Engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine_by_schema: dict[str, Engine] = {}
session_factory_by_schema: dict[str, sessionmaker[Session]] = {}


def json_serializer(*args: Any, **kwargs: Any) -> str:
    """
    JSON serializer for SQLAlchemy that handles Pydantic models and other types.
    """
    return json.dumps(*args, default=to_jsonable_python, **kwargs)


DB_URL = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}/{settings.POSTGRES_DB}"

engine = create_engine(
    DB_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
    pool_recycle=3600,
    json_serializer=json_serializer,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""

    pass
