from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import os
import enum

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://qa:qa@localhost:5432/qa_farm")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class RunStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class Flow(Base):
    __tablename__ = "flows"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    target_package = Column(String(255), nullable=False)  # app sob teste
    definition = Column(Text, nullable=False)  # JSON serializado dos passos
    created_at = Column(DateTime, default=datetime.utcnow)

    runs = relationship("FlowRun", back_populates="flow")


class FlowRun(Base):
    __tablename__ = "flow_runs"
    id = Column(Integer, primary_key=True)
    flow_id = Column(Integer, ForeignKey("flows.id"))
    device_serial = Column(String(128), nullable=False)
    status = Column(Enum(RunStatus), default=RunStatus.PENDING)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    log = Column(Text, default="")
    screenshot_path = Column(String(512), nullable=True)

    flow = relationship("Flow", back_populates="runs")


def init_db():
    Base.metadata.create_all(bind=engine)
