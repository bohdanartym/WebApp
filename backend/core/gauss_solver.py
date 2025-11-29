import numpy as np
import time
import uuid
from backend.core.validation import TaskValidator

class GaussSolver:

    @staticmethod
    def solve_system(matrix: list[list[float]], vector: list[float]):
        start_time = time.time()
        task_id = str(uuid.uuid4())     

        A = np.array(matrix, dtype=float)
        b = np.array(vector, dtype=float)
        n = len(A)
  
        for i in range(n):
            TaskValidator.validate_timeout(start_time)

            pivot = A[i][i]

            for j in range(i + 1, n):
                TaskValidator.validate_timeout(start_time)
                factor = A[j][i] / pivot
                A[j] = A[j] - factor * A[i]
                b[j] = b[j] - factor * b[i]
   
        for i in range(n - 1, -1, -1):
            TaskValidator.validate_timeout(start_time)
            b[i] = (b[i] - np.dot(A[i][i+1:], b[i+1:])) / A[i][i]

        return {
            "task_id": task_id,
            "solution": b.tolist(),
            "steps": []
        }
