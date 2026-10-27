from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List

from models import get_db, Order, OrderItem, MenuItem, Merchant, User, Review, RiderLocation
from auth import get_current_user, require_role, log_audit

router = APIRouter(prefix="/api/orders", tags=["Orders"])

class OrderItemRequest(BaseModel):
    menu_item_id: int
    quantity: int

class PlaceOrderRequest(BaseModel):
    merchant_id: int
    items: List[OrderItemRequest]
    delivery_address: str
    delivery_latitude: float = 0
    delivery_longitude: float = 0
    note: str = ""
    payment_method: str = "cash"

@router.post("/place")
def place_order(req: PlaceOrderRequest, user: User = Depends(require_role("customer")),
                db: Session = Depends(get_db)):
    merchant = db.query(Merchant).filter(Merchant.id == req.merchant_id).first()
    if not merchant:
        raise HTTPException(404, "Merchant not found")

    total = 0.0
    order_items_data = []
    for item_req in req.items:
        menu_item = db.query(MenuItem).filter(
            MenuItem.id == item_req.menu_item_id,
            MenuItem.merchant_id == req.merchant_id,
            MenuItem.is_available == True
        ).first()
        if not menu_item:
            raise HTTPException(404, f"Menu item {item_req.menu_item_id} not found")
        if menu_item.stock < item_req.quantity:
            raise HTTPException(400, f"Insufficient stock for {menu_item.name}")
        total += menu_item.price * item_req.quantity
        order_items_data.append({"menu_item": menu_item, "quantity": item_req.quantity})

    order = Order(
        customer_id=user.id,
        merchant_id=req.merchant_id,
        total_price=round(total, 2),
        delivery_address=req.delivery_address,
        delivery_latitude=req.delivery_latitude,
        delivery_longitude=req.delivery_longitude,
        note=req.note,
        payment_method=req.payment_method,
        status="pending"
    )
    db.add(order)
    db.flush()

    for data in order_items_data:
        mi = data["menu_item"]
        oi = OrderItem(order_id=order.id, menu_item_id=mi.id,
                       quantity=data["quantity"], unit_price=mi.price)
        db.add(oi)
        mi.stock -= data["quantity"]

    db.commit()
    db.refresh(order)

    return {"message": "Order placed", "order_id": order.id, "total_price": order.total_price}

@router.get("/my")
def get_my_orders(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role.value == "customer":
        orders = db.query(Order).filter(Order.customer_id == user.id).order_by(Order.created_at.desc()).all()
    elif user.role.value == "rider":
        orders = db.query(Order).filter(
            (Order.rider_id == user.id) | (Order.status.in_(["pending", "accepted", "preparing", "picked_up"]))
        ).order_by(Order.created_at.desc()).all()
    else:
        orders = db.query(Order).order_by(Order.created_at.desc()).all()

    result = []
    for o in orders:
        customer = db.query(User).filter(User.id == o.customer_id).first()
        merchant = db.query(Merchant).filter(Merchant.id == o.merchant_id).first()
        rider = db.query(User).filter(User.id == o.rider_id).first() if o.rider_id else None
        items = db.query(OrderItem).filter(OrderItem.order_id == o.id).all()
        result.append({
            "id": o.id, "status": o.status.value, "total_price": o.total_price,
            "delivery_address": o.delivery_address, "note": o.note,
            "payment_method": o.payment_method, "created_at": o.created_at.isoformat(),
            "customer_name": customer.username if customer else "Unknown",
            "merchant_name": merchant.name if merchant else "Unknown",
            "rider_name": rider.username if rider else None,
            "delivery_latitude": o.delivery_latitude,
            "delivery_longitude": o.delivery_longitude,
            "items": [{"id": i.id, "menu_item_id": i.menu_item_id, "quantity": i.quantity, "unit_price": i.unit_price} for i in items]
        })
    return result

@router.get("/available")
def get_available_orders(user: User = Depends(require_role("rider")), db: Session = Depends(get_db)):
    orders = db.query(Order).filter(Order.status == "pending").order_by(Order.created_at.asc()).all()
    result = []
    for o in orders:
        merchant = db.query(Merchant).filter(Merchant.id == o.merchant_id).first()
        customer = db.query(User).filter(User.id == o.customer_id).first()
        result.append({
            "id": o.id, "total_price": o.total_price,
            "delivery_address": o.delivery_address,
            "merchant_name": merchant.name if merchant else "Unknown",
            "customer_name": customer.username if customer else "Unknown",
            "created_at": o.created_at.isoformat()
        })
    return result

@router.post("/{order_id}/accept")
def accept_order(order_id: int, user: User = Depends(require_role("rider")),
                 db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id, Order.status == "pending").first()
    if not order:
        raise HTTPException(404, "Order not available")
    order.rider_id = user.id
    order.status = "accepted"
    db.commit()
    return {"message": f"Order {order_id} accepted", "order_id": order.id}

@router.post("/{order_id}/status")
def update_order_status(order_id: int, status: str,
                        user: User = Depends(require_role("rider")),
                        db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id, Order.rider_id == user.id).first()
    if not order:
        raise HTTPException(404, "Order not found or not assigned to you")
    valid = {"picked_up", "delivering", "delivered"}
    if status not in valid:
        raise HTTPException(400, f"Rider can set status to: {valid}")
    order.status = status
    db.commit()
    return {"message": f"Order {order_id} updated to {status}"}

@router.post("/{order_id}/cancel")
def cancel_order(order_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Order not found")
    if order.customer_id != user.id and user.role.value not in ["regulator", "analyst"]:
        raise HTTPException(403, "Not authorized to cancel this order")
    if order.status not in ["pending", "accepted"]:
        raise HTTPException(400, "Order cannot be cancelled at this stage")
    order.status = "cancelled"
    # Restore stock
    items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    for item in items:
        menu_item = db.query(MenuItem).filter(MenuItem.id == item.menu_item_id).first()
        if menu_item:
            menu_item.stock += item.quantity
    db.commit()
    return {"message": "Order cancelled"}

# --- Reviews ---
class ReviewCreate(BaseModel):
    order_id: int
    rating: int
    content: str = ""

@router.post("/review")
def create_review(req: ReviewCreate, user: User = Depends(require_role("customer")),
                  db: Session = Depends(get_db)):
    order = db.query(Order).filter(
        Order.id == req.order_id,
        Order.customer_id == user.id,
        Order.status == "delivered"
    ).first()
    if not order:
        raise HTTPException(404, "Delivered order not found")
    existing = db.query(Review).filter(Review.order_id == req.order_id).first()
    if existing:
        raise HTTPException(400, "Already reviewed")
    if req.rating < 1 or req.rating > 5:
        raise HTTPException(400, "Rating must be 1-5")
    review = Review(order_id=req.order_id, customer_id=user.id,
                    merchant_id=order.merchant_id, rating=req.rating, content=req.content)
    db.add(review)
    # Update merchant rating
    merchant = db.query(Merchant).filter(Merchant.id == order.merchant_id).first()
    if merchant:
        all_reviews = db.query(Review).filter(Review.merchant_id == merchant.id).all()
        merchant.rating = round(sum(r.rating for r in all_reviews) / len(all_reviews), 1)
    db.commit()
    return {"message": "Review submitted", "rating": req.rating}
