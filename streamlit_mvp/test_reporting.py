"""Checks for the short reader-facing report."""

import unittest

from core import EnglishOutputError, _validate
from reporting import build_markdown, build_pdf
from streamlit.testing.v1 import AppTest


def example_data():
    return {
        "summary": "Передача проекта по переносу клиентов.",
        "projects": [{"name": "CRM Migration", "status": "идёт тестирование", "background": "80% записей загружено", "next_steps": "завершить импорт", "decisions": "", "source": "example.txt"}],
        "tasks": [{"task": "Проверить дубликаты клиентов", "owner": "Игорь Петров", "deadline": "15.11.2026", "status": "в работе", "details": "проверить записи в тестовой среде", "source": "example.txt"}],
        "risks": [{"risk": "часть карточек без адреса электронной почты", "impact": "", "mitigation": "согласовать правило обработки с отделом продаж", "source": "example.txt"}],
        "contacts": [{"name": "Мария Смирнова", "role": "руководитель продаж", "context": "согласует запуск", "source": "example.txt"}],
        "instructions": [],
        "agreements": [],
        "open_questions": ["Кто будет поддерживать интеграцию?"],
    }


class ReportingTests(unittest.TestCase):
    def test_short_russian_report_and_pdf(self):
        data = example_data()
        markdown = build_markdown(data, ["example.txt"])
        self.assertIn("## Текущее состояние", markdown)
        self.assertIn("## Что делать дальше", markdown)
        self.assertIn("## На что обратить внимание", markdown)
        self.assertIn("## Что нужно уточнить", markdown)
        self.assertIn("Игорь Петров", markdown)
        self.assertNotIn("Handover Package", markdown)
        self.assertNotIn("###", markdown)
        self.assertTrue(build_pdf(data, ["example.txt"]).startswith(b"%PDF"))

    def test_english_model_prose_is_rejected(self):
        data = example_data()
        data["tasks"][0]["status"] = "In progress"
        with self.assertRaises(EnglishOutputError):
            _validate(data, "example.txt")

    def test_old_english_prose_is_hidden_from_report(self):
        data = example_data()
        data["projects"][0]["background"] = "The project is waiting for customer approval"
        markdown = build_markdown(data, ["example.txt"])
        self.assertNotIn("customer approval", markdown)

    def test_existing_session_report_is_rebuilt(self):
        app = AppTest.from_file("app.py")
        app.session_state["data"] = example_data()
        app.session_state["filenames"] = ["example.txt"]
        app.session_state["report"] = "Handover Package"
        app.run()
        self.assertFalse(app.exception)
        self.assertIn("## Текущее состояние", app.session_state["report"])
        self.assertNotIn("Handover Package", app.session_state["report"])


if __name__ == "__main__":
    unittest.main()
