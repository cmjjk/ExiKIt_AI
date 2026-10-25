"""Readable handover reports and PDF export. No external AI calls."""
import io
import os
import re
from datetime import datetime
from html import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether, HRFlowable

UNKNOWN = {"", "неизвестно", "не указан", "не указано", "нет данных", "none", "null", "n/a", "-"}


def clean(value):
    value = str(value or '').strip()
    return value if value and value.casefold() not in UNKNOWN else 'Не указано'


def known(value):
    return clean(value) != 'Не указано'


def items(data, key):
    return [x for x in data.get(key, []) if isinstance(x, dict)] if isinstance(data.get(key), list) else []


def short(text):
    return ' '.join(str(text).split())


def find_gaps(data):
    """Deterministic questions: work even with small LLMs and no network."""
    gaps = []
    for index, task in enumerate(items(data, 'tasks')):
        title = clean(task.get('task'))
        if not known(task.get('owner')):
            gaps.append({'id': f'tasks:{index}:owner', 'question': f'Кто отвечает за задачу «{title}»?', 'section': 'tasks', 'index': index, 'field': 'owner'})
        if not known(task.get('deadline')):
            gaps.append({'id': f'tasks:{index}:deadline', 'question': f'К какому сроку нужно выполнить задачу «{title}»?', 'section': 'tasks', 'index': index, 'field': 'deadline'})
    for index, project in enumerate(items(data, 'projects')):
        if not known(project.get('next_steps')):
            title = clean(project.get('name'))
            gaps.append({'id': f'projects:{index}:next_steps', 'question': f'Какое следующее действие по проекту «{title}»?', 'section': 'projects', 'index': index, 'field': 'next_steps'})
    return gaps


def section_blocks(data, filenames):
    """One content model for both on-screen and PDF output."""
    blocks = [('h1', 'Передача дел'), ('muted', 'Handover Package · ' + datetime.now().strftime('%d.%m.%Y %H:%M'))]
    blocks.append(('h2', 'Главное за минуту'))
    blocks.append(('p', clean(data.get('summary'))))
    projects = items(data, 'projects')
    blocks.append(('h2', f'Текущие проекты ({len(projects)})'))
    for x in projects:
        blocks.append(('h3', clean(x.get('name'))))
        if known(x.get('background')): blocks.append(('p', 'Контекст: ' + clean(x.get('background'))))
        blocks.append(('p', f"Состояние: {clean(x.get('status'))}."))
        blocks.append(('p', f"Что делать дальше: {clean(x.get('next_steps'))}."))
        if known(x.get('decisions')): blocks.append(('p', 'Принятые решения и договорённости: ' + clean(x.get('decisions'))))
        if known(x.get('source')): blocks.append(('meta', 'Источник: ' + clean(x.get('source'))))
    if not projects: blocks.append(('p', 'Проекты в материалах не обнаружены.'))
    tasks = items(data, 'tasks')
    blocks.append(('h2', f'Ближайшие задачи ({len(tasks)})'))
    for x in tasks:
        blocks.append(('h3', clean(x.get('task'))))
        blocks.append(('p', f"Кто делает: {clean(x.get('owner'))} · Когда: {clean(x.get('deadline'))}"))
        if known(x.get('status')): blocks.append(('p', 'Состояние: ' + clean(x.get('status'))))
        if known(x.get('details')): blocks.append(('p', 'Как выполнить и что учесть: ' + clean(x.get('details'))))
        if known(x.get('source')): blocks.append(('meta', 'Источник: ' + clean(x.get('source'))))
    if not tasks: blocks.append(('p', 'Незавершённые задачи в материалах не обнаружены.'))
    risks = items(data, 'risks')
    blocks.append(('h2', f'Риски и препятствия ({len(risks)})'))
    for x in risks:
        blocks.append(('h3', clean(x.get('risk'))))
        if known(x.get('impact')): blocks.append(('p', 'Чем это грозит: ' + clean(x.get('impact'))))
        if known(x.get('mitigation')): blocks.append(('p', 'Что можно сделать: ' + clean(x.get('mitigation'))))
        if known(x.get('source')): blocks.append(('meta', 'Источник: ' + clean(x.get('source'))))
    if not risks: blocks.append(('p', 'В загруженных материалах риски не обнаружены. Это не означает, что рисков нет.'))
    contacts = items(data, 'contacts')
    blocks.append(('h2', f'К кому обращаться ({len(contacts)})'))
    for x in contacts:
        blocks.append(('h3', clean(x.get('name'))))
        blocks.append(('p', f"Роль: {clean(x.get('role'))}. {clean(x.get('context'))}"))
    if not contacts: blocks.append(('p', 'Контакты не обнаружены.'))
    instructions = items(data, 'instructions')
    blocks.append(('h2', f'Рабочие инструкции и процессы ({len(instructions)})'))
    for x in instructions:
        blocks.append(('h3', clean(x.get('title'))))
        if known(x.get('steps')): blocks.append(('p', clean(x.get('steps'))))
        if known(x.get('source')): blocks.append(('meta', 'Источник: ' + clean(x.get('source'))))
    if not instructions: blocks.append(('p', 'Пошаговые инструкции в материалах не обнаружены.'))
    agreements = items(data, 'agreements')
    blocks.append(('h2', f'Договорённости и решения ({len(agreements)})'))
    for x in agreements:
        blocks.append(('h3', clean(x.get('topic'))))
        if known(x.get('details')): blocks.append(('p', clean(x.get('details'))))
        if known(x.get('source')): blocks.append(('meta', 'Источник: ' + clean(x.get('source'))))
    if not agreements: blocks.append(('p', 'Отдельные договорённости не найдены.'))
    gaps = find_gaps(data)
    custom = data.get('open_questions', [])
    custom = [short(x) for x in custom if isinstance(x, str) and x.strip()] if isinstance(custom, list) else []
    blocks.append(('h2', 'Что нужно уточнить'))
    all_questions = [x['question'] for x in gaps] + custom
    for question in dict.fromkeys(all_questions): blocks.append(('bullet', question))
    if not all_questions: blocks.append(('p', 'Обязательных уточнений пока нет.'))
    blocks.append(('h2', 'Использованные документы'))
    for filename in filenames: blocks.append(('bullet', filename))
    blocks.append(('footer', 'Этот документ подготовлен с помощью локального AI. Перед передачей дел проверьте факты, сроки и ответственных по исходным материалам.'))
    return blocks


