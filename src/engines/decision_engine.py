from src.models.decision_report import DecisionReport


class DecisionEngine:

    def decide(

        self,

        fii,

        risk_level,

        trend

    ):

        # ------------------------
        # Excellent Business
        # ------------------------

        if fii >= 85:

            if risk_level == "LOW":

                if trend == "UP":

                    return DecisionReport(

                        decision="EXPAND",

                        reason="Business is healthy with strong growth and low risk.",

                        confidence=98

                    )

        # ------------------------

        if fii >= 75:

            if risk_level != "HIGH":

                return DecisionReport(

                    decision="INVEST",

                    reason="Good financial performance. Consider investing for growth.",

                    confidence=92

                )

        # ------------------------

        if fii >= 60:

            return DecisionReport(

                decision="MAINTAIN",

                reason="Business is stable. Focus on operational improvements.",

                confidence=88

            )

        # ------------------------

        if fii >= 45:

            return DecisionReport(

                decision="OPTIMIZE",

                reason="Business performance is average. Reduce costs and improve KPIs.",

                confidence=86

            )

        # ------------------------

        return DecisionReport(

            decision="RECOVERY",

            reason="Business is underperforming. Immediate financial intervention required.",

            confidence=95

        )