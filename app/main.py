from dotenv import load_dotenv
from fastapi import FastAPI

from app.api_v1 import router as router_v1
from app.api_v2 import router as router_v2

load_dotenv(".env")

app = FastAPI(title="Workflow Automation Service", version="1.0.0")

app.include_router(prefix="/api/v1", router=router_v1)
app.include_router(prefix="/api/v2", router=router_v2)
