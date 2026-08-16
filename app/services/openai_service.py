from openai import OpenAI

from app.core.config import OPENAI_API_KEY


client = OpenAI(
    api_key=OPENAI_API_KEY
)


def test_openai_connection():
    response = client.responses.create(
        model="gpt-4o-mini",
        input="Responde solamente: AgenteCV conectado."
    )

    return response.output_text
