from src.engines.financial_engine import FinancialEngine
from src.engines.scoring_engine import ScoringEngine

engine = FinancialEngine(
    "Data/online_retail_II.csv"
)

engine.load()
engine.clean()

scoring = ScoringEngine()

growth = engine.growth_rate()

dependency = engine.largest_customer_dependency()

stability = engine.revenue_stability()

print("=" * 50)
print("SCORING ENGINE")
print("=" * 50)

print(
    "Growth Score:",
    scoring.growth_score(growth)
)

print(
    "Dependency Score:",
    scoring.dependency_score(
        dependency
    )
)

print(
    "Stability Score:",
    scoring.stability_score(
        stability
    )
)