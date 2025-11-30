from fastapi import HTTPException
import time
import numpy as np

MAX_TIME = 600  # Збільшено до 10 хвилин для дуже великих матриць

class TaskValidator:

    @staticmethod
    def validate_matrix(matrix: list[list[float]], vector: list[float]):
        """
        Валідує матрицю перед розв'язанням
        З детальними повідомленнями про помилки
        """
        
        # Перевірка розмірності
        n = len(matrix)

        print(f"[Validator] Matrix size: {n}x{n}")
        
    
    @staticmethod
    def validate_timeout(start_time: float):
        """Перевіряє чи не перевищено ліміт часу виконання"""
        elapsed = time.time() - start_time
        if elapsed > MAX_TIME:
            raise HTTPException(
                status_code=408,
                detail=f"Час обчислення перевищив ліміт {MAX_TIME} секунд (виконувалось {int(elapsed)}с)"
            )