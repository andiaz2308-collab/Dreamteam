from openai import OpenAI

from app.core.config import OPENAI_API_KEY, OPENAI_MODEL
from app.services.ai.usage import record_ai_call


MAX_INPUT_CHARS = 12_000


class StructuredOutputError(Exception):
    pass


def parse_structured(model_class, system_prompt: str, user_payload: str):
    if not OPENAI_API_KEY:
        raise StructuredOutputError(
            "OPENAI_API_KEY no esta configurada en el servidor."
        )

    client = OpenAI(api_key=OPENAI_API_KEY)
    payload = user_payload[:MAX_INPUT_CHARS]

    try:
        response = client.responses.parse(
            model=OPENAI_MODEL,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": payload},
            ],
            text_format=model_class,
        )
    except Exception as exc:
        record_ai_call("structured", False, type(exc).__name__)
        detail = str(exc).strip() or type(exc).__name__
        raise StructuredOutputError(
            f"OpenAI no respondió ({OPENAI_MODEL}): {detail[:240]}"
        ) from exc

    parsed = response.output_parsed
    if parsed is None:
        record_ai_call("structured", False, "empty_parsed")
        raise StructuredOutputError(
            "El modelo no devolvió un esquema válido."
        )
    record_ai_call(
        "structured",
        True,
        f"model={OPENAI_MODEL} schema={model_class.__name__}",
    )
    return parsed
