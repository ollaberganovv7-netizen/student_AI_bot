from __future__ import annotations
"""
Gemini AI service — research, Google Search grounding, image finding.
Used as the "researcher" before OpenAI formats the content.
"""
import logging
import os
import asyncio
import json
import re
from typing import Any

import httpx

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"


class GeminiError(Exception):
    pass


async def _call_gemini(
    prompt: str,
    use_search: bool = False,
    temperature: float = 0.7,
    max_tokens: int = 8000,
) -> str:
    """Low-level Gemini call. If use_search=True — enables Google Search grounding."""
    if not GEMINI_API_KEY:
        raise GeminiError("GEMINI_API_KEY is not configured")

    url = f"{GEMINI_BASE}/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"

    body: dict[str, Any] = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        },
    }
    if use_search:
        body["tools"] = [{"google_search": {}}]

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(url, json=body)
        if resp.status_code != 200:
            logger.error("Gemini error %d: %s", resp.status_code, resp.text[:300])
            raise GeminiError(f"Gemini API {resp.status_code}")
        data = resp.json()

    try:
        parts = data["candidates"][0]["content"]["parts"]
        return "".join(p.get("text", "") for p in parts).strip()
    except (KeyError, IndexError) as e:
        logger.error("Gemini parse error: %s — %s", e, data)
        raise GeminiError("Unexpected response shape")


async def research_topic(
    topic: str,
    language: str = "uz",
    num_slides: int = 10,
) -> dict:
    """
    Research a topic using Google Search grounding.
    Returns structured facts: key points, dates, names, image search queries.
    """
    lang_map = {
        "uz": "o'zbek tilida",
        "ru": "на русском языке",
        "en": "in English",
    }
    lang_instruction = lang_map.get(language, "o'zbek tilida")

    prompt = f"""Sen taqdimot uchun mavzuni chuqur o'rganadigan tadqiqotchisan.

MAVZU: "{topic}"

Vazifang:
1. Google'da qidirib, eng yangi va to'g'ri ma'lumotlarni to'pla
2. {num_slides} ta slayd uchun yetarli faktlar yig'
3. Muhim sanalar, ismlar, raqamlarni topib chiqar
4. Har bir slayd uchun rasm qidirish so'rovini (image search query) yoz

Javobni QAT'IY quyidagi JSON formatda ber ({lang_instruction} matnlar bilan):

```json
{{
  "title": "Taqdimot sarlavhasi",
  "summary": "1-2 jumla umumiy ta'rif",
  "key_facts": [
    "Muhim fakt 1 (aniq raqam/sana bilan)",
    "Muhim fakt 2",
    "..."
  ],
  "important_dates": ["1991", "2016", "..."],
  "key_people": ["Ism Familiya — qisqa rol", "..."],
  "sections": [
    {{
      "slide_title": "Slayd 1 sarlavhasi",
      "content_points": ["Asosiy gap 1", "Asosiy gap 2", "Asosiy gap 3"],
      "image_query": "english image search query for this slide"
    }}
  ],
  "sources": ["url1", "url2"]
}}
```

Faqat JSON ber, boshqa hech narsa yozma.
"""

    raw = await _call_gemini(prompt, use_search=True, temperature=0.5, max_tokens=10000)

    # Try to extract JSON
    match = re.search(r"\{[\s\S]*\}", raw)
    if not match:
        logger.warning("Gemini: no JSON in response, returning empty research")
        return {"title": topic, "key_facts": [], "sections": []}

    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError as e:
        logger.error("Gemini JSON parse error: %s", e)
        return {"title": topic, "key_facts": [], "sections": []}


async def summarize_long_text(text: str, language: str = "uz", max_words: int = 1000) -> str:
    """
    Use Gemini's huge context (2M tokens) to summarize very long texts.
    Useful for processing lecture PDFs, books, etc.
    """
    lang_map = {"uz": "o'zbek tilida", "ru": "на русском языке", "en": "in English"}
    lang = lang_map.get(language, "o'zbek tilida")

    prompt = f"""Quyidagi matnni {lang} {max_words} ta so'zda professional konspekt qilib chiqar.
Asosiy g'oyalar, sanalar, ismlar, raqamlarni saqla. Ortiqcha so'zlarni olib tashla.

MATN:
{text}

KONSPEKT:"""

    return await _call_gemini(prompt, use_search=False, temperature=0.4, max_tokens=8000)


async def is_available() -> bool:
    """Quick check if Gemini API key is configured and working."""
    if not GEMINI_API_KEY:
        return False
    try:
        await _call_gemini("Hi", use_search=False, max_tokens=10)
        return True
    except Exception:
        return False
