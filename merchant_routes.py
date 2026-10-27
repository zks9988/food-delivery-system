from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timezone

from models import get_db, Merchant, MenuItem, Order, OrderItem, User, Review
from auth import get_current_user, require_role, log_audit

router = APIRouter(prefix="/api/merchants", tags=["Merchants"])

class MerchantCreate(BaseModel):
    name: str
    description: str = ""
    address: str = ""
    cuisine_type: str = ""
    latitude: float = 0
    longitude: float = 0
    open_time: str = "09:00"
    close_time: str = "22:00"

class MenuItemCreate(BaseModel):
    name: str
    description: str = ""
    price: float
    category: str = ""
    stock: int = 999

# --- Merchant Profile ---
@router.post("/register")
def register_as_merchant(req: MerchantCreate, user: User = Depends(require_role("merchant")),
                         db: Session = Depends(get_db)):
    existing = db.query(Merchant).filter(Merchant.user_id == user.id).first()
    if existing:
        raise HTTPException(400, "You already have a merchant profile")
    merchant = Merchant(
        user_id=user.id, name=req.name, description=req.description,
        address=req.address, cuisine_type=req.cuisine_type,
        latitude=req.latitude, longitude=req.longitude
    )
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    return merchant

@router.get("/profile")
def get_merchant_profile(user: User = Depends(require_role("merchant")),
                         db: Session = Depends(get_db)):
    merchant = db.query(Merchant).filter(Merchant.user_id == user.id).first()
    if not merchant:
        raise HTTPException(404, "Merchant profile not found")
    return merchant

@router.get("/all")
def list_merchants(db: Session = Depends(get_db)):
    merchants = db.query(Merchant).filter(Merchant.is_open == True).all()
    result = []
    for m in merchants:
        owner = db.query(User).filter(User.id == m.user_id).first()
        result.append({
            "id": m.id, "name": m.name, "description": m.description,
            "address": m.address, "cuisine_type": m.cuisine_type,
            "rating": m.rating, "latitude": m.latitude, "longitude": m.longitude,
            "is_open": m.is_open, "image_url": m.image_url,
            "owner_name": owner.username if owner else ""
        })
    return result

@router.get("/{merchant_id}")
def get_merchant(merchant_id: int, db: Session = Depends(get_db)):
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
    if not merchant:
        raise HTTPException(404, "Merchant not found")
    return merchant

# --- Menu Items ---
@router.post("/menu")
def add_menu_item(req: MenuItemCreate, user: User = Depends(require_role("merchant")),
                  db: Session = Depends(get_db)):
    merchant = db.query(Merchant).filter(Merchant.user_id == user.id).first()
    if not merchant:
        raise HTTPException(404, "Register as merchant first")
    item = MenuItem(merchant_id=merchant.id, **req.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.get("/{merchant_id}/menu")
def get_menu(merchant_id: int, db: Session = Depends(get_db)):
    items = db.query(MenuItem).filter(
        MenuItem.merchant_id == merchant_id,
        MenuItem.is_available == True
    ).all()
    return items

@router.put("/menu/{item_id}")
def update_menu_item(item_id: int, req: MenuItemCreate,
                     user: User = Depends(require_role("merchant")),
                     db: Session = Depends(get_db)):
    merchant = db.query(Merchant).filter(Merchant.user_id == user.id).first()
    item = db.query(MenuItem).filter(MenuItem.id == item_id, MenuItem.merchant_id == merchant.id).first()
    if not item:
        raise HTTPException(404, "Menu item not found")
    for key, val in req.model_dump().items():
        setattr(item, key, val)
    db.commit()
    return item

@router.delete("/menu/{item_id}")
def delete_menu_item(item_id: int, user: User = Depends(require_role("merchant")),
                     db: Session = Depends(get_db)):
    merchant = db.query(Merchant).filter(Merchant.user_id == user.id).first()
    item = db.query(MenuItem).filter(MenuItem.id == item_id, MenuItem.merchant_id == merchant.id).first()
    if not item:
        raise HTTPException(404, "Menu item not found")
    db.delete(item)
    db.commit()
    return {"message": "Deleted"}

# --- Merchant Orders ---
@router.get("/orders/all")
def get_merchant_orders(user: User = Depends(require_role("merchant")),
                        db: Session = Depends(get_db)):
    merchant = db.query(Merchant).filter(Merchant.user_id == user.id).first()
    if not merchant:
        raise HTTPException(404, "Merchant not found")
    orders = db.query(Order).filter(Order.merchant_id == merchant.id).order_by(Order.created_at.desc()).all()
    result = []
    for o in orders:
        customer = db.query(User).filter(User.id == o.customer_id).first()
        items = db.query(OrderItem).filter(OrderItem.order_id == o.id).all()
        result.append({
            "id": o.id, "status": o.status.value, "total_price": o.total_price,
            "delivery_address": o.delivery_address, "note": o.note,
            "payment_method": o.payment_method, "created_at": o.created_at.isoformat(),
            "customer_name": customer.username if customer else "Unknown",
            "items": [{"id": i.id, "menu_item_id": i.menu_item_id, "quantity": i.quantity, "unit_price": i.unit_price} for i in items]
        })
    return result

@router.put("/orders/{order_id}/status")
def update_order_status(order_id: int, status: str,
                        user: User = Depends(require_role("merchant")),
                        db: Session = Depends(get_db)):
    merchant = db.query(Merchant).filter(Merchant.user_id == user.id).first()
    order = db.query(Order).filter(Order.id == order_id, Order.merchant_id == merchant.id).first()
    if not order:
        raise HTTPException(404, "Order not found")
    valid_statuses = ["accepted", "preparing", "cancelled"]
    if status not in valid_statuses:
        raise HTTPException(400, f"Merchant can set status to: {valid_statuses}")
    order.status = status
    db.commit()
    return {"message": f"Order {order_id} status updated to {status}"}
