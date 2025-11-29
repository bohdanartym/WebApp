import numpy as np
import time
from backend.core.validation import TaskValidator
from backend.core.progress import ProgressTracker
from backend.core.cancelation import CancelationManager

class GaussSolver:

    @staticmethod
    def solve_system(task_id: str, user_id: int, matrix: list[list[float]], vector: list[float]):
        """
        Розв'язує систему лінійних рівнянь методом Гауса з відстеженням прогресу
        """
        print(f"[GaussSolver] Starting solve for task {task_id}")
        start_time = time.time()
        
        try:
            A = np.array(matrix, dtype=float)
            b = np.array(vector, dtype=float)
            n = len(A)
            
            print(f"[GaussSolver] Matrix size: {n}x{n}")
            
            ProgressTracker.start(task_id, user_id)
            print(f"[GaussSolver] Progress initialized: {ProgressTracker.get(task_id)}")
            
            # Прямий хід методу Гауса
            for i in range(n):
                # Перевірка на скасування
                if CancelationManager.is_cancelled(task_id):
                    ProgressTracker.update(task_id, 0)
                    return {
                        "task_id": task_id,
                        "status": "cancelled",
                        "solution": None
                    }
                
                # Перевірка timeout
                TaskValidator.validate_timeout(start_time)
                
                # Оновлення прогресу (прямий хід = 0-70%)
                progress = (i / n) * 70
                ProgressTracker.update(task_id, progress)
                
                pivot = A[i][i]
                
                # Перевірка на нульовий елемент
                if abs(pivot) < 1e-10:
                    raise ValueError(f"Нульовий елемент на діагоналі (рядок {i})")
                
                for j in range(i + 1, n):
                    if CancelationManager.is_cancelled(task_id):
                        return {
                            "task_id": task_id,
                            "status": "cancelled",
                            "solution": None
                        }
                    
                    factor = A[j][i] / pivot
                    A[j] = A[j] - factor * A[i]
                    b[j] = b[j] - factor * b[i]
                    
                    # ЗАТРИМКА ДЛЯ ДЕМОНСТРАЦІЇ (можна видалити або зменшити)
                    """ if n > 100:
                        time.sleep(0.0001)  # Зменшено з 0.001 до 0.0001 """
            
            # Зворотній хід методу Гауса
            for i in range(n - 1, -1, -1):
                if CancelationManager.is_cancelled(task_id):
                    return {
                        "task_id": task_id,
                        "status": "cancelled",
                        "solution": None
                    }
                
                TaskValidator.validate_timeout(start_time)
                
                # Оновлення прогресу (зворотній хід = 70-100%)
                progress = 70 + ((n - i) / n) * 30
                ProgressTracker.update(task_id, progress)
                
                b[i] = (b[i] - np.dot(A[i][i+1:], b[i+1:])) / A[i][i]
                
                """ if n > 100:
                    time.sleep(0.0001)  # Зменшено """
            
            # Завершення
            ProgressTracker.finish(task_id)
            print(f"[GaussSolver] Task {task_id} completed successfully")
            
            return {
                "task_id": task_id,
                "status": "completed",
                "solution": b.tolist()
            }
            
        except Exception as e:
            print(f"[GaussSolver] Error in task {task_id}: {e}")
            ProgressTracker.update(task_id, 0)
            return {
                "task_id": task_id,
                "status": "error",
                "error": str(e),
                "solution": None
            }