import asyncio
import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

async def test_models():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    client = anthropic.AsyncAnthropic(api_key=api_key)
    
    models = [
        "claude-3-5-sonnet-20240620",
        "claude-3-sonnet-20240229",
        "claude-3-opus-20240229",
        "claude-sonnet-4-6" # The hardcoded one
    ]
    
    for model in models:
        try:
            print(f"Testing {model}...")
            response = await client.messages.create(
                model=model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            print(f"SUCCESS with {model}!")
        except Exception as e:
            print(f"Failed {model}: {e}")

if __name__ == "__main__":
    asyncio.run(test_models())
