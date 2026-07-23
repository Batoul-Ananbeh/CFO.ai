from __future__ import annotations

from importlib.metadata import (
    PackageNotFoundError,
    version,
)

from dotenv import load_dotenv
from google import genai

from src.ai.settings import AISettings


def get_package_version(package_name: str) -> str:
    try:
        return version(package_name)
    except PackageNotFoundError:
        return "NOT INSTALLED"


load_dotenv()

settings = AISettings.from_env()
settings.validate()

print("=== CFO.ai Gemini Diagnostics ===")
print("google-genai version:", get_package_version("google-genai"))
print("Model:", settings.model)
print("Provider:", settings.provider)
print("API key loaded:", bool(settings.api_key))
print("API key length:", len(settings.api_key or ""))
print()

client = genai.Client(
    api_key=settings.api_key,
)

try:
    print("Sending minimal Gemini request...")

    response = client.models.generate_content(
        model=settings.model,
        contents=(
            "Reply with exactly the following two letters: OK"
        ),
    )

    print()
    print("=== SUCCESS ===")
    print("Response text:", response.text)

except Exception as exception:
    print()
    print("=== GEMINI FAILURE ===")
    print(
        "Exception type:",
        f"{type(exception).__module__}."
        f"{type(exception).__name__}",
    )
    print("Exception message:")
    print(str(exception))
    print()
    print("Full representation:")
    print(repr(exception))

    raise

finally:
    close_method = getattr(
        client,
        "close",
        None,
    )

    if callable(close_method):
        close_method()
