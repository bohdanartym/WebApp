from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from backend.db.database import get_db
from backend.db.repository import get_user_by_email, create_user
from backend.auth.auth_utils import verify_password, create_access_token
from backend.auth.auth_schemas import TokenResponse, RegisterUserRequest

router = APIRouter()

class LoginJSON(BaseModel):
    email: str
    password: str


@router.post("/login", response_model=TokenResponse)
async def login_json(data: LoginJSON, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, data.email)
    if not user:
        raise HTTPException(status_code=400, detail="Невірний email або пароль")

    if not verify_password(data.password, user.password):
        raise HTTPException(status_code=400, detail="Невірний email або пароль")

    access_token = create_access_token({"user_id": user.id})

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register")
async def register_user(
    data: RegisterUserRequest,
    db: AsyncSession = Depends(get_db),
):
    existing = await get_user_by_email(db, data.email)
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Користувач з таким email вже існує"
        )

    new_user = await create_user(db, data)

    return {
        "status": "success",
        "user": {
            "id": new_user.id,
            "email": new_user.email,
            "name": new_user.name
        }
    }

