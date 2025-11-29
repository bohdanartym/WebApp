from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, ForeignKey, JSON, DateTime, func

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


