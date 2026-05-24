import json
import re

from django.conf import settings

from google import genai
from google.genai import types


class GeminiClientError(Exception):
    pass


def clean_json_text(text):
    if not text:
        return "{}"

    text = text.strip()

    text = re.sub(r"^```json", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"^```", "", text).strip()
    text = re.sub(r"```$", "", text).strip()

    return text


def parse_json_response(text):
    try:
        return json.loads(clean_json_text(text))
    except Exception:
        match = re.search(r"\{.*\}", text or "", flags=re.DOTALL)

        if match:
            return json.loads(match.group(0))

        raise GeminiClientError("Gemini response was not valid JSON.")


class GeminiClient:
    def __init__(self):
        self.api_key = getattr(settings, "GEMINI_API_KEY", "")
        self.model = getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash")

        if not self.api_key:
            raise GeminiClientError("GEMINI_API_KEY is missing.")

        self.client = genai.Client(api_key=self.api_key)

    def generate_json(self, prompt):
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.4,
                    response_mime_type="application/json",
                ),
            )

            text = response.text

            return parse_json_response(text)

        except Exception as exc:
            raise GeminiClientError(str(exc)) from exc