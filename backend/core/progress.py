import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from backend.db.database import DATABASE_URL
from backend.db import repository

# ОПТИМІЗАЦІЯ: Переиспользуємо engine замість створення нового кожного разу
_shared_engine = None

def get_shared_engine():
    """Отримує загальний engine (створює один раз)"""
    global _shared_engine
    if _shared_engine is None:
        _shared_engine = create_async_engine(
            DATABASE_URL, 
            echo=False,
            pool_size=5,  # Пул з'єднань
            max_overflow=10,
            pool_pre_ping=True  # Перевірка з'єднань перед використанням
        )
    return _shared_engine

class ProgressTracker:
    """
    Трекер прогресу виконання задач через PostgreSQL
    ШВИДКА ВЕРСІЯ: переиспользуємо з'єднання з БД
    """

    @staticmethod
    def _get_db_session():
        """Створює сесію з загального engine"""
        engine = get_shared_engine()
        async_session_maker = sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        return async_session_maker

    @staticmethod
    def _run_async_in_thread(coro):
        """Запускає async функцію в НОВОМУ event loop (для потоків)"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    # Кеш останнього збереженого значення
    _last_saved = {}

    @staticmethod
    def start(task_id: str, user_id: int = None):
        """Ініціалізує прогрес задачі в БД (ШВИДКА версія)"""
        if user_id is None:
            print(f"[ProgressTracker] Warning: user_id not provided for {task_id}")
            return
        
        async def _start():
            session_maker = ProgressTracker._get_db_session()
            async with session_maker() as db:
                await repository.create_task_progress(db, task_id, user_id)
        
        ProgressTracker._run_async_in_thread(_start())
        ProgressTracker._last_saved[task_id] = 0

    @staticmethod
    def update(task_id: str, value: float, matrix_size: int = 100):
        """
        Оновлює прогрес задачі в БД (АДАПТИВНА версія)
        """
        value = min(100, max(0, value))
        
        # Логуємо тільки значні зміни
        if int(value) % 20 == 0:
            print(f"[ProgressTracker] Task {task_id}: {int(value)}%")
        
        # АДАПТИВНА ЛОГІКА
        last_saved = ProgressTracker._last_saved.get(task_id, 0)
        
        if matrix_size <= 100:
            threshold = 10
        elif matrix_size <= 500:
            threshold = 5
        else:
            threshold = 2
        
        # Перевіряємо чи потрібно оновлювати БД
        should_update = (
            value == 100 or
            value == 0 or
            abs(value - last_saved) >= threshold
        )
        
        if not should_update:
            return
        
        async def _update():
            session_maker = ProgressTracker._get_db_session()
            async with session_maker() as db:
                await repository.update_task_progress_value(db, task_id, value)
        
        try:
            ProgressTracker._run_async_in_thread(_update())
            ProgressTracker._last_saved[task_id] = value
        except Exception as e:
            print(f"[ProgressTracker] Warning: failed to update progress: {e}")

    @staticmethod
    def get(task_id: str):
        """Отримує поточний прогрес задачі з БД"""
        async def _get():
            session_maker = ProgressTracker._get_db_session()
            async with session_maker() as db:
                task = await repository.get_task_progress(db, task_id)
                if task is None:
                    return None
                return task.progress
        
        try:
            return ProgressTracker._run_async_in_thread(_get())
        except Exception as e:
            print(f"[ProgressTracker] Warning: failed to get progress: {e}")
            return None

    @staticmethod
    def finish(task_id: str):
        """Завершує відстеження прогресу"""
        async def _finish():
            session_maker = ProgressTracker._get_db_session()
            async with session_maker() as db:
                await repository.update_task_progress_value(db, task_id, 100.0)
        
        try:
            ProgressTracker._run_async_in_thread(_finish())
            ProgressTracker._last_saved[task_id] = 100
            if task_id in ProgressTracker._last_saved:
                del ProgressTracker._last_saved[task_id]
        except Exception as e:
            print(f"[ProgressTracker] Warning: failed to finish progress: {e}")

    @staticmethod
    async def get_async(task_id: str, db: AsyncSession):
        """Async версія для FastAPI"""
        task = await repository.get_task_progress(db, task_id)
        if task is None:
            return None
        return task.progress