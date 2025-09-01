import enum
from datetime import datetime

from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy import JSON, DateTime, Integer, String, TypeDecorator
from sqlalchemy.orm import mapped_column


class TaskStatus(enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class EnumAsString(TypeDecorator):
    """A type decorator that stores enum values as strings in the database."""
    
    impl = String
    cache_ok = True
    
    def __init__(self, enum_class, *args, **kwargs):
        self.enum_class = enum_class
        super().__init__(*args, **kwargs)
    
    def process_bind_param(self, value, dialect):
        """Convert enum to string when saving to database."""
        if value is None:
            return None
        if isinstance(value, self.enum_class):
            return value.value
        return value
    
    def process_result_value(self, value, dialect):
        """Convert string to enum when loading from database."""
        if value is None:
            return None
        if isinstance(value, str):
            return self.enum_class(value)
        return value


class G2PQueBackgroundTask(BaseORMModel):
    __tablename__ = "g2p_que_background_task"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    worker_type = mapped_column(String, default="example_worker")  # Default worker type
    worker_payload = mapped_column(JSON, nullable=False)
    task_status = mapped_column(
        EnumAsString(TaskStatus), nullable=False, default=TaskStatus.PENDING
    )
    queued_datetime = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    number_of_attempts = mapped_column(Integer, default=0)
    last_attempt_datetime = mapped_column(DateTime, nullable=True)
    last_attempt_error_code = mapped_column(String, nullable=True)
