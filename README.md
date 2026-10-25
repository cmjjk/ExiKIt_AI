# ExitKit AI

Open-source AI-агент для передачи знаний и дел при увольнении или смене роли. Анализирует заметки и документы сотрудника и собирает **Handover Package**: проекты, задачи, сроки, риски, нерешённые вопросы. Работает локально через [Ollama](https://ollama.com), данные не уходят во внешние сервисы.

## Структура

- `backend/` — Python, FastAPI, AI-пайплайн (`app/pipeline`), LLM-клиент (`app/llm`), экспорт (`app/export`), контракт данных (`app/schemas.py`)
- `frontend/` — веб-интерфейс
- `docs/` — документация
- `examples/` — примеры входных данных

## Запуск

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

По умолчанию включён mock-режим (без LLM). Для Ollama: `EXITKIT_MOCK=0 OLLAMA_MODEL=llama3.1`.

## Лицензия

MIT
