"""
GPS / Hardware Integration Routes
- Riders can report their GPS location (simulating GPS hardware)
- Customers can track rider location
- Unstructured data storage via JSON extra_data column
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import Optional

from models import get_db, RiderLocation, Order, User
from auth import get_current_user, require_role

router = APIRouter(prefix="/api/gps", tags=["GPS Tracking"])

class GPSReport(BaseModel):
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    speed: Optional[float] = None
    bearing: Optional[float] = None
    extra_data: Optional[dict] = None  # Unstructured data

@router.post("/report")
def report_location(req: GPSReport, user: User = Depends(require_role("rider")),
                    db: Session = Depends(get_db)):
    """Rider reports GPS location - simulates GPS hardware integration"""
    location = RiderLocation(
        rider_id=user.id,
        latitude=req.latitude,
        longitude=req.longitude,
        accuracy=req.accuracy,
        speed=req.speed,
        bearing=req.bearing,
        extra_data=req.extra_data or {
            "device": "simulated-gps",
            "battery_level": 85,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "simulated": True
        }
    )
    db.add(location)
    db.commit()
    return {"message": "Location reported", "rider_id": user.id}

@router.get("/track/{order_id}")
def track_order(order_id: int, user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    """Customer tracks rider location for an order"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Order not found")
    if not order.rider_id:
        raise HTTPException(404, "No rider assigned yet")

    # Get latest rider location
    location = db.query(RiderLocation).filter(
        RiderLocation.rider_id == order.rider_id
    ).order_by(RiderLocation.recorded_at.desc()).first()

    if not location:
        return {"message": "No location data available yet", "rider_id": order.rider_id}

    rider = db.query(User).filter(User.id == order.rider_id).first()
    return {
        "order_id": order_id,
        "rider_id": order.rider_id,
        "rider_name": rider.username if rider else "Unknown",
        "latitude": location.latitude,
        "longitude": location.longitude,
        "accuracy": location.accuracy,
        "speed": location.speed,
        "last_updated": location.recorded_at.isoformat(),
        "extra_data": location.extra_data  # Unstructured data
    }

@router.get("/rider/{rider_id}/history")
def get_rider_history(rider_id: int, minutes: int = Query(30),
                      user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    """Get rider's GPS history for the last N minutes"""
    since = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    locations = db.query(RiderLocation).filter(
        RiderLocation.rider_id == rider_id,
        RiderLocation.recorded_at >= since
    ).order_by(RiderLocation.recorded_at.asc()).all()

    return [
        {
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "speed": loc.speed,
            "recorded_at": loc.recorded_at.isoformat(),
            "extra_data": loc.extra_data
        }
        for loc in locations
    ]
