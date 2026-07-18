from dataclasses import dataclass


@dataclass
class FIIResult:

    fii: float

    grade: str

    confidence: float

    summary: str


class FIIEngine:

    def calculate(
        self,
        revenue_stability,
        dependency_score,
        growth_score,
        risk_score
    ):

        # --------------------------
        # Financial Intelligence Index
        # --------------------------

        fii = (

            revenue_stability * 0.30 +

            dependency_score * 0.20 +

            growth_score * 0.30 +

            (100 - risk_score) * 0.20

        )

        # --------------------------

        if fii >= 85:

            grade = "A+"

        elif fii >= 75:

            grade = "A"

        elif fii >= 65:

            grade = "B"

        elif fii >= 55:

            grade = "C"

        else:

            grade = "D"

        confidence = min(
            99,
            70 + fii / 4
        )

        summary = (
            f"Financial Intelligence Index = "
            f"{fii:.2f}"
        )

        return FIIResult(

            fii,

            grade,

            confidence,

            summary

        )