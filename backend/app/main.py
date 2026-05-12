import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

load_dotenv("../.env")

from app.routers import recipes, ingestion

app = FastAPI(title="Recipe Agent API", version="0.1.0")

default_origins = "http://localhost:5173|http://localhost:4173|https://nexxt-bite.vercel.app|https://recipy-agent-flat6u1k1-alexandra-s-projects2.vercel.app"
allowed_origins = os.getenv("ALLOWED_ORIGINS", default_origins).split("|")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recipes.router)
app.include_router(ingestion.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
