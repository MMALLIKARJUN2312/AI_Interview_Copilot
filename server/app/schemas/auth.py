from pydantic import BaseModel
from pydantic import EmailStr

class RegisterRequest(BaseModel):
    full_name : str
    email : EmailStr
    password : str 
    
class LoginRequest(BaseModel):
    email : EmailStr
    password : str 
    
class TokenResponse(BaseModel):
    access_token : str
    refresh_token : str
    token_type : str

class RefreshRequest(BaseModel):
    refresh_token : str

class LogoutRequest(BaseModel):
    refresh_token : str

class UserResponse(BaseModel):
    id : int
    full_name : str
    email : EmailStr
    role : str

    model_config = {"from_attributes" : True}
