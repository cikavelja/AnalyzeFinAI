---
description: "Use when creating or editing Pydantic data models in app/models/. Covers Pydantic v2 conventions, field patterns, UUID ids, datetime handling, and serialization."
applyTo: "app/models/**/*.py"
---
# Pydantic v2 Model Conventions

## Required Patterns

- Use `model_config = ConfigDict(...)` — never the inner `class Config`.
- Every model id field must be `UUID` with `default_factory=uuid4`.
- All `datetime` fields must be timezone-aware: `datetime` with `default_factory=lambda: datetime.now(UTC)`.
- Use `Field(default_factory=...)` for mutable defaults (lists, dicts). Never use `= []`.
- Prefer `Annotated` types for reusable field constraints.
- Optional fields: `field: str | None = None` — never `Optional[str]`.

## Serialization

- Use `model.model_dump(mode="json")` for JSON-safe output.
- Use `model.model_dump_json()` only for string output.
- Never call `.dict()` or `.json()` — those are Pydantic v1 APIs.

## Example

```python
from uuid import UUID, uuid4
from datetime import datetime, UTC
from pydantic import BaseModel, ConfigDict, Field

class DocumentMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    file_name: str
    file_size: int
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
```

## Anti-Patterns

- No bare `class Config` inner class.
- No `Optional[T]` — use `T | None`.
- No mutable default values directly on fields.
- No `Any` type unless absolutely unavoidable.
