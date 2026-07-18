from src.engines.fii_engine import FIIEngine

engine = FIIEngine()

result = engine.calculate(

    revenue_stability=67.41,

    dependency_score=68.56,

    growth_score=53.62,

    risk_score=38

)

print("=" * 50)

print("FII ENGINE")

print("=" * 50)

print(result)