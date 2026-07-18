from dataclasses import dataclass


@dataclass
class DecisionReport:

    decision: str

    reason: str

    confidence: float