"""
Food Delivery Information System - Main Application
FastAPI Backend Server
"""
import uvicorn
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from config import HOST, PORT
from models import init_db

from routes.auth_routes import router as auth_router
from routes.merchant_routes import router as merchant_router
from routes.order_routes import router as order_router
from routes.analytics_routes import router as analytics_router
from routes.gps_routes import router as gps_router
from routes.ethical_routes import router as ethical_router
from routes.unstructured_routes import router as unstructured_router
from routes.admin_routes import router as admin_router
from seed_data import seed_demo_data

app = FastAPI(
    title="Food Delivery Information System",
    description="A comprehensive food delivery platform with multi-role support, AI analytics, GPS tracking, and ethical features.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(merchant_router)
app.include_router(order_router)
app.include_router(analytics_router)
app.include_router(gps_router)
app.include_router(ethical_router)
app.include_router(unstructured_router)
app.include_router(admin_router)

web_client_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web-client")
if os.path.exists(web_client_path):
    app.mount("/web", StaticFiles(directory=web_client_path, html=True), name="web")

app_client_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app-client")
if os.path.exists(app_client_path):
    app.mount("/app", StaticFiles(directory=app_client_path, html=True), name="app")

@app.on_event("startup")
async def startup():
    print("=" * 60)
    print("  Food Delivery Information System")
    print("  Starting up...")
    print("=" * 60)
    init_db()
    seed_demo_data()
    print("\n  Server ready! 🚀")
    print(f"  API:      http://localhost:{PORT}/docs")
    print(f"  Web:      http://localhost:{PORT}/web")
    print(f"  App:      http://localhost:{PORT}/app")
    print("=" * 60)

@app.get("/")
def root():
    return {
        "name": "Food Delivery Information System",
        "version": "1.0.0",
        "docs": "/docs",
        "web_client": "/web",
        "app_client": "/app",
        "api": "/api"
    }

@app.get("/api/health")
def health_check():
    from datetime import datetime, timezone
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
