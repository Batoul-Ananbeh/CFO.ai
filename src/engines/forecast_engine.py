import pandas as pd

from sklearn.linear_model import LinearRegression


class ForecastEngine:

    def __init__(self):

        self.model = LinearRegression()

    # ------------------------------------
    # Train Forecast Model
    # ------------------------------------

    def train(self, monthly_revenue):

        df = monthly_revenue.copy()

        df = df.reset_index(drop=True)

        df["MonthIndex"] = range(len(df))

        X = df[["MonthIndex"]]

        y = df["Revenue"]

        self.model.fit(X, y)

        return self.model

    # ------------------------------------
    # Forecast
    # ------------------------------------

    def predict(self, monthly_revenue, months=6):

        df = monthly_revenue.copy()

        df = df.reset_index(drop=True)

        df["MonthIndex"] = range(len(df))

        self.train(df)

        future_index = pd.DataFrame({

            "MonthIndex": range(

                len(df),

                len(df) + months

            )

        })

        predictions = self.model.predict(

            future_index

        )

        result = future_index.copy()

        result["ForecastRevenue"] = predictions

        return result

    # ------------------------------------
    # Trend
    # ------------------------------------

    def trend(self, monthly_revenue):

        prediction = self.predict(

            monthly_revenue,

            1

        )

        current = monthly_revenue["Revenue"].iloc[-1]

        future = prediction["ForecastRevenue"].iloc[0]

        if future > current:

            return "UP"

        elif future < current:

            return "DOWN"

        return "STABLE"