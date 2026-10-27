from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from models import get_db
from auth import get_current_user, require_role
from services.data_analysis import DataAnalysisService
from services.ai_service import AIService

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/overview")
def get_overview(db: Session = Depends(get_db),
                 user=Depends(require_role("analyst", "merchant", "regulator"))):
    return DataAnalysisService.overall_stats(db)

@router.get("/sales")
def get_sales(merchant_id: Optional[int] = Query(None), days: int = Query(30),
              db: Session = Depends(get_db),
              user=Depends(require_role("analyst", "merchant", "regulator"))):
    return DataAnalysisService.sales_overview(db, merchant_id, days)

@router.get("/cuisine-distribution")
def get_cuisine_distribution(db: Session = Depends(get_db),
                             user=Depends(require_role("analyst", "regulator"))):
    return DataAnalysisService.cuisine_distribution(db)

@router.get("/rider-performance")
def get_rider_performance(days: int = Query(7), db: Session = Depends(get_db),
                          user=Depends(require_role("analyst", "regulator"))):
    return DataAnalysisService.rider_performance(db, days)

@router.get("/customer-analysis")
def get_customer_analysis(db: Session = Depends(get_db),
                          user=Depends(require_role("analyst", "regulator"))):
    return DataAnalysisService.customer_orders_analysis(db)

@router.get("/hourly-distribution")
def get_hourly_distribution(db: Session = Depends(get_db),
                            user=Depends(require_role("analyst", "regulator"))):
    return DataAnalysisService.hourly_order_distribution(db)

@router.get("/payment-analysis")
def get_payment_analysis(days: int = Query(30), db: Session = Depends(get_db),
                         user=Depends(require_role("analyst", "regulator"))):
    return DataAnalysisService.revenue_by_payment_method(db, days)

@router.get("/rating-distribution")
def get_rating_distribution(db: Session = Depends(get_db),
                            user=Depends(require_role("analyst", "regulator"))):
    return DataAnalysisService.rating_distribution(db)

# --- AI Endpoints ---
@router.post("/ai/train")
def train_model(merchant_id: Optional[int] = Query(None), db: Session = Depends(get_db),
                user=Depends(require_role("analyst", "merchant"))):
    return AIService.train_sales_model(db, merchant_id)

@router.get("/ai/predict-sales")
def predict_sales(merchant_id: Optional[int] = Query(None), days: int = Query(7),
                  db: Session = Depends(get_db),
                  user=Depends(require_role("analyst", "merchant", "regulator"))):
    return AIService.predict_sales(db, merchant_id, days)

@router.get("/ai/recommendations")
def get_recommendations(top_n: int = Query(5), db: Session = Depends(get_db),
                        user=Depends(get_current_user)):
    return AIService.recommend_menu_items(db, user.id, top_n)