def build_markdown(data, filenames):
    output = []
    for kind, value in section_blocks(data, filenames):
        if kind == 'h1': output.extend(['# ' + value, ''])
        elif kind == 'h2': output.extend(['## ' + value, ''])
        elif kind == 'h3': output.extend(['### ' + value, ''])
        elif kind == 'bullet': output.append('- ' + value)
        elif kind == 'footer': output.extend(['', '---', '*' + value + '*'])
        else: output.extend([value, ''])
    return '\n'.join(output)


def _register_fonts():
    """Use locally installed system fonts; never distribute licensed fonts."""
    candidates = [
        ('/System/Library/Fonts/Supplemental/Arial.ttf', '/System/Library/Fonts/Supplemental/Arial Bold.ttf'),
        ('/Library/Fonts/Arial.ttf', '/Library/Fonts/Arial Bold.ttf'),
        ('/System/Library/Fonts/Supplemental/DejaVuSans.ttf', '/System/Library/Fonts/Supplemental/DejaVuSans-Bold.ttf'),
        ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),
    ]
    for regular, bold in candidates:
        if os.path.exists(regular):
            pdfmetrics.registerFont(TTFont('ExitBody', regular))
            pdfmetrics.registerFont(TTFont('ExitBold', bold if os.path.exists(bold) else regular))
            return 'ExitBody', 'ExitBold'
    raise RuntimeError('Для PDF нужен шрифт с кириллицей: установите Arial или DejaVu Sans.')


def build_pdf(data, filenames):
    regular, bold = _register_fonts()
    buf = io.BytesIO()
    navy = colors.HexColor('#18283F')
    muted = colors.HexColor('#65758A')
    styles = {
        'h1': ParagraphStyle('h1', fontName=bold, fontSize=22, leading=28, textColor=navy, spaceAfter=11),
        'h2': ParagraphStyle('h2', fontName=bold, fontSize=13.5, leading=19, textColor=navy, spaceBefore=19, spaceAfter=8, keepWithNext=True),
        'h3': ParagraphStyle('h3', fontName=bold, fontSize=10.5, leading=15, textColor=navy, spaceBefore=10, spaceAfter=4, keepWithNext=True),
        'p': ParagraphStyle('p', fontName=regular, fontSize=9.5, leading=15, textColor=navy, spaceAfter=5),
        'meta': ParagraphStyle('meta', fontName=regular, fontSize=8, leading=12, textColor=muted, spaceAfter=7),
        'muted': ParagraphStyle('muted', fontName=regular, fontSize=8.5, leading=13, textColor=muted, spaceAfter=8),
        'bullet': ParagraphStyle('bullet', fontName=regular, fontSize=9.5, leading=15, textColor=navy, leftIndent=12, firstLineIndent=-10, spaceAfter=4),
        'footer': ParagraphStyle('footer', fontName=regular, fontSize=8, leading=12, textColor=muted, spaceBefore=17)
    }
    story = []
    for kind, content in section_blocks(data, filenames):
        text = escape(str(content)).replace('\n', '<br/>')
        if kind == 'bullet': text = '•  ' + text
        story.append(Paragraph(text, styles[kind]))
    def on_page(canvas, doc):
        canvas.setStrokeColor(colors.HexColor('#DDE4ED'))
        canvas.line(17*mm, 19*mm, 193*mm, 19*mm)
        canvas.setFont(regular, 8)
        canvas.setFillColor(muted)
        canvas.drawString(17*mm, 14*mm, 'ExitKit AI · Передача дел')
        canvas.drawRightString(193*mm, 14*mm, f'Страница {doc.page}')
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=17*mm, bottomMargin=25*mm, title='ExitKit AI — Передача дел', author='ExitKit AI')
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return buf.getvalue()
