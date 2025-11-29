from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.db import models
from backend.db.schemas import TaskCreate, UserCreate
from datetime import datetime
from backend.auth.auth_utils import hash_password  

async def create_user(db: AsyncSession, data: UserCreate):
    new_user = models.User(
        name=data.name,
        email=data.email,

        password=hash_password(data.password),
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(
        select(models.User).where(models.User.email == email)
    )
    return result.scalar_one_or_none()

async def get_user_by_id(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(models.User).where(models.User.id == user_id)
    )
    return result.scalar_one_or_none()

async def add_task(db: AsyncSession, data: TaskCreate):
    new_task = models.TaskHistory(
        user_id=data.user_id,
        input_data=data.input_data,
        result=data.result,
        created_at=datetime.utcnow(),
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    return new_task


async def get_tasks_for_user(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(models.TaskHistory).where(models.TaskHistory.user_id == user_id)
    )
    return result.scalars().all()
