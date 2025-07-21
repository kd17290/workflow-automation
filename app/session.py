import json
import os
from typing import Any

from pydantic_core import to_jsonable_python
from sqlalchemy import create_engine
from sqlalchemy import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

engine_by_schema: dict[str, Engine] = {}
session_factory_by_schema: dict[str, sessionmaker[Session]] = {}


def json_serializer(*args: Any, **kwargs: Any) -> str:
    return json.dumps(*args, default=to_jsonable_python, **kwargs)


DB_URL = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/{POSTGRES_DB}"
)

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

Base = declarative_base()
