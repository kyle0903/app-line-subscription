import sqlalchemy
from sqlalchemy import Column, Integer, String, DateTime, UUID
from datetime import datetime
from sqlalchemy.orm import declarative_base 

base = declarative_base()


class User(base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    line_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    status = Column(Integer, nullable=False)
    role = Column(String, nullable=False)
    group_id = Column(UUID, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)



