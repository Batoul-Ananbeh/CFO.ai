"""Deterministic intent analysis for financial user requests."""

from __future__ import annotations

import re
from dataclasses import dataclass

from src.planning.intents import FinancialIntent


_ARABIC_DIACRITICS_RE = re.compile(
    "[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed]"
)

_ARABIC_NORMALIZATION_TABLE = str.maketrans(
    {
        "\u0622": "\u0627",
        "\u0623": "\u0627",
        "\u0625": "\u0627",
        "\u0649": "\u064a",
        "\u0624": "\u0648",
        "\u0626": "\u064a",
        "\u0640": "",
    }
)


@dataclass(frozen=True, slots=True)
class IntentRule:
    """Keywords associated with one financial intent."""

    intent: FinancialIntent
    keywords: tuple[str, ...]


INTENT_RULES: tuple[IntentRule, ...] = (
    IntentRule(
        intent=FinancialIntent.EXECUTIVE_CFO_BRIEF,
        keywords=(
            "executive summary",
            "executive brief",
            "cfo report",
            "cfo brief",
            "full financial report",
            "complete financial report",
            "overall financial position",
            "\u062a\u0642\u0631\u064a\u0631 cfo",
            "\u062a\u0642\u0631\u064a\u0631 "
            "\u0627\u0644\u0645\u062f\u064a\u0631 "
            "\u0627\u0644\u0645\u0627\u0644\u064a",
            "\u062a\u0642\u0631\u064a\u0631 "
            "\u0645\u0627\u0644\u064a "
            "\u0643\u0627\u0645\u0644",
            "\u0627\u0644\u062a\u0642\u0631\u064a\u0631 "
            "\u0627\u0644\u0645\u0627\u0644\u064a "
            "\u0627\u0644\u0643\u0627\u0645\u0644",
            "\u0645\u0644\u062e\u0635 "
            "\u062a\u0646\u0641\u064a\u0630\u064a",
            "\u0627\u0644\u0648\u0636\u0639 "
            "\u0627\u0644\u0645\u0627\u0644\u064a "
            "\u0627\u0644\u0643\u0627\u0645\u0644",
            "\u062d\u0644\u0644 "
            "\u0627\u0644\u0634\u0631\u0643\u0629 "
            "\u0628\u0627\u0644\u0643\u0627\u0645\u0644",
        ),
    ),
    IntentRule(
        intent=FinancialIntent.STRATEGY_ANALYSIS,
        keywords=(
            "strategy",
            "strategic",
            "capital allocation",
            "cost optimization",
            "growth plan",
            "financial priorities",
            "\u0627\u0633\u062a\u0631\u0627\u062a\u064a\u062c\u064a\u0629",
            "\u0627\u0633\u062a\u0631\u0627\u062a\u064a\u062c\u064a",
            "\u062e\u0637\u0629 \u0646\u0645\u0648",
            "\u062a\u062e\u0635\u064a\u0635 "
            "\u0631\u0623\u0633 "
            "\u0627\u0644\u0645\u0627\u0644",
            "\u062e\u0641\u0636 "
            "\u0627\u0644\u062a\u0643\u0627\u0644\u064a\u0641",
            "\u0627\u0644\u0623\u0648\u0644\u0648\u064a\u0627\u062a "
            "\u0627\u0644\u0645\u0627\u0644\u064a\u0629",
        ),
    ),
    IntentRule(
        intent=FinancialIntent.FORECAST_ANALYSIS,
        keywords=(
            "forecast",
            "projection",
            "cash runway",
            "future cash",
            "future revenue",
            "expected scenario",
            "\u062a\u0648\u0642\u0639",
            "\u062a\u0646\u0628\u0624",
            "\u0627\u0644\u062a\u062f\u0641\u0642 "
            "\u0627\u0644\u0646\u0642\u062f\u064a "
            "\u0627\u0644\u0645\u062a\u0648\u0642\u0639",
            "\u0627\u0644\u0625\u064a\u0631\u0627\u062f\u0627\u062a "
            "\u0627\u0644\u0645\u0633\u062a\u0642\u0628\u0644\u064a\u0629",
            "\u0627\u0644\u0645\u0635\u0631\u0648\u0641\u0627\u062a "
            "\u0627\u0644\u0645\u0633\u062a\u0642\u0628\u0644\u064a\u0629",
            "\u0645\u062f\u0629 "
            "\u0628\u0642\u0627\u0621 "
            "\u0627\u0644\u0633\u064a\u0648\u0644\u0629",
        ),
    ),
    IntentRule(
        intent=FinancialIntent.RISK_ANALYSIS,
        keywords=(
            "risk",
            "audit",
            "internal control",
            "fraud indicator",
            "suspicious transaction",
            "control weakness",
            "\u0645\u062e\u0627\u0637\u0631",
            "\u062a\u062f\u0642\u064a\u0642",
            "\u0631\u0642\u0627\u0628\u0629 "
            "\u062f\u0627\u062e\u0644\u064a\u0629",
            "\u0639\u0645\u0644\u064a\u0629 "
            "\u0645\u0634\u0628\u0648\u0647\u0629",
            "\u0645\u0639\u0627\u0645\u0644\u0629 "
            "\u0645\u0634\u0628\u0648\u0647\u0629",
            "\u0636\u0639\u0641 "
            "\u0631\u0642\u0627\u0628\u064a",
        ),
    ),
    IntentRule(
        intent=FinancialIntent.CONTROLLER_REVIEW,
        keywords=(
            "controller",
            "review journal",
            "review entry",
            "trial balance",
            "approve entry",
            "accounting review",
            "\u0631\u0627\u062c\u0639 "
            "\u0627\u0644\u0642\u064a\u062f",
            "\u0645\u0631\u0627\u062c\u0639\u0629 "
            "\u0627\u0644\u0642\u064a\u062f",
            "\u0645\u064a\u0632\u0627\u0646 "
            "\u0627\u0644\u0645\u0631\u0627\u062c\u0639\u0629",
            "\u0627\u0644\u0645\u0631\u0627\u0642\u0628 "
            "\u0627\u0644\u0645\u0627\u0644\u064a",
            "\u062a\u062f\u0642\u064a\u0642 "
            "\u0627\u0644\u0642\u064a\u062f",
            "\u0627\u0639\u062a\u0645\u0627\u062f "
            "\u0627\u0644\u0642\u064a\u062f",
        ),
    ),
    IntentRule(
        intent=FinancialIntent.GENERAL_LEDGER,
        keywords=(
            "general ledger",
            "journal entry",
            "ledger entry",
            "debit and credit",
            "accounting entry",
            "\u062f\u0641\u062a\u0631 "
            "\u0627\u0644\u0623\u0633\u062a\u0627\u0630",
            "\u0642\u064a\u062f "
            "\u064a\u0648\u0645\u064a\u0629",
            "\u0627\u0644\u0642\u064a\u062f "
            "\u0627\u0644\u0645\u062d\u0627\u0633\u0628\u064a",
            "\u0645\u062f\u064a\u0646 "
            "\u0648\u062f\u0627\u0626\u0646",
            "\u0627\u0634\u0631\u062d "
            "\u0627\u0644\u0642\u064a\u062f",
        ),
    ),
)


