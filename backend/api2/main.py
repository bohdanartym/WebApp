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

from backend.core.task_manager import TaskManager
from pydantic import BaseModel

class GaussInput(BaseModel):
    matrix: List[List[float]]
    rhs: List[float]

# ⚠️ ДЛЯ API1: title="API1", from="api1"
# ⚠️ ДЛЯ API2: title="API2", from="api2"
app = FastAPI(title="API2")

app.include_router(auth_router, prefix="/auth", tags=["Auth"])

@app.get("/health")
def health():
    return {"status": "ok", "from": "api2"}  # ⚠️ Змініть на "api2" для другого сервера

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
    """
    Запускає розв'язання системи рівнянь у фоновому режимі
    Повертає task_id для відстеження прогресу
    """
    result = await TaskManager.start_gauss_task(
        user_id=user.id,
        matrix=data.matrix,
        vector=data.rhs,
        db=db
    )
    
    return result

@app.get("/tasks/status/{task_id}")
async def get_task_status(task_id: str, db: AsyncSession = Depends(get_db)):
    """
    Отримує поточний статус задачі з БД
    """
    print(f"[API] Getting status for task {task_id}")
    result = await TaskManager.get_task_status_from_db(task_id, db)
    print(f"[API] Status result: {result}")
    return result

@app.get("/tasks/result/{task_id}")
async def get_task_result(task_id: str, db: AsyncSession = Depends(get_db)):
    """
    Отримує результат завершеної задачі з БД
    """
    result = await TaskManager.get_task_result_from_db(task_id, db)
    
    if result is None:
        return {
            "task_id": task_id,
            "status": "not_found",
            "message": "Задача не знайдена або ще не завершена"
        }
    
    return result

@app.post("/tasks/cancel/{task_id}")
async def cancel_task(task_id: str, db: AsyncSession = Depends(get_db)):
    """
    Скасовує виконання задачі через БД
    """
    return await TaskManager.cancel_task_in_db(task_id, db)

@app.get("/tasks/user/me", response_model=list[TaskOut])
async def get_my_tasks(
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    """
    Отримує всі задачі поточного користувача
    """
    return await get_tasks_for_user(db, user.id)

@app.get("/tasks/user/{user_id}", response_model=list[TaskOut])
async def get_user_tasks(user_id: int, db: AsyncSession = Depends(get_db)):
    """
    Отримує всі задачі конкретного користувача
    """
    return await get_tasks_for_user(db, user_id)