from datetime import datetime, timedelta
from typing import Optional, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from config import settings
from database import get_db, User

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token handler
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id

def get_current_user(user_id: str = Depends(verify_token), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

def check_usage_limit(user: User, db: Session) -> bool:
    """Check if user has exceeded their monthly forecast limit"""
    from datetime import datetime
    from sqlalchemy import func
    
    # Get current month usage
    current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    from database import UsageLog
    usage_count = db.query(func.count(UsageLog.id)).filter(
        UsageLog.user_id == user.id,
        UsageLog.action == "forecast_generated",
        UsageLog.timestamp >= current_month
    ).scalar()
    
    # Check limits based on subscription tier
    limits = {
        "free": settings.FREE_TIER_FORECASTS_PER_MONTH,
        "premium": settings.PREMIUM_TIER_FORECASTS_PER_MONTH,
        "enterprise": settings.ENTERPRISE_TIER_FORECASTS_PER_MONTH
    }
    
    limit = limits.get(user.subscription_tier, limits["free"])
    return usage_count < limit

def log_usage(user_id: str, action: str, resource_id: str = None, metadata: dict = None, db: Session = None):
    """Log user action for analytics and billing"""
    from database import UsageLog
    
    log_entry = UsageLog(
        user_id=user_id,
        action=action,
        resource_id=resource_id,
        metadata=metadata
    )
    db.add(log_entry)
    db.commit()
