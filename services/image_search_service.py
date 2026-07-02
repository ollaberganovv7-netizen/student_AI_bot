from __future__ import annotations
"""
Image search via Unsplash + Pexels (both free) + Gemini AI image generation.
"""
import logging
import os
import base64

import httpx

logger = logging.getLogger(__name__)

UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


async def search_unsplash(query: str, count: int = 3) -> list[str]:
    """Search Unsplash for free photos. Returns list of image URLs."""
    if not UNSPLASH_ACCESS_KEY:
        return []
    url = "https://api.unsplash.com/search/photos"
    params = {"query": query, "per_page": count, "orientation": "landscape"}
    headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code != 200:
                logger.warning("Unsplash %d: %s", resp.status_code, resp.text[:200])
                return []
            data = resp.json()
            return [r["urls"]["regular"] for r in data.get("results", [])]
    except Exception as e:
        logger.error("Unsplash error: %s", e)
        return []


async def search_pexels(query: str, count: int = 3) -> list[str]:
    """Search Pexels for free photos."""
    if not PEXELS_API_KEY:
        return []
    url = "https://api.pexels.com/v1/search"
    params = {"query": query, "per_page": count, "orientation": "landscape"}
    headers = {"Authorization": PEXELS_API_KEY}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code != 200:
                logger.warning("Pexels %d", resp.status_code)
                return []
            data = resp.json()
            return [p["src"]["large"] for p in data.get("photos", [])]
    except Exception as e:
        logger.error("Pexels error: %s", e)
        return []


async def generate_image_gemini(query: str) -> bytes | None:
    """Generate image via Gemini AI. Returns image bytes or None."""
    if not GEMINI_API_KEY:
        return None
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent?key={GEMINI_API_KEY}"
    
    prompt = (
        f"Generate a HIGH-QUALITY professional image for an academic presentation slide.\n\n"
        f"TOPIC: {query}\n\n"
        f"STYLE REQUIREMENTS:\n"
        f"- Educational, informative, and directly related to the TOPIC above\n"
        f"- Style: clean infographic, diagram, chart, or conceptual illustration\n"
        f"- Professional color palette (blues, teals, soft gradients)\n"
        f"- Modern flat design or isometric style\n"
        f"- Suitable for a university academic presentation\n"
        f"- Landscape orientation (4:3 ratio)\n"
        f"- High resolution, crisp and sharp\n\n"
        f"ABSOLUTE RULES (MUST FOLLOW):\n"
        f"- The image MUST be directly relevant to: {query}\n"
        f"- ABSOLUTELY NO TEXT anywhere on the image! No words, no labels, no titles!\n"
        f"- NO letters, NO numbers, NO signs, NO writing of ANY kind!\n"
        f"- NO watermarks, NO logos, NO stamps!\n"
        f"- NO borders, NO frames\n"
        f"- The image must clearly represent the topic visually"
    )
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]}
    }
    
    # Try up to 2 times in case of transient failures
    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code != 200:
                    logger.warning("Gemini Image attempt %d, status %d: %s", attempt+1, resp.status_code, resp.text[:150])
                    if attempt == 0:
                        import asyncio
                        await asyncio.sleep(2)
                        continue
                    return None
                
                data = resp.json()
                parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                for p in parts:
                    if "inlineData" in p:
                        img_bytes = base64.b64decode(p["inlineData"]["data"])
                        logger.info("✅ Gemini generated image for: %s", query[:50])
                        return img_bytes
                return None
        except Exception as e:
            logger.error("Gemini Image attempt %d error: %s", attempt+1, e)
            if attempt == 0:
                import asyncio
                await asyncio.sleep(2)
                continue
            return None
    return None


async def search_image(query: str) -> str | None:
    """
    Find one image URL for the query.
    Searches Pexels + Unsplash in parallel, returns first available.
    """
    if not query:
        return None
        
    query_lower = query.lower()
    if "mirziyoyev" in query_lower or "prezident" in query_lower:
        return "https://upload.wikimedia.org/wikipedia/commons/c/cd/Shavkat_Mirziyoyev_official_portrait_%28cropped_2%29.jpg"
        
    import asyncio
    # Search both in parallel
    pexels_task = asyncio.create_task(search_pexels(query, count=3))
    unsplash_task = asyncio.create_task(search_unsplash(query, count=3))
    
    pexels_urls, unsplash_urls = await asyncio.gather(pexels_task, unsplash_task)
    
    # Combine results, prefer variety
    all_urls = []
    if pexels_urls:
        all_urls.extend(pexels_urls)
    if unsplash_urls:
        all_urls.extend(unsplash_urls)
    
    return all_urls[0] if all_urls else None


async def search_images_batch(queries: list[str]) -> list[str | None]:
    """Find one image per query, in order."""
    import asyncio
    return await asyncio.gather(*[search_image(q) for q in queries])


async def download_image(url: str) -> bytes | None:
    """Download image bytes from URL."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                return resp.content
            return None
    except Exception as e:
        logger.error("Image download error: %s", e)
        return None
