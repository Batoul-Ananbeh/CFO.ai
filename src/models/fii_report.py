from dataclasses import dataclass


@dataclass
class FIIReport:

    score: float

    grade: str

    confidence: float

    summary: str