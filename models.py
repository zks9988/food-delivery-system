from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, Date, Time, JSON, Enum
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone
import enum

from config import DB_URL

engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if "sqlite" in DB_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# -------------------- Enums --------------------
class UserRole(str, enum.Enum):
    customer = "customer"
    rider = "rider"
    merchant = "merchant"
    analyst = "analyst"
    regulator = "regulator"

class OrderStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    preparing = "preparing"
    picked_up = "picked_up"
    delivering = "delivering"
    delivered = "delivered"
    cancelled = "cancelled"

# -------------------- Models --------------------
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.customer)
    phone = Column(String(20))
    avatar_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(255))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Merchant(Base):
    __tablename__ = "merchants"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    address = Column(String(500))
    latitude = Column(Float)
    longitude = Column(Float)
    cuisine_type = Column(String(100))
    rating = Column(Float, default=0.0)
    open_time = Column(Time, default=lambda: datetime.strptime("09:00", "%H:%M").time())
    close_time = Column(Time, default=lambda: datetime.strptime("22:00", "%H:%M").time())
    is_open = Column(Boolean, default=True)
    image_url = Column(String(500))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class MenuItem(Base):
    __tablename__ = "menu_items"
    id = Column(Integer, primary_key=True, index=True)
    merchant_id = Column(Integer, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    category = Column(String(100))
    image_url = Column(String(500))
    is_available = Column(Boolean, default=True)
    stock = Column(Integer, default=999)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, nullable=False)
    merchant_id = Column(Integer, nullable=False)
    rider_id = Column(Integer, nullable=True)
    status = Column(Enum(OrderStatus), default=OrderStatus.pending)
    total_price = Column(Float, nullable=False)
    delivery_address = Column(String(500), nullable=False)
    delivery_latitude = Column(Float)
    delivery_longitude = Column(Float)
    note = Column(Text)
    payment_method = Column(String(50), default="cash")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, nullable=False)
    menu_item_id = Column(Integer, nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, nullable=False)

class RiderLocation(Base):
    __tablename__ = "rider_locations"
    id = Column(Integer, primary_key=True, index=True)
    rider_id = Column(Integer, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    accuracy = Column(Float)
    speed = Column(Float)
    bearing = Column(Float)
    extra_data = Column(JSON)
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, unique=True, nullable=False)
    customer_id = Column(Integer, nullable=False)
    merchant_id = Column(Integer, nullable=False)
    rating = Column(Integer, nullable=False)
    content = Column(Text)
    images = Column(JSON)
    extra_meta = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    token = Column(String(255), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    action = Column(String(200), nullable=False)
    resource_type = Column(String(100))
    resource_id = Column(Integer)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    details = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class SalesPrediction(Base):
    __tablename__ = "sales_predictions"
    id = Column(Integer, primary_key=True, index=True)
    merchant_id = Column(Integer, nullable=False)
    predicted_date = Column(Date, nullable=False)
    predicted_sales = Column(Float)
    confidence = Column(Float)
    model_version = Column(String(50))
    features_used = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class UserSession(Base):
    __tablename__ = "user_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    session_token = Column(String(255), nullable=False)
    refresh_token = Column(String(255))
    device_info = Column(String(500))
    ip_address = Column(String(45))
    is_active = Column(Boolean, default=True)
    login_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime)

def init_db():
    Base.metadata.create_all(bind=engine)
    print("[DB] Database initialized successfully")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
