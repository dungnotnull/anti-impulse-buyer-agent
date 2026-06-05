"""anti-impulse-buyer — Local Python Backend

FastAPI server listening on localhost:7432.
"""

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import ALLOWED_ORIGINS, HOST, PORT
from backend.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="anti-impulse-buyer",
    version="0.1.0",
    description="Local backend for the anti-impulse-buyer browser extension",
    lifespan=lifespan,
)

# CORS — restrict to extension origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


# ─── Health check ───

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "anti-impulse-buyer"}


# ─── Register routers ───

from backend.routers import (
    dark_patterns,
    events,
    essentials,
    export,
    intercept,
    profile,
    summary,
    wishlist_digest,
)

app.include_router(intercept.router)
app.include_router(events.router)
app.include_router(essentials.router)
app.include_router(summary.router)
app.include_router(profile.router)
app.include_router(wishlist_digest.router)
app.include_router(dark_patterns.router)
app.include_router(export.router)


# ─── CLI entry point ───

def main():
    uvicorn.run("backend.main:app", host=HOST, port=PORT, reload=False)


if __name__ == "__main__":
    main()
