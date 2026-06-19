from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

# User schemas
class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: str
    is_premium: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Subscription schemas
class SubscriptionResponse(BaseModel):
    id: int
    plan: str
    status: str
    videos_per_month: int
    videos_used: int
    monthly_price: float
    renews_at: datetime

    class Config:
        from_attributes = True

# Video schemas
class VideoCreate(BaseModel):
    title: str
    prompt: str

class VideoResponse(BaseModel):
    id: int
    title: str
    status: str
    video_url: Optional[str]
    youtube_url: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True

# Payment schemas
class PaymentResponse(BaseModel):
    id: int
    amount: float
    status: str
    payment_method: str
    created_at: datetime

    class Config:
        from_attributes = True

