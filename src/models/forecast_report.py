from dataclasses import dataclass
import pandas as pd


@dataclass
class ForecastReport:

    trend: str

    forecast: pd.DataFrame