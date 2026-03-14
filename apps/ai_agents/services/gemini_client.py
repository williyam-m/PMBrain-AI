"""
Gemini AI Client for PMBrain AI.
Uses the Gemini REST API directly for maximum compatibility.
All responses come from live Gemini API — no mocked outputs.
Supports retry logic, timeout handling, structured JSON output, and streaming.
"""
import json
import logging
import os
import re
import time
import requests as http_requests

logger = logging.getLogger('pmbrain')


class GeminiAPIError(Exception):
    """Raised when Gemini API call fails after all retries."""
    pass


class GeminiClient:
    """
    Production-grade Gemini AI client using REST API.
    No mocks, no stubs — all responses are live from Gemini.
    """

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY', '')
        self.model = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash-lite')
        self.fallback_model = os.getenv('GEMINI_FALLBACK_MODEL', 'gemini-flash-lite-latest')
        self.max_retries = int(os.getenv('GEMINI_MAX_RETRIES', '3'))
        self.timeout = int(os.getenv('GEMINI_TIMEOUT', '60'))
        self._request_count = 0
        self._token_count = 0

        if not self.api_key:
            logger.error("GEMINI_API_KEY not set. All AI calls will fail.")
        else:
            logger.info(f"Gemini AI client initialized. Model: {self.model}, Fallback: {self.fallback_model}")

    @property
    def is_available(self):
        return bool(self.api_key)

    def generate(self, prompt, response_format="json", temperature=0.3, max_tokens=8192):
        """
        Generate a response from Gemini API.
        Returns parsed JSON when response_format is 'json'.
        Returns raw text when response_format is 'text'.

        Raises GeminiAPIError if all retries fail.
        """
        if not self.api_key:
            raise GeminiAPIError("GEMINI_API_KEY is not configured. Please set it in .env file.")

        start_time = time.time()
        self._request_count += 1

        # For JSON responses, instruct the model clearly
        full_prompt = prompt
        if response_format == "json":
            full_prompt += "\n\nCRITICAL INSTRUCTION: You MUST respond with ONLY valid JSON. No markdown code fences (```), no explanatory text before or after the JSON. Start your response with { or [ and end with } or ]."

        # Try primary model, then fallback
        models_to_try = [self.model, self.fallback_model]
        last_error = None

        for model_name in models_to_try:
            for attempt in range(self.max_retries):
                try:
                    result = self._call_api(model_name, full_prompt, temperature, max_tokens)
                    duration = time.time() - start_time

                    logger.info(
                        f"Gemini API success | model={model_name} | "
                        f"attempt={attempt+1} | duration={duration:.2f}s | "
                        f"prompt_len={len(prompt)} | response_len={len(str(result))}"
                    )

                    if response_format == "json":
                        return self._parse_json_response(result)
                    return result

                except http_requests.exceptions.Timeout:
                    last_error = f"Timeout after {self.timeout}s"
                    logger.warning(f"Gemini timeout | model={model_name} | attempt={attempt+1}")
                    time.sleep(min(2 ** attempt, 8))

                except http_requests.exceptions.ConnectionError as e:
                    last_error = f"Connection error: {str(e)}"
                    logger.warning(f"Gemini conn error | model={model_name} | attempt={attempt+1}")
                    time.sleep(min(2 ** attempt, 8))

                except GeminiAPIError as e:
                    error_msg = str(e)
                    last_error = error_msg

                    if "429" in error_msg or "quota" in error_msg.lower():
                        wait_time = min(2 ** (attempt + 1), 16)
                        logger.warning(f"Gemini rate limit | model={model_name} | waiting {wait_time}s")
                        time.sleep(wait_time)
                        continue

                    if "404" in error_msg or "not found" in error_msg.lower():
                        logger.warning(f"Model {model_name} not available, trying next")
                        break

                    logger.warning(f"Gemini API error | model={model_name} | attempt={attempt+1} | {error_msg[:200]}")
                    if attempt < self.max_retries - 1:
                        time.sleep(min(2 ** attempt, 8))

                except json.JSONDecodeError as e:
                    last_error = f"JSON parse error: {str(e)}"
                    logger.warning(f"Gemini JSON error | model={model_name} | attempt={attempt+1}")
                    if attempt < self.max_retries - 1:
                        time.sleep(1)

                except Exception as e:
                    last_error = str(e)
                    logger.error(f"Unexpected Gemini error | model={model_name} | {e}")
                    if attempt < self.max_retries - 1:
                        time.sleep(min(2 ** attempt, 8))

        raise GeminiAPIError(f"All Gemini API attempts failed. Last error: {last_error}")

    def generate_streaming(self, prompt, temperature=0.3, max_tokens=8192):
        """
        Generate a streaming response from Gemini.
        Yields text chunks as they arrive.
        """
        if not self.api_key:
            raise GeminiAPIError("GEMINI_API_KEY is not configured.")

        url = f"{self.BASE_URL}/models/{self.model}:streamGenerateContent?key={self.api_key}&alt=sse"
        payload = self._build_payload(prompt, temperature, max_tokens)

        try:
            response = http_requests.post(url, json=payload, timeout=self.timeout, stream=True)
            if response.status_code != 200:
                raise GeminiAPIError(f"Gemini streaming error {response.status_code}: {response.text[:500]}")

            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])
                            candidates = data.get('candidates', [])
                            if candidates:
                                parts = candidates[0].get('content', {}).get('parts', [])
                                for part in parts:
                                    if 'text' in part:
                                        yield part['text']
                        except json.JSONDecodeError:
                            continue
        except http_requests.exceptions.Timeout:
            raise GeminiAPIError(f"Streaming timeout after {self.timeout}s")

    def _call_api(self, model_name, prompt, temperature, max_tokens):
        """Make a single API call to Gemini."""
        url = f"{self.BASE_URL}/models/{model_name}:generateContent?key={self.api_key}"
        payload = self._build_payload(prompt, temperature, max_tokens)

        response = http_requests.post(url, json=payload, timeout=self.timeout)

        if response.status_code != 200:
            error_data = {}
            try:
                error_data = response.json()
            except Exception:
                pass
            error_msg = error_data.get('error', {}).get('message', response.text[:500])
            raise GeminiAPIError(f"Gemini API error {response.status_code}: {error_msg}")

        data = response.json()
        candidates = data.get('candidates', [])
        if not candidates:
            raise GeminiAPIError("Gemini returned no candidates")

        content = candidates[0].get('content', {})
        parts = content.get('parts', [])
        if not parts:
            raise GeminiAPIError("Gemini returned empty content")

        text = parts[0].get('text', '')

        usage = data.get('usageMetadata', {})
        self._token_count += usage.get('totalTokenCount', 0)

        return text.strip()

    def _build_payload(self, prompt, temperature, max_tokens):
        """Build the API request payload."""
        return {
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': {
                'temperature': temperature,
                'maxOutputTokens': max_tokens,
                'topP': 0.95,
            },
            'safetySettings': [
                {'category': 'HARM_CATEGORY_HARASSMENT', 'threshold': 'BLOCK_NONE'},
                {'category': 'HARM_CATEGORY_HATE_SPEECH', 'threshold': 'BLOCK_NONE'},
                {'category': 'HARM_CATEGORY_SEXUALLY_EXPLICIT', 'threshold': 'BLOCK_NONE'},
                {'category': 'HARM_CATEGORY_DANGEROUS_CONTENT', 'threshold': 'BLOCK_NONE'},
            ]
        }

    def _parse_json_response(self, text):
        """Parse JSON from Gemini response, handling common formatting issues."""
        if not text:
            raise GeminiAPIError("Empty response from Gemini")

        cleaned = text.strip()
        cleaned = re.sub(r'^```(?:json)?\s*\n?', '', cleaned)
        cleaned = re.sub(r'\n?\s*```\s*$', '', cleaned)
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            json_match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', cleaned)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass

            raise json.JSONDecodeError(
                f"Could not parse JSON from Gemini: {cleaned[:200]}",
                cleaned, 0
            )

    @property
    def stats(self):
        return {
            'total_requests': self._request_count,
            'total_tokens': self._token_count,
        }


# Singleton instance
gemini = GeminiClient()
