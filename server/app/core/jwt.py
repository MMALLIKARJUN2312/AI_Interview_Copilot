from datetime import datetime
from datetime import timedelta
from datetime import timezone

from jose import jwt

from app.core.config import Settings

def create_access_token(data : dict):
    to_encode = data.copy()
    expire = (datetime.now(timezone.utc) + timedelta(minutes=Settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp" : expire})
    encoded_jwt = jwt.encode(to_encode, Settings.JWT_SECRET, algorithm=Settings.JWT_ALGORITHM)
    return encoded_jwt