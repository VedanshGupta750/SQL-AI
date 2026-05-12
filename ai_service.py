import time
import itertools
from openai import OpenAI


class AIService:
    def __init__(self, api_keys: list[str], model_names: list[str]):
        if not api_keys:
            raise ValueError("AIService requires at least one OpenAI API key.")
        if not model_names:
            raise ValueError("AIService requires at least one model name.")
        self.api_keys = list(api_keys)
        self.model_names = list(model_names)
        self.api_key_cycle = itertools.cycle(self.api_keys)
        self.model_cycle = itertools.cycle(self.model_names)
        self._init_client()

    def _init_client(self):
        self.current_key = next(self.api_key_cycle)
        self.current_model = next(self.model_cycle)
        self.client = OpenAI(api_key=self.current_key)

    def _make_call_with_retry(self, system_instruction: str, user_content: str):
        max_retries = max(len(self.api_keys), len(self.model_names)) * 2
        attempts = 0
        while attempts < max_retries:
            try:
                return self.client.chat.completions.create(
                    model=self.current_model,
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": user_content},
                    ],
                )
            except Exception as e:
                error_msg = str(e).lower()
                transient = any(s in error_msg for s in (
                    "429", "rate_limit", "rate limit", "quota", "insufficient_quota",
                    "503", "service_unavailable", "unavailable", "overloaded",
                    "500", "internal_error", "internal server error",
                    "502", "bad gateway",
                    "504", "gateway timeout", "timeout",
                    "invalid_api_key", "incorrect api key", "api key expired",
                ))
                if transient:
                    attempts += 1
                    print(f"[WARN] Transient OpenAI error. Rotating credentials... ({e})")
                    self._init_client()
                    time.sleep(2 ** min(attempts, 4))
                else:
                    raise e
        raise Exception(f"Max retries ({max_retries}) reached: all OpenAI credentials/models exhausted.")

    def chat(self, system_instruction: str, user_content: str) -> str:
        try:
            response = self._make_call_with_retry(system_instruction, user_content)
            text = response.choices[0].message.content or ""
            if text.startswith("```"):
                text = (text.replace("```sql", "")
                            .replace("```python", "")
                            .replace("```json", "")
                            .replace("```", ""))
            return text.strip()
        except Exception as e:
            print(f"[ERROR] OpenAI API Error: {str(e)}")
            return ""

    def validate_sql_safety(self, sql_query: str, safe_mode: bool) -> bool:
        if not sql_query: return False
        if not safe_mode: return True
        forbidden = ["insert", "update", "delete", "drop", "alter", "truncate", "grant", "revoke"]
        return not any(word in sql_query.lower() for word in forbidden)

    def fix_sql(self, original_sql: str, error_message: str, schema_str: str, dialect: str) -> str:
        system_instruction = f"You are a {dialect.upper()} SQL Expert. Fix the provided SQL based on the error message."
        user_content = f"Schema: {schema_str}\nOriginal SQL: {original_sql}\nError: {error_message}\nProvide ONLY the corrected raw SQL. No markdown."
        return self.chat(system_instruction, user_content)
