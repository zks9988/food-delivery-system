from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from models import get_db, User, PasswordResetToken, UserSession
from auth import (hash_password, verify_password, create_access_token, create_refresh_token,
                  decode_token, get_current_user, generate_2fa_secret, get_2fa_uri,
                  verify_2fa_code, generate_reset_token, log_audit)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# ==================== Schemas ====================
class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    phone: str = ""
    role: str = "customer"

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict

class TwoFactorVerifyRequest(BaseModel):
    code: str

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class WechatLoginRequest(BaseModel):
    code: str

# ==================== Routes ====================

@router.post("/register")
def register(req: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    if db.query(User).filter((User.username == req.username) | (User.email == req.email)).first():
        raise HTTPException(400, "Username or email already exists")

    valid_roles = {"customer", "rider", "merchant", "analyst", "regulator"}
    if req.role not in valid_roles:
        raise HTTPException(400, f"Invalid role. Must be one of: {valid_roles}")

    user = User(
        username=req.username,
        email=req.email,
        password_hash=hash_password(req.password),
        role=req.role,
        phone=req.phone
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_audit(db, user.id, "user.register", "user", user.id,
              ip=request.client.host if request.client else None)

    access_token = create_access_token(user.id, user.role.value)
    refresh_token = create_refresh_token(user.id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id, "username": user.username, "email": user.email,
            "role": user.role.value, "phone": user.phone, "avatar_url": user.avatar_url
        }
    }

@router.post("/login")
def login(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(401, "Invalid username or password")
    if not user.is_active:
        raise HTTPException(403, "Account is deactivated")

    log_audit(db, user.id, "user.login", "user", user.id,
              ip=request.client.host if request.client else None)

    # If 2FA enabled, return partial token
    if user.two_factor_enabled:
        partial = create_access_token(user.id, user.role.value) + "_2fa_pending"
        return {"need_2fa": True, "partial_token": partial}

    access_token = create_access_token(user.id, user.role.value)
    refresh_token = create_refresh_token(user.id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id, "username": user.username, "email": user.email,
            "role": user.role.value, "phone": user.phone, "avatar_url": user.avatar_url
        }
    }

@router.post("/login/2fa")
def verify_2fa(req: TwoFactorVerifyRequest, request: Request, db: Session = Depends(get_db)):
    # Decode partial token
    try:
        payload = decode_token(req.code.replace("_2fa_pending", ""))
    except:
        raise HTTPException(400, "Invalid token")

    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user or not user.two_factor_enabled or not user.two_factor_secret:
        raise HTTPException(400, "2FA not configured")

    # The actual 2FA code is sent separately — for this demo, we accept the token
    log_audit(db, user.id, "user.2fa_verified", "user", user.id,
              ip=request.client.host if request.client else None)

    access_token = create_access_token(user.id, user.role.value)
    refresh_token = create_refresh_token(user.id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id, "username": user.username, "email": user.email,
            "role": user.role.value, "phone": user.phone, "avatar_url": user.avatar_url
        }
    }

@router.post("/2fa/setup")
def setup_2fa(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    secret = generate_2fa_secret()
    user.two_factor_secret = secret
    user.two_factor_enabled = True
    db.commit()
    uri = get_2fa_uri(secret, user.email)
    return {"secret": secret, "uri": uri, "message": "Scan with Google Authenticator or similar"}

@router.post("/2fa/disable")
def disable_2fa(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user.two_factor_enabled = False
    user.two_factor_secret = None
    db.commit()
    return {"message": "2FA disabled"}

@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        # Don't reveal whether email exists
        return {"message": "If the email exists, a reset link has been sent"}
    token = generate_reset_token()
    expires = datetime.now(timezone.utc) + timedelta(hours=1)
    reset = PasswordResetToken(user_id=user.id, token=token, expires_at=expires)
    db.add(reset)
    db.commit()
    # In production, send email. For demo, return token directly.
    return {"message": "Reset link sent", "reset_token": token}

@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    reset = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == req.token,
        PasswordResetToken.used == False,
        PasswordResetToken.expires_at > datetime.now(timezone.utc)
    ).first()
    if not reset:
        raise HTTPException(400, "Invalid or expired token")
    user = db.query(User).filter(User.id == reset.user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    user.password_hash = hash_password(req.new_password)
    reset.used = True
    db.commit()
    return {"message": "Password reset successful"}

@router.post("/wechat-login")
def wechat_login(req: WechatLoginRequest, request: Request, db: Session = Depends(get_db)):
    # Simulate WeChat OAuth: in production, call WeChat API with req.code
    # For demo, we use a simulated user lookup
    simulated_openid = f"wx_openid_{req.code[-8:] if len(req.code) >= 8 else req.code}"
    simulated_userinfo = {"nickname": f"微信用户_{req.code[:4]}", "avatar": ""}

    # Find or create user by WeChat ID
    user = db.query(User).filter(User.username == simulated_openid).first()
    if not user:
        user = User(
            username=simulated_openid,
            email=f"{simulated_openid}@wechat.sim",
            password_hash=hash_password(simulated_openid + "_wx_pwd"),
            role="customer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    log_audit(db, user.id, "user.wechat_login", "user", user.id,
              ip=request.client.host if request.client else None)

    access_token = create_access_token(user.id, user.role.value)
    refresh_token = create_refresh_token(user.id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id, "username": simulated_userinfo["nickname"],
            "email": user.email, "role": user.role.value, "phone": user.phone
        }
    }

@router.post("/refresh")
def refresh_token(token_data: dict, db: Session = Depends(get_db)):
    token = token_data.get("refresh_token", "")
    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise HTTPException(401, "Invalid token type")
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user:
        raise HTTPException(404, "User not found")
    access_token = create_access_token(user.id, user.role.value)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me")
def get_profile(user: User = Depends(get_current_user)):
    return {
        "id": user.id, "username": user.username, "email": user.email,
        "role": user.role.value, "phone": user.phone, "avatar_url": user.avatar_url,
        "two_factor_enabled": user.two_factor_enabled, "is_active": user.is_active
    }

@router.get("/roles")
def get_roles():
    return {"roles": ["customer", "rider", "merchant", "analyst", "regulator"]}
