from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, ForeignKey, JSON, DateTime, Float, Boolean, func

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)

    tasks = relationship("TaskHistory", back_populates="user", cascade="all, delete")


class TaskHistory(Base):
    __tablename__ = "tasks_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    input_data = Column(JSON, nullable=False)
    result = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=False), server_default=func.now())

    user = relationship("User", back_populates="tasks")


class TaskProgress(Base):
    """
    Таблиця для відстеження прогресу задач в реальному часі
    Використовується для синхронізації між backend серверами
    """
    __tablename__ = "task_progress"

    task_id = Column(String, primary_key=True, index=True)  # UUID задачі
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    status = Column(String, nullable=False, default="processing")  # processing, completed, error, cancelled
    progress = Column(Float, nullable=False, default=0.0)  # 0-100
    
    result = Column(JSON, nullable=True)  # Результат (solution або error)
    error_message = Column(String, nullable=True)  # Повідомлення про помилку
    
    is_cancelled = Column(Boolean, nullable=False, default=False)  # Чи скасована задача
    
    created_at = Column(DateTime(timezone=False), server_default=func.now())
    updated_at = Column(DateTime(timezone=False), server_default=func.now(), onupdate=func.now())