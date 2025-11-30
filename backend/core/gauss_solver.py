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
        З ДЕТАЛЬНИМ ЛОГУВАННЯМ для діагностики
        """
        print(f"[GaussSolver] ===== STARTING task {task_id} =====")
        print(f"[GaussSolver] Matrix size: {len(matrix)}x{len(matrix)}")
        start_time = time.time()
        
        try:
            # Крок 1: Конвертація в NumPy
            print(f"[GaussSolver] Converting to NumPy arrays...")
            A = np.array(matrix, dtype=float)
            b = np.array(vector, dtype=float)
            n = len(A)
            print(f"[GaussSolver] NumPy conversion done in {time.time() - start_time:.3f}s")
            
            # Крок 2: Ініціалізація прогресу
            print(f"[GaussSolver] Initializing progress tracker...")
            init_start = time.time()
            ProgressTracker.start(task_id, user_id)
            print(f"[GaussSolver] Progress tracker initialized in {time.time() - init_start:.3f}s")
            
            ProgressTracker.update(task_id, 5, matrix_size=n)
            
            # Інтервали перевірок
            check_interval = max(1, n // 20)
            print(f"[GaussSolver] Check interval: every {check_interval} iterations")
            
            # Крок 3: Прямий хід методу Гауса
            print(f"[GaussSolver] Starting forward elimination...")
            forward_start = time.time()
            
            for i in range(n):
                # Логування кожні 20% для великих матриць
                if n > 100 and i % (n // 5) == 0:
                    elapsed = time.time() - forward_start
                    print(f"[GaussSolver] Forward: {i}/{n} ({i/n*100:.1f}%) - {elapsed:.3f}s elapsed")
                
                # МІНІМАЛЬНІ ПЕРЕВІРКИ
                if i % check_interval == 0:
                    # Перевірка на скасування
                    if CancelationManager.is_cancelled(task_id):
                        print(f"[GaussSolver] Task {task_id} CANCELLED at forward step {i}")
                        ProgressTracker.update(task_id, 0, matrix_size=n)
                        return {
                            "task_id": task_id,
                            "status": "cancelled",
                            "solution": None
                        }
                    
                    # Перевірка timeout
                    TaskValidator.validate_timeout(start_time)
                    
                    # Оновлення прогресу
                    progress = 5 + (i / n) * 65
                    ProgressTracker.update(task_id, progress, matrix_size=n)
                
                # Частковий вибір головного елемента
                max_row = i + np.argmax(np.abs(A[i:, i]))
                if max_row != i:
                    A[[i, max_row]] = A[[max_row, i]]
                    b[i], b[max_row] = b[max_row], b[i]
                
                pivot = A[i][i]
                
                # Перевірка на вироджену матрицю
                if abs(pivot) < 1e-10:
                    error_msg = f"Матриця вироджена: нульовий елемент на діагоналі (рядок {i})"
                    print(f"[GaussSolver] ERROR: {error_msg}")
                    raise ValueError(error_msg)
                
                # ВЕКТОРИЗАЦІЯ через NumPy
                if i + 1 < n:
                    factors = A[i+1:, i] / pivot
                    A[i+1:] -= factors[:, np.newaxis] * A[i]
                    b[i+1:] -= factors * b[i]
            
            forward_time = time.time() - forward_start
            print(f"[GaussSolver] Forward elimination done in {forward_time:.3f}s")
            
            ProgressTracker.update(task_id, 70, matrix_size=n)
            
            # Крок 4: Зворотній хід методу Гауса
            print(f"[GaussSolver] Starting back substitution...")
            backward_start = time.time()
            
            x = np.zeros(n)
            for i in range(n - 1, -1, -1):
                step = n - 1 - i
                
                # Логування кожні 20%
                if n > 100 and step % (n // 5) == 0:
                    elapsed = time.time() - backward_start
                    print(f"[GaussSolver] Backward: {step}/{n} ({step/n*100:.1f}%) - {elapsed:.3f}s elapsed")
                
                # МІНІМАЛЬНІ ПЕРЕВІРКИ
                if step % check_interval == 0:
                    if CancelationManager.is_cancelled(task_id):
                        print(f"[GaussSolver] Task {task_id} CANCELLED at backward step {step}")
                        return {
                            "task_id": task_id,
                            "status": "cancelled",
                            "solution": None
                        }
                    
                    TaskValidator.validate_timeout(start_time)
                    
                    # Оновлення прогресу
                    progress = 70 + (step / n) * 30
                    ProgressTracker.update(task_id, progress, matrix_size=n)
                
                # Обчислення x[i]
                x[i] = (b[i] - np.dot(A[i, i+1:], x[i+1:])) / A[i][i]
            
            backward_time = time.time() - backward_start
            print(f"[GaussSolver] Back substitution done in {backward_time:.3f}s")
            
            # Крок 5: ОКРУГЛЕННЯ РЕЗУЛЬТАТІВ
            print(f"[GaussSolver] Rounding solution...")
            solution = GaussSolver._round_solution(x)
            
            # Крок 6: Завершення
            print(f"[GaussSolver] Finishing progress tracker...")
            ProgressTracker.finish(task_id)
            
            total_time = time.time() - start_time
            print(f"[GaussSolver] ===== COMPLETED task {task_id} =====")
            print(f"[GaussSolver] Total time: {total_time:.3f}s (forward: {forward_time:.3f}s, backward: {backward_time:.3f}s)")
            
            return {
                "task_id": task_id,
                "status": "completed",
                "solution": solution
            }
            
        except Exception as e:
            print(f"[GaussSolver] ===== ERROR in task {task_id} =====")
            print(f"[GaussSolver] Error type: {type(e).__name__}")
            print(f"[GaussSolver] Error message: {e}")
            import traceback
            traceback.print_exc()
            
            ProgressTracker.update(task_id, 0, matrix_size=len(matrix))
            return {
                "task_id": task_id,
                "status": "error",
                "error": str(e),
                "solution": None
            }

    @staticmethod
    def _round_solution(x: np.ndarray, decimals: int = 10) -> list:
        """
        Розумне округлення розв'язку
        
        Логіка:
        1. Округлюємо до 10 знаків після коми (видаляє похибки типу e-16)
        2. Якщо число дуже близьке до цілого (< 1e-9 від цілого) - округлюємо до цілого
        3. Інакше залишаємо як є
        """
        result = []
        
        for val in x:
            # Крок 1: Округлюємо до 10 знаків (видаляє e-16 похибки)
            rounded = round(val, decimals)
            
            # Крок 2: Перевіряємо чи близько до цілого числа
            nearest_int = round(rounded)
            if abs(rounded - nearest_int) < 1e-9:
                # Дуже близько до цілого - використовуємо ціле
                result.append(float(nearest_int))
            else:
                # Не близько до цілого - залишаємо округлене
                result.append(rounded)
        
        return result