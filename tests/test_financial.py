from src.engines.financial_engine import FinancialEngine

engine = FinancialEngine("Data/online_retail_II.csv")

engine.load()
engine.clean()

print("=" * 50)
print("FINANCIAL ENGINE TEST")
print("=" * 50)

print("Total Revenue:", engine.total_revenue())
print("Total Orders:", engine.total_orders())
print("Total Customers:", engine.total_customers())
print("Average Order Value:", engine.average_order_value())
print("Average Customer Value:", engine.average_customer_value())
print("Largest Customer Dependency:", engine.largest_customer_dependency())
print("Revenue Stability:", engine.revenue_stability())