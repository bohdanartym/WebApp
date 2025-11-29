from pydantic import BaseModel, EmailStr

class RegisterUserRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
