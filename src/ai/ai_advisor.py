from datetime import datetime

from src.ai.gemini_provider import GeminiProvider


class AIAdvisor:

    def __init__(self):

        self.ai = GeminiProvider()

    def generate(

        self,

        finance,

        risk,

        forecast,

        fii,

        decision

    ):

        today = datetime.now().strftime("%Y-%m-%d")

        prompt = f"""
You are the Chief Financial Officer (CFO) of a multinational company.

Today's Date: {today}

Prepare a professional Executive Financial Report.

Financial Data

Total Revenue: {finance['revenue']}

Orders: {finance['orders']}

Customers: {finance['customers']}

Average Order Value: {finance['average_order']}

Average Customer Value: {finance['average_customer']}

Customer Dependency: {finance['dependency']:.2f}%

Revenue Stability: {finance['stability']:.2f}

Financial Intelligence Index: {fii.fii:.2f}

Financial Grade: {fii.grade}

Risk Level: {risk.level}

Risk Score: {risk.score:.2f}

Forecast Trend: {forecast['trend']}

Final Decision: {decision.decision}

Write a detailed executive report with:

1. Executive Summary

2. Financial Performance

3. Risks

4. Opportunities

5. Strategic Recommendations

6. Final Conclusion

Use professional business language.

Do NOT invent numbers.

Use ONLY the provided data.
"""

        return self.ai.chat(prompt)