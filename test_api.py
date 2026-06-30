import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_anthropic():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("No Anthropic API key found.")
        return
        
    try:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=api_key)
        print("Testing Anthropic (Claude) API...")
        response = await client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=50,
            messages=[{"role": "user", "content": "Hello! Reply with exactly 'OK' if you receive this."}]
        )
        print("SUCCESS! Claude is working. Response:", response.content[0].text)
    except Exception as e:
        print(f"Anthropic ERROR: {e}")

async def test_openai():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("No OpenAI API key found.")
        return
        
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=api_key)
        print("Testing OpenAI API...")
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            max_tokens=50,
            messages=[{"role": "user", "content": "Hello! Reply with exactly 'OK' if you receive this."}]
        )
        print("SUCCESS! OpenAI is working. Response:", response.choices[0].message.content)
    except Exception as e:
        print(f"OpenAI ERROR: {e}")

async def main():
    await test_anthropic()
    print("-" * 30)
    await test_openai()

if __name__ == "__main__":
    asyncio.run(main())
