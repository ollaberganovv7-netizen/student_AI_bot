import asyncio
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

async def test_gemini():
    client = AsyncOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL")
    )
    
    model = os.getenv("OPENAI_MODEL")
    print(f"Testing connection to {model} via {os.getenv('OPENAI_BASE_URL')}...")
    
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Hello, are you connected?"}],
            max_tokens=50
        )
        print("SUCCESS! Response:")
        print(response.choices[0].message.content)
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_gemini())
