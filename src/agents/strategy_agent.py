class StrategyAgent:

    def decide(

        self,

        fii,

        risk,

        trend

    ):

        if fii >= 80 and risk == "LOW":

            if trend == "UP":

                return "EXPAND BUSINESS"

        if risk == "HIGH":

            return "CUT COSTS"

        if trend == "DOWN":

            return "PROTECT CASH"

        return "KEEP CURRENT STRATEGY"