"""Пайплайн: заметки -> HandoverPackage."""
from app.llm.client import generate_json
from app.schemas import HandoverPackage, Question

PROMPT = """Ты помощник по передаче дел. Из заметок уходящего сотрудника извлеки JSON:
{{"employee","summary","projects":[],"tasks":[{{"title","status","owner","deadline","priority"}}],
"risks":[{{"description","severity"}}],"open_questions":[{{"text","context"}}]}}
Заметки:
{notes}"""


def analyze(notes: str) -> HandoverPackage:
    data = generate_json(PROMPT.format(notes=notes))
    if data:
        return HandoverPackage.model_validate(data)
    # mock-режим: заглушка, чтобы фронт и экспорт работали без LLM
    return HandoverPackage(
        summary=notes[:200],
        open_questions=[Question(text="Mock-режим: подключите Ollama (EXITKIT_MOCK=0)")],
    )
