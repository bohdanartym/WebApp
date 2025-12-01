from fastapi import HTTPException
import time
import numpy as np

MAX_TIME = 600  

class TaskValidator:

    @staticmethod
    def validate_matrix(matrix: list[list[float]], vector: list[float]):

        n = len(matrix)

        print(f"[Validator] Matrix size: {n}x{n}")
        
    
    @staticmethod
    def validate_timeout(start_time: float):

        elapsed = time.time() - start_time
        if elapsed > MAX_TIME:
            raise HTTPException(
                status_code=408,
                detail=f"Час обчислення перевищив ліміт {MAX_TIME} секунд (виконувалось {int(elapsed)}с)"
            )