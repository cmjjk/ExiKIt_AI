"""Checks for the short reader-facing report."""

import json
import unittest
from unittest.mock import patch

from core import EnglishOutputError, MODEL, _english_prose, _validate, analyze
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
    def test_small_model_request_disables_thinking(self):
        with patch("core.requests.post") as post:
            data = example_data()
            data["open_questions"] = ["неизвестно"]
            post.return_value.json.return_value = {"message": {"content": json.dumps(data)}}
            result = analyze("Проект CRM: проверить дубликаты клиентов.\nОткрытый вопрос: кто отвечает за интеграцию?", "example.txt")
        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["model"], MODEL)
        self.assertFalse(payload["think"])
        self.assertEqual(payload["options"]["num_ctx"], 3072)
        self.assertEqual(payload["keep_alive"], 0)
        self.assertEqual(result["open_questions"], ["кто отвечает за интеграцию?"])

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

    def test_source_filename_does_not_count_as_english_prose(self):
        data = example_data()
        data["summary"] = "Документ: employee_handover (1).txt"
        self.assertEqual(_validate(data, "employee_handover (1).txt")["summary"], data["summary"])
        self.assertFalse(_english_prose("Документ CRM Migration Guide"))

    def test_repeated_english_field_does_not_discard_russian_report(self):
        data = example_data()
        data["tasks"][0]["status"] = "In progress"
        with patch("core.requests.post") as post:
            post.return_value.json.return_value = {"message": {"content": json.dumps(data)}}
            result = analyze("Задача: проверить дубликаты клиентов", "example.txt")
        self.assertEqual(post.call_count, 2)
        self.assertEqual(result["tasks"][0]["status"], "Неизвестно")
        self.assertIn("часть сведений", result["open_questions"][-1])
        self.assertNotIn("In progress", build_markdown(result, ["example.txt"]))

    def test_explicitly_unassigned_task_has_no_invented_owner(self):
        data = example_data()
        data["tasks"][0]["owner"] = "Руководитель продаж"
        data["tasks"][0]["status"] = "ответственный пока не назначен"
        self.assertEqual(_validate(data, "example.txt")["tasks"][0]["owner"], "Не назначен")

    def test_named_task_owner_takes_precedence(self):
        data = example_data()
        data["tasks"][0]["task"] = "Игорь Петров должен проверить дубликаты"
        data["tasks"][0]["owner"] = "Не назначен"
        self.assertEqual(_validate(data, "example.txt")["tasks"][0]["owner"], "Игорь Петров")

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
