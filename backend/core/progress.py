progress_store = {}   

class ProgressTracker:

    @staticmethod
    def start(task_id: str):
        progress_store[task_id] = 0

    @staticmethod
    def update(task_id: str, value: float):
        progress_store[task_id] = min(100, max(0, value))

    @staticmethod
    def get(task_id: str):
        return progress_store.get(task_id, None)

    @staticmethod
    def finish(task_id: str):
        progress_store[task_id] = 100
