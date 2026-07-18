from src.engines.decision_engine import DecisionEngine

engine = DecisionEngine()

result = engine.decide(

    fii=82,

    risk_level="LOW",

    trend="UP"

)

print(result)