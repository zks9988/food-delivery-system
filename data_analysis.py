"""
Data Analysis Service
- Multi-dimensional data analysis
- Data visualization data preparation
- Aggregation queries
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, case, text
from datetime import datetime, timedelta, date
from models import Order, OrderItem, Merchant, User, Review, RiderLocation

class DataAnalysisService:

    @staticmethod
    def sales_overview(db: Session, merchant_id: int = None, days: int = 30):
        """Sales overview for last N days"""
        since = datetime.now() - timedelta(days=days)
        query = db.query(
            func.date(Order.created_at).label("date"),
            func.count(Order.id).label("order_count"),
            func.sum(Order.total_price).label("total_sales"),
            func.avg(Order.total_price).label("avg_order_value")
        ).filter(Order.created_at >= since)

        if merchant_id:
            query = query.filter(Order.merchant_id == merchant_id)

        # Exclude cancelled
        query = query.filter(Order.status != "cancelled")
        result = query.group_by(func.date(Order.created_at)).order_by(func.date(Order.created_at)).all()

        return [
            {
                "date": str(r.date),
                "order_count": r.order_count,
                "total_sales": float(r.total_sales) if r.total_sales else 0,
                "avg_order_value": round(float(r.avg_order_value), 2) if r.avg_order_value else 0
            }
            for r in result
        ]

    @staticmethod
    def cuisine_distribution(db: Session):
        """Orders grouped by cuisine type"""
        result = db.query(
            Merchant.cuisine_type,
            func.count(Order.id).label("order_count"),
            func.sum(Order.total_price).label("total_sales")
        ).join(Order, Order.merchant_id == Merchant.id
        ).filter(Order.status != "cancelled"
        ).group_by(Merchant.cuisine_type).all()

        return [
            {"cuisine": r.cuisine_type or "Other", "order_count": r.order_count,
             "total_sales": float(r.total_sales) if r.total_sales else 0}
            for r in result
        ]

    @staticmethod
    def rider_performance(db: Session, days: int = 7):
        """Rider delivery performance"""
        since = datetime.now() - timedelta(days=days)
        result = db.query(
            User.id.label("rider_id"),
            User.username.label("rider_name"),
            func.count(Order.id).label("deliveries"),
            func.sum(case((Order.status == "delivered", 1), else_=0)).label("completed"),
            func.avg(
                func.strftime('%s', Order.updated_at) - func.strftime('%s', Order.created_at)
            ).label("avg_delivery_time_seconds")
        ).join(Order, Order.rider_id == User.id
        ).filter(Order.created_at >= since
        ).group_by(User.id).all()

        return [
            {
                "rider_id": r.rider_id,
                "rider_name": r.rider_name,
                "deliveries": r.deliveries,
                "completed": r.completed,
                "avg_delivery_time_min": round(float(r.avg_delivery_time_seconds) / 60, 1) if r.avg_delivery_time_seconds else 0
            }
            for r in result
        ]

    @staticmethod
    def customer_orders_analysis(db: Session):
        """Customer ordering patterns"""
        result = db.query(
            User.id.label("customer_id"),
            User.username.label("customer_name"),
            func.count(Order.id).label("total_orders"),
            func.sum(Order.total_price).label("total_spent"),
            func.avg(Order.total_price).label("avg_order_value"),
            func.max(Order.created_at).label("last_order_date")
        ).join(Order, Order.customer_id == User.id
        ).filter(Order.status != "cancelled"
        ).group_by(User.id).order_by(func.count(Order.id).desc()).all()

        return [
            {
                "customer_id": r.customer_id,
                "customer_name": r.customer_name,
                "total_orders": r.total_orders,
                "total_spent": float(r.total_spent) if r.total_spent else 0,
                "avg_order_value": round(float(r.avg_order_value), 2) if r.avg_order_value else 0,
                "last_order_date": str(r.last_order_date) if r.last_order_date else "N/A"
            }
            for r in result
        ]

    @staticmethod
    def hourly_order_distribution(db: Session):
        """Orders by hour of day"""
        # Use simpler approach for SQLite compat
        all_orders = db.query(Order).filter(Order.status != "cancelled").all()
        hourly = {}
        for o in all_orders:
            if o.created_at:
                h = o.created_at.hour
                hourly[h] = hourly.get(h, 0) + 1
        return [{"hour": h, "order_count": c} for h, c in sorted(hourly.items())]

    @staticmethod
    def revenue_by_payment_method(db: Session, days: int = 30):
        """Revenue grouped by payment method"""
        since = datetime.now() - timedelta(days=days)
        result = db.query(
            Order.payment_method,
            func.count(Order.id).label("count"),
            func.sum(Order.total_price).label("total")
        ).filter(Order.created_at >= since, Order.status != "cancelled"
        ).group_by(Order.payment_method).all()

        return [
            {"method": r.payment_method, "count": r.count,
             "total": float(r.total) if r.total else 0}
            for r in result
        ]

    @staticmethod
    def rating_distribution(db: Session):
        """Distribution of ratings"""
        result = db.query(
            Review.rating,
            func.count(Review.id).label("count")
        ).group_by(Review.rating).order_by(Review.rating).all()

        return [{"rating": r.rating, "count": r.count} for r in result]

    @staticmethod
    def overall_stats(db: Session):
        """Quick overall statistics"""
        total_users = db.query(func.count(User.id)).scalar() or 0
        total_orders = db.query(func.count(Order.id)).scalar() or 0
        total_merchants = db.query(func.count(Merchant.id)).scalar() or 0
        total_revenue = db.query(func.sum(Order.total_price)).filter(
            Order.status != "cancelled"
        ).scalar() or 0
        avg_rating = db.query(func.avg(Review.rating)).scalar() or 0

        return {
            "total_users": total_users,
            "total_orders": total_orders,
            "total_merchants": total_merchants,
            "total_revenue": round(float(total_revenue), 2),
            "average_rating": round(float(avg_rating), 2)
        }
