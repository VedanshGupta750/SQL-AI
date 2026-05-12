import json
from google import genai
from google.genai import types

import time
import itertools

class GeminiRateLimitError(Exception):
    pass

class AIService:
    def __init__(self, api_keys: list[str], model_names: list[str]):
        self.api_keys = list(api_keys)
        self.model_names = list(model_names)
        self.api_key_cycle = itertools.cycle(self.api_keys)
        self.model_cycle = itertools.cycle(self.model_names)
        self._init_client()

    def _init_client(self):
        self.current_key = next(self.api_key_cycle)
        self.current_model = next(self.model_cycle)
        self.client = genai.Client(api_key=self.current_key)

    def _make_gemini_call_with_retry(self, system_instruction: str, user_content: str):
        max_retries = len(self.api_keys) * 2 # Allow wrapping around at least twice
        attempts = 0
        while attempts < max_retries:
            try:
                return self.client.models.generate_content(
                    model=self.current_model,
                    config=types.GenerateContentConfig(system_instruction=system_instruction),
                    contents=user_content
                )
            except Exception as e:
                error_msg = str(e).lower()
                transient = any(s in error_msg for s in (
                    "429", "resource_exhausted", "quota",
                    "503", "unavailable", "overloaded",
                    "500", "internal",
                    "api_key_invalid", "api key expired", "api_key_expired",
                ))
                if transient:
                    attempts += 1
                    print(f"[WARN] Transient Gemini error. Rotating credentials... ({e})")
                    self._init_client()
                    time.sleep(2 ** min(attempts, 4))
                else:
                    raise e
        raise Exception(f"Max retries ({max_retries}) reached: All API keys exhausted.")

    def gemini_call(self, system_instruction: str, user_content: str) -> str:
        try:
            response = self._make_gemini_call_with_retry(system_instruction, user_content)
            text = response.text
            if text.startswith("```"):
                text = text.replace("```sql", "").replace("```python", "").replace("```json", "").replace("```", "")
            return text.strip()
        except Exception as e:
            print(f"[ERROR] Gemini API Error: {str(e)}")
            return ""

    def validate_sql_safety(self, sql_query: str, safe_mode: bool) -> bool:
        if not sql_query: return False
        if not safe_mode: return True
        forbidden = ["insert", "update", "delete", "drop", "alter", "truncate", "grant", "revoke"]
        return not any(word in sql_query.lower() for word in forbidden)

    def fix_sql(self, original_sql: str, error_message: str, schema_str: str, dialect: str) -> str:
        system_instruction = f"You are a {dialect.upper()} SQL Expert. Fix the provided SQL based on the error message."
        user_content = f"Schema: {schema_str}\nOriginal SQL: {original_sql}\nError: {error_message}\nProvide ONLY the corrected raw SQL. No markdown."
        return self.gemini_call(system_instruction, user_content)
