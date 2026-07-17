import pandas as pd

from pathlib import Path
from src.utils.constants import *
from src.utils.logger import logger

class FinancialEngine:

    def __init__(self, dataset_path):

        self.dataset_path = Path(dataset_path)

        self.df = None

    # -----------------------------
    # Load Dataset
    # -----------------------------

    def load(self):

        logger.info("Loading Dataset...")

        self.df = pd.read_csv(
            self.dataset_path,
            encoding="latin1"
        )

        logger.info(
            f"Dataset Loaded Successfully ({len(self.df)} rows)"
        )

        return self.df
    # -----------------------------
    # Clean Dataset
    # -----------------------------

    def clean(self):

        logger.info("Cleaning Dataset...")

        self.df = self.df.dropna(
            subset=["Customer ID"]
        )

        self.df = self.df.dropna(
            subset=["Description"]
        )

        self.df = self.df[
            self.df["Price"] > 0
        ]

        self.df = self.df[
            self.df["Quantity"] > 0
        ]

        self.df["InvoiceDate"] = pd.to_datetime(
            self.df["InvoiceDate"]
        )

        self.df["Revenue"] = (
            self.df["Quantity"] *
            self.df["Price"]
        )

        logger.info("Cleaning Finished.")

        return self.df