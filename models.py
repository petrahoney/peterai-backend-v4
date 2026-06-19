from sqlalchemy import Column, String, Integer, DateTime, Float, Boolean, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_premium = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    plan = Column(String)  # "pro", "professional", "enterprise"
    status = Column(String)  # "active", "cancelled", "expired"
    stripe_customer_id = Column(String, unique=True)
    stripe_subscription_id = Column(String)
    monthly_price = Column(Float)
    videos_per_month = Column(Integer)
    videos_used = Column(Integer, default=0)
    renews_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Video(Base):
    __tablename__ = "videos"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    title = Column(String)
    prompt = Column(Text)
    status = Column(String)  # "processing", "completed", "failed"
    video_url = Column(String)
    duration_seconds = Column(Integer)
    file_size_mb = Column(Float)
    thumbnail_url = Column(String)
    youtube_url = Column(String)
    celery_task_id = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    subscription_id = Column(Integer, index=True)
    amount = Column(Float)
    currency = Column(String, default="USD")
    status = Column(String)  # "pending", "completed", "failed"
    stripe_payment_id = Column(String)
    midtrans_transaction_id = Column(String)
    payment_method = Column(String)  # "stripe", "midtrans"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

