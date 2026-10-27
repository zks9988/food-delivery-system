import os
from datetime import timedelta
import json

# Database - switch to mysql by changing DB_URL
# MySQL: "mysql+pymysql://user:pass@localhost:3306/food_delivery"
DB_URL = os.getenv("DATABASE_URL", "sqlite:///./food_delivery.db")

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-f0od-d3l1v3ry")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE = timedelta(hours=2)
REFRESH_TOKEN_EXPIRE = timedelta(days=7)

# Password encryption
BCRYPT_ROUNDS = 12

# Server
HOST = "0.0.0.0"
PORT = 8000

# GPS tracking interval (seconds)
GPS_TRACKING_INTERVAL = 10

# Unstructured data storage: can be filesystem, or cloud (S3, etc.)
# For this project, we store JSON in DB and files on disk
UNSTRUCTURED_STORAGE_PATH = "./unstructured_data"

# WeChat login simulation config
WECHAT_APP_ID = "sim_wx_app_id"
WECHAT_APP_SECRET = "sim_wx_app_secret"

# AI Model config
AI_MODEL_PATH = "./models/sales_predictor.pkl"

os.makedirs(UNSTRUCTURED_STORAGE_PATH, exist_ok=True)
os.makedirs(os.path.dirname(AI_MODEL_PATH), exist_ok=True)
