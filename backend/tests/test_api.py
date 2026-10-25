from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_analyze_and_export():
    r = client.post("/api/analyze", json={"notes": "Проект X, дедлайн в пятницу"})
    assert r.status_code == 200
    pkg = r.json()
    assert "tasks" in pkg
    md = client.post("/api/export/markdown", json=pkg)
    assert md.status_code == 200 and "Handover Package" in md.text
