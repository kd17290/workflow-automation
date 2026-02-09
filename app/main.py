import asyncio
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

from app.api.deps import get_db
from app.api.v1.router import api_router
from app.core.config import settings
from app.db.session import SessionLocal, engine, Base
from app.repositories.health import save_health_status

load_dotenv()

# Create tables
Base.metadata.create_all(bind=engine)


async def health_status_task():
    """
    Background task to periodically save the health status to the database.
    Runs every 10 seconds.
    """
    while True:
        print("Health status task")
        async with asyncio.Lock():  # to prevent overlapping tasks
            db = SessionLocal()
            try:
                save_health_status(db, status="ok")
            finally:
                db.close()
        await asyncio.sleep(10)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for the FastAPI application.

    Handles startup and shutdown events, such as initializing background tasks.

    Args:
        app (FastAPI): The FastAPI application instance.
    """
    print("Starting up...")
    task = asyncio.create_task(health_status_task())
    yield
    # Clean up the task if necessary, though for now we just let it run until shutdown


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    """Root endpoint to verify API is running."""
    return {"message": "Hello World"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
