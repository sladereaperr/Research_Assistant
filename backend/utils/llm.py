# backend/utils/llm.py  — replace existing generate / generate_json implementations with this

import os
import google.generativeai as genai
from typing import Optional, Dict, Any
import json
import re
from dotenv import load_dotenv
load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class LLMClient:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.model_name = model_name
        self.model = None
        try:
            self.model = genai.GenerativeModel(model_name)
        except Exception as e:
            print(f"[LLMClient] Failed to initialize model '{model_name}': {e}")
            try:
                available = genai.list_models()
                print("[LLMClient] Available models (sample):")
                try:
                    for m in available[:10]:
                        print("  -", getattr(m, "name", str(m)))
                except Exception:
                    print(available)
            except Exception as e2:
                print("[LLMClient] Could not list models:", e2)
            self.model = None

    async def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2048) -> str:
        """Generate text using Gemini. Handles multi-part responses robustly."""
        if self.model is None:
            print("[LLMClient] generate() called but model is not available — returning empty string fallback.")
            return ""

        try:
            # SDK may return an object with different shapes. Call generate_content and then
            # extract text from whichever attribute exists.
            result = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                )
            )

            # Common accessor: response.text (works for simple single-part responses)
            if hasattr(result, "text") and isinstance(getattr(result, "text"), str):
                return result.text

            # Newer SDK shapes: result.result.parts or result.candidates[index].content.parts
            # Try a few safe access patterns:
            try:
                # result.result.parts is often a list of Part objects with a 'text' field
                if hasattr(result, "result") and hasattr(result.result, "parts"):
                    parts = result.result.parts
                    texts = []
                    for p in parts:
                        # each part might have 'text' or 'content' attributes
                        if hasattr(p, "text"):
                            texts.append(p.text)
                        elif hasattr(p, "content"):
                            texts.append(getattr(p.content, "text", str(p.content)))
                        else:
                            texts.append(str(p))
                    return "\n".join(texts)
            except Exception:
                pass

            try:
                # Another representation: result.candidates -> list -> content.parts
                if hasattr(result, "candidates"):
                    candidates = result.candidates
                    if len(candidates) > 0 and hasattr(candidates[0], "content"):
                        content = candidates[0].content
                        if hasattr(content, "parts"):
                            texts = [getattr(part, "text", str(part)) for part in content.parts]
                            return "\n".join(texts)
                        # fallback to stringifying content
                        return str(content)
            except Exception:
                pass

            # Last resort: stringify the whole result object
            return str(result)

        except Exception as e:
            print(f"[LLMClient] Error generating content: {e}")
            return ""

    async def generate_json(self, prompt: str, temperature: float = 0.7) -> Dict[Any, Any]:
        """Produce JSON from model output, robust to multi-part responses."""
        if self.model is None:
            print("[LLMClient] generate_json() called but model is not available — returning {} fallback.")
            return {}

        full_prompt = f"{prompt}\n\nReturn ONLY valid JSON, no markdown or explanation."
        try:
            response_text = await self.generate(full_prompt, temperature, max_tokens=2048)
            if not response_text:
                return {}
            # Attempt to extract JSON blocks first
            json_match = re.search(r'```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```', response_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except Exception:
                    pass
            # Try to parse the whole text
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                # Try to find first {...} or [...] chunk
                json_match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', response_text)
                if json_match:
                    try:
                        return json.loads(json_match.group(1))
                    except Exception:
                        pass
            print(f"[LLMClient] Failed to parse JSON from response: {response_text[:600]}")
            return {}
        except Exception as e:
            print(f"[LLMClient] generate_json error: {e}")
            return {}

# Create a global instance (optionally set model via env)
llm_client = LLMClient(model_name=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
