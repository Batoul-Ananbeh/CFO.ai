from src.engines.financial_engine import FinancialEngine


class FinanceAgent:

    def __init__(self, dataset):

        self.engine = FinancialEngine(dataset)

        self.engine.load()

        self.engine.clean()

    def analyze(self):

        return {

            "revenue": self.engine.total_revenue(),

            "orders": self.engine.total_orders(),

            "customers": self.engine.total_customers(),

            "average_order": self.engine.average_order_value(),

            "average_customer": self.engine.average_customer_value(),

            "dependency": self.engine.largest_customer_dependency(),

            "stability": self.engine.revenue_stability(),

            "monthly": self.engine.monthly_revenue()

        }