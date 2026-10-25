# Архитектура

заметки / файлы → `POST /api/generate` (`app/main.py`) → `agent.generate_handover` (LLM, `app/agent.py`) → `Handover` → правка в UI (`static/index.html`) → `POST /api/export/pdf`.

Контракт данных — модель `Handover` в `app/agent.py`; пример — `examples/handover.json`.

TODO: детали логики.
