from fastapi import HTTPException
import time, numpy as np
         
MAX_TIME = 5        

class TaskValidator:

    @staticmethod
    def validate_matrix(matrix: list[list[float]], vector: list[float]):
        if np.linalg.det(matrix) == 0:
            raise HTTPException(
            status_code=400,
            detail="Нульовий детермінант -> коренів немає"
        )

    @staticmethod
    def validate_timeout(start_time: float):
        if time.time() - start_time > MAX_TIME:
            raise HTTPException(
                status_code=400,
                detail=f"Час обчислення перевищив ліміт {MAX_TIME}-ти секунд."
            )
