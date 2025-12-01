from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
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



async def create_task_progress(db: AsyncSession, task_id: str, user_id: int):

    task_progress = models.TaskProgress(
        task_id=task_id,
        user_id=user_id,
        status="processing",
        progress=0.0,
        is_cancelled=False
    )
    db.add(task_progress)
    await db.commit()
    await db.refresh(task_progress)
    return task_progress

async def get_task_progress(db: AsyncSession, task_id: str):
    result = await db.execute(
        select(models.TaskProgress).where(models.TaskProgress.task_id == task_id)
    )
    return result.scalar_one_or_none()

async def update_task_progress_value(db: AsyncSession, task_id: str, progress: float):

    await db.execute(
        update(models.TaskProgress)
        .where(models.TaskProgress.task_id == task_id)
        .values(progress=progress, updated_at=datetime.utcnow())
    )
    await db.commit()

async def update_task_progress_status(
    db: AsyncSession, 
    task_id: str, 
    status: str, 
    progress: float = None,
    result: dict = None,
    error_message: str = None
):

    values = {
        "status": status,
        "updated_at": datetime.utcnow()
    }
    
    if progress is not None:
        values["progress"] = progress
    if result is not None:
        values["result"] = result
    if error_message is not None:
        values["error_message"] = error_message
    
    await db.execute(
        update(models.TaskProgress)
        .where(models.TaskProgress.task_id == task_id)
        .values(**values)
    )
    await db.commit()

async def cancel_task_progress(db: AsyncSession, task_id: str):

    await db.execute(
        update(models.TaskProgress)
        .where(models.TaskProgress.task_id == task_id)
        .values(
            is_cancelled=True,
            status="cancelled",
            progress=0.0,
            updated_at=datetime.utcnow()
        )
    )
    await db.commit()

async def is_task_cancelled(db: AsyncSession, task_id: str) -> bool:

    result = await db.execute(
        select(models.TaskProgress.is_cancelled)
        .where(models.TaskProgress.task_id == task_id)
    )
    cancelled = result.scalar_one_or_none()
    return cancelled if cancelled is not None else False

async def delete_old_task_progress(db: AsyncSession, days: int = 7):

    from datetime import timedelta
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    await db.execute(
        delete(models.TaskProgress)
        .where(models.TaskProgress.created_at < cutoff_date)
    )
    await db.commit()