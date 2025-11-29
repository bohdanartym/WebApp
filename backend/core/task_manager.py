import uuid
from backend.core.gauss_solver import GaussSolver
from backend.core.validation import TaskValidator
from backend.db.repository import add_task
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.progress import ProgressTracker
from backend.db.schemas import TaskCreate

class TaskManager:

    @staticmethod
    async def solve_gauss_task(
        user_id: int,
        matrix: list[list[float]],
        vector: list[float],
        db: AsyncSession
    ):
        task_id = str(uuid.uuid4())

        TaskValidator.validate_matrix(matrix, vector)

        result = GaussSolver.solve_system(
            matrix=matrix,
            vector=vector,
        )

        ProgressTracker.finish(task_id)

        db_task = await add_task(
            db,
            TaskCreate(
                user_id=user_id,
                input_data={"matrix": matrix, "rhs": vector},
                result=result
            )
        )

        return {
            "task_id": task_id,       
            "db_id": db_task.id,
            "solution": result["solution"]
        }
