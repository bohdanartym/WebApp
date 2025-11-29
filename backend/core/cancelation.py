cancel_store = {}   

class CancelationManager:

    @staticmethod
    def request_cancel(task_id: str):
        cancel_store[task_id] = True

    @staticmethod
    def is_cancelled(task_id: str):
        return cancel_store.get(task_id, False)
