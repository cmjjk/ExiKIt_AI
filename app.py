import requests
import streamlit as st

from core import MAX_FILE_CHARS, MODEL, OLLAMA_URL, analyze, extract_text, merge_analyses, split_text
from reporting import build_markdown, build_pdf, find_gaps

st.set_page_config(page_title="ExitKit AI", page_icon="📦", layout="wide")
st.title("📦 ExitKit AI")
st.caption("Локальный AI-помощник для передачи дел и сохранения знаний")

with st.sidebar:
    st.subheader("⚙️ Настройки")
    st.write(f"Модель: `{MODEL}`")
    st.write(f"Ollama: `{OLLAMA_URL}`")
    st.info("Поддерживаются текстовые PDF. Сканированные PDF без OCR не распознаются.")

files = st.file_uploader("Загрузите рабочие материалы", type=["txt", "md", "pdf", "docx"], accept_multiple_files=True)
pasted = st.text_area("…или вставьте заметки текстом", height=140)

if st.button("✨ Создать Handover Package", type="primary", disabled=not (files or pasted.strip())):
    pieces, errors, filenames = [], [], []
    sources = [(f.name, f.getvalue()) for f in files or []]
    if pasted.strip():
        sources.append(("заметки.txt", pasted.encode("utf-8")))
    for name, raw in sources:
        try:
            content = extract_text(name, raw).strip()
            if not content:
                errors.append(f"{name}: текст не найден (для сканированного PDF нужен OCR)")
                continue
            if len(content) > MAX_FILE_CHARS:
                errors.append(f"{name}: документ слишком большой ({len(content)} символов). Разделите его на меньшие файлы.")
                continue
            chunks = split_text(content)
            pieces.extend(f"ИСТОЧНИК: {name} (часть {i}/{len(chunks)})\n{chunk}" for i, chunk in enumerate(chunks, 1))
            filenames.append(name)
        except Exception as ex:
            errors.append(f"{name}: {ex}")
    for err in errors:
        st.warning(err)
    if not pieces:
        st.error("Нет доступного текста для анализа. Загрузите текстовые документы.")
    else:
        try:
            results = []
            progress = st.progress(0, text="Подготовка анализа…")
            for i, piece in enumerate(pieces):
                progress.progress(i / len(pieces), text=f"Анализ документов: часть {i + 1} из {len(pieces)}")
                results.append(analyze(piece))
            progress.progress(1.0, text="Анализ завершён")
            result = merge_analyses(results)
            st.session_state["filenames"] = filenames
            st.session_state["report"] = build_markdown(result, filenames)
            st.session_state["data"] = result
            st.success(f"Handover Package готов. Обработано частей: {len(pieces)}")
        except requests.exceptions.ConnectionError:
            st.error(f"Нет соединения с Ollama ({OLLAMA_URL}). Запустите Ollama (`ollama serve`) и повторите.")
        except requests.exceptions.HTTPError as ex:
            st.error(f"Ошибка Ollama: {ex}. Проверьте, что модель установлена: ollama pull {MODEL}")
        except Exception as ex:
            st.error(f"Ошибка анализа: {ex}")

if "report" in st.session_state:
    st.subheader("💬 Уточняющие вопросы")
    gaps = find_gaps(st.session_state["data"])
    if gaps:
        st.write("В некоторых задачах не хватает сведений. Ответьте на вопросы — отчёт обновится автоматически.")
        with st.form("gap_answers"):
            answers = {gap["id"]: st.text_input(gap["question"], key="answer_" + gap["id"]) for gap in gaps}
            if st.form_submit_button("💾 Добавить ответы в отчёт", type="primary"):
                count = 0
                for gap in gaps:
                    answer = answers[gap["id"]].strip()
                    if answer:
                        st.session_state["data"][gap["section"]][gap["index"]][gap["field"]] = answer
                        count += 1
                if count:
                    st.session_state["report"] = build_markdown(st.session_state["data"], st.session_state["filenames"])
                    st.rerun()
                else:
                    st.info("Заполните хотя бы один ответ.")
    else:
        st.success("В ключевых полях задач пробелов не найдено.")
    tab1, tab2 = st.tabs(["📄 Понятный отчёт", "🧩 JSON"])
    with tab1:
        st.markdown(st.session_state["report"])
    with tab2:
        st.json(st.session_state["data"])
    col_pdf, col_md = st.columns(2)
    with col_pdf:
        try:
            pdf_bytes = build_pdf(st.session_state["data"], st.session_state["filenames"])
            st.download_button("⬇️ Скачать PDF", data=pdf_bytes, file_name="exitkit_handover.pdf", mime="application/pdf", use_container_width=True)
        except Exception as ex:
            st.error(f"Не удалось сформировать PDF: {ex}")
    with col_md:
        st.download_button("⬇️ Скачать Markdown", data=st.session_state["report"], file_name="handover_package.md", mime="text/markdown", use_container_width=True)
