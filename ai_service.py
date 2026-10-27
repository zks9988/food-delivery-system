"""
AI Service - Sales Prediction using Linear Regression
Demonstrates applying AI algorithms for predictive analytics.
"""
import pickle
import numpy as np
import json
import os
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from sqlalchemy import func
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

from models import Order, Merchant, SalesPrediction

AI_MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "sales_predictor.pkl")

class AIService:

    @staticmethod
    def train_sales_model(db: Session, merchant_id: int = None):
        """Train a linear regression model for sales prediction"""
        query = db.query(
            func.date(Order.created_at).label("date"),
            func.count(Order.id).label("order_count"),
            func.sum(Order.total_price).label("total_sales")
        ).filter(Order.status != "cancelled")

        if merchant_id:
            query = query.filter(Order.merchant_id == merchant_id)

        results = query.group_by(func.date(Order.created_at)).order_by(func.date(Order.created_at)).all()

        if len(results) < 7:
            return {"error": "Not enough data to train model (need at least 7 days)"}

        # Feature engineering
        X, y = [], []
        for i in range(len(results) - 1):
            r = results[i]
            dt = datetime.strptime(str(r.date), "%Y-%m-%d")
            features = [
                dt.weekday(),       # Day of week (0=Mon)
                dt.day,             # Day of month
                dt.month,           # Month
                float(r.total_sales) if r.total_sales else 0,  # Previous day sales
                r.order_count       # Previous day order count
            ]
            X.append(features)
            next_sales = float(results[i + 1].total_sales) if results[i + 1].total_sales else 0
            y.append(next_sales)

        X = np.array(X)
        y = np.array(y)

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        model = LinearRegression()
        model.fit(X_scaled, y)

        score = model.score(X_scaled, y)

        # Save model
        model_data = {
            "model": model,
            "scaler": scaler,
            "merchant_id": merchant_id,
            "score": score,
            "trained_at": datetime.now().isoformat()
        }
        os.makedirs(os.path.dirname(AI_MODEL_PATH), exist_ok=True)
        with open(AI_MODEL_PATH, "wb") as f:
            pickle.dump(model_data, f)

        return {
            "message": "Model trained successfully",
            "r2_score": round(score, 4),
            "training_samples": len(X),
            "merchant_id": merchant_id
        }

    @staticmethod
    def predict_sales(db: Session, merchant_id: int = None, days_ahead: int = 7):
        """Predict sales for the next N days"""
        # Try to load cached predictions
        if merchant_id:
            today = date.today()
            cached = db.query(SalesPrediction).filter(
                SalesPrediction.merchant_id == merchant_id,
                SalesPrediction.predicted_date >= today
            ).order_by(SalesPrediction.predicted_date).all()
            if len(cached) >= days_ahead:
                return [{"date": str(c.predicted_date), "predicted_sales": c.predicted_sales,
                         "confidence": c.confidence} for c in cached[:days_ahead]]

        # Train or load model
        try:
            with open(AI_MODEL_PATH, "rb") as f:
                model_data = pickle.load(f)
            model = model_data["model"]
            scaler = model_data["scaler"]
        except FileNotFoundError:
            result = AIService.train_sales_model(db, merchant_id)
            if "error" in result:
                return result
            with open(AI_MODEL_PATH, "rb") as f:
                model_data = pickle.load(f)
            model = model_data["model"]
            scaler = model_data["scaler"]

        predictions = []
        today = datetime.now()

        for day in range(1, days_ahead + 1):
            pred_date = today + timedelta(days=day)
            # Use average of last 7 days as features
            seven_days_ago = today - timedelta(days=7)
            recent = db.query(
                func.avg(Order.total_price).label("avg_sales"),
                func.count(Order.id).label("avg_orders")
            ).filter(Order.created_at >= seven_days_ago)

            if merchant_id:
                recent = recent.filter(Order.merchant_id == merchant_id)

            recent_data = recent.first()
            avg_sales = float(recent_data.avg_sales) if recent_data and recent_data.avg_sales else 100
            avg_orders = recent_data.avg_orders if recent_data and recent_data.avg_orders else 5

            features = np.array([[
                pred_date.weekday(), pred_date.day, pred_date.month,
                avg_sales, avg_orders
            ]])
            features_scaled = scaler.transform(features)
            pred = float(model.predict(features_scaled)[0])
            pred = max(0, round(pred, 2))  # Sales can't be negative

            predictions.append({
                "date": pred_date.strftime("%Y-%m-%d"),
                "predicted_sales": pred,
                "confidence": round(model_data["score"], 2) if "score" in model_data else 0.5
            })

            # Cache prediction
            if merchant_id:
                existing = db.query(SalesPrediction).filter(
                    SalesPrediction.merchant_id == merchant_id,
                    SalesPrediction.predicted_date == pred_date.date()
                ).first()
                if existing:
                    existing.predicted_sales = pred
                else:
                    sp = SalesPrediction(
                        merchant_id=merchant_id,
                        predicted_date=pred_date.date(),
                        predicted_sales=pred,
                        confidence=round(model_data["score"], 2) if "score" in model_data else 0.5,
                        model_version="lr_v1",
                        features_used={"day_of_week", "day_of_month", "month", "avg_sales_7d", "avg_orders_7d"}
                    )
                    db.add(sp)
                db.commit()

        return predictions

    @staticmethod
    def recommend_menu_items(db: Session, user_id: int, top_n: int = 5):
        """
        Simple recommendation based on user's order history
        - Find frequently ordered categories
        - Recommend items from those categories not yet ordered
        """
        from models import OrderItem, MenuItem, User

        # Get user's order history
        user_orders = db.query(Order).filter(Order.customer_id == user_id, Order.status != "cancelled").all()
        if not user_orders:
            # No history: return popular items
            popular = db.query(
                MenuItem.id, MenuItem.name, MenuItem.price, MenuItem.category,
                MenuItem.merchant_id,
                func.count(OrderItem.id).label("order_count")
            ).join(OrderItem, OrderItem.menu_item_id == MenuItem.id
            ).join(Order, Order.id == OrderItem.order_id
            ).filter(Order.status != "cancelled"
            ).group_by(MenuItem.id).order_by(func.count(OrderItem.id).desc()).limit(top_n).all()

            return [{"id": r.id, "name": r.name, "price": r.price, "category": r.category,
                     "merchant_id": r.merchant_id, "reason": "Popular item"} for r in popular]

        # Get user's preferred categories
        order_ids = [o.id for o in user_orders]
        preferred = db.query(
            MenuItem.category,
            func.count(OrderItem.id).label("count")
        ).join(OrderItem, OrderItem.menu_item_id == MenuItem.id
        ).filter(OrderItem.order_id.in_(order_ids)
        ).group_by(MenuItem.category).order_by(func.count(OrderItem.id).desc()).all()

        preferred_categories = [p.category for p in preferred if p.category]

        # Get items user already ordered
        ordered_items = db.query(MenuItem.id).join(
            OrderItem, OrderItem.menu_item_id == MenuItem.id
        ).filter(OrderItem.order_id.in_(order_ids)).all()
        ordered_ids = {item.id for item in ordered_items}

        # Recommend items from preferred categories not yet ordered
        if preferred_categories:
            recommendations = db.query(MenuItem).filter(
                MenuItem.category.in_(preferred_categories),
                MenuItem.id.notin_(ordered_ids) if ordered_ids else True,
                MenuItem.is_available == True
            ).limit(top_n).all()
        else:
            recommendations = []

        # Fill remaining slots with popular items
        if len(recommendations) < top_n:
            existing_ids = {r.id for r in recommendations}
            popular = db.query(MenuItem).filter(
                MenuItem.id.notin_(existing_ids) if existing_ids else True,
                MenuItem.is_available == True
            ).limit(top_n - len(recommendations)).all()
            recommendations.extend(popular)

        return [{"id": r.id, "name": r.name, "price": r.price, "category": r.category,
                 "merchant_id": r.merchant_id, "reason": "Based on your preferences"}
                for r in recommendations[:top_n]]
