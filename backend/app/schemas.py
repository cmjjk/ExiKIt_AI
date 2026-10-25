"""Единый контракт данных: Handover Package."""
from typing import Literal

from pydantic import BaseModel, Field

Priority = Literal["low", "medium", "high"]


class Task(BaseModel):
    title: str
    status: str = "open"
    owner: str | None = None
    deadline: str | None = None
    priority: Priority = "medium"


class Risk(BaseModel):
    description: str
    severity: Priority = "medium"


class Question(BaseModel):
    text: str
    context: str | None = None


class HandoverPackage(BaseModel):
    employee: str | None = None
    summary: str = ""
    projects: list[str] = Field(default_factory=list)
    tasks: list[Task] = Field(default_factory=list)
    risks: list[Risk] = Field(default_factory=list)
    open_questions: list[Question] = Field(default_factory=list)


class AnalyzeRequest(BaseModel):
    notes: str
