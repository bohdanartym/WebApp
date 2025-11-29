from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List

from backend.db.database import get_db
from backend.db.schemas import TaskOut
from backend.db.repository import get_tasks_for_user
from backend.db import models

from backend.auth.auth_routes import router as auth_router
from backend.auth.auth_dependencies import get_current_user
from backend.core.progress import ProgressTracker
from backend.core.task_manager import TaskManager
from pydantic import BaseModel
from backend.core.cancelation import CancelationManager

class GaussInput(BaseModel):
    matrix: List[List[float]]
    rhs: List[float]

app = FastAPI(title="API2")

app.include_router(auth_router, prefix="/auth", tags=["Auth"])

@app.get("/health")
def health():
    return {"status": "ok", "from": "api2"}

@app.get("/db-test")
async def db_test(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT 1"))
    return {"db": "ok", "result": result.scalar()}

@app.post("/gauss/solve")
async def solve(
    data: GaussInput,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    result = await TaskManager.solve_gauss_task(
        user_id=user.id,
        matrix=data.matrix,
        vector=data.rhs,
        db=db
    )

    return {
    "user_id": user.id,
    "task_id": result["task_id"],
    "solution": result["solution"]
}

@app.get("/tasks/user/me", response_model=list[TaskOut])
async def get_my_tasks(
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    return await get_tasks_for_user(db, user.id)

@app.get("/tasks/user/{user_id}", response_model=list[TaskOut])
async def get_user_tasks(user_id: int, db: AsyncSession = Depends(get_db)):
    return await get_tasks_for_user(db, user_id)

@app.post("/tasks/cancel/{task_id}")
def cancel_task(task_id: str):
    CancelationManager.request_cancel(task_id)
    return {"task_id": task_id, "cancelled": True}

@app.get("/tasks/status/{task_id}")
def task_status(task_id: str):
    progress = ProgressTracker.get(task_id)
    cancelled = CancelationManager.is_cancelled(task_id)

    if progress is None:
        return {"task_id": task_id, "status": "not_found"}

    if cancelled:
        return {"task_id": task_id, "status": "cancelled"}

    if progress == 100:
        return {"task_id": task_id, "status": "finished", "progress": 100}

    return {
        "task_id": task_id,
        "status": "running",
        "progress": progress
    }