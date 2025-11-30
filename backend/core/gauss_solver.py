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
        МАКСИМАЛЬНО ОПТИМІЗОВАНА ВЕРСІЯ
        """
        print(f"[GaussSolver] Starting solve for task {task_id}, size: {len(matrix)}x{len(matrix)}")
        start_time = time.time()
        
        try:
            A = np.array(matrix, dtype=float)
            b = np.array(vector, dtype=float)
            n = len(A)
            
            # Ініціалізуємо прогрес (одразу 5% - показуємо що почали)
            ProgressTracker.start(task_id, user_id)
            ProgressTracker.update(task_id, 5)
            
            # Інтервали перевірок: рідше для великих матриць
            # Для 100: check_interval=5 (20 перевірок)
            # Для 1000: check_interval=50 (20 перевірок)
            # Для 10000: check_interval=500 (20 перевірок)
            check_interval = max(1, n // 20)
            
            # Прямий хід методу Гауса
            for i in range(n):
                # МІНІМАЛЬНІ ПЕРЕВІРКИ (тільки кожен check_interval-й крок)
                if i % check_interval == 0:
                    # Перевірка на скасування (БД запит)
                    if CancelationManager.is_cancelled(task_id):
                        ProgressTracker.update(task_id, 0)
                        return {
                            "task_id": task_id,
                            "status": "cancelled",
                            "solution": None
                        }
                    
                    # Перевірка timeout (без БД)
                    TaskValidator.validate_timeout(start_time)
                    
                    # Оновлення прогресу (прямий хід = 5-70%)
                    # БД запит тільки на кожні 10% (завдяки оптимізації в ProgressTracker)
                    progress = 5 + (i / n) * 65
                    ProgressTracker.update(task_id, progress)
                
                # Частковий вибір головного елемента (для числової стабільності)
                max_row = i + np.argmax(np.abs(A[i:, i]))
                if max_row != i:
                    A[[i, max_row]] = A[[max_row, i]]
                    b[i], b[max_row] = b[max_row], b[i]
                
                pivot = A[i][i]
                
                # Перевірка на вироджену матрицю
                if abs(pivot) < 1e-10:
                    raise ValueError(f"Матриця вироджена: нульовий елемент на діагоналі (рядок {i})")
                
                # ВЕКТОРИЗАЦІЯ через NumPy - це НАБАГАТО швидше ніж цикл for j
                # Це еквівалентно:
                # for j in range(i + 1, n):
                #     factor = A[j][i] / pivot
                #     A[j] = A[j] - factor * A[i]
                #     b[j] = b[j] - factor * b[i]
                if i + 1 < n:
                    factors = A[i+1:, i] / pivot
                    A[i+1:] -= factors[:, np.newaxis] * A[i]
                    b[i+1:] -= factors * b[i]
            
            ProgressTracker.update(task_id, 70)
            
            # Зворотній хід методу Гауса
            x = np.zeros(n)
            for i in range(n - 1, -1, -1):
                # МІНІМАЛЬНІ ПЕРЕВІРКИ
                step = n - 1 - i
                if step % check_interval == 0:
                    if CancelationManager.is_cancelled(task_id):
                        return {
                            "task_id": task_id,
                            "status": "cancelled",
                            "solution": None
                        }
                    
                    TaskValidator.validate_timeout(start_time)
                    
                    # Оновлення прогресу (зворотній хід = 70-100%)
                    progress = 70 + (step / n) * 30
                    ProgressTracker.update(task_id, progress)
                
                # Обчислення x[i]
                x[i] = (b[i] - np.dot(A[i, i+1:], x[i+1:])) / A[i][i]
            
            # Завершення
            ProgressTracker.finish(task_id)
            elapsed = time.time() - start_time
            print(f"[GaussSolver] Task {task_id} completed in {elapsed:.3f}s")
            
            return {
                "task_id": task_id,
                "status": "completed",
                "solution": x.tolist()
            }
            
        except Exception as e:
            print(f"[GaussSolver] Error in task {task_id}: {e}")
            import traceback
            traceback.print_exc()
            
            ProgressTracker.update(task_id, 0)
            return {
                "task_id": task_id,
                "status": "error",
                "error": str(e),
                "solution": None
            }