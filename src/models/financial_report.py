from dataclasses import dataclass
import pandas as pd


@dataclass
class FinancialReport:

    total_revenue: float

    total_orders: int

    total_customers: int

    average_order_value: float

    average_customer_value: float

    largest_customer_dependency: float

    revenue_stability: float

    monthly_revenue: pd.DataFrame