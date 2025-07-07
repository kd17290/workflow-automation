from dotenv import load_dotenv
from fastapi import FastAPI

from app.api import router as healthcheck_router

load_dotenv(".env")

app = FastAPI(title="Workflow Automation Service", version="1.0.0")

app.include_router(healthcheck_router)
