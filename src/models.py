from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .database import Base

class Priority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Category(Base):
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    color = Column(String)  # HEX цвет для отображения
    
    tasks = relationship("Task", back_populates="category")

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    notification_time = Column(Integer, default=24)  # За сколько часов до дедлайна уведомлять
    
    tasks = relationship("Task", back_populates="user")
    categories = relationship("Category", secondary="user_categories")

class UserCategory(Base):
    __tablename__ = 'user_categories'
    
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    category_id = Column(Integer, ForeignKey('categories.id'), primary_key=True)

class Task(Base):
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    title = Column(String)
    description = Column(String, nullable=True)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=True)
    priority = Column(Enum(Priority), default=Priority.MEDIUM)
    last_notified = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="tasks")
    category = relationship("Category", back_populates="tasks") 