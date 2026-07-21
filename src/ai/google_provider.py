"""Google Gemini implementation of the LLM provider."""

from __future__ import annotations

import json
from typing import Any, TypeVar

from google import genai
from google.genai import errors, types
from pydantic import BaseModel

from src.ai.errors import (
    AIProviderError,
    AIProviderResponseError,
)
from src.ai.models import AIRequest, AITextResult
from src.ai.provider import LLMProvider
from src.ai.settings import AISettings
from src.ai.telemetry import (
    AICallMetadata,
    AIUsageMetadata,
)


OutputModel = TypeVar(
    "OutputModel",
    bound=BaseModel,
)


_RETRYABLE_STATUS_CODES = {
    408,
    429,
    500,
    502,
    503,
    504,
}


class GoogleGenAIProvider(LLMProvider):
    """Google Gemini provider using the official Gen AI SDK."""

    def __init__(
        self,
        settings: AISettings | None = None,
        client: genai.Client | None = None,
    ) -> None:
        self.settings = settings or AISettings.from_env()
        self._last_call_metadata: AICallMetadata | None = None

        if client is None:
            self.settings.validate()

            retry_options = types.HttpRetryOptions(
                attempts=self.settings.retry_attempts,
                initial_delay=1.0,
                max_delay=16.0,
            )

            http_options = types.HttpOptions(
                timeout=self.settings.timeout_ms,
                retry_options=retry_options,
            )

            client = genai.Client(
                api_key=self.settings.api_key,
                http_options=http_options,
            )

        self.client = client

    @property
    def last_call_metadata(
        self,
    ) -> AICallMetadata | None:
        """Return metadata collected from the latest Gemini call."""

        return self._last_call_metadata

    def _build_prompt(
        self,
        request: AIRequest,
    ) -> str:
        context_json = json.dumps(
            request.context,
            ensure_ascii=False,
            default=str,
            indent=2,
        )

        return (
            f"USER REQUEST:\n{request.user_input}\n\n"
            f"VERIFIED CONTEXT:\n{context_json}"
        )

    def _build_config(
        self,
        request: AIRequest,
        *,
        output_schema: type[BaseModel] | None = None,
    ) -> types.GenerateContentConfig:
        config_values: dict[str, Any] = {
            "system_instruction": request.instruction,
            "temperature": self.settings.temperature,
            "max_output_tokens": (
                self.settings.max_output_tokens
            ),
        }

        if output_schema is not None:
            config_values.update(
                {
                    "response_mime_type": "application/json",
                    "response_schema": output_schema,
                }
            )

        return types.GenerateContentConfig(
            **config_values
        )

    def _call_generate_content(
        self,
        *,
        request: AIRequest,
        output_schema: type[BaseModel] | None = None,
    ) -> Any:
        self._last_call_metadata = None

        try:
            return self.client.models.generate_content(
                model=self.settings.model,
                contents=self._build_prompt(request),
                config=self._build_config(
                    request,
                    output_schema=output_schema,
                ),
            )
        except errors.APIError as exc:
            raw_code = getattr(
                exc,
                "code",
                None,
            )

            try:
                status_code = (
                    int(raw_code)
                    if raw_code is not None
                    else None
                )
            except (TypeError, ValueError):
                status_code = None

            raise AIProviderError(
                "Gemini request failed.",
                provider=self.settings.provider,
                status_code=status_code,
                retryable=(
                    status_code
                    in _RETRYABLE_STATUS_CODES
                ),
            ) from exc
        except Exception as exc:
            raise AIProviderError(
                "Unexpected Gemini provider failure.",
                provider=self.settings.provider,
                retryable=False,
            ) from exc

    def _capture_metadata(
        self,
        response: Any,
    ) -> None:
        raw_usage = getattr(
            response,
            "usage_metadata",
            None,
        )

        usage = None

        if raw_usage is not None:
            usage = AIUsageMetadata(
                prompt_tokens=getattr(
                    raw_usage,
                    "prompt_token_count",
                    None,
                ),
                output_tokens=getattr(
                    raw_usage,
                    "candidates_token_count",
                    None,
                ),
                total_tokens=getattr(
                    raw_usage,
                    "total_token_count",
                    None,
                ),
                cached_tokens=getattr(
                    raw_usage,
                    "cached_content_token_count",
                    None,
                ),
                thought_tokens=getattr(
                    raw_usage,
                    "thoughts_token_count",
                    None,
                ),
            )

        self._last_call_metadata = AICallMetadata(
            provider=self.settings.provider,
            model=self.settings.model,
            response_id=getattr(
                response,
                "response_id",
                None,
            ),
            model_version=getattr(
                response,
                "model_version",
                None,
            ),
            usage=usage,
        )

    def generate_text(
        self,
        request: AIRequest,
    ) -> AITextResult:
        response = self._call_generate_content(
            request=request,
        )

        self._capture_metadata(response)

        content = response.text or ""

        if not content.strip():
            raise AIProviderResponseError(
                "Gemini returned an empty text response.",
                provider=self.settings.provider,
                retryable=False,
            )

        return AITextResult(
            content=content,
            model=self.settings.model,
            provider=self.settings.provider,
            metadata=self.last_call_metadata,
        )

    def generate_structured(
        self,
        request: AIRequest,
        output_schema: type[OutputModel],
    ) -> OutputModel:
        response = self._call_generate_content(
            request=request,
            output_schema=output_schema,
        )

        self._capture_metadata(response)

        try:
            if response.parsed is not None:
                if isinstance(
                    response.parsed,
                    output_schema,
                ):
                    return response.parsed

                return output_schema.model_validate(
                    response.parsed
                )

            if not response.text:
                raise AIProviderResponseError(
                    "Gemini returned an empty structured response.",
                    provider=self.settings.provider,
                    retryable=False,
                )

            return output_schema.model_validate_json(
                response.text
            )
        except AIProviderResponseError:
            raise
        except Exception as exc:
            raise AIProviderResponseError(
                "Gemini returned an invalid structured response.",
                provider=self.settings.provider,
                retryable=False,
            ) from exc
