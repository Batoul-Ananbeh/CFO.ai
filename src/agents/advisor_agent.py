from src.ai.gemini_provider import GeminiProvider


class AdvisorAgent:

    def __init__(self):

        self.ai = GeminiProvider()

    def analyze(
        self,
        finance,
        risk,
        forecast,
        fii,
        decision
    ):

        prompt = f"""
You are an expert Chief Financial Officer.

Analyze the following company performance.

Financial Metrics

Revenue:
{finance['revenue']}

Customers:
{finance['customers']}

Orders:
{finance['orders']}

Average Order:
{finance['average_order']}

Average Customer:
{finance['average_customer']}

Risk Level:
{risk.level}

Risk Score:
{risk.score}

Financial Intelligence Index:
{fii.fii}

Grade:
{fii.grade}

Forecast Trend:
{forecast['trend']}

System Decision:
{decision.decision}

Write a professional executive report.

Include:

1. Executive Summary

2. Financial Health

3. Risks

4. Opportunities

5. Strategic Recommendations

6. Final Conclusion

Keep it professional.
"""

        return self.ai.chat(prompt)