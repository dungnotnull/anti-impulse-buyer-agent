"""Dark pattern detection API endpoint."""

from fastapi import APIRouter
from pydantic import BaseModel

from backend.services.dark_pattern_detector import analyze_page_text, get_dark_pattern_warnings

router = APIRouter(prefix="/api", tags=["dark_patterns"])


class DarkPatternRequest(BaseModel):
    text: str = ""


class DarkPatternResponse(BaseModel):
    count: int = 0
    warnings: list[str] = []
    patterns: list[dict] = []


@router.post("/detect-dark-patterns", response_model=DarkPatternResponse)
def detect_dark_patterns(req: DarkPatternRequest):
    """Analyze text for dark patterns. Returns count, warnings, and pattern details."""
    if not req.text:
        return DarkPatternResponse()

    patterns = analyze_page_text(req.text)
    warnings = get_dark_pattern_warnings(req.text)

    return DarkPatternResponse(
        count=len(patterns),
        warnings=warnings,
        patterns=patterns,
    )
