"""FastAPI application factory. Phase 0 wires health, checks, and sources.
Auth/orgs/billing routers arrive in later phases."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import health, checks, sources

app = FastAPI(title="Swipe API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(health.router)
app.include_router(checks.router)
app.include_router(sources.router)

@app.get("/")
def root():
    return {"service": "swipe", "docs": "/docs"}
