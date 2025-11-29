import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from backend.db.database import DATABASE_URL
from backend.db import repository

class ProgressTracker:
    """
    Трекер прогресу виконання задач через PostgreSQL
    Підтримує як sync (для потоків), так і async (для FastAPI) виклики
    """

    @staticmethod
    def _get_db_session():
        """Створює нову DB сесію"""
        engine = create_async_engine(DATABASE_URL, echo=False)
        async_session_maker = sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        return async_session_maker, engine

    @staticmethod
    def _run_async_in_thread(coro):
        """Запускає async функцію в НОВОМУ event loop (для потоків)"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    # ============= SYNC методи (для використання в потоках) =============

    @staticmethod
    def start(task_id: str, user_id: int = None):
        """Ініціалізує прогрес задачі в БД (sync версія для потоків)"""
        print(f"[ProgressTracker] Starting tracking {task_id} in DB")
        
        if user_id is None:
            print(f"[ProgressTracker] Warning: user_id not provided for {task_id}")
            return
        
        async def _start():
            session_maker, engine = ProgressTracker._get_db_session()
            try:
                async with session_maker() as db:
                    await repository.create_task_progress(db, task_id, user_id)
                print(f"[ProgressTracker] Task {task_id} created in DB")
            finally:
                await engine.dispose()
        
        ProgressTracker._run_async_in_thread(_start())

    @staticmethod
    def update(task_id: str, value: float):
        """Оновлює прогрес задачі в БД (sync версія для потоків)"""
        value = min(100, max(0, value))
        
        # Логуємо тільки кожні 10%
        if int(value) % 10 == 0:
            print(f"[ProgressTracker] Task {task_id} progress: {int(value)}%")
        
        async def _update():
            session_maker, engine = ProgressTracker._get_db_session()
            try:
                async with session_maker() as db:
                    await repository.update_task_progress_value(db, task_id, value)
            finally:
                await engine.dispose()
        
        ProgressTracker._run_async_in_thread(_update())

    @staticmethod
    def get(task_id: str):
        """Отримує поточний прогрес задачі з БД (sync версія для потоків)"""
        async def _get():
            session_maker, engine = ProgressTracker._get_db_session()
            try:
                async with session_maker() as db:
                    task = await repository.get_task_progress(db, task_id)
                    if task is None:
                        print(f"[ProgressTracker] Task {task_id} not found in DB")
                        return None
                    return task.progress
            finally:
                await engine.dispose()
        
        return ProgressTracker._run_async_in_thread(_get())

    @staticmethod
    def finish(task_id: str):
        """Завершує відстеження прогресу (sync версія для потоків)"""
        print(f"[ProgressTracker] Task {task_id} finished (100%)")
        
        async def _finish():
            session_maker, engine = ProgressTracker._get_db_session()
            try:
                async with session_maker() as db:
                    await repository.update_task_progress_value(db, task_id, 100.0)
            finally:
                await engine.dispose()
        
        ProgressTracker._run_async_in_thread(_finish())

    # ============= ASYNC методи (для використання в FastAPI) =============

    @staticmethod
    async def get_async(task_id: str, db: AsyncSession):
        """Отримує поточний прогрес задачі з БД (async версія для FastAPI)"""
        task = await repository.get_task_progress(db, task_id)
        if task is None:
            print(f"[ProgressTracker] Task {task_id} not found in DB")
            return None
        return task.progress