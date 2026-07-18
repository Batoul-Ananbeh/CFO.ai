from dataclasses import dataclass


@dataclass
class RiskResult:

    score: float
    level: str
    message: str


class RiskEngine:

    # -----------------------------
    # Growth Risk
    # -----------------------------

    def growth_risk(self, growth_score):

        if growth_score >= 80:
            return RiskResult(10, "LOW", "Strong business growth.")

        elif growth_score >= 60:
            return RiskResult(30, "LOW", "Healthy growth.")

        elif growth_score >= 40:
            return RiskResult(60, "MEDIUM", "Growth is slowing.")

        else:
            return RiskResult(90, "HIGH", "Business growth is weak.")

    # -----------------------------
    # Revenue Stability Risk
    # -----------------------------

    def revenue_risk(self, stability):

        if stability >= 80:
            return RiskResult(10, "LOW", "Revenue is very stable.")

        elif stability >= 60:
            return RiskResult(35, "LOW", "Revenue is acceptable.")

        elif stability >= 40:
            return RiskResult(65, "MEDIUM", "Revenue fluctuates.")

        else:
            return RiskResult(90, "HIGH", "Revenue is unstable.")

    # -----------------------------
    # Customer Dependency Risk
    # -----------------------------

    def dependency_risk(self, dependency):

        if dependency <= 5:
            return RiskResult(5, "LOW", "Excellent diversification.")

        elif dependency <= 10:
            return RiskResult(30, "LOW", "Good diversification.")

        elif dependency <= 20:
            return RiskResult(65, "MEDIUM", "Customer concentration detected.")

        else:
            return RiskResult(95, "HIGH", "Business depends on few customers.")

    # -----------------------------
    # Overall Risk
    # -----------------------------

    def overall_risk(
        self,
        growth_score,
        stability,
        dependency
    ):

        g = self.growth_risk(growth_score).score
        r = self.revenue_risk(stability).score
        d = self.dependency_risk(dependency).score

        overall = (g + r + d) / 3

        if overall < 30:
            level = "LOW"

        elif overall < 70:
            level = "MEDIUM"

        else:
            level = "HIGH"

        return RiskResult(
            overall,
            level,
            f"Overall business risk is {level}"
        )