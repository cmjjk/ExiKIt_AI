# ExitKit AI

Open-source AI-агент для передачи знаний и дел при увольнении, смене роли или переходе в другую команду. Принимает заметки и документы сотрудника (`.txt`, `.md`, `.pdf`, `.docx`) и собирает **Handover Package**: задачи, сроки, ответственных, блокеры, открытые вопросы, контакты, чек-лист. Результат можно поправить в интерфейсе и выгрузить в PDF.

Работает с любым OpenAI-совместимым API, по умолчанию — локально через [Ollama](https://ollama.com): данные не уходят во внешние сервисы.

## Структура

- `app/` — бэкенд на FastAPI: `main.py` (API, чтение файлов, PDF), `agent.py` (промпт, контракт `Handover`, вызов LLM)
- `static/` — веб-интерфейс (`index.html`)
- `tests/` — тесты
- `examples/` — примеры входных и выходных данных
- `docs/` — документация
- `.github/workflows/` — CI

## Запуск

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
ollama pull qwen2.5:7b
uvicorn app.main:app --reload
```

Откройте http://localhost:8000.

## Настройка LLM

| Переменная | По умолчанию |
|---|---|
| `LLM_BASE_URL` | `http://localhost:11434/v1` |
| `LLM_MODEL` | `qwen2.5:7b` |
| `LLM_API_KEY` | `ollama` |

## Тесты

```bash
pytest
```

Для PDF с кириллицей нужен шрифт DejaVu Sans (на macOS подхватываются системные шрифты).

## Лицензия

MIT
