from sqlmodel import SQLModel, Field, create_engine, Session, select
from typing import Optional
from datetime import datetime

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    category: str = Field(index=True)   # LECTURER / ADMIN / KPP / AUDITOR / AJK
    role: str = Field(index=True)
    name: str = ""
    username: str = Field(index=True, unique=True)
    password_hash: str
    notes: str = ""

class Subject(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(index=True, unique=True)
    name: str
    lic: str = ""         # comma separated names
    lic_start: str = ""
    lic_end: str = ""
    rp: str = ""
    rp_start: str = ""
    rp_end: str = ""

class FileItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    subject_code: str = Field(index=True)
    uploader_username: str = Field(index=True)
    role: str = Field(index=True)      # LIC / RP / STAFF
    doc_type: str = Field(index=True)  # rubrics/course_info/cap/lesson_plan/... 
    semester: str = Field(index=True)
    path: str
    sha256: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

def get_engine(db_path: str):
    return create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})

def init_db(engine):
    SQLModel.metadata.create_all(engine)
