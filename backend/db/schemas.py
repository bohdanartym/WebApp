from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Any, Dict

class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: int

    class Config:
        from_attributes = True

class TaskBase(BaseModel):
    user_id: int
    input_data: Dict[str, Any]
    result: Dict[str, Any]

class TaskCreate(TaskBase):
    pass

class TaskOut(TaskBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
