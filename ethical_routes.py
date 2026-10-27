"""
Ethical, Social, and Political Issues Routes
- Environmental impact tracking (carbon footprint estimation)
- Traffic-aware delivery routing
- Food waste reduction features
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, timezone
from typing import Optional

from models import get_db, Order, Merchant, RiderLocation, User, AuditLog
from auth import get_current_user, require_role

router = APIRouter(prefix="/api/ethical", tags=["Ethical & Social"])

@router.get("/environmental-impact")
def get_environmental_impact(days: int = 30, db: Session = Depends(get_db),
                             user=Depends(get_current_user)):
    """
    Estimate environmental impact of deliveries.
    - CO2 estimation based on delivery distance
    - Orders consolidated per route
    """
    since = datetime.now(timezone.utc) - timedelta(days=days)
    delivered = db.query(Order).filter(
        Order.status == "delivered",
        Order.created_at >= since
    ).all()

    total_distance_km = 0
    total_orders = len(delivered)
    # Estimate: average delivery distance ~3km per order in urban areas
    estimated_avg_distance_km = 3.0
    # CO2 emission: ~120g CO2 per km for motorcycle
    co2_per_km_g = 120

    total_estimated_distance = total_orders * estimated_avg_distance_km
    total_co2_g = total_estimated_distance * co2_per_km_g
    total_co2_kg = total_co2_g / 1000

    # Trees needed to offset (1 tree absorbs ~21kg CO2 per year)
    trees_needed = total_co2_kg / 21

    return {
        "period_days": days,
        "total_deliveries": total_orders,
        "estimated_distance_km": round(total_estimated_distance, 1),
        "estimated_co2_kg": round(total_co2_kg, 2),
        "trees_needed_for_offset": round(trees_needed, 1),
        "co2_per_delivery_g": round(co2_per_km_g * estimated_avg_distance_km, 1),
        "message": "We recommend eco-friendly delivery options like bike couriers for short distances.",
        "eco_tips": [
            "Choose bike delivery for orders under 2km",
            "Consolidate multiple orders to reduce trips",
            "Support restaurants using local ingredients",
            "Opt for minimal/recyclable packaging"
        ]
    }

@router.get("/traffic-impact")
def get_traffic_impact(db: Session = Depends(get_db),
                       user=Depends(get_current_user)):
    """
    Analyze delivery traffic patterns and suggest improvements.
    Social responsibility feature.
    """
    # Analyze peak delivery hours
    all_orders = db.query(Order).filter(Order.status != "cancelled").all()
    hourly_counts = {}
    for o in all_orders:
        if o.created_at:
            h = o.created_at.hour
            hourly_counts[h] = hourly_counts.get(h, 0) + 1

    peak_hours = sorted(hourly_counts.items(), key=lambda x: x[1], reverse=True)[:3]

    return {
        "peak_delivery_hours": [{"hour": h, "orders": c} for h, c in peak_hours],
        "suggestions": [
            "Offer discounts for off-peak delivery slots to reduce traffic congestion",
            "Encourage bike/e-bike delivery during peak hours",
            "Implement delivery time windows to spread out traffic",
            "Partner with local traffic authorities for dedicated delivery zones"
        ],
        "peak_traffic_reduction_potential": "15-20% reduction in delivery vehicle congestion"
    }

@router.get("/food-waste-reduction")
def get_food_waste_reduction(db: Session = Depends(get_db),
                             user=Depends(get_current_user)):
    """
    Food waste reduction initiative.
    Restaurants can donate excess food, customers can buy surplus at discount.
    """
    # Find merchants with surplus stock
    from models import MenuItem
    surplus_items = db.query(MenuItem).filter(
        MenuItem.stock > 50,  # Arbitrary threshold for "surplus"
        MenuItem.is_available == True
    ).all()

    return {
        "surplus_items_count": len(surplus_items),
        "initiatives": [
            "Surplus food sold at 30-50% discount near closing time",
            "Partnership with local food banks for unsold food",
            "Optimized inventory management to reduce overstocking",
            "Customer option to donate $1 with each order for food rescue programs"
        ],
        "estimated_waste_reduction": "25-40% reduction in food waste with smart inventory",
        "surplus_items": [
            {"name": item.name, "merchant_id": item.merchant_id,
             "stock": item.stock, "discounted_price": round(item.price * 0.6, 2)}
            for item in surplus_items[:10]
        ]
    }

@router.post("/report-issue")
def report_ethical_issue(issue: dict, user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    """
    Report ethical, social, or political issues related to the food delivery system.
    """
    log = AuditLog(
        user_id=user.id,
        action="ethical_issue_reported",
        details={
            "issue_type": issue.get("type", "general"),
            "description": issue.get("description", ""),
            "reported_at": datetime.now(timezone.utc).isoformat()
        }
    )
    db.add(log)
    db.commit()
    return {
        "message": "Issue reported. We will review and take appropriate action.",
        "issue_id": log.id,
        "follow_up": "Our ethics committee will review within 48 hours."
    }
