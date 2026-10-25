"""Readable handover reports and PDF export. No external AI calls."""
import io
import os
from datetime import datetime
from html import escape
import re

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph

UNKNOWN = {"", "неизвестно", "не указан", "не указано", "нет данных", "unknown", "not specified", "not provided", "none", "null", "n/a", "-"}


def clean(value):
    value = str(value or '').strip()
    return value if value and value.casefold() not in UNKNOWN else 'Не указано'


def known(value):
    return clean(value) != 'Не указано'


def items(data, key):
    return [x for x in data.get(key, []) if isinstance(x, dict)] if isinstance(data.get(key), list) else []


def short(text):
    return ' '.join(str(text).split())


def russian_fact(value):
    """Hide English prose in the reader-facing report; keep names separately."""
    if not known(value):
        return ''
    result = short(value)
    latin = re.findall(r'[A-Za-z]{2,}', result)
    cyrillic = re.findall(r'[А-Яа-яЁё]{2,}', result)
    if latin and ((not cyrillic and any(len(word) >= 4 for word in latin)) or len(latin) >= 3 and len(latin) > 2 * len(cyrillic)):
        return ''
    return result


def full_stop(value):
    result = short(value).rstrip()
    return result if result.endswith(('.', '!', '?', '…')) else result + '.'


def brief(value, limit=260):
    """Keep detailed procedures out of the short report without cutting a word."""
    result = short(value)
    if len(result) <= limit:
        return result
    return result[:limit].rsplit(' ', 1)[0].rstrip('.,;:') + '…'


def find_gaps(data):
    """Deterministic questions: work even with small LLMs and no network."""
    gaps = []
    for index, task in enumerate(items(data, 'tasks')):
        title = clean(task.get('task'))
        if not known(task.get('owner')):
            gaps.append({'id': f'tasks:{index}:owner', 'question': f'Кто отвечает за задачу «{title}»?', 'section': 'tasks', 'index': index, 'field': 'owner', 'input_type': 'text'})
        if not known(task.get('deadline')):
            gaps.append({'id': f'tasks:{index}:deadline', 'question': f'К какому сроку нужно выполнить задачу «{title}»?', 'section': 'tasks', 'index': index, 'field': 'deadline', 'input_type': 'date'})
    for index, project in enumerate(items(data, 'projects')):
        if not known(project.get('next_steps')):
            title = clean(project.get('name'))
            gaps.append({'id': f'projects:{index}:next_steps', 'question': f'Какое следующее действие по проекту «{title}»?', 'section': 'projects', 'index': index, 'field': 'next_steps', 'input_type': 'text'})
    return gaps


