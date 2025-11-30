import asyncio
import threading
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from backend.db.database import DATABASE_URL
from backend.db import repository

class ProgressTracker:
    """
    Трекер прогресу виконання задач через PostgreSQL
    THREAD-SAFE версія: кожен потік має свій engine
    """

    # Кеш останнього збереженого значення
    _last_saved = {}
    _last_saved_lock = threading.Lock()

    @staticmethod
    def _run_async_in_thread(coro):
        """
        Запускає async функцію в потоці
        Створює НОВИЙ loop для кожного виклику
        """
        # Створюємо НОВИЙ event loop для цього потоку
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(coro)
            return result
        except Exception as e:
            print(f"[ProgressTracker] Error in async execution: {e}")
            return None
        finally:
            # Закриваємо всі pending tasks
            try:
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
                # Даємо tasks можливість завершитися
                if pending:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except Exception:
                pass
            finally:
                loop.close()

    @staticmethod
    def _create_db_session():
        """
        Створює НОВУ DB сесію з НОВИМ engine для кожного виклику
        Це дозволяє уникнути проблем з різними event loops
        """
        # Створюємо новий engine (він буде прив'язаний до поточного loop)
        engine = create_async_engine(
            DATABASE_URL, 
            echo=False,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True
        )
        
        async_session_maker = sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        return async_session_maker, engine

    @staticmethod
    def start(task_id: str, user_id: int = None):
        """Ініціалізує прогрес задачі в БД"""
        if user_id is None:
            print(f"[ProgressTracker] Warning: user_id not provided for {task_id}")
            return
        
        async def _start():
            session_maker, engine = ProgressTracker._create_db_session()
            try:
                async with session_maker() as db:
                    await repository.create_task_progress(db, task_id, user_id)
            finally:
                await engine.dispose()
        
        ProgressTracker._run_async_in_thread(_start())
        
        with ProgressTracker._last_saved_lock:
            ProgressTracker._last_saved[task_id] = 0

    @staticmethod
    def update(task_id: str, value: float, matrix_size: int = 100):
        """
        Оновлює прогрес задачі в БД
        АДАПТИВНА версія з мінімальними оновленнями
        """
        value = min(100, max(0, value))
        
        # Логуємо тільки значні зміни
        if int(value) % 20 == 0:
            print(f"[ProgressTracker] Task {task_id}: {int(value)}%")
        
        # Отримуємо останнє збережене значення
        with ProgressTracker._last_saved_lock:
            last_saved = ProgressTracker._last_saved.get(task_id, 0)
        
        # АДАПТИВНА ЛОГІКА
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
            session_maker, engine = ProgressTracker._create_db_session()
            try:
                async with session_maker() as db:
                    await repository.update_task_progress_value(db, task_id, value)
            finally:
                await engine.dispose()
        
        try:
            ProgressTracker._run_async_in_thread(_update())
            
            with ProgressTracker._last_saved_lock:
                ProgressTracker._last_saved[task_id] = value
        except Exception as e:
            print(f"[ProgressTracker] Warning: failed to update progress: {e}")

    @staticmethod
    def get(task_id: str):
        """Отримує поточний прогрес задачі з БД"""
        async def _get():
            session_maker, engine = ProgressTracker._create_db_session()
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
            print(f"[ProgressTracker] Warning: failed to get progress: {e}")
            return None

    @staticmethod
    def finish(task_id: str):
        """Завершує відстеження прогресу"""
        async def _finish():
            session_maker, engine = ProgressTracker._create_db_session()
            try:
                async with session_maker() as db:
                    await repository.update_task_progress_value(db, task_id, 100.0)
            finally:
                await engine.dispose()
        
        try:
            ProgressTracker._run_async_in_thread(_finish())
            
            # Очищаємо кеш
            with ProgressTracker._last_saved_lock:
                if task_id in ProgressTracker._last_saved:
                    del ProgressTracker._last_saved[task_id]
        except Exception as e:
            print(f"[ProgressTracker] Warning: failed to finish progress: {e}")

    @staticmethod
    async def get_async(task_id: str, db: AsyncSession):
        """Async версія для FastAPI (використовує існуючу сесію)"""
        task = await repository.get_task_progress(db, task_id)
        if task is None:
            return None
        return task.progress