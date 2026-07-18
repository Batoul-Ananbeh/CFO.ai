from src.engines.forecast_engine import ForecastEngine


class ForecastAgent:

    def __init__(self):

        self.engine = ForecastEngine()

    def analyze(self, monthly):

        forecast = self.engine.predict(

            monthly,

            6

        )

        forecast["MonthIndex"] = forecast["MonthIndex"].astype(int)

        forecast["ForecastRevenue"] = forecast["ForecastRevenue"].astype(float)

        return {

            "forecast": forecast.to_dict(

                orient="records"

            ),

            "trend": str(

                self.engine.trend(

                    monthly

                )

            )

        }