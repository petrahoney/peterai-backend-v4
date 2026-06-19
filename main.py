from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta
import os
from dotenv import load_dotenv

from models import User, Video, Subscription
from schemas import UserRegister, UserLogin, UserResponse, VideoCreate, VideoResponse
from auth import create_access_token, verify_password, get_password_hash, decode_token, Token
import stripe
from database import get_db

load_dotenv()

app = FastAPI(title="PETER AI v4.0 Backend")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============= HEALTH CHECK =============
@app.get("/health")
async def health():
    return {"status": "healthy", "message": "PETER AI Backend Running"}

# ============= AUTH ENDPOINTS =============

@app.post("/api/auth/register", response_model=UserResponse)
async def register(user: UserRegister, db: Session = Depends(get_db)):
    """Register new user"""
    # Check if email exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check if username exists
    existing_username = db.query(User).filter(User.username == user.username).first()
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # Create user
    db_user = User(
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        hashed_password=get_password_hash(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/api/auth/login", response_model=Token)
async def login(user: UserLogin, db: Session = Depends(get_db)):
    """Login user and return JWT token"""
    db_user = db.query(User).filter(User.email == user.email).first()
    
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    access_token_expires = timedelta(days=7)
    access_token = create_access_token(
        data={"sub": db_user.email},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# ============= USER ENDPOINTS =============

@app.get("/api/user/me", response_model=UserResponse)
async def get_current_user(token: str = None, db: Session = Depends(get_db)):
    """Get current user profile"""
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    email = decode_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

# ============= VIDEO ENDPOINTS =============

@app.post("/api/videos/create", response_model=VideoResponse)
async def create_video(video: VideoCreate, token: str = None, db: Session = Depends(get_db)):
    """Create new video (send to Celery worker)"""
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    email = decode_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check subscription quota
    subscription = db.query(Subscription).filter(Subscription.user_id == user.id).first()
    if subscription and subscription.videos_used >= subscription.videos_per_month:
        raise HTTPException(status_code=429, detail="Video quota exceeded")
    
    # Create video record
    db_video = Video(
        user_id=user.id,
        title=video.title,
        prompt=video.prompt,
        status="queued"
    )
    db.add(db_video)
    db.commit()
    db.refresh(db_video)
    
    return db_video

@app.get("/api/videos/{video_id}", response_model=VideoResponse)
async def get_video(video_id: int, db: Session = Depends(get_db)):
    """Get video status"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video

@app.get("/api/videos", response_model=list[VideoResponse])
async def list_videos(token: str = None, db: Session = Depends(get_db)):
    """List user's videos"""
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    email = decode_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    videos = db.query(Video).filter(Video.user_id == user.id).all()
    return videos

@app.post("/api/videos/create")
def create_video(video: VideoCreate, token: str = Query(...), db: Session = Depends(get_db)):
    user = decode_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    db_video = Video(
        user_id=user["sub"],
        title=video.title,
        description=video.description,
        status="processing"
    )
    db.add(db_video)
    db.commit()
    db.refresh(db_video)
    return VideoResponse.from_orm(db_video)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


# ============= PAYMENT ENDPOINTS =============

from payment import StripeService

@app.post("/api/payments/create-subscription")
async def create_subscription(plan: str = "pro", token: str = None, db: Session = Depends(get_db)):
    """Create subscription for user"""
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    email = decode_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        result = StripeService.create_subscription(user, db, plan)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/payments/webhook")
async def stripe_webhook(request, db: Session = Depends(get_db)):
    """Handle Stripe webhook"""
    body = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        event = stripe.Webhook.construct_event(
            body, sig_header, os.getenv("STRIPE_WEBHOOK_SECRET")
        )
        StripeService.handle_payment_webhook(event, db)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

