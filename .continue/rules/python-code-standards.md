---
globs: "**/*.py"
description: Standard code style and requirements for the diagnostics-chatbot project.
alwaysApply: true
---

Use Python 3.10+ syntax and features. All functions and variables must have type hints. Use Pydantic v2 for data validation and configuration. Prefer explicit imports. Follow PEP 8 style guide with 4-space indentation. When type hinting, use `list`, `tuple`, `dict`, `set` directly instead of importing `List`, `Tuple` etc `from typing`.

Use the following simplified 3-Tier Project Structure (Small App):
src/
├── main.py                 # FastAPI app, includes routes
├── database.py             # DB session and engine
├── services/
│   └── user_service.py     # Business logic
├── models/
│   └── user.py             # ORM model
└── schemas/
    └── user.py             # Pydantic models