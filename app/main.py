import asyncio

from dotenv import load_dotenv
from fastapi import FastAPI

from app.api import router
from app.crud import save_health_status
from app.session import Base
from app.session import engine
from app.session import SessionLocal

load_dotenv(".env")

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Workflow Automation Service", version="1.0.0")

app.include_router(prefix="/api/v1", router=router)


async def health_status_task():
    while True:
        print("Health status task")
        async with asyncio.Lock():  # to prevent overlapping tasks
            db = SessionLocal()
            try:
                save_health_status(db, status="ok")
            finally:
                db.close()
        await asyncio.sleep(10)


@app.on_event("startup")
async def startup_event():
    print("Starting up...")
    asyncio.create_task(health_status_task())
