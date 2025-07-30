from typing import Optional
import os
from openai import AsyncOpenAI

client = AsyncOpenAI()


async def generate_file_description(content: str) -> Optional[str]:
    """Generate a description for file content using OpenAI.
    Args:
        content: The file content to generate description for (first 1000 words used)

    Returns:
        Generated description or None if generation fails
    """
    try:
        # Get first 1000 words
        words = content.split()[:1000]
        truncated_content = " ".join(words)

        # Use OpenAI to generate description
        response = await client.chat.completions.create(
            model=os.environ.get("LLM_MODEL"),
            messages=[
                {
                    "role": "system",
                    "content": "Generate a concise description of the provided file content.",
                },
                {
                    "role": "user",
                    "content": f"File content:\n{truncated_content}",
                },
            ],
            temperature=0.3,
            max_tokens=512,
        )
        return response.choices[0].message.content.strip() if response.choices else None
    except Exception:
        return None
