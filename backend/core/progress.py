import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from backend.db.database import DATABASE_URL
from backend.db import repository

class ProgressTracker:
    """
    Трекер прогресу виконання задач через PostgreSQL
    ОПТИМІЗОВАНА ВЕРСІЯ: мінімальна кількість БД запитів
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
        """
        Оновлює прогрес задачі в БД (sync версія для потоків)
        ОПТИМІЗОВАНО: мінімальні БД запити, без зайвих print
        """
        value = min(100, max(0, value))
        
        # Логуємо тільки значні зміни (кожні 20%)
        if int(value) % 20 == 0:
            print(f"[ProgressTracker] Task {task_id}: {int(value)}%")
        
        # КРИТИЧНА ОПТИМІЗАЦІЯ: оновлюємо БД тільки на значних кроках
        # Замість оновлення на кожному кроці - тільки кожні 10%
        if int(value) % 10 != 0 and value != 100:
            return  # Пропускаємо дрібні оновлення
        
        async def _update():
            session_maker, engine = ProgressTracker._get_db_session()
            try:
                async with session_maker() as db:
                    await repository.update_task_progress_value(db, task_id, value)
            finally:
                await engine.dispose()
        
        # Запускаємо оновлення асинхронно (не блокуємо обчислення)
        try:
            ProgressTracker._run_async_in_thread(_update())
        except Exception as e:
            # Не падаємо якщо БД недоступна - просто логуємо
            print(f"[ProgressTracker] Warning: failed to update progress for {task_id}: {e}")

    @staticmethod
    def get(task_id: str):
        """Отримує поточний прогрес задачі з БД (sync версія для потоків)"""
        async def _get():
            session_maker, engine = ProgressTracker._get_db_session()
            try:
                async with session_maker() as db:
                    task = await repository.get_task_progress(db, task_id)
                    if task is None:
                        return None
                    return task.progress
            finally:
                await engine.dispose()
        
        try:
            return ProgressTracker._run_async_in_thread(_get())
        except Exception as e:
            print(f"[ProgressTracker] Warning: failed to get progress for {task_id}: {e}")
            return None

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
        
        try:
            ProgressTracker._run_async_in_thread(_finish())
        except Exception as e:
            print(f"[ProgressTracker] Warning: failed to finish progress for {task_id}: {e}")

    # ============= ASYNC методи (для використання в FastAPI) =============

    @staticmethod
    async def get_async(task_id: str, db: AsyncSession):
        """Отримує поточний прогрес задачі з БД (async версія для FastAPI)"""
        task = await repository.get_task_progress(db, task_id)
        if task is None:
            return None
        return task.progress