import os
from typing import Optional

try:
    import google.generativeai as genai
except ImportError:
    raise ImportError("google-generativeai package not found. Install it with: pip install google-generativeai")

from dotenv import load_dotenv

load_dotenv()


class GeminiProvider:

    def __init__(self):

        genai.configure(
            api_key=os.getenv("GEMINI_API_KEY")
        )

        self.model = genai.GenerativeModel(
            "gemini-3.1-flash-lite"
        )

    def chat(self, prompt):

        response = self.model.generate_content(
            prompt
        )

        return response.text