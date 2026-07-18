from src.engines.risk_engine import RiskEngine


class RiskAgent:

    def __init__(self):

        self.engine = RiskEngine()

    def analyze(

        self,

        growth,

        stability,

        dependency

    ):

        return self.engine.overall_risk(

            growth,

            stability,

            dependency

        )