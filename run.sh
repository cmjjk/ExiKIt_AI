#!/usr/bin/env bash
# Запуск ExitKit AI: окружение, зависимости, модель Ollama, Streamlit.
set -e
cd "$(dirname "$0")"
MODEL="${OLLAMA_MODEL:-qwen2.5:3b}"

command -v ollama >/dev/null || { echo "Установите Ollama: https://ollama.com/download"; exit 1; }
curl -s -m 3 http://localhost:11434/api/tags >/dev/null || { echo "Ollama не запущена: откройте приложение Ollama или выполните 'ollama serve'"; exit 1; }
ollama list | grep -q "^$MODEL" || ollama pull "$MODEL"

[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt
OLLAMA_MODEL="$MODEL" .venv/bin/streamlit run app.py
