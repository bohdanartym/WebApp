import uuid
import threading
import time
from backend.core.gauss_solver import GaussSolver
from backend.core.validation import TaskValidator

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from backend.db.database import DATABASE_URL
from backend.db import repository

class TaskManager:

    @staticmethod
    def _run_task_in_background(
        task_id: str,
        user_id: int,
        matrix: list[list[float]],
        vector: list[float]
    ):

        print(f"[TaskManager] Thread started for task {task_id}")
        try:

            print(f"[TaskManager] Starting solver for task {task_id}, matrix size: {len(matrix)}x{len(matrix)}")
            result = GaussSolver.solve_system(
                task_id=task_id,
                user_id=user_id,
                matrix=matrix,
                vector=vector
            )
            print(f"[TaskManager] Solver finished for task {task_id}, status: {result.get('status')}")

            if result.get("status") == "completed":

                async def update_progress_result():
                    engine = create_async_engine(DATABASE_URL, echo=False)
                    async_session_maker = sessionmaker(
                        bind=engine,
                        class_=AsyncSession,
                        expire_on_commit=False
                    )
                    try:
                        async with async_session_maker() as db:
                            await repository.update_task_progress_status(
                                db, 
                                task_id, 
                                status="completed",
                                progress=100.0,
                                result={"solution": result["solution"]}
                            )
                    finally:
                        await engine.dispose()

                async def save_to_history():
                    engine = create_async_engine(DATABASE_URL, echo=False)
                    async_session_maker = sessionmaker(
                        bind=engine,
                        class_=AsyncSession,
                        expire_on_commit=False
                    )
                    try:
                        async with async_session_maker() as db:
                            from backend.db.schemas import TaskCreate
                            await repository.add_task(
                                db,
                                TaskCreate(
                                    user_id=user_id,
                                    input_data={"matrix": matrix, "rhs": vector},
                                    result=result
                                )
                            )
                    except Exception as db_error:
                        print(f"[TaskManager] Error saving to history: {db_error}")
                    finally:
                        await engine.dispose()

                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(update_progress_result())
                    loop.run_until_complete(save_to_history())
                    loop.close()
                except Exception as async_error:
                    print(f"[TaskManager] Error in async execution: {async_error}")
                    
            elif result.get("status") == "error":

                
                async def save_error():
                    engine = create_async_engine(DATABASE_URL, echo=False)
                    async_session_maker = sessionmaker(
                        bind=engine,
                        class_=AsyncSession,
                        expire_on_commit=False
                    )
                    try:
                        async with async_session_maker() as db:
                            await repository.update_task_progress_status(
                                db,
                                task_id,
                                status="error",
                                progress=0.0,
                                error_message=result.get("error")
                            )
                    finally:
                        await engine.dispose()
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(save_error())
                loop.close()
                
        except Exception as e:
            print(f"[TaskManager] Error in background task: {e}")
            
            async def save_error():
                engine = create_async_engine(DATABASE_URL, echo=False)
                async_session_maker = sessionmaker(
                    bind=engine,
                    class_=AsyncSession,
                    expire_on_commit=False
                )
                try:
                    async with async_session_maker() as db:
                        await repository.update_task_progress_status(
                            db,
                            task_id,
                            status="error",
                            progress=0.0,
                            error_message=str(e)
                        )
                finally:
                    await engine.dispose()
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(save_error())
            loop.close()

    @staticmethod
    async def start_gauss_task(
        user_id: int,
        matrix: list[list[float]],
        vector: list[float],
        db
    ):

        task_id = str(uuid.uuid4())
        
        print(f"[TaskManager] Creating new task {task_id} for user {user_id}")

        TaskValidator.validate_matrix(matrix, vector)
        print(f"[TaskManager] Matrix validated: {len(matrix)}x{len(matrix[0]) if matrix else 0}")

        thread = threading.Thread(
            target=TaskManager._run_task_in_background,
            args=(task_id, user_id, matrix, vector),
            daemon=True,
            name=f"GaussSolver-{task_id[:8]}"
        )
        thread.start()
        print(f"[TaskManager] Thread started: {thread.name}, alive: {thread.is_alive()}")

        timeout = 0.5
        start = time.time()
        while not thread.is_alive() and (time.time() - start) < timeout:
            time.sleep(0.001)
        
        if not thread.is_alive():
            print(f"[TaskManager] WARNING: Thread failed to start!")
        
        print(f"[TaskManager] Returning task_id {task_id}")
        
        return {
            "task_id": task_id,
            "status": "processing",
            "message": "Завдання прийнято та перебуває в обробці"
        }

    @staticmethod
    async def get_task_status_from_db(task_id: str, db):

        from backend.db import repository
        
        task = await repository.get_task_progress(db, task_id)
        
        if task is None:
            return {
                "task_id": task_id,
                "status": "not_found"
            }
        
        if task.is_cancelled:
            return {
                "task_id": task_id,
                "status": "cancelled",
                "progress": 0
            }
        
        return {
            "task_id": task_id,
            "status": task.status,
            "progress": task.progress
        }

    @staticmethod
    async def get_task_result_from_db(task_id: str, db):

        from backend.db import repository
        
        task = await repository.get_task_progress(db, task_id)
        
        if task is None:
            return None
        
        if task.status == "completed" and task.result:
            return {
                "task_id": task_id,
                "status": "completed",
                "solution": task.result.get("solution")
            }
        elif task.status == "error":
            return {
                "task_id": task_id,
                "status": "error",
                "error": task.error_message
            }
        elif task.status == "cancelled":
            return {
                "task_id": task_id,
                "status": "cancelled"
            }
        else:
            return {
                "task_id": task_id,
                "status": task.status
            }

    @staticmethod
    async def cancel_task_in_db(task_id: str, db):
        
        await repository.cancel_task_progress(db, task_id)
        
        return {
            "task_id": task_id,
            "status": "cancelling",
            "message": "Запит на скасування надіслано"
        }