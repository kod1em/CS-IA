from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime, timezone
import os

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(120), nullable=False)
    role = Column(String(20), default='student')
    is_approved = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    # Relationships
    created_courses = relationship('Course', back_populates='teacher')
    enrollments = relationship('Enrollment', back_populates='student')
    submissions = relationship('Submission', back_populates='student')

class Course(Base):
    __tablename__ = 'courses'
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    invitation_code = Column(String(10), unique=True, nullable=False)
    teacher_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    teacher = relationship('User', back_populates='created_courses')
    tasks = relationship('Task', back_populates='course', cascade="all, delete-orphan")
    enrollments = relationship('Enrollment', back_populates='course', cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    due_date = Column(DateTime)
    
    # Relationships
    course = relationship('Course', back_populates='tasks')
    submissions = relationship('Submission', back_populates='task', cascade="all, delete-orphan")

class Enrollment(Base):
    __tablename__ = 'enrollments'
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    enrolled_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    student = relationship('User', back_populates='enrollments')
    course = relationship('Course', back_populates='enrollments')

class Submission(Base):
    __tablename__ = 'submissions'
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    student_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    content = Column(Text)
    file_path = Column(String(255))
    file_name = Column(String(255))
    file_type = Column(String(50))
    submitted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    ai_score = Column(Float)
    ai_feedback = Column(Text)
    teacher_score = Column(Float)
    teacher_feedback = Column(Text)
    is_finalized = Column(Boolean, default=False)
    status = Column(String(20), default='processing')
    
    task = relationship('Task', back_populates='submissions')
    student = relationship('User', back_populates='submissions')

# Setup database
os.makedirs('instance', exist_ok=True)
engine = create_engine('sqlite:///instance/studysystem_desktop.db')
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
