from src.agents.finance_agent import FinanceAgent
from src.agents.forecast_agent import ForecastAgent
from src.agents.risk_agent import RiskAgent

from src.engines.scoring_engine import ScoringEngine
from src.engines.fii_engine import FIIEngine
from src.engines.decision_engine import DecisionEngine

from src.ai.ai_advisor import AIAdvisor


class ChiefCFO:

    def __init__(self, dataset):

        self.finance = FinanceAgent(dataset)

        self.forecast = ForecastAgent()

        self.risk = RiskAgent()

        self.scoring = ScoringEngine()

        self.fii = FIIEngine()

        self.decision = DecisionEngine()

        self.ai = AIAdvisor()

    # ----------------------------------------------------
    # Main Pipeline
    # ----------------------------------------------------

    def run(self):

        # ---------------------------------
        # Finance
        # ---------------------------------

        finance = self.finance.analyze()

        growth = self.finance.engine.growth_rate()

        dependency = finance["dependency"]

        stability = finance["stability"]

        # ---------------------------------
        # KPI Scores
        # ---------------------------------

        growth_score = self.scoring.growth_score(
            growth
        )

        dependency_score = self.scoring.dependency_score(
            dependency
        )

        stability_score = self.scoring.stability_score(
            stability
        )

        # ---------------------------------
        # Risk
        # ---------------------------------

        risk = self.risk.analyze(

            growth_score,

            stability,

            dependency

        )

        # ---------------------------------
        # Forecast
        # ---------------------------------

        forecast = self.forecast.analyze(

            finance["monthly"]

        )

        # ---------------------------------
        # Financial Intelligence Index
        # ---------------------------------

        fii = self.fii.calculate(

            revenue_stability=stability_score,

            dependency_score=dependency_score,

            growth_score=growth_score,

            risk_score=risk.score

        )

        # ---------------------------------
        # Decision
        # ---------------------------------

        decision = self.decision.decide(

            fii=fii.fii,

            risk_level=risk.level,

            trend=forecast["trend"]

        )

        # ---------------------------------
        # AI Executive Report
        # ---------------------------------

        ai_report = self.ai.generate(

            finance,

            risk,

            forecast,

            fii,

            decision

        )

        # ---------------------------------
        # Final Report
        # ---------------------------------

        return {

            "Finance": finance,

            "Risk": risk,

            "Forecast": forecast,

            "FII": fii,

            "Decision": decision,

            "AI_Report": ai_report

        }