def section_blocks(data, filenames):
    """Build one short Russian report for both Markdown and PDF."""
    blocks = [
        ('h1', 'Передача дел'),
        ('muted', 'Краткий отчёт · ' + datetime.now().strftime('%d.%m.%Y')),
    ]

    projects = items(data, 'projects')
    if projects:
        blocks.append(('h2', 'Текущее состояние'))
        for project in projects:
            parts = [f"Проект «{clean(project.get('name'))}»." ]
            status = russian_fact(project.get('status'))
            background = russian_fact(project.get('background'))
            if status: parts.append('Сейчас: ' + full_stop(status))
            if background: parts.append('Контекст: ' + full_stop(background))
            blocks.append(('p', ' '.join(parts)))

    tasks = items(data, 'tasks')
    next_steps = [(project.get('name'), russian_fact(project.get('next_steps'))) for project in projects]
    next_steps = [(name, step) for name, step in next_steps if step]
    instructions = items(data, 'instructions')
    if tasks or next_steps or instructions:
        blocks.append(('h2', 'Что делать дальше'))
        for task in tasks:
            title = russian_fact(task.get('task')) or 'Задача из материалов'
            parts = [f"Задача: {full_stop(title)}"]
            owner = task.get('owner')
            deadline = russian_fact(task.get('deadline'))
            if known(owner): parts.append('Ответственный — ' + full_stop(owner))
            else: parts.append('Ответственный не указан.')
            if known(deadline): parts.append('Срок — ' + full_stop(deadline))
            else: parts.append('Срок не указан.')
            status = russian_fact(task.get('status'))
            if status: parts.append('Состояние: ' + full_stop(status))
            detail = russian_fact(task.get('details'))
            if detail and detail.casefold() not in title.casefold():
                parts.append('Для выполнения: ' + full_stop(brief(detail)))
            blocks.append(('p', ' '.join(parts)))
        for name, step in next_steps:
            blocks.append(('p', f"По проекту «{clean(name)}» следующий шаг: {full_stop(step)}"))
        for instruction in instructions:
            steps = russian_fact(instruction.get('steps'))
            if steps:
                blocks.append(('p', f"Порядок работы «{clean(instruction.get('title'))}»: {full_stop(brief(steps))}"))

    risks = items(data, 'risks')
    agreements = items(data, 'agreements')
    contacts = items(data, 'contacts')
    if risks or agreements or contacts:
        blocks.append(('h2', 'На что обратить внимание'))
        for risk in risks:
            title = russian_fact(risk.get('risk'))
            if not title: continue
            parts = ['Риск: ' + full_stop(title)]
            impact = russian_fact(risk.get('impact'))
            mitigation = russian_fact(risk.get('mitigation'))
            if impact and impact != mitigation: parts.append('Последствие: ' + full_stop(impact))
            if mitigation: parts.append('Что делать: ' + full_stop(mitigation))
            blocks.append(('p', ' '.join(parts)))
        for agreement in agreements:
            topic = russian_fact(agreement.get('topic'))
            detail = russian_fact(agreement.get('details'))
            if topic:
                if detail:
                    blocks.append(('p', f"Договорённость по теме «{topic}»: {full_stop(brief(detail))}"))
                else:
                    blocks.append(('p', f"Договорённость по теме «{topic}» зафиксирована в материалах."))
        for contact in contacts:
            name = clean(contact.get('name'))
            role = russian_fact(contact.get('role'))
            context = russian_fact(contact.get('context'))
            parts = [f"Контакт: {name}."]
            if role: parts.append('Роль: ' + full_stop(role))
            if context: parts.append(full_stop(context[:1].upper() + context[1:]))
            blocks.append(('p', ' '.join(parts)))

    custom = data.get('open_questions', [])
    custom = [russian_fact(q) for q in custom if isinstance(q, str)] if isinstance(custom, list) else []
    questions = list(dict.fromkeys([gap['question'] for gap in find_gaps(data)] + [q for q in custom if q]))
    if questions:
        blocks.append(('h2', 'Что нужно уточнить'))
        for question in questions:
            blocks.append(('p', full_stop(question)))

    if filenames:
        blocks.append(('meta', 'Материалы: ' + ', '.join(dict.fromkeys(filenames)) + '.'))
    blocks.append(('footer', 'Перед передачей дел сверьте сроки, ответственных и договорённости с исходными материалами.'))
    return blocks


def build_markdown(data, filenames):
    output = []
    for kind, value in section_blocks(data, filenames):
        if kind == 'h1': output.extend(['# ' + value, ''])
        elif kind == 'h2': output.extend(['## ' + value, ''])
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
        'h1': ParagraphStyle('h1', fontName=bold, fontSize=19, leading=24, textColor=navy, spaceAfter=8),
        'h2': ParagraphStyle('h2', fontName=bold, fontSize=12, leading=16, textColor=navy, spaceBefore=16, spaceAfter=7, keepWithNext=True),
        'p': ParagraphStyle('p', fontName=regular, fontSize=10, leading=15, textColor=navy, spaceAfter=8),
        'meta': ParagraphStyle('meta', fontName=regular, fontSize=8, leading=12, textColor=muted, spaceBefore=10, spaceAfter=6),
        'muted': ParagraphStyle('muted', fontName=regular, fontSize=8.5, leading=12, textColor=muted, spaceAfter=13),
        'footer': ParagraphStyle('footer', fontName=regular, fontSize=8, leading=12, textColor=muted, spaceBefore=8)
    }
    story = []
    for kind, content in section_blocks(data, filenames):
        text = escape(str(content)).replace('\n', '<br/>')
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
