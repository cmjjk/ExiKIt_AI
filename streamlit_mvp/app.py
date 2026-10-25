"""Streamlit UI for local handover generation."""

from datetime import date

import requests
import streamlit as st

from core import (
    CHUNK_CHARS,
    MAX_FILE_CHARS,
    MAX_TOTAL_CHUNKS,
    MODEL,
    analyze,
    extract_text,
    merge_analyses,
    split_text,
)
from reporting import build_markdown, build_pdf, find_gaps
from theme import apply_theme, hero

REPORT_FORMAT_VERSION = 2


def gap_input(gap):
    """Render an input that matches the data expected by this question."""
    key = "answer_" + gap["id"]
    kind = gap.get("input_type", "text")
    if kind == "date":
        return st.date_input(
            gap["question"], value=None, min_value=date(1900, 1, 1),
            max_value=date(2100, 12, 31), format="DD.MM.YYYY", key=key,
        )
    if kind == "integer":
        return st.number_input(gap["question"], value=None, step=1, format="%d", key=key)
    if kind == "text":
        return st.text_input(gap["question"], key=key)
    raise ValueError(f"Неизвестный тип вопроса: {kind}")


def normalized_gap_answer(gap, value):
    """Validate again on the server before saving a widget value."""
    kind = gap.get("input_type", "text")
    if value is None or value == "":
        return None
    if kind == "date":
        if type(value) is not date:
            raise ValueError("Для срока выберите дату в календаре")
        return value.strftime("%d.%m.%Y")
    if kind == "integer":
        if type(value) is not int:
            raise ValueError("В числовом поле допустимо только целое число")
        return str(value)
    if kind == "text" and isinstance(value, str):
        return value.strip() or None
    raise ValueError("Недопустимое значение поля")


st.set_page_config(page_title="ExitKit AI", page_icon="📦", layout="wide")
apply_theme()
hero()

with st.sidebar:
    st.subheader("⚙️ Настройки")
    st.write(f"Модель: `{MODEL}`")
    st.write("Обработка через локальный Ollama")
    if MODEL.endswith(":1.5b"):
        st.info("Модель 1.5B экономнее, но может пропускать детали. Проверьте отчёт по исходным файлам.")
    st.info("Поддерживаются текстовые PDF. Сканированные PDF без OCR не распознаются.")

files = st.file_uploader(
    "Загрузите рабочие материалы",
    type=["txt", "md", "pdf", "docx"],
    accept_multiple_files=True,
)

if st.button("✨ Создать отчёт о передаче дел", type="primary", disabled=not files):
    for key in ("filenames", "report", "data"):
        st.session_state.pop(key, None)
    pieces, errors, filenames = [], [], []
    for upload in files:
        try:
            content = extract_text(upload).strip()
            if not content:
                raise ValueError("текст не найден; для сканированного PDF нужен OCR")
            if len(content) > MAX_FILE_CHARS:
                raise ValueError(f"документ слишком большой ({len(content)} символов); лимит {MAX_FILE_CHARS}")
            chunks = split_text(content, CHUNK_CHARS)
            if len(pieces) + len(chunks) > MAX_TOTAL_CHUNKS:
                raise ValueError(f"пакет превысит {MAX_TOTAL_CHUNKS} частей; разделите анализ на несколько запусков")
            pieces.extend((chunk, upload.name, index, len(chunks)) for index, chunk in enumerate(chunks, 1))
            filenames.append(upload.name)
        except Exception as exc:
            errors.append(f"{upload.name}: {exc}")
    for error in errors:
        st.warning(error)
    if not pieces:
        st.error("Нет доступного текста для анализа.")
    else:
        try:
            results = []
            progress = st.progress(0, text="Подготовка анализа…")
            for index, (chunk, filename, part, total) in enumerate(pieces):
                progress.progress(index / len(pieces), text=f"Анализ: часть {index + 1} из {len(pieces)}")
                try:
                    results.append(analyze(chunk, filename, final_chunk=index == len(pieces) - 1))
                except Exception as exc:
                    raise RuntimeError(f"{filename}, часть {part}/{total}: {exc}") from exc
            result = merge_analyses(results)
            progress.progress(1.0, text="Анализ завершён")
            st.session_state["filenames"] = filenames
            st.session_state["data"] = result
            st.session_state["report"] = build_markdown(result, filenames)
            st.session_state["report_format_version"] = REPORT_FORMAT_VERSION
            st.success(f"Отчёт готов. Обработано частей: {len(pieces)}")
        except requests.exceptions.ConnectionError:
            st.error("Нет соединения с Ollama. Запустите Ollama и обновите страницу.")
        except Exception as exc:
            st.error(f"Ошибка анализа: {exc}")

if "data" in st.session_state and st.session_state.get("report_format_version") != REPORT_FORMAT_VERSION:
    st.session_state["report"] = build_markdown(st.session_state["data"], st.session_state.get("filenames", []))
    st.session_state["report_format_version"] = REPORT_FORMAT_VERSION

if "report" in st.session_state:
    st.subheader("💬 Уточняющие вопросы")
    gaps = find_gaps(st.session_state["data"])
    if gaps:
        st.write("Ответьте на вопросы о недостающих данных — отчёт обновится.")
        with st.form("gap_answers"):
            answers = {gap["id"]: gap_input(gap) for gap in gaps}
            if st.form_submit_button("💾 Добавить ответы в отчёт", type="primary"):
                try:
                    updates = [(gap, normalized_gap_answer(gap, answers[gap["id"]])) for gap in gaps]
                    updates = [(gap, value) for gap, value in updates if value is not None]
                    if updates:
                        for gap, value in updates:
                            st.session_state["data"][gap["section"]][gap["index"]][gap["field"]] = value
                        st.session_state["report"] = build_markdown(st.session_state["data"], st.session_state["filenames"])
                        st.success(f"Обновлено полей: {len(updates)}")
                        st.rerun()
                    else:
                        st.info("Заполните хотя бы один ответ.")
                except ValueError as exc:
                    st.error(str(exc))
    else:
        st.success("В ключевых полях задач пробелов не найдено.")
    tab_report, tab_json = st.tabs(["📄 Отчёт", "🧩 Данные для разработчика"])
    with tab_report:
        st.markdown(st.session_state["report"])
    with tab_json:
        st.json(st.session_state["data"])
    col_pdf, col_md = st.columns(2)
    with col_pdf:
        try:
            pdf_bytes = build_pdf(st.session_state["data"], st.session_state["filenames"])
            st.download_button("⬇️ Скачать PDF", data=pdf_bytes, file_name="peredacha_del.pdf", mime="application/pdf", use_container_width=True)
        except Exception as exc:
            st.error(f"Не удалось сформировать PDF: {exc}")
    with col_md:
        st.download_button("⬇️ Скачать Markdown", data=st.session_state["report"], file_name="peredacha_del.md", mime="text/markdown", use_container_width=True)
