import asyncio
import os
import sys
import json
from dotenv import load_dotenv

sys.path.append(r'C:\Users\Шухрат\Desktop\Новая папка\student_AI_bot')
load_dotenv()

from services.ai_service import generate_presentation_content

async def test():
    print("Testing presentation structure generation...")
    # Generate content
    content_json = await generate_presentation_content(
        topic="Sog'lom turmush tarzi",
        language="uz",
        num_slides=10,
        quality="premium",
        num_chapters=2
    )
    
    data = json.loads(content_json)
    slides = data.get("slides", [])
    
    print(f"\nJami Slaydlar: {len(slides)} ta\n")
    for i, slide in enumerate(slides):
        title = slide.get("title", "")
        # Print first few characters of content
        c_list = slide.get("content", [])
        content_preview = str(c_list[0])[:30] + "..." if c_list else ""
        print(f"Slayd {i+2}: {title} | {content_preview}")
        
    print("\nEslatma: Slayd 1 - Muqova (pptx_service da qo'shiladi)")

if __name__ == '__main__':
    asyncio.run(test())
