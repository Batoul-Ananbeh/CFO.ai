import pandas as pd
from pathlib import Path

from src.utils.logger import logger
from src.utils.constants import *


class FinancialEngine:

    def __init__(self, dataset_path):

        self.dataset_path = Path(dataset_path)
        self.df = None

    # ============================
    # Load Dataset
    # ============================

    def load(self):

        logger.info("Loading dataset...")

        self.df = pd.read_csv(
            self.dataset_path,
            encoding="latin1"
        )

        logger.info(f"Loaded {len(self.df)} rows")

        return self.df

    # ============================
    # Clean Dataset
    # ============================

    def clean(self):

        logger.info("Cleaning dataset...")

        self.df = self.df.dropna(subset=[CUSTOMER_COLUMN])
        self.df = self.df.dropna(subset=[DESCRIPTION_COLUMN])

        self.df = self.df[self.df[PRICE_COLUMN] > 0]
        self.df = self.df[self.df[QUANTITY_COLUMN] > 0]

        self.df[DATE_COLUMN] = pd.to_datetime(
            self.df[DATE_COLUMN]
        )

        self.df[REVENUE_COLUMN] = (
            self.df[QUANTITY_COLUMN] *
            self.df[PRICE_COLUMN]
        )

        logger.info("Cleaning finished.")

        return self.df

    # ============================
    # KPIs
    # ============================

    def total_revenue(self):

        return float(
            self.df[REVENUE_COLUMN].sum()
        )

    def total_orders(self):

        return int(
            self.df[INVOICE_COLUMN].nunique()
        )

    def total_customers(self):

        return int(
            self.df[CUSTOMER_COLUMN].nunique()
        )

    def average_order_value(self):

        return (
            self.total_revenue()
            /
            self.total_orders()
        )

    def average_customer_value(self):

        return (
            self.total_revenue()
            /
            self.total_customers()
        )
    def growth_rate(self):
        monthly = self.monthly_revenue()

        monthly["Growth"] = (
            monthly[REVENUE_COLUMN]
            .pct_change()
            * 100
        )

        return (
            monthly["Growth"]
            .dropna()
            .mean()
        )
    # ============================
    # Monthly Revenue
    # ============================

    def monthly_revenue(self):

        temp = self.df.copy()

        temp["YearMonth"] = temp[DATE_COLUMN].dt.to_period("M")

        monthly = (
            temp.groupby("YearMonth")[REVENUE_COLUMN]
            .sum()
            .reset_index()
        )

        return monthly

    # ============================
    # Top Customers
    # ============================

    def top_customers(
        self,
        limit=10
    ):

        return (
            self.df.groupby(CUSTOMER_COLUMN)[REVENUE_COLUMN]
            .sum()
            .sort_values(ascending=False)
            .head(limit)
        )

    # ============================
    # Top Products
    # ============================

    def top_products(
        self,
        limit=10
    ):

        return (
            self.df.groupby(DESCRIPTION_COLUMN)[REVENUE_COLUMN]
            .sum()
            .sort_values(ascending=False)
            .head(limit)
        )

    # ============================
    # Monthly Growth
    # ============================

    def monthly_growth(self):

        monthly = self.monthly_revenue()

        monthly["Growth %"] = (
            monthly[REVENUE_COLUMN]
            .pct_change()
            * 100
        )

        return monthly

    # ============================
    # Largest Customer Dependency
    # ============================

    def largest_customer_dependency(self):

        customer_sales = (
            self.df.groupby(CUSTOMER_COLUMN)[REVENUE_COLUMN]
            .sum()
        )

        largest_customer = customer_sales.max()

        dependency = (
            largest_customer
            /
            self.total_revenue()
        ) * 100

        return dependency

    # ============================
    # Revenue Stability
    # ============================

    def revenue_stability(self):

        monthly = self.monthly_revenue()

        revenue_std = monthly[REVENUE_COLUMN].std()

        revenue_mean = monthly[REVENUE_COLUMN].mean()

        stability = (
            100 -
            ((revenue_std / revenue_mean) * 100)
        )

        return stability