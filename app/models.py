from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


class Study(Base):
    __tablename__ = "studies"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    indication: Mapped[str] = mapped_column(String(255), default="General")
    phase: Mapped[str] = mapped_column(String(50), default="II")
    status: Mapped[str] = mapped_column(String(50), default="Draft")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    versions: Mapped[list["BudgetVersion"]] = relationship(back_populates="study", cascade="all, delete-orphan")


class BudgetVersion(Base):
    __tablename__ = "budget_versions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    study_id: Mapped[int] = mapped_column(ForeignKey("studies.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    study: Mapped[Study] = relationship(back_populates="versions")
    items: Mapped[list["BudgetItem"]] = relationship(back_populates="version", cascade="all, delete-orphan")


class BudgetItem(Base):
    __tablename__ = "budget_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    budget_version_id: Mapped[int] = mapped_column(ForeignKey("budget_versions.id", ondelete="CASCADE"))
    category: Mapped[str] = mapped_column(String(100))
    subcategory: Mapped[str] = mapped_column(String(100), default="General")
    item_name: Mapped[str] = mapped_column(String(255))
    unit: Mapped[str] = mapped_column(String(50), default="unit")
    unit_cost: Mapped[float] = mapped_column(Float)
    qty_formula_type: Mapped[str] = mapped_column(String(30), default="fixed")
    manual_qty: Mapped[float] = mapped_column(Float, default=1)
    notes: Mapped[str] = mapped_column(Text, default="")
    version: Mapped[BudgetVersion] = relationship(back_populates="items")


class ScenarioRun(Base):
    __tablename__ = "scenario_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    budget_version_id: Mapped[int] = mapped_column(ForeignKey("budget_versions.id", ondelete="CASCADE"))
    label: Mapped[str] = mapped_column(String(255))
    patients: Mapped[int] = mapped_column(Integer)
    sites: Mapped[int] = mapped_column(Integer)
    visits: Mapped[int] = mapped_column(Integer)
    monitoring_visits_per_site: Mapped[int] = mapped_column(Integer, default=4)
    grand_total: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AIReport(Base):
    __tablename__ = "ai_reports"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scenario_run_id: Mapped[int] = mapped_column(ForeignKey("scenario_runs.id", ondelete="CASCADE"))
    report_type: Mapped[str] = mapped_column(String(50))
    model: Mapped[str] = mapped_column(String(255), default="openrouter/auto")
    input_snapshot: Mapped[str] = mapped_column(Text)
    output_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
