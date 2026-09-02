from dataclasses import dataclass


@dataclass
class RiskReport:

    score: float

    level: str

    message: str