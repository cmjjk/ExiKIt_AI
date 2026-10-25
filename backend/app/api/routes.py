from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from app.export.markdown import to_markdown
from app.pipeline.extract import analyze
from app.schemas import AnalyzeRequest, HandoverPackage

router = APIRouter()


@router.post("/analyze", response_model=HandoverPackage)
def analyze_notes(req: AnalyzeRequest):
    return analyze(req.notes)


@router.post("/export/markdown", response_class=PlainTextResponse)
def export_markdown(pkg: HandoverPackage):
    return to_markdown(pkg)
