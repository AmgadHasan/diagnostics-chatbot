from __future__ import annotations as _annotations

import os
from dataclasses import dataclass
from typing import Any, Dict
import json

from langfuse import get_client
from pydantic_ai import Agent, RunContext
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool
from pydantic_ai.messages import (
    ModelMessage,
)
from pydantic_ai.settings import ModelSettings

from .utils import JSONStorage, get_uploaded_files
from .ingest import search_knowledge_base, ingest_file

langfuse = get_client()

# Verify connection
if langfuse.auth_check():
    print("Langfuse client is authenticated and ready!")
else:
    print("Authentication failed. Please check your credentials and host.")
Agent.instrument_all()


MAIN_SYSTEM_MESSAGE = """You're an AI assistant that helps users with debugging and troubleshooting problems in industrial and mechanical systems.
You're friendly and helpful. You ask the user clarifying questions that are needed to help them with their problem.
Make sure that the response you return to the user is readable and nicely formatted using markdown.

You have the ability to search the web for manuals and documentation to help the user.
To do that, make sure to ask the user to get more information (e.g. make/model/manufacturer info for machines/equipments)

You have access to the following tools:
1. search_knowledge_base: Allows you to search an internal knowledge base using a query.
2. duckduckgo_search: Allows you to search the web using the duckduck go tool

If your response is based on information retrieved from the internal knowledge base, make sure to cite it properly as follows:
Use markdown formatting to cite using the footnote style as follows:

```md
<Some text here based on information from source 1>[^1].
<Some other text here >
<Some text here based on information from source 2>[^2].

______
Sources:

1: name: <source 1 name>, page: <page number or url>
2: name: <source 2 name>, page: <page number or url>
```

"""


@dataclass
class AgentDeps:
    uploaded_files: Dict[str, Dict[str, Any]]


# Initialize the AI agent
agent = Agent(
    f"openai:{os.environ.get('LLM_MODEL')}",
    deps_type=AgentDeps,
    tools=[duckduckgo_search_tool(), search_knowledge_base, ingest_file],
    model_settings=ModelSettings(temperature=0.1),
)


@agent.system_prompt
async def get_system_prompt(ctx: RunContext[AgentDeps]) -> str:
    files = get_uploaded_files()

    return f"""{MAIN_SYSTEM_MESSAGE}
    
Available Uploaded Files:

{json.dumps(files, ensure_ascii=False, indent=2)}
"""


async def process_chat_message(message: str, storage: JSONStorage) -> str:
    """Process a chat message and return AI response."""
    # Get chat history
    messages = await storage.get_messages()

    # Run the agent with the user prompt and chat history
    result = await agent.run(message, message_history=messages)

    # Add new messages to storage
    await storage.add_messages(result.new_messages_json())

    # Return response
    return result.data


async def get_chat_history(storage: JSONStorage) -> list[ModelMessage]:
    """Retrieve chat history from storage."""
    return await storage.get_messages()
