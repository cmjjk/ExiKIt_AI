from pathlib import Path
import json
import pytest
from fastapi.testclient import TestClient
from app.agent import Handover, _extract_json
from app.main import app, pdf_content, read_document

client = TestClient(app)


def test_health():
    assert client.get('/api/health').json() == {'status': 'ok'}


def test_extract_json_fenced():
    assert _extract_json('```json\n{"tasks": []}\n```')['tasks'] == []


def test_txt():
    assert read_document('a.txt', 'Привет'.encode()) == 'Привет'


def test_unsupported():
    with pytest.raises(Exception):
        read_document('a.exe', b'abc')


def test_export_pdf():
    payload = Handover.model_validate(json.loads((Path(__file__).parent.parent / 'examples/handover.json').read_text()))
    result = pdf_content(payload)
    assert result.startswith(b'%PDF')
    response = client.post('/api/export/pdf', json=payload.model_dump())
    assert response.status_code == 200
    assert response.content.startswith(b'%PDF')


def test_no_source():
    response = client.post('/api/generate', data={'notes': ''})
    assert response.status_code == 400
