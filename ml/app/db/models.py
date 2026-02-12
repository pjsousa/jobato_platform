from __future__ import annotations

from sqlalchemy import Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class RunResult(Base):
    __tablename__ = "run_items"
    __table_args__ = (Index("idx_run_items__run_id", "run_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String, nullable=False)
    query_id: Mapped[str | None] = mapped_column(String, nullable=True)
    query_text: Mapped[str] = mapped_column(String, nullable=False)
    search_query: Mapped[str] = mapped_column(String, nullable=False)
    domain: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    snippet: Mapped[str] = mapped_column(Text, nullable=False)
    raw_url: Mapped[str] = mapped_column(String, nullable=False)
    final_url: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)
    raw_html_path: Mapped[str | None] = mapped_column(String, nullable=True)
    visible_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    fetch_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    extract_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    cache_key: Mapped[str | None] = mapped_column(String, nullable=True)
    cached_at: Mapped[str | None] = mapped_column(String, nullable=True)
    cache_expires_at: Mapped[str | None] = mapped_column(String, nullable=True)
    last_seen_at: Mapped[str | None] = mapped_column(String, nullable=True)
    skip_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    normalized_url: Mapped[str | None] = mapped_column(String, nullable=True)
    normalization_error: Mapped[str | None] = mapped_column(String, nullable=True)
