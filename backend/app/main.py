import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import monitor

app = FastAPI(title="Monitor de Acearia")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(monitor.router, prefix="", tags=["Monitoramento"])

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(monitor.redis_listener())

@app.get("/")
def read_root():
    return {"status": "Online"}
