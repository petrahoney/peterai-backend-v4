import stripe
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import Subscription, PaymentTransaction

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

class StripeService:
    @staticmethod
    def create_customer(user, db: Session):
        existing = db.query(Subscription).filter(
            Subscription.user_id == user.id,
            Subscription.stripe_customer_id != None
        ).first()
        
        if existing:
            return existing.stripe_customer_id
        
        customer = stripe.Customer.create(
            email=user.email,
            name=user.full_name,
            metadata={"user_id": user.id}
        )
        return customer.id
    
    @staticmethod
    def create_subscription(user, db: Session, plan: str = "pro"):
        customer_id = StripeService.create_customer(user, db)
        
        plans = {
            "pro": {"price_id": "price_test_pro", "monthly_price": 9.99, "videos": 20},
            "pro_plus": {"price_id": "price_test_pro_plus", "monthly_price": 19.99, "videos": 50}
        }
        
        plan_config = plans.get(plan, plans["pro"])
        
        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": plan_config["price_id"]}],
            payment_behavior="default_incomplete",
            expand=["latest_invoice.payment_intent"]
        )
        
        db_subscription = Subscription(
            user_id=user.id,
            plan=plan,
            status="pending",
            stripe_customer_id=customer_id,
            stripe_subscription_id=subscription.id,
            monthly_price=plan_config["monthly_price"],
            videos_per_month=plan_config["videos"],
            renews_at=datetime.utcnow() + timedelta(days=30)
        )
        db.add(db_subscription)
        db.commit()
        db.refresh(db_subscription)
        
        return {
            "subscription_id": subscription.id,
            "client_secret": subscription.latest_invoice.payment_intent.client_secret
        }

