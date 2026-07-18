from src.ai.gemini_provider import GeminiProvider

ai = GeminiProvider()

answer = ai.chat(

"""
You are a CFO.

Say hello in one sentence.

"""

)

print(answer)