"""Экспорт HandoverPackage в Markdown (PDF — позже)."""
from app.schemas import HandoverPackage


def to_markdown(p: HandoverPackage) -> str:
    out = [f"# Handover Package — {p.employee or 'сотрудник'}", "", p.summary, ""]
    out += ["## Проекты", *[f"- {x}" for x in p.projects], ""]
    out += ["## Задачи", *[f"- [{t.status}] {t.title} ({t.owner or '—'}, {t.deadline or '—'})" for t in p.tasks], ""]
    out += ["## Риски", *[f"- ({r.severity}) {r.description}" for r in p.risks], ""]
    out += ["## Открытые вопросы", *[f"- {q.text}" for q in p.open_questions]]
    return "\n".join(out)