class FinancialIntentAnalyzer:
    """
    Identify financial intents from Arabic or English requests.

    This implementation is deterministic, fast, auditable,
    and does not require an LLM call.
    """

    def analyze(
        self,
        user_request: str,
    ) -> set[FinancialIntent]:
        """Return all financial intents detected in the request."""

        normalized_request = self._normalize(user_request)

        if not normalized_request:
            return {
                FinancialIntent.EXECUTIVE_CFO_BRIEF,
            }

        detected_intents: set[FinancialIntent] = set()

        for rule in INTENT_RULES:
            for keyword in rule.keywords:
                normalized_keyword = self._normalize(keyword)

                if normalized_keyword in normalized_request:
                    detected_intents.add(rule.intent)
                    break

        if not detected_intents:
            detected_intents.add(
                FinancialIntent.EXECUTIVE_CFO_BRIEF
            )

        return detected_intents

    @staticmethod
    def _normalize(
        value: str,
    ) -> str:
        """
        Normalize Arabic and English text before matching.

        Removes Arabic diacritics and tatweel, normalizes common
        Arabic letter variants, lowercases English, and collapses
        repeated whitespace.
        """

        normalized = value.strip().lower()

        normalized = _ARABIC_DIACRITICS_RE.sub(
            "",
            normalized,
        )

        normalized = normalized.translate(
            _ARABIC_NORMALIZATION_TABLE
        )

        normalized = re.sub(
            r"\s+",
            " ",
            normalized,
        )

        return normalized
