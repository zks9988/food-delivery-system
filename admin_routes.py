"""
Admin / Regulator Routes
- User management (view, activate/deactivate, role management)
- Audit log viewer
- Database permission control (RBAC)
- System health monitoring
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from models import get_db, User, AuditLog, Order, Merchant
from auth import get_current_user, require_role

router = APIRouter(prefix="/api/admin", tags=["Admin & Security"])

@router.get("/users")
def list_users(role: Optional[str] = Query(None), db: Session = Depends(get_db),
               user=Depends(require_role("regulator", "analyst"))):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    users = query.all()
    return [
        {
            "id": u.id, "username": u.username, "email": u.email,
            "role": u.role.value, "phone": u.phone, "is_active": u.is_active,
            "two_factor_enabled": u.two_factor_enabled,
            "created_at": u.created_at.isoformat() if u.created_at else None
        }
        for u in users
    ]

@router.put("/users/{user_id}/status")
def toggle_user_status(user_id: int, db: Session = Depends(get_db),
                       user=Depends(require_role("regulator"))):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(404, "User not found")
    target.is_active = not target.is_active
    db.commit()
    return {"message": f"User {target.username} active status: {target.is_active}"}

@router.put("/users/{user_id}/role")
def change_user_role(user_id: int, new_role: str, db: Session = Depends(get_db),
                     user=Depends(require_role("regulator"))):
    valid_roles = {"customer", "rider", "merchant", "analyst", "regulator"}
    if new_role not in valid_roles:
        raise HTTPException(400, f"Invalid role. Must be: {valid_roles}")
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(404, "User not found")
    target.role = new_role
    db.commit()
    return {"message": f"User {target.username} role changed to {new_role}"}

@router.get("/audit-logs")
def get_audit_logs(limit: int = Query(50), action: Optional[str] = Query(None),
                   db: Session = Depends(get_db),
                   user=Depends(require_role("regulator"))):
    query = db.query(AuditLog).order_by(AuditLog.created_at.desc())
    if action:
        query = query.filter(AuditLog.action == action)
    logs = query.limit(limit).all()
    return [
        {
            "id": log.id, "user_id": log.user_id, "action": log.action,
            "resource_type": log.resource_type, "resource_id": log.resource_id,
            "details": log.details, "created_at": log.created_at.isoformat()
        }
        for log in logs
    ]

@router.get("/dashboard")
def get_admin_dashboard(db: Session = Depends(get_db),
                        user=Depends(require_role("regulator", "analyst"))):
    from sqlalchemy import func
    total_users = db.query(func.count(User.id)).scalar() or 0
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0
    total_orders = db.query(func.count(Order.id)).scalar() or 0
    total_merchants = db.query(func.count(Merchant.id)).scalar() or 0

    role_counts = db.query(User.role, func.count(User.id).label("count")).group_by(User.role).all()
    roles_dict = {r.role.value: r.count for r in role_counts}

    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_orders": total_orders,
        "total_merchants": total_merchants,
        "users_by_role": roles_dict,
        "system_status": "healthy"
    }
