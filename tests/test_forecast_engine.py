from src.engines.financial_engine import FinancialEngine
from src.engines.forecast_engine import ForecastEngine

engine = FinancialEngine(
    "Data/online_retail_II.csv"
)

engine.load()
engine.clean()

forecast = ForecastEngine()

monthly = engine.monthly_revenue()

future = forecast.predict(monthly, 6)

print("=" * 50)
print("FORECAST ENGINE")
print("=" * 50)

print(future)

print()

print("Trend:")

print(forecast.trend(monthly))