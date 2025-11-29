from fastapi import HTTPException
import time
import numpy as np

MAX_TIME = 300  # 5 хвилин для великих матриць

class TaskValidator:

    @staticmethod
    def validate_matrix(matrix: list[list[float]], vector: list[float]):
        """Валідує матрицю перед розв'язанням"""
        
        # Перевірка розмірності
        n = len(matrix)
        if n == 0:
            raise HTTPException(
                status_code=400,
                detail="Матриця не може бути порожньою"
            )
        
        # Перевірка що всі рядки однакової довжини
        for row in matrix:
            if len(row) != n:
                raise HTTPException(
                    status_code=400,
                    detail="Матриця повинна бути квадратною"
                )
        
        # Перевірка довжини вектора
        if len(vector) != n:
            raise HTTPException(
                status_code=400,
                detail="Довжина вектора b не відповідає розміру матриці"
            )
        
        # Перевірка максимального розміру (опціонально)
        if n > 1000:
            raise HTTPException(
                status_code=400,
                detail="Максимальний розмір матриці: 1000×1000"
            )
        
        # Перевірка детермінанта (тільки для невеликих матриць)
        if n <= 100:  # Для великих матриць це занадто повільно
            try:
                det = np.linalg.det(matrix)
                if abs(det) < 1e-10:
                    raise HTTPException(
                        status_code=400,
                        detail="Матриця вироджена (детермінант ≈ 0), система не має єдиного розв'язку"
                    )
            except:
                pass  # Якщо не вдалося обчислити, продовжуємо

    @staticmethod
    def validate_timeout(start_time: float):
        """Перевіряє чи не перевищено ліміт часу виконання"""
        elapsed = time.time() - start_time
        if elapsed > MAX_TIME:
            raise HTTPException(
                status_code=408,
                detail=f"Час обчислення перевищив ліміт {MAX_TIME} секунд"
            )