from openai import OpenAI

from app.core.config import OPENAI_API_KEY, OPENAI_MODEL


MAX_INPUT_CHARS = 12_000


class StructuredOutputError(Exception):
    pass


def parse_structured(model_class, system_prompt: str, user_payload: str):
    if not OPENAI_API_KEY:
        raise StructuredOutputError("OPENAI_API_KEY no esta configurada.")

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
        raise StructuredOutputError(
            "No se pudo obtener una respuesta estructurada del modelo."
        ) from exc

    parsed = response.output_parsed
    if parsed is None:
        raise StructuredOutputError(
            "El modelo no devolvió un esquema válido."
        )
    return parsed
