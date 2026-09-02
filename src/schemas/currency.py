"""Currency utilities for the CFO.ai platform."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Mapping

from iso4217 import Currency


@dataclass(frozen=True, slots=True)
class CurrencyMetadata:
    """Normalized ISO 4217 currency metadata."""

    code: str
    name: str
    numeric_code: str
    minor_unit: int | None


def normalize_currency_code(value: str) -> str:
    """
    Normalize and validate an ISO 4217 currency code.

    Examples:
        usd -> USD
        Jod -> JOD
        eur -> EUR
    """

    if not isinstance(value, str):
        raise TypeError("currency code must be a string")

    normalized = value.strip().upper()

    if not normalized:
        raise ValueError("currency code cannot be empty")

    try:
        Currency(normalized)
    except ValueError as exc:
        raise ValueError(
            f"unsupported ISO 4217 currency code: {normalized}"
        ) from exc

    return normalized


def normalize_external_currency_code(
    value: str,
    aliases: Mapping[str, str] | None = None,
) -> tuple[str, str | None]:
    """
    Normalize a currency value received from a legacy or external system.

    Returns:
        A tuple containing:
        - normalized ISO code
        - original alias when an alias conversion occurred

    Example:
        JD -> JOD
    """

    if not isinstance(value, str):
        raise TypeError("currency code must be a string")

    raw = value.strip().upper()

    if not raw:
        raise ValueError("currency code cannot be empty")

    alias_map = {
        key.strip().upper(): mapped_value.strip().upper()
        for key, mapped_value in (aliases or {}).items()
    }

    mapped_code = alias_map.get(raw, raw)
    normalized = normalize_currency_code(mapped_code)

    alias_used = raw if raw != normalized else None

    return normalized, alias_used


def get_currency_metadata(code: str) -> CurrencyMetadata:
    """Return metadata for a valid ISO 4217 currency."""

    normalized = normalize_currency_code(code)
    currency = Currency(normalized)

    return CurrencyMetadata(
        code=currency.code,
        name=currency.currency_name,
        numeric_code=currency.number,
        minor_unit=currency.exponent,
    )


def quantize_amount(
    amount: Decimal,
    currency_code: str,
) -> Decimal:
    """
    Round an amount according to the currency minor unit.

    Examples:
        USD -> 2 decimal places
        JOD -> 3 decimal places
        JPY -> 0 decimal places
    """

    if not isinstance(amount, Decimal):
        raise TypeError("amount must be a Decimal")

    metadata = get_currency_metadata(currency_code)

    if metadata.minor_unit is None:
        return amount

    quantum = Decimal(1).scaleb(-metadata.minor_unit)

    return amount.quantize(
        quantum,
        rounding=ROUND_HALF_EVEN,
    )