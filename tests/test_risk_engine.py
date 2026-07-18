from src.engines.risk_engine import RiskEngine

risk = RiskEngine()

print("=" * 50)
print("RISK ENGINE TEST")
print("=" * 50)

print(risk.growth_risk(53.62))
print(risk.revenue_risk(67.41))
print(risk.dependency_risk(3.14))
print(risk.overall_risk(
    53.62,
    67.41,
    3.14
))