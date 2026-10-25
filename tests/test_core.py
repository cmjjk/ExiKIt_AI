import json

import pytest

import core
from reporting import build_markdown, build_pdf, find_gaps

DATA = {
    "summary": "Проект Alpha",
    "projects": [{"name": "Alpha", "status": "в работе", "next_steps": "Неизвестно", "source": "a.txt"}],
    "tasks": [{"task": "Релиз", "owner": "Неизвестно", "deadline": "15.11", "source": "a.txt"}],
    "risks": [], "contacts": [], "instructions": [], "agreements": [],
    "open_questions": ["Кто получит доступ?"],
}


def test_split_text_keeps_everything():
    text = "\n".join(f"строка {i} " + "x" * 50 for i in range(500))
    chunks = core.split_text(text, max_chars=1000)
    assert all(len(c) <= 1000 for c in chunks)
    assert "".join(chunks) == text


def test_extract_txt_and_unsupported():
    assert core.extract_text("a.txt", "Привет".encode()) == "Привет"
    with pytest.raises(ValueError):
        core.extract_text("a.exe", b"x")


def test_merge_dedups():
    merged = core.merge_analyses([DATA, DATA])
    assert len(merged["tasks"]) == 1 and merged["open_questions"] == ["Кто получит доступ?"]


def test_gaps():
    ids = [g["id"] for g in find_gaps(DATA)]
    assert "tasks:0:owner" in ids and "projects:0:next_steps" in ids and "tasks:0:deadline" not in ids


def test_report_and_pdf():
    assert "Передача дел" in build_markdown(DATA, ["a.txt"])
    assert build_pdf(DATA, ["a.txt"]).startswith(b"%PDF")


class FakeResp:
    def __init__(self, content): self._c = content
    def raise_for_status(self): pass
    def json(self): return {"message": {"content": self._c}}


def test_analyze_retries_on_bad_json(monkeypatch):
    replies = iter(["не json", json.dumps(DATA)])
    monkeypatch.setattr(core.requests, "post", lambda *a, **k: FakeResp(next(replies)))
    assert core.analyze("текст")["summary"] == "Проект Alpha"


def test_analyze_gives_up(monkeypatch):
    monkeypatch.setattr(core.requests, "post", lambda *a, **k: FakeResp("мусор"))
    with pytest.raises(ValueError):
        core.analyze("текст")
