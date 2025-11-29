import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from backend.db.database import DATABASE_URL
from backend.db import repository

class CancelationManager:
    """
    Менеджер для управління скасуванням задач через PostgreSQL
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
    def request_cancel(task_id: str):
        """Надсилає запит на скасування задачі в БД (sync версія)"""
        print(f"[CancelationManager] Cancelling task {task_id}")
        
        async def _cancel():
            session_maker, engine = CancelationManager._get_db_session()
            try:
                async with session_maker() as db:
                    await repository.cancel_task_progress(db, task_id)
            finally:
                await engine.dispose()
        
        CancelationManager._run_async_in_thread(_cancel())

    @staticmethod
    def is_cancelled(task_id: str) -> bool:
        """Перевіряє чи задача скасована через БД (sync версія)"""
        async def _check():
            session_maker, engine = CancelationManager._get_db_session()
            try:
                async with session_maker() as db:
                    return await repository.is_task_cancelled(db, task_id)
            finally:
                await engine.dispose()
        
        return CancelationManager._run_async_in_thread(_check())
    
    @staticmethod
    def clear(task_id: str):
        """Очищає статус скасування (при запуску нової задачі)"""
        # При створенні нового TaskProgress is_cancelled автоматично False
        # Тому цей метод не потрібен, але залишаємо для сумісності
        pass