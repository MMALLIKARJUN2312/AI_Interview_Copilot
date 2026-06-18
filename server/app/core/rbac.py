from fastapi import Depends, HTTPException
from app.core.dependencies import (get_current_user)

def require_role(allowed_roles : list):
    def checker(current_user = Depends(get_current_user)):
        if (current_user["role"] not in allowed_roles):
            raise HTTPException(status_code=403, detail="Forbidden")
        return current_user
    return checker